"""SQLAlchemy DeclarativeBase，所有 ORM 模型继承自此。"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
