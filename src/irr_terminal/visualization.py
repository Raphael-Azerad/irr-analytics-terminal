"""Bloomberg-inspired Plotly visualizations."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .calculations import irr

NAVY = "#08111f"
PANEL = "#101c2c"
GRID = "#26364d"
TEXT = "#dbe7f3"
MUTED = "#8fa5bd"
CYAN = "#28d7e5"
GREEN = "#3ddc97"
RED = "#ff6b6b"
GOLD = "#f4c95d"


def style_figure(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font={"color": TEXT, "family": "Inter, Arial, sans-serif"},
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        hoverlabel={"bgcolor": PANEL, "font_color": TEXT},
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def cash_flow_timeline(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=frame["Period"],
            y=frame["Cash Flow"],
            marker_color=[RED if value < 0 else CYAN for value in frame["Cash Flow"]],
        )
    )
    return style_figure(fig, "Cash Flow Timeline")


def cumulative_chart(frame: pd.DataFrame, discounted: bool = False) -> go.Figure:
    column = "Discounted Cumulative Cash Flow" if discounted else "Cumulative Cash Flow"
    fig = go.Figure(
        go.Scatter(
            x=frame["Period"],
            y=frame[column],
            mode="lines+markers",
            line={"color": GOLD if discounted else CYAN, "width": 3},
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    return style_figure(fig, column)


def npv_profile_chart(profile: pd.DataFrame, cash_flows: list[float]) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=profile["Discount Rate"],
            y=profile["NPV"],
            mode="lines",
            fill="tozeroy",
            line={"color": CYAN, "width": 3},
            fillcolor="rgba(40, 215, 229, 0.12)",
        )
    )
    project_irr = irr(cash_flows)
    if project_irr is not None and 0 <= project_irr <= 0.30:
        fig.add_vline(x=project_irr, line_dash="dot", line_color=GOLD)
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return style_figure(fig, "NPV Profile")


def sensitivity_heatmap(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            z=frame.to_numpy(),
            x=frame.columns,
            y=frame.index,
            colorscale=[[0, RED], [0.5, PANEL], [1, GREEN]],
            colorbar={"title": "NPV"},
        )
    )
    return style_figure(fig, "NPV Sensitivity: Discount Rate vs. Cash-Flow Growth")


def scenario_chart(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(x=frame["Scenario"], y=frame["NPV"], marker_color=[RED, CYAN, GREEN]))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return style_figure(fig, "Scenario NPV Comparison")


def ranking_chart(frame: pd.DataFrame) -> go.Figure:
    plot_frame = frame.sort_values("Score")
    fig = go.Figure(
        go.Bar(
            x=plot_frame["Score"],
            y=plot_frame["Project Name"],
            orientation="h",
            marker_color=CYAN,
        )
    )
    return style_figure(fig, "Balanced Multi-Project Ranking")
