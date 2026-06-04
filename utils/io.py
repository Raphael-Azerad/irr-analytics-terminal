"""File parsing and cash-flow validation."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def validate_cash_flow_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize an uploaded or edited cash-flow data frame."""

    if frame.empty:
        raise ValueError("The cash-flow file is empty.")

    normalized = frame.copy()
    normalized.columns = [str(column).strip().lower().replace(" ", "_") for column in normalized.columns]
    cash_column = next(
        (column for column in normalized.columns if column in {"cash_flow", "cashflow", "amount", "value"}),
        None,
    )
    if cash_column is None:
        if normalized.shape[1] == 1:
            cash_column = normalized.columns[0]
        else:
            raise ValueError("Include a 'Cash Flow' column in the uploaded file.")

    values = pd.to_numeric(normalized[cash_column], errors="coerce")
    if values.isna().any():
        raise ValueError("Cash flows must be numeric and cannot contain blank values.")
    if len(values) < 2:
        raise ValueError("At least two cash-flow periods are required.")
    if not (values.lt(0).any() and values.gt(0).any()):
        raise ValueError("Cash flows must include at least one outflow and one inflow.")

    result_data: dict[str, object] = {
        "Period": list(range(len(values))),
        "Cash Flow": values.astype(float).tolist(),
    }
    date_column = next(
        (column for column in normalized.columns if column in {"date", "cash_flow_date", "cashflow_date"}),
        None,
    )
    if date_column is not None:
        dates = pd.to_datetime(normalized[date_column], errors="coerce")
        if dates.isna().any():
            raise ValueError("Cash-flow dates must be valid date values.")
        if not dates.is_monotonic_increasing or dates.duplicated().any():
            raise ValueError("Cash-flow dates must be strictly increasing.")
        result_data["Date"] = dates.dt.date.tolist()

    result = pd.DataFrame(result_data)
    return result


def parse_uploaded_file(file_name: str, content: bytes) -> pd.DataFrame:
    """Parse CSV or Excel cash flows into the standard application format."""

    buffer = BytesIO(content)
    if file_name.lower().endswith(".csv"):
        frame = pd.read_csv(buffer)
    elif file_name.lower().endswith(".xlsx"):
        frame = pd.read_excel(buffer)
    else:
        raise ValueError("Only .csv and .xlsx files are supported.")
    return validate_cash_flow_frame(frame)
