"""学习计划相关Schema定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.shared.models.enums import TrainingType

# ==================== 学习计划相关Schema ====================


class LearningPlanConfigRequest(BaseModel):
    """学习计划配置请求."""

    duration_weeks: int = Field(12, ge=1, le=52, description="计划周期（周）")
    daily_study_time_minutes: int = Field(60, ge=15, le=240, description="每日学习时间（分钟）")
    weekly_sessions: int = Field(5, ge=1, le=7, description="每周学习次数")
    focus_areas: list[TrainingType] = Field(default_factory=list, description="重点关注领域")
    difficulty_preference: str = Field("adaptive", description="难度偏好")
    learning_goals: list[str] = Field(default_factory=list, description="学习目标")


class LearningPlanResponse(BaseModel):
    """学习计划响应."""

    plan_id: int = Field(..., description="计划ID")
    student_id: int = Field(..., description="学生ID")
    plan_data: dict[str, Any] = Field(..., description="计划数据")
    generated_at: datetime = Field(..., description="生成时间")
    status: str = Field(..., description="计划状态")


class WeeklyPlanResponse(BaseModel):
    """周计划响应."""

    week_number: int = Field(..., description="周数")
    week_difficulty: float = Field(..., description="本周难度")
    training_types: dict[str, float] = Field(..., description="训练类型分配")
    goals: dict[str, Any] = Field(..., description="本周目标")
    time_allocation: dict[str, int] = Field(..., description="时间分配")
    estimated_questions: dict[str, int] = Field(..., description="预估题目数")


class DailyTaskResponse(BaseModel):
    """每日任务响应."""

    day: int = Field(..., description="日期")
    week: int = Field(..., description="周数")
    total_time_minutes: int = Field(..., description="总时间")
    main_training_type: str = Field(..., description="主要训练类型")
    tasks: list[dict[str, Any]] = Field(..., description="任务列表")
    target_questions: int = Field(..., description="目标题目数")
    difficulty_level: float = Field(..., description="难度级别")


class PlanProgressResponse(BaseModel):
    """计划进度响应."""

    plan_id: int = Field(..., description="计划ID")
    student_id: int = Field(..., description="学生ID")
    overall_progress: float = Field(..., description="整体进度")
    weekly_progress: float = Field(..., description="本周进度")
    completion_rate: float = Field(..., description="完成率")
    time_spent_minutes: int = Field(..., description="已用时间")
    remaining_days: int = Field(..., description="剩余天数")


# ==================== 目标设定相关Schema ====================


class GoalCreateRequest(BaseModel):
    """目标创建请求."""

    title: str = Field(..., min_length=1, max_length=100, description="目标标题")
    description: str = Field(..., min_length=1, max_length=500, description="目标描述")
    goal_type: str = Field(..., description="目标类型")
    target_date: str = Field(..., description="目标日期")
    target_metrics: list[dict[str, Any]] = Field(default_factory=list, description="目标指标")
    priority: str = Field("medium", description="优先级")


class GoalResponse(BaseModel):
    """目标响应."""

    goal_id: int = Field(..., description="目标ID")
    student_id: int = Field(..., description="学生ID")
    title: str = Field(..., description="目标标题")
    description: str = Field(..., description="目标描述")
    goal_type: str = Field(..., description="目标类型")
    target_metrics: list[dict[str, Any]] = Field(..., description="目标指标")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    milestones: list[dict[str, Any]] = Field(..., description="里程碑")
    success_criteria: list[str] = Field(..., description="成功标准")
    status: str = Field(..., description="目标状态")
    progress: dict[str, Any] = Field(default_factory=dict, description="进度信息")
    created_at: datetime = Field(..., description="创建时间")


class GoalProgressUpdateRequest(BaseModel):
    """目标进度更新请求."""

    progress_data: dict[str, Any] = Field(..., description="进度数据")
    notes: str = Field("", description="备注")
    milestone_updates: list[dict[str, Any]] = Field(default_factory=list, description="里程碑更新")


class GoalSuggestionResponse(BaseModel):
    """目标建议响应."""

    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    goal_type: str = Field(..., description="目标类型")
    priority_score: float = Field(..., description="优先级分数")
    estimated_duration_weeks: int = Field(..., description="预估周期")
    target_metrics: list[str] = Field(..., description="目标指标")
    rationale: str = Field(..., description="推荐理由")


class GoalAchievementResponse(BaseModel):
    """目标达成评估响应."""

    goal_id: int = Field(..., description="目标ID")
    final_progress: dict[str, Any] = Field(..., description="最终进度")
    achievement_analysis: dict[str, Any] = Field(..., description="达成分析")
    summary_report: str = Field(..., description="总结报告")
    lessons_learned: list[str] = Field(..., description="经验教训")
    next_steps: list[str] = Field(..., description="后续建议")
    evaluated_at: datetime = Field(..., description="评估时间")


# ==================== 进度监控相关Schema ====================


class ProgressMonitoringResponse(BaseModel):
    """进度监控响应."""

    student_id: int = Field(..., description="学生ID")
    monitoring_timestamp: datetime = Field(..., description="监控时间")
    progress_metrics: dict[str, Any] = Field(..., description="进度指标")
    progress_trends: dict[str, Any] = Field(..., description="进度趋势")
    anomalies: list[dict[str, Any]] = Field(..., description="异常情况")
    progress_report: dict[str, Any] = Field(..., description="进度报告")
    reminders: list[dict[str, Any]] = Field(..., description="提醒列表")
    overall_status: str = Field(..., description="整体状态")


class RealTimeProgressResponse(BaseModel):
    """实时进度响应."""

    student_id: int = Field(..., description="学生ID")
    timestamp: datetime = Field(..., description="时间戳")
    today_progress: dict[str, Any] = Field(..., description="今日进度")
    week_progress: dict[str, Any] = Field(..., description="本周进度")
    current_session: dict[str, Any] | None = Field(None, description="当前会话")
    real_time_metrics: dict[str, Any] = Field(..., description="实时指标")
    suggestions: list[str] = Field(..., description="实时建议")


class GoalProgressTrackingResponse(BaseModel):
    """目标进度跟踪响应."""

    goal_id: int = Field(..., description="目标ID")
    student_id: int = Field(..., description="学生ID")
    goal_info: dict[str, Any] = Field(..., description="目标信息")
    goal_progress: dict[str, Any] = Field(..., description="目标进度")
    achievement_probability: float = Field(..., description="达成概率")
    milestone_status: list[dict[str, Any]] = Field(..., description="里程碑状态")
    goal_reminders: list[dict[str, Any]] = Field(..., description="目标提醒")
    time_analysis: dict[str, Any] = Field(..., description="时间分析")
    tracking_timestamp: datetime = Field(..., description="跟踪时间")


class ProgressAlertResponse(BaseModel):
    """进度预警响应."""

    alert_id: str = Field(..., description="预警ID")
    alert_type: str = Field(..., description="预警类型")
    priority: int = Field(..., description="优先级")
    title: str = Field(..., description="预警标题")
    message: str = Field(..., description="预警消息")
    suggested_actions: list[str] = Field(..., description="建议行动")
    created_at: datetime = Field(..., description="创建时间")


class ProgressSummaryResponse(BaseModel):
    """进度总结响应."""

    student_id: int = Field(..., description="学生ID")
    summary_period: dict[str, Any] = Field(..., description="总结周期")
    period_stats: dict[str, Any] = Field(..., description="期间统计")
    improvement_analysis: dict[str, Any] = Field(..., description="改进分析")
    achievements: list[dict[str, Any]] = Field(..., description="成就列表")
    learning_patterns: dict[str, Any] = Field(..., description="学习模式")
    summary_report: str = Field(..., description="总结报告")
    generated_at: datetime = Field(..., description="生成时间")


# ==================== 提醒相关Schema ====================


class ReminderCreateRequest(BaseModel):
    """提醒创建请求."""

    reminder_type: str = Field(..., description="提醒类型")
    message: str | None = Field(None, description="提醒消息")
    priority: str = Field("medium", description="优先级")
    scheduled_time: datetime | None = Field(None, description="计划时间")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class ReminderResponse(BaseModel):
    """提醒响应."""

    reminder_id: str = Field(..., description="提醒ID")
    student_id: int = Field(..., description="学生ID")
    reminder_type: str = Field(..., description="提醒类型")
    title: str = Field(..., description="提醒标题")
    message: str = Field(..., description="提醒消息")
    priority: str = Field(..., description="优先级")
    priority_score: int = Field(..., description="优先级分数")
    scheduled_time: datetime = Field(..., description="计划时间")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="状态")
    delivery_channels: list[str] = Field(..., description="发送渠道")
    metadata: dict[str, Any] = Field(..., description="元数据")


class ReminderStatisticsResponse(BaseModel):
    """提醒统计响应."""

    student_id: int = Field(..., description="学生ID")
    period_days: int = Field(..., description="统计周期")
    total_reminders: int = Field(..., description="总提醒数")
    type_distribution: dict[str, int] = Field(..., description="类型分布")
    priority_distribution: dict[str, int] = Field(..., description="优先级分布")
    response_rate: float = Field(..., description="响应率")
    most_common_type: str | None = Field(None, description="最常见类型")
    statistics_generated_at: datetime = Field(..., description="统计生成时间")


# ==================== 计划调整相关Schema ====================


class PlanAdjustmentRequest(BaseModel):
    """计划调整请求."""

    adjustment_type: str = Field(..., description="调整类型")
    adjustment_data: dict[str, Any] = Field(..., description="调整数据")
    reason: str = Field("", description="调整原因")
    effective_date: datetime | None = Field(None, description="生效日期")


class PlanAdjustmentResponse(BaseModel):
    """计划调整响应."""

    plan_id: int = Field(..., description="计划ID")
    student_id: int = Field(..., description="学生ID")
    adjustment_type: str = Field(..., description="调整类型")
    previous_config: dict[str, Any] = Field(..., description="之前配置")
    new_config: dict[str, Any] = Field(..., description="新配置")
    adjustment_reason: str = Field(..., description="调整原因")
    impact_analysis: dict[str, Any] = Field(..., description="影响分析")
    adjusted_at: datetime = Field(..., description="调整时间")


class DifficultyAdjustmentResponse(BaseModel):
    """难度调整响应."""

    plan_id: int = Field(..., description="计划ID")
    student_id: int = Field(..., description="学生ID")
    performance_analysis: dict[str, Any] = Field(..., description="表现分析")
    adjustment_applied: bool = Field(..., description="是否应用调整")
    adjustment_details: dict[str, Any] = Field(..., description="调整详情")
    adjusted_at: datetime = Field(..., description="调整时间")


# ==================== 学习统计相关Schema ====================


class LearningStatisticsResponse(BaseModel):
    """学习统计响应."""

    student_id: int = Field(..., description="学生ID")
    statistics_period: dict[str, Any] = Field(..., description="统计周期")
    completion_stats: dict[str, Any] = Field(..., description="完成统计")
    time_stats: dict[str, Any] = Field(..., description="时间统计")
    progress_stats: dict[str, Any] = Field(..., description="进度统计")
    effectiveness_stats: dict[str, Any] = Field(..., description="效果统计")
    generated_at: datetime = Field(..., description="生成时间")


class PlanEffectivenessResponse(BaseModel):
    """计划效果评估响应."""

    plan_id: int = Field(..., description="计划ID")
    student_id: int = Field(..., description="学生ID")
    effectiveness_score: float = Field(..., description="效果分数")
    improvement_metrics: dict[str, Any] = Field(..., description="改进指标")
    goal_achievement_rate: float = Field(..., description="目标达成率")
    learning_efficiency: float = Field(..., description="学习效率")
    satisfaction_indicators: dict[str, Any] = Field(..., description="满意度指标")
    recommendations: list[str] = Field(..., description="改进建议")
    evaluated_at: datetime = Field(..., description="评估时间")
