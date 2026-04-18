"""现金账户 routers（API #9 GET / #10 POST / #11 PUT / #12 DELETE）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.cash_account import CashAccount
from app.schemas.cash_account import (
    CashAccountCreateRequest,
    CashAccountItem,
    CashAccountListResponse,
    CashAccountUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cash-accounts", tags=["cash-accounts"])


@router.get(
    "",
    response_model=CashAccountListResponse,
    summary="获取现金账户列表（API #9）",
)
def list_cash_accounts(db: Session = Depends(get_db)) -> CashAccountListResponse:
    rows = (
        db.execute(
            select(CashAccount)
            .where(CashAccount.is_active == 1)
            .order_by(CashAccount.id.asc())
        )
        .scalars()
        .all()
    )
    return CashAccountListResponse(
        accounts=[CashAccountItem.model_validate(r) for r in rows]
    )


@router.post(
    "",
    response_model=CashAccountItem,
    status_code=status.HTTP_201_CREATED,
    summary="新增现金账户（API #10）",
)
def create_cash_account(
    req: CashAccountCreateRequest,
    db: Session = Depends(get_db),
) -> CashAccountItem:
    acct = CashAccount(
        name=req.name,
        amount=req.amount,
        currency=req.currency.value,
        is_active=1,
    )
    db.add(acct)
    db.commit()
    db.refresh(acct)
    logger.info("cash account created: id=%s name=%s", acct.id, acct.name)
    return CashAccountItem.model_validate(acct)


@router.put(
    "/{account_id}",
    response_model=CashAccountItem,
    summary="修改现金账户（API #11）",
)
def update_cash_account(
    req: CashAccountUpdateRequest,
    account_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> CashAccountItem:
    acct = db.get(CashAccount, account_id)
    if acct is None or acct.is_active != 1:
        raise business_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.ACCOUNT_NOT_FOUND,
            "账户不存在或已删除",
        )

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(acct, field, value)

    acct.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(acct)
    return CashAccountItem.model_validate(acct)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="软删除现金账户（API #12）",
)
def delete_cash_account(
    account_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> None:
    acct = db.get(CashAccount, account_id)
    if acct is None or acct.is_active != 1:
        raise business_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.ACCOUNT_NOT_FOUND,
            "账户不存在或已删除",
        )
    acct.is_active = 0
    acct.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    logger.info("cash account closed: id=%s name=%s", acct.id, acct.name)
