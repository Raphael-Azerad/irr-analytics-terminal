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
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font={"color": TEXT, "family": "Inter, Arial, sans-serif"},
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        hoverlabel={"bgcolor": PANEL, "font_color": TEXT},
        title={"text": title, "x": 0.02, "xanchor": "left"},
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
            hovertemplate="Period %{x}<br>Cash Flow: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    fig.update_xaxes(title="Period")
    fig.update_yaxes(title="Cash Flow", tickprefix="$", tickformat=",.0f")
    return style_figure(fig, "Cash Flow Timeline")


def cumulative_chart(frame: pd.DataFrame, discounted: bool = False) -> go.Figure:
    column = "Discounted Cumulative Cash Flow" if discounted else "Cumulative Cash Flow"
    fig = go.Figure(
        go.Scatter(
            x=frame["Period"],
            y=frame[column],
            mode="lines+markers",
            line={"color": GOLD if discounted else CYAN, "width": 3},
            hovertemplate="Period %{x}<br>Cumulative: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    fig.update_xaxes(title="Period")
    fig.update_yaxes(title="Cumulative Cash Flow", tickprefix="$", tickformat=",.0f")
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
            hovertemplate="Discount Rate: %{x:.1%}<br>NPV: $%{y:,.0f}<extra></extra>",
        )
    )
    project_irr = irr(cash_flows)
    if project_irr is not None and 0 <= project_irr <= 0.30:
        fig.add_vline(
            x=project_irr,
            line_dash="dot",
            line_color=GOLD,
            annotation_text=f"IRR {project_irr:.1%}",
            annotation_font_color=GOLD,
        )
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    fig.update_xaxes(title="Discount Rate", tickformat=".0%")
    fig.update_yaxes(title="Net Present Value", tickprefix="$", tickformat=",.0f")
    return style_figure(fig, "NPV Profile")


def sensitivity_heatmap(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            z=frame.to_numpy(),
            x=frame.columns,
            y=frame.index,
            colorscale=[[0, RED], [0.5, PANEL], [1, GREEN]],
            colorbar={"title": "NPV"},
            hovertemplate="Growth: %{x}<br>Discount Rate: %{y}<br>NPV: $%{z:,.0f}<extra></extra>",
        )
    )
    return style_figure(fig, "NPV Sensitivity: Discount Rate vs. Cash-Flow Growth")


def scenario_chart(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=frame["Scenario"],
            y=frame["NPV"],
            marker_color=[RED, CYAN, GREEN],
            hovertemplate="%{x}<br>NPV: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Scenario")
    fig.update_yaxes(title="Net Present Value", tickprefix="$", tickformat=",.0f")
    return style_figure(fig, "Scenario NPV Comparison")


def ranking_chart(frame: pd.DataFrame) -> go.Figure:
    plot_frame = frame.sort_values("Score")
    fig = go.Figure(
        go.Bar(
            x=plot_frame["Score"],
            y=plot_frame["Project Name"],
            orientation="h",
            marker_color=CYAN,
            hovertemplate="%{y}<br>Balanced Score: %{x:.1f}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Balanced Score")
    fig.update_yaxes(title="")
    return style_figure(fig, "Balanced Multi-Project Ranking")
