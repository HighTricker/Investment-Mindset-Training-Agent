"""补指定月份"最后一个交易日"的收盘价。

用于修复 P5 报告"N 月收益率"列为空的问题：
    build_report_html 需要该月 prices 表至少 2 条（首末日）才能算收益率，
    之前 import_from_legacy.py 只补了"每月第一个交易日"，缺月末。

用法：
    python tools/backfill_month_last_trading_day.py 2026-03        # 补单个月
    python tools/backfill_month_last_trading_day.py 2025-12 2026-03  # 范围补

如果某月已经有 >=2 条价格记录，跳过（避免重复拉）。
"""
from __future__ import annotations

import calendar
import sqlite3
import sys
import time
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "investment_data" / "portfolio.db"


def _month_last_day(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _fetch_yf(symbol: str, year: int, month: int) -> tuple[str, float] | None:
    import pandas as pd
    import yfinance as yf

    last_day = _month_last_day(year, month)
    start = (last_day - timedelta(days=7)).isoformat()
    end = (last_day + timedelta(days=1)).isoformat()
    hist = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=False)
    if hist.empty:
        return None
    date_str = pd.to_datetime(hist.index[-1]).strftime("%Y-%m-%d")
    return date_str, float(hist.iloc[-1]["Close"])


def _fetch_sge(year: int, month: int) -> tuple[str, float] | None:
    import akshare as ak
    import pandas as pd

    df = ak.spot_hist_sge(symbol="Au99.99")
    df["date"] = pd.to_datetime(df["date"])
    start = pd.Timestamp(year, month, 1)
    end = pd.Timestamp(year, month, calendar.monthrange(year, month)[1]) + pd.Timedelta(days=1)
    sub = df[(df["date"] >= start) & (df["date"] < end)]
    if sub.empty:
        return None
    last_row = sub.iloc[-1]
    return last_row["date"].strftime("%Y-%m-%d"), float(last_row["close"])


def _fetch_etf(symbol: str, year: int, month: int) -> tuple[str, float] | None:
    import akshare as ak
    import pandas as pd

    start = f"{year:04d}{month:02d}01"
    end = _month_last_day(year, month).strftime("%Y%m%d")
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            df = ak.fund_etf_hist_em(
                symbol=symbol, period="daily",
                start_date=start, end_date=end, adjust="",
            )
            break
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
    else:
        print(f"  ⚠️  ETF {symbol} SSL 重试 3 次失败: {last_err}")
        return None
    if df.empty:
        return None
    last_row = df.iloc[-1]
    date_str = pd.to_datetime(last_row["日期"]).strftime("%Y-%m-%d")
    return date_str, float(last_row["收盘"])


def _fetch_by_asset(symbol: str, year: int, month: int) -> tuple[str, float] | None:
    if symbol == "AU9999":
        return _fetch_sge(year, month)
    if symbol.isdigit() and len(symbol) == 6:
        return _fetch_etf(symbol, year, month)
    return _fetch_yf(symbol, year, month)


def _month_has_two_prices(con: sqlite3.Connection, asset_id: int, year: int, month: int) -> bool:
    start = date(year, month, 1).isoformat()
    end = (date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)).isoformat()
    n = con.execute(
        "SELECT COUNT(*) FROM prices WHERE asset_id=? AND date >= ? AND date < ?",
        (asset_id, start, end),
    ).fetchone()[0]
    return n >= 2


def _iter_months(start_ym: str, end_ym: str):
    sy, sm = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    y, m = sy, sm
    while (y, m) <= (ey, em):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/backfill_month_last_trading_day.py YYYY-MM [YYYY-MM]")
        return 1
    start_ym = sys.argv[1]
    end_ym = sys.argv[2] if len(sys.argv) > 2 else start_ym

    con = sqlite3.connect(DB)
    try:
        assets = con.execute(
            "SELECT id, symbol FROM assets WHERE is_active=1 ORDER BY id"
        ).fetchall()
        total_added = 0
        for year, month in _iter_months(start_ym, end_ym):
            print(f"\n=== 补 {year}-{month:02d} 月末交易日 ===")
            for asset_id, symbol in assets:
                if _month_has_two_prices(con, asset_id, year, month):
                    print(f"  ⏭  id={asset_id:2d} {symbol:10s}  该月已有 ≥2 条数据，跳过")
                    continue
                try:
                    result = _fetch_by_asset(symbol, year, month)
                except Exception as e:
                    print(f"  ✗  id={asset_id:2d} {symbol:10s}  异常: {e}")
                    continue
                if result is None:
                    print(f"  ✗  id={asset_id:2d} {symbol:10s}  无月末数据")
                    continue
                date_str, price = result
                con.execute(
                    "INSERT INTO prices (asset_id, date, close_price) VALUES (?, ?, ?) "
                    "ON CONFLICT(asset_id, date) DO UPDATE SET close_price=excluded.close_price",
                    (asset_id, date_str, price),
                )
                print(f"  ✓  id={asset_id:2d} {symbol:10s}  {date_str}  close={price:.4f}")
                total_added += 1
        con.commit()
        print(f"\n[done] 共写入 {total_added} 条")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
