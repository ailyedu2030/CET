"""数据备份管理API端点 - 需求9：数据备份与恢复."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas.analytics_schemas import (
    BackupConfig,
    BackupInfo,
    BackupRequest,
    BackupStatistics,
)
from app.backup.services.backup_service import BackupService
from app.core.database import get_db
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_super_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["数据备份"])


# ===== 备份管理 - 需求9.1 =====


@router.post("/", response_model=BackupInfo, status_code=http_status.HTTP_201_CREATED)
async def create_backup(
    backup_request: BackupRequest,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BackupInfo:
    """创建数据备份 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        backup_info = await service.create_backup(backup_request)

        logger.info(f"超级管理员 {current_user.id} 创建备份: {backup_info.backup_id}")

        return backup_info

    except ValueError as e:
        logger.warning(f"创建备份失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"创建备份异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建备份失败",
        ) from None


@router.get("/", response_model=list[BackupInfo])
async def list_backups(
    backup_type: str | None = Query(None, description="备份类型筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[BackupInfo]:
    """获取备份列表 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        backups = await service.list_backups(backup_type=backup_type, limit=limit)

        logger.info(f"超级管理员 {current_user.id} 查看备份列表")

        return backups

    except Exception as e:
        logger.error(f"获取备份列表异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取备份列表失败",
        ) from None


@router.get("/{backup_id}", response_model=BackupInfo)
async def get_backup_info(
    backup_id: str,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BackupInfo:
    """获取备份详情 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        backup_info = await service.get_backup_info(backup_id)

        if not backup_info:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="备份不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 查看备份详情: {backup_id}")

        return backup_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取备份详情异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取备份详情失败",
        ) from None


@router.delete("/{backup_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除备份 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        success = await service.delete_backup(backup_id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="备份不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 删除备份: {backup_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除备份异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除备份失败",
        ) from None


# ===== 备份策略管理 - 需求9.1 =====


@router.post("/schedule", status_code=http_status.HTTP_201_CREATED)
async def configure_backup_schedule(
    backup_config: BackupConfig,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """配置备份调度 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        service.configure_backup_schedule(backup_config)

        logger.info(f"超级管理员 {current_user.id} 配置备份调度: {backup_config.name}")

        return {
            "success": True,
            "message": "备份调度配置成功",
            "config_name": backup_config.name,
            "schedule": backup_config.schedule,
            "backup_type": backup_config.backup_type,
        }

    except ValueError as e:
        logger.warning(f"配置备份调度失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"配置备份调度异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置备份调度失败",
        ) from None


@router.post("/schedule/execute")
async def execute_scheduled_backups(
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """执行计划备份 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        results = await service.run_scheduled_backups()

        logger.info(f"超级管理员 {current_user.id} 执行计划备份")

        return {
            "success": True,
            "message": "计划备份执行完成",
            "results": results,
            "total_backups": len(results),
            "successful_backups": len([r for r in results if r["status"] == "success"]),
            "failed_backups": len([r for r in results if r["status"] == "failed"]),
        }

    except Exception as e:
        logger.error(f"执行计划备份异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="执行计划备份失败",
        ) from None


# ===== 增量备份 - 需求9.1 =====


@router.post("/incremental", response_model=BackupInfo, status_code=http_status.HTTP_201_CREATED)
async def create_incremental_backup(
    base_backup_id: str = Query(..., description="基础备份ID"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BackupInfo:
    """创建增量备份 - 需求9验收标准1."""
    try:
        service = BackupService(db)
        backup_info = await service.create_incremental_backup(base_backup_id)

        logger.info(f"超级管理员 {current_user.id} 创建增量备份，基于: {base_backup_id}")

        return backup_info

    except ValueError as e:
        logger.warning(f"创建增量备份失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"创建增量备份异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建增量备份失败",
        ) from None


# ===== 备份统计 - 需求9.3 =====


@router.get("/statistics", response_model=BackupStatistics)
async def get_backup_statistics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BackupStatistics:
    """获取备份统计信息 - 需求9验收标准3."""
    try:
        service = BackupService(db)

        statistics = await service.get_backup_statistics()

        logger.info(f"超级管理员 {current_user.id} 查看备份统计")

        return statistics

    except Exception as e:
        logger.error(f"获取备份统计异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取备份统计失败",
        ) from None


@router.post("/validate/{backup_id}")
async def validate_backup(
    backup_id: str,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """验证备份完整性 - 需求9验收标准2."""
    try:
        service = BackupService(db)
        validation_result = await service.validate_backup(backup_id)

        logger.info(f"超级管理员 {current_user.id} 验证备份: {backup_id}")

        return validation_result

    except ValueError as e:
        logger.warning(f"验证备份失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"验证备份异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证备份失败",
        ) from None
