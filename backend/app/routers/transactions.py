"""交易 routers（API #4 POST /transactions 加仓/减仓）。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy import case, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.asset import Asset
from app.models.price import Price
from app.models.transaction import Transaction
from app.schemas.transaction import AddTransactionRequest, TransactionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="加仓 / 减仓（API #4）",
)
def add_transaction(
    req: AddTransactionRequest,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    asset = db.get(Asset, req.asset_id)
    if asset is None or asset.is_active != 1:
        raise business_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.ASSET_NOT_FOUND,
            "资产不存在或已关闭",
        )

    if asset.currency == "CNY" and req.exchange_rate_to_cny != 1:
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.VALIDATION_ERROR,
            "CNY 资产 exchange_rate_to_cny 必须为 1",
        )

    if req.type == "sell":
        current_qty = _get_current_quantity(db, asset.id)
        if req.quantity > current_qty:
            raise business_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                ErrorCode.INSUFFICIENT_POSITION,
                "卖出数量不能超过当前持仓",
                current_quantity=current_qty,
            )

    tx = Transaction(
        asset_id=asset.id,
        type=req.type,
        quantity=req.quantity,
        price=req.price,
        exchange_rate_to_cny=req.exchange_rate_to_cny,
        reason=req.reason,
        date=req.date,
    )
    db.add(tx)
    db.flush()

    # buy 时顺带写入当日价格快照（同 POST /assets 策略）
    if req.type == "buy":
        price_stmt = (
            sqlite_insert(Price)
            .values(asset_id=asset.id, date=req.date, close_price=req.price)
            .on_conflict_do_nothing(index_elements=["asset_id", "date"])
        )
        db.execute(price_stmt)

    db.commit()
    db.refresh(tx)

    return TransactionResponse(
        transaction_id=tx.id,
        asset_id=tx.asset_id,
        type=tx.type,
        quantity=tx.quantity,
        price=tx.price,
        date=tx.date,
        created_at=tx.created_at,
    )


def _get_current_quantity(db: Session, asset_id: int) -> float:
    """当前持仓 = SUM(buy.quantity) − SUM(sell.quantity)。close 不计入。"""
    signed_qty = case(
        (Transaction.type == "buy", Transaction.quantity),
        (Transaction.type == "sell", -Transaction.quantity),
        else_=0.0,
    )
    result = db.execute(
        select(func.coalesce(func.sum(signed_qty), 0.0)).where(
            Transaction.asset_id == asset_id
        )
    ).scalar_one()
    return float(result)
