"""Metrics calculation for A/B testing"""
from sqlalchemy.orm import Session
from app.models import Event
from app.services.stats import StatisticalTest


class MetricsCalculator:
    """Calculate metrics for experiment results"""

    @staticmethod
    def get_experiment_metrics(experiment_id: int, db: Session):
        """
        Calculate aggregated metrics for both variants with statistical significance.
        
        Returns:
            {
                'control': {'impressions': int, 'clicks': int, 'conversions': int, 'ctr': float, 'conversion_rate': float},
                'treatment': {...},
                'control_conversion_rate': float,
                'treatment_conversion_rate': float,
                'uplift': float,
                'z_score': float,
                'p_value': float,
                'is_significant': bool
            }
        """
        metrics = {}
        
        for variant in ["control", "treatment"]:
            events = db.query(Event).filter(
                Event.experiment_id == experiment_id,
                Event.variant == variant
            ).all()
            
            impressions = sum(1 for e in events if e.event_type == "impression")
            clicks = sum(1 for e in events if e.event_type == "click")
            conversions = sum(1 for e in events if e.event_type == "conversion")
            
            # Calculate rates
            ctr = clicks / impressions if impressions > 0 else 0.0
            conversion_rate = conversions / impressions if impressions > 0 else 0.0
            
            metrics[variant] = {
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "ctr": round(ctr, 4),
                "conversion_rate": round(conversion_rate, 4)
            }
        
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
