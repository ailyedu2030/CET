"""专业发展支持Schema定义 - 需求17实现."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =================== 培训资源相关Schema ===================


class TrainingResourceBase(BaseModel):
    """培训资源基础Schema."""

    title: str = Field(..., description="培训标题")
    description: str = Field(..., description="培训描述")
    category: str = Field(..., description="培训分类")
    duration: str = Field(..., description="培训时长")
    difficulty: str = Field(..., description="难度等级")
    instructor: str = Field(..., description="讲师姓名")
    tags: list[str] = Field(default_factory=list, description="标签")


class TrainingResourceResponse(TrainingResourceBase):
    """培训资源响应Schema."""

    id: int = Field(..., description="培训ID")
    content_url: str | None = Field(None, description="内容链接")
    materials: list[dict[str, Any]] = Field(default_factory=list, description="培训材料")
    objectives: list[str] = Field(default_factory=list, description="学习目标")
    prerequisites: list[str] = Field(default_factory=list, description="前置要求")
    enrolled_count: int = Field(0, description="报名人数")
    rating: float = Field(0.0, description="评分")
    rating_count: int = Field(0, description="评分人数")
    is_active: bool = Field(True, description="是否激活")
    is_featured: bool = Field(False, description="是否推荐")
    is_enrolled: bool = Field(False, description="是否已报名")
    progress: float = Field(0.0, description="学习进度")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


class TrainingEnrollmentCreate(BaseModel):
    """培训报名创建Schema."""

    motivation: str | None = Field(None, description="报名动机")


class TrainingProgressResponse(BaseModel):
    """培训进度响应Schema."""

    progress: float = Field(..., description="学习进度")
    completed_lessons: int = Field(..., description="完成课程数")
    total_lessons: int = Field(..., description="总课程数")
    last_accessed_at: datetime | None = Field(None, description="最后访问时间")


# =================== 认证材料相关Schema ===================


class CertificationMaterialBase(BaseModel):
    """认证材料基础Schema."""

    title: str = Field(..., description="材料标题")
    description: str = Field(..., description="材料描述")
    type: str = Field(..., description="材料类型")
    category: str = Field(..., description="认证分类")
    tags: list[str] = Field(default_factory=list, description="标签")


class CertificationMaterialResponse(CertificationMaterialBase):
    """认证材料响应Schema."""

    id: int = Field(..., description="材料ID")
    file_url: str | None = Field(None, description="文件链接")
    file_size: int | None = Field(None, description="文件大小")
    file_format: str | None = Field(None, description="文件格式")
    download_count: int = Field(0, description="下载次数")
    rating: float = Field(0.0, description="评分")
    rating_count: int = Field(0, description="评分人数")
    is_active: bool = Field(True, description="是否激活")
    is_free: bool = Field(True, description="是否免费")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# =================== 社区交流相关Schema ===================


class UserInfo(BaseModel):
    """用户信息Schema."""

    id: int = Field(..., description="用户ID")
    name: str = Field(..., description="用户姓名")
    avatar: str | None = Field(None, description="头像")
    title: str | None = Field(None, description="职称")


class CommunityPostBase(BaseModel):
    """社区帖子基础Schema."""

    title: str = Field(..., description="帖子标题")
    content: str = Field(..., description="帖子内容")
    category: str = Field(..., description="帖子分类")
    tags: list[str] = Field(default_factory=list, description="标签")


class CommunityPostCreate(CommunityPostBase):
    """社区帖子创建Schema."""

    pass


class CommunityPostResponse(CommunityPostBase):
    """社区帖子响应Schema."""

    id: int = Field(..., description="帖子ID")
    author: UserInfo = Field(..., description="作者信息")
    likes: int = Field(0, description="点赞数")
    replies: int = Field(0, description="回复数")
    views: int = Field(0, description="浏览数")
    is_pinned: bool = Field(False, description="是否置顶")
    is_locked: bool = Field(False, description="是否锁定")
    is_featured: bool = Field(False, description="是否精华")
    is_liked: bool = Field(False, description="是否已点赞")
    is_bookmarked: bool = Field(False, description="是否已收藏")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


class CommunityReplyBase(BaseModel):
    """社区回复基础Schema."""

    content: str = Field(..., description="回复内容")


class CommunityReplyCreate(CommunityReplyBase):
    """社区回复创建Schema."""

    pass


class CommunityReplyResponse(CommunityReplyBase):
    """社区回复响应Schema."""

    id: int = Field(..., description="回复ID")
    post_id: int = Field(..., description="帖子ID")
    author: UserInfo = Field(..., description="作者信息")
    likes: int = Field(0, description="点赞数")
    reply_to_id: int | None = Field(None, description="回复的回复ID")
    is_liked: bool = Field(False, description="是否已点赞")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# =================== 研究动态相关Schema ===================


class ResearchUpdateBase(BaseModel):
    """研究动态基础Schema."""

    title: str = Field(..., description="标题")
    summary: str = Field(..., description="摘要")
    source: str = Field(..., description="来源")
    category: str = Field(..., description="分类")
    importance: str = Field(..., description="重要性")
    tags: list[str] = Field(default_factory=list, description="标签")


class ResearchUpdateResponse(ResearchUpdateBase):
    """研究动态响应Schema."""

    id: int = Field(..., description="动态ID")
    full_content: str | None = Field(None, description="全文内容")
    published_at: datetime = Field(..., description="发布时间")
    source_url: str | None = Field(None, description="原文链接")
    read_count: int = Field(0, description="阅读次数")
    bookmark_count: int = Field(0, description="收藏次数")
    is_active: bool = Field(True, description="是否激活")
    is_bookmarked: bool = Field(False, description="是否已收藏")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# =================== 通知设置相关Schema ===================


class NotificationSettingsBase(BaseModel):
    """通知设置基础Schema."""

    training_updates: bool = Field(True, description="培训更新通知")
    community_replies: bool = Field(True, description="社区回复通知")
    research_updates: bool = Field(True, description="研究动态通知")
    certification_reminders: bool = Field(True, description="认证提醒通知")
    email_notifications: bool = Field(True, description="邮件通知")
    push_notifications: bool = Field(True, description="推送通知")


class NotificationSettingsUpdate(NotificationSettingsBase):
    """通知设置更新Schema."""

    pass


class NotificationSettingsResponse(NotificationSettingsBase):
    """通知设置响应Schema."""

    id: int = Field(..., description="设置ID")
    user_id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# =================== 学习统计相关Schema ===================


class LearningStatsResponse(BaseModel):
    """学习统计响应Schema."""

    total_trainings: int = Field(0, description="总培训数")
    completed_trainings: int = Field(0, description="完成培训数")
    total_study_hours: float = Field(0.0, description="总学习时长")
    certifications_earned: int = Field(0, description="获得认证数")
    community_contributions: int = Field(0, description="社区贡献数")
    research_articles_read: int = Field(0, description="阅读研究文章数")
    completion_rate: float = Field(0.0, description="完成率")
    average_rating: float = Field(0.0, description="平均评分")


# =================== 推荐相关Schema ===================


class RecommendationResponse(BaseModel):
    """推荐响应Schema."""

    recommended_trainings: list[TrainingResourceResponse] = Field(
        default_factory=list, description="推荐培训"
    )
    recommended_materials: list[CertificationMaterialResponse] = Field(
        default_factory=list, description="推荐材料"
    )
    recommended_posts: list[CommunityPostResponse] = Field(
        default_factory=list, description="推荐帖子"
    )
    recommended_research: list[ResearchUpdateResponse] = Field(
        default_factory=list, description="推荐研究"
    )


# =================== 分页响应Schema ===================


class PaginatedTrainingResourceResponse(BaseModel):
    """分页培训资源响应Schema."""

    resources: list[TrainingResourceResponse] = Field(..., description="培训资源列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    categories: list[str] = Field(default_factory=list, description="分类列表")


class PaginatedCertificationMaterialResponse(BaseModel):
    """分页认证材料响应Schema."""

    materials: list[CertificationMaterialResponse] = Field(..., description="认证材料列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    categories: list[str] = Field(default_factory=list, description="分类列表")


class PaginatedCommunityPostResponse(BaseModel):
    """分页社区帖子响应Schema."""

    posts: list[CommunityPostResponse] = Field(..., description="帖子列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    categories: list[str] = Field(default_factory=list, description="分类列表")


class PaginatedResearchUpdateResponse(BaseModel):
    """分页研究动态响应Schema."""

    updates: list[ResearchUpdateResponse] = Field(..., description="研究动态列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    categories: list[str] = Field(default_factory=list, description="分类列表")
