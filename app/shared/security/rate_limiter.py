"""API限流模块

提供多种限流算法实现，包括令牌桶、滑动窗口、固定窗口等，
支持基于IP、用户、API端点的灵活限流策略。
"""

import asyncio
import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """限流算法类型"""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitResult(Enum):
    """限流结果"""

    ALLOWED = "allowed"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"


@dataclass
class RateLimitRule:
    """限流规则"""

    name: str
    requests_per_window: int
    window_size: int  # 秒
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    burst_size: int | None = None
    block_duration: int = 0  # 阻断时长（秒），0表示不阻断
    enabled: bool = True


@dataclass
class RateLimitStatus:
    """限流状态"""

    result: RateLimitResult
    remaining_requests: int
    reset_time: float
    retry_after: int | None
    rule_name: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenBucket:
    """令牌桶"""

    capacity: int
    tokens: float
    refill_rate: float  # 每秒补充的令牌数
    last_refill: float


@dataclass
class SlidingWindow:
    """滑动窗口"""

    window_size: int
    max_requests: int
    requests: deque[float]

    def __post_init__(self) -> None:
        if not hasattr(self, "requests"):
            self.requests = deque[float]()


@dataclass
class FixedWindow:
    """固定窗口"""

    window_size: int
    max_requests: int
    current_requests: int
    window_start: float


