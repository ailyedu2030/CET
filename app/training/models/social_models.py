"""学习社交与互动系统 - 数据模型"""

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


class PostType(str, Enum):
    """帖子类型枚举"""

    DISCUSSION = "discussion"  # 讨论
    QUESTION = "question"  # 问题
    SHARING = "sharing"  # 分享
    ANNOUNCEMENT = "announcement"  # 公告
    STUDY_GROUP = "study_group"  # 学习小组


class PostStatus(str, Enum):
    """帖子状态枚举"""

    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    HIDDEN = "hidden"  # 隐藏
    DELETED = "deleted"  # 已删除
    REPORTED = "reported"  # 被举报


class ReportReason(str, Enum):
    """举报原因枚举"""

    SPAM = "spam"  # 垃圾信息
    INAPPROPRIATE = "inappropriate"  # 不当内容
    HARASSMENT = "harassment"  # 骚扰
    COPYRIGHT = "copyright"  # 版权问题
    OTHER = "other"  # 其他


class MatchingStatus(str, Enum):
    """匹配状态枚举"""

    PENDING = "pending"  # 待处理
    MATCHED = "matched"  # 已匹配
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期


class DiscussionForumModel(BaseModel):
    """
    讨论区模型

    班级讨论区功能
    """

    __tablename__ = "discussion_forums"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False, comment="讨论区名称")
    description = Column(Text, comment="讨论区描述")
    category = Column(String(50), comment="分类")

    # 关联信息
    class_id = Column(
        Integer, ForeignKey("classes.id"), nullable=True, comment="班级ID"
    )
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=True, comment="课程ID"
    )

    # 权限设置
    is_public = Column(Boolean, default=True, comment="是否公开")
    allow_anonymous = Column(Boolean, default=False, comment="是否允许匿名")
    require_approval = Column(Boolean, default=False, comment="是否需要审核")

    # 统计信息
    post_count = Column(Integer, default=0, comment="帖子数量")
    member_count = Column(Integer, default=0, comment="成员数量")
    last_activity_at = Column(DateTime, comment="最后活动时间")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_archived = Column(Boolean, default=False, comment="是否归档")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    posts = relationship("ForumPostModel", back_populates="forum")

    def __repr__(self: "DiscussionForumModel") -> str:
        return f"<DiscussionForumModel(id={getattr(self, 'id', None)}, name={getattr(self, 'name', None)})>"


class ForumPostModel(BaseModel):
    """
    论坛帖子模型

    讨论区帖子内容
    """

    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    forum_id = Column(Integer, ForeignKey("discussion_forums.id"), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="发帖用户ID"
    )
    parent_id = Column(
        Integer, ForeignKey("forum_posts.id"), nullable=True, comment="父帖子ID"
    )

    # 内容信息
    title = Column(String(200), nullable=False, comment="帖子标题")
    content = Column(Text, nullable=False, comment="帖子内容")
    post_type = Column(String(20), nullable=False, comment="帖子类型")

    # 媒体内容
    attachments = Column(JSON, comment="附件列表")
    images = Column(JSON, comment="图片列表")

    # 标签和分类
    tags = Column(JSON, comment="标签列表")
    difficulty_level = Column(String(20), comment="难度等级")

    # 匿名设置
    is_anonymous = Column(Boolean, default=False, comment="是否匿名发布")
    anonymous_name = Column(String(50), comment="匿名昵称")

    # 互动统计
    view_count = Column(Integer, default=0, comment="查看次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    reply_count = Column(Integer, default=0, comment="回复数")
    share_count = Column(Integer, default=0, comment="分享数")

    # 质量评估
    quality_score = Column(Float, default=0.0, comment="质量评分")
    helpfulness_score = Column(Float, default=0.0, comment="有用性评分")

    # 状态
    status = Column(String(20), default=PostStatus.PUBLISHED, comment="帖子状态")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    is_featured = Column(Boolean, default=False, comment="是否精选")

    # 审核信息
    moderated_by = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID"
    )
    moderated_at = Column(DateTime, comment="审核时间")
    moderation_reason = Column(Text, comment="审核原因")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    forum = relationship("DiscussionForumModel", back_populates="posts")
    replies = relationship(
        "ForumPostModel",
        foreign_keys="ForumPostModel.parent_id",
        back_populates="parent",
    )
    parent = relationship(
        "ForumPostModel",
        foreign_keys=[parent_id],
        back_populates="replies",
        remote_side="ForumPostModel.id",
    )
    likes = relationship("PostLikeModel", back_populates="post")
    reports = relationship("PostReportModel", back_populates="post")

    def __repr__(self: "ForumPostModel") -> str:
        return f"<ForumPostModel(id={getattr(self, 'id', None)}, title={getattr(self, 'title', None)})>"


