"""数据恢复管理API端点 - 需求9：数据备份与恢复."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas.analytics_schemas import RestoreInfo, RestoreRequest
from app.backup.services.restore_service import RestoreService
from app.core.database import get_db
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_super_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/restore", tags=["数据恢复"])


# ===== 数据恢复管理 - 需求9.2 =====


@router.post("/", response_model=RestoreInfo, status_code=http_status.HTTP_201_CREATED)
async def restore_from_backup(
    restore_request: RestoreRequest,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreInfo:
    """从备份恢复数据 - 需求9验收标准2."""
    try:
        service = RestoreService(db)
        restore_info = await service.restore_from_backup(restore_request)

        logger.info(
            f"超级管理员 {current_user.id} 开始数据恢复: "
            f"备份ID {restore_request.backup_id}, 类型 {restore_request.restore_type}"
        )

        return restore_info

    except ValueError as e:
        logger.warning(f"数据恢复失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"数据恢复异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据恢复失败",
        ) from None


@router.get("/", response_model=list[RestoreInfo])
async def list_restore_operations(
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    status: str | None = Query(None, description="恢复状态筛选"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[RestoreInfo]:
    """获取恢复操作列表 - 需求9验收标准2."""
    try:
        service = RestoreService(db)
        restore_operations = await service.list_restore_operations(limit=limit, status=status)

        logger.info(f"超级管理员 {current_user.id} 查看恢复操作列表")

        return restore_operations

    except Exception as e:
        logger.error(f"获取恢复操作列表异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取恢复操作列表失败",
        ) from None


@router.get("/{restore_id}", response_model=RestoreInfo)
async def get_restore_info(
    restore_id: str,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreInfo:
    """获取恢复操作详情 - 需求9验收标准2."""
    try:
        service = RestoreService(db)
        restore_info = await service.get_restore_info(restore_id)

        if not restore_info:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="恢复操作不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 查看恢复操作详情: {restore_id}")

        return restore_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取恢复操作详情异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取恢复操作详情失败",
        ) from None


# ===== 时间点恢复 - 需求9.2 =====


@router.post(
    "/point-in-time",
    response_model=RestoreInfo,
    status_code=http_status.HTTP_201_CREATED,
)
async def restore_to_point_in_time(
    backup_id: str = Query(..., description="备份ID"),
    target_time: datetime = Query(..., description="目标时间点"),
    confirm_overwrite: bool = Query(False, description="确认覆盖现有数据"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreInfo:
    """时间点恢复 - 需求9验收标准2."""
    try:
        restore_request = RestoreRequest(
            backup_id=backup_id,
            restore_type="point_in_time",
            confirm_overwrite=confirm_overwrite,
            validate_before_restore=True,
            target_time=target_time,
        )

        service = RestoreService(db)
        restore_info = await service.restore_from_backup(restore_request)

        logger.info(
            f"超级管理员 {current_user.id} 执行时间点恢复: "
            f"备份ID {backup_id}, 目标时间 {target_time}"
        )

        return restore_info

    except ValueError as e:
        logger.warning(f"时间点恢复失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"时间点恢复异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="时间点恢复失败",
        ) from None


# ===== 选择性恢复 - 需求9.2 =====


@router.post("/partial", response_model=RestoreInfo, status_code=http_status.HTTP_201_CREATED)
async def restore_partial_data(
    backup_id: str = Query(..., description="备份ID"),
    tables: list[str] = Query(..., description="要恢复的表列表"),
    confirm_overwrite: bool = Query(False, description="确认覆盖现有数据"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreInfo:
    """选择性恢复 - 需求9验收标准2."""
    try:
        restore_request = RestoreRequest(
            backup_id=backup_id,
            restore_type="partial",
            tables=tables,
            confirm_overwrite=confirm_overwrite,
            validate_before_restore=True,
            target_time=None,
        )

        service = RestoreService(db)
        restore_info = await service.restore_from_backup(restore_request)

        logger.info(f"超级管理员 {current_user.id} 执行选择性恢复: 备份ID {backup_id}, 表 {tables}")

        return restore_info

    except ValueError as e:
        logger.warning(f"选择性恢复失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"选择性恢复异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="选择性恢复失败",
        ) from None


# ===== 恢复预检查 - 需求9.2 =====


@router.post("/validate/{backup_id}")
async def validate_restore_prerequisites(
    backup_id: str,
    restore_type: str = Query(..., description="恢复类型"),
    tables: list[str] = Query([], description="要恢复的表列表"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """验证恢复前提条件 - 需求9验收标准2."""
    try:
        service = RestoreService(db)

        # 创建恢复请求用于验证
        restore_request = RestoreRequest(
            backup_id=backup_id,
            restore_type=restore_type,
            tables=tables,
            confirm_overwrite=False,
            validate_before_restore=True,
            target_time=None,
        )

        validation_result = await service.validate_restore_prerequisites(restore_request)

        logger.info(f"超级管理员 {current_user.id} 验证恢复前提条件: {backup_id}")

        return validation_result

    except ValueError as e:
        logger.warning(f"验证恢复前提条件失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"验证恢复前提条件异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证恢复前提条件失败",
        ) from None


# ===== 恢复操作管理 - 需求9.3 =====


@router.post("/{restore_id}/cancel")
async def cancel_restore_operation(
    restore_id: str,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """取消恢复操作 - 需求9验收标准3."""
    try:
        service = RestoreService(db)
        success = await service.cancel_restore_operation(restore_id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="恢复操作不存在或无法取消",
            )

        logger.info(f"超级管理员 {current_user.id} 取消恢复操作: {restore_id}")

        return {
            "success": True,
            "message": "恢复操作已取消",
            "restore_id": restore_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消恢复操作异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消恢复操作失败",
        ) from None


@router.get("/{restore_id}/progress")
async def get_restore_progress(
    restore_id: str,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取恢复进度 - 需求9验收标准3."""
    try:
        service = RestoreService(db)
        progress = await service.get_restore_progress(restore_id)

        if not progress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="恢复操作不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 查看恢复进度: {restore_id}")

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取恢复进度异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取恢复进度失败",
        ) from None


# ===== 恢复历史记录 - 需求9.3 =====


@router.get("/history/summary")
async def get_restore_history_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取恢复历史摘要 - 需求9验收标准3."""
    try:
        service = RestoreService(db)
        summary = await service.get_restore_history_summary(days)

        logger.info(f"超级管理员 {current_user.id} 查看恢复历史摘要")

        return summary

    except Exception as e:
        logger.error(f"获取恢复历史摘要异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取恢复历史摘要失败",
        ) from None
