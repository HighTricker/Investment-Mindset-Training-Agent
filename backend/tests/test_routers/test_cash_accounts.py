"""测试 API #9-#12 现金账户 CRUD。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ============================================================
# GET /cash-accounts
# ============================================================
def test_get_returns_seed_4_accounts(client: TestClient) -> None:
    """seed.sql 预插 4 条默认账户。"""
    resp = client.get("/api/cash-accounts")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["accounts"]) == 4
    names = [a["name"] for a in data["accounts"]]
    assert names == ["日常消费卡", "应急事件应对卡", "5年及以上不动卡", "资产卡"]
    assert all(a["currency"] == "CNY" for a in data["accounts"])
    assert all(a["amount"] == 0 for a in data["accounts"])


# ============================================================
# POST /cash-accounts
# ============================================================
def test_create_account_success(client: TestClient) -> None:
    resp = client.post(
        "/api/cash-accounts",
        json={"name": "余额宝", "amount": 10000, "currency": "CNY"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "余额宝"
    assert data["amount"] == 10000
    assert data["currency"] == "CNY"
    assert data["account_id"] >= 5  # 已有 4 条种子


def test_create_usd_account(client: TestClient) -> None:
    resp = client.post(
        "/api/cash-accounts",
        json={"name": "Chase USD", "amount": 2000, "currency": "USD"},
    )
    assert resp.status_code == 201
    assert resp.json()["currency"] == "USD"


def test_create_empty_name_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/cash-accounts",
        json={"name": "", "amount": 100, "currency": "CNY"},
    )
    assert resp.status_code == 422


def test_create_negative_amount_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/cash-accounts",
        json={"name": "测试", "amount": -100, "currency": "CNY"},
    )
    assert resp.status_code == 422


def test_create_invalid_currency_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/cash-accounts",
        json={"name": "测试", "amount": 100, "currency": "HKD"},
    )
    assert resp.status_code == 422


# ============================================================
# PUT /cash-accounts/{id}
# ============================================================
def test_put_updates_seed_account(client: TestClient) -> None:
    """对种子账户 id=1「日常消费卡」设金额。"""
    resp = client.put(
        "/api/cash-accounts/1",
        json={"amount": 5000},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["amount"] == 5000
    assert data["name"] == "日常消费卡"  # name 未变


def test_put_partial_update_only_name(client: TestClient) -> None:
    resp = client.put("/api/cash-accounts/1", json={"name": "招行活期"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "招行活期"
    assert data["currency"] == "CNY"  # 未动
    assert data["amount"] == 0


def test_put_nonexistent_returns_404(client: TestClient) -> None:
    resp = client.put("/api/cash-accounts/9999", json={"amount": 100})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"


def test_put_after_delete_returns_404(client: TestClient) -> None:
    client.delete("/api/cash-accounts/1")
    resp = client.put("/api/cash-accounts/1", json={"amount": 100})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"


def test_put_invalid_currency_rejected(client: TestClient) -> None:
    resp = client.put("/api/cash-accounts/1", json={"currency": "HKD"})
    assert resp.status_code == 422


# ============================================================
# DELETE /cash-accounts/{id}
# ============================================================
def test_delete_seed_account_returns_204(client: TestClient) -> None:
    resp = client.delete("/api/cash-accounts/1")
    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_removes_from_list(client: TestClient) -> None:
    client.delete("/api/cash-accounts/1")
    data = client.get("/api/cash-accounts").json()
    assert len(data["accounts"]) == 3
    assert all(a["account_id"] != 1 for a in data["accounts"])


def test_delete_nonexistent_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/cash-accounts/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"


def test_delete_twice_rejects_second(client: TestClient) -> None:
    assert client.delete("/api/cash-accounts/1").status_code == 204
    resp2 = client.delete("/api/cash-accounts/1")
    assert resp2.status_code == 404
