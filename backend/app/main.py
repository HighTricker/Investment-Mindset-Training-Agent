"""FastAPI 入口：挂载 CORS + 路由 + 日志 + lifespan（scheduler 启停）。"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import (
    assets,
    cash_accounts,
    health,
    income,
    market,
    metrics,
    report,
    transactions,
    user_settings,
)
from app.services.scheduler import init_scheduler, shutdown_scheduler

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时初始化 scheduler，关闭时 graceful shutdown。"""
    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="Portfolio Backend",
    description="个人投资组合追踪 API（V1 MVP + V2 邮件报告）",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(user_settings.router, prefix="/api")
app.include_router(cash_accounts.router, prefix="/api")
app.include_router(income.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(report.router, prefix="/api")

logger.info("FastAPI app initialized; CORS origins=%s", settings.cors_origins)
