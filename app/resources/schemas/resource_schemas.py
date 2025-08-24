"""教学资源库Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.shared.models.enums import (
    ContentType,
    DifficultyLevel,
    PermissionType,
)


# ========== 资源库基础schemas ==========
class ResourceLibraryBase(BaseModel):
    """资源库基础schema."""

    name: str = Field(..., description="资源库名称")
    description: str | None = Field(None, description="资源库描述")
    version: str = Field(default="1.0.0", description="版本号")
    is_active: bool = Field(default=True, description="是否激活")
    is_public: bool = Field(default=False, description="是否公开")


class ResourceLibraryCreate(ResourceLibraryBase):
    """创建资源库schema."""

    course_id: int = Field(..., description="课程ID")


class ResourceLibraryUpdate(ResourceLibraryBase):
    """更新资源库schema."""

    name: str | None = Field(None, description="资源库名称")


class ResourceLibraryResponse(ResourceLibraryBase):
    """资源库响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="资源库ID")
    course_id: int = Field(..., description="课程ID")
    total_items: int = Field(..., description="总资源数量")
    last_updated: datetime | None = Field(None, description="最后更新时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ResourceLibraryListResponse(BaseModel):
    """资源库列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    items: list[ResourceLibraryResponse] = Field(..., description="资源库列表")


# ========== 词汇库schemas ==========
class VocabularyItemBase(BaseModel):
    """词汇条目基础schema."""

    word: str = Field(..., description="单词")
    pronunciation: str | None = Field(None, description="音标")
    part_of_speech: str | None = Field(None, description="词性")
    chinese_meaning: str = Field(..., description="中文释义")
    english_meaning: str | None = Field(None, description="英文释义")
    example_sentences: list[dict[str, Any]] = Field(default_factory=list, description="例句列表")
    synonyms: list[str] = Field(default_factory=list, description="同义词")
    antonyms: list[str] = Field(default_factory=list, description="反义词")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE, description="难度等级"
    )
    frequency: int = Field(default=0, description="使用频率")
    tags: list[str] = Field(default_factory=list, description="标签")
    audio_url: str | None = Field(None, description="音频URL")
    image_url: str | None = Field(None, description="图片URL")
    learning_tips: str | None = Field(None, description="学习提示")
    is_key_word: bool = Field(default=False, description="是否关键词")


class VocabularyItemCreate(VocabularyItemBase):
    """创建词汇条目schema."""

    library_id: int = Field(..., description="资源库ID")


class VocabularyItemUpdate(VocabularyItemBase):
    """更新词汇条目schema."""

    word: str | None = Field(None, description="单词")
    chinese_meaning: str | None = Field(None, description="中文释义")


class VocabularyItemResponse(VocabularyItemBase):
    """词汇条目响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="词汇ID")
    library_id: int = Field(..., description="资源库ID")
    review_count: int = Field(..., description="复习次数")
    mastery_level: float = Field(..., description="掌握程度")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class VocabularyBatchImport(BaseModel):
    """词汇批量导入schema."""

    library_id: int = Field(..., description="资源库ID")
    items: list[VocabularyItemBase] = Field(..., description="词汇列表")
    overwrite_existing: bool = Field(default=False, description="是否覆盖已存在的词汇")


class VocabularySearchRequest(BaseModel):
    """词汇搜索请求schema."""

    library_id: int | None = Field(None, description="资源库ID")
    keyword: str | None = Field(None, description="关键词")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    tags: list[str] = Field(default_factory=list, description="标签筛选")
    is_key_word: bool | None = Field(None, description="是否只搜索关键词")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")
    page: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页数量", ge=1, le=100)


