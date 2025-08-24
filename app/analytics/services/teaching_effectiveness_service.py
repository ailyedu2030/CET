"""
教学效果数据分析服务

实现教学内容效果评估、AI批改质量分析、学习路径优化效果评估和教学策略调整建议。
支持多维度教学效果分析和智能优化建议。
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class TeachingContentType(Enum):
    """教学内容类型枚举"""

    VOCABULARY_TRAINING = "vocabulary_training"
    GRAMMAR_EXERCISE = "grammar_exercise"
    LISTENING_PRACTICE = "listening_practice"
    READING_COMPREHENSION = "reading_comprehension"
    WRITING_GUIDANCE = "writing_guidance"
    SPEAKING_PRACTICE = "speaking_practice"
    ERROR_CORRECTION = "error_correction"
    ADAPTIVE_LEARNING = "adaptive_learning"


class EffectivenessMetric(Enum):
    """教学效果指标枚举"""

    COMPLETION_RATE = "completion_rate"  # 完成率
    ACCURACY_IMPROVEMENT = "accuracy_improvement"  # 准确率提升
    ENGAGEMENT_LEVEL = "engagement_level"  # 参与度
    RETENTION_RATE = "retention_rate"  # 知识保持率
    LEARNING_SPEED = "learning_speed"  # 学习速度
    SATISFACTION_SCORE = "satisfaction_score"  # 满意度评分
    DIFFICULTY_ADAPTATION = "difficulty_adaptation"  # 难度适应性


@dataclass
class TeachingSession:
    """教学会话数据"""

    session_id: str
    user_id: int
    content_type: TeachingContentType
    start_time: datetime
    end_time: datetime | None = None
    content_items: list[str] = field(default_factory=list)
    interactions: list[dict[str, Any]] = field(default_factory=list)
    completion_rate: float = 0.0
    initial_score: float | None = None
    final_score: float | None = None
    engagement_metrics: dict[str, float] = field(default_factory=dict)
    feedback_quality: float | None = None

    @property
    def duration_minutes(self) -> float:
        """会话持续时间（分钟）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0.0

    @property
    def score_improvement(self) -> float:
        """分数提升"""
        if self.initial_score is not None and self.final_score is not None:
            return self.final_score - self.initial_score
        return 0.0


@dataclass
class EffectivenessAnalysis:
    """教学效果分析结果"""

    content_type: TeachingContentType
    analysis_period: str
    total_sessions: int
    avg_completion_rate: float
    avg_score_improvement: float
    avg_engagement_level: float
    avg_session_duration: float
    retention_rate: float
    effectiveness_score: float  # 综合效果评分 0-100
    strengths: list[str]
    weaknesses: list[str]
    optimization_suggestions: list[str]
    trend_analysis: dict[str, str]
    created_at: datetime = field(default_factory=datetime.now)


