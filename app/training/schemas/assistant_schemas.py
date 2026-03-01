"""学习辅助工具系统 - 数据模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.training.models.assistant_models import (
    QuestionType,
    RecommendationSource,
    ResourceType,
)


# 知识库模式
class KnowledgeBaseCreate(BaseModel):
    """创建知识库的请求模式"""

    title: str = Field(..., description="知识标题", max_length=200)
    content: str = Field(..., description="知识内容")
    summary: str | None = Field(None, description="内容摘要")
    category: str | None = Field(None, description="知识分类", max_length=50)
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级", max_length=20)
    source_type: str | None = Field(None, description="来源类型", max_length=50)
    source_url: str | None = Field(None, description="来源URL", max_length=500)
    author: str | None = Field(None, description="作者", max_length=100)


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库的请求模式"""

    title: str | None = Field(None, description="知识标题", max_length=200)
    content: str | None = Field(None, description="知识内容")
    summary: str | None = Field(None, description="内容摘要")
    category: str | None = Field(None, description="知识分类", max_length=50)
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级", max_length=20)
    source_type: str | None = Field(None, description="来源类型", max_length=50)
    source_url: str | None = Field(None, description="来源URL", max_length=500)
    author: str | None = Field(None, description="作者", max_length=100)
    is_active: bool | None = Field(None, description="是否激活")
    is_verified: bool | None = Field(None, description="是否已验证")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应模式"""

    id: int = Field(..., description="ID")
    title: str = Field(..., description="知识标题")
    content: str = Field(..., description="知识内容")
    summary: str | None = Field(None, description="内容摘要")
    category: str | None = Field(None, description="知识分类")
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级")
    source_type: str | None = Field(None, description="来源类型")
    source_url: str | None = Field(None, description="来源URL")
    author: str | None = Field(None, description="作者")
    quality_score: float = Field(..., description="质量评分")
    relevance_score: float = Field(..., description="相关性评分")
    usage_count: int = Field(..., description="使用次数")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 问答模式
class QARequest(BaseModel):
    """问答请求模式"""

    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    question_type: QuestionType | None = Field(None, description="问题类型")
    context: dict[str, Any] | None = Field(None, description="上下文信息")
    session_id: str | None = Field(None, description="会话ID", max_length=100)


class QAResponse(BaseModel):
    """问答响应模式"""

    answer: str = Field(..., description="系统回答")
    confidence_score: float = Field(..., description="置信度评分")
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")
    related_resources: list[dict[str, Any]] | None = Field(None, description="相关资源")
    follow_up_questions: list[str] | None = Field(None, description="后续问题建议")
    sources: list[dict[str, Any]] | None = Field(None, description="信息来源")


class QARecordResponse(BaseModel):
    """问答记录响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="用户ID")
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="系统回答")
    question_type: QuestionType | None = Field(None, description="问题类型")
    context: dict[str, Any] | None = Field(None, description="上下文信息")
    session_id: str | None = Field(None, description="会话ID")
    ai_model_used: str | None = Field(None, description="使用的AI模型")
    processing_time_ms: int | None = Field(None, description="处理时间(毫秒)")
    confidence_score: float | None = Field(None, description="置信度评分")
    user_rating: int | None = Field(None, description="用户评分(1-5)")
    user_feedback: str | None = Field(None, description="用户反馈")
    is_helpful: bool | None = Field(None, description="是否有帮助")
    related_resources: list[dict[str, Any]] | None = Field(None, description="相关资源")
    follow_up_questions: list[str] | None = Field(None, description="后续问题建议")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class QAFeedback(BaseModel):
    """问答反馈模式"""

    user_rating: int = Field(..., description="用户评分(1-5)", ge=1, le=5)
    user_feedback: str | None = Field(None, description="用户反馈", max_length=500)
    is_helpful: bool = Field(..., description="是否有帮助")


# 学习资源模式
class LearningResourceCreate(BaseModel):
    """创建学习资源的请求模式"""

    title: str = Field(..., description="资源标题", max_length=200)
    description: str | None = Field(None, description="资源描述")
    resource_type: ResourceType = Field(..., description="资源类型")
    content_url: str | None = Field(None, description="资源URL", max_length=500)
    file_path: str | None = Field(None, description="文件路径", max_length=500)
    thumbnail_url: str | None = Field(None, description="缩略图URL", max_length=500)
    category: str | None = Field(None, description="资源分类", max_length=50)
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级", max_length=20)
    target_audience: list[str] | None = Field(None, description="目标受众")
    duration_minutes: int | None = Field(None, description="时长(分钟)", ge=0)
    language: str = Field(default="zh", description="语言", max_length=10)
    is_free: bool = Field(default=True, description="是否免费")


class LearningResourceUpdate(BaseModel):
    """更新学习资源的请求模式"""

    title: str | None = Field(None, description="资源标题", max_length=200)
    description: str | None = Field(None, description="资源描述")
    resource_type: ResourceType | None = Field(None, description="资源类型")
    content_url: str | None = Field(None, description="资源URL", max_length=500)
    file_path: str | None = Field(None, description="文件路径", max_length=500)
    thumbnail_url: str | None = Field(None, description="缩略图URL", max_length=500)
    category: str | None = Field(None, description="资源分类", max_length=50)
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级", max_length=20)
    target_audience: list[str] | None = Field(None, description="目标受众")
    duration_minutes: int | None = Field(None, description="时长(分钟)", ge=0)
    language: str | None = Field(None, description="语言", max_length=10)
    is_active: bool | None = Field(None, description="是否激活")
    is_featured: bool | None = Field(None, description="是否精选")
    is_free: bool | None = Field(None, description="是否免费")


