# Contributing

Thank you for helping improve IRR Analytics Terminal.

## Development Setup

```bash
git clone https://github.com/Raphael-Azerad/irr-analytics-terminal.git
cd irr-analytics-terminal
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Launch the application with:

```bash
streamlit run app.py
```

## Before Opening a Pull Request

1. Keep changes focused on one problem or feature.
2. Add or update tests for calculation or data-handling changes.
3. Run the test suite:

   ```bash
   python -m pytest -q
   ```

4. Confirm the application modules compile:

   ```bash
   python -m py_compile app.py calculations/*.py visualizations/*.py reports/*.py utils/*.py
   ```

5. Update the README or financial theory documentation when user-facing behavior changes.

## Financial Logic

Finance calculations should be transparent, deterministic where possible, and explicit about assumptions. Avoid presenting IRR as a standalone decision rule when NPV, scale, timing, or non-conventional cash flows materially affect the conclusion.
