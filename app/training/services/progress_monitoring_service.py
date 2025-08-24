"""进度监控服务 - 实时学习进度监控和智能提醒."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.training.models.training_models import TrainingRecord, TrainingSession
from app.training.utils.reminder_utils import ReminderUtils
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class ProgressMonitoringService:
    """进度监控服务 - 实时监控学习进度并提供智能提醒."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化进度监控服务."""
        self.db = db
        self.reminder_utils = ReminderUtils()

        # 监控配置
        self.monitoring_config = {
            "progress_check_interval_hours": 24,  # 进度检查间隔
            "reminder_threshold_days": 3,  # 提醒阈值天数
            "performance_decline_threshold": 0.1,  # 表现下降阈值
            "consistency_threshold": 0.7,  # 一致性阈值
            "goal_deadline_warning_days": 7,  # 目标截止提醒天数
        }

        # 进度指标配置
        self.progress_metrics = {
            "completion_rate": {"weight": 0.3, "target": 0.8},
            "accuracy_rate": {"weight": 0.25, "target": 0.75},
            "consistency_score": {"weight": 0.2, "target": 0.8},
            "improvement_rate": {"weight": 0.15, "target": 0.1},
            "engagement_score": {"weight": 0.1, "target": 0.7},
        }

    async def monitor_student_progress(self, student_id: int) -> dict[str, Any]:
        """监控学生学习进度."""
        try:
            # 获取学生信息
            student = await self.db.get(User, student_id)
            if not student:
                raise ValueError(f"学生不存在: {student_id}")

            # 计算各项进度指标
            progress_metrics = await self._calculate_progress_metrics(student_id)

            # 分析进度趋势
            progress_trends = await self._analyze_progress_trends(student_id)

            # 检测异常情况
            anomalies = await self._detect_progress_anomalies(student_id, progress_metrics)

            # 生成进度报告
            progress_report = await self._generate_progress_report(
                student_id, progress_metrics, progress_trends, anomalies
            )

            # 生成提醒和建议
            reminders = await self._generate_reminders(student_id, progress_metrics, anomalies)

            # 更新监控状态
            await self._update_monitoring_status(student_id, progress_metrics)

            logger.info(f"学生 {student_id} 进度监控完成")
            return {
                "student_id": student_id,
                "monitoring_timestamp": datetime.now(),
                "progress_metrics": progress_metrics,
                "progress_trends": progress_trends,
                "anomalies": anomalies,
                "progress_report": progress_report,
                "reminders": reminders,
                "overall_status": self._determine_overall_status(progress_metrics),
            }

        except Exception as e:
            logger.error(f"监控学生进度失败: {str(e)}")
            raise

    async def get_real_time_progress(self, student_id: int) -> dict[str, Any]:
        """获取实时学习进度."""
        try:
            # 获取今日学习数据
            today_progress = await self._get_today_progress(student_id)

            # 获取本周学习数据
            week_progress = await self._get_week_progress(student_id)

            # 获取当前会话进度
            current_session = await self._get_current_session_progress(student_id)

            # 计算实时指标
            real_time_metrics = await self._calculate_real_time_metrics(
                student_id, today_progress, week_progress
            )

            # 生成实时建议
            real_time_suggestions = await self._generate_real_time_suggestions(
                student_id, real_time_metrics
            )

            return {
                "student_id": student_id,
                "timestamp": datetime.now(),
                "today_progress": today_progress,
                "week_progress": week_progress,
                "current_session": current_session,
                "real_time_metrics": real_time_metrics,
                "suggestions": real_time_suggestions,
            }

        except Exception as e:
            logger.error(f"获取实时进度失败: {str(e)}")
            raise

    async def track_goal_progress(self, student_id: int, goal_id: int) -> dict[str, Any]:
        """跟踪特定目标的进度."""
        try:
            # 获取目标信息
            goal_info = await self._get_goal_info(goal_id)
            if not goal_info:
                raise ValueError(f"目标不存在: {goal_id}")

            # 计算目标进度
            goal_progress = await self._calculate_goal_progress(student_id, goal_id)

            # 分析目标达成可能性
            achievement_probability = await self._analyze_achievement_probability(
                goal_info, goal_progress
            )

            # 检查里程碑状态
            milestone_status = await self._check_milestone_status(goal_id, goal_progress)

            # 生成目标相关提醒
            goal_reminders = await self._generate_goal_reminders(
                goal_info, goal_progress, achievement_probability
            )

            # 计算剩余时间和所需努力
            time_analysis = await self._analyze_remaining_time(goal_info, goal_progress)

            return {
                "goal_id": goal_id,
                "student_id": student_id,
                "goal_info": goal_info,
                "goal_progress": goal_progress,
                "achievement_probability": achievement_probability,
                "milestone_status": milestone_status,
                "goal_reminders": goal_reminders,
                "time_analysis": time_analysis,
                "tracking_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"跟踪目标进度失败: {str(e)}")
            raise

    async def generate_progress_alerts(self, student_id: int) -> list[dict[str, Any]]:
        """生成进度预警."""
        try:
            alerts = []

            # 检查学习一致性
            consistency_alert = await self._check_consistency_alert(student_id)
            if consistency_alert:
                alerts.append(consistency_alert)

            # 检查表现下降
            performance_alert = await self._check_performance_decline_alert(student_id)
            if performance_alert:
                alerts.append(performance_alert)

            # 检查目标截止日期
            deadline_alerts = await self._check_deadline_alerts(student_id)
            alerts.extend(deadline_alerts)

            # 检查学习停滞
            stagnation_alert = await self._check_stagnation_alert(student_id)
            if stagnation_alert:
                alerts.append(stagnation_alert)

            # 按优先级排序
            alerts.sort(key=lambda x: x.get("priority", 0), reverse=True)

            logger.info(f"为学生 {student_id} 生成 {len(alerts)} 个进度预警")
            return alerts

        except Exception as e:
            logger.error(f"生成进度预警失败: {str(e)}")
            raise

    async def get_progress_summary(self, student_id: int, period_days: int = 30) -> dict[str, Any]:
        """获取进度总结."""
        try:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # 获取期间统计数据
            period_stats = await self._get_period_statistics(student_id, start_date, end_date)

            # 计算进步情况
            improvement_analysis = await self._analyze_improvement(student_id, period_stats)

            # 识别成就和里程碑
            achievements = await self._identify_achievements(student_id, start_date, end_date)

            # 分析学习模式
            learning_patterns = await self._analyze_learning_patterns(student_id, period_stats)

            # 生成总结报告
            summary_report = await self._generate_summary_report(
                student_id,
                period_stats,
                improvement_analysis,
                achievements,
                learning_patterns,
            )

            return {
                "student_id": student_id,
                "summary_period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": period_days,
                },
                "period_stats": period_stats,
                "improvement_analysis": improvement_analysis,
                "achievements": achievements,
                "learning_patterns": learning_patterns,
                "summary_report": summary_report,
                "generated_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"获取进度总结失败: {str(e)}")
            raise

    # ==================== 私有方法 ====================

    async def _calculate_progress_metrics(self, student_id: int) -> dict[str, Any]:
        """计算进度指标."""
        # 获取最近30天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # 完成率
        completion_rate = await self._calculate_completion_rate(student_id, start_date, end_date)

        # 准确率
        accuracy_rate = await self._calculate_accuracy_rate(student_id, start_date, end_date)

        # 一致性分数
        consistency_score = await self._calculate_consistency_score(
            student_id, start_date, end_date
        )

        # 改进率
        improvement_rate = await self._calculate_improvement_rate(student_id, start_date, end_date)

        # 参与度分数
        engagement_score = await self._calculate_engagement_score(student_id, start_date, end_date)

        # 计算综合分数
        overall_score = (
            completion_rate * self.progress_metrics["completion_rate"]["weight"]
            + accuracy_rate * self.progress_metrics["accuracy_rate"]["weight"]
            + consistency_score * self.progress_metrics["consistency_score"]["weight"]
            + improvement_rate * self.progress_metrics["improvement_rate"]["weight"]
            + engagement_score * self.progress_metrics["engagement_score"]["weight"]
        )

        return {
            "completion_rate": completion_rate,
            "accuracy_rate": accuracy_rate,
            "consistency_score": consistency_score,
            "improvement_rate": improvement_rate,
            "engagement_score": engagement_score,
            "overall_score": overall_score,
            "calculation_date": datetime.now(),
        }

    async def _analyze_progress_trends(self, student_id: int) -> dict[str, Any]:
        """分析进度趋势."""
        # 获取最近几周的数据
        trends = {}

        for weeks_back in [1, 2, 3, 4]:
            end_date = datetime.now() - timedelta(weeks=weeks_back - 1)
            start_date = end_date - timedelta(weeks=1)

            week_metrics = await self._calculate_progress_metrics_for_period(
                student_id, start_date, end_date
            )
            trends[f"week_{weeks_back}"] = week_metrics

        # 计算趋势方向
        trend_analysis = await self._calculate_trend_direction(trends)

        return {
            "weekly_trends": trends,
            "trend_analysis": trend_analysis,
            "trend_summary": self._summarize_trends(trend_analysis),
        }

    async def _detect_progress_anomalies(
        self, student_id: int, current_metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """检测进度异常."""
        anomalies = []

        # 检查各项指标是否异常
        for metric, config in self.progress_metrics.items():
            current_value = current_metrics.get(metric, 0)
            target_value = config["target"]

            if current_value < target_value * 0.7:  # 低于目标70%
                anomalies.append(
                    {
                        "type": "low_performance",
                        "metric": metric,
                        "current_value": current_value,
                        "target_value": target_value,
                        "severity": ("high" if current_value < target_value * 0.5 else "medium"),
                        "description": f"{metric}低于预期",
                    }
                )

        return anomalies

    async def _generate_progress_report(
        self,
        student_id: int,
        metrics: dict[str, Any],
        trends: dict[str, Any],
        anomalies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """生成进度报告."""
        # 总体评估
        overall_assessment = self._assess_overall_progress(metrics, trends)

        # 强项和弱项
        strengths = self._identify_strengths(metrics)
        weaknesses = self._identify_weaknesses(metrics, anomalies)

        # 改进建议
        recommendations = self._generate_recommendations(metrics, trends, anomalies)

        return {
            "overall_assessment": overall_assessment,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "summary": f"整体进度{overall_assessment}，建议关注{weaknesses[0] if weaknesses else '继续保持'}",
        }

    async def _generate_reminders(
        self,
        student_id: int,
        metrics: dict[str, Any],
        anomalies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """生成提醒."""
        reminders = []

        # 基于异常生成提醒
        for anomaly in anomalies:
            reminder = await self.reminder_utils.create_reminder(
                student_id=student_id,
                reminder_type="performance_alert",
                message=f"注意：{anomaly['description']}",
                priority=anomaly["severity"],
            )
            reminders.append(reminder)

        # 基于一致性生成提醒
        if metrics.get("consistency_score", 1) < self.monitoring_config["consistency_threshold"]:
            reminder = await self.reminder_utils.create_reminder(
                student_id=student_id,
                reminder_type="consistency_reminder",
                message="建议保持规律的学习习惯",
                priority="medium",
            )
            reminders.append(reminder)

        return reminders

    async def _update_monitoring_status(self, student_id: int, metrics: dict[str, Any]) -> None:
        """更新监控状态."""
        # TODO: 实现监控状态更新逻辑
        logger.info(f"更新学生 {student_id} 监控状态")

    def _determine_overall_status(self, metrics: dict[str, Any]) -> str:
        """确定整体状态."""
        overall_score = metrics.get("overall_score", 0)

        if overall_score >= 0.8:
            return "excellent"
        elif overall_score >= 0.6:
            return "good"
        elif overall_score >= 0.4:
            return "fair"
        else:
            return "needs_attention"

    async def _get_today_progress(self, student_id: int) -> dict[str, Any]:
        """获取今日进度."""
        today = datetime.now().date()

        # 获取今日训练记录
        stmt = select(func.count(TrainingRecord.id), func.avg(TrainingRecord.score)).where(
            and_(
                TrainingRecord.student_id == student_id,
                func.date(TrainingRecord.created_at) == today,
            )
        )

        result = await self.db.execute(stmt)
        count, avg_score = result.first()

        return {
            "date": today,
            "questions_completed": count or 0,
            "average_score": avg_score or 0,
            "study_time_minutes": await self._get_today_study_time(student_id),
        }

    async def _get_week_progress(self, student_id: int) -> dict[str, Any]:
        """获取本周进度."""
        # 计算本周开始日期
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

        # 获取本周训练记录
        stmt = select(func.count(TrainingRecord.id), func.avg(TrainingRecord.score)).where(
            and_(
                TrainingRecord.student_id == student_id,
                TrainingRecord.created_at >= week_start,
            )
        )

        result = await self.db.execute(stmt)
        count, avg_score = result.first()

        return {
            "week_start": week_start.date(),
            "questions_completed": count or 0,
            "average_score": avg_score or 0,
            "study_days": await self._get_week_study_days(student_id, week_start),
        }

    async def _get_current_session_progress(self, student_id: int) -> dict[str, Any] | None:
        """获取当前会话进度."""
        # 获取最近的活跃会话
        stmt = (
            select(TrainingSession)
            .where(TrainingSession.student_id == student_id)
            .order_by(desc(TrainingSession.created_at))
            .limit(1)
        )

        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session and session.completed_at is None:  # 活跃会话
            return {
                "session_id": session.id,
                "start_time": session.started_at,
                "duration_minutes": (datetime.now() - session.started_at).total_seconds() / 60,
                "questions_completed": await self._get_session_question_count(session.id),
            }

        return None

    async def _calculate_real_time_metrics(
        self,
        student_id: int,
        today_progress: dict[str, Any],
        week_progress: dict[str, Any],
    ) -> dict[str, Any]:
        """计算实时指标."""
        return {
            "daily_target_progress": today_progress["questions_completed"] / 20,  # 假设每日目标20题
            "weekly_target_progress": week_progress["questions_completed"]
            / 100,  # 假设每周目标100题
            "current_momentum": ("high" if today_progress["questions_completed"] > 10 else "low"),
            "consistency_this_week": week_progress["study_days"] / 7,
        }

    async def _generate_real_time_suggestions(
        self, student_id: int, metrics: dict[str, Any]
    ) -> list[str]:
        """生成实时建议."""
        suggestions = []

        if metrics["daily_target_progress"] < 0.5:
            suggestions.append("今日学习进度较慢，建议增加练习时间")

        if metrics["consistency_this_week"] < 0.6:
            suggestions.append("本周学习不够规律，建议制定固定学习时间")

        if metrics["current_momentum"] == "low":
            suggestions.append("当前学习动力不足，建议设定小目标激励自己")

        return suggestions

    # 简化实现的辅助方法
    async def _calculate_completion_rate(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> float:
        """计算完成率."""
        # TODO: 实现实际的完成率计算逻辑
        return 0.75

    async def _calculate_accuracy_rate(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> float:
        """计算准确率."""
        stmt = select(
            func.count(TrainingRecord.id).label("total"),
            func.count(TrainingRecord.id).filter(TrainingRecord.is_correct).label("correct"),  # noqa: E712
        ).where(
            and_(
                TrainingRecord.student_id == student_id,
                TrainingRecord.created_at.between(start_date, end_date),
            )
        )

        result = await self.db.execute(stmt)
        total, correct = result.first()

        return (correct or 0) / max(total or 1, 1)

    async def _calculate_consistency_score(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> float:
        """计算一致性分数."""
        # TODO: 实现一致性分数计算逻辑
        return 0.8

    async def _calculate_improvement_rate(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> float:
        """计算改进率."""
        # TODO: 实现改进率计算逻辑
        return 0.1

    async def _calculate_engagement_score(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> float:
        """计算参与度分数."""
        # TODO: 实现参与度分数计算逻辑
        return 0.7

    async def _get_today_study_time(self, student_id: int) -> int:
        """获取今日学习时间."""
        # TODO: 实现今日学习时间计算逻辑
        return 45

    async def _get_week_study_days(self, student_id: int, week_start: datetime) -> int:
        """获取本周学习天数."""
        # TODO: 实现本周学习天数计算逻辑
        return 5

    async def _get_session_question_count(self, session_id: int) -> int:
        """获取会话题目数量."""
        # TODO: 实现会话题目数量计算逻辑
        return 8

    # 其他简化实现的方法
    async def _calculate_progress_metrics_for_period(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        return {"overall_score": 0.7}

    async def _calculate_trend_direction(self, trends: dict[str, Any]) -> dict[str, Any]:
        return {"direction": "improving", "rate": 0.05}

    def _summarize_trends(self, trend_analysis: dict[str, Any]) -> str:
        return "整体呈上升趋势"

    def _assess_overall_progress(self, metrics: dict[str, Any], trends: dict[str, Any]) -> str:
        return "良好"

    def _identify_strengths(self, metrics: dict[str, Any]) -> list[str]:
        return ["学习一致性好", "准确率稳定"]

    def _identify_weaknesses(
        self, metrics: dict[str, Any], anomalies: list[dict[str, Any]]
    ) -> list[str]:
        return ["完成率需要提高"] if anomalies else []

    def _generate_recommendations(
        self,
        metrics: dict[str, Any],
        trends: dict[str, Any],
        anomalies: list[dict[str, Any]],
    ) -> list[str]:
        return ["建议增加每日练习时间", "保持当前学习节奏"]

    async def _get_goal_info(self, goal_id: int) -> dict[str, Any] | None:
        return {
            "goal_id": goal_id,
            "title": "提高词汇量",
            "target_date": datetime.now() + timedelta(days=30),
        }

    async def _calculate_goal_progress(self, student_id: int, goal_id: int) -> dict[str, Any]:
        return {"overall_progress": 0.6, "milestone_progress": 0.75}

    async def _analyze_achievement_probability(
        self, goal_info: dict[str, Any], progress: dict[str, Any]
    ) -> float:
        return 0.8

    async def _check_milestone_status(
        self, goal_id: int, progress: dict[str, Any]
    ) -> list[dict[str, Any]]:
        return [
            {"milestone_id": 1, "status": "completed"},
            {"milestone_id": 2, "status": "in_progress"},
        ]

    async def _generate_goal_reminders(
        self, goal_info: dict[str, Any], progress: dict[str, Any], probability: float
    ) -> list[dict[str, Any]]:
        return [{"type": "deadline_reminder", "message": "距离目标截止还有7天"}]

    async def _analyze_remaining_time(
        self, goal_info: dict[str, Any], progress: dict[str, Any]
    ) -> dict[str, Any]:
        return {"days_remaining": 15, "effort_required": "moderate", "on_track": True}

    async def _check_consistency_alert(self, student_id: int) -> dict[str, Any] | None:
        return {"type": "consistency", "message": "最近3天未学习", "priority": 3}

    async def _check_performance_decline_alert(self, student_id: int) -> dict[str, Any] | None:
        return None

    async def _check_deadline_alerts(self, student_id: int) -> list[dict[str, Any]]:
        return []

    async def _check_stagnation_alert(self, student_id: int) -> dict[str, Any] | None:
        return None

    async def _get_period_statistics(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        return {"total_questions": 150, "total_time": 1800, "avg_score": 0.75}

    async def _analyze_improvement(self, student_id: int, stats: dict[str, Any]) -> dict[str, Any]:
        return {"improvement_trend": "positive", "improvement_rate": 0.1}

    async def _identify_achievements(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "streak",
                "description": "连续学习7天",
                "achieved_date": datetime.now(),
            }
        ]

    async def _analyze_learning_patterns(
        self, student_id: int, stats: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "preferred_time": "evening",
            "session_length": "medium",
            "difficulty_preference": "moderate",
        }

    async def _generate_summary_report(
        self,
        student_id: int,
        stats: dict[str, Any],
        improvement: dict[str, Any],
        achievements: list[dict[str, Any]],
        patterns: dict[str, Any],
    ) -> str:
        return f"过去30天完成{stats['total_questions']}道题目，平均分{stats['avg_score']:.1%}，整体呈{improvement['improvement_trend']}趋势"
