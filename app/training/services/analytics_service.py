"""训练分析服务 - 学习进度跟踪和数据洞察."""

import datetime as dt
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import TrainingType
from app.training.models.training_models import TrainingRecord, TrainingSession
from app.training.schemas.training_schemas import (
    LearningProgressResponse,
    PerformanceMetrics,
    PerformanceReportResponse,
)


class AnalyticsService:
    """训练分析服务 - 提供全面的学习数据分析和洞察."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ==================== 学习进度分析 ====================

    async def get_learning_progress(
        self, student_id: int, training_type: TrainingType | None = None, days: int = 30
    ) -> LearningProgressResponse:
        """获取学生学习进度分析."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 构建基础查询
        base_query = select(TrainingRecord).where(
            and_(
                TrainingRecord.student_id == student_id,
                TrainingRecord.created_at >= start_date,
                TrainingRecord.created_at <= end_date,
            )
        )

        if training_type:
            # 通过session关联查询特定训练类型
            base_query = base_query.join(TrainingSession).where(
                TrainingSession.session_type == training_type
            )

        records = await self.db.execute(base_query)
        training_records = records.scalars().all()

        # 计算基础统计
        total_questions = len(training_records)
        correct_answers = sum(1 for r in training_records if r.is_correct)
        accuracy_rate = (correct_answers / total_questions) if total_questions > 0 else 0.0

        # 计算平均用时
        total_time = sum(r.time_spent for r in training_records if r.time_spent)
        avg_time = (total_time / total_questions) if total_questions > 0 else 0.0

        # 计算连续学习天数
        study_dates = set()
        for record in training_records:
            study_dates.add(record.created_at.date())
        # consecutive_days = await self._calculate_consecutive_days(student_id, end_date)

        # 转换为list类型
        training_records_list = list(training_records)

        # 按训练类型统计
        type_stats = await self._get_type_statistics(training_records_list)

        # 按难度统计
        difficulty_stats = await self._get_difficulty_statistics(training_records_list)

        # 学习趋势分析
        # trend_data = await self._get_learning_trend(student_id, start_date, end_date)

        # 知识点掌握情况
        # knowledge_mastery = await self._get_knowledge_mastery(training_records)

        # 构建PerformanceMetrics
        overall_metrics = PerformanceMetrics(
            total_sessions=len({r.session_id for r in training_records_list}),
            total_questions=total_questions,
            correct_answers=correct_answers,
            total_score=sum(r.score for r in training_records_list),
            average_score=(
                sum(r.score for r in training_records_list) / total_questions
                if total_questions > 0
                else 0
            ),
            accuracy_rate=accuracy_rate,
            total_time_spent=sum(r.time_spent for r in training_records_list),
            average_time_per_question=avg_time,
            improvement_rate=0.0,  # 需要计算
            consistency_score=0.0,  # 需要计算
        )

        return LearningProgressResponse(
            student_id=student_id,
            training_type=training_type,
            date_range={"start": start_date, "end": end_date},
            overall_metrics=overall_metrics,
            knowledge_point_progress=[],  # 需要实现
            difficulty_progression=difficulty_stats,
            time_distribution={},  # 需要实现
            strengths=[],  # 需要实现
            weaknesses=[],  # 需要实现
            recommendations=await self._generate_improvement_suggestions(
                accuracy_rate, type_stats, difficulty_stats
            ),
            updated_at=datetime.utcnow(),
        )

    async def get_performance_metrics(
        self, student_id: int, training_type: TrainingType, days: int = 7
    ) -> PerformanceMetrics:
        """获取特定训练类型的性能指标."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 查询训练记录
        query = (
            select(TrainingRecord)
            .join(TrainingSession)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingRecord.created_at >= start_date,
                )
            )
        )

        result = await self.db.execute(query)
        records = result.scalars().all()

        if not records:
            return PerformanceMetrics(
                total_sessions=0,
                total_questions=0,
                correct_answers=0,
                total_score=0.0,
                average_score=0.0,
                accuracy_rate=0.0,
                total_time_spent=0,
                average_time_per_question=0.0,
                improvement_rate=0.0,
                consistency_score=0.0,
            )

        # 基础统计
        total_attempts = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        accuracy_rate = correct_count / total_attempts

        # 平均分数和用时
        total_score = sum(r.score for r in records if r.score)
        average_score = total_score / total_attempts if total_attempts > 0 else 0.0

        total_time = sum(r.time_spent for r in records if r.time_spent)
        average_time = total_time / total_attempts if total_attempts > 0 else 0.0

        # 改进率计算（对比前一周期）
        improvement_rate = await self._calculate_improvement_rate(
            student_id, training_type, start_date
        )

        # 难度分布
        # difficulty_distribution = await self._get_difficulty_distribution(records)

        # 近期表现趋势
        # performance_trend = await self._get_performance_trend(records, days)

        return PerformanceMetrics(
            total_sessions=len({r.session_id for r in records}),
            total_questions=total_attempts,
            correct_answers=correct_count,
            total_score=total_score,
            average_score=average_score,
            accuracy_rate=accuracy_rate,
            total_time_spent=sum(r.time_spent for r in records),
            average_time_per_question=average_time,
            improvement_rate=improvement_rate,
            consistency_score=0.0,  # 需要计算
        )

    async def generate_performance_report(
        self, student_id: int, days: int = 30
    ) -> PerformanceReportResponse:
        """生成综合性能报告."""

        # 获取所有训练类型的数据
        all_metrics = {}
        for training_type in TrainingType:
            metrics = await self.get_performance_metrics(student_id, training_type, days)
            if metrics.total_questions > 0:
                all_metrics[training_type] = metrics

        # 整体统计
        total_questions = sum(m.total_questions for m in all_metrics.values())
        total_correct = sum(m.correct_answers for m in all_metrics.values())
        overall_accuracy = (total_correct / total_questions) if total_questions > 0 else 0.0

        # 最强和最弱领域
        best_area = None
        worst_area = None
        if all_metrics:
            best_area = max(all_metrics.keys(), key=lambda k: all_metrics[k].accuracy_rate)
            worst_area = min(all_metrics.keys(), key=lambda k: all_metrics[k].accuracy_rate)

        # 学习建议
        recommendations = await self._generate_comprehensive_recommendations(
            all_metrics, overall_accuracy
        )

        # 学习目标建议
        learning_goals = await self._suggest_learning_goals(student_id, all_metrics)

        # 构造图表数据
        from app.training.schemas.training_schemas import ChartData

        chart_data: list[ChartData] = []

        # 构造性能指标（使用第一个可用的指标作为主要指标）
        main_metrics = (
            next(iter(all_metrics.values()))
            if all_metrics
            else PerformanceMetrics(
                total_sessions=0,
                total_questions=0,
                correct_answers=0,
                total_score=0.0,
                average_score=0.0,
                accuracy_rate=0.0,
                total_time_spent=0,
                average_time_per_question=0.0,
                improvement_rate=0.0,
                consistency_score=0.0,
            )
        )

        return PerformanceReportResponse(
            student_id=student_id,
            report_type="综合性能报告",
            generated_at=datetime.utcnow(),
            date_range={
                "start_date": datetime.utcnow() - timedelta(days=days),
                "end_date": datetime.utcnow(),
            },
            executive_summary=f"在过去{days}天中，学生完成了{total_questions}道题目，整体准确率为{overall_accuracy:.1%}",
            key_findings=[
                f"总共回答了{total_questions}道题目",
                f"整体准确率达到{overall_accuracy:.1%}",
                f"最强领域：{best_area.value if best_area else '暂无数据'}",
                f"最弱领域：{worst_area.value if worst_area else '暂无数据'}",
            ],
            performance_metrics=main_metrics,
            progress_analysis={
                "training_types": len(all_metrics),
                "overall_accuracy": overall_accuracy,
                "total_questions": total_questions,
            },
            chart_data=chart_data,
            detailed_recommendations=[{"category": "学习建议", "items": recommendations}],
            next_steps=learning_goals,
        )

    # ==================== 数据洞察分析 ====================

    async def get_learning_patterns(self, student_id: int, days: int = 60) -> dict[str, Any]:
        """分析学习模式和习惯."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 查询学习记录
        query = select(TrainingRecord).where(
            and_(
                TrainingRecord.student_id == student_id,
                TrainingRecord.created_at >= start_date,
            )
        )

        result = await self.db.execute(query)
        records = result.scalars().all()

        if not records:
            return {"error": "没有足够的学习数据进行分析"}

        # 转换为list类型
        records_list = list(records)

        # 时间模式分析
        time_patterns = await self._analyze_time_patterns(records_list)

        # 学习频率分析
        frequency_patterns = await self._analyze_frequency_patterns(records_list)

        # 错误模式分析
        error_patterns = await self._analyze_error_patterns(records_list)

        # 进步模式分析
        progress_patterns = await self._analyze_progress_patterns(records_list)

        return {
            "analysis_period": f"{days}天",
            "total_records": len(records),
            "time_patterns": time_patterns,
            "frequency_patterns": frequency_patterns,
            "error_patterns": error_patterns,
            "progress_patterns": progress_patterns,
            "insights": await self._generate_pattern_insights(
                time_patterns, frequency_patterns, error_patterns, progress_patterns
            ),
        }

    async def get_comparative_analysis(
        self, student_id: int, comparison_group: str = "grade_level"
    ) -> dict[str, Any]:
        """获取对比分析数据."""
        # 获取学生数据
        student_progress = await self.get_learning_progress(student_id, days=30)

        # 获取对比组数据（这里简化处理，实际应根据comparison_group查询）
        comparison_data = await self._get_comparison_group_data(comparison_group)

        # 计算排名和百分位
        ranking_info = await self._calculate_ranking(student_id, comparison_data)

        # 生成对比洞察
        insights = await self._generate_comparative_insights(
            student_progress, comparison_data, ranking_info
        )

        return {
            "student_id": student_id,
            "comparison_group": comparison_group,
            "student_metrics": {
                "accuracy_rate": student_progress.overall_metrics.accuracy_rate,
                "total_questions": student_progress.overall_metrics.total_questions,
                "study_days": len(student_progress.time_distribution),
            },
            "group_averages": comparison_data,
            "ranking": ranking_info,
            "insights": insights,
            "improvement_opportunities": await self._identify_improvement_opportunities(
                student_progress, comparison_data
            ),
        }

    # ==================== 私有辅助方法 ====================

    async def _calculate_consecutive_days(self, student_id: int, end_date: datetime) -> int:
        """计算连续学习天数."""
        consecutive_days = 0
        current_date = end_date.date()

        for i in range(365):  # 最多检查一年
            check_date = current_date - timedelta(days=i)
            start_of_day = datetime.combine(check_date, datetime.min.time())
            end_of_day = datetime.combine(check_date, datetime.max.time())

            query = select(TrainingRecord).where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingRecord.created_at >= start_of_day,
                    TrainingRecord.created_at <= end_of_day,
                )
            )

            result = await self.db.execute(query)
            if result.scalars().first():
                consecutive_days += 1
            else:
                break

        return consecutive_days

    async def _get_type_statistics(
        self, records: list[TrainingRecord]
    ) -> dict[str, dict[str, Any]]:
        """按训练类型统计."""
        type_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "correct": 0, "accuracy": 0.0}
        )

        # 需要通过session获取training_type，这里简化处理
        for record in records:
            # 实际实现中需要join TrainingSession获取training_type
            # 这里使用占位符
            training_type = "VOCABULARY"  # 占位符
            type_stats[training_type]["total"] += 1
            if record.is_correct:
                type_stats[training_type]["correct"] += 1

        # 计算准确率
        for stats in type_stats.values():
            if stats["total"] > 0:
                stats["accuracy"] = stats["correct"] / stats["total"]

        return dict(type_stats)

    async def _get_difficulty_statistics(
        self, records: list[TrainingRecord]
    ) -> dict[str, dict[str, Any]]:
        """按难度统计."""
        difficulty_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "correct": 0, "accuracy": 0.0}
        )

        for record in records:
            # 需要通过question获取difficulty_level
            difficulty = "INTERMEDIATE"  # 占位符
            difficulty_stats[difficulty]["total"] += 1
            if record.is_correct:
                difficulty_stats[difficulty]["correct"] += 1

        # 计算准确率
        for stats in difficulty_stats.values():
            if stats["total"] > 0:
                stats["accuracy"] = stats["correct"] / stats["total"]

        return dict(difficulty_stats)

    async def _get_learning_trend(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """获取学习趋势数据."""
        trend_data = []
        current_date = start_date

        while current_date <= end_date:
            day_start = datetime.combine(current_date.date(), datetime.min.time())
            day_end = datetime.combine(current_date.date(), datetime.max.time())

            query = select(TrainingRecord).where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingRecord.created_at >= day_start,
                    TrainingRecord.created_at <= day_end,
                )
            )

            result = await self.db.execute(query)
            day_records = result.scalars().all()

            total = len(day_records)
            correct = sum(1 for r in day_records if r.is_correct)
            accuracy = (correct / total) if total > 0 else 0.0

            trend_data.append(
                {
                    "date": current_date.date().isoformat(),
                    "total_questions": total,
                    "correct_answers": correct,
                    "accuracy_rate": accuracy,
                }
            )

            current_date += timedelta(days=1)

        return trend_data

    async def _get_knowledge_mastery(
        self, records: list[TrainingRecord]
    ) -> dict[str, dict[str, Any]]:
        """分析知识点掌握情况."""
        knowledge_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "correct": 0, "mastery": 0.0}
        )

        for record in records:
            # 需要通过question获取knowledge_points
            # 这里使用占位符
            knowledge_points = ["vocabulary", "grammar"]  # 占位符
            for point in knowledge_points:
                knowledge_stats[point]["total"] += 1
                if record.is_correct:
                    knowledge_stats[point]["correct"] += 1

        # 计算掌握度
        for stats in knowledge_stats.values():
            if stats["total"] > 0:
                stats["mastery"] = stats["correct"] / stats["total"]

        return dict(knowledge_stats)

    async def _generate_improvement_suggestions(
        self,
        accuracy_rate: float,
        type_stats: dict[str, dict[str, Any]],
        difficulty_stats: dict[str, dict[str, Any]],
    ) -> list[str]:
        """生成改进建议."""
        suggestions = []

        # 基于整体准确率的建议
        if accuracy_rate < 0.6:
            suggestions.append("整体准确率较低，建议加强基础知识学习")
        elif accuracy_rate < 0.8:
            suggestions.append("准确率有待提高，建议针对性练习薄弱环节")
        else:
            suggestions.append("准确率良好，建议挑战更高难度题目")

        # 基于训练类型的建议
        if type_stats:
            weakest_type = min(type_stats.keys(), key=lambda k: type_stats[k]["accuracy"])
            suggestions.append(f"建议加强{weakest_type}类型题目的练习")

        # 基于难度的建议
        if difficulty_stats:
            for difficulty, stats in difficulty_stats.items():
                if stats["accuracy"] < 0.5:
                    suggestions.append(f"建议重点练习{difficulty}难度的题目")

        return suggestions

    async def _calculate_improvement_rate(
        self, student_id: int, training_type: TrainingType, current_start: datetime
    ) -> float:
        """计算改进率."""
        # 当前周期数据已在调用方获取
        # 获取前一周期数据
        period_length = (datetime.utcnow() - current_start).days
        previous_end = current_start
        previous_start = previous_end - timedelta(days=period_length)

        query = (
            select(TrainingRecord)
            .join(TrainingSession)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingRecord.created_at >= previous_start,
                    TrainingRecord.created_at < previous_end,
                )
            )
        )

        result = await self.db.execute(query)
        previous_records = result.scalars().all()

        if not previous_records:
            return 0.0

        previous_accuracy = sum(1 for r in previous_records if r.is_correct) / len(previous_records)

        # 当前准确率需要重新计算或传入
        # 这里简化处理
        current_accuracy = 0.75  # 占位符

        return (
            ((current_accuracy - previous_accuracy) / previous_accuracy * 100)
            if previous_accuracy > 0
            else 0.0
        )

    async def _get_difficulty_distribution(self, records: list[TrainingRecord]) -> dict[str, int]:
        """获取难度分布."""
        distribution: dict[str, int] = defaultdict(int)
        for _record in records:
            # 需要通过question获取difficulty_level
            difficulty = "INTERMEDIATE"  # 占位符
            distribution[difficulty] += 1
        return dict(distribution)

    async def _get_performance_trend(
        self, records: list[TrainingRecord], days: int
    ) -> list[dict[str, Any]]:
        """获取表现趋势."""
        # 按日期分组计算每日表现
        daily_performance = defaultdict(list)
        for record in records:
            date_key = record.created_at.date()
            daily_performance[date_key].append(record.is_correct)

        trend = []
        for date, correct_list in daily_performance.items():
            accuracy = sum(correct_list) / len(correct_list)
            trend.append({"date": date.isoformat(), "accuracy": accuracy})

        return sorted(trend, key=lambda x: x["date"])

    async def _generate_comprehensive_recommendations(
        self,
        all_metrics: dict[TrainingType, PerformanceMetrics],
        overall_accuracy: float,
    ) -> list[str]:
        """生成综合建议."""
        recommendations = []

        if overall_accuracy < 0.6:
            recommendations.append("建议从基础题目开始，循序渐进提高")
        elif overall_accuracy < 0.8:
            recommendations.append("整体表现良好，建议针对薄弱环节加强练习")
        else:
            recommendations.append("表现优秀，建议挑战更高难度或新的题型")

        # 针对具体训练类型的建议
        if all_metrics:
            weakest = min(all_metrics.keys(), key=lambda k: all_metrics[k].accuracy_rate)
            recommendations.append(f"重点关注{weakest.value}训练，提升准确率")

        return recommendations

    async def _suggest_learning_goals(
        self, student_id: int, all_metrics: dict[TrainingType, PerformanceMetrics]
    ) -> list[str]:
        """建议学习目标."""
        goals = []

        for training_type, metrics in all_metrics.items():
            if metrics.accuracy_rate < 0.8:
                target_accuracy = min(0.9, metrics.accuracy_rate + 0.1)
                goals.append(f"{training_type.value}准确率提升至{target_accuracy:.0%}")

        if not goals:
            goals.append("保持当前优秀水平，探索新的学习领域")

        return goals

    # ==================== 模式分析方法 ====================

    async def _analyze_time_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析时间模式."""
        hour_distribution: dict[int, int] = defaultdict(int)
        weekday_distribution: dict[int, int] = defaultdict(int)

        for record in records:
            hour = record.created_at.hour
            weekday = record.created_at.weekday()
            hour_distribution[hour] += 1
            weekday_distribution[weekday] += 1

        # 找出最活跃时段
        peak_hour = (
            max(hour_distribution.keys(), key=lambda h: hour_distribution[h])
            if hour_distribution
            else 0
        )
        peak_weekday = (
            max(weekday_distribution.keys(), key=lambda w: weekday_distribution[w])
            if weekday_distribution
            else 0
        )

        return {
            "peak_hour": peak_hour,
            "peak_weekday": peak_weekday,
            "hour_distribution": dict(hour_distribution),
            "weekday_distribution": dict(weekday_distribution),
        }

    async def _analyze_frequency_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析学习频率模式."""
        daily_counts: dict[dt.date, int] = defaultdict(int)
        for record in records:
            date_key = record.created_at.date()
            daily_counts[date_key] += 1

        if not daily_counts:
            return {
                "average_daily_questions": 0,
                "max_daily_questions": 0,
                "study_consistency": 0.0,
            }

        counts = list(daily_counts.values())
        average_daily = sum(counts) / len(counts)
        max_daily = max(counts)

        # 计算学习一致性（标准差的倒数）
        variance = sum((x - average_daily) ** 2 for x in counts) / len(counts)
        consistency = 1 / (1 + variance**0.5) if variance > 0 else 1.0

        return {
            "average_daily_questions": average_daily,
            "max_daily_questions": max_daily,
            "study_consistency": consistency,
        }

    async def _analyze_error_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析错误模式."""
        error_records = [r for r in records if not r.is_correct]
        total_errors = len(error_records)

        if total_errors == 0:
            return {"total_errors": 0, "error_rate": 0.0, "common_error_types": []}

        error_rate = total_errors / len(records)

        # 分析错误类型（需要更多数据支持）
        error_types: dict[str, int] = defaultdict(int)
        for _record in error_records:
            # 这里需要根据实际的错误分类逻辑
            error_types["答案错误"] += 1

        return {
            "total_errors": total_errors,
            "error_rate": error_rate,
            "common_error_types": dict(error_types),
        }

    async def _analyze_progress_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析进步模式."""
        if len(records) < 10:
            return {"trend": "数据不足", "improvement_rate": 0.0}

        # 按时间排序
        sorted_records = sorted(records, key=lambda r: r.created_at)

        # 计算滑动平均准确率
        window_size = min(10, len(sorted_records) // 3)
        early_accuracy = sum(1 for r in sorted_records[:window_size] if r.is_correct) / window_size
        late_accuracy = sum(1 for r in sorted_records[-window_size:] if r.is_correct) / window_size

        improvement_rate = (
            (late_accuracy - early_accuracy) / early_accuracy * 100 if early_accuracy > 0 else 0.0
        )

        if improvement_rate > 5:
            trend = "明显进步"
        elif improvement_rate > 0:
            trend = "稳步提升"
        elif improvement_rate > -5:
            trend = "基本稳定"
        else:
            trend = "需要关注"

        return {
            "trend": trend,
            "improvement_rate": improvement_rate,
            "early_period_accuracy": early_accuracy,
            "recent_period_accuracy": late_accuracy,
        }

    async def _generate_pattern_insights(
        self,
        time_patterns: dict[str, Any],
        frequency_patterns: dict[str, Any],
        error_patterns: dict[str, Any],
        progress_patterns: dict[str, Any],
    ) -> list[str]:
        """生成模式洞察."""
        insights = []

        # 时间模式洞察
        peak_hour = time_patterns.get("peak_hour", 0)
        if 6 <= peak_hour <= 9:
            insights.append("您是早晨学习型，建议保持这个良好习惯")
        elif 19 <= peak_hour <= 22:
            insights.append("您习惯晚间学习，注意保证充足睡眠")

        # 频率模式洞察
        consistency = frequency_patterns.get("study_consistency", 0)
        if consistency > 0.8:
            insights.append("学习频率很稳定，坚持得很好")
        elif consistency < 0.5:
            insights.append("学习频率不够稳定，建议制定固定学习计划")

        # 错误模式洞察
        error_rate = error_patterns.get("error_rate", 0)
        if error_rate > 0.4:
            insights.append("错误率较高，建议放慢节奏，注重理解")
        elif error_rate < 0.2:
            insights.append("错误率很低，可以尝试更有挑战性的题目")

        # 进步模式洞察
        trend = progress_patterns.get("trend", "")
        if trend == "明显进步":
            insights.append("学习效果显著，继续保持当前方法")
        elif trend == "需要关注":
            insights.append("近期表现有所下降，建议调整学习策略")

        return insights

    # ==================== 对比分析方法 ====================

    async def _get_comparison_group_data(self, comparison_group: str) -> dict[str, Any]:
        """获取对比组数据."""
        # 这里应该根据comparison_group查询相应的统计数据
        # 简化处理，返回模拟数据
        return {
            "average_accuracy": 0.72,
            "average_questions_per_day": 15,
            "average_study_days_per_month": 20,
        }

    async def _calculate_ranking(
        self, student_id: int, comparison_data: dict[str, Any]
    ) -> dict[str, Any]:
        """计算排名信息."""
        # 简化处理，返回模拟排名数据
        return {
            "accuracy_percentile": 75,
            "activity_percentile": 80,
            "overall_percentile": 78,
        }

    async def _generate_comparative_insights(
        self,
        student_progress: LearningProgressResponse,
        comparison_data: dict[str, Any],
        ranking_info: dict[str, Any],
    ) -> list[str]:
        """生成对比洞察."""
        insights = []

        # 准确率对比
        if student_progress.overall_metrics.accuracy_rate > comparison_data["average_accuracy"]:
            insights.append("您的准确率高于平均水平，表现优秀")
        else:
            insights.append("准确率低于平均水平，有提升空间")

        # 活跃度对比
        avg_daily = (
            student_progress.overall_metrics.total_questions / 30  # 假设30天分析周期
        )
        if avg_daily > comparison_data["average_questions_per_day"]:
            insights.append("学习活跃度很高，保持这个势头")
        else:
            insights.append("可以适当增加每日练习量")

        return insights

    async def _identify_improvement_opportunities(
        self,
        student_progress: LearningProgressResponse,
        comparison_data: dict[str, Any],
    ) -> list[str]:
        """识别改进机会."""
        opportunities = []

        if student_progress.overall_metrics.accuracy_rate < comparison_data["average_accuracy"]:
            opportunities.append("提升答题准确率至平均水平以上")

        if len(student_progress.time_distribution) < 7:
            opportunities.append("建立连续学习习惯，目标连续学习7天以上")

        return opportunities
