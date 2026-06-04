"""IRR Analytics Terminal - institutional capital budgeting platform."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from calculations.metrics import FinancialMetrics, calculate_metrics, xirr, xnpv
from calculations.monte_carlo import run_monte_carlo
from calculations.recommendation import generate_recommendation
from calculations.scenarios import irr_sensitivity, npv_sensitivity, scenario_table
from calculations.specialized import analyze_real_estate, analyze_sponsor_returns
from data.examples import EXAMPLE_INVESTMENTS
from reports.exporters import build_excel_report, build_pdf_report
from utils.io import parse_uploaded_file, validate_cash_flow_frame
from visualizations.charts import (
    cash_flow_waterfall,
    monte_carlo_histogram,
    npv_profile,
    probability_curve,
    project_ranking,
    scenario_comparison,
    sensitivity_heatmap,
)


st.set_page_config(
    page_title="IRR Analytics Terminal",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .stApp { background-color: #08111f; color: #dbe7f3; }
    [data-testid="stSidebar"] { background-color: #0b1726; border-right: 1px solid #1d3048; }
    [data-testid="stHeader"] { background-color: rgba(8, 17, 31, 0.85); }
    h1, h2, h3 { color: #f3f8fc; letter-spacing: -0.02em; }
    .terminal-label { color: #28d7e5; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.15em; }
    .terminal-title { color: #f3f8fc; font-size: 2.35rem; font-weight: 700; margin: 0.15rem 0 0.25rem; }
    .terminal-subtitle { color: #8fa5bd; font-size: 1rem; margin-bottom: 1.5rem; }
    .kpi-card { background: #101c2c; border: 1px solid #1d3048; border-radius: 8px; padding: 1rem 1rem 0.85rem; min-height: 112px; }
    .kpi-label { color: #8fa5bd; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; }
    .kpi-value { color: #f3f8fc; font-size: 1.55rem; font-weight: 700; margin-top: 0.35rem; }
    .kpi-context { color: #617b97; font-size: 0.75rem; margin-top: 0.2rem; }
    .recommendation { background: #101c2c; border-left: 4px solid #3ddc97; padding: 1rem 1.2rem; border-radius: 4px; margin: 0.5rem 0 1rem; }
    .recommendation.reject { border-left-color: #ff6b6b; }
    .recommendation.consider { border-left-color: #f4c95d; }
    .section-note { color: #8fa5bd; font-size: 0.88rem; }
    .stButton button, .stDownloadButton button { border-radius: 4px; border: 1px solid #28d7e5; color: #dbe7f3; background: #102438; }
    div[data-testid="stMetric"] { background: #101c2c; border: 1px solid #1d3048; padding: 0.8rem; border-radius: 8px; }
    div[data-testid="stDataFrame"] { border: 1px solid #1d3048; border-radius: 6px; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def initialize_state() -> None:
    if "project_name" not in st.session_state:
        example = EXAMPLE_INVESTMENTS["Corporate Expansion Project"]
        st.session_state.project_name = example["project_name"]
        st.session_state.investment_name = example["investment_name"]
        st.session_state.cash_flow_frame = pd.DataFrame(
            {
                "Period": range(len(example["cash_flows"])),
                "Date": pd.date_range("2026-01-01", periods=len(example["cash_flows"]), freq="YS").date,
                "Cash Flow": example["cash_flows"],
            }
        )
    defaults = {
        "discount_rate": 0.10,
        "hurdle_rate": 0.12,
        "cost_of_capital": 0.09,
        "finance_rate": 0.08,
        "reinvestment_rate": 0.08,
        "tax_rate": 0.25,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "comparison_projects" not in st.session_state:
        st.session_state.comparison_projects = {}


def fmt_currency(value: float | None) -> str:
    return "N/A" if value is None else f"${value:,.0f}"


def fmt_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2%}"


def fmt_years(value: float | None) -> str:
    return "No payback" if value is None else f"{value:.2f} yrs"


def fmt_multiple(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}x"


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="terminal-label">IRR ANALYTICS TERMINAL</div>
        <div class="terminal-title">{title}</div>
        <div class="terminal-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, context: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-context">{context}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def current_cash_flows() -> list[float]:
    validated = validate_cash_flow_frame(st.session_state.cash_flow_frame)
    return validated["Cash Flow"].tolist()


def current_dates() -> list[object] | None:
    validated = validate_cash_flow_frame(st.session_state.cash_flow_frame)
    return validated["Date"].tolist() if "Date" in validated.columns else None


def current_metrics() -> FinancialMetrics:
    return calculate_metrics(
        current_cash_flows(),
        st.session_state.discount_rate,
        st.session_state.hurdle_rate,
        st.session_state.cost_of_capital,
        st.session_state.finance_rate,
        st.session_state.reinvestment_rate,
    )


def render_sidebar() -> str:
    st.sidebar.markdown("## IRR Analytics Terminal")
    st.sidebar.caption("Capital allocation intelligence")
    page = st.sidebar.radio(
        "Workspace",
        [
            "Dashboard",
            "Cash Flow Builder",
            "Scenario & Sensitivity",
            "Monte Carlo",
            "Multi-Project Comparison",
            "Real Estate Mode",
            "Private Equity Mode",
            "Export Center",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.markdown("### Corporate Finance Assumptions")
    st.sidebar.number_input(
        "Discount Rate",
        min_value=0.0,
        max_value=1.0,
        step=0.005,
        format="%.3f",
        key="discount_rate",
    )
    st.sidebar.number_input(
        "Hurdle Rate",
        min_value=0.0,
        max_value=1.0,
        step=0.005,
        format="%.3f",
        key="hurdle_rate",
    )
    st.sidebar.number_input(
        "Cost of Capital",
        min_value=0.0,
        max_value=1.0,
        step=0.005,
        format="%.3f",
        key="cost_of_capital",
    )
    with st.sidebar.expander("Advanced assumptions"):
        st.number_input(
            "Finance Rate",
            min_value=0.0,
            max_value=1.0,
            step=0.005,
            format="%.3f",
            key="finance_rate",
        )
        st.number_input(
            "Reinvestment Rate",
            min_value=0.0,
            max_value=1.0,
            step=0.005,
            format="%.3f",
            key="reinvestment_rate",
        )
        st.number_input(
            "Tax Rate (Reference)",
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            format="%.2f",
            key="tax_rate",
        )
    st.sidebar.caption(
        "Rates are entered as decimals. Example: 0.10 = 10%. "
        "Project cash flows should be entered on an after-tax basis."
    )
    return page


def render_dashboard() -> None:
    metrics = current_metrics()
    flows = current_cash_flows()
    scenarios = scenario_table(
        flows,
        st.session_state.discount_rate,
        st.session_state.hurdle_rate,
        st.session_state.cost_of_capital,
        st.session_state.finance_rate,
        st.session_state.reinvestment_rate,
    )
    bear_case_npv = float(scenarios.loc[scenarios["Scenario"] == "Bear", "NPV"].iloc[0])
    recommendation = generate_recommendation(metrics, bear_case_npv=bear_case_npv)
    dates = current_dates()
    dated_irr = xirr(flows, dates) if dates is not None else None
    dated_npv = xnpv(st.session_state.discount_rate, flows, dates) if dates is not None else None

    header(
        "Executive Dashboard",
        f"{st.session_state.project_name} | {st.session_state.investment_name}",
    )
    row_one = st.columns(5)
    with row_one[0]:
        kpi_card("Initial Investment", fmt_currency(metrics.initial_investment), "Time-zero capital outlay")
    with row_one[1]:
        kpi_card("Total Cash Inflows", fmt_currency(metrics.total_inflows), "Gross project distributions")
    with row_one[2]:
        kpi_card("IRR", fmt_percent(metrics.irr), f"Hurdle: {metrics.hurdle_rate:.1%}")
    with row_one[3]:
        kpi_card("NPV", fmt_currency(metrics.npv), f"Discount rate: {metrics.discount_rate:.1%}")
    with row_one[4]:
        kpi_card("MIRR", fmt_percent(metrics.mirr), f"Reinvestment: {st.session_state.reinvestment_rate:.1%}")

    row_two = st.columns(4)
    with row_two[0]:
        kpi_card("Profitability Index", fmt_multiple(metrics.profitability_index), "PV inflows / initial outlay")
    with row_two[1]:
        kpi_card("Payback Period", fmt_years(metrics.payback_period), "Undiscounted recovery")
    with row_two[2]:
        kpi_card("Discounted Payback", fmt_years(metrics.discounted_payback_period), "Time-value adjusted")
    with row_two[3]:
        spread = None if metrics.irr is None else metrics.irr - metrics.cost_of_capital
        kpi_card("IRR vs. WACC", fmt_percent(spread), f"Cost of capital: {metrics.cost_of_capital:.1%}")

    if dates is not None:
        dated_columns = st.columns(3)
        with dated_columns[0]:
            st.metric("XIRR", fmt_percent(dated_irr), help="Annualized return using actual cash-flow dates.")
        with dated_columns[1]:
            st.metric("XNPV", fmt_currency(dated_npv), help="NPV using actual day-count timing.")
        with dated_columns[2]:
            st.metric("NPV / Initial Investment", fmt_percent(metrics.npv_to_investment))

    recommendation_class = recommendation.rating.lower().replace(" ", "-")
    st.markdown(
        f"""
        <div class="recommendation {recommendation_class}">
            <strong>{recommendation.rating}</strong><br>
            {recommendation.headline}
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_left, chart_right = st.columns([1.15, 1])
    with chart_left:
        st.plotly_chart(cash_flow_waterfall(flows), use_container_width=True)
    with chart_right:
        st.plotly_chart(npv_profile(flows), use_container_width=True)

    st.subheader("Investment Committee Rationale")
    for reason in recommendation.rationale:
        st.markdown(f"- {reason}")

    st.subheader("Decision Matrix")
    decision_rows = [
        {
            "Test": "NPV creates value",
            "Result": fmt_currency(metrics.npv),
            "Threshold": "> $0",
            "Status": "Pass" if metrics.npv > 0 else "Fail",
        },
        {
            "Test": "IRR clears hurdle rate",
            "Result": fmt_percent(metrics.irr),
            "Threshold": fmt_percent(metrics.hurdle_rate),
            "Status": "Pass" if metrics.irr is not None and metrics.irr > metrics.hurdle_rate else "Fail",
        },
        {
            "Test": "Profitability Index",
            "Result": fmt_multiple(metrics.profitability_index),
            "Threshold": "> 1.00x",
            "Status": "Pass" if metrics.profitability_index is not None and metrics.profitability_index > 1 else "Fail",
        },
        {
            "Test": "Bear-case NPV",
            "Result": fmt_currency(bear_case_npv),
            "Threshold": "> $0",
            "Status": "Pass" if bear_case_npv > 0 else "Diligence",
        },
    ]
    st.dataframe(pd.DataFrame(decision_rows), use_container_width=True, hide_index=True)


