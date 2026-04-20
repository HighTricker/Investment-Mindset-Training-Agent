"""资产 routers：POST / GET / DELETE /assets（API #2 #3 #5）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.asset import Asset
from app.models.exchange_rate import ExchangeRate
from app.models.price import Price
from app.models.transaction import Transaction
from app.schemas.asset import (
    AddAssetRequest,
    AddAssetResponse,
    AssetHeader,
    AssetItem,
    AssetListResponse,
    AssetSummary,
    AssetTransactionsResponse,
    BestWorstAsset,
    DeleteAssetRequest,
    TransactionDetailItem,
)
from app.services.calculators import (
    aggregate_transactions,
    cumulative_return_rate,
    current_value_cny,
    monthly_return_rate,
    position_ratio,
    total_return_rate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


# ============================================================
# POST /assets（API #2）
# ============================================================
@router.post(
    "",
    response_model=AddAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加资产（API #2）",
)
def add_asset(
    req: AddAssetRequest,
    db: Session = Depends(get_db),
) -> AddAssetResponse:
    """创建资产并写入首笔 buy 交易（assets + transactions + prices 同事务）。"""
    if req.currency == "CNY" and req.exchange_rate_to_cny != 1:
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.VALIDATION_ERROR,
            "CNY 资产 exchange_rate_to_cny 必须为 1",
        )

    existing_active = db.execute(
        select(Asset.id).where(Asset.symbol == req.symbol, Asset.is_active == 1)
    ).scalar_one_or_none()
    if existing_active is not None:
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.DUPLICATE_ASSET,
            "该资产已存在，请通过加仓操作",
        )

    asset = Asset(
        symbol=req.symbol,
        name=req.name,
        category=req.category.value,
        currency=req.currency.value,
        is_active=1,
    )
    db.add(asset)
    db.flush()

    tx = Transaction(
        asset_id=asset.id,
        type="buy",
        quantity=req.quantity,
        price=req.price,
        exchange_rate_to_cny=req.exchange_rate_to_cny,
        reason=req.reason,
        date=req.date,
    )
    db.add(tx)
    db.flush()

    price_stmt = (
        sqlite_insert(Price)
        .values(asset_id=asset.id, date=req.date, close_price=req.price)
        .on_conflict_do_nothing(index_elements=["asset_id", "date"])
    )
    db.execute(price_stmt)

    # 非 CNY 资产的汇率同步写入 exchange_rates（INSERT OR IGNORE）
    # 目的：让后续 GET /assets 能读到汇率快照（若用户跳过 symbol-lookup 直接 POST）
    if req.currency.value != "CNY":
        rate_stmt = (
            sqlite_insert(ExchangeRate)
            .values(
                currency=req.currency.value,
                rate_to_cny=req.exchange_rate_to_cny,
                date=req.date,
            )
            .on_conflict_do_nothing(index_elements=["currency", "date"])
        )
        db.execute(rate_stmt)

    db.commit()
    db.refresh(asset)
    db.refresh(tx)

    return AddAssetResponse(
        asset_id=asset.id,
        transaction_id=tx.id,
        symbol=asset.symbol,
        name=asset.name,
        is_active=bool(asset.is_active),
        created_at=asset.created_at,
    )


# ============================================================
# GET /assets（API #3）—— 核心聚合接口
# ============================================================
@router.get(
    "",
    response_model=AssetListResponse,
    summary="获取资产列表 + 聚合汇总（API #3）",
)
def list_assets(
    include_closed: bool = Query(
        False, description="true 时返回全部（含已关闭），false 仅返回活跃"
    ),
    db: Session = Depends(get_db),
) -> AssetListResponse:
    # 1) 查询资产
    stmt = select(Asset)
    if not include_closed:
        stmt = stmt.where(Asset.is_active == 1)
    assets = (
        db.execute(stmt.order_by(Asset.is_active.desc(), Asset.id.asc()))
        .scalars()
        .all()
    )

    active_assets = [a for a in assets if a.is_active == 1]

    # 2) 批量取活跃资产的 transactions（按 asset_id 归组）
    tx_by_asset: dict[int, list[dict]] = {}
    if active_assets:
        tx_rows = (
            db.execute(
                select(Transaction).where(
                    Transaction.asset_id.in_([a.id for a in active_assets])
                )
            )
            .scalars()
            .all()
        )
        for t in tx_rows:
            tx_by_asset.setdefault(t.asset_id, []).append(
                {
                    "type": t.type,
                    "quantity": t.quantity,
                    "price": t.price,
                    "exchange_rate_to_cny": t.exchange_rate_to_cny,
                }
            )

    current_month = datetime.now(timezone.utc).date().strftime("%Y-%m")

    # 3) 对每个活跃资产计算基础字段
    computed: dict[int, dict] = {}
    missing_price_count = 0
    for a in active_assets:
        agg = aggregate_transactions(tx_by_asset.get(a.id, []))

        current_price = db.execute(
            select(Price.close_price)
            .where(Price.asset_id == a.id)
            .order_by(Price.date.desc())
            .limit(1)
        ).scalar_one_or_none()
        if current_price is None:
            missing_price_count += 1

        if a.currency == "CNY":
            rate = 1.0
        else:
            rate = db.execute(
                select(ExchangeRate.rate_to_cny)
                .where(ExchangeRate.currency == a.currency)
                .order_by(ExchangeRate.date.desc())
                .limit(1)
            ).scalar_one_or_none()

        monthly_first = db.execute(
            select(Price.close_price)
            .where(
                Price.asset_id == a.id,
                func.strftime("%Y-%m", Price.date) == current_month,
            )
            .order_by(Price.date.asc())
            .limit(1)
        ).scalar_one_or_none()

        computed[a.id] = {
            "agg": agg,
            "current_price": (
                float(current_price) if current_price is not None else None
            ),
            "latest_rate": float(rate) if rate is not None else None,
            "monthly_first": (
                float(monthly_first) if monthly_first is not None else None
            ),
        }

    # 4) 全部活跃资产无价格 → PRICE_MISSING
    if active_assets and missing_price_count == len(active_assets):
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.PRICE_MISSING,
            "价格数据缺失，请先点击刷新",
        )

    # 5) 第一遍：单资产 value_cny、累计总值（为 position_ratio 做准备）
    total_value_cny = 0.0
    total_initial_cny = 0.0
    for a in active_assets:
        c = computed[a.id]
        agg = c["agg"]
        if c["current_price"] is not None and c["latest_rate"] is not None:
            value = current_value_cny(
                agg.current_quantity, c["current_price"], c["latest_rate"]
            )
            c["current_value_cny"] = value
            total_value_cny += value
        else:
            c["current_value_cny"] = None
        total_initial_cny += agg.total_initial_investment_cny

    # 6) 组装 AssetItem 列表
    items: list[AssetItem] = []
    for a in assets:
        if a.is_active == 1:
            c = computed[a.id]
            agg = c["agg"]
            cp = c["current_price"]
            rate = c["latest_rate"]
            value = c["current_value_cny"]
            items.append(
                AssetItem(
                    asset_id=a.id,
                    symbol=a.symbol,
                    name=a.name,
                    category=a.category,
                    currency=a.currency,
                    is_active=True,
                    initial_investment_cny=agg.total_initial_investment_cny,
                    quantity=agg.current_quantity,
                    cost_price_original=agg.cost_price_original,
                    current_price_original=cp,
                    position_ratio=(
                        position_ratio(value, total_value_cny)
                        if value is not None
                        else None
                    ),
                    exchange_rate_to_cny=rate,
                    current_value_cny=value,
                    cumulative_return_rate=(
                        cumulative_return_rate(cp, agg.cost_price_original)
                        if cp is not None
                        else None
                    ),
                    monthly_return_rate=(
                        monthly_return_rate(cp, c["monthly_first"])
                        if cp is not None
                        else None
                    ),
                )
            )
        else:
            items.append(
                AssetItem(
                    asset_id=a.id,
                    symbol=a.symbol,
                    name=a.name,
                    category=a.category,
                    currency=a.currency,
                    is_active=False,
                    initial_investment_cny=None,
                    quantity=None,
                    cost_price_original=None,
                    current_price_original=None,
                    position_ratio=None,
                    exchange_rate_to_cny=None,
                    current_value_cny=None,
                    cumulative_return_rate=None,
                    monthly_return_rate=None,
                )
            )

    # 7) summary
    active_items = [
        i for i in items if i.is_active and i.monthly_return_rate is not None
    ]
    best = (
        max(active_items, key=lambda i: i.monthly_return_rate)
        if active_items
        else None
    )
    worst = (
        min(active_items, key=lambda i: i.monthly_return_rate)
        if active_items
        else None
    )

    usd_to_cny = db.execute(
        select(ExchangeRate.rate_to_cny)
        .where(ExchangeRate.currency == "USD")
        .order_by(desc(ExchangeRate.date))
        .limit(1)
    ).scalar_one_or_none()

    summary = AssetSummary(
        total_initial_investment_cny=total_initial_cny,
        total_current_value_cny=total_value_cny,
        total_return_rate=total_return_rate(total_value_cny, total_initial_cny),
        total_profit_loss_cny=total_value_cny - total_initial_cny,
        usd_to_cny=float(usd_to_cny) if usd_to_cny is not None else None,
        best_asset=(
            BestWorstAsset(
                asset_id=best.asset_id,
                symbol=best.symbol,
                name=best.name,
                category=best.category,
                monthly_return_rate=best.monthly_return_rate,
            )
            if best is not None
            else None
        ),
        worst_asset=(
            BestWorstAsset(
                asset_id=worst.asset_id,
                symbol=worst.symbol,
                name=worst.name,
                category=worst.category,
                monthly_return_rate=worst.monthly_return_rate,
            )
            if worst is not None
            else None
        ),
    )

    return AssetListResponse(summary=summary, assets=items)


# ============================================================
# DELETE /assets/{asset_id}（API #5）
# ============================================================
@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="软删除资产（API #5，close 元操作）",
)
def delete_asset(
    asset_id: int = Path(..., gt=0),
    req: DeleteAssetRequest | None = None,
    db: Session = Depends(get_db),
) -> None:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.is_active != 1:
        raise business_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.ASSET_NOT_FOUND,
            "资产不存在或已关闭",
        )

    today = datetime.now(timezone.utc).date().isoformat()
    reason = req.reason if req is not None else None

    close_tx = Transaction(
        asset_id=asset.id,
        type="close",
        quantity=0.0,
        price=0.0,
        exchange_rate_to_cny=1.0,
        reason=reason,
        date=today,
    )
    db.add(close_tx)
    asset.is_active = 0

    db.commit()
    logger.info(
        "asset closed: id=%s symbol=%s reason=%r", asset.id, asset.symbol, reason
    )


# ============================================================
# GET /assets/{asset_id}/transactions（API #16）
# ============================================================
@router.get(
    "/{asset_id}/transactions",
    response_model=AssetTransactionsResponse,
    summary="获取单资产交易历史（API #16）",
)
def list_asset_transactions(
    asset_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> AssetTransactionsResponse:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise business_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.ASSET_NOT_FOUND,
            "资产不存在",
        )

    tx_rows = (
        db.execute(
            select(Transaction)
            .where(Transaction.asset_id == asset_id)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        .scalars()
        .all()
    )

    return AssetTransactionsResponse(
        asset=AssetHeader(
            asset_id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            is_active=bool(asset.is_active),
        ),
        transactions=[
            TransactionDetailItem(
                transaction_id=t.id,
                type=t.type,
                date=t.date,
                quantity=t.quantity,
                price=t.price,
                exchange_rate_to_cny=t.exchange_rate_to_cny,
                reason=t.reason,
            )
            for t in tx_rows
        ],
    )
