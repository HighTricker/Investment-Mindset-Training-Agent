"""交易（加仓/减仓）相关 Pydantic schemas。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AddTransactionRequest(BaseModel):
    """POST /transactions 请求体。仅支持 buy / sell；close 走 DELETE /assets。"""

    asset_id: int = Field(..., gt=0)
    type: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    exchange_rate_to_cny: float = Field(..., gt=0)
    date: str = Field(..., min_length=10)
    reason: str | None = None


class TransactionResponse(BaseModel):
    """POST /transactions 响应体。"""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    asset_id: int
    type: str
    quantity: float
    price: float
    date: str
    created_at: str
