"""智能训练闭环辅助方法 - 🔥需求21支持模块."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import TrainingType
from app.training.models.training_models import TrainingRecord, TrainingSession

logger = logging.getLogger(__name__)


class IntelligentTrainingLoopHelpers:
    """智能训练闭环辅助方法类."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化辅助方法类."""
        self.db = db

    # ==================== AI分析验证方法 ====================

    async def verify_knowledge_analysis(
        self, knowledge_mastery: dict[str, Any], training_records: list[dict[str, Any]]
    ) -> float:
        """验证知识点分析准确性."""
        if not training_records or not knowledge_mastery:
            return 0.5

        # 计算实际知识点掌握情况
        actual_mastery = {}
        for record in training_records:
            for kp in record["knowledge_points"]:
                if kp not in actual_mastery:
                    actual_mastery[kp] = {"correct": 0, "total": 0}
                actual_mastery[kp]["total"] += 1
                if record["is_correct"]:
                    actual_mastery[kp]["correct"] += 1

        # 计算准确率
        for kp in actual_mastery:
            actual_mastery[kp]["accuracy"] = (
                actual_mastery[kp]["correct"] / actual_mastery[kp]["total"]
                if actual_mastery[kp]["total"] > 0
                else 0
            )

        # 验证AI分析的准确性
        strong_points = knowledge_mastery.get("强项知识点", [])
        weak_points = knowledge_mastery.get("薄弱知识点", [])

        correct_predictions = 0
        total_predictions = len(strong_points) + len(weak_points)

        if total_predictions == 0:
            return 0.5

        # 验证强项知识点
        for kp in strong_points:
            if kp in actual_mastery and actual_mastery[kp]["accuracy"] >= 0.8:
                correct_predictions += 1

        # 验证薄弱知识点
        for kp in weak_points:
            if kp in actual_mastery and actual_mastery[kp]["accuracy"] <= 0.6:
                correct_predictions += 1

        return correct_predictions / total_predictions

    async def verify_weak_areas_analysis(
        self, weak_areas: list[dict[str, Any]], training_records: list[dict[str, Any]]
    ) -> float:
        """验证薄弱环节识别准确性."""
        if not weak_areas or not training_records:
            return 0.5

        # 分析实际错误分布
        error_areas: dict[str, int] = {}
        for record in training_records:
            if not record["is_correct"]:
                for kp in record["knowledge_points"]:
                    error_areas[kp] = error_areas.get(kp, 0) + 1

        # 验证AI识别的薄弱环节
        correct_identifications = 0
        for weak_area in weak_areas:
            area_name = weak_area.get("area", "")
            severity = weak_area.get("severity", "medium")

            # 检查是否确实是薄弱环节
            if area_name in error_areas:
                error_count = error_areas[area_name]
                expected_severity = (
                    "high" if error_count >= 5 else "medium" if error_count >= 2 else "low"
                )

                if severity == expected_severity:
                    correct_identifications += 1
                elif (
                    abs(
                        ["low", "medium", "high"].index(severity)
                        - ["low", "medium", "high"].index(expected_severity)
                    )
                    <= 1
                ):
                    correct_identifications += 0.5

        return correct_identifications / len(weak_areas) if weak_areas else 0.5

    async def verify_improvement_suggestions(
        self, suggestions: list[dict[str, Any]], training_records: list[dict[str, Any]]
    ) -> float:
        """验证改进建议的合理性."""
        if not suggestions:
            return 0.5

        # 基于训练记录分析学习状况
        total_questions = len(training_records)
        correct_answers = sum(1 for r in training_records if r["is_correct"])
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0

        reasonable_suggestions = 0
        for suggestion in suggestions:
            suggestion_text = suggestion.get("suggestion", "").lower()

            # 验证建议的合理性
            is_reasonable = False

            # 低准确率应该有基础练习建议
            if accuracy_rate < 0.6 and ("基础" in suggestion_text or "练习" in suggestion_text):
                is_reasonable = True

            # 高准确率应该有提升难度建议
            elif accuracy_rate > 0.8 and ("难度" in suggestion_text or "挑战" in suggestion_text):
                is_reasonable = True

            # 中等准确率应该有针对性建议
            elif 0.6 <= accuracy_rate <= 0.8 and (
                "针对" in suggestion_text or "重点" in suggestion_text
            ):
                is_reasonable = True

            if is_reasonable:
                reasonable_suggestions += 1

        return reasonable_suggestions / len(suggestions)

    # ==================== 策略调整方法 ====================

    async def calculate_difficulty_adjustment_strategy(
        self,
        student_id: int,
        training_type: TrainingType,
        analysis_result: dict[str, Any],
    ) -> dict[str, Any]:
        """计算难度调整策略."""
        # 获取最近的训练表现
        stmt = (
            select(TrainingRecord)
            .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingRecord.created_at >= datetime.now() - timedelta(days=7),
                )
            )
            .order_by(desc(TrainingRecord.created_at))
            .limit(10)
        )

        result = await self.db.execute(stmt)
        recent_records = result.scalars().all()

        if not recent_records:
            return {"should_adjust": False, "reason": "insufficient_data"}

        # 计算近10次正确率
        correct_count = sum(1 for r in recent_records if r.is_correct)
        accuracy_rate = correct_count / len(recent_records)

        # 应用🔥需求21的调整规则：>90%升级，<60%降级
        should_adjust = False
        adjustment_direction = "maintain"
        adjustment_data = {}

        if accuracy_rate > 0.9:
            should_adjust = True
            adjustment_direction = "increase"
            adjustment_data = {
                "current_accuracy": accuracy_rate,
                "target_difficulty": "higher",
                "adjustment_reason": "高准确率，建议提升难度",
            }
        elif accuracy_rate < 0.6:
            should_adjust = True
            adjustment_direction = "decrease"
            adjustment_data = {
                "current_accuracy": accuracy_rate,
                "target_difficulty": "lower",
                "adjustment_reason": "低准确率，建议降低难度",
            }

        return {
            "should_adjust": should_adjust,
            "adjustment_direction": adjustment_direction,
            "adjustment_data": adjustment_data,
            "current_accuracy": accuracy_rate,
        }

    async def calculate_content_adjustment_strategy(
        self, weak_areas: list[dict[str, Any]], knowledge_mastery: dict[str, Any]
    ) -> dict[str, Any]:
        """计算内容调整策略."""
        adjustments = []

        # 基于薄弱环节调整内容
        for weak_area in weak_areas:
            area_name = weak_area.get("area", "")
            severity = weak_area.get("severity", "medium")

            if severity == "high":
                adjustments.append(
                    {
                        "type": "increase_focus",
                        "target": area_name,
                        "weight": 0.4,
                        "reason": f"高优先级薄弱环节：{area_name}",
                    }
                )
            elif severity == "medium":
                adjustments.append(
                    {
                        "type": "moderate_focus",
                        "target": area_name,
                        "weight": 0.2,
                        "reason": f"中优先级薄弱环节：{area_name}",
                    }
                )

        # 基于强项知识点减少重复练习
        strong_points = knowledge_mastery.get("强项知识点", [])
        for strong_point in strong_points:
            adjustments.append(
                {
                    "type": "reduce_focus",
                    "target": strong_point,
                    "weight": -0.1,
                    "reason": f"已掌握知识点，减少练习：{strong_point}",
                }
            )

        return {
            "adjustments": adjustments,
            "total_adjustments": len(adjustments),
            "focus_areas": [adj["target"] for adj in adjustments if adj["weight"] > 0],
        }

    async def calculate_frequency_adjustment_strategy(
        self,
        student_id: int,
        training_type: TrainingType,
        analysis_result: dict[str, Any],
    ) -> dict[str, Any]:
        """计算频率调整策略."""
        # 获取参与度水平
        engagement_level = (
            analysis_result.get("ai_analysis", {})
            .get("engagement_metrics", {})
            .get("engagement_level", "medium")
        )

        # 基于参与度调整频率
        frequency_adjustments = {}

        if engagement_level == "high":
            frequency_adjustments = {
                "daily_questions": "increase",
                "session_length": "maintain",
                "break_intervals": "reduce",
                "reason": "高参与度，可增加练习量",
            }
        elif engagement_level == "low":
            frequency_adjustments = {
                "daily_questions": "decrease",
                "session_length": "reduce",
                "break_intervals": "increase",
                "reason": "低参与度，减少练习量避免疲劳",
            }
        else:
            frequency_adjustments = {
                "daily_questions": "maintain",
                "session_length": "maintain",
                "break_intervals": "maintain",
                "reason": "中等参与度，保持当前频率",
            }

        return {
            "frequency_adjustments": frequency_adjustments,
            "engagement_level": engagement_level,
            "recommended_changes": frequency_adjustments,
        }

    # ==================== 效果验证方法 ====================

    async def get_baseline_performance(
        self, student_id: int, training_type: TrainingType, days: int
    ) -> dict[str, Any]:
        """获取基线表现数据."""
        cutoff_date = datetime.now() - timedelta(days=days)

        stmt = (
            select(TrainingRecord)
            .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingRecord.created_at >= cutoff_date,
                )
            )
        )

        result = await self.db.execute(stmt)
        records = result.scalars().all()

        if not records:
            return {"accuracy": 0.0, "total_questions": 0, "avg_time": 0.0}

        correct_count = sum(1 for r in records if r.is_correct)
        total_questions = len(records)
        accuracy = correct_count / total_questions

        time_spent_list = [r.time_spent for r in records if r.time_spent]
        avg_time = sum(time_spent_list) / len(time_spent_list) if time_spent_list else 0

        return {
            "accuracy": accuracy,
            "total_questions": total_questions,
            "avg_time": avg_time,
            "period_days": days,
        }

    async def get_current_performance(
        self, student_id: int, training_type: TrainingType, days: int = 3
    ) -> dict[str, Any]:
        """获取当前表现数据."""
        return await self.get_baseline_performance(student_id, training_type, days)

    async def calculate_improvement_effect(
        self,
        baseline_data: dict[str, Any],
        current_data: dict[str, Any],
        adjustment_result: dict[str, Any],
    ) -> dict[str, Any]:
        """计算改进效果."""
        baseline_accuracy = baseline_data.get("accuracy", 0.0)
        current_accuracy = current_data.get("accuracy", 0.0)

        improvement_rate = current_accuracy - baseline_accuracy
        improvement_percentage = (
            (improvement_rate / baseline_accuracy * 100) if baseline_accuracy > 0 else 0
        )

        return {
            "improvement_rate": improvement_rate,
            "improvement_percentage": improvement_percentage,
            "baseline_accuracy": baseline_accuracy,
            "current_accuracy": current_accuracy,
            "is_improving": improvement_rate > 0.05,  # 5%以上改进认为有效
        }

    async def verify_success_criteria(
        self, improvement_analysis: dict[str, Any], verification_config: dict[str, Any]
    ) -> dict[str, Any]:
        """验证是否达到成功标准."""
        improvement_threshold = verification_config.get("improvement_threshold", 0.05)
        success_criteria = verification_config.get("success_criteria", 0.8)

        improvement_rate = improvement_analysis.get("improvement_rate", 0.0)
        current_accuracy = improvement_analysis.get("current_accuracy", 0.0)

        meets_improvement = improvement_rate >= improvement_threshold
        meets_accuracy = current_accuracy >= success_criteria

        return {
            "meets_criteria": meets_improvement or meets_accuracy,
            "meets_improvement_threshold": meets_improvement,
            "meets_accuracy_threshold": meets_accuracy,
            "next_loop_recommended": not meets_improvement,
            "success_score": (
                improvement_rate / improvement_threshold + current_accuracy / success_criteria
            )
            / 2,
        }
