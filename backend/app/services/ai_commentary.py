"""AI 月度点评服务（V3 P5 报告生成约 150 字中文智能分析）。

调用 OpenAI Chat Completions API（或 OpenAI-compatible 端点如 DeepSeek / 智谱 /
SiliconFlow 等，通过 OPENAI_BASE_URL 切换）。

降级策略：
    - AI_COMMENTARY_ENABLED=false → 返回 None
    - OPENAI_API_KEY 未配 → 返回 None
    - API 调用失败（超时 / 认证 / 网络）→ 返回 None + 日志
调用方（report_builder）据此显示"功能待开发"占位。
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from app.services.report_builder import ReportData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业、务实的个人投资顾问。用户每月收到投资月报邮件，\
你为"AI 月度点评" section 生成约 150 字中文分析。

风格要求：
- 简洁专业，不啰嗦
- 数据为本，基于用户实际仓位和收益率
- 不劝交易（不说"建议卖出 X"/"应该买入 Y"），只做客观观察
- 口吻像亲切的财务顾问
- 约 150 字（最多 200）"""


def generate_ai_commentary(data: "ReportData") -> str | None:
    """基于报告数据调 OpenAI 生成中文月度点评。

    Returns: 约 150 字点评字符串；或 None（未启用 / API KEY 缺失 / 调用失败）。
    """
    if not settings.ai_commentary_enabled:
        return None
    if not settings.openai_api_key:
        logger.info("AI commentary enabled but OPENAI_API_KEY empty, skip")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai SDK not installed, skip AI commentary")
        return None

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        timeout=30.0,
    )
    prompt = _build_prompt(data)
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.5,
        )
    except Exception as e:
        logger.warning("AI commentary API call failed: %s", e)
        return None

    try:
        content = response.choices[0].message.content
        if not content:
            return None
        return content.strip()
    except (IndexError, AttributeError) as e:
        logger.warning("AI commentary response parse failed: %s", e)
        return None


def _build_prompt(data: "ReportData") -> str:
    """把 ReportData 转成 LLM 友好的中文 prompt 文本。"""
    lines: list[str] = [
        f"### {data.month_label} 投资月报数据",
        "",
        f"- 总投入：¥{data.total_invested_cny:,.2f}",
        f"- 当前总价值：¥{data.total_value_cny:,.2f}",
        f"- 总盈亏：¥{data.total_profit_loss_cny:+,.2f}",
    ]
    if data.total_return_rate is not None:
        lines.append(f"- 累计总收益率：{data.total_return_rate * 100:+.2f}%")

    if data.best and data.best.monthly_return is not None:
        b = data.best
        lines.append(
            f"- {data.month_label}最佳：{b.name}（{b.category}）"
            f"{b.monthly_return * 100:+.2f}%"
        )
    if data.worst and data.worst.monthly_return is not None:
        w = data.worst
        lines.append(
            f"- {data.month_label}最差：{w.name}（{w.category}）"
            f"{w.monthly_return * 100:+.2f}%"
        )

    lines.append("")
    lines.append(f"### 各资产{data.month_label}表现")
    for it in data.items:
        m = (
            f"{it.monthly_return * 100:+.2f}%"
            if it.monthly_return is not None else "—"
        )
        c = (
            f"{it.cumulative_return * 100:+.2f}%"
            if it.cumulative_return is not None else "—"
        )
        pr = (
            f"{it.position_ratio * 100:.1f}%"
            if it.position_ratio is not None else "—"
        )
        lines.append(
            f"- {it.name}（{it.category}，仓位 {pr}）：{data.month_label}收益率 {m}，累计 {c}"
        )

    lines.append("")
    lines.append(
        f"请基于以上数据为{data.month_label}生成约 150 字的中文月度点评。"
    )
    return "\n".join(lines)
