"""Statistical significance testing for A/B tests with logging"""
import logging
import math
from typing import Dict, Union
from scipy import stats

logger = logging.getLogger(__name__)


class StatisticalTest:
    """Two-proportion z-test for A/B testing significance testing"""

    @staticmethod
    def two_proportion_z_test(
        control_conversions: int,
        control_impressions: int,
        treatment_conversions: int,
        treatment_impressions: int,
        alpha: float = 0.05
    ) -> Dict[str, Union[float, bool, str]]:
        """
        Perform two-proportion z-test to determine if treatment conversion rate
        is statistically significantly different from control conversion rate.

        **Formula (Two-Proportion Z-Test):**
        
        1. Calculate conversion rates for each variant:
           - p1 = control_conversions / control_impressions
           - p2 = treatment_conversions / treatment_impressions

        2. Calculate pooled proportion (overall conversion rate):
           - p_pool = (control_conversions + treatment_conversions) / 
                      (control_impressions + treatment_impressions)

        3. Calculate standard error (SE):
           - SE = sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
           - where n1 = control impressions, n2 = treatment impressions

        4. Calculate z-statistic:
           - z = (p2 - p1) / SE

        5. Calculate two-tailed p-value:
           - p_value = 2 * P(Z > |z|)
           - (multiply by 2 because we test both directions)

        6. Compare p-value to alpha (0.05):
           - is_significant = p_value < alpha

        **Args:**
        - control_conversions: Number of conversions in control variant
        - control_impressions: Number of impressions in control variant
        - treatment_conversions: Number of conversions in treatment variant
        - treatment_impressions: Number of impressions in treatment variant
        - alpha: Significance level (default 0.05 = 95% confidence)

        **Returns:**
            dict with keys:
            - 'control_conversion_rate': float (0.0 to 1.0)
            - 'treatment_conversion_rate': float (0.0 to 1.0)
            - 'uplift': float (treatment - control)
            - 'z_score': float (z-statistic)
            - 'p_value': float (two-tailed p-value)
            - 'is_significant': bool (p_value < alpha)
            - 'alpha': float (significance level used)
        """

        # Handle edge cases
        if control_impressions == 0 or treatment_impressions == 0:
            logger.warning(f"Insufficient data: control={control_impressions} impressions, "
                          f"treatment={treatment_impressions} impressions")
            return {
                'control_conversion_rate': 0.0,
                'treatment_conversion_rate': 0.0,
                'uplift': 0.0,
                'z_score': 0.0,
                'p_value': 1.0,
                'is_significant': False,
                'alpha': alpha,
                'note': 'Insufficient data (zero impressions)'
            }

        # Calculate conversion rates
        p1 = control_conversions / control_impressions
        p2 = treatment_conversions / treatment_impressions

        # Calculate pooled proportion
        p_pool = (control_conversions + treatment_conversions) / (
            control_impressions + treatment_impressions
        )

        # Calculate standard error
        se = math.sqrt(
            p_pool * (1 - p_pool) * (1 / control_impressions + 1 / treatment_impressions)
        )

        # Handle case where SE is zero (both variants have same conversion rate)
        if se == 0:
            return {
                'control_conversion_rate': round(p1, 4),
                'treatment_conversion_rate': round(p2, 4),
                'uplift': round(p2 - p1, 4),
                'z_score': 0.0,
                'p_value': 1.0,
                'is_significant': False,
                'alpha': alpha,
                'note': 'No variance between variants'
            }

        # Calculate z-statistic
        z_score = (p2 - p1) / se

        # Calculate two-tailed p-value
        # P(Z > |z|) * 2 for two-tailed test
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # Determine significance
        is_significant = p_value < alpha

        return {
            'control_conversion_rate': round(p1, 4),
            'treatment_conversion_rate': round(p2, 4),
            'uplift': round(p2 - p1, 4),
            'z_score': round(z_score, 4),
            'p_value': round(p_value, 4),
            'is_significant': is_significant,
            'alpha': alpha
        }
