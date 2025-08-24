"""数据备份工具类 - 提供数据备份的底层工具函数."""

import gzip
import hashlib
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class BackupEncryption:
    """备份加密工具."""

    def __init__(self, key: bytes | None = None) -> None:
        """初始化加密工具."""
        if key is None:
            key = Fernet.generate_key()
        self.fernet = Fernet(key)
        self.key = key

    def encrypt_file(self, file_path: str, encrypted_path: str) -> None:
        """加密文件."""
        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            encrypted_data = self.fernet.encrypt(file_data)

            with open(encrypted_path, "wb") as encrypted_file:
                encrypted_file.write(encrypted_data)

            logger.info(f"文件加密完成: {file_path} -> {encrypted_path}")
        except Exception as e:
            logger.error(f"文件加密失败: {e}")
            raise e

    def decrypt_file(self, encrypted_path: str, decrypted_path: str) -> None:
        """解密文件."""
        try:
            with open(encrypted_path, "rb") as encrypted_file:
                encrypted_data = encrypted_file.read()

            decrypted_data = self.fernet.decrypt(encrypted_data)

            with open(decrypted_path, "wb") as decrypted_file:
                decrypted_file.write(decrypted_data)

            logger.info(f"文件解密完成: {encrypted_path} -> {decrypted_path}")
        except Exception as e:
            logger.error(f"文件解密失败: {e}")
            raise e

    @classmethod
    def generate_key(cls) -> bytes:
        """生成新的加密密钥."""
        key: bytes = Fernet.generate_key()
        return key


