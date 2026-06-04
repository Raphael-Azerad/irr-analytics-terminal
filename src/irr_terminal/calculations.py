"""Core capital-budgeting calculations and IRR diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

from .exceptions import CashFlowError


@dataclass(frozen=True)
class IRRAnalysis:
    value: float | None
    roots: tuple[float, ...]
    sign_changes: int
    status: str
    warning: str | None


@dataclass(frozen=True)
class FinancialMetrics:
    initial_investment: float
    total_cash_inflows: float
    net_cash_flow: float
    irr: float | None
    mirr: float | None
    npv: float
    payback_period: float | None
    discounted_payback_period: float | None
    profitability_index: float | None
    hurdle_rate: float
    decision_status: str
    irr_status: str
    irr_warning: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cash_flow_array(values: Iterable[float]) -> np.ndarray:
    flows = np.asarray(list(values), dtype=float)
    if flows.ndim != 1 or flows.size < 2:
        raise CashFlowError("At least two cash-flow periods are required.")
    if not np.all(np.isfinite(flows)):
        raise CashFlowError("Cash flows must contain only finite numeric values.")
    return flows


def npv(rate: float, cash_flows: Iterable[float]) -> float:
    """Return net present value using period 0 as the undiscounted initial cash flow."""
    flows = cash_flow_array(cash_flows)
    if rate <= -1:
        raise CashFlowError("Discount rate must be greater than -100%.")
    periods = np.arange(flows.size)
    return float(np.sum(flows / (1 + rate) ** periods))


def sign_change_count(cash_flows: Iterable[float]) -> int:
    flows = cash_flow_array(cash_flows)
    signs = np.sign(flows[flows != 0])
    return int(np.sum(signs[1:] != signs[:-1])) if signs.size else 0


def _bisect_root(cash_flows: np.ndarray, left: float, right: float) -> float:
    """Solve for a zero-NPV discount rate inside a bracket."""
    left_value = npv(left, cash_flows)
    for _ in range(100):
        midpoint = (left + right) / 2
        midpoint_value = npv(midpoint, cash_flows)
        if abs(midpoint_value) < 1e-10 or abs(right - left) < 1e-10:
            return float(midpoint)
        if left_value * midpoint_value <= 0:
            right = midpoint
        else:
            left = midpoint
            left_value = midpoint_value
    return float((left + right) / 2)


def find_irr_roots(cash_flows: Iterable[float]) -> tuple[float, ...]:
    """Find real IRR roots across a wide practical search grid."""
    flows = cash_flow_array(cash_flows)
    if not (np.any(flows < 0) and np.any(flows > 0)):
        return ()
    grid = np.concatenate(
        [np.linspace(-0.9999, 1.0, 3000), np.geomspace(2.01, 1000.0, 1500) - 1]
    )
    values = np.array([npv(rate, flows) for rate in grid])
    roots: list[float] = []
    for left, right, left_value, right_value in zip(
        grid[:-1], grid[1:], values[:-1], values[1:]
    ):
        if abs(left_value) < 1e-10:
            roots.append(float(left))
        elif left_value * right_value < 0:
            roots.append(_bisect_root(flows, float(left), float(right)))
    unique: list[float] = []
    for root in roots:
        if not any(abs(root - existing) < 1e-6 for existing in unique):
            unique.append(root)
    return tuple(unique)


def analyze_irr(cash_flows: Iterable[float]) -> IRRAnalysis:
    flows = cash_flow_array(cash_flows)
    changes = sign_change_count(flows)
    if np.all(flows >= 0):
        return IRRAnalysis(None, (), changes, "No valid IRR", "Cash flows contain no outflow.")
    if np.all(flows <= 0):
        return IRRAnalysis(None, (), changes, "No valid IRR", "Cash flows contain no inflow.")
    roots = find_irr_roots(flows)
    if not roots:
        return IRRAnalysis(None, (), changes, "No valid IRR", "No real IRR was found.")
    if changes > 1 or len(roots) > 1:
        warning = (
            "Cash-flow signs change multiple times, so multiple IRRs may exist. "
            "Use NPV and MIRR as the primary decision measures."
        )
        return IRRAnalysis(roots[0], roots, changes, "Review cash-flow pattern", warning)
    return IRRAnalysis(roots[0], roots, changes, "Valid IRR", None)


def irr(cash_flows: Iterable[float]) -> float | None:
    return analyze_irr(cash_flows).value


def mirr(
    cash_flows: Iterable[float], finance_rate: float, reinvestment_rate: float
) -> float | None:
    """Return modified IRR using explicit finance and reinvestment assumptions."""
    flows = cash_flow_array(cash_flows)
    if finance_rate <= -1 or reinvestment_rate <= -1:
        raise CashFlowError("Finance and reinvestment rates must be greater than -100%.")
    periods = flows.size - 1
    negative_pv = sum(
        flow / (1 + finance_rate) ** period
        for period, flow in enumerate(flows)
        if flow < 0
    )
    positive_fv = sum(
        flow * (1 + reinvestment_rate) ** (periods - period)
        for period, flow in enumerate(flows)
        if flow > 0
    )
    if negative_pv == 0 or positive_fv == 0:
        return None
    return float((positive_fv / abs(negative_pv)) ** (1 / periods) - 1)


def payback_period(
    cash_flows: Iterable[float], discount_rate: float | None = None
) -> float | None:
    """Return fractional payback period, or None when cumulative cash flow never recovers."""
    flows = cash_flow_array(cash_flows)
    if discount_rate is not None:
        if discount_rate <= -1:
            raise CashFlowError("Discount rate must be greater than -100%.")
        flows = flows / (1 + discount_rate) ** np.arange(flows.size)
    cumulative = np.cumsum(flows)
    if cumulative[0] >= 0:
        return 0.0
    for period in range(1, flows.size):
        if cumulative[period] >= 0:
            prior_deficit = abs(cumulative[period - 1])
            return float(period - 1 + prior_deficit / flows[period])
    return None


def profitability_index(cash_flows: Iterable[float], discount_rate: float) -> float | None:
    """Return PV of future cash flows divided by the initial outlay."""
    flows = cash_flow_array(cash_flows)
    initial_outlay = abs(min(float(flows[0]), 0.0))
    if initial_outlay == 0:
        return None
    return float(npv(discount_rate, [0.0, *flows[1:]]) / initial_outlay)


def decision_status(
    project_irr: float | None,
    project_npv: float,
    hurdle_rate: float,
    irr_status: str,
) -> str:
    if irr_status == "Review cash-flow pattern":
        return "Review cash-flow pattern"
    if project_irr is None:
        return "No valid IRR"
    if project_npv > 0 and project_irr >= hurdle_rate:
        return "Passes hurdle rate"
    if project_npv > 0:
        return "Positive NPV"
    if project_irr >= hurdle_rate:
        return "Mixed result"
    return "Fails hurdle rate"


def calculate_metrics(
    cash_flows: Iterable[float],
    discount_rate: float,
    hurdle_rate: float,
    finance_rate: float | None = None,
    reinvestment_rate: float | None = None,
) -> FinancialMetrics:
    flows = cash_flow_array(cash_flows)
    irr_result = analyze_irr(flows)
    project_npv = npv(discount_rate, flows)
    finance_rate = discount_rate if finance_rate is None else finance_rate
    reinvestment_rate = discount_rate if reinvestment_rate is None else reinvestment_rate
    initial = abs(min(float(flows[0]), 0.0))
    return FinancialMetrics(
        initial_investment=initial,
        total_cash_inflows=float(np.sum(flows[flows > 0])),
        net_cash_flow=float(np.sum(flows)),
        irr=irr_result.value,
        mirr=mirr(flows, finance_rate, reinvestment_rate),
        npv=project_npv,
        payback_period=payback_period(flows),
        discounted_payback_period=payback_period(flows, discount_rate),
        profitability_index=profitability_index(flows, discount_rate),
        hurdle_rate=hurdle_rate,
        decision_status=decision_status(
            irr_result.value, project_npv, hurdle_rate, irr_result.status
        ),
        irr_status=irr_result.status,
        irr_warning=irr_result.warning,
    )
