"""资源评论和评分模型 - 用户对资源的评论和评分."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.resources.models.resource_models import ResourceLibrary
    from app.users.models.user_models import User


class ResourceComment(BaseModel):
    """资源评论模型 - 用户对资源的评论."""

    __tablename__ = "resource_comments"

    # 外键
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="资源ID",
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 评论内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="评论内容",
    )

    # 父评论ID（用于回复）
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("resource_comments.id", ondelete="CASCADE"),
        nullable=True,
        comment="父评论ID",
    )

    # 审计信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="更新时间",
    )

    # 关系 - 使用字符串引用避免循环导入
    resource: Mapped["ResourceLibrary"] = relationship(
        "ResourceLibrary",
        back_populates="comments",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="resource_comments",
    )
    parent: Mapped["ResourceComment | None"] = relationship(
        "ResourceComment",
        remote_side=[parent_id],
        back_populates="replies",
    )
    replies: Mapped[list["ResourceComment"]] = relationship(
        "ResourceComment",
        back_populates="parent",
    )

    def __repr__(self) -> str:
        return f"<ResourceComment(id={self.id}, resource_id={self.resource_id}, user_id={self.user_id})>"


class ResourceRating(BaseModel):
    """资源评分模型 - 用户对资源的评分."""

    __tablename__ = "resource_ratings"

    # 外键
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="资源ID",
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 评分信息
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="评分(1-5)",
    )

    # 审计信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="更新时间",
    )

    # 关系 - 使用字符串引用避免循环导入
    resource: Mapped["ResourceLibrary"] = relationship(
        "ResourceLibrary",
        back_populates="ratings",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="resource_ratings",
    )

    def __repr__(self) -> str:
        return f"<ResourceRating(id={self.id}, resource_id={self.resource_id}, rating={self.rating})>"


# 导出
__all__ = [
    "ResourceComment",
    "ResourceRating",
    "ResourceTag",
    "ResourceCategory",
    "ResourceQuota",
    "ResourceSyncLog",
]


class ResourceTag(BaseModel):
    """资源标签模型 - 用于分类和检索资源."""

    __tablename__ = "resource_tags"

    # 标签信息
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="标签名称",
    )
    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="标签颜色",
    )
    description: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="标签描述",
    )

    # 审计信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    def __repr__(self) -> str:
        return f"<ResourceTag(id={self.id}, name={self.name})>"


class ResourceCategory(BaseModel):
    """资源分类模型 - 用于树形分类资源."""

    __tablename__ = "resource_categories"

    # 分类信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="分类名称",
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("resource_categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="父分类ID",
    )
    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="分类层级",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序顺序",
    )
    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="分类图标",
    )
    description: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="分类描述",
    )

    # 审计信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="更新时间",
    )

    # 关系
    parent: Mapped["ResourceCategory | None"] = relationship(
        "ResourceCategory",
        remote_side=[parent_id],
        back_populates="children",
    )
    children: Mapped[list["ResourceCategory"]] = relationship(
        "ResourceCategory",
        back_populates="parent",
    )


class ResourceQuota(BaseModel):
    """资源配额模型 - 用户资源上传配额限制."""

    __tablename__ = "resource_quotas"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="用户ID",
    )

    # 配额设置
    max_storage_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1024,  # 默认1GB
        comment="最大存储空间(MB)",
    )
    max_file_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="最大文件数量",
    )
    max_file_size_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="最大单个文件大小(MB)",
    )

    # 配额周期
    quota_period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
        comment="配额周期: daily/weekly/monthly/unlimited",
    )

    # 使用统计
    used_storage_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="已使用存储空间(MB)",
    )
    used_file_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="已使用文件数量",
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="周期开始时间",
    )

    # 审计信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<ResourceQuota(user_id={self.user_id}, used={self.used_storage_mb}MB/{self.max_storage_mb}MB)>"


class ResourceSyncLog(BaseModel):
    """资源同步日志模型 - 记录资源同步操作."""

    __tablename__ = "resource_sync_logs"

    # 同步信息
    sync_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="同步类型: backup/restore/migration",
    )
    sync_direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="同步方向: upload/download",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="资源类型",
    )
    resource_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="资源ID",
    )

    # 文件信息
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="文件路径",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小(bytes)",
    )
    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="文件校验和",
    )

    # 同步状态
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="同步状态: pending/processing/completed/failed",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )

    # 节点信息
    source_node: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="源节点",
    )
    target_node: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="目标节点",
    )

    # 审计信息
    initiated_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="操作者ID",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<ResourceSyncLog(id={self.id}, type={self.sync_type}, status={self.status})>"

    def __repr__(self) -> str:
        return f"<ResourceCategory(id={self.id}, name={self.name}, level={self.level})>"
