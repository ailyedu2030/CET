"""
指标收集器

提供全面的系统指标收集和分析：
- 实时性能指标收集
- 自定义指标定义
- 指标聚合和统计
- 历史数据存储
- 告警和通知
- Prometheus格式指标输出
"""

import asyncio
import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.shared.models.enums import AlertLevel, MetricType

# Prometheus客户端支持
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )
    from prometheus_client import Enum as PrometheusEnum

    PROMETHEUS_AVAILABLE = True
except ImportError:
    # 如果prometheus_client不可用，创建模拟类
    class Counter:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._value = 0

        def inc(self, amount: float = 1) -> None:
            self._value += amount

        def labels(self, **kwargs: Any) -> "Counter":
            return self  # type: ignore[return-value]

    class Histogram:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._observations: list[float] = []

        def observe(self, amount: float) -> None:
            self._observations.append(amount)

        def labels(self, **kwargs: Any) -> "Histogram":
            return self  # type: ignore[return-value]

        def time(self) -> Any:
            return MockTimer()

    class Gauge:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._value = 0

        def set(self, value: float) -> None:
            self._value = value

        def inc(self, amount: float = 1) -> None:
            self._value += amount

        def dec(self, amount: float = 1) -> None:
            self._value -= amount

        def labels(self, **kwargs: Any) -> "Gauge":
            return self  # type: ignore[return-value]

    class Info:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def info(self, info_dict: dict[str, str]) -> None:
            pass

    class PrometheusEnum:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def state(self, state: str) -> None:
            pass

    class CollectorRegistry:  # type: ignore[no-redef]
        def __init__(self) -> None:
            pass

    class MockTimer:
        def __enter__(self) -> "MockTimer":
            return self

        def __exit__(self, *args: Any) -> None:
            pass

    def generate_latest(registry: Any) -> bytes:
        return b"# Mock metrics\n"

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AggregationType(Enum):
    """聚合类型"""

    SUM = "sum"  # 求和
    AVERAGE = "average"  # 平均值
    MIN = "min"  # 最小值
    MAX = "max"  # 最大值
    COUNT = "count"  # 计数
    PERCENTILE_95 = "percentile_95"  # 95分位数
    PERCENTILE_99 = "percentile_99"  # 99分位数


class MetricUnit(Enum):
    """指标单位"""

    NONE = "none"  # 无单位
    BYTES = "bytes"  # 字节
    SECONDS = "seconds"  # 秒
    MILLISECONDS = "milliseconds"  # 毫秒
    PERCENT = "percent"  # 百分比
    COUNT = "count"  # 计数
    RATE = "rate"  # 速率


@dataclass
class MetricDefinition:
    """指标定义"""

    name: str
    metric_type: MetricType
    unit: MetricUnit
    description: str
    tags: dict[str, str] = field(default_factory=dict)
    aggregations: list[AggregationType] = field(default_factory=lambda: [AggregationType.AVERAGE])
    retention_period: timedelta = field(default_factory=lambda: timedelta(days=7))


