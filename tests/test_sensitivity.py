"""Tests for sensitivity analysis."""

from irr_terminal.sensitivity import npv_profile, sensitivity_table


def test_npv_profile() -> None:
    frame = npv_profile([-1000, 400, 500, 600])
    assert frame.iloc[0]["NPV"] == 500
    assert frame.iloc[-1]["Discount Rate"] == 0.30


def test_sensitivity_table_shape() -> None:
    frame = sensitivity_table([-1000, 400, 500, 600], [0.08, 0.10], [-0.05, 0.05])
    assert frame.shape == (2, 2)
