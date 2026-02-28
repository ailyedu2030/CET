"""权限管理相关的SQLAlchemy模型定义."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.users.models.user_models import User


# 多对多关联表：用户-角色
user_role_association = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
    UniqueConstraint("user_id", "role_id", name="uq_user_role"),
)

# 多对多关联表：角色-权限
role_permission_association = Table(
    "role_permissions",
    BaseModel.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE")),
    UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
)


class Permission(BaseModel):
    """权限模型 - 精确到操作级别的权限控制."""

    __tablename__ = "permissions"

    # 权限基础信息
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="权限名称",
    )
    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="权限代码",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="权限描述",
    )

    # 权限分类
    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="所属模块",
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="操作类型",
    )
    resource: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="资源类型",
    )

    # 权限状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    # 关系
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=role_permission_association,
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        """权限模型字符串表示."""
        return f"<Permission(id={self.id}, code='{self.code}', module='{self.module}')>"


class Role(BaseModel):
    """角色模型 - RBAC角色定义."""

    __tablename__ = "roles"

    # 角色基础信息
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="角色名称",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="角色代码",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="角色描述",
    )

    # 角色分级
    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="角色等级（数字越大权限越高）",
    )

    # 角色状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否系统内置角色",
    )

    # 关系
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_role_association,
        back_populates="roles",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permission_association,
        back_populates="roles",
    )

    def __repr__(self) -> str:
        """角色模型字符串表示."""
        return f"<Role(id={self.id}, code='{self.code}', level={self.level})>"


class LoginSession(BaseModel):
    """登录会话模型 - 追踪用户登录状态."""

    __tablename__ = "login_sessions"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 会话信息
    session_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="会话令牌",
    )
    refresh_token: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="刷新令牌",
    )

    # 登录信息
    login_ip: Mapped[str | None] = mapped_column(
        String(45),  # IPv6最大长度
        nullable=True,
        comment="登录IP地址",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="用户代理字符串",
    )
    device_info: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="设备信息",
    )

    # 会话状态
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="过期时间",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )
    last_activity: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后活跃时间",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="login_sessions",
    )

    def __repr__(self) -> str:
        """登录会话模型字符串表示."""
        return f"<LoginSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class LoginAttempt(BaseModel):
    """登录尝试模型 - 安全审计和暴力破解防护."""

    __tablename__ = "login_attempts"

    # 登录尝试信息
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="尝试登录的用户名",
    )
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
        comment="来源IP地址",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="用户代理字符串",
    )

    # 尝试结果
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="是否成功",
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="失败原因",
    )

    # 额外信息
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="尝试时间",
    )

    def __repr__(self) -> str:
        """登录尝试模型字符串表示."""
        return f"<LoginAttempt(id={self.id}, username='{self.username}', success={self.success})>"
