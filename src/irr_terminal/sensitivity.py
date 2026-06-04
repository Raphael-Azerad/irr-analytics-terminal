"""Sensitivity analysis for discount rates and cash-flow growth."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .calculations import cash_flow_array, npv


def grow_cash_flows(cash_flows: Iterable[float], growth_rate: float) -> list[float]:
    flows = cash_flow_array(cash_flows).copy()
    for period in range(1, len(flows)):
        if flows[period] > 0:
            flows[period] *= (1 + growth_rate) ** period
    return flows.tolist()


def sensitivity_table(
    cash_flows: Iterable[float],
    discount_rates: Iterable[float],
    growth_rates: Iterable[float],
) -> pd.DataFrame:
    rates = list(discount_rates)
    growth = list(growth_rates)
    values = [
        [npv(rate, grow_cash_flows(cash_flows, growth_rate)) for growth_rate in growth]
        for rate in rates
    ]
    return pd.DataFrame(
        values,
        index=[f"{rate:.1%}" for rate in rates],
        columns=[f"{rate:+.1%}" for rate in growth],
    )


def npv_profile(
    cash_flows: Iterable[float], max_rate: float = 0.30, points: int = 121
) -> pd.DataFrame:
    rates = [max_rate * index / (points - 1) for index in range(points)]
    return pd.DataFrame({"Discount Rate": rates, "NPV": [npv(rate, cash_flows) for rate in rates]})
