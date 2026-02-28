"""AI模块工具类导出."""

from .api_key_pool import (
    APICallManager,
    APIKeyPool,
    APIUsageStats,
    DeepSeekAPIKeyPool,
    get_api_stats,
    get_deepseek_pool,
)
from .content_generator import (
    ContentTemplate,
    LessonPlanGenerator,
    ScheduleOptimizer,
    SmartSuggestionEngine,
    SyllabusGenerator,
)
from .text_utils import (
    calculate_chinese_ratio,
    calculate_text_similarity,
    check_content_length,
    check_content_repetition,
    check_educational_relevance,
    check_special_characters,
    extract_sentences,
    format_ai_error_message,
    generate_cache_key,
)

__all__ = [
    # API密钥池管理
    "APIKeyPool",
    "DeepSeekAPIKeyPool",
    "APICallManager",
    "APIUsageStats",
    "get_deepseek_pool",
    "get_api_stats",
    # 内容生成器
    "ContentTemplate",
    "SyllabusGenerator",
    "LessonPlanGenerator",
    "ScheduleOptimizer",
    "SmartSuggestionEngine",
    # 文本处理工具
    "calculate_text_similarity",
    "calculate_chinese_ratio",
    "check_content_length",
    "check_content_repetition",
    "check_educational_relevance",
    "check_special_characters",
    "extract_sentences",
    "format_ai_error_message",
    "generate_cache_key",
]
