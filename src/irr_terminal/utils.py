"""Formatting helpers."""


def format_currency(value: float | None) -> str:
    return "N/A" if value is None else f"${value:,.0f}"


def format_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2%}"


def format_years(value: float | None) -> str:
    return "No payback" if value is None else f"{value:.2f} years"


def format_multiple(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}x"
