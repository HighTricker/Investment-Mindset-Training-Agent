"""用户设置 routers（API #7 GET、#8 PUT）。"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ErrorCode, business_error
from app.models.user_setting import UserSetting
from app.schemas.user_setting import UserSettingResponse, UserSettingUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-settings", tags=["user-settings"])

# 宽松邮箱校验（RFC 5322 的完整正则太复杂，MVP 用常见字符校验）
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _get_or_create_setting(db: Session) -> UserSetting:
    """若 user_settings 表无记录则插入默认后返回。API #7 业务规则。"""
    setting = db.execute(select(UserSetting).order_by(UserSetting.id).limit(1)).scalar_one_or_none()
    if setting is None:
        setting = UserSetting()
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.get("", response_model=UserSettingResponse, summary="获取用户设置（API #7）")
def get_user_settings(db: Session = Depends(get_db)) -> UserSettingResponse:
    setting = _get_or_create_setting(db)
    return UserSettingResponse.model_validate(setting)


@router.put("", response_model=UserSettingResponse, summary="更新用户设置（API #8）")
def update_user_settings(
    req: UserSettingUpdate,
    db: Session = Depends(get_db),
) -> UserSettingResponse:
    # email 格式校验映射为业务错误码（Pydantic 默认 VALIDATION_ERROR 不够精确）
    if req.email is not None and req.email != "":
        if not EMAIL_PATTERN.match(req.email):
            raise business_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                ErrorCode.INVALID_EMAIL_FORMAT,
                "邮箱格式不正确",
            )

    setting = _get_or_create_setting(db)

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # CashOrIncomeCurrency 枚举值需要 .value
        if hasattr(value, "value"):
            value = value.value
        setattr(setting, field, value)

    setting.updated_at = datetime.now(timezone.utc).isoformat()

    db.commit()
    db.refresh(setting)
    logger.info("user settings updated: fields=%s", list(update_data.keys()))
    return UserSettingResponse.model_validate(setting)
