# IRR Analytics Terminal

[![CI](https://github.com/Raphael-Azerad/irr-analytics-terminal/actions/workflows/ci.yml/badge.svg)](https://github.com/Raphael-Azerad/irr-analytics-terminal/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

IRR Analytics Terminal is a Streamlit app for evaluating investment cash flows. It calculates IRR, NPV, MIRR, payback period, discounted payback, and profitability index, then visualizes cash-flow timing, NPV profiles, scenarios, and project comparisons.

## Overview

The project is built for capital-budgeting analysis rather than a single headline return. It puts IRR beside NPV, MIRR, liquidity measures, scenario outcomes, sensitivity tables, and a balanced multi-project ranking.

## Live Demo

Live demo: coming soon.

## Key Findings From Default Example

The default Corporate Expansion Project assumes a `$10,000,000` initial investment, six years of forecast inflows, and a `10%` hurdle rate.

| Metric | Result |
| --- | ---: |
| Initial investment | $10,000,000 |
| Forecast horizon | 6 years |
| Hurdle rate | 10.00% |
| IRR | 14.96% |
| MIRR | 12.94% |
| NPV | $1,713,138 |
| Payback period | 4.12 years |
| Discounted payback period | 5.20 years |
| Profitability index | 1.17x |
| Decision status | Passes hurdle rate |

The project clears the hurdle rate and creates positive value at the selected discount rate. The positive NPV is the stronger evidence of value creation; IRR is useful as a return benchmark, but it should not be viewed alone.

## Screenshots

![Dashboard overview](screenshots/dashboard-overview.png)
![NPV profile](screenshots/npv-profile.png)
![Scenario analysis](screenshots/scenario-analysis.png)
![Project comparison](screenshots/project-comparison.png)

## Features

- Executive metric dashboard with neutral decision language
- Manual cash-flow editing and built-in project examples
- CSV and Excel upload with flexible column names
- IRR, NPV, MIRR, payback, discounted payback, and profitability index
- Cash-flow timeline and cumulative cash-flow charts
- NPV profile from 0% to 30%
- Bear, base, and bull scenarios with probability-weighted NPV
- Discount-rate and cash-flow-growth sensitivity heatmap
- Balanced multi-project comparison
- Formatted eight-sheet Excel export

## Methodology

The application treats NPV as the primary measure of absolute value creation and uses IRR as a return benchmark. It identifies non-conventional cash-flow patterns and warns when multiple IRRs may exist.

## IRR

Internal Rate of Return is the discount rate that sets project NPV equal to zero. A valid IRR can be compared with a hurdle rate, but it does not measure the dollar value created.

## NPV

Net Present Value discounts every project cash flow at the required rate of return. Positive NPV indicates expected value creation after accounting for risk and the time value of money.

## MIRR

Modified Internal Rate of Return applies explicit financing and reinvestment rates. It addresses some of the reinvestment assumptions embedded in standard IRR.

## Why IRR Can Be Misleading

- Non-conventional cash flows can produce multiple IRRs.
- All-positive or all-negative cash flows have no meaningful IRR.
- IRR can favor smaller or faster-paying projects.
- IRR can mis-rank projects with different scale or timing.
- NPV is usually better for measuring absolute value creation.

## Scenario Analysis

The default scenario model applies:

- Bear case: future inflows down 15%, discount rate up 2%
- Base case: original cash flows
- Bull case: future inflows up 15%, discount rate down 1%

Scenario probabilities are normalized when they do not total 100%.

## Sensitivity Analysis

The sensitivity view shows how NPV changes across discount rates and cash-flow growth assumptions. This makes the assumptions behind the base case visible.

## Multi-Project Comparison

Projects are not ranked by IRR alone. The scoring system considers positive NPV, IRR versus hurdle rate, discounted payback, profitability index, and scale of value creation.

## Excel Export

The formatted workbook includes:

- Summary
- Cash Flows
- Metrics
- NPV Profile
- Scenario Analysis
- Sensitivity Analysis
- Multi-Project Comparison
- Assumptions

## Installation

```bash
git clone https://github.com/Raphael-Azerad/irr-analytics-terminal.git
cd irr-analytics-terminal
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Testing

```bash
pytest
ruff check .
black --check .
```

## Deployment

The app is prepared for Streamlit Community Cloud. Use `app.py` as the entry point. No secrets are required.

## Repository Structure

```text
.
├── app.py
├── pyproject.toml
├── examples/
├── notebooks/
├── screenshots/
├── src/irr_terminal/
├── tests/
└── .github/workflows/ci.yml
```

## Limitations

- Forecast quality depends on the assumptions supplied by the user.
- Scenario and sensitivity analysis are deterministic and do not replace diligence.
- The app does not model taxes, debt schedules, or accounting statements.
- Investment outputs are analytical aids, not financial advice.

## Future Improvements

- Correlated Monte Carlo simulation
- Debt schedules and leverage metrics
- Portfolio capital-allocation optimization
- Persistent project storage
- Branded investment memo exports

## References

- Brealey, Myers, and Allen, *Principles of Corporate Finance*
- Berk and DeMarzo, *Corporate Finance*
- CFA Institute capital-budgeting materials

## License

This project is released under the [MIT License](LICENSE).