@dataclass
class MetricPoint:
    """指标数据点"""

    name: str
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """聚合指标"""

    name: str
    aggregation_type: AggregationType
    value: float
    start_time: datetime
    end_time: datetime
    sample_count: int
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricAlert:
    """指标告警"""

    alert_id: str
    metric_name: str
    level: AlertLevel
    threshold: float
    current_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_points_per_metric: int = 10000) -> None:
        self.max_points_per_metric = max_points_per_metric
        self.logger = logging.getLogger(__name__)

        # 指标定义注册表
        self.metric_definitions: dict[str, MetricDefinition] = {}

        # 原始指标数据存储
        self.raw_metrics: dict[str, deque[MetricPoint]] = defaultdict(
            lambda: deque(maxlen=self.max_points_per_metric)
        )

        # 聚合指标缓存
        self.aggregated_metrics: dict[str, dict[AggregationType, AggregatedMetric]] = defaultdict(
            dict
        )

        # 告警规则
        self.alert_rules: dict[str, dict[str, Any]] = {}

        # 活跃告警
        self.active_alerts: dict[str, MetricAlert] = {}

        # 告警回调
        self.alert_callbacks: list[Callable[[MetricAlert], None]] = []

        # 收集器状态
        self.is_collecting = False
        self.collection_task: asyncio.Task[None] | None = None
        self.collection_interval = 1.0  # 秒

        # 性能统计
        self.collection_stats: dict[str, Any] = {
            "total_points_collected": 0,
            "collection_errors": 0,
            "last_collection_time": None,
            "collection_duration": 0.0,
        }

    def register_metric(self, definition: MetricDefinition) -> None:
        """注册指标定义"""
        self.metric_definitions[definition.name] = definition
        self.logger.info(f"注册指标: {definition.name} ({definition.metric_type.value})")

    def add_alert_rule(
        self,
        metric_name: str,
        threshold: float,
        level: AlertLevel,
        comparison: str = "greater",  # greater, less, equal
        tags_filter: dict[str, str] | None = None,
    ) -> None:
        """添加告警规则"""
        rule_id = f"{metric_name}_{level.value}_{int(time.time())}"
        self.alert_rules[rule_id] = {
            "metric_name": metric_name,
            "threshold": threshold,
            "level": level,
            "comparison": comparison,
            "tags_filter": tags_filter or {},
        }
        self.logger.info(f"添加告警规则: {metric_name} {comparison} {threshold}")

    async def collect_metric(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """收集单个指标"""
        try:
            point = MetricPoint(
                name=name,
                value=value,
                timestamp=timestamp or datetime.utcnow(),
                tags=tags or {},
            )

            # 添加到原始数据存储
            self.raw_metrics[name].append(point)

            # 更新统计
            self.collection_stats["total_points_collected"] += 1
            self.collection_stats["last_collection_time"] = datetime.utcnow()

            # 检查告警
            await self._check_alerts(point)

        except Exception as e:
            self.logger.error(f"收集指标失败: {name}, 错误: {e}")
            self.collection_stats["collection_errors"] += 1

    async def collect_metrics_batch(self, points: list[MetricPoint]) -> None:
        """批量收集指标"""
        start_time = time.time()

        try:
            for point in points:
                await self.collect_metric(point.name, point.value, point.tags, point.timestamp)

        except Exception as e:
            self.logger.error(f"批量收集指标失败: {e}")

        finally:
            self.collection_stats["collection_duration"] = time.time() - start_time

    async def start_collection(self) -> None:
        """启动自动收集"""
        if self.is_collecting:
            return

        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("指标收集器已启动")

    async def stop_collection(self) -> None:
        """停止自动收集"""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("指标收集器已停止")

    async def _collection_loop(self) -> None:
        """收集循环"""
        while self.is_collecting:
            try:
                start_time = time.time()

                # 执行自动收集任务
                await self._auto_collect_system_metrics()

                # 更新聚合指标
                await self._update_aggregated_metrics()

                # 清理过期数据
                await self._cleanup_expired_data()

                # 记录收集时间
                self.collection_stats["collection_duration"] = time.time() - start_time

                # 等待下次收集
                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                self.logger.error(f"收集循环错误: {e}")
                await asyncio.sleep(5)

    async def _auto_collect_system_metrics(self) -> None:
        """自动收集系统指标"""
        try:
            import psutil

            # CPU使用率
            cpu_percent = psutil.cpu_percent()
            await self.collect_metric("system.cpu.usage", float(cpu_percent), {"unit": "percent"})

            # 内存使用率
            memory = psutil.virtual_memory()
            await self.collect_metric(
                "system.memory.usage", float(memory.percent), {"unit": "percent"}
            )
            await self.collect_metric(
                "system.memory.available", float(memory.available), {"unit": "bytes"}
            )

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = (float(disk.used) / float(disk.total)) * 100
            await self.collect_metric("system.disk.usage", disk_percent, {"unit": "percent"})

            # 网络IO
            network = psutil.net_io_counters()
            await self.collect_metric(
                "system.network.bytes_sent",
                float(network.bytes_sent),
                {"unit": "bytes"},
            )
            await self.collect_metric(
                "system.network.bytes_recv",
                float(network.bytes_recv),
                {"unit": "bytes"},
            )

        except Exception as e:
            self.logger.error(f"自动收集系统指标失败: {e}")

    async def _update_aggregated_metrics(self) -> None:
        """更新聚合指标"""
        try:
            current_time = datetime.utcnow()

            for metric_name, points in self.raw_metrics.items():
                if not points:
                    continue

                # 获取指标定义
                definition = self.metric_definitions.get(metric_name)
                if not definition:
                    continue

                # 计算时间窗口（最近5分钟）
                window_start = current_time - timedelta(minutes=5)
                window_points = [p for p in points if p.timestamp >= window_start]

                if not window_points:
                    continue

                # 计算各种聚合
                values = [p.value for p in window_points]

                for agg_type in definition.aggregations:
                    agg_value = self._calculate_aggregation(values, agg_type)

                    aggregated = AggregatedMetric(
                        name=metric_name,
                        aggregation_type=agg_type,
                        value=agg_value,
                        start_time=window_start,
                        end_time=current_time,
                        sample_count=len(values),
                    )

                    self.aggregated_metrics[metric_name][agg_type] = aggregated

        except Exception as e:
            self.logger.error(f"更新聚合指标失败: {e}")

    def _calculate_aggregation(self, values: list[float], agg_type: AggregationType) -> float:
        """计算聚合值"""
        if not values:
            return 0.0

        if agg_type == AggregationType.SUM:
            return sum(values)
        elif agg_type == AggregationType.AVERAGE:
            return statistics.mean(values)
        elif agg_type == AggregationType.MIN:
            return min(values)
        elif agg_type == AggregationType.MAX:
            return max(values)
        elif agg_type == AggregationType.COUNT:
            return float(len(values))
        elif agg_type == AggregationType.PERCENTILE_95:
            return statistics.quantiles(values, n=20)[18]  # 95th percentile
        elif agg_type == AggregationType.PERCENTILE_99:
            return statistics.quantiles(values, n=100)[98]  # 99th percentile

        # 对于未知的聚合类型，返回平均值
        return statistics.mean(values)  # type: ignore[unreachable]

    async def _check_alerts(self, point: MetricPoint) -> None:
        """检查告警条件"""
        try:
            for rule_id, rule in self.alert_rules.items():
                if rule["metric_name"] != point.name:
                    continue

                # 检查标签过滤
                tags_filter = rule["tags_filter"]
                if tags_filter:
                    if not all(point.tags.get(k) == v for k, v in tags_filter.items()):
                        continue

                # 检查阈值
                threshold = rule["threshold"]
                comparison = rule["comparison"]
                triggered = False

                if comparison == "greater" and point.value > threshold:
                    triggered = True
                elif comparison == "less" and point.value < threshold:
                    triggered = True
                elif comparison == "equal" and abs(point.value - threshold) < 0.001:
                    triggered = True

                if triggered:
                    await self._create_alert(rule, point)
                else:
                    # 检查是否需要解决告警
                    await self._resolve_alert(rule_id, point)

        except Exception as e:
            self.logger.error(f"检查告警失败: {e}")

    async def _create_alert(self, rule: dict[str, Any], point: MetricPoint) -> None:
        """创建告警"""
        try:
            alert_id = f"{rule['metric_name']}_{rule['level'].value}_{int(time.time())}"

            # 避免重复告警
            existing_alerts = [
                alert
                for alert in self.active_alerts.values()
                if alert.metric_name == rule["metric_name"]
                and alert.level == rule["level"]
                and not alert.resolved
            ]

            if existing_alerts:
                return

            alert = MetricAlert(
                alert_id=alert_id,
                metric_name=rule["metric_name"],
                level=rule["level"],
                threshold=rule["threshold"],
                current_value=point.value,
                message=f"指标 {rule['metric_name']} {rule['comparison']} {rule['threshold']}: 当前值 {point.value}",
                timestamp=point.timestamp,
                tags=point.tags,
            )

            self.active_alerts[alert_id] = alert

            # 触发告警回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回调执行失败: {e}")

            self.logger.warning(f"指标告警: {alert.message}")

        except Exception as e:
            self.logger.error(f"创建告警失败: {e}")

    async def _resolve_alert(self, rule_id: str, point: MetricPoint) -> None:
        """解决告警"""
        try:
            alerts_to_resolve = []

            for alert in self.active_alerts.values():
                if alert.metric_name == point.name and not alert.resolved:
                    # 检查是否满足解决条件（值回到正常范围）
                    rule = self.alert_rules.get(rule_id)
                    if rule:
                        threshold = rule["threshold"]
                        comparison = rule["comparison"]
                        should_resolve = False

                        if comparison == "greater" and point.value <= threshold * 0.9:
                            should_resolve = True
                        elif comparison == "less" and point.value >= threshold * 1.1:
                            should_resolve = True

                        if should_resolve:
                            alerts_to_resolve.append(alert)

            # 解决告警
            for alert in alerts_to_resolve:
                alert.resolved = True
                self.logger.info(f"告警已解决: {alert.message}")

        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")

    async def _cleanup_expired_data(self) -> None:
        """清理过期数据"""
        try:
            current_time = datetime.utcnow()

            for metric_name, points in self.raw_metrics.items():
                definition = self.metric_definitions.get(metric_name)
                if not definition:
                    continue

                # 清理超过保留期的数据
                cutoff_time = current_time - definition.retention_period
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()

        except Exception as e:
            self.logger.error(f"清理过期数据失败: {e}")

    def get_metric_values(
        self,
        metric_name: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        tags_filter: dict[str, str] | None = None,
    ) -> list[MetricPoint]:
        """获取指标值"""
        points: list[MetricPoint] = list(self.raw_metrics.get(metric_name, []))

        # 时间过滤
        if start_time or end_time:
            filtered_points = []
            for point in points:
                if start_time and point.timestamp < start_time:
                    continue
                if end_time and point.timestamp > end_time:
                    continue
                filtered_points.append(point)
            points = filtered_points

        # 标签过滤
        if tags_filter:
            filtered_points = []
            for point in points:
                if all(point.tags.get(k) == v for k, v in tags_filter.items()):
                    filtered_points.append(point)
            points = filtered_points

        return list(points)

    def get_aggregated_metric(
        self, metric_name: str, aggregation_type: AggregationType
    ) -> AggregatedMetric | None:
        """获取聚合指标"""
        return self.aggregated_metrics.get(metric_name, {}).get(aggregation_type)

    def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        summary: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_metrics": len(self.metric_definitions),
            "total_data_points": sum(len(points) for points in self.raw_metrics.values()),
            "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
            "collection_stats": self.collection_stats,
            "metrics": {},
        }

        # 各指标的基本统计
        for name, points in self.raw_metrics.items():
            if points:
                values = [p.value for p in points]
                summary["metrics"][name] = {
                    "count": len(values),
                    "latest_value": values[-1],
                    "min": min(values),
                    "max": max(values),
                    "average": statistics.mean(values),
                }

        return summary

    def add_alert_callback(self, callback: Callable[[MetricAlert], None]) -> None:
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def export_metrics(self, format_type: str = "json", include_raw_data: bool = False) -> str:
        """导出指标数据"""
        export_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "definitions": {
                name: {
                    "name": def_.name,
                    "type": def_.metric_type.value,
                    "unit": def_.unit.value,
                    "description": def_.description,
                    "tags": def_.tags,
                }
                for name, def_ in self.metric_definitions.items()
            },
            "aggregated_metrics": {},
        }

        # 导出聚合指标
        for metric_name, agg_dict in self.aggregated_metrics.items():
            export_data["aggregated_metrics"][metric_name] = {}
            for agg_type, agg_metric in agg_dict.items():
                export_data["aggregated_metrics"][metric_name][agg_type.value] = {
                    "value": agg_metric.value,
                    "start_time": agg_metric.start_time.isoformat(),
                    "end_time": agg_metric.end_time.isoformat(),
                    "sample_count": agg_metric.sample_count,
                }

        # 可选导出原始数据
        if include_raw_data:
            export_data["raw_data"] = {}
            for metric_name, points in self.raw_metrics.items():
                export_data["raw_data"][metric_name] = [
                    {
                        "value": p.value,
                        "timestamp": p.timestamp.isoformat(),
                        "tags": p.tags,
                    }
                    for p in points
                ]

        if format_type == "json":
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            return str(export_data)


