"""市场数据服务（V1）。

封装 yfinance（美股/港股/加密/黄金/美国国债）+ akshare（A 股「中概股」/ 中国国债），
对外暴露领域 API：
    - `infer_category(symbol)`：纯字符串规则推断资产类别
    - `lookup_symbol(symbol)` → SymbolInfo：按 symbol 查 name/currency/price
    - `fetch_current_price(symbol, category)` → float：只拿最新价（供 refresh，
      不查 name 因此比 lookup_symbol 快 5-10 倍，且覆盖 AU9999/ETF）
    - `fetch_exchange_rate(currency)` → float：某币种对 CNY 的汇率

上层 routers 只调用本模块公开函数，不直接接触 yfinance/akshare 的 API。

异常模型:
    - `SymbolNotFoundError`：在所有数据源中都找不到该代码 → 上层映射 INVALID_SYMBOL (422)
    - `ExternalSourceError`：外部数据源超时/异常 → 上层映射 EXTERNAL_SOURCE_FAILED (502)
"""
from __future__ import annotations

import logging
from typing import Callable

import akshare as ak
import yfinance as yf

from app.schemas.market import SymbolInfo

logger = logging.getLogger(__name__)


# ============================================================
# 异常类型
# ============================================================
class SymbolNotFoundError(LookupError):
    """INVALID_SYMBOL：在所有数据源中都找不到该代码。"""


class ExternalSourceError(RuntimeError):
    """EXTERNAL_SOURCE_FAILED：外部数据源超时或返回错误。"""


# ============================================================
# 类别推断（纯字符串规则，不联网）
# ============================================================
_CRYPTO_SUFFIX = "-USD"
_HK_SUFFIX = ".HK"
_GOLD_SYMBOLS = {"GLD", "IAU", "GC=F", "GLDM"}
_US_TREASURY_PREFIXES = ("TLT", "IEF", "BIL", "SHY", "GOVT")
_CN_TREASURY_PREFIXES = ("019", "511010", "511260", "511520")  # A 股国债 ETF/债券代码


def _is_a_share(symbol: str) -> bool:
    """A 股代码特征：纯数字 6 位（沪 60/深 00 开头最常见）。"""
    return symbol.isdigit() and len(symbol) == 6


def infer_category(symbol: str) -> str:
    """按 symbol 字符串特征推断 PRD 7 种类别之一。

    用户可在前端「添加资产」弹窗手动覆盖。规则顺序重要：先特殊后通用。
    """
    s = symbol.strip().upper()
    if s.endswith(_CRYPTO_SUFFIX):
        return "加密货币"
    if s.endswith(_HK_SUFFIX):
        return "港股"
    if s in _GOLD_SYMBOLS:
        return "黄金"
    if s.startswith(_US_TREASURY_PREFIXES):
        return "美国国债"
    if any(s.startswith(p) for p in _CN_TREASURY_PREFIXES):
        return "中国国债"
    if _is_a_share(s):
        return "中概股"  # 项目语境：6 位数字 A 股归为此类（非美股上市的中概公司）
    return "美股"


# ============================================================
# 公开 API
# ============================================================
def lookup_symbol(symbol: str) -> SymbolInfo:
    """按 symbol 查资产基本信息 + 当前价。

    数据源分流：
        - A 股（6 位数字）/ 中国国债 → akshare
        - 其他 → yfinance
    """
    symbol = symbol.strip()
    category = infer_category(symbol)
    try:
        if category in ("中概股", "中国国债") and _is_a_share(symbol):
            return _lookup_via_akshare(symbol, category)
        return _lookup_via_yfinance(symbol, category)
    except (SymbolNotFoundError, ExternalSourceError):
        raise
    except Exception as e:
        logger.exception("lookup_symbol failed: symbol=%s", symbol)
        raise ExternalSourceError(f"数据源查询异常：{e}") from e


