"""智能预警服务 - 🔥需求21第三阶段智能预警核心实现.

智能预警功能：
- 学习效果下降自动预警
- 异常学习模式识别
- 可配置预警阈值和规则
- 多级预警机制
- 预警历史记录和分析
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, TypedDict

import redis.asyncio as redis
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.training.models.training_models import TrainingRecord, TrainingSession

logger = logging.getLogger(__name__)


class AlertThresholds(TypedDict):
    """预警阈值配置类型."""

    accuracy_drop_warning: float
    accuracy_drop_critical: float
    speed_drop_warning: float
    speed_drop_critical: float
    consecutive_errors_warning: int
    consecutive_errors_critical: int
    engagement_drop_warning: float
    session_timeout_warning: int
    session_timeout_critical: int


class PatternDetection(TypedDict):
    """模式检测配置类型."""

    enable_pattern_analysis: bool
    analysis_window_minutes: int
    min_samples_for_analysis: int
    anomaly_threshold: float


class AlertRules(TypedDict):
    """预警规则配置类型."""

    enable_smart_filtering: bool
    duplicate_alert_interval: int
    escalation_time: int
    auto_recovery_check: bool
    max_alerts_per_session: int


class NotificationConfig(TypedDict):
    """通知配置类型."""

    immediate_push: list[str]
    batch_push: list[str]
    push_interval: int
    enable_email_alerts: bool


class AlertConfig(TypedDict):
    """智能预警配置类型."""

    thresholds: AlertThresholds
    pattern_detection: PatternDetection
    alert_rules: AlertRules
    notification: NotificationConfig


class IntelligentAlertService:
    """智能预警服务 - 学习效果下降和异常模式自动预警."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.redis_client: redis.Redis | None = None

        # 智能预警配置
        self.alert_config: AlertConfig = {
            # 基础预警阈值
            "thresholds": {
                "accuracy_drop_warning": 0.15,  # 正确率下降15%预警
                "accuracy_drop_critical": 0.25,  # 正确率下降25%严重预警
                "speed_drop_warning": 0.20,  # 答题速度下降20%预警
                "speed_drop_critical": 0.35,  # 答题速度下降35%严重预警
                "consecutive_errors_warning": 3,  # 连续3次错误预警
                "consecutive_errors_critical": 5,  # 连续5次错误严重预警
                "engagement_drop_warning": 0.3,  # 参与度下降30%预警
                "session_timeout_warning": 600,  # 10分钟无活动预警
                "session_timeout_critical": 1800,  # 30分钟无活动严重预警
            },
            # 异常模式检测
            "pattern_detection": {
                "enable_pattern_analysis": True,
                "analysis_window_minutes": 30,  # 30分钟分析窗口
                "min_samples_for_analysis": 10,  # 最少10个样本才分析
                "anomaly_threshold": 2.0,  # 异常阈值（标准差倍数）
            },
            # 预警规则
            "alert_rules": {
                "enable_smart_filtering": True,  # 启用智能过滤
                "duplicate_alert_interval": 300,  # 5分钟内不重复相同预警
                "escalation_time": 900,  # 15分钟后升级预警级别
                "auto_recovery_check": True,  # 自动恢复检查
                "max_alerts_per_session": 10,  # 每会话最多10个预警
            },
            # 通知配置
            "notification": {
                "immediate_push": ["critical"],  # 立即推送的预警级别
                "batch_push": ["warning", "info"],  # 批量推送的预警级别
                "push_interval": 30,  # 批量推送间隔（秒）
                "enable_email_alerts": False,  # 邮件预警（暂未实现）
            },
        }

    async def initialize_redis(self) -> None:
        """初始化Redis连接."""
        try:
            self.redis_client = redis.from_url(  # type: ignore[no-untyped-call]
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                encoding="utf-8",
                decode_responses=True,
            )
            if self.redis_client:
                await self.redis_client.ping()
            logger.info("智能预警Redis连接初始化成功")
        except Exception as e:
            logger.error(f"智能预警Redis连接初始化失败: {str(e)}")
            self.redis_client = None

    async def analyze_and_generate_alerts(
        self, student_id: int, session_id: int, current_metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """分析并生成智能预警."""
        try:
            logger.debug(f"开始智能预警分析: 学生{student_id}, 会话{session_id}")

            alerts = []

            # 1. 基础阈值预警
            threshold_alerts = await self._check_threshold_alerts(
                student_id, session_id, current_metrics
            )
            alerts.extend(threshold_alerts)

            # 2. 异常模式检测
            if self.alert_config["pattern_detection"]["enable_pattern_analysis"]:
                pattern_alerts = await self._detect_anomaly_patterns(
                    student_id, session_id, current_metrics
                )
                alerts.extend(pattern_alerts)

            # 3. 学习效果趋势分析
            trend_alerts = await self._analyze_learning_trends(
                student_id, session_id, current_metrics
            )
            alerts.extend(trend_alerts)

            # 4. 智能过滤和去重
            if self.alert_config["alert_rules"]["enable_smart_filtering"]:
                alerts = await self._filter_and_deduplicate_alerts(
                    student_id, session_id, alerts
                )

            # 5. 记录预警历史
            if alerts:
                await self._record_alert_history(student_id, session_id, alerts)

            logger.info(f"智能预警分析完成: 学生{student_id}, 生成{len(alerts)}个预警")
            return alerts

        except Exception as e:
            logger.error(f"智能预警分析失败: {str(e)}")
            return []

    async def _check_threshold_alerts(
        self, student_id: int, session_id: int, metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """检查基础阈值预警."""
        alerts = []
        thresholds = self.alert_config["thresholds"]

        try:
            # 获取历史基线数据
            baseline = await self._get_performance_baseline(student_id)

            # 检查正确率下降
            accuracy_metrics = metrics.get("accuracy_metrics", {})
            current_accuracy = accuracy_metrics.get("current_accuracy", 0)
            baseline_accuracy = baseline.get("avg_accuracy", 0.7)

            accuracy_drop = baseline_accuracy - current_accuracy

            if accuracy_drop >= thresholds["accuracy_drop_critical"]:
                alerts.append(
                    {
                        "type": "accuracy_drop",
                        "severity": "critical",
                        "message": f"正确率严重下降{accuracy_drop:.1%}",
                        "current_value": current_accuracy,
                        "baseline_value": baseline_accuracy,
                        "threshold": thresholds["accuracy_drop_critical"],
                        "recommendation": "建议降低难度或提供额外指导",
                    }
                )
            elif accuracy_drop >= thresholds["accuracy_drop_warning"]:
                alerts.append(
                    {
                        "type": "accuracy_drop",
                        "severity": "warning",
                        "message": f"正确率下降{accuracy_drop:.1%}",
                        "current_value": current_accuracy,
                        "baseline_value": baseline_accuracy,
                        "threshold": thresholds["accuracy_drop_warning"],
                        "recommendation": "建议关注学习状态",
                    }
                )

            # 检查连续错误
            consecutive_errors = accuracy_metrics.get("consecutive_errors", 0)

            if consecutive_errors >= thresholds["consecutive_errors_critical"]:
                alerts.append(
                    {
                        "type": "consecutive_errors",
                        "severity": "critical",
                        "message": f"连续{consecutive_errors}次答错",
                        "current_value": consecutive_errors,
                        "threshold": thresholds["consecutive_errors_critical"],
                        "recommendation": "建议暂停训练，检查学习方法",
                    }
                )
            elif consecutive_errors >= thresholds["consecutive_errors_warning"]:
                alerts.append(
                    {
                        "type": "consecutive_errors",
                        "severity": "warning",
                        "message": f"连续{consecutive_errors}次答错",
                        "current_value": consecutive_errors,
                        "threshold": thresholds["consecutive_errors_warning"],
                        "recommendation": "建议调整学习策略",
                    }
                )

            # 检查答题速度下降
            speed_metrics = metrics.get("answer_speed", {})
            current_speed = speed_metrics.get("average_time", 0)
            baseline_speed = baseline.get("avg_answer_time", 60)

            if current_speed > 0 and baseline_speed > 0:
                speed_increase = (current_speed - baseline_speed) / baseline_speed

                if speed_increase >= thresholds["speed_drop_critical"]:
                    alerts.append(
                        {
                            "type": "speed_decline",
                            "severity": "critical",
                            "message": f"答题速度严重下降{speed_increase:.1%}",
                            "current_value": current_speed,
                            "baseline_value": baseline_speed,
                            "threshold": thresholds["speed_drop_critical"],
                            "recommendation": "建议检查理解程度或降低难度",
                        }
                    )
                elif speed_increase >= thresholds["speed_drop_warning"]:
                    alerts.append(
                        {
                            "type": "speed_decline",
                            "severity": "warning",
                            "message": f"答题速度下降{speed_increase:.1%}",
                            "current_value": current_speed,
                            "baseline_value": baseline_speed,
                            "threshold": thresholds["speed_drop_warning"],
                            "recommendation": "建议关注答题效率",
                        }
                    )

            # 检查参与度下降
            engagement_metrics = metrics.get("engagement_metrics", {})
            engagement_level = engagement_metrics.get("engagement_level", "medium")
            activity_score = engagement_metrics.get("activity_score", 0.5)

            if (
                engagement_level == "low"
                or activity_score < thresholds["engagement_drop_warning"]
            ):
                alerts.append(
                    {
                        "type": "low_engagement",
                        "severity": "warning",
                        "message": "学习参与度较低",
                        "current_value": activity_score,
                        "threshold": thresholds["engagement_drop_warning"],
                        "recommendation": "建议调整学习内容或休息",
                    }
                )

            # 检查会话超时
            last_activity = engagement_metrics.get("time_since_last_activity", 0)

            if last_activity >= thresholds["session_timeout_critical"]:
                alerts.append(
                    {
                        "type": "session_timeout",
                        "severity": "critical",
                        "message": f"已{last_activity // 60}分钟无活动",
                        "current_value": last_activity,
                        "threshold": thresholds["session_timeout_critical"],
                        "recommendation": "建议结束当前会话",
                    }
                )
            elif last_activity >= thresholds["session_timeout_warning"]:
                alerts.append(
                    {
                        "type": "session_timeout",
                        "severity": "warning",
                        "message": f"已{last_activity // 60}分钟无活动",
                        "current_value": last_activity,
                        "threshold": thresholds["session_timeout_warning"],
                        "recommendation": "建议检查学习状态",
                    }
                )

            return alerts

        except Exception as e:
            logger.error(f"基础阈值预警检查失败: {str(e)}")
            return []

    async def _detect_anomaly_patterns(
        self, student_id: int, session_id: int, current_metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """检测异常学习模式."""
        alerts: list[dict[str, Any]] = []

        try:
            # 获取分析窗口内的历史数据
            window_minutes = self.alert_config["pattern_detection"][
                "analysis_window_minutes"
            ]
            min_samples = self.alert_config["pattern_detection"][
                "min_samples_for_analysis"
            ]

            historical_data = await self._get_historical_metrics(
                student_id, session_id, window_minutes
            )

            if len(historical_data) < min_samples:
                return alerts

            # 分析答题时间异常
            time_anomaly = await self._detect_time_anomaly(
                historical_data, current_metrics
            )
            if time_anomaly:
                alerts.append(time_anomaly)

            # 分析正确率波动异常
            accuracy_anomaly = await self._detect_accuracy_anomaly(
                historical_data, current_metrics
            )
            if accuracy_anomaly:
                alerts.append(accuracy_anomaly)

            # 分析学习节奏异常
            rhythm_anomaly = await self._detect_rhythm_anomaly(
                historical_data, current_metrics
            )
            if rhythm_anomaly:
                alerts.append(rhythm_anomaly)

            return alerts

        except Exception as e:
            logger.error(f"异常模式检测失败: {str(e)}")
            return []

    async def _analyze_learning_trends(
        self, student_id: int, session_id: int, current_metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """分析学习效果趋势."""
        alerts: list[dict[str, Any]] = []

        try:
            # 获取最近的学习趋势数据
            trend_data = await self._get_learning_trend_data(student_id, session_id)

            if not trend_data:
                return alerts

            # 分析正确率趋势
            accuracy_trend = trend_data.get("accuracy_trend", "stable")
            if accuracy_trend == "declining":
                alerts.append(
                    {
                        "type": "learning_trend",
                        "severity": "warning",
                        "message": "学习效果呈下降趋势",
                        "trend": accuracy_trend,
                        "recommendation": "建议调整学习策略或寻求帮助",
                    }
                )

            # 分析学习效率趋势
            efficiency_trend = trend_data.get("efficiency_trend", "stable")
            if efficiency_trend == "declining":
                alerts.append(
                    {
                        "type": "efficiency_trend",
                        "severity": "info",
                        "message": "学习效率呈下降趋势",
                        "trend": efficiency_trend,
                        "recommendation": "建议适当休息或调整学习环境",
                    }
                )

            # 分析难度适应性
            difficulty_adaptation = current_metrics.get("difficulty_adaptation", {})
            adaptation_status = difficulty_adaptation.get(
                "adaptation_status", "appropriate"
            )

            if adaptation_status == "too_hard":
                alerts.append(
                    {
                        "type": "difficulty_mismatch",
                        "severity": "warning",
                        "message": "当前难度可能过高",
                        "adaptation_status": adaptation_status,
                        "recommendation": "建议降低难度等级",
                    }
                )
            elif adaptation_status == "too_easy":
                alerts.append(
                    {
                        "type": "difficulty_mismatch",
                        "severity": "info",
                        "message": "当前难度可能过低",
                        "adaptation_status": adaptation_status,
                        "recommendation": "建议提高难度等级",
                    }
                )

            return alerts

        except Exception as e:
            logger.error(f"学习趋势分析失败: {str(e)}")
            return []

    async def _filter_and_deduplicate_alerts(
        self, student_id: int, session_id: int, alerts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """智能过滤和去重预警."""
        if not alerts:
            return alerts

        try:
            filtered_alerts = []
            duplicate_interval = self.alert_config["alert_rules"][
                "duplicate_alert_interval"
            ]
            max_alerts = self.alert_config["alert_rules"]["max_alerts_per_session"]

            # 获取最近的预警历史
            recent_alerts = await self._get_recent_alerts(
                student_id, session_id, duplicate_interval
            )
            recent_alert_types = {alert.get("type") for alert in recent_alerts}

            for alert in alerts:
                alert_type = alert.get("type")

                # 检查是否重复
                if alert_type not in recent_alert_types:
                    # 添加时间戳和ID
                    alert.update(
                        {
                            "alert_id": f"{student_id}_{session_id}_{alert_type}_{int(datetime.now().timestamp())}",
                            "timestamp": datetime.now(),
                            "student_id": student_id,
                            "session_id": session_id,
                        }
                    )
                    filtered_alerts.append(alert)

            # 限制预警数量
            if len(filtered_alerts) > max_alerts:
                # 按严重程度排序，保留最重要的预警
                severity_order = {"critical": 0, "warning": 1, "info": 2}
                filtered_alerts.sort(
                    key=lambda x: severity_order.get(x.get("severity", "info"), 3)
                )
                filtered_alerts = filtered_alerts[:max_alerts]

            return filtered_alerts

        except Exception as e:
            logger.error(f"预警过滤失败: {str(e)}")
            return alerts

    async def _record_alert_history(
        self, student_id: int, session_id: int, alerts: list[dict[str, Any]]
    ) -> None:
        """记录预警历史."""
        if not self.redis_client or not alerts:
            return

        try:
            for alert in alerts:
                # 记录到Redis
                alert_key = f"alert_history:{student_id}:{session_id}"
                timestamp = int(datetime.now().timestamp())

                await self.redis_client.zadd(
                    alert_key, {json.dumps(alert, default=str): timestamp}
                )

                # 设置过期时间（7天）
                await self.redis_client.expire(alert_key, 86400 * 7)

                # 记录全局预警统计
                stats_key = f"alert_stats:{student_id}"
                await self.redis_client.hincrby(stats_key, f"total_{alert['type']}", 1)
                await self.redis_client.hincrby(
                    stats_key, f"severity_{alert['severity']}", 1
                )
                await self.redis_client.expire(stats_key, 86400 * 30)

        except Exception as e:
            logger.error(f"记录预警历史失败: {str(e)}")

    async def _get_performance_baseline(self, student_id: int) -> dict[str, Any]:
        """获取性能基线数据."""
        if not self.redis_client:
            return await self._calculate_baseline_from_db(student_id)

        try:
            baseline_key = f"baseline:{student_id}"
            baseline_data = await self.redis_client.hgetall(baseline_key)

            if baseline_data:
                return {
                    k: (
                        json.loads(v)
                        if v.startswith("{") or v.startswith("[")
                        else float(v)
                        if "." in v
                        else v
                    )
                    for k, v in baseline_data.items()
                }
            else:
                return await self._calculate_baseline_from_db(student_id)

        except Exception as e:
            logger.error(f"获取性能基线失败: {str(e)}")
            return await self._calculate_baseline_from_db(student_id)

    async def _calculate_baseline_from_db(self, student_id: int) -> dict[str, Any]:
        """从数据库计算基线数据."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)

            stmt = (
                select(TrainingRecord)
                .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
                .where(
                    and_(
                        TrainingSession.student_id == student_id,
                        TrainingRecord.created_at >= cutoff_date,
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
                .limit(100)
            )

            result = await self.db.execute(stmt)
            records = result.scalars().all()

            if not records:
                return {"avg_accuracy": 0.7, "avg_answer_time": 60.0}

            # 计算基线指标
            correct_count = sum(1 for r in records if r.is_correct)
            avg_accuracy = correct_count / len(records)

            times = [r.time_spent for r in records if r.time_spent]
            avg_answer_time = sum(times) / len(times) if times else 60.0

            return {
                "avg_accuracy": avg_accuracy,
                "avg_answer_time": avg_answer_time,
                "sample_size": len(records),
            }

        except Exception as e:
            logger.error(f"计算基线数据失败: {str(e)}")
            return {"avg_accuracy": 0.7, "avg_answer_time": 60.0}

    async def _get_historical_metrics(
        self, student_id: int, session_id: int, window_minutes: int
    ) -> list[dict[str, Any]]:
        """获取历史指标数据."""
        if not self.redis_client:
            return []

        try:
            timeseries_key = f"metrics:timeseries:{student_id}:{session_id}"
            cutoff_timestamp = int(
                (datetime.now() - timedelta(minutes=window_minutes)).timestamp()
            )

            # 获取时间窗口内的数据
            data = await self.redis_client.zrangebyscore(
                timeseries_key, cutoff_timestamp, "+inf", withscores=True
            )

            metrics_list = []
            for item, timestamp in data:
                try:
                    metrics = json.loads(item)
                    metrics["timestamp"] = timestamp
                    metrics_list.append(metrics)
                except json.JSONDecodeError:
                    continue

            return metrics_list

        except Exception as e:
            logger.error(f"获取历史指标失败: {str(e)}")
            return []

    async def _detect_time_anomaly(
        self, historical_data: list[dict[str, Any]], current_metrics: dict[str, Any]
    ) -> dict[str, Any] | None:
        """检测答题时间异常."""
        try:
            # 提取历史答题时间
            historical_times = []
            for data in historical_data:
                speed_metrics = data.get("answer_speed", {})
                avg_time = speed_metrics.get("average_time", 0)
                if avg_time > 0:
                    historical_times.append(avg_time)

            if len(historical_times) < 5:
                return None

            # 计算统计指标
            import statistics

            mean_time = statistics.mean(historical_times)
            stdev_time = (
                statistics.stdev(historical_times) if len(historical_times) > 1 else 0
            )

            # 获取当前答题时间
            current_speed = current_metrics.get("answer_speed", {})
            current_time = current_speed.get("average_time", 0)

            if current_time <= 0 or stdev_time <= 0:
                return None

            # 计算Z分数
            z_score = abs(current_time - mean_time) / stdev_time
            anomaly_threshold = self.alert_config["pattern_detection"][
                "anomaly_threshold"
            ]

            if z_score > anomaly_threshold:
                return {
                    "type": "time_anomaly",
                    "severity": "warning",
                    "message": f"答题时间异常（Z分数: {z_score:.2f}）",
                    "current_value": current_time,
                    "mean_value": mean_time,
                    "z_score": z_score,
                    "recommendation": "建议检查学习状态或网络连接",
                }

            return None

        except Exception as e:
            logger.error(f"时间异常检测失败: {str(e)}")
            return None

    async def _detect_accuracy_anomaly(
        self, historical_data: list[dict[str, Any]], current_metrics: dict[str, Any]
    ) -> dict[str, Any] | None:
        """检测正确率波动异常."""
        try:
            # 提取历史正确率
            historical_accuracies = []
            for data in historical_data:
                accuracy_metrics = data.get("accuracy_metrics", {})
                accuracy = accuracy_metrics.get("current_accuracy", 0)
                if accuracy > 0:
                    historical_accuracies.append(accuracy)

            if len(historical_accuracies) < 5:
                return None

            # 计算变异系数
            import statistics

            mean_accuracy = statistics.mean(historical_accuracies)
            stdev_accuracy = (
                statistics.stdev(historical_accuracies)
                if len(historical_accuracies) > 1
                else 0
            )

            if mean_accuracy <= 0:
                return None

            coefficient_of_variation = stdev_accuracy / mean_accuracy

            # 如果变异系数过大，说明正确率波动异常
            if coefficient_of_variation > 0.3:  # 30%的变异系数阈值
                return {
                    "type": "accuracy_volatility",
                    "severity": "info",
                    "message": f"正确率波动较大（变异系数: {coefficient_of_variation:.2f}）",
                    "mean_accuracy": mean_accuracy,
                    "coefficient_of_variation": coefficient_of_variation,
                    "recommendation": "建议保持稳定的学习节奏",
                }

            return None

        except Exception as e:
            logger.error(f"正确率异常检测失败: {str(e)}")
            return None

    async def _detect_rhythm_anomaly(
        self, historical_data: list[dict[str, Any]], current_metrics: dict[str, Any]
    ) -> dict[str, Any] | None:
        """检测学习节奏异常."""
        try:
            # 分析答题间隔
            timestamps = [data.get("timestamp", 0) for data in historical_data]
            timestamps.sort()

            if len(timestamps) < 3:
                return None

            # 计算答题间隔
            intervals = []
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i - 1]
                intervals.append(interval)

            if not intervals:
                return None

            # 检查是否有异常长的间隔
            import statistics

            mean_interval = statistics.mean(intervals)
            max_interval = max(intervals)

            # 如果最大间隔超过平均间隔的3倍，认为是节奏异常
            if max_interval > mean_interval * 3 and max_interval > 300:  # 5分钟
                return {
                    "type": "rhythm_anomaly",
                    "severity": "info",
                    "message": f"学习节奏不规律（最大间隔: {max_interval // 60}分钟）",
                    "max_interval": max_interval,
                    "mean_interval": mean_interval,
                    "recommendation": "建议保持规律的学习节奏",
                }

            return None

        except Exception as e:
            logger.error(f"学习节奏异常检测失败: {str(e)}")
            return None

    async def _get_learning_trend_data(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """获取学习趋势数据."""
        try:
            # 获取最近的训练记录
            cutoff_date = datetime.now() - timedelta(hours=2)

            stmt = (
                select(TrainingRecord)
                .where(
                    and_(
                        TrainingRecord.session_id == session_id,
                        TrainingRecord.created_at >= cutoff_date,
                    )
                )
                .order_by(TrainingRecord.created_at)
            )

            result = await self.db.execute(stmt)
            records = result.scalars().all()

            if len(records) < 10:
                return {}

            # 分析正确率趋势
            mid_point = len(records) // 2
            early_records = records[:mid_point]
            recent_records = records[mid_point:]

            early_accuracy = sum(1 for r in early_records if r.is_correct) / len(
                early_records
            )
            recent_accuracy = sum(1 for r in recent_records if r.is_correct) / len(
                recent_records
            )

            if recent_accuracy < early_accuracy - 0.1:
                accuracy_trend = "declining"
            elif recent_accuracy > early_accuracy + 0.1:
                accuracy_trend = "improving"
            else:
                accuracy_trend = "stable"

            # 分析效率趋势
            early_times = [r.time_spent for r in early_records if r.time_spent]
            recent_times = [r.time_spent for r in recent_records if r.time_spent]

            if early_times and recent_times:
                early_avg_time = sum(early_times) / len(early_times)
                recent_avg_time = sum(recent_times) / len(recent_times)

                if recent_avg_time > early_avg_time * 1.2:
                    efficiency_trend = "declining"
                elif recent_avg_time < early_avg_time * 0.8:
                    efficiency_trend = "improving"
                else:
                    efficiency_trend = "stable"
            else:
                efficiency_trend = "unknown"

            return {
                "accuracy_trend": accuracy_trend,
                "efficiency_trend": efficiency_trend,
                "early_accuracy": early_accuracy,
                "recent_accuracy": recent_accuracy,
                "sample_size": len(records),
            }

        except Exception as e:
            logger.error(f"获取学习趋势数据失败: {str(e)}")
            return {}

    async def _get_recent_alerts(
        self, student_id: int, session_id: int, interval_seconds: int
    ) -> list[dict[str, Any]]:
        """获取最近的预警记录."""
        if not self.redis_client:
            return []

        try:
            alert_key = f"alert_history:{student_id}:{session_id}"
            cutoff_timestamp = int(
                (datetime.now() - timedelta(seconds=interval_seconds)).timestamp()
            )

            data = await self.redis_client.zrangebyscore(
                alert_key, cutoff_timestamp, "+inf"
            )

            alerts = []
            for item in data:
                try:
                    alert = json.loads(item)
                    alerts.append(alert)
                except json.JSONDecodeError:
                    continue

            return alerts

        except Exception as e:
            logger.error(f"获取最近预警失败: {str(e)}")
            return []

    async def get_alert_statistics(self, student_id: int) -> dict[str, Any]:
        """获取预警统计信息."""
        if not self.redis_client:
            return {}

        try:
            stats_key = f"alert_stats:{student_id}"
            stats = await self.redis_client.hgetall(stats_key)

            return {
                "student_id": student_id,
                "statistics": stats,
                "total_alerts": sum(
                    int(v) for k, v in stats.items() if k.startswith("total_")
                ),
                "critical_alerts": int(stats.get("severity_critical", 0)),
                "warning_alerts": int(stats.get("severity_warning", 0)),
                "info_alerts": int(stats.get("severity_info", 0)),
            }

        except Exception as e:
            logger.error(f"获取预警统计失败: {str(e)}")
            return {}

    def update_alert_config(self, config_updates: dict[str, Any]) -> dict[str, Any]:
        """更新预警配置."""
        try:
            # 深度更新配置
            def deep_update(
                base_dict: dict[str, Any], update_dict: dict[str, Any]
            ) -> None:
                for key, value in update_dict.items():
                    if (
                        key in base_dict
                        and isinstance(base_dict[key], dict)
                        and isinstance(value, dict)
                    ):
                        deep_update(base_dict[key], value)
                    else:
                        base_dict[key] = value

            # 将AlertConfig转换为普通字典进行更新
            config_dict = dict(self.alert_config)
            deep_update(config_dict, config_updates)
            # 更新回AlertConfig（这里假设更新后的结构仍然符合AlertConfig）
            self.alert_config.update(config_dict)  # type: ignore[typeddict-item]

            logger.info(f"预警配置已更新: {config_updates}")
            return dict(self.alert_config)

        except Exception as e:
            logger.error(f"更新预警配置失败: {str(e)}")
            return dict(self.alert_config)
