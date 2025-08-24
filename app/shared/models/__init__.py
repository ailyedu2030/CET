"""共享模型模块 - 导出所有模型类和枚举."""

from pydantic import BaseModel

from .enums import (
    AIModelType,
    AITaskType,
    CacheType,
    ContentType,
    CourseShareLevel,
    CourseStatus,
    DifficultyLevel,
    EventType,
    GradingStatus,
    LearningStatus,
    LogLevel,
    NotificationStatus,
    PermissionType,
    QuestionType,
    TaskStatus,
    TrainingType,
    UserType,
)
from .learning_mixins import (
    AdaptiveLearningMixin,
    AIAnalysisMixin,
    ComplianceMixin,
    LearningProgressMixin,
)
from .metrics import (
    AIServiceMetrics,
    LearningMetrics,
    SystemMetrics,
    TeachingMetrics,
)
from .validators import (
    ResourceValidator,
    TrainingValidator,
    UserValidator,
)

__all__ = [
    # Pydantic BaseModel
    "BaseModel",
    # 枚举类型
    "AIModelType",
    "AITaskType",
    "CacheType",
    "ContentType",
    "CourseShareLevel",
    "CourseStatus",
    "DifficultyLevel",
    "EventType",
    "GradingStatus",
    "LearningStatus",
    "LogLevel",
    "NotificationStatus",
    "PermissionType",
    "QuestionType",
    "TaskStatus",
    "TrainingType",
    "UserType",
    # 混入类
    "AIAnalysisMixin",
    "AdaptiveLearningMixin",
    "ComplianceMixin",
    "LearningProgressMixin",
    # 指标类
    "AIServiceMetrics",
    "LearningMetrics",
    "SystemMetrics",
    "TeachingMetrics",
    # 验证器类
    "ResourceValidator",
    "TrainingValidator",
    "UserValidator",
]
