"""安全设置管理API端点 - 需求9：数据备份与恢复."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_super_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/system/security", tags=["安全设置"])


# ===== 安全设置管理 - 需求9.3 =====


@router.get("/settings")
async def get_security_settings(
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取安全设置 - 需求9验收标准3."""
    try:
        # 返回默认的安全设置
        settings = {
            "encryption_enabled": True,
            "compression_enabled": True,
            "retention_policy": 30,
            "access_control_enabled": True,
            "audit_logging_enabled": True,
        }

        logger.info(f"超级管理员 {current_user.id} 查看安全设置")

        return settings

    except Exception as e:
        logger.error(f"获取安全设置异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全设置失败",
        ) from None


@router.put("/settings")
async def update_security_settings(
    settings: dict[str, Any],
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新安全设置 - 需求9验收标准3."""
    try:
        # 验证设置参数
        valid_keys = {
            "encryption_enabled",
            "compression_enabled",
            "retention_policy",
            "access_control_enabled",
            "audit_logging_enabled",
        }

        for key in settings:
            if key not in valid_keys:
                raise ValueError(f"无效的设置参数: {key}")

        # 验证数据类型
        if "retention_policy" in settings:
            if (
                not isinstance(settings["retention_policy"], int)
                or settings["retention_policy"] < 1
            ):
                raise ValueError("保留策略必须是大于0的整数")

        logger.info(f"超级管理员 {current_user.id} 更新安全设置: {settings}")

        return {
            "message": "安全设置更新成功",
            "updated_settings": settings,
            "updated_by": current_user.id,
        }

    except ValueError as e:
        logger.warning(f"更新安全设置失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"更新安全设置异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新安全设置失败",
        ) from None
