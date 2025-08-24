"""多因素认证API端点 - 需求7：权限中枢管理."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.services.cache_service import CacheService, get_cache_service
from app.users.models import User
from app.users.schemas.mfa_schemas import (
    EmailVerificationRequest,
    MFASessionRequest,
    MFASessionResponse,
    SMSVerificationRequest,
    VerificationCodeRequest,
    VerificationResponse,
)
from app.users.services.mfa_service import MFAService
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mfa", tags=["多因素认证"])


# ===== 短信验证码端点 =====


@router.post("/sms/send", response_model=VerificationResponse)
async def send_sms_verification_code(
    request: SMSVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> VerificationResponse:
    """发送短信验证码 - 需求7验收标准5."""
    try:
        service = MFAService(db, cache_service)
        result = await service.send_sms_verification_code(
            phone_number=request.phone_number,
            user_id=current_user.id,
            purpose=request.purpose,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"用户 {current_user.id} 发送短信验证码")

        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_in=result.get("expires_in"),
            masked_target=result.get("phone_number"),
            verified_user_id=None,
            remaining_attempts=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送短信验证码失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送短信验证码失败",
        ) from e


@router.post("/sms/verify", response_model=VerificationResponse)
async def verify_sms_code(
    request: VerificationCodeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> VerificationResponse:
    """验证短信验证码 - 需求7验收标准5."""
    try:
        service = MFAService(db, cache_service)
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

        logger.info(f"用户 {current_user.id} 短信验证码验证成功")

        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_in=None,
            masked_target=None,
            verified_user_id=result.get("user_id"),
            remaining_attempts=result.get("remaining_attempts"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证短信验证码失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证短信验证码失败",
        ) from e


# ===== 邮箱验证码端点 =====


@router.post("/email/send", response_model=VerificationResponse)
async def send_email_verification_code(
    request: EmailVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> VerificationResponse:
    """发送邮箱验证码 - 需求7验收标准5."""
    try:
        service = MFAService(db, cache_service)
        result = await service.send_email_verification_code(
            email=request.email,
            user_id=current_user.id,
            purpose=request.purpose,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"用户 {current_user.id} 发送邮箱验证码")

        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_in=result.get("expires_in"),
            masked_target=result.get("email"),
            verified_user_id=None,
            remaining_attempts=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送邮箱验证码失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送邮箱验证码失败",
        ) from e


@router.post("/email/verify", response_model=VerificationResponse)
async def verify_email_code(
    request: VerificationCodeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> VerificationResponse:
    """验证邮箱验证码 - 需求7验收标准5."""
    try:
        service = MFAService(db, cache_service)
        result = await service.verify_email_code(
            email=request.target,
            verification_code=request.verification_code,
            purpose=request.purpose,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"用户 {current_user.id} 邮箱验证码验证成功")

        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_in=None,
            masked_target=None,
            verified_user_id=result.get("user_id"),
            remaining_attempts=result.get("remaining_attempts"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证邮箱验证码失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证邮箱验证码失败",
        ) from e


# ===== MFA会话管理端点 =====


@router.post("/session/create", response_model=MFASessionResponse)
async def create_mfa_session(
    request: MFASessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> MFASessionResponse:
    """创建MFA会话 - 需求7验收标准5."""
    try:
        service = MFAService(db, cache_service)
        result = await service.create_mfa_session(
            user_id=current_user.id,
            mfa_method=request.mfa_method,
            session_duration_minutes=request.session_duration_minutes,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"用户 {current_user.id} 创建MFA会话")

        return MFASessionResponse(
            success=result["success"],
            mfa_token=result["mfa_token"],
            expires_in=result["expires_in"],
            mfa_method=result["mfa_method"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建MFA会话失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建MFA会话失败",
        ) from e


@router.get("/session/verify")
async def verify_mfa_session(
    mfa_token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """验证MFA会话 - 需求7验收标准5."""
    try:
        service = MFAService(db, cache_service)
        result = await service.verify_mfa_session(
            user_id=current_user.id,
            mfa_token=mfa_token,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=result["error"],
            )

        logger.info(f"用户 {current_user.id} MFA会话验证成功")

        return {
            "success": result["success"],
            "verified": result["verified"],
            "mfa_method": result["mfa_method"],
            "expires_at": result["expires_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证MFA会话失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证MFA会话失败",
        ) from e


# ===== MFA状态查询端点 =====


@router.get("/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取用户MFA状态 - 需求7验收标准5."""
    try:
        # 这里应该从用户配置中获取MFA设置
        # 目前返回模拟数据
        mfa_status = {
            "user_id": current_user.id,
            "mfa_enabled": False,  # 从用户配置获取
            "available_methods": ["sms", "email"],
            "configured_methods": [],  # 从用户配置获取
            "last_mfa_verification": None,  # 从缓存获取
        }

        logger.info(f"用户 {current_user.id} 查询MFA状态")

        return mfa_status

    except Exception as e:
        logger.error(f"获取MFA状态失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取MFA状态失败",
        ) from e
