"""Transaction ORM，对应 transactions 表。

close 记录字段约定（SSOT：SQL_prompt_schema.md）：
  - type='close'、quantity=0、price=0、exchange_rate_to_cny=1、reason 可空
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"))
    type: Mapped[str]  # buy / sell / close
    quantity: Mapped[float]
    price: Mapped[float]
    exchange_rate_to_cny: Mapped[float]
    reason: Mapped[str | None] = mapped_column(nullable=True)
    date: Mapped[str]
    created_at: Mapped[str] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
