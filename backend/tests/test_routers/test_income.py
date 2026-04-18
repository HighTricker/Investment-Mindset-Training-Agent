"""测试 API #13 GET /income + #14 POST /income（含月度聚合 + 增长率）。"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


def _current_month() -> str:
    return datetime.now(timezone.utc).date().strftime("%Y-%m")


# ============================================================
# POST /income
# ============================================================
def test_create_income_cny_success(client: TestClient) -> None:
    resp = client.post(
        "/api/income",
        json={
            "date": "2026-04-15",
            "name": "工资",
            "category": "纯劳动收入",
            "amount": 15000,
            "currency": "CNY",
            "note": None,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["income_id"] >= 1
    assert data["amount"] == 15000
    assert data["category"] == "纯劳动收入"


def test_create_income_negative_amount_allowed(client: TestClient) -> None:
    """负数 amount 代表冲正记录，允许创建。"""
    resp = client.post(
        "/api/income",
        json={
            "date": "2026-04-15",
            "name": "冲正",
            "category": "纯劳动收入",
            "amount": -1000,
            "currency": "CNY",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["amount"] == -1000


def test_create_invalid_category_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/income",
        json={
            "date": "2026-04-15",
            "name": "测试",
            "category": "不存在的类别",
            "amount": 100,
            "currency": "CNY",
        },
    )
    assert resp.status_code == 422


def test_create_invalid_currency_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/income",
        json={
            "date": "2026-04-15",
            "name": "工资",
            "category": "纯劳动收入",
            "amount": 100,
            "currency": "HKD",  # 不在 CashOrIncomeCurrency
        },
    )
    assert resp.status_code == 422


# ============================================================
# GET /income
# ============================================================
def test_get_empty_returns_3_category_zero_summary(client: TestClient) -> None:
    resp = client.get("/api/income")
    assert resp.status_code == 200
    data = resp.json()
    assert data["view_month"] == _current_month()
    assert data["records"] == []
    assert len(data["summary"]) == 3
    cats = [s["category"] for s in data["summary"]]
    assert set(cats) == {"纯劳动收入", "代码&自媒体收入", "资本收入"}
    assert all(s["current_month_total_cny"] == 0 for s in data["summary"])
    assert all(s["last_month_total_cny"] == 0 for s in data["summary"])
    assert all(s["growth_rate"] is None for s in data["summary"])


def test_get_with_records_summary_aggregation(client: TestClient) -> None:
    """本月 2 条纯劳动收入；上月 0 → growth_rate null（上月为 0）。"""
    cur_m = _current_month()
    client.post("/api/income", json={
        "date": f"{cur_m}-05", "name": "工资1", "category": "纯劳动收入",
        "amount": 10000, "currency": "CNY",
    }).raise_for_status()
    client.post("/api/income", json={
        "date": f"{cur_m}-20", "name": "工资2", "category": "纯劳动收入",
        "amount": 5000, "currency": "CNY",
    }).raise_for_status()

    data = client.get("/api/income").json()
    labor = next(s for s in data["summary"] if s["category"] == "纯劳动收入")
    assert labor["current_month_total_cny"] == 15000
    assert labor["last_month_total_cny"] == 0
    assert labor["growth_rate"] is None


def test_growth_rate_positive(client: TestClient) -> None:
    """上月 10000，本月 15000 → growth_rate = 0.5。"""
    cur_m = _current_month()
    # 上月
    last_y, last_m = _prev(cur_m)
    client.post("/api/income", json={
        "date": f"{last_y:04d}-{last_m:02d}-15",
        "name": "上月工资", "category": "纯劳动收入",
        "amount": 10000, "currency": "CNY",
    }).raise_for_status()
    # 本月
    client.post("/api/income", json={
        "date": f"{cur_m}-15", "name": "本月工资", "category": "纯劳动收入",
        "amount": 15000, "currency": "CNY",
    }).raise_for_status()

    data = client.get("/api/income").json()
    labor = next(s for s in data["summary"] if s["category"] == "纯劳动收入")
    assert labor["current_month_total_cny"] == 15000
    assert labor["last_month_total_cny"] == 10000
    assert labor["growth_rate"] == pytest.approx(0.5)


def test_negative_growth_rate(client: TestClient) -> None:
    """上月 1000，本月 0 → -1.0（彻底没收入）。"""
    cur_m = _current_month()
    last_y, last_m = _prev(cur_m)
    client.post("/api/income", json={
        "date": f"{last_y:04d}-{last_m:02d}-10",
        "name": "last", "category": "资本收入", "amount": 1000, "currency": "CNY",
    }).raise_for_status()
    data = client.get("/api/income").json()
    cap = next(s for s in data["summary"] if s["category"] == "资本收入")
    assert cap["current_month_total_cny"] == 0
    assert cap["last_month_total_cny"] == 1000
    assert cap["growth_rate"] == pytest.approx(-1.0)


def test_get_with_month_param_filters_records(client: TestClient) -> None:
    """month 参数：切换到指定月份，records / summary 基于该月。"""
    client.post("/api/income", json={
        "date": "2026-03-15", "name": "三月工资", "category": "纯劳动收入",
        "amount": 8000, "currency": "CNY",
    }).raise_for_status()
    client.post("/api/income", json={
        "date": "2026-04-15", "name": "四月工资", "category": "纯劳动收入",
        "amount": 9000, "currency": "CNY",
    }).raise_for_status()

    data = client.get("/api/income", params={"month": "2026-03"}).json()
    assert data["view_month"] == "2026-03"
    assert len(data["records"]) == 1
    assert data["records"][0]["amount"] == 8000

    labor = next(s for s in data["summary"] if s["category"] == "纯劳动收入")
    assert labor["current_month_total_cny"] == 8000


def test_get_invalid_month_format_rejected(client: TestClient) -> None:
    resp = client.get("/api/income", params={"month": "2026/04"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_records_sorted_desc_by_date(client: TestClient) -> None:
    cur_m = _current_month()
    for day in ["05", "20", "10"]:
        client.post("/api/income", json={
            "date": f"{cur_m}-{day}", "name": f"day{day}",
            "category": "纯劳动收入", "amount": 100, "currency": "CNY",
        }).raise_for_status()
    data = client.get("/api/income").json()
    dates = [r["date"] for r in data["records"]]
    assert dates == sorted(dates, reverse=True)


# 工具
def _prev(yyyy_mm: str) -> tuple[int, int]:
    y, m = yyyy_mm.split("-")
    y, m = int(y), int(m)
    if m == 1:
        return (y - 1, 12)
    return (y, m - 1)
