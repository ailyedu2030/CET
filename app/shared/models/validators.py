"""数据验证器定义."""

import re
from typing import Any

from pydantic import BaseModel, Field, validator


class UserValidator(BaseModel):
    """用户数据验证器."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = Field(default=None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    phone: str | None = Field(default=None, pattern=r"^\+?1?\d{9,15}$")
    user_type: str = Field(pattern=r"^(student|teacher|admin)$")

    @validator("username")
    def validate_username(cls, v: str) -> str:
        """验证用户名."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """验证密码强度."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v


class TrainingValidator(BaseModel):
    """训练数据验证器."""

    training_type: str = Field(
        pattern=r"^(vocabulary|listening|reading|writing|translation|grammar|comprehensive)$",
    )
    difficulty_level: int = Field(ge=1, le=5)
    question_count: int = Field(ge=1, le=100)
    time_limit: int | None = Field(default=None, ge=60, le=7200)  # 1分钟到2小时
    content_filter: str = Field(default="standard", pattern=r"^(strict|standard|relaxed)$")

    @validator("question_count")
    def validate_question_count(cls, v: int, values: dict[str, Any]) -> int:
        """验证题目数量."""
        training_type = values.get("training_type")
        if training_type is None:
            return v

        max_counts = {
            "vocabulary": 50,
            "listening": 30,
            "reading": 20,
            "writing": 5,
            "translation": 10,
            "grammar": 40,
            "comprehensive": 100,
        }

        max_count = max_counts.get(training_type, 50)
        if v > max_count:
            raise ValueError(f"{training_type}类型最多{max_count}道题")
        return v

    @validator("difficulty_level")
    def validate_difficulty_level(cls, v: int, values: dict[str, Any]) -> int:
        """验证难度级别."""
        if v < 1 or v > 5:
            raise ValueError("难度级别必须在1-5之间")
        return v

    @validator("time_limit")
    def validate_time_limit(cls, v: int | None, values: dict[str, Any]) -> int | None:
        """验证时间限制."""
        if v is None:
            return v

        training_type = values.get("training_type")
        if training_type is None:
            return v

        min_times = {
            "vocabulary": 300,  # 5分钟
            "listening": 600,  # 10分钟
            "reading": 900,  # 15分钟
            "writing": 1800,  # 30分钟
            "translation": 1200,  # 20分钟
            "grammar": 600,  # 10分钟
            "comprehensive": 3600,  # 60分钟
        }

        min_time = min_times.get(training_type, 300)
        if v < min_time:
            raise ValueError(f"{training_type}类型最少需要{min_time // 60}分钟")
        return v


class AIConfigValidator(BaseModel):
    """AI配置验证器."""

    model_name: str = Field(pattern=r"^(deepseek-chat|deepseek-reasoner)$")
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(ge=1, le=32000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = Field(default=False)

    @validator("temperature")
    def validate_temperature(cls, v: float, values: dict[str, Any]) -> float:
        """验证温度参数."""
        model_name = values.get("model_name")

        # 根据DeepSeek官方建议验证温度范围
        if model_name == "deepseek-chat":
            if v < 0.0 or v > 2.0:
                raise ValueError("deepseek-chat模型温度范围应为0.0-2.0")
        elif model_name == "deepseek-reasoner":
            if v < 0.0 or v > 1.5:
                raise ValueError("deepseek-reasoner模型温度范围应为0.0-1.5")

        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v: int, values: dict[str, Any]) -> int:
        """验证最大token数."""
        model_name = values.get("model_name")
        if model_name is None:
            return v

        # 根据模型限制验证token数
        max_limits = {"deepseek-chat": 8000, "deepseek-reasoner": 64000}

        max_limit = max_limits.get(model_name, 8000)
        if v > max_limit:
            raise ValueError(f"{model_name}模型最大token数为{max_limit}")

        return v

    @validator("model_name")
    def validate_model_type(cls, v: str) -> str:
        """验证模型类型."""
        valid_models = ["deepseek-chat", "deepseek-reasoner"]
        if v not in valid_models:
            raise ValueError(f"模型必须是{valid_models}中的一个")
        return v


