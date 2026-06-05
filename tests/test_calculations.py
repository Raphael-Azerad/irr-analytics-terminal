"""Tests for core finance calculations."""

import pytest

from irr_terminal.calculations import (
    analyze_irr,
    calculate_metrics,
    irr,
    mirr,
    npv,
    payback_period,
    profitability_index,
)

FLOWS = [-1000, 300, 400, 500]
CORPORATE_EXPANSION_FLOWS = [
    -10_000_000,
    1_800_000,
    2_200_000,
    2_600_000,
    3_000_000,
    3_400_000,
    3_800_000,
]


def test_npv_calculation() -> None:
    assert npv(0.0, FLOWS) == pytest.approx(200.0)


def test_irr_calculation() -> None:
    result = irr(FLOWS)
    assert result is not None
    assert npv(result, FLOWS) == pytest.approx(0.0, abs=1e-6)


def test_irr_for_normal_investment_cash_flows() -> None:
    result = irr(CORPORATE_EXPANSION_FLOWS)
    assert result == pytest.approx(0.1496, abs=0.0001)


def test_mirr_calculation() -> None:
    assert mirr(FLOWS, 0.08, 0.08) == pytest.approx(0.0863, abs=0.001)


def test_payback_period() -> None:
    assert payback_period(FLOWS) == pytest.approx(2.6)


def test_discounted_payback_period() -> None:
    assert payback_period(FLOWS, 0.25) is None


def test_profitability_index() -> None:
    assert profitability_index(FLOWS, 0.10) == pytest.approx(0.9790, abs=0.001)


def test_non_conventional_cash_flow_detection() -> None:
    result = analyze_irr([-100, 230, -132])
    assert result.sign_changes == 2
    assert result.status == "Review cash-flow pattern"
    assert len(result.roots) == 2


def test_all_positive_cash_flows_have_no_irr() -> None:
    assert analyze_irr([100, 200]).status == "No valid IRR"


def test_all_negative_cash_flows_have_no_irr() -> None:
    assert analyze_irr([-100, -200]).status == "No valid IRR"


def test_no_payback_case() -> None:
    assert payback_period([-1000, 100, 100]) is None


def test_metrics_use_neutral_decision_language() -> None:
    status = calculate_metrics(FLOWS, 0.10, 0.10).decision_status
    assert status in {
        "Passes hurdle rate",
        "Positive NPV",
        "Mixed result",
        "Fails hurdle rate",
        "No valid IRR",
        "Review cash-flow pattern",
    }
