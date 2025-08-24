"""用户激活API端点 - 🔥需求20验收标准5."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.email import EmailService, get_email_service
from app.shared.services.cache_service import CacheService, get_cache_service
from app.users.services.activation_service import ActivationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/activation", tags=["用户激活"])


class ActivationRequest(BaseModel):
    """激活请求模型."""

    activation_token: str


class ResendActivationRequest(BaseModel):
    """重发激活邮件请求模型."""

    email: EmailStr


class ActivationResponse(BaseModel):
    """激活响应模型."""

    success: bool
    message: str
    user_id: int | None = None
    username: str | None = None


@router.post("/activate", response_model=ActivationResponse)
async def activate_user_account(
    request: ActivationRequest,
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
    email_service: EmailService = Depends(get_email_service),
) -> ActivationResponse:
    """激活用户账号 - 🔥需求20验收标准5."""
    try:
        service = ActivationService(db, cache_service, email_service)
        result = await service.activate_user(request.activation_token)

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"用户激活成功: {result.get('user_id')}")

        return ActivationResponse(
            success=result["success"],
            message=result["message"],
            user_id=result.get("user_id"),
            username=result.get("username"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户激活失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活失败，请稍后重试",
        ) from e


@router.post("/resend", response_model=dict[str, Any])
async def resend_activation_email(
    request: ResendActivationRequest,
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, Any]:
    """重发激活邮件 - 🔥需求20验收标准5."""
    try:
        service = ActivationService(db, cache_service, email_service)
        result = await service.resend_activation_email(request.email)

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"重发激活邮件成功: {request.email}")

        return {
            "success": result["success"],
            "message": result["message"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重发激活邮件失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重发激活邮件失败",
        ) from e


@router.get("/status/{activation_token}")
async def get_activation_status(
    activation_token: str,
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取激活链接状态."""
    try:
        token_key = f"activation_token:{activation_token}"
        token_data = await cache_service.get(token_key)

        if not token_data:
            return {
                "valid": False,
                "message": "激活链接无效或已过期",
            }

        return {
            "valid": True,
            "message": "激活链接有效",
            "user_id": token_data.get("user_id"),
            "email": token_data.get("email"),
            "created_at": token_data.get("created_at"),
        }

    except Exception as e:
        logger.error(f"获取激活状态失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取激活状态失败",
        ) from e
