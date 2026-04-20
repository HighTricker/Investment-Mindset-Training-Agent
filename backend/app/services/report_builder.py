"""投资报告 HTML 生成服务（P5 V2）。

职责：
    - 读取样式配置（每次请求重读 config/report_style.json，手改即时生效）
    - 推导上月（基于 send_date）
    - 查询所有活跃资产 + 建仓 / 当前 / 上月首末日价格
    - 组装成 4 section + AI 点评占位的 HTML 字符串
    - 输出给 routers/report.py 返回 text/html

设计原则：
    - 邮件客户端兼容：全部 table 布局 + inline CSS（不用 className）
    - 样式来自 JSON 配置，用户可手编辑 config/report_style.json 定制
    - 13 列明细表（对齐 P1）+ 动态列名（"N 月收益率"）
    - AI 点评占位 section（V3 接 LLM 时替换内容，结构先就位）

SSOT：../../../开发文档/PRD_template.md §P5 + ../../../开发文档/API_template.md §P5
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ErrorCode, business_error
from app.models.asset import Asset
from app.models.exchange_rate import ExchangeRate
from app.models.price import Price
from app.models.transaction import Transaction
from app.services.calculators import aggregate_transactions

logger = logging.getLogger(__name__)

# 样式配置路径（相对 backend/ 目录，指向项目根的 config/）
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
STYLE_PATH = BACKEND_ROOT.parent / "config" / "report_style.json"


# ============================================================
# 数据结构
# ============================================================
@dataclass
class AssetReportItem:
    asset_id: int
    symbol: str
    name: str
    category: str
    currency: str

    # 聚合
    quantity: float
    cost_price_original: float
    total_invested_cny: float
    current_price_original: float
    current_rate_to_cny: float
    current_value_cny: float

    # 收益率
    cumulative_return: float | None
    monthly_return: float | None  # 上月首末日 close 差

    # 后计算
    position_ratio: float | None = None


@dataclass
class ReportData:
    send_date: date
    month_label: str  # "3月"
    year_month_title: str  # "2026 年 3 月"
    items: list[AssetReportItem]
    total_invested_cny: float
    total_value_cny: float
    total_profit_loss_cny: float
    total_return_rate: float | None
    best: AssetReportItem | None
    worst: AssetReportItem | None
    style: dict[str, Any] = field(default_factory=dict)


# ============================================================
# 顶层入口
# ============================================================
def build_report_html(db: Session, send_date: date) -> str:
    """生成投资月报 HTML。

    Raises:
        HTTPException(422, NO_ACTIVE_ASSETS): 无活跃资产
        HTTPException(422, PRICE_MISSING): 某资产 send_date 前无价格
        HTTPException(500, INTERNAL_ERROR): 样式配置文件缺失/格式错误
    """
    style = _load_style()
    data = _collect_report_data(db, send_date, style)
    return _render_html(data)


def build_report_subject(send_date: date) -> str:
    """邮件主题：`YYYY年M月投资月报` 基于上月。"""
    prev = _previous_month_first_day(send_date)
    return f"{prev.year}年{prev.month}月投资月报"


# ============================================================
# 样式读取（每次调用读文件，手改即时生效）
# ============================================================
def _load_style() -> dict[str, Any]:
    if not STYLE_PATH.exists():
        raise business_error(
            500, ErrorCode.INTERNAL_ERROR,
            f"样式配置文件缺失：{STYLE_PATH}",
        )
    try:
        with STYLE_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise business_error(
            500, ErrorCode.INTERNAL_ERROR,
            f"样式配置文件格式错误：{e}",
        )
    # 合并到平铺字典方便后续 f-string 使用
    return {
        **raw.get("style", {}),
        **{"report": raw.get("report", {})},
    }


# ============================================================
# 日期工具
# ============================================================
def _previous_month_first_day(d: date) -> date:
    """返回 d 所在月的 **前一个自然月** 的 1 号。

    例：d=2026-04-17 → 2026-03-01
    例：d=2026-01-15 → 2025-12-01
    """
    if d.month == 1:
        return date(d.year - 1, 12, 1)
    return date(d.year, d.month - 1, 1)


def _current_month_first_day(d: date) -> date:
    return date(d.year, d.month, 1)


# ============================================================
# 数据收集
# ============================================================
def _collect_report_data(
    db: Session, send_date: date, style: dict[str, Any],
) -> ReportData:
    prev_month = _previous_month_first_day(send_date)
    current_month = _current_month_first_day(send_date)

    assets = db.execute(
        select(Asset).where(Asset.is_active == 1).order_by(Asset.id)
    ).scalars().all()
    if not assets:
        raise business_error(
            422, ErrorCode.NO_ACTIVE_ASSETS,
            "当前无活跃资产，无法生成报告",
        )

    send_date_iso = send_date.isoformat()
    items: list[AssetReportItem] = []
    for asset in assets:
        items.append(_build_asset_item(
            db, asset, send_date_iso,
            prev_month.isoformat(), current_month.isoformat(),
        ))

    # 二遍：仓位占比
    total_value = sum(it.current_value_cny for it in items)
    for it in items:
        it.position_ratio = (
            it.current_value_cny / total_value if total_value > 0 else None
        )

    # 汇总
    total_invested = sum(it.total_invested_cny for it in items)
    total_pl = total_value - total_invested
    total_return = total_pl / total_invested if total_invested > 0 else None

    # 最佳/最差（基于上月收益率；None 排除）
    rated = [it for it in items if it.monthly_return is not None]
    best = max(rated, key=lambda x: x.monthly_return) if rated else None  # type: ignore[arg-type, return-value]
    worst = min(rated, key=lambda x: x.monthly_return) if rated else None  # type: ignore[arg-type, return-value]

    return ReportData(
        send_date=send_date,
        month_label=f"{prev_month.month}月",
        year_month_title=f"{prev_month.year} 年 {prev_month.month} 月 投资月报",
        items=items,
        total_invested_cny=total_invested,
        total_value_cny=total_value,
        total_profit_loss_cny=total_pl,
        total_return_rate=total_return,
        best=best,
        worst=worst,
        style=style,
    )


def _build_asset_item(
    db: Session, asset: Asset,
    send_date_iso: str, prev_month_iso: str, current_month_iso: str,
) -> AssetReportItem:
    # 交易聚合（只算 send_date 之前的交易）
    txs = db.execute(
        select(Transaction).where(
            Transaction.asset_id == asset.id,
            Transaction.date < send_date_iso,
        )
    ).scalars().all()
    if not txs:
        raise business_error(
            422, ErrorCode.PRICE_MISSING,
            f"资产 {asset.symbol} 在 {send_date_iso} 前无交易",
        )
    agg = aggregate_transactions([
        {
            "type": tx.type, "quantity": tx.quantity,
            "price": tx.price, "exchange_rate_to_cny": tx.exchange_rate_to_cny,
        }
        for tx in txs
    ])

    # 当前价（send_date 前最新一条 prices）
    current_price_row = db.execute(
        select(Price.close_price).where(
            Price.asset_id == asset.id,
            Price.date < send_date_iso,
        ).order_by(Price.date.desc()).limit(1)
    ).scalar_one_or_none()
    if current_price_row is None:
        raise business_error(
            422, ErrorCode.PRICE_MISSING,
            f"资产 {asset.symbol} 在 {send_date_iso} 前无价格",
        )
    current_price = float(current_price_row)

    # 当前汇率（send_date 前最新一条；CNY=1）
    if asset.currency == "CNY":
        current_rate = 1.0
    else:
        rate_row = db.execute(
            select(ExchangeRate.rate_to_cny).where(
                ExchangeRate.currency == asset.currency,
                ExchangeRate.date < send_date_iso,
            ).order_by(ExchangeRate.date.desc()).limit(1)
        ).scalar_one_or_none()
        if rate_row is None:
            raise business_error(
                422, ErrorCode.EXCHANGE_RATE_MISSING,
                f"币种 {asset.currency} 在 {send_date_iso} 前无汇率",
            )
        current_rate = float(rate_row)

    current_value_cny = agg.current_quantity * current_price * current_rate

    cumulative = (
        (current_price - agg.cost_price_original) / agg.cost_price_original
        if agg.cost_price_original > 0 else None
    )

    # 上月首末日收盘价
    month_rows = db.execute(
        select(Price.date, Price.close_price).where(
            Price.asset_id == asset.id,
            Price.date >= prev_month_iso,
            Price.date < current_month_iso,
        ).order_by(Price.date)
    ).all()
    monthly_return: float | None = None
    if len(month_rows) >= 2:
        first_close = float(month_rows[0].close_price)
        last_close = float(month_rows[-1].close_price)
        if first_close > 0:
            monthly_return = (last_close - first_close) / first_close

    return AssetReportItem(
        asset_id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        category=asset.category,
        currency=asset.currency,
        quantity=agg.current_quantity,
        cost_price_original=agg.cost_price_original,
        total_invested_cny=agg.total_initial_investment_cny,
        current_price_original=current_price,
        current_rate_to_cny=current_rate,
        current_value_cny=current_value_cny,
        cumulative_return=cumulative,
        monthly_return=monthly_return,
    )


# ============================================================
# HTML 渲染
# ============================================================
def _fmt_pct(v: float | None, signed: bool = True) -> str:
    if v is None:
        return "—"
    sign = "+" if signed and v > 0 else ""
    return f"{sign}{v * 100:.2f}%"


def _fmt_cny(v: float | None) -> str:
    if v is None:
        return "—"
    return f"¥{v:,.2f}"


def _fmt_num(v: float | None, decimals: int = 4) -> str:
    if v is None:
        return "—"
    return f"{v:,.{decimals}f}"


def _rate_color(v: float | None, colors: dict[str, Any]) -> str:
    if v is None or v == 0:
        return colors.get("text_secondary", "#8E8E93")
    return colors["positive"] if v > 0 else colors["negative"]


def _card_bg(v: float | None, colors: dict[str, Any]) -> str:
    if v is None or v == 0:
        return colors.get("neutral_background", "#F2F2F7")
    return (
        colors.get("card_positive_bg", "#D4F4DD")
        if v > 0
        else colors.get("card_negative_bg", "#FFE5E3")
    )


def _render_html(data: ReportData) -> str:
    colors = data.style.get("colors", {})
    typo = data.style.get("typography", {})
    spacing = data.style.get("spacing", {})
    report_cfg = data.style.get("report", {})

    font = typo.get("font_family", "-apple-system, BlinkMacSystemFont, sans-serif")
    max_width = report_cfg.get("max_width", "800px")
    radius = spacing.get("border_radius", "8px")
    brand = report_cfg.get("brand_name", "还有多久可以财富自由")
    footer_text = report_cfg.get("footer_text", "数据来源：yfinance + akshare")

    header = _render_header(data.year_month_title, colors, typo, spacing)
    overview = _render_overview(data, colors, typo, spacing, radius)
    best_worst = _render_best_worst(data, colors, typo, spacing, radius)
    cards_grid = _render_asset_cards(data, colors, typo, spacing, radius)
    ai_section = _render_ai_placeholder(colors, typo, spacing, radius)
    detail_table = _render_detail_table(data, colors, typo, spacing)
    footer = _render_footer(footer_text, brand, colors, typo)

    return (
        f'<!DOCTYPE html>\n'
        f'<html lang="zh-CN"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{data.year_month_title}</title></head>'
        f'<body style="font-family:{font};max-width:{max_width};margin:0 auto;'
        f'padding:24px;color:{colors.get("text_primary", "#1C1C1E")};'
        f'background:#ffffff">'
        f'{header}{overview}{best_worst}{cards_grid}'
        f'{ai_section}{detail_table}{footer}'
        f'</body></html>'
    )


def _render_header(title: str, colors: dict, typo: dict, spacing: dict) -> str:
    return (
        f'<h1 style="color:{colors.get("title", "#1C1C1E")};'
        f'font-size:{typo.get("h1_size", "22px")};'
        f'border-bottom:2px solid {colors.get("border", "#D1D1D6")};'
        f'padding-bottom:12px;margin:0 0 20px">'
        f'{title}</h1>'
    )


def _render_overview(data: ReportData, colors: dict, typo: dict, spacing: dict, radius: str) -> str:
    pl_color = _rate_color(data.total_profit_loss_cny, colors)
    ret_color = _rate_color(data.total_return_rate, colors)
    bg = colors.get("neutral_background", "#F2F2F7")
    label_size = typo.get("label_size", "13px")
    value_size = typo.get("value_size", "20px")
    secondary = colors.get("text_secondary", "#8E8E93")

    def _cell(label: str, value: str, color: str | None = None) -> str:
        c = color or colors.get("text_primary", "#1C1C1E")
        return (
            f'<td style="width:50%;padding:6px">'
            f'<div style="text-align:center;padding:14px;background:{bg};'
            f'border-radius:{radius}">'
            f'<div style="color:{secondary};font-size:{label_size}">{label}</div>'
            f'<div style="font-size:{value_size};font-weight:700;color:{c};margin-top:4px">{value}</div>'
            f'</div></td>'
        )

    return (
        f'<table style="width:100%;border-collapse:collapse;margin:20px 0">'
        f'<tr>{_cell("总投入(CNY)", _fmt_cny(data.total_invested_cny))}'
        f'{_cell("当前价值(CNY)", _fmt_cny(data.total_value_cny))}</tr>'
        f'<tr>{_cell("总收益率", _fmt_pct(data.total_return_rate), ret_color)}'
        f'{_cell("盈亏(CNY)", _fmt_cny(data.total_profit_loss_cny), pl_color)}</tr>'
        f'</table>'
    )


def _render_best_worst(data: ReportData, colors: dict, typo: dict, spacing: dict, radius: str) -> str:
    pos_bg = colors.get("card_positive_bg", "#D4F4DD")
    neg_bg = colors.get("card_negative_bg", "#FFE5E3")
    label_size = typo.get("label_size", "13px")
    secondary = colors.get("text_secondary", "#8E8E93")

    def _card(title: str, it: AssetReportItem | None, bg: str, color: str) -> str:
        inner = (
            f'<div style="font-size:18px;font-weight:600;margin-top:6px">'
            f'{it.name if it else "—"}</div>'
            f'<div style="color:{color};font-size:16px;margin-top:4px">'
            f'{_fmt_pct(it.monthly_return) if it else "—"}</div>'
        )
        return (
            f'<td style="width:50%;padding:6px">'
            f'<div style="background:{bg};padding:14px;border-radius:{radius};text-align:center">'
            f'<div style="color:{secondary};font-size:{label_size}">{title}</div>'
            f'{inner}</div></td>'
        )

    return (
        f'<table style="width:100%;border-collapse:collapse;margin:16px 0">'
        f'<tr>{_card(f"{data.month_label}最佳", data.best, pos_bg, colors["positive"])}'
        f'{_card(f"{data.month_label}最差", data.worst, neg_bg, colors["negative"])}</tr>'
        f'</table>'
    )


def _render_asset_cards(data: ReportData, colors: dict, typo: dict, spacing: dict, radius: str) -> str:
    secondary = colors.get("text_secondary", "#8E8E93")
    label_size = typo.get("label_size", "13px")
    cells: list[str] = []
    for it in data.items:
        bg = _card_bg(it.monthly_return, colors)
        color = _rate_color(it.monthly_return, colors)
        cells.append(
            f'<td style="width:33.33%;padding:6px;vertical-align:top">'
            f'<div style="background:{bg};padding:12px 14px;border-radius:{radius};text-align:center">'
            f'<div style="color:{secondary};font-size:{label_size}">{it.category}</div>'
            f'<div style="font-size:16px;font-weight:600;margin-top:4px">{it.name}</div>'
            f'<div style="color:{color};font-size:15px;margin-top:4px">'
            f'{_fmt_pct(it.monthly_return)}</div>'
            f'</div></td>'
        )
    # 每 3 个一行
    rows: list[str] = []
    for i in range(0, len(cells), 3):
        group = cells[i:i + 3]
        while len(group) < 3:
            group.append('<td style="width:33.33%"></td>')
        rows.append(f'<tr>{"".join(group)}</tr>')
    return (
        f'<h2 style="color:{colors.get("subtitle", "#48484A")};'
        f'font-size:{typo.get("h2_size", "18px")};margin:24px 0 8px">'
        f'{data.month_label}各资产表现</h2>'
        f'<table style="width:100%;border-collapse:collapse">{"".join(rows)}</table>'
    )


def _render_ai_placeholder(colors: dict, typo: dict, spacing: dict, radius: str) -> str:
    bg = colors.get("neutral_background", "#F2F2F7")
    secondary = colors.get("text_secondary", "#8E8E93")
    return (
        f'<div style="background:{bg};padding:16px;border-radius:{radius};'
        f'margin:24px 0;border:1px dashed {colors.get("border", "#D1D1D6")}">'
        f'<div style="font-size:14px;font-weight:600;'
        f'color:{colors.get("title", "#1C1C1E")}">🤖 AI 月度点评</div>'
        f'<div style="margin-top:8px;font-size:13px;color:{secondary};font-style:italic">'
        f'（功能待开发）V3 阶段接入 LLM 生成约 150 字智能点评，'
        f'基于本月表现、收益率分布、仓位变化自动生成。'
        f'</div></div>'
    )


def _render_detail_table(data: ReportData, colors: dict, typo: dict, spacing: dict) -> str:
    header_bg = colors.get("neutral_background", "#F2F2F7")
    border = colors.get("border", "#D1D1D6")
    table_size = typo.get("table_size", "12px")
    subtitle = colors.get("subtitle", "#48484A")
    secondary = colors.get("text_secondary", "#8E8E93")
    month_col = f"{data.month_label}收益率"

    # 13 列表头（对齐 P1 AssetsTable）
    headers = [
        "序号", "代码", "名称", "类别",
        "初始投入(CNY)", "持仓数量", "成本(原币)", "现价(原币)",
        "仓位占比", "汇率(对CNY)", "当前值(CNY)",
        "累计收益率", month_col,
    ]
    th = "".join(
        f'<th style="padding:8px 6px;text-align:{"right" if i >= 4 else "left"};'
        f'border-bottom:1px solid {border};font-weight:600;color:{subtitle}">'
        f'{h}</th>'
        for i, h in enumerate(headers)
    )

    rows_html: list[str] = []
    for idx, it in enumerate(data.items, start=1):
        cum_color = _rate_color(it.cumulative_return, colors)
        mon_color = _rate_color(it.monthly_return, colors)
        tds = [
            f'<td style="padding:6px;color:{secondary}">{idx}</td>',
            f'<td style="padding:6px">{it.symbol}</td>',
            f'<td style="padding:6px">{it.name}</td>',
            f'<td style="padding:6px;color:{secondary}">{it.category}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_cny(it.total_invested_cny)}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_num(it.quantity, 4)}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_num(it.cost_price_original, 4)}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_num(it.current_price_original, 4)}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_pct(it.position_ratio, signed=False)}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_num(it.current_rate_to_cny, 4)}</td>',
            f'<td style="padding:6px;text-align:right">{_fmt_cny(it.current_value_cny)}</td>',
            f'<td style="padding:6px;text-align:right;color:{cum_color}">{_fmt_pct(it.cumulative_return)}</td>',
            f'<td style="padding:6px;text-align:right;color:{mon_color}">{_fmt_pct(it.monthly_return)}</td>',
        ]
        rows_html.append(
            f'<tr style="border-bottom:1px solid {border}">{"".join(tds)}</tr>'
        )

    return (
        f'<h2 style="color:{subtitle};font-size:{typo.get("h2_size", "18px")};'
        f'margin:24px 0 8px">资产明细</h2>'
        f'<div style="overflow-x:auto">'
        f'<table style="width:100%;border-collapse:collapse;font-size:{table_size}">'
        f'<thead><tr style="background:{header_bg}">{th}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table></div>'
    )


def _render_footer(text: str, brand: str, colors: dict, typo: dict) -> str:
    return (
        f'<p style="color:{colors.get("text_secondary", "#8E8E93")};'
        f'font-size:12px;margin-top:32px;'
        f'border-top:1px solid {colors.get("border", "#D1D1D6")};'
        f'padding-top:12px;text-align:center">'
        f'此报告由 {brand} 自动生成 | {text}'
        f'</p>'
    )
