"""管理员功能相关的Pydantic模式定义."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, validator


class AdminDashboardResponse(BaseModel):
    """管理员仪表盘响应模式."""

    model_config = ConfigDict(from_attributes=True)

    # 用户统计
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    pending_applications: int = Field(..., description="待审核申请数")
    new_registrations_today: int = Field(..., description="今日新注册数")

    # 课程统计
    total_courses: int = Field(..., description="总课程数")
    active_courses: int = Field(..., description="活跃课程数")
    total_classes: int = Field(..., description="总班级数")
    active_classes: int = Field(..., description="活跃班级数")

    # 系统状态
    system_health: str = Field(..., description="系统健康状态")
    last_backup_time: datetime | None = Field(None, description="最后备份时间")
    storage_usage: float = Field(..., description="存储使用率")
    api_response_time: float = Field(..., description="API平均响应时间")

    # 最近活动
    recent_activities: list[dict[str, Any]] = Field(default_factory=list, description="最近活动")


class UserManagementStatsResponse(BaseModel):
    """用户管理统计响应模式."""

    model_config = ConfigDict(from_attributes=True)

    # 用户类型统计
    student_count: int = Field(..., description="学生数量")
    teacher_count: int = Field(..., description="教师数量")
    admin_count: int = Field(..., description="管理员数量")

    # 注册申请统计
    pending_student_applications: int = Field(..., description="待审核学生申请")
    pending_teacher_applications: int = Field(..., description="待审核教师申请")
    approved_applications_today: int = Field(..., description="今日审批通过数")
    rejected_applications_today: int = Field(..., description="今日审批驳回数")

    # 用户状态统计
    active_students: int = Field(..., description="活跃学生数")
    active_teachers: int = Field(..., description="活跃教师数")
    suspended_users: int = Field(..., description="停用用户数")

    # 最近注册趋势
    registration_trend: list[dict[str, Any]] = Field(default_factory=list, description="注册趋势")


class CourseManagementStatsResponse(BaseModel):
    """课程管理统计响应模式."""

    model_config = ConfigDict(from_attributes=True)

    # 课程状态统计
    preparing_courses: int = Field(..., description="筹备中课程数")
    reviewing_courses: int = Field(..., description="审核中课程数")
    active_courses: int = Field(..., description="已上线课程数")
    archived_courses: int = Field(..., description="已归档课程数")

    # 班级统计
    total_classes: int = Field(..., description="总班级数")
    classes_with_teacher: int = Field(..., description="已分配教师的班级数")
    classes_with_students: int = Field(..., description="有学生的班级数")
    average_class_size: float = Field(..., description="平均班级规模")

    # 资源统计
    total_classrooms: int = Field(..., description="总教室数")
    available_classrooms: int = Field(..., description="可用教室数")
    classroom_utilization: float = Field(..., description="教室利用率")


class ClassManagementRequest(BaseModel):
    """班级管理请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    code: str | None = Field(None, max_length=50, description="班级编号")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int | None = Field(None, description="教师ID")
    classroom_id: int | None = Field(None, description="教室ID")
    capacity: int = Field(default=30, ge=1, le=100, description="班级容量")
    min_students: int = Field(default=10, ge=1, description="最小学生数")
    max_students: int = Field(default=50, ge=1, description="最大学生数")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    schedule: dict[str, Any] | None = Field(None, description="课程表")

    @validator("max_students")
    def validate_max_students(cls, v: int | None, values: dict[str, Any]) -> int | None:
        """验证最大学生数必须大于等于最小学生数."""
        min_students = values.get("min_students", 0)
        if v is not None and v < min_students:
            raise ValueError("最大学生数不能小于最小学生数")
        return v


class ClassManagementResponse(BaseModel):
    """班级管理响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="班级ID")
    name: str = Field(..., description="班级名称")
    code: str | None = Field(None, description="班级编号")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int | None = Field(None, description="教师ID")
    classroom_id: int | None = Field(None, description="教室ID")
    capacity: int = Field(..., description="班级容量")
    min_students: int = Field(..., description="最小学生数")
    max_students: int = Field(..., description="最大学生数")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    status: str = Field(..., description="班级状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")


class CourseAssignmentRequest(BaseModel):
    """课程分配请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    teacher_id: int = Field(..., description="教师ID")
    notes: str | None = Field(None, max_length=500, description="分配备注")


