"""MinIO客户端工具模块

提供MinIO对象存储的客户端封装，包括连接管理、存储桶操作、
文件上传下载、权限管理等功能。
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from minio import Minio
    from minio.lifecycleconfig import Expiration, LifecycleConfig, Rule
    from minio.sseconfig import SSEConfig, SseConfigurationRule
    from minio.versioningconfig import VersioningConfig

    MINIO_AVAILABLE = True
except ImportError:
    # 如果MinIO不可用，创建模拟类
    from typing import Any

    class Minio:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def list_buckets(self) -> list[Any]:
            return []

        def bucket_exists(self, bucket_name: str) -> bool:
            return True

        def make_bucket(self, bucket_name: str) -> None:
            pass

        def fput_object(self, *args: Any, **kwargs: Any) -> None:
            pass

        def put_object(self, *args: Any, **kwargs: Any) -> None:
            pass

        def fget_object(self, *args: Any, **kwargs: Any) -> None:
            pass

        def get_object(self, *args: Any, **kwargs: Any) -> Any:
            class MockResponse:
                def read(self) -> bytes:
                    return b"mock data"

                def close(self) -> None:
                    pass

                def release_conn(self) -> None:
                    pass

            return MockResponse()

        def remove_object(self, *args: Any, **kwargs: Any) -> None:
            pass

        def list_objects(self, *args: Any, **kwargs: Any) -> list[Any]:
            return []

        def presigned_get_object(self, *args: Any, **kwargs: Any) -> str:
            return "https://mock-url.com"

        def set_bucket_versioning(self, *args: Any, **kwargs: Any) -> None:
            pass

        def set_bucket_lifecycle(self, *args: Any, **kwargs: Any) -> None:
            pass

        def set_bucket_encryption(self, *args: Any, **kwargs: Any) -> None:
            pass

    class VersioningConfig:  # type: ignore[no-redef]
        def __init__(self, status: str) -> None:
            self.status = status

    class LifecycleConfig:  # type: ignore[no-redef]
        def __init__(self, rules: list[Any]) -> None:
            self.rules = rules

    class Rule:  # type: ignore[no-redef]
        def __init__(
            self, rule_id: str, rule_filter: Any, rule_status: str, expiration: Any
        ) -> None:
            pass

    class Expiration:  # type: ignore[no-redef]
        def __init__(self, days: int) -> None:
            pass

    class SSEConfig:  # type: ignore[no-redef]
        def __init__(self, rules: list[Any]) -> None:
            pass

    class SseConfigurationRule:  # type: ignore[no-redef]
        @staticmethod
        def new_sse_s3_rule() -> None:
            return None

    MINIO_AVAILABLE = False

from app.shared.config.storage_config import BucketConfig, storage_config

logger = logging.getLogger(__name__)


class MinIOClientError(Exception):
    """MinIO客户端异常"""

    pass


class MinIOClient:
    """MinIO客户端封装类"""

    def __init__(self) -> None:
        """初始化MinIO客户端"""
        self.config = storage_config
        self.client: Minio | None = None
        self._connected = False

    async def connect(self) -> bool:
        """连接到MinIO服务器"""
        try:
            connection_config = self.config.connection

            self.client = Minio(
                endpoint=connection_config.endpoint,
                access_key=connection_config.access_key,
                secret_key=connection_config.secret_key,
                secure=connection_config.secure,
                region=connection_config.region,
            )

            # 测试连接
            await self._test_connection()

            # 初始化存储桶
            await self._initialize_buckets()

            self._connected = True
            logger.info(f"Successfully connected to MinIO at {connection_config.endpoint}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MinIO: {str(e)}")
            self._connected = False
            return False

    async def _test_connection(self) -> None:
        """测试MinIO连接"""
        if not self.client:
            raise MinIOClientError("MinIO client not initialized")

        try:
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, list, self.client.list_buckets())
        except Exception as e:
            raise MinIOClientError(f"Connection test failed: {str(e)}") from e

    async def _initialize_buckets(self) -> None:
        """初始化存储桶"""
        if not self.client:
            raise MinIOClientError("MinIO client not initialized")

        loop = asyncio.get_event_loop()

        for _bucket_type, bucket_config in self.config.buckets.items():
            try:
                # 检查存储桶是否存在
                bucket_exists = await loop.run_in_executor(
                    None, self.client.bucket_exists, bucket_config.name
                )

                if not bucket_exists:
                    # 创建存储桶
                    await loop.run_in_executor(None, self.client.make_bucket, bucket_config.name)
                    logger.info(f"Created bucket: {bucket_config.name}")

                # 配置存储桶
                await self._configure_bucket(bucket_config)

            except Exception as e:
                logger.error(f"Failed to initialize bucket {bucket_config.name}: {str(e)}")
                raise MinIOClientError(f"Bucket initialization failed: {str(e)}") from e

    async def _configure_bucket(self, bucket_config: BucketConfig) -> None:
        """配置存储桶"""
        if not self.client:
            raise MinIOClientError("MinIO client not initialized")

        loop = asyncio.get_event_loop()

        try:
            # 配置版本控制
            if bucket_config.versioning:
                versioning_config = VersioningConfig(status="Enabled")
                await loop.run_in_executor(
                    None,
                    self.client.set_bucket_versioning,
                    bucket_config.name,
                    versioning_config,
                )

            # 配置生命周期
            if bucket_config.lifecycle_days > 0:
                lifecycle_config = LifecycleConfig(
                    [
                        Rule(
                            rule_id="expire_objects",
                            rule_filter=None,
                            rule_status="Enabled",
                            expiration=Expiration(days=bucket_config.lifecycle_days),
                        )
                    ]
                )
                await loop.run_in_executor(
                    None,
                    self.client.set_bucket_lifecycle,
                    bucket_config.name,
                    lifecycle_config,
                )

            # 配置加密
            if bucket_config.encryption and self.config.security["enable_encryption"]:
                sse_config = SSEConfig([SseConfigurationRule.new_sse_s3_rule()])
                await loop.run_in_executor(
                    None,
                    self.client.set_bucket_encryption,
                    bucket_config.name,
                    sse_config,
                )

        except Exception as e:
            logger.warning(f"Failed to configure bucket {bucket_config.name}: {str(e)}")

    async def upload_file(
        self,
        bucket_type: str,
        file_path: str | Path,
        object_name: str | None = None,
        metadata: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> str:
        """上传文件到MinIO"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        file_path = Path(file_path)
        if not file_path.exists():
            raise MinIOClientError(f"File not found: {file_path}")

        # 验证文件类型和大小
        await self._validate_file(file_path)

        # 生成对象名称
        if not object_name:
            object_name = self._generate_object_name(file_path)

        # 准备元数据
        if not metadata:
            metadata = {}
        metadata.update(
            {
                "upload_time": datetime.now().isoformat(),
                "original_filename": file_path.name,
                "file_size": str(file_path.stat().st_size),
                "file_hash": await self._calculate_file_hash(file_path),
            }
        )

        try:
            loop = asyncio.get_event_loop()

            # 上传文件
            await loop.run_in_executor(
                None,
                self.client.fput_object,
                bucket_config.name,
                object_name,
                str(file_path),
                content_type,
                metadata,
            )

            logger.info(f"Successfully uploaded {file_path} to {bucket_config.name}/{object_name}")
            return object_name

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {str(e)}")
            raise MinIOClientError(f"Upload failed: {str(e)}") from e

    async def upload_data(
        self,
        bucket_type: str,
        data: bytes,
        object_name: str,
        metadata: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> str:
        """上传数据到MinIO"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        # 验证数据大小
        file_extension = Path(object_name).suffix
        max_size = self.config.get_max_file_size(file_extension)
        if len(data) > max_size:
            raise MinIOClientError(f"Data size {len(data)} exceeds limit {max_size}")

        # 准备元数据
        if not metadata:
            metadata = {}
        metadata.update(
            {
                "upload_time": datetime.now().isoformat(),
                "data_size": str(len(data)),
                "data_hash": hashlib.md5(data).hexdigest(),
            }
        )

        try:
            from io import BytesIO

            loop = asyncio.get_event_loop()

            # 上传数据
            await loop.run_in_executor(
                None,
                self.client.put_object,
                bucket_config.name,
                object_name,
                BytesIO(data),
                len(data),
                content_type,
                metadata,
            )

            logger.info(f"Successfully uploaded data to {bucket_config.name}/{object_name}")
            return object_name

        except Exception as e:
            logger.error(f"Failed to upload data to {object_name}: {str(e)}")
            raise MinIOClientError(f"Upload failed: {str(e)}") from e

    async def download_file(
        self, bucket_type: str, object_name: str, file_path: str | Path
    ) -> bool:
        """从MinIO下载文件"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        try:
            loop = asyncio.get_event_loop()

            # 下载文件
            await loop.run_in_executor(
                None,
                self.client.fget_object,
                bucket_config.name,
                object_name,
                str(file_path),
            )

            logger.info(
                f"Successfully downloaded {bucket_config.name}/{object_name} to {file_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to download {object_name}: {str(e)}")
            raise MinIOClientError(f"Download failed: {str(e)}") from e

    async def download_data(self, bucket_type: str, object_name: str) -> bytes:
        """从MinIO下载数据"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        try:
            loop = asyncio.get_event_loop()

            # 下载数据
            response = await loop.run_in_executor(
                None, self.client.get_object, bucket_config.name, object_name
            )

            data: bytes = response.read()
            response.close()
            response.release_conn()

            logger.info(f"Successfully downloaded data from {bucket_config.name}/{object_name}")
            return data

        except Exception as e:
            logger.error(f"Failed to download data from {object_name}: {str(e)}")
            raise MinIOClientError(f"Download failed: {str(e)}") from e

    async def delete_object(self, bucket_type: str, object_name: str) -> bool:
        """删除对象"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        try:
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None, self.client.remove_object, bucket_config.name, object_name
            )

            logger.info(f"Successfully deleted {bucket_config.name}/{object_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete {object_name}: {str(e)}")
            raise MinIOClientError(f"Delete failed: {str(e)}") from e

    async def list_objects(
        self, bucket_type: str, prefix: str | None = None, recursive: bool = True
    ) -> list[dict[str, Any]]:
        """列出对象"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        try:
            loop = asyncio.get_event_loop()

            if not self.client:
                raise MinIOClientError("MinIO client not initialized")

            client = self.client  # 保存引用以避免类型检查问题
            objects = await loop.run_in_executor(
                None,
                lambda: list(
                    client.list_objects(bucket_config.name, prefix=prefix, recursive=recursive)
                ),
            )

            result = []
            for obj in objects:
                result.append(
                    {
                        "name": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                        "content_type": obj.content_type,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to list objects: {str(e)}")
            raise MinIOClientError(f"List failed: {str(e)}") from e

    async def get_presigned_url(
        self, bucket_type: str, object_name: str, expires: timedelta | None = None
    ) -> str:
        """生成预签名URL"""
        if not self._connected or not self.client:
            raise MinIOClientError("MinIO client not connected")

        bucket_config = self.config.get_bucket_config(bucket_type)
        if not bucket_config:
            raise MinIOClientError(f"Unknown bucket type: {bucket_type}")

        if not expires:
            expires = timedelta(seconds=self.config.security["presigned_url_expiry"])

        try:
            loop = asyncio.get_event_loop()

            if not self.client:
                raise MinIOClientError("MinIO client not initialized")

            url: str = await loop.run_in_executor(
                None,
                self.client.presigned_get_object,
                bucket_config.name,
                object_name,
                expires,
            )

            return url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {str(e)}")
            raise MinIOClientError(f"Presigned URL generation failed: {str(e)}") from e

    async def _validate_file(self, file_path: Path) -> None:
        """验证文件"""
        file_extension = file_path.suffix.lower()

        # 检查文件类型
        if not self.config.is_file_type_allowed(file_extension):
            raise MinIOClientError(f"File type {file_extension} not allowed")

        # 检查文件大小
        file_size = file_path.stat().st_size
        max_size = self.config.get_max_file_size(file_extension)
        if file_size > max_size:
            raise MinIOClientError(f"File size {file_size} exceeds limit {max_size}")

    def _generate_object_name(self, file_path: Path) -> str:
        """生成对象名称"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        return f"{timestamp}_{file_hash}_{file_path.name}"

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False
        self.client = None
        logger.info("Disconnected from MinIO")

    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected and self.client is not None


# 全局MinIO客户端实例
minio_client = MinIOClient()
