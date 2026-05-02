"""User assignment endpoint with ML-based variant selection"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.models import Experiment
from app.services.assignment import AssignmentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assign", tags=["assignment"])


class AssignmentResponse(BaseModel):
    """Response model for user assignment with reasoning and next steps"""
    user_id: int = Field(..., description="User ID")
    experiment_id: int = Field(..., description="Experiment ID")
    variant: str = Field(..., description="Assigned variant (control or treatment)")
    assignment_reason: str = Field(..., description="Why this variant was assigned (exploration vs exploitation)")
    next_steps: str = Field(..., description="Suggested next action")


@router.get("/", response_model=AssignmentResponse)
def assign_user(
    user_id: int = Query(..., gt=0, description="Unique user identifier (must be > 0)"),
    experiment_id: int = Query(..., gt=0, description="Experiment identifier (must be > 0)"),
    db: Session = Depends(get_db)
):
    """
    Assign a user to an experiment variant using epsilon-greedy bandit algorithm.
    
    **Validation:**
    - Both user_id and experiment_id must be positive integers
    
    **Logic:**
    - If user already assigned to this experiment, return existing assignment (idempotent)
    - If < 100 impressions total: assign randomly (exploration phase)
    - Else:
      - 10% of time: assign randomly (continued exploration)
      - 90% of time: assign to variant with higher conversion rate (exploitation phase)
    
    **Returns:** The assigned variant ('control' or 'treatment').
    
    **Raises:**
    - 404: Experiment not found
    - 400: Invalid user or experiment ID
    """
    try:
        # Verify experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            logger.warning(f"Assignment failed: Experiment {experiment_id} not found (user {user_id})")
            raise HTTPException(
                status_code=404, 
                detail=f"Experiment {experiment_id} not found"
            )
        
        # Get assignment from service
        logger.info(f"Assigning user {user_id} to experiment {experiment_id}")
        variant, assignment_reason = AssignmentService.assign_user(user_id, experiment_id, db)
        logger.info(f"User {user_id} assigned to variant: {variant}")
        
        # Generate helpful next steps
        next_steps = f"Log events for this user: POST /event with user_id={user_id}, experiment_id={experiment_id}, variant='{variant}'"
        
        return AssignmentResponse(
            user_id=user_id,
            experiment_id=experiment_id,
            variant=variant,
            assignment_reason=assignment_reason,
            next_steps=next_steps
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during assignment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during assignment"
        )