def fetch_current_price(symbol: str, category: str) -> float:
    """按 symbol + category 拉最新价（供 POST /market/refresh 专用）。

    与 `lookup_symbol` 的差异：不查 name（不调 yfinance 的慢接口 `ticker.info`），
    且按 category 精确路由数据源，原生支持 AU9999（SGE）和 A 股 ETF（东方财富）。

    路由规则:
        - category='黄金' 且 symbol 以 'AU' 开头 → 上海黄金交易所 Au99.99
        - _is_a_share(symbol) 且 category='中国国债' → 东方财富 ETF 历史接口
        - _is_a_share(symbol) 其他情况 → A 股实时快照
        - 其他 → yfinance fast_info
    """
    symbol = symbol.strip()
    try:
        if category == "黄金" and symbol.upper().startswith("AU"):
            return _fetch_price_sge()
        if _is_a_share(symbol):
            if category == "中国国债":
                return _fetch_price_a_share_etf(symbol)
            return _fetch_price_a_share_stock(symbol)
        return _fetch_price_yfinance(symbol)
    except (SymbolNotFoundError, ExternalSourceError):
        raise
    except Exception as e:
        logger.exception("fetch_current_price failed: symbol=%s", symbol)
        raise ExternalSourceError(f"价格查询异常：{e}") from e


def fetch_exchange_rate(currency: str) -> float:
    """获取 `currency` 对 CNY 汇率（1 单位原币 = 多少 CNY）。

    CNY 直接返回 1.0 不联网。其他币种使用 yfinance 的 FX ticker `{CCY}CNY=X`，
    覆盖 USD/HKD/EUR/GBP/CHF 全部 AssetCurrency 枚举值。
    """
    currency = currency.strip().upper()
    if currency == "CNY":
        return 1.0
    try:
        return _fetch_fx_via_yfinance(currency)
    except SymbolNotFoundError:
        raise
    except Exception as e:
        logger.exception("fetch_exchange_rate failed: currency=%s", currency)
        raise ExternalSourceError(f"汇率查询异常：{e}") from e


# ============================================================
# 内部：yfinance
# ============================================================
def _lookup_via_yfinance(symbol: str, category: str) -> SymbolInfo:
    ticker = yf.Ticker(symbol)

    # fast_info 比 .info 快且稳定（不触发完整元数据拉取）
    try:
        fast_info = ticker.fast_info
        price_raw = getattr(fast_info, "last_price", None)
        currency_raw = getattr(fast_info, "currency", None)
    except Exception as e:
        raise ExternalSourceError(f"yfinance fast_info 异常：{e}") from e

    if price_raw is None:
        raise SymbolNotFoundError(f"yfinance 未找到有效报价：{symbol}")
    try:
        price = float(price_raw)
    except (TypeError, ValueError):
        raise SymbolNotFoundError(f"yfinance 返回非法价格：{symbol} = {price_raw!r}")
    if price <= 0:
        raise SymbolNotFoundError(f"yfinance 返回非正价格：{symbol} = {price}")

    currency = str(currency_raw).upper() if currency_raw else _default_currency_for(category)

    # 名称：.info 可能较慢且偶尔失败，仅做补充查询
    name = symbol  # 兜底
    try:
        info = ticker.info or {}
        name = info.get("longName") or info.get("shortName") or symbol
    except Exception:
        logger.warning("yfinance .info 获取失败，用 symbol 作为 name：%s", symbol)

    return SymbolInfo(
        symbol=symbol,
        name=name,
        currency=currency,
        category=category,
        current_price_original=price,
    )


def _fetch_fx_via_yfinance(currency: str) -> float:
    fx_symbol = f"{currency}CNY=X"
    try:
        fast = yf.Ticker(fx_symbol).fast_info
        rate_raw = getattr(fast, "last_price", None)
    except Exception as e:
        raise ExternalSourceError(f"yfinance FX 查询异常：{e}") from e

    if rate_raw is None:
        raise SymbolNotFoundError(f"未找到汇率：{currency}/CNY")
    try:
        rate = float(rate_raw)
    except (TypeError, ValueError):
        raise SymbolNotFoundError(f"汇率返回非法数值：{currency} = {rate_raw!r}")
    if rate <= 0:
        raise SymbolNotFoundError(f"汇率返回非正数值：{currency} = {rate}")
    return rate


# ============================================================
# 内部：akshare
# ============================================================
def _lookup_via_akshare(symbol: str, category: str) -> SymbolInfo:
    """A 股实时行情查询（stock_zh_a_spot_em 返回所有 A 股当前快照）。"""
    try:
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        raise ExternalSourceError(f"akshare stock_zh_a_spot_em 异常：{e}") from e

    row = df[df["代码"] == symbol]
    if row.empty:
        raise SymbolNotFoundError(f"akshare 未找到 A 股代码：{symbol}")

    first = row.iloc[0]
    try:
        price = float(first["最新价"])
        name = str(first["名称"])
    except (KeyError, TypeError, ValueError) as e:
        raise ExternalSourceError(f"akshare 行情字段解析失败：{e}") from e

    if price <= 0:
        # 停牌时最新价可能为 0，按未找到处理，避免写入脏数据
        raise SymbolNotFoundError(f"A 股停牌或价格异常：{symbol} = {price}")

    return SymbolInfo(
        symbol=symbol,
        name=name,
        currency="CNY",
        category=category,
        current_price_original=price,
    )


