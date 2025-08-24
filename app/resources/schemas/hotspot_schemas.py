"""热点资源池相关的Pydantic模式定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.shared.models.enums import ContentType, DifficultyLevel


class HotspotResourceBase(BaseModel):
    """热点资源基础模式."""

    title: str = Field(..., description="资源标题", max_length=300)
    source_type: str = Field(..., description="来源类型", max_length=50)
    source_url: str | None = Field(None, description="来源URL", max_length=500)
    author: str | None = Field(None, description="作者", max_length=200)
    publish_date: str | None = Field(None, description="发布日期")
    content_preview: str | None = Field(None, description="内容预览", max_length=1000)
    full_content: str | None = Field(None, description="完整内容")
    content_type: ContentType = Field(ContentType.TEXT, description="内容类型")
    language: str = Field("en", description="语言", max_length=10)
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.INTERMEDIATE, description="难度级别")
    topics: list[str] = Field(default_factory=list, description="话题标签")
    keywords: list[str] = Field(default_factory=list, description="关键词")
    vocabulary_highlights: list[dict[str, Any]] = Field(
        default_factory=list, description="重点词汇"
    )
    grammar_points: list[str] = Field(default_factory=list, description="语法点")
    cultural_notes: str | None = Field(None, description="文化注释")
    comprehension_questions: list[dict[str, Any]] = Field(
        default_factory=list, description="理解问题"
    )
    discussion_topics: list[str] = Field(default_factory=list, description="讨论话题")


class HotspotResourceCreate(HotspotResourceBase):
    """创建热点资源的请求模式."""

    library_id: int = Field(..., description="资源库ID")


class HotspotResourceUpdate(BaseModel):
    """更新热点资源的请求模式."""

    title: str | None = Field(None, description="资源标题", max_length=300)
    source_type: str | None = Field(None, description="来源类型", max_length=50)
    source_url: str | None = Field(None, description="来源URL", max_length=500)
    author: str | None = Field(None, description="作者", max_length=200)
    content_preview: str | None = Field(None, description="内容预览", max_length=1000)
    full_content: str | None = Field(None, description="完整内容")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度级别")
    topics: list[str] | None = Field(None, description="话题标签")
    keywords: list[str] | None = Field(None, description="关键词")
    vocabulary_highlights: list[dict[str, Any]] | None = Field(None, description="重点词汇")
    grammar_points: list[str] | None = Field(None, description="语法点")
    cultural_notes: str | None = Field(None, description="文化注释")
    comprehension_questions: list[dict[str, Any]] | None = Field(None, description="理解问题")
    discussion_topics: list[str] | None = Field(None, description="讨论话题")
    is_recommended: bool | None = Field(None, description="是否推荐")
    recommendation_reason: str | None = Field(None, description="推荐理由")
    expiry_date: str | None = Field(None, description="过期日期")


class HotspotResourceResponse(HotspotResourceBase):
    """热点资源响应模式."""

    id: int = Field(..., description="资源ID")
    library_id: int = Field(..., description="资源库ID")
    popularity_score: float = Field(..., description="热度分数")
    relevance_score: float = Field(..., description="相关性分数")
    view_count: int = Field(..., description="查看次数")
    like_count: int = Field(..., description="点赞次数")
    share_count: int = Field(..., description="分享次数")
    engagement_rate: float = Field(..., description="参与度")
    is_trending: bool = Field(..., description="是否热门")
    is_recommended: bool = Field(..., description="是否推荐")
    recommendation_reason: str | None = Field(None, description="推荐理由")
    expiry_date: str | None = Field(None, description="过期日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


class HotspotResourceSearchRequest(BaseModel):
    """热点资源搜索请求模式."""

    library_id: int | None = Field(None, description="资源库ID")
    keyword: str | None = Field(None, description="关键词搜索", max_length=100)
    source_type: str | None = Field(None, description="来源类型")
    language: str | None = Field(None, description="语言")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度级别")
    topics: list[str] | None = Field(None, description="话题筛选")
    is_trending: bool | None = Field(None, description="是否热门")
    is_recommended: bool | None = Field(None, description="是否推荐")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页大小", ge=1, le=100)


class RSSFeedCreate(BaseModel):
    """RSS订阅源创建请求模式."""

    name: str = Field(..., description="订阅源名称", max_length=200)
    url: str = Field(..., description="RSS URL", max_length=500)
    description: str | None = Field(None, description="描述", max_length=1000)
    language: str = Field("en", description="语言", max_length=10)
    category: str | None = Field(None, description="分类", max_length=100)
    is_active: bool = Field(True, description="是否启用")
    update_frequency: int = Field(60, description="更新频率（分钟）", ge=30, le=1440)


class RSSFeedResponse(BaseModel):
    """RSS订阅源响应模式."""

    id: int = Field(..., description="订阅源ID")
    name: str = Field(..., description="订阅源名称")
    url: str = Field(..., description="RSS URL")
    description: str | None = Field(None, description="描述")
    language: str = Field(..., description="语言")
    category: str | None = Field(None, description="分类")
    is_active: bool = Field(..., description="是否启用")
    update_frequency: int = Field(..., description="更新频率（分钟）")
    last_updated: datetime | None = Field(None, description="最后更新时间")
    total_items: int = Field(..., description="总条目数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


class DailyRecommendationResponse(BaseModel):
    """每日推荐响应模式."""

    date: str = Field(..., description="推荐日期")
    library_id: int = Field(..., description="资源库ID")
    recommended_resources: list[HotspotResourceResponse] = Field(..., description="推荐资源列表")
    trending_resources: list[HotspotResourceResponse] = Field(..., description="热门资源列表")
    total_count: int = Field(..., description="总数量")
    generated_at: datetime = Field(..., description="生成时间")


class HotspotInteractionRequest(BaseModel):
    """热点资源交互请求模式."""

    interaction_type: str = Field(..., description="交互类型", max_length=50)
    metadata: dict[str, Any] | None = Field(None, description="交互元数据")


class HotspotAnalyticsResponse(BaseModel):
    """热点资源分析响应模式."""

    resource_id: int = Field(..., description="资源ID")
    total_views: int = Field(..., description="总查看次数")
    total_likes: int = Field(..., description="总点赞次数")
    total_shares: int = Field(..., description="总分享次数")
    engagement_rate: float = Field(..., description="参与度")
    popularity_trend: list[dict[str, Any]] = Field(..., description="热度趋势")
    user_feedback: list[dict[str, Any]] = Field(..., description="用户反馈")
    performance_score: float = Field(..., description="表现评分")


class HotspotCollectionRequest(BaseModel):
    """热点资源收集请求模式."""

    max_items_per_feed: int = Field(5, description="每个源的最大条目数", ge=1, le=20)
    target_language: str = Field("en", description="目标语言")
    difficulty_filter: DifficultyLevel | None = Field(None, description="难度筛选")
    topic_filter: list[str] | None = Field(None, description="话题筛选")
    auto_save: bool = Field(True, description="是否自动保存")


class HotspotCollectionResponse(BaseModel):
    """热点资源收集响应模式."""

    success: bool = Field(..., description="是否成功")
    collected_count: int = Field(..., description="收集数量")
    saved_count: int = Field(..., description="保存数量")
    failed_count: int = Field(..., description="失败数量")
    resources: list[dict[str, Any]] = Field(..., description="资源预览")
    errors: list[str] = Field(default_factory=list, description="错误信息")
    timestamp: datetime = Field(..., description="收集时间")
