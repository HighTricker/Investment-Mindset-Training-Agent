"""测试接口 #1 `GET /market/symbol-lookup`。

分层：
- 参数校验测试：不联网（FastAPI Query 内置 422）
- 业务正确性测试：联网真实 yfinance / akshare，标 @pytest.mark.integration
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ============================================================
# 参数校验（不联网）
# ============================================================
def test_missing_symbol_returns_422(client: TestClient) -> None:
    resp = client.get("/api/market/symbol-lookup")
    assert resp.status_code == 422


def test_empty_symbol_returns_422(client: TestClient) -> None:
    resp = client.get("/api/market/symbol-lookup", params={"symbol": ""})
    assert resp.status_code == 422


def test_health_still_works_after_migration(client: TestClient) -> None:
    """health.py 从 app/api/ 迁到 app/routers/ 后，URL 仍然是 /api/health。"""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ============================================================
# 业务正确性（联网真实外部 API）
# ============================================================
@pytest.mark.integration
def test_symbol_lookup_aapl_usd(client: TestClient) -> None:
    resp = client.get("/api/market/symbol-lookup", params={"symbol": "AAPL"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["category"] == "美股"
    assert data["currency"] == "USD"
    assert data["current_price_original"] > 0
    assert data["name"]
    assert 5.0 <= data["exchange_rate_to_cny"] <= 10.0


@pytest.mark.integration
def test_symbol_lookup_hk_stock(client: TestClient) -> None:
    resp = client.get("/api/market/symbol-lookup", params={"symbol": "0700.HK"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["category"] == "港股"
    assert data["currency"] == "HKD"
    assert data["current_price_original"] > 0
    assert 0.5 <= data["exchange_rate_to_cny"] <= 1.5


@pytest.mark.integration
def test_symbol_lookup_crypto(client: TestClient) -> None:
    resp = client.get("/api/market/symbol-lookup", params={"symbol": "BTC-USD"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["category"] == "加密货币"
    assert data["currency"] == "USD"
    assert data["current_price_original"] > 1000  # BTC 长期 > $1000


@pytest.mark.integration
def test_symbol_lookup_a_share_cny_no_fx(client: TestClient) -> None:
    """A 股 CNY 资产：汇率直接返回 1.0，不查 exchange_rates 表。"""
    resp = client.get("/api/market/symbol-lookup", params={"symbol": "601318"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["category"] == "中概股"
    assert data["currency"] == "CNY"
    assert data["exchange_rate_to_cny"] == 1.0
    assert "平安" in data["name"]


@pytest.mark.integration
def test_symbol_lookup_invalid_returns_422(client: TestClient) -> None:
    resp = client.get(
        "/api/market/symbol-lookup",
        params={"symbol": "NOTEXIST_XYZ_12345"},
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["detail"]["code"] == "INVALID_SYMBOL"
    assert "未找到" in body["detail"]["message"]


@pytest.mark.integration
def test_symbol_lookup_caches_exchange_rate(client: TestClient) -> None:
    """同一币种第二次请求应命中 DB 缓存（通过 exchange_rates 表直接验证）。"""
    from app.core.database import SessionLocal
    from app.models.exchange_rate import ExchangeRate
    from sqlalchemy import select

    # 第一次调用，必然触发 INSERT OR IGNORE
    resp1 = client.get("/api/market/symbol-lookup", params={"symbol": "AAPL"})
    assert resp1.status_code == 200
    rate1 = resp1.json()["exchange_rate_to_cny"]

    # 第二次调用
    resp2 = client.get("/api/market/symbol-lookup", params={"symbol": "AAPL"})
    assert resp2.status_code == 200
    rate2 = resp2.json()["exchange_rate_to_cny"]

    # 同一天内两次返回值必须完全一致（快照特性）
    assert rate1 == rate2

    # DB 里至少有一条 USD 记录
    with SessionLocal() as db:
        rows = db.execute(
            select(ExchangeRate).where(ExchangeRate.currency == "USD")
        ).scalars().all()
        assert len(rows) >= 1
        assert all(r.rate_to_cny == rate1 for r in rows)
