"""测试 API #6 POST /market/refresh。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

AAPL = {
    "symbol": "AAPL", "name": "Apple Inc.", "category": "美股", "currency": "USD",
    "quantity": 10, "price": 200.0, "exchange_rate_to_cny": 7.0,
    "date": "2026-04-01",
}


def test_refresh_empty_portfolio_returns_zero_counts(client: TestClient) -> None:
    """无活跃资产时不调外部，直接返回 0 更新。"""
    resp = client.post("/api/market/refresh")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["prices_updated"] == 0
    assert data["rates_updated"] == 0
    assert data["failed_assets"] == []
    assert data["failed_currencies"] == []
    assert data["refreshed_at"]


@pytest.mark.integration
def test_refresh_updates_single_asset(client: TestClient, fresh_db) -> None:
    """1 个美股资产：调用后 prices 和 rates 各增加 1 条（今日）。"""
    assert client.post("/api/assets", json=AAPL).status_code == 201

    resp = client.post("/api/market/refresh")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["prices_updated"] == 1
    assert data["rates_updated"] == 1
    assert data["failed_assets"] == []
    assert data["failed_currencies"] == []

    # DB 侧核验今日记录
    from datetime import datetime, timezone
    from sqlalchemy import select

    from app.models.exchange_rate import ExchangeRate
    from app.models.price import Price

    today = datetime.now(timezone.utc).date().isoformat()
    with fresh_db() as db:
        price_rows = db.execute(
            select(Price).where(Price.date == today)
        ).scalars().all()
        rate_rows = db.execute(
            select(ExchangeRate).where(ExchangeRate.date == today)
        ).scalars().all()
        assert len(price_rows) == 1
        assert len(rate_rows) == 1
        assert price_rows[0].close_price > 0
        assert rate_rows[0].currency == "USD"
        assert rate_rows[0].rate_to_cny > 0
