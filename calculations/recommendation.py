"""Investment committee recommendation logic."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import FinancialMetrics


@dataclass(frozen=True)
class InvestmentRecommendation:
    rating: str
    score: int
    headline: str
    rationale: tuple[str, ...]


def generate_recommendation(
    metrics: FinancialMetrics,
    bear_case_npv: float | None = None,
) -> InvestmentRecommendation:
    """Generate a transparent recommendation from capital budgeting metrics."""

    score = 0
    reasons: list[str] = []

    if metrics.npv > 0:
        score += 2
        reasons.append("The project creates value at the selected discount rate.")
    else:
        score -= 3
        reasons.append("The project destroys value at the selected discount rate.")

    if metrics.irr is not None and metrics.irr > metrics.hurdle_rate:
        score += 2
        spread = metrics.irr - metrics.hurdle_rate
        reasons.append(f"IRR exceeds the hurdle rate by {spread:.1%}.")
    else:
        score -= 2
        reasons.append("IRR does not clear the required hurdle rate.")

    if metrics.irr is not None and metrics.irr > metrics.cost_of_capital:
        score += 1
        reasons.append("Returns exceed the cost of capital.")
    else:
        score -= 1
        reasons.append("Returns do not exceed the cost of capital.")

    if metrics.profitability_index is not None and metrics.profitability_index > 1:
        score += 1
        reasons.append("The profitability index is above 1.0x.")

    if metrics.discounted_payback_period is None:
        score -= 1
        reasons.append("The investment does not achieve discounted payback.")

    if bear_case_npv is not None:
        if bear_case_npv > 0:
            score += 1
            reasons.append("The project remains value-accretive in the bear case.")
        else:
            score -= 1
            reasons.append("The bear case produces a negative NPV and requires downside mitigation.")

    if score >= 5:
        rating = "Strong Buy"
        headline = (
            "Capital deployment is recommended. The project demonstrates compelling "
            "value creation and return performance."
        )
    elif score >= 2:
        rating = "Consider"
        headline = (
            "The project is investable, subject to diligence on the key operating "
            "assumptions and downside protection."
        )
    else:
        rating = "Reject"
        headline = (
            "Capital deployment is not recommended under the current assumptions."
        )

    return InvestmentRecommendation(rating, score, headline, tuple(reasons))
