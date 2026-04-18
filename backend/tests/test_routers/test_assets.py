"""测试 API #2 POST /assets + #5 DELETE /assets/{id}。

用 fresh_db fixture（临时 SQLite），不污染真实 portfolio.db。
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

AAPL_PAYLOAD = {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "category": "美股",
    "currency": "USD",
    "quantity": 10,
    "price": 200.0,
    "exchange_rate_to_cny": 7.2,
    "date": "2026-04-18",
    "reason": "测试：看好 AI 算力",
}

MAOTAI_CNY_PAYLOAD = {
    "symbol": "600519",
    "name": "贵州茅台",
    "category": "中概股",
    "currency": "CNY",
    "quantity": 5,
    "price": 1500.0,
    "exchange_rate_to_cny": 1.0,
    "date": "2026-04-18",
    "reason": None,
}


# ============================================================
# POST /assets
# ============================================================
def test_add_asset_success(client: TestClient) -> None:
    resp = client.post("/api/assets", json=AAPL_PAYLOAD)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."
    assert data["is_active"] is True
    assert data["asset_id"] >= 1
    assert data["transaction_id"] >= 1
    assert data["created_at"]


def test_add_asset_cny_with_rate_one_succeeds(client: TestClient) -> None:
    resp = client.post("/api/assets", json=MAOTAI_CNY_PAYLOAD)
    assert resp.status_code == 201, resp.text


def test_add_asset_cny_with_non_one_rate_rejected(client: TestClient) -> None:
    payload = {**MAOTAI_CNY_PAYLOAD, "exchange_rate_to_cny": 1.01}
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_add_asset_duplicate_symbol_rejected(client: TestClient) -> None:
    # 第一次添加成功
    r1 = client.post("/api/assets", json=AAPL_PAYLOAD)
    assert r1.status_code == 201, r1.text
    # 第二次相同 symbol 应返回 DUPLICATE_ASSET
    r2 = client.post("/api/assets", json=AAPL_PAYLOAD)
    assert r2.status_code == 422, r2.text
    assert r2.json()["detail"]["code"] == "DUPLICATE_ASSET"


def test_add_asset_invalid_category_rejected(client: TestClient) -> None:
    payload = {**AAPL_PAYLOAD, "category": "不存在的类别"}
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 422


def test_add_asset_zero_quantity_rejected(client: TestClient) -> None:
    payload = {**AAPL_PAYLOAD, "quantity": 0}
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 422


def test_add_asset_negative_price_rejected(client: TestClient) -> None:
    payload = {**AAPL_PAYLOAD, "price": -1}
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 422


# ============================================================
# DELETE /assets/{asset_id}
# ============================================================
def _create_sample_asset(client: TestClient, payload: dict = AAPL_PAYLOAD) -> int:
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["asset_id"]


def test_delete_asset_success_returns_204(client: TestClient, fresh_db) -> None:
    asset_id = _create_sample_asset(client)
    resp = client.request("DELETE", f"/api/assets/{asset_id}", json={"reason": "不再看好"})
    assert resp.status_code == 204
    assert resp.content == b""

    # DB 侧核验：is_active=0 + 有一条 close transaction
    from sqlalchemy import select
    from app.models.asset import Asset
    from app.models.transaction import Transaction

    with fresh_db() as db:
        asset = db.get(Asset, asset_id)
        assert asset is not None
        assert asset.is_active == 0

        close_rows = db.execute(
            select(Transaction).where(
                Transaction.asset_id == asset_id, Transaction.type == "close"
            )
        ).scalars().all()
        assert len(close_rows) == 1
        close = close_rows[0]
        assert close.quantity == 0.0
        assert close.price == 0.0
        assert close.exchange_rate_to_cny == 1.0
        assert close.reason == "不再看好"


def test_delete_asset_without_body(client: TestClient) -> None:
    asset_id = _create_sample_asset(client)
    resp = client.delete(f"/api/assets/{asset_id}")
    assert resp.status_code == 204


def test_delete_asset_not_found_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/assets/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ASSET_NOT_FOUND"


def test_delete_asset_twice_rejects_second(client: TestClient) -> None:
    asset_id = _create_sample_asset(client)
    assert client.delete(f"/api/assets/{asset_id}").status_code == 204
    # 再次删除同一资产
    resp2 = client.delete(f"/api/assets/{asset_id}")
    assert resp2.status_code == 404
    assert resp2.json()["detail"]["code"] == "ASSET_NOT_FOUND"


def test_symbol_reusable_after_close(client: TestClient) -> None:
    """close 后同一 symbol 应该允许新建独立资产（新持仓周期）。"""
    asset_id = _create_sample_asset(client)
    assert client.delete(f"/api/assets/{asset_id}").status_code == 204

    # 重新添加 AAPL：应该创建新的 asset_id
    resp = client.post("/api/assets", json=AAPL_PAYLOAD)
    assert resp.status_code == 201, resp.text
    new_id = resp.json()["asset_id"]
    assert new_id != asset_id
