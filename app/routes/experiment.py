"""Experiment creation and management endpoints with logging"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from app.database import get_db
from app.models import Experiment

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
