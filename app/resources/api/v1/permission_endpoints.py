"""
资源权限管理API端点 - 需求11三级权限共享机制
符合设计文档技术要求：零缺陷交付、统一异常处理、完整日志记录
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
)
from app.resources.schemas.permission_schemas import (
    PermissionSettingRequest,
    PermissionSettingResponse,
    SharedResourceResponse,
)
from app.resources.services.permission_service import PermissionService
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/api/v1/resource-permissions", tags=["资源权限管理"])


@router.post("/permissions", response_model=PermissionSettingResponse)
async def set_resource_permission(
    permission_data: PermissionSettingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PermissionSettingResponse:
    """
    设置资源权限 - 需求11验收标准5
    支持三级权限：私有/班级/公开，细粒度权限控制
    """
    try:
        logger.info(
            "设置资源权限",
            extra={
                "user_id": current_user.id,
                "resource_type": permission_data.resource_type,
                "resource_id": permission_data.resource_id,
                "permission": permission_data.permission,
                "action": "set_resource_permission",
            },
        )

        service = PermissionService(db)
        result = await service.set_resource_permission(permission_data, current_user.id)

        logger.info(
            "权限设置成功",
            extra={
                "resource_type": permission_data.resource_type,
                "resource_id": permission_data.resource_id,
                "new_permission": permission_data.permission,
            },
        )

        return result

    except PermissionDeniedError as e:
        logger.warning(
            f"权限设置被拒绝: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": permission_data.resource_type,
                "resource_id": permission_data.resource_id,
            },
        )
        raise HTTPException(status_code=403, detail=e.message) from e
    except ResourceNotFoundError as e:
        logger.warning(
            f"资源不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": permission_data.resource_type,
                "resource_id": permission_data.resource_id,
            },
        )
        raise HTTPException(status_code=404, detail=e.message) from e
    except ValidationError as e:
        logger.warning(
            f"权限数据验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"设置权限失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": permission_data.resource_type,
                "resource_id": permission_data.resource_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="设置权限失败") from e


@router.get("/shared/{resource_type}", response_model=list[SharedResourceResponse])
async def get_shared_resources(
    resource_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SharedResourceResponse]:
    """
    获取共享资源列表 - 需求11验收标准5
    根据用户权限返回可访问的共享资源
    """
    try:
        # 验证资源类型
        valid_types = ["vocabulary", "knowledge", "material", "syllabus"]
        if resource_type not in valid_types:
            raise ValidationError(
                message="无效的资源类型",
                error_code="INVALID_RESOURCE_TYPE",
                details={"valid_types": valid_types},
            )

        logger.info(
            "获取共享资源列表",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "action": "get_shared_resources",
            },
        )

        service = PermissionService(db)
        resources = await service.get_shared_resources(resource_type, current_user.id)

        logger.info(
            f"成功获取{len(resources)}个共享资源",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_count": len(resources),
            },
        )

        return resources

    except ValidationError as e:
        logger.warning(
            f"参数验证失败: {e.message}",
            extra={"user_id": current_user.id, "resource_type": resource_type},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取共享资源失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="获取共享资源失败") from e


@router.get(
    "/permissions/{resource_type}/{resource_id}",
    response_model=PermissionSettingResponse,
)
async def get_resource_permission(
    resource_type: str,
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PermissionSettingResponse:
    """
    获取资源权限设置 - 需求11验收标准5
    返回资源的当前权限配置
    """
    try:
        logger.info(
            "获取资源权限设置",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": "get_resource_permission",
            },
        )

        service = PermissionService(db)
        permission = await service.get_resource_permission(
            resource_type, resource_id, current_user.id
        )

        logger.info(
            "成功获取权限设置",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "permission": permission.permission,
            },
        )

        return permission

    except ResourceNotFoundError as e:
        logger.warning(
            f"资源不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        raise HTTPException(status_code=404, detail=e.message) from e
    except PermissionDeniedError as e:
        logger.warning(
            f"权限不足: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        raise HTTPException(status_code=403, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取权限设置失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="获取权限设置失败") from e


@router.delete("/permissions/{resource_type}/{resource_id}")
async def reset_resource_permission(
    resource_type: str,
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    重置资源权限为私有 - 需求11验收标准5
    将资源权限重置为默认的私有状态
    """
    try:
        logger.info(
            "重置资源权限",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": "reset_resource_permission",
            },
        )

        service = PermissionService(db)
        await service.reset_resource_permission(
            resource_type, resource_id, current_user.id
        )

        logger.info(
            "权限重置成功",
            extra={"resource_type": resource_type, "resource_id": resource_id},
        )

        return {"success": True, "message": "权限已重置为私有"}

    except ResourceNotFoundError as e:
        logger.warning(
            f"资源不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        raise HTTPException(status_code=404, detail=e.message) from e
    except PermissionDeniedError as e:
        logger.warning(
            f"权限不足: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        raise HTTPException(status_code=403, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"重置权限失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="重置权限失败") from e


@router.get("/permissions/my-shared", response_model=list[SharedResourceResponse])
async def get_my_shared_resources(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[SharedResourceResponse]:
    """
    获取我分享的资源列表 - 需求11验收标准5
    返回当前用户分享给他人的所有资源
    """
    try:
        logger.info(
            "获取我分享的资源列表",
            extra={"user_id": current_user.id, "action": "get_my_shared_resources"},
        )

        service = PermissionService(db)
        resources = await service.get_my_shared_resources(current_user.id)

        logger.info(
            f"成功获取{len(resources)}个分享资源",
            extra={"user_id": current_user.id, "shared_count": len(resources)},
        )

        return resources

    except Exception as e:
        logger.error(
            f"获取分享资源失败: {str(e)}",
            extra={"user_id": current_user.id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="获取分享资源失败") from e
