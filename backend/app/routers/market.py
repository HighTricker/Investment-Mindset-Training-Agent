"""市场数据 routers。

对应 API_template.md：
  - #1 `GET /market/symbol-lookup` ✅ 本节实现
  - #16 `POST /market/refresh`      ⏳ 2.2c 实现
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.exchange_rate import ExchangeRate
from app.schemas.market import SymbolLookupResponse
from app.services.market_data import (
    ExternalSourceError,
    SymbolNotFoundError,
    fetch_exchange_rate,
    lookup_symbol,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


@router.get(
    "/symbol-lookup",
    response_model=SymbolLookupResponse,
    summary="查询交易代码（API #1）",
)
def get_symbol_lookup(
    symbol: str = Query(
        ...,
        min_length=1,
        description="交易代码，如 AAPL / 00700.HK / BTC-USD / 601318",
    ),
    db: Session = Depends(get_db),
) -> SymbolLookupResponse:
    """查询 symbol → 基本信息 + 当日汇率快照。

    业务流程：
    1. 调 market_data 服务查 name/currency/category/price（yfinance 或 akshare）
    2. 查本地 exchange_rates 表当日快照，缺失则拉外部并 `INSERT OR IGNORE`
    3. 返回 SymbolLookupResponse

    错误码映射：
    - SymbolNotFoundError → 422 INVALID_SYMBOL
    - ExternalSourceError → 502 EXTERNAL_SOURCE_FAILED
    """
    symbol = symbol.strip()
    try:
        info = lookup_symbol(symbol)
    except SymbolNotFoundError:
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.INVALID_SYMBOL,
            "未找到该交易代码，请检查后重试",
        )
    except ExternalSourceError as e:
        logger.warning("symbol-lookup external source failed: %s → %s", symbol, e)
        raise business_error(
            status.HTTP_502_BAD_GATEWAY,
            ErrorCode.EXTERNAL_SOURCE_FAILED,
            "数据源连接失败，请稍后重试",
        )

    rate = _get_or_fetch_exchange_rate(db, info.currency)
    return SymbolLookupResponse(**info.model_dump(), exchange_rate_to_cny=rate)


def _get_or_fetch_exchange_rate(db: Session, currency: str) -> float:
    """优先读当日本地汇率快照，缺失时拉外部并 INSERT OR IGNORE 写入。

    对齐 API #1 业务规则：
    「保证本接口返回的汇率与后续 POST /assets 保存 transactions.exchange_rate_to_cny
     是同一时点快照，避免用户前后看到不同金额」
    """
    if currency == "CNY":
        return 1.0

    today = datetime.now(timezone.utc).date().isoformat()

    cached = db.execute(
        select(ExchangeRate.rate_to_cny).where(
            ExchangeRate.currency == currency,
            ExchangeRate.date == today,
        )
    ).scalar_one_or_none()
    if cached is not None:
        return float(cached)

    try:
        rate = fetch_exchange_rate(currency)
    except (SymbolNotFoundError, ExternalSourceError) as e:
        logger.warning("exchange rate fetch failed: %s → %s", currency, e)
        raise business_error(
            status.HTTP_502_BAD_GATEWAY,
            ErrorCode.EXTERNAL_SOURCE_FAILED,
            "汇率数据源连接失败",
        )

    stmt = (
        sqlite_insert(ExchangeRate)
        .values(currency=currency, rate_to_cny=rate, date=today)
        .on_conflict_do_nothing(index_elements=["currency", "date"])
    )
    db.execute(stmt)
    db.commit()
    return rate
