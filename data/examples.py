"""Professional example investments available from the application."""

from __future__ import annotations

EXAMPLE_INVESTMENTS: dict[str, dict[str, object]] = {
    "Corporate Expansion Project": {
        "project_name": "North American Capacity Expansion",
        "investment_name": "Corporate Expansion Project",
        "cash_flows": [-2_500_000, 480_000, 620_000, 760_000, 890_000, 1_050_000],
        "description": "Incremental capacity investment with a five-year operating horizon.",
    },
    "Manufacturing Plant": {
        "project_name": "Advanced Components Facility",
        "investment_name": "Manufacturing Plant",
        "cash_flows": [-8_000_000, 1_150_000, 1_450_000, 1_800_000, 2_100_000, 2_350_000, 3_000_000],
        "description": "Greenfield manufacturing facility with ramp-up economics.",
    },
    "Acquisition Opportunity": {
        "project_name": "Project Atlas",
        "investment_name": "Acquisition Opportunity",
        "cash_flows": [-12_000_000, 1_700_000, 2_050_000, 2_400_000, 2_750_000, 3_100_000, 9_500_000],
        "description": "Strategic acquisition including a terminal exit value.",
    },
    "Real Estate Development": {
        "project_name": "Urban Mixed-Use Development",
        "investment_name": "Real Estate Development",
        "cash_flows": [-6_500_000, -1_000_000, 850_000, 1_250_000, 1_550_000, 9_000_000],
        "description": "Development-phase capital followed by lease-up and disposition.",
    },
    "Renewable Energy Project": {
        "project_name": "Solar Infrastructure Portfolio",
        "investment_name": "Renewable Energy Project",
        "cash_flows": [-10_000_000, 1_200_000, 1_300_000, 1_400_000, 1_500_000, 1_600_000, 1_700_000, 1_800_000, 1_900_000],
        "description": "Long-duration contracted infrastructure cash flows.",
    },
}