class BackupCompression:
    """备份压缩工具."""

    @staticmethod
    def compress_file(
        source_path: str, compressed_path: str, compression_level: int = 6
    ) -> dict[str, Any]:
        """压缩文件."""
        try:
            original_size = os.path.getsize(source_path)

            with open(source_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb", compresslevel=compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            compressed_size = os.path.getsize(compressed_path)
            compression_ratio = compressed_size / original_size

            result = {
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "space_saved": original_size - compressed_size,
                "space_saved_percent": (1 - compression_ratio) * 100,
            }

            logger.info(
                f"文件压缩完成: {source_path} -> {compressed_path} "
                f"(压缩比: {compression_ratio:.2%})"
            )
            return result

        except Exception as e:
            logger.error(f"文件压缩失败: {e}")
            raise e

    @staticmethod
    def decompress_file(compressed_path: str, output_path: str) -> None:
        """解压文件."""
        try:
            with gzip.open(compressed_path, "rb") as f_in:
                with open(output_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"文件解压完成: {compressed_path} -> {output_path}")
        except Exception as e:
            logger.error(f"文件解压失败: {e}")
            raise e


class BackupValidator:
    """备份验证工具."""

    @staticmethod
    def calculate_checksum(file_path: str, algorithm: str = "sha256") -> str:
        """计算文件校验和."""
        try:
            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as file:
                for chunk in iter(lambda: file.read(8192), b""):
                    hash_obj.update(chunk)

            checksum = hash_obj.hexdigest()
            logger.info(f"文件校验和计算完成: {file_path} -> {checksum}")
            return checksum

        except Exception as e:
            logger.error(f"校验和计算失败: {e}")
            raise e

    @staticmethod
    def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
        """验证文件校验和."""
        try:
            actual_checksum = BackupValidator.calculate_checksum(file_path, algorithm)
            is_valid = actual_checksum == expected_checksum

            if is_valid:
                logger.info(f"文件校验和验证通过: {file_path}")
            else:
                logger.warning(
                    f"文件校验和验证失败: {file_path} "
                    f"(期望: {expected_checksum}, 实际: {actual_checksum})"
                )

            return is_valid
        except Exception as e:
            logger.error(f"校验和验证失败: {e}")
            return False

    @staticmethod
    def validate_backup_file(
        file_path: str, expected_checksum: str | None = None, min_size: int = 0
    ) -> dict[str, Any]:
        """验证备份文件完整性."""
        try:
            if not os.path.exists(file_path):
                return {"valid": False, "error": "备份文件不存在"}

            file_size = os.path.getsize(file_path)
            if file_size < min_size:
                return {
                    "valid": False,
                    "error": f"备份文件过小 (实际: {file_size}, 最小: {min_size})",
                }

            # 检查文件可读性
            try:
                with open(file_path, "rb") as f:
                    f.read(1024)  # 读取前1KB测试
            except Exception:
                return {"valid": False, "error": "备份文件无法读取"}

            # 校验和验证
            checksum_valid = True
            if expected_checksum:
                checksum_valid = BackupValidator.verify_checksum(file_path, expected_checksum)

            return {
                "valid": checksum_valid,
                "file_size": file_size,
                "checksum": BackupValidator.calculate_checksum(file_path),
            }

        except Exception as e:
            logger.error(f"备份文件验证失败: {e}")
            return {"valid": False, "error": str(e)}


class DatabaseDumper:
    """数据库备份导出工具."""

    def __init__(self, db_config: dict[str, Any]) -> None:
        """初始化数据库备份工具."""
        self.db_config = db_config

    def create_postgresql_dump(
        self,
        output_path: str,
        tables: list[str] | None = None,
        data_only: bool = False,
        schema_only: bool = False,
    ) -> dict[str, Any]:
        """创建PostgreSQL数据库备份."""
        try:
            pg_dump_cmd = [
                "pg_dump",
                f"--host={self.db_config.get('host', 'localhost')}",
                f"--port={self.db_config.get('port', 5432)}",
                f"--username={self.db_config.get('username')}",
                f"--dbname={self.db_config.get('database')}",
                "--no-password",  # 使用环境变量或.pgpass文件
                "--verbose",
                "--create",
                "--clean",
                f"--file={output_path}",
            ]

            # 添加额外选项
            if data_only:
                pg_dump_cmd.append("--data-only")
            elif schema_only:
                pg_dump_cmd.append("--schema-only")

            # 指定表
            if tables:
                for table in tables:
                    pg_dump_cmd.extend(["--table", table])

            # 设置环境变量
            env = os.environ.copy()
            if self.db_config.get("password"):
                env["PGPASSWORD"] = self.db_config["password"]

            # 执行备份命令
            start_time = datetime.now()
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
            )
            end_time = datetime.now()

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, pg_dump_cmd, result.stderr)

            file_size = os.path.getsize(output_path)
            duration = (end_time - start_time).total_seconds()

            logger.info(f"PostgreSQL备份完成: {output_path} ({file_size} bytes)")

            return {
                "success": True,
                "file_path": output_path,
                "file_size": file_size,
                "duration": duration,
                "tables_included": tables or ["all"],
                "backup_type": (
                    "data_only" if data_only else "schema_only" if schema_only else "full"
                ),
            }

        except subprocess.TimeoutExpired:
            logger.error("数据库备份超时")
            return {"success": False, "error": "备份操作超时"}
        except subprocess.CalledProcessError as e:
            logger.error(f"数据库备份失败: {e.stderr}")
            return {"success": False, "error": f"pg_dump失败: {e.stderr}"}
        except Exception as e:
            logger.error(f"数据库备份异常: {e}")
            return {"success": False, "error": str(e)}

    def restore_postgresql_dump(
        self, backup_path: str, target_database: str | None = None
    ) -> dict[str, Any]:
        """恢复PostgreSQL数据库备份."""
        try:
            database = target_database or self.db_config.get("database")

            psql_cmd = [
                "psql",
                f"--host={self.db_config.get('host', 'localhost')}",
                f"--port={self.db_config.get('port', 5432)}",
                f"--username={self.db_config.get('username')}",
                f"--dbname={database}",
                "--no-password",
                "--verbose",
                f"--file={backup_path}",
            ]

            # 设置环境变量
            env = os.environ.copy()
            if self.db_config.get("password"):
                env["PGPASSWORD"] = self.db_config["password"]

            # 执行恢复命令
            start_time = datetime.now()
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=7200,  # 2小时超时
            )
            end_time = datetime.now()

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, psql_cmd, result.stderr)

            duration = (end_time - start_time).total_seconds()

            logger.info(f"PostgreSQL恢复完成: {backup_path} -> {database}")

            return {
                "success": True,
                "backup_path": backup_path,
                "target_database": database,
                "duration": duration,
            }

        except subprocess.TimeoutExpired:
            logger.error("数据库恢复超时")
            return {"success": False, "error": "恢复操作超时"}
        except subprocess.CalledProcessError as e:
            logger.error(f"数据库恢复失败: {e.stderr}")
            return {"success": False, "error": f"psql失败: {e.stderr}"}
        except Exception as e:
            logger.error(f"数据库恢复异常: {e}")
            return {"success": False, "error": str(e)}


