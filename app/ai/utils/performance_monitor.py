"""
AI性能监控工具

提供全面的性能监控和分析功能：
- 实时性能指标收集
- 性能趋势分析
- 异常检测和告警
- 性能优化建议
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.shared.models.enums import AIModelType


class MetricType(Enum):
    """指标类型"""

    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    QUEUE_LENGTH = "queue_length"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    TOKEN_RATE = "token_rate"


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """性能指标"""

    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolution_time: datetime | None = None


@dataclass
class PerformanceReport:
    """性能报告"""

    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    error_rate: float
    alerts_count: int
    top_errors: list[dict[str, Any]]


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history_size: int = 10000) -> None:
        self.logger = logging.getLogger(__name__)
        self.max_history_size = max_history_size

        # 性能指标存储
        self.metrics_history: dict[MetricType, deque[PerformanceMetric]] = {
            metric_type: deque(maxlen=max_history_size) for metric_type in MetricType
        }

        # 告警存储
        self.active_alerts: dict[str, PerformanceAlert] = {}
        self.alert_history: deque[PerformanceAlert] = deque(maxlen=1000)

        # 性能阈值配置
        self.thresholds = {
            MetricType.RESPONSE_TIME: {"warning": 3.0, "error": 5.0, "critical": 10.0},
            MetricType.ERROR_RATE: {
                "warning": 0.05,  # 5%
                "error": 0.10,  # 10%
                "critical": 0.20,  # 20%
            },
            MetricType.SUCCESS_RATE: {
                "warning": 0.95,  # 95%
                "error": 0.90,  # 90%
                "critical": 0.80,  # 80%
            },
            MetricType.THROUGHPUT: {
                "warning": 10.0,  # 每秒10个请求
                "error": 5.0,  # 每秒5个请求
                "critical": 1.0,  # 每秒1个请求
            },
            MetricType.QUEUE_LENGTH: {"warning": 50, "error": 100, "critical": 200},
        }

        # 统计窗口
        self.stats_windows = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
        }

        # 请求跟踪
        self.active_requests: dict[str, dict[str, Any]] = {}
        self.request_history: deque[dict[str, Any]] = deque(maxlen=max_history_size)

        # 告警回调
        self.alert_callbacks: list[Callable[[PerformanceAlert], Awaitable[None]]] = []

    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """记录性能指标"""
        try:
            metric = PerformanceMetric(
                metric_type=metric_type,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metadata=metadata or {},
            )

            self.metrics_history[metric_type].append(metric)

            # 检查是否触发告警
            asyncio.create_task(self._check_alert_conditions(metric))

        except Exception as e:
            self.logger.error(f"记录性能指标失败: {e}")

    async def start_request_tracking(
        self,
        request_id: str,
        model_type: AIModelType,
        estimated_tokens: int = 0,
        priority: str = "normal",
    ) -> None:
        """开始请求跟踪"""
        try:
            self.active_requests[request_id] = {
                "start_time": time.time(),
                "model_type": model_type.value,
                "estimated_tokens": estimated_tokens,
                "priority": priority,
                "status": "processing",
            }

            # 记录队列长度
            self.record_metric(MetricType.QUEUE_LENGTH, len(self.active_requests))

        except Exception as e:
            self.logger.error(f"开始请求跟踪失败: {e}")

    async def end_request_tracking(
        self,
        request_id: str,
        success: bool,
        actual_tokens: int = 0,
        error_message: str | None = None,
    ) -> None:
        """结束请求跟踪"""
        try:
            if request_id not in self.active_requests:
                self.logger.warning(f"未找到请求跟踪记录: {request_id}")
                return

            request_info = self.active_requests.pop(request_id)
            end_time = time.time()
            response_time = end_time - request_info["start_time"]

            # 记录请求历史
            request_record = {
                "request_id": request_id,
                "start_time": request_info["start_time"],
                "end_time": end_time,
                "response_time": response_time,
                "success": success,
                "model_type": request_info["model_type"],
                "estimated_tokens": request_info["estimated_tokens"],
                "actual_tokens": actual_tokens,
                "priority": request_info["priority"],
                "error_message": error_message,
            }

            self.request_history.append(request_record)

            # 记录性能指标
            self.record_metric(MetricType.RESPONSE_TIME, response_time)

            # 更新队列长度
            self.record_metric(MetricType.QUEUE_LENGTH, len(self.active_requests))

            # 计算并记录成功率和错误率
            await self._update_success_error_rates()

            # 计算并记录吞吐量
            await self._update_throughput()

        except Exception as e:
            self.logger.error(f"结束请求跟踪失败: {e}")

    async def _update_success_error_rates(self) -> None:
        """更新成功率和错误率"""
        try:
            # 计算最近5分钟的成功率
            cutoff_time = time.time() - 300  # 5分钟
            recent_requests = [
                req for req in self.request_history if req["end_time"] >= cutoff_time
            ]

            if recent_requests:
                successful = sum(1 for req in recent_requests if req["success"])
                total = len(recent_requests)

                success_rate = successful / total
                error_rate = 1.0 - success_rate

                self.record_metric(MetricType.SUCCESS_RATE, success_rate)
                self.record_metric(MetricType.ERROR_RATE, error_rate)

        except Exception as e:
            self.logger.error(f"更新成功率失败: {e}")

    async def _update_throughput(self) -> None:
        """更新吞吐量"""
        try:
            # 计算最近1分钟的吞吐量
            cutoff_time = time.time() - 60  # 1分钟
            recent_requests = [
                req for req in self.request_history if req["end_time"] >= cutoff_time
            ]

            throughput = len(recent_requests) / 60.0  # 每秒请求数
            self.record_metric(MetricType.THROUGHPUT, throughput)

        except Exception as e:
            self.logger.error(f"更新吞吐量失败: {e}")

    async def _check_alert_conditions(self, metric: PerformanceMetric) -> None:
        """检查告警条件"""
        try:
            metric_type = metric.metric_type
            value = metric.value

            if metric_type not in self.thresholds:
                return

            thresholds: dict[str, float] = self.thresholds[metric_type]
            alert_level = None

            # 确定告警级别
            if metric_type in [MetricType.SUCCESS_RATE, MetricType.THROUGHPUT]:
                # 这些指标值越低越严重
                if value < thresholds.get("critical", 0):
                    alert_level = AlertLevel.CRITICAL
                elif value < thresholds.get("error", 0):
                    alert_level = AlertLevel.ERROR
                elif value < thresholds.get("warning", 0):
                    alert_level = AlertLevel.WARNING
            else:
                # 这些指标值越高越严重
                if value > thresholds.get("critical", float("inf")):
                    alert_level = AlertLevel.CRITICAL
                elif value > thresholds.get("error", float("inf")):
                    alert_level = AlertLevel.ERROR
                elif value > thresholds.get("warning", float("inf")):
                    alert_level = AlertLevel.WARNING

            if alert_level:
                await self._create_alert(metric, alert_level)
            else:
                # 检查是否需要解决现有告警
                await self._resolve_alerts(metric_type, value)

        except Exception as e:
            self.logger.error(f"检查告警条件失败: {e}")

    async def _create_alert(self, metric: PerformanceMetric, level: AlertLevel) -> None:
        """创建告警"""
        try:
            alert_id = (
                f"{metric.metric_type.value}_{level.value}_{int(metric.timestamp.timestamp())}"
            )

            # 避免重复告警
            existing_alerts = [
                alert
                for alert in self.active_alerts.values()
                if alert.metric_type == metric.metric_type
                and alert.level == level
                and not alert.resolved
            ]

            if existing_alerts:
                return

            threshold_dict: dict[str, float] = self.thresholds[metric.metric_type]
            threshold: float = threshold_dict.get(level.value, 0.0)

            alert = PerformanceAlert(
                alert_id=alert_id,
                level=level,
                metric_type=metric.metric_type,
                message=self._generate_alert_message(metric, level, threshold),
                current_value=metric.value,
                threshold=threshold,
                timestamp=metric.timestamp,
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            self.logger.warning(f"性能告警: {alert.message}")

            # 触发告警回调
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回调执行失败: {e}")

        except Exception as e:
            self.logger.error(f"创建告警失败: {e}")

    async def _resolve_alerts(self, metric_type: MetricType, current_value: float) -> None:
        """解决告警"""
        try:
            alerts_to_resolve = []

            for alert in self.active_alerts.values():
                if alert.metric_type == metric_type and not alert.resolved:
                    # 检查是否满足解决条件
                    should_resolve = False

                    if metric_type in [MetricType.SUCCESS_RATE, MetricType.THROUGHPUT]:
                        # 这些指标需要恢复到正常水平
                        threshold_dict_success: dict[str, float] = self.thresholds[metric_type]
                        normal_threshold: float = threshold_dict_success.get("warning", 0.0)
                        should_resolve = current_value > normal_threshold * 1.1  # 10%缓冲
                    else:
                        # 这些指标需要降低到正常水平
                        threshold_dict_other: dict[str, float] = self.thresholds[metric_type]
                        normal_threshold = threshold_dict_other.get("warning", float("inf"))
                        should_resolve = current_value < normal_threshold * 0.9  # 10%缓冲

                    if should_resolve:
                        alerts_to_resolve.append(alert)

            # 解决告警
            for alert in alerts_to_resolve:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                self.logger.info(f"告警已解决: {alert.message}")

        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")

    def _generate_alert_message(
        self, metric: PerformanceMetric, level: AlertLevel, threshold: float
    ) -> str:
        """生成告警消息"""
        try:
            metric_name = metric.metric_type.value.replace("_", " ").title()

            if metric.metric_type == MetricType.RESPONSE_TIME:
                return f"{metric_name} {level.value}: {metric.value:.2f}s (threshold: {threshold:.2f}s)"
            elif metric.metric_type == MetricType.ERROR_RATE:
                return (
                    f"{metric_name} {level.value}: {metric.value:.1%} (threshold: {threshold:.1%})"
                )
            elif metric.metric_type == MetricType.SUCCESS_RATE:
                return (
                    f"{metric_name} {level.value}: {metric.value:.1%} (threshold: {threshold:.1%})"
                )
            elif metric.metric_type == MetricType.THROUGHPUT:
                return f"{metric_name} {level.value}: {metric.value:.1f} req/s (threshold: {threshold:.1f} req/s)"
            elif metric.metric_type == MetricType.QUEUE_LENGTH:
                return f"{metric_name} {level.value}: {metric.value:.0f} requests (threshold: {threshold:.0f})"
            else:
                return f"{metric_name} {level.value}: {metric.value} (threshold: {threshold})"

        except Exception as e:
            self.logger.error(f"生成告警消息失败: {e}")
            return f"Performance alert: {metric.metric_type.value} = {metric.value}"

    def get_current_metrics(self) -> dict[str, Any]:
        """获取当前性能指标"""
        try:
            current_metrics = {}

            for metric_type in MetricType:
                history = self.metrics_history[metric_type]
                if history:
                    latest_metric = history[-1]
                    current_metrics[metric_type.value] = {
                        "value": latest_metric.value,
                        "timestamp": latest_metric.timestamp.isoformat(),
                        "tags": latest_metric.tags,
                    }

            return {
                "metrics": current_metrics,
                "active_requests": len(self.active_requests),
                "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
                "total_requests_processed": len(self.request_history),
            }

        except Exception as e:
            self.logger.error(f"获取当前指标失败: {e}")
            return {}

    def get_statistics(self, window: str = "5m") -> dict[str, Any]:
        """获取统计信息"""
        try:
            if window not in self.stats_windows:
                window = "5m"

            cutoff_time = datetime.utcnow() - self.stats_windows[window]
            stats = {}

            for metric_type in MetricType:
                history = self.metrics_history[metric_type]
                recent_metrics = [m for m in history if m.timestamp >= cutoff_time]

                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    stats[metric_type.value] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    }

                    # 计算百分位数
                    if len(values) >= 2:
                        sorted_values = sorted(values)
                        stats[metric_type.value]["p95"] = sorted_values[
                            int(len(sorted_values) * 0.95)
                        ]
                        stats[metric_type.value]["p99"] = sorted_values[
                            int(len(sorted_values) * 0.99)
                        ]

            return {
                "window": window,
                "window_duration": self.stats_windows[window].total_seconds(),
                "statistics": stats,
            }

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}

    def generate_performance_report(
        self, start_time: datetime, end_time: datetime
    ) -> PerformanceReport:
        """生成性能报告"""
        try:
            # 过滤时间范围内的请求
            period_requests = [
                req
                for req in self.request_history
                if start_time.timestamp() <= req["end_time"] <= end_time.timestamp()
            ]

            if not period_requests:
                return PerformanceReport(
                    start_time=start_time,
                    end_time=end_time,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    average_response_time=0.0,
                    p95_response_time=0.0,
                    p99_response_time=0.0,
                    throughput=0.0,
                    error_rate=0.0,
                    alerts_count=0,
                    top_errors=[],
                )

            # 计算基础统计
            total_requests = len(period_requests)
            successful_requests = sum(1 for req in period_requests if req["success"])
            failed_requests = total_requests - successful_requests

            # 响应时间统计
            response_times = [req["response_time"] for req in period_requests]
            average_response_time = statistics.mean(response_times)

            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]

            # 吞吐量计算
            duration_seconds = (end_time - start_time).total_seconds()
            throughput = total_requests / duration_seconds if duration_seconds > 0 else 0

            # 错误率
            error_rate = failed_requests / total_requests if total_requests > 0 else 0

            # 告警统计
            period_alerts = [
                alert for alert in self.alert_history if start_time <= alert.timestamp <= end_time
            ]
            alerts_count = len(period_alerts)

            # 错误分析
            error_requests = [req for req in period_requests if not req["success"]]
            error_counts: defaultdict[str, int] = defaultdict(int)
            for req in error_requests:
                error_msg = req.get("error_message", "Unknown error")
                error_counts[error_msg] += 1

            top_errors = [
                {"error": error, "count": count}
                for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[
                    :5
                ]
            ]

            return PerformanceReport(
                start_time=start_time,
                end_time=end_time,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                average_response_time=average_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                throughput=throughput,
                error_rate=error_rate,
                alerts_count=alerts_count,
                top_errors=top_errors,
            )

        except Exception as e:
            self.logger.error(f"生成性能报告失败: {e}")
            return PerformanceReport(
                start_time=start_time,
                end_time=end_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                throughput=0.0,
                error_rate=0.0,
                alerts_count=0,
                top_errors=[],
            )

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], Awaitable[None]]) -> None:
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def get_active_alerts(self) -> list[PerformanceAlert]:
        """获取活跃告警"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]

    def get_alert_history(self, limit: int = 100) -> list[PerformanceAlert]:
        """获取告警历史"""
        return list(self.alert_history)[-limit:]


# 全局性能监控器实例
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()

    return _performance_monitor
