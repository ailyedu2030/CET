"""AI模块数据模式导出."""

from .ai_schemas import (
    AITaskRequest,
    AITaskResponse,
    CollaborationJoinRequest,
    CollaborationSessionResponse,
    CollaborationUpdateRequest,
    LearningAnalysisCreate,
    LearningAnalysisListResponse,
    LearningAnalysisRequest,
    LearningAnalysisResponse,
    LessonPlanCreate,
    LessonPlanGenerationRequest,
    LessonPlanListResponse,
    LessonPlanResponse,
    LessonPlanUpdate,
    LessonScheduleCreate,
    LessonScheduleResponse,
    LessonScheduleUpdate,
    ScheduleGenerationRequest,
    ScheduleListResponse,
    SmartSuggestionRequest,
    SmartSuggestionResponse,
    SyllabusCreate,
    SyllabusGenerationRequest,
    SyllabusListResponse,
    SyllabusResponse,
    SyllabusUpdate,
    TeachingAdjustmentCreate,
    TeachingAdjustmentListResponse,
    TeachingAdjustmentRequest,
    TeachingAdjustmentResponse,
    TeachingAdjustmentUpdate,
)

__all__ = [
    # 大纲相关
    "SyllabusGenerationRequest",
    "SyllabusCreate",
    "SyllabusUpdate",
    "SyllabusResponse",
    "SyllabusListResponse",
    # 教案相关
    "LessonPlanGenerationRequest",
    "LessonPlanCreate",
    "LessonPlanUpdate",
    "LessonPlanResponse",
    "LessonPlanListResponse",
    # 课程表相关
    "ScheduleGenerationRequest",
    "LessonScheduleCreate",
    "LessonScheduleUpdate",
    "LessonScheduleResponse",
    "ScheduleListResponse",
    # 学情分析相关
    "LearningAnalysisRequest",
    "LearningAnalysisCreate",
    "LearningAnalysisResponse",
    "LearningAnalysisListResponse",
    # 教学调整相关
    "TeachingAdjustmentRequest",
    "TeachingAdjustmentCreate",
    "TeachingAdjustmentUpdate",
    "TeachingAdjustmentResponse",
    "TeachingAdjustmentListResponse",
    # AI任务相关
    "AITaskRequest",
    "AITaskResponse",
    # 协作相关
    "CollaborationJoinRequest",
    "CollaborationUpdateRequest",
    "CollaborationSessionResponse",
    # 智能建议相关
    "SmartSuggestionRequest",
    "SmartSuggestionResponse",
]
