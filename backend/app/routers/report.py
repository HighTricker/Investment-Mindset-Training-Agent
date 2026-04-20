"""P5 投资报告 routers（API #17 preview / #18 send，V2）。"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.user_setting import UserSetting
from app.schemas.report import ReportRequest, SendReportResponse
from app.services.email_sender import EmailSenderError, send_html_email
from app.services.report_builder import build_report_html, build_report_subject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])

# 邮箱格式简单校验（更严格在前端 + SMTP 服务器兜底）
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@router.post(
    "/preview",
    response_class=HTMLResponse,
    summary="生成投资报告预览 HTML（API #17）",
)
def preview_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    send_date = payload.send_date or date.today()
    html = build_report_html(db, send_date)
    return HTMLResponse(content=html, status_code=200)


@router.post(
    "/send",
    response_model=SendReportResponse,
    summary="发送投资报告邮件（API #18）",
)
def send_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
) -> SendReportResponse:
    send_date = payload.send_date or date.today()

    email = db.execute(select(UserSetting.email)).scalar_one_or_none()
    if not email or not EMAIL_PATTERN.match(email):
        raise business_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            ErrorCode.INVALID_EMAIL_FORMAT,
            "未保存收件人邮箱或邮箱格式非法，请先在 P5 页面保存有效邮箱",
        )

    html = build_report_html(db, send_date)
    subject = build_report_subject(send_date)

    try:
        send_html_email(email, subject, html)
    except EmailSenderError as e:
        logger.warning("Email send failed to %s: %s", email, e)
        raise business_error(
            status.HTTP_502_BAD_GATEWAY,
            ErrorCode.EMAIL_SEND_FAILED,
            f"邮件发送失败：{e}",
            smtp_error=str(e),
        )

    return SendReportResponse(
        status="sent",
        recipient=email,
        send_date=send_date.isoformat(),
        subject=subject,
        sent_at=datetime.now(timezone.utc).isoformat(),
    )