class LearningResourceResponse(BaseModel):
    """学习资源响应模式"""

    id: int = Field(..., description="ID")
    title: str = Field(..., description="资源标题")
    description: str | None = Field(None, description="资源描述")
    resource_type: ResourceType = Field(..., description="资源类型")
    content_url: str | None = Field(None, description="资源URL")
    file_path: str | None = Field(None, description="文件路径")
    thumbnail_url: str | None = Field(None, description="缩略图URL")
    category: str | None = Field(None, description="资源分类")
    tags: list[str] | None = Field(None, description="标签列表")
    difficulty_level: str | None = Field(None, description="难度等级")
    target_audience: list[str] | None = Field(None, description="目标受众")
    duration_minutes: int | None = Field(None, description="时长(分钟)")
    file_size_mb: float | None = Field(None, description="文件大小(MB)")
    language: str = Field(..., description="语言")
    quality_score: float = Field(..., description="质量评分")
    popularity_score: float = Field(..., description="热度评分")
    view_count: int = Field(..., description="查看次数")
    download_count: int = Field(..., description="下载次数")
    recommendation_score: float = Field(..., description="推荐评分")
    recommendation_reasons: list[str] | None = Field(None, description="推荐理由")
    is_active: bool = Field(..., description="是否激活")
    is_featured: bool = Field(..., description="是否精选")
    is_free: bool = Field(..., description="是否免费")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 资源推荐模式
class ResourceRecommendationRequest(BaseModel):
    """资源推荐请求模式"""

    limit: int = Field(default=10, description="推荐数量", ge=1, le=50)
    category: str | None = Field(None, description="资源分类")
    difficulty_level: str | None = Field(None, description="难度等级")
    resource_type: ResourceType | None = Field(None, description="资源类型")
    exclude_viewed: bool = Field(default=True, description="排除已查看的资源")


class ResourceRecommendationResponse(BaseModel):
    """资源推荐响应模式"""

    resource: LearningResourceResponse = Field(..., description="推荐资源")
    recommendation_score: float = Field(..., description="推荐评分")
    recommendation_reason: str | None = Field(None, description="推荐理由")
    recommendation_source: RecommendationSource = Field(..., description="推荐来源")


# 语音识别模式
class VoiceRecognitionRequest(BaseModel):
    """语音识别请求模式"""

    audio_file: str = Field(..., description="音频文件路径或base64编码")
    exercise_type: str | None = Field(None, description="练习类型", max_length=50)
    target_text: str | None = Field(None, description="目标文本")
    language: str = Field(default="en", description="语言", max_length=10)


class VoiceRecognitionResponse(BaseModel):
    """语音识别响应模式"""

    recognized_text: str = Field(..., description="识别文本")
    confidence_score: float = Field(..., description="置信度评分")
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")
    pronunciation_score: float | None = Field(None, description="发音评分")
    fluency_score: float | None = Field(None, description="流利度评分")
    accuracy_score: float | None = Field(None, description="准确性评分")
    pronunciation_errors: list[dict[str, Any]] | None = Field(None, description="发音错误")
    grammar_errors: list[dict[str, Any]] | None = Field(None, description="语法错误")
    vocabulary_suggestions: list[dict[str, Any]] | None = Field(
        None, description="词汇建议"
    )
    improvement_suggestions: list[str] | None = Field(None, description="改进建议")
    practice_recommendations: list[dict[str, Any]] | None = Field(
        None, description="练习推荐"
    )


class VoiceRecognitionRecordResponse(BaseModel):
    """语音识别记录响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="用户ID")
    audio_file_path: str | None = Field(None, description="音频文件路径")
    audio_duration_seconds: float | None = Field(None, description="音频时长(秒)")
    audio_format: str | None = Field(None, description="音频格式")
    audio_quality: str | None = Field(None, description="音频质量")
    recognized_text: str | None = Field(None, description="识别文本")
    confidence_score: float | None = Field(None, description="置信度评分")
    processing_time_ms: int | None = Field(None, description="处理时间(毫秒)")
    pronunciation_score: float | None = Field(None, description="发音评分")
    fluency_score: float | None = Field(None, description="流利度评分")
    accuracy_score: float | None = Field(None, description="准确性评分")
    pronunciation_errors: list[dict[str, Any]] | None = Field(None, description="发音错误")
    grammar_errors: list[dict[str, Any]] | None = Field(None, description="语法错误")
    vocabulary_suggestions: list[dict[str, Any]] | None = Field(
        None, description="词汇建议"
    )
    improvement_suggestions: list[str] | None = Field(None, description="改进建议")
    practice_recommendations: list[dict[str, Any]] | None = Field(
        None, description="练习推荐"
    )
    exercise_type: str | None = Field(None, description="练习类型")
    target_text: str | None = Field(None, description="目标文本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 用户交互模式
class UserResourceInteractionCreate(BaseModel):
    """创建用户资源交互的请求模式"""

    resource_id: int = Field(..., description="资源ID")
    interaction_type: str = Field(..., description="交互类型", max_length=20)
    interaction_duration: int | None = Field(None, description="交互时长(秒)", ge=0)
    completion_rate: float | None = Field(None, description="完成率", ge=0.0, le=1.0)
    difficulty_rating: int | None = Field(None, description="难度评分(1-5)", ge=1, le=5)
    usefulness_rating: int | None = Field(None, description="有用性评分(1-5)", ge=1, le=5)


# 列表响应模式
class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[KnowledgeBaseResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class QARecordListResponse(BaseModel):
    """问答记录列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[QARecordResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class LearningResourceListResponse(BaseModel):
    """学习资源列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[LearningResourceResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class VoiceRecognitionRecordListResponse(BaseModel):
    """语音识别记录列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[VoiceRecognitionRecordResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
