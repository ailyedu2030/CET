"""增强的性能监控引擎 - 全面的系统性能监控和智能告警."""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Any

# # 可选依赖处理
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False  # 可选依赖，如果未安装则使用模拟数据
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.utils.alert_utils import AlertManager
from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class EnhancedPerformanceMonitor:
    """增强的性能监控引擎."""

    def __init__(self, db: AsyncSession, cache_service: CacheService | None = None) -> None:
        self.db = db
        self.cache_service = cache_service
        self.alert_manager = AlertManager()

        # 性能基准配置
        self.performance_baselines = {
            "api_response_time": {
                "excellent": 100,  # ms
                "good": 300,
                "acceptable": 1000,
                "poor": 3000,
            },
            "database_query_time": {
                "excellent": 50,  # ms
                "good": 200,
                "acceptable": 500,
                "poor": 2000,
            },
            "memory_usage": {
                "excellent": 60,  # %
                "good": 75,
                "acceptable": 85,
                "poor": 95,
            },
            "cpu_usage": {
                "excellent": 50,  # %
                "good": 70,
                "acceptable": 85,
                "poor": 95,
            },
            "error_rate": {
                "excellent": 0.1,  # %
                "good": 0.5,
                "acceptable": 1.0,
                "poor": 5.0,
            },
        }

        # SLA配置
        self.sla_targets = {
            "availability": 99.9,  # %
            "response_time_p95": 500,  # ms
            "error_rate": 0.1,  # %
            "throughput": 1000,  # requests/minute
        }

        # 监控历史数据
        self.metrics_history: dict[str, list[dict[str, Any]]] = {}
        self.max_history_size = 1000

    async def comprehensive_performance_analysis(
        self, analysis_period_hours: int = 24
    ) -> dict[str, Any]:
        """执行综合性能分析."""
        try:
            # 1. 收集系统资源指标
            system_metrics = await self._collect_system_metrics()

            # 2. 收集应用性能指标
            application_metrics = await self._collect_application_metrics()

            # 3. 收集数据库性能指标
            database_metrics = await self._collect_database_metrics()

            # 4. 收集业务性能指标
            business_metrics = await self._collect_business_metrics(analysis_period_hours)

            # 5. 执行性能基准对比
            baseline_analysis = await self._analyze_performance_baselines(
                system_metrics, application_metrics, database_metrics
            )

            # 6. SLA合规性检查
            sla_compliance = await self._check_sla_compliance(
                system_metrics, application_metrics, analysis_period_hours
            )

            # 7. 性能趋势分析
            trend_analysis = await self._analyze_performance_trends(analysis_period_hours)

            # 8. 智能告警评估
            alert_assessment = await self._assess_intelligent_alerts(
                system_metrics, application_metrics, database_metrics
            )

            # 9. 性能优化建议
            optimization_recommendations = await self._generate_optimization_recommendations(
                baseline_analysis, sla_compliance, trend_analysis
            )

            return {
                "analysis_metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_period_hours": analysis_period_hours,
                    "data_quality_score": self._calculate_data_quality_score(),
                },
                "system_metrics": system_metrics,
                "application_metrics": application_metrics,
                "database_metrics": database_metrics,
                "business_metrics": business_metrics,
                "baseline_analysis": baseline_analysis,
                "sla_compliance": sla_compliance,
                "trend_analysis": trend_analysis,
                "alert_assessment": alert_assessment,
                "optimization_recommendations": optimization_recommendations,
                "overall_performance_score": self._calculate_overall_performance_score(
                    baseline_analysis, sla_compliance
                ),
            }

        except Exception as e:
            logger.error(f"综合性能分析失败: {str(e)}")
            raise

    async def _collect_system_metrics(self) -> dict[str, Any]:
        """收集系统资源指标."""
        try:
            if PSUTIL_AVAILABLE:
                # CPU指标
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()

                # 内存指标
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()

                # 磁盘指标
                disk_usage = psutil.disk_usage("/")
                disk_io = psutil.disk_io_counters()

                # 网络指标
                network_io = psutil.net_io_counters()

                # 进程指标
                process_count = len(psutil.pids())
            else:
                # 模拟数据（当psutil不可用时）
                import random

                cpu_percent = random.uniform(20, 80)
                cpu_count = 4
                cpu_freq = None

                # 模拟内存数据
                class MockMemory:
                    total = 8 * 1024**3  # 8GB
                    available = 4 * 1024**3  # 4GB
                    used = 4 * 1024**3  # 4GB
                    percent = 50.0

                class MockSwap:
                    total = 2 * 1024**3  # 2GB
                    used = 0.5 * 1024**3  # 0.5GB
                    percent = 25.0

                memory = MockMemory()
                swap = MockSwap()

                # 模拟磁盘数据
                class MockDisk:
                    total = 100 * 1024**3  # 100GB
                    used = 50 * 1024**3  # 50GB
                    free = 50 * 1024**3  # 50GB

                disk_usage = MockDisk()
                disk_io = None
                network_io = None
                process_count = 150

            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                    "load_average": (
                        psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0]
                    ),
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "usage_percent": memory.percent,
                    "swap_total_gb": swap.total / (1024**3),
                    "swap_used_gb": swap.used / (1024**3),
                    "swap_usage_percent": swap.percent,
                },
                "disk": {
                    "total_gb": disk_usage.total / (1024**3),
                    "used_gb": disk_usage.used / (1024**3),
                    "free_gb": disk_usage.free / (1024**3),
                    "usage_percent": (disk_usage.used / disk_usage.total) * 100,
                    "read_bytes_per_sec": disk_io.read_bytes if disk_io else 0,
                    "write_bytes_per_sec": disk_io.write_bytes if disk_io else 0,
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0,
                },
                "processes": {
                    "count": process_count,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _collect_application_metrics(self) -> dict[str, Any]:
        """收集应用性能指标."""
        try:
            # 从缓存获取应用指标
            app_metrics = {}

            if self.cache_service:
                # 获取API响应时间统计
                response_times = await self._get_cached_metrics("api_response_times")
                if response_times:
                    app_metrics["api_performance"] = {
                        "avg_response_time": statistics.mean(response_times),
                        "p95_response_time": (
                            statistics.quantiles(response_times, n=20)[18]
                            if len(response_times) > 20
                            else max(response_times)
                            if response_times
                            else 0
                        ),
                        "p99_response_time": (
                            statistics.quantiles(response_times, n=100)[98]
                            if len(response_times) > 100
                            else max(response_times)
                            if response_times
                            else 0
                        ),
                        "min_response_time": (min(response_times) if response_times else 0),
                        "max_response_time": (max(response_times) if response_times else 0),
                    }

                # 获取错误率统计
                error_counts = await self._get_cached_metrics("error_counts")
                request_counts = await self._get_cached_metrics("request_counts")

                if error_counts and request_counts:
                    total_errors = sum(error_counts)
                    total_requests = sum(request_counts)
                    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

                    app_metrics["reliability"] = {
                        "error_rate_percent": error_rate,
                        "total_requests": total_requests,
                        "total_errors": total_errors,
                        "success_rate_percent": 100 - error_rate,
                    }

                # 获取吞吐量统计
                throughput_data = await self._get_cached_metrics("throughput")
                if throughput_data:
                    app_metrics["throughput"] = {
                        "requests_per_minute": statistics.mean(throughput_data),
                        "peak_throughput": max(throughput_data),
                        "min_throughput": min(throughput_data),
                    }

            # 如果没有缓存数据，使用默认值
            if not app_metrics:
                app_metrics = {
                    "api_performance": {
                        "avg_response_time": 0,
                        "p95_response_time": 0,
                        "p99_response_time": 0,
                    },
                    "reliability": {
                        "error_rate_percent": 0,
                        "success_rate_percent": 100,
                    },
                    "throughput": {
                        "requests_per_minute": 0,
                    },
                }

            app_metrics["timestamp"] = datetime.now().isoformat()
            return app_metrics

        except Exception as e:
            logger.error(f"收集应用指标失败: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _collect_database_metrics(self) -> dict[str, Any]:
        """收集数据库性能指标."""
        try:
            # 数据库连接统计
            connection_query = text(
                """
                SELECT
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            )

            connection_result = await self.db.execute(connection_query)
            connection_stats = connection_result.fetchone()

            # 数据库大小统计
            size_query = text(
                """
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_database_size(current_database()) as database_size_bytes
            """
            )

            size_result = await self.db.execute(size_query)
            size_stats = size_result.fetchone()

            # 查询性能统计
            query_stats_query = text(
                """
                SELECT
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    min_exec_time
                FROM pg_stat_statements
                ORDER BY total_exec_time DESC
                LIMIT 1
            """
            )

            try:
                query_stats_result = await self.db.execute(query_stats_query)
                query_stats = query_stats_result.fetchone()
            except Exception:
                # pg_stat_statements可能未启用
                query_stats = None

            return {
                "connections": {
                    "total": connection_stats[0] if connection_stats else 0,
                    "active": connection_stats[1] if connection_stats else 0,
                    "idle": connection_stats[2] if connection_stats else 0,
                },
                "storage": {
                    "database_size_gb": size_stats[1] / (1024**3) if size_stats else 0,
                    "database_size_pretty": size_stats[0] if size_stats else "0 bytes",
                },
                "query_performance": (
                    {
                        "avg_query_time_ms": query_stats[2] if query_stats else 0,
                        "max_query_time_ms": query_stats[3] if query_stats else 0,
                        "min_query_time_ms": query_stats[4] if query_stats else 0,
                        "total_queries": query_stats[0] if query_stats else 0,
                    }
                    if query_stats
                    else {
                        "avg_query_time_ms": 0,
                        "max_query_time_ms": 0,
                        "min_query_time_ms": 0,
                        "total_queries": 0,
                    }
                ),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"收集数据库指标失败: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _collect_business_metrics(self, hours: int) -> dict[str, Any]:
        """收集业务性能指标."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)

            # 用户活跃度统计
            from app.users.models.user_models import User

            active_users_result = await self.db.execute(
                select(func.count(User.id)).where(User.last_login >= start_time, User.is_active)
            )
            active_users = active_users_result.scalar() or 0

            # 训练会话统计
            from app.training.models.training_models import TrainingSession

            training_sessions_result = await self.db.execute(
                select(func.count(TrainingSession.id)).where(
                    TrainingSession.created_at >= start_time
                )
            )
            training_sessions = training_sessions_result.scalar() or 0

            # 系统使用率统计
            total_users_result = await self.db.execute(
                select(func.count(User.id)).where(User.is_active)
            )
            total_users = total_users_result.scalar() or 1

            usage_rate = (active_users / total_users * 100) if total_users > 0 else 0

            return {
                "user_activity": {
                    "active_users": active_users,
                    "total_users": total_users,
                    "usage_rate_percent": usage_rate,
                },
                "training_activity": {
                    "training_sessions": training_sessions,
                    "sessions_per_hour": training_sessions / hours if hours > 0 else 0,
                },
                "system_utilization": {
                    "peak_concurrent_users": active_users,  # 简化实现
                    "avg_session_duration_minutes": 30,  # 简化实现
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"收集业务指标失败: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _analyze_performance_baselines(
        self,
        system_metrics: dict[str, Any],
        app_metrics: dict[str, Any],
        db_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """分析性能基准对比."""
        try:
            baseline_analysis = {}

            # API响应时间基准分析
            api_response_time = app_metrics.get("api_performance", {}).get("avg_response_time", 0)
            baseline_analysis["api_response_time"] = self._evaluate_against_baseline(
                "api_response_time", api_response_time
            )

            # 数据库查询时间基准分析
            db_query_time = db_metrics.get("query_performance", {}).get("avg_query_time_ms", 0)
            baseline_analysis["database_query_time"] = self._evaluate_against_baseline(
                "database_query_time", db_query_time
            )

            # 内存使用率基准分析
            memory_usage = system_metrics.get("memory", {}).get("usage_percent", 0)
            baseline_analysis["memory_usage"] = self._evaluate_against_baseline(
                "memory_usage", memory_usage
            )

            # CPU使用率基准分析
            cpu_usage = system_metrics.get("cpu", {}).get("usage_percent", 0)
            baseline_analysis["cpu_usage"] = self._evaluate_against_baseline("cpu_usage", cpu_usage)

            # 错误率基准分析
            error_rate = app_metrics.get("reliability", {}).get("error_rate_percent", 0)
            baseline_analysis["error_rate"] = self._evaluate_against_baseline(
                "error_rate", error_rate
            )

            # 计算整体基准评分
            baseline_scores = [analysis["score"] for analysis in baseline_analysis.values()]
            overall_baseline_score = statistics.mean(baseline_scores) if baseline_scores else 0

            return {
                "individual_baselines": baseline_analysis,
                "overall_baseline_score": overall_baseline_score,
                "baseline_grade": self._get_performance_grade(overall_baseline_score),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"性能基准分析失败: {str(e)}")
            return {"error": str(e)}

    def _evaluate_against_baseline(self, metric_name: str, current_value: float) -> dict[str, Any]:
        """评估指标与基准的对比."""
        baseline = self.performance_baselines.get(metric_name, {})
        if not baseline:
            return {"score": 0.5, "grade": "unknown", "status": "no_baseline"}

        # 确保baseline是字典类型
        if not isinstance(baseline, dict):
            baseline = {}

        # 对于错误率，值越低越好
        if metric_name == "error_rate":
            excellent = float(baseline.get("excellent", 0.01))
            good = float(baseline.get("good", 0.05))
            acceptable = float(baseline.get("acceptable", 0.1))

            if current_value <= excellent:
                score, grade = 1.0, "excellent"
            elif current_value <= good:
                score, grade = 0.8, "good"
            elif current_value <= acceptable:
                score, grade = 0.6, "acceptable"
            else:
                score, grade = 0.2, "poor"
        else:
            # 对于其他指标，值越低越好（响应时间、使用率等）
            excellent = float(baseline.get("excellent", 100))
            good = float(baseline.get("good", 200))
            acceptable = float(baseline.get("acceptable", 500))

            if current_value <= excellent:
                score, grade = 1.0, "excellent"
            elif current_value <= good:
                score, grade = 0.8, "good"
            elif current_value <= acceptable:
                score, grade = 0.6, "acceptable"
            else:
                score, grade = 0.2, "poor"

        return {
            "current_value": current_value,
            "baseline_thresholds": baseline,
            "score": score,
            "grade": grade,
            "status": "evaluated",
        }

    def _get_performance_grade(self, score: float) -> str:
        """根据评分获取性能等级."""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        else:
            return "D"

    async def _calculate_metric_trend(self, metric_name: str, hours: int) -> dict[str, Any]:
        """计算指标趋势."""
        try:
            # 从历史数据计算趋势（简化实现）
            if metric_name not in self.metrics_history:
                return {
                    "trend_direction": "unknown",
                    "trend_strength": 0,
                    "data_points": 0,
                    "message": "insufficient_data",
                }

            history = self.metrics_history[metric_name]
            if len(history) < 2:
                return {
                    "trend_direction": "stable",
                    "trend_strength": 0,
                    "data_points": len(history),
                    "message": "insufficient_data_for_trend",
                }

            # 简单的趋势计算
            recent_values = [point["value"] for point in history[-10:]]
            if len(recent_values) >= 2:
                trend_slope = (recent_values[-1] - recent_values[0]) / len(recent_values)

                if abs(trend_slope) < 0.1:
                    direction = "stable"
                elif trend_slope > 0:
                    direction = "increasing"
                else:
                    direction = "decreasing"

                # 对于某些指标，增加是好的，对于某些是坏的
                if metric_name in ["throughput"]:
                    trend_direction = (
                        "improving"
                        if direction == "increasing"
                        else "degrading"
                        if direction == "decreasing"
                        else "stable"
                    )
                else:
                    trend_direction = (
                        "degrading"
                        if direction == "increasing"
                        else "improving"
                        if direction == "decreasing"
                        else "stable"
                    )

                return {
                    "trend_direction": trend_direction,
                    "trend_strength": abs(trend_slope),
                    "data_points": len(recent_values),
                    "raw_direction": direction,
                }

            return {
                "trend_direction": "stable",
                "trend_strength": 0,
                "data_points": len(recent_values),
                "message": "calculated_as_stable",
            }

        except Exception as e:
            logger.error(f"计算指标趋势失败: {str(e)}")
            return {"error": str(e)}

    async def _get_cached_metrics(self, metric_type: str) -> list[float]:
        """从缓存获取指标数据."""
        try:
            if not self.cache_service:
                return []

            # 获取最近1小时的数据
            cache_key = f"performance_metrics:{metric_type}"
            cached_data = await self.cache_service.get(cache_key)

            if cached_data:
                import json

                data = json.loads(cached_data)
                values = data.get("values", [])
                return [float(v) for v in values if isinstance(v, int | float)]

            return []

        except Exception as e:
            logger.error(f"获取缓存指标失败: {str(e)}")
            return []

    def _calculate_data_quality_score(self) -> float:
        """计算数据质量评分."""
        # 简化实现
        return 0.85

    def _calculate_overall_performance_score(
        self, baseline_analysis: dict[str, Any], sla_compliance: dict[str, Any]
    ) -> float:
        """计算整体性能评分."""
        try:
            baseline_score = float(baseline_analysis.get("overall_baseline_score", 0))
            sla_score = float(sla_compliance.get("overall_compliance_percent", 0)) / 100

            # 加权平均
            overall_score = baseline_score * 0.6 + sla_score * 0.4
            return round(overall_score, 3)

        except Exception:
            return 0.5

    async def _check_sla_compliance(
        self, system_metrics: dict[str, Any], app_metrics: dict[str, Any], hours: int
    ) -> dict[str, Any]:
        """检查SLA合规性."""
        try:
            sla_compliance = {}

            # 可用性检查（简化实现）
            error_rate = app_metrics.get("reliability", {}).get("error_rate_percent", 0)
            availability = 100 - error_rate
            sla_compliance["availability"] = {
                "current": availability,
                "target": self.sla_targets["availability"],
                "compliant": availability >= self.sla_targets["availability"],
                "deviation": availability - self.sla_targets["availability"],
            }

            # 响应时间P95检查
            p95_response_time = app_metrics.get("api_performance", {}).get("p95_response_time", 0)
            sla_compliance["response_time_p95"] = {
                "current": p95_response_time,
                "target": self.sla_targets["response_time_p95"],
                "compliant": p95_response_time <= self.sla_targets["response_time_p95"],
                "deviation": p95_response_time - self.sla_targets["response_time_p95"],
            }

            # 错误率检查
            sla_compliance["error_rate"] = {
                "current": error_rate,
                "target": self.sla_targets["error_rate"],
                "compliant": error_rate <= self.sla_targets["error_rate"],
                "deviation": error_rate - self.sla_targets["error_rate"],
            }

            # 吞吐量检查
            throughput = app_metrics.get("throughput", {}).get("requests_per_minute", 0)
            sla_compliance["throughput"] = {
                "current": throughput,
                "target": self.sla_targets["throughput"],
                "compliant": throughput >= self.sla_targets["throughput"],
                "deviation": throughput - self.sla_targets["throughput"],
            }

            # 计算整体SLA合规性
            compliant_count = sum(1 for sla in sla_compliance.values() if sla["compliant"])
            overall_compliance = (compliant_count / len(sla_compliance)) * 100

            return {
                "individual_slas": sla_compliance,
                "overall_compliance_percent": overall_compliance,
                "compliant_slas": compliant_count,
                "total_slas": len(sla_compliance),
                "sla_grade": (
                    "A"
                    if overall_compliance >= 95
                    else (
                        "B"
                        if overall_compliance >= 85
                        else "C"
                        if overall_compliance >= 75
                        else "D"
                    )
                ),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"SLA合规性检查失败: {str(e)}")
            return {"error": str(e)}

    async def _analyze_performance_trends(self, hours: int) -> dict[str, Any]:
        """分析性能趋势."""
        try:
            # 获取历史性能数据
            trend_analysis = {
                "cpu_usage_trend": await self._calculate_metric_trend("cpu_usage", hours),
                "memory_usage_trend": await self._calculate_metric_trend("memory_usage", hours),
                "response_time_trend": await self._calculate_metric_trend("response_time", hours),
                "error_rate_trend": await self._calculate_metric_trend("error_rate", hours),
                "throughput_trend": await self._calculate_metric_trend("throughput", hours),
            }

            # 计算整体趋势
            trend_scores = []
            for _trend_name, trend_data in trend_analysis.items():
                if isinstance(trend_data, dict) and "trend_direction" in trend_data:
                    if trend_data["trend_direction"] == "improving":
                        trend_scores.append(1)
                    elif trend_data["trend_direction"] == "stable":
                        trend_scores.append(1)
                    else:
                        trend_scores.append(0)

            overall_trend_score = statistics.mean(trend_scores) if trend_scores else 0.5

            return {
                "individual_trends": trend_analysis,
                "overall_trend_score": overall_trend_score,
                "overall_trend_direction": (
                    "improving"
                    if overall_trend_score > 0.6
                    else "stable"
                    if overall_trend_score > 0.4
                    else "degrading"
                ),
                "analysis_period_hours": hours,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"性能趋势分析失败: {str(e)}")
            return {"error": str(e)}

    async def _assess_intelligent_alerts(
        self,
        system_metrics: dict[str, Any],
        app_metrics: dict[str, Any],
        db_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """评估智能告警."""
        try:
            alert_assessment: dict[str, Any] = {
                "active_alerts": [],
                "potential_issues": [],
                "recommendations": [],
            }

            # CPU使用率告警评估
            cpu_usage = float(system_metrics.get("cpu", {}).get("usage_percent", 0))
            if cpu_usage > 85:
                alert_assessment["active_alerts"].append(
                    {
                        "type": "high_cpu_usage",
                        "severity": "high" if cpu_usage > 95 else "medium",
                        "message": f"CPU使用率过高: {cpu_usage:.1f}%",
                        "current_value": cpu_usage,
                        "threshold": 85,
                    }
                )

            # 内存使用率告警评估
            memory_usage = system_metrics.get("memory", {}).get("usage_percent", 0)
            if memory_usage > 85:
                alert_assessment["active_alerts"].append(
                    {
                        "type": "high_memory_usage",
                        "severity": "high" if memory_usage > 95 else "medium",
                        "message": f"内存使用率过高: {memory_usage:.1f}%",
                        "current_value": memory_usage,
                        "threshold": 85,
                    }
                )

            # API响应时间告警评估
            response_time = app_metrics.get("api_performance", {}).get("avg_response_time", 0)
            if response_time > 1000:
                alert_assessment["active_alerts"].append(
                    {
                        "type": "slow_api_response",
                        "severity": "high" if response_time > 3000 else "medium",
                        "message": f"API响应时间过长: {response_time:.0f}ms",
                        "current_value": response_time,
                        "threshold": 1000,
                    }
                )

            # 错误率告警评估
            error_rate = app_metrics.get("reliability", {}).get("error_rate_percent", 0)
            if error_rate > 1.0:
                alert_assessment["active_alerts"].append(
                    {
                        "type": "high_error_rate",
                        "severity": "high" if error_rate > 5.0 else "medium",
                        "message": f"错误率过高: {error_rate:.1f}%",
                        "current_value": error_rate,
                        "threshold": 1.0,
                    }
                )

            # 数据库连接数告警评估
            db_connections = db_metrics.get("connections", {}).get("total", 0)
            if db_connections > 50:
                alert_assessment["potential_issues"].append(
                    {
                        "type": "high_db_connections",
                        "message": f"数据库连接数较高: {db_connections}",
                        "current_value": db_connections,
                        "recommendation": "考虑优化数据库连接池配置",
                    }
                )

            return {
                "alert_summary": {
                    "total_active_alerts": len(alert_assessment["active_alerts"]),
                    "high_severity_alerts": len(
                        [a for a in alert_assessment["active_alerts"] if a["severity"] == "high"]
                    ),
                    "medium_severity_alerts": len(
                        [a for a in alert_assessment["active_alerts"] if a["severity"] == "medium"]
                    ),
                    "potential_issues_count": len(alert_assessment["potential_issues"]),
                },
                "alerts": alert_assessment,
                "alert_status": (
                    "critical"
                    if any(a["severity"] == "high" for a in alert_assessment["active_alerts"])
                    else "warning"
                    if alert_assessment["active_alerts"]
                    else "healthy"
                ),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"智能告警评估失败: {str(e)}")
            return {"error": str(e)}

    async def _generate_optimization_recommendations(
        self,
        baseline_analysis: dict[str, Any],
        sla_compliance: dict[str, Any],
        trend_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """生成性能优化建议."""
        try:
            recommendations: dict[str, Any] = {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": [],
                "best_practices": [],
            }

            # 基于基准分析的建议
            individual_baselines = baseline_analysis.get("individual_baselines", {})

            for metric_name, analysis in individual_baselines.items():
                if analysis.get("grade") == "poor":
                    if metric_name == "api_response_time":
                        recommendations["high_priority"].append(
                            {
                                "category": "performance",
                                "title": "优化API响应时间",
                                "description": f"当前API响应时间 {analysis['current_value']:.0f}ms 超出可接受范围",
                                "actions": [
                                    "检查数据库查询性能",
                                    "优化API业务逻辑",
                                    "考虑添加缓存层",
                                    "检查网络延迟问题",
                                ],
                                "expected_impact": "high",
                            }
                        )
                    elif metric_name == "memory_usage":
                        recommendations["high_priority"].append(
                            {
                                "category": "resource",
                                "title": "优化内存使用",
                                "description": f"当前内存使用率 {analysis['current_value']:.1f}% 过高",
                                "actions": [
                                    "检查内存泄漏",
                                    "优化数据结构",
                                    "调整缓存策略",
                                    "考虑增加内存容量",
                                ],
                                "expected_impact": "high",
                            }
                        )
                elif analysis.get("grade") == "acceptable":
                    recommendations["medium_priority"].append(
                        {
                            "category": "optimization",
                            "title": f"改进{metric_name}性能",
                            "description": f"当前{metric_name}性能可接受但有优化空间",
                            "actions": ["定期监控", "制定优化计划"],
                            "expected_impact": "medium",
                        }
                    )

            # 基于SLA合规性的建议
            individual_slas = sla_compliance.get("individual_slas", {})
            for sla_name, sla_data in individual_slas.items():
                if not sla_data.get("compliant"):
                    recommendations["high_priority"].append(
                        {
                            "category": "sla",
                            "title": f"修复SLA违规: {sla_name}",
                            "description": f"当前值 {sla_data['current']} 未达到目标 {sla_data['target']}",
                            "actions": ["立即调查根本原因", "制定修复计划", "加强监控"],
                            "expected_impact": "critical",
                        }
                    )

            # 基于趋势分析的建议
            individual_trends = trend_analysis.get("individual_trends", {})
            for trend_name, trend_data in individual_trends.items():
                if trend_data.get("trend_direction") == "degrading":
                    recommendations["medium_priority"].append(
                        {
                            "category": "trend",
                            "title": f"关注{trend_name}下降趋势",
                            "description": f"{trend_name}呈现下降趋势，需要关注",
                            "actions": ["分析趋势原因", "制定预防措施"],
                            "expected_impact": "medium",
                        }
                    )

            # 最佳实践建议
            recommendations["best_practices"] = [
                {
                    "title": "定期性能审查",
                    "description": "建议每周进行性能审查，及时发现问题",
                },
                {
                    "title": "自动化监控",
                    "description": "设置自动化监控和告警，提高响应速度",
                },
                {
                    "title": "容量规划",
                    "description": "基于趋势分析进行容量规划，避免资源不足",
                },
            ]

            return {
                "recommendations": recommendations,
                "total_recommendations": sum(
                    len(recs) for recs in recommendations.values() if isinstance(recs, list)
                ),
                "priority_distribution": {
                    "high": len(recommendations["high_priority"]),
                    "medium": len(recommendations["medium_priority"]),
                    "low": len(recommendations["low_priority"]),
                },
                "generation_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"生成优化建议失败: {str(e)}")
            return {"error": str(e)}
