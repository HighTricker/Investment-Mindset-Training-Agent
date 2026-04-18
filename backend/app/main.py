"""FastAPI 入口：挂载 CORS + 路由 + 日志。"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import assets, cash_accounts, health, market, transactions, user_settings

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Portfolio Backend",
    description="个人投资组合追踪 API（V1 MVP）",
    version="0.1.0",
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

logger.info("FastAPI app initialized; CORS origins=%s", settings.cors_origins)
