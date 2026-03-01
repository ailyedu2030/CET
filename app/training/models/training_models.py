"""训练系统相关的SQLAlchemy模型定义."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel
from app.shared.models.enums import DifficultyLevel, GradingStatus, QuestionType, TrainingType

if TYPE_CHECKING:
    from app.users.models import User


class TrainingSession(BaseModel):
    """训练会话模型 - 支持完整训练流程."""

    __tablename__ = "training_sessions"

    # 外键
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )

    # 会话信息
    session_type: Mapped[TrainingType] = mapped_column(
        Enum(TrainingType),
        nullable=False,
        index=True,
        comment="训练类型",
    )
    session_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="会话名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="会话描述",
    )

    # 配置参数
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.ELEMENTARY,
        nullable=False,
        comment="难度等级",
    )
    question_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="题目数量",
    )
    time_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="时间限制（分钟）",
    )

    # 会话状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="in_progress",
        nullable=False,
        index=True,
        comment="会话状态",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )

    # 结果统计
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总题目数",
    )
    correct_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="正确答案数",
    )
    total_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="总分数",
    )
    time_spent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="实际用时（秒）",
    )

    # 自适应数据
    initial_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="初始难度等级",
    )
    final_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="最终难度等级",
    )
    adaptation_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="自适应调整数据",
    )

    # 关系
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
    )
    records: Mapped[list["TrainingRecord"]] = relationship(
        "TrainingRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """训练会话模型字符串表示."""
        return f"<TrainingSession(id={self.id}, type={self.session_type}, student_id={self.student_id})>"


class Question(BaseModel):
    """题目模型 - 支持多种题型."""

    __tablename__ = "questions"

    # 题目信息
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType),
        nullable=False,
        index=True,
        comment="题目类型",
    )
    training_type: Mapped[TrainingType] = mapped_column(
        Enum(TrainingType),
        nullable=False,
        index=True,
        comment="训练类型",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="题目标题",
    )
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="题目内容",
    )

    # 题目配置
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.ELEMENTARY,
        nullable=False,
        index=True,
        comment="难度等级",
    )
    max_score: Mapped[float] = mapped_column(
        Float,
        default=10.0,
        nullable=False,
        comment="满分分数",
    )
    time_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="时间限制（秒）",
    )

    # 题目元数据
    knowledge_points: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="知识点标签",
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="题目标签",
    )

    # 答案和评分
    correct_answer: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="正确答案",
    )
    answer_analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="答案解析",
    )
    grading_criteria: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="评分标准",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    # 统计数据
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="使用次数",
    )
    average_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="平均分数",
    )
    correct_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="正确率",
    )

    def __repr__(self) -> str:
        """题目模型字符串表示."""
        return f"<Question(id={self.id}, type={self.question_type}, difficulty={self.difficulty_level})>"


class TrainingRecord(BaseModel):
    """训练记录模型 - 详细记录每次答题."""

    __tablename__ = "training_records"

    # 外键
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="训练会话ID",
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("questions.id"),
        nullable=False,
        comment="题目ID",
    )

    # 答题信息
    user_answer: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="用户答案",
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="是否正确",
    )
    score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="得分",
    )

    # 时间统计
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="开始时间",
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="结束时间",
    )
    time_spent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="用时（秒）",
    )

    # AI批改结果
    grading_status: Mapped[GradingStatus] = mapped_column(
        Enum(GradingStatus),
        default=GradingStatus.PENDING,
        nullable=False,
        comment="批改状态",
    )
    ai_feedback: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="AI反馈内容",
    )
    ai_confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="AI置信度",
    )

    # 学习数据
    knowledge_points_mastered: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="掌握的知识点",
    )
    knowledge_points_weak: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="薄弱的知识点",
    )

    # 关系
    session: Mapped["TrainingSession"] = relationship(
        "TrainingSession",
        back_populates="records",
    )
    question: Mapped["Question"] = relationship(
        "Question",
    )
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
    )

    def __repr__(self) -> str:
        """训练记录模型字符串表示."""
        return f"<TrainingRecord(id={self.id}, session_id={self.session_id}, score={self.score})>"


class IntelligentTrainingLoop(BaseModel):
    """智能训练闭环记录模型 - 🔥需求21核心数据."""

    __tablename__ = "intelligent_training_loops"

    # 基本信息
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )
    training_type: Mapped[TrainingType] = mapped_column(
        Enum(TrainingType),
        nullable=False,
        index=True,
        comment="训练类型",
    )

    # 执行时间
    execution_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="执行时间",
    )
    next_execution_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次执行时间",
    )

    # 闭环阶段数据
    data_collection_result: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="数据采集结果",
    )
    ai_analysis_result: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="AI分析结果",
    )
    strategy_adjustment_result: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="策略调整结果",
    )
    effect_verification_result: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="效果验证结果",
    )

    # 闭环成功指标
    loop_success: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="闭环是否成功",
    )
    ai_analysis_accuracy: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="AI分析准确率",
    )
    improvement_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="改进率",
    )

    # 关系
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
    )

    def __repr__(self) -> str:
        """智能训练闭环模型字符串表示."""
        return f"<IntelligentTrainingLoop(id={self.id}, student_id={self.student_id}, success={self.loop_success})>"


class QuestionBatch(BaseModel):
    """题目批次模型 - 用于批量管理题目."""

    __tablename__ = "question_batches"

    # 批次信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="批次名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="批次描述",
    )
    training_type: Mapped[TrainingType] = mapped_column(
        Enum(TrainingType),
        nullable=False,
        index=True,
        comment="训练类型",
    )

    # 批次配置
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.ELEMENTARY,
        nullable=False,
        comment="难度等级",
    )
    question_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="题目数量",
    )
    time_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="时间限制（分钟）",
    )

    # 批次元数据
    knowledge_points: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="涵盖的知识点",
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="批次标签",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    def __repr__(self) -> str:
        """题目批次模型字符串表示."""
        return f"<QuestionBatch(id={self.id}, name='{self.name}', count={self.question_count})>"


# ==================== 训练工坊相关模型 (需求15) ====================


class TrainingParameterTemplate(BaseModel):
    """训练参数模板模型 - 需求15验收标准2."""

    __tablename__ = "training_parameter_templates"

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="模板名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述",
    )

    # 配置信息
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="训练参数配置JSON",
    )

    # 状态信息
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为默认模板",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    # 外键
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="创建者ID",
    )

    # 关系
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="training_parameter_templates",
    )

    def __repr__(self) -> str:
        """训练参数模板字符串表示."""
        return f"<TrainingParameterTemplate(id={self.id}, name='{self.name}')>"


class TrainingTask(BaseModel):
    """训练任务模型 - 需求15验收标准4."""

    __tablename__ = "training_tasks"

    # 基本信息
    task_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="任务名称",
    )
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="任务类型: weekly/custom",
    )

    # 配置信息
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="任务配置JSON",
    )

    # 状态信息
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        index=True,
        comment="任务状态: draft/published/completed",
    )

    # 时间信息
    publish_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="发布时间",
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="截止时间",
    )

    # 外键
    class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="班级ID",
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("training_parameter_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="使用的参数模板ID",
    )

    # 关系
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys=[teacher_id],
        back_populates="training_tasks",
    )
    template: Mapped[TrainingParameterTemplate | None] = relationship(
        "TrainingParameterTemplate",
        foreign_keys=[template_id],
    )

    def __repr__(self) -> str:
        """训练任务字符串表示."""
        return f"<TrainingTask(id={self.id}, name='{self.task_name}', status='{self.status}')>"


class TrainingTaskSubmission(BaseModel):
    """训练任务提交记录模型 - 需求15验收标准5."""

    __tablename__ = "training_task_submissions"

    # 基本信息
    submission_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="提交数据JSON",
    )
    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="得分",
    )
    completion_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="完成率",
    )

    # 时间信息
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间",
    )

    # 外键
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="任务ID",
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )

    # 关系
    task: Mapped[TrainingTask] = relationship(
        "TrainingTask",
        foreign_keys=[task_id],
    )
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="training_task_submissions",
    )

    def __repr__(self) -> str:
        """训练任务提交记录字符串表示."""
        return f"<TrainingTaskSubmission(id={self.id}, task_id={self.task_id}, student_id={self.student_id})>"
