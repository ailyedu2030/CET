"""英语四级写作标准库 - 数据模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.training.models.writing_models import (
    WritingDifficulty,
    WritingScoreLevel,
    WritingType,
)


# 写作模板模式
class WritingTemplateBase(BaseModel):
    """写作模板基础模式"""

    template_name: str = Field(..., description="模板名称", max_length=100)
    writing_type: WritingType = Field(..., description="写作类型")
    difficulty: WritingDifficulty = Field(..., description="难度等级")
    template_structure: dict[str, Any] = Field(..., description="模板结构")
    opening_sentences: list[str] | None = Field(None, description="开头句式")
    transition_phrases: list[str] | None = Field(None, description="过渡词汇")
    conclusion_sentences: list[str] | None = Field(None, description="结尾句式")
    example_essay: str | None = Field(None, description="示例作文")
    usage_instructions: str | None = Field(None, description="使用说明")
    key_phrases: list[str] | None = Field(None, description="关键短语")


class WritingTemplateCreate(WritingTemplateBase):
    """创建写作模板的请求模式"""


class WritingTemplateUpdate(BaseModel):
    """更新写作模板的请求模式"""

    template_name: str | None = Field(None, description="模板名称", max_length=100)
    writing_type: WritingType | None = Field(None, description="写作类型")
    difficulty: WritingDifficulty | None = Field(None, description="难度等级")
    template_structure: dict[str, Any] | None = Field(None, description="模板结构")
    opening_sentences: list[str] | None = Field(None, description="开头句式")
    transition_phrases: list[str] | None = Field(None, description="过渡词汇")
    conclusion_sentences: list[str] | None = Field(None, description="结尾句式")
    example_essay: str | None = Field(None, description="示例作文")
    usage_instructions: str | None = Field(None, description="使用说明")
    key_phrases: list[str] | None = Field(None, description="关键短语")
    is_active: bool | None = Field(None, description="是否激活")
    is_recommended: bool | None = Field(None, description="是否推荐")


class WritingTemplateResponse(WritingTemplateBase):
    """写作模板响应模式"""

    id: int = Field(..., description="ID")
    usage_count: int = Field(..., description="使用次数")
    average_score: float = Field(..., description="平均得分")
    success_rate: float = Field(..., description="成功率")
    is_active: bool = Field(..., description="是否激活")
    is_recommended: bool = Field(..., description="是否推荐")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 写作任务模式
class WritingTaskBase(BaseModel):
    """写作任务基础模式"""

    task_title: str = Field(..., description="任务标题", max_length=200)
    task_prompt: str = Field(..., description="写作提示")
    writing_type: WritingType = Field(..., description="写作类型")
    difficulty: WritingDifficulty = Field(..., description="难度等级")
    word_count_min: int = Field(default=120, description="最少字数", ge=50, le=500)
    word_count_max: int = Field(default=180, description="最多字数", ge=100, le=1000)
    time_limit_minutes: int = Field(
        default=30, description="时间限制(分钟)", ge=10, le=120
    )
    scoring_criteria: dict[str, Any] | None = Field(None, description="评分标准")
    sample_answers: list[str] | None = Field(None, description="参考答案")
    keywords: list[str] | None = Field(None, description="关键词")
    outline_suggestions: list[str] | None = Field(None, description="大纲建议")
    template_id: int | None = Field(None, description="推荐模板ID")

    @field_validator("word_count_max")
    @classmethod
    def validate_word_count_max(cls: type["WritingTaskBase"], v: int, info: Any) -> int:
        """验证最大字数必须大于最小字数"""
        if (
            hasattr(info, "data")
            and "word_count_min" in info.data
            and v <= info.data["word_count_min"]
        ):
            raise ValueError("最大字数必须大于最小字数")
        return v

    @field_validator("task_title")
    @classmethod
    def validate_task_title(cls: type["WritingTaskBase"], v: str) -> str:
        """验证任务标题不能为空"""
        if not v or not v.strip():
            raise ValueError("任务标题不能为空")
        return v.strip()

    @field_validator("task_prompt")
    @classmethod
    def validate_task_prompt(cls: type["WritingTaskBase"], v: str) -> str:
        """验证写作提示不能为空"""
        if not v or not v.strip():
            raise ValueError("写作提示不能为空")
        return v.strip()


class WritingTaskCreate(WritingTaskBase):
    """创建写作任务的请求模式"""


class WritingTaskUpdate(BaseModel):
    """更新写作任务的请求模式"""

    task_title: str | None = Field(None, description="任务标题", max_length=200)
    task_prompt: str | None = Field(None, description="写作提示")
    writing_type: WritingType | None = Field(None, description="写作类型")
    difficulty: WritingDifficulty | None = Field(None, description="难度等级")
    word_count_min: int | None = Field(None, description="最少字数", ge=50, le=500)
    word_count_max: int | None = Field(None, description="最多字数", ge=100, le=1000)
    time_limit_minutes: int | None = Field(
        None, description="时间限制(分钟)", ge=10, le=120
    )
    scoring_criteria: dict[str, Any] | None = Field(None, description="评分标准")
    sample_answers: list[str] | None = Field(None, description="参考答案")
    keywords: list[str] | None = Field(None, description="关键词")
    outline_suggestions: list[str] | None = Field(None, description="大纲建议")
    template_id: int | None = Field(None, description="推荐模板ID")
    is_active: bool | None = Field(None, description="是否激活")


class WritingTaskResponse(WritingTaskBase):
    """写作任务响应模式"""

    id: int = Field(..., description="ID")
    usage_count: int = Field(..., description="使用次数")
    average_score: float = Field(..., description="平均得分")
    completion_rate: float = Field(..., description="完成率")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 写作提交模式
class WritingSubmissionCreate(BaseModel):
    """创建写作提交的请求模式"""

    task_id: int = Field(..., description="任务ID")
    essay_content: str = Field(..., description="作文内容", min_length=50)
    writing_time_minutes: int = Field(..., description="写作用时(分钟)", ge=1, le=120)


class WritingSubmissionUpdate(BaseModel):
    """更新写作提交的请求模式"""

    essay_content: str | None = Field(None, description="作文内容", min_length=50)


class WritingSubmissionResponse(BaseModel):
    """写作提交响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="学生ID")
    task_id: int = Field(..., description="任务ID")
    essay_content: str = Field(..., description="作文内容")
    word_count: int = Field(..., description="字数")
    started_at: datetime = Field(..., description="开始时间")
    submitted_at: datetime = Field(..., description="提交时间")
    writing_time_minutes: int = Field(..., description="写作用时(分钟)")
    total_score: float = Field(..., description="总分")
    score_level: WritingScoreLevel | None = Field(None, description="评分等级")
    content_score: float = Field(..., description="内容分")
    structure_score: float = Field(..., description="结构分")
    language_score: float = Field(..., description="语言分")
    grammar_score: float = Field(..., description="语法分")
    ai_feedback: dict[str, Any] | None = Field(None, description="AI反馈")
    grammar_errors: list[dict[str, Any]] | None = Field(None, description="语法错误")
    vocabulary_suggestions: list[dict[str, Any]] | None = Field(
        None, description="词汇建议"
    )
    structure_analysis: dict[str, Any] | None = Field(None, description="结构分析")
    strengths: list[str] | None = Field(None, description="优点")
    weaknesses: list[str] | None = Field(None, description="不足")
    improvement_suggestions: list[str] | None = Field(None, description="改进建议")
    is_graded: bool = Field(..., description="是否已评分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 写作词汇模式
class WritingVocabularyBase(BaseModel):
    """写作词汇基础模式"""

    word_or_phrase: str = Field(..., description="词汇或短语", max_length=100)
    part_of_speech: str | None = Field(None, description="词性", max_length=20)
    meaning: str | None = Field(None, description="含义", max_length=200)
    category: str | None = Field(None, description="分类", max_length=50)
    writing_type: WritingType | None = Field(None, description="适用写作类型")
    difficulty_level: WritingDifficulty | None = Field(None, description="难度等级")
    usage_examples: list[str] | None = Field(None, description="使用例句")
    synonyms: list[str] | None = Field(None, description="同义词")
    antonyms: list[str] | None = Field(None, description="反义词")
    collocations: list[str] | None = Field(None, description="搭配")


class WritingVocabularyCreate(WritingVocabularyBase):
    """创建写作词汇的请求模式"""


class WritingVocabularyUpdate(BaseModel):
    """更新写作词汇的请求模式"""

    word_or_phrase: str | None = Field(None, description="词汇或短语", max_length=100)
    part_of_speech: str | None = Field(None, description="词性", max_length=20)
    meaning: str | None = Field(None, description="含义", max_length=200)
    category: str | None = Field(None, description="分类", max_length=50)
    writing_type: WritingType | None = Field(None, description="适用写作类型")
    difficulty_level: WritingDifficulty | None = Field(None, description="难度等级")
    usage_examples: list[str] | None = Field(None, description="使用例句")
    synonyms: list[str] | None = Field(None, description="同义词")
    antonyms: list[str] | None = Field(None, description="反义词")
    collocations: list[str] | None = Field(None, description="搭配")
    is_active: bool | None = Field(None, description="是否激活")
    is_recommended: bool | None = Field(None, description="是否推荐")


class WritingVocabularyResponse(WritingVocabularyBase):
    """写作词汇响应模式"""

    id: int = Field(..., description="ID")
    usage_frequency: int = Field(..., description="使用频率")
    effectiveness_score: float = Field(..., description="有效性评分")
    is_active: bool = Field(..., description="是否激活")
    is_recommended: bool = Field(..., description="是否推荐")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 语法检查结果模式
class GrammarCheckResult(BaseModel):
    """语法检查结果模式"""

    error_count: int = Field(..., description="错误数量")
    errors: list[dict[str, Any]] = Field(..., description="错误详情")
    suggestions: list[dict[str, Any]] = Field(..., description="修改建议")
    corrected_text: str = Field(..., description="修正后文本")
    grammar_score: float = Field(..., description="语法得分")


# 写作评分结果模式
class WritingGradingResult(BaseModel):
    """写作评分结果模式"""

    total_score: float = Field(..., description="总分")
    score_level: WritingScoreLevel = Field(..., description="评分等级")
    content_score: float = Field(..., description="内容分")
    structure_score: float = Field(..., description="结构分")
    language_score: float = Field(..., description="语言分")
    grammar_score: float = Field(..., description="语法分")
    detailed_feedback: dict[str, Any] = Field(..., description="详细反馈")
    strengths: list[str] = Field(..., description="优点")
    weaknesses: list[str] = Field(..., description="不足")
    improvement_suggestions: list[str] = Field(..., description="改进建议")


# 写作统计模式
class WritingStatistics(BaseModel):
    """写作统计模式"""

    total_submissions: int = Field(..., description="总提交数")
    average_score: float = Field(..., description="平均得分")
    score_distribution: dict[str, int] = Field(..., description="分数分布")
    writing_type_performance: dict[str, float] = Field(..., description="各类型表现")
    improvement_trend: list[float] = Field(..., description="提升趋势")
    common_errors: list[dict[str, Any]] = Field(..., description="常见错误")
    vocabulary_usage: dict[str, int] = Field(..., description="词汇使用情况")


# 写作推荐模式
class WritingRecommendation(BaseModel):
    """写作推荐模式"""

    recommended_templates: list[WritingTemplateResponse] = Field(
        ..., description="推荐模板"
    )
    recommended_tasks: list[WritingTaskResponse] = Field(..., description="推荐任务")
    focus_areas: list[str] = Field(..., description="重点关注领域")
    vocabulary_suggestions: list[WritingVocabularyResponse] = Field(
        ..., description="词汇建议"
    )
    practice_plan: dict[str, Any] = Field(..., description="练习计划")


# 列表响应模式
class WritingTemplateListResponse(BaseModel):
    """写作模板列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[WritingTemplateResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class WritingTaskListResponse(BaseModel):
    """写作任务列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[WritingTaskResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class WritingSubmissionListResponse(BaseModel):
    """写作提交列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[WritingSubmissionResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class WritingVocabularyListResponse(BaseModel):
    """写作词汇列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[WritingVocabularyResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
