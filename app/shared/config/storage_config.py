"""MinIO对象存储配置模块

提供MinIO对象存储的配置管理，包括连接配置、存储桶配置、
安全配置和性能优化配置。
"""

import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, validator


@dataclass
class MinIOConnectionConfig:
    """MinIO连接配置"""

    endpoint: str
    access_key: str
    secret_key: str
    secure: bool = False
    region: str = "us-east-1"

    def __post_init__(self) -> None:
        """验证配置"""
        if not self.endpoint:
            raise ValueError("MinIO endpoint cannot be empty")
        if not self.access_key:
            raise ValueError("MinIO access key cannot be empty")
        if not self.secret_key:
            raise ValueError("MinIO secret key cannot be empty")


@dataclass
class BucketConfig:
    """存储桶配置"""

    name: str
    versioning: bool = True
    encryption: bool = True
    lifecycle_days: int = 365
    public_read: bool = False

    def __post_init__(self) -> None:
        """验证配置"""
        if not self.name:
            raise ValueError("Bucket name cannot be empty")
        if self.lifecycle_days < 1:
            raise ValueError("Lifecycle days must be positive")


class FileTypeConfig(BaseModel):
    """文件类型配置"""

    model_config = {"from_attributes": True}

    extension: str = Field(..., description="文件扩展名")
    max_size: int = Field(..., description="最大文件大小（字节）")
    mime_types: list[str] = Field(default_factory=list, description="允许的MIME类型")
    compression: bool = Field(default=False, description="是否压缩")
    encryption: bool = Field(default=True, description="是否加密")

    @validator("extension")
    def validate_extension(cls, v: str) -> str:
        """验证文件扩展名"""
        if not v.startswith("."):
            v = f".{v}"
        return v.lower()

    @validator("max_size")
    def validate_max_size(cls, v: int) -> int:
        """验证文件大小"""
        if v <= 0:
            raise ValueError("Max size must be positive")
        return v


