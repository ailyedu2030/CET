"""
资源库性能监控服务

实现功能：
1. 向量检索性能监控
2. 文档处理性能监控
3. AI服务调用监控
4. 错误率统计
5. 性能告警机制
"""

from datetime import datetime
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.services.cache_service import CacheService


class PerformanceMetric(BaseModel):
    """性能指标模型"""

    service_name: str
    operation_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerformanceStats(BaseModel):
    """性能统计模型"""

    service_name: str
    total_requests: int
    success_requests: int
    error_requests: int
    success_rate: float
    avg_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    last_24h_requests: int


class PerformanceAlert(BaseModel):
    """性能告警模型"""

    alert_type: str  # "high_latency", "high_error_rate", "service_down"
    service_name: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourcePerformanceMonitor:
    """资源库性能监控服务"""

    def __init__(self, db: AsyncSession, cache_service: CacheService) -> None:
        self.db = db
        self.cache_service = cache_service

        # 性能阈值配置
        self.thresholds = {
            "vector_search": {
                "max_duration_ms": 1000,  # 1秒
                "max_error_rate": 0.05,  # 5%
            },
            "document_processing": {
                "max_duration_ms": 30000,  # 30秒
                "max_error_rate": 0.10,  # 10%
            },
            "ai_generation": {
                "max_duration_ms": 60000,  # 60秒
                "max_error_rate": 0.15,  # 15%
            },
            "embedding": {
                "max_duration_ms": 5000,  # 5秒
                "max_error_rate": 0.10,  # 10%
            },
        }

        # 监控配置
        self.metrics_retention_hours = 24
        self.alert_cooldown_minutes = 15

    async def record_metric(
        self,
        service_name: str,
        operation_name: str,
        start_time: datetime,
        end_time: datetime,
        success: bool,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        记录性能指标

        Args:
            service_name: 服务名称
            operation_name: 操作名称
            start_time: 开始时间
            end_time: 结束时间
            success: 是否成功
            error_message: 错误信息
            metadata: 元数据
        """
        try:
            duration_ms = (end_time - start_time).total_seconds() * 1000

            metric = PerformanceMetric(
                service_name=service_name,
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )

            # 存储到缓存
            cache_key = f"metrics:{service_name}:{int(start_time.timestamp())}"
            await self.cache_service.set(cache_key, metric.model_dump_json())

            # 检查性能阈值
            await self._check_performance_thresholds(service_name, metric)

            logger.debug(
                "Performance metric recorded",
                extra={
                    "service": service_name,
                    "operation": operation_name,
                    "duration_ms": duration_ms,
                    "success": success,
                },
            )

        except Exception as e:
            logger.error(f"Failed to record performance metric: {str(e)}")

    async def get_performance_stats(self, service_name: str, hours: int = 24) -> PerformanceStats:
        """
        获取性能统计

        Args:
            service_name: 服务名称
            hours: 统计时间范围（小时）

        Returns:
            PerformanceStats: 性能统计
        """
        try:
            # 从缓存获取指标数据
            metrics = await self._get_metrics_from_cache(service_name, hours)

            if not metrics:
                return PerformanceStats(
                    service_name=service_name,
                    total_requests=0,
                    success_requests=0,
                    error_requests=0,
                    success_rate=0.0,
                    avg_duration_ms=0.0,
                    p95_duration_ms=0.0,
                    p99_duration_ms=0.0,
                    last_24h_requests=0,
                )

            # 计算统计指标
            total_requests = len(metrics)
            success_requests = sum(1 for m in metrics if m.success)
            error_requests = total_requests - success_requests
            success_rate = success_requests / total_requests if total_requests > 0 else 0.0

            durations = [m.duration_ms for m in metrics]
            durations.sort()

            avg_duration_ms = sum(durations) / len(durations) if durations else 0.0
            p95_duration_ms = durations[int(len(durations) * 0.95)] if durations else 0.0
            p99_duration_ms = durations[int(len(durations) * 0.99)] if durations else 0.0

            return PerformanceStats(
                service_name=service_name,
                total_requests=total_requests,
                success_requests=success_requests,
                error_requests=error_requests,
                success_rate=success_rate,
                avg_duration_ms=avg_duration_ms,
                p95_duration_ms=p95_duration_ms,
                p99_duration_ms=p99_duration_ms,
                last_24h_requests=total_requests,
            )

        except Exception as e:
            logger.error(f"Failed to get performance stats: {str(e)}")
            return PerformanceStats(
                service_name=service_name,
                total_requests=0,
                success_requests=0,
                error_requests=0,
                success_rate=0.0,
                avg_duration_ms=0.0,
                p95_duration_ms=0.0,
                p99_duration_ms=0.0,
                last_24h_requests=0,
            )

    async def get_all_services_stats(self) -> dict[str, PerformanceStats]:
        """
        获取所有服务的性能统计

        Returns:
            Dict[str, PerformanceStats]: 服务性能统计字典
        """
        services = [
            "vector_search",
            "document_processing",
            "ai_generation",
            "embedding",
        ]
        stats = {}

        for service in services:
            stats[service] = await self.get_performance_stats(service)

        return stats

    async def check_service_health(self) -> dict[str, Any]:
        """
        检查服务健康状态

        Returns:
            Dict[str, Any]: 健康状态报告
        """
        try:
            all_stats = await self.get_all_services_stats()
            health_report: dict[str, Any] = {
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {},
                "alerts": [],
            }

            for service_name, stats in all_stats.items():
                service_health = self._evaluate_service_health(service_name, stats)
                health_report["services"][service_name] = service_health

                if service_health["status"] != "healthy":
                    health_report["overall_status"] = "degraded"

            # 获取最近的告警
            recent_alerts = await self._get_recent_alerts()
            health_report["alerts"] = [alert.model_dump() for alert in recent_alerts]

            return health_report

        except Exception as e:
            logger.error(f"Failed to check service health: {str(e)}")
            return {
                "overall_status": "unknown",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    def create_performance_context_manager(
        self, service_name: str, operation_name: str
    ) -> "PerformanceContext":
        """
        创建性能监控上下文管理器

        Args:
            service_name: 服务名称
            operation_name: 操作名称

        Returns:
            PerformanceContext: 性能监控上下文
        """
        return PerformanceContext(self, service_name, operation_name)

    async def _get_metrics_from_cache(
        self, service_name: str, hours: int
    ) -> list[PerformanceMetric]:
        """从缓存获取指标数据"""
        try:
            # 这里简化实现，实际应该根据时间范围查询
            # 由于缓存服务的限制，这里返回空列表
            return []

        except Exception as e:
            logger.error(f"Failed to get metrics from cache: {str(e)}")
            return []

    async def _check_performance_thresholds(
        self, service_name: str, metric: PerformanceMetric
    ) -> None:
        """检查性能阈值"""
        try:
            thresholds = self.thresholds.get(service_name)
            if not thresholds:
                return

            # 检查延迟阈值
            if metric.duration_ms > thresholds["max_duration_ms"]:
                alert = PerformanceAlert(
                    alert_type="high_latency",
                    service_name=service_name,
                    message=f"High latency detected: {metric.duration_ms:.2f}ms > {thresholds['max_duration_ms']}ms",
                    severity=(
                        "medium"
                        if metric.duration_ms < thresholds["max_duration_ms"] * 2
                        else "high"
                    ),
                    timestamp=datetime.utcnow(),
                    metadata={
                        "duration_ms": metric.duration_ms,
                        "operation": metric.operation_name,
                    },
                )
                await self._send_alert(alert)

        except Exception as e:
            logger.error(f"Failed to check performance thresholds: {str(e)}")

    async def _send_alert(self, alert: PerformanceAlert) -> None:
        """发送性能告警"""
        try:
            # 检查告警冷却时间
            cooldown_key = f"alert_cooldown:{alert.service_name}:{alert.alert_type}"
            if await self.cache_service.get(cooldown_key):
                return

            # 记录告警
            alert_key = f"alert:{alert.service_name}:{int(alert.timestamp.timestamp())}"
            await self.cache_service.set(alert_key, alert.model_dump_json())

            # 设置冷却时间
            await self.cache_service.set(cooldown_key, "1")

            logger.warning(
                f"Performance alert: {alert.message}",
                extra={
                    "alert_type": alert.alert_type,
                    "service": alert.service_name,
                    "severity": alert.severity,
                },
            )

        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")

    async def _get_recent_alerts(self, hours: int = 24) -> list[PerformanceAlert]:
        """获取最近的告警"""
        try:
            # 简化实现，返回空列表
            return []

        except Exception as e:
            logger.error(f"Failed to get recent alerts: {str(e)}")
            return []

    def _evaluate_service_health(
        self, service_name: str, stats: PerformanceStats
    ) -> dict[str, Any]:
        """评估服务健康状态"""
        thresholds = self.thresholds.get(service_name, {})

        status = "healthy"
        issues = []

        # 检查错误率
        max_error_rate = thresholds.get("max_error_rate", 0.1)
        if stats.success_rate < (1 - max_error_rate):
            status = "unhealthy"
            issues.append(f"High error rate: {(1 - stats.success_rate) * 100:.1f}%")

        # 检查延迟
        max_duration = thresholds.get("max_duration_ms", 5000)
        if stats.p95_duration_ms > max_duration:
            status = "degraded" if status == "healthy" else status
            issues.append(f"High latency: P95 {stats.p95_duration_ms:.0f}ms")

        # 检查请求量
        if stats.total_requests == 0:
            status = "unknown"
            issues.append("No recent requests")

        return {
            "status": status,
            "success_rate": stats.success_rate,
            "avg_duration_ms": stats.avg_duration_ms,
            "p95_duration_ms": stats.p95_duration_ms,
            "total_requests": stats.total_requests,
            "issues": issues,
        }


class PerformanceContext:
    """性能监控上下文管理器"""

    def __init__(
        self,
        monitor: ResourcePerformanceMonitor,
        service_name: str,
        operation_name: str,
    ) -> None:
        self.monitor = monitor
        self.service_name = service_name
        self.operation_name = operation_name
        self.start_time: datetime | None = None
        self.metadata: dict[str, Any] = {}

    async def __aenter__(self) -> "PerformanceContext":
        self.start_time = datetime.utcnow()
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any
    ) -> None:
        if self.start_time:
            end_time = datetime.utcnow()
            success = exc_type is None
            error_message = str(exc_val) if exc_val else None

            await self.monitor.record_metric(
                service_name=self.service_name,
                operation_name=self.operation_name,
                start_time=self.start_time,
                end_time=end_time,
                success=success,
                error_message=error_message,
                metadata=self.metadata,
            )

    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据"""
        self.metadata[key] = value
