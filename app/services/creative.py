"""Creative management service for A/B testing assets"""
import logging
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Creative, CreativeVariant, Experiment

logger = logging.getLogger(__name__)


class CreativeService:
    """Manages creative assets and their association with experiment variants"""

    @staticmethod
    def create_creative(
        name: str,
        description: str,
        creative_type: str,
        content: str,
        creative_metadata: Optional[Dict] = None,
        db: Session = None
    ) -> Creative:
        """Create a new creative asset"""
        if db is None:
            from app.database import get_db
            db = next(get_db())

        creative = Creative(
            name=name,
            description=description,
            creative_type=creative_type,
            content=content,
            creative_metadata=json.dumps(creative_metadata) if creative_metadata else None
        )

        db.add(creative)
        db.commit()
        db.refresh(creative)

        logger.info(f"Created creative: {name} (ID: {creative.id})")
        return creative

    @staticmethod
    def assign_creative_to_variant(
        experiment_id: int,
        variant: str,
        creative_id: int,
        db: Session
    ) -> CreativeVariant:
        """Assign a creative to an experiment variant"""
        # Validate experiment exists
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Validate creative exists
        creative = db.query(Creative).filter(Creative.id == creative_id).first()
        if not creative:
            raise ValueError(f"Creative {creative_id} not found")

        # Check if variant already has a creative
        existing = db.query(CreativeVariant).filter(
            CreativeVariant.experiment_id == experiment_id,
            CreativeVariant.variant == variant
        ).first()

        if existing:
            # Update existing assignment
            existing.creative_id = creative_id
            db.commit()
            logger.info(f"Updated creative assignment: experiment {experiment_id}, variant {variant}, creative {creative_id}")
            return existing
        else:
            # Create new assignment
            assignment = CreativeVariant(
                experiment_id=experiment_id,
                variant=variant,
                creative_id=creative_id
            )
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            logger.info(f"Created creative assignment: experiment {experiment_id}, variant {variant}, creative {creative_id}")
            return assignment

    @staticmethod
    def get_creative_for_variant(experiment_id: int, variant: str, db: Session) -> Optional[Dict]:
        """Get the creative assigned to a specific experiment variant"""
        result = db.query(CreativeVariant, Creative).join(
            Creative, CreativeVariant.creative_id == Creative.id
        ).filter(
            CreativeVariant.experiment_id == experiment_id,
            CreativeVariant.variant == variant
        ).first()

        if result:
            assignment, creative = result
            metadata = json.loads(creative.creative_metadata) if creative.creative_metadata else {}

            return {
                "creative_id": creative.id,
                "name": creative.name,
                "description": creative.description,
                "type": creative.creative_type,
                "content": creative.content,
                "metadata": metadata,
                "assigned_at": assignment.created_at
            }

        return None

    @staticmethod
    def get_experiment_creatives(experiment_id: int, db: Session) -> Dict[str, Optional[Dict]]:
        """Get all creatives for an experiment (control and treatment)"""
        return {
            "control": CreativeService.get_creative_for_variant(experiment_id, "control", db),
            "treatment": CreativeService.get_creative_for_variant(experiment_id, "treatment", db)
        }

    @staticmethod
    def list_creatives(db: Session, creative_type: Optional[str] = None) -> List[Dict]:
        """List all creatives, optionally filtered by type"""
        query = db.query(Creative)
        if creative_type:
            query = query.filter(Creative.creative_type == creative_type)

        creatives = query.all()

        result = []
        for creative in creatives:
            metadata = json.loads(creative.creative_metadata) if creative.creative_metadata else {}
            result.append({
                "id": creative.id,
                "name": creative.name,
                "description": creative.description,
                "type": creative.creative_type,
                "content": creative.content,
                "metadata": metadata,
                "created_at": creative.created_at
            })

        return result

    @staticmethod
    def get_creative_usage(creative_id: int, db: Session) -> Dict:
        """Get usage statistics for a creative across experiments"""
        # Count assignments
        assignments = db.query(CreativeVariant).filter(
            CreativeVariant.creative_id == creative_id
        ).all()

        # Count events
        from app.models import Event
        event_count = db.query(Event).filter(
            Event.creative_id == creative_id
        ).count()

        experiments = []
        for assignment in assignments:
            experiment = db.query(Experiment).filter(
                Experiment.id == assignment.experiment_id
            ).first()
            if experiment:
                experiments.append({
                    "experiment_id": experiment.id,
                    "experiment_name": experiment.name,
                    "variant": assignment.variant,
                    "assigned_at": assignment.created_at
                })

        return {
            "creative_id": creative_id,
            "total_experiments": len(experiments),
            "experiments": experiments,
            "total_events": event_count
        }