"""Cash-flow input normalization for manual, CSV, and Excel workflows."""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from .exceptions import UploadError


PERIOD_COLUMNS = {"period", "year", "date"}
CASH_FLOW_COLUMNS = {"cash_flow", "cashflow", "cf", "amount", "value"}
PROJECT_COLUMNS = {"project", "project_name"}


def _column_key(value: object) -> str:
    return str(value).strip().lower().replace(" ", "_")


def normalize_cash_flow_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize uploaded or manually edited cash flows into the app's standard schema."""
    if frame.empty:
        raise UploadError("The cash-flow file is empty.")
    normalized = frame.copy()
    normalized.columns = [_column_key(column) for column in normalized.columns]
    cash_column = next((c for c in normalized.columns if c in CASH_FLOW_COLUMNS), None)
    period_column = next((c for c in normalized.columns if c in PERIOD_COLUMNS), None)
    project_column = next((c for c in normalized.columns if c in PROJECT_COLUMNS), None)
    if cash_column is None:
        raise UploadError("Include a Cash Flow, CashFlow, CF, Amount, or Value column.")
    values = pd.to_numeric(normalized[cash_column], errors="coerce")
    if values.isna().any():
        raise UploadError("Cash flows must be numeric and cannot contain blank values.")
    if len(values) < 2:
        raise UploadError("At least two cash-flow periods are required.")
    result = pd.DataFrame(
        {
            "Project": (
                normalized[project_column].fillna("Current Project").astype(str)
                if project_column
                else pd.Series(["Current Project"] * len(values))
            ),
            "Period": (
                normalized[period_column].tolist()
                if period_column
                else list(range(len(values)))
            ),
            "Cash Flow": values.astype(float),
        }
    )
    return result


def parse_uploaded_file(file_name: str, content: bytes) -> pd.DataFrame:
    buffer = BytesIO(content)
    try:
        if file_name.lower().endswith(".csv"):
            frame = pd.read_csv(buffer)
        elif file_name.lower().endswith(".xlsx"):
            frame = pd.read_excel(buffer)
        else:
            raise UploadError("Only .csv and .xlsx files are supported.")
    except UploadError:
        raise
    except Exception as exc:
        raise UploadError("The uploaded file could not be read.") from exc
    return normalize_cash_flow_frame(frame)


def discounted_cash_flow_frame(cash_flows: list[float], discount_rate: float) -> pd.DataFrame:
    frame = pd.DataFrame({"Period": range(len(cash_flows)), "Cash Flow": cash_flows})
    frame["Cumulative Cash Flow"] = frame["Cash Flow"].cumsum()
    frame["Discounted Cash Flow"] = frame["Cash Flow"] / (
        (1 + discount_rate) ** frame["Period"]
    )
    frame["Discounted Cumulative Cash Flow"] = frame["Discounted Cash Flow"].cumsum()
    return frame
