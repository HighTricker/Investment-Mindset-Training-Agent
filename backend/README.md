# Portfolio Backend

个人投资组合追踪 API（FastAPI + SQLAlchemy + SQLite）。

项目级文档 SSOT 在 `../开发文档/`。

---

## 启动（开发模式）

```bash
cd backend

# 推荐：显式 --reload-dir + --reload-include，避免 schema 改动偶发未热更
uv run uvicorn app.main:app \
  --reload \
  --reload-dir app \
  --reload-include "*.py" \
  --host 127.0.0.1 --port 8000
```

启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger。

---

## 启动踩坑备忘（B4）

**现象**：改了 `schemas/*.py` 加字段或 `routers/*.py` 改逻辑，`uvicorn --reload` 触发了重启（stdout 有 `Reloading...`），但 `curl` 打接口仍拿到旧 schema / 旧行为。

**根因**：uvicorn 基于 watchfiles 监控文件变化，但 Python 模块级类定义（特别是 Pydantic）存在"import-time 一次性构造"的语义，某些改动（比如新字段）重启后的模块重导入偶尔不生效；Windows 文件系统时间戳精度问题也有可能触发误判。

**排查三招**：
1. `curl` 直接打接口对比响应与新 schema
2. 查 uvicorn stdout 是否出现 `Reloading...` 日志
3. 若仍不对：`Ctrl+C` 结束进程 + 重新启动

**经验法则**：schema / router 结构性改动后，保险起见手动重启后端；仅业务逻辑内部改动（不动响应结构）可信任 `--reload`。

---

## 测试

```bash
# 单元测试（快，< 20s）
uv run pytest -m "not integration" tests/ -q

# 含 integration（需网络访问 yfinance / akshare）
uv run pytest tests/ -q
```

---

## 环境变量

复制模板并按需修改（见 `app/core/config.py`）：

```bash
cp .env.example .env
```

字段说明在 `.env.example` 内注释。

---

## 目录结构

```
backend/
├── app/
│   ├── core/       # 配置/DB/异常/日志
│   ├── db/         # schema.sql + seed.sql
│   ├── models/     # SQLAlchemy ORM
│   ├── routers/    # FastAPI 路由
│   ├── schemas/    # Pydantic 请求/响应 schema
│   ├── services/   # 业务服务（market_data / calculators / wealth_freedom）
│   └── main.py     # 入口
├── tests/          # pytest（含 integration 标记）
├── pyproject.toml  # uv 依赖管理
├── .env            # 本地配置（gitignore）
└── .env.example    # 配置模板
```
