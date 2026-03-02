"""文件存储数据模型."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel


class FileMetadataModel(BaseModel):
    """文件元数据模型."""

    __tablename__ = "file_metadata"

    file_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True, comment="文件ID"
    )
    original_name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="原始文件名"
    )
    object_name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="存储对象名"
    )
    bucket_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="存储桶类型"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="文件大小"
    )
    content_type: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="内容类型"
    )
    file_hash: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="文件哈希"
    )
    upload_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="上传时间"
    )
    uploaded_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="上传用户"
    )
    access_level: Mapped[str] = mapped_column(
        String(50), default="private", nullable=False, comment="访问级别"
    )
    version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="版本号"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否已删除"
    )
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="扩展元数据"
    )

    # 关系
    permissions: Mapped[list["FilePermissionModel"]] = relationship(
        "FilePermissionModel", back_populates="file", cascade="all, delete-orphan"
    )


class FilePermissionModel(BaseModel):
    """文件权限模型."""

    __tablename__ = "file_permissions"

    file_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("file_metadata.file_id"), nullable=False, comment="文件ID"
    )
    user_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="用户ID"
    )
    role: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="角色"
    )
    permission: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="权限类型"
    )
    granted_by: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="授权用户"
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="授权时间"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间"
    )

    # 关系
    file: Mapped[FileMetadataModel] = relationship(
        "FileMetadataModel", back_populates="permissions"
    )
