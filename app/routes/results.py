"""Results and metrics endpoint with logging and validation"""
import logging
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Experiment, Event, Assignment
from app.services.metrics import MetricsCalculator
from app.services.bayesian_stats import BayesianTest

logger = logging.getLogger(__name__)
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
    experiment_id: int = Query(..., gt=0, description="Experiment identifier (must be > 0)"),
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
    
    **Returns:** Detailed metrics for both 'control' and 'treatment' variants with statistical significance
    
    **Raises:**
    - 404: Experiment not found
    """
    try:
        logger.info(f"Retrieving results for experiment {experiment_id}")
        
        # Verify experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            logger.warning(f"Results retrieval failed: Experiment {experiment_id} not found")
            raise HTTPException(
                status_code=404, 
                detail=f"Experiment {experiment_id} not found"
            )
        
        # Calculate metrics
        logger.debug(f"Calculating metrics for experiment {experiment_id}")
        metrics = MetricsCalculator.get_experiment_metrics(experiment_id, db)
        
        logger.info(f"Results retrieved successfully: control CR={metrics['control_conversion_rate']:.2%}, "
                   f"treatment CR={metrics['treatment_conversion_rate']:.2%}, "
                   f"significant={metrics['is_significant']}")
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving results"
        )


@router.get("/{experiment_id}/export/csv")
def export_results_csv(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """
    📊 Export experiment data as CSV file.
    
    **Includes:**
    - Summary metrics (same as /results endpoint)
    - Raw event data (all impressions, clicks, conversions)
    - User assignments
    
    **Format:** CSV file with multiple sheets (summary + raw data)
    
    **Use cases:**
    - Import into Excel/Google Sheets for analysis
    - Share with stakeholders
    - Backup experiment data
    - Custom analysis in R/Python
    
    **Returns:** CSV file download
    """
    try:
        logger.info(f"Exporting CSV data for experiment {experiment_id}")
        
        # Verify experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            raise HTTPException(
                status_code=404,
                detail=f"Experiment {experiment_id} not found"
            )
        
        # Get metrics
        metrics = MetricsCalculator.get_experiment_metrics(experiment_id, db)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Summary section
        writer.writerow(["EXPERIMENT SUMMARY"])
        writer.writerow(["Experiment ID", experiment_id])
        writer.writerow(["Experiment Name", experiment.name])
        writer.writerow(["Status", experiment.status])
        writer.writerow([])
        
        writer.writerow(["METRICS SUMMARY"])
        writer.writerow(["Metric", "Control", "Treatment"])
        writer.writerow(["Impressions", metrics["control"]["impressions"], metrics["treatment"]["impressions"]])
        writer.writerow(["Clicks", metrics["control"]["clicks"], metrics["treatment"]["clicks"]])
        writer.writerow(["Conversions", metrics["control"]["conversions"], metrics["treatment"]["conversions"]])
        writer.writerow(["CTR", ".1f", ".1f"])
        writer.writerow(["Conversion Rate", ".1f", ".1f"])
        writer.writerow([])
        
        writer.writerow(["STATISTICAL ANALYSIS"])
        writer.writerow(["Control Conversion Rate", ".1f"])
        writer.writerow(["Treatment Conversion Rate", ".1f"])
        writer.writerow(["Uplift", "+.1f"])
        writer.writerow(["Z-Score", ".3f"])
        writer.writerow(["P-Value", ".4f"])
        writer.writerow(["Is Significant", metrics["is_significant"]])
        writer.writerow([])
        
        # Raw events section
        writer.writerow(["RAW EVENT DATA"])
        writer.writerow(["User ID", "Variant", "Event Type", "Timestamp"])
        
        events = db.query(Event).filter(
            Event.experiment_id == experiment_id
        ).order_by(Event.created_at).all()
        
        for event in events:
            writer.writerow([
                event.user_id,
                event.variant,
                event.event_type,
                event.created_at.isoformat()
            ])
        
        writer.writerow([])
        
        # Assignments section
        writer.writerow(["USER ASSIGNMENTS"])
        writer.writerow(["User ID", "Variant", "Assigned At"])
        
        assignments = db.query(Assignment).filter(
            Assignment.experiment_id == experiment_id
        ).order_by(Assignment.assigned_at).all()
        
        for assignment in assignments:
            writer.writerow([
                assignment.user_id,
                assignment.variant,
                assignment.assigned_at.isoformat()
            ])
        
        output.seek(0)
        
        logger.info(f"CSV export completed for experiment {experiment_id}")
        
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=experiment_{experiment_id}_results.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error exporting CSV"
        )


@router.get("/{experiment_id}/export/json")
def export_results_json(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """
    📋 Export complete experiment data as JSON.
    
    **Includes:**
    - Experiment metadata
    - Summary metrics
    - Statistical analysis
    - All raw events
    - All user assignments
    - Export timestamp
    
    **Use cases:**
    - API integration
    - Data warehousing
    - Custom analysis
    - Backup and archival
    
    **Returns:** Complete JSON export
    """
    try:
        logger.info(f"Exporting JSON data for experiment {experiment_id}")
        
        # Verify experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        if not experiment:
            raise HTTPException(
                status_code=404,
                detail=f"Experiment {experiment_id} not found"
            )
        
        # Get metrics
        metrics = MetricsCalculator.get_experiment_metrics(experiment_id, db)
        
        # Get raw events
        events = db.query(Event).filter(
            Event.experiment_id == experiment_id
        ).order_by(Event.created_at).all()
        
        events_data = [{
            "user_id": event.user_id,
            "variant": event.variant,
            "event_type": event.event_type,
            "created_at": event.created_at.isoformat()
        } for event in events]
        
        # Get assignments
        assignments = db.query(Assignment).filter(
            Assignment.experiment_id == experiment_id
        ).order_by(Assignment.assigned_at).all()
        
        assignments_data = [{
            "user_id": assignment.user_id,
            "variant": assignment.variant,
            "assigned_at": assignment.assigned_at.isoformat()
        } for assignment in assignments]
        
        # Build complete export
        export_data = {
            "export_info": {
                "experiment_id": experiment_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "export_type": "complete_experiment_data"
            },
            "experiment": {
                "id": experiment.id,
                "name": experiment.name,
                "status": experiment.status,
                "created_at": experiment.created_at.isoformat()
            },
            "summary_metrics": metrics,
            "raw_data": {
                "events": events_data,
                "assignments": assignments_data,
                "totals": {
                    "events_count": len(events_data),
                    "assignments_count": len(assignments_data)
                }
            }
        }
        
        logger.info(f"JSON export completed for experiment {experiment_id}")
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting JSON: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error exporting JSON"
        )


@router.get("/{experiment_id}/bayesian")
def get_bayesian_results(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """
    🧠 Bayesian A/B Test Analysis - More intuitive than p-values!

    **Why Bayesian?**
    - **Probability-based**: "80% chance treatment is better" vs "p = 0.03"
    - **Better for small data**: Works well with limited samples
    - **Credible intervals**: Range of plausible effects
    - **No p-hacking**: No arbitrary significance thresholds

    **What you get:**
    - `probability_treatment_better`: Chance treatment outperforms control
    - `expected_uplift_percent`: Average expected improvement
    - `credible_interval_95`: 95% range of possible uplifts
    - `evidence_strength`: How strong the evidence is
    - `recommendation`: Plain English advice

    **Interpretation:**
    - Probability > 95%: Very strong evidence treatment is better
    - Probability > 80%: Good evidence treatment is better
    - Probability 40-60%: No clear winner yet
    - Probability < 5%: Strong evidence control is better

    **Returns:** Bayesian analysis with intuitive probability-based results
    """
    try:
        logger.info(f"Running Bayesian analysis for experiment {experiment_id}")

        # Verify experiment exists
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()

        if not experiment:
            raise HTTPException(
                status_code=404,
                detail=f"Experiment {experiment_id} not found"
            )

        # Get conversion data
        control_conversions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "control",
            Event.event_type == "conversion"
        ).count()

        treatment_conversions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "treatment",
            Event.event_type == "conversion"
        ).count()

        control_impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "control",
            Event.event_type == "impression"
        ).count()

        treatment_impressions = db.query(Event).filter(
            Event.experiment_id == experiment_id,
            Event.variant == "treatment",
            Event.event_type == "impression"
        ).count()

        # Run Bayesian analysis
        bayesian_results = BayesianTest.beta_binomial_ab_test(
            control_conversions=control_conversions,
            control_impressions=control_impressions,
            treatment_conversions=treatment_conversions,
            treatment_impressions=treatment_impressions
        )

        logger.info(f"Bayesian analysis complete: P(treatment better) = {bayesian_results['probability_treatment_better']:.1%}")

        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "analysis_type": "Bayesian A/B Test (Beta-Binomial)",
            "raw_data": {
                "control": f"{control_conversions}/{control_impressions} conversions",
                "treatment": f"{treatment_conversions}/{treatment_impressions} conversions"
            },
            "bayesian_results": bayesian_results,
            "interpretation_guide": {
                "probability_treatment_better": {
                    "0.95+": "Very strong evidence treatment is better",
                    "0.80-0.95": "Strong evidence treatment is better",
                    "0.60-0.80": "Moderate evidence treatment is better",
                    "0.40-0.60": "No clear winner - collect more data",
                    "0.20-0.40": "Moderate evidence control is better",
                    "0.05-0.20": "Strong evidence control is better",
                    "0-0.05": "Very strong evidence control is better"
                },
                "credible_interval": "95% of possible uplift values fall in this range",
                "risk_of_choosing_wrong": "Probability of picking the wrong variant if you stop now"
            },
            "next_steps": [
                "If probability > 95%, consider implementing treatment",
                "If probability < 5%, stick with control",
                "Otherwise, continue collecting data",
                f"Compare with frequentist results: GET /results/{experiment_id}"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Bayesian analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error in Bayesian analysis"
        )


@router.get("/sample-size-calculator")
def calculate_sample_size(
    expected_uplift: float = 0.05,
    baseline_conversion: float = 0.10,
    desired_probability: float = 0.95
):
    """
    📏 Bayesian Sample Size Calculator - How much data do you need?

    **Parameters:**
    - `expected_uplift`: Minimum effect you want to detect (e.g., 0.05 = 5% improvement)
    - `baseline_conversion`: Your current conversion rate (e.g., 0.10 = 10%)
    - `desired_probability`: How confident you want to be (e.g., 0.95 = 95%)

    **Example:**
    - Detect 5% uplift from 10% baseline with 95% confidence
    - Returns: ~7,000 samples per variant

    **Returns:** Required sample size for Bayesian A/B test
    """
    try:
        logger.info(f"Calculating sample size: uplift={expected_uplift}, baseline={baseline_conversion}, confidence={desired_probability}")

        result = BayesianTest.calculate_required_sample_size(
            expected_uplift=expected_uplift,
            baseline_conversion=baseline_conversion,
            desired_probability=desired_probability
        )

        return {
            "calculation_parameters": {
                "expected_uplift": expected_uplift,
                "baseline_conversion_rate": baseline_conversion,
                "desired_probability": desired_probability
            },
            "sample_size_requirements": result,
            "interpretation": ".1f",
            "tips": [
                "This is a rough estimate - real experiments may need more data",
                "Consider seasonal effects and external factors",
                "Start with smaller sample, check results, then continue if needed",
                f"For {baseline_conversion:.1%} baseline, detecting {expected_uplift:.1%} uplift requires careful planning"
            ]
        }

    except Exception as e:
        logger.error(f"Error calculating sample size: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error calculating sample size"
        )
