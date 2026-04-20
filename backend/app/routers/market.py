"""市场数据 routers（API #1 symbol-lookup、#6 refresh）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.asset import Asset
from app.models.exchange_rate import ExchangeRate
from app.models.price import Price
from app.schemas.market import (
    FailedAsset,
    FailedCurrency,
    RefreshResponse,
    SymbolLookupResponse,
)
from app.services.market_data import (
    ExternalSourceError,
    SymbolNotFoundError,
    fetch_current_price,
    fetch_exchange_rate,
    lookup_symbol,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


# ============================================================
# GET /market/symbol-lookup（API #1）
# ============================================================
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
    usd_to_cny = (
        rate if info.currency == "USD" else _get_or_fetch_exchange_rate(db, "USD")
    )
    return SymbolLookupResponse(
        **info.model_dump(),
        exchange_rate_to_cny=rate,
        usd_to_cny=usd_to_cny,
    )


def _get_or_fetch_exchange_rate(db: Session, currency: str) -> float:
    """优先读当日本地汇率快照，缺失时拉外部并 INSERT OR IGNORE 写入。"""
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


# ============================================================
# POST /market/refresh（API #6）
# ============================================================
@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="刷新活跃资产价格与汇率（API #6）",
)
def refresh_market_data(db: Session = Depends(get_db)) -> RefreshResponse:
    """批量刷新 is_active=1 资产的 prices + 涉及币种的 exchange_rates。

    策略：
    - UPSERT（`ON CONFLICT DO UPDATE`）覆盖同日重复记录
    - 单条失败不阻塞整体；失败资产/币种列在返回体 `failed_*` 数组
    - 所有资产都失败时返回 502 EXTERNAL_SOURCE_FAILED
    """
    today = datetime.now(timezone.utc).date().isoformat()

    active_assets = (
        db.execute(select(Asset).where(Asset.is_active == 1)).scalars().all()
    )

    failed_assets: list[FailedAsset] = []
    prices_updated = 0
    for asset in active_assets:
        try:
            price = fetch_current_price(asset.symbol, asset.category)
        except (SymbolNotFoundError, ExternalSourceError) as e:
            failed_assets.append(
                FailedAsset(asset_id=asset.id, symbol=asset.symbol, error=str(e))
            )
            continue

        upsert_price = (
            sqlite_insert(Price)
            .values(asset_id=asset.id, date=today, close_price=price)
            .on_conflict_do_update(
                index_elements=["asset_id", "date"],
                set_={"close_price": price},
            )
        )
        db.execute(upsert_price)
        prices_updated += 1

    currencies: list[str] = (
        db.execute(
            select(Asset.currency)
            .distinct()
            .where(Asset.is_active == 1, Asset.currency != "CNY")
        )
        .scalars()
        .all()
    )

    failed_currencies: list[FailedCurrency] = []
    rates_updated = 0
    for currency in currencies:
        try:
            rate = fetch_exchange_rate(currency)
        except (SymbolNotFoundError, ExternalSourceError) as e:
            failed_currencies.append(FailedCurrency(currency=currency, error=str(e)))
            continue

        upsert_rate = (
            sqlite_insert(ExchangeRate)
            .values(currency=currency, rate_to_cny=rate, date=today)
            .on_conflict_do_update(
                index_elements=["currency", "date"],
                set_={"rate_to_cny": rate},
            )
        )
        db.execute(upsert_rate)
        rates_updated += 1

    db.commit()

    if active_assets and len(failed_assets) == len(active_assets):
        raise business_error(
            status.HTTP_502_BAD_GATEWAY,
            ErrorCode.EXTERNAL_SOURCE_FAILED,
            "所有资产刷新失败，请稍后重试",
        )

    return RefreshResponse(
        prices_updated=prices_updated,
        rates_updated=rates_updated,
        failed_assets=failed_assets,
        failed_currencies=failed_currencies,
        refreshed_at=datetime.now(timezone.utc).isoformat(),
    )
