"""Results and metrics endpoint"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Experiment
from app.services.metrics import MetricsCalculator

router = APIRouter(prefix="/results", tags=["results"])


class VariantMetrics(BaseModel):
    """Metrics for a single variant"""
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float


class ResultsResponse(BaseModel):
    """Response model for experiment results with statistical significance"""
    experiment_id: int
    experiment_name: str
    control: VariantMetrics
    treatment: VariantMetrics
    control_conversion_rate: float
    treatment_conversion_rate: float
    uplift: float
    z_score: float
    p_value: float
    is_significant: bool
    alpha: float


@router.get("/", response_model=ResultsResponse)
def get_results(
    experiment_id: int = Query(..., description="Experiment identifier"),
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregated A/B testing results for an experiment with statistical significance.
    
    **Metrics Per Variant:**
    - `impressions`: Total times variant was shown
    - `clicks`: Total clicks on variant
    - `conversions`: Total conversions for variant
    - `ctr`: Click-through rate (clicks / impressions)
    - `conversion_rate`: Conversion rate (conversions / impressions)
    
    **Statistical Analysis:**
    - `control_conversion_rate`: Control variant conversion rate
    - `treatment_conversion_rate`: Treatment variant conversion rate
    - `uplift`: Relative improvement (treatment - control)
    - `z_score`: Z-statistic from two-proportion z-test
    - `p_value`: Two-tailed p-value (significance of difference)
    - `is_significant`: Whether result is statistically significant (p < 0.05)
    
    **Interpretation:**
    - If `is_significant` is true, the difference is unlikely due to chance
    - A `z_score` of ±1.96 or higher indicates p < 0.05
    - `p_value` < 0.05 means 95% confidence in the result
    
    Returns detailed metrics for both 'control' and 'treatment' variants.
    """
    # Verify experiment exists
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Calculate metrics
    metrics = MetricsCalculator.get_experiment_metrics(experiment_id, db)
    
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment.name,
        "control": metrics["control"],
        "treatment": metrics["treatment"],
        "control_conversion_rate": metrics["control_conversion_rate"],
        "treatment_conversion_rate": metrics["treatment_conversion_rate"],
        "uplift": metrics["uplift"],
        "z_score": metrics["z_score"],
        "p_value": metrics["p_value"],
        "is_significant": metrics["is_significant"],
        "alpha": metrics["alpha"]
    }
