"""文件存储服务模块

提供统一的文件存储接口，支持文件上传、下载、权限管理、
版本控制和备份策略。基于MinIO对象存储实现。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.config.storage_config import storage_config
from app.shared.services.cache_service import CacheService
from app.shared.utils.minio_client import minio_client

logger = logging.getLogger(__name__)


class FileMetadata(BaseModel):
    """文件元数据模型"""

    model_config = {"from_attributes": True}

    file_id: str = Field(..., description="文件ID")
    original_name: str = Field(..., description="原始文件名")
    object_name: str = Field(..., description="存储对象名")
    bucket_type: str = Field(..., description="存储桶类型")
    file_size: int = Field(..., description="文件大小")
    content_type: str = Field(..., description="内容类型")
    file_hash: str = Field(..., description="文件哈希")
    upload_time: datetime = Field(..., description="上传时间")
    uploaded_by: str | None = Field(None, description="上传用户")
    access_level: str = Field(default="private", description="访问级别")
    version: int = Field(default=1, description="版本号")
    is_deleted: bool = Field(default=False, description="是否已删除")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class FileUploadResult(BaseModel):
    """文件上传结果"""

    model_config = {"from_attributes": True}

    file_id: str = Field(..., description="文件ID")
    object_name: str = Field(..., description="存储对象名")
    download_url: str | None = Field(None, description="下载URL")
    file_size: int = Field(..., description="文件大小")
    content_type: str = Field(..., description="内容类型")
    upload_time: datetime = Field(..., description="上传时间")


class FilePermission(BaseModel):
    """文件权限模型"""

    model_config = {"from_attributes": True}

    file_id: str = Field(..., description="文件ID")
    user_id: str | None = Field(None, description="用户ID")
    role: str | None = Field(None, description="角色")
    permission: str = Field(..., description="权限类型")  # read, write, delete
    granted_by: str = Field(..., description="授权用户")
    granted_at: datetime = Field(..., description="授权时间")
    expires_at: datetime | None = Field(None, description="过期时间")


class FileStorageService:
    """文件存储服务"""

    def __init__(self, db: AsyncSession, cache_service: CacheService | None = None) -> None:
        """初始化文件存储服务"""
        self.db = db
        self.cache_service = cache_service
        self.minio_client = minio_client

        # 确保MinIO客户端已连接
        if not self.minio_client.is_connected:
            asyncio.create_task(self.minio_client.connect())

    async def upload_file(
        self,
        file: UploadFile,
        bucket_type: str = "documents",
        user_id: str | None = None,
        access_level: str = "private",
        metadata: dict[str, Any] | None = None,
    ) -> FileUploadResult:
        """上传文件"""
        try:
            # 生成文件ID
            file_id = str(uuid4())

            # 读取文件内容
            file_content = await file.read()
            await file.seek(0)  # 重置文件指针

            # 验证文件
            await self._validate_upload_file(file, file_content)

            # 生成对象名称
            object_name = self._generate_object_name(file.filename or "unknown", file_id)

            # 准备元数据
            upload_metadata = {
                "file_id": file_id,
                "original_filename": file.filename or "unknown",
                "uploaded_by": user_id or "anonymous",
                "access_level": access_level,
                "upload_time": datetime.now().isoformat(),
            }
            if metadata:
                upload_metadata.update(metadata)

            # 上传到MinIO
            await self.minio_client.upload_data(
                bucket_type=bucket_type,
                data=file_content,
                object_name=object_name,
                metadata=upload_metadata,
                content_type=file.content_type,
            )

            # 保存文件元数据到数据库
            file_metadata = FileMetadata(
                file_id=file_id,
                original_name=file.filename or "unknown",
                object_name=object_name,
                bucket_type=bucket_type,
                file_size=len(file_content),
                content_type=file.content_type or "application/octet-stream",
                file_hash=self._calculate_hash(file_content),
                upload_time=datetime.now(),
                uploaded_by=user_id,
                access_level=access_level,
                metadata=metadata or {},
            )

            await self._save_file_metadata(file_metadata)

            # 生成下载URL（如果需要）
            download_url = None
            if access_level == "public":
                download_url = await self.get_download_url(file_id)

            # 缓存文件信息
            if self.cache_service:
                await self.cache_service.set(
                    f"file_metadata:{file_id}",
                    file_metadata.model_dump(),
                    ttl=3600,  # 1小时
                )

            logger.info(f"Successfully uploaded file {file.filename} with ID {file_id}")

            return FileUploadResult(
                file_id=file_id,
                object_name=object_name,
                download_url=download_url,
                file_size=len(file_content),
                content_type=file.content_type or "application/octet-stream",
                upload_time=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {str(e)}")
            raise

    async def download_file(
        self, file_id: str, user_id: str | None = None
    ) -> tuple[bytes, FileMetadata]:
        """下载文件"""
        try:
            # 获取文件元数据
            file_metadata = await self.get_file_metadata(file_id)
            if not file_metadata:
                raise ValueError(f"File not found: {file_id}")

            # 检查权限
            if not await self._check_file_permission(file_id, user_id, "read"):
                raise PermissionError(f"No permission to read file: {file_id}")

            # 从MinIO下载文件
            file_data = await self.minio_client.download_data(
                bucket_type=file_metadata.bucket_type,
                object_name=file_metadata.object_name,
            )

            logger.info(f"Successfully downloaded file {file_id}")
            return file_data, file_metadata

        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {str(e)}")
            raise

    async def get_download_url(
        self, file_id: str, user_id: str | None = None, expires: timedelta | None = None
    ) -> str:
        """获取文件下载URL"""
        try:
            # 获取文件元数据
            file_metadata = await self.get_file_metadata(file_id)
            if not file_metadata:
                raise ValueError(f"File not found: {file_id}")

            # 检查权限
            if not await self._check_file_permission(file_id, user_id, "read"):
                raise PermissionError(f"No permission to read file: {file_id}")

            # 生成预签名URL
            url = await self.minio_client.get_presigned_url(
                bucket_type=file_metadata.bucket_type,
                object_name=file_metadata.object_name,
                expires=expires,
            )

            return url

        except Exception as e:
            logger.error(f"Failed to get download URL for file {file_id}: {str(e)}")
            raise

    async def delete_file(
        self, file_id: str, user_id: str | None = None, permanent: bool = False
    ) -> bool:
        """删除文件"""
        try:
            # 获取文件元数据
            file_metadata = await self.get_file_metadata(file_id)
            if not file_metadata:
                raise ValueError(f"File not found: {file_id}")

            # 检查权限
            if not await self._check_file_permission(file_id, user_id, "delete"):
                raise PermissionError(f"No permission to delete file: {file_id}")

            if permanent:
                # 永久删除：从MinIO删除文件
                await self.minio_client.delete_object(
                    bucket_type=file_metadata.bucket_type,
                    object_name=file_metadata.object_name,
                )

                # 从数据库删除元数据
                await self._delete_file_metadata(file_id)
            else:
                # 软删除：只标记为已删除
                await self._mark_file_deleted(file_id)

            # 清除缓存
            if self.cache_service:
                await self.cache_service.delete(f"file_metadata:{file_id}")

            logger.info(f"Successfully deleted file {file_id} (permanent: {permanent})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {str(e)}")
            raise

    async def list_files(
        self,
        user_id: str | None = None,
        bucket_type: str | None = None,
        access_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FileMetadata]:
        """列出文件"""
        try:
            # 从数据库查询文件列表
            files = await self._query_files(
                user_id=user_id,
                bucket_type=bucket_type,
                access_level=access_level,
                limit=limit,
                offset=offset,
            )

            return files

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise

    async def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """获取文件元数据"""
        try:
            # 先从缓存获取
            if self.cache_service:
                cached_data = await self.cache_service.get(f"file_metadata:{file_id}")
                if cached_data:
                    return FileMetadata(**cached_data)

            # 从数据库获取
            metadata = await self._get_file_metadata_from_db(file_id)

            # 缓存结果
            if metadata and self.cache_service:
                await self.cache_service.set(
                    f"file_metadata:{file_id}", metadata.model_dump(), ttl=3600
                )

            return metadata

        except Exception as e:
            logger.error(f"Failed to get file metadata {file_id}: {str(e)}")
            raise

    async def grant_file_permission(
        self,
        file_id: str,
        target_user_id: str | None,
        target_role: str | None,
        permission: str,
        granted_by: str,
        expires_at: datetime | None = None,
    ) -> bool:
        """授予文件权限"""
        try:
            permission_record = FilePermission(
                file_id=file_id,
                user_id=target_user_id,
                role=target_role,
                permission=permission,
                granted_by=granted_by,
                granted_at=datetime.now(),
                expires_at=expires_at,
            )

            await self._save_file_permission(permission_record)

            # 清除权限缓存
            if self.cache_service:
                cache_key = f"file_permission:{file_id}:{target_user_id or target_role}"
                await self.cache_service.delete(cache_key)

            logger.info(f"Granted {permission} permission on file {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to grant file permission: {str(e)}")
            raise

    async def revoke_file_permission(
        self,
        file_id: str,
        target_user_id: str | None,
        target_role: str | None,
        permission: str,
    ) -> bool:
        """撤销文件权限"""
        try:
            await self._delete_file_permission(file_id, target_user_id, target_role, permission)

            # 清除权限缓存
            if self.cache_service:
                cache_key = f"file_permission:{file_id}:{target_user_id or target_role}"
                await self.cache_service.delete(cache_key)

            logger.info(f"Revoked {permission} permission on file {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke file permission: {str(e)}")
            raise

    async def create_file_version(
        self, original_file_id: str, new_file: UploadFile, user_id: str | None = None
    ) -> FileUploadResult:
        """创建文件新版本"""
        try:
            # 获取原文件元数据
            original_metadata = await self.get_file_metadata(original_file_id)
            if not original_metadata:
                raise ValueError(f"Original file not found: {original_file_id}")

            # 检查权限
            if not await self._check_file_permission(original_file_id, user_id, "write"):
                raise PermissionError(f"No permission to update file: {original_file_id}")

            # 上传新版本
            result = await self.upload_file(
                file=new_file,
                bucket_type=original_metadata.bucket_type,
                user_id=user_id,
                access_level=original_metadata.access_level,
                metadata={
                    "original_file_id": original_file_id,
                    "version": original_metadata.version + 1,
                },
            )

            # 更新版本信息
            await self._update_file_version(result.file_id, original_metadata.version + 1)

            logger.info(f"Created new version of file {original_file_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to create file version: {str(e)}")
            raise

    async def _validate_upload_file(self, file: UploadFile, content: bytes) -> None:
        """验证上传文件"""
        if not file.filename:
            raise ValueError("Filename is required")

        file_extension = Path(file.filename).suffix.lower()

        # 检查文件类型
        if not storage_config.is_file_type_allowed(file_extension):
            raise ValueError(f"File type {file_extension} not allowed")

        # 检查文件大小
        max_size = storage_config.get_max_file_size(file_extension)
        if len(content) > max_size:
            raise ValueError(f"File size {len(content)} exceeds limit {max_size}")

    def _generate_object_name(self, filename: str, file_id: str) -> str:
        """生成对象名称"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(filename).suffix
        return f"{timestamp}_{file_id}{file_extension}"

    def _calculate_hash(self, content: bytes) -> str:
        """计算文件哈希"""
        import hashlib

        return hashlib.md5(content).hexdigest()

    async def _check_file_permission(
        self, file_id: str, user_id: str | None, permission: str
    ) -> bool:
        """检查文件权限"""
        # 获取文件元数据
        file_metadata = await self.get_file_metadata(file_id)
        if not file_metadata:
            return False

        # 公开文件的读权限
        if file_metadata.access_level == "public" and permission == "read":
            return True

        # 文件所有者拥有所有权限
        if file_metadata.uploaded_by == user_id:
            return True

        # 检查显式权限
        return await self._check_explicit_permission(file_id, user_id, permission)

    # 以下方法需要根据实际数据库模型实现
    async def _save_file_metadata(self, metadata: FileMetadata) -> None:
        """保存文件元数据到数据库"""
        # TODO: 实现数据库保存逻辑
        pass

    async def _get_file_metadata_from_db(self, file_id: str) -> FileMetadata | None:
        """从数据库获取文件元数据"""
        # TODO: 实现数据库查询逻辑
        return None

    async def _query_files(
        self,
        user_id: str | None = None,
        bucket_type: str | None = None,
        access_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FileMetadata]:
        """查询文件列表"""
        # TODO: 实现数据库查询逻辑
        return []

    async def _delete_file_metadata(self, file_id: str) -> None:
        """删除文件元数据"""
        # TODO: 实现数据库删除逻辑
        pass

    async def _mark_file_deleted(self, file_id: str) -> None:
        """标记文件为已删除"""
        # TODO: 实现数据库更新逻辑
        pass

    async def _save_file_permission(self, permission: FilePermission) -> None:
        """保存文件权限"""
        # TODO: 实现数据库保存逻辑
        pass

    async def _delete_file_permission(
        self, file_id: str, user_id: str | None, role: str | None, permission: str
    ) -> None:
        """删除文件权限"""
        # TODO: 实现数据库删除逻辑
        pass

    async def _check_explicit_permission(
        self, file_id: str, user_id: str | None, permission: str
    ) -> bool:
        """检查显式权限"""
        # TODO: 实现权限检查逻辑
        return False

    async def _update_file_version(self, file_id: str, version: int) -> None:
        """更新文件版本"""
        # TODO: 实现版本更新逻辑
        pass
