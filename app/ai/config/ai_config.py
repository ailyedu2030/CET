"""
AI服务配置

集中管理AI服务的所有配置参数：
- API密钥和端点配置
- 模型参数配置
- 成本控制配置
- 性能优化配置
- 降级策略配置
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.shared.models.enums import AIModelType


class DeploymentEnvironment(Enum):
    """部署环境"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class APIKeyConfig:
    """API密钥配置"""

    key_id: str
    api_key: str
    endpoint: str
    daily_quota: int
    rate_limit_per_minute: int
    priority: int
    cost_per_token: float
    is_active: bool = True


@dataclass
class ModelConfig:
    """模型配置"""

    model_type: AIModelType
    model_name: str
    max_tokens: int
    context_window: int
    temperature_range: tuple[float, float]
    default_temperature: float
    supports_streaming: bool
    cost_multiplier: float


@dataclass
class CostControlConfig:
    """成本控制配置"""

    daily_limit: float
    hourly_limit: float
    monthly_limit: float
    per_request_limit: float
    alert_thresholds: dict[str, float]
    auto_throttle_enabled: bool
    emergency_stop_threshold: float


@dataclass
class PerformanceConfig:
    """性能配置"""

    max_concurrent_requests: int
    request_timeout: float
    retry_attempts: int
    retry_delay: float
    cache_ttl: int
    batch_size: int
    queue_size: int


@dataclass
class FallbackConfig:
    """降级配置"""

    enabled: bool
    health_check_interval: int
    failure_threshold: float
    recovery_threshold: float
    max_fallback_level: int
    fallback_timeout: float


