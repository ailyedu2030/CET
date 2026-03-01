"""备份记录数据库模型 - 用于追踪所有备份操作."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.users.models import User


class BackupType(str, Enum):
    """备份类型枚举."""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(str, Enum):
    """备份状态枚举."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    RESTORED = "restored"


class BackupRecord(BaseModel):
    """备份记录模型 - 追踪所有备份操作."""

    __tablename__ = "backup_records"

    # 备份基本信息
    backup_type: Mapped[BackupType] = mapped_column(
        SQLEnum(BackupType),
        nullable=False,
        comment="备份类型",
    )
    status: Mapped[BackupStatus] = mapped_column(
        SQLEnum(BackupStatus),
        nullable=False,
        default=BackupStatus.PENDING,
        comment="备份状态",
    )

    # 文件信息
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="备份文件路径",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小(字节)",
    )
    file_checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="文件校验和",
    )
    compression: Mapped[str] = mapped_column(
        String(20),
        default="gzip",
        comment="压缩算法",
    )
    encryption: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="加密算法",
    )

    # 备份范围
    modules: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        comment="备份的模块列表",
    )

    # 描述
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备份描述",
    )

    # 验证信息
    is_valid: Mapped[bool | None] = mapped_column(
        nullable=True,
        comment="备份是否有效",
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="验证时间",
    )
    verification_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="验证详情",
    )

    # 恢复信息
    restored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="恢复时间",
    )
    restored_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="恢复操作人",
    )
    restore_modules: Mapped[str | None] = mapped_column(
        JSON,
        nullable=True,
        comment="恢复的模块",
    )

    # 时间信息
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

    # 操作人
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID",
    )

    # 关联
    creator: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_backups",
    )
    restorer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[restored_by],
        back_populates="restored_backups",
    )

    def __repr__(self) -> str:
        return (
            f"BackupRecord(id={self.id}, type={self.backup_type}, status={self.status})"
        )
