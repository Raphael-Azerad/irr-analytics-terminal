"""Tests for scenario analysis."""

import pytest

from irr_terminal.scenarios import apply_scenario, probability_weighted_npv, scenario_analysis


def test_scenario_calculations() -> None:
    frame = scenario_analysis([-1000, 400, 500, 600], 0.10, 0.10)
    assert frame["Scenario"].tolist() == ["Bear", "Base", "Bull"]
    assert frame.loc[2, "NPV"] > frame.loc[0, "NPV"]


def test_scenario_adjusts_future_positive_cash_flows_only() -> None:
    assert apply_scenario([-100, 50, -20, 60], 0.8) == [-100, 40, -20, 48]


def test_probability_weighted_npv_normalizes_probabilities() -> None:
    frame = scenario_analysis([-1000, 400, 500, 600], 0.10, 0.10, [1, 2, 1])
    assert frame["Probability"].sum() == pytest.approx(1.0)
    assert probability_weighted_npv(frame) == pytest.approx(
        sum(frame["Probability"] * frame["NPV"])
    )