def load_example(name: str) -> None:
    example = EXAMPLE_INVESTMENTS[name]
    st.session_state.project_name = example["project_name"]
    st.session_state.investment_name = example["investment_name"]
    st.session_state.cash_flow_frame = pd.DataFrame(
        {
            "Period": range(len(example["cash_flows"])),
            "Date": pd.date_range("2026-01-01", periods=len(example["cash_flows"]), freq="YS").date,
            "Cash Flow": example["cash_flows"],
        }
    )


def render_cash_flow_builder() -> None:
    header("Cash Flow Builder", "Construct, upload, validate, and analyze project cash flows.")
    info_left, info_right = st.columns(2)
    with info_left:
        st.text_input("Project Name", key="project_name")
    with info_right:
        st.text_input("Investment Name", key="investment_name")

    example_name = st.selectbox("Load Example Investment", list(EXAMPLE_INVESTMENTS))
    example_description = EXAMPLE_INVESTMENTS[example_name]["description"]
    st.caption(str(example_description))
    if st.button("Load Selected Example", use_container_width=False):
        load_example(example_name)
        st.rerun()

    st.divider()
    builder_tab, upload_tab = st.tabs(["Manual Entry", "Excel / CSV Upload"])
    with builder_tab:
        period_count = st.number_input(
            "Number of periods",
            min_value=2,
            max_value=50,
            value=len(st.session_state.cash_flow_frame),
            step=1,
        )
        if st.button("Resize Cash Flow Model"):
            existing = st.session_state.cash_flow_frame["Cash Flow"].tolist()
            resized = existing[:period_count] + [0.0] * max(0, period_count - len(existing))
            existing_dates = (
                pd.to_datetime(st.session_state.cash_flow_frame["Date"]).tolist()
                if "Date" in st.session_state.cash_flow_frame.columns
                else [pd.Timestamp("2026-01-01")]
            )
            while len(existing_dates) < period_count:
                existing_dates.append(existing_dates[-1] + pd.DateOffset(years=1))
            st.session_state.cash_flow_frame = pd.DataFrame(
                {
                    "Period": range(period_count),
                    "Date": [value.date() for value in existing_dates[:period_count]],
                    "Cash Flow": resized,
                }
            )
            st.rerun()
        edited = st.data_editor(
            st.session_state.cash_flow_frame,
            use_container_width=True,
            hide_index=True,
            disabled=["Period"],
            column_config={
                "Period": st.column_config.NumberColumn("Period", format="%d"),
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Cash Flow": st.column_config.NumberColumn("Cash Flow", format="$%.2f"),
            },
            key="cash_flow_editor",
        )
        if st.button("Apply Cash Flow Changes", type="primary"):
            try:
                st.session_state.cash_flow_frame = validate_cash_flow_frame(edited)
                st.success("Cash-flow model updated.")
            except ValueError as exc:
                st.error(str(exc))

    with upload_tab:
        uploaded = st.file_uploader("Upload cash flows", type=["xlsx", "csv"])
        st.caption("Files should include a cash-flow column. Add a `Date` column to calculate XIRR and XNPV.")
        if uploaded is not None and st.button("Import Uploaded File"):
            try:
                st.session_state.cash_flow_frame = parse_uploaded_file(uploaded.name, uploaded.getvalue())
                st.success("File imported and validated.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    metrics = current_metrics()
    dates = current_dates()
    preview_columns = st.columns(6 if dates is not None else 4)
    preview_values = [
        ("IRR", fmt_percent(metrics.irr)),
        ("NPV", fmt_currency(metrics.npv)),
        ("MIRR", fmt_percent(metrics.mirr)),
        ("Payback", fmt_years(metrics.payback_period)),
    ]
    if dates is not None:
        preview_values.extend(
            [
                ("XIRR", fmt_percent(xirr(current_cash_flows(), dates))),
                ("XNPV", fmt_currency(xnpv(st.session_state.discount_rate, current_cash_flows(), dates))),
            ]
        )
    for column, (label, value) in zip(preview_columns, preview_values):
        with column:
            st.metric(label, value)


def render_scenario_sensitivity() -> None:
    header(
        "Scenario & Sensitivity",
        "Understand which operating assumptions matter most to investment returns.",
    )
    flows = current_cash_flows()
    scenarios = scenario_table(
        flows,
        st.session_state.discount_rate,
        st.session_state.hurdle_rate,
        st.session_state.cost_of_capital,
        st.session_state.finance_rate,
        st.session_state.reinvestment_rate,
    )

    st.subheader("Bear / Base / Bull Scenarios")
    st.dataframe(
        scenarios.style.format(
            {
                "IRR": "{:.2%}",
                "NPV": "${:,.0f}",
                "Payback": "{:.2f}",
                "Profitability Index": "{:.2f}x",
            },
            na_rep="N/A",
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.plotly_chart(scenario_comparison(scenarios), use_container_width=True)

    st.subheader("Two-Way Sensitivity Analysis")
    changes = [-0.20, -0.10, 0.00, 0.10, 0.20]
    irr_frame = irr_sensitivity(flows, changes, changes)
    npv_frame = npv_sensitivity(
        flows,
        [
            max(0.0, st.session_state.discount_rate - 0.04),
            max(0.0, st.session_state.discount_rate - 0.02),
            st.session_state.discount_rate,
            st.session_state.discount_rate + 0.02,
            st.session_state.discount_rate + 0.04,
        ],
        changes,
    )
    heatmap_left, heatmap_right = st.columns(2)
    with heatmap_left:
        st.plotly_chart(
            sensitivity_heatmap(irr_frame, "IRR Sensitivity: Revenue vs. Cost Growth", ".1%"),
            use_container_width=True,
        )
        st.caption("Rows: revenue change. Columns: cost change.")
    with heatmap_right:
        st.plotly_chart(
            sensitivity_heatmap(npv_frame, "NPV Sensitivity: Discount Rate vs. Terminal Value", ",.0f"),
            use_container_width=True,
        )
        st.caption("Rows: discount rate. Columns: terminal value change.")


@st.cache_data(show_spinner=False)
def cached_monte_carlo(
    cash_flows: tuple[float, ...],
    discount_rate: float,
    hurdle_rate: float,
    simulations: int,
    revenue_uncertainty: float,
    cost_uncertainty: float,
    growth_uncertainty: float,
):
    return run_monte_carlo(
        cash_flows,
        discount_rate,
        hurdle_rate,
        simulations,
        revenue_uncertainty,
        cost_uncertainty,
        growth_uncertainty,
    )


def render_monte_carlo() -> None:
    header(
        "Monte Carlo Risk Analysis",
        "Quantify the probability of value creation under operating uncertainty.",
    )
    input_one, input_two, input_three, input_four = st.columns(4)
    with input_one:
        simulations = st.selectbox("Simulations", [1000, 5000, 10000], index=1)
    with input_two:
        revenue_uncertainty = st.slider("Revenue uncertainty", 0.0, 0.50, 0.10, 0.01)
    with input_three:
        cost_uncertainty = st.slider("Cost uncertainty", 0.0, 0.50, 0.08, 0.01)
    with input_four:
        growth_uncertainty = st.slider("Growth uncertainty", 0.0, 0.20, 0.03, 0.01)

    with st.spinner("Running simulations..."):
        result = cached_monte_carlo(
            tuple(current_cash_flows()),
            st.session_state.discount_rate,
            st.session_state.hurdle_rate,
            simulations,
            revenue_uncertainty,
            cost_uncertainty,
            growth_uncertainty,
        )

    probability_columns = st.columns(4)
    with probability_columns[0]:
        st.metric("Probability NPV > 0", f"{result.probability_positive_npv:.1%}")
    with probability_columns[1]:
        st.metric("Probability IRR > Hurdle", f"{result.probability_irr_above_hurdle:.1%}")
    with probability_columns[2]:
        st.metric("Median NPV", fmt_currency(result.simulations["NPV"].median()))
    with probability_columns[3]:
        st.metric("Median IRR", fmt_percent(result.simulations["IRR"].median()))

    downside_columns = st.columns(3)
    with downside_columns[0]:
        st.metric("5th Percentile NPV", fmt_currency(result.npv_value_at_risk_5))
    with downside_columns[1]:
        st.metric("Downside Tail Average", fmt_currency(result.npv_conditional_value_at_risk_5))
    with downside_columns[2]:
        st.metric("5th Percentile IRR", fmt_percent(result.irr_value_at_risk_5))
    st.caption(
        "The downside tail average is the mean NPV of the worst 5% of simulated outcomes."
    )

    histogram_left, histogram_right = st.columns(2)
    with histogram_left:
        st.plotly_chart(monte_carlo_histogram(result.simulations, "NPV"), use_container_width=True)
    with histogram_right:
        st.plotly_chart(monte_carlo_histogram(result.simulations, "IRR"), use_container_width=True)

    curve_left, curve_right = st.columns(2)
    with curve_left:
        st.plotly_chart(probability_curve(result.simulations, "NPV"), use_container_width=True)
    with curve_right:
        st.plotly_chart(probability_curve(result.simulations, "IRR"), use_container_width=True)

    st.subheader("Simulation Summary Statistics")
    st.dataframe(result.summary, use_container_width=True)


def project_comparison_frame(include_examples: bool = True) -> pd.DataFrame:
    projects: dict[str, list[float]] = {}
    if include_examples:
        projects.update(
            {name: list(details["cash_flows"]) for name, details in EXAMPLE_INVESTMENTS.items()}
        )
    projects.update(st.session_state.comparison_projects)
    if not projects:
        projects[f"Current: {st.session_state.investment_name}"] = current_cash_flows()
    rows = []
    for name, flows in projects.items():
        metrics = calculate_metrics(
            flows,
            st.session_state.discount_rate,
            st.session_state.hurdle_rate,
            st.session_state.cost_of_capital,
            st.session_state.finance_rate,
            st.session_state.reinvestment_rate,
        )
        rows.append(
            {
                "Project": name,
                "IRR": metrics.irr,
                "NPV": metrics.npv,
                "MIRR": metrics.mirr,
                "Payback": metrics.payback_period,
                "PI": metrics.profitability_index,
            }
        )
    frame = pd.DataFrame(rows)
    frame["Rank"] = frame["NPV"].rank(ascending=False, method="min").astype(int)
    return frame.sort_values("Rank")


def render_project_comparison() -> None:
    header(
        "Multi-Project Comparison",
        "Rank competing capital allocation opportunities on a consistent basis.",
    )
    controls = st.columns([1.2, 1, 1])
    with controls[0]:
        if st.button("Add Current Project to Pipeline", type="primary", use_container_width=True):
            project_key = st.session_state.investment_name.strip() or st.session_state.project_name.strip()
            st.session_state.comparison_projects[project_key] = current_cash_flows()
            st.success(f"Added {project_key} to the comparison pipeline.")
    with controls[1]:
        include_examples = st.checkbox("Include built-in examples", value=True)
    with controls[2]:
        saved_names = sorted(st.session_state.comparison_projects)
        remove_name = st.selectbox(
            "Remove saved project",
            ["None", *saved_names],
            disabled=not saved_names,
        )
        if remove_name != "None" and st.button("Remove Selected Project", use_container_width=True):
            del st.session_state.comparison_projects[remove_name]
            st.rerun()

    frame = project_comparison_frame(include_examples=include_examples)
    best = frame.iloc[0]
    st.success(
        f"Top-ranked opportunity: **{best['Project']}** with NPV of {fmt_currency(best['NPV'])} "
        f"and IRR of {fmt_percent(best['IRR'])}."
    )
    st.dataframe(
        frame.style.format(
            {
                "IRR": "{:.2%}",
                "NPV": "${:,.0f}",
                "MIRR": "{:.2%}",
                "Payback": "{:.2f}",
                "PI": "{:.2f}x",
            },
            na_rep="N/A",
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.plotly_chart(project_ranking(frame), use_container_width=True)
    st.caption(
        f"Pipeline contains {len(st.session_state.comparison_projects)} saved user project(s). "
        "All projects are evaluated using the same current discount-rate assumptions."
    )


def render_real_estate() -> None:
    header("Real Estate Mode", "Underwrite property cash flows, exit proceeds, and equity returns.")
    left, right = st.columns(2)
    with left:
        purchase_price = st.number_input("Purchase Price", min_value=0.0, value=5_000_000.0, step=100_000.0)
        annual_rent = st.number_input("Annual Rental Income", min_value=0.0, value=650_000.0, step=25_000.0)
        annual_expenses = st.number_input("Annual Operating Expenses", min_value=0.0, value=220_000.0, step=10_000.0)
    with right:
        exit_value = st.number_input("Exit Value", min_value=0.0, value=6_500_000.0, step=100_000.0)
        hold_period = st.number_input("Hold Period (Years)", min_value=1, max_value=30, value=5)
        discount_rate = st.number_input("Real Estate Discount Rate", min_value=0.0, max_value=1.0, value=0.10, step=0.005)
    analysis = analyze_real_estate(
        purchase_price,
        annual_rent,
        annual_expenses,
        exit_value,
        hold_period,
        discount_rate,
    )
    columns = st.columns(4)
    with columns[0]:
        st.metric("Net Operating Income", fmt_currency(annual_rent - annual_expenses))
    with columns[1]:
        st.metric("IRR", fmt_percent(analysis.irr))
    with columns[2]:
        st.metric("NPV", fmt_currency(analysis.npv))
    with columns[3]:
        st.metric("Equity Multiple", fmt_multiple(analysis.equity_multiple))
    st.plotly_chart(cash_flow_waterfall(analysis.cash_flows), use_container_width=True)


def render_private_equity() -> None:
    header("Private Equity Mode", "Evaluate sponsor returns, leverage, debt paydown, and exit equity value.")
    left, right = st.columns(2)
    with left:
        entry_equity = st.number_input("Entry Equity", min_value=0.0, value=10_000_000.0, step=250_000.0)
        debt = st.number_input("Entry Debt", min_value=0.0, value=15_000_000.0, step=250_000.0)
        annual_distributions = st.number_input("Annual Cash Distributions", min_value=0.0, value=750_000.0, step=50_000.0)
    with right:
        exit_enterprise_value = st.number_input("Exit Enterprise Value", min_value=0.0, value=25_000_000.0, step=250_000.0)
        exit_debt = st.number_input("Exit Debt", min_value=0.0, value=7_000_000.0, step=250_000.0)
        hold_period = st.number_input("Sponsor Hold Period (Years)", min_value=1, max_value=15, value=5)
        discount_rate = st.number_input("Sponsor Discount Rate", min_value=0.0, max_value=1.0, value=0.20, step=0.01)
    exit_equity = max(exit_enterprise_value - exit_debt, 0.0)
    analysis = analyze_sponsor_returns(
        entry_equity,
        annual_distributions,
        exit_equity,
        hold_period,
        discount_rate,
    )
    entry_enterprise_value = entry_equity + debt
    entry_leverage = debt / entry_enterprise_value if entry_enterprise_value else 0.0
    debt_paydown = debt - exit_debt
    columns = st.columns(5)
    with columns[0]:
        st.metric("Entry Enterprise Value", fmt_currency(entry_enterprise_value))
    with columns[1]:
        st.metric("Sponsor IRR", fmt_percent(analysis.irr))
    with columns[2]:
        st.metric("Money-on-Money", fmt_multiple(analysis.money_on_money))
    with columns[3]:
        st.metric("Entry Leverage", fmt_percent(entry_leverage))
    with columns[4]:
        st.metric("Debt Paydown", fmt_currency(debt_paydown))
    st.caption(
        f"Calculated exit equity value: {fmt_currency(exit_equity)} "
        f"({fmt_currency(exit_enterprise_value)} exit enterprise value less {fmt_currency(exit_debt)} exit debt)."
    )
    st.plotly_chart(cash_flow_waterfall(analysis.cash_flows), use_container_width=True)


def render_export_center() -> None:
    header("Export Center", "Package the analysis for review, diligence, and investment committee circulation.")
    metrics = current_metrics()
    scenarios = scenario_table(
        current_cash_flows(),
        st.session_state.discount_rate,
        st.session_state.hurdle_rate,
        st.session_state.cost_of_capital,
        st.session_state.finance_rate,
        st.session_state.reinvestment_rate,
    )
    bear_case_npv = float(scenarios.loc[scenarios["Scenario"] == "Bear", "NPV"].iloc[0])
    recommendation = generate_recommendation(metrics, bear_case_npv=bear_case_npv)
    st.markdown(
        f"""
        <div class="recommendation {recommendation.rating.lower().replace(" ", "-")}">
            <strong>{recommendation.rating}</strong><br>
            {recommendation.headline}
        </div>
        """,
        unsafe_allow_html=True,
    )
    excel_bytes = build_excel_report(
        st.session_state.project_name,
        st.session_state.investment_name,
        current_cash_flows(),
        metrics,
        recommendation,
        scenarios,
        dates=current_dates(),
    )
    pdf_bytes = build_pdf_report(
        st.session_state.project_name,
        st.session_state.investment_name,
        metrics,
        recommendation,
        scenarios,
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Professional Excel Workbook")
        st.write("Includes executive summary, cash flows, scenarios, and assumptions.")
        st.download_button(
            "Download Excel Analysis",
            data=excel_bytes,
            file_name="irr_analytics_terminal_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with right:
        st.subheader("Investment Committee Memo")
        st.write("Includes executive summary, recommendation, rationale, scenario analysis, assumptions, and risk analysis.")
        st.download_button(
            "Download PDF Memo",
            data=pdf_bytes,
            file_name="irr_analytics_terminal_memo.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


initialize_state()
selected_page = render_sidebar()

try:
    page_map = {
        "Dashboard": render_dashboard,
        "Cash Flow Builder": render_cash_flow_builder,
        "Scenario & Sensitivity": render_scenario_sensitivity,
        "Monte Carlo": render_monte_carlo,
        "Multi-Project Comparison": render_project_comparison,
        "Real Estate Mode": render_real_estate,
        "Private Equity Mode": render_private_equity,
        "Export Center": render_export_center,
    }
    page_map[selected_page]()
except ValueError as error:
    st.error(f"Unable to complete the analysis: {error}")
    st.info("Review the cash-flow model and confirm that it contains valid numeric outflows and inflows.")
