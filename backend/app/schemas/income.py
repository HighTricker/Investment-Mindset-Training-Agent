"""收入相关 Pydantic schemas（API #13 GET / #14 POST）。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import CashOrIncomeCurrency, IncomeCategory


class IncomeRecord(BaseModel):
    """明细行（GET /income 的 records 元素 + POST /income 响应）。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    income_id: int = Field(..., validation_alias="id")
    date: str
    name: str
    category: str
    amount: float
    currency: str
    note: str | None
    created_at: str


class IncomeCategorySummary(BaseModel):
    """某类别的当月/上月汇总（CNY 换算后）+ 同比增长率。"""

    category: str
    current_month_total_cny: float
    last_month_total_cny: float
    growth_rate: float | None  # 上月为 0 时 null


class IncomeListResponse(BaseModel):
    view_month: str  # YYYY-MM
    summary: list[IncomeCategorySummary]
    records: list[IncomeRecord]


class IncomeCreateRequest(BaseModel):
    """POST /income 请求体。"""

    date: str = Field(..., min_length=10)
    name: str = Field(..., min_length=1)
    category: IncomeCategory
    amount: float  # 可为负（冲正）
    currency: CashOrIncomeCurrency
    note: str | None = None
