"""P5 投资报告相关 Pydantic schemas（V2）。

SSOT：../../../开发文档/API_template.md §P5 报告接口（#17 preview / #18 send）。
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """POST /report/preview 和 POST /report/send 共用请求体。"""

    send_date: date | None = Field(
        default=None,
        description="发送基准日（ISO 8601 YYYY-MM-DD）；不传则用服务器本地时区的 date.today()",
    )


class SendReportResponse(BaseModel):
    """POST /report/send 响应体。"""

    status: str = Field(..., description="固定 'sent'")
    recipient: str = Field(..., description="收件人邮箱")
    send_date: str = Field(..., description="基准发送日 YYYY-MM-DD")
    subject: str = Field(..., description="邮件主题（含年月）")
    sent_at: str = Field(..., description="实际发送完成时刻 ISO 8601 UTC")
