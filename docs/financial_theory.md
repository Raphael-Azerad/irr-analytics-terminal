# Financial Theory Reference

IRR Analytics Terminal is built around the principle that no single return metric is sufficient for a capital allocation decision. Each metric answers a different question and carries a different set of limitations.

## Net Present Value

Net Present Value discounts each project cash flow to time zero:

```text
NPV = Σ CF_t / (1 + r)^t
```

NPV is the primary value-creation metric because it measures the dollar value added after compensating capital providers for risk and the time value of money. A positive NPV indicates that a project is expected to create value at the selected discount rate.

## Internal Rate of Return

IRR is the discount rate at which NPV equals zero:

```text
0 = Σ CF_t / (1 + IRR)^t
```

IRR is intuitive because it expresses project returns as an annualized percentage. It should be compared with a hurdle rate and the cost of capital. Non-conventional cash flows can produce multiple IRRs, and IRR can mis-rank mutually exclusive projects of different sizes.

## XNPV and XIRR

Periodic NPV and IRR assume evenly spaced cash flows. Real investments often close, distribute cash, or require follow-on capital on irregular dates. XNPV and XIRR use the actual number of days between cash flows, producing a more accurate annualized return and present value for dated models.

## Modified Internal Rate of Return

MIRR separates the financing rate applied to negative cash flows from the reinvestment rate applied to positive cash flows. It avoids the implicit IRR assumption that interim distributions can be reinvested at the project IRR.

## Profitability Index

Profitability Index measures present value created per dollar of initial capital:

```text
PI = PV of future cash flows / Initial investment
```

PI is particularly useful when capital is constrained and projects must be ranked by capital efficiency.

## Payback Period

Traditional payback measures how long it takes for cumulative nominal cash flows to recover the initial investment. Discounted payback applies the same concept after discounting future cash flows. Payback is a useful liquidity and risk indicator, but it ignores cash flows after the recovery point.

## Scenario and Sensitivity Analysis

Scenario analysis tests coherent sets of assumptions, such as a bear, base, and bull case. Sensitivity analysis isolates the impact of individual variables. Both are important because a point estimate can hide the project's dependency on uncertain assumptions.

## Monte Carlo Analysis

Monte Carlo simulation replaces a single deterministic forecast with a distribution of possible outcomes. The terminal reports the probability of positive NPV and the probability that IRR exceeds the hurdle rate, enabling a more complete view of downside risk and expected value.

The terminal also reports the 5th percentile NPV and the average NPV in the worst 5% of outcomes. This downside tail average is a Conditional Value at Risk-style measure that helps reviewers understand the severity of adverse outcomes, not merely their probability.
