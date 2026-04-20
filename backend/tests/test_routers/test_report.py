"""测试 P5 API #17 /report/preview + #18 /report/send。"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

AAPL = {
    "symbol": "AAPL", "name": "Apple Inc.", "category": "美股", "currency": "USD",
    "quantity": 10, "price": 200.0, "exchange_rate_to_cny": 7.0,
    "date": "2026-04-01",
}


def test_preview_empty_portfolio_returns_422(client: TestClient) -> None:
    """无活跃资产时 preview 返回 422 NO_ACTIVE_ASSETS。"""
    resp = client.post("/api/report/preview", json={})
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "NO_ACTIVE_ASSETS"


def test_preview_with_asset_returns_html(client: TestClient, fresh_db) -> None:
    """有资产时 preview 返回 HTML（text/html content-type + 含资产名）。"""
    assert client.post("/api/assets", json=AAPL).status_code == 201

    resp = client.post("/api/report/preview", json={"send_date": "2026-04-15"})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/html")
    body = resp.text
    assert "投资月报" in body
    assert "Apple Inc." in body
    assert "资产明细" in body
    assert "AI 月度点评" in body  # 占位 section 必须存在


def test_send_empty_email_returns_422(client: TestClient, fresh_db) -> None:
    """user_settings.email 为空时 send 返回 422 INVALID_EMAIL_FORMAT。"""
    assert client.post("/api/assets", json=AAPL).status_code == 201

    resp = client.post("/api/report/send", json={})
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "INVALID_EMAIL_FORMAT"


def test_send_smtp_failure_returns_502(client: TestClient, fresh_db) -> None:
    """SMTP 发送抛 EmailSenderError 时 send 返回 502 EMAIL_SEND_FAILED。"""
    from app.services.email_sender import EmailSenderError

    assert client.post("/api/assets", json=AAPL).status_code == 201
    assert client.put(
        "/api/user-settings", json={"email": "test@example.com"}
    ).status_code == 200

    with patch(
        "app.routers.report.send_html_email",
        side_effect=EmailSenderError("SMTP 认证失败（授权码错误）"),
    ):
        resp = client.post("/api/report/send", json={})
    assert resp.status_code == 502, resp.text
    body = resp.json()
    assert body["detail"]["code"] == "EMAIL_SEND_FAILED"
    assert "smtp_error" in body["detail"]["details"]


@pytest.mark.integration
def test_send_real_smtp_not_configured_returns_502(
    client: TestClient, fresh_db,
) -> None:
    """未配 SMTP 凭证时真实 send 应该返回 502（而非崩溃）。"""
    assert client.post("/api/assets", json=AAPL).status_code == 201
    assert client.put(
        "/api/user-settings", json={"email": "test@example.com"}
    ).status_code == 200

    resp = client.post("/api/report/send", json={})
    # 无 SMTP_HOST/USER/PASSWORD 时 email_sender 内抛 EmailSenderError
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "EMAIL_SEND_FAILED"
