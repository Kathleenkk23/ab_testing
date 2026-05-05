"""User assignment endpoint with ML-based variant selection"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
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
    creative: Optional[dict] = Field(None, description="Creative asset assigned to this variant (if any)")
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
        try:
            variant, assignment_reason = AssignmentService.assign_user(user_id, experiment_id, db)
        except ValueError as e:
            error_msg = str(e)
            if "paused" in error_msg:
                logger.warning(f"Assignment blocked: {error_msg}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot assign users: {error_msg}. Use PUT /experiment/{experiment_id}/resume to resume the experiment."
                )
            elif "completed" in error_msg:
                logger.warning(f"Assignment blocked: {error_msg}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot assign users: {error_msg}. Create a new experiment instead."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )
        
        logger.info(f"User {user_id} assigned to variant: {variant}")
        
        # Get creative for this variant (if assigned)
        creative = None
        try:
            from app.services.creative import CreativeService
            creative = CreativeService.get_creative_for_variant(experiment_id, variant, db)
        except Exception as e:
            logger.warning(f"Could not retrieve creative for experiment {experiment_id}, variant {variant}: {str(e)}")
        
        # Generate helpful next steps
        next_steps = f"Log events for this user: POST /event with user_id={user_id}, experiment_id={experiment_id}, variant='{variant}'"
        if creative:
            next_steps += f". Serve creative '{creative['name']}' to the user."
        
        return AssignmentResponse(
            user_id=user_id,
            experiment_id=experiment_id,
            variant=variant,
            assignment_reason=assignment_reason,
            creative=creative,
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
