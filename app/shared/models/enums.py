"""共享枚举类型定义."""

from enum import Enum


class UserType(str, Enum):
    """用户类型枚举."""

    ADMIN = "admin"  # 管理员
    TEACHER = "teacher"  # 教师
    STUDENT = "student"  # 学生


class TrainingType(str, Enum):
    """训练类型枚举."""

    VOCABULARY = "vocabulary"  # 词汇训练
    LISTENING = "listening"  # 听力训练
    READING = "reading"  # 阅读训练
    WRITING = "writing"  # 写作训练
    TRANSLATION = "translation"  # 翻译训练
    GRAMMAR = "grammar"  # 语法训练
    COMPREHENSIVE = "comprehensive"  # 综合训练


class DifficultyLevel(int, Enum):
    """难度等级枚举."""

    BEGINNER = 1  # 初级
    ELEMENTARY = 2  # 基础
    INTERMEDIATE = 3  # 中级
    UPPER_INTERMEDIATE = 4  # 中高级
    ADVANCED = 5  # 高级


class QuestionType(str, Enum):
    """题目类型枚举."""

    MULTIPLE_CHOICE = "multiple_choice"  # 选择题
    FILL_BLANK = "fill_blank"  # 填空题
    TRUE_FALSE = "true_false"  # 判断题
    SHORT_ANSWER = "short_answer"  # 简答题
    ESSAY = "essay"  # 作文题
    LISTENING_COMPREHENSION = "listening_comprehension"  # 听力理解
    READING_COMPREHENSION = "reading_comprehension"  # 阅读理解
    TRANSLATION_EN_TO_CN = "translation_en_to_cn"  # 英译中
    TRANSLATION_CN_TO_EN = "translation_cn_to_en"  # 中译英


class GradingStatus(str, Enum):
    """批改状态枚举."""

    PENDING = "pending"  # 待批改
    GRADING = "grading"  # 批改中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 批改失败
    REVIEWING = "reviewing"  # 人工复审中


class LearningStatus(str, Enum):
    """学习状态枚举."""

    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    PAUSED = "paused"  # 已暂停
    ABANDONED = "abandoned"  # 已放弃


class CourseStatus(str, Enum):
    """课程状态枚举."""

    PREPARING = "preparing"  # 筹备中
    UNDER_REVIEW = "under_review"  # 审核中
    APPROVED = "approved"  # 已通过审核
    PUBLISHED = "published"  # 已上线
    SUSPENDED = "suspended"  # 已暂停
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


class CourseShareLevel(str, Enum):
    """课程共享级别枚举."""

    PRIVATE = "private"  # 私有
    CLASS_SHARED = "class_shared"  # 班级内共享
    SCHOOL_SHARED = "school_shared"  # 全校共享
    PUBLIC = "public"  # 公开


class NotificationStatus(str, Enum):
    """通知状态枚举."""

    PENDING = "pending"  # 待发送
    SENT = "sent"  # 已发送
    DELIVERED = "delivered"  # 已送达
    READ = "read"  # 已读
    FAILED = "failed"  # 发送失败


class ContentType(str, Enum):
    """内容类型枚举."""

    TEXT = "text"  # 文本
    IMAGE = "image"  # 图片
    AUDIO = "audio"  # 音频
    VIDEO = "video"  # 视频
    DOCUMENT = "document"  # 文档
    INTERACTIVE = "interactive"  # 交互式内容


class PermissionType(str, Enum):
    """权限类型枚举."""

    # 用户管理权限
    USER_CREATE = "user_create"
    USER_READ = "user_read"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_AUDIT = "user_audit"

    # 课程管理权限
    COURSE_CREATE = "course_create"
    COURSE_READ = "course_read"
    COURSE_UPDATE = "course_update"
    COURSE_DELETE = "course_delete"
    COURSE_ASSIGN = "course_assign"

    # 训练管理权限
    TRAINING_CREATE = "training_create"
    TRAINING_READ = "training_read"
    TRAINING_UPDATE = "training_update"
    TRAINING_DELETE = "training_delete"
    TRAINING_GRADE = "training_grade"

    # 系统管理权限
    SYSTEM_MONITOR = "system_monitor"
    SYSTEM_CONFIG = "system_config"
    SYSTEM_BACKUP = "system_backup"

    # 数据分析权限
    ANALYTICS_VIEW = "analytics_view"
    ANALYTICS_EXPORT = "analytics_export"