class BackupStorageManager:
    """备份存储管理器."""

    def __init__(self, base_path: str) -> None:
        """初始化存储管理器."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def organize_backup_path(self, backup_id: str, backup_type: str = "full") -> str:
        """组织备份文件路径."""
        now = datetime.now()
        year_month = now.strftime("%Y/%m")

        backup_dir = self.base_path / backup_type / year_month
        backup_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{backup_id}_{now.strftime('%Y%m%d_%H%M%S')}.sql"
        return str(backup_dir / filename)

    def cleanup_old_backups(
        self, retention_days: int = 30, max_backups: int | None = None
    ) -> dict[str, Any]:
        """清理过期备份."""
        try:
            deleted_files = []
            total_freed_space = 0
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)

            for backup_file in self.base_path.rglob("*.sql*"):
                if backup_file.stat().st_mtime < cutoff_time:
                    file_size = backup_file.stat().st_size
                    backup_file.unlink()
                    deleted_files.append(str(backup_file))
                    total_freed_space += file_size

            # 如果设置了最大备份数量限制
            if max_backups:
                remaining_files = list(self.base_path.rglob("*.sql*"))
                if len(remaining_files) > max_backups:
                    # 按修改时间排序，删除最旧的
                    remaining_files.sort(key=lambda x: x.stat().st_mtime)
                    files_to_delete = remaining_files[:-max_backups]

                    for file_to_delete in files_to_delete:
                        file_size = file_to_delete.stat().st_size
                        file_to_delete.unlink()
                        deleted_files.append(str(file_to_delete))
                        total_freed_space += file_size

            logger.info(
                f"备份清理完成: 删除 {len(deleted_files)} 个文件, "
                f"释放空间 {total_freed_space / 1024 / 1024:.2f} MB"
            )

            return {
                "deleted_files": deleted_files,
                "files_deleted_count": len(deleted_files),
                "space_freed": total_freed_space,
            }

        except Exception as e:
            logger.error(f"备份清理失败: {e}")
            return {
                "deleted_files": [],
                "files_deleted_count": 0,
                "space_freed": 0,
                "error": str(e),
            }

    def get_storage_statistics(self) -> dict[str, Any]:
        """获取存储统计信息."""
        try:
            total_files = 0
            total_size = 0
            backup_types = {}

            for backup_file in self.base_path.rglob("*.sql*"):
                total_files += 1
                file_size = backup_file.stat().st_size
                total_size += file_size

                # 按备份类型分类
                backup_type = backup_file.parent.parent.name
                if backup_type not in backup_types:
                    backup_types[backup_type] = {"count": 0, "size": 0}
                backup_types[backup_type]["count"] += 1
                backup_types[backup_type]["size"] += file_size

            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": total_size / 1024 / 1024,
                "backup_types": backup_types,
                "storage_path": str(self.base_path),
            }

        except Exception as e:
            logger.error(f"存储统计失败: {e}")
            return {
                "total_files": 0,
                "total_size": 0,
                "total_size_mb": 0,
                "backup_types": {},
                "error": str(e),
            }
