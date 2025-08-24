"""权限审计相关的Pydantic模型 - 需求7：权限中枢管理."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ===== 审计日志相关Schema =====


class AuditLogResponse(BaseModel):
    """审计日志响应模型."""

    id: int = Field(..., description="日志ID")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    action_type: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str | None = Field(None, description="资源ID")
    details: dict[str, Any] | None = Field(None, description="操作详情")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    timestamp: datetime = Field(..., description="时间戳")
    success: bool = Field(..., description="是否成功")
    error_message: str | None = Field(None, description="错误信息")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# ===== 权限审计相关Schema =====


class PermissionAuditRequest(BaseModel):
    """权限审计查询请求模型."""

    user_id: int | None = Field(None, description="用户ID")
    permission_code: str | None = Field(None, description="权限代码")
    change_type: str | None = Field(None, description="变更类型", pattern="^(grant|revoke|modify)$")
    start_date: str | None = Field(None, description="开始日期")
    end_date: str | None = Field(None, description="结束日期")
    limit: int = Field(100, ge=1, le=1000, description="返回记录数")
    offset: int = Field(0, ge=0, description="偏移量")


class PermissionAuditResponse(BaseModel):
    """权限审计响应模型."""

    id: int = Field(..., description="审计记录ID")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    permission_code: str = Field(..., description="权限代码")
    permission_name: str = Field(..., description="权限名称")
    change_type: str = Field(..., description="变更类型")
    old_value: dict[str, Any] | None = Field(None, description="旧值")
    new_value: dict[str, Any] | None = Field(None, description="新值")
    changed_by: int = Field(..., description="变更人ID")
    changed_by_username: str = Field(..., description="变更人用户名")
    reason: str | None = Field(None, description="变更原因")
    timestamp: datetime = Field(..., description="变更时间")
    ip_address: str = Field(..., description="IP地址")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# ===== 安全事件相关Schema =====


class SecurityEventResponse(BaseModel):
    """安全事件响应模型."""

    id: int = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型")
    severity: str = Field(..., description="严重级别")
    user_id: int | None = Field(None, description="用户ID")
    username: str | None = Field(None, description="用户名")
    description: str = Field(..., description="事件描述")
    details: dict[str, Any] | None = Field(None, description="事件详情")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    timestamp: datetime = Field(..., description="事件时间")
    resolved: bool = Field(..., description="是否已解决")
    resolved_by: int | None = Field(None, description="解决人ID")
    resolved_at: datetime | None = Field(None, description="解决时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# ===== 用户活动相关Schema =====


class UserActivityResponse(BaseModel):
    """用户活动响应模型."""

    id: int = Field(..., description="活动ID")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    activity_type: str = Field(..., description="活动类型")
    description: str = Field(..., description="活动描述")
    details: dict[str, Any] | None = Field(None, description="活动详情")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    timestamp: datetime = Field(..., description="活动时间")
    session_id: str | None = Field(None, description="会话ID")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# ===== 权限统计相关Schema =====


class PermissionStatsResponse(BaseModel):
    """权限统计响应模型."""

    total_permissions: int = Field(..., description="总权限数")
    active_permissions: int = Field(..., description="激活权限数")
    total_roles: int = Field(..., description="总角色数")
    active_roles: int = Field(..., description="激活角色数")
    total_users_with_roles: int = Field(..., description="有角色的用户数")
    permission_usage: dict[str, int] = Field(..., description="权限使用统计")
    role_distribution: dict[str, int] = Field(..., description="角色分布统计")
    recent_changes: int = Field(..., description="最近变更数")


# ===== 审计报告相关Schema =====


class AuditReportRequest(BaseModel):
    """审计报告生成请求模型."""

    report_type: str = Field(
        ...,
        description="报告类型",
        pattern="^(permission_changes|security_events|user_activity|comprehensive)$",
    )
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    format: str = Field("json", description="报告格式", pattern="^(json|csv|pdf)$")
    include_details: bool = Field(True, description="是否包含详细信息")
    filters: dict[str, Any] | None = Field(None, description="筛选条件")


class AuditReportResponse(BaseModel):
    """审计报告响应模型."""

    report_id: str = Field(..., description="报告ID")
    report_type: str = Field(..., description="报告类型")
    format: str = Field(..., description="报告格式")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    generated_by: int = Field(..., description="生成人ID")
    generated_at: datetime = Field(..., description="生成时间")
    file_path: str | None = Field(None, description="文件路径")
    download_url: str | None = Field(None, description="下载链接")
    summary: dict[str, Any] | None = Field(None, description="报告摘要")
    status: str = Field(..., description="报告状态")


# ===== 异常检测相关Schema =====


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求模型."""

    detection_type: str = Field(
        ...,
        description="检测类型",
        pattern="^(login_anomaly|permission_anomaly|access_anomaly)$",
    )
    time_window_hours: int = Field(24, ge=1, le=168, description="时间窗口（小时）")
    sensitivity: str = Field("medium", description="敏感度", pattern="^(low|medium|high)$")
    user_id: int | None = Field(None, description="特定用户ID")


