"""市场数据相关的 Pydantic schema。
服务层（market_data.py）返回 SymbolInfo；路由层组合汇率后返回 SymbolLookupResponse。
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SymbolInfo(BaseModel):
    """服务层查询单个 symbol 后得到的基本信息（不含汇率）。"""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., description="交易代码，如 AAPL / 00700.HK / BTC-USD / 601318")
    name: str = Field(..., description="资产名称，如 Apple Inc.")
    currency: str = Field(..., description="报价币种 CNY/USD/HKD/EUR/GBP/CHF")
    category: str = Field(..., description="资产类别：美股/港股/中概股/加密货币/黄金/美国国债/中国国债")
    current_price_original: float = Field(..., gt=0, description="当前原币报价")


class SymbolLookupResponse(SymbolInfo):
    """接口 #1 GET /market/symbol-lookup 的响应：在 SymbolInfo 基础上加汇率。"""

    exchange_rate_to_cny: float = Field(..., gt=0, description="1 单位原币 = 多少 CNY")


# ============================================================
# POST /market/refresh 响应（API #16）
# ============================================================
class FailedAsset(BaseModel):
    asset_id: int
    symbol: str
    error: str


class FailedCurrency(BaseModel):
    currency: str
    error: str


class RefreshResponse(BaseModel):
    prices_updated: int
    rates_updated: int
    failed_assets: list[FailedAsset]
    failed_currencies: list[FailedCurrency]
    refreshed_at: str
