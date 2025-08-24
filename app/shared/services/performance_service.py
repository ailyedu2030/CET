"""
实时性能优化服务

提供系统级性能监控和优化功能：
- 实时性能指标收集
- 自动性能调优
- 资源使用监控
- 性能瓶颈检测
- 自动扩缩容决策
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import psutil
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import AlertLevel, MetricType


class PerformanceLevel(Enum):
    """性能等级"""

    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    FAIR = "fair"  # 一般
    POOR = "poor"  # 较差
    CRITICAL = "critical"  # 危险


class ResourceType(Enum):
    """资源类型"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"


@dataclass
class PerformanceMetric:
    """性能指标"""

    metric_type: MetricType
    value: float
    timestamp: datetime
    resource_type: ResourceType
    metadata: dict[str, Any]


@dataclass
class ResourceUsage:
    """资源使用情况"""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: dict[str, float]
    active_connections: int
    timestamp: datetime


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_id: str
    level: AlertLevel
    resource_type: ResourceType
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False


@dataclass
class OptimizationRecommendation:
    """优化建议"""

    recommendation_id: str
    resource_type: ResourceType
    issue_description: str
    recommended_action: str
    expected_improvement: str
    priority: int
    implementation_complexity: str


class PerformanceService:
    """实时性能优化服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.logger = logging.getLogger(__name__)

        # 性能指标存储
        self.metrics_history: dict[ResourceType, deque[PerformanceMetric]] = {
            resource_type: deque(maxlen=1000) for resource_type in ResourceType
        }

        # 告警管理
        self.active_alerts: dict[str, PerformanceAlert] = {}
        self.alert_callbacks: list[Callable[[PerformanceAlert], None]] = []

        # 性能阈值配置
        self.thresholds = {
            ResourceType.CPU: {"warning": 70.0, "error": 85.0, "critical": 95.0},
            ResourceType.MEMORY: {"warning": 75.0, "error": 90.0, "critical": 98.0},
            ResourceType.DISK: {"warning": 80.0, "error": 90.0, "critical": 95.0},
            ResourceType.NETWORK: {
                "warning": 100.0,
                "error": 500.0,
                "critical": 1000.0,
            },  # MB/s
            ResourceType.DATABASE: {
                "warning": 100,
                "error": 200,
                "critical": 500,
            },  # 连接数
            ResourceType.CACHE: {
                "warning": 80.0,
                "error": 90.0,
                "critical": 95.0,
            },  # 使用率
        }

        # 优化建议缓存
        self.optimization_cache: dict[str, OptimizationRecommendation] = {}

        # 监控任务
        self.monitoring_task: asyncio.Task[None] | None = None
        self.is_monitoring = False

    async def start_monitoring(self) -> None:
        """开始性能监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("性能监控已启动")

    async def stop_monitoring(self) -> None:
        """停止性能监控"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("性能监控已停止")

    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统资源使用情况
                resource_usage = await self._collect_resource_usage()

                # 生成性能指标
                metrics = self._generate_performance_metrics(resource_usage)

                # 存储指标
                for metric in metrics:
                    self.metrics_history[metric.resource_type].append(metric)

                # 检查告警条件
                await self._check_alert_conditions(metrics)

                # 生成优化建议
                await self._generate_optimization_recommendations(resource_usage)

                # 等待下一次检查
                await asyncio.sleep(5)  # 每5秒检查一次

            except Exception as e:
                self.logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(10)  # 错误时等待更长时间

    async def _collect_resource_usage(self) -> ResourceUsage:
        """收集资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # 网络IO
            network_io = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": float(network_io.bytes_sent),
                "bytes_recv": float(network_io.bytes_recv),
                "packets_sent": float(network_io.packets_sent),
                "packets_recv": float(network_io.packets_recv),
            }

            # 活跃连接数（估算）
            active_connections = len(psutil.net_connections())

            return ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_stats,
                active_connections=active_connections,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            self.logger.error(f"收集资源使用情况失败: {e}")
            # 返回默认值
            return ResourceUsage(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={},
                active_connections=0,
                timestamp=datetime.utcnow(),
            )

    def _generate_performance_metrics(self, usage: ResourceUsage) -> list[PerformanceMetric]:
        """生成性能指标"""
        metrics = []

        # CPU指标
        metrics.append(
            PerformanceMetric(
                metric_type=MetricType.CPU_USAGE,
                value=usage.cpu_percent,
                timestamp=usage.timestamp,
                resource_type=ResourceType.CPU,
                metadata={"unit": "percent"},
            )
        )

        # 内存指标
        metrics.append(
            PerformanceMetric(
                metric_type=MetricType.MEMORY_USAGE,
                value=usage.memory_percent,
                timestamp=usage.timestamp,
                resource_type=ResourceType.MEMORY,
                metadata={"unit": "percent"},
            )
        )

        # 磁盘指标
        metrics.append(
            PerformanceMetric(
                metric_type=MetricType.DISK_USAGE,
                value=usage.disk_percent,
                timestamp=usage.timestamp,
                resource_type=ResourceType.DISK,
                metadata={"unit": "percent"},
            )
        )

        # 网络指标
        if usage.network_io:
            network_throughput = (
                usage.network_io.get("bytes_sent", 0) + usage.network_io.get("bytes_recv", 0)
            ) / (1024 * 1024)  # 转换为MB

            metrics.append(
                PerformanceMetric(
                    metric_type=MetricType.NETWORK_THROUGHPUT,
                    value=network_throughput,
                    timestamp=usage.timestamp,
                    resource_type=ResourceType.NETWORK,
                    metadata={"unit": "MB", "details": usage.network_io},
                )
            )

        # 连接数指标
        metrics.append(
            PerformanceMetric(
                metric_type=MetricType.ACTIVE_CONNECTIONS,
                value=float(usage.active_connections),
                timestamp=usage.timestamp,
                resource_type=ResourceType.DATABASE,
                metadata={"unit": "count"},
            )
        )

        return metrics

    async def _check_alert_conditions(self, metrics: list[PerformanceMetric]) -> None:
        """检查告警条件"""
        for metric in metrics:
            resource_type = metric.resource_type
            value = metric.value

            if resource_type not in self.thresholds:
                continue

            thresholds: dict[str, float] = self.thresholds[resource_type]
            alert_level = None

            # 确定告警级别
            if value >= thresholds.get("critical", float("inf")):
                alert_level = AlertLevel.CRITICAL
            elif value >= thresholds.get("error", float("inf")):
                alert_level = AlertLevel.ERROR
            elif value >= thresholds.get("warning", float("inf")):
                alert_level = AlertLevel.WARNING

            if alert_level:
                await self._create_alert(metric, alert_level)
            else:
                # 检查是否需要解决现有告警
                await self._resolve_alerts(resource_type, value)

    async def _create_alert(self, metric: PerformanceMetric, level: AlertLevel) -> None:
        """创建告警"""
        try:
            alert_id = (
                f"{metric.resource_type.value}_{level.value}_{int(metric.timestamp.timestamp())}"
            )

            # 避免重复告警
            existing_alerts = [
                alert
                for alert in self.active_alerts.values()
                if alert.resource_type == metric.resource_type and not alert.resolved
            ]

            if existing_alerts:
                return

            threshold_dict: dict[str, float] = self.thresholds[metric.resource_type]
            threshold = threshold_dict.get(level.value, 0)

            alert = PerformanceAlert(
                alert_id=alert_id,
                level=level,
                resource_type=metric.resource_type,
                message=self._generate_alert_message(metric, level, threshold),
                current_value=metric.value,
                threshold=threshold,
                timestamp=metric.timestamp,
            )

            self.active_alerts[alert_id] = alert

            # 触发告警回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回调执行失败: {e}")

            self.logger.warning(f"性能告警: {alert.message}")

        except Exception as e:
            self.logger.error(f"创建告警失败: {e}")

    async def _resolve_alerts(self, resource_type: ResourceType, current_value: float) -> None:
        """解决告警"""
        try:
            alerts_to_resolve = []

            for alert in self.active_alerts.values():
                if alert.resource_type == resource_type and not alert.resolved:
                    # 检查是否满足解决条件
                    threshold_dict: dict[str, float] = self.thresholds[resource_type]
                    threshold = threshold_dict.get("warning", float("inf"))
                    should_resolve = current_value < threshold * 0.9  # 10%缓冲

                    if should_resolve:
                        alerts_to_resolve.append(alert)

            # 解决告警
            for alert in alerts_to_resolve:
                alert.resolved = True
                self.logger.info(f"告警已解决: {alert.message}")

        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")

    def _generate_alert_message(
        self, metric: PerformanceMetric, level: AlertLevel, threshold: float
    ) -> str:
        """生成告警消息"""
        resource_name = {
            ResourceType.CPU: "CPU使用率",
            ResourceType.MEMORY: "内存使用率",
            ResourceType.DISK: "磁盘使用率",
            ResourceType.NETWORK: "网络吞吐量",
            ResourceType.DATABASE: "数据库连接数",
            ResourceType.CACHE: "缓存使用率",
        }.get(metric.resource_type, str(metric.resource_type))

        if metric.resource_type in [
            ResourceType.CPU,
            ResourceType.MEMORY,
            ResourceType.DISK,
            ResourceType.CACHE,
        ]:
            return f"{resource_name} {level.value}: {metric.value:.1f}% (阈值: {threshold:.1f}%)"
        elif metric.resource_type == ResourceType.NETWORK:
            return f"{resource_name} {level.value}: {metric.value:.1f} MB/s (阈值: {threshold:.1f} MB/s)"
        elif metric.resource_type == ResourceType.DATABASE:
            return f"{resource_name} {level.value}: {metric.value:.0f} 个连接 (阈值: {threshold:.0f} 个)"
        else:
            return f"{resource_name} {level.value}: {metric.value:.2f} (阈值: {threshold:.2f})"

    async def _generate_optimization_recommendations(self, usage: ResourceUsage) -> None:
        """生成优化建议"""
        try:
            recommendations = []

            # CPU优化建议
            if usage.cpu_percent > 80:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"cpu_opt_{int(time.time())}",
                        resource_type=ResourceType.CPU,
                        issue_description=f"CPU使用率过高: {usage.cpu_percent:.1f}%",
                        recommended_action="考虑增加CPU核心数或优化计算密集型任务",
                        expected_improvement="降低CPU使用率15-30%",
                        priority=1,
                        implementation_complexity="中等",
                    )
                )

            # 内存优化建议
            if usage.memory_percent > 85:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"memory_opt_{int(time.time())}",
                        resource_type=ResourceType.MEMORY,
                        issue_description=f"内存使用率过高: {usage.memory_percent:.1f}%",
                        recommended_action="增加内存容量或优化内存使用模式",
                        expected_improvement="降低内存使用率20-40%",
                        priority=1,
                        implementation_complexity="简单",
                    )
                )

            # 磁盘优化建议
            if usage.disk_percent > 85:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"disk_opt_{int(time.time())}",
                        resource_type=ResourceType.DISK,
                        issue_description=f"磁盘使用率过高: {usage.disk_percent:.1f}%",
                        recommended_action="清理临时文件或增加存储容量",
                        expected_improvement="释放10-30%磁盘空间",
                        priority=2,
                        implementation_complexity="简单",
                    )
                )

            # 网络优化建议
            network_throughput = (
                usage.network_io.get("bytes_sent", 0) + usage.network_io.get("bytes_recv", 0)
            ) / (1024 * 1024)

            if network_throughput > 100:  # 100MB/s
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"network_opt_{int(time.time())}",
                        resource_type=ResourceType.NETWORK,
                        issue_description=f"网络吞吐量较高: {network_throughput:.1f} MB/s",
                        recommended_action="考虑启用压缩或优化数据传输",
                        expected_improvement="减少网络带宽使用20-50%",
                        priority=3,
                        implementation_complexity="中等",
                    )
                )

            # 更新优化建议缓存
            for rec in recommendations:
                self.optimization_cache[rec.recommendation_id] = rec

        except Exception as e:
            self.logger.error(f"生成优化建议失败: {e}")

    def get_performance_level(self, resource_type: ResourceType) -> PerformanceLevel:
        """获取性能等级"""
        try:
            if resource_type not in self.metrics_history:
                return PerformanceLevel.FAIR

            recent_metrics = list(self.metrics_history[resource_type])[-10:]  # 最近10个指标
            if not recent_metrics:
                return PerformanceLevel.FAIR

            avg_value = sum(m.value for m in recent_metrics) / len(recent_metrics)
            thresholds: dict[str, float] = self.thresholds.get(resource_type, {})

            if avg_value >= thresholds.get("critical", float("inf")):
                return PerformanceLevel.CRITICAL
            elif avg_value >= thresholds.get("error", float("inf")):
                return PerformanceLevel.POOR
            elif avg_value >= thresholds.get("warning", float("inf")):
                return PerformanceLevel.FAIR
            elif avg_value < thresholds.get("warning", 0) * 0.5:
                return PerformanceLevel.EXCELLENT
            else:
                return PerformanceLevel.GOOD

        except Exception as e:
            self.logger.error(f"获取性能等级失败: {e}")
            return PerformanceLevel.FAIR

    def get_optimization_recommendations(
        self, resource_type: ResourceType | None = None
    ) -> list[OptimizationRecommendation]:
        """获取优化建议"""
        try:
            if resource_type:
                return [
                    rec
                    for rec in self.optimization_cache.values()
                    if rec.resource_type == resource_type
                ]
            else:
                return list(self.optimization_cache.values())

        except Exception as e:
            self.logger.error(f"获取优化建议失败: {e}")
            return []

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        try:
            summary: dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat(),
                "resource_levels": {},
                "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
                "total_recommendations": len(self.optimization_cache),
                "monitoring_status": "active" if self.is_monitoring else "inactive",
            }

            # 各资源性能等级
            for resource_type in ResourceType:
                level = self.get_performance_level(resource_type)
                summary["resource_levels"][resource_type.value] = level.value

            return summary

        except Exception as e:
            self.logger.error(f"获取性能摘要失败: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "monitoring_status": "error",
            }


# 全局性能服务实例
_performance_service: PerformanceService | None = None


async def get_performance_service() -> PerformanceService:
    """获取性能服务实例"""
    global _performance_service

    if _performance_service is None:
        from app.core.database import get_db

        async for db in get_db():
            _performance_service = PerformanceService(db)
            await _performance_service.start_monitoring()
            break

    if _performance_service is None:
        raise RuntimeError("无法初始化性能服务")

    return _performance_service
