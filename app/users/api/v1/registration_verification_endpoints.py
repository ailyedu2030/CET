"""注册验证码API端点 - 🔥需求20验收标准3."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.services.cache_service import CacheService, get_cache_service
from app.users.schemas.mfa_schemas import (
    SMSVerificationRequest,
    VerificationCodeRequest,
    VerificationResponse,
)
from app.users.services.registration_verification_service import (
    RegistrationVerificationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registration", tags=["注册验证码"])


@router.post("/sms/send", response_model=VerificationResponse)
async def send_registration_sms_verification_code(
    request: SMSVerificationRequest,
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> VerificationResponse:
    """发送注册短信验证码 - 🔥需求20验收标准3."""
    try:
        service = RegistrationVerificationService(db, cache_service)
        result = await service.send_sms_verification_code(
            phone_number=request.phone_number,
            purpose=request.purpose,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"发送注册短信验证码到 {request.phone_number}")

        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_in=result.get("expires_in"),
            masked_target=result.get("masked_target"),
            verified_user_id=None,
            remaining_attempts=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送注册短信验证码失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送短信验证码失败",
        ) from e


@router.post("/sms/verify", response_model=VerificationResponse)
async def verify_registration_sms_code(
    request: VerificationCodeRequest,
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> VerificationResponse:
    """验证注册短信验证码 - 🔥需求20验收标准3."""
    try:
        service = RegistrationVerificationService(db, cache_service)
        result = await service.verify_sms_code(
            phone_number=request.target,
            verification_code=request.verification_code,
            purpose=request.purpose,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"注册短信验证码验证成功: {request.target}")

        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_in=None,
            masked_target=None,
            verified_user_id=result.get("verified_user_id"),
            remaining_attempts=result.get("remaining_attempts"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证注册短信验证码失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证短信验证码失败",
        ) from e


@router.get("/sms/status/{phone_number}")
async def get_verification_status(
    phone_number: str,
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取验证码发送状态 - 用于检查重发限制."""
    try:
        service = RegistrationVerificationService(None, cache_service)
        status = await service.get_verification_status(phone_number)

        return {
            "phone_number": phone_number,
            "can_send": status.get("can_send", True),
            "next_send_time": status.get("next_send_time"),
            "remaining_attempts": status.get("remaining_attempts", 3),
        }

    except Exception as e:
        logger.error(f"获取验证状态失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取验证状态失败",
        ) from e
