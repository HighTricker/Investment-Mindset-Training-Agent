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


# ============================================================
# GET /assets 响应结构（API #3）
# ============================================================
class AssetItem(BaseModel):
    """资产明细项。已关闭资产的计算字段全部为 null。"""

    asset_id: int
    symbol: str
    name: str
    category: str
    currency: str
    is_active: bool
    initial_investment_cny: float | None
    quantity: float | None
    cost_price_original: float | None
    current_price_original: float | None
    position_ratio: float | None
    exchange_rate_to_cny: float | None
    current_value_cny: float | None
    cumulative_return_rate: float | None
    monthly_return_rate: float | None


class BestWorstAsset(BaseModel):
    """summary 里的最佳/最差资产（简化版，只含展示字段）。"""

    asset_id: int
    symbol: str
    name: str
    category: str
    monthly_return_rate: float


class AssetSummary(BaseModel):
    total_initial_investment_cny: float
    total_current_value_cny: float
    total_return_rate: float | None
    total_profit_loss_cny: float
    best_asset: BestWorstAsset | None
    worst_asset: BestWorstAsset | None


class AssetListResponse(BaseModel):
    summary: AssetSummary
    assets: list[AssetItem]