class StorageConfig:
    """MinIO存储配置管理器"""

    def __init__(self) -> None:
        """初始化配置"""
        self.connection = self._load_connection_config()
        self.buckets = self._load_bucket_configs()
        self.file_types = self._load_file_type_configs()
        self.security = self._load_security_config()
        self.performance = self._load_performance_config()

    def _load_connection_config(self) -> MinIOConnectionConfig:
        """加载连接配置"""
        return MinIOConnectionConfig(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            region=os.getenv("MINIO_REGION", "us-east-1"),
        )

    def _load_bucket_configs(self) -> dict[str, BucketConfig]:
        """加载存储桶配置"""
        base_bucket = os.getenv("MINIO_BUCKET_NAME", "cet4-learning")

        return {
            "documents": BucketConfig(
                name=f"{base_bucket}-documents",
                versioning=True,
                encryption=True,
                lifecycle_days=365,
                public_read=False,
            ),
            "images": BucketConfig(
                name=f"{base_bucket}-images",
                versioning=False,
                encryption=False,
                lifecycle_days=180,
                public_read=True,
            ),
            "audio": BucketConfig(
                name=f"{base_bucket}-audio",
                versioning=True,
                encryption=True,
                lifecycle_days=365,
                public_read=False,
            ),
            "video": BucketConfig(
                name=f"{base_bucket}-video",
                versioning=True,
                encryption=True,
                lifecycle_days=365,
                public_read=False,
            ),
            "backups": BucketConfig(
                name=f"{base_bucket}-backups",
                versioning=True,
                encryption=True,
                lifecycle_days=730,  # 2年
                public_read=False,
            ),
            "temp": BucketConfig(
                name=f"{base_bucket}-temp",
                versioning=False,
                encryption=False,
                lifecycle_days=7,  # 7天
                public_read=False,
            ),
        }

    def _load_file_type_configs(self) -> dict[str, FileTypeConfig]:
        """加载文件类型配置"""
        return {
            # 文档类型
            ".pdf": FileTypeConfig(
                extension=".pdf",
                max_size=50 * 1024 * 1024,  # 50MB
                mime_types=["application/pdf"],
                compression=True,
                encryption=True,
            ),
            ".doc": FileTypeConfig(
                extension=".doc",
                max_size=20 * 1024 * 1024,  # 20MB
                mime_types=["application/msword"],
                compression=True,
                encryption=True,
            ),
            ".docx": FileTypeConfig(
                extension=".docx",
                max_size=20 * 1024 * 1024,  # 20MB
                mime_types=[
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ],
                compression=True,
                encryption=True,
            ),
            ".txt": FileTypeConfig(
                extension=".txt",
                max_size=5 * 1024 * 1024,  # 5MB
                mime_types=["text/plain"],
                compression=True,
                encryption=False,
            ),
            # 图片类型
            ".jpg": FileTypeConfig(
                extension=".jpg",
                max_size=10 * 1024 * 1024,  # 10MB
                mime_types=["image/jpeg"],
                compression=False,
                encryption=False,
            ),
            ".jpeg": FileTypeConfig(
                extension=".jpeg",
                max_size=10 * 1024 * 1024,  # 10MB
                mime_types=["image/jpeg"],
                compression=False,
                encryption=False,
            ),
            ".png": FileTypeConfig(
                extension=".png",
                max_size=10 * 1024 * 1024,  # 10MB
                mime_types=["image/png"],
                compression=False,
                encryption=False,
            ),
            ".gif": FileTypeConfig(
                extension=".gif",
                max_size=5 * 1024 * 1024,  # 5MB
                mime_types=["image/gif"],
                compression=False,
                encryption=False,
            ),
            # 音频类型
            ".mp3": FileTypeConfig(
                extension=".mp3",
                max_size=50 * 1024 * 1024,  # 50MB
                mime_types=["audio/mpeg"],
                compression=False,
                encryption=True,
            ),
            ".wav": FileTypeConfig(
                extension=".wav",
                max_size=100 * 1024 * 1024,  # 100MB
                mime_types=["audio/wav"],
                compression=True,
                encryption=True,
            ),
            # 视频类型
            ".mp4": FileTypeConfig(
                extension=".mp4",
                max_size=500 * 1024 * 1024,  # 500MB
                mime_types=["video/mp4"],
                compression=False,
                encryption=True,
            ),
            ".avi": FileTypeConfig(
                extension=".avi",
                max_size=500 * 1024 * 1024,  # 500MB
                mime_types=["video/x-msvideo"],
                compression=True,
                encryption=True,
            ),
        }

    def _load_security_config(self) -> dict[str, Any]:
        """加载安全配置"""
        return {
            "enable_encryption": os.getenv("MINIO_ENABLE_ENCRYPTION", "true").lower() == "true",
            "encryption_key": os.getenv("MINIO_ENCRYPTION_KEY", ""),
            "enable_access_log": os.getenv("MINIO_ENABLE_ACCESS_LOG", "true").lower() == "true",
            "max_concurrent_uploads": int(os.getenv("MINIO_MAX_CONCURRENT_UPLOADS", "10")),
            "upload_timeout": int(os.getenv("MINIO_UPLOAD_TIMEOUT", "300")),  # 5分钟
            "download_timeout": int(os.getenv("MINIO_DOWNLOAD_TIMEOUT", "300")),  # 5分钟
            "presigned_url_expiry": int(os.getenv("MINIO_PRESIGNED_URL_EXPIRY", "3600")),  # 1小时
        }

    def _load_performance_config(self) -> dict[str, Any]:
        """加载性能配置"""
        return {
            "connection_pool_size": int(os.getenv("MINIO_CONNECTION_POOL_SIZE", "10")),
            "retry_attempts": int(os.getenv("MINIO_RETRY_ATTEMPTS", "3")),
            "retry_delay": float(os.getenv("MINIO_RETRY_DELAY", "1.0")),
            "chunk_size": int(os.getenv("MINIO_CHUNK_SIZE", "8192")),  # 8KB
            "multipart_threshold": int(os.getenv("MINIO_MULTIPART_THRESHOLD", "64")),  # 64MB
            "multipart_chunksize": int(os.getenv("MINIO_MULTIPART_CHUNKSIZE", "16")),  # 16MB
            "enable_compression": os.getenv("MINIO_ENABLE_COMPRESSION", "true").lower() == "true",
        }

    def get_bucket_config(self, bucket_type: str) -> BucketConfig | None:
        """获取存储桶配置"""
        return self.buckets.get(bucket_type)

    def get_file_type_config(self, extension: str) -> FileTypeConfig | None:
        """获取文件类型配置"""
        if not extension.startswith("."):
            extension = f".{extension}"
        return self.file_types.get(extension.lower())

    def is_file_type_allowed(self, extension: str) -> bool:
        """检查文件类型是否允许"""
        return self.get_file_type_config(extension) is not None

    def get_max_file_size(self, extension: str) -> int:
        """获取文件最大大小"""
        config = self.get_file_type_config(extension)
        return config.max_size if config else 0

    def should_compress_file(self, extension: str) -> bool:
        """检查文件是否需要压缩"""
        config = self.get_file_type_config(extension)
        return config.compression if config else False

    def should_encrypt_file(self, extension: str) -> bool:
        """检查文件是否需要加密"""
        config = self.get_file_type_config(extension)
        return config.encryption if config else True


# 全局配置实例
storage_config = StorageConfig()
