"""Event logging endpoint"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Event, Experiment

router = APIRouter(prefix="/event", tags=["event"])


class EventCreate(BaseModel):
    """Request model for logging an event"""
    user_id: int
    experiment_id: int
    variant: str
    event_type: str


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
    
    **Payload:**
    ```json
    {
        "user_id": 123,
        "experiment_id": 1,
        "variant": "control",
        "event_type": "click"
    }
    ```
    """
    # Validate experiment exists
    experiment = db.query(Experiment).filter(
        Experiment.id == event.experiment_id
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Validate variant
    if event.variant not in ["control", "treatment"]:
        raise HTTPException(
            status_code=400,
            detail="Variant must be 'control' or 'treatment'"
        )
    
    # Validate event type
    if event.event_type not in ["impression", "click", "conversion"]:
        raise HTTPException(
            status_code=400,
            detail="Event type must be 'impression', 'click', or 'conversion'"
        )
    
    # Create event
    db_event = Event(
        user_id=event.user_id,
        experiment_id=event.experiment_id,
        variant=event.variant,
        event_type=event.event_type
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event