# 全局指标收集器实例
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()

    return _metrics_collector


# 便捷函数
async def collect_metric(
    name: str,
    value: float,
    tags: dict[str, str] | None = None,
    timestamp: datetime | None = None,
) -> None:
    """收集指标的便捷函数"""
    collector = get_metrics_collector()
    await collector.collect_metric(name, value, tags, timestamp)


def register_system_metrics() -> None:
    """注册系统指标"""
    collector = get_metrics_collector()

    # CPU指标
    collector.register_metric(
        MetricDefinition(
            name="system.cpu.usage",
            metric_type=MetricType.CPU_USAGE,
            unit=MetricUnit.PERCENT,
            description="CPU使用率",
            aggregations=[AggregationType.AVERAGE, AggregationType.MAX],
        )
    )

    # 内存指标
    collector.register_metric(
        MetricDefinition(
            name="system.memory.usage",
            metric_type=MetricType.MEMORY_USAGE,
            unit=MetricUnit.PERCENT,
            description="内存使用率",
            aggregations=[AggregationType.AVERAGE, AggregationType.MAX],
        )
    )

    # 网络指标
    collector.register_metric(
        MetricDefinition(
            name="system.network.throughput",
            metric_type=MetricType.NETWORK_THROUGHPUT,
            unit=MetricUnit.BYTES,
            description="网络吞吐量",
            aggregations=[AggregationType.SUM, AggregationType.AVERAGE],
        )
    )


