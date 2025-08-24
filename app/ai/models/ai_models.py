"""AI模块的SQLAlchemy数据模型."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel


class AISyllabus(BaseModel):
    """AI生成的教学大纲模型."""

    __tablename__ = "ai_syllabi"

    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="大纲标题")
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, comment="关联课程ID"
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建教师ID"
    )
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="大纲内容结构化数据"
    )
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0.0", comment="版本号"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        comment="状态: draft/review/approved",
    )
    ai_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否AI生成"
    )
    source_materials: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="生成大纲的源材料信息"
    )

    # 关联关系
    course = relationship("Course", back_populates="syllabi")
    teacher = relationship("User", back_populates="syllabi")
    lesson_plans = relationship("LessonPlan", back_populates="syllabus")


class LessonPlan(BaseModel):
    """教案模型."""

    __tablename__ = "lesson_plans"

    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="教案标题")
    syllabus_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("syllabi.id"), nullable=False, comment="关联大纲ID"
    )
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="课时编号")
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=45, comment="课程时长(分钟)"
    )
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, comment="学习目标列表"
    )
    content_structure: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="教学内容结构"
    )
    teaching_methods: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, comment="教学方法列表"
    )
    resources_needed: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, comment="所需资源列表"
    )
    assessment_methods: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, comment="评估方法列表"
    )
    homework_assignments: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="作业安排"
    )
    ai_suggestions: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="AI优化建议"
    )
    collaboration_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list, comment="协作日志"
    )

    # 关联关系
    syllabus = relationship("Syllabus", back_populates="lesson_plans")
    schedules = relationship("LessonSchedule", back_populates="lesson_plan")


class LessonSchedule(BaseModel):
    """课程表模型."""

    __tablename__ = "lesson_schedules"

    lesson_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lesson_plans.id"), nullable=False, comment="关联教案ID"
    )
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id"), nullable=False, comment="关联班级ID"
    )
    scheduled_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="计划上课日期"
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="结束时间")
    classroom: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="教室位置")
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
        comment="状态: scheduled/in_progress/completed/cancelled",
    )
    actual_start_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="实际开始时间"
    )
    actual_end_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="实际结束时间"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注信息")
    ai_recommendations: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="AI优化建议"
    )

    # 关联关系
    lesson_plan = relationship("LessonPlan", back_populates="schedules")
    class_ = relationship("Class", back_populates="lesson_schedules")


class AITaskLog(BaseModel):
    """AI任务执行日志."""

    __tablename__ = "ai_task_logs"

    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="任务类型: syllabus/lesson_plan/schedule"
    )
    request_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, comment="请求参数")
    response_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="响应数据"
    )
    api_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="deepseek", comment="API提供商"
    )
    api_model: Mapped[str] = mapped_column(String(100), nullable=False, comment="使用的模型")
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="消耗的token数")
    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="执行时间(毫秒)"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="状态: pending/success/failed"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="请求用户ID"
    )

    # 关联关系
    user = relationship("User", back_populates="ai_task_logs")


class CollaborativeSession(BaseModel):
    """协作会话模型."""

    __tablename__ = "collaborative_sessions"

    session_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="会话ID"
    )
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="协作资源类型: syllabus/lesson_plan"
    )
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="资源ID")
    participants: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, comment="参与者用户ID列表"
    )
    session_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, comment="会话数据")
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="最后活动时间"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否活跃"
    )
    conflict_resolution_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list, comment="冲突解决日志"
    )


class LearningAnalysis(BaseModel):
    """学情分析模型."""

    __tablename__ = "learning_analyses"

    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id"), nullable=False, comment="关联班级ID"
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, comment="关联课程ID"
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="分析教师ID"
    )
    analysis_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="分析类型: progress/difficulty/engagement"
    )
    analysis_period: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="分析周期: weekly/monthly/semester"
    )

    # 分析数据
    student_count: Mapped[int] = mapped_column(Integer, nullable=False, comment="分析学生数量")
    analysis_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="详细分析数据"
    )
    insights: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, comment="关键洞察"
    )
    risk_students: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, default=list, comment="风险学生ID列表"
    )

    # AI生成标识
    ai_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否AI生成"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="分析置信度(0-1)"
    )

    # 状态和时间
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed", comment="分析状态"
    )
    analysis_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="分析日期"
    )


class TeachingAdjustment(BaseModel):
    """教学调整建议模型."""

    __tablename__ = "teaching_adjustments"

    learning_analysis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("learning_analyses.id"),
        nullable=False,
        comment="关联学情分析ID",
    )
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id"), nullable=False, comment="关联班级ID"
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, comment="关联课程ID"
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="目标教师ID"
    )

    # 调整建议内容
    adjustment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="调整类型: content/pace/method/assessment"
    )
    priority_level: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="优先级: high/medium/low"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="调整建议标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="详细调整说明")

    # 具体调整方案
    adjustments: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="具体调整方案"
    )
    target_students: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, default=list, comment="目标学生ID列表，空为全班"
    )
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=True, comment="预期效果")
    implementation_timeline: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="实施时间线"
    )

    # AI生成标识
    ai_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否AI生成"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="建议置信度(0-1)"
    )
    reasoning: Mapped[str] = mapped_column(Text, nullable=True, comment="建议依据说明")

    # 实施状态
    implementation_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="实施状态: pending/in_progress/completed/dismissed",
    )
    implementation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, comment="开始实施日期"
    )
    feedback: Mapped[str] = mapped_column(Text, nullable=True, comment="实施反馈")
    effectiveness_rating: Mapped[int] = mapped_column(
        Integer, nullable=True, comment="效果评分(1-5)"
    )


class APIKeyPool(BaseModel):
    """API密钥池模型."""

    __tablename__ = "api_key_pools"

    key_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="密钥标识符"
    )
    api_key: Mapped[str] = mapped_column(String(500), nullable=False, comment="API密钥")
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False, comment="API端点")
    daily_quota: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1000000, comment="每日配额"
    )
    rate_limit_per_minute: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, comment="每分钟速率限制"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="优先级")
    cost_per_token: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0014, comment="每token成本"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否激活"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", comment="状态"
    )
    success_rate: Mapped[float] = mapped_column(Float, nullable=True, comment="成功率")
    last_used: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后使用时间"
    )


class APIKeyUsage(BaseModel):
    """API密钥使用记录模型."""

    __tablename__ = "api_key_usages"

    key_id: Mapped[str] = mapped_column(String(100), nullable=False, comment="密钥标识符")
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="模型类型")
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, comment="使用的token数")
    cost: Mapped[float] = mapped_column(Float, nullable=False, comment="成本")
    response_time: Mapped[float] = mapped_column(Float, nullable=False, comment="响应时间(秒)")
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="是否成功")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误消息")


class CostOptimizationLog(BaseModel):
    """成本优化日志模型."""

    __tablename__ = "cost_optimization_logs"

    strategy: Mapped[str] = mapped_column(String(50), nullable=False, comment="优化策略")
    original_cost: Mapped[float] = mapped_column(Float, nullable=False, comment="原始成本")
    optimized_cost: Mapped[float] = mapped_column(Float, nullable=False, comment="优化后成本")
    savings_amount: Mapped[float] = mapped_column(Float, nullable=False, comment="节省金额")
    savings_percentage: Mapped[float] = mapped_column(Float, nullable=False, comment="节省百分比")
    optimization_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="优化元数据"
    )


class ServiceHealthLog(BaseModel):
    """服务健康日志模型."""

    __tablename__ = "service_health_logs"

    service_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="服务名称")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="服务状态")
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, comment="成功率")
    average_response_time: Mapped[float] = mapped_column(
        Float, nullable=False, comment="平均响应时间"
    )
    error_rate: Mapped[float] = mapped_column(Float, nullable=False, comment="错误率")
    availability: Mapped[float] = mapped_column(Float, nullable=False, comment="可用性")
    throughput: Mapped[float] = mapped_column(Float, nullable=False, comment="吞吐量")


class FallbackLog(BaseModel):
    """降级日志模型."""

    __tablename__ = "fallback_logs"

    fallback_level: Mapped[int] = mapped_column(Integer, nullable=False, comment="降级级别")
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False, comment="触发原因")
    request_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, comment="请求数据")
    response_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, comment="响应数据")
