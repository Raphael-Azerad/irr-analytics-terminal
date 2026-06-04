"""Capital budgeting calculations used throughout the application."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Iterable

import numpy as np

try:
    from scipy.optimize import brentq
except ImportError:  # pragma: no cover - deployment installs SciPy
    brentq = None


@dataclass(frozen=True)
class FinancialMetrics:
    """A complete capital budgeting metric set."""

    initial_investment: float
    total_inflows: float
    net_cash_flow: float
    irr: float | None
    npv: float
    mirr: float | None
    profitability_index: float | None
    payback_period: float | None
    discounted_payback_period: float | None
    discount_rate: float
    hurdle_rate: float
    cost_of_capital: float
    irr_spread_to_hurdle: float | None
    npv_to_investment: float | None

    def to_dict(self) -> dict[str, float | None]:
        return asdict(self)


def _cash_flows(values: Iterable[float]) -> np.ndarray:
    flows = np.asarray(list(values), dtype=float)
    if flows.ndim != 1 or flows.size < 2:
        raise ValueError("At least two cash-flow periods are required.")
    if not np.all(np.isfinite(flows)):
        raise ValueError("Cash flows must contain only finite numeric values.")
    return flows


def npv(rate: float, cash_flows: Iterable[float]) -> float:
    """Return NPV where the first cash flow occurs at time zero."""

    flows = _cash_flows(cash_flows)
    if rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")
    periods = np.arange(flows.size)
    return float(np.sum(flows / (1 + rate) ** periods))


def _dates(values: Iterable[date | datetime | str]) -> list[date]:
    parsed: list[date] = []
    for value in values:
        if isinstance(value, datetime):
            parsed.append(value.date())
        elif isinstance(value, date):
            parsed.append(value)
        elif isinstance(value, str):
            parsed.append(datetime.fromisoformat(value).date())
        else:
            raise ValueError("Dates must be date, datetime, or ISO-formatted string values.")
    if len(parsed) < 2:
        raise ValueError("At least two cash-flow dates are required.")
    if any(current <= previous for previous, current in zip(parsed, parsed[1:])):
        raise ValueError("Cash-flow dates must be strictly increasing.")
    return parsed


def xnpv(
    rate: float,
    cash_flows: Iterable[float],
    dates: Iterable[date | datetime | str],
) -> float:
    """Return date-aware NPV using actual day counts and a 365-day year."""

    flows = _cash_flows(cash_flows)
    parsed_dates = _dates(dates)
    if len(parsed_dates) != flows.size:
        raise ValueError("Cash flows and dates must have the same length.")
    if rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")
    day_offsets = np.array(
        [(value - parsed_dates[0]).days / 365.0 for value in parsed_dates],
        dtype=float,
    )
    return float(np.sum(flows / (1 + rate) ** day_offsets))


def xirr(
    cash_flows: Iterable[float],
    dates: Iterable[date | datetime | str],
) -> float | None:
    """Return annualized IRR for irregularly timed cash flows."""

    flows = _cash_flows(cash_flows)
    parsed_dates = _dates(dates)
    if len(parsed_dates) != flows.size:
        raise ValueError("Cash flows and dates must have the same length.")
    if not (np.any(flows < 0) and np.any(flows > 0)):
        return None

    left, right = -0.9999, 1.0
    function = lambda rate: xnpv(rate, flows, parsed_dates)
    left_value, right_value = function(left), function(right)
    while left_value * right_value > 0 and right < 1000:
        right = right * 2 + 1
        right_value = function(right)
    if left_value * right_value > 0:
        return None
    return float(_solve_root(function, left, right))


def irr(cash_flows: Iterable[float]) -> float | None:
    """Return the economically relevant IRR, if one can be identified."""

    flows = _cash_flows(cash_flows)
    if not (np.any(flows < 0) and np.any(flows > 0)):
        return None

    non_zero_signs = np.sign(flows[flows != 0])
    sign_changes = int(np.sum(non_zero_signs[1:] != non_zero_signs[:-1]))
    if sign_changes == 1:
        left, right = -0.9999, 1.0
        left_value, right_value = npv(left, flows), npv(right, flows)
        while left_value * right_value > 0 and right < 1000:
            right = right * 2 + 1
            right_value = npv(right, flows)
        if left_value * right_value < 0:
            return float(_solve_root(lambda rate: npv(rate, flows), left, right))
        return None

    # Scan a wide range to find NPV sign changes, then select the lowest
    # non-negative root. This is more transparent than silently returning a
    # potentially misleading result for non-conventional cash flows.
    grid = np.concatenate(
        [
            np.linspace(-0.9999, 1.0, 1000),
            np.geomspace(2.01, 1000.0, 500) - 1,
        ]
    )
    values = np.array([npv(rate, flows) for rate in grid])
    roots: list[float] = []
    for left, right, left_value, right_value in zip(
        grid[:-1], grid[1:], values[:-1], values[1:]
    ):
        if left_value == 0:
            roots.append(float(left))
        elif left_value * right_value < 0:
            root = _solve_root(lambda rate: npv(rate, flows), left, right)
            roots.append(float(root))

    if not roots:
        return None
    non_negative = [root for root in roots if root >= 0]
    return min(non_negative) if non_negative else max(roots)


def _solve_root(function, left: float, right: float) -> float:
    if brentq is not None:
        return float(brentq(function, left, right))
    return _bisect_root(function, left, right)


def _bisect_root(function, left: float, right: float, tolerance: float = 1e-10) -> float:
    """Small fallback used only when SciPy is unavailable."""

    left_value = function(left)
    for _ in range(200):
        midpoint = (left + right) / 2
        midpoint_value = function(midpoint)
        if abs(midpoint_value) < tolerance or abs(right - left) < tolerance:
            return midpoint
        if left_value * midpoint_value <= 0:
            right = midpoint
        else:
            left = midpoint
            left_value = midpoint_value
    return (left + right) / 2


def mirr(
    cash_flows: Iterable[float], finance_rate: float, reinvestment_rate: float
) -> float | None:
    """Return modified IRR using separate financing and reinvestment rates."""

    flows = _cash_flows(cash_flows)
    if finance_rate <= -1 or reinvestment_rate <= -1:
        raise ValueError("Finance and reinvestment rates must be greater than -100%.")
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


def payback_period(cash_flows: Iterable[float], discount_rate: float | None = None) -> float | None:
    """Return fractional payback period, optionally on discounted cash flows."""

    flows = _cash_flows(cash_flows)
    if discount_rate is not None:
        if discount_rate <= -1:
            raise ValueError("Discount rate must be greater than -100%.")
        flows = flows / (1 + discount_rate) ** np.arange(flows.size)

    cumulative = np.cumsum(flows)
    if cumulative[0] >= 0:
        return 0.0
    for period in range(1, flows.size):
        if cumulative[period] >= 0:
            previous_deficit = abs(cumulative[period - 1])
            period_flow = flows[period]
            if period_flow <= 0:
                return float(period)
            return float(period - 1 + previous_deficit / period_flow)
    return None


def profitability_index(cash_flows: Iterable[float], discount_rate: float) -> float | None:
    """Return PV of future cash flows divided by the absolute time-zero outlay."""

    flows = _cash_flows(cash_flows)
    initial_outlay = abs(min(flows[0], 0))
    if initial_outlay == 0:
        return None
    future_pv = npv(discount_rate, [0.0, *flows[1:]])
    return float(future_pv / initial_outlay)


def calculate_metrics(
    cash_flows: Iterable[float],
    discount_rate: float,
    hurdle_rate: float,
    cost_of_capital: float,
    finance_rate: float,
    reinvestment_rate: float,
) -> FinancialMetrics:
    """Calculate the full investment decision metric set."""

    flows = _cash_flows(cash_flows)
    initial_investment = abs(min(float(flows[0]), 0))
    project_irr = irr(flows)
    project_npv = npv(discount_rate, flows)
    return FinancialMetrics(
        initial_investment=initial_investment,
        total_inflows=float(np.sum(flows[flows > 0])),
        net_cash_flow=float(np.sum(flows)),
        irr=project_irr,
        npv=project_npv,
        mirr=mirr(flows, finance_rate, reinvestment_rate),
        profitability_index=profitability_index(flows, discount_rate),
        payback_period=payback_period(flows),
        discounted_payback_period=payback_period(flows, discount_rate),
        discount_rate=discount_rate,
        hurdle_rate=hurdle_rate,
        cost_of_capital=cost_of_capital,
        irr_spread_to_hurdle=None if project_irr is None else project_irr - hurdle_rate,
        npv_to_investment=None if initial_investment == 0 else project_npv / initial_investment,
    )
