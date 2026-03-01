"""学习辅助工具系统 - 数据模型"""

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


class QuestionType(str, Enum):
    """问题类型枚举"""

    GENERAL = "general"  # 一般问题
    VOCABULARY = "vocabulary"  # 词汇问题
    GRAMMAR = "grammar"  # 语法问题
    LISTENING = "listening"  # 听力问题
    READING = "reading"  # 阅读问题
    WRITING = "writing"  # 写作问题
    EXAM_STRATEGY = "exam_strategy"  # 考试策略


class ResourceType(str, Enum):
    """资源类型枚举"""

    ARTICLE = "article"  # 文章
    VIDEO = "video"  # 视频
    AUDIO = "audio"  # 音频
    EXERCISE = "exercise"  # 练习
    DOCUMENT = "document"  # 文档
    LINK = "link"  # 链接


class RecommendationSource(str, Enum):
    """推荐来源枚举"""

    COLLABORATIVE_FILTERING = "collaborative_filtering"  # 协同过滤
    CONTENT_BASED = "content_based"  # 基于内容
    KNOWLEDGE_GRAPH = "knowledge_graph"  # 知识图谱
    AI_ANALYSIS = "ai_analysis"  # AI分析
    MANUAL = "manual"  # 人工推荐


class KnowledgeBaseModel(BaseModel):
    """
    知识库模型

    存储RAG智能问答系统的知识内容
    """

    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)

    # 知识内容
    title = Column(String(200), nullable=False, comment="知识标题")
    content = Column(Text, nullable=False, comment="知识内容")
    summary = Column(Text, comment="内容摘要")

    # 分类信息
    category = Column(String(50), comment="知识分类")
    tags = Column(JSON, comment="标签列表")
    difficulty_level = Column(String(20), comment="难度等级")

    # 向量信息
    embedding_vector = Column(JSON, comment="向量表示")
    vector_dimension = Column(Integer, comment="向量维度")

    # 来源信息
    source_type = Column(String(50), comment="来源类型")
    source_url = Column(String(500), comment="来源URL")
    author = Column(String(100), comment="作者")

    # 质量评估
    quality_score = Column(Float, default=0.0, comment="质量评分")
    relevance_score = Column(Float, default=0.0, comment="相关性评分")
    usage_count = Column(Integer, default=0, comment="使用次数")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否已验证")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    qa_records = relationship("QARecordModel", back_populates="knowledge_base")

    def __repr__(self: "KnowledgeBaseModel") -> str:
        return f"<KnowledgeBaseModel(id={getattr(self, 'id', None)}, title={getattr(self, 'title', None)})>"


class QARecordModel(BaseModel):
    """
    问答记录模型

    记录用户的问答历史
    """

    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_base.id"), nullable=True)

    # 问答内容
    question = Column(Text, nullable=False, comment="用户问题")
    answer = Column(Text, nullable=False, comment="系统回答")
    question_type = Column(String(20), comment="问题类型")

    # 上下文信息
    context = Column(JSON, comment="上下文信息")
    session_id = Column(String(100), comment="会话ID")

    # AI处理信息
    ai_model_used = Column(String(50), comment="使用的AI模型")
    processing_time_ms = Column(Integer, comment="处理时间(毫秒)")
    confidence_score = Column(Float, comment="置信度评分")

    # 用户反馈
    user_rating = Column(Integer, comment="用户评分(1-5)")
    user_feedback = Column(Text, comment="用户反馈")
    is_helpful = Column(Boolean, comment="是否有帮助")

    # 相关资源
    related_resources = Column(JSON, comment="相关资源")
    follow_up_questions = Column(JSON, comment="后续问题建议")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    knowledge_base = relationship("KnowledgeBaseModel", back_populates="qa_records")

    def __repr__(self: "QARecordModel") -> str:
        return f"<QARecordModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class LearningResourceModel(BaseModel):
    """
    学习资源模型

    存储学习资源信息
    """

    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)

    # 资源基本信息
    title = Column(String(200), nullable=False, comment="资源标题")
    description = Column(Text, comment="资源描述")
    resource_type = Column(String(20), nullable=False, comment="资源类型")

    # 资源内容
    content_url = Column(String(500), comment="资源URL")
    file_path = Column(String(500), comment="文件路径")
    thumbnail_url = Column(String(500), comment="缩略图URL")

    # 分类信息
    category = Column(String(50), comment="资源分类")
    tags = Column(JSON, comment="标签列表")
    difficulty_level = Column(String(20), comment="难度等级")
    target_audience = Column(JSON, comment="目标受众")

    # 元数据
    duration_minutes = Column(Integer, comment="时长(分钟)")
    file_size_mb = Column(Float, comment="文件大小(MB)")
    language = Column(String(10), default="zh", comment="语言")

    # 质量评估
    quality_score = Column(Float, default=0.0, comment="质量评分")
    popularity_score = Column(Float, default=0.0, comment="热度评分")
    view_count = Column(Integer, default=0, comment="查看次数")
    download_count = Column(Integer, default=0, comment="下载次数")

    # 推荐信息
    recommendation_score = Column(Float, default=0.0, comment="推荐评分")
    recommendation_reasons = Column(JSON, comment="推荐理由")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_featured = Column(Boolean, default=False, comment="是否精选")
    is_free = Column(Boolean, default=True, comment="是否免费")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    recommendations = relationship(
        "ResourceRecommendationModel", back_populates="resource"
    )
    user_interactions = relationship(
        "UserResourceInteractionModel", back_populates="resource"
    )

    def __repr__(self: "LearningResourceModel") -> str:
        return f"<LearningResourceModel(id={getattr(self, 'id', None)}, title={getattr(self, 'title', None)})>"


