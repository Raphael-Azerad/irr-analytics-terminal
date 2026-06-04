"""Built-in project examples."""

from __future__ import annotations

import pandas as pd


EXAMPLES: dict[str, list[float]] = {
    "Corporate Expansion Project": [
        -10_000_000,
        1_800_000,
        2_200_000,
        2_600_000,
        3_000_000,
        3_400_000,
        3_800_000,
    ],
    "Acquisition Case": [
        -18_000_000,
        2_100_000,
        2_500_000,
        2_900_000,
        3_300_000,
        3_800_000,
        14_000_000,
    ],
    "Real Estate Development": [
        -8_000_000,
        -2_000_000,
        900_000,
        1_400_000,
        1_800_000,
        12_500_000,
    ],
    "Renewable Energy Project": [
        -15_000_000,
        2_000_000,
        2_100_000,
        2_200_000,
        2_300_000,
        2_400_000,
        2_500_000,
        2_600_000,
        2_700_000,
    ],
}


def example_frame(name: str) -> pd.DataFrame:
    flows = EXAMPLES[name]
    return pd.DataFrame({"Project": name, "Period": range(len(flows)), "Cash Flow": flows})
