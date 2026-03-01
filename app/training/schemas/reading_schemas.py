"""阅读理解训练 - 数据模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.training.models.reading_models import ReadingDifficulty, ReadingQuestionType, ReadingTheme


# 阅读文章模式
class ReadingPassageBase(BaseModel):
    """阅读文章基础模式"""

    title: str = Field(..., description="文章标题", max_length=200)
    content: str = Field(..., description="文章内容")
    theme: ReadingTheme = Field(..., description="主题分类")
    difficulty: ReadingDifficulty = Field(..., description="难度等级")
    source: str | None = Field(None, description="文章来源", max_length=100)
    keywords: list[str] | None = Field(None, description="关键词列表")
    summary: str | None = Field(None, description="文章摘要")
    reading_time_minutes: int | None = Field(
        None, description="建议阅读时间(分钟)", ge=1, le=60
    )


class ReadingPassageCreate(ReadingPassageBase):
    """创建阅读文章的请求模式"""


class ReadingPassageUpdate(BaseModel):
    """更新阅读文章的请求模式"""

    title: str | None = Field(None, description="文章标题", max_length=200)
    content: str | None = Field(None, description="文章内容")
    theme: ReadingTheme | None = Field(None, description="主题分类")
    difficulty: ReadingDifficulty | None = Field(None, description="难度等级")
    source: str | None = Field(None, description="文章来源", max_length=100)
    keywords: list[str] | None = Field(None, description="关键词列表")
    summary: str | None = Field(None, description="文章摘要")
    reading_time_minutes: int | None = Field(
        None, description="建议阅读时间(分钟)", ge=1, le=60
    )
    is_active: bool | None = Field(None, description="是否激活")


class ReadingPassageResponse(ReadingPassageBase):
    """阅读文章响应模式"""

    id: int = Field(..., description="ID")
    word_count: int = Field(..., description="字数")
    is_active: bool = Field(..., description="是否激活")
    usage_count: int = Field(..., description="使用次数")
    average_score: float = Field(..., description="平均得分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 阅读题目模式
class ReadingQuestionBase(BaseModel):
    """阅读题目基础模式"""

    question_text: str = Field(..., description="题目内容")
    question_type: ReadingQuestionType = Field(..., description="题目类型")
    order_index: int = Field(..., description="题目顺序", ge=1)
    options: list[str] = Field(..., description="选项列表", min_length=2, max_length=6)
    correct_answer: str = Field(..., description="正确答案", max_length=10)
    explanation: str | None = Field(None, description="答案解析")
    difficulty: ReadingDifficulty = Field(..., description="题目难度")
    points: int = Field(default=1, description="题目分值", ge=1, le=10)


class ReadingQuestionCreate(ReadingQuestionBase):
    """创建阅读题目的请求模式"""

    passage_id: int = Field(..., description="文章ID")


class ReadingQuestionUpdate(BaseModel):
    """更新阅读题目的请求模式"""

    question_text: str | None = Field(None, description="题目内容")
    question_type: ReadingQuestionType | None = Field(None, description="题目类型")
    order_index: int | None = Field(None, description="题目顺序", ge=1)
    options: list[str] | None = Field(
        None, description="选项列表", min_length=2, max_length=6
    )
    correct_answer: str | None = Field(None, description="正确答案", max_length=10)
    explanation: str | None = Field(None, description="答案解析")
    difficulty: ReadingDifficulty | None = Field(None, description="题目难度")
    points: int | None = Field(None, description="题目分值", ge=1, le=10)
    is_active: bool | None = Field(None, description="是否激活")


class ReadingQuestionResponse(ReadingQuestionBase):
    """阅读题目响应模式"""

    id: int = Field(..., description="ID")
    passage_id: int = Field(..., description="文章ID")
    usage_count: int = Field(..., description="使用次数")
    correct_rate: float = Field(..., description="正确率")
    average_time_seconds: int = Field(..., description="平均答题时间(秒)")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 训练计划模式
class ReadingTrainingPlanBase(BaseModel):
    """阅读训练计划基础模式"""

    plan_name: str = Field(..., description="计划名称", max_length=100)
    description: str | None = Field(None, description="计划描述")
    weekly_target: int = Field(default=15, description="每周目标题数", ge=5, le=50)
    themes_per_week: list[ReadingTheme] | None = Field(None, description="每周主题安排")
    difficulty_progression: list[ReadingDifficulty] | None = Field(
        None, description="难度递进安排"
    )
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    training_days: list[int] | None = Field(
        None, description="训练日安排(1-7)", min_length=1, max_length=7
    )


class ReadingTrainingPlanCreate(ReadingTrainingPlanBase):
    """创建阅读训练计划的请求模式"""


class ReadingTrainingPlanUpdate(BaseModel):
    """更新阅读训练计划的请求模式"""

    plan_name: str | None = Field(None, description="计划名称", max_length=100)
    description: str | None = Field(None, description="计划描述")
    weekly_target: int | None = Field(None, description="每周目标题数", ge=5, le=50)
    themes_per_week: list[ReadingTheme] | None = Field(None, description="每周主题安排")
    difficulty_progression: list[ReadingDifficulty] | None = Field(
        None, description="难度递进安排"
    )
    end_date: datetime | None = Field(None, description="结束日期")
    training_days: list[int] | None = Field(
        None, description="训练日安排(1-7)", min_length=1, max_length=7
    )
    is_active: bool | None = Field(None, description="是否激活")


class ReadingTrainingPlanResponse(ReadingTrainingPlanBase):
    """阅读训练计划响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="学生ID")
    is_active: bool = Field(..., description="是否激活")
    completion_rate: float = Field(..., description="完成率")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 训练记录模式
