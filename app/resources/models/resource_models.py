"""教学资源库数据模型."""

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
from app.shared.models.enums import (
    ContentType,
    DifficultyLevel,
    PermissionLevel,
    PermissionType,
    ProcessingStatus,
    ResourceType,
)

# 导出枚举以供其他模块使用
__all__ = [
    "ResourceLibrary",
    "VocabularyItem",
    "KnowledgePoint",
    "TeachingMaterial",
    "ExamSyllabus",
    "HotspotResource",
    "ResourceShare",
    "ResourceUsage",
    "DocumentChunk",
    "ResourceType",
    "ProcessingStatus",
    "PermissionLevel",
]

if TYPE_CHECKING:
    from app.users.models.user_models import User


class ResourceLibrary(BaseModel):
    """教学资源库模型 - 管理课程专属资源库."""

    __tablename__ = "resource_libraries"

    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="资源名称")
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType), nullable=False, comment="资源类型"
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="资源分类")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="资源描述")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="文件路径")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="文件大小")
    file_format: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="文件格式")
    permission_level: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel),
        default=PermissionLevel.PRIVATE,
        nullable=False,
        comment="权限级别",
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        comment="处理状态",
    )
    vector_indexed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否已向量化"
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0", nullable=False, comment="版本号"
    )
    download_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="下载次数"
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="查看次数")
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="评分")
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID"
    )

    # 关系
    creator: Mapped[User] = relationship("User")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk", back_populates="resource", cascade="all, delete-orphan"
    )


class VocabularyItem(BaseModel):
    """词汇库条目模型."""

    __tablename__ = "vocabulary_items"

    library_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源库ID",
    )
    word: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="单词")
    pronunciation: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="音标")
    part_of_speech: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="词性")
    chinese_meaning: Mapped[str] = mapped_column(Text, nullable=False, comment="中文释义")
    english_meaning: Mapped[str | None] = mapped_column(Text, nullable=True, comment="英文释义")
    example_sentences: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="例句列表"
    )
    synonyms: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="同义词"
    )
    antonyms: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="反义词"
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
        comment="难度等级",
    )
    frequency: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="使用频率")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="音频URL")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="图片URL")
    learning_tips: Mapped[str | None] = mapped_column(Text, nullable=True, comment="学习提示")
    is_key_word: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否关键词"
    )
    review_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="复习次数"
    )
    mastery_level: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="掌握程度 (0-1)"
    )

    # 关系
    library: Mapped[ResourceLibrary] = relationship(
        "ResourceLibrary", back_populates="vocabularies"
    )


class KnowledgePoint(BaseModel):
    """知识点库模型."""

    __tablename__ = "knowledge_points"

    library_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源库ID",
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("knowledge_points.id", ondelete="CASCADE"),
        nullable=True,
        comment="父知识点ID",
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="知识点标题")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="知识点分类")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="知识点内容")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="详细描述")
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
        comment="难度等级",
    )
    importance_score: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False, comment="重要性分数 (0-1)"
    )
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="学习目标"
    )
    prerequisite_points: Mapped[list[int]] = mapped_column(
        JSON, default=list, nullable=False, comment="前置知识点ID列表"
    )
    related_points: Mapped[list[int]] = mapped_column(
        JSON, default=list, nullable=False, comment="相关知识点ID列表"
    )
    examples: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="示例列表"
    )
    exercises: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="练习题列表"
    )
    resources: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="相关资源"
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")
    estimated_time: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False, comment="预估学习时间(分钟)"
    )
    is_core: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否核心知识点"
    )
    review_frequency: Mapped[int] = mapped_column(
        Integer, default=7, nullable=False, comment="建议复习频率(天)"
    )

    # 关系
    library: Mapped[ResourceLibrary] = relationship(
        "ResourceLibrary", back_populates="knowledge_points"
    )
    parent: Mapped[KnowledgePoint | None] = relationship(
        "KnowledgePoint", remote_side="KnowledgePoint.id", back_populates="children"
    )
    children: Mapped[list[KnowledgePoint]] = relationship("KnowledgePoint", back_populates="parent")


class TeachingMaterial(BaseModel):
    """教材库模型."""

    __tablename__ = "teaching_materials"

    library_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源库ID",
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, comment="教材标题")
    authors: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="作者列表"
    )
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="出版社")
    publication_date: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="出版日期"
    )
    isbn: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="ISBN")
    edition: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="版本")
    language: Mapped[str] = mapped_column(
        String(20), default="zh-CN", nullable=False, comment="语言"
    )
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        default=ContentType.TEXT,
        nullable=False,
        comment="内容类型",
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="文件路径")
    file_size: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="文件大小(字节)"
    )
    file_format: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="文件格式")
    preview_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="预览URL")
    download_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="下载URL")
    chapters: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="章节信息"
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
        comment="难度等级",
    )
    target_audience: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="目标受众"
    )
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="学习目标"
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="使用次数")
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="评分 (0-5)")
    review_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="评价数量"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否主教材"
    )
    is_supplementary: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否辅助教材"
    )

    # 关系
    library: Mapped[ResourceLibrary] = relationship("ResourceLibrary", back_populates="materials")


