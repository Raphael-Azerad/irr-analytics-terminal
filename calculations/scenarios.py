"""Scenario and sensitivity analysis helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .metrics import calculate_metrics, irr, npv


@dataclass(frozen=True)
class Scenario:
    name: str
    revenue_factor: float
    cost_factor: float
    terminal_value_factor: float


DEFAULT_SCENARIOS = (
    Scenario("Bear", 0.85, 1.10, 0.85),
    Scenario("Base", 1.00, 1.00, 1.00),
    Scenario("Bull", 1.15, 0.95, 1.15),
)


def apply_operating_assumptions(
    cash_flows: Iterable[float],
    revenue_factor: float = 1.0,
    cost_factor: float = 1.0,
    terminal_value_factor: float = 1.0,
    cost_share: float = 0.40,
) -> np.ndarray:
    """Transform net cash flows using an implied revenue and cost split."""

    flows = np.asarray(list(cash_flows), dtype=float).copy()
    if flows.size < 2:
        raise ValueError("At least two cash-flow periods are required.")
    operating = flows[1:].copy()
    implied_revenue = np.maximum(operating, 0) / max(1 - cost_share, 0.01)
    implied_cost = implied_revenue * cost_share
    adjusted = implied_revenue * revenue_factor - implied_cost * cost_factor
    adjusted[operating < 0] = operating[operating < 0] * cost_factor
    flows[1:] = adjusted
    flows[-1] *= terminal_value_factor
    return flows


def scenario_table(
    cash_flows: Iterable[float],
    discount_rate: float,
    hurdle_rate: float,
    cost_of_capital: float,
    finance_rate: float,
    reinvestment_rate: float,
) -> pd.DataFrame:
    rows = []
    for scenario in DEFAULT_SCENARIOS:
        adjusted = apply_operating_assumptions(
            cash_flows,
            scenario.revenue_factor,
            scenario.cost_factor,
            scenario.terminal_value_factor,
        )
        metrics = calculate_metrics(
            adjusted,
            discount_rate,
            hurdle_rate,
            cost_of_capital,
            finance_rate,
            reinvestment_rate,
        )
        rows.append(
            {
                "Scenario": scenario.name,
                "IRR": metrics.irr,
                "NPV": metrics.npv,
                "Payback": metrics.payback_period,
                "Profitability Index": metrics.profitability_index,
            }
        )
    return pd.DataFrame(rows)


def irr_sensitivity(
    cash_flows: Iterable[float],
    revenue_changes: Iterable[float],
    cost_changes: Iterable[float],
) -> pd.DataFrame:
    data = []
    for revenue_change in revenue_changes:
        row = []
        for cost_change in cost_changes:
            adjusted = apply_operating_assumptions(
                cash_flows,
                revenue_factor=1 + revenue_change,
                cost_factor=1 + cost_change,
            )
            row.append(irr(adjusted))
        data.append(row)
    return pd.DataFrame(
        data,
        index=[f"{value:+.0%}" for value in revenue_changes],
        columns=[f"{value:+.0%}" for value in cost_changes],
    )


def npv_sensitivity(
    cash_flows: Iterable[float],
    discount_rates: Iterable[float],
    terminal_value_changes: Iterable[float],
) -> pd.DataFrame:
    data = []
    for discount_rate in discount_rates:
        row = []
        for terminal_change in terminal_value_changes:
            adjusted = apply_operating_assumptions(
                cash_flows, terminal_value_factor=1 + terminal_change
            )
            row.append(npv(discount_rate, adjusted))
        data.append(row)
    return pd.DataFrame(
        data,
        index=[f"{value:.1%}" for value in discount_rates],
        columns=[f"{value:+.0%}" for value in terminal_value_changes],
    )