class AIConfig:
    """AI服务配置管理器"""

    def __init__(
        self, environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    ) -> None:
        self.environment = environment
        self._load_configuration()

    def _load_configuration(self) -> None:
        """加载配置"""
        # API密钥配置
        self.api_keys = self._load_api_keys()

        # 模型配置
        self.models = self._load_model_configs()

        # 成本控制配置
        self.cost_control = self._load_cost_control_config()

        # 性能配置
        self.performance = self._load_performance_config()

        # 降级配置
        self.fallback = self._load_fallback_config()

        # 错峰时段配置
        self.off_peak_hours = list(range(0, 8)) + list(range(22, 24))
        self.peak_hours = list(range(9, 21))

        # 缓存配置
        self.cache_config = {
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "cache_prefix": "ai_service:",
            "default_ttl": 3600,
            "max_cache_size": 10000,
        }

        # 监控配置
        self.monitoring = {
            "metrics_retention_days": 30,
            "alert_webhook_url": os.getenv("ALERT_WEBHOOK_URL"),
            "performance_sampling_rate": 0.1,
            "log_level": os.getenv("AI_LOG_LEVEL", "INFO"),
        }

    def _load_api_keys(self) -> list[APIKeyConfig]:
        """加载API密钥配置"""
        api_keys = []

        # 从环境变量加载主密钥
        main_key = os.getenv("DEEPSEEK_API_KEY")
        if main_key:
            api_keys.append(
                APIKeyConfig(
                    key_id="main",
                    api_key=main_key,
                    endpoint=os.getenv("DEEPSEEK_API_ENDPOINT", "https://api.deepseek.com/v1"),
                    daily_quota=int(os.getenv("DEEPSEEK_DAILY_QUOTA", "1000000")),
                    rate_limit_per_minute=int(os.getenv("DEEPSEEK_RATE_LIMIT", "60")),
                    priority=1,
                    cost_per_token=float(os.getenv("DEEPSEEK_COST_PER_TOKEN", "0.0014")),
                )
            )

        # 从环境变量加载备用密钥
        for i in range(1, 26):  # 支持最多25个备用密钥
            key_env = f"DEEPSEEK_API_KEY_{i}"
            key = os.getenv(key_env)
            if key:
                api_keys.append(
                    APIKeyConfig(
                        key_id=f"backup_{i}",
                        api_key=key,
                        endpoint=os.getenv(
                            f"DEEPSEEK_API_ENDPOINT_{i}", "https://api.deepseek.com/v1"
                        ),
                        daily_quota=int(os.getenv(f"DEEPSEEK_DAILY_QUOTA_{i}", "500000")),
                        rate_limit_per_minute=int(os.getenv(f"DEEPSEEK_RATE_LIMIT_{i}", "30")),
                        priority=i + 1,
                        cost_per_token=float(os.getenv(f"DEEPSEEK_COST_PER_TOKEN_{i}", "0.0014")),
                    )
                )

        # 开发环境默认配置
        if not api_keys and self.environment == DeploymentEnvironment.DEVELOPMENT:
            api_keys.append(
                APIKeyConfig(
                    key_id="dev_default",
                    api_key="sk-dev-key-placeholder",
                    endpoint="https://api.deepseek.com/v1",
                    daily_quota=10000,
                    rate_limit_per_minute=10,
                    priority=1,
                    cost_per_token=0.0014,
                    is_active=False,  # 开发环境默认不激活
                )
            )

        return api_keys

    def _load_model_configs(self) -> dict[AIModelType, ModelConfig]:
        """加载模型配置"""
        return {
            AIModelType.DEEPSEEK_CHAT: ModelConfig(
                model_type=AIModelType.DEEPSEEK_CHAT,
                model_name="deepseek-chat",
                max_tokens=4096,
                context_window=32768,
                temperature_range=(0.0, 2.0),
                default_temperature=0.7,
                supports_streaming=True,
                cost_multiplier=1.0,
            ),
            AIModelType.DEEPSEEK_CODER: ModelConfig(
                model_type=AIModelType.DEEPSEEK_CODER,
                model_name="deepseek-coder",
                max_tokens=4096,
                context_window=16384,
                temperature_range=(0.0, 2.0),
                default_temperature=0.1,
                supports_streaming=True,
                cost_multiplier=1.0,
            ),
            AIModelType.DEEPSEEK_LITE: ModelConfig(
                model_type=AIModelType.DEEPSEEK_LITE,
                model_name="deepseek-lite",
                max_tokens=2048,
                context_window=8192,
                temperature_range=(0.0, 1.0),
                default_temperature=0.7,
                supports_streaming=False,
                cost_multiplier=0.5,
            ),
        }

    def _load_cost_control_config(self) -> CostControlConfig:
        """加载成本控制配置"""
        base_daily_limit = 100.0
        base_hourly_limit = 10.0

        # 根据环境调整限制
        if self.environment == DeploymentEnvironment.PRODUCTION:
            daily_multiplier = 10.0
            hourly_multiplier = 5.0
        elif self.environment == DeploymentEnvironment.STAGING:
            daily_multiplier = 3.0
            hourly_multiplier = 2.0
        else:
            daily_multiplier = 1.0
            hourly_multiplier = 1.0

        return CostControlConfig(
            daily_limit=float(
                os.getenv("AI_DAILY_COST_LIMIT", base_daily_limit * daily_multiplier)
            ),
            hourly_limit=float(
                os.getenv("AI_HOURLY_COST_LIMIT", base_hourly_limit * hourly_multiplier)
            ),
            monthly_limit=float(
                os.getenv("AI_MONTHLY_COST_LIMIT", base_daily_limit * daily_multiplier * 30)
            ),
            per_request_limit=float(os.getenv("AI_PER_REQUEST_LIMIT", "5.0")),
            alert_thresholds={
                "daily_80_percent": base_daily_limit * daily_multiplier * 0.8,
                "daily_90_percent": base_daily_limit * daily_multiplier * 0.9,
                "hourly_80_percent": base_hourly_limit * hourly_multiplier * 0.8,
                "hourly_90_percent": base_hourly_limit * hourly_multiplier * 0.9,
            },
            auto_throttle_enabled=os.getenv("AI_AUTO_THROTTLE", "true").lower() == "true",
            emergency_stop_threshold=float(
                os.getenv(
                    "AI_EMERGENCY_STOP_THRESHOLD",
                    base_daily_limit * daily_multiplier * 1.2,
                )
            ),
        )

    def _load_performance_config(self) -> PerformanceConfig:
        """加载性能配置"""
        base_concurrent = 10

        # 根据环境调整并发数
        if self.environment == DeploymentEnvironment.PRODUCTION:
            concurrent_multiplier = 10
        elif self.environment == DeploymentEnvironment.STAGING:
            concurrent_multiplier = 5
        else:
            concurrent_multiplier = 1

        return PerformanceConfig(
            max_concurrent_requests=int(
                os.getenv("AI_MAX_CONCURRENT", base_concurrent * concurrent_multiplier)
            ),
            request_timeout=float(os.getenv("AI_REQUEST_TIMEOUT", "30.0")),
            retry_attempts=int(os.getenv("AI_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("AI_RETRY_DELAY", "1.0")),
            cache_ttl=int(os.getenv("AI_CACHE_TTL", "3600")),
            batch_size=int(os.getenv("AI_BATCH_SIZE", "10")),
            queue_size=int(os.getenv("AI_QUEUE_SIZE", "1000")),
        )

    def _load_fallback_config(self) -> FallbackConfig:
        """加载降级配置"""
        return FallbackConfig(
            enabled=os.getenv("AI_FALLBACK_ENABLED", "true").lower() == "true",
            health_check_interval=int(os.getenv("AI_HEALTH_CHECK_INTERVAL", "60")),
            failure_threshold=float(os.getenv("AI_FAILURE_THRESHOLD", "0.5")),
            recovery_threshold=float(os.getenv("AI_RECOVERY_THRESHOLD", "0.8")),
            max_fallback_level=int(os.getenv("AI_MAX_FALLBACK_LEVEL", "3")),
            fallback_timeout=float(os.getenv("AI_FALLBACK_TIMEOUT", "300.0")),
        )

    def get_active_api_keys(self) -> list[APIKeyConfig]:
        """获取活跃的API密钥"""
        return [key for key in self.api_keys if key.is_active]

    def get_model_config(self, model_type: AIModelType) -> ModelConfig | None:
        """获取模型配置"""
        return self.models.get(model_type)

    def is_off_peak_time(self, hour: int) -> bool:
        """判断是否为错峰时间"""
        return hour in self.off_peak_hours

    def get_cost_limit_for_period(self, period: str) -> float:
        """获取指定周期的成本限制"""
        if period == "daily":
            return self.cost_control.daily_limit
        elif period == "hourly":
            return self.cost_control.hourly_limit
        elif period == "monthly":
            return self.cost_control.monthly_limit
        elif period == "per_request":
            return self.cost_control.per_request_limit
        else:
            return 0.0

    def should_throttle_requests(self, current_cost: float, period: str) -> bool:
        """判断是否应该限流"""
        if not self.cost_control.auto_throttle_enabled:
            return False

        limit = self.get_cost_limit_for_period(period)
        threshold_key = f"{period}_80_percent"

        if threshold_key in self.cost_control.alert_thresholds:
            threshold = self.cost_control.alert_thresholds[threshold_key]
            return current_cost >= threshold

        return current_cost >= limit * 0.8

    def should_emergency_stop(self, current_cost: float) -> bool:
        """判断是否应该紧急停止"""
        return current_cost >= self.cost_control.emergency_stop_threshold

    def get_environment_config(self) -> dict[str, Any]:
        """获取环境配置摘要"""
        return {
            "environment": self.environment.value,
            "api_keys_count": len(self.get_active_api_keys()),
            "models_available": list(self.models.keys()),
            "cost_limits": {
                "daily": self.cost_control.daily_limit,
                "hourly": self.cost_control.hourly_limit,
                "monthly": self.cost_control.monthly_limit,
            },
            "performance": {
                "max_concurrent": self.performance.max_concurrent_requests,
                "timeout": self.performance.request_timeout,
                "cache_ttl": self.performance.cache_ttl,
            },
            "fallback_enabled": self.fallback.enabled,
            "off_peak_hours": self.off_peak_hours,
        }

    def validate_configuration(self) -> list[str]:
        """验证配置"""
        issues = []

        # 检查API密钥
        active_keys = self.get_active_api_keys()
        if not active_keys:
            issues.append("没有配置活跃的API密钥")

        # 检查成本限制
        if self.cost_control.daily_limit <= 0:
            issues.append("日成本限制必须大于0")

        if self.cost_control.hourly_limit > self.cost_control.daily_limit:
            issues.append("小时成本限制不应超过日成本限制")

        # 检查性能配置
        if self.performance.max_concurrent_requests <= 0:
            issues.append("最大并发请求数必须大于0")

        if self.performance.request_timeout <= 0:
            issues.append("请求超时时间必须大于0")

        # 检查模型配置
        for model_type, config in self.models.items():
            if config.max_tokens <= 0:
                issues.append(f"模型 {model_type.value} 的最大token数必须大于0")

            if config.context_window < config.max_tokens:
                issues.append(f"模型 {model_type.value} 的上下文窗口应大于等于最大token数")

        return issues

    def update_api_key_status(self, key_id: str, is_active: bool) -> bool:
        """更新API密钥状态"""
        for key in self.api_keys:
            if key.key_id == key_id:
                key.is_active = is_active
                return True
        return False

    def get_optimization_suggestions(self) -> list[str]:
        """获取配置优化建议"""
        suggestions = []

        # 检查API密钥分布
        active_keys = self.get_active_api_keys()
        if len(active_keys) < 3:
            suggestions.append("建议配置至少3个API密钥以提高可用性")

        # 检查成本控制
        if not self.cost_control.auto_throttle_enabled:
            suggestions.append("建议启用自动限流以控制成本")

        # 检查缓存配置
        if self.performance.cache_ttl < 1800:  # 30分钟
            suggestions.append("建议增加缓存TTL以提高性能")

        # 检查并发配置
        if self.environment == DeploymentEnvironment.PRODUCTION:
            if self.performance.max_concurrent_requests < 50:
                suggestions.append("生产环境建议增加最大并发请求数")

        # 检查降级配置
        if not self.fallback.enabled:
            suggestions.append("建议启用降级机制以提高系统稳定性")

        return suggestions


# 全局配置实例
_ai_config: AIConfig | None = None


def get_ai_config() -> AIConfig:
    """获取AI配置实例"""
    global _ai_config

    if _ai_config is None:
        env = DeploymentEnvironment(os.getenv("DEPLOYMENT_ENV", "development"))
        _ai_config = AIConfig(env)

    return _ai_config


def reload_ai_config() -> AIConfig:
    """重新加载AI配置"""
    global _ai_config
    _ai_config = None
    return get_ai_config()
