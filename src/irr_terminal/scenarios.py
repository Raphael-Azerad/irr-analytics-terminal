"""Bear, base, and bull scenario analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .calculations import calculate_metrics, cash_flow_array


@dataclass(frozen=True)
class Scenario:
    name: str
    inflow_factor: float
    discount_rate_adjustment: float
    probability: float


DEFAULT_SCENARIOS = (
    Scenario("Bear", 0.85, 0.02, 0.25),
    Scenario("Base", 1.00, 0.00, 0.50),
    Scenario("Bull", 1.15, -0.01, 0.25),
)


def apply_scenario(cash_flows: Iterable[float], inflow_factor: float) -> list[float]:
    flows = cash_flow_array(cash_flows).copy()
    future_positive_flows = (flows > 0) & (pd.Series(range(len(flows))).to_numpy() > 0)
    flows[future_positive_flows] *= inflow_factor
    return flows.tolist()


def normalize_probabilities(probabilities: Iterable[float]) -> list[float]:
    values = [float(value) for value in probabilities]
    total = sum(values)
    if total <= 0:
        raise ValueError("Scenario probabilities must total more than zero.")
    return [value / total for value in values]


def scenario_analysis(
    cash_flows: Iterable[float],
    discount_rate: float,
    hurdle_rate: float,
    probabilities: Iterable[float] | None = None,
) -> pd.DataFrame:
    probability_values = normalize_probabilities(
        probabilities
        if probabilities is not None
        else [scenario.probability for scenario in DEFAULT_SCENARIOS]
    )
    rows = []
    for scenario, probability in zip(DEFAULT_SCENARIOS, probability_values):
        adjusted_rate = max(discount_rate + scenario.discount_rate_adjustment, 0.0)
        adjusted_flows = apply_scenario(cash_flows, scenario.inflow_factor)
        metrics = calculate_metrics(adjusted_flows, adjusted_rate, hurdle_rate)
        rows.append(
            {
                "Scenario": scenario.name,
                "Probability": probability,
                "Discount Rate": adjusted_rate,
                "IRR": metrics.irr,
                "MIRR": metrics.mirr,
                "NPV": metrics.npv,
                "Payback Period": metrics.payback_period,
                "Discounted Payback": metrics.discounted_payback_period,
                "Profitability Index": metrics.profitability_index,
                "Decision Status": metrics.decision_status,
            }
        )
    return pd.DataFrame(rows)


def probability_weighted_npv(frame: pd.DataFrame) -> float:
    probabilities = normalize_probabilities(frame["Probability"])
    return float(
        sum(probability * value for probability, value in zip(probabilities, frame["NPV"]))
    )
