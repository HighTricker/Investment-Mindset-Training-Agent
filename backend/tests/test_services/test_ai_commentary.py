"""测试 AI 月度点评服务（mock OpenAI）。"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_commentary import generate_ai_commentary
from app.services.report_builder import AssetReportItem, ReportData


@pytest.fixture
def sample_report() -> ReportData:
    item = AssetReportItem(
        asset_id=1, symbol="AAPL", name="Apple", category="美股", currency="USD",
        quantity=0.01, cost_price_original=200.0,
        total_invested_cny=7.0, current_price_original=250.0,
        current_rate_to_cny=7.0, current_value_cny=17.5,
        cumulative_return=0.25, monthly_return=-0.04,
        position_ratio=1.0,
    )
    return ReportData(
        send_date=date(2026, 4, 15),
        month_label="3月",
        year_month_title="2026 年 3 月 投资月报",
        items=[item],
        total_invested_cny=7.0, total_value_cny=17.5,
        total_profit_loss_cny=10.5, total_return_rate=1.5,
        best=item, worst=item,
    )


def test_disabled_returns_none(sample_report, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.ai_commentary_enabled", False
    )
    assert generate_ai_commentary(sample_report) is None


def test_no_api_key_returns_none(sample_report, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.ai_commentary_enabled", True
    )
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.openai_api_key", None
    )
    assert generate_ai_commentary(sample_report) is None


def test_success_returns_commentary(sample_report, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.ai_commentary_enabled", True
    )
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.openai_api_key", "sk-test"
    )
    mock_msg = MagicMock()
    mock_msg.content = "本月总体表现平稳，苹果小幅回调 4%，持仓结构合理。"
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        result = generate_ai_commentary(sample_report)
    assert result == "本月总体表现平稳，苹果小幅回调 4%，持仓结构合理。"


def test_api_failure_returns_none(sample_report, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.ai_commentary_enabled", True
    )
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.openai_api_key", "sk-test"
    )
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API timeout")
        mock_cls.return_value = mock_client
        result = generate_ai_commentary(sample_report)
    assert result is None


def test_empty_content_returns_none(sample_report, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.ai_commentary_enabled", True
    )
    monkeypatch.setattr(
        "app.services.ai_commentary.settings.openai_api_key", "sk-test"
    )
    mock_msg = MagicMock()
    mock_msg.content = ""  # 空响应
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        result = generate_ai_commentary(sample_report)
    assert result is None
