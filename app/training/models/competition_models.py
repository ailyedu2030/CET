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
    competition_id = Column(String(50), unique=True, index=True, nullable=False, comment="竞赛唯一标识")

    # 基本信息
    title = Column(String(200), nullable=False, comment="竞赛标题")
    description = Column(Text, comment="竞赛描述")
    competition_type = Column(String(30), nullable=False, comment="竞赛类型")
    difficulty_level = Column(String(20), default="intermediate", comment="难度级别")

    # 时间信息
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=False, comment="结束时间")
    registration_deadline = Column(DateTime, nullable=False, comment="报名截止时间")
    duration_minutes = Column(Integer, default=30, comment="竞赛时长（分钟）")

    # 组织者信息
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="组织者用户ID")

    # 参与限制
    max_participants = Column(Integer, default=100, comment="最大参与人数")
    participant_count = Column(Integer, default=0, comment="当前参与人数")

    # 竞赛配置
    entry_requirements = Column(JSON, comment="参赛要求")
    question_pool = Column(JSON, comment="题库配置")
    rules = Column(JSON, comment="竞赛规则")
    prizes = Column(JSON, comment="奖励设置")
    scoring_method = Column(String(50), comment="评分方式")

    # 状态
    status = Column(String(20), default="upcoming", comment="竞赛状态")

    # 统计信息
    view_count = Column(Integer, default=0, comment="查看次数")
    is_featured = Column(Boolean, default=False, comment="是否推荐")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    registrations = relationship("CompetitionRegistrationModel", back_populates="competition")
    sessions = relationship("CompetitionSessionModel", back_populates="competition")
    leaderboard_entries = relationship("LeaderboardEntryModel", back_populates="competition")

    def __repr__(self: "CompetitionModel") -> str:
        return f"<CompetitionModel(id={getattr(self, 'id', None)}, title={getattr(self, 'title', None)})>"


class CompetitionRegistrationModel(BaseModel):
    """
    竞赛报名模型

    用户竞赛报名记录
    """

    __tablename__ = "competition_registrations"

    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(String(50), unique=True, index=True, nullable=False, comment="报名唯一标识")

    # 关联信息
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, comment="竞赛ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, comment="团队ID（团队赛）")

    # 报名信息
    registered_at = Column(DateTime, default=datetime.utcnow, comment="报名时间")
    status = Column(String(20), default="registered", comment="报名状态")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    competition = relationship("CompetitionModel", back_populates="registrations")

    def __repr__(self: "CompetitionRegistrationModel") -> str:
        return f"<CompetitionRegistrationModel(id={getattr(self, 'id', None)}, registration_id={getattr(self, 'registration_id', None)})>"


class CompetitionSessionModel(BaseModel):
    """
    竞赛会话模型

    用户竞赛答题会话
    """

    __tablename__ = "competition_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False, comment="会话唯一标识")

    # 关联信息
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, comment="竞赛ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 会话信息
    questions = Column(JSON, comment="题目列表")
    answers = Column(JSON, comment="答案记录")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    current_question_index = Column(Integer, default=0, comment="当前题目索引")
    score = Column(Float, default=0.0, comment="得分")
    status = Column(String(20), default="active", comment="会话状态")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    competition = relationship("CompetitionModel", back_populates="sessions")

    def __repr__(self: "CompetitionSessionModel") -> str:
        return f"<CompetitionSessionModel(id={getattr(self, 'id', None)}, session_id={getattr(self, 'session_id', None)})>"


class LeaderboardEntryModel(BaseModel):
    """
    排行榜模型

    竞赛排行榜记录
    """

    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)

    # 关联信息
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, comment="竞赛ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 排名信息
    rank = Column(Integer, comment="排名")
    final_score = Column(Float, nullable=False, comment="最终得分")
    completion_time = Column(Integer, comment="完成时间（秒）")
    accuracy_rate = Column(Float, comment="准确率")
    total_participants = Column(Integer, comment="总参与人数")

    # 奖励信息
    reward_points = Column(Integer, default=0, comment="奖励积分")
    reward_badge = Column(String(50), comment="奖励徽章")
    reward_title = Column(String(50), comment="奖励称号")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    competition = relationship("CompetitionModel", back_populates="leaderboard_entries")

    def __repr__(self: "LeaderboardEntryModel") -> str:
        return f"<LeaderboardEntryModel(id={getattr(self, 'id', None)}, competition_id={getattr(self, 'competition_id', None)}, user_id={getattr(self, 'user_id', None)})>"
