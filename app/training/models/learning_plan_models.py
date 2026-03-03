"""学习计划与管理系统 - 数据模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel


class PlanStatus(str, Enum):
    """计划状态枚举"""

    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 进行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class PlanType(str, Enum):
    """计划类型枚举"""

    CET4 = "cet4"  # CET4计划
    CET6 = "cet6"  # CET6计划
    CUSTOM = "custom"  # 自定义计划
    DAILY = "daily"  # 日计划
    WEEKLY = "weekly"  # 周计划
    MONTHLY = "monthly"  # 月计划


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 待完成
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    OVERDUE = "overdue"  # 已逾期
    CANCELLED = "cancelled"  # 已取消


class NotificationFrequency(str, Enum):
    """通知频率枚举"""

    NONE = "none"  # 不通知
    DAILY = "daily"  # 每日
    WEEKLY = "weekly"  # 每周
    BEFORE_DEADLINE = "before_deadline"  # 截止前
    CUSTOM = "custom"  # 自定义


class LearningPlanModel(BaseModel):
    """
    学习计划模型

    管理用户的学习计划
    """

    __tablename__ = "learning_plans"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )

    # 计划基本信息
    plan_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="计划名称"
    )
    plan_description: Mapped[str | None] = mapped_column(
        Text, comment="计划描述"
    )
    plan_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="计划类型"
    )

    # 时间安排
    start_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="开始日期"
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="结束日期"
    )
    estimated_hours: Mapped[int | None] = mapped_column(
        Integer, comment="预估学习时长(小时)"
    )

    # 目标设置
    learning_goals: Mapped[dict | None] = mapped_column(
        JSON, comment="学习目标"
    )
    target_score: Mapped[int | None] = mapped_column(
        Integer, comment="目标分数"
    )
    priority_level: Mapped[int] = mapped_column(
        Integer, default=3, comment="优先级(1-5)"
    )

    # 计划配置
    daily_study_time: Mapped[int | None] = mapped_column(
        Integer, comment="每日学习时间(分钟)"
    )
    study_schedule: Mapped[dict | None] = mapped_column(
        JSON, comment="学习时间表"
    )
    reminder_settings: Mapped[dict | None] = mapped_column(
        JSON, comment="提醒设置"
    )

    # 状态和进度
    status: Mapped[str] = mapped_column(
        String(20), default=PlanStatus.DRAFT, comment="计划状态"
    )
    completion_rate: Mapped[float] = mapped_column(
        Float, default=0.0, comment="完成率"
    )
    actual_hours: Mapped[float] = mapped_column(
        Float, default=0.0, comment="实际学习时长"
    )

    # 统计数据
    total_tasks: Mapped[int] = mapped_column(
        Integer, default=0, comment="总任务数"
    )
    completed_tasks: Mapped[int] = mapped_column(
        Integer, default=0, comment="已完成任务数"
    )
    overdue_tasks: Mapped[int] = mapped_column(
        Integer, default=0, comment="逾期任务数"
    )

    # 关系
    tasks: Mapped[list["LearningTaskModel"]] = relationship(
        "LearningTaskModel", back_populates="plan"
    )
    progress_records: Mapped[list["LearningProgressModel"]] = relationship(
        "LearningProgressModel", back_populates="plan"
    )


class LearningTaskModel(BaseModel):
    """
    学习任务模型

    管理学习计划中的具体任务
    """

    __tablename__ = "learning_tasks"

    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_plans.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )

    # 任务基本信息
    task_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="任务名称"
    )
    task_description: Mapped[str | None] = mapped_column(
        Text, comment="任务描述"
    )
    task_type: Mapped[str | None] = mapped_column(
        String(50), comment="任务类型"
    )

    # 时间安排
    scheduled_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="计划日期"
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime, comment="截止日期"
    )
    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer, comment="预估时长(分钟)"
    )
    actual_minutes: Mapped[int] = mapped_column(
        Integer, default=0, comment="实际时长(分钟)"
    )

    # 任务内容
    task_content: Mapped[dict | None] = mapped_column(
        JSON, comment="任务内容配置"
    )
    resources: Mapped[dict | None] = mapped_column(
        JSON, comment="学习资源"
    )
    requirements: Mapped[dict | None] = mapped_column(
        JSON, comment="完成要求"
    )

    # 状态和进度
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.PENDING, comment="任务状态"
    )
    completion_rate: Mapped[float] = mapped_column(
        Float, default=0.0, comment="完成率"
    )
    difficulty_level: Mapped[int] = mapped_column(
        Integer, default=3, comment="难度等级(1-5)"
    )

    # 完成情况
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="开始时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="完成时间"
    )
    result_score: Mapped[float | None] = mapped_column(
        Float, comment="完成得分"
    )
    result_data: Mapped[dict | None] = mapped_column(
        JSON, comment="完成结果数据"
    )

    # 反馈和评价
    self_rating: Mapped[int | None] = mapped_column(
        Integer, comment="自我评分(1-5)"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, comment="学习笔记"
    )

    # 关系
    plan: Mapped["LearningPlanModel"] = relationship(
        "LearningPlanModel", back_populates="tasks"
    )


class LearningProgressModel(BaseModel):
    """
    学习进度模型

    记录学习进度和数据
    """

    __tablename__ = "learning_plan_progress"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )
    plan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("learning_plans.id"), nullable=True
    )

    # 进度记录
    record_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="记录日期"
    )
    study_minutes: Mapped[int] = mapped_column(
        Integer, default=0, comment="学习时长(分钟)"
    )
    tasks_completed: Mapped[int] = mapped_column(
        Integer, default=0, comment="完成任务数"
    )

    # 学习数据
    listening_score: Mapped[float | None] = mapped_column(
        Float, comment="听力得分"
    )
    reading_score: Mapped[float | None] = mapped_column(
        Float, comment="阅读得分"
    )
    writing_score: Mapped[float | None] = mapped_column(
        Float, comment="写作得分"
    )
    overall_score: Mapped[float | None] = mapped_column(
        Float, comment="综合得分"
    )

    # 学习行为
    login_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="登录次数"
    )
    practice_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="练习次数"
    )
    mistake_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="错误次数"
    )

    # 学习状态
    focus_level: Mapped[int | None] = mapped_column(
        Integer, comment="专注度(1-5)"
    )
    satisfaction_level: Mapped[int | None] = mapped_column(
        Integer, comment="满意度(1-5)"
    )
    difficulty_perception: Mapped[int | None] = mapped_column(
        Integer, comment="难度感知(1-5)"
    )

    # 额外数据
    notes: Mapped[str | None] = mapped_column(
        Text, comment="学习笔记"
    )
    achievements: Mapped[dict | None] = mapped_column(
        JSON, comment="当日成就"
    )

    # 关系
    plan: Mapped["LearningPlanModel | None"] = relationship(
        "LearningPlanModel", back_populates="progress_records"
    )


class LearningReminderModel(BaseModel):
    """
    学习提醒模型

    管理学习提醒和通知
    """

    __tablename__ = "learning_reminders"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )
    plan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("learning_plans.id"), nullable=True
    )
    task_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("learning_tasks.id"), nullable=True
    )

    # 提醒设置
    reminder_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="提醒名称"
    )
    reminder_type: Mapped[str | None] = mapped_column(
        String(50), comment="提醒类型"
    )
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="提醒频率"
    )

    # 时间设置
    reminder_time: Mapped[datetime | None] = mapped_column(
        DateTime, comment="提醒时间"
    )
    repeat_pattern: Mapped[dict | None] = mapped_column(
        JSON, comment="重复模式"
    )
    timezone: Mapped[str | None] = mapped_column(
        String(50), comment="时区"
    )

    # 提醒内容
    message: Mapped[str | None] = mapped_column(
        Text, comment="提醒消息"
    )
    notification_channels: Mapped[dict | None] = mapped_column(
        JSON, comment="通知渠道"
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否激活"
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后发送时间"
    )
    next_send_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="下次发送时间"
    )

    # 统计
    sent_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="发送次数"
    )
    click_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="点击次数"
    )


class LearningReportModel(BaseModel):
    """
    学习报告模型

    生成和存储学习报告
    """

    __tablename__ = "learning_reports"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )
    plan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("learning_plans.id"), nullable=True
    )

    # 报告基本信息
    report_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="报告名称"
    )
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="报告类型"
    )
    report_period: Mapped[str | None] = mapped_column(
        String(50), comment="报告周期"
    )

    # 时间范围
    start_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="开始日期"
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="结束日期"
    )

    # 报告内容
    summary_data: Mapped[dict | None] = mapped_column(
        JSON, comment="汇总数据"
    )
    detailed_data: Mapped[dict | None] = mapped_column(
        JSON, comment="详细数据"
    )
    charts_data: Mapped[dict | None] = mapped_column(
        JSON, comment="图表数据"
    )
    insights: Mapped[dict | None] = mapped_column(
        JSON, comment="洞察分析"
    )
    recommendations: Mapped[dict | None] = mapped_column(
        JSON, comment="改进建议"
    )

    # 报告状态
    is_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已生成"
    )
    generation_time: Mapped[datetime | None] = mapped_column(
        DateTime, comment="生成时间"
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500), comment="文件路径"
    )

    # 分享设置
    is_shared: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否分享"
    )
    share_token: Mapped[str | None] = mapped_column(
        String(100), comment="分享令牌"
    )