class TeachingEffectivenessService:
    """教学效果数据分析服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 教学会话存储
        self.sessions: dict[str, TeachingSession] = {}
        self.user_sessions: dict[int, list[str]] = defaultdict(list)
        self.content_sessions: dict[TeachingContentType, list[str]] = defaultdict(list)

        # 效果分析缓存
        self.analysis_cache: dict[str, EffectivenessAnalysis] = {}
        self.cache_ttl = timedelta(hours=2)

        # 基准数据
        self.benchmarks = {
            TeachingContentType.VOCABULARY_TRAINING: {
                "target_completion_rate": 0.85,
                "target_improvement": 0.15,
                "target_engagement": 0.75,
                "target_duration": 20.0,
            },
            TeachingContentType.GRAMMAR_EXERCISE: {
                "target_completion_rate": 0.80,
                "target_improvement": 0.20,
                "target_engagement": 0.70,
                "target_duration": 25.0,
            },
            TeachingContentType.LISTENING_PRACTICE: {
                "target_completion_rate": 0.75,
                "target_improvement": 0.18,
                "target_engagement": 0.80,
                "target_duration": 30.0,
            },
            TeachingContentType.READING_COMPREHENSION: {
                "target_completion_rate": 0.78,
                "target_improvement": 0.16,
                "target_engagement": 0.72,
                "target_duration": 35.0,
            },
            TeachingContentType.WRITING_GUIDANCE: {
                "target_completion_rate": 0.70,
                "target_improvement": 0.25,
                "target_engagement": 0.85,
                "target_duration": 45.0,
            },
        }

        # 统计数据
        self.stats: dict[str, Any] = {
            "total_sessions": 0,
            "active_content_types": 0,
            "avg_effectiveness_score": 0.0,
            "improvement_trend": "stable",
        }

    async def record_teaching_session(
        self,
        session_id: str,
        user_id: int,
        content_type: TeachingContentType,
        content_items: list[str],
        initial_score: float | None = None,
    ) -> None:
        """记录教学会话开始"""
        session = TeachingSession(
            session_id=session_id,
            user_id=user_id,
            content_type=content_type,
            start_time=datetime.now(),
            content_items=content_items,
            initial_score=initial_score,
        )

        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)
        self.content_sessions[content_type].append(session_id)
        self.stats["total_sessions"] += 1

    async def record_interaction(
        self, session_id: str, interaction_type: str, data: dict[str, Any]
    ) -> None:
        """记录教学交互"""
        if session_id in self.sessions:
            interaction = {
                "type": interaction_type,
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }
            self.sessions[session_id].interactions.append(interaction)

    async def complete_teaching_session(
        self,
        session_id: str,
        completion_rate: float,
        final_score: float | None = None,
        engagement_metrics: dict[str, float] | None = None,
        feedback_quality: float | None = None,
    ) -> None:
        """完成教学会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.end_time = datetime.now()
            session.completion_rate = completion_rate
            session.final_score = final_score
            session.engagement_metrics = engagement_metrics or {}
            session.feedback_quality = feedback_quality

    async def analyze_content_effectiveness(
        self, content_type: TeachingContentType, days: int = 7
    ) -> EffectivenessAnalysis:
        """分析特定内容类型的教学效果"""
        cache_key = f"{content_type.value}_{days}d"

        # 检查缓存
        if cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            if datetime.now() - cached.created_at < self.cache_ttl:
                return cached

        # 获取指定时间范围的会话
        start_time = datetime.now() - timedelta(days=days)
        session_ids = self.content_sessions.get(content_type, [])

        relevant_sessions = [
            self.sessions[sid]
            for sid in session_ids
            if sid in self.sessions and self.sessions[sid].start_time >= start_time
        ]

        if not relevant_sessions:
            return self._create_empty_analysis(content_type, f"{days}d")

        # 计算基础指标
        total_sessions = len(relevant_sessions)
        completed_sessions = [s for s in relevant_sessions if s.end_time is not None]

        avg_completion_rate = (
            statistics.mean([s.completion_rate for s in completed_sessions])
            if completed_sessions
            else 0
        )

        # 计算分数提升
        score_improvements = [
            s.score_improvement for s in completed_sessions if s.score_improvement != 0
        ]
        avg_score_improvement = statistics.mean(score_improvements) if score_improvements else 0

        # 计算参与度
        engagement_scores = []
        for session in completed_sessions:
            if session.engagement_metrics:
                avg_engagement = statistics.mean(session.engagement_metrics.values())
                engagement_scores.append(avg_engagement)
        avg_engagement_level = statistics.mean(engagement_scores) if engagement_scores else 0

        # 计算平均会话时长
        durations = [s.duration_minutes for s in completed_sessions if s.duration_minutes > 0]
        avg_session_duration = statistics.mean(durations) if durations else 0

        # 计算知识保持率（简化计算）
        retention_rate = self._calculate_retention_rate(content_type, completed_sessions)

        # 计算综合效果评分
        effectiveness_score = self._calculate_effectiveness_score(
            content_type,
            avg_completion_rate,
            avg_score_improvement,
            avg_engagement_level,
            avg_session_duration,
        )

        # 分析优势和劣势
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            content_type,
            avg_completion_rate,
            avg_score_improvement,
            avg_engagement_level,
            avg_session_duration,
        )

        # 生成优化建议
        optimization_suggestions = await self._generate_optimization_suggestions(
            content_type, weaknesses, completed_sessions
        )

        # 趋势分析
        trend_analysis = self._analyze_trends(content_type, completed_sessions)

        # 创建分析结果
        analysis = EffectivenessAnalysis(
            content_type=content_type,
            analysis_period=f"{days}d",
            total_sessions=total_sessions,
            avg_completion_rate=avg_completion_rate,
            avg_score_improvement=avg_score_improvement,
            avg_engagement_level=avg_engagement_level,
            avg_session_duration=avg_session_duration,
            retention_rate=retention_rate,
            effectiveness_score=effectiveness_score,
            strengths=strengths,
            weaknesses=weaknesses,
            optimization_suggestions=optimization_suggestions,
            trend_analysis=trend_analysis,
        )

        # 缓存结果
        self.analysis_cache[cache_key] = analysis

        return analysis

    def _create_empty_analysis(
        self, content_type: TeachingContentType, period: str
    ) -> EffectivenessAnalysis:
        """创建空的分析结果"""
        return EffectivenessAnalysis(
            content_type=content_type,
            analysis_period=period,
            total_sessions=0,
            avg_completion_rate=0.0,
            avg_score_improvement=0.0,
            avg_engagement_level=0.0,
            avg_session_duration=0.0,
            retention_rate=0.0,
            effectiveness_score=0.0,
            strengths=[],
            weaknesses=["缺少数据"],
            optimization_suggestions=["需要更多教学数据来进行分析"],
            trend_analysis={"overall": "no_data"},
        )

    def _calculate_retention_rate(
        self, content_type: TeachingContentType, sessions: list[TeachingSession]
    ) -> float:
        """计算知识保持率"""
        # 简化计算：基于重复学习的表现
        if len(sessions) < 2:
            return 0.0

        # 按用户分组
        user_sessions = defaultdict(list)
        for session in sessions:
            user_sessions[session.user_id].append(session)

        retention_scores = []
        for _user_id, user_session_list in user_sessions.items():
            if len(user_session_list) >= 2:
                # 比较第一次和最后一次的表现
                first_session = min(user_session_list, key=lambda s: s.start_time)
                last_session = max(user_session_list, key=lambda s: s.start_time)

                if first_session.final_score is not None and last_session.final_score is not None:
                    # 如果最后一次表现不低于第一次，认为知识得到保持
                    retention = min(
                        last_session.final_score / max(first_session.final_score, 0.1),
                        1.0,
                    )
                    retention_scores.append(retention)

        return statistics.mean(retention_scores) if retention_scores else 0.0

    def _calculate_effectiveness_score(
        self,
        content_type: TeachingContentType,
        completion_rate: float,
        score_improvement: float,
        engagement_level: float,
        session_duration: float,
    ) -> float:
        """计算综合效果评分"""
        benchmark = self.benchmarks.get(content_type, {})

        # 各指标得分（0-25分）
        completion_score = min(
            completion_rate / benchmark.get("target_completion_rate", 0.8) * 25, 25
        )
        improvement_score = min(
            score_improvement / benchmark.get("target_improvement", 0.2) * 25, 25
        )
        engagement_score = min(engagement_level / benchmark.get("target_engagement", 0.75) * 25, 25)

        # 时长得分（适中最好）
        target_duration = benchmark.get("target_duration", 30.0)
        duration_ratio = session_duration / target_duration
        if 0.8 <= duration_ratio <= 1.2:  # 在目标时长的80%-120%范围内
            duration_score = 25
        elif duration_ratio < 0.8:
            duration_score = duration_ratio / 0.8 * 25
        else:
            duration_score = max(25 - (duration_ratio - 1.2) * 20, 0)

        total_score = completion_score + improvement_score + engagement_score + duration_score
        return min(total_score, 100.0)

    def _analyze_strengths_weaknesses(
        self,
        content_type: TeachingContentType,
        completion_rate: float,
        score_improvement: float,
        engagement_level: float,
        session_duration: float,
    ) -> tuple[list[str], list[str]]:
        """分析优势和劣势"""
        benchmark = self.benchmarks.get(content_type, {})
        strengths = []
        weaknesses = []

        # 完成率分析
        target_completion = benchmark.get("target_completion_rate", 0.8)
        if completion_rate >= target_completion:
            strengths.append(f"完成率优秀 ({completion_rate:.1%})")
        elif completion_rate < target_completion * 0.8:
            weaknesses.append(f"完成率偏低 ({completion_rate:.1%})")

        # 提升效果分析
        target_improvement = benchmark.get("target_improvement", 0.2)
        if score_improvement >= target_improvement:
            strengths.append(f"学习提升效果显著 (+{score_improvement:.1%})")
        elif score_improvement < target_improvement * 0.7:
            weaknesses.append(f"学习提升效果有限 (+{score_improvement:.1%})")

        # 参与度分析
        target_engagement = benchmark.get("target_engagement", 0.75)
        if engagement_level >= target_engagement:
            strengths.append(f"学生参与度高 ({engagement_level:.1%})")
        elif engagement_level < target_engagement * 0.8:
            weaknesses.append(f"学生参与度不足 ({engagement_level:.1%})")

        # 时长分析
        target_duration = benchmark.get("target_duration", 30.0)
        if abs(session_duration - target_duration) / target_duration <= 0.2:
            strengths.append(f"学习时长适中 ({session_duration:.1f}分钟)")
        elif session_duration < target_duration * 0.7:
            weaknesses.append(f"学习时长过短 ({session_duration:.1f}分钟)")
        elif session_duration > target_duration * 1.5:
            weaknesses.append(f"学习时长过长 ({session_duration:.1f}分钟)")

        return strengths, weaknesses

    async def _generate_optimization_suggestions(
        self,
        content_type: TeachingContentType,
        weaknesses: list[str],
        sessions: list[TeachingSession],
    ) -> list[str]:
        """生成优化建议"""
        suggestions = []

        # 基于弱点生成建议
        for weakness in weaknesses:
            if "完成率偏低" in weakness:
                suggestions.append("建议降低内容难度或增加引导提示")
                suggestions.append("考虑将长内容拆分为更小的学习单元")
            elif "提升效果有限" in weakness:
                suggestions.append("建议增加个性化练习和针对性反馈")
                suggestions.append("考虑引入自适应学习算法")
            elif "参与度不足" in weakness:
                suggestions.append("建议增加互动元素和游戏化设计")
                suggestions.append("考虑优化界面设计和用户体验")
            elif "时长过短" in weakness:
                suggestions.append("建议增加内容深度或扩展练习")
            elif "时长过长" in weakness:
                suggestions.append("建议精简内容或优化学习路径")

        # 基于内容类型的专门建议
        if content_type == TeachingContentType.VOCABULARY_TRAINING:
            suggestions.append("考虑使用间隔重复算法优化词汇复习")
        elif content_type == TeachingContentType.WRITING_GUIDANCE:
            suggestions.append("建议增加写作模板和范例展示")
        elif content_type == TeachingContentType.LISTENING_PRACTICE:
            suggestions.append("考虑提供多种语速和口音选择")

        return suggestions[:5]  # 最多返回5条建议

    def _analyze_trends(
        self, content_type: TeachingContentType, sessions: list[TeachingSession]
    ) -> dict[str, str]:
        """分析趋势"""
        if len(sessions) < 5:
            return {"overall": "insufficient_data"}

        # 按时间排序
        sessions_sorted = sorted(sessions, key=lambda s: s.start_time)

        # 分析完成率趋势
        recent_completion = [s.completion_rate for s in sessions_sorted[-5:]]
        early_completion = [s.completion_rate for s in sessions_sorted[:5]]

        completion_trend = "stable"
        if len(recent_completion) >= 3 and len(early_completion) >= 3:
            recent_avg = statistics.mean(recent_completion)
            early_avg = statistics.mean(early_completion)

            if recent_avg > early_avg * 1.1:
                completion_trend = "improving"
            elif recent_avg < early_avg * 0.9:
                completion_trend = "declining"

        # 分析分数提升趋势
        score_improvements = [
            s.score_improvement for s in sessions_sorted if s.score_improvement != 0
        ]
        improvement_trend = "stable"

        if len(score_improvements) >= 5:
            recent_improvements = score_improvements[-3:]
            early_improvements = score_improvements[:3]

            if len(recent_improvements) >= 2 and len(early_improvements) >= 2:
                recent_avg = statistics.mean(recent_improvements)
                early_avg = statistics.mean(early_improvements)

                if recent_avg > early_avg * 1.2:
                    improvement_trend = "improving"
                elif recent_avg < early_avg * 0.8:
                    improvement_trend = "declining"

        return {
            "overall": completion_trend,
            "completion_rate": completion_trend,
            "score_improvement": improvement_trend,
        }

    async def get_comprehensive_report(self, days: int = 30) -> dict[str, Any]:
        """获取综合教学效果报告"""
        report: dict[str, Any] = {
            "report_period": f"{days} days",
            "generated_at": datetime.now().isoformat(),
            "content_analysis": {},
            "overall_metrics": {},
            "recommendations": [],
        }

        # 分析各内容类型
        all_effectiveness_scores = []
        for content_type in TeachingContentType:
            analysis = await self.analyze_content_effectiveness(content_type, days)
            report["content_analysis"][content_type.value] = {
                "total_sessions": analysis.total_sessions,
                "effectiveness_score": analysis.effectiveness_score,
                "completion_rate": analysis.avg_completion_rate,
                "score_improvement": analysis.avg_score_improvement,
                "engagement_level": analysis.avg_engagement_level,
                "strengths": analysis.strengths,
                "weaknesses": analysis.weaknesses,
                "trend": analysis.trend_analysis.get("overall", "stable"),
            }

            if analysis.total_sessions > 0:
                all_effectiveness_scores.append(analysis.effectiveness_score)

        # 计算整体指标
        if all_effectiveness_scores:
            report["overall_metrics"] = {
                "avg_effectiveness_score": statistics.mean(all_effectiveness_scores),
                "best_performing_content": max(
                    report["content_analysis"].items(),
                    key=lambda x: x[1]["effectiveness_score"],
                )[0],
                "needs_improvement_content": min(
                    report["content_analysis"].items(),
                    key=lambda x: x[1]["effectiveness_score"],
                )[0],
                "total_sessions": sum(
                    analysis["total_sessions"] for analysis in report["content_analysis"].values()
                ),
            }

        # 生成整体建议
        report["recommendations"] = await self._generate_overall_recommendations(
            report["content_analysis"]
        )

        return report

    async def _generate_overall_recommendations(
        self, content_analysis: dict[str, Any]
    ) -> list[str]:
        """生成整体优化建议"""
        recommendations = []

        # 找出表现最差的内容类型
        worst_content = min(content_analysis.items(), key=lambda x: x[1]["effectiveness_score"])

        if worst_content[1]["effectiveness_score"] < 60:
            recommendations.append(f"重点优化 {worst_content[0]} 的教学效果")

        # 分析整体趋势
        declining_contents = [
            name for name, data in content_analysis.items() if data["trend"] == "declining"
        ]

        if declining_contents:
            recommendations.append(f"关注 {', '.join(declining_contents)} 的效果下降趋势")

        # 参与度建议
        low_engagement_contents = [
            name for name, data in content_analysis.items() if data["engagement_level"] < 0.7
        ]

        if low_engagement_contents:
            recommendations.append("提升学生参与度，增加互动性设计")

        return recommendations[:5]

    async def get_service_stats(self) -> dict[str, Any]:
        """获取服务统计"""
        active_content_types = len(
            [ct for ct in TeachingContentType if len(self.content_sessions.get(ct, [])) > 0]
        )

        return {
            "stats": self.stats.copy(),
            "active_content_types": active_content_types,
            "cache_size": len(self.analysis_cache),
            "total_sessions_stored": len(self.sessions),
        }


# 全局教学效果分析服务实例
teaching_effectiveness_service = TeachingEffectivenessService()
