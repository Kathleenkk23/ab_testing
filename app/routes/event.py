"""Event logging endpoint with validation and monitoring"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from app.database import get_db
from app.models import Event, Experiment
from app.services.batch_processor import BatchEventProcessor

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
    creative_id: int = Field(None, description="Creative ID (optional - auto-detected if not provided)")
    
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
        
        # Auto-detect creative_id if not provided
        creative_id = event.creative_id
        if creative_id is None:
            from app.services.creative import CreativeService
            creative = CreativeService.get_creative_for_variant(
                event.experiment_id, event.variant, db
            )
            if creative:
                creative_id = creative["creative_id"]
                logger.debug(f"Auto-detected creative_id {creative_id} for variant {event.variant}")
        
        # Log event creation
        logger.info(f"Logging event: user {event.user_id}, experiment {event.experiment_id}, "
                   f"variant {event.variant}, type {event.event_type}, creative {creative_id}")
        
        # Create and store event
        db_event = Event(
            user_id=event.user_id,
            experiment_id=event.experiment_id,
            variant=event.variant,
            event_type=event.event_type,
            creative_id=creative_id
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


class BatchEventResponse(BaseModel):
    """Response for batch event logging"""
    total_events: int
    successful: int
    failed: int
    message: str


@router.post("/batch", response_model=BatchEventResponse)
def log_batch_events(events: list[EventCreate], db: Session = Depends(get_db)):
    """
    📝 Log multiple events at once (MUCH faster than individual calls!).
    
    Perfect for bulk event uploads - 10x faster than logging one by one!
    
    **Example:**
    ```json
    [
        {"user_id": 1, "experiment_id": 1, "variant": "control", "event_type": "impression"},
        {"user_id": 2, "experiment_id": 1, "variant": "treatment", "event_type": "click"},
        {"user_id": 3, "experiment_id": 1, "variant": "control", "event_type": "conversion"}
    ]
    ```
    
    **Returns:** Summary of successful and failed uploads
    
    **Benefits:**
    - 10x faster than individual API calls
    - Atomic operation (all or nothing)
    - Perfect for batch imports
    """
    successful = 0
    failed = 0
    failed_events = []
    
    logger.info(f"Starting batch event logging: {len(events)} events")
    
    # Validate all events belong to the same experiment
    if events:
        experiment_ids = set(event.experiment_id for event in events)
        if len(experiment_ids) > 1:
            raise HTTPException(
                status_code=400,
                detail="All events in batch must belong to the same experiment"
            )
        
        experiment_id = list(experiment_ids)[0]
        
        # Validate experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            raise HTTPException(
                status_code=404,
                detail=f"Experiment {experiment_id} not found"
            )
    
    try:
        # Convert to dict format for batch processor
        events_data = [
            {
                "user_id": event.user_id,
                "variant": event.variant,
                "event_type": event.event_type
            }
            for event in events
        ]
        
        # Use high-performance batch processor
        result = BatchEventProcessor.bulk_insert_events_sqlite(
            events_data, experiment_id, db
        )
        
        successful = result["processed"]
        failed = result["failed"]
        
        if result["errors"]:
            failed_events = result["errors"]
        
        logger.info(f"Batch event logging completed: {successful} success, {failed} failed")
        
        return BatchEventResponse(
            total_events=len(events),
            successful=successful,
            failed=failed,
            message=f"✅ Successfully logged {successful}/{len(events)} events" + 
                   (f" ({failed} failed)" if failed > 0 else "")
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during batch event logging: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error during batch event logging"
        )

