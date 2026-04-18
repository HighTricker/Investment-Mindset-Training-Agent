"""指标聚合 routers（API #15 GET /metrics/wealth-freedom）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metrics import WealthFreedomMetrics
from app.services.wealth_freedom import compute_wealth_freedom

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/wealth-freedom",
    response_model=WealthFreedomMetrics,
    summary="财富自由综合计算（API #15）",
)
def get_wealth_freedom_metrics(db: Session = Depends(get_db)) -> WealthFreedomMetrics:
    return compute_wealth_freedom(db, datetime.now(timezone.utc))
