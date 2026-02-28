"""阅读理解训练 - 数据模型"""

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


class ReadingTheme(str, Enum):
    """阅读主题枚举"""

    SCIENCE_TECHNOLOGY = "science_technology"  # 科学技术
    SOCIAL_CULTURE = "social_culture"  # 社会文化
    EDUCATION_CAREER = "education_career"  # 教育职业
    ENVIRONMENT_HEALTH = "environment_health"  # 环境健康
    ECONOMICS_BUSINESS = "economics_business"  # 经济商业


class ReadingDifficulty(str, Enum):
    """阅读难度枚举"""

    EASY = "easy"  # 简单
    MEDIUM = "medium"  # 中等
    HARD = "hard"  # 困难
    EXPERT = "expert"  # 专家级


class ReadingQuestionType(str, Enum):
    """阅读题型枚举"""

    MAIN_IDEA = "main_idea"  # 主旨大意
    DETAIL = "detail"  # 细节理解
    INFERENCE = "inference"  # 推理判断
    VOCABULARY = "vocabulary"  # 词汇理解
    STRUCTURE = "structure"  # 文章结构


class ReadingPassageModel(BaseModel):
    """
    阅读文章模型

    存储阅读理解的文章内容和元数据
    """

    __tablename__ = "reading_passages"

    id = Column(Integer, primary_key=True, index=True)

    # 文章基本信息
    title = Column(String(200), nullable=False, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章内容")
    word_count = Column(Integer, nullable=False, comment="字数")

    # 分类信息
    theme = Column(String(30), nullable=False, comment="主题分类")
    difficulty = Column(String(20), nullable=False, comment="难度等级")
    source = Column(String(100), comment="文章来源")

    # 元数据
    keywords = Column(JSON, comment="关键词列表")
    summary = Column(Text, comment="文章摘要")
    reading_time_minutes = Column(Integer, comment="建议阅读时间(分钟)")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    usage_count = Column(Integer, default=0, comment="使用次数")
    average_score = Column(Float, default=0.0, comment="平均得分")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    questions = relationship("ReadingQuestionModel", back_populates="passage")
    training_records = relationship(
        "ReadingTrainingRecordModel", back_populates="passage"
    )

    def __repr__(self: "ReadingPassageModel") -> str:
        return f"<ReadingPassageModel(id={getattr(self, 'id', None)}, title={getattr(self, 'title', None)})>"


class ReadingQuestionModel(BaseModel):
    """
    阅读理解题目模型

    存储与文章相关的题目
    """

    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True, index=True)
    passage_id = Column(Integer, ForeignKey("reading_passages.id"), nullable=False)

    # 题目信息
    question_text = Column(Text, nullable=False, comment="题目内容")
    question_type = Column(String(20), nullable=False, comment="题目类型")
    order_index = Column(Integer, nullable=False, comment="题目顺序")

    # 选项和答案
    options = Column(JSON, nullable=False, comment="选项列表")
    correct_answer = Column(String(10), nullable=False, comment="正确答案")
    explanation = Column(Text, comment="答案解析")

    # 难度和分值
    difficulty = Column(String(20), nullable=False, comment="题目难度")
    points = Column(Integer, default=1, comment="题目分值")

    # 统计数据
    usage_count = Column(Integer, default=0, comment="使用次数")
    correct_rate = Column(Float, default=0.0, comment="正确率")
    average_time_seconds = Column(Integer, default=0, comment="平均答题时间(秒)")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    passage = relationship("ReadingPassageModel", back_populates="questions")
    answer_records = relationship("ReadingAnswerRecordModel", back_populates="question")

    def __repr__(self: "ReadingQuestionModel") -> str:
        return f"<ReadingQuestionModel(id={getattr(self, 'id', None)}, passage_id={getattr(self, 'passage_id', None)})>"


class ReadingTrainingPlanModel(BaseModel):
    """
    阅读训练计划模型

    管理学生的阅读训练计划
    """

    __tablename__ = "reading_training_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 计划信息
    plan_name = Column(String(100), nullable=False, comment="计划名称")
    description = Column(Text, comment="计划描述")

    # 计划配置
    weekly_target = Column(Integer, default=15, comment="每周目标题数(3主题×5题)")
    themes_per_week = Column(JSON, comment="每周主题安排")
    difficulty_progression = Column(JSON, comment="难度递进安排")

    # 时间安排
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    end_date = Column(DateTime, nullable=False, comment="结束日期")
    training_days = Column(JSON, comment="训练日安排")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    completion_rate = Column(Float, default=0.0, comment="完成率")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    training_records = relationship(
        "ReadingTrainingRecordModel", back_populates="training_plan"
    )

    def __repr__(self: "ReadingTrainingPlanModel") -> str:
        return f"<ReadingTrainingPlanModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class ReadingTrainingRecordModel(BaseModel):
    """
    阅读训练记录模型

    记录学生的阅读训练过程和结果
    """

    __tablename__ = "reading_training_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")
    passage_id = Column(Integer, ForeignKey("reading_passages.id"), nullable=False)
    training_plan_id = Column(
        Integer, ForeignKey("reading_training_plans.id"), nullable=True
    )

    # 训练信息
    training_mode = Column(String(20), nullable=False, comment="训练模式")
    started_at = Column(DateTime, nullable=False, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 训练结果
    total_questions = Column(Integer, default=0, comment="总题数")
    correct_answers = Column(Integer, default=0, comment="正确答案数")
    accuracy_rate = Column(Float, default=0.0, comment="正确率")
    total_score = Column(Integer, default=0, comment="总得分")

    # 时间统计
    reading_time_seconds = Column(Integer, default=0, comment="阅读时间(秒)")
    answering_time_seconds = Column(Integer, default=0, comment="答题时间(秒)")
    total_time_seconds = Column(Integer, default=0, comment="总用时(秒)")

    # 状态
    is_completed = Column(Boolean, default=False, comment="是否完成")

    # AI分析
    reading_analysis = Column(JSON, comment="阅读分析结果")
    weak_points = Column(JSON, comment="薄弱知识点")
    suggestions = Column(JSON, comment="改进建议")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    passage = relationship("ReadingPassageModel", back_populates="training_records")
    training_plan = relationship(
        "ReadingTrainingPlanModel", back_populates="training_records"
    )
    answer_records = relationship(
        "ReadingAnswerRecordModel", back_populates="training_record"
    )

    def __repr__(self: "ReadingTrainingRecordModel") -> str:
        return f"<ReadingTrainingRecordModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class ReadingAnswerRecordModel(BaseModel):
    """
    阅读答题记录模型

    记录每道题的详细答题情况
    """

    __tablename__ = "reading_answer_records"

    id = Column(Integer, primary_key=True, index=True)
    training_record_id = Column(
        Integer, ForeignKey("reading_training_records.id"), nullable=False
    )
    question_id = Column(Integer, ForeignKey("reading_questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 答题信息
    user_answer = Column(String(10), nullable=False, comment="学生答案")
    is_correct = Column(Boolean, nullable=False, comment="是否正确")
    answer_time_seconds = Column(Integer, default=0, comment="答题时间(秒)")

    # 分析数据
    confidence_level = Column(Float, default=0.0, comment="答题置信度")
    difficulty_perceived = Column(String(20), comment="感知难度")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    training_record = relationship(
        "ReadingTrainingRecordModel", back_populates="answer_records"
    )
    question = relationship("ReadingQuestionModel", back_populates="answer_records")

    def __repr__(self: "ReadingAnswerRecordModel") -> str:
        return f"<ReadingAnswerRecordModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"
