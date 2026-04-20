"""SMTP 邮件发送服务（P5 V2）。

Python 标准库 smtplib + email.mime，支持 SSL（465）和 STARTTLS（587）两种连接模式。
SMTP 凭证从 .env 读取（见 core/config.py 的 smtp_* 字段）。

异常模型：
    - EmailSenderError: SMTP 连接/认证/协议异常 → 上层 routers 映射 EMAIL_SEND_FAILED (502)
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailSenderError(RuntimeError):
    """SMTP 发送失败（连接超时 / 认证失败 / 协议异常）。"""


def send_html_email(to: str, subject: str, html_body: str) -> None:
    """同步发送 HTML 邮件。失败抛 EmailSenderError。

    端口规则:
        - 465: SSL 直连（163 / QQ 邮箱推荐）
        - 587: STARTTLS（Gmail / Outlook 推荐）
        - 其他: 保守走 STARTTLS
    """
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        raise EmailSenderError(
            "SMTP 配置不完整，请检查 backend/.env 的 SMTP_HOST / SMTP_USER / SMTP_PASSWORD"
        )

    host = settings.smtp_host
    port = settings.smtp_port
    user = settings.smtp_user
    password = settings.smtp_password

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("投资月报", user))
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        server: smtplib.SMTP
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        try:
            server.login(user, password)
            server.send_message(msg)
        finally:
            try:
                server.quit()
            except Exception:
                pass
    except smtplib.SMTPAuthenticationError as e:
        logger.warning("SMTP auth failed host=%s user=%s: %s", host, user, e)
        raise EmailSenderError(f"SMTP 认证失败（请检查授权码）：{e}") from e
    except smtplib.SMTPException as e:
        logger.warning("SMTP protocol error host=%s: %s", host, e)
        raise EmailSenderError(f"SMTP 协议错误：{e}") from e
    except OSError as e:
        logger.warning("SMTP network error host=%s: %s", host, e)
        raise EmailSenderError(f"SMTP 网络异常（连接超时或 DNS 失败）：{e}") from e
    except Exception as e:
        logger.exception("SMTP unexpected error")
        raise EmailSenderError(f"邮件发送异常：{e}") from e

    logger.info("Email sent to %s subject=%r", to, subject)
