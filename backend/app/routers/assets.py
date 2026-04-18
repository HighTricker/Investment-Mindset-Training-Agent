"""资产 routers（API #2 POST /assets、#5 DELETE /assets/{id}；#3 GET 在 2.2c 补）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.asset import Asset
from app.models.price import Price
from app.models.transaction import Transaction
from app.schemas.asset import AddAssetRequest, AddAssetResponse, DeleteAssetRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


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
    """创建资产并写入首笔 buy 交易。

    事务原子性：`assets` INSERT + `transactions` INSERT + `prices` INSERT（同日快照）
    必须同事务。部分唯一索引保证同一 symbol 在活跃资产里唯一。
    """
    # CNY 资产汇率必须为 1
    if req.currency == "CNY" and req.exchange_rate_to_cny != 1:
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.VALIDATION_ERROR,
            "CNY 资产 exchange_rate_to_cny 必须为 1",
        )

    # 活跃资产 symbol 唯一性校验
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
    db.flush()  # 拿到 asset.id

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

    # 同时把当日价格写入 prices 表：让 P1 首页立即有数据展示，无需等 refresh
    price_stmt = (
        sqlite_insert(Price)
        .values(asset_id=asset.id, date=req.date, close_price=req.price)
        .on_conflict_do_nothing(index_elements=["asset_id", "date"])
    )
    db.execute(price_stmt)

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
    """软删除：写一条 type='close' 交易 + 置 is_active=0，同事务。"""
    asset = db.get(Asset, asset_id)
    if asset is None or asset.is_active != 1:
        raise business_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.ASSET_NOT_FOUND,
            "资产不存在或已关闭",
        )

    today = datetime.now(timezone.utc).date().isoformat()
    reason = req.reason if req is not None else None

    # close 记录约定：quantity=0, price=0, exchange_rate_to_cny=1
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
    logger.info("asset closed: id=%s symbol=%s reason=%r", asset.id, asset.symbol, reason)
    # 204 No Content —— FastAPI 依据 status_code 自动不返回 body
