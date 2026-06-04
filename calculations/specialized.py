"""Specialized real estate and private equity return calculations."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import calculate_metrics


@dataclass(frozen=True)
class RealEstateAnalysis:
    cash_flows: list[float]
    irr: float | None
    npv: float
    equity_multiple: float


@dataclass(frozen=True)
class SponsorReturns:
    cash_flows: list[float]
    irr: float | None
    npv: float
    money_on_money: float


def analyze_real_estate(
    purchase_price: float,
    annual_rental_income: float,
    annual_expenses: float,
    exit_value: float,
    hold_period: int,
    discount_rate: float,
) -> RealEstateAnalysis:
    noi = annual_rental_income - annual_expenses
    flows = [-purchase_price] + [noi] * hold_period
    flows[-1] += exit_value
    metrics = calculate_metrics(
        flows,
        discount_rate,
        discount_rate,
        discount_rate,
        discount_rate,
        discount_rate,
    )
    total_distributions = sum(flow for flow in flows if flow > 0)
    return RealEstateAnalysis(
        flows,
        metrics.irr,
        metrics.npv,
        total_distributions / purchase_price if purchase_price else 0.0,
    )


def analyze_sponsor_returns(
    entry_equity: float,
    annual_cash_distributions: float,
    exit_equity: float,
    hold_period: int,
    discount_rate: float,
) -> SponsorReturns:
    flows = [-entry_equity] + [annual_cash_distributions] * hold_period
    flows[-1] += exit_equity
    metrics = calculate_metrics(
        flows,
        discount_rate,
        discount_rate,
        discount_rate,
        discount_rate,
        discount_rate,
    )
    total_distributions = sum(flow for flow in flows if flow > 0)
    return SponsorReturns(
        flows,
        metrics.irr,
        metrics.npv,
        total_distributions / entry_equity if entry_equity else 0.0,
    )
