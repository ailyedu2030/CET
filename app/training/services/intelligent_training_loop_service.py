"""智能训练闭环服务 - 🔥需求21核心实现.

实现完整的数据采集→AI分析→策略调整→效果验证闭环流程。
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.models.enums import TrainingType
from app.training.models.training_models import (
    Question,
    TrainingRecord,
    TrainingSession,
)
from app.training.services.adaptive_service import AdaptiveLearningService
from app.training.services.analytics_service import AnalyticsService
from app.training.services.intelligent_training_loop_helpers import (
    IntelligentTrainingLoopHelpers,
)

logger = logging.getLogger(__name__)


class IntelligentTrainingLoopService:
    """智能训练闭环服务 - 系统核心."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化智能训练闭环服务."""
        self.db = db
        self.deepseek_service = DeepSeekService()
        self.adaptive_service = AdaptiveLearningService(db)
        self.analytics_service = AnalyticsService(db)
        self.helpers = IntelligentTrainingLoopHelpers(db)

        # 闭环配置参数
        self.loop_config = {
            "data_collection": {
                "min_records_for_analysis": 10,  # 最少记录数
                "analysis_window_days": 7,  # 分析窗口
                "real_time_threshold_minutes": 5,  # 实时阈值
            },
            "ai_analysis": {
                "accuracy_threshold": 0.9,  # AI分析准确率阈值>90%
                "confidence_threshold": 0.85,  # 置信度阈值
                "analysis_depth": "comprehensive",  # 分析深度
            },
            "strategy_adjustment": {
                "adjustment_sensitivity": 0.1,  # 调整敏感度
                "max_adjustment_per_cycle": 2,  # 每周期最大调整幅度
                "stability_period_hours": 24,  # 稳定期
            },
            "effect_verification": {
                "verification_period_days": 7,  # 7天效果验证周期
                "improvement_threshold": 0.05,  # 改进阈值
                "success_criteria": 0.8,  # 成功标准
            },
        }

    # ==================== 智能训练闭环主流程 ====================

    async def execute_training_loop(
        self, student_id: int, training_type: TrainingType
    ) -> dict[str, Any]:
        """执行完整的智能训练闭环流程."""
        try:
            logger.info(f"开始执行智能训练闭环: 学生{student_id}, 训练类型{training_type}")

            # 第一步：数据采集
            collected_data = await self._data_collection_phase(
                student_id, training_type
            )

            # 第二步：AI分析
            analysis_result = await self._ai_analysis_phase(collected_data)

            # 第三步：策略调整
            adjustment_result = await self._strategy_adjustment_phase(
                student_id, training_type, analysis_result
            )

            # 第四步：效果验证
            verification_result = await self._effect_verification_phase(
                student_id, training_type, adjustment_result
            )

            # 构建闭环结果
            loop_result = {
                "student_id": student_id,
                "training_type": training_type.value,
                "execution_time": datetime.now(),
                "phases": {
                    "data_collection": collected_data,
                    "ai_analysis": analysis_result,
                    "strategy_adjustment": adjustment_result,
                    "effect_verification": verification_result,
                },
                "loop_success": self._evaluate_loop_success(
                    analysis_result, adjustment_result, verification_result
                ),
                "next_execution_time": datetime.now()
                + timedelta(
                    days=self.loop_config["effect_verification"]["verification_period_days"]  # type: ignore
                ),
            }

            # 记录闭环执行结果
            await self._record_loop_execution(loop_result)

            logger.info(f"智能训练闭环执行完成: 学生{student_id}, 成功={loop_result['loop_success']}")
            return loop_result

        except Exception as e:
            logger.error(f"智能训练闭环执行失败: 学生{student_id}, 错误: {str(e)}")
            raise

    # ==================== 第一步：数据采集阶段 ====================

    async def _data_collection_phase(
        self, student_id: int, training_type: TrainingType
    ) -> dict[str, Any]:
        """数据采集阶段 - 实时记录学生答题数据."""
        try:
            collection_config = self.loop_config["data_collection"]
            analysis_window = timedelta(days=collection_config["analysis_window_days"])  # type: ignore
            cutoff_date = datetime.now() - analysis_window

            # 收集训练记录
            training_records = await self._collect_training_records(
                student_id, training_type, cutoff_date
            )

            # 收集学习路径数据
            learning_path_data = await self._collect_learning_path_data(
                student_id, training_type, cutoff_date
            )

            # 收集答题行为数据
            behavior_data = await self._collect_behavior_data(
                student_id, training_type, cutoff_date
            )

            # 数据质量检查
            data_quality = await self._assess_data_quality(
                training_records, learning_path_data, behavior_data
            )

            collected_data = {
                "collection_time": datetime.now(),
                "data_window_days": collection_config["analysis_window_days"],  # type: ignore
                "training_records": training_records,
                "learning_path_data": learning_path_data,
                "behavior_data": behavior_data,
                "data_quality": data_quality,
                "total_records": len(training_records),
                "collection_success": data_quality["overall_quality"] >= 0.8,
            }

            logger.info(
                f"数据采集完成: 学生{student_id}, 记录数{len(training_records)}, "
                f"质量{data_quality['overall_quality']:.2f}"
            )
            return collected_data

        except Exception as e:
            logger.error(f"数据采集失败: 学生{student_id}, 错误: {str(e)}")
            raise

    async def _collect_training_records(
        self, student_id: int, training_type: TrainingType, cutoff_date: datetime
    ) -> list[dict[str, Any]]:
        """收集训练记录数据."""
        stmt = (
            select(TrainingRecord, Question)
            .join(Question, TrainingRecord.question_id == Question.id)
            .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingRecord.created_at >= cutoff_date,
                )
            )
            .order_by(desc(TrainingRecord.created_at))
        )

        result = await self.db.execute(stmt)
        records = result.all()

        training_data = []
        for record, question in records:
            training_data.append(
                {
                    "record_id": record.id,
                    "session_id": record.session_id,
                    "question_id": record.question_id,
                    "is_correct": record.is_correct,
                    "score": record.score,
                    "time_spent": record.time_spent,
                    "difficulty_level": question.difficulty_level.value,
                    "knowledge_points": record.knowledge_points_mastered
                    + record.knowledge_points_weak,
                    "ai_confidence": record.ai_confidence,
                    "created_at": record.created_at,
                }
            )

        return training_data

    async def _collect_learning_path_data(
        self, student_id: int, training_type: TrainingType, cutoff_date: datetime
    ) -> dict[str, Any]:
        """收集学习路径数据."""
        # 获取学习会话序列
        stmt = (
            select(TrainingSession)
            .where(
                and_(
                    TrainingSession.student_id == student_id,
                    TrainingSession.session_type == training_type,
                    TrainingSession.started_at >= cutoff_date,
                )
            )
            .order_by(TrainingSession.started_at)
        )

        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())

        learning_path = {
            "session_sequence": [
                {
                    "session_id": session.id,
                    "difficulty_level": session.difficulty_level.value,
                    "question_count": session.question_count,
                    "accuracy_rate": (
                        (session.correct_answers / session.total_questions)
                        if session.total_questions > 0
                        else 0
                    ),
                    "time_spent": session.time_spent,
                    "started_at": session.started_at,
                }
                for session in sessions
            ],
            "difficulty_progression": self._analyze_difficulty_progression(sessions),
            "learning_velocity": self._calculate_learning_velocity(sessions),
        }

        return learning_path

    async def _collect_behavior_data(
        self, student_id: int, training_type: TrainingType, cutoff_date: datetime
    ) -> dict[str, Any]:
        """收集答题行为数据."""
        # 分析答题模式
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
            .order_by(TrainingRecord.created_at)
        )

        result = await self.db.execute(stmt)
        records = list(result.scalars().all())

        behavior_data = {
            "answer_patterns": self._analyze_answer_patterns(records),
            "time_patterns": self._analyze_time_patterns(records),
            "error_patterns": self._analyze_error_patterns(records),
            "engagement_metrics": self._calculate_engagement_metrics(records),
        }

        return behavior_data

    # ==================== 第二步：AI分析阶段 ====================

    async def _ai_analysis_phase(
        self, collected_data: dict[str, Any]
    ) -> dict[str, Any]:
        """AI分析阶段 - 智能分析知识点掌握度和薄弱环节."""
        try:
            analysis_config = self.loop_config["ai_analysis"]

            # 检查数据质量
            if not collected_data["collection_success"]:
                return {
                    "analysis_success": False,
                    "error": "数据质量不足，无法进行AI分析",
                    "accuracy": 0.0,
                }

            # 构建AI分析prompt
            analysis_prompt = await self._build_ai_analysis_prompt(collected_data)

            # 调用DeepSeek进行分析
            (
                success,
                ai_response,
                error_msg,
            ) = await self.deepseek_service.generate_completion(
                prompt=analysis_prompt,
                temperature=0.2,  # 低温度确保分析准确性
                max_tokens=2000,
            )

            if not success or not ai_response:
                raise ValueError(f"AI分析失败: {error_msg}")

            # 解析AI分析结果
            analysis_result = await self._parse_ai_analysis_result(ai_response)

            # 验证AI分析准确率
            accuracy_verification = await self._verify_ai_analysis_accuracy(
                analysis_result, collected_data
            )

            # 构建分析结果
            final_analysis = {
                "analysis_time": datetime.now(),
                "ai_analysis": analysis_result,
                "accuracy_verification": accuracy_verification,
                "analysis_accuracy": accuracy_verification["accuracy_score"],
                "analysis_success": accuracy_verification["accuracy_score"]
                >= analysis_config["accuracy_threshold"],  # type: ignore
                "confidence_score": analysis_result.get("confidence", 0.0),
                "knowledge_mastery": analysis_result.get("knowledge_mastery", {}),
                "weak_areas": analysis_result.get("weak_areas", []),
                "improvement_suggestions": analysis_result.get(
                    "improvement_suggestions", []
                ),
            }

            logger.info(
                f"AI分析完成: 准确率{accuracy_verification['accuracy_score']:.2f}, "
                f"成功={final_analysis['analysis_success']}"
            )
            return final_analysis

        except Exception as e:
            logger.error(f"AI分析失败: 错误: {str(e)}")
            return {
                "analysis_success": False,
                "error": str(e),
                "accuracy": 0.0,
            }

    async def _build_ai_analysis_prompt(self, collected_data: dict[str, Any]) -> str:
        """构建AI分析prompt."""
        training_records = collected_data["training_records"]
        learning_path = collected_data["learning_path_data"]
        behavior_data = collected_data["behavior_data"]

        # 计算基础统计
        total_questions = len(training_records)
        correct_answers = sum(1 for r in training_records if r["is_correct"])
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0

        # 知识点统计
        all_knowledge_points = []
        for record in training_records:
            all_knowledge_points.extend(record["knowledge_points"])

        knowledge_stats = {}
        for kp in set(all_knowledge_points):
            kp_records = [r for r in training_records if kp in r["knowledge_points"]]
            kp_correct = sum(1 for r in kp_records if r["is_correct"])
            knowledge_stats[kp] = {
                "total": len(kp_records),
                "correct": kp_correct,
                "accuracy": kp_correct / len(kp_records) if kp_records else 0,
            }

        prompt = f"""
请分析以下学生的英语四级训练数据，提供准确的学习分析报告。

## 训练数据概览
- 分析时间窗口: {collected_data["data_window_days"]}天
- 总题目数: {total_questions}
- 正确答案数: {correct_answers}
- 整体准确率: {accuracy_rate:.2%}

## 知识点掌握情况
{json.dumps(knowledge_stats, ensure_ascii=False, indent=2)}

## 学习路径分析
- 难度进展: {learning_path.get("difficulty_progression", {})}
- 学习速度: {learning_path.get("learning_velocity", {})}

## 答题行为分析
- 答题模式: {behavior_data.get("answer_patterns", {})}
- 时间模式: {behavior_data.get("time_patterns", {})}
- 错误模式: {behavior_data.get("error_patterns", {})}

## 分析要求
请基于以上数据进行深度分析，返回JSON格式结果：

{{
    "knowledge_mastery": {{
        "强项知识点": ["知识点1", "知识点2"],
        "掌握中知识点": ["知识点3", "知识点4"],
        "薄弱知识点": ["知识点5", "知识点6"]
    }},
    "weak_areas": [
        {{
            "area": "薄弱环节名称",
            "severity": "high/medium/low",
            "evidence": "支撑证据",
            "impact_score": 0.8
        }}
    ],
    "learning_patterns": {{
        "学习风格": "visual/auditory/kinesthetic",
        "学习偏好": "短时高频/长时低频",
        "最佳学习时间": "morning/afternoon/evening"
    }},
    "improvement_suggestions": [
        {{
            "suggestion": "具体建议",
            "priority": "high/medium/low",
            "expected_improvement": 0.15,
            "implementation_difficulty": "easy/medium/hard"
        }}
    ],
    "confidence": 0.95,
    "analysis_quality": "high/medium/low"
}}

请确保分析的准确性和实用性，置信度应基于数据质量和分析深度。
"""
        return prompt

    async def _parse_ai_analysis_result(
        self, ai_response: dict[str, Any]
    ) -> dict[str, Any]:
        """解析AI分析结果."""
        try:
            # 提取AI响应内容
            content = (
                ai_response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            # 解析JSON结果
            analysis_data: dict[str, Any] = json.loads(content)

            # 验证必要字段
            required_fields = [
                "knowledge_mastery",
                "weak_areas",
                "improvement_suggestions",
                "confidence",
            ]
            for field in required_fields:
                if field not in analysis_data:
                    analysis_data[field] = {} if field == "knowledge_mastery" else []

            return analysis_data

        except json.JSONDecodeError as e:
            logger.error(f"AI分析结果解析失败: {str(e)}")
            return {
                "knowledge_mastery": {},
                "weak_areas": [],
                "improvement_suggestions": [],
                "confidence": 0.5,
                "parse_error": str(e),
            }

    async def _verify_ai_analysis_accuracy(
        self, analysis_result: dict[str, Any], collected_data: dict[str, Any]
    ) -> dict[str, Any]:
        """验证AI分析准确率 - 确保>90%准确率."""
        try:
            training_records = collected_data["training_records"]

            # 验证知识点分析准确性
            knowledge_accuracy = await self.helpers.verify_knowledge_analysis(
                analysis_result.get("knowledge_mastery", {}), training_records
            )

            # 验证薄弱环节识别准确性
            weak_areas_accuracy = await self.helpers.verify_weak_areas_analysis(
                analysis_result.get("weak_areas", []), training_records
            )

            # 验证改进建议的合理性
            suggestions_accuracy = await self.helpers.verify_improvement_suggestions(
                analysis_result.get("improvement_suggestions", []), training_records
            )

            # 计算综合准确率
            overall_accuracy = (
                knowledge_accuracy * 0.4
                + weak_areas_accuracy * 0.4
                + suggestions_accuracy * 0.2
            )

            verification_result = {
                "accuracy_score": overall_accuracy,
                "knowledge_accuracy": knowledge_accuracy,
                "weak_areas_accuracy": weak_areas_accuracy,
                "suggestions_accuracy": suggestions_accuracy,
                "verification_time": datetime.now(),
                "meets_threshold": overall_accuracy
                >= self.loop_config["ai_analysis"]["accuracy_threshold"],  # type: ignore
            }

            logger.info(f"AI分析准确率验证: {overall_accuracy:.2f}")
            return verification_result

        except Exception as e:
            logger.error(f"AI分析准确率验证失败: {str(e)}")
            return {
                "accuracy_score": 0.0,
                "error": str(e),
                "meets_threshold": False,
            }

    # ==================== 第三步：策略调整阶段 ====================

    async def _strategy_adjustment_phase(
        self,
        student_id: int,
        training_type: TrainingType,
        analysis_result: dict[str, Any],
    ) -> dict[str, Any]:
        """策略调整阶段 - 基于AI分析结果自动调整训练策略."""
        try:
            # 检查AI分析是否成功
            if not analysis_result.get("analysis_success", False):
                return {
                    "adjustment_success": False,
                    "error": "AI分析失败，无法进行策略调整",
                }

            # 生成调整策略
            adjustment_strategy = await self._generate_adjustment_strategy(
                student_id, training_type, analysis_result
            )

            # 应用策略调整
            applied_adjustments = await self._apply_strategy_adjustments(
                student_id, training_type, adjustment_strategy
            )

            # 记录调整历史
            await self._record_strategy_adjustment(
                student_id, training_type, adjustment_strategy, applied_adjustments
            )

            adjustment_result = {
                "adjustment_time": datetime.now(),
                "adjustment_strategy": adjustment_strategy,
                "applied_adjustments": applied_adjustments,
                "adjustment_success": applied_adjustments["success"],
                "next_verification_time": datetime.now()
                + timedelta(
                    days=self.loop_config["effect_verification"]["verification_period_days"]  # type: ignore
                ),
            }

            logger.info(
                f"策略调整完成: 学生{student_id}, 成功={adjustment_result['adjustment_success']}"
            )
            return adjustment_result

        except Exception as e:
            logger.error(f"策略调整失败: 学生{student_id}, 错误: {str(e)}")
            return {
                "adjustment_success": False,
                "error": str(e),
            }

    async def _generate_adjustment_strategy(
        self,
        student_id: int,
        training_type: TrainingType,
        analysis_result: dict[str, Any],
    ) -> dict[str, Any]:
        """生成调整策略."""
        weak_areas = analysis_result.get("weak_areas", [])
        knowledge_mastery = analysis_result.get("knowledge_mastery", {})
        improvement_suggestions = analysis_result.get("improvement_suggestions", [])

        # 难度调整策略
        difficulty_adjustment = (
            await self.helpers.calculate_difficulty_adjustment_strategy(
                student_id, training_type, analysis_result
            )
        )

        # 内容调整策略
        content_adjustment = await self.helpers.calculate_content_adjustment_strategy(
            weak_areas, knowledge_mastery
        )

        # 频率调整策略
        frequency_adjustment = (
            await self.helpers.calculate_frequency_adjustment_strategy(
                student_id, training_type, analysis_result
            )
        )

        strategy = {
            "difficulty_adjustment": difficulty_adjustment,
            "content_adjustment": content_adjustment,
            "frequency_adjustment": frequency_adjustment,
            "priority_focus": (weak_areas[:3] if weak_areas else []),  # 重点关注前3个薄弱环节
            "implementation_timeline": "immediate",  # 立即实施
            "expected_improvement": (
                sum(s.get("expected_improvement", 0) for s in improvement_suggestions)
                / len(improvement_suggestions)
                if improvement_suggestions
                else 0.1
            ),
        }

        return strategy

    async def _apply_strategy_adjustments(
        self, student_id: int, training_type: TrainingType, strategy: dict[str, Any]
    ) -> dict[str, Any]:
        """应用策略调整."""
        try:
            applied_changes: list[dict[str, Any]] = []

            # 应用难度调整
            if strategy["difficulty_adjustment"]["should_adjust"]:
                difficulty_result = await self.adaptive_service.update_adaptive_config(
                    student_id=student_id,
                    training_type=training_type,
                    session_results=strategy["difficulty_adjustment"][
                        "adjustment_data"
                    ],
                )
                applied_changes.append(
                    {
                        "type": "difficulty",
                        "result": difficulty_result,
                        "success": difficulty_result is not None,
                    }
                )

            # 应用内容调整
            content_result = await self._apply_content_adjustments(
                student_id, training_type, strategy["content_adjustment"]
            )
            applied_changes.append(
                {
                    "type": "content",
                    "result": content_result,
                    "success": content_result.get("success", False),
                }
            )

            # 应用频率调整
            frequency_result = await self._apply_frequency_adjustments(
                student_id, training_type, strategy["frequency_adjustment"]
            )
            applied_changes.append(
                {
                    "type": "frequency",
                    "result": frequency_result,
                    "success": frequency_result.get("success", False),
                }
            )

            return {
                "success": all(change["success"] for change in applied_changes),
                "applied_changes": applied_changes,
                "total_adjustments": len(applied_changes),
            }

        except Exception as e:
            logger.error(f"应用策略调整失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "applied_changes": [],
            }

    # ==================== 第四步：效果验证阶段 ====================

    async def _effect_verification_phase(
        self,
        student_id: int,
        training_type: TrainingType,
        adjustment_result: dict[str, Any],
    ) -> dict[str, Any]:
        """效果验证阶段 - 7天调整效果评估周期."""
        try:
            verification_config = self.loop_config["effect_verification"]

            # 检查策略调整是否成功
            if not adjustment_result.get("adjustment_success", False):
                return {
                    "verification_success": False,
                    "error": "策略调整失败，无法进行效果验证",
                }

            # 获取调整前的基线数据
            baseline_data = await self.helpers.get_baseline_performance(
                student_id,
                training_type,
                verification_config["verification_period_days"],  # type: ignore
            )

            # 获取调整后的表现数据
            current_data = await self.helpers.get_current_performance(
                student_id,
                training_type,
                days=3,  # 获取最近3天的数据
            )

            # 计算改进效果
            improvement_analysis = await self.helpers.calculate_improvement_effect(
                baseline_data, current_data, adjustment_result
            )

            # 验证是否达到成功标准
            success_verification = await self.helpers.verify_success_criteria(
                improvement_analysis,
                dict(verification_config),  # type: ignore
            )

            verification_result = {
                "verification_time": datetime.now(),
                "baseline_data": baseline_data,
                "current_data": current_data,
                "improvement_analysis": improvement_analysis,
                "success_verification": success_verification,
                "verification_success": success_verification["meets_criteria"],
                "next_loop_recommended": success_verification["next_loop_recommended"],
            }

            logger.info(
                f"效果验证完成: 学生{student_id}, 成功={verification_result['verification_success']}"
            )
            return verification_result

        except Exception as e:
            logger.error(f"效果验证失败: 学生{student_id}, 错误: {str(e)}")
            return {
                "verification_success": False,
                "error": str(e),
            }

    # ==================== 辅助方法实现 ====================

    def _evaluate_loop_success(
        self,
        analysis_result: dict[str, Any],
        adjustment_result: dict[str, Any],
        verification_result: dict[str, Any],
    ) -> bool:
        """评估闭环是否成功."""
        return bool(
            analysis_result.get("analysis_success", False)
            and adjustment_result.get("adjustment_success", False)
            and verification_result.get("verification_success", False)
        )

    async def _record_loop_execution(self, loop_result: dict[str, Any]) -> None:
        """记录闭环执行结果."""
        try:
            from app.training.models.training_models import IntelligentTrainingLoop

            loop_record = IntelligentTrainingLoop(
                student_id=loop_result["student_id"],
                training_type=TrainingType(loop_result["training_type"]),
                execution_time=loop_result["execution_time"],
                next_execution_time=loop_result["next_execution_time"],
                data_collection_result=loop_result["phases"]["data_collection"],
                ai_analysis_result=loop_result["phases"]["ai_analysis"],
                strategy_adjustment_result=loop_result["phases"]["strategy_adjustment"],
                effect_verification_result=loop_result["phases"]["effect_verification"],
                loop_success=loop_result["loop_success"],
                ai_analysis_accuracy=loop_result["phases"]["ai_analysis"].get(
                    "analysis_accuracy", 0.0
                ),
                improvement_rate=loop_result["phases"]["effect_verification"]
                .get("improvement_analysis", {})
                .get("improvement_rate", 0.0),
            )

            self.db.add(loop_record)
            await self.db.commit()

        except Exception as e:
            logger.error(f"记录闭环执行结果失败: {str(e)}")
            await self.db.rollback()

    async def _assess_data_quality(
        self,
        training_records: list[dict[str, Any]],
        learning_path_data: dict[str, Any],
        behavior_data: dict[str, Any],
    ) -> dict[str, Any]:
        """评估数据质量."""
        # 数据完整性检查
        completeness_score = 0.0
        if training_records:
            completeness_score += 0.4
        if learning_path_data.get("session_sequence"):
            completeness_score += 0.3
        if behavior_data.get("answer_patterns"):
            completeness_score += 0.3

        # 数据量检查
        volume_score = min(len(training_records) / 50, 1.0)  # 50题为满分

        # 数据时效性检查
        if training_records:
            latest_record = max(training_records, key=lambda x: x["created_at"])
            time_diff = datetime.now() - latest_record["created_at"]
            freshness_score = max(0, 1 - time_diff.days / 7)  # 7天内为满分
        else:
            freshness_score = 0.0

        overall_quality = (
            completeness_score * 0.4 + volume_score * 0.4 + freshness_score * 0.2
        )

        return {
            "completeness_score": completeness_score,
            "volume_score": volume_score,
            "freshness_score": freshness_score,
            "overall_quality": overall_quality,
        }

    def _analyze_difficulty_progression(
        self, sessions: list[TrainingSession]
    ) -> dict[str, Any]:
        """分析难度进展."""
        if not sessions:
            return {"trend": "no_data", "progression_rate": 0.0}

        difficulty_levels = [session.difficulty_level.value for session in sessions]

        # 计算难度趋势
        if len(difficulty_levels) < 2:
            return {"trend": "insufficient_data", "progression_rate": 0.0}

        # 简单的线性趋势分析
        trend_score = 0
        for i in range(1, len(difficulty_levels)):
            if difficulty_levels[i] > difficulty_levels[i - 1]:
                trend_score += 1
            elif difficulty_levels[i] < difficulty_levels[i - 1]:
                trend_score -= 1

        progression_rate = (
            trend_score / (len(difficulty_levels) - 1)
            if len(difficulty_levels) > 1
            else 0
        )

        return {
            "trend": (
                "increasing"
                if progression_rate > 0.2
                else "decreasing"
                if progression_rate < -0.2
                else "stable"
            ),
            "progression_rate": progression_rate,
            "difficulty_range": [min(difficulty_levels), max(difficulty_levels)],
        }

    def _calculate_learning_velocity(
        self, sessions: list[TrainingSession]
    ) -> dict[str, Any]:
        """计算学习速度."""
        if not sessions:
            return {"velocity": 0.0, "trend": "no_data"}

        # 计算每个会话的效率
        velocities = []
        for session in sessions:
            if session.time_spent and session.time_spent > 0:
                velocity = session.correct_answers / (
                    session.time_spent / 60
                )  # 每分钟正确答题数
                velocities.append(velocity)

        if not velocities:
            return {"velocity": 0.0, "trend": "no_data"}

        avg_velocity = sum(velocities) / len(velocities)

        # 分析趋势
        if len(velocities) >= 3:
            recent_avg = sum(velocities[-3:]) / 3
            early_avg = sum(velocities[:3]) / 3
            trend = (
                "improving"
                if recent_avg > early_avg * 1.1
                else "declining"
                if recent_avg < early_avg * 0.9
                else "stable"
            )
        else:
            trend = "insufficient_data"

        return {
            "velocity": avg_velocity,
            "trend": trend,
            "velocity_range": [min(velocities), max(velocities)],
        }

    def _analyze_answer_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析答题模式."""
        if not records:
            return {"pattern": "no_data"}

        correct_count = sum(1 for r in records if r.is_correct)
        accuracy_rate = correct_count / len(records)

        # 分析连续正确/错误模式
        max_correct_streak = 0
        max_incorrect_streak = 0
        current_correct_streak = 0
        current_incorrect_streak = 0

        for record in records:
            if record.is_correct:
                current_correct_streak += 1
                current_incorrect_streak = 0
                max_correct_streak = max(max_correct_streak, current_correct_streak)
            else:
                current_incorrect_streak += 1
                current_correct_streak = 0
                max_incorrect_streak = max(
                    max_incorrect_streak, current_incorrect_streak
                )

        return {
            "accuracy_rate": accuracy_rate,
            "max_correct_streak": max_correct_streak,
            "max_incorrect_streak": max_incorrect_streak,
            "pattern": (
                "consistent"
                if accuracy_rate > 0.8
                else "inconsistent"
                if accuracy_rate < 0.6
                else "moderate"
            ),
        }

    def _analyze_time_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析时间模式."""
        if not records:
            return {"pattern": "no_data"}

        time_spent_list = [r.time_spent for r in records if r.time_spent]
        if not time_spent_list:
            return {"pattern": "no_time_data"}

        avg_time = sum(time_spent_list) / len(time_spent_list)

        return {
            "average_time": avg_time,
            "time_range": [min(time_spent_list), max(time_spent_list)],
            "pattern": (
                "fast" if avg_time < 30 else "slow" if avg_time > 120 else "normal"
            ),
        }

    def _analyze_error_patterns(self, records: list[TrainingRecord]) -> dict[str, Any]:
        """分析错误模式."""
        incorrect_records = [r for r in records if not r.is_correct]
        if not incorrect_records:
            return {"pattern": "no_errors"}

        # 分析错误的知识点分布
        error_knowledge_points = []
        for record in incorrect_records:
            error_knowledge_points.extend(record.knowledge_points_weak)

        from collections import Counter

        error_distribution = Counter(error_knowledge_points)

        return {
            "error_count": len(incorrect_records),
            "error_rate": len(incorrect_records) / len(records),
            "top_error_areas": dict(error_distribution.most_common(5)),
            "pattern": "concentrated" if len(error_distribution) <= 3 else "scattered",
        }

    def _calculate_engagement_metrics(
        self, records: list[TrainingRecord]
    ) -> dict[str, Any]:
        """计算参与度指标."""
        if not records:
            return {"engagement": "no_data"}

        # 基于答题时间和AI置信度计算参与度
        engagement_scores = []
        for record in records:
            score = 0.5  # 基础分

            # 时间因素
            if record.time_spent:
                if 30 <= record.time_spent <= 120:  # 合理时间范围
                    score += 0.3
                elif record.time_spent < 10:  # 过快可能不认真
                    score -= 0.2

            # AI置信度因素
            if record.ai_confidence and record.ai_confidence > 0.8:
                score += 0.2

            engagement_scores.append(max(0, min(1, score)))

        avg_engagement = sum(engagement_scores) / len(engagement_scores)

        return {
            "engagement_score": avg_engagement,
            "engagement_level": (
                "high"
                if avg_engagement > 0.7
                else "low"
                if avg_engagement < 0.4
                else "medium"
            ),
        }

    # ==================== 策略应用方法 ====================

    async def _apply_content_adjustments(
        self,
        student_id: int,
        training_type: TrainingType,
        content_adjustment: dict[str, Any],
    ) -> dict[str, Any]:
        """应用内容调整."""
        try:
            adjustments = content_adjustment.get("adjustments", [])
            applied_count = 0

            for adjustment in adjustments:
                # 这里可以调用自适应服务来应用具体的内容调整
                # 暂时记录调整意图
                logger.info(f"应用内容调整: {adjustment}")
                applied_count += 1

            return {
                "success": True,
                "applied_adjustments": applied_count,
                "total_adjustments": len(adjustments),
            }

        except Exception as e:
            logger.error(f"应用内容调整失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _apply_frequency_adjustments(
        self,
        student_id: int,
        training_type: TrainingType,
        frequency_adjustment: dict[str, Any],
    ) -> dict[str, Any]:
        """应用频率调整."""
        try:
            adjustments = frequency_adjustment.get("frequency_adjustments", {})
            applied_changes = []

            for key, value in adjustments.items():
                if key != "reason":
                    # 这里可以调用相关服务来应用频率调整
                    logger.info(f"应用频率调整: {key} -> {value}")
                    applied_changes.append(f"{key}: {value}")

            return {
                "success": True,
                "applied_changes": applied_changes,
                "total_changes": len(applied_changes),
            }

        except Exception as e:
            logger.error(f"应用频率调整失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _record_strategy_adjustment(
        self,
        student_id: int,
        training_type: TrainingType,
        strategy: dict[str, Any],
        applied_adjustments: dict[str, Any],
    ) -> None:
        """记录策略调整历史."""
        try:
            # 这里可以创建专门的策略调整记录表
            # 暂时使用日志记录
            logger.info(
                f"策略调整记录: 学生{student_id}, 训练类型{training_type}, "
                f"策略{strategy}, 应用结果{applied_adjustments}"
            )

        except Exception as e:
            logger.error(f"记录策略调整失败: {str(e)}")
