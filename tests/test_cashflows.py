"""Tests for cash-flow parsing."""

import pandas as pd
import pytest

from irr_terminal.cashflows import normalize_cash_flow_frame, parse_uploaded_file
from irr_terminal.exceptions import UploadError


def test_flexible_csv_columns() -> None:
    frame = pd.DataFrame({"Project Name": ["A", "A"], "Year": [0, 1], "CF": [-100, 120]})
    result = normalize_cash_flow_frame(frame)
    assert result.columns.tolist() == ["Project", "Period", "Cash Flow"]


def test_amount_column_is_supported() -> None:
    frame = pd.DataFrame({"Project": ["A", "A"], "Period": [0, 1], "Amount": [-100, 120]})
    result = normalize_cash_flow_frame(frame)
    assert result["Cash Flow"].tolist() == [-100.0, 120.0]


def test_csv_parsing() -> None:
    content = b"Project,Period,Cash Flow\nA,0,-100\nA,1,120\n"
    assert parse_uploaded_file("model.csv", content)["Cash Flow"].tolist() == [-100.0, 120.0]


def test_invalid_upload_handling() -> None:
    with pytest.raises(UploadError):
        parse_uploaded_file("model.txt", b"nope")
