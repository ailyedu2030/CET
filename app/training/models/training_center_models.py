"""学生综合训练中心 - 数据模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from app.shared.models.base_model import BaseModel


class TrainingMode(str, Enum):
    """训练模式枚举"""

    PRACTICE = "practice"  # 练习模式
    SIMULATION = "simulation"  # 模拟模式
    SPRINT = "sprint"  # 冲刺模式


class TrainingType(str, Enum):
    """训练类型枚举"""

    VOCABULARY = "vocabulary"  # 词汇训练
    LISTENING = "listening"  # 听力训练
    READING = "reading"  # 阅读理解
    WRITING = "writing"  # 写作训练
    TRANSLATION = "translation"  # 翻译训练


class DifficultyLevel(str, Enum):
    """难度等级枚举"""

    BEGINNER = "beginner"  # 初级
    ELEMENTARY = "elementary"  # 基础
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"  # 高级
    EXPERT = "expert"  # 专家


class TrainingCenterModel(BaseModel):
    """
    学生综合训练中心数据模型

    基于需求21：学生综合训练中心（系统核心）
    实现智能训练闭环系统
    """

    __tablename__ = "training_centers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")
    name = Column(String(255), nullable=False, comment="训练中心名称")
    description = Column(Text, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 训练配置
    preferred_difficulty = Column(
        String(20), default=DifficultyLevel.INTERMEDIATE, comment="偏好难度"
    )
    daily_target_minutes = Column(Integer, default=60, comment="每日目标训练时长(分钟)")
    weekly_target_sessions = Column(Integer, default=5, comment="每周目标训练次数")

    # 统计数据
    total_sessions = Column(Integer, default=0, comment="总训练次数")
    total_minutes = Column(Integer, default=0, comment="总训练时长")
    current_streak = Column(Integer, default=0, comment="当前连续训练天数")
    best_streak = Column(Integer, default=0, comment="最佳连续训练天数")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
    last_training_at = Column(DateTime, nullable=True, comment="最后训练时间")

    # 关系
    training_sessions = relationship(
        "TrainingSessionModel", back_populates="training_center"
    )
    progress_records = relationship(
        "TrainingProgressModel", back_populates="training_center"
    )
    training_goals = relationship("TrainingGoalModel", back_populates="training_center")
    training_achievements = relationship(
        "TrainingAchievementModel", back_populates="training_center"
    )

    def __repr__(self: "TrainingCenterModel") -> str:
        return f"<TrainingCenterModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, name={getattr(self, 'name', None)})>"


class TrainingSessionModel(BaseModel):
    """
    训练会话模型

    记录每次训练的详细信息
    """

    __tablename__ = "training_center_sessions"

    id = Column(Integer, primary_key=True, index=True)
    training_center_id = Column(
        Integer, ForeignKey("training_centers.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 训练基本信息
    training_type = Column(String(20), nullable=False, comment="训练类型")
    training_mode = Column(String(20), nullable=False, comment="训练模式")
    difficulty_level = Column(String(20), nullable=False, comment="难度等级")

    # 训练内容
    questions_data = Column(JSON, comment="题目数据")
    answers_data = Column(JSON, comment="答案数据")

    # 训练结果
    total_questions = Column(Integer, default=0, comment="总题数")
    correct_answers = Column(Integer, default=0, comment="正确答案数")
    accuracy_rate = Column(Float, default=0.0, comment="正确率")
    completion_rate = Column(Float, default=0.0, comment="完成率")

    # 时间统计
    duration_minutes = Column(Integer, default=0, comment="训练时长(分钟)")
    started_at = Column(DateTime, nullable=False, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 状态
    is_completed = Column(Boolean, default=False, comment="是否完成")
    is_graded = Column(Boolean, default=False, comment="是否已批改")

    # AI分析结果
    ai_analysis = Column(JSON, comment="AI分析结果")
    weak_points = Column(JSON, comment="薄弱知识点")
    recommendations = Column(JSON, comment="学习建议")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    training_center = relationship(
        "TrainingCenterModel", back_populates="training_sessions"
    )
    progress_record = relationship(
        "TrainingProgressModel", back_populates="training_session", uselist=False
    )
    feedback_records = relationship(
        "TrainingFeedbackModel", back_populates="training_session"
    )

    def __repr__(self: "TrainingSessionModel") -> str:
        return f"<TrainingSessionModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, type={getattr(self, 'training_type', None)})>"


class TrainingProgressModel(BaseModel):
    """
    训练进度记录模型

    跟踪学生的学习进度和能力发展
    """

    __tablename__ = "training_progress"

    id = Column(Integer, primary_key=True, index=True)
    training_center_id = Column(
        Integer, ForeignKey("training_centers.id"), nullable=False
    )
    training_session_id = Column(
        Integer, ForeignKey("training_center_sessions.id"), nullable=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 进度信息
    training_type = Column(String(20), nullable=False, comment="训练类型")
    knowledge_point = Column(String(100), nullable=False, comment="知识点")

    # 能力评估
    mastery_level = Column(Float, default=0.0, comment="掌握程度(0-1)")
    confidence_score = Column(Float, default=0.0, comment="置信度(0-1)")
    improvement_rate = Column(Float, default=0.0, comment="提升速度")

    # 统计数据
    practice_count = Column(Integer, default=0, comment="练习次数")
    correct_count = Column(Integer, default=0, comment="正确次数")
    recent_accuracy = Column(Float, default=0.0, comment="近期正确率")

    # 时间信息
    first_encounter_at = Column(DateTime, default=datetime.utcnow, comment="首次接触时间")
    last_practice_at = Column(DateTime, default=datetime.utcnow, comment="最后练习时间")
    mastery_achieved_at = Column(DateTime, nullable=True, comment="掌握达成时间")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    training_center = relationship(
        "TrainingCenterModel", back_populates="progress_records"
    )
    training_session = relationship(
        "TrainingSessionModel", back_populates="progress_record"
    )

    def __repr__(self: "TrainingProgressModel") -> str:
        return f"<TrainingProgressModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, knowledge_point={getattr(self, 'knowledge_point', None)})>"


class TrainingGoalModel(BaseModel):
    """
    训练目标模型

    用于设定和跟踪学生的学习目标
    """

    __tablename__ = "training_goals"

    id = Column(Integer, primary_key=True, index=True)
    training_center_id = Column(
        Integer, ForeignKey("training_centers.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 目标信息
    goal_type = Column(String(20), nullable=False, comment="目标类型")
    goal_title = Column(String(200), nullable=False, comment="目标标题")
    goal_description = Column(Text, comment="目标描述")

    # 目标指标
    target_value = Column(Float, nullable=False, comment="目标值")
    current_value = Column(Float, default=0.0, comment="当前值")
    unit = Column(String(20), nullable=False, comment="单位")

    # 时间设定
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    target_date = Column(DateTime, nullable=False, comment="目标日期")
    completed_date = Column(DateTime, nullable=True, comment="完成日期")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_completed = Column(Boolean, default=False, comment="是否完成")
    completion_rate = Column(Float, default=0.0, comment="完成率")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    training_center = relationship(
        "TrainingCenterModel", back_populates="training_goals"
    )

    def __repr__(self: "TrainingGoalModel") -> str:
        return f"<TrainingGoalModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, goal_title={getattr(self, 'goal_title', None)})>"


class TrainingAchievementModel(BaseModel):
    """
    训练成就模型

    记录学生在训练过程中获得的成就和徽章
    """

    __tablename__ = "training_achievements"

    id = Column(Integer, primary_key=True, index=True)
    training_center_id = Column(
        Integer, ForeignKey("training_centers.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 成就信息
    achievement_type = Column(String(50), nullable=False, comment="成就类型")
    achievement_name = Column(String(100), nullable=False, comment="成就名称")
    achievement_description = Column(Text, comment="成就描述")
    achievement_icon = Column(String(200), comment="成就图标URL")

    # 成就条件
    condition_type = Column(String(50), nullable=False, comment="条件类型")
    condition_value = Column(Float, nullable=False, comment="条件值")
    current_progress = Column(Float, default=0.0, comment="当前进度")

    # 奖励信息
    reward_points = Column(Integer, default=0, comment="奖励积分")
    reward_items = Column(JSON, comment="奖励物品")

    # 状态
    is_unlocked = Column(Boolean, default=False, comment="是否解锁")
    is_claimed = Column(Boolean, default=False, comment="是否领取")
    unlocked_at = Column(DateTime, nullable=True, comment="解锁时间")
    claimed_at = Column(DateTime, nullable=True, comment="领取时间")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    training_center = relationship(
        "TrainingCenterModel", back_populates="training_achievements"
    )

    def __repr__(self: "TrainingAchievementModel") -> str:
        return f"<TrainingAchievementModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, achievement_name={getattr(self, 'achievement_name', None)})>"


class TrainingFeedbackModel(BaseModel):
    """
    训练反馈模型

    收集和管理学生对训练内容的反馈
    """

    __tablename__ = "training_feedback"

    id = Column(Integer, primary_key=True, index=True)
    training_session_id = Column(
        Integer, ForeignKey("training_center_sessions.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")

    # 反馈内容
    feedback_type = Column(String(20), nullable=False, comment="反馈类型")
    rating = Column(Integer, nullable=False, comment="评分(1-5)")
    content = Column(Text, comment="反馈内容")

    # 反馈分类
    difficulty_rating = Column(Integer, comment="难度评分(1-5)")
    usefulness_rating = Column(Integer, comment="有用性评分(1-5)")
    engagement_rating = Column(Integer, comment="参与度评分(1-5)")

    # 改进建议
    suggestions = Column(Text, comment="改进建议")
    tags = Column(JSON, comment="标签")

    # 状态
    is_anonymous = Column(Boolean, default=False, comment="是否匿名")
    is_processed = Column(Boolean, default=False, comment="是否已处理")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    training_session = relationship(
        "TrainingSessionModel", back_populates="feedback_records"
    )

    def __repr__(self: "TrainingFeedbackModel") -> str:
        return f"<TrainingFeedbackModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, rating={getattr(self, 'rating', None)})>"