class ResourceRecommendationModel(BaseModel):
    """
    资源推荐模型

    记录个性化资源推荐
    """

    __tablename__ = "resource_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False)

    # 推荐信息
    recommendation_source = Column(String(30), nullable=False, comment="推荐来源")
    recommendation_score = Column(Float, nullable=False, comment="推荐评分")
    recommendation_reason = Column(Text, comment="推荐理由")

    # 推荐上下文
    context_data = Column(JSON, comment="推荐上下文")
    user_profile_snapshot = Column(JSON, comment="用户画像快照")

    # 用户反馈
    user_clicked = Column(Boolean, default=False, comment="用户是否点击")
    user_viewed = Column(Boolean, default=False, comment="用户是否查看")
    user_rating = Column(Integer, comment="用户评分(1-5)")
    user_feedback = Column(Text, comment="用户反馈")

    # 效果评估
    conversion_rate = Column(Float, comment="转化率")
    engagement_score = Column(Float, comment="参与度评分")

    # 时间戳
    recommended_at = Column(DateTime, default=datetime.utcnow, comment="推荐时间")
    clicked_at = Column(DateTime, comment="点击时间")
    viewed_at = Column(DateTime, comment="查看时间")

    # 关系
    resource = relationship("LearningResourceModel", back_populates="recommendations")

    def __repr__(self: "ResourceRecommendationModel") -> str:
        return f"<ResourceRecommendationModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class UserResourceInteractionModel(BaseModel):
    """
    用户资源交互模型

    记录用户与学习资源的交互行为
    """

    __tablename__ = "user_resource_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False)

    # 交互行为
    interaction_type = Column(String(20), nullable=False, comment="交互类型")
    interaction_duration = Column(Integer, comment="交互时长(秒)")
    completion_rate = Column(Float, comment="完成率")

    # 行为数据
    view_count = Column(Integer, default=0, comment="查看次数")
    download_count = Column(Integer, default=0, comment="下载次数")
    share_count = Column(Integer, default=0, comment="分享次数")
    bookmark_count = Column(Integer, default=0, comment="收藏次数")

    # 学习效果
    learning_progress = Column(Float, comment="学习进度")
    mastery_level = Column(Float, comment="掌握程度")
    difficulty_rating = Column(Integer, comment="难度评分(1-5)")
    usefulness_rating = Column(Integer, comment="有用性评分(1-5)")

    # 设备和环境
    device_type = Column(String(20), comment="设备类型")
    browser_type = Column(String(50), comment="浏览器类型")
    ip_address = Column(String(45), comment="IP地址")

    # 时间戳
    first_interaction_at = Column(
        DateTime, default=datetime.utcnow, comment="首次交互时间"
    )
    last_interaction_at = Column(
        DateTime, default=datetime.utcnow, comment="最后交互时间"
    )
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    resource = relationship("LearningResourceModel", back_populates="user_interactions")

    def __repr__(self: "UserResourceInteractionModel") -> str:
        return f"<UserResourceInteractionModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class VoiceRecognitionRecordModel(BaseModel):
    """
    语音识别记录模型

    记录语音识别的结果和分析
    """

    __tablename__ = "voice_recognition_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 音频信息
    audio_file_path = Column(String(500), comment="音频文件路径")
    audio_duration_seconds = Column(Float, comment="音频时长(秒)")
    audio_format = Column(String(10), comment="音频格式")
    audio_quality = Column(String(20), comment="音频质量")

    # 识别结果
    recognized_text = Column(Text, comment="识别文本")
    confidence_score = Column(Float, comment="置信度评分")
    processing_time_ms = Column(Integer, comment="处理时间(毫秒)")

    # 语音分析
    pronunciation_score = Column(Float, comment="发音评分")
    fluency_score = Column(Float, comment="流利度评分")
    accuracy_score = Column(Float, comment="准确性评分")

    # 错误分析
    pronunciation_errors = Column(JSON, comment="发音错误")
    grammar_errors = Column(JSON, comment="语法错误")
    vocabulary_suggestions = Column(JSON, comment="词汇建议")

    # 改进建议
    improvement_suggestions = Column(JSON, comment="改进建议")
    practice_recommendations = Column(JSON, comment="练习推荐")

    # 上下文
    exercise_type = Column(String(50), comment="练习类型")
    target_text = Column(Text, comment="目标文本")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "VoiceRecognitionRecordModel") -> str:
        return f"<VoiceRecognitionRecordModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"
