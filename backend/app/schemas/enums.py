"""全局枚举值。

SSOT：`../../../开发文档/fastapi_prompt_schema.md` 格子 3「全局枚举值一览」+
      `../../../开发文档/SQL_prompt_schema.md` 表字段 CHECK 约束。
前后端两套 schema（Python StrEnum / TypeScript union）保持字面值严格一致。
"""
from __future__ import annotations

from enum import StrEnum


class AssetCategory(StrEnum):
    US_STOCK = "美股"
    HK_STOCK = "港股"
    CN_STOCK = "中概股"
    CRYPTO = "加密货币"
    GOLD = "黄金"
    US_TREASURY = "美国国债"
    CN_TREASURY = "中国国债"


class AssetCurrency(StrEnum):
    """资产币种（6 种）。用于 assets / transactions。"""

    CNY = "CNY"
    USD = "USD"
    HKD = "HKD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"


class CashOrIncomeCurrency(StrEnum):
    """现金账户/收入/用户目标币种（2 种）。"""

    CNY = "CNY"
    USD = "USD"


class TransactionType(StrEnum):
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"


class IncomeCategory(StrEnum):
    LABOR = "纯劳动收入"
    CODE_MEDIA = "代码&自媒体收入"
    CAPITAL = "资本收入"
