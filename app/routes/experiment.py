"""Experiment creation and management endpoints with logging"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from app.database import get_db
from app.models import Experiment, Event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/experiment", tags=["experiment"])


class ExperimentCreate(BaseModel):
    """Request model for creating an experiment"""
    name: str = Field(..., min_length=1, max_length=255, description="Unique experiment name (e.g., 'homepage_banner_v1')")


class ExperimentResponse(BaseModel):
    """Response model for experiment with helpful metadata"""
    id: int = Field(..., description="Unique experiment identifier")
    name: str = Field(..., description="Experiment name")
    status: str = Field(..., description="Current status: active or completed")
    created_at: datetime = Field(..., description="Timestamp when experiment was created")
    next_steps: str = Field(..., description="Suggested next action")
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """
    Create a new A/B testing experiment.
    
    **Parameters:**
    - **name**: Unique experiment name (1-255 characters, e.g., "homepage_banner_v1")
    
    **Returns:** The created experiment with auto-generated ID
    
    **Raises:**
    - 400: Experiment with this name already exists
    """
    try:
        # Validate name is not empty
        if not experiment.name or not experiment.name.strip():
            raise HTTPException(
                status_code=400,
                detail="Experiment name cannot be empty"
            )
        
        # Check if experiment already exists
        existing = db.query(Experiment).filter(
            Experiment.name == experiment.name
        ).first()
        
        if existing:
            logger.warning(f"Attempt to create duplicate experiment: {experiment.name}")
            raise HTTPException(
                status_code=400,
                detail=f"Experiment '{experiment.name}' already exists (ID: {existing.id})"
            )
        
        # Create new experiment
        logger.info(f"Creating new experiment: {experiment.name}")
        db_experiment = Experiment(name=experiment.name)
        db.add(db_experiment)
        db.commit()
        db.refresh(db_experiment)
        
        logger.info(f"Experiment created successfully: ID {db_experiment.id}, name {experiment.name}")
        
        return ExperimentResponse(
            id=db_experiment.id,
            name=db_experiment.name,
            status=db_experiment.status,
            created_at=db_experiment.created_at,
            next_steps=f"Ready to assign users! Use GET /assign?user_id=1&experiment_id={db_experiment.id} to start"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during experiment creation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during experiment creation"
        )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """
    Retrieve experiment details by ID.
    
    **Parameters:**
    - **experiment_id**: The experiment ID to retrieve
    
    **Returns:** Experiment details
    
    **Raises:**
    - 404: Experiment not found
    """
    try:
        logger.debug(f"Retrieving experiment {experiment_id}")
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found")
            raise HTTPException(
                status_code=404, 
                detail=f"Experiment {experiment_id} not found"
            )
        
        logger.debug(f"Successfully retrieved experiment {experiment_id}")
        return experiment
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving experiment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving experiment"
        )


@router.get("/{experiment_id}/status")
def experiment_status(experiment_id: int, db: Session = Depends(get_db)):
    """
    🎯 Quick experiment status - See everything at a glance!
    Perfect for monitoring your experiment without diving into detailed results.
    
    **Returns:** Quick snapshot of experiment progress
    - How many users assigned
    - Event counts (impressions, clicks, conversions)
    - Quick performance summary
    - Next recommended action
    
    **Example Response:**
    ```json
    {
        "experiment_id": 1,
        "experiment_name": "homepage_test",
        "status": "in_progress",
        "progress": {
            "total_users": 150,
            "ready_for_analysis": true,
            "estimated_completion": "2 more days"
        },
        "events_summary": {
            "total_events": 450,
            "impressions": 300,
            "clicks": 150,
            "conversions": 20
        },
        "quick_performance": {
            "control_conversion_rate": "6%",
            "treatment_conversion_rate": "8%",
            "predicted_winner": "treatment"
        },
        "recommendation": "Good progress! Keep running until is_significant=true"
    }
    ```
    """
    try:
        logger.debug(f"Checking status of experiment {experiment_id}")
        
        # Get experiment
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found for status check")
            raise HTTPException(
                status_code=404,
                detail=f"Experiment {experiment_id} not found"
            )
        
        # Get event counts
        total_events = db.query(Event).filter(
            Event.experiment_id == experiment_id
        ).count()
        
        impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.event_type == "impression"
        ).count()
        
        clicks = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.event_type == "click"
        ).count()
        
        conversions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.event_type == "conversion"
        ).count()
        
        # Calculate quick metrics
        control_impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "control",
            Event.event_type == "impression"
        ).count()
        
        treatment_impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "treatment",
            Event.event_type == "impression"
        ).count()
        
        control_conversions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "control",
            Event.event_type == "conversion"
        ).count()
        
        treatment_conversions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "treatment",
            Event.event_type == "conversion"
        ).count()
        
        # Calculate rates
        control_cr = (control_conversions / control_impressions * 100) if control_impressions > 0 else 0
        treatment_cr = (treatment_conversions / treatment_impressions * 100) if treatment_impressions > 0 else 0
        
        # Determine if ready
        total_impressions = control_impressions + treatment_impressions
        ready_for_analysis = total_impressions >= 100
        
        # Predict winner
        if control_cr > treatment_cr:
            predicted_winner = "control 🎯"
        elif treatment_cr > control_cr:
            predicted_winner = "treatment 🎯"
        else:
            predicted_winner = "tie"
        
        # Recommendation
        if not ready_for_analysis:
            recommendation = f"Keep collecting data ({total_impressions}/100 impressions)"
        elif control_cr == treatment_cr:
            recommendation = "Results are identical - try a different variant!"
        else:
            recommendation = "Good progress! Check /results for full analysis"
        
        return {
            "title": "🎯 Experiment Status",
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "status": "in_progress ⏳",
            "progress": {
                "total_users_assigned": max(control_impressions, treatment_impressions),
                "data_collection_status": "🟢 Collecting" if total_impressions < 1000 else "🟡 Almost ready" if total_impressions < 5000 else "🟢 Complete",
                "ready_for_analysis": ready_for_analysis,
                "estimated_completion": "Soon ⏱️" if total_impressions >= 100 else f"Need {100 - total_impressions} more impressions"
            },
            "events_summary": {
                "total_events": total_events,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "breakdown": {
                    "control_impressions": control_impressions,
                    "treatment_impressions": treatment_impressions
                }
            },
            "quick_performance": {
                "control_conversion_rate": f"{control_cr:.1f}%",
                "treatment_conversion_rate": f"{treatment_cr:.1f}%",
                "predicted_winner": predicted_winner,
                "difference": f"{abs(treatment_cr - control_cr):+.1f}%"
            },
            "next_action": recommendation,
            "helpful_links": {
                "view_full_results": f"/results?experiment_id={experiment_id}",
                "view_api_guide": "/api-guide"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error getting experiment status"
        )
