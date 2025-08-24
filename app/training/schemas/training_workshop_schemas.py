"""智能训练工坊数据模型 - 需求15实现."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

from app.shared.models.enums import DifficultyLevel, TrainingType

# ==================== 训练参数配置相关 ====================


class TrainingParameterConfig(BaseModel):
    """训练参数配置."""

    knowledge_points: list[str] = Field(..., description="关联知识点列表")
    vocabulary_library_ids: list[int] = Field(..., description="词汇库ID列表")
    hot_topics_fusion_rate: int = Field(..., ge=0, le=100, description="热点融合程度(0-100%)")
    lesson_plan_connection_rate: int = Field(..., ge=0, le=100, description="教案衔接度(0-100%)")
    difficulty_distribution: dict[DifficultyLevel, int] = Field(..., description="难度分布配置")
    question_count_per_type: dict[TrainingType, int] = Field(..., description="各类型题目数量")

    @validator("difficulty_distribution")
    def validate_difficulty_distribution(
        cls, v: dict[DifficultyLevel, int]
    ) -> dict[DifficultyLevel, int]:
        """验证难度分布总和为100%."""
        total = sum(v.values())
        if total != 100:
            raise ValueError("难度分布总和必须为100%")
        return v


class TrainingParameterTemplate(BaseModel):
    """训练参数模板."""

    id: int | None = None
    name: str = Field(..., description="模板名称")
    description: str | None = Field(None, description="模板描述")
    config: TrainingParameterConfig = Field(..., description="参数配置")
    is_default: bool = Field(False, description="是否为默认模板")
    created_by: int = Field(..., description="创建者ID")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TrainingParameterTemplateRequest(BaseModel):
    """创建/更新训练参数模板请求."""

    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: str | None = Field(None, max_length=500, description="模板描述")
    config: TrainingParameterConfig = Field(..., description="参数配置")
    is_default: bool = Field(False, description="是否为默认模板")


class TrainingParameterTemplateResponse(BaseModel):
    """训练参数模板响应."""

    id: int
    name: str
    description: str | None
    config: TrainingParameterConfig
    is_default: bool
    created_by: int
    created_at: datetime
    updated_at: datetime


# ==================== 周训练配置相关 ====================


class ReadingTrainingConfig(BaseModel):
    """阅读理解训练配置."""

    topic_count: int = Field(..., ge=1, le=10, description="主题数量")
    questions_per_topic: int = Field(..., ge=1, le=10, description="每主题题目数")
    syllabus_relevance_rate: int = Field(80, ge=0, le=100, description="考纲关联度要求")
    topics: list[str] | None = Field(None, description="指定主题列表")


class WritingTrainingConfig(BaseModel):
    """写作训练配置."""

    writing_types: list[str] = Field(..., description="写作类型组合")
    cet4_standard_embedded: bool = Field(True, description="是否嵌入四级评分标准")
    topic_sources: list[str] = Field(default_factory=list, description="题目来源")


class WeeklyTrainingConfig(BaseModel):
    """周训练配置."""

    week_number: int = Field(..., ge=1, le=52, description="周次")
    reading_config: ReadingTrainingConfig | None = Field(None, description="阅读理解配置")
    writing_config: WritingTrainingConfig | None = Field(None, description="写作配置")
    vocabulary_config: dict[str, Any] | None = Field(None, description="词汇训练配置")
    listening_config: dict[str, Any] | None = Field(None, description="听力训练配置")
    translation_config: dict[str, Any] | None = Field(None, description="翻译训练配置")


class WeeklyTrainingRequest(BaseModel):
    """周训练配置请求."""

    class_id: int = Field(..., description="班级ID")
    week_config: WeeklyTrainingConfig = Field(..., description="周训练配置")
    publish_type: str = Field(..., description="发布类型: immediate/scheduled")
    scheduled_time: datetime | None = Field(None, description="定时发布时间")

    @validator("scheduled_time")
    def validate_scheduled_time(cls, v: datetime | None, values: dict[str, Any]) -> datetime | None:
        """验证定时发布时间."""
        if values.get("publish_type") == "scheduled" and not v:
            raise ValueError("定时发布必须指定发布时间")
        return v


# ==================== 训练任务相关 ====================


class TrainingTask(BaseModel):
    """训练任务."""

    id: int | None = None
    class_id: int = Field(..., description="班级ID")
    teacher_id: int = Field(..., description="教师ID")
    task_name: str = Field(..., description="任务名称")
    task_type: str = Field(..., description="任务类型: weekly/custom")
    config: dict[str, Any] = Field(..., description="任务配置")
    status: str = Field("draft", description="任务状态: draft/published/completed")
    publish_time: datetime | None = Field(None, description="发布时间")
    deadline: datetime | None = Field(None, description="截止时间")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TrainingTaskRequest(BaseModel):
    """创建训练任务请求."""

    class_id: int = Field(..., description="班级ID")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    task_type: str = Field(..., description="任务类型")
    config: dict[str, Any] = Field(..., description="任务配置")
    publish_type: str = Field(..., description="发布类型")
    scheduled_time: datetime | None = Field(None, description="定时发布时间")
    deadline: datetime | None = Field(None, description="截止时间")


class TrainingTaskResponse(BaseModel):
    """训练任务响应."""

    id: int
    class_id: int
    teacher_id: int
    task_name: str
    task_type: str
    config: dict[str, Any]
    status: str
    publish_time: datetime | None
    deadline: datetime | None
    created_at: datetime
    updated_at: datetime

    # 统计信息
    total_students: int | None = None
    completed_students: int | None = None
    completion_rate: float | None = None


# ==================== 训练数据分析相关 ====================


class TrainingAnalyticsData(BaseModel):
    """训练数据分析."""

    class_id: int = Field(..., description="班级ID")
    task_id: int | None = Field(None, description="任务ID")
    time_range: str = Field(..., description="时间范围")

    # 整体统计
    total_questions: int = Field(0, description="总题目数")
    total_submissions: int = Field(0, description="总提交数")
    average_score: float = Field(0.0, description="平均分")
    completion_rate: float = Field(0.0, description="完成率")

    # 分类统计
    type_statistics: dict[TrainingType, dict[str, Any]] = Field(
        default_factory=dict, description="类型统计"
    )
    difficulty_statistics: dict[DifficultyLevel, dict[str, Any]] = Field(
        default_factory=dict, description="难度统计"
    )
    knowledge_point_statistics: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="知识点统计"
    )

    # 学生表现
    student_performance: list[dict[str, Any]] = Field(default_factory=list, description="学生表现")
    risk_students: list[dict[str, Any]] = Field(default_factory=list, description="风险学生")


class TrainingAnalyticsRequest(BaseModel):
    """训练数据分析请求."""

    class_id: int = Field(..., description="班级ID")
    task_id: int | None = Field(None, description="任务ID")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    analysis_type: str = Field("comprehensive", description="分析类型")


# ==================== 响应模型 ====================


class TrainingWorkshopResponse(BaseModel):
    """训练工坊通用响应."""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field("", description="响应消息")
    data: Any | None = Field(None, description="响应数据")


class TrainingParameterTemplateListResponse(BaseModel):
    """训练参数模板列表响应."""

    templates: list[TrainingParameterTemplateResponse]
    total: int
    page: int
    page_size: int


class TrainingTaskListResponse(BaseModel):
    """训练任务列表响应."""

    tasks: list[TrainingTaskResponse]
    total: int
    page: int
    page_size: int
