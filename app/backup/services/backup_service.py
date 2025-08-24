"""数据备份服务 - 提供完整的数据库备份功能."""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas.analytics_schemas import (
    BackupConfig,
    BackupInfo,
    BackupRequest,
    BackupStatistics,
)
from app.backup.utils.backup_utils import (
    BackupCompression,
    BackupEncryption,
    BackupStorageManager,
    BackupValidator,
    DatabaseDumper,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class BackupScheduler:
    """备份调度器."""

    def __init__(self) -> None:
        """初始化备份调度器."""
        self.scheduled_backups: dict[str, dict[str, Any]] = {}

    def parse_cron_expression(self, cron_expr: str) -> dict[str, Any]:
        """解析cron表达式."""
        # 简化的cron解析器，实际项目中应该使用专业的cron库
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("无效的cron表达式")

        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "weekday": parts[4],
        }

    def calculate_next_run_time(self, cron_expr: str) -> datetime:
        """计算下次执行时间."""
        # 简化实现，实际应该使用croniter库
        now = datetime.now()

        # 对于演示，假设每天的指定时间执行
        if cron_expr == "0 2 * * *":  # 每天凌晨2点
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        elif cron_expr == "0 */6 * * *":  # 每6小时
            next_hour = (now.hour // 6 + 1) * 6
            next_run = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
            if next_hour >= 24:
                next_run += timedelta(days=1)
            return next_run
        else:
            # 默认1小时后执行
            return now + timedelta(hours=1)

    def schedule_backup(self, config: BackupConfig) -> None:
        """安排备份任务."""
        if not config.enabled:
            return

        next_run = self.calculate_next_run_time(config.schedule)
        self.scheduled_backups[config.name] = {
            "config": config,
            "next_run": next_run,
            "last_run": None,
        }

        logger.info(f"备份任务已安排: {config.name} (下次执行: {next_run})")

    def get_pending_backups(self) -> list[BackupConfig]:
        """获取待执行的备份任务."""
        now = datetime.now()
        pending = []

        for _backup_name, backup_info in self.scheduled_backups.items():
            if backup_info["next_run"] <= now:
                pending.append(backup_info["config"])

        return pending

    def mark_backup_completed(self, backup_name: str) -> None:
        """标记备份任务完成."""
        if backup_name in self.scheduled_backups:
            backup_info = self.scheduled_backups[backup_name]
            backup_info["last_run"] = datetime.now()
            backup_info["next_run"] = self.calculate_next_run_time(backup_info["config"].schedule)


class BackupService:
    """主要备份服务类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化备份服务."""
        self.db = db_session
        self.storage_manager = BackupStorageManager(
            settings.BACKUP_STORAGE_PATH or "/var/backups/cet"
        )
        self.scheduler = BackupScheduler()
        self.db_dumper = DatabaseDumper(
            {
                "host": settings.DATABASE_HOST,
                "port": settings.DATABASE_PORT,
                "username": settings.DATABASE_USER,
                "password": settings.DATABASE_PASSWORD,
                "database": settings.DATABASE_NAME,
            }
        )

    async def create_backup(self, request: BackupRequest) -> BackupInfo:
        """创建数据库备份."""
        backup_id = str(uuid.uuid4())
        logger.info(f"开始创建备份: {backup_id} (类型: {request.backup_type})")

        try:
            # 生成备份文件路径
            backup_path = self.storage_manager.organize_backup_path(backup_id, request.backup_type)

            # 创建数据库备份
            dump_result = self.db_dumper.create_postgresql_dump(
                backup_path,
                tables=request.tables if request.tables else None,
                data_only=request.backup_type == "data_only",
                schema_only=request.backup_type == "schema_only",
            )

            if not dump_result["success"]:
                raise Exception(dump_result["error"])

            final_path = backup_path
            compression_ratio = None

            # 压缩处理
            if request.compression:
                compressed_path = f"{backup_path}.gz"
                compression_result = BackupCompression.compress_file(backup_path, compressed_path)
                compression_ratio = compression_result["compression_ratio"]

                # 删除原始文件，使用压缩文件
                os.unlink(backup_path)
                final_path = compressed_path

            # 加密处理
            if request.encryption:
                encryption = BackupEncryption()
                encrypted_path = f"{final_path}.enc"
                encryption.encrypt_file(final_path, encrypted_path)

                # 保存加密密钥（在实际项目中应该安全存储）
                key_path = f"{encrypted_path}.key"
                with open(key_path, "wb") as key_file:
                    key_file.write(encryption.key)

                # 删除未加密文件，使用加密文件
                os.unlink(final_path)
                final_path = encrypted_path

            # 计算文件校验和
            checksum = BackupValidator.calculate_checksum(final_path)
            file_size = os.path.getsize(final_path)

            # 创建备份信息
            backup_info = BackupInfo(
                backup_id=backup_id,
                backup_type=request.backup_type,
                file_path=final_path,
                file_size=file_size,
                checksum=checksum,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),  # 默认30天过期
                status="completed",
                tables_included=request.tables or ["all"],
                compression_ratio=compression_ratio,
                encryption_enabled=request.encryption,
            )

            # 保存备份元数据
            await self._save_backup_metadata(backup_info, request.description)

            logger.info(f"备份创建成功: {backup_id} (文件大小: {file_size / 1024 / 1024:.2f} MB)")
            return backup_info

        except Exception as e:
            logger.error(f"创建备份失败: {backup_id} - {e}")
            # 创建失败的备份信息
            backup_info = BackupInfo(
                backup_id=backup_id,
                backup_type=request.backup_type,
                file_path="",
                file_size=0,
                checksum="",
                created_at=datetime.now(),
                expires_at=None,
                status="failed",
                tables_included=request.tables or [],
                compression_ratio=None,
                encryption_enabled=request.encryption,
            )
            await self._save_backup_metadata(backup_info, str(e))
            raise e

    async def _save_backup_metadata(
        self, backup_info: BackupInfo, description: str | None = None
    ) -> None:
        """保存备份元数据."""
        try:
            metadata = {
                "backup_id": backup_info.backup_id,
                "backup_type": backup_info.backup_type,
                "file_path": backup_info.file_path,
                "file_size": backup_info.file_size,
                "checksum": backup_info.checksum,
                "created_at": backup_info.created_at.isoformat(),
                "expires_at": (
                    backup_info.expires_at.isoformat() if backup_info.expires_at else None
                ),
                "status": backup_info.status,
                "tables_included": backup_info.tables_included,
                "compression_ratio": backup_info.compression_ratio,
                "encryption_enabled": backup_info.encryption_enabled,
                "description": description,
            }

            # 保存到metadata文件
            metadata_dir = Path(settings.BACKUP_STORAGE_PATH or "/var/backups/cet") / "metadata"
            metadata_dir.mkdir(parents=True, exist_ok=True)

            metadata_file = metadata_dir / f"{backup_info.backup_id}.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存备份元数据失败: {e}")

    async def list_backups(
        self, backup_type: str | None = None, limit: int = 50
    ) -> list[BackupInfo]:
        """列出备份."""
        try:
            metadata_dir = Path(settings.BACKUP_STORAGE_PATH or "/var/backups/cet") / "metadata"
            if not metadata_dir.exists():
                return []

            backups = []
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)

                    if backup_type and metadata.get("backup_type") != backup_type:
                        continue

                    backup_info = BackupInfo(
                        backup_id=metadata["backup_id"],
                        backup_type=metadata["backup_type"],
                        file_path=metadata["file_path"],
                        file_size=metadata["file_size"],
                        checksum=metadata["checksum"],
                        created_at=datetime.fromisoformat(metadata["created_at"]),
                        expires_at=(
                            datetime.fromisoformat(metadata["expires_at"])
                            if metadata.get("expires_at")
                            else None
                        ),
                        status=metadata["status"],
                        tables_included=metadata["tables_included"],
                        compression_ratio=metadata.get("compression_ratio"),
                        encryption_enabled=metadata["encryption_enabled"],
                    )
                    backups.append(backup_info)

                except Exception as e:
                    logger.warning(f"读取备份元数据失败: {metadata_file} - {e}")
                    continue

            # 按创建时间排序，最新的在前
            backups.sort(key=lambda x: x.created_at, reverse=True)
            return backups[:limit]

        except Exception as e:
            logger.error(f"列出备份失败: {e}")
            return []

    async def get_backup_info(self, backup_id: str) -> BackupInfo | None:
        """获取备份信息."""
        try:
            metadata_file = (
                Path(settings.BACKUP_STORAGE_PATH or "/var/backups/cet")
                / "metadata"
                / f"{backup_id}.json"
            )

            if not metadata_file.exists():
                return None

            with open(metadata_file) as f:
                metadata = json.load(f)

            return BackupInfo(
                backup_id=metadata["backup_id"],
                backup_type=metadata["backup_type"],
                file_path=metadata["file_path"],
                file_size=metadata["file_size"],
                checksum=metadata["checksum"],
                created_at=datetime.fromisoformat(metadata["created_at"]),
                expires_at=(
                    datetime.fromisoformat(metadata["expires_at"])
                    if metadata.get("expires_at")
                    else None
                ),
                status=metadata["status"],
                tables_included=metadata["tables_included"],
                compression_ratio=metadata.get("compression_ratio"),
                encryption_enabled=metadata["encryption_enabled"],
            )

        except Exception as e:
            logger.error(f"获取备份信息失败: {backup_id} - {e}")
            return None

    async def delete_backup(self, backup_id: str) -> bool:
        """删除备份."""
        try:
            backup_info = await self.get_backup_info(backup_id)
            if not backup_info:
                logger.warning(f"备份不存在: {backup_id}")
                return False

            # 删除备份文件
            if backup_info.file_path and os.path.exists(backup_info.file_path):
                os.unlink(backup_info.file_path)

                # 删除相关的密钥文件（如果存在）
                key_file = f"{backup_info.file_path}.key"
                if os.path.exists(key_file):
                    os.unlink(key_file)

            # 删除元数据文件
            metadata_file = (
                Path(settings.BACKUP_STORAGE_PATH or "/var/backups/cet")
                / "metadata"
                / f"{backup_id}.json"
            )

            if metadata_file.exists():
                metadata_file.unlink()

            logger.info(f"备份删除成功: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"删除备份失败: {backup_id} - {e}")
            return False

    async def cleanup_expired_backups(self) -> dict[str, Any]:
        """清理过期备份."""
        try:
            backups = await self.list_backups(limit=1000)
            now = datetime.now()

            deleted_count = 0
            freed_space = 0
            errors = []

            for backup in backups:
                if backup.expires_at and backup.expires_at <= now:
                    try:
                        if await self.delete_backup(backup.backup_id):
                            deleted_count += 1
                            freed_space += backup.file_size
                    except Exception as e:
                        errors.append(f"删除备份失败 {backup.backup_id}: {e}")

            logger.info(
                f"过期备份清理完成: 删除 {deleted_count} 个备份, "
                f"释放空间 {freed_space / 1024 / 1024:.2f} MB"
            )

            return {
                "deleted_count": deleted_count,
                "freed_space": freed_space,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"清理过期备份失败: {e}")
            return {"deleted_count": 0, "freed_space": 0, "errors": [str(e)]}

    async def get_backup_statistics(self) -> BackupStatistics:
        """获取备份统计信息."""
        try:
            backups = await self.list_backups(limit=1000)
            storage_stats = self.storage_manager.get_storage_statistics()

            total_backups = len(backups)
            successful_backups = sum(1 for b in backups if b.status == "completed")
            failed_backups = sum(1 for b in backups if b.status == "failed")

            # 备份类型频率统计
            backup_frequency: dict[str, int] = {}
            for backup in backups:
                backup_frequency[backup.backup_type] = (
                    backup_frequency.get(backup.backup_type, 0) + 1
                )

            # 存储分布（简化版本）
            storage_distribution = {"local": total_backups}

            # 最后备份时间
            last_backup_time = backups[0].created_at if backups else None

            # 下次计划备份时间（从调度器获取）
            next_scheduled = None
            if self.scheduler.scheduled_backups:
                next_runs = [info["next_run"] for info in self.scheduler.scheduled_backups.values()]
                next_scheduled = min(next_runs) if next_runs else None

            return BackupStatistics(
                total_backups=total_backups,
                successful_backups=successful_backups,
                failed_backups=failed_backups,
                total_size=storage_stats["total_size"],
                last_backup_time=last_backup_time,
                next_scheduled_backup=next_scheduled,
                backup_frequency=backup_frequency,
                storage_distribution=storage_distribution,
            )

        except Exception as e:
            logger.error(f"获取备份统计失败: {e}")
            return BackupStatistics(
                total_backups=0,
                successful_backups=0,
                failed_backups=0,
                total_size=0,
                last_backup_time=None,
                next_scheduled_backup=None,
                backup_frequency={},
                storage_distribution={},
            )

    async def validate_backup(self, backup_id: str) -> dict[str, Any]:
        """验证备份文件完整性."""
        try:
            backup_info = await self.get_backup_info(backup_id)
            if not backup_info:
                return {"valid": False, "error": "备份不存在"}

            if not os.path.exists(backup_info.file_path):
                return {"valid": False, "error": "备份文件不存在"}

            # 验证文件完整性
            validation_result = BackupValidator.validate_backup_file(
                backup_info.file_path, backup_info.checksum
            )

            if validation_result["valid"]:
                logger.info(f"备份验证通过: {backup_id}")
            else:
                logger.warning(f"备份验证失败: {backup_id} - {validation_result.get('error')}")

            return validation_result

        except Exception as e:
            logger.error(f"备份验证异常: {backup_id} - {e}")
            return {"valid": False, "error": str(e)}

    async def create_incremental_backup(self, base_backup_id: str) -> BackupInfo:
        """创建增量备份（简化实现）."""
        # 在实际实现中，增量备份需要更复杂的逻辑
        # 这里提供一个基础框架
        logger.info(f"开始创建增量备份，基于备份: {base_backup_id}")

        # 对于PostgreSQL，可以使用WAL文件或者基于时间戳的增量备份
        # 这里简化为一个常规备份
        request = BackupRequest(
            backup_type="incremental",
            tables=[],
            storage_location="local",
            description=f"增量备份，基于 {base_backup_id}",
        )

        return await self.create_backup(request)

    def configure_backup_schedule(self, config: BackupConfig) -> None:
        """配置备份调度."""
        try:
            self.scheduler.schedule_backup(config)
            logger.info(f"备份调度配置成功: {config.name}")
        except Exception as e:
            logger.error(f"配置备份调度失败: {config.name} - {e}")
            raise e

    async def run_scheduled_backups(self) -> list[dict[str, Any]]:
        """执行计划的备份任务."""
        pending_backups = self.scheduler.get_pending_backups()
        results = []

        for config in pending_backups:
            try:
                logger.info(f"执行计划备份: {config.name}")

                request = BackupRequest(
                    backup_type=config.backup_type,
                    tables=config.tables_to_backup,
                    compression=config.compression_enabled,
                    encryption=config.encryption_enabled,
                    description=f"计划备份: {config.name}",
                )

                backup_info = await self.create_backup(request)
                self.scheduler.mark_backup_completed(config.name)

                results.append(
                    {
                        "config_name": config.name,
                        "backup_id": backup_info.backup_id,
                        "status": "success",
                        "file_size": backup_info.file_size,
                    }
                )

            except Exception as e:
                logger.error(f"计划备份执行失败: {config.name} - {e}")
                results.append(
                    {
                        "config_name": config.name,
                        "backup_id": None,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results

    async def list_expired_backups(self, cutoff_date: datetime) -> list[BackupInfo]:
        """获取过期备份列表 - 需求9验收标准3."""
        try:
            all_backups = await self.list_backups(limit=1000)
            expired_backups = [
                backup
                for backup in all_backups
                if backup.expires_at and backup.expires_at < cutoff_date
            ]
            return expired_backups

        except Exception as e:
            logger.error(f"获取过期备份列表失败: {e}")
            return []
