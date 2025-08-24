"""
智能缓存服务

提供多层缓存策略和优化：
- 内存缓存（Redis）
- 本地缓存（LRU）
- 分布式缓存
- 缓存预热和失效
- 缓存命中率优化
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import CacheType


class CacheStrategy(Enum):
    """缓存策略"""

    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于时间
    ADAPTIVE = "adaptive"  # 自适应


class CacheLevel(Enum):
    """缓存层级"""

    L1_MEMORY = "l1_memory"  # 一级内存缓存
    L2_REDIS = "l2_redis"  # 二级Redis缓存
    L3_DATABASE = "l3_database"  # 三级数据库缓存


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: int | None  # 生存时间（秒）
    size: int  # 字节大小
    metadata: dict[str, Any]


@dataclass
class CacheStats:
    """缓存统计"""

    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_size: int
    entry_count: int
    eviction_count: int
    timestamp: datetime


@dataclass
class CacheConfig:
    """缓存配置"""

    max_size: int  # 最大条目数
    max_memory: int  # 最大内存使用（字节）
    default_ttl: int  # 默认TTL（秒）
    strategy: CacheStrategy
    enable_compression: bool
    enable_serialization: bool


class LRUCache:
    """LRU本地缓存实现"""

    def __init__(self, max_size: int = 1000, max_memory: int = 100 * 1024 * 1024) -> None:
        self.max_size = max_size
        self.max_memory = max_memory
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.total_size = 0
        self.stats = CacheStats(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
            total_size=0,
            entry_count=0,
            eviction_count=0,
            timestamp=datetime.utcnow(),
        )

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        self.stats.total_requests += 1

        if key in self.cache:
            entry = self.cache[key]

            # 检查TTL
            if entry.ttl and (datetime.utcnow() - entry.created_at).total_seconds() > entry.ttl:
                self.delete(key)
                self.stats.cache_misses += 1
                return None

            # 更新访问信息
            entry.last_accessed = datetime.utcnow()
            entry.access_count += 1

            # 移到末尾（最近使用）
            self.cache.move_to_end(key)

            self.stats.cache_hits += 1
            self._update_hit_rate()
            return entry.value

        self.stats.cache_misses += 1
        self._update_hit_rate()
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存值"""
        try:
            # 计算值大小
            size = self._calculate_size(value)

            # 检查是否需要淘汰
            while (
                len(self.cache) >= self.max_size or self.total_size + size > self.max_memory
            ) and self.cache:
                self._evict_lru()

            # 如果单个值太大，不缓存
            if size > self.max_memory:
                return False

            # 删除已存在的条目
            if key in self.cache:
                self.delete(key)

            # 创建新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=0,
                ttl=ttl,
                size=size,
                metadata={},
            )

            self.cache[key] = entry
            self.total_size += size
            self.stats.entry_count = len(self.cache)
            self.stats.total_size = self.total_size

            return True

        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.total_size -= entry.size
            self.stats.entry_count = len(self.cache)
            self.stats.total_size = self.total_size
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.total_size = 0
        self.stats.entry_count = 0
        self.stats.total_size = 0

    def _evict_lru(self) -> None:
        """淘汰最近最少使用的条目"""
        if self.cache:
            key, entry = self.cache.popitem(last=False)  # 移除最旧的
            self.total_size -= entry.size
            self.stats.eviction_count += 1

    def _calculate_size(self, value: Any) -> int:
        """计算值的大小"""
        try:
            return len(pickle.dumps(value))
        except Exception:
            return len(str(value).encode("utf-8"))

    def _update_hit_rate(self) -> None:
        """更新命中率"""
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / self.stats.total_requests

    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        self.stats.timestamp = datetime.utcnow()
        return self.stats


