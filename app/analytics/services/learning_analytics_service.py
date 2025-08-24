"""
学习数据分析服务

提供全面的学习数据分析和洞察：
- 学习行为分析
- 学习效果评估
- 学习路径优化
- 个性化学习建议
- 学习趋势预测
"""

import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import DifficultyLevel
from app.shared.utils.metrics_collector import collect_metric
from app.training.models.training_models import (
    Question,
    TrainingRecord,
    TrainingSession,
)


class AnalysisType(Enum):
    """分析类型"""

    LEARNING_BEHAVIOR = "learning_behavior"  # 学习行为分析
    PERFORMANCE_ANALYSIS = "performance_analysis"  # 学习表现分析
    PROGRESS_TRACKING = "progress_tracking"  # 学习进度跟踪
    DIFFICULTY_ANALYSIS = "difficulty_analysis"  # 难度分析
    TIME_ANALYSIS = "time_analysis"  # 时间分析
    KNOWLEDGE_MAPPING = "knowledge_mapping"  # 知识点映射
    LEARNING_PATH = "learning_path"  # 学习路径分析
    PREDICTION = "prediction"  # 学习预测


class LearningPattern(Enum):
    """学习模式"""

    CONSISTENT = "consistent"  # 稳定型
    PROGRESSIVE = "progressive"  # 进步型
    FLUCTUATING = "fluctuating"  # 波动型
    DECLINING = "declining"  # 下降型
    BURST = "burst"  # 爆发型
    IRREGULAR = "irregular"  # 不规律型


class RecommendationType(Enum):
    """推荐类型"""

    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"  # 难度调整
    TOPIC_FOCUS = "topic_focus"  # 主题聚焦
    PRACTICE_FREQUENCY = "practice_frequency"  # 练习频率
    LEARNING_METHOD = "learning_method"  # 学习方法
    TIME_MANAGEMENT = "time_management"  # 时间管理
    KNOWLEDGE_REINFORCEMENT = "knowledge_reinforcement"  # 知识强化


@dataclass
class LearningMetrics:
    """学习指标"""

    user_id: str
    total_sessions: int
    total_questions: int
    correct_answers: int
    accuracy_rate: float
    average_time_per_question: float
    total_study_time: int  # 秒
    difficulty_distribution: dict[DifficultyLevel, int]
    topic_performance: dict[str, float]
    learning_streak: int  # 连续学习天数
    last_activity: datetime
    improvement_rate: float  # 改进率


@dataclass
class LearningInsight:
    """学习洞察"""

    insight_id: str
    user_id: str
    insight_type: AnalysisType
    title: str
    description: str
    metrics: dict[str, Any]
    recommendations: list[str]
    confidence_score: float  # 0-1
    priority: int  # 1-10
    timestamp: datetime
    expires_at: datetime | None = None


@dataclass
class LearningRecommendation:
    """学习建议"""

    recommendation_id: str
    user_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    action_items: list[str]
    expected_improvement: str
    difficulty_level: str
    estimated_time: int  # 分钟
    priority_score: float
    created_at: datetime
    expires_at: datetime


@dataclass
class LearningTrend:
    """学习趋势"""

    user_id: str
    trend_type: str
    time_period: str
    trend_direction: str  # "improving", "stable", "declining"
    trend_strength: float  # 0-1
    key_metrics: dict[str, float]
    predictions: dict[str, Any]
    confidence: float


