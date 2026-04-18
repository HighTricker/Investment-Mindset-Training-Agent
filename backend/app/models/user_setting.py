"""UserSetting ORM。对应 user_settings 表。

MVP 单用户只有一行（id=1）；GET /user-settings 在无记录时自动补一条默认值。
SSOT：../../../开发文档/SQL_prompt_schema.md §表 user_settings
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserSetting(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_monthly_living: Mapped[float] = mapped_column(default=0)
    target_living_currency: Mapped[str] = mapped_column(default="CNY")
    target_passive_income: Mapped[float] = mapped_column(default=0)
    target_passive_currency: Mapped[str] = mapped_column(default="CNY")
    target_cash_savings: Mapped[float] = mapped_column(default=0)
    target_cash_currency: Mapped[str] = mapped_column(default="CNY")
    email: Mapped[str | None] = mapped_column(nullable=True)
    updated_at: Mapped[str] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
