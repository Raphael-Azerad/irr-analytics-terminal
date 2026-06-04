"""Balanced multi-project comparison."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable

import pandas as pd

from .calculations import calculate_metrics


def compare_projects(
    projects: Mapping[str, Iterable[float]], discount_rate: float, hurdle_rate: float
) -> pd.DataFrame:
    rows = []
    for name, cash_flows in projects.items():
        metrics = calculate_metrics(cash_flows, discount_rate, hurdle_rate)
        rows.append(
            {
                "Project Name": name,
                "Initial Investment": metrics.initial_investment,
                "IRR": metrics.irr,
                "MIRR": metrics.mirr,
                "NPV": metrics.npv,
                "Payback Period": metrics.payback_period,
                "Discounted Payback": metrics.discounted_payback_period,
                "Profitability Index": metrics.profitability_index,
                "Decision Status": metrics.decision_status,
            }
        )
    frame = pd.DataFrame(rows)
    positive_npvs = frame["NPV"].clip(lower=0)
    max_npv = positive_npvs.max() or 1.0
    frame["Score"] = (
        (frame["NPV"] > 0).astype(float) * 25
        + (frame["IRR"].fillna(-1) >= hurdle_rate).astype(float) * 20
        + frame["Profitability Index"].fillna(0).clip(upper=2) / 2 * 15
        + positive_npvs / max_npv * 30
        + (1 / frame["Discounted Payback"].fillna(100).clip(lower=1)) * 10
    )
    frame["Rank"] = frame["Score"].rank(method="dense", ascending=False).astype(int)
    return frame.sort_values(["Rank", "NPV"], ascending=[True, False]).reset_index(drop=True)
