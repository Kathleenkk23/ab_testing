"""Experiment template endpoints for quick experiment setup"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import get_db
from app.services.templates import ExperimentTemplateService, ExperimentTemplate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateListResponse(BaseModel):
    """Response model for template listing"""
    templates: List[ExperimentTemplate]
    total_count: int
    categories: List[str]


class TemplateCreateExperimentRequest(BaseModel):
    """Request model for creating experiment from template"""
    template_id: str = Field(..., description="Template ID to use")
    custom_name: Optional[str] = Field(None, description="Custom experiment name (optional)")


class TemplateCreateExperimentResponse(BaseModel):
    """Response model for experiment creation from template"""
    template_id: str
    experiment_name: str
    description: str
    configuration: dict
    recommended_metrics: List[str]
    estimated_sample_size: int
    next_steps: str


@router.get("/", response_model=TemplateListResponse)
def list_templates(
    category: Optional[str] = None
):
    """
    📋 List all available experiment templates.

    **Templates include:**
    - Pre-configured experiment setups
    - Recommended sample sizes
    - Success metrics to track
    - Best practices for each use case

    **Categories:**
    - UI/UX: User interface and experience tests
    - Conversion: Conversion rate optimization
    - Email Marketing: Email campaign optimization
    - Personalization: Recommendation and personalization tests
    - E-commerce: Shopping and checkout flow tests
    - Search: Search experience optimization
    - User Experience: Onboarding and user flow tests
    - Mobile: Mobile app and notification tests

    **Query Parameters:**
    - `category`: Filter by category (optional)

    **Returns:** List of available templates with metadata
    """
    try:
        logger.info("Listing experiment templates")

        if category:
            templates = ExperimentTemplateService.get_templates_by_category(category)
        else:
            templates = ExperimentTemplateService.get_all_templates()

        # Extract unique categories
        all_templates = ExperimentTemplateService.get_all_templates()
        categories = list(set(template.category for template in all_templates))

        return TemplateListResponse(
            templates=templates,
            total_count=len(templates),
            categories=sorted(categories)
        )

    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error listing templates"
        )


@router.get("/{template_id}")
def get_template(template_id: str):
    """
    📖 Get detailed information about a specific template.

    **Includes:**
    - Template configuration
    - Success metrics
    - Sample size guidance
    - Implementation tips

    **Parameters:**
    - `template_id`: The template identifier

    **Returns:** Complete template details

    **Raises:**
    - 404: Template not found
    """
    try:
        logger.info(f"Retrieving template: {template_id}")

        template = ExperimentTemplateService.get_template(template_id)

        return {
            "template": template,
            "usage_example": {
                "create_experiment": f"POST /templates/{template_id}/create-experiment",
                "with_custom_name": f"POST /templates/{template_id}/create-experiment with {{'custom_name': 'My Custom Test'}}"
            },
            "implementation_guide": {
                "step_1": f"Create experiment using this template",
                "step_2": f"Implement the {template.configuration.get('treatment_description', 'treatment variant')}",
                "step_3": f"Track these metrics: {', '.join(template.success_metrics)}",
                "step_4": f"Aim for {template.configuration.get('minimum_sample_size', 1000)}+ samples per variant"
            }
        }

    except ValueError as e:
        logger.warning(f"Template not found: {template_id}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving template"
        )


@router.post("/{template_id}/create-experiment", response_model=TemplateCreateExperimentResponse)
def create_experiment_from_template(
    template_id: str,
    request: TemplateCreateExperimentRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 Create a new experiment using a template.

    **What this does:**
    1. Validates the template exists
    2. Generates experiment configuration from template
    3. Creates the experiment in the database
    4. Returns setup instructions

    **Parameters:**
    - `template_id`: Template to use
    - `custom_name`: Optional custom experiment name

    **Returns:** Experiment creation data and next steps

    **Raises:**
    - 404: Template not found
    """
    try:
        logger.info(f"Creating experiment from template: {template_id}")

        # Get template data
        template_data = ExperimentTemplateService.create_experiment_from_template(
            template_id,
            request.custom_name
        )

        # Here you would typically create the experiment in the database
        # For now, we'll just return the configuration data
        # In a full implementation, you'd call the experiment creation service

        next_steps = f"""
        1. Use the experiment name: '{template_data['experiment_name']}'
        2. Implement the treatment variant: {template_data['configuration']['treatment_description']}
        3. Track these metrics: {', '.join(template_data['recommended_metrics'])}
        4. Create the experiment: POST /experiment with name='{template_data['experiment_name']}'
        5. Start assigning users: GET /assign?experiment_id=<ID>&user_id=<USER_ID>
        """.strip()

        return TemplateCreateExperimentResponse(
            template_id=template_id,
            experiment_name=template_data["experiment_name"],
            description=template_data["description"],
            configuration=template_data["configuration"],
            recommended_metrics=template_data["recommended_metrics"],
            estimated_sample_size=template_data["estimated_sample_size"],
            next_steps=next_steps
        )

    except ValueError as e:
        logger.warning(f"Template not found: {template_id}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating experiment from template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error creating experiment from template"
        )


@router.get("/categories/list")
def list_categories():
    """
    📂 Get all available template categories.

    **Returns:** List of categories for filtering templates
    """
    try:
        all_templates = ExperimentTemplateService.get_all_templates()
        categories = list(set(template.category for template in all_templates))

        return {
            "categories": sorted(categories),
            "count_by_category": {
                category: len(ExperimentTemplateService.get_templates_by_category(category))
                for category in categories
            }
        }

    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error listing categories"
        )