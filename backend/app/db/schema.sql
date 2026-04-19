-- portfolio.db schema
-- SSOT: ../../../开发文档/SQL_prompt_schema.md
-- SQLite 3.8.0+ 需支持 WHERE 部分索引

PRAGMA foreign_keys = ON;

-- ========================================
-- 1. assets（持仓资产）
-- ========================================
CREATE TABLE IF NOT EXISTS assets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol     TEXT    NOT NULL,
    name       TEXT    NOT NULL,
    category   TEXT    NOT NULL CHECK (category IN ('美股', '港股', '中概股', '加密货币', '黄金', '美国国债', '中国国债')),
    currency   TEXT    NOT NULL CHECK (currency IN ('CNY', 'USD', 'HKD', 'EUR', 'GBP', 'CHF')),
    is_active  INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 部分唯一索引：仅活跃资产 symbol 唯一（支持同一 symbol 的历史多次持仓周期）
CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_symbol_active
    ON assets(symbol) WHERE is_active = 1;


-- ========================================
-- 2. transactions（交易记录）
-- ========================================
CREATE TABLE IF NOT EXISTS transactions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id             INTEGER NOT NULL,
    type                 TEXT    NOT NULL CHECK (type IN ('buy', 'sell', 'close')),
    quantity             REAL    NOT NULL,
    price                REAL    NOT NULL,
    exchange_rate_to_cny REAL    NOT NULL,
    reason               TEXT,
    date                 TEXT    NOT NULL,
    created_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT
);

-- 常用查询索引：按 asset_id + date 聚合持仓
CREATE INDEX IF NOT EXISTS idx_transactions_asset_date
    ON transactions(asset_id, date);


-- ========================================
-- 3. prices（价格历史）
-- ========================================
CREATE TABLE IF NOT EXISTS prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    INTEGER NOT NULL,
    date        TEXT    NOT NULL,
    close_price REAL    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT,
    UNIQUE (asset_id, date)
);


-- ========================================
-- 4. exchange_rates（汇率历史）
-- ========================================
CREATE TABLE IF NOT EXISTS exchange_rates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    currency    TEXT    NOT NULL CHECK (currency IN ('USD', 'HKD', 'EUR', 'GBP', 'CHF')),
    rate_to_cny REAL    NOT NULL,
    date        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (currency, date)
);


-- ========================================
-- 5. cash_accounts（现金账户）
-- ========================================
CREATE TABLE IF NOT EXISTS cash_accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    amount     REAL    NOT NULL DEFAULT 0,
    currency   TEXT    NOT NULL DEFAULT 'CNY' CHECK (currency IN ('CNY', 'USD')),
    is_active  INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);


-- ========================================
-- 6. income（收入记录）
-- ========================================
CREATE TABLE IF NOT EXISTS income (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT    NOT NULL,
    name       TEXT    NOT NULL,
    category   TEXT    NOT NULL CHECK (category IN ('纯劳动收入', '代码&自媒体收入', '资本收入')),
    amount     REAL    NOT NULL,
    currency   TEXT    NOT NULL DEFAULT 'CNY' CHECK (currency IN ('CNY', 'USD')),
    note       TEXT,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 月份聚合查询索引
CREATE INDEX IF NOT EXISTS idx_income_date ON income(date);


-- ========================================
-- 7. news_cache（新闻缓存，V3）
-- ========================================
CREATE TABLE IF NOT EXISTS news_cache (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id     INTEGER NOT NULL,
    title        TEXT    NOT NULL,
    summary      TEXT,
    source_url   TEXT,
    published_at TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_news_asset_published
    ON news_cache(asset_id, published_at DESC);


-- ========================================
-- 8. user_settings（用户设置）
-- ========================================
CREATE TABLE IF NOT EXISTS user_settings (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    target_monthly_living    REAL    NOT NULL DEFAULT 0,
    target_living_currency   TEXT    NOT NULL DEFAULT 'CNY' CHECK (target_living_currency IN ('CNY', 'USD')),
    target_passive_income    REAL    NOT NULL DEFAULT 0,
    target_passive_currency  TEXT    NOT NULL DEFAULT 'CNY' CHECK (target_passive_currency IN ('CNY', 'USD')),
    target_cash_savings      REAL    NOT NULL DEFAULT 0,
    target_cash_currency     TEXT    NOT NULL DEFAULT 'CNY' CHECK (target_cash_currency IN ('CNY', 'USD')),
    email                    TEXT,
    updated_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
