"""User assignment service with epsilon-greedy bandit algorithm and logging"""
import logging
import random
from sqlalchemy.orm import Session
from app.models import Assignment, Event

logger = logging.getLogger(__name__)


class AssignmentService:
    """Handles user assignment to experiment variants using epsilon-greedy bandit algorithm"""
    
    EPSILON = 0.1  # Exploration probability (10%)
    MIN_IMPRESSIONS = 100  # Minimum impressions before exploitation starts
    
    @staticmethod
    def assign_user(user_id: int, experiment_id: int, db: Session) -> str:
        """
        Assign user to a variant using epsilon-greedy bandit algorithm.
        
        **Algorithm:**
        
        1. **Check Existing Assignment**: If user already assigned to this experiment, return cached assignment (idempotent)
        2. **Check Experiment Status**: If experiment is paused or completed, block new assignments
        3. **Exploration Phase** (< 100 impressions): Random assignment to each variant
        4. **Exploitation Phase** (>= 100 impressions):
           - 90% of the time: Assign to variant with higher conversion rate
           - 10% of the time: Randomly assign to explore new variants
        
        This balances exploration (learning which variant is better) with exploitation 
        (using the best variant we've learned so far).
        
        **Args:**
        - user_id: Unique user identifier (positive integer)
        - experiment_id: Experiment identifier (positive integer)
        - db: Database session
            
        **Returns:**
        - Tuple of (variant_name, assignment_reason)
        - variant_name: 'control' or 'treatment'
        - assignment_reason: Explanation of why this variant was chosen
        """
        from app.models import Experiment
        
        # Check if user already has assignment for this experiment (idempotent)
        existing = db.query(Assignment).filter(
            Assignment.user_id == user_id,
            Assignment.experiment_id == experiment_id
        ).first()
        
        if existing:
            logger.debug(f"User {user_id} already assigned: {existing.variant}")
            return existing.variant, "User was previously assigned to this variant (cached result)"
        
        # Check experiment status
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found for user {user_id}")
            raise ValueError(f"Experiment {experiment_id} not found")
        
        if experiment.status == "paused":
            logger.warning(f"Attempted assignment to paused experiment {experiment_id}")
            raise ValueError(f"Experiment {experiment_id} is paused - no new assignments allowed")
        
        if experiment.status == "completed":
            logger.warning(f"Attempted assignment to completed experiment {experiment_id}")
            raise ValueError(f"Experiment {experiment_id} is completed - no new assignments allowed")
        
        # Count total impressions across both variants
        total_impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.event_type == "impression"
        ).count()
        
        # Phase 1: Exploration (random) - when not enough data
        if total_impressions < AssignmentService.MIN_IMPRESSIONS:
            variant = random.choice(["control", "treatment"])
            logger.debug(f"Exploration phase: {total_impressions} impressions, assigned random: {variant}")
            reason = f"Exploration phase ({total_impressions} impressions < {AssignmentService.MIN_IMPRESSIONS})"
        else:
            # Phase 2: Epsilon-greedy decision
            if random.random() < AssignmentService.EPSILON:
                # Explore: choose random variant
                variant = random.choice(["control", "treatment"])
                logger.debug(f"Exploitation phase (explore): assigned random: {variant}")
                reason = f"Exploitation phase with exploration (random assignment)"
            else:
                # Exploit: choose variant with higher conversion rate
                variant = AssignmentService._get_best_variant(
                    experiment_id, db
                )
                logger.debug(f"Exploitation phase (exploit): assigned best: {variant}")
                reason = f"Exploitation phase (exploit): assigned best performing variant"
        
        # Record the assignment
        assignment = Assignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant=variant
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        logger.info(f"User {user_id} assigned to {variant} for experiment {experiment_id}")
        return assignment.variant, reason
    
    @staticmethod
    def _get_best_variant(experiment_id: int, db: Session) -> str:
        """
        Determine variant with highest conversion rate.
        
        Compares conversion rates (conversions / impressions) for both variants
        and returns the one with the higher rate.
        Falls back to random assignment if no data available.
        
        **Args:**
        - experiment_id: Experiment ID to analyze
        - db: Database session
        
        **Returns:**
        - Variant name with highest conversion rate ('control' or 'treatment')
        """
        variant_rates = {}
        
        for variant in ["control", "treatment"]:
            events = db.query(Event).filter(
                Event.experiment_id == experiment_id,
                Event.variant == variant
            ).all()
            
            impressions = sum(1 for e in events if e.event_type == "impression")
            conversions = sum(1 for e in events if e.event_type == "conversion")
            conversion_rate = conversions / impressions if impressions > 0 else 0.0
            variant_rates[variant] = conversion_rate
        
        # Return variant with highest conversion rate
        best = max(variant_rates, key=variant_rates.get)
        logger.debug(f"Best variant: {best} (control CR: {variant_rates['control']:.2%}, "
                    f"treatment CR: {variant_rates['treatment']:.2%})")
        
        return best if variant_rates[best] > 0 else random.choice(["control", "treatment"])
