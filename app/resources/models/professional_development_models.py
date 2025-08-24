"""专业发展支持数据模型 - 需求17实现."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel
from app.shared.models.enums import DifficultyLevel

if TYPE_CHECKING:
    from app.users.models.user_models import User

# 导出模型
__all__ = [
    "TrainingResource",
    "TrainingEnrollment",
    "CertificationMaterial",
    "CommunityPost",
    "CommunityReply",
    "ResearchUpdate",
    "NotificationSettings",
    "LearningProgress",
]


class TrainingResource(BaseModel):
    """培训资源模型 - 教学能力培训资源."""

    __tablename__ = "training_resources"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="培训标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="培训描述")
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="培训分类")

    # 培训配置
    duration: Mapped[str] = mapped_column(String(50), nullable=False, comment="培训时长")
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
        comment="难度等级",
    )
    instructor: Mapped[str] = mapped_column(String(100), nullable=False, comment="讲师姓名")

    # 内容信息
    content_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="内容链接")
    materials: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="培训材料"
    )
    objectives: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="学习目标"
    )
    prerequisites: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="前置要求"
    )

    # 统计信息
    enrolled_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="报名人数"
    )
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="评分")
    rating_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="评分人数"
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否推荐"
    )

    # 标签
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")

    # 关系
    enrollments: Mapped[list[TrainingEnrollment]] = relationship(
        "TrainingEnrollment", back_populates="training"
    )


class TrainingEnrollment(BaseModel):
    """培训报名模型."""

    __tablename__ = "training_enrollments"

    # 外键
    training_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_resources.id", ondelete="CASCADE"),
        nullable=False,
        comment="培训ID",
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )

    # 报名信息
    motivation: Mapped[str | None] = mapped_column(Text, nullable=True, comment="报名动机")
    status: Mapped[str] = mapped_column(
        String(20), default="enrolled", nullable=False, comment="状态"
    )

    # 学习进度
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="学习进度")
    completed_lessons: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="完成课程数"
    )
    total_lessons: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="总课程数"
    )

    # 时间信息
    enrolled_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="报名时间")
    last_accessed_at: Mapped[DateTime | None] = mapped_column(
        DateTime, nullable=True, comment="最后访问时间"
    )
    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime, nullable=True, comment="完成时间"
    )

    # 关系
    training: Mapped[TrainingResource] = relationship(
        "TrainingResource", back_populates="enrollments"
    )
    user: Mapped[User] = relationship("User")


class CertificationMaterial(BaseModel):
    """认证辅导材料模型."""

    __tablename__ = "certification_materials"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="材料标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="材料描述")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="材料类型")
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="认证分类")

    # 文件信息
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="文件链接")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="文件大小")
    file_format: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="文件格式")

    # 统计信息
    download_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="下载次数"
    )
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="评分")
    rating_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="评分人数"
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否免费")

    # 标签
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")


class CommunityPost(BaseModel):
    """社区帖子模型."""

    __tablename__ = "community_posts"

    # 外键
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="作者ID",
    )

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="帖子标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="帖子内容")
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="帖子分类")

    # 互动统计
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="点赞数")
    replies: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="回复数")
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览数")

    # 状态信息
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否置顶"
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否锁定"
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否精华"
    )

    # 标签
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")

    # 关系
    author: Mapped[User] = relationship("User")
    replies_list: Mapped[list[CommunityReply]] = relationship(
        "CommunityReply", back_populates="post"
    )


class CommunityReply(BaseModel):
    """社区回复模型."""

    __tablename__ = "community_replies"

    # 外键
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=False,
        comment="帖子ID",
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="作者ID",
    )

    # 基本信息
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="回复内容")

    # 互动统计
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="点赞数")

    # 回复关系
    reply_to_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("community_replies.id", ondelete="CASCADE"),
        nullable=True,
        comment="回复的回复ID",
    )

    # 关系
    post: Mapped[CommunityPost] = relationship("CommunityPost", back_populates="replies_list")
    author: Mapped[User] = relationship("User")


class ResearchUpdate(BaseModel):
    """研究动态模型."""

    __tablename__ = "research_updates"

    # 基本信息
    title: Mapped[str] = mapped_column(String(300), nullable=False, comment="标题")
    summary: Mapped[str] = mapped_column(Text, nullable=False, comment="摘要")
    full_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="全文内容")
    source: Mapped[str] = mapped_column(String(200), nullable=False, comment="来源")

    # 分类信息
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="分类")
    importance: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, comment="重要性"
    )

    # 发布信息
    published_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="发布时间")
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="原文链接")

    # 统计信息
    read_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="阅读次数")
    bookmark_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="收藏次数"
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )

    # 标签
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")


class NotificationSettings(BaseModel):
    """通知设置模型."""

    __tablename__ = "notification_settings"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="用户ID",
    )

    # 通知设置
    training_updates: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="培训更新通知"
    )
    community_replies: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="社区回复通知"
    )
    research_updates: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="研究动态通知"
    )
    certification_reminders: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="认证提醒通知"
    )
    email_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="邮件通知"
    )
    push_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="推送通知"
    )

    # 关系
    user: Mapped[User] = relationship("User")


class LearningProgress(BaseModel):
    """学习进度模型."""

    __tablename__ = "learning_progress"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )

    # 统计信息
    total_trainings: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="总培训数"
    )
    completed_trainings: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="完成培训数"
    )
    total_study_hours: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="总学习时长"
    )
    certifications_earned: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="获得认证数"
    )
    community_contributions: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="社区贡献数"
    )
    research_articles_read: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="阅读研究文章数"
    )

    # 最后更新时间
    last_updated_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, comment="最后更新时间"
    )

    # 关系
    user: Mapped[User] = relationship("User")
