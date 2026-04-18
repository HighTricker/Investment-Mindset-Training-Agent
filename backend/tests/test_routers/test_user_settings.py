"""测试 API #7 GET /user-settings + #8 PUT /user-settings。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_get_returns_seed_defaults(client: TestClient) -> None:
    """种子数据已有 1 条默认记录（seed.sql），不自动插入第二条。"""
    resp = client.get("/api/user-settings")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["target_monthly_living"] == 0
    assert data["target_passive_income"] == 0
    assert data["target_cash_savings"] == 0
    assert data["target_living_currency"] == "CNY"
    assert data["email"] is None
    assert data["updated_at"]


def test_put_partial_update_only_affects_sent_fields(client: TestClient) -> None:
    # 先读当前值
    r_before = client.get("/api/user-settings").json()

    # 只更新 target_monthly_living
    resp = client.put("/api/user-settings", json={"target_monthly_living": 15000.0})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["target_monthly_living"] == 15000.0
    # 其他字段不变
    assert data["target_passive_income"] == r_before["target_passive_income"]
    assert data["target_cash_savings"] == r_before["target_cash_savings"]


def test_put_all_fields_at_once(client: TestClient) -> None:
    resp = client.put(
        "/api/user-settings",
        json={
            "target_monthly_living": 18000,
            "target_living_currency": "CNY",
            "target_passive_income": 25000,
            "target_passive_currency": "CNY",
            "target_cash_savings": 600000,
            "target_cash_currency": "CNY",
            "email": "user@example.com",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["target_monthly_living"] == 18000
    assert data["target_passive_income"] == 25000
    assert data["target_cash_savings"] == 600000
    assert data["email"] == "user@example.com"


def test_put_persists_across_requests(client: TestClient) -> None:
    client.put("/api/user-settings", json={"email": "new@test.com"}).raise_for_status()
    resp = client.get("/api/user-settings")
    assert resp.json()["email"] == "new@test.com"


def test_put_invalid_email_returns_business_error(client: TestClient) -> None:
    resp = client.put("/api/user-settings", json={"email": "not-an-email"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_EMAIL_FORMAT"


def test_put_valid_email_variants(client: TestClient) -> None:
    for email in ["a@b.co", "user.name+tag@example.com", "x@sub.domain.io"]:
        resp = client.put("/api/user-settings", json={"email": email})
        assert resp.status_code == 200, f"{email}: {resp.text}"


def test_put_null_email_clears(client: TestClient) -> None:
    client.put("/api/user-settings", json={"email": "x@y.com"}).raise_for_status()
    resp = client.put("/api/user-settings", json={"email": None})
    assert resp.status_code == 200
    assert resp.json()["email"] is None


def test_put_empty_email_accepted_as_null(client: TestClient) -> None:
    """空字符串视为"未设置"，跳过格式校验。"""
    resp = client.put("/api/user-settings", json={"email": ""})
    assert resp.status_code == 200, resp.text


def test_put_negative_amount_rejected(client: TestClient) -> None:
    resp = client.put("/api/user-settings", json={"target_monthly_living": -1})
    assert resp.status_code == 422


def test_put_invalid_currency_rejected(client: TestClient) -> None:
    resp = client.put("/api/user-settings", json={"target_living_currency": "HKD"})
    # HKD 不在 CashOrIncomeCurrency (CNY/USD) → Pydantic 拒绝
    assert resp.status_code == 422


def test_put_usd_currency_accepted(client: TestClient) -> None:
    resp = client.put(
        "/api/user-settings",
        json={"target_passive_income": 2000, "target_passive_currency": "USD"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["target_passive_currency"] == "USD"
    assert data["target_passive_income"] == 2000


def test_put_updates_updated_at_timestamp(client: TestClient) -> None:
    r1 = client.get("/api/user-settings").json()
    ts1 = r1["updated_at"]
    client.put("/api/user-settings", json={"target_monthly_living": 100}).raise_for_status()
    r2 = client.get("/api/user-settings").json()
    assert r2["updated_at"] != ts1
