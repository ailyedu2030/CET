"""通知系统数据模型 - 需求16通知中枢数据层."""

from datetime import datetime, time
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.users.models.user_models import User


class Notification(BaseModel):
    """通知模型 - 系统内消息核心."""

    __tablename__ = "notifications"

    # 基础信息
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="接收用户ID",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="通知标题",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="通知内容",
    )

    # 通知分类
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="通知类型",
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
        comment="优先级: urgent/high/normal/low",
    )

    # 发送渠道
    channels: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="发送渠道列表",
    )

    # 状态信息
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否已读",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="阅读时间",
    )

    # 扩展信息
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="扩展元数据",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        lazy="select",
    )
    history: Mapped[list["NotificationHistory"]] = relationship(
        "NotificationHistory",
        back_populates="notification",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index("idx_notification_user_type", "user_id", "notification_type"),
        Index("idx_notification_user_read", "user_id", "is_read"),
        Index("idx_notification_priority_created", "priority", "created_at"),
    )

    def __repr__(self) -> str:
        """通知模型字符串表示."""
        return (
            f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.notification_type}')>"
        )


class NotificationTemplate(BaseModel):
    """通知模板模型 - 模板管理."""

    __tablename__ = "notification_templates"

    # 模板信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="模板名称",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="模板代码",
    )
    title_template: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="标题模板",
    )
    content_template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="内容模板",
    )

    # 模板分类
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="模板分类",
    )
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="对应通知类型",
    )

    # 渠道配置
    supported_channels: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="支持的发送渠道",
    )
    default_channels: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="默认发送渠道",
    )

    # 模板状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    # 变量定义
    variables: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="模板变量定义",
    )

    def __repr__(self) -> str:
        """模板模型字符串表示."""
        return (
            f"<NotificationTemplate(id={self.id}, code='{self.code}', category='{self.category}')>"
        )


class NotificationPreference(BaseModel):
    """用户通知偏好模型 - 个性化设置."""

    __tablename__ = "notification_preferences"

    # 用户关联
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="用户ID",
    )

    # 渠道偏好
    enable_in_app: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="启用系统内消息",
    )
    enable_email: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="启用邮件通知",
    )
    enable_sms: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="启用短信通知",
    )
    enable_push: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="启用推送通知",
    )

    # 免打扰设置
    quiet_hours_start: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
        comment="免打扰开始时间",
    )
    quiet_hours_end: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
        comment="免打扰结束时间",
    )

    # 通知类型偏好
    notification_types: Mapped[dict[str, bool]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="各类型通知开关",
    )

    # 频率控制
    max_daily_notifications: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="每日最大通知数量",
    )
    batch_similar_notifications: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否合并相似通知",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notification_preference",
        lazy="select",
    )

    def __repr__(self) -> str:
        """偏好模型字符串表示."""
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id})>"


class NotificationHistory(BaseModel):
    """通知发送历史模型 - 发送记录追踪."""

    __tablename__ = "notification_history"

    # 关联通知
    notification_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="通知ID",
    )

    # 发送信息
    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="发送时间",
    )
    send_results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="各渠道发送结果",
    )

    # 状态统计
    total_channels: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总发送渠道数",
    )
    success_channels: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="成功发送渠道数",
    )

    # 关系
    notification: Mapped["Notification"] = relationship(
        "Notification",
        back_populates="history",
        lazy="select",
    )

    # 索引
    __table_args__ = (Index("idx_history_notification_sent", "notification_id", "sent_at"),)

    def __repr__(self) -> str:
        """历史模型字符串表示."""
        return f"<NotificationHistory(id={self.id}, notification_id={self.notification_id})>"


class NotificationBatch(BaseModel):
    """批量通知模型 - 批量发送管理."""

    __tablename__ = "notification_batches"

    # 批次信息
    batch_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="批次名称",
    )
    batch_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="批次类型",
    )

    # 目标信息
    target_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="目标类型: user/class/role",
    )
    target_ids: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="目标ID列表",
    )

    # 发送统计
    total_recipients: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总接收人数",
    )
    sent_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="已发送数量",
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="发送失败数量",
    )

    # 状态信息
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="批次状态: pending/sending/completed/failed",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始发送时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间",
    )

    # 配置信息
    channels: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="发送渠道",
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("notification_templates.id"),
        nullable=True,
        comment="使用的模板ID",
    )

    # 关系
    template: Mapped[Optional["NotificationTemplate"]] = relationship(
        "NotificationTemplate",
        lazy="select",
    )

    def __repr__(self) -> str:
        """批次模型字符串表示."""
        return (
            f"<NotificationBatch(id={self.id}, name='{self.batch_name}', status='{self.status}')>"
        )
