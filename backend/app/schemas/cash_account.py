"""现金账户相关 Pydantic schemas（API #9-#12）。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import CashOrIncomeCurrency


class CashAccountItem(BaseModel):
    """列表 + 新增/修改响应共用的单条账户模型。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # validation_alias 让 model_validate(ORM) 从 `.id` 读取；JSON 输出仍是 account_id
    account_id: int = Field(..., validation_alias="id")
    name: str
    amount: float
    currency: str
    created_at: str
    updated_at: str


class CashAccountListResponse(BaseModel):
    accounts: list[CashAccountItem]


class CashAccountCreateRequest(BaseModel):
    """POST /cash-accounts 请求体。"""

    name: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)
    currency: CashOrIncomeCurrency


class CashAccountUpdateRequest(BaseModel):
    """PUT /cash-accounts/{id} 请求体。全部字段选填。"""

    name: str | None = Field(None, min_length=1)
    amount: float | None = Field(None, ge=0)
    currency: CashOrIncomeCurrency | None = None
