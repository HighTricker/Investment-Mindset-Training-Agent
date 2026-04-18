"""测试 API #4 POST /transactions（加仓/减仓 + 持仓校验）。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

AAPL_ASSET = {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "category": "美股",
    "currency": "USD",
    "quantity": 10,
    "price": 200.0,
    "exchange_rate_to_cny": 7.2,
    "date": "2026-04-18",
    "reason": "首笔 buy",
}


def _create_asset(client: TestClient, payload: dict = AAPL_ASSET) -> int:
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["asset_id"]


# ============================================================
# buy
# ============================================================
def test_buy_success(client: TestClient) -> None:
    asset_id = _create_asset(client)
    resp = client.post(
        "/api/transactions",
        json={
            "asset_id": asset_id,
            "type": "buy",
            "quantity": 5,
            "price": 210.0,
            "exchange_rate_to_cny": 7.25,
            "date": "2026-04-18",
            "reason": "补仓",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["asset_id"] == asset_id
    assert data["type"] == "buy"
    assert data["quantity"] == 5


# ============================================================
# sell
# ============================================================
def test_sell_within_position_success(client: TestClient) -> None:
    asset_id = _create_asset(client)  # 建仓 10 股
    resp = client.post(
        "/api/transactions",
        json={
            "asset_id": asset_id,
            "type": "sell",
            "quantity": 3,
            "price": 220.0,
            "exchange_rate_to_cny": 7.2,
            "date": "2026-04-18",
            "reason": "止盈",
        },
    )
    assert resp.status_code == 201, resp.text


def test_sell_exceeds_position_rejected(client: TestClient) -> None:
    asset_id = _create_asset(client)  # 建仓 10 股
    resp = client.post(
        "/api/transactions",
        json={
            "asset_id": asset_id,
            "type": "sell",
            "quantity": 11,  # > 10
            "price": 220.0,
            "exchange_rate_to_cny": 7.2,
            "date": "2026-04-18",
        },
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["detail"]["code"] == "INSUFFICIENT_POSITION"
    assert body["detail"]["details"]["current_quantity"] == 10


def test_sell_exact_position_depletes_to_zero(client: TestClient) -> None:
    asset_id = _create_asset(client)  # 10 股
    resp = client.post(
        "/api/transactions",
        json={
            "asset_id": asset_id,
            "type": "sell",
            "quantity": 10,  # == 10
            "price": 220.0,
            "exchange_rate_to_cny": 7.2,
            "date": "2026-04-18",
        },
    )
    assert resp.status_code == 201, resp.text


def test_sell_after_partial_sells_tracks_running_balance(client: TestClient) -> None:
    asset_id = _create_asset(client)  # 10 股
    # 卖 3 剩 7
    r1 = client.post("/api/transactions", json={
        "asset_id": asset_id, "type": "sell", "quantity": 3,
        "price": 210.0, "exchange_rate_to_cny": 7.2, "date": "2026-04-18",
    })
    assert r1.status_code == 201
    # 再卖 8 超过剩余 7
    r2 = client.post("/api/transactions", json={
        "asset_id": asset_id, "type": "sell", "quantity": 8,
        "price": 210.0, "exchange_rate_to_cny": 7.2, "date": "2026-04-18",
    })
    assert r2.status_code == 422
    assert r2.json()["detail"]["details"]["current_quantity"] == 7


# ============================================================
# 异常路径
# ============================================================
def test_asset_not_found(client: TestClient) -> None:
    resp = client.post("/api/transactions", json={
        "asset_id": 9999, "type": "buy", "quantity": 1,
        "price": 100.0, "exchange_rate_to_cny": 7.0, "date": "2026-04-18",
    })
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ASSET_NOT_FOUND"


def test_inactive_asset_not_found(client: TestClient) -> None:
    asset_id = _create_asset(client)
    client.delete(f"/api/assets/{asset_id}")  # close
    resp = client.post("/api/transactions", json={
        "asset_id": asset_id, "type": "buy", "quantity": 1,
        "price": 100.0, "exchange_rate_to_cny": 7.0, "date": "2026-04-18",
    })
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ASSET_NOT_FOUND"


def test_cny_asset_with_non_one_rate_rejected(client: TestClient) -> None:
    asset_id = _create_asset(client, {
        "symbol": "600519", "name": "贵州茅台",
        "category": "中概股", "currency": "CNY",
        "quantity": 5, "price": 1500.0, "exchange_rate_to_cny": 1.0,
        "date": "2026-04-18",
    })
    resp = client.post("/api/transactions", json={
        "asset_id": asset_id, "type": "buy", "quantity": 1,
        "price": 1600.0, "exchange_rate_to_cny": 1.05,  # ≠ 1 for CNY asset
        "date": "2026-04-18",
    })
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_close_type_rejected_by_schema(client: TestClient) -> None:
    """type='close' 不在本接口允许列表（Pydantic Literal['buy','sell']）。"""
    asset_id = _create_asset(client)
    resp = client.post("/api/transactions", json={
        "asset_id": asset_id, "type": "close", "quantity": 0,
        "price": 0, "exchange_rate_to_cny": 1.0, "date": "2026-04-18",
    })
    assert resp.status_code == 422  # FastAPI 自动


def test_zero_quantity_rejected_by_schema(client: TestClient) -> None:
    asset_id = _create_asset(client)
    resp = client.post("/api/transactions", json={
        "asset_id": asset_id, "type": "buy", "quantity": 0,
        "price": 200.0, "exchange_rate_to_cny": 7.2, "date": "2026-04-18",
    })
    assert resp.status_code == 422
