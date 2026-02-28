"""管理员操作日志模型 - 用于审计追踪所有管理员操作."""

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


class OperationType(str, Enum):
    """操作类型枚举."""

    # 用户管理
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    USER_PASSWORD_RESET = "user_password_reset"

    # 课程管理
    COURSE_CREATE = "course_create"
    COURSE_UPDATE = "course_update"
    COURSE_DELETE = "course_delete"
    COURSE_APPROVE = "course_approve"
    COURSE_REJECT = "course_reject"

    # 班级管理
    CLASS_CREATE = "class_create"
    CLASS_UPDATE = "class_update"
    CLASS_DELETE = "class_delete"
    CLASS_BATCH_CREATE = "class_batch_create"

    # 课程分配
    COURSE_ASSIGN = "course_assign"
    COURSE_UNASSIGN = "course_unassign"
    COURSE_REASSIGN = "course_reassign"

    # 系统管理
    RULE_UPDATE = "rule_update"
    RULE_EXEMPTION_CREATE = "rule_exemption_create"

    # 备份恢复
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    BACKUP_VERIFY = "backup_verify"

    # 权限管理
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"


class OperationResult(str, Enum):
    """操作结果枚举."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class AdminOperationLog(BaseModel):
    """管理员操作日志模型 - 审计追踪."""

    __tablename__ = "admin_operation_logs"

    # 操作人信息
    admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="管理员ID",
    )
    admin_username: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="管理员用户名",
    )

    # 操作类型
    operation_type: Mapped[OperationType] = mapped_column(
        SQLEnum(OperationType),
        nullable=False,
        comment="操作类型",
    )
    operation_target: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="操作目标",
    )
    target_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="目标ID",
    )

    # 操作详情
    operation_details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="操作详情(JSON)",
    )
    operation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="操作原因",
    )

    # 请求信息
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IP地址",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="用户代理",
    )

    # 结果
    result: Mapped[OperationResult] = mapped_column(
        SQLEnum(OperationResult),
        nullable=False,
        comment="操作结果",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )

    # 时间戳
    operation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="操作时间",
    )

    # 关联
    admin: Mapped["User"] = relationship(
        "User",
        back_populates="admin_operation_logs",
    )

    def __repr__(self) -> str:
        return f"AdminOperationLog(id={self.id}, type={self.operation_type}, result={self.result})"
