"""Tests for uploaded cash-flow model normalization."""

import pandas as pd
import pytest

from utils.io import validate_cash_flow_frame


def test_validation_preserves_valid_dates() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2026-01-01", "2026-08-01", "2027-05-01"],
            "Cash Flow": [-1000, 400, 800],
        }
    )
    result = validate_cash_flow_frame(frame)
    assert result.columns.tolist() == ["Period", "Cash Flow", "Date"]
    assert str(result.loc[0, "Date"]) == "2026-01-01"


def test_validation_rejects_duplicate_dates() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2026-01-01", "2026-01-01"],
            "Cash Flow": [-1000, 1200],
        }
    )
    with pytest.raises(ValueError):
        validate_cash_flow_frame(frame)
