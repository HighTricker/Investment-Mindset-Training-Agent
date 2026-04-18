"""财富自由综合计算响应 schema（API #15）。"""
from __future__ import annotations

from pydantic import BaseModel


class AnalysisText(BaseModel):
    line1: str
    line2: str


class WealthFreedomMetrics(BaseModel):
    """GET /metrics/wealth-freedom 响应结构。

    边界条件矩阵（见 API_template.md §API #15）驱动下列字段的 null/非 null：
      - has_prediction=false 时 annualized_rate / predicted_date / analysis_text 均为 null
    """

    achievement_rate: float
    current_hourly_income_cny: float
    target_hourly_income_cny: float
    current_annualized_return_rate: float | None
    required_investment_principal_cny: float | None
    target_total_assets_cny: float
    current_total_cash_cny: float
    current_total_investment_cny: float
    current_total_assets_cny: float
    asset_gap_cny: float
    monthly_savings_cny: float
    predicted_freedom_date: str | None
    years_months_remaining: str | None
    analysis_text: AnalysisText | None
    has_prediction: bool
