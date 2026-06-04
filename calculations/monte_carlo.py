"""Monte Carlo simulation for capital budgeting uncertainty."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .metrics import irr


@dataclass(frozen=True)
class MonteCarloResult:
    simulations: pd.DataFrame
    probability_positive_npv: float
    probability_irr_above_hurdle: float
    summary: pd.DataFrame
    npv_value_at_risk_5: float
    npv_conditional_value_at_risk_5: float
    irr_value_at_risk_5: float | None


def run_monte_carlo(
    cash_flows: Iterable[float],
    discount_rate: float,
    hurdle_rate: float,
    simulations: int = 5000,
    revenue_uncertainty: float = 0.10,
    cost_uncertainty: float = 0.08,
    growth_uncertainty: float = 0.03,
    cost_share: float = 0.40,
    seed: int = 42,
) -> MonteCarloResult:
    """Simulate NPV and IRR under correlated operating uncertainty."""

    base = np.asarray(list(cash_flows), dtype=float)
    if simulations < 100:
        raise ValueError("Monte Carlo analysis requires at least 100 simulations.")

    rng = np.random.default_rng(seed)
    periods = np.arange(base.size)
    future = base[1:]
    implied_revenue = np.maximum(future, 0) / max(1 - cost_share, 0.01)
    implied_cost = implied_revenue * cost_share

    revenue_shocks = rng.normal(1.0, revenue_uncertainty, simulations)
    cost_shocks = rng.normal(1.0, cost_uncertainty, simulations)
    growth_shocks = rng.normal(0.0, growth_uncertainty, simulations)
    growth_curve = (1 + growth_shocks[:, None]) ** np.arange(1, base.size)

    simulated_future = (
        implied_revenue[None, :] * revenue_shocks[:, None] * growth_curve
        - implied_cost[None, :] * cost_shocks[:, None]
    )
    simulated_future[:, future < 0] = (
        future[future < 0][None, :] * cost_shocks[:, None]
    )
    simulated = np.column_stack(
        [np.full(simulations, base[0]), simulated_future]
    )

    discount_factors = (1 + discount_rate) ** periods
    npvs = np.sum(simulated / discount_factors, axis=1)
    irrs = np.array([irr(row) for row in simulated], dtype=float)

    frame = pd.DataFrame({"NPV": npvs, "IRR": irrs})
    summary = frame.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
    npv_var_5 = float(np.quantile(npvs, 0.05))
    downside_npvs = npvs[npvs <= npv_var_5]
    valid_irrs = irrs[np.isfinite(irrs)]
    return MonteCarloResult(
        simulations=frame,
        probability_positive_npv=float(np.mean(npvs > 0)),
        probability_irr_above_hurdle=float(np.nanmean(irrs > hurdle_rate)),
        summary=summary,
        npv_value_at_risk_5=npv_var_5,
        npv_conditional_value_at_risk_5=float(np.mean(downside_npvs)),
        irr_value_at_risk_5=(
            None if valid_irrs.size == 0 else float(np.quantile(valid_irrs, 0.05))
        ),
    )
