"""Event logging endpoint with validation and monitoring"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from app.database import get_db
from app.models import Event, Experiment

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/event", tags=["event"])

# Valid event types and variants
VALID_EVENT_TYPES = {"impression", "click", "conversion"}
VALID_VARIANTS = {"control", "treatment"}


class EventCreate(BaseModel):
    """Request model for logging an event"""
    user_id: int = Field(..., gt=0, description="User ID (must be > 0)")
    experiment_id: int = Field(..., gt=0, description="Experiment ID (must be > 0)")
    variant: str = Field(..., description="Variant name (control or treatment)")
    event_type: str = Field(..., description="Event type (impression, click, or conversion)")
    
    @validator('variant')
    def validate_variant(cls, v):
        if v not in VALID_VARIANTS:
            raise ValueError(f"Variant must be one of {VALID_VARIANTS}")
        return v
    
    @validator('event_type')
    def validate_event_type(cls, v):
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Event type must be one of {VALID_EVENT_TYPES}")
        return v


class EventResponse(BaseModel):
    """Response model for event"""
    id: int
    user_id: int
    experiment_id: int
    variant: str
    event_type: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=EventResponse)
def log_event(event: EventCreate, db: Session = Depends(get_db)):
    """
    Log a user event (impression, click, or conversion).
    
    **Event Types:**
    - `impression`: User saw the experiment variant
    - `click`: User clicked on the variant element
    - `conversion`: User completed the desired action
    
    **Variants:**
    - `control`: Control group
    - `treatment`: Treatment group
    
    **Payload:**
    ```json
    {
        "user_id": 123,
        "experiment_id": 1,
        "variant": "control",
        "event_type": "click"
    }
    ```
    
    **Raises:**
    - 404: Experiment not found
    - 422: Invalid event type or variant
    """
    try:
        # Validate experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == event.experiment_id
        ).first()
        
        if not experiment:
            logger.warning(f"Event logging failed: Experiment {event.experiment_id} not found")
            raise HTTPException(
                status_code=404, 
                detail=f"Experiment {event.experiment_id} not found"
            )
        
        # Log event creation
        logger.info(f"Logging event: user {event.user_id}, experiment {event.experiment_id}, "
                   f"variant {event.variant}, type {event.event_type}")
        
        # Create and store event
        db_event = Event(
            user_id=event.user_id,
            experiment_id=event.experiment_id,
            variant=event.variant,
            event_type=event.event_type
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Event logged successfully: ID {db_event.id}")
        return db_event
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during event logging: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during event logging"
        )