class CourseAssignmentResponse(BaseModel):
    """课程分配响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分配记录ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    assigned_by: int = Field(..., description="分配人ID")
    assigned_at: datetime = Field(..., description="分配时间")
    status: str = Field(..., description="分配状态")
    notes: str | None = Field(None, description="分配备注")


class SystemMonitoringResponse(BaseModel):
    """系统监控响应模式."""

    model_config = ConfigDict(from_attributes=True)

    # 应用健康状态
    application_status: str = Field(..., description="应用状态")
    database_status: str = Field(..., description="数据库状态")
    redis_status: str = Field(..., description="Redis状态")
    ai_service_status: str = Field(..., description="AI服务状态")

    # 性能指标
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    network_io: dict[str, float] = Field(default_factory=dict, description="网络IO")

    # API统计
    api_call_count_today: int = Field(..., description="今日API调用次数")
    api_success_rate: float = Field(..., description="API成功率")
    average_response_time: float = Field(..., description="平均响应时间")
    error_count_today: int = Field(..., description="今日错误次数")

    # AI服务统计
    ai_api_calls_today: int = Field(..., description="今日AI API调用次数")
    ai_api_success_rate: float = Field(..., description="AI API成功率")
    ai_cost_today: float = Field(..., description="今日AI服务费用")
    ai_quota_remaining: dict[str, float] = Field(default_factory=dict, description="AI配额剩余")

    # 用户活动
    active_users_now: int = Field(..., description="当前活跃用户数")
    peak_concurrent_users: int = Field(..., description="峰值并发用户数")
    user_sessions_today: int = Field(..., description="今日用户会话数")

    # 告警信息
    active_alerts: list[dict[str, Any]] = Field(default_factory=list, description="活跃告警")
    recent_errors: list[dict[str, Any]] = Field(default_factory=list, description="最近错误")


class SystemRulesConfigRequest(BaseModel):
    """系统规则配置请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # 班级绑定规则
    class_teacher_binding: bool = Field(default=True, description="班级教师绑定规则")
    class_course_binding: bool = Field(default=True, description="班级课程绑定规则")
    allow_multiple_teachers: bool = Field(default=False, description="允许多教师")

    # 教室排课规则
    classroom_single_occupancy: bool = Field(default=True, description="教室单一占用规则")
    allow_classroom_sharing: bool = Field(default=False, description="允许教室共享")
    conflict_detection_enabled: bool = Field(default=True, description="启用冲突检测")

    # 权限规则
    strict_permission_check: bool = Field(default=True, description="严格权限检查")
    allow_cross_role_access: bool = Field(default=False, description="允许跨角色访问")

    # 数据规则
    data_retention_days: int = Field(default=1095, ge=30, description="数据保留天数")
    auto_backup_enabled: bool = Field(default=True, description="启用自动备份")
    backup_frequency_hours: int = Field(default=24, ge=1, description="备份频率(小时)")


class SystemRulesConfigResponse(BaseModel):
    """系统规则配置响应模式."""

    model_config = ConfigDict(from_attributes=True)

    # 班级绑定规则
    class_teacher_binding: bool = Field(..., description="班级教师绑定规则")
    class_course_binding: bool = Field(..., description="班级课程绑定规则")
    allow_multiple_teachers: bool = Field(..., description="允许多教师")

    # 教室排课规则
    classroom_single_occupancy: bool = Field(..., description="教室单一占用规则")
    allow_classroom_sharing: bool = Field(..., description="允许教室共享")
    conflict_detection_enabled: bool = Field(..., description="启用冲突检测")

    # 权限规则
    strict_permission_check: bool = Field(..., description="严格权限检查")
    allow_cross_role_access: bool = Field(..., description="允许跨角色访问")

    # 数据规则
    data_retention_days: int = Field(..., description="数据保留天数")
    auto_backup_enabled: bool = Field(..., description="启用自动备份")
    backup_frequency_hours: int = Field(..., description="备份频率(小时)")

    # 元数据
    last_updated_by: int | None = Field(None, description="最后更新人")
    last_updated_at: datetime | None = Field(None, description="最后更新时间")


