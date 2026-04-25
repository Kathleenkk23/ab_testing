"""Experiment creation and management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Experiment

router = APIRouter(prefix="/experiment", tags=["experiment"])


class ExperimentCreate(BaseModel):
    """Request model for creating an experiment"""
    name: str


class ExperimentResponse(BaseModel):
    """Response model for experiment"""
    id: int
    name: str
    status: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """
    Create a new A/B testing experiment.
    
    - **name**: Unique experiment name (e.g., "homepage_banner_v1")
    
    Returns the created experiment with ID.
    """
    # Check if experiment already exists
    existing = db.query(Experiment).filter(
        Experiment.name == experiment.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Experiment '{experiment.name}' already exists"
        )
    
    # Create new experiment
    db_experiment = Experiment(name=experiment.name)
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    
    return db_experiment


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Retrieve experiment details by ID."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return experiment
