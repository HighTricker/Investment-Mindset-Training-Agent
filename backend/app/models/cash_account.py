"""CashAccount ORM。对应 cash_accounts 表。

种子数据已预插 4 条（日常消费卡/应急事件应对卡/5年及以上不动卡/资产卡，全 CNY amount=0）。
is_active=0 即软删除。
SSOT：../../../开发文档/SQL_prompt_schema.md §表 cash_accounts
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CashAccount(Base):
    __tablename__ = "cash_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    amount: Mapped[float] = mapped_column(default=0)
    currency: Mapped[str] = mapped_column(default="CNY")
    is_active: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[str] = mapped_column(server_default=text("(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"))
    updated_at: Mapped[str] = mapped_column(server_default=text("(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"))