class VocabularyListResponse(BaseModel):
    """词汇列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    items: list[VocabularyItemResponse] = Field(..., description="词汇列表")


# ========== 知识点库schemas ==========
class KnowledgePointBase(BaseModel):
    """知识点基础schema."""

    title: str = Field(..., description="知识点标题")
    category: str | None = Field(None, description="知识点分类")
    content: str = Field(..., description="知识点内容")
    description: str | None = Field(None, description="详细描述")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE, description="难度等级"
    )
    importance_score: float = Field(default=0.5, description="重要性分数", ge=0, le=1)
    learning_objectives: list[str] = Field(default_factory=list, description="学习目标")
    prerequisite_points: list[int] = Field(default_factory=list, description="前置知识点ID列表")
    related_points: list[int] = Field(default_factory=list, description="相关知识点ID列表")
    examples: list[dict[str, Any]] = Field(default_factory=list, description="示例列表")
    exercises: list[dict[str, Any]] = Field(default_factory=list, description="练习题列表")
    resources: list[dict[str, Any]] = Field(default_factory=list, description="相关资源")
    tags: list[str] = Field(default_factory=list, description="标签")
    estimated_time: int = Field(default=30, description="预估学习时间(分钟)")
    is_core: bool = Field(default=False, description="是否核心知识点")
    review_frequency: int = Field(default=7, description="建议复习频率(天)")


class KnowledgePointCreate(KnowledgePointBase):
    """创建知识点schema."""

    library_id: int = Field(..., description="资源库ID")
    parent_id: int | None = Field(None, description="父知识点ID")


class KnowledgePointUpdate(KnowledgePointBase):
    """更新知识点schema."""

    title: str | None = Field(None, description="知识点标题")
    content: str | None = Field(None, description="知识点内容")


class KnowledgePointResponse(KnowledgePointBase):
    """知识点响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="知识点ID")
    library_id: int = Field(..., description="资源库ID")
    parent_id: int | None = Field(None, description="父知识点ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    children: list[KnowledgePointResponse] | None = Field(None, description="子知识点")


class KnowledgePointSearchRequest(BaseModel):
    """知识点搜索请求schema."""

    library_id: int | None = Field(None, description="资源库ID")
    keyword: str | None = Field(None, description="关键词")
    category: str | None = Field(None, description="分类")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    is_core: bool | None = Field(None, description="是否只搜索核心知识点")
    parent_id: int | None = Field(None, description="父知识点ID")
    tags: list[str] = Field(default_factory=list, description="标签筛选")
    sort_by: str = Field(default="importance_score", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")
    page: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页数量", ge=1, le=100)


class KnowledgePointListResponse(BaseModel):
    """知识点列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    items: list[KnowledgePointResponse] = Field(..., description="知识点列表")


# ========== 教材库schemas ==========
class TeachingMaterialBase(BaseModel):
    """教材基础schema."""

    title: str = Field(..., description="教材标题")
    authors: list[str] = Field(default_factory=list, description="作者列表")
    publisher: str | None = Field(None, description="出版社")
    publication_date: str | None = Field(None, description="出版日期")
    isbn: str | None = Field(None, description="ISBN")
    edition: str | None = Field(None, description="版本")
    language: str = Field(default="zh-CN", description="语言")
    content_type: ContentType = Field(default=ContentType.TEXT, description="内容类型")
    file_format: str | None = Field(None, description="文件格式")
    chapters: list[dict[str, Any]] = Field(default_factory=list, description="章节信息")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE, description="难度等级"
    )
    target_audience: str | None = Field(None, description="目标受众")
    learning_objectives: list[str] = Field(default_factory=list, description="学习目标")
    tags: list[str] = Field(default_factory=list, description="标签")
    is_primary: bool = Field(default=False, description="是否主教材")
    is_supplementary: bool = Field(default=True, description="是否辅助教材")


class TeachingMaterialCreate(TeachingMaterialBase):
    """创建教材schema."""

    library_id: int = Field(..., description="资源库ID")
    file_path: str | None = Field(None, description="文件路径")


class TeachingMaterialUpdate(TeachingMaterialBase):
    """更新教材schema."""

    title: str | None = Field(None, description="教材标题")


class TeachingMaterialResponse(TeachingMaterialBase):
    """教材响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="教材ID")
    library_id: int = Field(..., description="资源库ID")
    file_path: str | None = Field(None, description="文件路径")
    file_size: int = Field(..., description="文件大小")
    preview_url: str | None = Field(None, description="预览URL")
    download_url: str | None = Field(None, description="下载URL")
    usage_count: int = Field(..., description="使用次数")
    rating: float = Field(..., description="评分")
    review_count: int = Field(..., description="评价数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TeachingMaterialSearchRequest(BaseModel):
    """教材搜索请求schema."""

    library_id: int | None = Field(None, description="资源库ID")
    keyword: str | None = Field(None, description="关键词")
    authors: list[str] = Field(default_factory=list, description="作者筛选")
    publisher: str | None = Field(None, description="出版社")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    content_type: ContentType | None = Field(None, description="内容类型")
    is_primary: bool | None = Field(None, description="是否主教材")
    tags: list[str] = Field(default_factory=list, description="标签筛选")
    sort_by: str = Field(default="rating", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")
    page: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页数量", ge=1, le=100)


class TeachingMaterialListResponse(BaseModel):
    """教材列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    items: list[TeachingMaterialResponse] = Field(..., description="教材列表")


# ========== 考纲schemas ==========
class ExamSyllabusBase(BaseModel):
    """考纲基础schema."""

    title: str = Field(..., description="考纲标题")
    exam_type: str = Field(..., description="考试类型")
    exam_level: str | None = Field(None, description="考试级别")
    version: str = Field(default="1.0", description="版本号")
    effective_date: str | None = Field(None, description="生效日期")
    expiry_date: str | None = Field(None, description="失效日期")
    issuing_authority: str | None = Field(None, description="颁布机构")
    description: str | None = Field(None, description="考纲描述")
    exam_structure: dict[str, Any] = Field(default_factory=dict, description="考试结构")
    skill_requirements: dict[str, Any] = Field(default_factory=dict, description="技能要求")
    vocabulary_requirements: dict[str, Any] = Field(default_factory=dict, description="词汇要求")
    grammar_requirements: list[dict[str, Any]] = Field(default_factory=list, description="语法要求")
    topic_areas: list[dict[str, Any]] = Field(default_factory=list, description="话题领域")
    question_types: list[dict[str, Any]] = Field(default_factory=list, description="题型说明")
    scoring_criteria: dict[str, Any] = Field(default_factory=dict, description="评分标准")
    sample_papers: list[dict[str, Any]] = Field(default_factory=list, description="样卷信息")
    preparation_suggestions: list[str] = Field(default_factory=list, description="备考建议")
    tags: list[str] = Field(default_factory=list, description="标签")
    is_current: bool = Field(default=True, description="是否为当前版本")
    is_official: bool = Field(default=True, description="是否官方版本")


class ExamSyllabusCreate(ExamSyllabusBase):
    """创建考纲schema."""

    library_id: int = Field(..., description="资源库ID")


class ExamSyllabusUpdate(ExamSyllabusBase):
    """更新考纲schema."""

    title: str | None = Field(None, description="考纲标题")
    exam_type: str | None = Field(None, description="考试类型")


class ExamSyllabusResponse(ExamSyllabusBase):
    """考纲响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="考纲ID")
    library_id: int = Field(..., description="资源库ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ExamSyllabusListResponse(BaseModel):
    """考纲列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    items: list[ExamSyllabusResponse] = Field(..., description="考纲列表")


# ========== 热点资源schemas ==========
class HotspotResourceBase(BaseModel):
    """热点资源基础schema."""

    title: str = Field(..., description="资源标题")
    source_type: str = Field(..., description="来源类型")
    source_url: str | None = Field(None, description="来源URL")
    author: str | None = Field(None, description="作者")
    publish_date: str | None = Field(None, description="发布日期")
    content_preview: str | None = Field(None, description="内容预览")
    full_content: str | None = Field(None, description="完整内容")
    content_type: ContentType = Field(default=ContentType.TEXT, description="内容类型")
    language: str = Field(default="en", description="语言")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE, description="难度等级"
    )
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
    is_trending: bool = Field(default=False, description="是否热门")
    is_recommended: bool = Field(default=False, description="是否推荐")
    recommendation_reason: str | None = Field(None, description="推荐理由")
    expiry_date: str | None = Field(None, description="过期日期")


class HotspotResourceCreate(HotspotResourceBase):
    """创建热点资源schema."""

    library_id: int = Field(..., description="资源库ID")


class HotspotResourceUpdate(HotspotResourceBase):
    """更新热点资源schema."""

    title: str | None = Field(None, description="资源标题")
    source_type: str | None = Field(None, description="来源类型")


class HotspotResourceResponse(HotspotResourceBase):
    """热点资源响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="热点资源ID")
    library_id: int = Field(..., description="资源库ID")
    popularity_score: float = Field(..., description="热度分数")
    relevance_score: float = Field(..., description="相关性分数")
    engagement_rate: float = Field(..., description="参与度")
    view_count: int = Field(..., description="浏览次数")
    like_count: int = Field(..., description="点赞次数")
    share_count: int = Field(..., description="分享次数")
    comment_count: int = Field(..., description="评论次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class HotspotResourceSearchRequest(BaseModel):
    """热点资源搜索请求schema."""

    library_id: int | None = Field(None, description="资源库ID")
    keyword: str | None = Field(None, description="关键词")
    source_type: str | None = Field(None, description="来源类型")
    language: str | None = Field(None, description="语言")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    topics: list[str] = Field(default_factory=list, description="话题筛选")
    is_trending: bool | None = Field(None, description="是否热门")
    is_recommended: bool | None = Field(None, description="是否推荐")
    sort_by: str = Field(default="popularity_score", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")
    page: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页数量", ge=1, le=100)


class HotspotResourceListResponse(BaseModel):
    """热点资源列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    items: list[HotspotResourceResponse] = Field(..., description="热点资源列表")


# ========== 资源共享schemas ==========
class ResourceShareBase(BaseModel):
    """资源共享基础schema."""

    resource_id: int = Field(..., description="资源ID")
    resource_type: str = Field(..., description="资源类型")
    share_scope: str = Field(default="public", description="分享范围")
    permission_level: PermissionType = Field(
        default=PermissionType.COURSE_READ, description="权限级别"
    )
    share_message: str | None = Field(None, description="分享说明")


class ResourceShareCreate(ResourceShareBase):
    """创建资源共享schema."""

    shared_with: int | None = Field(None, description="分享给用户ID")
    expires_at: datetime | None = Field(None, description="过期时间")


class ResourceShareResponse(ResourceShareBase):
    """资源共享响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分享ID")
    shared_by: int = Field(..., description="分享者ID")
    shared_with: int | None = Field(None, description="分享给用户ID")
    access_count: int = Field(..., description="访问次数")
    is_active: bool = Field(..., description="是否激活")
    expires_at: datetime | None = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ========== 资源使用记录schemas ==========
class ResourceUsageCreate(BaseModel):
    """创建资源使用记录schema."""

    resource_id: int = Field(..., description="资源ID")
    resource_type: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")
    session_id: str | None = Field(None, description="会话ID")
    duration: int = Field(default=0, description="使用时长(秒)")
    interaction_data: dict[str, Any] = Field(default_factory=dict, description="交互数据")
    learning_progress: float = Field(default=0.0, description="学习进度", ge=0, le=1)
    comprehension_score: float = Field(default=0.0, description="理解分数", ge=0, le=1)
    feedback: str | None = Field(None, description="用户反馈")
    rating: float = Field(default=0.0, description="用户评分", ge=0, le=5)


class ResourceUsageResponse(BaseModel):
    """资源使用记录响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="使用记录ID")
    resource_id: int = Field(..., description="资源ID")
    resource_type: str = Field(..., description="资源类型")
    user_id: int = Field(..., description="用户ID")
    action: str = Field(..., description="操作类型")
    duration: int = Field(..., description="使用时长(秒)")
    learning_progress: float = Field(..., description="学习进度")
    comprehension_score: float = Field(..., description="理解分数")
    rating: float = Field(..., description="用户评分")
    is_completed: bool = Field(..., description="是否完成")
    completion_time: datetime | None = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")


# ========== 通用响应schemas ==========
class ResourceStatistics(BaseModel):
    """资源统计schema."""

    total_libraries: int = Field(..., description="资源库总数")
    total_vocabularies: int = Field(..., description="词汇总数")
    total_knowledge_points: int = Field(..., description="知识点总数")
    total_materials: int = Field(..., description="教材总数")
    total_syllabi: int = Field(..., description="考纲总数")
    total_hotspots: int = Field(..., description="热点资源总数")
    popular_resources: list[dict[str, Any]] = Field(..., description="热门资源")
    recent_updates: list[dict[str, Any]] = Field(..., description="最近更新")


class ImportResult(BaseModel):
    """导入结果schema."""

    total: int = Field(..., description="总数量")
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    skipped: int = Field(..., description="跳过数量")
    errors: list[str] = Field(..., description="错误信息")
    warnings: list[str] = Field(..., description="警告信息")


class ExportRequest(BaseModel):
    """导出请求schema."""

    resource_type: str = Field(..., description="资源类型")
    library_id: int | None = Field(None, description="资源库ID")
    format: str = Field(default="excel", description="导出格式")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    filters: dict[str, Any] = Field(default_factory=dict, description="筛选条件")
