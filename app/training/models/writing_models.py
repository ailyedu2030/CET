"""英语四级写作标准库 - 数据模型"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.shared.models.base_model import BaseModel


class WritingType(str, Enum):
    """写作类型枚举"""

    ARGUMENTATIVE = "argumentative"  # 议论文
    NARRATIVE = "narrative"  # 记叙文
    DESCRIPTIVE = "descriptive"  # 描述文
    EXPOSITORY = "expository"  # 说明文
    PRACTICAL = "practical"  # 应用文


class WritingDifficulty(str, Enum):
    """写作难度枚举"""

    BASIC = "basic"  # 基础级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"  # 高级
    EXPERT = "expert"  # 专家级


class WritingScoreLevel(str, Enum):
    """写作评分等级枚举"""

    EXCELLENT = "excellent"  # 优秀 (14分)
    GOOD = "good"  # 良好 (11分)
    FAIR = "fair"  # 及格 (8分)
    POOR = "poor"  # 不及格 (5分)


class WritingTemplateModel(BaseModel):
    """
    写作模板模型

    存储各种类型的写作模板
    """

    __tablename__ = "writing_templates"

    id = Column(Integer, primary_key=True, index=True)

    # 模板基本信息
    template_name = Column(String(100), nullable=False, comment="模板名称")
    writing_type = Column(String(20), nullable=False, comment="写作类型")
    difficulty = Column(String(20), nullable=False, comment="难度等级")

    # 模板内容
    template_structure = Column(JSON, nullable=False, comment="模板结构")
    opening_sentences = Column(JSON, comment="开头句式")
    transition_phrases = Column(JSON, comment="过渡词汇")
    conclusion_sentences = Column(JSON, comment="结尾句式")

    # 示例和说明
    example_essay = Column(Text, comment="示例作文")
    usage_instructions = Column(Text, comment="使用说明")
    key_phrases = Column(JSON, comment="关键短语")

    # 统计数据
    usage_count = Column(Integer, default=0, comment="使用次数")
    average_score = Column(Float, default=0.0, comment="平均得分")
    success_rate = Column(Float, default=0.0, comment="成功率")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_recommended = Column(Boolean, default=False, comment="是否推荐")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    writing_tasks = relationship("WritingTaskModel", back_populates="template")

    def __repr__(self: "WritingTemplateModel") -> str:
        return f"<WritingTemplateModel(id={getattr(self, 'id', None)}, name={getattr(self, 'template_name', None)})>"


class WritingTaskModel(BaseModel):
    """
    写作任务模型

    存储写作练习题目
    """

    __tablename__ = "writing_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # 任务基本信息
    task_title = Column(String(200), nullable=False, comment="任务标题")
    task_prompt = Column(Text, nullable=False, comment="写作提示")
    writing_type = Column(String(20), nullable=False, comment="写作类型")
    difficulty = Column(String(20), nullable=False, comment="难度等级")

    # 任务要求
    word_count_min = Column(Integer, default=120, comment="最少字数")
    word_count_max = Column(Integer, default=180, comment="最多字数")
    time_limit_minutes = Column(Integer, default=30, comment="时间限制(分钟)")

    # 评分标准
    scoring_criteria = Column(JSON, comment="评分标准")
    sample_answers = Column(JSON, comment="参考答案")

    # 辅助信息
    keywords = Column(JSON, comment="关键词")
    outline_suggestions = Column(JSON, comment="大纲建议")
    template_id = Column(
        Integer, ForeignKey("writing_templates.id"), nullable=True, comment="推荐模板ID"
    )

    # 统计数据
    usage_count = Column(Integer, default=0, comment="使用次数")
    average_score = Column(Float, default=0.0, comment="平均得分")
    completion_rate = Column(Float, default=0.0, comment="完成率")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    template = relationship("WritingTemplateModel", back_populates="writing_tasks")
    submissions = relationship("WritingSubmissionModel", back_populates="task")

    def __repr__(self: "WritingTaskModel") -> str:
        return f"<WritingTaskModel(id={getattr(self, 'id', None)}, title={getattr(self, 'task_title', None)})>"


class WritingSubmissionModel(BaseModel):
    """
    写作提交模型

    记录学生的写作提交和评分
    """

    __tablename__ = "writing_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="学生ID")
    task_id = Column(Integer, ForeignKey("writing_tasks.id"), nullable=False)

    # 提交内容
    essay_content = Column(Text, nullable=False, comment="作文内容")
    word_count = Column(Integer, nullable=False, comment="字数")

    # 时间记录
    started_at = Column(DateTime, nullable=False, comment="开始时间")
    submitted_at = Column(DateTime, nullable=False, comment="提交时间")
    writing_time_minutes = Column(Integer, nullable=False, comment="写作用时(分钟)")

    # 评分结果
    total_score = Column(Float, default=0.0, comment="总分")
    score_level = Column(String(20), comment="评分等级")

    # 详细评分
    content_score = Column(Float, default=0.0, comment="内容分")
    structure_score = Column(Float, default=0.0, comment="结构分")
    language_score = Column(Float, default=0.0, comment="语言分")
    grammar_score = Column(Float, default=0.0, comment="语法分")

    # AI分析结果
    ai_feedback = Column(JSON, comment="AI反馈")
    grammar_errors = Column(JSON, comment="语法错误")
    vocabulary_suggestions = Column(JSON, comment="词汇建议")
    structure_analysis = Column(JSON, comment="结构分析")

    # 改进建议
    strengths = Column(JSON, comment="优点")
    weaknesses = Column(JSON, comment="不足")
    improvement_suggestions = Column(JSON, comment="改进建议")

    # 状态
    is_graded = Column(Boolean, default=False, comment="是否已评分")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    task = relationship("WritingTaskModel", back_populates="submissions")

    def __repr__(self: "WritingSubmissionModel") -> str:
        return f"<WritingSubmissionModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)})>"


class WritingVocabularyModel(BaseModel):
    """
    写作词汇库模型

    存储写作相关的词汇和短语
    """

    __tablename__ = "writing_vocabulary"

    id = Column(Integer, primary_key=True, index=True)

    # 词汇信息
    word_or_phrase = Column(String(100), nullable=False, comment="词汇或短语")
    part_of_speech = Column(String(20), comment="词性")
    meaning = Column(String(200), comment="含义")

    # 分类信息
    category = Column(String(50), comment="分类")
    writing_type = Column(String(20), comment="适用写作类型")
    difficulty_level = Column(String(20), comment="难度等级")

    # 使用信息
    usage_examples = Column(JSON, comment="使用例句")
    synonyms = Column(JSON, comment="同义词")
    antonyms = Column(JSON, comment="反义词")
    collocations = Column(JSON, comment="搭配")

    # 统计数据
    usage_frequency = Column(Integer, default=0, comment="使用频率")
    effectiveness_score = Column(Float, default=0.0, comment="有效性评分")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_recommended = Column(Boolean, default=False, comment="是否推荐")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "WritingVocabularyModel") -> str:
        return f"<WritingVocabularyModel(id={getattr(self, 'id', None)}, word={getattr(self, 'word_or_phrase', None)})>"


class WritingDraftModel(BaseModel):
    """
    写作草稿模型

    存储用户的写作草稿
    """

    __tablename__ = "writing_drafts"

    id = Column(Integer, primary_key=True, index=True)

    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    task_id = Column(
        Integer, ForeignKey("writing_tasks.id"), nullable=False, comment="写作任务ID"
    )

    # 草稿内容
    content = Column(Text, nullable=False, comment="草稿内容")
    word_count = Column(Integer, default=0, comment="字数")

    # 元数据
    title = Column(String(200), comment="草稿标题")
    auto_saved = Column(Boolean, default=True, comment="是否自动保存")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
    last_accessed_at = Column(DateTime, default=datetime.utcnow, comment="最后访问时间")

    # 索引
    __table_args__ = (
        Index("idx_writing_drafts_user_task", "user_id", "task_id", unique=True),
        Index("idx_writing_drafts_updated", "updated_at"),
    )

    def __repr__(self: "WritingDraftModel") -> str:
        return f"<WritingDraftModel(id={getattr(self, 'id', None)}, user_id={getattr(self, 'user_id', None)}, task_id={getattr(self, 'task_id', None)})>"


class WritingGrammarRuleModel(BaseModel):
    """
    写作语法规则模型

    存储写作相关的语法规则和检查
    """

    __tablename__ = "writing_grammar_rules"

    id = Column(Integer, primary_key=True, index=True)

    # 规则信息
    rule_name = Column(String(100), nullable=False, comment="规则名称")
    rule_description = Column(Text, nullable=False, comment="规则描述")
    rule_category = Column(String(50), comment="规则分类")

    # 检查模式
    pattern_regex = Column(String(500), comment="正则表达式模式")
    error_examples = Column(JSON, comment="错误示例")
    correct_examples = Column(JSON, comment="正确示例")

    # 修正建议
    correction_template = Column(String(200), comment="修正模板")
    explanation = Column(Text, comment="解释说明")

    # 严重程度
    severity_level = Column(String(20), default="medium", comment="严重程度")
    score_impact = Column(Float, default=0.5, comment="对分数的影响")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self: "WritingGrammarRuleModel") -> str:
        return f"<WritingGrammarRuleModel(id={getattr(self, 'id', None)}, name={getattr(self, 'rule_name', None)})>"
