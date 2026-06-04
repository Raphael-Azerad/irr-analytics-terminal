"""Institutional-style Plotly charts for investment analysis."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from calculations.metrics import irr, npv


NAVY = "#08111f"
PANEL = "#101c2c"
GRID = "#26364d"
TEXT = "#dbe7f3"
MUTED = "#8fa5bd"
CYAN = "#28d7e5"
GREEN = "#3ddc97"
RED = "#ff6b6b"
GOLD = "#f4c95d"


def _style(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font={"color": TEXT, "family": "Inter, Arial, sans-serif"},
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        legend={"orientation": "h", "y": 1.08, "x": 0},
        hoverlabel={"bgcolor": PANEL, "font_color": TEXT},
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def cash_flow_waterfall(cash_flows: Iterable[float]) -> go.Figure:
    flows = np.asarray(list(cash_flows), dtype=float)
    labels = [f"Year {period}" for period in range(len(flows))]
    cumulative = np.cumsum(flows)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=flows,
            name="Periodic Cash Flow",
            marker_color=[RED if value < 0 else CYAN for value in flows],
            hovertemplate="%{x}<br>Cash Flow: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=cumulative,
            name="Cumulative Cash Flow",
            mode="lines+markers",
            line={"color": GOLD, "width": 3},
            hovertemplate="%{x}<br>Cumulative: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    return _style(fig, "Cash Flow Waterfall and Break-Even Path")


def npv_profile(cash_flows: Iterable[float], max_rate: float = 0.25) -> go.Figure:
    flows = list(cash_flows)
    rates = np.linspace(0, max_rate, 101)
    values = [npv(rate, flows) for rate in rates]
    project_irr = irr(flows)
    fig = go.Figure(
        go.Scatter(
            x=rates,
            y=values,
            mode="lines",
            fill="tozeroy",
            line={"color": CYAN, "width": 3},
            fillcolor="rgba(40, 215, 229, 0.12)",
            name="NPV",
            hovertemplate="Discount Rate: %{x:.1%}<br>NPV: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED)
    if project_irr is not None and 0 <= project_irr <= max_rate:
        fig.add_vline(
            x=project_irr,
            line_dash="dot",
            line_color=GOLD,
            annotation_text=f"IRR {project_irr:.1%}",
            annotation_font_color=GOLD,
        )
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return _style(fig, "NPV Profile")


def sensitivity_heatmap(frame: pd.DataFrame, title: str, value_format: str) -> go.Figure:
    values = frame.to_numpy(dtype=float)
    text = np.empty_like(values, dtype=object)
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = values[row, column]
            text[row, column] = "N/A" if np.isnan(value) else format(value, value_format)
    fig = go.Figure(
        go.Heatmap(
            z=values,
            x=frame.columns,
            y=frame.index,
            text=text,
            texttemplate="%{text}",
            colorscale=[[0, RED], [0.5, PANEL], [1, GREEN]],
            colorbar={"title": title.split()[0]},
            hovertemplate="X: %{x}<br>Y: %{y}<br>Value: %{text}<extra></extra>",
        )
    )
    return _style(fig, title)


def scenario_comparison(frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=frame["Scenario"],
            y=frame["NPV"],
            name="NPV",
            marker_color=GOLD,
            yaxis="y",
            hovertemplate="%{x}<br>NPV: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=frame["Scenario"],
            y=frame["IRR"],
            name="IRR",
            mode="lines+markers",
            line={"color": CYAN, "width": 3},
            marker={"size": 9},
            yaxis="y2",
            hovertemplate="%{x}<br>IRR: %{y:.2%}<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis={"title": "NPV", "tickprefix": "$", "tickformat": ",.0f"},
        yaxis2={
            "title": "IRR",
            "tickformat": ".0%",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
        },
    )
    return _style(fig, "Scenario Comparison")


def monte_carlo_histogram(frame: pd.DataFrame, metric: str) -> go.Figure:
    fig = px.histogram(
        frame,
        x=metric,
        nbins=60,
        opacity=0.85,
        color_discrete_sequence=[CYAN if metric == "IRR" else GOLD],
    )
    if metric == "IRR":
        fig.update_xaxes(tickformat=".0%")
    else:
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    return _style(fig, f"Monte Carlo {metric} Distribution")


def probability_curve(frame: pd.DataFrame, metric: str) -> go.Figure:
    values = np.sort(frame[metric].dropna().to_numpy())
    probabilities = 1 - np.arange(1, len(values) + 1) / len(values)
    fig = go.Figure(
        go.Scatter(
            x=values,
            y=probabilities,
            mode="lines",
            line={"color": GREEN, "width": 3},
            hovertemplate="Value: %{x}<br>Probability of Exceedance: %{y:.1%}<extra></extra>",
        )
    )
    fig.update_yaxes(tickformat=".0%")
    if metric == "IRR":
        fig.update_xaxes(tickformat=".0%")
    else:
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    return _style(fig, f"{metric} Probability of Exceedance")


def project_ranking(frame: pd.DataFrame) -> go.Figure:
    plot_frame = frame.sort_values("NPV", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=plot_frame["NPV"],
            y=plot_frame["Project"],
            orientation="h",
            marker_color=CYAN,
            text=plot_frame["Rank"].map(lambda value: f"Rank {value}"),
            textposition="outside",
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    return _style(fig, "Project Ranking by NPV")
