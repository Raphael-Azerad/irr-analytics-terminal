"""Core financial analytics for IRR Analytics Terminal."""

from .metrics import FinancialMetrics, calculate_metrics, xirr, xnpv
from .monte_carlo import MonteCarloResult, run_monte_carlo
from .recommendation import InvestmentRecommendation, generate_recommendation

__all__ = [
    "FinancialMetrics",
    "InvestmentRecommendation",
    "MonteCarloResult",
    "calculate_metrics",
    "generate_recommendation",
    "run_monte_carlo",
    "xirr",
    "xnpv",
]
