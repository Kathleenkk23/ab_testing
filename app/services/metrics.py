"""Metrics calculation for A/B testing with logging"""
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models import Event
from app.services.stats import StatisticalTest

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculate metrics for experiment results with proper logging and error handling"""

    @staticmethod
    def get_experiment_metrics(experiment_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculate aggregated metrics for both variants with statistical significance.
        
        Metrics calculated:
        - impressions: Number of times variant was shown
        - clicks: Number of clicks on variant
        - conversions: Number of conversions for variant
        - ctr: Click-through rate (clicks / impressions)
        - conversion_rate: Conversion rate (conversions / impressions)
        - z_score: Z-statistic from two-proportion z-test
        - p_value: P-value from statistical test
        - is_significant: Whether difference is statistically significant (p < 0.05)
        - uplift: Relative improvement (treatment - control)
        
        Args:
            experiment_id: The ID of the experiment
            db: Database session
            
        Returns:
            Dictionary containing metrics for both variants and statistical results
        """
        logger.debug(f"Calculating metrics for experiment {experiment_id}")
        metrics = {}
        
        for variant in ["control", "treatment"]:
            events = db.query(Event).filter(
                Event.experiment_id == experiment_id,
                Event.variant == variant
            ).all()
            
            impressions = sum(1 for e in events if e.event_type == "impression")
            clicks = sum(1 for e in events if e.event_type == "click")
            conversions = sum(1 for e in events if e.event_type == "conversion")
            
            # Calculate rates with safe division
            ctr = clicks / impressions if impressions > 0 else 0.0
            conversion_rate = conversions / impressions if impressions > 0 else 0.0
            
            metrics[variant] = {
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "ctr": round(ctr, 4),
                "conversion_rate": round(conversion_rate, 4)
            }
            
            logger.debug(f"Variant {variant}: {impressions} impressions, "
                        f"{conversions} conversions, {conversion_rate:.2%} conversion rate")
        
        # Calculate statistical significance
        control_conversions = metrics["control"]["conversions"]
        control_impressions = metrics["control"]["impressions"]
        treatment_conversions = metrics["treatment"]["conversions"]
        treatment_impressions = metrics["treatment"]["impressions"]
        
        significance_result = StatisticalTest.two_proportion_z_test(
            control_conversions, control_impressions,
            treatment_conversions, treatment_impressions,
            alpha=0.05
        )
        
        # Add statistical results to metrics dict
        metrics.update(significance_result)
        
        return metrics

    @staticmethod
    def get_variant_conversion_rate(experiment_id: int, variant: str, db: Session) -> float:
        """Get conversion rate for a specific variant"""
        events = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == variant
        ).all()
        
        impressions = sum(1 for e in events if e.event_type == "impression")
        conversions = sum(1 for e in events if e.event_type == "conversion")
        
        return conversions / impressions if impressions > 0 else 0.0