class ExamSyllabus(BaseModel):
    """考纲模型."""

    __tablename__ = "exam_syllabi"

    library_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源库ID",
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, comment="考纲标题")
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="考试类型")
    exam_level: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="考试级别")
    version: Mapped[str] = mapped_column(
        String(20), default="1.0", nullable=False, comment="版本号"
    )
    effective_date: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="生效日期"
    )
    expiry_date: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="失效日期")
    issuing_authority: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="颁布机构"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="考纲描述")
    exam_structure: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="考试结构"
    )
    skill_requirements: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="技能要求"
    )
    vocabulary_requirements: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="词汇要求"
    )
    grammar_requirements: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="语法要求"
    )
    topic_areas: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="话题领域"
    )
    question_types: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="题型说明"
    )
    scoring_criteria: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="评分标准"
    )
    sample_papers: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="样卷信息"
    )
    preparation_suggestions: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="备考建议"
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签")
    is_current: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否为当前版本"
    )
    is_official: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否官方版本"
    )

    # 关系
    library: Mapped[ResourceLibrary] = relationship("ResourceLibrary", back_populates="syllabi")


class HotspotResource(BaseModel):
    """热点资源池模型."""

    __tablename__ = "hotspot_resources"

    library_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源库ID",
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, comment="资源标题")
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="来源类型 (news, paper, blog, etc.)"
    )
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="来源URL")
    author: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="作者")
    publish_date: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="发布日期")
    content_preview: Mapped[str | None] = mapped_column(Text, nullable=True, comment="内容预览")
    full_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完整内容")
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        default=ContentType.TEXT,
        nullable=False,
        comment="内容类型",
    )
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False, comment="语言")
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
        comment="难度等级",
    )
    topics: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="话题标签"
    )
    keywords: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="关键词"
    )
    vocabulary_highlights: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="重点词汇"
    )
    grammar_points: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="语法点"
    )
    cultural_notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文化注释")
    comprehension_questions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False, comment="理解问题"
    )
    discussion_topics: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="讨论话题"
    )
    popularity_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="热度分数"
    )
    relevance_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="相关性分数"
    )
    engagement_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="参与度"
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览次数")
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="点赞次数")
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="分享次数")
    comment_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="评论次数"
    )
    is_trending: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否热门"
    )
    is_recommended: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否推荐"
    )
    recommendation_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="推荐理由"
    )
    expiry_date: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="过期日期")

    # 关系
    library: Mapped[ResourceLibrary] = relationship("ResourceLibrary", back_populates="hotspots")


class ResourceShare(BaseModel):
    """资源共享模型."""

    __tablename__ = "resource_shares"

    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="资源ID")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="资源类型")
    shared_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="分享者ID",
    )
    shared_with: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="分享给用户ID(为空表示公开分享)",
    )
    share_scope: Mapped[str] = mapped_column(
        String(20),
        default="public",
        nullable=False,
        comment="分享范围 (public, class, school, private)",
    )
    permission_level: Mapped[PermissionType] = mapped_column(
        Enum(PermissionType),
        default=PermissionType.COURSE_READ,
        nullable=False,
        comment="权限级别",
    )
    share_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="分享说明")
    access_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="访问次数"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True, comment="过期时间")

    # 关系
    sharer: Mapped[User] = relationship("User", foreign_keys=[shared_by])
    recipient: Mapped[User | None] = relationship("User", foreign_keys=[shared_with])


class ResourceUsage(BaseModel):
    """资源使用记录模型."""

    __tablename__ = "resource_usage"

    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="资源ID")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="资源类型")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="操作类型 (view, download, edit, etc.)"
    )
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="会话ID")
    duration: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="使用时长(秒)"
    )
    interaction_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="交互数据"
    )
    learning_progress: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="学习进度 (0-1)"
    )
    comprehension_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="理解分数 (0-1)"
    )
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户反馈")
    rating: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="用户评分 (0-5)"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否完成"
    )
    completion_time: Mapped[DateTime | None] = mapped_column(
        DateTime, nullable=True, comment="完成时间"
    )

    # 关系
    user: Mapped[User] = relationship("User")


class DocumentChunk(BaseModel):
    """文档切片模型 - 支持大规模文档处理."""

    __tablename__ = "document_chunks"

    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resource_libraries.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源ID",
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="切片序号")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="切片内容")
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="切片大小")
    start_position: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="在原文档中的起始位置"
    )
    end_position: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="在原文档中的结束位置"
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="页码")
    section_title: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="章节标题"
    )
    vector_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="在Milvus中的向量ID"
    )
    embedding_model: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="使用的embedding模型"
    )
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="额外元数据"
    )

    # 关系
    resource: Mapped[ResourceLibrary] = relationship("ResourceLibrary")