class ReadingTrainingRecordCreate(BaseModel):
    """创建阅读训练记录的请求模式"""

    passage_id: int = Field(..., description="文章ID")
    training_plan_id: int | None = Field(None, description="训练计划ID")
    training_mode: str = Field(..., description="训练模式", max_length=20)


class ReadingTrainingRecordUpdate(BaseModel):
    """更新阅读训练记录的请求模式"""

    reading_time_seconds: int | None = Field(None, description="阅读时间(秒)", ge=0)
    answering_time_seconds: int | None = Field(None, description="答题时间(秒)", ge=0)
    is_completed: bool | None = Field(None, description="是否完成")


class ReadingTrainingRecordResponse(BaseModel):
    """阅读训练记录响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="学生ID")
    passage_id: int = Field(..., description="文章ID")
    training_plan_id: int | None = Field(None, description="训练计划ID")
    training_mode: str = Field(..., description="训练模式")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    total_questions: int = Field(..., description="总题数")
    correct_answers: int = Field(..., description="正确答案数")
    accuracy_rate: float = Field(..., description="正确率")
    total_score: int = Field(..., description="总得分")
    reading_time_seconds: int = Field(..., description="阅读时间(秒)")
    answering_time_seconds: int = Field(..., description="答题时间(秒)")
    total_time_seconds: int = Field(..., description="总用时(秒)")
    is_completed: bool = Field(..., description="是否完成")
    reading_analysis: dict[str, Any] | None = Field(None, description="阅读分析结果")
    weak_points: list[str] | None = Field(None, description="薄弱知识点")
    suggestions: list[str] | None = Field(None, description="改进建议")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 答题记录模式
class ReadingAnswerRecordCreate(BaseModel):
    """创建答题记录的请求模式"""

    question_id: int = Field(..., description="题目ID")
    user_answer: str = Field(..., description="学生答案", max_length=10)
    answer_time_seconds: int = Field(default=0, description="答题时间(秒)", ge=0)
    confidence_level: float | None = Field(None, description="答题置信度", ge=0.0, le=1.0)
    difficulty_perceived: ReadingDifficulty | None = Field(None, description="感知难度")


class ReadingAnswerRecordResponse(BaseModel):
    """答题记录响应模式"""

    id: int = Field(..., description="ID")
    training_record_id: int = Field(..., description="训练记录ID")
    question_id: int = Field(..., description="题目ID")
    user_id: int = Field(..., description="学生ID")
    user_answer: str = Field(..., description="学生答案")
    is_correct: bool = Field(..., description="是否正确")
    answer_time_seconds: int = Field(..., description="答题时间(秒)")
    confidence_level: float = Field(..., description="答题置信度")
    difficulty_perceived: ReadingDifficulty | None = Field(None, description="感知难度")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# 综合模式
class ReadingTrainingSession(BaseModel):
    """阅读训练会话模式"""

    passage: ReadingPassageResponse = Field(..., description="阅读文章")
    questions: list[ReadingQuestionResponse] = Field(..., description="题目列表")
    training_record: ReadingTrainingRecordResponse = Field(..., description="训练记录")


class ReadingStatistics(BaseModel):
    """阅读统计模式"""

    total_passages_read: int = Field(..., description="总阅读文章数")
    total_questions_answered: int = Field(..., description="总答题数")
    overall_accuracy: float = Field(..., description="总体正确率")
    average_reading_speed: float = Field(..., description="平均阅读速度(字/分钟)")
    theme_performance: dict[str, float] = Field(..., description="各主题表现")
    difficulty_performance: dict[str, float] = Field(..., description="各难度表现")
    question_type_performance: dict[str, float] = Field(..., description="各题型表现")
    recent_improvement: float = Field(..., description="近期提升幅度")


class ReadingRecommendation(BaseModel):
    """阅读推荐模式"""

    recommended_theme: ReadingTheme = Field(..., description="推荐主题")
    recommended_difficulty: ReadingDifficulty = Field(..., description="推荐难度")
    recommended_passages: list[ReadingPassageResponse] = Field(..., description="推荐文章")
    focus_areas: list[str] = Field(..., description="重点关注领域")
    training_suggestions: list[str] = Field(..., description="训练建议")


# 列表响应模式
class ReadingPassageListResponse(BaseModel):
    """阅读文章列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[ReadingPassageResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ReadingTrainingPlanListResponse(BaseModel):
    """阅读训练计划列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[ReadingTrainingPlanResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ReadingTrainingRecordListResponse(BaseModel):
    """阅读训练记录列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[ReadingTrainingRecordResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
