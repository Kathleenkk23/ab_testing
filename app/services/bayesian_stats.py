"""Bayesian A/B testing with Beta-Binomial model for more intuitive results"""
import logging
import math
from typing import Dict, Union, Tuple
from scipy import stats
import numpy as np

logger = logging.getLogger(__name__)


class BayesianTest:
    """
    Bayesian A/B testing using Beta-Binomial model.

    **Why Bayesian?**
    - More intuitive than p-values ("80% chance treatment is better")
    - Better for small sample sizes
    - Provides credible intervals
    - No p-value hacking concerns

    **Beta-Binomial Model:**
    - Uses Beta distribution as prior for conversion rates
    - Binomial likelihood for observed data
    - Beta posterior distribution for updated beliefs

    **Default Prior:** Beta(1, 1) = Uniform distribution
    - Represents complete uncertainty about conversion rate
    - Can be customized based on historical data
    """

    @staticmethod
    def beta_binomial_ab_test(
        control_conversions: int,
        control_impressions: int,
        treatment_conversions: int,
        treatment_impressions: int,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0
    ) -> Dict[str, Union[float, bool, str]]:
        """
        Perform Bayesian A/B test using Beta-Binomial model.

        **Parameters:**
        - control_conversions: Conversions in control variant
        - control_impressions: Total impressions in control
        - treatment_conversions: Conversions in treatment variant
        - treatment_impressions: Total impressions in treatment
        - prior_alpha: Alpha parameter for Beta prior (default: 1.0)
        - prior_beta: Beta parameter for Beta prior (default: 1.0)

        **Returns:**
        - probability_treatment_better: P(treatment > control)
        - expected_uplift: Expected relative improvement
        - credible_interval: 95% credible interval for uplift
        - treatment_conversion_rate: Posterior mean for treatment
        - control_conversion_rate: Posterior mean for control
        - risk_of_choosing_wrong: Probability of making wrong decision
        """

        logger.debug(f"Running Bayesian A/B test: C({control_conversions}/{control_impressions}) vs T({treatment_conversions}/{treatment_impressions})")

        # Posterior parameters for Beta distributions
        control_alpha = prior_alpha + control_conversions
        control_beta = prior_beta + (control_impressions - control_conversions)

        treatment_alpha = prior_alpha + treatment_conversions
        treatment_beta = prior_beta + (treatment_impressions - treatment_conversions)

        # Posterior means (expected conversion rates)
        control_cr = control_alpha / (control_alpha + control_beta)
        treatment_cr = treatment_alpha / (treatment_alpha + treatment_beta)

        # Probability that treatment is better than control
        # This requires numerical integration of the difference of two Beta distributions
        prob_treatment_better = BayesianTest._calculate_probability_treatment_better(
            control_alpha, control_beta, treatment_alpha, treatment_beta
        )

        # Expected uplift
        expected_uplift = ((treatment_cr - control_cr) / control_cr) * 100 if control_cr > 0 else 0

        # 95% credible interval for uplift (simulated)
        uplift_samples = BayesianTest._sample_uplift_distribution(
            control_alpha, control_beta, treatment_alpha, treatment_beta, n_samples=10000
        )
        credible_interval = np.percentile(uplift_samples, [2.5, 97.5])

        # Risk of choosing wrong variant
        risk_wrong = min(prob_treatment_better, 1 - prob_treatment_better)

        # Strength of evidence (Kullback-Leibler divergence)
        evidence_strength = BayesianTest._calculate_evidence_strength(
            control_alpha, control_beta, treatment_alpha, treatment_beta
        )

        return {
            "probability_treatment_better": round(prob_treatment_better, 4),
            "expected_uplift_percent": round(expected_uplift, 2),
            "credible_interval_95": [round(credible_interval[0], 2), round(credible_interval[1], 2)],
            "treatment_conversion_rate": round(treatment_cr, 4),
            "control_conversion_rate": round(control_cr, 4),
            "risk_of_choosing_wrong_variant": round(risk_wrong, 4),
            "evidence_strength": evidence_strength,
            "sample_size_adequate": control_impressions >= 100 and treatment_impressions >= 100,
            "recommendation": BayesianTest._generate_recommendation(
                prob_treatment_better, expected_uplift, risk_wrong
            )
        }

    @staticmethod
    def _calculate_probability_treatment_better(
        control_alpha: float, control_beta: float,
        treatment_alpha: float, treatment_beta: float,
        n_samples: int = 100000
    ) -> float:
        """
        Calculate P(treatment > control) using Monte Carlo simulation.
        """
        # Sample from posterior distributions
        control_samples = np.random.beta(control_alpha, control_beta, n_samples)
        treatment_samples = np.random.beta(treatment_alpha, treatment_beta, n_samples)

        # Count how often treatment > control
        prob_better = np.mean(treatment_samples > control_samples)

        return float(prob_better)

    @staticmethod
    def _sample_uplift_distribution(
        control_alpha: float, control_beta: float,
        treatment_alpha: float, treatment_beta: float,
        n_samples: int = 10000
    ) -> np.ndarray:
        """
        Sample from the uplift distribution for credible intervals.
        """
        control_samples = np.random.beta(control_alpha, control_beta, n_samples)
        treatment_samples = np.random.beta(treatment_alpha, treatment_beta, n_samples)

        # Calculate relative uplift: (treatment - control) / control
        # Handle division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            uplift = (treatment_samples - control_samples) / control_samples
            uplift = np.where(control_samples == 0, 0, uplift)  # Set uplift to 0 when control is 0

        return uplift

    @staticmethod
    def _calculate_evidence_strength(
        control_alpha: float, control_beta: float,
        treatment_alpha: float, treatment_beta: float
    ) -> str:
        """
        Calculate strength of evidence using Bayes factor approximation.
        """
        # Simplified evidence strength based on probability difference from 0.5
        prob_better = BayesianTest._calculate_probability_treatment_better(
            control_alpha, control_beta, treatment_alpha, treatment_beta, n_samples=10000
        )

        diff_from_50 = abs(prob_better - 0.5) * 2  # Scale to 0-1

        if diff_from_50 < 0.1:
            return "Weak evidence"
        elif diff_from_50 < 0.3:
            return "Moderate evidence"
        elif diff_from_50 < 0.5:
            return "Strong evidence"
        else:
            return "Very strong evidence"

    @staticmethod
    def _generate_recommendation(
        prob_better: float, expected_uplift: float, risk: float
    ) -> str:
        """
        Generate human-readable recommendation based on Bayesian results.
        """
        if prob_better > 0.95:
            return ".1f"
        elif prob_better > 0.90:
            return ".1f"
        elif prob_better > 0.80:
            return ".1f"
        elif prob_better > 0.70:
            return ".1f"
        elif prob_better < 0.05:
            return ".1f"
        elif prob_better < 0.10:
            return ".1f"
        elif prob_better < 0.20:
            return ".1f"
        elif prob_better < 0.30:
            return ".1f"
        else:
            return ".1f"

    @staticmethod
    def calculate_required_sample_size(
        expected_uplift: float = 0.05,
        baseline_conversion: float = 0.10,
        desired_probability: float = 0.95,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0
    ) -> Dict[str, Union[int, float]]:
        """
        Calculate required sample size for Bayesian A/B test.

        **Parameters:**
        - expected_uplift: Minimum detectable effect size (e.g., 0.05 = 5% uplift)
        - baseline_conversion: Baseline conversion rate
        - desired_probability: Desired probability of detecting the effect
        - prior_alpha, prior_beta: Prior parameters

        **Returns:**
        - Required samples per variant
        - Total experiment duration estimate
        """
        # This is a simplified calculation - real Bayesian sample size
        # calculation is complex and typically requires simulation

        # Rough approximation using normal approximation
        effect_size = expected_uplift * baseline_conversion
        variance = baseline_conversion * (1 - baseline_conversion)

        # Z-score for desired probability
        z_score = stats.norm.ppf(desired_probability)

        # Required samples (simplified)
        n_per_variant = int((z_score ** 2 * variance * 2) / (effect_size ** 2))

        return {
            "samples_per_variant": n_per_variant,
            "total_samples": n_per_variant * 2,
            "estimated_weeks": max(1, n_per_variant // 1000),  # Rough estimate
            "confidence_level": desired_probability,
            "minimum_detectable_effect": expected_uplift
        }