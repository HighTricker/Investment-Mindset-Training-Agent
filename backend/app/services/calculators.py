"""派生字段计算（纯函数，无 DB/外部依赖）。

输入已从 DB 读出的原始值，输出计算结果；上层 router 负责数据获取和编排。
SSOT：../../../开发文档/SQL_prompt_schema.md §表 transactions →「计算说明」
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class TransactionAggregate:
    """单资产的交易聚合结果。"""

    current_quantity: float
    total_cost_original: float           # SUM(buy.qty × buy.price) —— 仅 buy
    total_initial_investment_cny: float  # SUM(buy.qty × buy.price × buy.rate)
    cost_price_original: float           # 加权平均成本（原币）


def aggregate_transactions(txs: Iterable[Mapping[str, object]]) -> TransactionAggregate:
    """按交易记录汇总：持仓数量、原币成本、CNY 初始投入、原币加权平均成本。

    close 记录一律忽略（quantity=0 不影响持仓，也不代表真实买卖金额）。
    """
    qty_bought = 0.0
    qty_sold = 0.0
    total_cost = 0.0
    total_cny = 0.0
    for tx in txs:
        ttype = tx["type"]
        if ttype == "buy":
            q = float(tx["quantity"])
            p = float(tx["price"])
            r = float(tx["exchange_rate_to_cny"])
            qty_bought += q
            total_cost += q * p
            total_cny += q * p * r
        elif ttype == "sell":
            qty_sold += float(tx["quantity"])
        # close 忽略

    current_qty = qty_bought - qty_sold
    cost_price = total_cost / qty_bought if qty_bought > 0 else 0.0
    return TransactionAggregate(
        current_quantity=current_qty,
        total_cost_original=total_cost,
        total_initial_investment_cny=total_cny,
        cost_price_original=cost_price,
    )


def current_value_cny(quantity: float, price: float, rate_to_cny: float) -> float:
    """当前价值(CNY) = 持仓 × 最新收盘价 × 最新汇率。"""
    return quantity * price * rate_to_cny


def cumulative_return_rate(current_price: float, cost_price: float) -> float | None:
    """累计收益率 = (最新价 − 成本) / 成本。成本为 0 返回 None。"""
    if cost_price <= 0:
        return None
    return (current_price - cost_price) / cost_price


def monthly_return_rate(
    current_price: float, first_close_of_month: float | None
) -> float | None:
    """本月收益率 = (最新价 − 本月首交易日收盘价) / 本月首交易日收盘价。

    SSOT：SQL_prompt_schema.md line 117-120。当月无价格记录返回 None。
    """
    if first_close_of_month is None or first_close_of_month <= 0:
        return None
    return (current_price - first_close_of_month) / first_close_of_month


def position_ratio(
    asset_value_cny: float, total_active_value_cny: float
) -> float | None:
    """仓位占比 = 该资产当前价值(CNY) / 所有活跃资产合计(CNY)。"""
    if total_active_value_cny <= 0:
        return None
    return asset_value_cny / total_active_value_cny


def total_return_rate(
    total_value_cny: float, total_initial_cny: float
) -> float | None:
    """总收益率 = (当前总价值 − 总初始投入) / 总初始投入。"""
    if total_initial_cny <= 0:
        return None
    return (total_value_cny - total_initial_cny) / total_initial_cny
