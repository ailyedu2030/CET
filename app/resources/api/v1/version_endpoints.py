"""
资源版本控制API端点 - 需求11 Git-like版本管理
符合设计文档技术要求：零缺陷交付、统一异常处理、完整日志记录
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError, ValidationError
from app.resources.schemas.version_schemas import (
    ResourceVersionResponse,
    RollbackRequest,
    RollbackResponse,
    VersionComparisonResponse,
)
from app.resources.services.version_service import VersionService
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/api/v1/resource-versions", tags=["资源版本控制"])


@router.get(
    "/{resource_type}/{resource_id}/versions",
    response_model=list[ResourceVersionResponse],
)
async def get_resource_versions(
    resource_type: str,
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ResourceVersionResponse]:
    """
    获取资源版本历史 - 需求11验收标准6
    支持Git-like版本控制，完整的版本历史记录
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
            "获取资源版本历史",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": "get_resource_versions",
            },
        )

        service = VersionService(db)
        versions = await service.get_resource_versions(
            resource_type, resource_id, current_user.id
        )

        logger.info(
            f"成功获取{len(versions)}个版本记录",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_count": len(versions),
            },
        )

        return versions

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
    except ValidationError as e:
        logger.warning(
            f"参数验证失败: {e.message}",
            extra={"user_id": current_user.id, "resource_type": resource_type},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取版本历史失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="获取版本历史失败") from e


@router.post("/{resource_type}/{resource_id}/rollback", response_model=RollbackResponse)
async def rollback_to_version(
    resource_type: str,
    resource_id: int,
    rollback_data: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RollbackResponse:
    """
    回滚到指定版本 - 需求11验收标准6
    支持Git-like回滚操作，自动创建新版本记录
    """
    try:
        logger.info(
            f"回滚资源到版本{rollback_data.version_id}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "target_version_id": rollback_data.version_id,
                "action": "rollback_to_version",
            },
        )

        service = VersionService(db)
        result = await service.rollback_to_version(
            resource_type, resource_id, rollback_data, current_user.id
        )

        logger.info(
            "回滚操作成功",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "target_version_id": rollback_data.version_id,
                "new_version": result.new_version,
            },
        )

        return result

    except ResourceNotFoundError as e:
        logger.warning(
            f"资源或版本不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": rollback_data.version_id,
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
    except ValidationError as e:
        logger.warning(
            f"回滚数据验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"回滚操作失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="回滚操作失败") from e


@router.get(
    "/{resource_type}/{resource_id}/versions/{version_id}/compare",
    response_model=VersionComparisonResponse,
)
async def compare_versions(
    resource_type: str,
    resource_id: int,
    version_id: int,
    compare_with: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VersionComparisonResponse:
    """
    版本对比 - 需求11验收标准6
    支持版本间的详细对比，显示变更内容
    """
    try:
        logger.info(
            f"对比版本{version_id}和{compare_with}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "compare_with": compare_with,
                "action": "compare_versions",
            },
        )

        service = VersionService(db)
        comparison = await service.compare_versions(
            resource_type, resource_id, version_id, compare_with, current_user.id
        )

        logger.info(
            "版本对比完成",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "changes_count": len(comparison.changes),
            },
        )

        return comparison

    except ResourceNotFoundError as e:
        logger.warning(
            f"资源或版本不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "compare_with": compare_with,
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
            f"版本对比失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="版本对比失败") from e


@router.get(
    "/{resource_type}/{resource_id}/versions/{version_id}",
    response_model=ResourceVersionResponse,
)
async def get_version_detail(
    resource_type: str,
    resource_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceVersionResponse:
    """
    获取版本详情 - 需求11验收标准6
    返回指定版本的详细信息和内容
    """
    try:
        logger.info(
            "获取版本详情",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "action": "get_version_detail",
            },
        )

        service = VersionService(db)
        version = await service.get_version_detail(
            resource_type, resource_id, version_id, current_user.id
        )

        logger.info(
            "成功获取版本详情",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "version_number": version.version,
            },
        )

        return version

    except ResourceNotFoundError as e:
        logger.warning(
            f"版本不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
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
            f"获取版本详情失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="获取版本详情失败") from e


@router.delete("/{resource_type}/{resource_id}/versions/{version_id}")
async def delete_version(
    resource_type: str,
    resource_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    删除版本 - 需求11验收标准6
    删除指定版本（不能删除当前活跃版本）
    """
    try:
        logger.info(
            f"删除版本{version_id}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "action": "delete_version",
            },
        )

        service = VersionService(db)
        await service.delete_version(
            resource_type, resource_id, version_id, current_user.id
        )

        logger.info(
            "版本删除成功",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
            },
        )

        return {"success": True, "message": "版本已删除"}

    except ResourceNotFoundError as e:
        logger.warning(
            f"版本不存在: {e.message}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
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
    except ValidationError as e:
        logger.warning(
            f"删除验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"删除版本失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "version_id": version_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="删除版本失败") from e
