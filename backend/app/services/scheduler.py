"""APScheduler 定时任务服务（P5 V2）。

启动时从 .env 读 cron 表达式，注册每月自动发送投资月报。
- REPORT_SCHEDULE_ENABLED=false（本地默认） → 不启动
- REPORT_SCHEDULE_ENABLED=true（生产） → 按 REPORT_SCHEDULE_CRON 表达式触发
- 默认 cron "0 9 1 * *" = 每月 1 号 9:00（北京时区）

失败策略：任务内部异常被捕获并记录日志，不影响下次触发；max_instances=1 避免重叠；
coalesce=True 避免服务重启后错过的任务堆积执行。
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def _run_scheduled_report() -> None:
    """定时任务回调：以服务器本地时区 today 为 send_date 生成 + 发送月报。"""
    # 延迟导入，避免启动时循环依赖
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.user_setting import UserSetting
    from app.services.email_sender import EmailSenderError, send_html_email
    from app.services.report_builder import build_report_html, build_report_subject

    send_date = date.today()
    logger.info("Scheduled report triggered, send_date=%s", send_date)
    try:
        with SessionLocal() as db:
            email = db.execute(select(UserSetting.email)).scalar_one_or_none()
            if not email:
                logger.warning(
                    "Scheduled report skipped: user_settings.email is empty"
                )
                return
            html = build_report_html(db, send_date)
            subject = build_report_subject(send_date)
        send_html_email(email, subject, html)
        logger.info("Scheduled report sent to %s", email)
    except EmailSenderError as e:
        logger.error("Scheduled report SMTP failed: %s", e)
    except Exception:
        logger.exception("Scheduled report unexpected error")


def init_scheduler() -> BackgroundScheduler | None:
    """FastAPI startup 调用。本地开发默认 disabled，生产 enable。"""
    global _scheduler
    if not settings.report_schedule_enabled:
        logger.info("Scheduler disabled (REPORT_SCHEDULE_ENABLED=false)")
        return None
    try:
        trigger = CronTrigger.from_crontab(
            settings.report_schedule_cron, timezone="Asia/Shanghai",
        )
    except ValueError as e:
        logger.error(
            "Invalid REPORT_SCHEDULE_CRON=%r: %s",
            settings.report_schedule_cron, e,
        )
        return None
    sch = BackgroundScheduler(timezone="Asia/Shanghai")
    sch.add_job(
        _run_scheduled_report,
        trigger=trigger,
        id="monthly_report",
        max_instances=1,
        coalesce=True,
    )
    sch.start()
    _scheduler = sch
    logger.info(
        "Scheduler started: cron=%r tz=Asia/Shanghai",
        settings.report_schedule_cron,
    )
    return sch


def shutdown_scheduler() -> None:
    """FastAPI shutdown 调用，graceful 关闭。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
