"""IRR Analytics Terminal Streamlit application."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from irr_terminal.calculations import calculate_metrics
from irr_terminal.cashflows import (
    discounted_cash_flow_frame,
    normalize_cash_flow_frame,
    parse_uploaded_file,
)
from irr_terminal.comparison import compare_projects
from irr_terminal.examples import EXAMPLES, example_frame
from irr_terminal.exceptions import UploadError
from irr_terminal.export import build_excel_workbook
from irr_terminal.scenarios import probability_weighted_npv, scenario_analysis
from irr_terminal.sensitivity import npv_profile, sensitivity_table
from irr_terminal.utils import (
    format_currency,
    format_multiple,
    format_percent,
    format_years,
)
from irr_terminal.visualization import (
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
    st.session_state.setdefault("discount_rate_percent", 10.00)
    st.session_state.setdefault("hurdle_rate_percent", 10.00)
    st.session_state.setdefault("finance_rate_percent", 10.00)
    st.session_state.setdefault("reinvestment_rate_percent", 10.00)


initialize_state()

st.sidebar.title("IRR Analytics Terminal")
st.sidebar.caption("Capital budgeting and investment cash-flow analysis")
st.sidebar.number_input(
    "Discount Rate (%)",
    min_value=0.0,
    max_value=100.0,
    key="discount_rate_percent",
    step=0.25,
    format="%.2f",
    help="Used to discount cash flows for NPV and discounted payback.",
)
st.sidebar.number_input(
    "Hurdle Rate (%)",
    min_value=0.0,
    max_value=100.0,
    key="hurdle_rate_percent",
    step=0.25,
    format="%.2f",
    help="Minimum acceptable return threshold for screening IRR and MIRR.",
)
with st.sidebar.expander("MIRR assumptions"):
    st.number_input(
        "Finance Rate (%)",
        min_value=0.0,
        max_value=100.0,
        key="finance_rate_percent",
        step=0.25,
        format="%.2f",
        help="Rate used to discount negative interim cash flows in MIRR.",
    )
    st.number_input(
        "Reinvestment Rate (%)",
        min_value=0.0,
        max_value=100.0,
        key="reinvestment_rate_percent",
        step=0.25,
        format="%.2f",
        help="Rate used to compound positive cash flows in MIRR.",
    )
st.sidebar.caption("Enter rates as percentages. Example: 10.00 means 10%.")

discount_rate = st.session_state.discount_rate_percent / 100
hurdle_rate = st.session_state.hurdle_rate_percent / 100
finance_rate = st.session_state.finance_rate_percent / 100
reinvestment_rate = st.session_state.reinvestment_rate_percent / 100

frame = st.session_state.cash_flow_frame
flows = frame["Cash Flow"].astype(float).tolist()
metrics = calculate_metrics(flows, discount_rate, hurdle_rate, finance_rate, reinvestment_rate)
cash_flow_analysis = discounted_cash_flow_frame(flows, discount_rate)
profile = npv_profile(flows)
scenarios = scenario_analysis(flows, discount_rate, hurdle_rate)
growth_rates = [-0.10, -0.05, 0.0, 0.05, 0.10]
discount_rates = [max(discount_rate + change, 0.0) for change in [-0.04, -0.02, 0.0, 0.02, 0.04]]
sensitivity = sensitivity_table(flows, discount_rates, growth_rates)
comparison = compare_projects(EXAMPLES, discount_rate, hurdle_rate)

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
        ("NPV", format_currency(metrics.npv), f"At {discount_rate:.1%} discount rate"),
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
        st.caption("Periodic cash flows by year. Negative bars represent investment outlays.")
    with table_col:
        st.dataframe(cash_flow_analysis, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Cash Flow Builder")
    st.info(
        "Year 0 is typically the initial investment and should usually be negative. "
        "Future periods represent expected cash inflows or outflows."
    )
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
            project_count = uploaded["Project"].nunique()
            if project_count > 1:
                selected_project = st.selectbox(
                    "Uploaded projects",
                    sorted(uploaded["Project"].unique()),
                    help="Choose which project to use for the main dashboard.",
                )
                uploaded = uploaded.loc[uploaded["Project"] == selected_project].reset_index(
                    drop=True
                )
            st.success("Upload parsed successfully. Review the preview before applying it.")
            st.dataframe(uploaded, use_container_width=True, hide_index=True)
            if st.button("Use uploaded cash flows"):
                st.session_state.project_name = str(uploaded["Project"].iloc[0])
                st.session_state.cash_flow_frame = uploaded
                st.rerun()
        except UploadError as exc:
            st.error(str(exc))
    edited = st.data_editor(frame, num_rows="dynamic", use_container_width=True)
    if st.button("Apply manual edits"):
        try:
            normalized = normalize_cash_flow_frame(edited)
            st.session_state.cash_flow_frame = normalized
            st.session_state.project_name = str(normalized["Project"].iloc[0])
            st.rerun()
        except UploadError as exc:
            st.error(str(exc))

with tabs[2]:
    st.subheader("IRR / NPV Analysis")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(cumulative_chart(cash_flow_analysis), use_container_width=True)
        st.caption("Undiscounted cumulative cash flow highlights simple break-even timing.")
    with right:
        st.plotly_chart(
            cumulative_chart(cash_flow_analysis, discounted=True),
            use_container_width=True,
        )
        st.caption("Discounted cumulative cash flow includes the time value of money.")
    st.plotly_chart(npv_profile_chart(profile, flows), use_container_width=True)
    st.caption(
        "The NPV profile shows value creation across discount rates. A valid IRR is the point "
        "where the line crosses zero."
    )
    st.info(
        "NPV is usually the stronger measure of absolute value creation. IRR can favor "
        "smaller or faster-paying projects and may be unreliable for non-conventional cash flows."
    )

with tabs[3]:
    st.subheader("Scenario Analysis")
    st.caption(
        "Bear lowers future positive cash flows by 15% and raises the discount rate by 2%. "
        "Bull raises future positive cash flows by 15% and lowers the discount rate by 1%."
    )
    probabilities = st.columns(3)
    bear_pct = probabilities[0].number_input("Bear Probability (%)", 0.0, 100.0, 25.0, 5.0)
    base_pct = probabilities[1].number_input("Base Probability (%)", 0.0, 100.0, 50.0, 5.0)
    bull_pct = probabilities[2].number_input("Bull Probability (%)", 0.0, 100.0, 25.0, 5.0)
    raw_probabilities = [bear_pct / 100, base_pct / 100, bull_pct / 100]
    scenarios = scenario_analysis(flows, discount_rate, hurdle_rate, raw_probabilities)
    if abs(sum(raw_probabilities) - 1.0) > 1e-6:
        st.warning("Probabilities were normalized because they did not sum to 100%.")
    metric_card("Probability-Weighted NPV", format_currency(probability_weighted_npv(scenarios)))
    st.plotly_chart(scenario_chart(scenarios), use_container_width=True)
    st.caption("Scenario NPVs are probability-weighted after normalizing the probabilities.")
    st.dataframe(scenarios, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Sensitivity Analysis")
    st.plotly_chart(sensitivity_heatmap(sensitivity), use_container_width=True)
    st.caption("Cells show NPV under paired discount-rate and cash-flow-growth assumptions.")
    st.dataframe(sensitivity, use_container_width=True)

with tabs[5]:
    st.subheader("Multi-Project Comparison")
    st.info(
        "The ranking is not based on IRR alone. It balances NPV, hurdle-rate performance, "
        "discounted payback, profitability index, and scale of value creation."
    )
    st.caption(
        "IRR can favor smaller or faster-paying projects. This ranking balances return, "
        "value creation, payback timing, and efficiency."
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
        discount_rate,
        hurdle_rate,
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
