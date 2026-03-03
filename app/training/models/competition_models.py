"""学习竞赛系统 - 数据模型"""

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


class CompetitionType(str, Enum):
    """竞赛类型枚举"""

    SPEED_CHALLENGE = "speed_challenge"  # 速度挑战
    ACCURACY_CONTEST = "accuracy_contest"  # 准确率竞赛
    ENDURANCE_MARATHON = "endurance_marathon"  # 学习马拉松
    TEAM_BATTLE = "team_battle"  # 团队对战
    DAILY_CHALLENGE = "daily_challenge"  # 每日挑战


class CompetitionStatus(str, Enum):
    """竞赛状态枚举"""

    UPCOMING = "upcoming"  # 即将开始
    ACTIVE = "active"  # 进行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class RegistrationStatus(str, Enum):
    """报名状态枚举"""

    REGISTERED = "registered"  # 已报名
    CANCELLED = "cancelled"  # 已取消
    WITHDRAWN = "withdrawn"  # 已退出
    COMPLETED = "completed"  # 已完成


class SessionStatus(str, Enum):
    """竞赛会话状态枚举"""

    ACTIVE = "active"  # 进行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    ABANDONED = "abandoned"  # 已放弃


class CompetitionModel(BaseModel):
    """
    竞赛模型

    学习竞赛活动管理
    """

    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    title = Column(String(200), nullable=False, comment="竞赛标题")
    description = Column(Text, comment="竞赛描述")
    competition_type = Column(String(50), nullable=False, comment="竞赛类型")
    status = Column(String(50), nullable=False, comment="竞赛状态")
    organizer_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="组织者用户ID"
    )
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=False, comment="结束时间")
    registration_deadline = Column(DateTime, nullable=False, comment="报名截止时间")
    max_participants = Column(Integer, comment="最大参与人数")
    current_participants = Column(Integer, nullable=False, comment="当前参与人数")
    difficulty_level = Column(String(50), nullable=False, comment="难度级别")
    duration_minutes = Column(Integer, nullable=False, comment="竞赛时长（分钟）")
    question_count = Column(Integer, nullable=False, comment="题目数量")
    passing_score = Column(Float, nullable=False, comment="及格分数")
    reward_config = Column(JSON, comment="奖励配置")
    rules = Column(Text, comment="竞赛规则")
    is_public = Column(Boolean, nullable=False, comment="是否公开")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    registrations = relationship(
        "CompetitionRegistrationModel", back_populates="competition"
    )
    sessions = relationship("CompetitionSessionModel", back_populates="competition")

    def __repr__(self: "CompetitionModel") -> str:
        return f"<CompetitionModel(id={getattr(self, 'id', None)}, title={getattr(self, 'title', None)})>"


class CompetitionRegistrationModel(BaseModel):
    """
    竞赛报名模型

    用户竞赛报名记录
    """

    __tablename__ = "competition_registrations"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(
        Integer, ForeignKey("competitions.id"), nullable=False, comment="竞赛ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    registration_time = Column(DateTime, nullable=False, comment="报名时间")
    status = Column(String(50), nullable=False, comment="报名状态")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    competition = relationship("CompetitionModel", back_populates="registrations")

    def __repr__(self: "CompetitionRegistrationModel") -> str:
        return f"<CompetitionRegistrationModel(id={getattr(self, 'id', None)}, competition_id={getattr(self, 'competition_id', None)}, user_id={getattr(self, 'user_id', None)})>"


class CompetitionSessionModel(BaseModel):
    """
    竞赛会话模型

    用户竞赛答题会话
    """

    __tablename__ = "competition_sessions"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(
        Integer, ForeignKey("competitions.id"), nullable=False, comment="竞赛ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_id = Column(String(100), nullable=False, comment="会话唯一标识")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    current_question_index = Column(Integer, nullable=False, comment="当前题目索引")
    score = Column(Float, nullable=False, comment="得分")
    answers = Column(JSON, comment="答案记录")
    status = Column(String(50), nullable=False, comment="会话状态")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    competition = relationship("CompetitionModel", back_populates="sessions")

    def __repr__(self: "CompetitionSessionModel") -> str:
        return f"<CompetitionSessionModel(id={getattr(self, 'id', None)}, session_id={getattr(self, 'session_id', None)})>"


class CompetitionResultModel(BaseModel):
    """
    竞赛结果模型

    竞赛结果记录
    """

    __tablename__ = "competition_results"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(
        Integer, ForeignKey("competitions.id"), nullable=False, comment="竞赛ID"
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_id = Column(String(100), nullable=False, comment="会话唯一标识")
    final_score = Column(Float, nullable=False, comment="最终得分")
    rank = Column(Integer, comment="排名")
    completion_time = Column(Integer, nullable=False, comment="完成时间（秒）")
    correct_answers = Column(Integer, nullable=False, comment="正确答案数")
    total_questions = Column(Integer, nullable=False, comment="总题数")
    accuracy_rate = Column(Float, nullable=False, comment="准确率")
    reward_earned = Column(JSON, comment="获得的奖励")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "CompetitionResultModel") -> str:
        return f"<CompetitionResultModel(id={getattr(self, 'id', None)}, competition_id={getattr(self, 'competition_id', None)}, user_id={getattr(self, 'user_id', None)})>"
