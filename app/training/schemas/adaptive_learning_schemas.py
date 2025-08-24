"""自适应学习相关Schema定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.shared.models.enums import DifficultyLevel

# ==================== 错题分析相关Schema ====================


class ErrorCategoryResponse(BaseModel):
    """错误分类响应."""

    category: str = Field(..., description="错误类别")
    category_name: str = Field(..., description="类别名称")
    error_count: int = Field(..., description="错误数量")
    error_rate: float = Field(..., description="错误率")
    recent_errors: list[dict[str, Any]] = Field(default_factory=list, description="最近错误")


class ErrorAnalysisResponse(BaseModel):
    """错题分析响应."""

    student_id: int = Field(..., description="学生ID")
    analysis_period_days: int = Field(..., description="分析周期天数")
    total_errors: int = Field(..., description="总错误数")
    error_categories: list[ErrorCategoryResponse] = Field(
        default_factory=list, description="错误分类"
    )
    error_frequency: dict[str, int] = Field(default_factory=dict, description="错误频率")
    error_trend: dict[str, Any] = Field(default_factory=dict, description="错误趋势")
    weak_knowledge_points: list[dict[str, Any]] = Field(
        default_factory=list, description="薄弱知识点"
    )
    improvement_suggestions: list[str] = Field(default_factory=list, description="改进建议")
    analysis_time: datetime = Field(..., description="分析时间")


class ErrorPatternResponse(BaseModel):
    """错题模式分析响应."""

    student_id: int = Field(..., description="学生ID")
    analysis_period_days: int = Field(..., description="分析周期天数")
    total_errors: int = Field(..., description="总错误数")
    error_frequency: dict[str, int] = Field(default_factory=dict, description="错误频率")
    error_trend: dict[str, Any] = Field(default_factory=dict, description="错误趋势")
    weak_knowledge_points: list[dict[str, Any]] = Field(
        default_factory=list, description="薄弱知识点"
    )
    improvement_suggestions: list[str] = Field(default_factory=list, description="改进建议")
    analysis_time: datetime = Field(..., description="分析时间")


class KnowledgeGapResponse(BaseModel):
    """知识缺口响应."""

    knowledge_point_id: int = Field(..., description="知识点ID")
    knowledge_point_title: str = Field(..., description="知识点标题")
    difficulty_level: DifficultyLevel = Field(..., description="难度级别")
    total_attempts: int = Field(..., description="总尝试次数")
    error_count: int = Field(..., description="错误次数")
    error_rate: float = Field(..., description="错误率")
    mastery_level: str = Field(..., description="掌握程度")
    error_types: dict[str, int] = Field(default_factory=dict, description="错误类型分布")
    last_error_time: datetime | None = Field(None, description="最后错误时间")
    improvement_priority: float = Field(..., description="改进优先级")


class ReinforcementPlanResponse(BaseModel):
    """强化训练计划响应."""

    student_id: int = Field(..., description="学生ID")
    plan_created_at: datetime = Field(..., description="计划创建时间")
    knowledge_gaps_count: int = Field(..., description="知识缺口数量")
    training_modules: list[dict[str, Any]] = Field(default_factory=list, description="训练模块")
    estimated_completion_days: int = Field(..., description="预计完成天数")
    priority_focus_areas: list[str] = Field(default_factory=list, description="重点关注领域")


# ==================== 遗忘曲线相关Schema ====================


class ForgettingCurveResponse(BaseModel):
    """遗忘曲线响应."""

    student_id: int = Field(..., description="学生ID")
    question_id: int = Field(..., description="题目ID")
    current_retention: float = Field(..., description="当前记忆保持率")
    learning_sessions: int = Field(..., description="学习次数")
    curve_data: list[dict[str, Any]] = Field(default_factory=list, description="曲线数据点")
    next_review_date: datetime = Field(..., description="下次复习时间")
    mastery_status: str = Field(..., description="掌握状态")
    analysis_time: datetime = Field(..., description="分析时间")


class ReviewScheduleResponse(BaseModel):
    """复习计划响应."""

    student_id: int = Field(..., description="学生ID")
    schedule_period_days: int = Field(..., description="计划周期天数")
    total_review_items: int = Field(..., description="总复习项目数")
    urgent_review_items: int = Field(..., description="紧急复习项目数")
    daily_schedule: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict, description="每日计划"
    )
    generated_at: datetime = Field(..., description="生成时间")


class MemoryStrengthUpdate(BaseModel):
    """记忆强度更新."""

    student_id: int = Field(..., description="学生ID")
    question_id: int = Field(..., description="题目ID")
    previous_retention: float = Field(..., description="之前保持率")
    new_retention: float = Field(..., description="新保持率")
    performance_score: float = Field(..., description="表现分数")
    strength_boost: float = Field(..., description="强度提升")
    next_review_date: datetime = Field(..., description="下次复习时间")
    mastery_level: str = Field(..., description="掌握程度")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 学习策略相关Schema ====================


class LearningStyleResponse(BaseModel):
    """学习风格响应."""

    style_type: str = Field(..., description="学习风格类型")
    characteristics: list[str] = Field(default_factory=list, description="特征描述")
    strengths: list[str] = Field(default_factory=list, description="优势")
    recommendations: list[str] = Field(default_factory=list, description="建议")


class PerformanceAnalysis(BaseModel):
    """表现分析."""

    avg_score: float = Field(..., description="平均分数")
    trend: str = Field(..., description="趋势")
    consistency: float = Field(..., description="一致性")
    recent_sessions: int = Field(..., description="最近会话数")
    improvement_rate: float = Field(..., description="改进率")


class LearningStrategyResponse(BaseModel):
    """学习策略推荐响应."""

    student_id: int = Field(..., description="学生ID")
    learning_style: str = Field(..., description="学习风格")
    current_performance: dict[str, Any] = Field(default_factory=dict, description="当前表现")
    weak_areas: list[str] = Field(default_factory=list, description="薄弱环节")
    recommendations: list[str] = Field(default_factory=list, description="策略建议")
    confidence_score: float = Field(..., description="推荐置信度")
    generated_at: datetime = Field(..., description="生成时间")


# ==================== 知识图谱相关Schema ====================


class KnowledgePointInfo(BaseModel):
    """知识点信息."""

    knowledge_point_id: int = Field(..., description="知识点ID")
    title: str = Field(..., description="标题")
    difficulty_level: DifficultyLevel = Field(..., description="难度级别")
    importance_score: float = Field(..., description="重要性分数")
    estimated_time: int = Field(..., description="预计学习时间(分钟)")
    is_core: bool = Field(..., description="是否核心知识点")


class LearningPathStep(BaseModel):
    """学习路径步骤."""

    step: int = Field(..., description="步骤序号")
    knowledge_point: KnowledgePointInfo = Field(..., description="知识点信息")
    prerequisites: list[int] = Field(default_factory=list, description="前置知识点ID")
    dependents: list[int] = Field(default_factory=list, description="后续知识点ID")
    estimated_time: int = Field(..., description="预计学习时间")


class LearningPathResponse(BaseModel):
    """学习路径响应."""

    start_knowledge_id: int = Field(..., description="起始知识点ID")
    target_knowledge_id: int = Field(..., description="目标知识点ID")
    path_length: int = Field(..., description="路径长度")
    learning_path: list[LearningPathStep] = Field(default_factory=list, description="学习路径")
    estimated_total_time: int = Field(..., description="预计总时间(分钟)")


class KnowledgeDependencyResponse(BaseModel):
    """知识点依赖关系响应."""

    knowledge_point_id: int = Field(..., description="知识点ID")
    prerequisites: list[KnowledgePointInfo] = Field(default_factory=list, description="前置知识点")
    dependents: list[KnowledgePointInfo] = Field(default_factory=list, description="后续知识点")
    dependency_depth: int = Field(..., description="依赖深度")
    critical_paths: list[list[int]] = Field(default_factory=list, description="关键路径")
    influence_scope: int = Field(..., description="影响范围")
    centrality_score: float = Field(..., description="中心性分数")


class KnowledgeRecommendation(BaseModel):
    """知识点推荐."""

    knowledge_point: KnowledgePointInfo = Field(..., description="知识点信息")
    recommendation_score: float = Field(..., description="推荐分数")
    readiness_level: str = Field(..., description="准备程度")
    learning_priority: str = Field(..., description="学习优先级")
    estimated_difficulty: float = Field(..., description="预估难度")


class NextKnowledgePointsResponse(BaseModel):
    """下一个知识点推荐响应."""

    student_id: int = Field(..., description="学生ID")
    mastered_count: int = Field(..., description="已掌握知识点数量")
    recommendations: list[KnowledgeRecommendation] = Field(
        default_factory=list, description="推荐列表"
    )
    total_available: int = Field(..., description="总可用数量")


# ==================== 学习效果评估Schema ====================


class LearningEffectiveness(BaseModel):
    """学习效果评估."""

    student_id: int = Field(..., description="学生ID")
    evaluation_period_days: int = Field(..., description="评估周期天数")
    overall_progress: float = Field(..., description="整体进步")
    knowledge_mastery_rate: float = Field(..., description="知识掌握率")
    learning_efficiency: float = Field(..., description="学习效率")
    retention_rate: float = Field(..., description="记忆保持率")
    engagement_score: float = Field(..., description="参与度分数")
    improvement_areas: list[str] = Field(default_factory=list, description="改进领域")
    strengths: list[str] = Field(default_factory=list, description="优势领域")
    next_goals: list[str] = Field(default_factory=list, description="下一步目标")
    evaluation_time: datetime = Field(..., description="评估时间")


class AdaptiveLearningMetrics(BaseModel):
    """自适应学习指标."""

    difficulty_adjustment_accuracy: float = Field(..., description="难度调整准确性")
    personalization_effectiveness: float = Field(..., description="个性化有效性")
    learning_path_optimization: float = Field(..., description="学习路径优化度")
    error_reduction_rate: float = Field(..., description="错误减少率")
    knowledge_transfer_rate: float = Field(..., description="知识迁移率")
    adaptive_algorithm_performance: dict[str, float] = Field(
        default_factory=dict, description="自适应算法性能"
    )


# ==================== 请求Schema ====================


class ErrorAnalysisRequest(BaseModel):
    """错题分析请求."""

    student_id: int = Field(..., description="学生ID")
    analysis_days: int = Field(30, ge=1, le=365, description="分析天数")
    include_categories: list[str] = Field(default_factory=list, description="包含的错误类别")


class ReinforcementPlanRequest(BaseModel):
    """强化训练计划请求."""

    student_id: int = Field(..., description="学生ID")
    focus_knowledge_points: list[int] = Field(default_factory=list, description="重点知识点")
    training_intensity: str = Field("moderate", description="训练强度")
    target_completion_days: int = Field(14, ge=1, le=90, description="目标完成天数")


class LearningStrategyRequest(BaseModel):
    """学习策略请求."""

    student_id: int = Field(..., description="学生ID")
    include_learning_style_analysis: bool = Field(True, description="包含学习风格分析")
    include_performance_prediction: bool = Field(True, description="包含表现预测")
    strategy_scope: str = Field("comprehensive", description="策略范围")
