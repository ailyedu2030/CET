"""精确自适应算法服务 - 🔥需求21第二阶段核心实现.

基于近10次正确率的精确调整算法：
- >90%升级规则：当学生近10次答题正确率超过90%时，自动提升难度等级
- <60%降级规则：当学生近10次答题正确率低于60%时，自动降低难度等级
- 自适应算法精度>90%验证系统
- 个性化程度>80%量化机制
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import DifficultyLevel, TrainingType
from app.training.models.training_models import (
    IntelligentTrainingLoop,
    TrainingRecord,
    TrainingSession,
)

logger = logging.getLogger(__name__)


class PreciseAdaptiveService:
    """精确自适应算法服务 - 基于近10次正确率的精确调整."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

        # 精确调整算法配置
        self.precise_config = {
            "recent_attempts_count": 10,  # 近10次答题
            "upgrade_threshold": 0.90,  # >90%升级
            "downgrade_threshold": 0.60,  # <60%降级
            "algorithm_precision_target": 0.90,  # 算法精度>90%
            "personalization_target": 0.80,  # 个性化程度>80%
            "min_attempts_for_adjustment": 5,  # 最少答题次数
        }

    async def execute_precise_adjustment(
        self, student_id: int, training_type: TrainingType
    ) -> dict[str, Any]:
        """执行基于近10次正确率的精确调整算法."""
        try:
            logger.info(f"开始执行精确自适应调整: 学生{student_id}, 训练类型{training_type}")

            # 第一步：获取近10次答题记录
            recent_records = await self._get_recent_training_records(
                student_id,
                training_type,
                int(self.precise_config["recent_attempts_count"]),
            )

            if len(recent_records) < self.precise_config["min_attempts_for_adjustment"]:
                return {
                    "adjustment_made": False,
                    "reason": f"答题次数不足{self.precise_config['min_attempts_for_adjustment']}次，无法进行精确调整",
                    "current_attempts": len(recent_records),
                    "algorithm_precision": 0.0,
                    "personalization_score": 0.0,
                }

            # 第二步：计算近10次正确率
            accuracy_analysis = self._calculate_recent_accuracy(recent_records)

            # 第三步：执行精确调整决策
            adjustment_decision = await self._make_precise_adjustment_decision(
                student_id, training_type, accuracy_analysis
            )

            # 第四步：验证算法精度
            algorithm_precision = await self._verify_algorithm_precision(
                student_id, training_type, adjustment_decision
            )

            # 第五步：计算个性化程度
            personalization_score = await self._calculate_personalization_score(
                student_id, training_type, adjustment_decision
            )

            # 第六步：应用调整（如果需要）
            application_result = await self._apply_precise_adjustment(
                student_id, training_type, adjustment_decision
            )

            return {
                "adjustment_made": adjustment_decision["should_adjust"],
                "adjustment_type": adjustment_decision.get("adjustment_type"),
                "current_accuracy": accuracy_analysis["accuracy"],
                "recent_attempts": len(recent_records),
                "algorithm_precision": algorithm_precision,
                "personalization_score": personalization_score,
                "meets_precision_target": algorithm_precision
                >= self.precise_config["algorithm_precision_target"],
                "meets_personalization_target": personalization_score
                >= self.precise_config["personalization_target"],
                "adjustment_details": adjustment_decision,
                "application_result": application_result,
                "execution_time": datetime.now(),
            }

        except Exception as e:
            logger.error(f"精确自适应调整执行失败: {str(e)}")
            raise

    async def _get_recent_training_records(
        self, student_id: int, training_type: TrainingType, count: int
    ) -> list[TrainingRecord]:
        """获取近N次训练记录."""
        stmt = (
            select(TrainingRecord)
            .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
            .where(
                and_(
                    TrainingSession.student_id == student_id,
                    TrainingSession.session_type == training_type,
                )
            )
            .order_by(desc(TrainingRecord.created_at))
            .limit(count)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _calculate_recent_accuracy(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """计算近期答题正确率分析."""
        if not records:
            return {"accuracy": 0.0, "total_attempts": 0, "correct_attempts": 0}

        correct_count = sum(1 for record in records if record.is_correct)
        total_count = len(records)
        accuracy = correct_count / total_count

        # 分析答题模式
        recent_5 = records[:5] if len(records) >= 5 else records
        recent_5_accuracy = sum(1 for r in recent_5 if r.is_correct) / len(recent_5)

        return {
            "accuracy": accuracy,
            "total_attempts": total_count,
            "correct_attempts": correct_count,
            "recent_5_accuracy": recent_5_accuracy,
            "accuracy_trend": ("improving" if recent_5_accuracy > accuracy else "declining"),
            "consistency_score": self._calculate_consistency_score(records),
        }

    def _calculate_consistency_score(self, records: list[TrainingRecord]) -> float:
        """计算答题一致性分数."""
        if len(records) < 5:
            return 0.5

        # 计算每5题的正确率方差
        chunk_size = 5
        chunk_accuracies = []

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            if len(chunk) >= 3:  # 至少3题才计算
                accuracy = sum(1 for r in chunk if r.is_correct) / len(chunk)
                chunk_accuracies.append(accuracy)

        if len(chunk_accuracies) < 2:
            return 0.5

        # 计算方差，方差越小一致性越高
        mean_accuracy = sum(chunk_accuracies) / len(chunk_accuracies)
        variance = sum((acc - mean_accuracy) ** 2 for acc in chunk_accuracies) / len(
            chunk_accuracies
        )

        # 将方差转换为一致性分数（0-1）
        consistency = max(0.0, 1.0 - variance * 4)  # 方差*4作为惩罚因子
        return min(1.0, consistency)

    async def _make_precise_adjustment_decision(
        self,
        student_id: int,
        training_type: TrainingType,
        accuracy_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """基于近10次正确率做出精确调整决策."""
        accuracy = accuracy_analysis["accuracy"]
        upgrade_threshold = self.precise_config["upgrade_threshold"]
        downgrade_threshold = self.precise_config["downgrade_threshold"]

        # 获取当前难度等级
        current_difficulty = await self._get_current_difficulty(student_id, training_type)

        decision = {
            "should_adjust": False,
            "adjustment_type": None,
            "current_difficulty": current_difficulty,
            "target_difficulty": current_difficulty,
            "confidence_score": 0.0,
            "decision_reason": "",
        }

        # 精确调整逻辑
        if accuracy > upgrade_threshold:
            # >90%升级规则
            if current_difficulty < DifficultyLevel.ADVANCED:
                decision.update(
                    {
                        "should_adjust": True,
                        "adjustment_type": "upgrade",
                        "target_difficulty": DifficultyLevel(current_difficulty.value + 1),
                        "confidence_score": min(1.0, (accuracy - upgrade_threshold) * 10),
                        "decision_reason": f"近10次正确率{accuracy:.1%}超过{upgrade_threshold:.0%}，执行升级",
                    }
                )
        elif accuracy < downgrade_threshold:
            # <60%降级规则
            if current_difficulty > DifficultyLevel.BEGINNER:
                decision.update(
                    {
                        "should_adjust": True,
                        "adjustment_type": "downgrade",
                        "target_difficulty": DifficultyLevel(current_difficulty.value - 1),
                        "confidence_score": min(1.0, (downgrade_threshold - accuracy) * 10),
                        "decision_reason": f"近10次正确率{accuracy:.1%}低于{downgrade_threshold:.0%}，执行降级",
                    }
                )
        else:
            # 60%-90%之间，保持当前难度
            decision.update(
                {
                    "decision_reason": f"近10次正确率{accuracy:.1%}在合理范围内，保持当前难度",
                    "confidence_score": 1.0 - abs(accuracy - 0.75) * 2,  # 75%为最佳点
                }
            )

        return decision

    async def _get_current_difficulty(
        self, student_id: int, training_type: TrainingType
    ) -> DifficultyLevel:
        """获取学生当前训练类型的难度等级."""
        # 从最近的训练会话获取难度等级
        stmt = (
            select(TrainingSession.difficulty_level)
            .where(
                and_(
                    TrainingSession.student_id == student_id,
                    TrainingSession.session_type == training_type,
                )
            )
            .order_by(desc(TrainingSession.created_at))
            .limit(1)
        )

        result = await self.db.execute(stmt)
        difficulty = result.scalar_one_or_none()

        return difficulty if difficulty else DifficultyLevel.ELEMENTARY

    async def _verify_algorithm_precision(
        self,
        student_id: int,
        training_type: TrainingType,
        adjustment_decision: dict[str, Any],
    ) -> float:
        """验证自适应算法精度>90%."""
        try:
            # 获取历史调整记录进行精度验证
            historical_adjustments = await self._get_historical_adjustments(
                student_id, training_type, days=30
            )

            if len(historical_adjustments) < 3:
                return 0.5  # 数据不足，返回中等精度

            correct_predictions = 0
            total_predictions = len(historical_adjustments)

            for adjustment in historical_adjustments:
                # 验证调整是否正确
                was_correct = await self._validate_adjustment_correctness(
                    student_id, training_type, adjustment
                )
                if was_correct:
                    correct_predictions += 1

            precision = correct_predictions / total_predictions
            logger.info(
                f"算法精度验证: {precision:.2%} ({correct_predictions}/{total_predictions})"
            )

            return precision

        except Exception as e:
            logger.error(f"算法精度验证失败: {str(e)}")
            return 0.0

    async def _calculate_personalization_score(
        self,
        student_id: int,
        training_type: TrainingType,
        adjustment_decision: dict[str, Any],
    ) -> float:
        """计算个性化程度>80%量化机制."""
        try:
            # 获取学生个人学习特征
            learning_profile = await self._build_learning_profile(student_id, training_type)

            # 计算个性化匹配度
            personalization_factors = {
                "learning_pace_match": self._calculate_pace_match(
                    learning_profile, adjustment_decision
                ),
                "difficulty_preference_match": self._calculate_difficulty_preference_match(
                    learning_profile, adjustment_decision
                ),
                "knowledge_gap_targeting": self._calculate_knowledge_gap_targeting(
                    learning_profile, adjustment_decision
                ),
                "learning_style_alignment": self._calculate_learning_style_alignment(
                    learning_profile, adjustment_decision
                ),
            }

            # 加权计算总个性化分数
            weights = {
                "learning_pace_match": 0.3,
                "difficulty_preference_match": 0.25,
                "knowledge_gap_targeting": 0.25,
                "learning_style_alignment": 0.2,
            }

            personalization_score = sum(
                personalization_factors[factor] * weights[factor]
                for factor in personalization_factors
            )

            logger.info(f"个性化程度计算: {personalization_score:.2%}")
            return personalization_score

        except Exception as e:
            logger.error(f"个性化程度计算失败: {str(e)}")
            return 0.0

    async def _apply_precise_adjustment(
        self,
        student_id: int,
        training_type: TrainingType,
        adjustment_decision: dict[str, Any],
    ) -> dict[str, Any]:
        """应用精确调整决策."""
        if not adjustment_decision["should_adjust"]:
            return {
                "applied": False,
                "reason": "无需调整",
                "current_difficulty": adjustment_decision["current_difficulty"],
            }

        try:
            # 记录调整决策到智能训练闭环
            await self._record_adjustment_to_loop(student_id, training_type, adjustment_decision)

            return {
                "applied": True,
                "adjustment_type": adjustment_decision["adjustment_type"],
                "from_difficulty": adjustment_decision["current_difficulty"],
                "to_difficulty": adjustment_decision["target_difficulty"],
                "confidence_score": adjustment_decision["confidence_score"],
                "application_time": datetime.now(),
            }

        except Exception as e:
            logger.error(f"应用精确调整失败: {str(e)}")
            return {
                "applied": False,
                "error": str(e),
                "current_difficulty": adjustment_decision["current_difficulty"],
            }

    async def _get_historical_adjustments(
        self, student_id: int, training_type: TrainingType, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取历史调整记录."""
        cutoff_date = datetime.now() - timedelta(days=days)

        stmt = (
            select(IntelligentTrainingLoop)
            .where(
                and_(
                    IntelligentTrainingLoop.student_id == student_id,
                    IntelligentTrainingLoop.training_type == training_type,
                    IntelligentTrainingLoop.execution_time >= cutoff_date,
                )
            )
            .order_by(desc(IntelligentTrainingLoop.execution_time))
        )

        result = await self.db.execute(stmt)
        loops = result.scalars().all()

        adjustments = []
        for loop in loops:
            if loop.strategy_adjustment_result:
                adjustment_data = loop.strategy_adjustment_result
                if adjustment_data.get("adjustment_success"):
                    adjustments.append(
                        {
                            "execution_time": loop.execution_time,
                            "adjustment_data": adjustment_data,
                            "loop_success": loop.loop_success,
                            "improvement_rate": loop.improvement_rate,
                        }
                    )

        return adjustments

    async def _validate_adjustment_correctness(
        self, student_id: int, training_type: TrainingType, adjustment: dict[str, Any]
    ) -> bool:
        """验证调整决策的正确性."""
        try:
            # 获取调整后的表现数据
            adjustment_time = adjustment["execution_time"]
            post_adjustment_records = await self._get_records_after_time(
                student_id, training_type, adjustment_time, days=7
            )

            if len(post_adjustment_records) < 5:
                return False  # 数据不足，无法验证

            # 计算调整后的表现
            post_accuracy = sum(1 for r in post_adjustment_records if r.is_correct) / len(
                post_adjustment_records
            )

            # 验证调整是否带来了预期效果
            improvement_rate = adjustment.get("improvement_rate", 0.0)
            expected_improvement = improvement_rate > 0.05  # 期望至少5%的改进

            # 验证准确率是否在合理范围内
            reasonable_accuracy = 0.6 <= post_accuracy <= 0.9

            return expected_improvement and reasonable_accuracy

        except Exception as e:
            logger.error(f"验证调整正确性失败: {str(e)}")
            return False

    async def _get_records_after_time(
        self,
        student_id: int,
        training_type: TrainingType,
        after_time: datetime,
        days: int = 7,
    ) -> list[TrainingRecord]:
        """获取指定时间后的训练记录."""
        end_time = after_time + timedelta(days=days)

        stmt = (
            select(TrainingRecord)
            .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
            .where(
                and_(
                    TrainingSession.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingRecord.created_at >= after_time,
                    TrainingRecord.created_at <= end_time,
                )
            )
            .order_by(TrainingRecord.created_at)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _build_learning_profile(
        self, student_id: int, training_type: TrainingType
    ) -> dict[str, Any]:
        """构建学生个人学习特征档案."""
        # 获取最近30天的训练记录
        recent_records = await self._get_recent_training_records(student_id, training_type, 50)

        if not recent_records:
            return {
                "learning_pace": "unknown",
                "difficulty_preference": "unknown",
                "knowledge_gaps": [],
                "learning_style": "unknown",
                "consistency_level": 0.5,
            }

        # 分析学习节奏
        learning_pace = self._analyze_learning_pace(recent_records)

        # 分析难度偏好
        difficulty_preference = await self._analyze_difficulty_preference(student_id, training_type)

        # 识别知识薄弱点
        knowledge_gaps = self._identify_knowledge_gaps(recent_records)

        # 分析学习风格
        learning_style = self._analyze_learning_style(recent_records)

        # 计算一致性水平
        consistency_level = self._calculate_consistency_score(recent_records)

        return {
            "learning_pace": learning_pace,
            "difficulty_preference": difficulty_preference,
            "knowledge_gaps": knowledge_gaps,
            "learning_style": learning_style,
            "consistency_level": consistency_level,
            "profile_confidence": min(1.0, len(recent_records) / 30),  # 数据越多置信度越高
        }

    def _analyze_learning_pace(self, records: list[TrainingRecord]) -> str:
        """分析学习节奏."""
        if len(records) < 10:
            return "unknown"

        # 计算平均答题时间
        avg_time = sum(r.time_spent for r in records if r.time_spent) / len(records)

        # 分析时间趋势
        recent_10 = records[:10]
        early_10 = records[-10:] if len(records) >= 20 else records[10:]

        if early_10:
            recent_avg = sum(r.time_spent for r in recent_10 if r.time_spent) / len(recent_10)
            early_avg = sum(r.time_spent for r in early_10 if r.time_spent) / len(early_10)

            if recent_avg < early_avg * 0.8:
                return "accelerating"  # 越来越快
            elif recent_avg > early_avg * 1.2:
                return "decelerating"  # 越来越慢

        # 基于绝对时间判断
        if avg_time < 60:
            return "fast"
        elif avg_time > 180:
            return "slow"
        else:
            return "moderate"

    async def _analyze_difficulty_preference(
        self, student_id: int, training_type: TrainingType
    ) -> str:
        """分析难度偏好."""
        # 获取不同难度下的表现
        difficulty_performance = {}

        for difficulty in DifficultyLevel:
            stmt = (
                select(TrainingRecord)
                .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
                .where(
                    and_(
                        TrainingSession.student_id == student_id,
                        TrainingSession.session_type == training_type,
                        TrainingSession.difficulty_level == difficulty,
                    )
                )
                .limit(20)
            )

            result = await self.db.execute(stmt)
            records = list(result.scalars().all())

            if len(records) >= 5:
                accuracy = sum(1 for r in records if r.is_correct) / len(records)
                avg_time = sum(r.time_spent for r in records if r.time_spent) / len(records)

                # 综合表现分数：准确率70% + 时间效率30%
                time_efficiency = min(1.0, 120 / max(avg_time, 60))  # 2分钟为标准
                performance_score = accuracy * 0.7 + time_efficiency * 0.3

                difficulty_performance[difficulty] = {
                    "accuracy": accuracy,
                    "performance_score": performance_score,
                    "sample_size": len(records),
                }

        if not difficulty_performance:
            return "unknown"

        # 找到表现最好的难度
        best_difficulty = max(
            difficulty_performance.keys(),
            key=lambda d: difficulty_performance[d]["performance_score"],
        )

        return best_difficulty.name.lower()

    def _identify_knowledge_gaps(self, records: list[TrainingRecord]) -> list[str]:
        """识别知识薄弱点."""
        knowledge_stats = {}

        for record in records:
            if hasattr(record, "knowledge_points") and record.knowledge_points:
                for point in record.knowledge_points:
                    if point not in knowledge_stats:
                        knowledge_stats[point] = {"total": 0, "correct": 0}

                    knowledge_stats[point]["total"] += 1
                    if record.is_correct:
                        knowledge_stats[point]["correct"] += 1

        # 识别薄弱点（正确率<70%且至少做过5题）
        weak_points = []
        for point, stats in knowledge_stats.items():
            if stats["total"] >= 5:
                accuracy = stats["correct"] / stats["total"]
                if accuracy < 0.7:
                    weak_points.append(point)

        return weak_points

    def _analyze_learning_style(self, records: list[TrainingRecord]) -> str:
        """分析学习风格."""
        if len(records) < 10:
            return "unknown"

        # 分析答题模式
        correct_streak_lengths = []
        current_streak = 0

        for record in records:
            if record.is_correct:
                current_streak += 1
            else:
                if current_streak > 0:
                    correct_streak_lengths.append(current_streak)
                current_streak = 0

        if current_streak > 0:
            correct_streak_lengths.append(current_streak)

        if not correct_streak_lengths:
            return "struggling"

        avg_streak = sum(correct_streak_lengths) / len(correct_streak_lengths)
        max_streak = max(correct_streak_lengths)

        # 基于连续正确模式判断学习风格
        if avg_streak >= 5 and max_streak >= 8:
            return "consistent_high_performer"
        elif avg_streak >= 3 and max_streak >= 5:
            return "steady_learner"
        elif max_streak >= 6 and avg_streak < 3:
            return "burst_learner"  # 爆发式学习
        else:
            return "gradual_learner"

    def _calculate_pace_match(
        self, learning_profile: dict[str, Any], adjustment_decision: dict[str, Any]
    ) -> float:
        """计算学习节奏匹配度."""
        pace = learning_profile.get("learning_pace", "unknown")
        adjustment_type = adjustment_decision.get("adjustment_type")

        if pace == "unknown":
            return 0.5

        # 快节奏学习者适合更频繁的难度提升
        if pace == "fast" and adjustment_type == "upgrade":
            return 0.9
        elif pace == "fast" and adjustment_type == "downgrade":
            return 0.3

        # 慢节奏学习者需要更稳定的难度
        elif pace == "slow" and adjustment_type is None:
            return 0.8
        elif pace == "slow" and adjustment_type == "upgrade":
            return 0.4

        # 中等节奏适合标准调整
        elif pace == "moderate":
            return 0.7

        return 0.5

    def _calculate_difficulty_preference_match(
        self, learning_profile: dict[str, Any], adjustment_decision: dict[str, Any]
    ) -> float:
        """计算难度偏好匹配度."""
        preference = learning_profile.get("difficulty_preference", "unknown")
        target_difficulty = adjustment_decision.get("target_difficulty")

        if preference == "unknown" or not target_difficulty:
            return 0.5

        # 偏好匹配度计算
        preference_level_map = {
            "beginner": DifficultyLevel.BEGINNER,
            "elementary": DifficultyLevel.ELEMENTARY,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "advanced": DifficultyLevel.ADVANCED,
        }

        preferred_level = preference_level_map.get(preference)
        if not preferred_level:
            return 0.5

        # 计算难度差距
        level_diff = abs(target_difficulty.value - preferred_level.value)

        # 差距越小匹配度越高
        if level_diff == 0:
            return 1.0
        elif level_diff == 1:
            return 0.7
        elif level_diff == 2:
            return 0.4
        else:
            return 0.2

    def _calculate_knowledge_gap_targeting(
        self, learning_profile: dict[str, Any], adjustment_decision: dict[str, Any]
    ) -> float:
        """计算知识薄弱点针对性."""
        knowledge_gaps = learning_profile.get("knowledge_gaps", [])

        if not knowledge_gaps:
            return 0.8  # 没有明显薄弱点，调整合理

        # 如果有薄弱点但选择升级，针对性较低
        if adjustment_decision.get("adjustment_type") == "upgrade":
            return 0.3

        # 如果有薄弱点且选择降级或保持，针对性较高
        elif adjustment_decision.get("adjustment_type") == "downgrade":
            return 0.9
        else:
            return 0.7

    def _calculate_learning_style_alignment(
        self, learning_profile: dict[str, Any], adjustment_decision: dict[str, Any]
    ) -> float:
        """计算学习风格对齐度."""
        style = learning_profile.get("learning_style", "unknown")
        adjustment_type = adjustment_decision.get("adjustment_type")

        if style == "unknown":
            return 0.5

        # 不同学习风格的调整偏好
        style_preferences = {
            "consistent_high_performer": {"upgrade": 0.9, "downgrade": 0.2, None: 0.6},
            "steady_learner": {"upgrade": 0.7, "downgrade": 0.7, None: 0.8},
            "burst_learner": {"upgrade": 0.8, "downgrade": 0.5, None: 0.6},
            "gradual_learner": {"upgrade": 0.5, "downgrade": 0.8, None: 0.7},
            "struggling": {"upgrade": 0.2, "downgrade": 0.9, None: 0.7},
        }

        preferences = style_preferences.get(style, {})
        return preferences.get(adjustment_type, 0.5)

    async def _record_adjustment_to_loop(
        self,
        student_id: int,
        training_type: TrainingType,
        adjustment_decision: dict[str, Any],
    ) -> None:
        """记录调整决策到智能训练闭环."""
        # 这里可以与智能训练闭环服务集成
        # 暂时记录日志
        logger.info(
            f"精确调整决策记录: 学生{student_id}, 训练类型{training_type}, "
            f"调整类型{adjustment_decision.get('adjustment_type')}, "
            f"置信度{adjustment_decision.get('confidence_score', 0):.2f}"
        )
