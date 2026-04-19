"""测试 API #16 GET /assets/{asset_id}/transactions（P3.1 单资产交易历史）。

用 fresh_db fixture（临时 SQLite），不污染真实 portfolio.db。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

AAPL_PAYLOAD = {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "category": "美股",
    "currency": "USD",
    "quantity": 10,
    "price": 200.0,
    "exchange_rate_to_cny": 7.2,
    "date": "2026-04-01",
    "reason": "看好 AI 算力需求",
}


def _create_aapl(client: TestClient, **overrides) -> int:
    payload = {**AAPL_PAYLOAD, **overrides}
    resp = client.post("/api/assets", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["asset_id"]


def _add_transaction(
    client: TestClient,
    asset_id: int,
    *,
    type_: str = "buy",
    quantity: float = 5,
    price: float = 210.0,
    exchange_rate_to_cny: float = 7.25,
    date: str = "2026-04-15",
    reason: str | None = "加仓",
) -> int:
    payload = {
        "asset_id": asset_id,
        "type": type_,
        "quantity": quantity,
        "price": price,
        "exchange_rate_to_cny": exchange_rate_to_cny,
        "date": date,
        "reason": reason,
    }
    resp = client.post("/api/transactions", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["transaction_id"]


# ============================================================
# GET /assets/{asset_id}/transactions
# ============================================================
def test_get_asset_transactions_active_single_buy(client: TestClient) -> None:
    """活跃资产仅首笔 buy：字段完整且 is_active=true。"""
    asset_id = _create_aapl(client)

    resp = client.get(f"/api/assets/{asset_id}/transactions")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["asset"] == {
        "asset_id": asset_id,
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "is_active": True,
    }

    assert len(data["transactions"]) == 1
    tx = data["transactions"][0]
    assert set(tx.keys()) == {
        "transaction_id",
        "type",
        "date",
        "quantity",
        "price",
        "exchange_rate_to_cny",
        "reason",
    }
    assert tx["type"] == "buy"
    assert tx["quantity"] == 10
    assert tx["price"] == 200.0
    assert tx["exchange_rate_to_cny"] == 7.2
    assert tx["reason"] == "看好 AI 算力需求"
    assert tx["date"] == "2026-04-01"


def test_get_asset_transactions_active_multiple_sorted_desc(
    client: TestClient,
) -> None:
    """3 笔不同日期的交易按 date DESC 排序。"""
    asset_id = _create_aapl(client, date="2026-04-01")
    _add_transaction(client, asset_id, date="2026-04-17", reason="补仓")
    _add_transaction(
        client, asset_id, type_="sell", quantity=2, date="2026-04-10", reason="获利了结一部分"
    )

    resp = client.get(f"/api/assets/{asset_id}/transactions")
    assert resp.status_code == 200, resp.text
    dates = [t["date"] for t in resp.json()["transactions"]]
    assert dates == ["2026-04-17", "2026-04-10", "2026-04-01"]


def test_get_asset_transactions_closed_asset_returns_history(
    client: TestClient,
) -> None:
    """已关闭资产也可查询，含 close 记录且 quantity=0 price=0。"""
    asset_id = _create_aapl(client, date="2026-04-01")
    _add_transaction(client, asset_id, date="2026-04-10")

    close_resp = client.request(
        "DELETE", f"/api/assets/{asset_id}", json={"reason": "不再看好"}
    )
    assert close_resp.status_code == 204

    resp = client.get(f"/api/assets/{asset_id}/transactions")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["asset"]["is_active"] is False
    assert len(data["transactions"]) == 3

    close_records = [t for t in data["transactions"] if t["type"] == "close"]
    assert len(close_records) == 1
    close = close_records[0]
    assert close["quantity"] == 0
    assert close["price"] == 0
    assert close["exchange_rate_to_cny"] == 1.0
    assert close["reason"] == "不再看好"


def test_get_asset_transactions_asset_not_found(client: TestClient) -> None:
    """asset_id 不存在返回 404 ASSET_NOT_FOUND。"""
    resp = client.get("/api/assets/9999/transactions")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ASSET_NOT_FOUND"


def test_get_asset_transactions_reason_nullable(client: TestClient) -> None:
    """reason 可为 null（close 无理由场景）。"""
    asset_id = _create_aapl(client, reason=None)

    resp = client.get(f"/api/assets/{asset_id}/transactions")
    assert resp.status_code == 200, resp.text
    assert resp.json()["transactions"][0]["reason"] is None


def test_get_asset_transactions_invalid_asset_id_zero(client: TestClient) -> None:
    """asset_id=0 被 Pydantic Path gt=0 校验拦截，返回 422。"""
    resp = client.get("/api/assets/0/transactions")
    assert resp.status_code == 422


def test_get_asset_transactions_same_date_multiple_secondary_sort_by_id(
    client: TestClient,
) -> None:
    """同日期多笔 transaction 按 id DESC 作次级排序（新交易优先）。"""
    asset_id = _create_aapl(client, date="2026-04-01")
    tx_id_2 = _add_transaction(client, asset_id, date="2026-04-10", reason="第二笔")
    tx_id_3 = _add_transaction(client, asset_id, date="2026-04-10", reason="第三笔")

    resp = client.get(f"/api/assets/{asset_id}/transactions")
    assert resp.status_code == 200, resp.text
    txs = resp.json()["transactions"]
    assert len(txs) == 3

    assert [t["date"] for t in txs] == ["2026-04-10", "2026-04-10", "2026-04-01"]
    assert txs[0]["transaction_id"] == tx_id_3
    assert txs[1]["transaction_id"] == tx_id_2
    assert txs[0]["transaction_id"] > txs[1]["transaction_id"] > txs[2]["transaction_id"]
