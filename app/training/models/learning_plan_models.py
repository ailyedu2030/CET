"""学习计划与管理系统 - 数据模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

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

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 计划基本信息
    plan_name = Column(String(100), nullable=False, comment="计划名称")
    plan_description = Column(Text, comment="计划描述")
    plan_type = Column(String(20), nullable=False, comment="计划类型")

    # 时间安排
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    end_date = Column(DateTime, nullable=False, comment="结束日期")
    estimated_hours = Column(Integer, comment="预估学习时长(小时)")

    # 目标设置
    learning_goals = Column(JSON, comment="学习目标")
    target_score = Column(Integer, comment="目标分数")
    priority_level = Column(Integer, default=3, comment="优先级(1-5)")

    # 计划配置
    daily_study_time = Column(Integer, comment="每日学习时间(分钟)")
    study_schedule = Column(JSON, comment="学习时间表")
    reminder_settings = Column(JSON, comment="提醒设置")

    # 状态和进度
    status = Column(String(20), default=PlanStatus.DRAFT, comment="计划状态")
    completion_rate = Column(Float, default=0.0, comment="完成率")
    actual_hours = Column(Float, default=0.0, comment="实际学习时长")

    # 统计数据
    total_tasks = Column(Integer, default=0, comment="总任务数")
    completed_tasks = Column(Integer, default=0, comment="已完成任务数")
    overdue_tasks = Column(Integer, default=0, comment="逾期任务数")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    tasks = relationship("LearningTaskModel", back_populates="plan")
    progress_records = relationship("LearningProgressModel", back_populates="plan")

    def __repr__(self: "LearningPlanModel") -> str:
        return f"<LearningPlanModel(id={getattr(self, 'id', None)}, name={getattr(self, 'plan_name', None)})>"


class LearningTaskModel(BaseModel):
    """
    学习任务模型

    管理学习计划中的具体任务
    """

    __tablename__ = "learning_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 任务基本信息
    task_name = Column(String(200), nullable=False, comment="任务名称")
    task_description = Column(Text, comment="任务描述")
    task_type = Column(String(50), comment="任务类型")

    # 时间安排
    scheduled_date = Column(DateTime, nullable=False, comment="计划日期")
    due_date = Column(DateTime, comment="截止日期")
    estimated_minutes = Column(Integer, comment="预估时长(分钟)")
    actual_minutes = Column(Integer, default=0, comment="实际时长(分钟)")

    # 任务内容
    task_content = Column(JSON, comment="任务内容配置")
    resources = Column(JSON, comment="学习资源")
    requirements = Column(JSON, comment="完成要求")

    # 状态和进度
    status = Column(String(20), default=TaskStatus.PENDING, comment="任务状态")
    completion_rate = Column(Float, default=0.0, comment="完成率")
    difficulty_level = Column(Integer, default=3, comment="难度等级(1-5)")

    # 完成情况
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    result_score = Column(Float, comment="完成得分")
    result_data = Column(JSON, comment="完成结果数据")

    # 反馈和评价
    self_rating = Column(Integer, comment="自我评分(1-5)")
    notes = Column(Text, comment="学习笔记")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    plan = relationship("LearningPlanModel", back_populates="tasks")

    def __repr__(self: "LearningTaskModel") -> str:
        return f"<LearningTaskModel(id={getattr(self, 'id', None)}, name={getattr(self, 'task_name', None)})>"


class LearningProgressModel(BaseModel):
    """
    学习进度模型

    记录学习进度和数据
    """

    __tablename__ = "learning_plan_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=True)

    # 进度记录
    record_date = Column(DateTime, nullable=False, comment="记录日期")
    study_minutes = Column(Integer, default=0, comment="学习时长(分钟)")
    tasks_completed = Column(Integer, default=0, comment="完成任务数")

    # 学习数据
    listening_score = Column(Float, comment="听力得分")
    reading_score = Column(Float, comment="阅读得分")
    writing_score = Column(Float, comment="写作得分")
    overall_score = Column(Float, comment="综合得分")

    # 学习行为
    login_count = Column(Integer, default=0, comment="登录次数")
    practice_count = Column(Integer, default=0, comment="练习次数")
    mistake_count = Column(Integer, default=0, comment="错误次数")

    # 学习状态
    focus_level = Column(Integer, comment="专注度(1-5)")
    satisfaction_level = Column(Integer, comment="满意度(1-5)")
    difficulty_perception = Column(Integer, comment="难度感知(1-5)")

    # 额外数据
    notes = Column(Text, comment="学习笔记")
    achievements = Column(JSON, comment="当日成就")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    plan = relationship("LearningPlanModel", back_populates="progress_records")

    def __repr__(self: "LearningProgressModel") -> str:
        return f"<LearningProgressModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class LearningReminderModel(BaseModel):
    """
    学习提醒模型

    管理学习提醒和通知
    """

    __tablename__ = "learning_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("learning_tasks.id"), nullable=True)

    # 提醒设置
    reminder_name = Column(String(100), nullable=False, comment="提醒名称")
    reminder_type = Column(String(50), comment="提醒类型")
    frequency = Column(String(20), nullable=False, comment="提醒频率")

    # 时间设置
    reminder_time = Column(DateTime, comment="提醒时间")
    repeat_pattern = Column(JSON, comment="重复模式")
    timezone = Column(String(50), comment="时区")

    # 提醒内容
    message = Column(Text, comment="提醒消息")
    notification_channels = Column(JSON, comment="通知渠道")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_sent_at = Column(DateTime, comment="最后发送时间")
    next_send_at = Column(DateTime, comment="下次发送时间")

    # 统计
    sent_count = Column(Integer, default=0, comment="发送次数")
    click_count = Column(Integer, default=0, comment="点击次数")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "LearningReminderModel") -> str:
        return f"<LearningReminderModel(id={getattr(self, 'id', None)}, name={getattr(self, 'reminder_name', None)})>"


class LearningReportModel(BaseModel):
    """
    学习报告模型

    生成和存储学习报告
    """

    __tablename__ = "learning_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=True)

    # 报告基本信息
    report_name = Column(String(100), nullable=False, comment="报告名称")
    report_type = Column(String(50), nullable=False, comment="报告类型")
    report_period = Column(String(50), comment="报告周期")

    # 时间范围
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    end_date = Column(DateTime, nullable=False, comment="结束日期")

    # 报告内容
    summary_data = Column(JSON, comment="汇总数据")
    detailed_data = Column(JSON, comment="详细数据")
    charts_data = Column(JSON, comment="图表数据")
    insights = Column(JSON, comment="洞察分析")
    recommendations = Column(JSON, comment="改进建议")

    # 报告状态
    is_generated = Column(Boolean, default=False, comment="是否已生成")
    generation_time = Column(DateTime, comment="生成时间")
    file_path = Column(String(500), comment="文件路径")

    # 分享设置
    is_shared = Column(Boolean, default=False, comment="是否分享")
    share_token = Column(String(100), comment="分享令牌")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "LearningReportModel") -> str:
        return f"<LearningReportModel(id={getattr(self, 'id', None)}, name={getattr(self, 'report_name', None)})>"
