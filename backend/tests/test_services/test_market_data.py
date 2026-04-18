"""市场数据服务测试。

两层：
  - 单元测试：infer_category 纯字符串规则，不联网
  - 集成测试：真实调用 yfinance / akshare，用 @pytest.mark.integration 标记

跑所有：  uv run pytest tests/
跳过联网：uv run pytest tests/ -m "not integration"
仅联网：  uv run pytest tests/ -m integration
"""
from __future__ import annotations

import pytest

from app.services.market_data import (
    ExternalSourceError,
    SymbolNotFoundError,
    fetch_exchange_rate,
    infer_category,
    lookup_symbol,
)


# ============================================================
# infer_category 单元测试
# ============================================================
@pytest.mark.parametrize(
    "symbol,expected",
    [
        # 加密货币
        ("BTC-USD", "加密货币"),
        ("ETH-USD", "加密货币"),
        ("btc-usd", "加密货币"),  # 大小写不敏感
        # 港股
        ("00700.HK", "港股"),
        ("09988.HK", "港股"),
        # 黄金
        ("GLD", "黄金"),
        ("IAU", "黄金"),
        # 美国国债
        ("TLT", "美国国债"),
        ("IEF", "美国国债"),
        # 中国国债 ETF
        ("511010", "中国国债"),
        ("019666", "中国国债"),
        # A 股（走到 6 位数字规则前先匹配中国国债前缀）
        ("600519", "中概股"),  # 贵州茅台
        ("000001", "中概股"),  # 平安银行
        ("601318", "中概股"),  # 中国平安
        # 美股（兜底）
        ("AAPL", "美股"),
        ("TSLA", "美股"),
        ("BABA", "美股"),  # 美股上市中概公司，仍按 symbol 规则归美股；用户可改
    ],
)
def test_infer_category(symbol: str, expected: str) -> None:
    assert infer_category(symbol) == expected


# ============================================================
# lookup_symbol 集成测试（联网 yfinance / akshare）
# ============================================================
@pytest.mark.integration
@pytest.mark.parametrize(
    "symbol,expected_category,expected_currency",
    [
        ("AAPL", "美股", "USD"),
        ("0700.HK", "港股", "HKD"),
        ("BTC-USD", "加密货币", "USD"),
    ],
)
def test_lookup_symbol_yfinance(symbol: str, expected_category: str, expected_currency: str) -> None:
    info = lookup_symbol(symbol)
    assert info.symbol == symbol
    assert info.category == expected_category
    assert info.currency == expected_currency
    assert info.current_price_original > 0
    assert info.name  # 至少不是空串


@pytest.mark.integration
def test_lookup_symbol_akshare_a_share() -> None:
    """A 股：中国平安 601318。akshare stock_zh_a_spot_em 真实调用。"""
    info = lookup_symbol("601318")
    assert info.symbol == "601318"
    assert info.category == "中概股"
    assert info.currency == "CNY"
    assert info.current_price_original > 0
    assert "平安" in info.name  # 名称含「中国平安」或类似


@pytest.mark.integration
def test_lookup_symbol_invalid() -> None:
    with pytest.raises(SymbolNotFoundError):
        lookup_symbol("NOTEXIST_XYZ_12345")


# ============================================================
# fetch_exchange_rate 集成测试
# ============================================================
def test_fetch_exchange_rate_cny_is_one() -> None:
    """CNY 对 CNY 固定 1.0，不联网。"""
    assert fetch_exchange_rate("CNY") == 1.0


@pytest.mark.integration
@pytest.mark.parametrize(
    "currency,reasonable_range",
    [
        ("USD", (5.0, 10.0)),    # USDCNY 历史区间
        ("HKD", (0.5, 1.5)),     # HKDCNY 约 0.9
        ("EUR", (5.0, 12.0)),    # EURCNY 约 7-8
    ],
)
def test_fetch_exchange_rate(currency: str, reasonable_range: tuple[float, float]) -> None:
    rate = fetch_exchange_rate(currency)
    lo, hi = reasonable_range
    assert lo <= rate <= hi, f"{currency}/CNY = {rate} 超出合理区间 {reasonable_range}"


@pytest.mark.integration
def test_fetch_exchange_rate_unknown_currency() -> None:
    with pytest.raises((SymbolNotFoundError, ExternalSourceError)):
        fetch_exchange_rate("ZZZ")