class TaskStatus(str, Enum):
    """任务状态枚举."""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消
    RETRYING = "retrying"  # 重试中


class AIModelType(str, Enum):
    """AI模型类型枚举."""

    DEEPSEEK_CHAT = "deepseek-chat"  # DeepSeek对话模型
    DEEPSEEK_REASONER = "deepseek-reasoner"  # DeepSeek推理模型
    DEEPSEEK_CODER = "deepseek-coder"  # DeepSeek代码模型
    DEEPSEEK_LITE = "deepseek-lite"  # DeepSeek轻量模型


class AITaskType(str, Enum):
    """AI任务类型枚举."""

    # 批改相关
    WRITING_GRADING = "writing_grading"
    MULTIPLE_CHOICE_GRADING = "multiple_choice_grading"
    TRANSLATION_GRADING = "translation_grading"

    # 生成相关
    QUESTION_GENERATION = "question_generation"
    CONTENT_GENERATION = "content_generation"
    SYLLABUS_GENERATION = "syllabus_generation"

    # 分析相关
    LEARNING_ANALYSIS = "learning_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"

    # 辅助相关
    WRITING_ASSIST = "writing_assist"
    GRAMMAR_CHECK = "grammar_check"
    VOCABULARY_EXPLANATION = "vocabulary_explanation"


class CacheType(str, Enum):
    """缓存类型枚举."""

    USER_SESSION = "user_session"  # 用户会话
    API_RESPONSE = "api_response"  # API响应
    DATABASE_QUERY = "database_query"  # 数据库查询
    AI_RESULT = "ai_result"  # AI结果
    STATIC_CONTENT = "static_content"  # 静态内容

    # 需求18新增缓存类型
    RESOURCE_DATA = "resource_data"  # 资源数据
    KNOWLEDGE_DATA = "knowledge_data"  # 知识点数据
    PERMISSION = "permission"  # 权限数据
    SYSTEM_DATA = "system_data"  # 系统数据


class MetricType(str, Enum):
    """指标类型枚举."""

    # 性能指标
    RESPONSE_TIME = "response_time"  # 响应时间
    THROUGHPUT = "throughput"  # 吞吐量
    ERROR_RATE = "error_rate"  # 错误率
    SUCCESS_RATE = "success_rate"  # 成功率

    # 资源指标
    CPU_USAGE = "cpu_usage"  # CPU使用率
    MEMORY_USAGE = "memory_usage"  # 内存使用率
    DISK_USAGE = "disk_usage"  # 磁盘使用率
    NETWORK_THROUGHPUT = "network_throughput"  # 网络吞吐量
    ACTIVE_CONNECTIONS = "active_connections"  # 活跃连接数


class AlertLevel(str, Enum):
    """告警级别枚举."""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


class PriorityLevel(int, Enum):
    """优先级枚举."""

    LOW = 1  # 低优先级
    NORMAL = 2  # 普通优先级
    HIGH = 3  # 高优先级
    URGENT = 4  # 紧急优先级


class LogLevel(str, Enum):
    """日志级别枚举."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(str, Enum):
    """事件类型枚举."""

    # 用户事件
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"

    # 学习事件
    TRAINING_START = "training_start"
    TRAINING_COMPLETE = "training_complete"
    QUESTION_ANSWER = "question_answer"

    # 系统事件
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ERROR_OCCURRED = "error_occurred"

    # AI事件
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"


class ResourceType(str, Enum):
    """资源类型枚举."""

    TEXTBOOK = "textbook"  # 教材
    SYLLABUS = "syllabus"  # 考纲
    VOCABULARY = "vocabulary"  # 词汇库
    HOTSPOT = "hotspot"  # 热点资源
    DOCUMENT = "document"  # 文档
    AUDIO = "audio"  # 音频
    VIDEO = "video"  # 视频
    IMAGE = "image"  # 图片


class ProcessingStatus(str, Enum):
    """处理状态枚举."""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 处理失败
    CANCELLED = "cancelled"  # 已取消


class PermissionLevel(str, Enum):
    """权限级别枚举."""

    PRIVATE = "private"  # 私有
    CLASS_SHARED = "class_shared"  # 班级共享
    PUBLIC = "public"  # 公开
