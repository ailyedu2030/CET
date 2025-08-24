"""数据备份定时任务 - 需求9：数据备份与恢复."""

import logging
from datetime import datetime, timedelta
from typing import Any

from celery import shared_task

from app.analytics.schemas.analytics_schemas import BackupRequest
from app.backup.services.backup_service import BackupService
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="backup.daily_incremental")
def daily_incremental_backup(self: Any) -> dict[str, str | None]:
    """每日增量备份任务 - 需求9验收标准1."""
    try:
        logger.info("开始执行每日增量备份任务")

        # 创建增量备份请求
        backup_request = BackupRequest(
            backup_type="incremental",
            tables=[],  # 空列表表示所有表
            storage_location="local",
            compression=True,
            encryption=True,
            description="每日自动增量备份",
        )

        # 执行备份
        result = _execute_backup_task(backup_request)

        logger.info(f"每日增量备份完成: {result['backup_id']}")
        return {
            "status": "success",
            "backup_id": result["backup_id"],
            "backup_type": "incremental",
            "message": "每日增量备份成功",
        }

    except Exception as e:
        logger.error(f"每日增量备份失败: {str(e)}")
        return {
            "status": "failed",
            "backup_id": None,
            "backup_type": "incremental",
            "error": str(e),
        }


@shared_task(bind=True, name="backup.weekly_full")
def weekly_full_backup(self: Any) -> dict[str, str | None]:
    """每周全量备份任务 - 需求9验收标准1."""
    try:
        logger.info("开始执行每周全量备份任务")

        # 创建全量备份请求
        backup_request = BackupRequest(
            backup_type="full",
            tables=[],  # 空列表表示所有表
            storage_location="local",
            compression=True,
            encryption=True,
            description="每周自动全量备份",
        )

        # 执行备份
        result = _execute_backup_task(backup_request)

        logger.info(f"每周全量备份完成: {result['backup_id']}")
        return {
            "status": "success",
            "backup_id": result["backup_id"],
            "backup_type": "full",
            "message": "每周全量备份成功",
        }

    except Exception as e:
        logger.error(f"每周全量备份失败: {str(e)}")
        return {
            "status": "failed",
            "backup_id": None,
            "backup_type": "full",
            "error": str(e),
        }


@shared_task(bind=True, name="backup.cleanup_old_backups")
def cleanup_old_backups(self: Any, retention_days: int = 30) -> dict[str, str]:
    """清理过期备份任务 - 需求9验收标准3."""
    try:
        logger.info(f"开始清理 {retention_days} 天前的备份")

        async def _cleanup_backups() -> dict[str, int]:
            async with AsyncSessionLocal() as db:
                service = BackupService(db)

                # 计算过期时间
                cutoff_date = datetime.now() - timedelta(days=retention_days)

                # 获取过期备份列表
                expired_backups = await service.list_expired_backups(cutoff_date)

                deleted_count = 0
                failed_count = 0

                for backup in expired_backups:
                    try:
                        success = await service.delete_backup(backup.backup_id)
                        if success:
                            deleted_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"删除备份失败 {backup.backup_id}: {str(e)}")
                        failed_count += 1

                return {
                    "total_expired": len(expired_backups),
                    "deleted_count": deleted_count,
                    "failed_count": failed_count,
                }

        # 执行清理
        import asyncio

        result = asyncio.run(_cleanup_backups())

        logger.info(f"备份清理完成: 删除 {result['deleted_count']} 个备份")
        return {
            "status": "success",
            "deleted_count": str(result["deleted_count"]),
            "failed_count": str(result["failed_count"]),
            "message": f"成功清理 {result['deleted_count']} 个过期备份",
        }

    except Exception as e:
        logger.error(f"清理过期备份失败: {str(e)}")
        return {
            "status": "failed",
            "deleted_count": "0",
            "failed_count": "0",
            "error": str(e),
        }


@shared_task(bind=True, name="backup.validate_backups")
def validate_backup_integrity(self: Any) -> dict[str, str]:
    """验证备份完整性任务 - 需求9验收标准2."""
    try:
        logger.info("开始验证备份完整性")

        async def _validate_backups() -> dict[str, int]:
            async with AsyncSessionLocal() as db:
                service = BackupService(db)

                # 获取最近7天的备份
                recent_backups = await service.list_backups(limit=50)

                valid_count = 0
                invalid_count = 0

                for backup in recent_backups:
                    try:
                        validation_result = await service.validate_backup(backup.backup_id)
                        if validation_result.get("is_valid", False):
                            valid_count += 1
                        else:
                            invalid_count += 1
                            logger.warning(f"备份验证失败: {backup.backup_id}")
                    except Exception as e:
                        logger.error(f"验证备份失败 {backup.backup_id}: {str(e)}")
                        invalid_count += 1

                return {
                    "total_checked": len(recent_backups),
                    "valid_count": valid_count,
                    "invalid_count": invalid_count,
                }

        # 执行验证
        import asyncio

        result = asyncio.run(_validate_backups())

        logger.info(
            f"备份验证完成: {result['valid_count']} 个有效，{result['invalid_count']} 个无效"
        )
        return {
            "status": "success",
            "valid_count": str(result["valid_count"]),
            "invalid_count": str(result["invalid_count"]),
            "message": f"验证完成，{result['valid_count']} 个备份有效",
        }

    except Exception as e:
        logger.error(f"验证备份完整性失败: {str(e)}")
        return {
            "status": "failed",
            "valid_count": "0",
            "invalid_count": "0",
            "error": str(e),
        }


@shared_task(bind=True, name="backup.execute_scheduled")
def execute_scheduled_backups(self: Any) -> dict[str, str]:
    """执行计划备份任务 - 需求9验收标准1."""
    try:
        logger.info("开始执行计划备份任务")

        async def _execute_scheduled() -> dict[str, int]:
            async with AsyncSessionLocal() as db:
                service = BackupService(db)

                # 执行所有待执行的计划备份
                results = await service.run_scheduled_backups()

                successful_count = len([r for r in results if r["status"] == "success"])
                failed_count = len([r for r in results if r["status"] == "failed"])

                return {
                    "total_executed": len(results),
                    "successful_count": successful_count,
                    "failed_count": failed_count,
                }

        # 执行计划备份
        import asyncio

        result = asyncio.run(_execute_scheduled())

        logger.info(
            f"计划备份执行完成: {result['successful_count']} 成功，{result['failed_count']} 失败"
        )
        return {
            "status": "success",
            "successful_count": str(result["successful_count"]),
            "failed_count": str(result["failed_count"]),
            "message": f"执行完成，{result['successful_count']} 个备份成功",
        }

    except Exception as e:
        logger.error(f"执行计划备份失败: {str(e)}")
        return {
            "status": "failed",
            "successful_count": "0",
            "failed_count": "0",
            "error": str(e),
        }


def _execute_backup_task(backup_request: BackupRequest) -> dict[str, str]:
    """执行备份任务的辅助函数."""

    async def _create_backup() -> dict[str, str]:
        async with AsyncSessionLocal() as db:
            service = BackupService(db)
            backup_info = await service.create_backup(backup_request)
            return {
                "backup_id": backup_info.backup_id,
                "file_path": backup_info.file_path,
                "file_size": str(backup_info.file_size),
            }

    import asyncio

    return asyncio.run(_create_backup())
