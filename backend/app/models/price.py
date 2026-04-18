"""Price ORM，对应 prices 表。UNIQUE(asset_id, date) 在 DB 侧强制。"""
from __future__ import annotations

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"))
    date: Mapped[str]
    close_price: Mapped[float]
    created_at: Mapped[str] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
