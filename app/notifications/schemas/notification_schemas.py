"""通知系统数据模式 - 需求16通知中枢API接口定义."""

from datetime import datetime, time
from typing import Any

from pydantic import BaseModel, Field, validator


class NotificationBase(BaseModel):
    """通知基础模式."""

    title: str = Field(..., max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    notification_type: str = Field(..., max_length=50, description="通知类型")
    priority: str = Field(
        default="normal",
        pattern="^(urgent|high|normal|low)$",
        description="优先级",
    )
    metadata: dict[str, Any] | None = Field(default_factory=dict, description="扩展元数据")


class NotificationCreate(NotificationBase):
    """创建通知请求模式."""

    channels: list[str] | None = Field(
        default=None,
        description="发送渠道列表",
    )

    @validator("channels")
    def validate_channels(cls, v: list[str] | None) -> list[str] | None:
        """验证发送渠道."""
        if v is not None:
            valid_channels = {"in_app", "email", "sms", "push"}
            for channel in v:
                if channel not in valid_channels:
                    raise ValueError(f"无效的发送渠道: {channel}")
        return v


class NotificationResponse(NotificationBase):
    """通知响应模式."""

    id: int
    user_id: int
    channels: list[str]
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    send_results: dict[str, Any] | None = None

    class Config:
        """Pydantic配置."""

        from_attributes = True


class NotificationUpdate(BaseModel):
    """更新通知模式."""

    is_read: bool | None = None
    read_at: datetime | None = None


class NotificationBatchCreate(BaseModel):
    """批量通知创建模式."""

    notification_data: NotificationCreate
    target_type: str = Field(..., pattern="^(user|class|role)$", description="目标类型")
    target_ids: list[int] = Field(..., min_length=1, description="目标ID列表")
    channels: list[str] | None = Field(default=None, description="发送渠道")

    @validator("channels")
    def validate_channels(cls, v: list[str] | None) -> list[str] | None:
        """验证发送渠道."""
        if v is not None:
            valid_channels = {"in_app", "email", "sms", "push"}
            for channel in v:
                if channel not in valid_channels:
                    raise ValueError(f"无效的发送渠道: {channel}")
        return v


class NotificationListRequest(BaseModel):
    """通知列表请求模式."""

    user_id: int | None = None
    notification_type: str | None = None
    is_read: bool | None = None
    priority: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class NotificationListResponse(BaseModel):
    """通知列表响应模式."""

    notifications: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NotificationTemplateBase(BaseModel):
    """通知模板基础模式."""

    name: str = Field(..., max_length=100, description="模板名称")
    code: str = Field(..., max_length=50, description="模板代码")
    title_template: str = Field(..., max_length=200, description="标题模板")
    content_template: str = Field(..., description="内容模板")
    category: str = Field(..., max_length=50, description="模板分类")
    notification_type: str = Field(..., max_length=50, description="对应通知类型")
    supported_channels: list[str] = Field(default_factory=list, description="支持的发送渠道")
    default_channels: list[str] = Field(default_factory=list, description="默认发送渠道")
    variables: dict[str, Any] = Field(default_factory=dict, description="模板变量定义")


class NotificationTemplateCreate(NotificationTemplateBase):
    """创建通知模板模式."""

    is_active: bool = Field(default=True, description="是否激活")


class NotificationTemplateResponse(NotificationTemplateBase):
    """通知模板响应模式."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    class Config:
        """Pydantic配置."""

        from_attributes = True


class NotificationPreferenceBase(BaseModel):
    """通知偏好基础模式."""

    enable_in_app: bool = Field(default=True, description="启用系统内消息")
    enable_email: bool = Field(default=True, description="启用邮件通知")
    enable_sms: bool = Field(default=False, description="启用短信通知")
    enable_push: bool = Field(default=True, description="启用推送通知")
    quiet_hours_start: time | None = Field(default=None, description="免打扰开始时间")
    quiet_hours_end: time | None = Field(default=None, description="免打扰结束时间")
    notification_types: dict[str, bool] = Field(default_factory=dict, description="各类型通知开关")
    max_daily_notifications: int = Field(default=50, ge=1, le=200, description="每日最大通知数量")
    batch_similar_notifications: bool = Field(default=True, description="是否合并相似通知")


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """创建通知偏好模式."""

    user_id: int


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """更新通知偏好模式."""

    pass


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """通知偏好响应模式."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        """Pydantic配置."""

        from_attributes = True


class NotificationHistoryResponse(BaseModel):
    """通知历史响应模式."""

    id: int
    notification_id: int
    sent_at: datetime
    send_results: dict[str, Any]
    total_channels: int
    success_channels: int

    class Config:
        """Pydantic配置."""

        from_attributes = True


class NotificationBatchResponse(BaseModel):
    """批量通知响应模式."""

    id: int
    batch_name: str
    batch_type: str
    target_type: str
    target_ids: list[int]
    total_recipients: int
    sent_count: int
    failed_count: int
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    channels: list[str]
    created_at: datetime

    class Config:
        """Pydantic配置."""

        from_attributes = True


# 特定通知类型的模式
class TeachingPlanChangeNotification(BaseModel):
    """教学计划变更通知模式 - 需求16验收标准1."""

    plan_id: int
    change_type: str = Field(..., description="变更类型")
    affected_classes: list[int] = Field(..., description="受影响的班级")
    change_details: dict[str, Any] = Field(..., description="变更详情")
    notify_channels: list[str] = Field(default=["in_app", "email"], description="通知渠道")


class TrainingAnomalyAlert(BaseModel):
    """学生训练异常预警模式 - 需求16验收标准1."""

    student_id: int
    anomaly_type: str = Field(..., description="异常类型")
    anomaly_details: dict[str, Any] = Field(..., description="异常详情")
    teacher_ids: list[int] = Field(..., description="通知的教师ID列表")
    urgency_level: str = Field(
        default="high", pattern="^(urgent|high|normal)$", description="紧急程度"
    )


class ResourceAuditNotification(BaseModel):
    """资源审核状态通知模式 - 需求16验收标准1."""

    resource_id: int
    audit_status: str = Field(..., description="审核状态")
    resource_type: str = Field(..., description="资源类型")
    creator_id: int
    audit_comments: str | None = Field(default=None, description="审核意见")


# WebSocket消息模式
class WebSocketNotificationMessage(BaseModel):
    """WebSocket通知消息模式."""

    type: str = Field(..., description="消息类型")
    notification: NotificationResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketConnectionInfo(BaseModel):
    """WebSocket连接信息模式."""

    user_id: int
    connection_id: str
    connected_at: datetime
    last_heartbeat: datetime


# 统计和分析模式
class NotificationStats(BaseModel):
    """通知统计模式."""

    total_notifications: int
    unread_count: int
    read_count: int
    by_type: dict[str, int]
    by_priority: dict[str, int]
    by_channel: dict[str, int]
    recent_activity: list[dict[str, Any]]


class NotificationAnalytics(BaseModel):
    """通知分析模式."""

    delivery_rate: float = Field(..., description="送达率")
    read_rate: float = Field(..., description="阅读率")
    response_time: float = Field(..., description="平均响应时间")
    channel_effectiveness: dict[str, float] = Field(..., description="渠道有效性")
    peak_hours: list[int] = Field(..., description="高峰时段")
    user_engagement: dict[str, Any] = Field(..., description="用户参与度")