class CacheService:
    """智能缓存服务"""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.logger = logging.getLogger(__name__)

        # 本地缓存实例
        self.l1_cache = LRUCache(max_size=1000, max_memory=50 * 1024 * 1024)  # 50MB

        # 缓存配置
        self.cache_configs = {
            CacheType.USER_SESSION: CacheConfig(
                max_size=10000,
                max_memory=10 * 1024 * 1024,
                default_ttl=3600,  # 1小时
                strategy=CacheStrategy.LRU,
                enable_compression=False,
                enable_serialization=True,
            ),
            CacheType.API_RESPONSE: CacheConfig(
                max_size=5000,
                max_memory=20 * 1024 * 1024,
                default_ttl=300,  # 5分钟
                strategy=CacheStrategy.TTL,
                enable_compression=True,
                enable_serialization=True,
            ),
            CacheType.DATABASE_QUERY: CacheConfig(
                max_size=2000,
                max_memory=30 * 1024 * 1024,
                default_ttl=600,  # 10分钟
                strategy=CacheStrategy.LFU,
                enable_compression=True,
                enable_serialization=True,
            ),
            CacheType.AI_RESULT: CacheConfig(
                max_size=1000,
                max_memory=100 * 1024 * 1024,
                default_ttl=1800,  # 30分钟
                strategy=CacheStrategy.LRU,
                enable_compression=True,
                enable_serialization=True,
            ),
        }

        # 缓存预热任务
        self.warmup_tasks: dict[str, asyncio.Task[None]] = {}

        # 统计信息
        self.global_stats = {
            "total_operations": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "total_misses": 0,
        }

    async def get(
        self,
        key: str,
        cache_type: CacheType = CacheType.API_RESPONSE,
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> Any | None:
        """获取缓存值（多层缓存）"""
        try:
            self.global_stats["total_operations"] += 1
            full_key = self._build_cache_key(key, cache_type)

            # L1缓存（本地内存）
            if use_l1:
                value = self.l1_cache.get(full_key)
                if value is not None:
                    self.global_stats["l1_hits"] += 1
                    return value

            # L2缓存（Redis）
            if use_l2:
                value = await self._get_from_redis(full_key, cache_type)
                if value is not None:
                    self.global_stats["l2_hits"] += 1

                    # 回写到L1缓存
                    if use_l1:
                        config = self.cache_configs.get(cache_type)
                        ttl = config.default_ttl if config else None
                        self.l1_cache.set(full_key, value, ttl)

                    return value

            self.global_stats["total_misses"] += 1
            return None

        except Exception as e:
            self.logger.error(f"缓存获取失败: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: CacheType = CacheType.API_RESPONSE,
        ttl: int | None = None,
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> bool:
        """设置缓存值（多层缓存）"""
        try:
            full_key = self._build_cache_key(key, cache_type)
            config = self.cache_configs.get(cache_type)

            if ttl is None and config:
                ttl = config.default_ttl

            success = True

            # L1缓存（本地内存）
            if use_l1:
                success &= self.l1_cache.set(full_key, value, ttl)

            # L2缓存（Redis）
            if use_l2:
                success &= await self._set_to_redis(full_key, value, cache_type, ttl)

            return success

        except Exception as e:
            self.logger.error(f"缓存设置失败: {e}")
            return False

    async def delete(
        self,
        key: str,
        cache_type: CacheType = CacheType.API_RESPONSE,
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> bool:
        """删除缓存值"""
        try:
            full_key = self._build_cache_key(key, cache_type)
            success = True

            # L1缓存
            if use_l1:
                success &= self.l1_cache.delete(full_key)

            # L2缓存
            if use_l2:
                success &= bool(self.redis.delete(full_key))

            return success

        except Exception as e:
            self.logger.error(f"缓存删除失败: {e}")
            return False

    async def clear(self, cache_type: CacheType | None = None) -> bool:
        """清空缓存"""
        try:
            if cache_type:
                # 清空特定类型的缓存
                pattern = f"cache:{cache_type.value}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)

                # 清空L1缓存中的相关条目
                keys_to_delete = [
                    k
                    for k in self.l1_cache.cache.keys()
                    if k.startswith(f"cache:{cache_type.value}:")
                ]
                for key in keys_to_delete:
                    self.l1_cache.delete(key)
            else:
                # 清空所有缓存
                self.redis.flushdb()
                self.l1_cache.clear()

            return True

        except Exception as e:
            self.logger.error(f"缓存清空失败: {e}")
            return False

    async def _get_from_redis(self, key: str, cache_type: CacheType) -> Any | None:
        """从Redis获取值"""
        try:
            raw_value = self.redis.get(key)
            if raw_value is None:
                return None

            # 确保raw_value是bytes类型
            if not isinstance(raw_value, bytes | str):
                return None

            config = self.cache_configs.get(cache_type)

            # 反序列化
            if config and config.enable_serialization:
                try:
                    if isinstance(raw_value, bytes):
                        value = pickle.loads(raw_value)
                    else:
                        value = json.loads(str(raw_value))
                except Exception:
                    if isinstance(raw_value, bytes):
                        value = json.loads(raw_value.decode("utf-8"))
                    else:
                        value = json.loads(str(raw_value))
            else:
                if isinstance(raw_value, bytes):
                    value = raw_value.decode("utf-8")
                else:
                    value = str(raw_value)

            return value

        except Exception as e:
            self.logger.error(f"Redis获取失败: {e}")
            return None

    async def _set_to_redis(
        self, key: str, value: Any, cache_type: CacheType, ttl: int | None
    ) -> bool:
        """设置值到Redis"""
        try:
            config = self.cache_configs.get(cache_type)

            # 序列化
            if config and config.enable_serialization:
                try:
                    raw_value = pickle.dumps(value)
                except Exception:
                    raw_value = json.dumps(value).encode("utf-8")
            else:
                raw_value = str(value).encode("utf-8")

            # 压缩（如果启用）
            if config and config.enable_compression and len(raw_value) > 1024:
                import gzip

                raw_value = gzip.compress(raw_value)
                key = f"{key}:compressed"

            # 设置到Redis
            if ttl:
                return bool(self.redis.setex(key, ttl, raw_value))
            else:
                return bool(self.redis.set(key, raw_value))

        except Exception as e:
            self.logger.error(f"Redis设置失败: {e}")
            return False

    def _build_cache_key(self, key: str, cache_type: CacheType) -> str:
        """构建缓存键"""
        # 使用MD5哈希来处理长键
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode("utf-8")).hexdigest()
            return f"cache:{cache_type.value}:{key_hash}"
        else:
            return f"cache:{cache_type.value}:{key}"

    async def warmup_cache(
        self,
        cache_type: CacheType,
        data_loader: Callable[[], Awaitable[dict[str, Any]]],
    ) -> None:
        """缓存预热"""
        try:
            task_id = f"warmup_{cache_type.value}_{int(time.time())}"

            async def warmup_task() -> None:
                try:
                    self.logger.info(f"开始缓存预热: {cache_type.value}")

                    # 调用数据加载器
                    data_items = await data_loader()

                    # 批量设置缓存
                    for key, value in data_items.items():
                        await self.set(key, value, cache_type)

                    self.logger.info(
                        f"缓存预热完成: {cache_type.value}, 加载了 {len(data_items)} 个条目"
                    )

                except Exception as e:
                    self.logger.error(f"缓存预热失败: {e}")
                finally:
                    # 清理任务引用
                    if task_id in self.warmup_tasks:
                        del self.warmup_tasks[task_id]

            # 启动预热任务
            task = asyncio.create_task(warmup_task())
            self.warmup_tasks[task_id] = task

        except Exception as e:
            self.logger.error(f"启动缓存预热失败: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        try:
            l1_stats = self.l1_cache.get_stats()

            # Redis统计
            redis_info_raw = self.redis.info()
            redis_info = redis_info_raw if isinstance(redis_info_raw, dict) else {}
            redis_stats = {
                "used_memory": redis_info.get("used_memory", 0),
                "used_memory_human": redis_info.get("used_memory_human", "0B"),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0),
                "connected_clients": redis_info.get("connected_clients", 0),
            }

            # 计算Redis命中率
            redis_total = redis_stats["keyspace_hits"] + redis_stats["keyspace_misses"]
            redis_hit_rate = redis_stats["keyspace_hits"] / redis_total if redis_total > 0 else 0.0

            # 全局统计
            total_ops = self.global_stats["total_operations"]
            total_hits = (
                self.global_stats["l1_hits"]
                + self.global_stats["l2_hits"]
                + self.global_stats["l3_hits"]
            )
            global_hit_rate = total_hits / total_ops if total_ops > 0 else 0.0

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "l1_cache": {
                    "hit_rate": l1_stats.hit_rate,
                    "total_requests": l1_stats.total_requests,
                    "cache_hits": l1_stats.cache_hits,
                    "cache_misses": l1_stats.cache_misses,
                    "entry_count": l1_stats.entry_count,
                    "total_size": l1_stats.total_size,
                    "eviction_count": l1_stats.eviction_count,
                },
                "l2_cache": {
                    "hit_rate": redis_hit_rate,
                    "used_memory": redis_stats["used_memory"],
                    "used_memory_human": redis_stats["used_memory_human"],
                    "keyspace_hits": redis_stats["keyspace_hits"],
                    "keyspace_misses": redis_stats["keyspace_misses"],
                    "connected_clients": redis_stats["connected_clients"],
                },
                "global_stats": {
                    "total_operations": total_ops,
                    "total_hit_rate": global_hit_rate,
                    "l1_hits": self.global_stats["l1_hits"],
                    "l2_hits": self.global_stats["l2_hits"],
                    "l3_hits": self.global_stats["l3_hits"],
                    "total_misses": self.global_stats["total_misses"],
                },
                "active_warmup_tasks": len(self.warmup_tasks),
            }

        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    async def optimize_cache(self) -> dict[str, Any]:
        """缓存优化"""
        try:
            optimization_results: dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat(),
                "actions_taken": [],
                "performance_improvement": {},
            }

            # 分析缓存使用模式
            stats = self.get_cache_stats()

            # L1缓存优化
            l1_hit_rate = stats["l1_cache"]["hit_rate"]
            if l1_hit_rate < 0.3:  # 命中率低于30%
                # 增加L1缓存大小
                old_size = self.l1_cache.max_size
                self.l1_cache.max_size = min(old_size * 2, 5000)
                optimization_results["actions_taken"].append(
                    f"增加L1缓存大小: {old_size} -> {self.l1_cache.max_size}"
                )

            # L2缓存优化
            l2_hit_rate = stats["l2_cache"]["hit_rate"]
            if l2_hit_rate < 0.5:  # 命中率低于50%
                # 建议增加Redis内存或调整TTL
                optimization_results["actions_taken"].append("建议增加Redis内存配置或调整TTL策略")

            # 清理过期缓存
            expired_count = await self._cleanup_expired_cache()
            if expired_count > 0:
                optimization_results["actions_taken"].append(
                    f"清理过期缓存条目: {expired_count} 个"
                )

            return optimization_results

        except Exception as e:
            self.logger.error(f"缓存优化失败: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    async def _cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        try:
            expired_count = 0

            # 清理L1缓存中的过期条目
            current_time = datetime.utcnow()
            keys_to_delete = []

            for key, entry in self.l1_cache.cache.items():
                if entry.ttl and (current_time - entry.created_at).total_seconds() > entry.ttl:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                self.l1_cache.delete(key)
                expired_count += 1

            return expired_count

        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {e}")
            return 0


# 全局缓存服务实例
_cache_service: CacheService | None = None


async def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service

    if _cache_service is None:
        from app.core.database import get_db
        from app.core.redis import get_redis

        async for db in get_db():
            redis = await get_redis()
            _cache_service = CacheService(db, redis)
            break

    if _cache_service is None:
        raise RuntimeError("无法初始化缓存服务")

    return _cache_service