class LearningAnalyticsService:
    """学习数据分析服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 分析缓存
        self.analysis_cache: dict[str, Any] = {}
        self.cache_ttl = 3600  # 1小时缓存

        # 洞察历史
        self.insights_history: deque[LearningInsight] = deque(maxlen=10000)

        # 推荐历史
        self.recommendations_history: deque[LearningRecommendation] = deque(maxlen=5000)

        # 分析统计
        self.analytics_stats = {
            "total_analyses": 0,
            "insights_generated": 0,
            "recommendations_made": 0,
            "last_analysis_time": None,
        }

    async def analyze_user_learning(
        self, user_id: str, db: AsyncSession, days: int = 30
    ) -> dict[str, Any]:
        """分析用户学习数据"""
        try:
            # 检查缓存
            cache_key = f"user_analysis_{user_id}_{days}"
            if cache_key in self.analysis_cache:
                cached_data = self.analysis_cache[cache_key]
                if (datetime.utcnow() - cached_data["timestamp"]).total_seconds() < self.cache_ttl:
                    return dict(cached_data["data"])

            # 获取时间范围
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            # 获取学习数据
            learning_metrics = await self._calculate_learning_metrics(
                user_id, db, start_time, end_time
            )

            # 进行各类分析
            analyses = {}

            # 1. 学习行为分析
            behavior_analysis = await self._analyze_learning_behavior(
                user_id, db, start_time, end_time
            )
            analyses["behavior"] = behavior_analysis

            # 2. 学习表现分析
            performance_analysis = await self._analyze_learning_performance(
                user_id, db, learning_metrics
            )
            analyses["performance"] = performance_analysis

            # 3. 学习进度分析
            progress_analysis = await self._analyze_learning_progress(
                user_id, db, start_time, end_time
            )
            analyses["progress"] = progress_analysis

            # 4. 难度适应性分析
            difficulty_analysis = await self._analyze_difficulty_adaptation(
                user_id, db, learning_metrics
            )
            analyses["difficulty"] = difficulty_analysis

            # 5. 时间模式分析
            time_analysis = await self._analyze_time_patterns(user_id, db, start_time, end_time)
            analyses["time_patterns"] = time_analysis

            # 6. 知识点掌握分析
            knowledge_analysis = await self._analyze_knowledge_mastery(
                user_id, db, learning_metrics
            )
            analyses["knowledge"] = knowledge_analysis

            # 生成综合分析结果
            comprehensive_analysis = {
                "user_id": user_id,
                "analysis_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "days": days,
                },
                "learning_metrics": learning_metrics.__dict__,
                "analyses": analyses,
                "overall_assessment": self._generate_overall_assessment(learning_metrics, analyses),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 缓存结果
            self.analysis_cache[cache_key] = {
                "data": comprehensive_analysis,
                "timestamp": datetime.utcnow(),
            }

            # 更新统计
            total_analyses = self.analytics_stats.get("total_analyses", 0)
            self.analytics_stats["total_analyses"] = (
                total_analyses if isinstance(total_analyses, int) else 0
            ) + 1
            self.analytics_stats["last_analysis_time"] = datetime.utcnow()

            # 收集指标
            await self._collect_analysis_metrics(user_id, comprehensive_analysis)

            self.logger.info(f"用户学习分析完成: {user_id}")
            return comprehensive_analysis

        except Exception as e:
            self.logger.error(f"用户学习分析失败: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _calculate_learning_metrics(
        self, user_id: str, db: AsyncSession, start_time: datetime, end_time: datetime
    ) -> LearningMetrics:
        """计算学习指标"""
        # 获取训练会话
        sessions_query = select(TrainingSession).where(
            TrainingSession.student_id == user_id,
            TrainingSession.created_at >= start_time,
            TrainingSession.created_at <= end_time,
        )
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        # 获取训练记录
        records_query = select(TrainingRecord).where(
            TrainingRecord.student_id == user_id,
            TrainingRecord.created_at >= start_time,
            TrainingRecord.created_at <= end_time,
        )
        records_result = await db.execute(records_query)
        records = records_result.scalars().all()

        # 计算基础指标
        total_sessions = len(sessions)
        total_questions = len(records)
        correct_answers = sum(1 for record in records if record.is_correct)
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0.0

        # 计算平均答题时间
        total_time = sum(record.time_spent or 0 for record in records)
        average_time_per_question = total_time / total_questions if total_questions > 0 else 0.0

        # 计算总学习时间
        total_study_time = sum(int(session.time_spent or 0) for session in sessions)

        # 难度分布
        difficulty_distribution: defaultdict[DifficultyLevel, int] = defaultdict(int)
        for record in records:
            if hasattr(record, "question") and record.question:
                difficulty_distribution[record.question.difficulty_level] += 1

        # 主题表现（简化实现）
        topic_performance = {}
        topic_stats: defaultdict[str, dict[str, int]] = defaultdict(
            lambda: {"correct": 0, "total": 0}
        )

        for record in records:
            if hasattr(record, "question") and record.question:
                # 假设有主题字段
                topic = getattr(record.question, "topic", "general")
                topic_stats[topic]["total"] += 1
                if record.is_correct:
                    topic_stats[topic]["correct"] += 1

        for topic, stats in topic_stats.items():
            topic_performance[topic] = (
                stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
            )

        # 学习连续天数
        learning_streak = await self._calculate_learning_streak(user_id, db, end_time)

        # 最后活动时间
        last_activity = max((session.created_at for session in sessions), default=start_time)

        # 改进率计算
        improvement_rate = await self._calculate_improvement_rate(user_id, db, start_time, end_time)

        return LearningMetrics(
            user_id=user_id,
            total_sessions=total_sessions,
            total_questions=total_questions,
            correct_answers=correct_answers,
            accuracy_rate=accuracy_rate,
            average_time_per_question=average_time_per_question,
            total_study_time=total_study_time,
            difficulty_distribution=dict(difficulty_distribution),
            topic_performance=topic_performance,
            learning_streak=learning_streak,
            last_activity=last_activity,
            improvement_rate=improvement_rate,
        )

    async def _analyze_learning_behavior(
        self, user_id: str, db: AsyncSession, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """分析学习行为"""
        # 获取学习会话数据
        sessions_query = select(TrainingSession).where(
            TrainingSession.student_id == user_id,
            TrainingSession.created_at >= start_time,
            TrainingSession.created_at <= end_time,
        )
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        if not sessions:
            return {"pattern": "no_data", "details": {}}

        # 分析学习频率
        daily_sessions: defaultdict[Any, int] = defaultdict(int)
        for session in sessions:
            day_key = session.created_at.date()
            daily_sessions[day_key] += 1

        # 分析学习时长模式
        session_durations = [session.time_spent or 0 for session in sessions]
        avg_session_duration = statistics.mean(session_durations) if session_durations else 0

        # 分析学习时间偏好
        hour_distribution: defaultdict[int, int] = defaultdict(int)
        for session in sessions:
            hour_distribution[session.created_at.hour] += 1

        # 确定学习模式
        learning_pattern = self._identify_learning_pattern(daily_sessions, session_durations)

        return {
            "pattern": learning_pattern.value,
            "details": {
                "total_sessions": len(sessions),
                "average_session_duration": avg_session_duration,
                "daily_frequency": dict(daily_sessions),
                "preferred_hours": dict(hour_distribution),
                "session_duration_stats": {
                    "min": min(session_durations) if session_durations else 0,
                    "max": max(session_durations) if session_durations else 0,
                    "avg": avg_session_duration,
                    "std": (
                        statistics.stdev(session_durations) if len(session_durations) > 1 else 0
                    ),
                },
            },
        }

    async def _analyze_learning_performance(
        self, user_id: str, db: AsyncSession, metrics: LearningMetrics
    ) -> dict[str, Any]:
        """分析学习表现"""
        # 表现等级评估
        performance_level = "beginner"
        if metrics.accuracy_rate >= 0.9:
            performance_level = "expert"
        elif metrics.accuracy_rate >= 0.8:
            performance_level = "advanced"
        elif metrics.accuracy_rate >= 0.7:
            performance_level = "intermediate"
        elif metrics.accuracy_rate >= 0.6:
            performance_level = "basic"

        # 强项和弱项分析
        strengths = []
        weaknesses = []

        for topic, performance in metrics.topic_performance.items():
            if performance >= 0.8:
                strengths.append(topic)
            elif performance < 0.6:
                weaknesses.append(topic)

        # 效率分析
        efficiency_score = 0.0
        if metrics.average_time_per_question > 0:
            # 效率 = 准确率 / 平均答题时间（标准化）
            normalized_time = min(metrics.average_time_per_question / 60.0, 5.0)  # 最多5分钟
            efficiency_score = metrics.accuracy_rate / normalized_time

        return {
            "performance_level": performance_level,
            "accuracy_rate": metrics.accuracy_rate,
            "efficiency_score": efficiency_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_rate": metrics.improvement_rate,
            "consistency": self._calculate_consistency_score(metrics),
        }

    async def _analyze_learning_progress(
        self, user_id: str, db: AsyncSession, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """分析学习进度"""
        # 按周分析进度
        weekly_progress = {}
        current_time = start_time

        while current_time < end_time:
            week_end = min(current_time + timedelta(days=7), end_time)

            # 获取该周的记录
            week_records_query = select(TrainingRecord).where(
                TrainingRecord.student_id == user_id,
                TrainingRecord.created_at >= current_time,
                TrainingRecord.created_at < week_end,
            )
            week_records_result = await db.execute(week_records_query)
            week_records = week_records_result.scalars().all()

            week_key = current_time.strftime("%Y-W%U")
            if week_records:
                correct = sum(1 for record in week_records if record.is_correct)
                total = len(week_records)
                weekly_progress[week_key] = {
                    "accuracy": correct / total,
                    "questions_answered": total,
                    "study_time": sum(int(record.time_spent or 0) for record in week_records),
                }
            else:
                weekly_progress[week_key] = {
                    "accuracy": 0.0,
                    "questions_answered": 0,
                    "study_time": 0,
                }

            current_time = week_end

        # 计算进度趋势
        accuracies = [week["accuracy"] for week in weekly_progress.values()]
        progress_trend = "stable"
        if len(accuracies) >= 2:
            if accuracies[-1] > accuracies[0] + 0.1:
                progress_trend = "improving"
            elif accuracies[-1] < accuracies[0] - 0.1:
                progress_trend = "declining"

        return {
            "weekly_progress": weekly_progress,
            "trend": progress_trend,
            "total_improvement": accuracies[-1] - accuracies[0] if accuracies else 0.0,
            "consistency": statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0,
        }

    async def _analyze_difficulty_adaptation(
        self, user_id: str, db: AsyncSession, metrics: LearningMetrics
    ) -> dict[str, Any]:
        """分析难度适应性"""
        difficulty_performance = {}

        for difficulty, count in metrics.difficulty_distribution.items():
            if count > 0:
                # 获取该难度的准确率
                difficulty_records_query = (
                    select(TrainingRecord)
                    .join(Question)
                    .where(
                        TrainingRecord.student_id == user_id,
                        Question.difficulty_level == difficulty,
                    )
                )
                difficulty_records_result = await db.execute(difficulty_records_query)
                difficulty_records = difficulty_records_result.scalars().all()

                if difficulty_records:
                    correct = sum(1 for record in difficulty_records if record.is_correct)
                    accuracy = correct / len(difficulty_records)
                    difficulty_performance[difficulty.value] = {
                        "accuracy": accuracy,
                        "count": len(difficulty_records),
                        "avg_time": statistics.mean(
                            [record.time_spent or 0 for record in difficulty_records]
                        ),
                    }

        # 推荐难度
        if metrics.accuracy_rate >= 0.85:
            recommended_difficulty = "hard"
        elif metrics.accuracy_rate >= 0.70:
            recommended_difficulty = "medium"
        else:
            recommended_difficulty = "easy"

        return {
            "difficulty_performance": difficulty_performance,
            "recommended_difficulty": recommended_difficulty,
            "adaptation_score": self._calculate_adaptation_score(
                {str(k): v for k, v in difficulty_performance.items()}
            ),
        }

    async def _analyze_time_patterns(
        self, user_id: str, db: AsyncSession, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """分析时间模式"""
        sessions_query = select(TrainingSession).where(
            TrainingSession.student_id == user_id,
            TrainingSession.created_at >= start_time,
            TrainingSession.created_at <= end_time,
        )
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        if not sessions:
            return {"pattern": "no_data"}

        # 分析时间分布
        hourly_distribution: defaultdict[int, int] = defaultdict(int)
        daily_distribution: defaultdict[int, int] = defaultdict(int)
        weekly_distribution: defaultdict[str, int] = defaultdict(int)

        for session in sessions:
            hourly_distribution[session.created_at.hour] += 1
            daily_distribution[session.created_at.weekday()] += 1
            weekly_distribution[session.created_at.date().strftime("%Y-W%U")] += 1

        # 找出最佳学习时间
        best_hour = (
            max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else 0
        )
        best_day = (
            max(daily_distribution.items(), key=lambda x: x[1])[0] if daily_distribution else 0
        )

        # 学习规律性评分
        regularity_score = self._calculate_regularity_score(weekly_distribution)

        return {
            "hourly_distribution": dict(hourly_distribution),
            "daily_distribution": dict(daily_distribution),
            "weekly_distribution": dict(weekly_distribution),
            "best_learning_hour": best_hour,
            "best_learning_day": best_day,
            "regularity_score": regularity_score,
            "recommendations": self._generate_time_recommendations(
                hourly_distribution, daily_distribution, regularity_score
            ),
        }

    async def _analyze_knowledge_mastery(
        self, user_id: str, db: AsyncSession, metrics: LearningMetrics
    ) -> dict[str, Any]:
        """分析知识点掌握情况"""
        # 知识点掌握程度
        mastery_levels = {}
        for topic, performance in metrics.topic_performance.items():
            if performance >= 0.9:
                mastery_levels[topic] = "mastered"
            elif performance >= 0.8:
                mastery_levels[topic] = "proficient"
            elif performance >= 0.7:
                mastery_levels[topic] = "developing"
            elif performance >= 0.6:
                mastery_levels[topic] = "basic"
            else:
                mastery_levels[topic] = "needs_work"

        # 知识点关联分析（简化实现）
        knowledge_gaps = [
            topic for topic, level in mastery_levels.items() if level in ["basic", "needs_work"]
        ]

        # 学习路径建议
        learning_path = self._generate_learning_path(mastery_levels, knowledge_gaps)

        return {
            "mastery_levels": mastery_levels,
            "knowledge_gaps": knowledge_gaps,
            "learning_path": learning_path,
            "overall_mastery_score": (
                statistics.mean(metrics.topic_performance.values())
                if metrics.topic_performance
                else 0.0
            ),
        }

    def _identify_learning_pattern(
        self, daily_sessions: dict[Any, int], session_durations: list[int]
    ) -> LearningPattern:
        """识别学习模式"""
        if not daily_sessions or not session_durations:
            return LearningPattern.IRREGULAR

        # 分析频率稳定性
        session_counts = list(daily_sessions.values())
        frequency_std = statistics.stdev(session_counts) if len(session_counts) > 1 else 0

        # 分析时长稳定性
        duration_std = statistics.stdev(session_durations) if len(session_durations) > 1 else 0
        avg_duration = statistics.mean(session_durations)

        # 判断模式
        if frequency_std < 1.0 and duration_std < avg_duration * 0.3:
            return LearningPattern.CONSISTENT
        elif len(session_counts) >= 7:
            # 检查是否有上升趋势
            recent_avg = statistics.mean(session_counts[-3:])
            early_avg = statistics.mean(session_counts[:3])
            if recent_avg > early_avg * 1.2:
                return LearningPattern.PROGRESSIVE
            elif recent_avg < early_avg * 0.8:
                return LearningPattern.DECLINING

        if frequency_std > 2.0:
            return LearningPattern.FLUCTUATING

        return LearningPattern.IRREGULAR

    def _calculate_consistency_score(self, metrics: LearningMetrics) -> float:
        """计算一致性评分"""
        # 基于准确率和学习频率的一致性
        base_score = metrics.accuracy_rate

        # 学习连续性加分
        if metrics.learning_streak >= 7:
            base_score += 0.1
        elif metrics.learning_streak >= 3:
            base_score += 0.05

        return min(1.0, base_score)

    def _calculate_adaptation_score(self, difficulty_performance: dict[str, Any]) -> float:
        """计算难度适应性评分"""
        if not difficulty_performance:
            return 0.0

        # 计算各难度的表现平衡度
        accuracies = [float(perf["accuracy"]) for perf in difficulty_performance.values()]
        if len(accuracies) <= 1:
            return float(accuracies[0]) if accuracies else 0.0

        # 适应性 = 平均准确率 - 准确率标准差
        avg_accuracy = statistics.mean(accuracies)
        accuracy_std = statistics.stdev(accuracies)

        return max(0.0, avg_accuracy - accuracy_std * 0.5)

    def _calculate_regularity_score(self, weekly_distribution: dict[str, int]) -> float:
        """计算学习规律性评分"""
        if len(weekly_distribution) < 2:
            return 0.0

        session_counts = list(weekly_distribution.values())
        avg_sessions = float(statistics.mean(session_counts))
        std_sessions = float(statistics.stdev(session_counts))

        # 规律性 = 1 - (标准差 / 平均值)
        if avg_sessions == 0:
            return 0.0

        regularity = 1.0 - min(1.0, std_sessions / avg_sessions)
        return max(0.0, regularity)

    def _generate_time_recommendations(
        self, hourly_dist: dict[int, int], daily_dist: dict[int, int], regularity: float
    ) -> list[str]:
        """生成时间管理建议"""
        recommendations = []

        if regularity < 0.5:
            recommendations.append("建议制定固定的学习时间表，提高学习规律性")

        if hourly_dist:
            peak_hours = sorted(hourly_dist.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_hour_str = "、".join([f"{hour}点" for hour, _ in peak_hours])
            recommendations.append(
                f"您在{peak_hour_str}学习效果较好，建议在这些时间段安排重要学习内容"
            )

        if daily_dist:
            weekday_sessions = sum(daily_dist.get(i, 0) for i in range(5))  # 周一到周五
            weekend_sessions = sum(daily_dist.get(i, 0) for i in range(5, 7))  # 周末

            if weekend_sessions > weekday_sessions * 2:
                recommendations.append("建议在工作日也安排一些学习时间，保持学习连续性")

        return recommendations

    def _generate_learning_path(
        self, mastery_levels: dict[str, str], knowledge_gaps: list[str]
    ) -> list[str]:
        """生成学习路径建议"""
        path = []

        # 优先处理基础薄弱的知识点
        basic_gaps = [topic for topic, level in mastery_levels.items() if level == "needs_work"]
        if basic_gaps:
            path.append(f"优先加强基础薄弱的知识点：{', '.join(basic_gaps)}")

        # 巩固发展中的知识点
        developing_topics = [
            topic for topic, level in mastery_levels.items() if level == "developing"
        ]
        if developing_topics:
            path.append(f"继续巩固发展中的知识点：{', '.join(developing_topics)}")

        # 提升熟练度
        proficient_topics = [
            topic for topic, level in mastery_levels.items() if level == "proficient"
        ]
        if proficient_topics:
            path.append(f"通过综合练习提升熟练知识点：{', '.join(proficient_topics)}")

        return path

    def _generate_overall_assessment(
        self, metrics: LearningMetrics, analyses: dict[str, Any]
    ) -> dict[str, Any]:
        """生成综合评估"""
        # 计算综合评分
        performance_score = analyses.get("performance", {}).get("efficiency_score", 0.0)
        consistency_score = analyses.get("performance", {}).get("consistency", 0.0)
        progress_score = max(0.0, analyses.get("progress", {}).get("total_improvement", 0.0))

        overall_score = performance_score * 0.4 + consistency_score * 0.3 + progress_score * 0.3

        # 确定学习者类型
        learner_type = "developing"
        if overall_score >= 0.8:
            learner_type = "advanced"
        elif overall_score >= 0.6:
            learner_type = "intermediate"
        elif overall_score >= 0.4:
            learner_type = "basic"

        # 生成关键洞察
        key_insights = []
        if metrics.accuracy_rate >= 0.8:
            key_insights.append("学习准确率较高，表现优秀")
        if metrics.learning_streak >= 7:
            key_insights.append("学习连续性很好，保持了良好的学习习惯")
        if metrics.improvement_rate > 0.1:
            key_insights.append("学习进步明显，继续保持")

        return {
            "overall_score": overall_score,
            "learner_type": learner_type,
            "key_insights": key_insights,
            "summary": f"在过去的学习中，您的整体表现为{learner_type}水平，"
            f"准确率达到{metrics.accuracy_rate:.1%}，"
            f"已连续学习{metrics.learning_streak}天。",
        }

    async def _calculate_learning_streak(
        self, user_id: str, db: AsyncSession, end_date: datetime
    ) -> int:
        """计算学习连续天数"""
        streak = 0
        current_date = end_date.date()

        for _ in range(365):  # 最多检查一年
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            # 检查当天是否有学习记录
            daily_query = select(TrainingSession).where(
                TrainingSession.student_id == user_id,
                TrainingSession.created_at >= day_start,
                TrainingSession.created_at < day_end,
            )
            daily_result = await db.execute(daily_query)
            daily_sessions = daily_result.scalars().all()

            if daily_sessions:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

        return streak

    async def _calculate_improvement_rate(
        self, user_id: str, db: AsyncSession, start_time: datetime, end_time: datetime
    ) -> float:
        """计算改进率"""
        # 将时间段分为前后两半
        mid_time = start_time + (end_time - start_time) / 2

        # 前半段准确率
        early_records_query = select(TrainingRecord).where(
            TrainingRecord.student_id == user_id,
            TrainingRecord.created_at >= start_time,
            TrainingRecord.created_at < mid_time,
        )
        early_records_result = await db.execute(early_records_query)
        early_records = early_records_result.scalars().all()

        # 后半段准确率
        late_records_query = select(TrainingRecord).where(
            TrainingRecord.student_id == user_id,
            TrainingRecord.created_at >= mid_time,
            TrainingRecord.created_at <= end_time,
        )
        late_records_result = await db.execute(late_records_query)
        late_records = late_records_result.scalars().all()

        if not early_records or not late_records:
            return 0.0

        early_accuracy = sum(1 for r in early_records if r.is_correct) / len(early_records)
        late_accuracy = sum(1 for r in late_records if r.is_correct) / len(late_records)

        return late_accuracy - early_accuracy

    async def _collect_analysis_metrics(self, user_id: str, analysis: dict[str, Any]) -> None:
        """收集分析指标"""
        try:
            metrics = analysis.get("learning_metrics", {})

            # 收集基础学习指标
            await collect_metric(
                "learning.accuracy_rate",
                metrics.get("accuracy_rate", 0.0),
                {"user_id": user_id},
            )

            await collect_metric(
                "learning.total_questions",
                metrics.get("total_questions", 0),
                {"user_id": user_id},
            )

            await collect_metric(
                "learning.study_time",
                metrics.get("total_study_time", 0),
                {"user_id": user_id},
            )

            # 收集分析结果指标
            overall = analysis.get("overall_assessment", {})
            await collect_metric(
                "learning.overall_score",
                overall.get("overall_score", 0.0),
                {
                    "user_id": user_id,
                    "learner_type": overall.get("learner_type", "unknown"),
                },
            )

        except Exception as e:
            self.logger.error(f"收集分析指标失败: {e}")

    async def generate_learning_insights(
        self, user_id: str, analysis: dict[str, Any]
    ) -> list[LearningInsight]:
        """生成学习洞察"""
        insights = []

        try:
            # 基于分析结果生成洞察
            analyses = analysis.get("analyses", {})

            # 1. 学习表现洞察
            performance = analyses.get("performance", {})
            if performance.get("accuracy_rate", 0) >= 0.8:
                insights.append(
                    LearningInsight(
                        insight_id=f"performance_{user_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        insight_type=AnalysisType.PERFORMANCE_ANALYSIS,
                        title="学习表现优秀",
                        description=f"您的准确率达到{performance.get('accuracy_rate', 0):.1%}，表现优秀！",
                        metrics=performance,
                        recommendations=[
                            "继续保持当前的学习方法",
                            "可以尝试更有挑战性的内容",
                        ],
                        confidence_score=0.9,
                        priority=8,
                        timestamp=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=7),
                    )
                )

            # 2. 学习习惯洞察
            behavior = analyses.get("behavior", {})
            if behavior.get("pattern") == "consistent":
                insights.append(
                    LearningInsight(
                        insight_id=f"behavior_{user_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        insight_type=AnalysisType.LEARNING_BEHAVIOR,
                        title="学习习惯良好",
                        description="您保持了稳定的学习习惯，这对长期学习效果很有帮助。",
                        metrics=behavior,
                        recommendations=[
                            "继续保持规律的学习时间",
                            "可以适当增加学习强度",
                        ],
                        confidence_score=0.8,
                        priority=7,
                        timestamp=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=14),
                    )
                )

            # 3. 知识点掌握洞察
            knowledge = analyses.get("knowledge", {})
            knowledge_gaps = knowledge.get("knowledge_gaps", [])
            if knowledge_gaps:
                insights.append(
                    LearningInsight(
                        insight_id=f"knowledge_{user_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        insight_type=AnalysisType.KNOWLEDGE_MAPPING,
                        title="发现知识薄弱点",
                        description=f"在{', '.join(knowledge_gaps)}方面还需要加强练习。",
                        metrics=knowledge,
                        recommendations=[
                            f"重点练习{', '.join(knowledge_gaps[:2])}",
                            "建议从基础概念开始复习",
                        ],
                        confidence_score=0.85,
                        priority=9,
                        timestamp=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=30),
                    )
                )

            # 添加到历史记录
            self.insights_history.extend(insights)
            insights_generated = self.analytics_stats.get("insights_generated", 0)
            self.analytics_stats["insights_generated"] = (
                insights_generated if isinstance(insights_generated, int) else 0
            ) + len(insights)

            return insights

        except Exception as e:
            self.logger.error(f"生成学习洞察失败: {e}")
            return []

    async def generate_learning_recommendations(
        self, user_id: str, analysis: dict[str, Any]
    ) -> list[LearningRecommendation]:
        """生成学习建议"""
        recommendations = []

        try:
            analyses = analysis.get("analyses", {})

            # 1. 难度调整建议
            difficulty_analysis = analyses.get("difficulty", {})
            recommended_difficulty = difficulty_analysis.get("recommended_difficulty", "medium")

            if recommended_difficulty != "medium":
                recommendations.append(
                    LearningRecommendation(
                        recommendation_id=f"difficulty_{user_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        recommendation_type=RecommendationType.DIFFICULTY_ADJUSTMENT,
                        title="调整练习难度",
                        description=f"建议调整到{recommended_difficulty}难度的题目",
                        action_items=[
                            f"选择{recommended_difficulty}难度的练习题",
                            "逐步适应新的难度水平",
                        ],
                        expected_improvement="提高学习效率和成就感",
                        difficulty_level="medium",
                        estimated_time=30,
                        priority_score=0.8,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=14),
                    )
                )

            # 2. 时间管理建议
            time_analysis = analyses.get("time_patterns", {})
            regularity_score = time_analysis.get("regularity_score", 0.0)

            if regularity_score < 0.5:
                recommendations.append(
                    LearningRecommendation(
                        recommendation_id=f"time_{user_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        recommendation_type=RecommendationType.TIME_MANAGEMENT,
                        title="改善学习时间规律性",
                        description="建立固定的学习时间表，提高学习效果",
                        action_items=[
                            "制定每日固定学习时间",
                            "设置学习提醒",
                            "记录学习时间和效果",
                        ],
                        expected_improvement="提高学习连续性和效果",
                        difficulty_level="easy",
                        estimated_time=15,
                        priority_score=0.7,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=21),
                    )
                )

            # 3. 知识强化建议
            knowledge_analysis = analyses.get("knowledge", {})
            knowledge_gaps = knowledge_analysis.get("knowledge_gaps", [])

            if knowledge_gaps:
                recommendations.append(
                    LearningRecommendation(
                        recommendation_id=f"knowledge_{user_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        recommendation_type=RecommendationType.KNOWLEDGE_REINFORCEMENT,
                        title="强化薄弱知识点",
                        description=f"重点加强{', '.join(knowledge_gaps[:3])}的学习",
                        action_items=[
                            f"每天练习{knowledge_gaps[0]}相关题目",
                            "复习相关理论知识",
                            "寻找相关学习资源",
                        ],
                        expected_improvement="提高薄弱环节的掌握程度",
                        difficulty_level="medium",
                        estimated_time=45,
                        priority_score=0.9,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=30),
                    )
                )

            # 添加到历史记录
            self.recommendations_history.extend(recommendations)
            recommendations_made = self.analytics_stats.get("recommendations_made", 0)
            self.analytics_stats["recommendations_made"] = (
                recommendations_made if isinstance(recommendations_made, int) else 0
            ) + len(recommendations)

            return recommendations

        except Exception as e:
            self.logger.error(f"生成学习建议失败: {e}")
            return []

    def get_analytics_summary(self) -> dict[str, Any]:
        """获取分析服务摘要"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analytics_stats": self.analytics_stats,
            "cache_size": len(self.analysis_cache),
            "insights_count": len(self.insights_history),
            "recommendations_count": len(self.recommendations_history),
        }


# 全局学习分析服务实例
_learning_analytics_service: LearningAnalyticsService | None = None


def get_learning_analytics_service() -> LearningAnalyticsService:
    """获取学习分析服务实例"""
    global _learning_analytics_service

    if _learning_analytics_service is None:
        _learning_analytics_service = LearningAnalyticsService()

    return _learning_analytics_service
