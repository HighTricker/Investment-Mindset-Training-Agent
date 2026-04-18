"""Income ORM。对应 income 表。

不支持 DELETE / PUT（所有操作可复盘；录错通过新增负数 amount 反向记录冲正）。
SSOT：../../../开发文档/SQL_prompt_schema.md §表 income
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Income(Base):
    __tablename__ = "income"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[str]
    name: Mapped[str]
    category: Mapped[str]
    amount: Mapped[float]
    currency: Mapped[str] = mapped_column(default="CNY")
    note: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
