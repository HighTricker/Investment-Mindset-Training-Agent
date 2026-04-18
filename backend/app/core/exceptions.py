"""业务错误码统一定义。

SSOT：../../../开发文档/API_template.md §业务错误码枚举（13 个）。
路由层统一用 `business_error(...)` 抛出 HTTPException，前端按 code 字符串分派 UI 响应。
"""
from __future__ import annotations

from enum import StrEnum

from fastapi import HTTPException


class ErrorCode(StrEnum):
    INVALID_SYMBOL = "INVALID_SYMBOL"
    DUPLICATE_ASSET = "DUPLICATE_ASSET"
    INSUFFICIENT_POSITION = "INSUFFICIENT_POSITION"
    ASSET_NOT_FOUND = "ASSET_NOT_FOUND"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    EXCHANGE_RATE_MISSING = "EXCHANGE_RATE_MISSING"
    PRICE_MISSING = "PRICE_MISSING"
    EXTERNAL_SOURCE_FAILED = "EXTERNAL_SOURCE_FAILED"
    INVALID_EMAIL_FORMAT = "INVALID_EMAIL_FORMAT"
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"
    NO_ACTIVE_ASSETS = "NO_ACTIVE_ASSETS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def business_error(
    status_code: int,
    code: ErrorCode,
    message: str,
    **details: object,
) -> HTTPException:
    """构造与 API_template.md §统一错误响应格式 对齐的 HTTPException。"""
    detail: dict[str, object] = {"code": code.value, "message": message}
    if details:
        detail["details"] = details
    return HTTPException(status_code=status_code, detail=detail)