class PrometheusMetricsCollector:
    """Prometheus格式指标收集器"""

    def __init__(self) -> None:
        """初始化Prometheus指标收集器"""
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        self._running = False
        self._collection_thread: threading.Thread | None = None

    def _setup_prometheus_metrics(self) -> None:
        """设置Prometheus指标"""
        # 系统资源指标
        self.cpu_usage = Gauge(
            "system_cpu_usage_percent", "CPU使用率百分比", registry=self.registry
        )

        self.memory_usage = Gauge(
            "system_memory_usage_percent", "内存使用率百分比", registry=self.registry
        )

        # HTTP请求指标
        self.http_requests_total = Counter(
            "http_requests_total",
            "HTTP请求总数",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP请求持续时间",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # 用户活动指标
        self.active_users_total = Gauge(
            "cet4_active_users_total", "当前活跃用户总数", registry=self.registry
        )

        self.active_students_total = Gauge(
            "cet4_active_students_total", "当前活跃学生数", registry=self.registry
        )

        self.active_teachers_total = Gauge(
            "cet4_active_teachers_total", "当前活跃教师数", registry=self.registry
        )

        self.user_actions_total = Counter(
            "cet4_user_actions_total",
            "用户操作总数",
            ["action", "user_type"],
            registry=self.registry,
        )

        # AI服务指标
        self.ai_service_requests_total = Counter(
            "ai_service_requests_total",
            "AI服务请求总数",
            ["service", "status"],
            registry=self.registry,
        )

        self.ai_service_request_duration = Histogram(
            "ai_service_request_duration_seconds",
            "AI服务请求持续时间",
            ["service"],
            registry=self.registry,
        )

        self.ai_service_daily_cost = Gauge(
            "ai_service_daily_cost_yuan",
            "AI服务日成本（元）",
            ["service"],
            registry=self.registry,
        )

        self.ai_service_quota_usage = Gauge(
            "ai_service_quota_usage_percent",
            "AI服务配额使用率",
            ["service"],
            registry=self.registry,
        )

        # 系统信息
        self.system_info = Info("cet4_system_info", "CET4系统信息", registry=self.registry)

        # 设置系统信息
        self.system_info.info(
            {
                "version": "1.0.0",
                "environment": "production",
                "python_version": "3.11",
                "framework": "FastAPI",
            }
        )

    def start_collection(self) -> None:
        """启动指标收集"""
        if self._running:
            return

        self._running = True
        self._collection_thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        self._collection_thread.start()
        logger.info("Prometheus metrics collection started")

    def stop_collection(self) -> None:
        """停止指标收集"""
        self._running = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Prometheus metrics collection stopped")

    def _collect_system_metrics(self) -> None:
        """收集系统指标"""

        import psutil

        while self._running:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.set(cpu_percent)

                # 内存使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self.memory_usage.set(memory_percent)

                time.sleep(30)  # 每30秒收集一次

            except Exception as e:
                logger.error(f"Error collecting system metrics: {str(e)}")
                time.sleep(30)

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """记录HTTP请求指标"""
        status = str(status_code)
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def set_active_users(self, total: int, students: int, teachers: int) -> None:
        """设置活跃用户数"""
        self.active_users_total.set(total)
        self.active_students_total.set(students)
        self.active_teachers_total.set(teachers)

    def record_user_action(self, action: str, user_type: str) -> None:
        """记录用户操作"""
        self.user_actions_total.labels(action=action, user_type=user_type).inc()

    def record_ai_service_request(
        self, service: str, status: str, duration: float, cost: float | None = None
    ) -> None:
        """记录AI服务请求"""
        self.ai_service_requests_total.labels(service=service, status=status).inc()

        self.ai_service_request_duration.labels(service=service).observe(duration)

        if cost is not None:
            current_cost = getattr(self.ai_service_daily_cost.labels(service=service), "_value", 0)
            self.ai_service_daily_cost.labels(service=service).set(current_cost + cost)

    def set_ai_service_quota_usage(self, service: str, usage_percent: float) -> None:
        """设置AI服务配额使用率"""
        self.ai_service_quota_usage.labels(service=service).set(usage_percent)

    def get_metrics(self) -> bytes:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """获取指标内容类型"""
        return CONTENT_TYPE_LATEST


# 全局Prometheus指标收集器实例
prometheus_metrics_collector = PrometheusMetricsCollector()
