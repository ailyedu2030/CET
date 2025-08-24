"""自适应学习服务 - 难度调整算法和个性化推荐引擎."""

import math
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Float, and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.models.enums import DifficultyLevel, TrainingType
from app.training.models.training_models import (
    Question,
    TrainingRecord,
    TrainingSession,
)
from app.training.schemas.training_schemas import (
    AdaptiveConfigRequest,
    AdaptiveLearningResponse,
    DifficultyAdjustment,
    LearningRecommendation,
)


class AdaptiveLearningService:
    """自适应学习服务 - 个性化学习路径优化."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化自适应学习服务."""
        self.db = db
        self.deepseek_service = DeepSeekService()

    # ==================== 自适应配置管理 ====================

    async def create_adaptive_config(
        self, config_request: AdaptiveConfigRequest
    ) -> AdaptiveLearningResponse:
        """创建自适应学习配置."""
        # 分析学生当前学习状态
        student_performance = await self._analyze_student_performance(
            config_request.student_id, config_request.training_type
        )

        # 计算初始难度调整
        difficulty_adjustment = await self._calculate_difficulty_adjustment(
            config_request, student_performance
        )

        # 生成学习推荐
        recommendations = await self._generate_learning_recommendations(
            config_request, student_performance, difficulty_adjustment
        )

        # 构建下次会话配置
        next_session_config = await self._build_next_session_config(
            config_request, difficulty_adjustment, recommendations
        )

        return AdaptiveLearningResponse(
            student_id=config_request.student_id,
            current_config=config_request,
            difficulty_adjustment=difficulty_adjustment,
            recommendations=recommendations,
            performance_trend=student_performance,
            next_session_config=next_session_config,
        )

    async def update_adaptive_config(
        self,
        student_id: int,
        training_type: TrainingType,
        session_results: dict[str, Any],
    ) -> DifficultyAdjustment | None:
        """根据训练结果更新自适应配置."""
        # 获取最新的训练记录
        recent_performance = await self._get_recent_performance(student_id, training_type, limit=10)

        if not recent_performance:
            return None

        # 计算表现指标
        current_accuracy = sum(1 for r in recent_performance if r.is_correct) / len(
            recent_performance
        )
        average_time = sum(r.time_spent for r in recent_performance) / len(recent_performance)

        # 基于表现调整难度
        current_level = recent_performance[0].question.difficulty_level
        suggested_level = await self._suggest_difficulty_level(
            current_level, current_accuracy, average_time, training_type
        )

        # 计算置信度
        confidence_score = await self._calculate_adjustment_confidence(
            recent_performance, current_accuracy
        )

        return DifficultyAdjustment(
            current_level=current_level.value,
            suggested_level=suggested_level.value,
            adjustment_reason=self._get_adjustment_reason(
                current_level, suggested_level, current_accuracy
            ),
            confidence_score=confidence_score,
            supporting_data={
                "accuracy": current_accuracy,
                "average_time": average_time,
                "sample_size": len(recent_performance),
                "trend": "improving" if current_accuracy > 0.8 else "declining",
            },
        )

    # ==================== 难度调整算法 ====================

    async def _calculate_difficulty_adjustment(
        self, config: AdaptiveConfigRequest, performance: dict[str, Any]
    ) -> DifficultyAdjustment | None:
        """计算难度调整建议."""
        current_accuracy = performance.get("overall_accuracy", 0.0)
        target_accuracy = config.target_accuracy

        # 获取当前难度等级
        current_level = performance.get("current_difficulty", DifficultyLevel.ELEMENTARY)

        # 计算难度调整
        accuracy_diff = current_accuracy - target_accuracy
        sensitivity = config.adjustment_sensitivity

        # 难度调整逻辑
        if abs(accuracy_diff) < 0.05:  # 在目标范围内，不调整
            return None

        # 计算建议调整幅度
        adjustment_magnitude = min(abs(accuracy_diff) * sensitivity * 2, config.max_difficulty_jump)

        if accuracy_diff > 0.1:  # 正确率太高，增加难度
            suggested_level = min(
                DifficultyLevel.ADVANCED,
                DifficultyLevel(current_level.value + int(adjustment_magnitude)),
            )
            reason = f"正确率{current_accuracy:.1%}超过目标{target_accuracy:.1%}，建议提高难度"
        else:  # 正确率太低，降低难度
            suggested_level = max(
                DifficultyLevel.BEGINNER,
                DifficultyLevel(current_level.value - int(adjustment_magnitude)),
            )
            reason = f"正确率{current_accuracy:.1%}低于目标{target_accuracy:.1%}，建议降低难度"

        # 计算置信度
        confidence = self._calculate_confidence_score(performance, accuracy_diff)

        return DifficultyAdjustment(
            current_level=current_level.value,
            suggested_level=suggested_level.value,
            adjustment_reason=reason,
            confidence_score=confidence,
            supporting_data={
                "accuracy_diff": accuracy_diff,
                "sensitivity": sensitivity,
                "performance_data": performance,
            },
        )

    async def _suggest_difficulty_level(
        self,
        current_level: DifficultyLevel,
        accuracy: float,
        average_time: float,
        training_type: TrainingType,
    ) -> DifficultyLevel:
        """基于表现建议难度等级."""
        # 获取训练类型的标准用时
        standard_times = {
            TrainingType.VOCABULARY: 120,  # 2分钟
            TrainingType.LISTENING: 300,  # 5分钟
            TrainingType.READING: 400,  # 6分40秒
            TrainingType.WRITING: 1800,  # 30分钟
            TrainingType.TRANSLATION: 600,  # 10分钟
            TrainingType.COMPREHENSIVE: 300,  # 5分钟
        }

        standard_time = standard_times.get(training_type, 300)
        time_efficiency = standard_time / max(average_time, 1)

        # 综合考虑正确率和时间效率
        performance_score = accuracy * 0.7 + min(time_efficiency, 1.0) * 0.3

        # 根据综合表现调整难度
        if performance_score >= 0.85:  # 表现优秀，提高难度
            return min(DifficultyLevel.ADVANCED, DifficultyLevel(current_level.value + 1))
        elif performance_score >= 0.75:  # 表现良好，保持难度
            return current_level
        elif performance_score >= 0.6:  # 表现一般，略降难度
            return max(DifficultyLevel.BEGINNER, DifficultyLevel(current_level.value - 1))
        else:  # 表现较差，明显降低难度
            return max(DifficultyLevel.BEGINNER, DifficultyLevel(current_level.value - 2))

    def _calculate_confidence_score(
        self, performance: dict[str, Any], accuracy_diff: float
    ) -> float:
        """计算调整置信度."""
        sample_size = performance.get("total_attempts", 1)
        consistency = performance.get("performance_consistency", 0.5)

        # 样本量权重
        sample_weight = min(sample_size / 20, 1.0)  # 20个样本以上置信度满分

        # 准确率差异权重
        diff_weight = min(abs(accuracy_diff) * 2, 1.0)

        # 一致性权重
        consistency_weight = consistency

        # 综合置信度
        confidence = sample_weight * 0.4 + diff_weight * 0.4 + consistency_weight * 0.2

        return float(round(max(0.1, min(0.95, confidence)), 2))

    # ==================== 个性化推荐引擎 ====================

    async def _generate_learning_recommendations(
        self,
        config: AdaptiveConfigRequest,
        performance: dict[str, Any],
        difficulty_adjustment: DifficultyAdjustment | None,
    ) -> list[LearningRecommendation]:
        """生成个性化学习推荐."""
        recommendations: list[LearningRecommendation] = []

        # 分析薄弱知识点
        weak_points = performance.get("weak_knowledge_points", [])
        strong_points = performance.get("strong_knowledge_points", [])

        # 推荐1：针对薄弱知识点的强化训练
        if weak_points:
            recommendations.append(
                LearningRecommendation(
                    training_type=config.training_type,
                    difficulty_level=(
                        DifficultyLevel(difficulty_adjustment.suggested_level)
                        if difficulty_adjustment
                        else DifficultyLevel.ELEMENTARY
                    ),
                    knowledge_points=weak_points[:3],  # 最多3个薄弱点
                    question_count=max(10, len(weak_points) * 3),
                    time_allocation=20,
                    priority_score=0.9,
                    reason="针对薄弱知识点进行专项强化训练",
                    expected_improvement={"accuracy": 0.15, "confidence": 0.2},
                )
            )

        # 推荐2：巩固优势知识点
        if strong_points:
            recommendations.append(
                LearningRecommendation(
                    training_type=config.training_type,
                    difficulty_level=DifficultyLevel.UPPER_INTERMEDIATE,
                    knowledge_points=strong_points[:2],
                    question_count=8,
                    time_allocation=15,
                    priority_score=0.6,
                    reason="巩固优势知识点，保持学习自信",
                    expected_improvement={"mastery": 0.1, "confidence": 0.15},
                )
            )

        # 推荐3：跨模块综合训练
        if performance.get("overall_accuracy", 0) > 0.7:
            recommendations.append(
                LearningRecommendation(
                    training_type=TrainingType.COMPREHENSIVE,
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    knowledge_points=[],
                    question_count=15,
                    time_allocation=25,
                    priority_score=0.7,
                    reason="进行跨模块综合训练，提升整体水平",
                    expected_improvement={"overall": 0.1, "versatility": 0.2},
                )
            )

        # 推荐4：基于学习偏好的推荐
        preferred_types = await self._identify_preferred_training_types(config.student_id)
        for training_type in preferred_types[:2]:
            if training_type != config.training_type:
                recommendations.append(
                    LearningRecommendation(
                        training_type=training_type,
                        difficulty_level=DifficultyLevel.INTERMEDIATE,
                        knowledge_points=[],
                        question_count=10,
                        time_allocation=15,
                        priority_score=0.5,
                        reason=f"基于学习偏好推荐{training_type.value}训练",
                        expected_improvement={"interest": 0.2, "engagement": 0.15},
                    )
                )

        # 按优先级排序
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)

        return recommendations[:4]  # 最多返回4个推荐

    async def _identify_preferred_training_types(self, student_id: int) -> list[TrainingType]:
        """识别学生偏好的训练类型."""
        # 统计各训练类型的参与度和表现
        stmt = (
            select(
                TrainingSession.session_type,
                func.count(TrainingSession.id).label("session_count"),
                func.avg(TrainingSession.total_score).label("avg_score"),
                func.avg(
                    func.cast(TrainingSession.correct_answers, Float)
                    / func.cast(TrainingSession.total_questions, Float)
                ).label("avg_accuracy"),
            )
            .where(
                and_(
                    TrainingSession.student_id == student_id,
                    TrainingSession.status == "completed",
                    TrainingSession.created_at >= datetime.utcnow() - timedelta(days=30),
                )
            )
            .group_by(TrainingSession.session_type)
            .order_by(desc("avg_score"))
        )

        result = await self.db.execute(stmt)
        preferences = result.all()

        # 基于参与度和表现计算偏好分数
        preferred_types: list[tuple[TrainingType, float]] = []

        for pref in preferences:
            training_type = pref.session_type
            session_count = pref.session_count
            avg_accuracy = pref.avg_accuracy or 0

            # 综合偏好分数：参与度40% + 表现60%
            preference_score = min(session_count / 10, 1.0) * 0.4 + (avg_accuracy * 0.6)
            preferred_types.append((training_type, preference_score))

        # 按偏好分数排序
        preferred_types.sort(key=lambda x: x[1], reverse=True)

        return [t[0] for t in preferred_types]

    # ==================== 学习数据分析 ====================

    async def _analyze_student_performance(
        self, student_id: int, training_type: TrainingType | None = None
    ) -> dict[str, Any]:
        """分析学生学习表现."""
        # 构建基础查询
        base_stmt = select(TrainingRecord).where(
            and_(
                TrainingRecord.student_id == student_id,
                TrainingRecord.created_at >= datetime.utcnow() - timedelta(days=30),
            )
        )

        if training_type:
            # 通过关联查询筛选训练类型
            base_stmt = base_stmt.join(Question).where(Question.training_type == training_type)

        result = await self.db.execute(base_stmt.order_by(desc(TrainingRecord.created_at)))
        records = result.scalars().all()

        if not records:
            return {"overall_accuracy": 0.0, "total_attempts": 0}

        # 基础统计
        total_attempts = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        overall_accuracy = correct_count / total_attempts

        # 转换为list类型
        records_list = list(records)

        # 知识点分析
        knowledge_point_stats = await self._analyze_knowledge_points(records_list)

        # 时间趋势分析
        time_trend = await self._analyze_time_trend(records_list)

        # 难度分布分析
        difficulty_stats = await self._analyze_difficulty_distribution(records_list)

        # 一致性分析
        consistency_score = await self._calculate_performance_consistency(records_list)

        return {
            "total_attempts": total_attempts,
            "overall_accuracy": overall_accuracy,
            "correct_count": correct_count,
            "current_difficulty": difficulty_stats.get("most_common", DifficultyLevel.ELEMENTARY),
            "weak_knowledge_points": knowledge_point_stats["weak_points"],
            "strong_knowledge_points": knowledge_point_stats["strong_points"],
            "time_trend": time_trend,
            "difficulty_distribution": difficulty_stats,
            "performance_consistency": consistency_score,
        }

    async def _analyze_knowledge_points(
        self, records: list[TrainingRecord]
    ) -> dict[str, list[str]]:
        """分析知识点掌握情况."""
        knowledge_stats: dict[str, dict[str, int]] = {}

        # 统计每个知识点的对错情况
        for record in records:
            # 获取题目的知识点
            stmt = select(Question.knowledge_points).where(Question.id == record.question_id)
            result = await self.db.execute(stmt)
            knowledge_points = result.scalar_one_or_none() or []

            for point in knowledge_points:
                if point not in knowledge_stats:
                    knowledge_stats[point] = {"correct": 0, "total": 0}

                knowledge_stats[point]["total"] += 1
                if record.is_correct:
                    knowledge_stats[point]["correct"] += 1

        # 计算正确率并分类
        weak_points: list[str] = []
        strong_points: list[str] = []

        for point, stats in knowledge_stats.items():
            if stats["total"] >= 3:  # 至少做过3道题才有统计意义
                accuracy = stats["correct"] / stats["total"]
                if accuracy < 0.6:
                    weak_points.append(point)
                elif accuracy > 0.8:
                    strong_points.append(point)

        return {"weak_points": weak_points, "strong_points": strong_points}

    async def _analyze_time_trend(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析时间趋势."""
        if len(records) < 5:
            return {"trend": "insufficient_data"}

        # 按时间排序，计算正确率趋势
        sorted_records = sorted(records, key=lambda x: x.created_at)
        window_size = max(5, len(sorted_records) // 4)

        # 计算滑动窗口正确率
        accuracies: list[float] = []
        for i in range(len(sorted_records) - window_size + 1):
            window = sorted_records[i : i + window_size]
            accuracy = sum(1 for r in window if r.is_correct) / len(window)
            accuracies.append(accuracy)

        # 计算趋势
        if len(accuracies) >= 2:
            early_avg = sum(accuracies[: len(accuracies) // 2]) / (len(accuracies) // 2)
            recent_avg = sum(accuracies[len(accuracies) // 2 :]) / (
                len(accuracies) - len(accuracies) // 2
            )

            trend = "improving" if recent_avg > early_avg + 0.05 else "stable"
            if recent_avg < early_avg - 0.05:
                trend = "declining"
        else:
            trend = "stable"

        return {"trend": trend, "accuracies": accuracies}

    async def _analyze_difficulty_distribution(
        self, records: list[TrainingRecord]
    ) -> dict[str, Any]:
        """分析难度分布."""
        difficulty_stats: dict[DifficultyLevel, dict[str, int]] = {}

        for record in records:
            # 获取题目难度
            stmt = select(Question.difficulty_level).where(Question.id == record.question_id)
            result = await self.db.execute(stmt)
            difficulty = result.scalar_one_or_none() or DifficultyLevel.ELEMENTARY

            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"correct": 0, "total": 0}

            difficulty_stats[difficulty]["total"] += 1
            if record.is_correct:
                difficulty_stats[difficulty]["correct"] += 1

        # 找出最常见的难度等级
        most_common = max(
            difficulty_stats.keys(),
            key=lambda k: difficulty_stats[k]["total"],
            default=DifficultyLevel.ELEMENTARY,
        )

        return {"distribution": difficulty_stats, "most_common": most_common}

    async def _calculate_performance_consistency(self, records: list[TrainingRecord]) -> float:
        """计算表现一致性."""
        if len(records) < 5:
            return 0.5

        # 计算每5道题的正确率
        chunk_size = 5
        chunk_accuracies: list[float] = []

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            accuracy = sum(1 for r in chunk if r.is_correct) / len(chunk)
            chunk_accuracies.append(accuracy)

        # 计算标准差，标准差越小一致性越高
        if len(chunk_accuracies) <= 1:
            return 0.8

        mean_accuracy = sum(chunk_accuracies) / len(chunk_accuracies)
        variance = sum((a - mean_accuracy) ** 2 for a in chunk_accuracies) / len(chunk_accuracies)
        std_dev = math.sqrt(variance)

        # 将标准差转换为一致性分数（0-1）
        consistency = max(0.1, 1.0 - std_dev * 2)

        return round(consistency, 2)

    # ==================== 辅助方法 ====================

    async def _get_recent_performance(
        self, student_id: int, training_type: TrainingType, limit: int = 10
    ) -> list[TrainingRecord]:
        """获取最近的训练表现."""
        stmt = (
            select(TrainingRecord)
            .join(Question)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    Question.training_type == training_type,
                )
            )
            .order_by(desc(TrainingRecord.created_at))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _calculate_adjustment_confidence(
        self, records: list[TrainingRecord], accuracy: float
    ) -> float:
        """计算调整置信度."""
        sample_size = len(records)
        time_span_hours = (
            (records[0].created_at - records[-1].created_at).total_seconds() / 3600
            if len(records) > 1
            else 24
        )

        # 样本量权重
        sample_weight = min(sample_size / 15, 1.0)

        # 时间跨度权重（太集中或太分散都降低置信度）
        optimal_span = 72  # 3天
        time_weight = 1.0 - abs(time_span_hours - optimal_span) / optimal_span
        time_weight = max(0.3, min(1.0, time_weight))

        # 准确率稳定性
        accuracies = [1.0 if r.is_correct else 0.0 for r in records]
        stability = 1.0 - (max(accuracies) - min(accuracies)) if accuracies else 0.5

        confidence = sample_weight * 0.4 + time_weight * 0.3 + stability * 0.3

        return float(round(max(0.2, min(0.9, confidence)), 2))

    def _get_adjustment_reason(
        self,
        current_level: DifficultyLevel,
        suggested_level: DifficultyLevel,
        accuracy: float,
    ) -> str:
        """获取难度调整原因."""
        if suggested_level.value > current_level.value:
            return f"当前正确率{accuracy:.1%}表现优秀，建议提高至{suggested_level.name}难度"
        elif suggested_level.value < current_level.value:
            return f"当前正确率{accuracy:.1%}需要强化，建议降至{suggested_level.name}难度"
        else:
            return f"当前{current_level.name}难度适合，建议保持"

    async def _build_next_session_config(
        self,
        config: AdaptiveConfigRequest,
        difficulty_adjustment: DifficultyAdjustment | None,
        recommendations: list[LearningRecommendation],
    ) -> dict[str, Any]:
        """构建下次会话配置."""
        # 基础配置
        next_config: dict[str, Any] = {
            "training_type": config.training_type.value,
            "question_count": 15,  # 默认题目数
            "time_limit": 30,  # 默认30分钟
            "auto_adaptive": True,
        }

        # 应用难度调整
        if difficulty_adjustment:
            next_config["difficulty_level"] = difficulty_adjustment.suggested_level
        else:
            next_config["difficulty_level"] = DifficultyLevel.ELEMENTARY.value

        # 应用推荐的知识点
        if recommendations:
            primary_rec = recommendations[0]  # 优先级最高的推荐
            next_config.update(
                {
                    "knowledge_points": primary_rec.knowledge_points,
                    "question_count": primary_rec.question_count,
                    "time_limit": primary_rec.time_allocation,
                    "focus_reason": primary_rec.reason,
                }
            )

        return next_config
