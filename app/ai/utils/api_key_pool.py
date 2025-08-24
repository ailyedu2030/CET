"""API密钥池管理工具."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class APIKeyStatus:
    """API密钥状态."""

    key: str
    is_active: bool = True
    last_used: datetime | None = None
    usage_count: int = 0
    rate_limit_reset: datetime | None = None
    error_count: int = 0
    max_errors: int = 5


class APIKeyPool:
    """API密钥池管理器."""

    def __init__(self, keys: list[str], provider: str = "deepseek") -> None:
        """初始化密钥池."""
        self.provider = provider
        self.keys: dict[str, APIKeyStatus] = {key: APIKeyStatus(key=key) for key in keys}
        self.lock = asyncio.Lock()
        self._current_key_index = 0

        # 配置参数
        self.min_interval_seconds = 1  # 最小请求间隔
        self.max_retries = 3
        self.error_reset_hours = 1  # 错误计数重置时间

        logger.info(f"初始化{provider}密钥池，共{len(keys)}个密钥")

    async def get_available_key(self) -> str | None:
        """获取可用的API密钥."""
        async with self.lock:
            available_keys = [
                status for status in self.keys.values() if self._is_key_available(status)
            ]

            if not available_keys:
                logger.warning("没有可用的API密钥")
                return None

            # 优先选择最少使用的密钥
            selected = min(available_keys, key=lambda x: x.usage_count)
            selected.last_used = datetime.utcnow()
            selected.usage_count += 1

            return selected.key

    def _is_key_available(self, status: APIKeyStatus) -> bool:
        """检查密钥是否可用."""
        if not status.is_active:
            return False

        # 检查错误次数是否超限
        if status.error_count >= status.max_errors:
            # 检查是否过了重置时间
            if status.last_used and datetime.utcnow() - status.last_used < timedelta(
                hours=self.error_reset_hours
            ):
                return False
            else:
                # 重置错误计数
                status.error_count = 0

        # 检查频率限制
        if status.last_used and datetime.utcnow() - status.last_used < timedelta(
            seconds=self.min_interval_seconds
        ):
            return False

        # 检查速率限制重置时间
        if status.rate_limit_reset and datetime.utcnow() < status.rate_limit_reset:
            return False

        return True

    async def mark_key_error(self, key: str, error_type: str = "general") -> None:
        """标记密钥发生错误."""
        async with self.lock:
            if key in self.keys:
                self.keys[key].error_count += 1

                # 如果是速率限制错误，设置重置时间
                if "rate" in error_type.lower():
                    self.keys[key].rate_limit_reset = datetime.utcnow() + timedelta(minutes=10)

                logger.warning(
                    f"密钥{key[:8]}...发生错误: {error_type}, "
                    f"累计错误次数: {self.keys[key].error_count}"
                )

    async def mark_key_success(self, key: str) -> None:
        """标记密钥请求成功."""
        async with self.lock:
            if key in self.keys:
                # 重置错误计数
                self.keys[key].error_count = 0
                self.keys[key].rate_limit_reset = None

    def get_pool_status(self) -> dict[str, dict[str, Any]]:
        """获取密钥池状态."""
        return {
            key[:8] + "...": {
                "active": status.is_active,
                "usage_count": status.usage_count,
                "error_count": status.error_count,
                "last_used": status.last_used.isoformat() if status.last_used else None,
                "rate_limit_reset": (
                    status.rate_limit_reset.isoformat() if status.rate_limit_reset else None
                ),
            }
            for key, status in self.keys.items()
        }

    async def disable_key(self, key: str, reason: str = "") -> None:
        """禁用密钥."""
        async with self.lock:
            if key in self.keys:
                self.keys[key].is_active = False
                logger.warning(f"密钥{key[:8]}...已禁用: {reason}")

    async def enable_key(self, key: str) -> None:
        """启用密钥."""
        async with self.lock:
            if key in self.keys:
                self.keys[key].is_active = True
                self.keys[key].error_count = 0
                logger.info(f"密钥{key[:8]}...已启用")


class DeepSeekAPIKeyPool(APIKeyPool):
    """DeepSeek专用API密钥池."""

    def __init__(self) -> None:
        """初始化DeepSeek密钥池."""
        keys = self._load_deepseek_keys()
        super().__init__(keys, provider="deepseek")

        # DeepSeek特定配置
        self.min_interval_seconds = 0.5  # DeepSeek允许更频繁的请求
        self.max_retries = 5

    def _load_deepseek_keys(self) -> list[str]:
        """从配置加载DeepSeek密钥."""
        keys = []

        # 从环境变量加载主密钥
        if hasattr(settings, "DEEPSEEK_API_KEY") and settings.DEEPSEEK_API_KEY:
            keys.append(settings.DEEPSEEK_API_KEY)

        # 从环境变量加载备用密钥池
        backup_keys_env = getattr(settings, "DEEPSEEK_BACKUP_KEYS", "")
        if backup_keys_env:
            backup_keys = [key.strip() for key in backup_keys_env.split(",") if key.strip()]
            keys.extend(backup_keys)

        if not keys:
            logger.error("未配置DeepSeek API密钥")
            raise ValueError("DeepSeek API密钥未配置")

        logger.info(f"加载了{len(keys)}个DeepSeek API密钥")
        return keys


# 全局密钥池实例
_deepseek_pool: DeepSeekAPIKeyPool | None = None


async def get_deepseek_pool() -> DeepSeekAPIKeyPool:
    """获取DeepSeek密钥池实例."""
    global _deepseek_pool
    if _deepseek_pool is None:
        _deepseek_pool = DeepSeekAPIKeyPool()
    return _deepseek_pool


class APICallManager:
    """API调用管理器，负责重试和错误处理."""

    def __init__(self, key_pool: APIKeyPool) -> None:
        self.key_pool = key_pool

    async def execute_with_retry(
        self, api_call_func: Callable[..., Any], max_retries: int = 3, **kwargs: Any
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """带重试的API调用执行."""
        last_error = None

        for attempt in range(max_retries):
            # 获取可用密钥
            api_key = await self.key_pool.get_available_key()
            if not api_key:
                last_error = "无可用API密钥"
                await asyncio.sleep(min(2**attempt, 10))  # 指数退避
                continue

            try:
                # 执行API调用
                result = await api_call_func(api_key=api_key, **kwargs)

                # 标记成功
                await self.key_pool.mark_key_success(api_key)
                return True, result, None

            except Exception as e:
                error_msg = str(e)
                last_error = error_msg

                # 标记错误
                await self.key_pool.mark_key_error(api_key, error_msg)

                # 判断是否需要重试
                if "rate" in error_msg.lower() or attempt < max_retries - 1:
                    wait_time = min(2**attempt, 10)
                    logger.warning(
                        f"API调用失败，{wait_time}秒后重试 (尝试{attempt + 1}/{max_retries}): {error_msg}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API调用最终失败: {error_msg}")

        return False, None, last_error


# 性能监控和统计
class APIUsageStats:
    """API使用统计."""

    def __init__(self) -> None:
        self.stats: dict[str, Any] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "average_response_time": 0.0,
            "response_times": [],
        }
        self.lock = asyncio.Lock()

    async def record_call(
        self, success: bool, tokens_used: int = 0, response_time_ms: int = 0
    ) -> None:
        """记录API调用统计."""
        async with self.lock:
            self.stats["total_calls"] += 1

            if success:
                self.stats["successful_calls"] += 1
            else:
                self.stats["failed_calls"] += 1

            if tokens_used > 0:
                self.stats["total_tokens"] += tokens_used

            if response_time_ms > 0:
                self.stats["response_times"].append(response_time_ms)
                # 保持最近1000个响应时间记录
                if len(self.stats["response_times"]) > 1000:
                    self.stats["response_times"] = self.stats["response_times"][-1000:]

                # 计算平均响应时间
                self.stats["average_response_time"] = sum(self.stats["response_times"]) / len(
                    self.stats["response_times"]
                )

    def get_stats(self) -> dict[str, Any]:
        """获取统计数据."""
        success_rate = 0.0
        if self.stats["total_calls"] > 0:
            success_rate = self.stats["successful_calls"] / self.stats["total_calls"] * 100

        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "average_response_time": round(self.stats["average_response_time"], 2),
        }


# 全局统计实例
_api_stats: APIUsageStats | None = None


def get_api_stats() -> APIUsageStats:
    """获取API统计实例."""
    global _api_stats
    if _api_stats is None:
        _api_stats = APIUsageStats()
    return _api_stats