class PostLikeModel(BaseModel):
    """
    帖子点赞模型

    记录用户对帖子的点赞
    """

    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="点赞用户ID"
    )

    # 点赞类型
    like_type = Column(
        String(20), default="like", comment="点赞类型"
    )  # like, love, helpful, etc.

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    post = relationship("ForumPostModel", back_populates="likes")

    def __repr__(self: "PostLikeModel") -> str:
        return f"<PostLikeModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class PostReportModel(BaseModel):
    """
    帖子举报模型

    记录用户对帖子的举报
    """

    __tablename__ = "post_reports"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    reporter_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="举报人ID"
    )

    # 举报信息
    reason = Column(String(20), nullable=False, comment="举报原因")
    description = Column(Text, comment="举报描述")
    evidence = Column(JSON, comment="举报证据")

    # 处理信息
    status = Column(String(20), default="pending", comment="处理状态")
    handled_by = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="处理人ID"
    )
    handled_at = Column(DateTime, comment="处理时间")
    handling_result = Column(Text, comment="处理结果")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    post = relationship("ForumPostModel", back_populates="reports")

    def __repr__(self: "PostReportModel") -> str:
        return f"<PostReportModel(id={getattr(self, 'id', None)}, reason={getattr(self, 'reason', None)})>"


class StudyPartnerRequestModel(BaseModel):
    """
    学习伙伴请求模型

    学习伙伴匹配系统
    """

    __tablename__ = "study_partner_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="请求人ID"
    )

    # 匹配条件
    target_level = Column(String(20), comment="目标水平")
    study_goals = Column(JSON, comment="学习目标")
    preferred_schedule = Column(JSON, comment="偏好时间")
    study_style = Column(String(50), comment="学习风格")

    # 个人信息
    introduction = Column(Text, comment="自我介绍")
    interests = Column(JSON, comment="兴趣爱好")
    contact_preferences = Column(JSON, comment="联系偏好")

    # 匹配设置
    max_partners = Column(Integer, default=3, comment="最大伙伴数")
    auto_match = Column(Boolean, default=True, comment="是否自动匹配")
    location_preference = Column(String(100), comment="地区偏好")

    # 状态
    status = Column(String(20), default=MatchingStatus.PENDING, comment="匹配状态")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
    expires_at = Column(DateTime, comment="过期时间")

    # 关系
    matches = relationship(
        "StudyPartnerMatchModel", foreign_keys="StudyPartnerMatchModel.request_id"
    )

    def __repr__(self: "StudyPartnerRequestModel") -> str:
        return f"<StudyPartnerRequestModel(id={getattr(self, 'id', None)}, requester_id={getattr(self, 'requester_id', None)})>"


class StudyPartnerMatchModel(BaseModel):
    """
    学习伙伴匹配模型

    记录匹配结果
    """

    __tablename__ = "study_partner_matches"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        Integer, ForeignKey("study_partner_requests.id"), nullable=False
    )
    partner_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="匹配伙伴ID"
    )

    # 匹配信息
    match_score = Column(Float, nullable=False, comment="匹配度评分")
    match_reasons = Column(JSON, comment="匹配原因")
    compatibility_factors = Column(JSON, comment="兼容性因素")

    # 状态
    status = Column(String(20), default=MatchingStatus.PENDING, comment="匹配状态")
    accepted_by_requester = Column(Boolean, comment="请求人是否接受")
    accepted_by_partner = Column(Boolean, comment="伙伴是否接受")

    # 互动记录
    interaction_count = Column(Integer, default=0, comment="互动次数")
    last_interaction_at = Column(DateTime, comment="最后互动时间")
    satisfaction_rating = Column(Integer, comment="满意度评分(1-5)")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "StudyPartnerMatchModel") -> str:
        return f"<StudyPartnerMatchModel(id={getattr(self, 'id', None)}, match_score={getattr(self, 'match_score', None)})>"


