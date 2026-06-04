"""IRR Analytics Terminal Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from irr_terminal.calculations import calculate_metrics  # noqa: E402
from irr_terminal.cashflows import discounted_cash_flow_frame, parse_uploaded_file  # noqa: E402
from irr_terminal.comparison import compare_projects  # noqa: E402
from irr_terminal.examples import EXAMPLES, example_frame  # noqa: E402
from irr_terminal.export import build_excel_workbook  # noqa: E402
from irr_terminal.scenarios import probability_weighted_npv, scenario_analysis  # noqa: E402
from irr_terminal.sensitivity import npv_profile, sensitivity_table  # noqa: E402
from irr_terminal.utils import (  # noqa: E402
    format_currency,
    format_multiple,
    format_percent,
    format_years,
)
from irr_terminal.visualization import (  # noqa: E402
    cash_flow_timeline,
    cumulative_chart,
    npv_profile_chart,
    ranking_chart,
    scenario_chart,
    sensitivity_heatmap,
)

st.set_page_config(page_title="IRR Analytics Terminal", page_icon="$", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #08111f; color: #dbe7f3; }
    [data-testid="stSidebar"] { background-color: #0b1726; border-right: 1px solid #1d3048; }
    h1, h2, h3 { color: #f3f8fc; letter-spacing: -0.02em; }
    .metric-card { background: #101c2c; border: 1px solid #1d3048; border-radius: 6px;
      padding: 0.9rem; min-height: 104px; }
    .metric-label { color: #8fa5bd; font-size: 0.72rem; font-weight: 700;
      letter-spacing: 0.08em; text-transform: uppercase; }
    .metric-value { color: #f3f8fc; font-size: 1.45rem; font-weight: 700; margin-top: 0.35rem; }
    .metric-note { color: #617b97; font-size: 0.75rem; margin-top: 0.15rem; }
    .terminal-note { background: #101c2c; border-left: 3px solid #28d7e5;
      padding: 0.8rem 1rem; border-radius: 4px; }
    div[data-testid="stDataFrame"] { border: 1px solid #1d3048; border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    if "cash_flow_frame" not in st.session_state:
        st.session_state.cash_flow_frame = example_frame("Corporate Expansion Project")
    st.session_state.setdefault("project_name", "Corporate Expansion Project")
    st.session_state.setdefault("discount_rate", 0.10)
    st.session_state.setdefault("hurdle_rate", 0.10)


initialize_state()

st.sidebar.title("IRR Analytics Terminal")
st.sidebar.caption("Capital budgeting and investment cash-flow analysis")
st.sidebar.number_input("Discount Rate", 0.0, 1.0, key="discount_rate", step=0.005, format="%.3f")
st.sidebar.number_input("Hurdle Rate", 0.0, 1.0, key="hurdle_rate", step=0.005, format="%.3f")
st.sidebar.caption("Rates are decimals. Example: 0.10 = 10%.")

frame = st.session_state.cash_flow_frame
flows = frame["Cash Flow"].astype(float).tolist()
metrics = calculate_metrics(flows, st.session_state.discount_rate, st.session_state.hurdle_rate)
cash_flow_analysis = discounted_cash_flow_frame(flows, st.session_state.discount_rate)
profile = npv_profile(flows)
scenarios = scenario_analysis(flows, st.session_state.discount_rate, st.session_state.hurdle_rate)
growth_rates = [-0.10, -0.05, 0.0, 0.05, 0.10]
discount_rates = [
    max(st.session_state.discount_rate + change, 0.0)
    for change in [-0.04, -0.02, 0.0, 0.02, 0.04]
]
sensitivity = sensitivity_table(flows, discount_rates, growth_rates)
comparison = compare_projects(
    EXAMPLES, st.session_state.discount_rate, st.session_state.hurdle_rate
)

st.title("IRR Analytics Terminal")
st.caption(
    "A decision-oriented Streamlit dashboard for investment cash flows, value creation, "
    "return thresholds, timing, scenarios, and project comparisons."
)

tabs = st.tabs(
    [
        "Executive Dashboard",
        "Cash Flow Builder",
        "IRR / NPV Analysis",
        "Scenario Analysis",
        "Sensitivity Analysis",
        "Multi-Project Comparison",
        "Export / Investment Memo",
        "Methodology",
    ]
)

with tabs[0]:
    st.subheader(st.session_state.project_name)
    row_one = st.columns(5)
    cards = [
        ("Initial Investment", format_currency(metrics.initial_investment), "Time-zero outlay"),
        ("Total Cash Inflows", format_currency(metrics.total_cash_inflows), "Gross inflows"),
        ("Net Cash Flow", format_currency(metrics.net_cash_flow), "Undiscounted total"),
        ("IRR", format_percent(metrics.irr), metrics.irr_status),
        ("MIRR", format_percent(metrics.mirr), "Reinvestment-aware return"),
    ]
    for column, card in zip(row_one, cards):
        with column:
            metric_card(*card)
    row_two = st.columns(5)
    cards = [
        ("NPV", format_currency(metrics.npv), f"At {metrics.hurdle_rate:.1%} hurdle"),
        ("Payback Period", format_years(metrics.payback_period), "Undiscounted"),
        (
            "Discounted Payback",
            format_years(metrics.discounted_payback_period),
            "Time value included",
        ),
        (
            "Profitability Index",
            format_multiple(metrics.profitability_index),
            "PV inflows / outlay",
        ),
        ("Decision Status", metrics.decision_status, "Neutral finance screen"),
    ]
    for column, card in zip(row_two, cards):
        with column:
            metric_card(*card)
    if metrics.irr_warning:
        st.warning(metrics.irr_warning)
    chart_col, table_col = st.columns([1.5, 1])
    with chart_col:
        st.plotly_chart(cash_flow_timeline(cash_flow_analysis), use_container_width=True)
    with table_col:
        st.dataframe(cash_flow_analysis, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Cash Flow Builder")
    example_name = st.selectbox(
        "Built-in example",
        list(EXAMPLES),
        index=list(EXAMPLES).index(st.session_state.project_name),
    )
    if st.button("Load selected example"):
        st.session_state.project_name = example_name
        st.session_state.cash_flow_frame = example_frame(example_name)
        st.rerun()
    upload = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if upload is not None:
        try:
            uploaded = parse_uploaded_file(upload.name, upload.getvalue())
            if st.button("Use uploaded cash flows"):
                st.session_state.project_name = str(uploaded["Project"].iloc[0])
                st.session_state.cash_flow_frame = uploaded
                st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    edited = st.data_editor(frame, num_rows="dynamic", use_container_width=True)
    if st.button("Apply manual edits"):
        edited["Cash Flow"] = pd.to_numeric(edited["Cash Flow"], errors="raise")
        st.session_state.cash_flow_frame = edited
        st.rerun()

with tabs[2]:
    st.subheader("IRR / NPV Analysis")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(cumulative_chart(cash_flow_analysis), use_container_width=True)
    with right:
        st.plotly_chart(
            cumulative_chart(cash_flow_analysis, discounted=True),
            use_container_width=True,
        )
    st.plotly_chart(npv_profile_chart(profile, flows), use_container_width=True)
    st.info(
        "NPV is usually the stronger measure of absolute value creation. IRR can favor "
        "smaller or faster-paying projects and may be unreliable for non-conventional cash flows."
    )

with tabs[3]:
    st.subheader("Scenario Analysis")
    probabilities = st.columns(3)
    bear = probabilities[0].number_input("Bear Probability", 0.0, 1.0, 0.25, 0.05)
    base = probabilities[1].number_input("Base Probability", 0.0, 1.0, 0.50, 0.05)
    bull = probabilities[2].number_input("Bull Probability", 0.0, 1.0, 0.25, 0.05)
    scenarios = scenario_analysis(
        flows, st.session_state.discount_rate, st.session_state.hurdle_rate, [bear, base, bull]
    )
    if abs(bear + base + bull - 1.0) > 1e-6:
        st.warning("Probabilities were normalized because they did not sum to 100%.")
    metric_card("Probability-Weighted NPV", format_currency(probability_weighted_npv(scenarios)))
    st.plotly_chart(scenario_chart(scenarios), use_container_width=True)
    st.dataframe(scenarios, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Sensitivity Analysis")
    st.plotly_chart(sensitivity_heatmap(sensitivity), use_container_width=True)
    st.dataframe(sensitivity, use_container_width=True)

with tabs[5]:
    st.subheader("Multi-Project Comparison")
    st.info(
        "The ranking is not based on IRR alone. It balances NPV, hurdle-rate performance, "
        "discounted payback, profitability index, and scale of value creation."
    )
    st.plotly_chart(ranking_chart(comparison), use_container_width=True)
    st.dataframe(comparison, use_container_width=True, hide_index=True)

with tabs[6]:
    st.subheader("Export / Investment Memo")
    workbook = build_excel_workbook(
        st.session_state.project_name,
        cash_flow_analysis,
        metrics,
        profile,
        scenarios,
        sensitivity,
        comparison,
        st.session_state.discount_rate,
        st.session_state.hurdle_rate,
    )
    st.download_button(
        "Download formatted Excel workbook",
        workbook,
        file_name="irr_analytics_terminal.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.markdown(
        '<div class="terminal-note">The workbook includes summary, cash flows, metrics, '
        "NPV profile, scenarios, sensitivity, project comparison, and assumptions.</div>",
        unsafe_allow_html=True,
    )

with tabs[7]:
    st.subheader("Methodology")
    st.markdown(
        """
        **IRR** is the discount rate that sets NPV to zero. It is useful for comparing a
        project's return with a hurdle rate, but it can be misleading when cash-flow signs
        change multiple times, when projects differ in scale, or when timing differs materially.

        **NPV** measures absolute value creation at the selected discount rate and is usually
        the preferred decision measure for mutually exclusive projects.

        **MIRR** addresses some IRR reinvestment-assumption problems by applying explicit
        finance and reinvestment rates.

        **Payback period** is a liquidity measure. It ignores value created after the
        payback date, while discounted payback includes the time value of money but still
        ignores later value.
        """
    )
