"""User assignment service with epsilon-greedy bandit algorithm"""
import random
from sqlalchemy.orm import Session
from app.models import Assignment, Event


class AssignmentService:
    """Handles user assignment to experiment variants using bandit algorithm"""
    
    EPSILON = 0.1  # Exploration probability
    MIN_IMPRESSIONS = 100  # Minimum impressions before exploitation
    
    @staticmethod
    def assign_user(user_id: int, experiment_id: int, db: Session) -> str:
        """
        Assign user to a variant using epsilon-greedy bandit.
        
        Strategy:
        1. If user already assigned to this experiment, return existing assignment
        2. If not enough data (impressions < MIN_IMPRESSIONS), assign randomly
        3. Else:
           - With probability epsilon: assign randomly (explore)
           - Otherwise: assign to variant with higher conversion rate (exploit)
        
        Args:
            user_id: Unique user identifier
            experiment_id: Experiment identifier
            db: Database session
            
        Returns:
            Variant name: 'control' or 'treatment'
        """
        # Check if user already has assignment for this experiment
        existing = db.query(Assignment).filter(
            Assignment.user_id == user_id,
            Assignment.experiment_id == experiment_id
        ).first()
        
        if existing:
            return existing.variant
        
        # Count total impressions across both variants
        total_impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.event_type == "impression"
        ).count()
        
        # Phase 1: Exploration (random) - when not enough data
        if total_impressions < AssignmentService.MIN_IMPRESSIONS:
            variant = random.choice(["control", "treatment"])
        else:
            # Phase 2: Epsilon-greedy decision
            if random.random() < AssignmentService.EPSILON:
                # Explore: choose random variant
                variant = random.choice(["control", "treatment"])
            else:
                # Exploit: choose variant with higher conversion rate
                variant = AssignmentService._get_best_variant(
                    experiment_id, db
                )
        
        # Record the assignment
        assignment = Assignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant=variant
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        return assignment.variant
    
    @staticmethod
    def _get_best_variant(experiment_id: int, db: Session) -> str:
        """
        Determine variant with highest conversion rate.
        Falls back to random if no data available.
        """
        for variant in ["control", "treatment"]:
            events = db.query(Event).filter(
                Event.experiment_id == experiment_id,
                Event.variant == variant
            ).all()
            
            if not events:
                continue
            
            impressions = sum(1 for e in events if e.event_type == "impression")
            conversions = sum(1 for e in events if e.event_type == "conversion")
            
            variant_rates = {}
            for v in ["control", "treatment"]:
                v_events = db.query(Event).filter(
                    Event.experiment_id == experiment_id,
                    Event.variant == v
                ).all()
                v_impressions = sum(1 for e in v_events if e.event_type == "impression")
                v_conversions = sum(1 for e in v_events if e.event_type == "conversion")
                v_rate = v_conversions / v_impressions if v_impressions > 0 else 0.0
                variant_rates[v] = v_rate
        
        # Return variant with highest conversion rate
        best = max(variant_rates, key=variant_rates.get)
        return best if variant_rates[best] > 0 else random.choice(["control", "treatment"])