class ComplianceValidator(BaseModel):
    """合规性验证器."""

    daily_study_minutes: int = Field(ge=0, le=480)  # 最多8小时
    age: int | None = Field(default=None, ge=6, le=100)
    parental_consent: bool = Field(default=True)

    @validator("daily_study_minutes")
    def validate_study_time(cls, v: int) -> int:
        """验证学习时长."""
        if v > 120:  # 超过2小时需要特别注意
            return v
        return v


class ContentSafetyValidator(BaseModel):
    """内容安全验证器."""

    content: str = Field(min_length=1, max_length=10000)
    content_type: str = Field(pattern=r"^(text|audio|image|video)$")

    @validator("content")
    def validate_content_safety(cls, v: str) -> str:
        """验证内容安全性."""
        # 基础的内容安全检查
        forbidden_words = [
            "暴力",
            "色情",
            "赌博",
            "毒品",
            "政治敏感",
            # 可以根据需要添加更多敏感词
        ]

        content_lower = v.lower()
        for word in forbidden_words:
            if word in content_lower:
                raise ValueError(f"内容包含不当词汇: {word}")

        return v


class ResourceValidator(BaseModel):
    """资源验证器."""

    resource_type: str = Field(pattern=r"^(document|audio|video|image|exercise)$")
    file_size: int = Field(ge=1, le=100 * 1024 * 1024)  # 最大100MB
    file_format: str
    content_level: str = Field(default="standard", pattern=r"^(beginner|intermediate|advanced)$")

    @validator("resource_type")
    def validate_resource_type(cls, v: str) -> str:
        """验证资源类型."""
        return v


class PerformanceValidator(BaseModel):
    """性能数据验证器."""

    accuracy_score: float = Field(ge=0.0, le=1.0)
    completion_time: int = Field(ge=1)  # 秒
    attempt_count: int = Field(ge=1, le=10)
    difficulty_rating: float = Field(ge=1.0, le=5.0)

    @validator("accuracy_score")
    def validate_training_results(cls, v: float) -> float:
        """验证训练结果."""
        if v < 0.0 or v > 1.0:
            raise ValueError("准确率必须在0.0-1.0之间")
        return v


class AdaptiveValidator(BaseModel):
    """自适应学习验证器."""

    difficulty_preference: float = Field(ge=0.0, le=1.0)
    learning_style: str = Field(pattern=r"^(visual|auditory|kinesthetic|reading)$")
    weak_points: list[str] = Field(default_factory=list)
    strong_points: list[str] = Field(default_factory=list)

    @validator("difficulty_preference")
    def validate_adjustment_threshold(cls, v: float) -> float:
        """验证调整阈值."""
        return max(0.0, min(1.0, v))


class AnalyticsValidator(BaseModel):
    """分析数据验证器."""

    performance_history: list[dict[str, Any]] = Field(default_factory=list)
    learning_trends: dict[str, Any] = Field(default_factory=dict)
    recommended_difficulty: float = Field(ge=0.0, le=1.0)

    @validator("performance_history")
    def validate_performance_history(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """验证性能历史数据."""
        if len(v) > 1000:  # 限制历史记录数量
            return v[-1000:]  # 只保留最近1000条
        return v

    @validator("recommended_difficulty")
    def validate_recommended_difficulty(cls, v: float) -> float:
        """验证推荐难度."""
        return max(0.0, min(1.0, v))


class ErrorAnalysisValidator(BaseModel):
    """错误分析验证器."""

    error_type: str = Field(pattern=r"^(grammar|vocabulary|comprehension|logic|other)$")
    error_frequency: int = Field(ge=0)
    error_pattern: str
    confidence_score: float = Field(ge=0.0, le=1.0)

    @validator("error_type")
    def validate_error_data(cls, v: str) -> str:
        """验证错误数据."""
        valid_types = ["grammar", "vocabulary", "comprehension", "logic", "other"]
        if v not in valid_types:
            raise ValueError(f"错误类型必须是{valid_types}中的一个")
        return v

    @validator("confidence_score")
    def validate_pattern_confidence(cls, v: float) -> float:
        """验证模式置信度."""
        return max(0.0, min(1.0, v))
