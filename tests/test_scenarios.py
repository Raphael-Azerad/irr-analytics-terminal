"""Tests for scenario analysis."""

import pytest

from irr_terminal.scenarios import probability_weighted_npv, scenario_analysis


def test_scenario_calculations() -> None:
    frame = scenario_analysis([-1000, 400, 500, 600], 0.10, 0.10)
    assert frame["Scenario"].tolist() == ["Bear", "Base", "Bull"]
    assert frame.loc[2, "NPV"] > frame.loc[0, "NPV"]


def test_probability_weighted_npv_normalizes_probabilities() -> None:
    frame = scenario_analysis([-1000, 400, 500, 600], 0.10, 0.10, [1, 2, 1])
    assert frame["Probability"].sum() == pytest.approx(1.0)
    assert probability_weighted_npv(frame) == pytest.approx(
        sum(frame["Probability"] * frame["NPV"])
    )