class StudyGroupModel(BaseModel):
    """
    学习小组模型

    学习小组功能
    """

    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID"
    )

    # 基本信息
    name = Column(String(100), nullable=False, comment="小组名称")
    description = Column(Text, comment="小组描述")
    avatar_url = Column(String(500), comment="小组头像")

    # 学习信息
    study_topic = Column(String(100), comment="学习主题")
    target_level = Column(String(20), comment="目标水平")
    study_schedule = Column(JSON, comment="学习计划")

    # 小组设置
    max_members = Column(Integer, default=10, comment="最大成员数")
    is_public = Column(Boolean, default=True, comment="是否公开")
    require_approval = Column(Boolean, default=False, comment="是否需要审核")

    # 统计信息
    member_count = Column(Integer, default=1, comment="成员数量")
    activity_score = Column(Float, default=0.0, comment="活跃度评分")
    last_activity_at = Column(DateTime, comment="最后活动时间")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_archived = Column(Boolean, default=False, comment="是否归档")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    memberships = relationship("StudyGroupMembershipModel", back_populates="group")

    def __repr__(self: "StudyGroupModel") -> str:
        return f"<StudyGroupModel(id={getattr(self, 'id', None)}, name={getattr(self, 'name', None)})>"


class StudyGroupMembershipModel(BaseModel):
    """
    学习小组成员模型

    记录小组成员关系
    """

    __tablename__ = "study_group_memberships"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="成员用户ID"
    )

    # 成员角色
    role = Column(
        String(20), default="member", comment="成员角色"
    )  # creator, admin, member
    permissions = Column(JSON, comment="权限列表")

    # 加入信息
    invitation_code = Column(String(50), comment="邀请码")
    invited_by = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="邀请人ID"
    )

    # 活跃度
    participation_score = Column(Float, default=0.0, comment="参与度评分")
    contribution_count = Column(Integer, default=0, comment="贡献次数")
    last_active_at = Column(DateTime, comment="最后活跃时间")

    # 状态
    status = Column(String(20), default="active", comment="成员状态")
    is_muted = Column(Boolean, default=False, comment="是否被禁言")

    # 时间戳
    joined_at = Column(DateTime, default=datetime.utcnow, comment="加入时间")
    left_at = Column(DateTime, comment="离开时间")

    # 关系
    group = relationship("StudyGroupModel", back_populates="memberships")

    def __repr__(self: "StudyGroupMembershipModel") -> str:
        return f"<StudyGroupMembershipModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class MessageModel(BaseModel):
    """
    消息模型

    实时通信功能
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="发送者ID"
    )
    receiver_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="接收者ID"
    )
    group_id = Column(
        Integer, ForeignKey("study_groups.id"), nullable=True, comment="群组ID"
    )

    # 消息内容
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(20), default="text", comment="消息类型")
    attachments = Column(JSON, comment="附件列表")

    # 消息状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_deleted = Column(Boolean, default=False, comment="是否已删除")
    read_at = Column(DateTime, comment="阅读时间")

    # 回复信息
    reply_to_id = Column(
        Integer, ForeignKey("messages.id"), nullable=True, comment="回复消息ID"
    )

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    replies = relationship(
        "MessageModel",
        foreign_keys="MessageModel.reply_to_id",
        back_populates="reply_to",
    )
    reply_to = relationship(
        "MessageModel",
        foreign_keys=[reply_to_id],
        back_populates="replies",
        remote_side="MessageModel.id",
    )

    def __repr__(self: "MessageModel") -> str:
        return f"<MessageModel(id={getattr(self, 'id', None)}, sender_id={getattr(self, 'sender_id', None)})>"
