"""ExchangeRate ORM。

对应 `investment_data/portfolio.db` 的 exchange_rates 表。
SSOT：../../../开发文档/SQL_prompt_schema.md §表 exchange_rates
约束（UNIQUE(currency, date) + CHECK currency IN ...）由 schema.sql 在 DB 侧强制，
ORM 这里不重复声明（避免与 CREATE TABLE 命名冲突）。
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    currency: Mapped[str]
    rate_to_cny: Mapped[float]
    date: Mapped[str]
    created_at: Mapped[str] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
