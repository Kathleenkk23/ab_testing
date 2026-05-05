"""Creative management endpoints for A/B testing assets"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.database import get_db
from app.services.creative import CreativeService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/creative", tags=["creative"])


class CreativeCreate(BaseModel):
    """Request model for creating a creative"""
    name: str = Field(..., min_length=1, max_length=255, description="Creative name")
    description: str = Field(..., description="Creative description")
    creative_type: str = Field(..., description="Type: 'image', 'copy', 'video', 'design', 'html'")
    content: str = Field(..., description="Creative content (URL, HTML, text, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as key-value pairs")


class CreativeResponse(BaseModel):
    """Response model for creative"""
    id: int
    name: str
    description: str
    creative_type: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


class CreativeAssignment(BaseModel):
    """Request model for assigning creative to variant"""
    experiment_id: int = Field(..., description="Experiment ID")
    variant: str = Field(..., description="Variant: 'control' or 'treatment'")
    creative_id: int = Field(..., description="Creative ID to assign")


class ExperimentCreativesResponse(BaseModel):
    """Response showing creatives for both variants"""
    experiment_id: int
    control: Optional[Dict[str, Any]]
    treatment: Optional[Dict[str, Any]]


@router.post("/", response_model=CreativeResponse)
def create_creative(creative: CreativeCreate, db: Session = Depends(get_db)):
    """
    🎨 Create a new creative asset for A/B testing.

    **Creative Types:**
    - `image`: Image URLs or base64 data
    - `copy`: Text content, headlines, descriptions
    - `video`: Video URLs or embed codes
    - `design`: CSS, design specifications
    - `html`: Complete HTML snippets

    **Examples:**
    ```json
    {
        "name": "Hero Banner Image A",
        "description": "Blue background with white text",
        "creative_type": "image",
        "content": "https://example.com/banner-a.jpg",
        "metadata": {"alt_text": "Welcome to our site", "dimensions": "1200x400"}
    }
    ```

    ```json
    {
        "name": "Call-to-Action Button",
        "description": "Green button with white text",
        "creative_type": "html",
        "content": "<button class='cta-btn green'>Sign Up Now!</button>",
        "metadata": {"color": "#00ff00", "size": "large"}
    }
    ```
    """
    try:
        db_creative = CreativeService.create_creative(
            name=creative.name,
            description=creative.description,
            creative_type=creative.creative_type,
            content=creative.content,
            creative_metadata=creative.metadata,
            db=db
        )

        return CreativeResponse(
            id=db_creative.id,
            name=db_creative.name,
            description=db_creative.description,
            creative_type=db_creative.creative_type,
            content=db_creative.content,
            metadata=creative.metadata,
            created_at=db_creative.created_at
        )

    except Exception as e:
        logger.error(f"Error creating creative: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create creative: {str(e)}")


@router.get("/", response_model=List[CreativeResponse])
def list_creatives(creative_type: Optional[str] = None, db: Session = Depends(get_db)):
    """
    📚 List all creative assets.

    **Optional Filter:**
    - `creative_type`: Filter by type ('image', 'copy', 'video', 'design', 'html')
    """
    try:
        creatives = CreativeService.list_creatives(db, creative_type)
        return [
            CreativeResponse(
                id=c["id"],
                name=c["name"],
                description=c["description"],
                creative_type=c["type"],
                content=c["content"],
                metadata=c["metadata"],
                created_at=c["created_at"]
            )
            for c in creatives
        ]
    except Exception as e:
        logger.error(f"Error listing creatives: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list creatives: {str(e)}")


@router.post("/assign")
def assign_creative_to_variant(assignment: CreativeAssignment, db: Session = Depends(get_db)):
    """
    🔗 Assign a creative to an experiment variant.

    **Example:**
    ```json
    {
        "experiment_id": 1,
        "variant": "treatment",
        "creative_id": 5
    }
    ```

    **Use Cases:**
    - Assign different images to control/treatment variants
    - Test different copy variations
    - Compare design alternatives
    """
    try:
        db_assignment = CreativeService.assign_creative_to_variant(
            experiment_id=assignment.experiment_id,
            variant=assignment.variant,
            creative_id=assignment.creative_id,
            db=db
        )

        return {
            "message": f"✅ Creative {assignment.creative_id} assigned to experiment {assignment.experiment_id} variant '{assignment.variant}'",
            "assignment_id": db_assignment.id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning creative: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign creative: {str(e)}")


@router.get("/experiment/{experiment_id}")
def get_experiment_creatives(experiment_id: int, db: Session = Depends(get_db)):
    """
    🎯 Get creatives assigned to an experiment's variants.

    **Returns:** Creative details for both control and treatment variants
    """
    try:
        creatives = CreativeService.get_experiment_creatives(experiment_id, db)

        return ExperimentCreativesResponse(
            experiment_id=experiment_id,
            control=creatives["control"],
            treatment=creatives["treatment"]
        )

    except Exception as e:
        logger.error(f"Error getting experiment creatives: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get experiment creatives: {str(e)}")


@router.get("/{creative_id}/usage")
def get_creative_usage(creative_id: int, db: Session = Depends(get_db)):
    """
    📊 Get usage statistics for a creative asset.

    **Shows:**
    - Which experiments use this creative
    - Which variants it's assigned to
    - Total events tracked for this creative
    """
    try:
        usage = CreativeService.get_creative_usage(creative_id, db)
        return usage

    except Exception as e:
        logger.error(f"Error getting creative usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get creative usage: {str(e)}")


@router.get("/variant/{experiment_id}/{variant}")
def get_variant_creative(experiment_id: int, variant: str, db: Session = Depends(get_db)):
    """
    🎨 Get the creative assigned to a specific experiment variant.

    **Use this endpoint in your application** to serve the correct creative
    to users based on their experiment assignment.

    **Example Response:**
    ```json
    {
        "creative_id": 5,
        "name": "Hero Banner Image A",
        "description": "Blue background with white text",
        "type": "image",
        "content": "https://example.com/banner-a.jpg",
        "metadata": {"alt_text": "Welcome to our site"}
    }
    ```
    """
    try:
        creative = CreativeService.get_creative_for_variant(experiment_id, variant, db)

        if not creative:
            return {"message": f"No creative assigned to experiment {experiment_id} variant '{variant}'"}

        return creative

    except Exception as e:
        logger.error(f"Error getting variant creative: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get variant creative: {str(e)}")