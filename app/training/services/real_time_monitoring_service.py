"""实时性能监控服务 - 🔥需求21第三阶段核心实现.

实时数据采集功能：
- 答题速度实时监控
- 正确率实时计算
- 学习进度实时跟踪
- 关键指标实时采集
- 性能数据实时缓存
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, TypedDict

import redis.asyncio as redis
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.shared.models.enums import DifficultyLevel
from app.training.models.training_models import (
    TrainingRecord,
    TrainingSession,
)

logger = logging.getLogger(__name__)


class AlertThresholds(TypedDict):
    """预警阈值配置类型."""

    accuracy_drop: float
    speed_drop: float
    consecutive_errors: int
    session_timeout: int


class MetricsRetention(TypedDict):
    """指标保留配置类型."""

    real_time: int
    hourly: int
    daily: int


class MonitoringConfig(TypedDict):
    """实时监控配置类型."""

    data_collection_interval: int
    cache_ttl: int
    performance_window: int
    alert_thresholds: AlertThresholds
    metrics_retention: MetricsRetention


class RealTimeMonitoringService:
    """实时性能监控服务 - 训练过程实时数据采集和监控."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.redis_client: redis.Redis | None = None

        # 实时监控配置
        self.monitoring_config: MonitoringConfig = {
            "data_collection_interval": 1,  # 1秒采集间隔
            "cache_ttl": 300,  # 5分钟缓存TTL
            "performance_window": 60,  # 60秒性能窗口
            "alert_thresholds": {
                "accuracy_drop": 0.2,  # 正确率下降20%触发预警
                "speed_drop": 0.3,  # 答题速度下降30%触发预警
                "consecutive_errors": 5,  # 连续5次错误触发预警
                "session_timeout": 1800,  # 30分钟无活动超时
            },
            "metrics_retention": {
                "real_time": 3600,  # 实时数据保留1小时
                "hourly": 86400 * 7,  # 小时数据保留7天
                "daily": 86400 * 30,  # 日数据保留30天
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
            logger.info("Redis连接初始化成功")
        except Exception as e:
            logger.error(f"Redis连接初始化失败: {str(e)}")
            self.redis_client = None

    async def start_real_time_monitoring(self, student_id: int, session_id: int) -> dict[str, Any]:
        """开始实时监控训练会话."""
        try:
            logger.info(f"开始实时监控: 学生{student_id}, 会话{session_id}")

            # 初始化监控会话
            monitoring_session = await self._initialize_monitoring_session(student_id, session_id)

            # 启动数据采集任务
            await self._start_data_collection_task(student_id, session_id)

            # 初始化性能基线
            baseline_metrics = await self._establish_performance_baseline(student_id, session_id)

            return {
                "monitoring_started": True,
                "session_id": session_id,
                "student_id": student_id,
                "monitoring_session": monitoring_session,
                "baseline_metrics": baseline_metrics,
                "collection_interval": self.monitoring_config["data_collection_interval"],
                "start_time": datetime.now(),
            }

        except Exception as e:
            logger.error(f"启动实时监控失败: {str(e)}")
            raise RuntimeError(f"启动实时监控失败: {str(e)}") from e

    async def collect_real_time_metrics(self, student_id: int, session_id: int) -> dict[str, Any]:
        """采集实时性能指标."""
        try:
            current_time = datetime.now()

            # 获取当前会话信息
            session_info = await self._get_session_info(session_id)
            if not session_info:
                return {"error": "会话不存在"}

            # 采集核心指标
            metrics = {
                "timestamp": current_time,
                "session_id": session_id,
                "student_id": student_id,
                # 答题速度指标
                "answer_speed": await self._calculate_real_time_answer_speed(
                    student_id, session_id
                ),
                # 正确率指标
                "accuracy_metrics": await self._calculate_real_time_accuracy(
                    student_id, session_id
                ),
                # 学习进度指标
                "progress_metrics": await self._calculate_learning_progress(student_id, session_id),
                # 参与度指标
                "engagement_metrics": await self._calculate_engagement_metrics(
                    student_id, session_id
                ),
                # 难度适应性指标
                "difficulty_adaptation": await self._calculate_difficulty_adaptation(
                    student_id, session_id
                ),
            }

            # 缓存实时数据
            await self._cache_real_time_metrics(student_id, session_id, metrics)

            # 检查预警条件
            alerts = await self._check_alert_conditions(student_id, session_id, metrics)
            if alerts:
                metrics["alerts"] = alerts

            logger.debug(f"实时指标采集完成: 学生{student_id}, 会话{session_id}")
            return metrics

        except Exception as e:
            logger.error(f"实时指标采集失败: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now()}

    async def _initialize_monitoring_session(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """初始化监控会话."""
        session_key = f"monitoring:session:{student_id}:{session_id}"

        session_data = {
            "student_id": student_id,
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "status": "active",
            "metrics_collected": 0,
            "alerts_triggered": 0,
        }

        if self.redis_client:
            await self.redis_client.hset(session_key, mapping=session_data)
            await self.redis_client.expire(session_key, self.monitoring_config["cache_ttl"])

        return session_data

    async def _start_data_collection_task(self, student_id: int, session_id: int) -> None:
        """启动数据采集任务."""
        # 这里可以启动后台任务进行定期数据采集
        # 暂时记录启动信息
        logger.info(f"数据采集任务已启动: 学生{student_id}, 会话{session_id}")

    async def _establish_performance_baseline(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """建立性能基线."""
        try:
            # 获取学生历史表现数据
            historical_performance = await self._get_historical_performance(student_id)

            # 计算基线指标
            baseline = {
                "average_answer_time": historical_performance.get("avg_answer_time", 60.0),
                "average_accuracy": historical_performance.get("avg_accuracy", 0.7),
                "typical_session_duration": historical_performance.get(
                    "avg_session_duration", 1800
                ),
                "preferred_difficulty": historical_performance.get(
                    "preferred_difficulty", DifficultyLevel.ELEMENTARY
                ),
                "baseline_established_at": datetime.now(),
            }

            # 缓存基线数据
            if self.redis_client:
                baseline_key = f"baseline:{student_id}"
                await self.redis_client.hset(
                    baseline_key,
                    mapping={k: json.dumps(v, default=str) for k, v in baseline.items()},
                )
                await self.redis_client.expire(baseline_key, 86400)  # 24小时

            return baseline

        except Exception as e:
            logger.error(f"建立性能基线失败: {str(e)}")
            return {}

    async def _get_session_info(self, session_id: int) -> dict[str, Any] | None:
        """获取会话信息."""
        stmt = select(TrainingSession).where(TrainingSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            return {
                "id": session.id,
                "student_id": session.student_id,
                "session_type": session.session_type,
                "difficulty_level": session.difficulty_level,
                "question_count": session.question_count,
                "created_at": session.created_at,
            }
        return None

    async def _calculate_real_time_answer_speed(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """计算实时答题速度."""
        try:
            # 获取最近的答题记录
            recent_window = datetime.now() - timedelta(
                seconds=self.monitoring_config["performance_window"]
            )

            stmt = (
                select(TrainingRecord)
                .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
                .where(
                    and_(
                        TrainingSession.student_id == student_id,
                        TrainingRecord.session_id == session_id,
                        TrainingRecord.created_at >= recent_window,
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
                .limit(10)
            )

            result = await self.db.execute(stmt)
            recent_records = result.scalars().all()

            if not recent_records:
                return {"average_time": 0, "trend": "no_data", "sample_size": 0}

            # 计算平均答题时间
            times = [record.time_spent for record in recent_records if record.time_spent]
            if not times:
                return {"average_time": 0, "trend": "no_data", "sample_size": 0}

            avg_time = sum(times) / len(times)

            # 分析趋势
            if len(times) >= 5:
                recent_half = times[: len(times) // 2]
                earlier_half = times[len(times) // 2 :]

                recent_avg = sum(recent_half) / len(recent_half)
                earlier_avg = sum(earlier_half) / len(earlier_half)

                if recent_avg < earlier_avg * 0.9:
                    trend = "accelerating"
                elif recent_avg > earlier_avg * 1.1:
                    trend = "decelerating"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            return {
                "average_time": avg_time,
                "trend": trend,
                "sample_size": len(times),
                "min_time": min(times),
                "max_time": max(times),
                "last_answer_time": times[0] if times else 0,
            }

        except Exception as e:
            logger.error(f"计算实时答题速度失败: {str(e)}")
            return {"error": str(e)}

    async def _calculate_real_time_accuracy(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """计算实时正确率."""
        try:
            # 获取当前会话的所有答题记录
            stmt = (
                select(TrainingRecord)
                .where(TrainingRecord.session_id == session_id)
                .order_by(desc(TrainingRecord.created_at))
            )

            result = await self.db.execute(stmt)
            all_records = result.scalars().all()

            if not all_records:
                return {"current_accuracy": 0, "trend": "no_data", "total_attempts": 0}

            # 计算总体正确率
            correct_count = sum(1 for record in all_records if record.is_correct)
            total_count = len(all_records)
            current_accuracy = correct_count / total_count

            # 计算最近10题的正确率
            recent_10 = all_records[:10]
            recent_correct = sum(1 for record in recent_10 if record.is_correct)
            recent_accuracy = recent_correct / len(recent_10) if recent_10 else 0

            # 分析趋势
            if len(all_records) >= 20:
                first_half = all_records[10:20]
                first_half_accuracy = sum(1 for r in first_half if r.is_correct) / len(first_half)

                if recent_accuracy > first_half_accuracy + 0.1:
                    trend = "improving"
                elif recent_accuracy < first_half_accuracy - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            # 连续错误检查
            consecutive_errors = 0
            for record in all_records:
                if not record.is_correct:
                    consecutive_errors += 1
                else:
                    break

            return {
                "current_accuracy": current_accuracy,
                "recent_10_accuracy": recent_accuracy,
                "trend": trend,
                "total_attempts": total_count,
                "correct_attempts": correct_count,
                "consecutive_errors": consecutive_errors,
                "accuracy_change": (
                    recent_accuracy - (current_accuracy - recent_accuracy)
                    if len(all_records) >= 20
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"计算实时正确率失败: {str(e)}")
            return {"error": str(e)}

    async def _calculate_learning_progress(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """计算学习进度."""
        try:
            # 获取会话信息
            session_info = await self._get_session_info(session_id)
            if not session_info:
                return {"error": "会话不存在"}

            # 计算完成进度
            stmt = select(func.count(TrainingRecord.id)).where(
                TrainingRecord.session_id == session_id
            )
            result = await self.db.execute(stmt)
            completed_questions = result.scalar() or 0

            target_questions = session_info["question_count"]
            completion_rate = completed_questions / target_questions if target_questions > 0 else 0

            # 计算时间进度
            session_start = session_info["created_at"]
            elapsed_time = (datetime.now() - session_start).total_seconds()

            # 估算剩余时间
            if completed_questions > 0:
                avg_time_per_question = elapsed_time / completed_questions
                estimated_remaining_time = (
                    target_questions - completed_questions
                ) * avg_time_per_question
            else:
                estimated_remaining_time = 0

            return {
                "completion_rate": completion_rate,
                "completed_questions": completed_questions,
                "target_questions": target_questions,
                "remaining_questions": target_questions - completed_questions,
                "elapsed_time": elapsed_time,
                "estimated_remaining_time": estimated_remaining_time,
                "estimated_total_time": elapsed_time + estimated_remaining_time,
                "pace": (
                    "ahead"
                    if completion_rate > elapsed_time / 1800
                    else ("behind" if completion_rate < elapsed_time / 2400 else "on_track")
                ),
            }

        except Exception as e:
            logger.error(f"计算学习进度失败: {str(e)}")
            return {"error": str(e)}

    async def _calculate_engagement_metrics(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """计算参与度指标."""
        try:
            # 获取最近的活动记录
            recent_window = datetime.now() - timedelta(minutes=10)

            stmt = (
                select(TrainingRecord)
                .where(
                    and_(
                        TrainingRecord.session_id == session_id,
                        TrainingRecord.created_at >= recent_window,
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
            )

            result = await self.db.execute(stmt)
            recent_records = result.scalars().all()

            if not recent_records:
                return {
                    "engagement_level": "low",
                    "activity_score": 0,
                    "last_activity": None,
                }

            # 计算活动频率
            activity_count = len(recent_records)
            time_span = (datetime.now() - recent_records[-1].created_at).total_seconds()
            activity_rate = activity_count / max(time_span / 60, 1)  # 每分钟活动次数

            # 计算参与度分数
            if activity_rate >= 2:
                engagement_level = "high"
                activity_score = min(1.0, activity_rate / 3)
            elif activity_rate >= 1:
                engagement_level = "medium"
                activity_score = activity_rate / 2
            else:
                engagement_level = "low"
                activity_score = activity_rate

            # 检查连续活动时间
            last_activity = recent_records[0].created_at if recent_records else None
            time_since_last = (
                (datetime.now() - last_activity).total_seconds() if last_activity else float("inf")
            )

            return {
                "engagement_level": engagement_level,
                "activity_score": activity_score,
                "activity_rate": activity_rate,
                "recent_activity_count": activity_count,
                "last_activity": last_activity,
                "time_since_last_activity": time_since_last,
                "is_active": time_since_last < 300,  # 5分钟内有活动
            }

        except Exception as e:
            logger.error(f"计算参与度指标失败: {str(e)}")
            return {"error": str(e)}

    async def _calculate_difficulty_adaptation(
        self, student_id: int, session_id: int
    ) -> dict[str, Any]:
        """计算难度适应性指标."""
        try:
            # 获取当前会话的难度等级
            session_info = await self._get_session_info(session_id)
            if not session_info:
                return {"error": "会话不存在"}

            current_difficulty = session_info["difficulty_level"]

            # 获取当前难度下的表现
            stmt = (
                select(TrainingRecord)
                .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
                .where(
                    and_(
                        TrainingSession.student_id == student_id,
                        TrainingSession.difficulty_level == current_difficulty,
                        TrainingRecord.created_at >= datetime.now() - timedelta(hours=1),
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
                .limit(20)
            )

            result = await self.db.execute(stmt)
            difficulty_records = result.scalars().all()

            if not difficulty_records:
                return {"adaptation_status": "unknown", "difficulty_match": 0.5}

            # 计算当前难度下的表现
            correct_count = sum(1 for record in difficulty_records if record.is_correct)
            accuracy = correct_count / len(difficulty_records)

            avg_time = sum(
                record.time_spent for record in difficulty_records if record.time_spent
            ) / len(difficulty_records)

            # 评估难度适应性
            if accuracy >= 0.85 and avg_time <= 90:
                adaptation_status = "too_easy"
                difficulty_match = 0.3
                suggestion = "increase_difficulty"
            elif accuracy <= 0.6 or avg_time >= 180:
                adaptation_status = "too_hard"
                difficulty_match = 0.3
                suggestion = "decrease_difficulty"
            else:
                adaptation_status = "appropriate"
                difficulty_match = 0.8 + (0.2 * (1 - abs(accuracy - 0.75) / 0.25))
                suggestion = "maintain_difficulty"

            return {
                "adaptation_status": adaptation_status,
                "difficulty_match": difficulty_match,
                "current_difficulty": current_difficulty.name,
                "accuracy_at_difficulty": accuracy,
                "avg_time_at_difficulty": avg_time,
                "suggestion": suggestion,
                "sample_size": len(difficulty_records),
            }

        except Exception as e:
            logger.error(f"计算难度适应性失败: {str(e)}")
            return {"error": str(e)}

    async def _cache_real_time_metrics(
        self, student_id: int, session_id: int, metrics: dict[str, Any]
    ) -> None:
        """缓存实时指标数据."""
        if not self.redis_client:
            return

        try:
            # 缓存当前指标
            current_key = f"metrics:current:{student_id}:{session_id}"
            await self.redis_client.set(
                current_key,
                json.dumps(metrics, default=str),
                ex=self.monitoring_config["cache_ttl"],
            )

            # 添加到时间序列
            timestamp = int(datetime.now().timestamp())
            timeseries_key = f"metrics:timeseries:{student_id}:{session_id}"

            await self.redis_client.zadd(
                timeseries_key, {json.dumps(metrics, default=str): timestamp}
            )

            # 清理过期数据
            cutoff = timestamp - self.monitoring_config["metrics_retention"]["real_time"]
            await self.redis_client.zremrangebyscore(timeseries_key, 0, cutoff)

        except Exception as e:
            logger.error(f"缓存实时指标失败: {str(e)}")

    async def _check_alert_conditions(
        self, student_id: int, session_id: int, metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """检查预警条件."""
        alerts = []
        thresholds = self.monitoring_config["alert_thresholds"]

        try:
            # 检查正确率下降
            accuracy_metrics = metrics.get("accuracy_metrics", {})
            if accuracy_metrics.get("accuracy_change", 0) < -thresholds["accuracy_drop"]:
                alerts.append(
                    {
                        "type": "accuracy_drop",
                        "severity": "warning",
                        "message": f"正确率下降超过{thresholds['accuracy_drop']:.0%}",
                        "current_value": accuracy_metrics.get("current_accuracy", 0),
                        "threshold": thresholds["accuracy_drop"],
                        "timestamp": datetime.now(),
                    }
                )

            # 检查连续错误
            consecutive_errors = accuracy_metrics.get("consecutive_errors", 0)
            if consecutive_errors >= thresholds["consecutive_errors"]:
                alerts.append(
                    {
                        "type": "consecutive_errors",
                        "severity": "critical",
                        "message": f"连续{consecutive_errors}次答错",
                        "current_value": consecutive_errors,
                        "threshold": thresholds["consecutive_errors"],
                        "timestamp": datetime.now(),
                    }
                )

            # 检查答题速度下降
            speed_metrics = metrics.get("answer_speed", {})
            if speed_metrics.get("trend") == "decelerating":
                alerts.append(
                    {
                        "type": "speed_decline",
                        "severity": "info",
                        "message": "答题速度明显下降",
                        "current_value": speed_metrics.get("average_time", 0),
                        "timestamp": datetime.now(),
                    }
                )

            # 检查参与度下降
            engagement_metrics = metrics.get("engagement_metrics", {})
            if engagement_metrics.get("engagement_level") == "low":
                alerts.append(
                    {
                        "type": "low_engagement",
                        "severity": "warning",
                        "message": "学习参与度较低",
                        "current_value": engagement_metrics.get("activity_score", 0),
                        "timestamp": datetime.now(),
                    }
                )

            # 缓存预警信息
            if alerts:
                await self._cache_alerts(student_id, session_id, alerts)

            return alerts

        except Exception as e:
            logger.error(f"检查预警条件失败: {str(e)}")
            return []

    async def _cache_alerts(
        self, student_id: int, session_id: int, alerts: list[dict[str, Any]]
    ) -> None:
        """缓存预警信息."""
        if not self.redis_client:
            return

        try:
            alerts_key = f"alerts:{student_id}:{session_id}"
            timestamp = int(datetime.now().timestamp())

            for alert in alerts:
                await self.redis_client.zadd(
                    alerts_key, {json.dumps(alert, default=str): timestamp}
                )

            # 设置过期时间
            await self.redis_client.expire(alerts_key, 86400)  # 24小时

        except Exception as e:
            logger.error(f"缓存预警信息失败: {str(e)}")

    async def _get_historical_performance(self, student_id: int) -> dict[str, Any]:
        """获取学生历史表现数据."""
        try:
            # 获取最近30天的训练记录
            cutoff_date = datetime.now() - timedelta(days=30)

            stmt = (
                select(TrainingRecord, TrainingSession)
                .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
                .where(
                    and_(
                        TrainingSession.student_id == student_id,
                        TrainingRecord.created_at >= cutoff_date,
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
                .limit(200)
            )

            result = await self.db.execute(stmt)
            records = result.all()

            if not records:
                return {}

            # 计算历史指标
            training_records = [record[0] for record in records]
            sessions = [record[1] for record in records]

            # 平均答题时间
            times = [r.time_spent for r in training_records if r.time_spent]
            avg_answer_time = sum(times) / len(times) if times else 60.0

            # 平均正确率
            correct_count = sum(1 for r in training_records if r.is_correct)
            avg_accuracy = correct_count / len(training_records)

            # 平均会话时长
            session_durations = []
            for session in set(sessions):
                session_records = [r for r in training_records if r.session_id == session.id]
                if session_records:
                    duration = (
                        max(r.created_at for r in session_records)
                        - min(r.created_at for r in session_records)
                    ).total_seconds()
                    session_durations.append(duration)

            avg_session_duration = (
                sum(session_durations) / len(session_durations) if session_durations else 1800
            )

            # 偏好难度
            difficulty_counts: dict[DifficultyLevel, int] = {}
            for session in sessions:
                difficulty = session.difficulty_level
                difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

            preferred_difficulty = (
                max(difficulty_counts.keys(), key=lambda x: difficulty_counts[x])
                if difficulty_counts
                else DifficultyLevel.ELEMENTARY
            )

            return {
                "avg_answer_time": avg_answer_time,
                "avg_accuracy": avg_accuracy,
                "avg_session_duration": avg_session_duration,
                "preferred_difficulty": preferred_difficulty,
                "total_records": len(training_records),
                "analysis_period_days": 30,
            }

        except Exception as e:
            logger.error(f"获取历史表现数据失败: {str(e)}")
            return {}

    async def stop_real_time_monitoring(self, student_id: int, session_id: int) -> dict[str, Any]:
        """停止实时监控."""
        try:
            logger.info(f"停止实时监控: 学生{student_id}, 会话{session_id}")

            # 获取最终指标
            final_metrics = await self.collect_real_time_metrics(student_id, session_id)

            # 更新监控会话状态
            if self.redis_client:
                session_key = f"monitoring:session:{student_id}:{session_id}"
                await self.redis_client.hset(session_key, "status", "completed")
                await self.redis_client.hset(session_key, "end_time", datetime.now().isoformat())

            return {
                "monitoring_stopped": True,
                "session_id": session_id,
                "student_id": student_id,
                "final_metrics": final_metrics,
                "stop_time": datetime.now(),
            }

        except Exception as e:
            logger.error(f"停止实时监控失败: {str(e)}")
            raise RuntimeError(f"停止实时监控失败: {str(e)}") from e

    async def get_cached_metrics(self, student_id: int, session_id: int) -> dict[str, Any] | None:
        """获取缓存的实时指标."""
        if not self.redis_client:
            return None

        try:
            current_key = f"metrics:current:{student_id}:{session_id}"
            cached_data = await self.redis_client.get(current_key)

            if cached_data:
                return json.loads(cached_data)  # type: ignore[no-any-return]
            return None

        except Exception as e:
            logger.error(f"获取缓存指标失败: {str(e)}")
            return None