class AnomalyDetectionResponse(BaseModel):
    """异常检测响应模型."""

    detection_id: str = Field(..., description="检测ID")
    detection_type: str = Field(..., description="检测类型")
    anomalies_found: int = Field(..., description="发现的异常数量")
    anomalies: list[dict[str, Any]] = Field(..., description="异常详情列表")
    risk_score: float = Field(..., description="风险评分")
    recommendations: list[str] = Field(..., description="建议措施")
    detected_at: datetime = Field(..., description="检测时间")


# ===== 合规性检查相关Schema =====


class ComplianceCheckRequest(BaseModel):
    """合规性检查请求模型."""

    check_type: str = Field(..., description="检查类型", pattern="^(gdpr|sox|iso27001|custom)$")
    scope: str = Field(
        "all", description="检查范围", pattern="^(all|users|permissions|data_access)$"
    )
    include_recommendations: bool = Field(True, description="是否包含建议")


class ComplianceCheckResponse(BaseModel):
    """合规性检查响应模型."""

    check_id: str = Field(..., description="检查ID")
    check_type: str = Field(..., description="检查类型")
    scope: str = Field(..., description="检查范围")
    compliance_score: float = Field(..., description="合规评分")
    total_checks: int = Field(..., description="总检查项")
    passed_checks: int = Field(..., description="通过检查项")
    failed_checks: int = Field(..., description="失败检查项")
    issues: list[dict[str, Any]] = Field(..., description="问题列表")
    recommendations: list[str] = Field(..., description="建议措施")
    checked_at: datetime = Field(..., description="检查时间")


# ===== 实时监控相关Schema =====


class RealTimeMonitoringRequest(BaseModel):
    """实时监控请求模型."""

    monitor_type: str = Field(
        ...,
        description="监控类型",
        pattern="^(login_attempts|permission_usage|data_access|all)$",
    )
    alert_threshold: int = Field(10, ge=1, description="告警阈值")
    time_window_minutes: int = Field(5, ge=1, le=60, description="时间窗口（分钟）")


class RealTimeMonitoringResponse(BaseModel):
    """实时监控响应模型."""

    monitor_id: str = Field(..., description="监控ID")
    monitor_type: str = Field(..., description="监控类型")
    current_count: int = Field(..., description="当前计数")
    threshold: int = Field(..., description="阈值")
    status: str = Field(..., description="状态", pattern="^(normal|warning|critical)$")
    recent_events: list[dict[str, Any]] = Field(..., description="最近事件")
    last_updated: datetime = Field(..., description="最后更新时间")


# ===== 数据保留策略相关Schema =====


class DataRetentionPolicyRequest(BaseModel):
    """数据保留策略请求模型."""

    policy_type: str = Field(
        ...,
        description="策略类型",
        pattern="^(audit_logs|security_events|user_activity)$",
    )
    retention_days: int = Field(..., ge=30, le=2555, description="保留天数")
    auto_archive: bool = Field(True, description="是否自动归档")
    archive_location: str | None = Field(None, description="归档位置")


class DataRetentionPolicyResponse(BaseModel):
    """数据保留策略响应模型."""

    policy_id: str = Field(..., description="策略ID")
    policy_type: str = Field(..., description="策略类型")
    retention_days: int = Field(..., description="保留天数")
    auto_archive: bool = Field(..., description="是否自动归档")
    archive_location: str | None = Field(None, description="归档位置")
    created_by: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    last_executed: datetime | None = Field(None, description="最后执行时间")
    next_execution: datetime | None = Field(None, description="下次执行时间")