class BackupRestoreRequest(BaseModel):
    """备份恢复请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    restore_modules: list[str] = Field(
        ...,
        description="要恢复的模块列表",
        min_length=1,
    )
    confirm_data_loss: bool = Field(
        default=False,
        description="确认数据丢失风险",
    )

    @validator("restore_modules")
    def validate_restore_modules(cls, v: list[str]) -> list[str]:
        """验证恢复模块列表."""
        valid_modules = [
            "users",
            "courses",
            "training",
            "resources",
            "system_config",
            "permissions",
        ]
        for module in v:
            if module not in valid_modules:
                raise ValueError(f"无效的恢复模块: {module}")
        return v


class BackupRestoreResponse(BaseModel):
    """备份恢复响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="备份ID")
    backup_type: str = Field(..., description="备份类型")
    status: str = Field(..., description="备份状态")
    file_path: str | None = Field(None, description="备份文件路径")
    file_size: int | None = Field(None, description="文件大小")
    description: str | None = Field(None, description="备份描述")
    created_by: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")


class RuleExemptionRequest(BaseModel):
    """规则豁免请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    rule_type: str = Field(..., description="规则类型")
    target_id: int = Field(..., description="目标ID")
    reason: str = Field(..., min_length=10, max_length=500, description="豁免原因")
    duration_days: int | None = Field(None, ge=1, le=365, description="豁免天数")
    auto_expire: bool = Field(default=True, description="自动过期")


class RuleExemptionResponse(BaseModel):
    """规则豁免响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="豁免记录ID")
    rule_type: str = Field(..., description="规则类型")
    target_id: int = Field(..., description="目标ID")
    reason: str = Field(..., description="豁免原因")
    duration_days: int | None = Field(None, description="豁免天数")
    expires_at: datetime | None = Field(None, description="过期时间")
    status: str = Field(..., description="豁免状态")
    created_by: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")


class AdminOperationLogResponse(BaseModel):
    """管理员操作日志响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="日志ID")
    admin_id: int = Field(..., description="管理员ID")
    operation_type: str = Field(..., description="操作类型")
    operation_target: str = Field(..., description="操作目标")
    operation_details: dict[str, Any] = Field(default_factory=dict, description="操作详情")
    ip_address: str | None = Field(None, description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    result: str = Field(..., description="操作结果")
    error_message: str | None = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="操作时间")


class AdminReportRequest(BaseModel):
    """管理员报告请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    report_type: str = Field(
        ...,
        pattern="^(user_management|course_management|system_performance|security_audit)$",
        description="报告类型",
    )
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    include_details: bool = Field(default=True, description="包含详细信息")
    format: str = Field(
        default="pdf",
        pattern="^(pdf|excel|json)$",
        description="报告格式",
    )

    @validator("end_date")
    def validate_date_range(cls, v: date | None, values: dict[str, Any]) -> date | None:
        """验证日期范围."""
        start_date = values.get("start_date")
        if start_date and v and v < start_date:
            raise ValueError("结束日期不能早于开始日期")
        return v


class AdminReportResponse(BaseModel):
    """管理员报告响应模式."""

    model_config = ConfigDict(from_attributes=True)

    report_id: str = Field(..., description="报告ID")
    report_type: str = Field(..., description="报告类型")
    status: str = Field(..., description="生成状态")
    file_path: str | None = Field(None, description="文件路径")
    download_url: str | None = Field(None, description="下载链接")
    file_size: int | None = Field(None, description="文件大小")
    generated_by: int = Field(..., description="生成人ID")
    generated_at: datetime = Field(..., description="生成时间")
    expires_at: datetime | None = Field(None, description="过期时间")
