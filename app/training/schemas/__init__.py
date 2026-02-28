"""训练系统Pydantic模式定义."""

from .training_schemas import (  # 自适应学习相关; 基础响应模式; 学习分析相关; 题目批次相关; 题目相关; 训练记录相关; 训练会话相关
    AdaptiveConfigRequest, AdaptiveLearningResponse, BaseResponse, ChartData,
    ChartDataPoint, DifficultyAdjustment, GradingResult, KnowledgePointProgress,
    LearningProgressRequest, LearningProgressResponse, LearningRecommendation,
    PaginatedResponse, PerformanceMetrics, PerformanceReportRequest,
    PerformanceReportResponse, QuestionBatchListResponse, QuestionBatchRequest,
    QuestionBatchResponse, QuestionContentModel, QuestionFilter, QuestionListResponse,
    QuestionRequest, QuestionResponse, QuestionWithAnswerResponse, SubmitAnswerRequest,
    TrainingRecordListResponse, TrainingRecordResponse, TrainingSessionListResponse,
    TrainingSessionRequest, TrainingSessionResponse, TrainingSessionUpdate)

__all__ = [
    # 基础响应模式
    "BaseResponse",
    "PaginatedResponse",
    # 训练会话相关
    "TrainingSessionRequest",
    "TrainingSessionResponse",
    "TrainingSessionUpdate",
    "TrainingSessionListResponse",
    # 题目相关
    "QuestionContentModel",
    "QuestionRequest",
    "QuestionResponse",
    "QuestionWithAnswerResponse",
    "QuestionFilter",
    "QuestionListResponse",
    # 训练记录相关
    "SubmitAnswerRequest",
    "GradingResult",
    "TrainingRecordResponse",
    "TrainingRecordListResponse",
    # 自适应学习相关
    "AdaptiveConfigRequest",
    "DifficultyAdjustment",
    "LearningRecommendation",
    "AdaptiveLearningResponse",
    # 学习分析相关
    "LearningProgressRequest",
    "KnowledgePointProgress",
    "PerformanceMetrics",
    "LearningProgressResponse",
    "PerformanceReportRequest",
    "ChartDataPoint",
    "ChartData",
    "PerformanceReportResponse",
    # 题目批次相关
    "QuestionBatchRequest",
    "QuestionBatchResponse",
    "QuestionBatchListResponse",
]
