"""财富自由综合计算服务（API #15）。

接受 DB Session + 当前时间，编排 user_settings / cash_accounts / assets / transactions /
prices / exchange_rates / income 的读取，调用 calculators.py 的纯函数算衍生字段，
返回完整的 WealthFreedomMetrics 领域对象。

公式 SSOT：../../../开发文档/SQL_prompt_schema.md § P2.1 财富自由时间表计算说明
边界矩阵 SSOT：../../../开发文档/API_template.md § API #15 → 边界条件矩阵
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date as date_cls, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.cash_account import CashAccount
from app.models.exchange_rate import ExchangeRate
from app.models.income import Income
from app.models.price import Price
from app.models.transaction import Transaction
from app.models.user_setting import UserSetting
from app.schemas.metrics import AnalysisText, WealthFreedomMetrics
from app.services.calculators import (
    TransactionAggregate,
    aggregate_transactions,
    cumulative_return_rate,
    current_value_cny,
    total_return_rate,
)

logger = logging.getLogger(__name__)

HOURS_PER_MONTH = 420.0  # (24 - 8 睡眠 - 2 必要) × 30
SIMULATION_MAX_MONTHS = 1200  # 100 年硬上限，防死循环


@dataclass
class _AssetSnapshot:
    asset: Asset
    agg: TransactionAggregate
    current_price: float | None
    latest_rate: float | None
    monthly_first_price: float | None
    current_value_cny: float | None
    monthly_appreciation_cny: float  # 当月投资增值(CNY)
    earliest_buy_date: str | None    # 最早 buy 交易日，ISO


def compute_wealth_freedom(db: Session, now: datetime) -> WealthFreedomMetrics:
    today = now.date()
    current_month = today.strftime("%Y-%m")

    # 1) user_settings（无则默认 0）
    settings = db.execute(select(UserSetting).order_by(UserSetting.id).limit(1)).scalar_one_or_none()
    if settings is None:
        settings = UserSetting()

    def _to_cny(amount: float, currency: str) -> float:
        if currency == "CNY":
            return amount
        rate = _latest_rate(db, currency)
        return amount * (rate if rate is not None else 1.0)

    target_monthly_living_cny = _to_cny(settings.target_monthly_living, settings.target_living_currency)
    target_passive_income_cny = _to_cny(settings.target_passive_income, settings.target_passive_currency)
    target_cash_savings_cny = _to_cny(settings.target_cash_savings, settings.target_cash_currency)

    # 2) 当前总现金（CNY）
    cash_rows = db.execute(select(CashAccount).where(CashAccount.is_active == 1)).scalars().all()
    current_total_cash_cny = sum(_to_cny(c.amount, c.currency) for c in cash_rows)

    # 3) 活跃资产快照
    active_assets = db.execute(select(Asset).where(Asset.is_active == 1)).scalars().all()
    snapshots: list[_AssetSnapshot] = []
    total_initial_investment_cny = 0.0
    total_investment_value_cny = 0.0
    total_monthly_appreciation = 0.0

    for asset in active_assets:
        snap = _build_snapshot(db, asset, current_month)
        snapshots.append(snap)
        total_initial_investment_cny += snap.agg.total_initial_investment_cny
        if snap.current_value_cny is not None:
            total_investment_value_cny += snap.current_value_cny
        total_monthly_appreciation += snap.monthly_appreciation_cny

    # 4) 当月收入（CNY）
    current_month_income_cny = _total_income_cny(db, current_month)

    # 5) 衍生字段
    current_total_assets_cny = current_total_cash_cny + total_investment_value_cny
    monthly_savings_cny = current_month_income_cny - target_monthly_living_cny

    # achievement_rate = 当月投资增值 / target_passive_income(CNY)
    achievement_rate = (
        total_monthly_appreciation / target_passive_income_cny
        if target_passive_income_cny > 0
        else 0.0
    )

    # 时薪
    current_hourly_income_cny = (
        (current_month_income_cny + total_monthly_appreciation) / HOURS_PER_MONTH
    )
    target_hourly_income_cny = target_monthly_living_cny / HOURS_PER_MONTH

    # 年化收益率（边界矩阵）
    annualized = _compute_annualized(snapshots, total_initial_investment_cny, total_investment_value_cny, today)

    # required_investment_principal / target_total_assets
    if annualized is not None and annualized > 0:
        required_principal = target_passive_income_cny * 12 / annualized
    else:
        required_principal = None

    target_total_assets_cny = (required_principal or 0.0) + target_cash_savings_cny
    asset_gap_cny = target_total_assets_cny - current_total_assets_cny

    # 财富自由日期预测
    has_prediction = bool(
        active_assets
        and annualized is not None
        and annualized > 0
        and any(s.current_value_cny is not None for s in snapshots)
        and required_principal is not None
    )

    if has_prediction:
        predicted_date, years_months = _simulate_to_target(
            start_cash=current_total_cash_cny,
            start_investment=total_investment_value_cny,
            monthly_savings=monthly_savings_cny,
            annualized_rate=annualized,
            target_total=target_total_assets_cny,
            today=today,
        )
        if predicted_date is None:
            # 模拟上限内未达标（极端情况，如目标太高或收益太低）
            has_prediction = False
            analysis = None
        else:
            analysis = _build_analysis_text(
                annualized_rate=annualized,
                required_principal_cny=required_principal,
                monthly_savings_cny=monthly_savings_cny,
                years_months_str=years_months,
            )
    else:
        predicted_date = None
        years_months = None
        analysis = None

    return WealthFreedomMetrics(
        achievement_rate=achievement_rate,
        current_hourly_income_cny=current_hourly_income_cny,
        target_hourly_income_cny=target_hourly_income_cny,
        current_annualized_return_rate=annualized,
        required_investment_principal_cny=required_principal,
        target_total_assets_cny=target_total_assets_cny,
        current_total_cash_cny=current_total_cash_cny,
        current_total_investment_cny=total_investment_value_cny,
        current_total_assets_cny=current_total_assets_cny,
        asset_gap_cny=asset_gap_cny,
        monthly_savings_cny=monthly_savings_cny,
        predicted_freedom_date=predicted_date,
        years_months_remaining=years_months,
        analysis_text=analysis,
        has_prediction=has_prediction,
    )


# ============================================================
# 内部工具
# ============================================================
def _build_snapshot(db: Session, asset: Asset, current_month: str) -> _AssetSnapshot:
    """构造单个活跃资产的计算快照。"""
    tx_rows = (
        db.execute(select(Transaction).where(Transaction.asset_id == asset.id))
        .scalars()
        .all()
    )
    txs = [
        {"type": t.type, "quantity": t.quantity, "price": t.price, "exchange_rate_to_cny": t.exchange_rate_to_cny}
        for t in tx_rows
    ]
    agg = aggregate_transactions(txs)

    current_price = db.execute(
        select(Price.close_price)
        .where(Price.asset_id == asset.id)
        .order_by(Price.date.desc())
        .limit(1)
    ).scalar_one_or_none()

    latest_rate = 1.0 if asset.currency == "CNY" else _latest_rate(db, asset.currency)

    monthly_first = db.execute(
        select(Price.close_price)
        .where(
            Price.asset_id == asset.id,
            func.strftime("%Y-%m", Price.date) == current_month,
        )
        .order_by(Price.date.asc())
        .limit(1)
    ).scalar_one_or_none()

    value = None
    if current_price is not None and latest_rate is not None:
        value = current_value_cny(agg.current_quantity, float(current_price), float(latest_rate))

    # 当月增值 = 持仓 × (最新价 − 当月首日价) × 最新汇率
    monthly_appreciation = 0.0
    if (
        current_price is not None
        and monthly_first is not None
        and latest_rate is not None
        and agg.current_quantity > 0
    ):
        monthly_appreciation = (
            agg.current_quantity * (float(current_price) - float(monthly_first)) * float(latest_rate)
        )

    earliest_buy_date = db.execute(
        select(func.min(Transaction.date)).where(
            Transaction.asset_id == asset.id,
            Transaction.type == "buy",
        )
    ).scalar_one_or_none()

    return _AssetSnapshot(
        asset=asset,
        agg=agg,
        current_price=float(current_price) if current_price is not None else None,
        latest_rate=float(latest_rate) if latest_rate is not None else None,
        monthly_first_price=float(monthly_first) if monthly_first is not None else None,
        current_value_cny=value,
        monthly_appreciation_cny=monthly_appreciation,
        earliest_buy_date=earliest_buy_date,
    )


def _latest_rate(db: Session, currency: str) -> float | None:
    if currency == "CNY":
        return 1.0
    rate = db.execute(
        select(ExchangeRate.rate_to_cny)
        .where(ExchangeRate.currency == currency)
        .order_by(ExchangeRate.date.desc())
        .limit(1)
    ).scalar_one_or_none()
    return float(rate) if rate is not None else None


def _total_income_cny(db: Session, yyyy_mm: str) -> float:
    rows = (
        db.execute(
            select(Income).where(func.strftime("%Y-%m", Income.date) == yyyy_mm)
        )
        .scalars()
        .all()
    )
    total = 0.0
    for r in rows:
        if r.currency == "CNY":
            total += r.amount
        else:
            rate = _latest_rate(db, r.currency)
            total += r.amount * (rate if rate is not None else 1.0)
    return total


def _compute_annualized(
    snapshots: list[_AssetSnapshot],
    total_initial_cny: float,
    total_value_cny: float,
    today: date_cls,
) -> float | None:
    """年化收益率（边界矩阵）。
    - 无活跃资产 → None
    - 任一活跃资产缺价格（snapshot.current_value_cny is None）→ None
    - 持仓天数 = 0（同日买入同日查询）→ None
    - 总初始投入 = 0 → None
    """
    if not snapshots:
        return None
    if any(s.current_value_cny is None for s in snapshots):
        return None
    if total_initial_cny <= 0:
        return None

    # 持仓天数 = 最早 buy 日到今天
    earliest_dates = [s.earliest_buy_date for s in snapshots if s.earliest_buy_date]
    if not earliest_dates:
        return None
    earliest = min(earliest_dates)
    try:
        earliest_d = date_cls.fromisoformat(earliest)
    except ValueError:
        return None
    holding_days = (today - earliest_d).days
    if holding_days <= 0:
        return None

    tr = total_return_rate(total_value_cny, total_initial_cny)
    if tr is None:
        return None
    # annualized = (1 + tr) ^ (365 / days) − 1
    try:
        return (1.0 + tr) ** (365.0 / holding_days) - 1.0
    except (OverflowError, ZeroDivisionError):
        return None


def _simulate_to_target(
    *,
    start_cash: float,
    start_investment: float,
    monthly_savings: float,
    annualized_rate: float,
    target_total: float,
    today: date_cls,
) -> tuple[str | None, str | None]:
    """逐月模拟直到 总资产 ≥ target_total。返回 (ISO 日期, "Y年M月")。"""
    monthly_rate = (1.0 + annualized_rate) ** (1.0 / 12.0) - 1.0
    cash = start_cash
    investment = start_investment

    for months in range(1, SIMULATION_MAX_MONTHS + 1):
        cash = cash + monthly_savings
        investment = investment * (1.0 + monthly_rate)
        if cash + investment >= target_total:
            # 推算到 today + months 月
            predicted = _add_months(today, months)
            years = months // 12
            rem = months % 12
            years_months = f"{years}年{rem}月"
            return predicted.isoformat(), years_months

    return None, None


def _add_months(d: date_cls, months: int) -> date_cls:
    """date + months，月末越界自动 clamp 到当月最后一天。"""
    total_month = d.month + months
    year = d.year + (total_month - 1) // 12
    month = (total_month - 1) % 12 + 1
    # 当月最大天数
    if month == 12:
        next_month_start = date_cls(year + 1, 1, 1)
    else:
        next_month_start = date_cls(year, month + 1, 1)
    last_day_of_month = (next_month_start - date_cls.resolution).day if False else None
    # 简单计算：尝试同 day，溢出则退到当月末
    import calendar

    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return date_cls(year, month, day)


def _build_analysis_text(
    *,
    annualized_rate: float,
    required_principal_cny: float,
    monthly_savings_cny: float,
    years_months_str: str,
) -> AnalysisText:
    """生成两行自然语言说明。金额统一用「万」为单位。"""
    pct = annualized_rate * 100
    principal_wan = required_principal_cny / 10000
    savings_wan = monthly_savings_cny / 10000
    line1 = (
        f"按照你当前 {pct:.2f}% 的年化收益率，你需要 {principal_wan:.0f}万 的投资本金，"
        f"才能达到你的目标被动收入。"
    )
    line2 = (
        f"按照你当前每月储蓄 {savings_wan:.1f}万 及投资增值速度，"
        f"预计还需 {years_months_str} 达到目标。"
    )
    return AnalysisText(line1=line1, line2=line2)
