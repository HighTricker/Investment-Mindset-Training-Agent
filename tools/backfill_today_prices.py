"""补 prices 表今日最新价（fast_info 版，秒级完成）。

背景：tools/import_from_legacy.py 只导入到 2026-04-01 的月度快照，
导致"本月首交易日价 = 最新价"，monthly_return_rate 恒为 0。
routers/market.py 的 refresh 用慢的 ticker.info，前端 30s timeout 顶不住。
本脚本用 fast_info（底层 chart API，不 scrape 网页）拉 11 资产今价，
UPSERT 到 prices，5-10 秒搞定。

用法：python tools/backfill_today_prices.py
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "investment_data" / "portfolio.db"
TODAY = date.today().isoformat()


def fetch_price(symbol: str) -> float | None:
    """按 symbol 规则分流到 yfinance.fast_info / akshare。"""
    if symbol == "AU9999":
        import akshare as ak
        df = ak.spot_hist_sge(symbol="Au99.99")
        return float(df.iloc[-1]["close"])
    if symbol.isdigit() and len(symbol) == 6:  # A 股 ETF
        import akshare as ak
        start = (TODAY.replace("-", ""))  # 今天
        # 往前推 10 天保证有数据
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        end = datetime.now().strftime("%Y%m%d")
        df = ak.fund_etf_hist_em(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="",
        )
        return float(df.iloc[-1]["收盘"])
    # 默认 yfinance fast_info
    import yfinance as yf
    fast = yf.Ticker(symbol).fast_info
    price = getattr(fast, "last_price", None)
    return float(price) if price is not None else None


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        assets = con.execute(
            "SELECT id, symbol, currency FROM assets WHERE is_active = 1 "
            "ORDER BY id"
        ).fetchall()
        print(f"[info] 要补 {len(assets)} 个资产今日价 date={TODAY}")

        ok, fail = 0, 0
        for asset_id, symbol, currency in assets:
            try:
                price = fetch_price(symbol)
                if price is None or price <= 0:
                    raise ValueError(f"invalid price {price}")
                con.execute(
                    "INSERT INTO prices (asset_id, date, close_price) "
                    "VALUES (?, ?, ?) "
                    "ON CONFLICT(asset_id, date) DO UPDATE SET close_price=excluded.close_price",
                    (asset_id, TODAY, price),
                )
                print(f"  ✓ id={asset_id:2d} {symbol:10s} ({currency})  price={price:.4f}")
                ok += 1
            except Exception as e:
                print(f"  ✗ id={asset_id:2d} {symbol:10s}  fail: {e}")
                fail += 1

        # 同时补汇率今日
        print(f"\n[info] 补汇率今日（USD/HKD）")
        import yfinance as yf
        for ccy in ["USD", "HKD"]:
            try:
                fast = yf.Ticker(f"{ccy}CNY=X").fast_info
                rate = getattr(fast, "last_price", None)
                if rate is None or rate <= 0:
                    raise ValueError(f"invalid rate {rate}")
                con.execute(
                    "INSERT INTO exchange_rates (currency, rate_to_cny, date) "
                    "VALUES (?, ?, ?) "
                    "ON CONFLICT(currency, date) DO UPDATE SET rate_to_cny=excluded.rate_to_cny",
                    (ccy, float(rate), TODAY),
                )
                print(f"  ✓ {ccy}/CNY = {rate:.4f}")
            except Exception as e:
                print(f"  ✗ {ccy}/CNY  fail: {e}")

        con.commit()
        print(f"\n[done] 成功 {ok} / 失败 {fail}")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
