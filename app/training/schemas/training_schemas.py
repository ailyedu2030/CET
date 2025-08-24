"""训练系统相关的Pydantic模式定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

from app.shared.models.enums import (
    DifficultyLevel,
    GradingStatus,
    QuestionType,
    TrainingType,
)

# ==================== 基础响应模式 ====================


class BaseResponse(BaseModel):
    """基础响应模式."""

    success: bool = Field(default=True, description="操作是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class PaginatedResponse(BaseModel):
    """分页响应模式."""

    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")
    # 兼容性字段
    page_size: int = Field(description="每页大小（别名）")
    total_items: int = Field(description="总数量（别名）")
    total_pages: int = Field(description="总页数（别名）")


# ==================== 训练会话相关模式 ====================


class TrainingSessionRequest(BaseModel):
    """创建训练会话请求模式."""

    session_name: str = Field(..., min_length=1, max_length=200, description="会话名称")
    session_type: TrainingType = Field(..., description="训练类型")
    description: str | None = Field(None, max_length=1000, description="会话描述")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.ELEMENTARY, description="难度等级"
    )
    question_count: int = Field(..., ge=1, le=100, description="题目数量")
    time_limit: int | None = Field(None, ge=1, le=300, description="时间限制（分钟）")
    knowledge_points: list[str] = Field(default_factory=list, description="指定知识点")
    auto_adaptive: bool = Field(default=True, description="是否启用自适应调整")

    @validator("session_name")
    def validate_session_name(cls, v: str) -> str:
        """验证会话名称."""
        if not v.strip():
            raise ValueError("会话名称不能为空")
        return v.strip()


class TrainingSessionResponse(BaseModel):
    """训练会话响应模式."""

    id: int = Field(description="会话ID")
    student_id: int = Field(description="学生ID")
    session_name: str = Field(description="会话名称")
    session_type: TrainingType = Field(description="训练类型")
    training_type: TrainingType = Field(description="训练类型（别名）")
    description: str | None = Field(description="会话描述")
    difficulty_level: DifficultyLevel = Field(description="难度等级")
    question_count: int = Field(description="题目数量")
    time_limit: int | None = Field(description="时间限制（分钟）")
    status: str = Field(description="会话状态")
    started_at: datetime = Field(description="开始时间")
    completed_at: datetime | None = Field(description="完成时间")
    completion_time: int | None = Field(description="完成用时（秒）")
    total_questions: int = Field(description="总题目数")
    correct_answers: int = Field(description="正确答案数")
    total_score: float = Field(description="总分数")
    time_spent: int = Field(description="实际用时（秒）")
    accuracy_rate: float = Field(description="正确率")
    initial_level: int = Field(description="初始难度等级")
    final_level: int = Field(description="最终难度等级")
    adaptation_data: dict[str, Any] = Field(description="自适应调整数据")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    @validator("accuracy_rate", pre=True, always=True)
    def calculate_accuracy_rate(cls, v: float, values: dict[str, Any]) -> float:
        """计算正确率."""
        if "total_questions" in values and values["total_questions"] > 0:
            correct_answers = int(values.get("correct_answers", 0) or 0)
            total_questions = int(values["total_questions"])
            return float(round(correct_answers / total_questions * 100, 2))  # type: ignore[no-any-return]
        return 0.0


class TrainingSessionUpdate(BaseModel):
    """更新训练会话请求模式."""

    session_name: str | None = Field(None, min_length=1, max_length=200, description="会话名称")
    description: str | None = Field(None, max_length=1000, description="会话描述")
    status: str | None = Field(None, description="会话状态")
    completed_at: datetime | None = Field(None, description="完成时间")
    total_score: float | None = Field(None, ge=0, description="总分数")
    time_spent: int | None = Field(None, ge=0, description="实际用时（秒）")


class TrainingSessionListResponse(BaseModel):
    """训练会话列表响应模式."""

    sessions: list[TrainingSessionResponse] = Field(description="训练会话列表")
    pagination: PaginatedResponse = Field(description="分页信息")


# ==================== 题目相关模式 ====================


class QuestionContentModel(BaseModel):
    """题目内容模式."""

    text: str = Field(..., description="题目文本")
    options: list[str] | None = Field(None, description="选项（适用于选择题）")
    audio_url: str | None = Field(None, description="音频文件URL（听力题）")
    image_url: str | None = Field(None, description="图片URL")
    passages: list[str] | None = Field(None, description="阅读材料")


class QuestionRequest(BaseModel):
    """创建题目请求模式."""

    question_type: QuestionType = Field(..., description="题目类型")
    training_type: TrainingType = Field(..., description="训练类型")
    title: str = Field(..., min_length=1, max_length=500, description="题目标题")
    content: QuestionContentModel = Field(..., description="题目内容")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.ELEMENTARY, description="难度等级"
    )
    max_score: float = Field(default=10.0, ge=0, le=100, description="满分分数")
    time_limit: int | None = Field(None, ge=1, le=3600, description="时间限制（秒）")
    knowledge_points: list[str] = Field(default_factory=list, description="知识点标签")
    tags: list[str] = Field(default_factory=list, description="题目标签")
    correct_answer: dict[str, Any] = Field(..., description="正确答案")
    answer_analysis: str | None = Field(None, description="答案解析")
    grading_criteria: dict[str, Any] = Field(default_factory=dict, description="评分标准")


class QuestionResponse(BaseModel):
    """题目响应模式."""

    id: int = Field(description="题目ID")
    question_type: QuestionType = Field(description="题目类型")
    training_type: TrainingType = Field(description="训练类型")
    title: str = Field(description="题目标题")
    content: dict[str, Any] = Field(description="题目内容")
    difficulty_level: DifficultyLevel = Field(description="难度等级")
    max_score: float = Field(description="满分分数")
    time_limit: int | None = Field(description="时间限制（秒）")
    knowledge_points: list[str] = Field(description="知识点标签")
    tags: list[str] = Field(description="题目标签")
    is_active: bool = Field(description="是否启用")
    usage_count: int = Field(description="使用次数")
    average_score: float = Field(description="平均分数")
    correct_rate: float = Field(description="正确率")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class QuestionWithAnswerResponse(QuestionResponse):
    """带答案的题目响应模式（仅供教师/管理员使用）."""

    correct_answer: dict[str, Any] = Field(description="正确答案")
    answer_analysis: str | None = Field(description="答案解析")
    grading_criteria: dict[str, Any] = Field(description="评分标准")


class QuestionFilter(BaseModel):
    """题目筛选条件."""

    question_type: QuestionType | None = Field(None, description="题目类型")
    training_type: TrainingType | None = Field(None, description="训练类型")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    knowledge_points: list[str] | None = Field(None, description="知识点筛选")
    tags: list[str] | None = Field(None, description="标签筛选")
    is_active: bool | None = Field(None, description="是否启用")
    created_after: datetime | None = Field(None, description="创建时间起始")
    created_before: datetime | None = Field(None, description="创建时间结束")


class QuestionListResponse(BaseModel):
    """题目列表响应模式."""

    questions: list[QuestionResponse] = Field(description="题目列表")
    pagination: PaginatedResponse = Field(description="分页信息")


# ==================== 训练记录相关模式 ====================


class SubmitAnswerRequest(BaseModel):
    """提交答案请求模式."""

    session_id: int = Field(..., description="训练会话ID")
    question_id: int = Field(..., description="题目ID")
    user_answer: dict[str, Any] = Field(..., description="用户答案")
    start_time: datetime = Field(..., description="开始答题时间")
    end_time: datetime | None = Field(None, description="结束答题时间")
    time_spent: int = Field(default=0, ge=0, description="用时（秒）")

    @validator("time_spent", pre=True, always=True)
    def calculate_time_spent(cls, v: int, values: dict[str, Any]) -> int:
        """计算答题用时."""
        if (
            "start_time" in values
            and "end_time" in values
            and values["end_time"]
            and values["start_time"]
        ):
            delta = values["end_time"] - values["start_time"]
            return max(0, int(delta.total_seconds()))
        return v


class GradingResult(BaseModel):
    """批改结果模式."""

    is_correct: bool = Field(description="是否正确")
    score: float = Field(ge=0, description="得分")
    max_score: float = Field(ge=0, description="满分")
    grading_status: GradingStatus = Field(description="批改状态")
    ai_feedback: dict[str, Any] = Field(description="AI反馈内容")
    ai_confidence: float = Field(ge=0, le=1, description="AI置信度")
    knowledge_points_mastered: list[str] = Field(description="掌握的知识点")
    knowledge_points_weak: list[str] = Field(description="薄弱的知识点")
    detailed_feedback: str | None = Field(None, description="详细反馈")
    improvement_suggestions: list[str] = Field(default_factory=list, description="改进建议")


class TrainingRecordResponse(BaseModel):
    """训练记录响应模式."""

    id: int = Field(description="记录ID")
    session_id: int = Field(description="训练会话ID")
    student_id: int = Field(description="学生ID")
    question_id: int = Field(description="题目ID")
    user_answer: dict[str, Any] = Field(description="用户答案")
    grading_result: GradingResult = Field(description="批改结果")
    start_time: datetime = Field(description="开始时间")
    end_time: datetime | None = Field(description="结束时间")
    time_spent: int = Field(description="用时（秒）")
    created_at: datetime = Field(description="创建时间")


class TrainingRecordListResponse(BaseModel):
    """训练记录列表响应模式."""

    records: list[TrainingRecordResponse] = Field(description="训练记录列表")
    pagination: PaginatedResponse = Field(description="分页信息")


# ==================== 自适应学习相关模式 ====================


class AdaptiveConfigRequest(BaseModel):
    """自适应配置请求模式."""

    student_id: int = Field(..., description="学生ID")
    training_type: TrainingType = Field(..., description="训练类型")
    target_accuracy: float = Field(default=0.75, ge=0.5, le=1.0, description="目标正确率")
    adjustment_sensitivity: float = Field(default=0.5, ge=0.1, le=1.0, description="调整敏感度")
    max_difficulty_jump: int = Field(default=1, ge=1, le=3, description="最大难度跳跃")
    knowledge_weight: dict[str, float] = Field(default_factory=dict, description="知识点权重")


class DifficultyAdjustment(BaseModel):
    """难度调整模式."""

    current_level: int = Field(description="当前难度等级")
    suggested_level: int = Field(description="建议难度等级")
    adjustment_reason: str = Field(description="调整原因")
    confidence_score: float = Field(ge=0, le=1, description="调整置信度")
    supporting_data: dict[str, Any] = Field(description="支持数据")


class LearningRecommendation(BaseModel):
    """学习推荐模式."""

    training_type: TrainingType = Field(description="推荐训练类型")
    difficulty_level: DifficultyLevel = Field(description="推荐难度等级")
    knowledge_points: list[str] = Field(description="推荐知识点")
    question_count: int = Field(description="推荐题目数量")
    time_allocation: int = Field(description="建议时间分配（分钟）")
    priority_score: float = Field(ge=0, le=1, description="优先级分数")
    reason: str = Field(description="推荐理由")
    expected_improvement: dict[str, float] = Field(description="预期提升")


class AdaptiveLearningResponse(BaseModel):
    """自适应学习响应模式."""

    student_id: int = Field(description="学生ID")
    current_config: AdaptiveConfigRequest = Field(description="当前配置")
    difficulty_adjustment: DifficultyAdjustment | None = Field(None, description="难度调整")
    recommendations: list[LearningRecommendation] = Field(description="学习推荐")
    performance_trend: dict[str, Any] = Field(description="表现趋势")
    next_session_config: dict[str, Any] = Field(description="下次会话配置")


# ==================== 学习分析相关模式 ====================


class LearningProgressRequest(BaseModel):
    """学习进度请求模式."""

    student_id: int = Field(..., description="学生ID")
    training_type: TrainingType | None = Field(None, description="训练类型筛选")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    include_details: bool = Field(default=False, description="是否包含详细信息")


class KnowledgePointProgress(BaseModel):
    """知识点进度模式."""

    knowledge_point: str = Field(description="知识点名称")
    mastery_level: float = Field(ge=0, le=1, description="掌握程度")
    practice_count: int = Field(description="练习次数")
    correct_rate: float = Field(ge=0, le=1, description="正确率")
    average_score: float = Field(description="平均分数")
    trend: str = Field(description="学习趋势")  # improving, stable, declining
    last_practiced: datetime | None = Field(description="最后练习时间")


class PerformanceMetrics(BaseModel):
    """表现指标模式."""

    total_sessions: int = Field(description="总训练次数")
    total_questions: int = Field(description="总题目数")
    correct_answers: int = Field(description="正确答案数")
    total_score: float = Field(description="总分数")
    average_score: float = Field(description="平均分数")
    accuracy_rate: float = Field(description="正确率")
    total_time_spent: int = Field(description="总用时（秒）")
    average_time_per_question: float = Field(description="平均每题用时（秒）")
    improvement_rate: float = Field(description="提升速度")
    consistency_score: float = Field(description="稳定性分数")


class LearningProgressResponse(BaseModel):
    """学习进度响应模式."""

    student_id: int = Field(description="学生ID")
    training_type: TrainingType | None = Field(description="训练类型")
    date_range: dict[str, datetime | None] = Field(description="日期范围")
    overall_metrics: PerformanceMetrics = Field(description="整体指标")
    knowledge_point_progress: list[KnowledgePointProgress] = Field(description="知识点进度")
    difficulty_progression: dict[str, Any] = Field(description="难度进展")
    time_distribution: dict[str, int] = Field(description="时间分布")
    strengths: list[str] = Field(description="优势领域")
    weaknesses: list[str] = Field(description="薄弱环节")
    recommendations: list[str] = Field(description="改进建议")
    updated_at: datetime = Field(description="数据更新时间")


class PerformanceReportRequest(BaseModel):
    """表现报告请求模式."""

    student_id: int = Field(..., description="学生ID")
    report_type: str = Field(
        default="comprehensive", description="报告类型"
    )  # comprehensive, summary, detailed
    training_types: list[TrainingType] | None = Field(None, description="训练类型筛选")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    include_charts: bool = Field(default=True, description="是否包含图表数据")
    language: str = Field(default="zh", description="报告语言")


class ChartDataPoint(BaseModel):
    """图表数据点模式."""

    x: str | int | float | datetime = Field(description="X轴数据")
    y: int | float = Field(description="Y轴数据")
    label: str | None = Field(None, description="标签")
    category: str | None = Field(None, description="分类")


class ChartData(BaseModel):
    """图表数据模式."""

    chart_type: str = Field(description="图表类型")  # line, bar, pie, scatter
    title: str = Field(description="图表标题")
    data: list[ChartDataPoint] = Field(description="数据点")
    x_axis_label: str | None = Field(None, description="X轴标签")
    y_axis_label: str | None = Field(None, description="Y轴标签")
    colors: list[str] | None = Field(None, description="颜色配置")


class PerformanceReportResponse(BaseModel):
    """表现报告响应模式."""

    student_id: int = Field(description="学生ID")
    report_type: str = Field(description="报告类型")
    generated_at: datetime = Field(description="生成时间")
    date_range: dict[str, datetime | None] = Field(description="日期范围")
    executive_summary: str = Field(description="执行摘要")
    key_findings: list[str] = Field(description="关键发现")
    performance_metrics: PerformanceMetrics = Field(description="表现指标")
    progress_analysis: dict[str, Any] = Field(description="进度分析")
    chart_data: list[ChartData] = Field(description="图表数据")
    detailed_recommendations: list[dict[str, Any]] = Field(description="详细建议")
    next_steps: list[str] = Field(description="下一步行动")


# ==================== 题目批次相关模式 ====================


class QuestionBatchRequest(BaseModel):
    """题目批次请求模式."""

    name: str = Field(..., min_length=1, max_length=200, description="批次名称")
    description: str | None = Field(None, max_length=1000, description="批次描述")
    training_type: TrainingType = Field(..., description="训练类型")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.ELEMENTARY, description="难度等级"
    )
    question_count: int = Field(default=0, ge=0, description="题目数量")
    time_limit: int | None = Field(None, ge=1, le=300, description="时间限制（分钟）")
    knowledge_points: list[str] = Field(default_factory=list, description="涵盖的知识点")
    tags: list[str] = Field(default_factory=list, description="批次标签")
    question_ids: list[int] = Field(default_factory=list, description="包含的题目ID列表")


class QuestionBatchResponse(BaseModel):
    """题目批次响应模式."""

    id: int = Field(description="批次ID")
    name: str = Field(description="批次名称")
    description: str | None = Field(description="批次描述")
    training_type: TrainingType = Field(description="训练类型")
    difficulty_level: DifficultyLevel = Field(description="难度等级")
    question_count: int = Field(description="题目数量")
    time_limit: int | None = Field(description="时间限制（分钟）")
    knowledge_points: list[str] = Field(description="涵盖的知识点")
    tags: list[str] = Field(description="批次标签")
    is_active: bool = Field(description="是否启用")
    created_by: int | None = Field(description="创建者ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class QuestionBatchListResponse(BaseModel):
    """题目批次列表响应模式."""

    batches: list[QuestionBatchResponse] = Field(description="题目批次列表")
    pagination: PaginatedResponse = Field(description="分页信息")
