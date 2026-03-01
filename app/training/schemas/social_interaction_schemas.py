"""学习社交与互动系统 - 数据模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.training.models.social_models import MatchingStatus, PostStatus, PostType, ReportReason


# 讨论区模式
class DiscussionForumCreate(BaseModel):
    """创建讨论区的请求模式"""

    name: str = Field(..., description="讨论区名称", max_length=100)
    description: str | None = Field(None, description="讨论区描述")
    category: str | None = Field(None, description="分类", max_length=50)
    class_id: int | None = Field(None, description="班级ID")
    course_id: int | None = Field(None, description="课程ID")
    is_public: bool = Field(default=True, description="是否公开")
    allow_anonymous: bool = Field(default=False, description="是否允许匿名")
    require_approval: bool = Field(default=False, description="是否需要审核")


class DiscussionForumUpdate(BaseModel):
    """更新讨论区的请求模式"""

    name: str | None = Field(None, description="讨论区名称", max_length=100)
    description: str | None = Field(None, description="讨论区描述")
    category: str | None = Field(None, description="分类", max_length=50)
    is_public: bool | None = Field(None, description="是否公开")
    allow_anonymous: bool | None = Field(None, description="是否允许匿名")
    require_approval: bool | None = Field(None, description="是否需要审核")
    is_active: bool | None = Field(None, description="是否激活")
    is_archived: bool | None = Field(None, description="是否归档")


class DiscussionForumResponse(BaseModel):
    """讨论区响应模式"""

    id: int = Field(..., description="ID")
    name: str = Field(..., description="讨论区名称")
    description: str | None = Field(None, description="讨论区描述")
    category: str | None = Field(None, description="分类")
    class_id: int | None = Field(None, description="班级ID")
    course_id: int | None = Field(None, description="课程ID")
    is_public: bool = Field(..., description="是否公开")
    allow_anonymous: bool = Field(..., description="是否允许匿名")
    require_approval: bool = Field(..., description="是否需要审核")
    post_count: int = Field(..., description="帖子数量")
    member_count: int = Field(..., description="成员数量")
    last_activity_at: datetime | None = Field(None, description="最后活动时间")
    is_active: bool = Field(..., description="是否激活")
    is_archived: bool = Field(..., description="是否归档")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 论坛帖子模式
class ForumPostCreate(BaseModel):
    """创建论坛帖子的请求模式"""

    forum_id: int = Field(..., description="讨论区ID")
    parent_id: int | None = Field(None, description="父帖子ID")
    title: str = Field(..., description="帖子标题", max_length=200)
    content: str = Field(..., description="帖子内容", min_length=1)
    post_type: PostType = Field(..., description="帖子类型")
    attachments: list[str] | None = Field(None, description="附件列表")
    images: list[str] | None = Field(None, description="图片列表")
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级", max_length=20)
    is_anonymous: bool = Field(default=False, description="是否匿名发布")
    anonymous_name: str | None = Field(None, description="匿名昵称", max_length=50)


class ForumPostUpdate(BaseModel):
    """更新论坛帖子的请求模式"""

    title: str | None = Field(None, description="帖子标题", max_length=200)
    content: str | None = Field(None, description="帖子内容")
    post_type: PostType | None = Field(None, description="帖子类型")
    attachments: list[str] | None = Field(None, description="附件列表")
    images: list[str] | None = Field(None, description="图片列表")
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级", max_length=20)
    status: PostStatus | None = Field(None, description="帖子状态")
    is_pinned: bool | None = Field(None, description="是否置顶")
    is_featured: bool | None = Field(None, description="是否精选")


class ForumPostResponse(BaseModel):
    """论坛帖子响应模式"""

    id: int = Field(..., description="ID")
    forum_id: int = Field(..., description="讨论区ID")
    user_id: int = Field(..., description="发帖用户ID")
    parent_id: int | None = Field(None, description="父帖子ID")
    title: str = Field(..., description="帖子标题")
    content: str = Field(..., description="帖子内容")
    post_type: PostType = Field(..., description="帖子类型")
    attachments: list[str] | None = Field(None, description="附件列表")
    images: list[str] | None = Field(None, description="图片列表")
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级")
    is_anonymous: bool = Field(..., description="是否匿名发布")
    anonymous_name: str | None = Field(None, description="匿名昵称")
    view_count: int = Field(..., description="查看次数")
    like_count: int = Field(..., description="点赞数")
    reply_count: int = Field(..., description="回复数")
    share_count: int = Field(..., description="分享数")
    quality_score: float = Field(..., description="质量评分")
    helpfulness_score: float = Field(..., description="有用性评分")
    status: PostStatus = Field(..., description="帖子状态")
    is_pinned: bool = Field(..., description="是否置顶")
    is_featured: bool = Field(..., description="是否精选")
    moderated_by: int | None = Field(None, description="审核人ID")
    moderated_at: datetime | None = Field(None, description="审核时间")
    moderation_reason: str | None = Field(None, description="审核原因")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 帖子点赞模式
class PostLikeCreate(BaseModel):
    """创建帖子点赞的请求模式"""

    post_id: int = Field(..., description="帖子ID")
    like_type: str = Field(default="like", description="点赞类型", max_length=20)


class PostLikeResponse(BaseModel):
    """帖子点赞响应模式"""

    id: int = Field(..., description="ID")
    post_id: int = Field(..., description="帖子ID")
    user_id: int = Field(..., description="点赞用户ID")
    like_type: str = Field(..., description="点赞类型")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# 帖子举报模式
class PostReportCreate(BaseModel):
    """创建帖子举报的请求模式"""

    post_id: int = Field(..., description="帖子ID")
    reason: ReportReason = Field(..., description="举报原因")
    description: str | None = Field(None, description="举报描述", max_length=500)
    evidence: list[str] | None = Field(None, description="举报证据")


class PostReportResponse(BaseModel):
    """帖子举报响应模式"""

    id: int = Field(..., description="ID")
    post_id: int = Field(..., description="帖子ID")
    reporter_id: int = Field(..., description="举报人ID")
    reason: ReportReason = Field(..., description="举报原因")
    description: str | None = Field(None, description="举报描述")
    evidence: list[str] | None = Field(None, description="举报证据")
    status: str = Field(..., description="处理状态")
    handled_by: int | None = Field(None, description="处理人ID")
    handled_at: datetime | None = Field(None, description="处理时间")
    handling_result: str | None = Field(None, description="处理结果")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 学习伙伴模式
class StudyPartnerRequestCreate(BaseModel):
    """创建学习伙伴请求的请求模式"""

    target_level: str | None = Field(None, description="目标水平", max_length=20)
    study_goals: list[str] | None = Field(None, description="学习目标")
    preferred_schedule: dict[str, Any] | None = Field(None, description="偏好时间")
    study_style: str | None = Field(None, description="学习风格", max_length=50)
    introduction: str | None = Field(None, description="自我介绍", max_length=500)
    interests: list[str] | None = Field(None, description="兴趣爱好")
    contact_preferences: dict[str, Any] | None = Field(None, description="联系偏好")
    max_partners: int = Field(default=3, description="最大伙伴数", ge=1, le=10)
    auto_match: bool = Field(default=True, description="是否自动匹配")
    location_preference: str | None = Field(None, description="地区偏好", max_length=100)


class StudyPartnerRequestUpdate(BaseModel):
    """更新学习伙伴请求的请求模式"""

    target_level: str | None = Field(None, description="目标水平", max_length=20)
    study_goals: list[str] | None = Field(None, description="学习目标")
    preferred_schedule: dict[str, Any] | None = Field(None, description="偏好时间")
    study_style: str | None = Field(None, description="学习风格", max_length=50)
    introduction: str | None = Field(None, description="自我介绍", max_length=500)
    interests: list[str] | None = Field(None, description="兴趣爱好")
    contact_preferences: dict[str, Any] | None = Field(None, description="联系偏好")
    max_partners: int | None = Field(None, description="最大伙伴数", ge=1, le=10)
    auto_match: bool | None = Field(None, description="是否自动匹配")
    location_preference: str | None = Field(None, description="地区偏好", max_length=100)
    status: MatchingStatus | None = Field(None, description="匹配状态")
    is_active: bool | None = Field(None, description="是否激活")


class StudyPartnerRequestResponse(BaseModel):
    """学习伙伴请求响应模式"""

    id: int = Field(..., description="ID")
    requester_id: int = Field(..., description="请求人ID")
    target_level: str | None = Field(None, description="目标水平")
    study_goals: list[str] | None = Field(None, description="学习目标")
    preferred_schedule: dict[str, Any] | None = Field(None, description="偏好时间")
    study_style: str | None = Field(None, description="学习风格")
    introduction: str | None = Field(None, description="自我介绍")
    interests: list[str] | None = Field(None, description="兴趣爱好")
    contact_preferences: dict[str, Any] | None = Field(None, description="联系偏好")
    max_partners: int = Field(..., description="最大伙伴数")
    auto_match: bool = Field(..., description="是否自动匹配")
    location_preference: str | None = Field(None, description="地区偏好")
    status: MatchingStatus = Field(..., description="匹配状态")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    expires_at: datetime | None = Field(None, description="过期时间")

    class Config:
        from_attributes = True


class StudyPartnerMatchResponse(BaseModel):
    """学习伙伴匹配响应模式"""

    id: int = Field(..., description="ID")
    request_id: int = Field(..., description="请求ID")
    partner_id: int = Field(..., description="匹配伙伴ID")
    match_score: float = Field(..., description="匹配度评分")
    match_reasons: list[str] | None = Field(None, description="匹配原因")
    compatibility_factors: dict[str, Any] | None = Field(None, description="兼容性因素")
    status: MatchingStatus = Field(..., description="匹配状态")
    accepted_by_requester: bool | None = Field(None, description="请求人是否接受")
    accepted_by_partner: bool | None = Field(None, description="伙伴是否接受")
    interaction_count: int = Field(..., description="互动次数")
    last_interaction_at: datetime | None = Field(None, description="最后互动时间")
    satisfaction_rating: int | None = Field(None, description="满意度评分(1-5)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 学习小组模式
class StudyGroupCreate(BaseModel):
    """创建学习小组的请求模式"""

    name: str = Field(..., description="小组名称", max_length=100)
    description: str | None = Field(None, description="小组描述", max_length=500)
    avatar_url: str | None = Field(None, description="小组头像", max_length=500)
    study_topic: str | None = Field(None, description="学习主题", max_length=100)
    target_level: str | None = Field(None, description="目标水平", max_length=20)
    study_schedule: dict[str, Any] | None = Field(None, description="学习计划")
    max_members: int = Field(default=10, description="最大成员数", ge=2, le=50)
    is_public: bool = Field(default=True, description="是否公开")
    require_approval: bool = Field(default=False, description="是否需要审核")


class StudyGroupUpdate(BaseModel):
    """更新学习小组的请求模式"""

    name: str | None = Field(None, description="小组名称", max_length=100)
    description: str | None = Field(None, description="小组描述", max_length=500)
    avatar_url: str | None = Field(None, description="小组头像", max_length=500)
    study_topic: str | None = Field(None, description="学习主题", max_length=100)
    target_level: str | None = Field(None, description="目标水平", max_length=20)
    study_schedule: dict[str, Any] | None = Field(None, description="学习计划")
    max_members: int | None = Field(None, description="最大成员数", ge=2, le=50)
    is_public: bool | None = Field(None, description="是否公开")
    require_approval: bool | None = Field(None, description="是否需要审核")
    is_active: bool | None = Field(None, description="是否激活")
    is_archived: bool | None = Field(None, description="是否归档")


class StudyGroupResponse(BaseModel):
    """学习小组响应模式"""

    id: int = Field(..., description="ID")
    creator_id: int = Field(..., description="创建者ID")
    name: str = Field(..., description="小组名称")
    description: str | None = Field(None, description="小组描述")
    avatar_url: str | None = Field(None, description="小组头像")
    study_topic: str | None = Field(None, description="学习主题")
    target_level: str | None = Field(None, description="目标水平")
    study_schedule: dict[str, Any] | None = Field(None, description="学习计划")
    max_members: int = Field(..., description="最大成员数")
    is_public: bool = Field(..., description="是否公开")
    require_approval: bool = Field(..., description="是否需要审核")
    member_count: int = Field(..., description="成员数量")
    activity_score: float = Field(..., description="活跃度评分")
    last_activity_at: datetime | None = Field(None, description="最后活动时间")
    is_active: bool = Field(..., description="是否激活")
    is_archived: bool = Field(..., description="是否归档")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 消息模式
class MessageCreate(BaseModel):
    """创建消息的请求模式"""

    receiver_id: int | None = Field(None, description="接收者ID")
    group_id: int | None = Field(None, description="群组ID")
    content: str = Field(..., description="消息内容", min_length=1, max_length=1000)
    message_type: str = Field(default="text", description="消息类型", max_length=20)
    attachments: list[str] | None = Field(None, description="附件列表")
    reply_to_id: int | None = Field(None, description="回复消息ID")


class MessageResponse(BaseModel):
    """消息响应模式"""

    id: int = Field(..., description="ID")
    sender_id: int = Field(..., description="发送者ID")
    receiver_id: int | None = Field(None, description="接收者ID")
    group_id: int | None = Field(None, description="群组ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(..., description="消息类型")
    attachments: list[str] | None = Field(None, description="附件列表")
    is_read: bool = Field(..., description="是否已读")
    is_deleted: bool = Field(..., description="是否已删除")
    read_at: datetime | None = Field(None, description="阅读时间")
    reply_to_id: int | None = Field(None, description="回复消息ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 列表响应模式
class DiscussionForumListResponse(BaseModel):
    """讨论区列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[DiscussionForumResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ForumPostListResponse(BaseModel):
    """论坛帖子列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[ForumPostResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class StudyPartnerRequestListResponse(BaseModel):
    """学习伙伴请求列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[StudyPartnerRequestResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class StudyGroupListResponse(BaseModel):
    """学习小组列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[StudyGroupResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class MessageListResponse(BaseModel):
    """消息列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[MessageResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
