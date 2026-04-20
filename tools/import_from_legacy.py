"""从旧系统 invest.db 迁移投资组合到 portfolio.db。

策略概述（详见 devlog 2026-04-20）：
- 11 个资产，每项按 "1 USD 等值" 建仓，日期 2025-12-01
- ticker 映射：^TNX → IEF（7-10 年美债 ETF），CN10Y → 511260（十年国债 ETF，
  失败降级 511010）
- 建仓价：用旧 DB monthly_prices[2025-12-01]；IEF / 511260 现场拉 yfinance / akshare
- prices 表：迁旧 33 行 + 补 2026-03/04 每月第一个交易日（共约 55 行）
- exchange_rates：补 5 个月度 USD/CNY + HKD/CNY（共 10 条）
- 旧 DB 以只读模式打开，绝不写入

用法：
    python tools/import_from_legacy.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
OLD_DB = Path(r"E:/invest_angent/data/invest.db")
NEW_DB = ROOT / "investment_data" / "portfolio.db"

# 旧 ticker → 新 (symbol, name, category, currency, data_source)
# data_source ∈ {yf, ak_sge, ak_etf}
MAPPING: dict[str, tuple[str, str, str, str, str]] = {
    "GOOGL":   ("GOOGL", "Google",                            "美股",     "USD", "yf"),
    "AMZN":    ("AMZN",  "Amazon",                            "美股",     "USD", "yf"),
    "META":    ("META",  "Meta Platforms",                    "美股",     "USD", "yf"),
    "AAPL":    ("AAPL",  "Apple",                             "美股",     "USD", "yf"),
    "NVDA":    ("NVDA",  "NVIDIA",                            "美股",     "USD", "yf"),
    "0700.HK": ("0700.HK", "Tencent",                         "港股",     "HKD", "yf"),
    "BABA":    ("BABA",  "Alibaba",                           "中概股",   "USD", "yf"),
    "BTC-USD": ("BTC-USD", "比特币",                          "加密货币", "USD", "yf"),
    "AU9999":  ("AU9999", "国际版黄金",                        "黄金",     "CNY", "ak_sge"),
    "^TNX":    ("IEF",    "iShares 7-10 Year Treasury ETF",   "美国国债", "USD", "yf"),
    "CN10Y":   ("511260", "十年国债ETF",                       "中国国债", "CNY", "ak_etf"),
}

TARGET_MONTHS = ["2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]
BUILD_DATE = "2025-12-01"
FETCH_START = "2025-11-20"   # 稍前以覆盖 12-01
FETCH_END = "2026-04-21"     # 当前日 +1
FX_CURRENCIES = ["USD", "HKD"]
BUY_REASON = "初始建仓（1 USD 等值，迁移自旧系统 invest.db）"


# ============================================================
# 历史价格获取
# ============================================================
def fetch_yfinance_history(symbol: str) -> pd.DataFrame:
    """返回 DataFrame，index=date, column 'close'（已去除 tz）。"""
    import yfinance as yf
    hist = yf.Ticker(symbol).history(
        start=FETCH_START, end=FETCH_END, auto_adjust=False,
    )
    if hist.empty:
        raise RuntimeError(f"yfinance 未返回数据：{symbol}")
    hist = hist.rename(columns={"Close": "close"})
    hist.index = pd.to_datetime(hist.index).tz_localize(None).normalize()
    return hist[["close"]]


def fetch_akshare_sge_gold() -> pd.DataFrame:
    """上海黄金交易所 AU99.99 历史行情。"""
    import akshare as ak
    df = ak.spot_hist_sge(symbol="Au99.99")
    # akshare 返回列：date, open, high, low, close
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df[["close"]]


def fetch_akshare_etf(symbol: str) -> pd.DataFrame:
    """A 股 ETF 历史日线（东方财富）。"""
    import akshare as ak
    start = FETCH_START.replace("-", "")
    end = FETCH_END.replace("-", "")
    df = ak.fund_etf_hist_em(
        symbol=symbol, period="daily", start_date=start, end_date=end, adjust="",
    )
    # 返回列：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
    df = df.rename(columns={"日期": "date", "收盘": "close"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df[["close"]]


def fetch_with_fallback(
    old_ticker: str, new_symbol: str, data_source: str,
) -> tuple[str, pd.DataFrame]:
    """返回 (实际用的 symbol, 历史 DataFrame)。511260 失败时降级 511010。"""
    if data_source == "yf":
        return new_symbol, fetch_yfinance_history(new_symbol)
    if data_source == "ak_sge":
        return new_symbol, fetch_akshare_sge_gold()
    if data_source == "ak_etf":
        try:
            return new_symbol, fetch_akshare_etf(new_symbol)
        except Exception as e:
            print(f"[warn] akshare fund_etf_hist_em({new_symbol}) 失败，降级到 511010：{e}")
            return "511010", fetch_akshare_etf("511010")
    raise ValueError(f"未知数据源：{data_source}")


def first_trading_day_each_month(hist: pd.DataFrame, months: list[str]) -> dict[str, tuple[str, float]]:
    """从日线 DataFrame 按月份选"第一个交易日"的 (date_str, close)。"""
    hist = hist.copy()
    hist["ym"] = hist.index.strftime("%Y-%m")
    out: dict[str, tuple[str, float]] = {}
    for ym in months:
        rows = hist[hist["ym"] == ym]
        if rows.empty:
            continue
        first = rows.iloc[0]
        out[ym] = (first.name.strftime("%Y-%m-%d"), float(first["close"]))
    return out


# ============================================================
# 主流程
# ============================================================
def read_old_db() -> tuple[list[dict], dict[int, dict[str, float]]]:
    """返回 (assets 列表, asset_id → {record_date: close_price})。"""
    if not OLD_DB.exists():
        raise FileNotFoundError(f"旧 DB 不存在：{OLD_DB}")
    uri = f"file:{OLD_DB.as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        assets_raw = [dict(r) for r in con.execute(
            "SELECT id, ticker, name, asset_type, base_price, base_date "
            "FROM assets ORDER BY id"
        )]
        prices_by_asset: dict[int, dict[str, float]] = {}
        for r in con.execute(
            "SELECT asset_id, record_date, close_price FROM monthly_prices "
            "ORDER BY asset_id, record_date"
        ):
            d = dict(r)
            prices_by_asset.setdefault(d["asset_id"], {})[d["record_date"]] = d["close_price"]
    finally:
        con.close()
    return assets_raw, prices_by_asset


def compute_quantity(price: float, currency: str, usd_cny: float, hkd_cny: float) -> float:
    """1 USD 等值买入对应的 quantity。"""
    if currency == "USD":
        return 1.0 / price
    if currency == "HKD":
        usd_hkd = usd_cny / hkd_cny
        return usd_hkd / price
    if currency == "CNY":
        return usd_cny / price
    raise ValueError(f"unsupported currency: {currency}")


def main() -> int:
    print("=" * 60)
    print("阶段 1: 读旧 DB + 拉外部数据")
    print("=" * 60)

    old_assets, old_prices = read_old_db()
    print(f"[read] 旧 DB 11 assets + {sum(len(v) for v in old_prices.values())} 行 monthly_prices")

    # 拉所有资产的月度历史 + 汇率
    fetched_prices: dict[str, dict[str, tuple[str, float]]] = {}
    actual_symbols: dict[str, str] = {}   # 旧 ticker → 实际 new symbol（考虑 fallback）

    for old_asset in old_assets:
        old_ticker = old_asset["ticker"]
        new_sym, _, _, _, source = MAPPING[old_ticker]
        print(f"[fetch] {old_ticker} → {new_sym} ({source})...", end=" ")
        actual_sym, hist = fetch_with_fallback(old_ticker, new_sym, source)
        actual_symbols[old_ticker] = actual_sym
        monthly = first_trading_day_each_month(hist, TARGET_MONTHS)
        fetched_prices[old_ticker] = monthly
        print(f"OK 实际 symbol={actual_sym}, 月度条数={len(monthly)}")

    # 汇率
    print(f"[fetch] USD/CNY + HKD/CNY...", end=" ")
    fx_data: dict[str, dict[str, tuple[str, float]]] = {}
    for ccy in FX_CURRENCIES:
        hist = fetch_yfinance_history(f"{ccy}CNY=X")
        fx_data[ccy] = first_trading_day_each_month(hist, TARGET_MONTHS)
    print(f"OK, USD={len(fx_data['USD'])} 月, HKD={len(fx_data['HKD'])} 月")

    # 2025-12-01 建仓汇率
    usd_cny_build = fx_data["USD"].get("2025-12", (None, None))[1]
    hkd_cny_build = fx_data["HKD"].get("2025-12", (None, None))[1]
    if usd_cny_build is None or hkd_cny_build is None:
        print("[FATAL] 拿不到 2025-12 的 USD/CNY 或 HKD/CNY 汇率")
        return 1
    print(f"[build] 2025-12-01 汇率：USD/CNY={usd_cny_build:.4f}, HKD/CNY={hkd_cny_build:.4f}")
    print(f"[build] 推导 USD/HKD={usd_cny_build/hkd_cny_build:.4f}")

    print()
    print("=" * 60)
    print("阶段 2: 写入 portfolio.db")
    print("=" * 60)

    con = sqlite3.connect(NEW_DB)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        cur = con.cursor()

        # 写 assets
        asset_id_map: dict[str, int] = {}   # 新 symbol → assets.id
        for old_asset in old_assets:
            old_ticker = old_asset["ticker"]
            new_sym, new_name, category, currency, _ = MAPPING[old_ticker]
            actual_sym = actual_symbols[old_ticker]
            cur.execute(
                "INSERT INTO assets (symbol, name, category, currency, is_active) "
                "VALUES (?, ?, ?, ?, 1)",
                (actual_sym, new_name, category, currency),
            )
            asset_id_map[actual_sym] = cur.lastrowid
        print(f"[write] assets: 11 条")

        # 写 transactions + prices + exchange_rates
        tx_count = 0
        price_count = 0
        for old_asset in old_assets:
            old_id = old_asset["id"]
            old_ticker = old_asset["ticker"]
            new_sym, _, _, currency, _ = MAPPING[old_ticker]
            actual_sym = actual_symbols[old_ticker]
            new_asset_id = asset_id_map[actual_sym]

            # 建仓价：9 个原资产用旧 DB 12-01 收盘；IEF / 511260 用新拉的 12-01
            if old_ticker in ("^TNX", "CN10Y"):
                build_info = fetched_prices[old_ticker].get("2025-12")
                if build_info is None:
                    print(f"[FATAL] {actual_sym} 2025-12 无数据")
                    return 1
                build_price = build_info[1]
            else:
                build_price = old_prices.get(old_id, {}).get("2025-12-01")
                if build_price is None:
                    print(f"[FATAL] 旧 DB asset_id={old_id} 无 2025-12-01 价格")
                    return 1

            quantity = compute_quantity(build_price, currency, usd_cny_build, hkd_cny_build)
            ex_rate = {
                "USD": usd_cny_build,
                "HKD": hkd_cny_build,
                "CNY": 1.0,
            }[currency]

            cur.execute(
                "INSERT INTO transactions (asset_id, type, quantity, price, "
                "exchange_rate_to_cny, reason, date) "
                "VALUES (?, 'buy', ?, ?, ?, ?, ?)",
                (new_asset_id, quantity, build_price, ex_rate, BUY_REASON, BUILD_DATE),
            )
            tx_count += 1

            # prices: 5 月度
            for ym, (dt_str, close) in fetched_prices[old_ticker].items():
                cur.execute(
                    "INSERT OR IGNORE INTO prices (asset_id, date, close_price) "
                    "VALUES (?, ?, ?)",
                    (new_asset_id, dt_str, close),
                )
                price_count += 1

            print(f"  {actual_sym:10s} ({currency}) qty={quantity:.8f} "
                  f"price={build_price:.4f} fx={ex_rate:.4f} → CNY {quantity*build_price*ex_rate:.4f}")

        print(f"[write] transactions: {tx_count} 条（全 buy, 2025-12-01）")
        print(f"[write] prices: {price_count} 条（已去重）")

        # exchange_rates: USD/HKD × 5 月
        fx_count = 0
        for ccy in FX_CURRENCIES:
            for ym, (dt_str, rate) in fx_data[ccy].items():
                cur.execute(
                    "INSERT OR IGNORE INTO exchange_rates (currency, rate_to_cny, date) "
                    "VALUES (?, ?, ?)",
                    (ccy, rate, dt_str),
                )
                fx_count += 1
        print(f"[write] exchange_rates: {fx_count} 条（USD + HKD × 5 月）")

        con.commit()
    except Exception as e:
        con.rollback()
        print(f"[FATAL] 写入异常，已回滚：{e}")
        raise
    finally:
        con.close()

    print()
    print("=" * 60)
    print("完成 ✓")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
