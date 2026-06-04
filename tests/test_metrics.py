"""Tests for the capital budgeting engine."""

import pytest

from calculations.metrics import (
    calculate_metrics,
    irr,
    mirr,
    npv,
    payback_period,
    profitability_index,
    xirr,
    xnpv,
)


FLOWS = [-1000, 300, 400, 500]


def test_npv_at_zero_rate_equals_net_cash_flow() -> None:
    assert npv(0.0, FLOWS) == pytest.approx(200.0)


def test_irr_sets_npv_to_zero() -> None:
    project_irr = irr(FLOWS)
    assert project_irr is not None
    assert npv(project_irr, FLOWS) == pytest.approx(0.0, abs=1e-6)


def test_mirr_uses_finance_and_reinvestment_rates() -> None:
    project_mirr = mirr(FLOWS, 0.08, 0.08)
    assert project_mirr == pytest.approx(0.0863, abs=0.001)


def test_payback_period_is_fractional() -> None:
    assert payback_period(FLOWS) == pytest.approx(2.6)


def test_discounted_payback_can_be_unachieved() -> None:
    assert payback_period(FLOWS, 0.25) is None


def test_profitability_index() -> None:
    assert profitability_index(FLOWS, 0.10) == pytest.approx(0.9790, abs=0.001)


def test_complete_metric_set() -> None:
    metrics = calculate_metrics(FLOWS, 0.10, 0.12, 0.09, 0.08, 0.08)
    assert metrics.initial_investment == 1000
    assert metrics.total_inflows == 1200
    assert metrics.npv < 0
    assert metrics.irr is not None
    assert metrics.irr_spread_to_hurdle == pytest.approx(metrics.irr - 0.12)
    assert metrics.npv_to_investment == pytest.approx(metrics.npv / 1000)


def test_invalid_cash_flows_are_rejected() -> None:
    with pytest.raises(ValueError):
        npv(0.10, [100])


def test_xnpv_matches_npv_for_annual_dates() -> None:
    dates = ["2026-01-01", "2027-01-01", "2028-01-01", "2029-01-01"]
    assert xnpv(0.10, FLOWS, dates) == pytest.approx(npv(0.10, FLOWS), abs=0.20)


def test_xirr_sets_xnpv_to_zero() -> None:
    dates = ["2026-01-01", "2026-07-01", "2027-02-15", "2028-01-01"]
    project_xirr = xirr(FLOWS, dates)
    assert project_xirr is not None
    assert xnpv(project_xirr, FLOWS, dates) == pytest.approx(0.0, abs=1e-6)


def test_xirr_rejects_non_increasing_dates() -> None:
    with pytest.raises(ValueError):
        xirr(FLOWS, ["2026-01-01", "2026-01-01", "2027-01-01", "2028-01-01"])