# ============================================================
# 内部：现价拉取（供 fetch_current_price）
# ============================================================
def _fetch_price_yfinance(symbol: str) -> float:
    try:
        fast = yf.Ticker(symbol).fast_info
        raw = getattr(fast, "last_price", None)
    except Exception as e:
        raise ExternalSourceError(f"yfinance fast_info 异常：{e}") from e
    if raw is None:
        raise SymbolNotFoundError(f"yfinance 未找到报价：{symbol}")
    try:
        price = float(raw)
    except (TypeError, ValueError):
        raise SymbolNotFoundError(f"yfinance 非法价格：{symbol}={raw!r}")
    if price <= 0:
        raise SymbolNotFoundError(f"yfinance 非正价格：{symbol}={price}")
    return price


def _fetch_price_sge() -> float:
    """上海黄金交易所 Au99.99 最近一个交易日收盘。"""
    try:
        df = ak.spot_hist_sge(symbol="Au99.99")
    except Exception as e:
        raise ExternalSourceError(f"akshare sge 异常：{e}") from e
    if df.empty:
        raise SymbolNotFoundError("SGE 返回空")
    try:
        price = float(df.iloc[-1]["close"])
    except (KeyError, TypeError, ValueError) as e:
        raise ExternalSourceError(f"SGE 字段解析失败：{e}") from e
    if price <= 0:
        raise SymbolNotFoundError(f"SGE 非正价格：{price}")
    return price


def _fetch_price_a_share_etf(symbol: str) -> float:
    """A 股 ETF 近期最新收盘（东方财富 K 线最后一行）。

    带 3 次指数退避重试（1s / 2s）应对 eastmoney 的 SSL 偶发握手失败
    （511260 在部分本地网络环境下 push2his.eastmoney.com 会 SSL 错误）。
    业务错误（空数据、非正价格）不重试。
    """
    import time
    from datetime import datetime, timedelta
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=15)).strftime("%Y%m%d")
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            df = ak.fund_etf_hist_em(
                symbol=symbol, period="daily",
                start_date=start, end_date=end, adjust="",
            )
            if df.empty:
                raise SymbolNotFoundError(f"ETF 返回空：{symbol}")
            try:
                price = float(df.iloc[-1]["收盘"])
            except (KeyError, TypeError, ValueError) as e:
                raise ExternalSourceError(f"ETF 字段解析失败：{e}") from e
            if price <= 0:
                raise SymbolNotFoundError(f"ETF 非正价格：{symbol}={price}")
            return price
        except SymbolNotFoundError:
            raise  # 业务错误不重试
        except Exception as e:
            last_err = e
            if attempt < 2:
                logger.warning(
                    "akshare ETF %s attempt %d failed: %s, retrying...",
                    symbol, attempt + 1, e,
                )
                time.sleep(2 ** attempt)
    raise ExternalSourceError(
        f"akshare ETF 重试 3 次仍失败：{symbol}={last_err}"
    ) from last_err


def _fetch_price_a_share_stock(symbol: str) -> float:
    """A 股 stock 实时行情（`stock_zh_a_spot_em` 全市场快照）。"""
    try:
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        raise ExternalSourceError(f"akshare spot_em 异常：{e}") from e
    row = df[df["代码"] == symbol]
    if row.empty:
        raise SymbolNotFoundError(f"A 股未找到：{symbol}")
    try:
        price = float(row.iloc[0]["最新价"])
    except (KeyError, TypeError, ValueError) as e:
        raise ExternalSourceError(f"A 股字段解析失败：{e}") from e
    if price <= 0:
        raise SymbolNotFoundError(f"A 股停牌或异常：{symbol}={price}")
    return price


# ============================================================
# 工具
# ============================================================
def _default_currency_for(category: str) -> str:
    return {
        "港股": "HKD",
        "加密货币": "USD",
        "美股": "USD",
        "黄金": "USD",
        "美国国债": "USD",
        "中概股": "CNY",
        "中国国债": "CNY",
    }.get(category, "USD")
