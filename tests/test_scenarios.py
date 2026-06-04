"""Tests for scenario, simulation, and specialized analysis."""

import pytest

from calculations.monte_carlo import run_monte_carlo
from calculations.recommendation import generate_recommendation
from calculations.scenarios import scenario_table
from calculations.specialized import analyze_real_estate, analyze_sponsor_returns
from calculations.metrics import calculate_metrics


FLOWS = [-1_000_000, 250_000, 300_000, 350_000, 450_000]


def test_scenario_table_contains_bear_base_bull() -> None:
    frame = scenario_table(FLOWS, 0.10, 0.12, 0.09, 0.08, 0.08)
    assert frame["Scenario"].tolist() == ["Bear", "Base", "Bull"]
    assert frame.loc[2, "NPV"] > frame.loc[0, "NPV"]


def test_monte_carlo_is_reproducible() -> None:
    first = run_monte_carlo(FLOWS, 0.10, 0.12, simulations=200, seed=7)
    second = run_monte_carlo(FLOWS, 0.10, 0.12, simulations=200, seed=7)
    assert first.simulations["NPV"].tolist() == second.simulations["NPV"].tolist()
    assert first.npv_conditional_value_at_risk_5 <= first.npv_value_at_risk_5


def test_positive_project_receives_positive_recommendation() -> None:
    metrics = calculate_metrics(FLOWS, 0.08, 0.10, 0.08, 0.08, 0.08)
    recommendation = generate_recommendation(metrics)
    assert recommendation.rating in {"Strong Buy", "Consider"}


def test_negative_bear_case_reduces_recommendation_score() -> None:
    metrics = calculate_metrics(FLOWS, 0.08, 0.10, 0.08, 0.08, 0.08)
    base = generate_recommendation(metrics)
    downside = generate_recommendation(metrics, bear_case_npv=-100_000)
    assert downside.score == base.score - 1


def test_real_estate_equity_multiple() -> None:
    analysis = analyze_real_estate(1_000_000, 150_000, 50_000, 1_200_000, 5, 0.10)
    assert analysis.equity_multiple == pytest.approx(1.7)


def test_sponsor_money_on_money() -> None:
    analysis = analyze_sponsor_returns(1_000_000, 100_000, 1_500_000, 5, 0.20)
    assert analysis.money_on_money == pytest.approx(2.0)
