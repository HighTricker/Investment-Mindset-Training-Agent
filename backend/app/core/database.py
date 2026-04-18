"""SQLAlchemy engine + SessionLocal + FastAPI `get_db` 依赖。

SQLite 特殊要求：
- connect_args `check_same_thread=False`：FastAPI 异步线程跨线程用同一 connection
- 每次新 connection 必须手动 `PRAGMA foreign_keys = ON`（SQLite 默认关闭）
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine: Engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency：每次 HTTP 请求开一个 session，结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
