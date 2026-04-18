"""派生字段计算单元测试（纯函数，不联网不依赖 DB）。"""
from __future__ import annotations

import pytest

from app.services.calculators import (
    aggregate_transactions,
    cumulative_return_rate,
    current_value_cny,
    monthly_return_rate,
    position_ratio,
    total_return_rate,
)


# ============================================================
# aggregate_transactions
# ============================================================
def _tx(type_: str, qty: float, price: float, rate: float = 1.0) -> dict:
    return {"type": type_, "quantity": qty, "price": price, "exchange_rate_to_cny": rate}


def test_aggregate_buy_only() -> None:
    agg = aggregate_transactions([_tx("buy", 10, 100, 7.0)])
    assert agg.current_quantity == 10
    assert agg.total_cost_original == 1000
    assert agg.total_initial_investment_cny == 7000
    assert agg.cost_price_original == 100


def test_aggregate_multiple_buys_weighted_avg() -> None:
    agg = aggregate_transactions(
        [_tx("buy", 10, 100, 7.0), _tx("buy", 5, 120, 7.2)]
    )
    assert agg.current_quantity == 15
    assert agg.total_cost_original == pytest.approx(1000 + 600)
    assert agg.cost_price_original == pytest.approx(1600 / 15)


def test_aggregate_buy_then_sell_reduces_position_not_cost() -> None:
    """sell 减持仓但 cost_price_original 仍基于 buy 成本累计（MVP 加权平均）。"""
    agg = aggregate_transactions(
        [_tx("buy", 10, 100, 7.0), _tx("sell", 3, 110, 7.0)]
    )
    assert agg.current_quantity == 7
    assert agg.cost_price_original == 100  # buy 平均成本未变
    assert agg.total_initial_investment_cny == pytest.approx(7000)


def test_aggregate_close_ignored() -> None:
    """close 是元操作，quantity=0 price=0，不影响任何汇总。"""
    agg = aggregate_transactions(
        [_tx("buy", 10, 100), _tx("close", 0, 0, 1.0)]
    )
    assert agg.current_quantity == 10
    assert agg.total_cost_original == 1000


def test_aggregate_empty() -> None:
    agg = aggregate_transactions([])
    assert agg.current_quantity == 0
    assert agg.cost_price_original == 0
    assert agg.total_initial_investment_cny == 0


# ============================================================
# 纯计算
# ============================================================
def test_current_value_cny() -> None:
    assert current_value_cny(10, 200, 7.2) == pytest.approx(14400)


def test_cumulative_return_rate_positive() -> None:
    assert cumulative_return_rate(120, 100) == pytest.approx(0.2)


def test_cumulative_return_rate_negative() -> None:
    assert cumulative_return_rate(80, 100) == pytest.approx(-0.2)


def test_cumulative_return_rate_zero_cost_returns_none() -> None:
    assert cumulative_return_rate(100, 0) is None


def test_monthly_return_rate() -> None:
    assert monthly_return_rate(110, 100) == pytest.approx(0.1)


def test_monthly_return_rate_first_none() -> None:
    assert monthly_return_rate(110, None) is None


def test_monthly_return_rate_first_zero() -> None:
    assert monthly_return_rate(110, 0) is None


def test_position_ratio() -> None:
    assert position_ratio(3000, 10000) == pytest.approx(0.3)


def test_position_ratio_zero_total_returns_none() -> None:
    assert position_ratio(3000, 0) is None


def test_total_return_rate() -> None:
    assert total_return_rate(120000, 100000) == pytest.approx(0.2)


def test_total_return_rate_zero_initial_returns_none() -> None:
    assert total_return_rate(0, 0) is None
