"""Experiment templates for quick experiment setup"""
import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExperimentTemplate(BaseModel):
    """Template for creating pre-configured experiments"""
    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Template category")
    use_case: str = Field(..., description="Primary use case")
    estimated_duration: str = Field(..., description="Expected experiment duration")
    sample_size_guidance: str = Field(..., description="Sample size recommendations")
    success_metrics: List[str] = Field(..., description="Key metrics to track")
    configuration: Dict[str, Any] = Field(..., description="Default configuration")


class ExperimentTemplateService:
    """Service for managing experiment templates"""

    TEMPLATES = {
        "homepage_button_color": {
            "id": "homepage_button_color",
            "name": "Homepage Button Color Test",
            "description": "Test different button colors to optimize click-through rates",
            "category": "UI/UX",
            "use_case": "Increase conversion rates on primary call-to-action buttons",
            "estimated_duration": "1-2 weeks",
            "sample_size_guidance": "10,000+ visitors per variant for statistical significance",
            "success_metrics": ["click_through_rate", "conversion_rate", "bounce_rate"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current button color (usually blue)",
                "treatment_description": "Alternative color (green, red, orange, etc.)",
                "events_to_track": ["impression", "click", "conversion"],
                "minimum_sample_size": 10000
            }
        },

        "pricing_page_layout": {
            "id": "pricing_page_layout",
            "name": "Pricing Page Layout Test",
            "description": "Compare different pricing page layouts and information hierarchy",
            "category": "Conversion",
            "use_case": "Optimize pricing page to increase subscription signups",
            "estimated_duration": "2-3 weeks",
            "sample_size_guidance": "5,000+ visitors per variant",
            "success_metrics": ["conversion_rate", "time_on_page", "scroll_depth"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current pricing layout",
                "treatment_description": "Alternative layout (table vs cards, feature highlights, etc.)",
                "events_to_track": ["impression", "click", "conversion"],
                "minimum_sample_size": 5000
            }
        },

        "email_subject_line": {
            "id": "email_subject_line",
            "name": "Email Subject Line Test",
            "description": "Test different email subject lines to improve open rates",
            "category": "Email Marketing",
            "use_case": "Increase email open rates and engagement",
            "estimated_duration": "1 week",
            "sample_size_guidance": "1,000+ email recipients per variant",
            "success_metrics": ["open_rate", "click_rate", "conversion_rate"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current subject line",
                "treatment_description": "Alternative subject line",
                "events_to_track": ["sent", "opened", "clicked", "converted"],
                "minimum_sample_size": 1000
            }
        },

        "product_recommendation": {
            "id": "product_recommendation",
            "name": "Product Recommendation Algorithm",
            "description": "Test different recommendation algorithms on product pages",
            "category": "Personalization",
            "use_case": "Improve cross-sell and up-sell through better recommendations",
            "estimated_duration": "3-4 weeks",
            "sample_size_guidance": "2,000+ product page views per variant",
            "success_metrics": ["click_through_rate", "add_to_cart_rate", "conversion_rate"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current recommendation algorithm",
                "treatment_description": "Alternative algorithm (collaborative filtering, content-based, etc.)",
                "events_to_track": ["impression", "click", "add_to_cart", "purchase"],
                "minimum_sample_size": 2000
            }
        },

        "checkout_flow": {
            "id": "checkout_flow",
            "name": "Checkout Flow Optimization",
            "description": "Test different checkout processes to reduce cart abandonment",
            "category": "E-commerce",
            "use_case": "Reduce checkout abandonment and increase completed purchases",
            "estimated_duration": "2-4 weeks",
            "sample_size_guidance": "1,000+ checkout starts per variant",
            "success_metrics": ["completion_rate", "abandonment_rate", "average_order_value"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current checkout flow",
                "treatment_description": "Simplified or multi-step checkout",
                "events_to_track": ["checkout_start", "step_completion", "abandonment", "purchase"],
                "minimum_sample_size": 1000
            }
        },

        "search_results": {
            "id": "search_results",
            "name": "Search Results Page Test",
            "description": "Test different search result layouts and ranking algorithms",
            "category": "Search",
            "use_case": "Improve search experience and conversion from search results",
            "estimated_duration": "2-3 weeks",
            "sample_size_guidance": "5,000+ search queries per variant",
            "success_metrics": ["click_through_rate", "conversion_rate", "search_satisfaction"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current search results layout",
                "treatment_description": "Alternative layout (grid vs list, filters, etc.)",
                "events_to_track": ["search", "result_click", "conversion"],
                "minimum_sample_size": 5000
            }
        },

        "onboarding_flow": {
            "id": "onboarding_flow",
            "name": "User Onboarding Flow Test",
            "description": "Test different user onboarding experiences for new users",
            "category": "User Experience",
            "use_case": "Improve user activation and retention through better onboarding",
            "estimated_duration": "3-4 weeks",
            "sample_size_guidance": "500+ new users per variant",
            "success_metrics": ["activation_rate", "retention_rate", "feature_adoption"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current onboarding flow",
                "treatment_description": "Alternative onboarding (guided tour, progressive disclosure, etc.)",
                "events_to_track": ["signup", "onboarding_start", "onboarding_complete", "feature_usage"],
                "minimum_sample_size": 500
            }
        },

        "notification_timing": {
            "id": "notification_timing",
            "name": "Push Notification Timing Test",
            "description": "Test different timing strategies for push notifications",
            "category": "Mobile",
            "use_case": "Optimize notification timing to improve engagement",
            "estimated_duration": "1-2 weeks",
            "sample_size_guidance": "1,000+ users per variant",
            "success_metrics": ["open_rate", "engagement_rate", "opt_out_rate"],
            "configuration": {
                "variants": ["control", "treatment"],
                "control_description": "Current notification timing",
                "treatment_description": "Alternative timing (immediate, batched, scheduled)",
                "events_to_track": ["notification_sent", "notification_opened", "engagement"],
                "minimum_sample_size": 1000
            }
        }
    }

    @staticmethod
    def get_all_templates() -> List[ExperimentTemplate]:
        """Get all available experiment templates"""
        return [ExperimentTemplate(**template) for template in ExperimentTemplateService.TEMPLATES.values()]

    @staticmethod
    def get_template(template_id: str) -> ExperimentTemplate:
        """Get a specific template by ID"""
        if template_id not in ExperimentTemplateService.TEMPLATES:
            raise ValueError(f"Template '{template_id}' not found")
        return ExperimentTemplate(**ExperimentTemplateService.TEMPLATES[template_id])

    @staticmethod
    def get_templates_by_category(category: str) -> List[ExperimentTemplate]:
        """Get templates filtered by category"""
        return [
            ExperimentTemplate(**template)
            for template in ExperimentTemplateService.TEMPLATES.values()
            if template["category"].lower() == category.lower()
        ]

    @staticmethod
    def create_experiment_from_template(template_id: str, custom_name: str = None) -> Dict[str, Any]:
        """Generate experiment creation data from a template"""
        template = ExperimentTemplateService.get_template(template_id)

        experiment_name = custom_name or f"{template.name} - {template.id}"

        return {
            "template_id": template_id,
            "experiment_name": experiment_name,
            "description": template.description,
            "configuration": template.configuration,
            "recommended_metrics": template.success_metrics,
            "estimated_sample_size": template.configuration.get("minimum_sample_size", 1000)
        }