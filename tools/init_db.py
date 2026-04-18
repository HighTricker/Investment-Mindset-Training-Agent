"""
初始化 portfolio.db：执行 schema.sql + seed.sql 并做基础验证。

用法：
    python tools/init_db.py          # 若 db 已存在则跳过
    python tools/init_db.py --reset  # 删掉旧 db 重建
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "investment_data" / "portfolio.db"
SCHEMA_SQL = ROOT / "backend" / "app" / "db" / "schema.sql"
SEED_SQL = ROOT / "backend" / "app" / "db" / "seed.sql"

EXPECTED_TABLES = {
    "assets", "transactions", "prices", "exchange_rates",
    "cash_accounts", "income", "news_cache", "user_settings",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 portfolio.db")
    parser.add_argument("--reset", action="store_true", help="删除已存在的 db 重新初始化")
    args = parser.parse_args()

    if DB_PATH.exists():
        if args.reset:
            DB_PATH.unlink()
            print(f"[reset] 已删除旧数据库 {DB_PATH}")
        else:
            print(f"[skip] {DB_PATH} 已存在；如需重建请加 --reset")
            return 0

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        for label, path in [("schema", SCHEMA_SQL), ("seed", SEED_SQL)]:
            sql = path.read_text(encoding="utf-8")
            conn.executescript(sql)
            print(f"[ok] 已执行 {label}.sql")
        conn.commit()

        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}
        missing = EXPECTED_TABLES - tables
        extra = tables - EXPECTED_TABLES - {"sqlite_sequence"}
        print(f"[verify] 表数量：{len(tables & EXPECTED_TABLES)}/8  "
              f"缺失：{sorted(missing) or '无'}  额外：{sorted(extra) or '无'}")

        cursor.execute("SELECT COUNT(*) FROM cash_accounts")
        ca_count = cursor.fetchone()[0]
        cursor.execute("SELECT name, amount, currency FROM cash_accounts ORDER BY id")
        ca_rows = cursor.fetchall()
        print(f"[verify] cash_accounts：{ca_count} 条 → {ca_rows}")

        cursor.execute("SELECT COUNT(*) FROM user_settings")
        us_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT target_monthly_living, target_passive_income, target_cash_savings, email "
            "FROM user_settings"
        )
        us_rows = cursor.fetchall()
        print(f"[verify] user_settings：{us_count} 条 → {us_rows}")

        cursor.execute("PRAGMA foreign_keys")
        fk_state = cursor.fetchone()[0]
        print(f"[verify] foreign_keys PRAGMA 会话值：{fk_state}  （注：SQLite 每次连接需重新 ON）")

        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name")
        idx_rows = cursor.fetchall()
        print(f"[verify] 自定义索引数：{len(idx_rows)}")
        for name, _ in idx_rows:
            print(f"         - {name}")

        assert not missing, f"缺表：{missing}"
        assert ca_count == 4, f"cash_accounts 应为 4 条，实际 {ca_count}"
        assert us_count == 1, f"user_settings 应为 1 条，实际 {us_count}"
    finally:
        conn.close()

    print(f"\n[done] 数据库初始化完成：{DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
