[中文](#中文)

# Investment Mindset Training Agent

A personal investment tracking tool that visualizes asset allocation, calculates your path to financial freedom, and sends automated monthly email reports — with an optional LLM-powered monthly commentary.

## Status

- **V1 MVP** ✅ Complete (4 pages + 19 APIs + 128 passing tests)
- **V2 Email Report** ✅ Complete (HTML report, SMTP, APScheduler, optional AI commentary)
- **V3 RAG Agent** 🚧 Planned (news integration, conversational agent with tool calling)

## Features

### 📊 P1 — Portfolio Dashboard
13-column asset table across multiple markets (US stocks, HK stocks, A-shares, crypto, gold, US/CN treasuries). Monthly return color coding. Add / modify / close positions. Best/worst cards. One-click market refresh (~13s for 11 assets via `fast_info`).

### 🎯 P2.1 — Financial Freedom Timeline
Set monthly living cost target, passive income target, cash savings target. Track cash accounts + monthly income by category. Real-time countdown with predicted freedom date + years/months remaining. Live coupling — edit a target, countdown updates instantly.

### 📜 P3.1 — Investment Journal
All assets (active + closed) in one table. Click a row → right-side drawer slides in with full transaction history + reason for each trade. Supports fractional shares and "invest $1 in TSLA" style amount-based entries.

### ✉️ P5 — Automated Email Reports
HTML email with 4 sections: overview (2×2 grid), best/worst of the month, per-asset cards, 13-column detail table. Monthly returns use CFA-standard method (month-end to month-end). Send via SMTP (Gmail / QQ / 163 / Outlook supported). APScheduler runs it monthly on your server. Optional LLM monthly commentary (~150 words) via OpenAI-compatible APIs (DeepSeek / Zhipu / SiliconFlow / OpenAI).

### 🛠️ Tooling Scripts
`tools/init_db.py` — bootstrap schema + seed data
`tools/import_from_legacy.py` — migrate from an older SQLite portfolio with 1 USD-equivalent rebasing
`tools/backfill_today_prices.py` / `tools/backfill_month_last_trading_day.py` — fill gaps in `prices` table

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite 8 + Tailwind CSS 4 + React Router 7 + Axios |
| Backend | FastAPI + SQLAlchemy 2.0 + Pydantic 2 + Python 3.12 |
| Database | SQLite (single file, `investment_data/portfolio.db`) |
| Scheduler | APScheduler (BackgroundScheduler, cron trigger) |
| LLM | OpenAI SDK — works with any OpenAI-compatible API |
| Market Data | yfinance (US / HK / crypto / USD FX) + akshare (A-shares / gold / CN treasuries) |
| Mail | Python `smtplib` (SSL / STARTTLS auto-switch) |
| Tooling | `uv` (Python deps) + `npm` + `pytest` + ESLint + `tsc -b` |

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`)

### Backend

```bash
cd backend
uv sync
cp .env.example .env     # then edit SMTP / OpenAI keys as needed

# Initialize database (seeds default cash accounts + user settings)
python ../tools/init_db.py

# Dev server with explicit reload args (workaround for schema-change hot reload)
uv run uvicorn app.main:app \
  --reload --reload-dir app --reload-include "*.py" \
  --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Tests

```bash
# Backend unit tests (128 tests, <20s)
cd backend && uv run pytest -m "not integration" tests/ -q

# Frontend type check + build
cd frontend && npm run build

# Frontend lint
cd frontend && npm run lint
```

## Environment Variables

See `backend/.env.example` for the full list. Key fields:

| Variable | Purpose |
|---------|---------|
| `CORS_ORIGINS` | Frontend origins allowed (JSON array) |
| `DB_PATH` | SQLite file path (relative to `backend/`) |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Email sending (use authorization code, not login password) |
| `REPORT_SCHEDULE_CRON` | cron expression, default `0 9 1 * *` (1st of month 9 AM) |
| `REPORT_SCHEDULE_ENABLED` | `true` on production server; `false` locally |
| `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL` | LLM commentary (optional; supports OpenAI-compatible endpoints) |
| `AI_COMMENTARY_ENABLED` | Enable LLM-generated monthly commentary in email report |

Frontend: `frontend/.env.example` — just `VITE_API_BASE_URL` if you need to override the default.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/         # config, database, exceptions, logging
│   │   ├── db/           # schema.sql + seed.sql
│   │   ├── models/       # 7 SQLAlchemy ORM models
│   │   ├── routers/      # 9 FastAPI routers
│   │   ├── schemas/      # Pydantic request/response models
│   │   └── services/     # calculators, market_data, wealth_freedom,
│   │                     # email_sender, report_builder, scheduler,
│   │                     # ai_commentary
│   ├── tests/            # pytest (routers + services)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # common / dialogs / layout / p2_1 / p3_1 / p5
│   │   ├── pages/        # 8 page components (P1, P2.1, P3.1, ...)
│   │   ├── hooks/        # useAssets, useUserSettings, ...
│   │   ├── stores/       # Context + Provider split per domain
│   │   ├── services/api/ # API client modules
│   │   ├── types/        # entities, api, enums
│   │   └── utils/        # formatters, errors, unitConverter
│   └── package.json
├── config/               # report_style.json, report_preview_sample.html
├── investment_data/      # portfolio.db (gitignored)
└── tools/                # maintenance scripts
```

## License

MIT — see [LICENSE](LICENSE).

---

<a id="中文"></a>
[English](#investment-mindset-training-agent)

# 投资心态训练 Agent

一个个人投资追踪工具，帮你可视化资产配置、计算财富自由时间线、自动发送月度邮件报告，并可选接入 LLM 生成月度点评。

## 项目状态

- **V1 MVP** ✅ 完成（4 个页面 + 19 个 API + 128 个测试全绿）
- **V2 邮件报告** ✅ 完成（HTML 报告、SMTP 发送、APScheduler 定时、可选 AI 点评）
- **V3 RAG Agent** 🚧 规划中（新闻集成、支持工具调用的对话式 agent）

## 功能特性

### 📊 P1 — 投资组合仪表盘
跨多市场 13 列资产明细表（美股 / 港股 / A 股 / 加密货币 / 黄金 / 中美国债）。本月收益率红绿染色。添加 / 加减仓 / 关闭持仓。最佳/最差卡片。一键刷新市场价格（11 资产约 13 秒，基于 `fast_info`）。

### 🎯 P2.1 — 财富自由时间表
设定月生活目标、被动收入目标、现金储蓄目标。管理现金账户 + 月度收入分类。实时倒计时含预计达成日期 + 剩余年月。**联动更新** — 改目标，倒计时立即刷新。

### 📜 P3.1 — 投资日志
所有资产（活跃 + 已关闭）同表展示。点击行 → 右侧抽屉滑入显示完整交易历史 + 每笔理由。支持零股 + "投 1 美元买 TSLA" 按金额输入模式。

### ✉️ P5 — 自动化邮件报告
HTML 邮件 4 个 section：概况（2×2）/ 本月最佳最差 / 各资产表现 / 13 列明细表。月度收益率采用 **CFA 标准算法**（月末对月末）。SMTP 发送（Gmail / QQ / 163 / Outlook）。APScheduler 服务端每月定时触发。可选 **LLM 月度点评**（约 150 字，支持 OpenAI / DeepSeek / 智谱 / SiliconFlow 等 OpenAI-compatible 端点）。

### 🛠️ 工具脚本
- `tools/init_db.py` — 初始化 schema + 种子数据
- `tools/import_from_legacy.py` — 从旧 SQLite 投资库按"1 USD 等值"策略迁移
- `tools/backfill_today_prices.py` / `tools/backfill_month_last_trading_day.py` — 补齐 `prices` 表缺失日期

## 技术栈

| 层级 | 技术 |
|-------|-----------|
| 前端 | React 19 + TypeScript + Vite 8 + Tailwind CSS 4 + React Router 7 + Axios |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic 2 + Python 3.12 |
| 数据库 | SQLite（单文件，`investment_data/portfolio.db`） |
| 定时任务 | APScheduler（BackgroundScheduler + cron 触发） |
| LLM | OpenAI SDK（兼容任何 OpenAI-compatible API） |
| 行情数据 | yfinance（美股 / 港股 / 加密 / USD 汇率） + akshare（A 股 / 黄金 / 中国国债） |
| 邮件 | Python 标准库 `smtplib`（SSL / STARTTLS 自动切换） |
| 工具链 | `uv`（Python 依赖） + `npm` + `pytest` + ESLint + `tsc -b` |

## 快速开始

### 前置环境
- Python 3.12+
- Node.js 18+
- `uv`（`pip install uv` 或官网安装）

### 后端

```bash
cd backend
uv sync
cp .env.example .env     # 按需填写 SMTP / OpenAI 密钥

# 初始化数据库（写入默认现金账户 + 用户设置）
python ../tools/init_db.py

# 启动开发服务器
uv run uvicorn app.main:app \
  --reload --reload-dir app --reload-include "*.py" \
  --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

### 测试

```bash
# 后端单元测试（128 个，< 20 秒）
cd backend && uv run pytest -m "not integration" tests/ -q

# 前端类型检查 + 构建
cd frontend && npm run build

# 前端 lint
cd frontend && npm run lint
```

## 环境变量

完整说明见 `backend/.env.example`。关键字段：

| 变量 | 用途 |
|---------|---------|
| `CORS_ORIGINS` | 允许的前端源（JSON 数组） |
| `DB_PATH` | SQLite 文件路径（相对 `backend/`） |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | 邮件发送（填授权码，非登录密码） |
| `REPORT_SCHEDULE_CRON` | cron 表达式，默认 `0 9 1 * *`（每月 1 号 9 点） |
| `REPORT_SCHEDULE_ENABLED` | 生产服务器设 `true`；本地默认 `false` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL` | LLM 点评（可选；支持 OpenAI-compatible 端点） |
| `AI_COMMENTARY_ENABLED` | 启用邮件报告内 LLM 生成月度点评 |

前端 `frontend/.env.example` 只有一个 `VITE_API_BASE_URL`（需要覆盖默认后端地址时用）。

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── core/         # config / database / exceptions / logging
│   │   ├── db/           # schema.sql + seed.sql
│   │   ├── models/       # 7 个 SQLAlchemy ORM 模型
│   │   ├── routers/      # 9 个 FastAPI 路由
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   └── services/     # calculators / market_data / wealth_freedom
│   │                     # email_sender / report_builder / scheduler
│   │                     # ai_commentary
│   ├── tests/            # pytest（routers + services）
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # common / dialogs / layout / p2_1 / p3_1 / p5
│   │   ├── pages/        # 8 个页面组件（P1, P2.1, P3.1, ...）
│   │   ├── hooks/        # useAssets, useUserSettings 等
│   │   ├── stores/       # 按领域拆分的 Context + Provider
│   │   ├── services/api/ # API 客户端模块
│   │   ├── types/        # entities / api / enums
│   │   └── utils/        # formatters / errors / unitConverter
│   └── package.json
├── config/               # report_style.json, report_preview_sample.html
├── investment_data/      # portfolio.db（gitignored）
└── tools/                # 维护脚本
```

## 开源协议

MIT 协议 — 详见 [LICENSE](LICENSE)。
