"""资产相关 Pydantic schemas（请求/响应）。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AssetCategory, AssetCurrency


class AddAssetRequest(BaseModel):
    """POST /assets 请求体。"""

    symbol: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: AssetCategory
    currency: AssetCurrency
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0, description="原币单价")
    exchange_rate_to_cny: float = Field(..., gt=0)
    date: str = Field(..., min_length=10, description="ISO 8601 YYYY-MM-DD")
    reason: str | None = None


class AddAssetResponse(BaseModel):
    """POST /assets 响应体。"""

    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    transaction_id: int
    symbol: str
    name: str
    is_active: bool
    created_at: str


class DeleteAssetRequest(BaseModel):
    """DELETE /assets/{id} 请求体（选填）。"""

    reason: str | None = None
