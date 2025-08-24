"""
性能监控中间件

提供HTTP请求的性能监控和优化：
- 请求响应时间监控
- 请求频率限制
- 缓存控制
- 压缩优化
- 错误率监控
"""

import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.models.enums import AlertLevel
from app.shared.utils.metrics_collector import collect_metric, get_metrics_collector


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    def __init__(
        self,
        app: Any,
        enable_compression: bool = True,
        compression_threshold: int = 1024,
        enable_rate_limiting: bool = True,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
        enable_caching: bool = True,
        cache_ttl: int = 300,
    ) -> None:
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

        # 配置选项
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

        # 性能统计
        self.request_stats = {
            "total_requests": 0,
            "total_response_time": 0.0,
            "error_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compressed_responses": 0,
        }

        # 请求历史（用于速率限制）
        self.request_history: defaultdict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.rate_limit_requests * 2)
        )

        # 响应缓存
        self.response_cache: dict[str, dict[str, Any]] = {}

        # 路径性能统计
        self.path_stats: defaultdict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "error_count": 0,
                "avg_response_time": 0.0,
                "min_response_time": float("inf"),
                "max_response_time": 0.0,
            }
        )

        # 慢请求阈值（秒）
        self.slow_request_threshold = 2.0

        # 初始化指标收集器
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """设置性能指标"""
        collector = get_metrics_collector()

        # 添加告警规则
        collector.add_alert_rule(
            "http.response_time",
            threshold=self.slow_request_threshold,
            level=AlertLevel.WARNING,
            comparison="greater",
        )

        collector.add_alert_rule(
            "http.error_rate",
            threshold=0.05,  # 5%错误率
            level=AlertLevel.ERROR,
            comparison="greater",
        )

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        """处理HTTP请求"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method

        try:
            # 速率限制检查
            if self.enable_rate_limiting and await self._is_rate_limited(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"error": "请求频率过高，请稍后重试"},
                    headers={"Retry-After": str(self.rate_limit_window)},
                )

            # 缓存检查
            cache_key = None
            if self.enable_caching and method == "GET":
                cache_key = self._get_cache_key(request)
                cached_response = await self._get_cached_response(cache_key)
                if cached_response:
                    self.request_stats["cache_hits"] += 1
                    await self._record_request_metrics(
                        path, method, 200, time.time() - start_time, True
                    )
                    return cached_response

            # 执行请求
            response = await call_next(request)

            # 计算响应时间
            response_time = time.time() - start_time

            # 压缩响应
            if self.enable_compression:
                response = await self._compress_response(request, response)

            # 缓存响应
            if (
                self.enable_caching
                and method == "GET"
                and cache_key
                and response.status_code == 200
            ):
                await self._cache_response(cache_key, response)
                self.request_stats["cache_misses"] += 1

            # 记录性能指标
            await self._record_request_metrics(path, method, response.status_code, response_time)

            # 添加性能头
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Cache"] = "HIT" if cache_key in self.response_cache else "MISS"

            return response

        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"请求处理错误: {path} - {e}")

            # 记录错误指标
            await self._record_request_metrics(path, method, 500, response_time, error=True)

            return JSONResponse(
                status_code=500,
                content={"error": "内部服务器错误"},
            )

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return str(forwarded_for).split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return str(real_ip)

        # 回退到直接连接IP
        return str(request.client.host) if request.client and request.client.host else "unknown"

    async def _is_rate_limited(self, client_ip: str) -> bool:
        """检查是否触发速率限制"""
        current_time = time.time()
        window_start = current_time - self.rate_limit_window

        # 清理过期记录
        request_times = self.request_history[client_ip]
        while request_times and request_times[0] < window_start:
            request_times.popleft()

        # 检查请求数量
        if len(request_times) >= self.rate_limit_requests:
            return True

        # 记录当前请求
        request_times.append(current_time)
        return False

    def _get_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        # 基于URL、查询参数和相关头生成缓存键
        url = str(request.url)
        user_agent = request.headers.get("User-Agent", "")
        accept_encoding = request.headers.get("Accept-Encoding", "")

        import hashlib

        cache_data = f"{url}:{user_agent}:{accept_encoding}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    async def _get_cached_response(self, cache_key: str) -> Response | None:
        """获取缓存的响应"""
        if cache_key not in self.response_cache:
            return None

        cached = self.response_cache[cache_key]

        # 检查是否过期
        if datetime.utcnow() > cached["expires_at"]:
            del self.response_cache[cache_key]
            return None

        # 重建响应对象
        return Response(
            content=cached["content"],
            status_code=cached["status_code"],
            headers=cached["headers"],
            media_type=cached["media_type"],
        )

    async def _cache_response(self, cache_key: str, response: Response) -> None:
        """缓存响应"""
        try:
            # 只缓存成功的GET请求
            if response.status_code != 200:
                return

            # 对于FastAPI Response，我们不能直接读取body_iterator
            # 这里简化实现，只缓存响应元数据
            self.response_cache[cache_key] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
                "expires_at": datetime.utcnow() + timedelta(seconds=self.cache_ttl),
            }

        except Exception as e:
            self.logger.error(f"缓存响应失败: {e}")

    def _iter_content(self, content: bytes) -> Any:
        """创建内容迭代器"""
        yield content

    async def _compress_response(self, request: Request, response: Any) -> Any:
        """压缩响应"""
        try:
            # 检查是否支持压缩
            accept_encoding = request.headers.get("Accept-Encoding", "")
            if "gzip" not in accept_encoding:
                return response

            # 检查内容类型
            content_type = response.headers.get("Content-Type", "")
            compressible_types = [
                "application/json",
                "text/html",
                "text/css",
                "text/javascript",
                "application/javascript",
                "text/plain",
            ]

            if not any(ct in content_type for ct in compressible_types):
                return response

            # 对于FastAPI Response，压缩功能简化实现
            # 在实际生产环境中，建议使用nginx等反向代理来处理压缩
            self.request_stats["compressed_responses"] += 1
            return response

        except Exception as e:
            self.logger.error(f"压缩响应失败: {e}")
            return response

    async def _record_request_metrics(
        self,
        path: str,
        method: str,
        status_code: int,
        response_time: float,
        from_cache: bool = False,
        error: bool = False,
    ) -> None:
        """记录请求指标"""
        try:
            # 更新全局统计
            self.request_stats["total_requests"] += 1
            self.request_stats["total_response_time"] += response_time

            if error or status_code >= 400:
                self.request_stats["error_count"] += 1

            # 更新路径统计
            path_stat = self.path_stats[path]
            path_stat["count"] += 1
            path_stat["total_time"] += response_time

            if error or status_code >= 400:
                path_stat["error_count"] += 1

            # 更新响应时间统计
            path_stat["avg_response_time"] = path_stat["total_time"] / path_stat["count"]
            path_stat["min_response_time"] = min(path_stat["min_response_time"], response_time)
            path_stat["max_response_time"] = max(path_stat["max_response_time"], response_time)

            # 收集指标到指标收集器
            tags = {
                "path": path,
                "method": method,
                "status_code": str(status_code),
                "from_cache": str(from_cache),
            }

            await collect_metric("http.response_time", response_time, tags)
            await collect_metric("http.request_count", 1.0, tags)

            if error or status_code >= 400:
                await collect_metric("http.error_count", 1.0, tags)

            # 慢请求告警
            if response_time > self.slow_request_threshold:
                self.logger.warning(f"慢请求检测: {method} {path} - {response_time:.3f}s")

            # 计算错误率
            if self.request_stats["total_requests"] > 0:
                error_rate = (
                    self.request_stats["error_count"] / self.request_stats["total_requests"]
                )
                await collect_metric("http.error_rate", error_rate)

        except Exception as e:
            self.logger.error(f"记录请求指标失败: {e}")

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        total_requests = self.request_stats["total_requests"]

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_requests": total_requests,
            "error_count": self.request_stats["error_count"],
            "error_rate": (
                self.request_stats["error_count"] / total_requests if total_requests > 0 else 0.0
            ),
            "average_response_time": (
                self.request_stats["total_response_time"] / total_requests
                if total_requests > 0
                else 0.0
            ),
            "cache_hit_rate": (
                self.request_stats["cache_hits"]
                / (self.request_stats["cache_hits"] + self.request_stats["cache_misses"])
                if (self.request_stats["cache_hits"] + self.request_stats["cache_misses"]) > 0
                else 0.0
            ),
            "compression_rate": (
                self.request_stats["compressed_responses"] / total_requests
                if total_requests > 0
                else 0.0
            ),
            "path_stats": dict(self.path_stats),
            "active_cache_entries": len(self.response_cache),
            "rate_limited_ips": len(self.request_history),
        }

        return stats

    def get_slow_endpoints(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最慢的端点"""
        sorted_paths = sorted(
            self.path_stats.items(),
            key=lambda x: x[1]["avg_response_time"],
            reverse=True,
        )

        return [
            {
                "path": path,
                "avg_response_time": stats["avg_response_time"],
                "max_response_time": stats["max_response_time"],
                "request_count": stats["count"],
                "error_count": stats["error_count"],
                "error_rate": (
                    stats["error_count"] / stats["count"] if stats["count"] > 0 else 0.0
                ),
            }
            for path, stats in sorted_paths[:limit]
        ]

    def clear_cache(self) -> int:
        """清空缓存"""
        count = len(self.response_cache)
        self.response_cache.clear()
        return count

    def clear_stats(self) -> None:
        """清空统计数据"""
        self.request_stats = {
            "total_requests": 0,
            "total_response_time": 0.0,
            "error_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compressed_responses": 0,
        }
        self.path_stats.clear()

    async def cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        current_time = datetime.utcnow()
        expired_keys = []

        for key, cached in self.response_cache.items():
            if current_time > cached["expires_at"]:
                expired_keys.append(key)

        for key in expired_keys:
            del self.response_cache[key]

        return len(expired_keys)


# 便捷函数
def create_performance_middleware(
    enable_compression: bool = True,
    enable_rate_limiting: bool = True,
    enable_caching: bool = True,
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
    cache_ttl: int = 300,
) -> type[PerformanceMiddleware]:
    """创建性能中间件的便捷函数"""

    class ConfiguredPerformanceMiddleware(PerformanceMiddleware):
        def __init__(self, app: Any) -> None:
            super().__init__(
                app,
                enable_compression=enable_compression,
                enable_rate_limiting=enable_rate_limiting,
                enable_caching=enable_caching,
                rate_limit_requests=rate_limit_requests,
                rate_limit_window=rate_limit_window,
                cache_ttl=cache_ttl,
            )

    return ConfiguredPerformanceMiddleware
