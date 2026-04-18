"""用户设置相关 Pydantic schemas（API #7 GET / #8 PUT）。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import CashOrIncomeCurrency


class UserSettingResponse(BaseModel):
    """GET/PUT /user-settings 响应结构。"""

    model_config = ConfigDict(from_attributes=True)

    target_monthly_living: float
    target_living_currency: str
    target_passive_income: float
    target_passive_currency: str
    target_cash_savings: float
    target_cash_currency: str
    email: str | None
    updated_at: str


class UserSettingUpdate(BaseModel):
    """PUT /user-settings 请求体。所有字段选填（partial update）。"""

    target_monthly_living: float | None = Field(None, ge=0)
    target_living_currency: CashOrIncomeCurrency | None = None
    target_passive_income: float | None = Field(None, ge=0)
    target_passive_currency: CashOrIncomeCurrency | None = None
    target_cash_savings: float | None = Field(None, ge=0)
    target_cash_currency: CashOrIncomeCurrency | None = None
    email: str | None = None  # 格式校验由 router 手动处理（需映射 INVALID_EMAIL_FORMAT 错误码）
