"""业务指标和监控模型."""

from datetime import datetime

from pydantic import BaseModel, Field


class LearningMetrics(BaseModel):
    """学习指标模型."""

    student_id: int
    course_id: int
    training_type: str

    # 学习效果指标
    completion_rate: float = Field(..., ge=0.0, le=1.0, description="完成率")
    accuracy_rate: float = Field(..., ge=0.0, le=1.0, description="正确率")
    improvement_rate: float = Field(..., ge=-1.0, le=1.0, description="提升率")

    # 学习行为指标
    study_time: int = Field(..., ge=0, description="学习时长(分钟)")
    login_frequency: int = Field(..., ge=0, description="登录频次")
    exercise_count: int = Field(..., ge=0, description="练习次数")

    # 学习质量指标
    focus_score: float = Field(..., ge=0.0, le=100.0, description="专注度评分")
    persistence_score: float = Field(..., ge=0.0, le=100.0, description="坚持度评分")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TeachingMetrics(BaseModel):
    """教学指标模型."""

    teacher_id: int
    course_id: int
    class_id: int

    # 教学效果指标
    student_satisfaction: float = Field(..., ge=0.0, le=5.0, description="学生满意度")
    learning_effectiveness: float = Field(..., ge=0.0, le=1.0, description="学习有效性")
    engagement_rate: float = Field(..., ge=0.0, le=1.0, description="参与度")

    # 教学活动指标
    content_update_frequency: int = Field(..., ge=0, description="内容更新频次")
    feedback_response_time: int = Field(..., ge=0, description="反馈响应时间(小时)")
    interaction_count: int = Field(..., ge=0, description="师生互动次数")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIServiceMetrics(BaseModel):
    """AI服务指标模型."""

    service_type: str
    model_type: str

    # 性能指标
    response_time: float = Field(..., ge=0.0, description="响应时间(秒)")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="成功率")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="准确率")

    # 使用指标
    request_count: int = Field(..., ge=0, description="请求次数")
    token_usage: int = Field(..., ge=0, description="Token使用量")
    cost: float = Field(..., ge=0.0, description="成本(元)")

    # 质量指标
    user_satisfaction: float = Field(..., ge=0.0, le=5.0, description="用户满意度")
    content_quality: float = Field(..., ge=0.0, le=1.0, description="内容质量")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemMetrics(BaseModel):
    """系统指标模型."""

    # 性能指标
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU使用率")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="内存使用率")
    disk_usage: float = Field(..., ge=0.0, le=100.0, description="磁盘使用率")

    # 业务指标
    active_users: int = Field(..., ge=0, description="活跃用户数")
    concurrent_sessions: int = Field(..., ge=0, description="并发会话数")
    api_requests_per_minute: int = Field(..., ge=0, description="每分钟API请求数")

    # 可用性指标
    uptime: float = Field(..., ge=0.0, le=100.0, description="系统可用性")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="错误率")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BusinessAlert(BaseModel):
    """业务告警模型 - 教育系统专用告警机制."""

    alert_type: str = Field(..., description="告警类型")
    severity: str = Field(
        ...,
        pattern=r"^(low|medium|high|critical)$",
        description="严重程度",
    )
    title: str = Field(..., min_length=1, max_length=200, description="告警标题")
    message: str = Field(..., min_length=1, description="告警消息")

    # 告警上下文
    resource_type: str = Field(..., description="资源类型")
    resource_id: str | None = Field(None, description="资源ID")
    metric_name: str = Field(..., description="指标名称")
    current_value: float = Field(..., description="当前值")
    threshold_value: float = Field(..., description="阈值")

    # 教育系统特定字段
    affected_users: list[int] = Field(
        default_factory=list,
        description="受影响用户ID列表",
    )
    learning_impact: str = Field(
        default="none",
        pattern=r"^(none|low|medium|high|critical)$",
        description="对学习的影响程度",
    )
    auto_recovery_attempted: bool = Field(default=False, description="是否尝试自动恢复")

    # 告警状态
    status: str = Field(default="active", pattern=r"^(active|resolved|suppressed)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = Field(None)

    # 处理信息
    assigned_to: str | None = Field(None, description="分配给")
    resolution_notes: str | None = Field(None, description="解决说明")

    # 权限控制
    visibility_roles: list[str] = Field(
        default_factory=lambda: ["admin"],
        description="可见角色列表",
    )


class LearningPathMetrics(BaseModel):
    """学习路径指标模型 - 个性化学习路径跟踪."""

    student_id: int
    path_id: str

    # 路径完成情况
    total_steps: int = Field(..., ge=1, description="总步骤数")
    completed_steps: int = Field(..., ge=0, description="已完成步骤数")
    current_step: int = Field(..., ge=1, description="当前步骤")

    # 学习效果
    overall_score: float = Field(..., ge=0.0, le=100.0, description="总体得分")
    skill_improvements: dict[str, float] = Field(
        default_factory=dict,
        description="技能提升",
    )
    weak_areas: list[str] = Field(default_factory=list, description="薄弱环节")

    # 时间统计
    estimated_completion_time: int = Field(
        ...,
        ge=0,
        description="预计完成时间(小时)",
    )
    actual_time_spent: int = Field(..., ge=0, description="实际花费时间(分钟)")

    # 学习行为分析
    learning_pattern: str = Field(
        default="regular",
        pattern=r"^(intensive|regular|sporadic|irregular)$",
        description="学习模式",
    )
    difficulty_preference: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="难度偏好(0=简单,1=困难)",
    )

    # 智能推荐效果
    recommendation_accuracy: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="推荐准确率",
    )
    path_adjustment_count: int = Field(default=0, ge=0, description="路径调整次数")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AdaptiveLearningMetrics(BaseModel):
    """自适应学习指标模型 - 智能化个性化学习效果跟踪."""

    student_id: int
    algorithm_version: str

    # 适应性指标
    difficulty_adjustment_count: int = Field(..., ge=0, description="难度调整次数")
    content_recommendation_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="内容推荐准确率",
    )
    learning_style_match: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="学习风格匹配度",
    )

    # 个性化效果
    engagement_improvement: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="参与度提升",
    )
    learning_efficiency: float = Field(..., ge=0.0, le=10.0, description="学习效率")
    retention_rate: float = Field(..., ge=0.0, le=1.0, description="知识保持率")

    # 智能训练闭环指标
    feedback_loop_effectiveness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="反馈闭环有效性",
    )
    ai_human_teaching_balance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="AI与人工教学平衡度",
    )

    # 学习成果预测
    predicted_exam_score: float = Field(
        default=0.0,
        ge=0.0,
        le=710.0,
        description="预测四级考试分数",
    )
    confidence_interval: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="预测置信度",
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EducationalComplianceMetrics(BaseModel):
    """教育合规性指标模型 - 教育行业特殊要求监控."""

    # 未成年人保护指标
    minor_protection_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="未成年人保护评分",
    )
    daily_usage_limit_compliance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="每日使用限制合规率",
    )
    night_time_restriction_effectiveness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="夜间限制有效性",
    )

    # 数据隐私保护
    student_data_encryption_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="学生数据加密率",
    )
    privacy_policy_compliance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="隐私政策合规性",
    )
    data_access_audit_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="数据访问审计评分",
    )

    # 教育内容质量
    content_appropriateness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="内容适宜性评分",
    )
    educational_standard_compliance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="教育标准合规性",
    )
    ai_content_safety_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI内容安全率",
    )

    # 学习效果保障
    learning_outcome_guarantee: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="学习效果保障度",
    )
    teacher_supervision_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="教师监督覆盖率",
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IntelligentTrainingLoopMetrics(BaseModel):
    """智能训练闭环指标模型 - 核心业务闭环效果监控."""

    loop_id: str = Field(..., description="闭环标识")
    student_id: int
    teacher_id: int | None = Field(None, description="指导教师ID")

    # 闭环各阶段效果
    training_data_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="训练数据质量",
    )
    ai_analysis_accuracy: float = Field(..., ge=0.0, le=1.0, description="AI分析准确性")
    teacher_adjustment_timeliness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="教师调整及时性",
    )
    content_optimization_effectiveness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="内容优化有效性",
    )

    # 闭环完整性指标
    loop_completion_rate: float = Field(..., ge=0.0, le=1.0, description="闭环完成率")
    cycle_time_hours: int = Field(..., ge=0, description="闭环周期时间(小时)")
    intervention_count: int = Field(..., ge=0, description="人工干预次数")

    # 学习效果改进
    pre_loop_performance: float = Field(..., ge=0.0, le=100.0, description="闭环前表现")
    post_loop_performance: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="闭环后表现",
    )
    improvement_rate: float = Field(..., ge=-1.0, le=1.0, description="改进率")

    # 系统智能化程度
    automation_level: float = Field(..., ge=0.0, le=1.0, description="自动化程度")
    human_ai_collaboration_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="人机协作评分",
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow)
