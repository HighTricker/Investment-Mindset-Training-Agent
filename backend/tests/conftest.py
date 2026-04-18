"""pytest 根配置 + 测试 fixtures。

fixtures 提供两层工具：
    - `fresh_db`：每个测试独立的临时 SQLite DB（含 schema + seed），避免污染真实 portfolio.db
    - `client`：FastAPI TestClient，自动 dep-override 让 get_db 指向 fresh_db
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

SCHEMA_SQL = BACKEND_ROOT / "app" / "db" / "schema.sql"
SEED_SQL = BACKEND_ROOT / "app" / "db" / "seed.sql"


@pytest.fixture
def fresh_db(tmp_path: Path):
    """每个测试开一个独立的临时 SQLite DB，已装 schema + seed，返回 sessionmaker。"""
    db_file = tmp_path / "test_portfolio.db"

    with sqlite3.connect(db_file) as raw:
        raw.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        raw.executescript(SEED_SQL.read_text(encoding="utf-8"))
        raw.commit()

    engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, conn_rec) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield SessionLocal
    engine.dispose()


@pytest.fixture
def client(fresh_db):
    """FastAPI TestClient，用 fresh_db override 掉全局 get_db。"""
    from app.core.database import get_db
    from app.main import app

    def override_get_db():
        db: Session = fresh_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
