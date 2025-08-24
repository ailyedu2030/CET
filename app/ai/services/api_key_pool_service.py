"""
DeepSeek API密钥池管理服务

实现智能的API密钥池管理，包括：
- 多密钥轮询调度
- 智能负载均衡
- 错峰时段优化
- 成本控制机制
- 服务降级策略
"""

import asyncio
import datetime as dt
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.ai_models import APIKeyPool, APIKeyUsage
from app.core.config import settings
from app.core.database import get_db
from app.shared.models.enums import AIModelType


class KeyStatus(Enum):
    """API密钥状态"""

    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"
    DISABLED = "disabled"


class PriorityLevel(Enum):
    """请求优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class APIKeyInfo:
    """API密钥信息"""

    key_id: str
    api_key: str
    status: KeyStatus
    daily_quota: int
    used_quota: int
    rate_limit: int
    current_requests: int
    last_used: datetime
    error_count: int
    success_rate: float
    cost_per_token: float
    priority: int


@dataclass
class UsageStats:
    """使用统计"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost: float
    average_response_time: float
    peak_hour_usage: dict[int, int]


class APIKeyPoolService:
    """API密钥池管理服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.key_pool: list[APIKeyInfo] = []
        self.usage_stats: dict[str, UsageStats] = {}
        self.last_refresh = datetime.utcnow()
        self.refresh_interval = timedelta(minutes=5)

        # 错峰时段配置（北京时间）
        self.off_peak_hours = list(range(0, 8)) + list(range(22, 24))  # 00:00-08:00, 22:00-24:00
        self.peak_hours = list(range(9, 21))  # 09:00-21:00

        # 成本控制配置
        self.daily_cost_limit = settings.AI_DAILY_COST_LIMIT or 1000.0  # 每日成本限制
        self.hourly_cost_limit = settings.AI_HOURLY_COST_LIMIT or 50.0  # 每小时成本限制

        # 降级策略配置
        self.fallback_enabled = True
        self.fallback_threshold = 0.8  # 80%失败率触发降级

    async def initialize_pool(self) -> None:
        """初始化API密钥池"""
        try:
            # 从数据库加载API密钥配置
            stmt = select(APIKeyPool).where(APIKeyPool.is_active)
            result = await self.db.execute(stmt)
            key_configs = result.scalars().all()

            self.key_pool = []
            for config in key_configs:
                key_info = APIKeyInfo(
                    key_id=config.key_id,
                    api_key=config.api_key,
                    status=KeyStatus(config.status),
                    daily_quota=config.daily_quota,
                    used_quota=0,
                    rate_limit=config.rate_limit_per_minute,
                    current_requests=0,
                    last_used=config.last_used or datetime.utcnow(),
                    error_count=0,
                    success_rate=config.success_rate or 1.0,
                    cost_per_token=config.cost_per_token or 0.002,
                    priority=config.priority or 1,
                )
                self.key_pool.append(key_info)

            # 加载今日使用统计
            await self._load_daily_usage()

            self.logger.info(f"API密钥池初始化完成，共加载 {len(self.key_pool)} 个密钥")

        except Exception as e:
            self.logger.error(f"API密钥池初始化失败: {e}")
            raise

    async def get_optimal_key(
        self,
        priority: PriorityLevel = PriorityLevel.NORMAL,
        estimated_tokens: int = 1000,
        model_type: AIModelType = AIModelType.DEEPSEEK_CHAT,
    ) -> APIKeyInfo | None:
        """获取最优API密钥"""
        try:
            # 检查是否需要刷新密钥池
            if datetime.utcnow() - self.last_refresh > self.refresh_interval:
                await self._refresh_key_status()

            # 过滤可用密钥
            available_keys = [
                key
                for key in self.key_pool
                if key.status == KeyStatus.ACTIVE
                and key.used_quota + estimated_tokens <= key.daily_quota
                and key.current_requests < key.rate_limit
            ]

            if not available_keys:
                self.logger.warning("没有可用的API密钥")
                return None

            # 智能调度算法选择最优密钥
            optimal_key = await self._select_optimal_key(available_keys, priority, estimated_tokens)

            if optimal_key:
                # 更新密钥使用状态
                optimal_key.current_requests += 1
                optimal_key.last_used = datetime.utcnow()

            return optimal_key

        except Exception as e:
            self.logger.error(f"获取最优API密钥失败: {e}")
            return None

    async def _select_optimal_key(
        self,
        available_keys: list[APIKeyInfo],
        priority: PriorityLevel,
        estimated_tokens: int,
    ) -> APIKeyInfo | None:
        """智能选择最优密钥"""
        current_hour = datetime.utcnow().hour
        is_off_peak = current_hour in self.off_peak_hours

        # 计算每个密钥的综合得分
        scored_keys = []
        for key in available_keys:
            score = await self._calculate_key_score(key, priority, estimated_tokens, is_off_peak)
            scored_keys.append((key, score))

        # 按得分排序，选择最优密钥
        scored_keys.sort(key=lambda x: x[1], reverse=True)

        if scored_keys:
            return scored_keys[0][0]
        return None

    async def _calculate_key_score(
        self,
        key: APIKeyInfo,
        priority: PriorityLevel,
        estimated_tokens: int,
        is_off_peak: bool,
    ) -> float:
        """计算密钥综合得分"""
        score = 0.0

        # 1. 成功率权重 (40%)
        score += key.success_rate * 0.4

        # 2. 剩余配额权重 (25%)
        remaining_quota = (key.daily_quota - key.used_quota) / key.daily_quota
        score += remaining_quota * 0.25

        # 3. 当前负载权重 (20%)
        load_factor = 1.0 - (key.current_requests / key.rate_limit)
        score += load_factor * 0.20

        # 4. 成本效益权重 (10%)
        if is_off_peak:
            # 错峰时段，成本权重降低
            cost_factor = 1.0 - (key.cost_per_token / 0.01)  # 假设最高成本0.01
            score += cost_factor * 0.05
        else:
            cost_factor = 1.0 - (key.cost_per_token / 0.01)
            score += cost_factor * 0.10

        # 5. 优先级匹配权重 (5%)
        if key.priority >= priority.value:
            score += 0.05

        # 错峰时段加成
        if is_off_peak:
            score *= 1.1

        return max(0.0, min(1.0, score))

    async def record_usage(
        self,
        key_id: str,
        success: bool,
        tokens_used: int,
        response_time: float,
        cost: float,
        error_message: str | None = None,
    ) -> None:
        """记录API使用情况"""
        try:
            # 更新内存中的密钥状态
            key_info = next((k for k in self.key_pool if k.key_id == key_id), None)
            if key_info:
                key_info.current_requests = max(0, key_info.current_requests - 1)
                key_info.used_quota += tokens_used

                if success:
                    # 更新成功率
                    total_requests = key_info.used_quota / 1000  # 估算总请求数
                    key_info.success_rate = (
                        key_info.success_rate * (total_requests - 1) + 1.0
                    ) / total_requests
                else:
                    key_info.error_count += 1
                    # 检查是否需要暂停密钥
                    if key_info.error_count >= 10:
                        await self._check_key_health(key_info)

            # 记录到数据库
            usage_record = APIKeyUsage(
                key_id=key_id,
                model_type=AIModelType.DEEPSEEK_CHAT,
                tokens_used=tokens_used,
                cost=cost,
                response_time=response_time,
                success=success,
                error_message=error_message,
                created_at=datetime.utcnow(),
            )

            self.db.add(usage_record)
            await self.db.commit()

            # 检查成本限制
            await self._check_cost_limits()

        except Exception as e:
            self.logger.error(f"记录API使用情况失败: {e}")

    async def _check_key_health(self, key_info: APIKeyInfo) -> None:
        """检查密钥健康状态"""
        # 计算最近的成功率
        recent_success_rate = await self._get_recent_success_rate(key_info.key_id)

        if recent_success_rate < self.fallback_threshold:
            key_info.status = KeyStatus.ERROR
            self.logger.warning(f"API密钥 {key_info.key_id} 成功率过低，暂时禁用")

            # 设置恢复时间
            await asyncio.sleep(300)  # 5分钟后重新启用
            key_info.status = KeyStatus.ACTIVE
            key_info.error_count = 0

    async def _get_recent_success_rate(self, key_id: str) -> float:
        """获取最近的成功率"""
        try:
            # 查询最近1小时的使用记录
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            stmt = select(APIKeyUsage).where(
                and_(APIKeyUsage.key_id == key_id, APIKeyUsage.created_at >= one_hour_ago)
            )
            result = await self.db.execute(stmt)
            records = result.scalars().all()

            if not records:
                return 1.0

            successful = sum(1 for r in records if r.success)
            return successful / len(records)

        except Exception as e:
            self.logger.error(f"获取成功率失败: {e}")
            return 1.0

    async def _check_cost_limits(self) -> None:
        """检查成本限制"""
        try:
            # 检查今日总成本
            today = datetime.utcnow().date()
            daily_cost = await self._get_daily_cost(today)

            if daily_cost >= self.daily_cost_limit:
                self.logger.warning(f"今日成本已达限制: {daily_cost}")
                # 暂停所有非关键密钥
                for key in self.key_pool:
                    if key.priority < PriorityLevel.CRITICAL.value:
                        key.status = KeyStatus.QUOTA_EXCEEDED

            # 检查当前小时成本
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hourly_cost = await self._get_hourly_cost(current_hour)

            if hourly_cost >= self.hourly_cost_limit:
                self.logger.warning(f"当前小时成本已达限制: {hourly_cost}")
                # 降低非关键请求的处理优先级

        except Exception as e:
            self.logger.error(f"检查成本限制失败: {e}")

    async def _get_daily_cost(self, date: dt.date) -> float:
        """获取指定日期的总成本"""
        try:
            stmt = select(func.sum(APIKeyUsage.cost)).where(
                func.date(APIKeyUsage.created_at) == date
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0.0
        except Exception:
            return 0.0

    async def _get_hourly_cost(self, hour: datetime) -> float:
        """获取指定小时的总成本"""
        try:
            next_hour = hour + timedelta(hours=1)
            stmt = select(func.sum(APIKeyUsage.cost)).where(
                and_(APIKeyUsage.created_at >= hour, APIKeyUsage.created_at < next_hour)
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0.0
        except Exception:
            return 0.0

    async def _load_daily_usage(self) -> None:
        """加载今日使用统计"""
        try:
            today = datetime.utcnow().date()
            for key in self.key_pool:
                stmt = select(func.sum(APIKeyUsage.tokens_used)).where(
                    and_(
                        APIKeyUsage.key_id == key.key_id,
                        func.date(APIKeyUsage.created_at) == today,
                    )
                )
                result = await self.db.execute(stmt)
                key.used_quota = result.scalar() or 0

        except Exception as e:
            self.logger.error(f"加载今日使用统计失败: {e}")

    async def _refresh_key_status(self) -> None:
        """刷新密钥状态"""
        try:
            for key in self.key_pool:
                # 重置当前请求数（简单的速率限制重置）
                key.current_requests = 0

                # 检查配额是否重置（新的一天）
                if datetime.utcnow().date() > key.last_used.date():
                    key.used_quota = 0
                    key.error_count = 0
                    key.status = KeyStatus.ACTIVE

            self.last_refresh = datetime.utcnow()

        except Exception as e:
            self.logger.error(f"刷新密钥状态失败: {e}")

    async def get_pool_status(self) -> dict[str, Any]:
        """获取密钥池状态"""
        try:
            active_keys = len([k for k in self.key_pool if k.status == KeyStatus.ACTIVE])
            total_quota = sum(k.daily_quota for k in self.key_pool)
            used_quota = sum(k.used_quota for k in self.key_pool)

            today_cost = await self._get_daily_cost(datetime.utcnow().date())

            return {
                "total_keys": len(self.key_pool),
                "active_keys": active_keys,
                "total_daily_quota": total_quota,
                "used_quota": used_quota,
                "quota_utilization": ((used_quota / total_quota) * 100 if total_quota > 0 else 0),
                "today_cost": today_cost,
                "cost_limit": self.daily_cost_limit,
                "cost_utilization": (today_cost / self.daily_cost_limit) * 100,
                "is_off_peak": datetime.utcnow().hour in self.off_peak_hours,
                "pool_health": "healthy" if active_keys > 0 else "degraded",
            }

        except Exception as e:
            self.logger.error(f"获取密钥池状态失败: {e}")
            return {}

    async def enable_fallback_mode(self) -> None:
        """启用降级模式"""
        self.fallback_enabled = True
        self.logger.info("API服务降级模式已启用")

    async def disable_fallback_mode(self) -> None:
        """禁用降级模式"""
        self.fallback_enabled = False
        self.logger.info("API服务降级模式已禁用")

    async def get_usage_analytics(self, days: int = 7) -> dict[str, Any]:
        """获取使用分析数据"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 查询使用记录
            stmt = (
                select(APIKeyUsage)
                .where(APIKeyUsage.created_at >= start_date)
                .order_by(desc(APIKeyUsage.created_at))
            )

            result = await self.db.execute(stmt)
            records = result.scalars().all()

            # 统计分析
            total_requests = len(records)
            successful_requests = sum(1 for r in records if r.success)
            total_tokens = sum(r.tokens_used for r in records)
            total_cost = sum(r.cost for r in records)

            # 按小时统计
            hourly_stats = {}
            for record in records:
                hour = record.created_at.hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = {"requests": 0, "tokens": 0, "cost": 0.0}
                hourly_stats[hour]["requests"] += 1
                hourly_stats[hour]["tokens"] += record.tokens_used
                hourly_stats[hour]["cost"] += record.cost

            return {
                "period_days": days,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": (
                    (successful_requests / total_requests) * 100 if total_requests > 0 else 0
                ),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "average_cost_per_request": (
                    total_cost / total_requests if total_requests > 0 else 0
                ),
                "hourly_distribution": hourly_stats,
                "peak_hours": sorted(
                    hourly_stats.keys(),
                    key=lambda h: hourly_stats[h]["requests"],
                    reverse=True,
                )[:3],
                "off_peak_savings": self._calculate_off_peak_savings(hourly_stats),
            }

        except Exception as e:
            self.logger.error(f"获取使用分析数据失败: {e}")
            return {}

    def _calculate_off_peak_savings(self, hourly_stats: dict[int, dict[str, Any]]) -> float:
        """计算错峰节省成本"""
        off_peak_cost = sum(
            hourly_stats.get(hour, {}).get("cost", 0) for hour in self.off_peak_hours
        )

        # 假设错峰时段有20%的成本优势
        potential_savings = off_peak_cost * 0.20
        return float(potential_savings)


# 全局API密钥池服务实例
_api_key_pool_service: APIKeyPoolService | None = None


async def get_api_key_pool_service() -> APIKeyPoolService:
    """获取API密钥池服务实例"""
    global _api_key_pool_service

    if _api_key_pool_service is None:
        async for db in get_db():
            _api_key_pool_service = APIKeyPoolService(db)
            await _api_key_pool_service.initialize_pool()
            break

    if _api_key_pool_service is None:
        raise RuntimeError("无法初始化API密钥池服务")

    return _api_key_pool_service