class RateLimiter:
    """API限流器"""

    def __init__(self) -> None:
        """初始化限流器"""
        self.rules: dict[str, RateLimitRule] = {}
        self.token_buckets: dict[str, TokenBucket] = {}
        self.sliding_windows: dict[str, SlidingWindow] = {}
        self.fixed_windows: dict[str, FixedWindow] = {}
        self.blocked_clients: dict[str, float] = {}  # 客户端ID -> 解封时间
        self._lock = asyncio.Lock()

    def add_rule(self, rule: RateLimitRule) -> None:
        """添加限流规则"""
        self.rules[rule.name] = rule
        logger.info(f"Added rate limit rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """移除限流规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            # 清理相关数据
            self._cleanup_rule_data(rule_name)
            logger.info(f"Removed rate limit rule: {rule_name}")
            return True
        return False

    def _cleanup_rule_data(self, rule_name: str) -> None:
        """清理规则相关数据"""
        # 清理令牌桶
        keys_to_remove = [
            key for key in self.token_buckets.keys() if key.startswith(f"{rule_name}:")
        ]
        for key in keys_to_remove:
            del self.token_buckets[key]

        # 清理滑动窗口
        keys_to_remove = [
            key for key in self.sliding_windows.keys() if key.startswith(f"{rule_name}:")
        ]
        for key in keys_to_remove:
            del self.sliding_windows[key]

        # 清理固定窗口
        keys_to_remove = [
            key for key in self.fixed_windows.keys() if key.startswith(f"{rule_name}:")
        ]
        for key in keys_to_remove:
            del self.fixed_windows[key]

    async def check_rate_limit(
        self, client_id: str, rule_name: str, endpoint: str | None = None
    ) -> RateLimitStatus:
        """检查限流状态"""
        async with self._lock:
            # 检查规则是否存在
            if rule_name not in self.rules:
                return RateLimitStatus(
                    result=RateLimitResult.ALLOWED,
                    remaining_requests=-1,
                    reset_time=0,
                    retry_after=None,
                    rule_name=rule_name,
                    details={"reason": "rule_not_found"},
                )

            rule = self.rules[rule_name]

            # 检查规则是否启用
            if not rule.enabled:
                return RateLimitStatus(
                    result=RateLimitResult.ALLOWED,
                    remaining_requests=-1,
                    reset_time=0,
                    retry_after=None,
                    rule_name=rule_name,
                    details={"reason": "rule_disabled"},
                )

            # 检查客户端是否被阻断
            if client_id in self.blocked_clients:
                unblock_time = self.blocked_clients[client_id]
                current_time = time.time()

                if current_time < unblock_time:
                    return RateLimitStatus(
                        result=RateLimitResult.BLOCKED,
                        remaining_requests=0,
                        reset_time=unblock_time,
                        retry_after=int(unblock_time - current_time),
                        rule_name=rule_name,
                        details={
                            "reason": "client_blocked",
                            "unblock_time": unblock_time,
                        },
                    )
                else:
                    # 解除阻断
                    del self.blocked_clients[client_id]

            # 根据算法检查限流
            if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                return await self._check_token_bucket(client_id, rule, endpoint)
            elif rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                return await self._check_sliding_window(client_id, rule, endpoint)
            elif rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                return await self._check_fixed_window(client_id, rule, endpoint)
            else:
                # 默认使用令牌桶
                return await self._check_token_bucket(client_id, rule, endpoint)

    async def _check_token_bucket(
        self, client_id: str, rule: RateLimitRule, endpoint: str | None
    ) -> RateLimitStatus:
        """检查令牌桶限流"""
        bucket_key = f"{rule.name}:{client_id}"
        if endpoint:
            bucket_key += f":{endpoint}"

        current_time = time.time()

        # 获取或创建令牌桶
        if bucket_key not in self.token_buckets:
            capacity = rule.burst_size or rule.requests_per_window
            self.token_buckets[bucket_key] = TokenBucket(
                capacity=capacity,
                tokens=float(capacity),
                refill_rate=rule.requests_per_window / rule.window_size,
                last_refill=current_time,
            )

        bucket = self.token_buckets[bucket_key]

        # 补充令牌
        time_passed = current_time - bucket.last_refill
        tokens_to_add = time_passed * bucket.refill_rate
        bucket.tokens = min(bucket.capacity, bucket.tokens + tokens_to_add)
        bucket.last_refill = current_time

        # 检查是否有可用令牌
        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return RateLimitStatus(
                result=RateLimitResult.ALLOWED,
                remaining_requests=int(bucket.tokens),
                reset_time=current_time + (bucket.capacity - bucket.tokens) / bucket.refill_rate,
                retry_after=None,
                rule_name=rule.name,
                details={"algorithm": "token_bucket", "tokens": bucket.tokens},
            )
        else:
            # 限流触发
            retry_after = int((1.0 - bucket.tokens) / bucket.refill_rate) + 1

            # 检查是否需要阻断
            if rule.block_duration > 0:
                self.blocked_clients[client_id] = current_time + rule.block_duration

            return RateLimitStatus(
                result=RateLimitResult.RATE_LIMITED,
                remaining_requests=0,
                reset_time=current_time + retry_after,
                retry_after=retry_after,
                rule_name=rule.name,
                details={"algorithm": "token_bucket", "tokens": bucket.tokens},
            )

    async def _check_sliding_window(
        self, client_id: str, rule: RateLimitRule, endpoint: str | None
    ) -> RateLimitStatus:
        """检查滑动窗口限流"""
        window_key = f"{rule.name}:{client_id}"
        if endpoint:
            window_key += f":{endpoint}"

        current_time = time.time()

        # 获取或创建滑动窗口
        if window_key not in self.sliding_windows:
            self.sliding_windows[window_key] = SlidingWindow(
                window_size=rule.window_size,
                max_requests=rule.requests_per_window,
                requests=deque(),
            )

        window = self.sliding_windows[window_key]

        # 清理过期请求
        cutoff_time = current_time - rule.window_size
        while window.requests and window.requests[0] < cutoff_time:
            window.requests.popleft()

        # 检查请求数量
        if len(window.requests) < rule.requests_per_window:
            window.requests.append(current_time)
            remaining = rule.requests_per_window - len(window.requests)

            return RateLimitStatus(
                result=RateLimitResult.ALLOWED,
                remaining_requests=remaining,
                reset_time=current_time + rule.window_size,
                retry_after=None,
                rule_name=rule.name,
                details={
                    "algorithm": "sliding_window",
                    "requests_count": len(window.requests),
                },
            )
        else:
            # 限流触发
            oldest_request = window.requests[0]
            retry_after = int(oldest_request + rule.window_size - current_time) + 1

            # 检查是否需要阻断
            if rule.block_duration > 0:
                self.blocked_clients[client_id] = current_time + rule.block_duration

            return RateLimitStatus(
                result=RateLimitResult.RATE_LIMITED,
                remaining_requests=0,
                reset_time=oldest_request + rule.window_size,
                retry_after=retry_after,
                rule_name=rule.name,
                details={
                    "algorithm": "sliding_window",
                    "requests_count": len(window.requests),
                },
            )

    async def _check_fixed_window(
        self, client_id: str, rule: RateLimitRule, endpoint: str | None
    ) -> RateLimitStatus:
        """检查固定窗口限流"""
        window_key = f"{rule.name}:{client_id}"
        if endpoint:
            window_key += f":{endpoint}"

        current_time = time.time()

        # 获取或创建固定窗口
        if window_key not in self.fixed_windows:
            window_start = (current_time // rule.window_size) * rule.window_size
            self.fixed_windows[window_key] = FixedWindow(
                window_size=rule.window_size,
                max_requests=rule.requests_per_window,
                current_requests=0,
                window_start=window_start,
            )

        window = self.fixed_windows[window_key]

        # 检查是否需要重置窗口
        window_start = (current_time // rule.window_size) * rule.window_size
        if window_start > window.window_start:
            window.current_requests = 0
            window.window_start = window_start

        # 检查请求数量
        if window.current_requests < rule.requests_per_window:
            window.current_requests += 1
            remaining = rule.requests_per_window - window.current_requests
            reset_time = window.window_start + rule.window_size

            return RateLimitStatus(
                result=RateLimitResult.ALLOWED,
                remaining_requests=remaining,
                reset_time=reset_time,
                retry_after=None,
                rule_name=rule.name,
                details={
                    "algorithm": "fixed_window",
                    "requests_count": window.current_requests,
                },
            )
        else:
            # 限流触发
            reset_time = window.window_start + rule.window_size
            retry_after = int(reset_time - current_time) + 1

            # 检查是否需要阻断
            if rule.block_duration > 0:
                self.blocked_clients[client_id] = current_time + rule.block_duration

            return RateLimitStatus(
                result=RateLimitResult.RATE_LIMITED,
                remaining_requests=0,
                reset_time=reset_time,
                retry_after=retry_after,
                rule_name=rule.name,
                details={
                    "algorithm": "fixed_window",
                    "requests_count": window.current_requests,
                },
            )

    def get_client_id(
        self, ip_address: str, user_id: str | None = None, api_key: str | None = None
    ) -> str:
        """生成客户端ID"""
        if user_id:
            return f"user:{user_id}"
        elif api_key:
            # 对API密钥进行哈希处理
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"api:{api_key_hash}"
        else:
            return f"ip:{ip_address}"

    def get_rate_limit_headers(self, status: RateLimitStatus) -> dict[str, str]:
        """获取限流响应头"""
        headers = {
            "X-RateLimit-Rule": status.rule_name,
            "X-RateLimit-Remaining": str(status.remaining_requests),
        }

        if status.reset_time > 0:
            headers["X-RateLimit-Reset"] = str(int(status.reset_time))

        if status.retry_after is not None:
            headers["Retry-After"] = str(status.retry_after)

        return headers

    def get_statistics(self) -> dict[str, Any]:
        """获取限流统计信息"""
        return {
            "rules_count": len(self.rules),
            "active_token_buckets": len(self.token_buckets),
            "active_sliding_windows": len(self.sliding_windows),
            "active_fixed_windows": len(self.fixed_windows),
            "blocked_clients": len(self.blocked_clients),
            "rules": {name: rule.enabled for name, rule in self.rules.items()},
        }

    async def cleanup_expired_data(self) -> None:
        """清理过期数据"""
        current_time = time.time()

        # 清理过期的阻断客户端
        expired_blocks = [
            client_id
            for client_id, unblock_time in self.blocked_clients.items()
            if current_time >= unblock_time
        ]
        for client_id in expired_blocks:
            del self.blocked_clients[client_id]

        # 清理过期的滑动窗口数据
        for window in self.sliding_windows.values():
            cutoff_time = current_time - window.window_size
            while window.requests and window.requests[0] < cutoff_time:
                window.requests.popleft()

        if expired_blocks:
            logger.debug(f"Cleaned up {len(expired_blocks)} expired client blocks")


# 预定义限流规则
DEFAULT_RATE_LIMIT_RULES = [
    RateLimitRule(
        name="api_general",
        requests_per_window=100,
        window_size=60,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        burst_size=20,
    ),
    RateLimitRule(
        name="api_auth",
        requests_per_window=10,
        window_size=60,
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        block_duration=300,  # 5分钟阻断
    ),
    RateLimitRule(
        name="api_upload",
        requests_per_window=5,
        window_size=60,
        algorithm=RateLimitAlgorithm.FIXED_WINDOW,
    ),
    RateLimitRule(
        name="api_ai",
        requests_per_window=20,
        window_size=60,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        burst_size=5,
    ),
]

# 全局限流器实例
rate_limiter = RateLimiter()

# 初始化默认规则
for rule in DEFAULT_RATE_LIMIT_RULES:
    rate_limiter.add_rule(rule)
