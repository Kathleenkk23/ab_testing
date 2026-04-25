"""User assignment endpoint with ML-based variant selection"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Experiment
from app.services.assignment import AssignmentService

router = APIRouter(prefix="/assign", tags=["assignment"])


class AssignmentResponse(BaseModel):
    """Response model for user assignment"""
    user_id: int
    experiment_id: int
    variant: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=AssignmentResponse)
def assign_user(
    user_id: int = Query(..., description="Unique user identifier"),
    experiment_id: int = Query(..., description="Experiment identifier"),
    db: Session = Depends(get_db)
):
    """
    Assign a user to an experiment variant using epsilon-greedy bandit algorithm.
    
    **Logic:**
    - If user already assigned to this experiment, return existing assignment
    - If < 100 impressions total: assign randomly
    - Else:
      - 10% of time: assign randomly (explore)
      - 90% of time: assign to variant with higher conversion rate (exploit)
    
    Returns the assigned variant ('control' or 'treatment').
    """
    # Verify experiment exists
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Get assignment from service
    variant = AssignmentService.assign_user(user_id, experiment_id, db)
    
    return {
        "user_id": user_id,
        "experiment_id": experiment_id,
        "variant": variant
    }
