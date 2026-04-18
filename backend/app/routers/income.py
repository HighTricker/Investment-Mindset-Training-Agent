"""收入 routers（API #13 GET、#14 POST）。

GET 支持 `?month=YYYY-MM` 查询任意月份；默认当前月。
不提供 PUT/DELETE（所有操作可复盘）。
"""
from __future__ import annotations

import logging
import re
from datetime import date as date_cls, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.exchange_rate import ExchangeRate
from app.models.income import Income
from app.schemas.enums import IncomeCategory
from app.schemas.income import (
    IncomeCategorySummary,
    IncomeCreateRequest,
    IncomeListResponse,
    IncomeRecord,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/income", tags=["income"])

MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
CATEGORIES = [
    IncomeCategory.LABOR.value,
    IncomeCategory.CODE_MEDIA.value,
    IncomeCategory.CAPITAL.value,
]


@router.get(
    "",
    response_model=IncomeListResponse,
    summary="获取收入列表 + 月度复盘汇总（API #13）",
)
def list_income(
    month: Optional[str] = Query(
        None,
        description="YYYY-MM 格式的视图月份；不传则为今天所在月",
    ),
    db: Session = Depends(get_db),
) -> IncomeListResponse:
    # view_month
    if month is None:
        view_month = datetime.now(timezone.utc).date().strftime("%Y-%m")
    else:
        if not MONTH_PATTERN.match(month):
            raise business_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                ErrorCode.VALIDATION_ERROR,
                "month 参数格式必须为 YYYY-MM",
            )
        view_month = month

    last_month = _prev_month(view_month)

    # 明细：当月全部记录
    records_rows = (
        db.execute(
            select(Income)
            .where(func.strftime("%Y-%m", Income.date) == view_month)
            .order_by(Income.date.desc())
        )
        .scalars()
        .all()
    )
    records = [IncomeRecord.model_validate(r) for r in records_rows]

    # summary：按类别聚合当月 + 上月（均换成 CNY）
    summary: list[IncomeCategorySummary] = []
    for cat in CATEGORIES:
        cur = _total_cny_for_category(db, cat, view_month)
        prev = _total_cny_for_category(db, cat, last_month)
        growth = (cur - prev) / prev if prev != 0 else None
        summary.append(
            IncomeCategorySummary(
                category=cat,
                current_month_total_cny=cur,
                last_month_total_cny=prev,
                growth_rate=growth,
            )
        )

    return IncomeListResponse(view_month=view_month, summary=summary, records=records)


@router.post(
    "",
    response_model=IncomeRecord,
    status_code=status.HTTP_201_CREATED,
    summary="新增收入记录（API #14）",
)
def create_income(
    req: IncomeCreateRequest,
    db: Session = Depends(get_db),
) -> IncomeRecord:
    row = Income(
        date=req.date,
        name=req.name,
        category=req.category.value,
        amount=req.amount,
        currency=req.currency.value,
        note=req.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("income created: id=%s cat=%s amount=%s %s", row.id, row.category, row.amount, row.currency)
    return IncomeRecord.model_validate(row)


# ============================================================
# 内部工具
# ============================================================
def _prev_month(yyyy_mm: str) -> str:
    """'2026-04' → '2026-03'；跨年正确处理。"""
    y, m = yyyy_mm.split("-")
    y, m = int(y), int(m)
    if m == 1:
        return f"{y - 1:04d}-12"
    return f"{y:04d}-{m - 1:02d}"


def _total_cny_for_category(db: Session, category: str, yyyy_mm: str) -> float:
    """指定类别在指定月份的 CNY 总和（USD 按 income.date 当日汇率换算）。"""
    rows = (
        db.execute(
            select(Income).where(
                Income.category == category,
                func.strftime("%Y-%m", Income.date) == yyyy_mm,
            )
        )
        .scalars()
        .all()
    )
    total = 0.0
    for r in rows:
        if r.currency == "CNY":
            total += r.amount
            continue
        rate = _rate_on_or_before(db, r.currency, r.date)
        if rate is None:
            # 汇率缺失：按 1.0 兜底（不阻塞复盘），日志记录
            logger.warning(
                "income currency %s has no rate before %s; fallback to 1.0", r.currency, r.date
            )
            rate = 1.0
        total += r.amount * rate
    return total


def _rate_on_or_before(db: Session, currency: str, target_date: str) -> Optional[float]:
    """取 ≤ target_date 的最近一条汇率（若当日无记录则顺延到最近的交易日记录）。"""
    rate = db.execute(
        select(ExchangeRate.rate_to_cny)
        .where(
            ExchangeRate.currency == currency,
            ExchangeRate.date <= target_date,
        )
        .order_by(ExchangeRate.date.desc())
        .limit(1)
    ).scalar_one_or_none()
    return float(rate) if rate is not None else None
