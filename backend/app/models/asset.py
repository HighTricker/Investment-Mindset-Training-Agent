"""Asset ORM，对应 assets 表。

CHECK + 部分唯一索引由 schema.sql 在 DB 侧强制；ORM 只做字段映射。
SSOT：../../../开发文档/SQL_prompt_schema.md §表 assets
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str]
    name: Mapped[str]
    category: Mapped[str]
    currency: Mapped[str]
    is_active: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[str] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
