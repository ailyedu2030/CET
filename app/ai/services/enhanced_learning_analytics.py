"""增强的学情分析引擎 - 多维度数据融合和智能预测."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import get_deepseek_service
from app.training.models.training_models import TrainingRecord
from app.users.models.user_models import StudentProfile, User

logger = logging.getLogger(__name__)


class EnhancedLearningAnalytics:
    """增强的学情分析引擎."""

    def __init__(self) -> None:
        self.deepseek_service = get_deepseek_service()
        self.analysis_cache: dict[str, Any] = {}
        self.cache_ttl = 3600  # 1小时缓存

    async def comprehensive_learning_analysis(
        self,
        db: AsyncSession,
        class_id: int,
        course_id: int,
        analysis_period_days: int = 30,
    ) -> dict[str, Any]:
        """综合学情分析 - 多维度数据融合."""
        try:
            # 检查缓存
            cache_key = f"comprehensive_analysis_{class_id}_{course_id}_{analysis_period_days}"
            if cache_key in self.analysis_cache:
                cached_data = self.analysis_cache[cache_key]
                if (datetime.now() - cached_data["timestamp"]).total_seconds() < self.cache_ttl:
                    data = cached_data["data"]
                    return data if isinstance(data, dict) else {}

            # 1. 收集多维度数据
            multi_dimensional_data = await self._collect_multi_dimensional_data(
                db, class_id, course_id, analysis_period_days
            )

            # 2. 执行AI驱动的深度分析
            ai_analysis = await self._perform_ai_deep_analysis(multi_dimensional_data)

            # 3. 生成预测模型
            prediction_results = await self._generate_learning_predictions(
                multi_dimensional_data, ai_analysis
            )

            # 4. 识别风险学生和预警
            risk_assessment = await self._assess_learning_risks(multi_dimensional_data, ai_analysis)

            # 5. 生成个性化建议
            personalized_recommendations = await self._generate_personalized_recommendations(
                multi_dimensional_data, ai_analysis, prediction_results
            )

            # 整合分析结果
            comprehensive_result = {
                "analysis_metadata": {
                    "class_id": class_id,
                    "course_id": course_id,
                    "analysis_period_days": analysis_period_days,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "data_quality_score": self._calculate_data_quality_score(
                        multi_dimensional_data
                    ),
                },
                "multi_dimensional_data": multi_dimensional_data,
                "ai_analysis": ai_analysis,
                "prediction_results": prediction_results,
                "risk_assessment": risk_assessment,
                "personalized_recommendations": personalized_recommendations,
                "overall_insights": await self._generate_overall_insights(
                    ai_analysis, prediction_results, risk_assessment
                ),
            }

            # 缓存结果
            self.analysis_cache[cache_key] = {
                "data": comprehensive_result,
                "timestamp": datetime.now(),
            }

            return comprehensive_result

        except Exception as e:
            logger.error(f"综合学情分析失败: {str(e)}")
            raise

    async def _collect_multi_dimensional_data(
        self,
        db: AsyncSession,
        class_id: int,
        course_id: int,
        analysis_period_days: int,
    ) -> dict[str, Any]:
        """收集多维度学习数据."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=analysis_period_days)

        # 获取班级学生列表
        students_result = await db.execute(
            select(User)
            .join(StudentProfile)
            .where(
                and_(
                    User.user_type == "student",
                    # 这里需要通过班级学生关联表查询，暂时简化
                    User.is_active,
                )
            )
        )
        students = students_result.scalars().all()

        # 收集训练记录数据
        training_data = await self._collect_training_data(
            db, [s.id for s in students], start_time, end_time
        )

        # 收集学习行为数据
        behavior_data = await self._collect_behavior_data(
            db, [s.id for s in students], start_time, end_time
        )

        # 收集知识点掌握数据
        knowledge_mastery_data = await self._collect_knowledge_mastery_data(
            db, [s.id for s in students], course_id
        )

        # 收集时间模式数据
        time_pattern_data = await self._collect_time_pattern_data(
            db, [s.id for s in students], start_time, end_time
        )

        return {
            "students": [{"id": s.id, "username": s.username} for s in students],
            "training_data": training_data,
            "behavior_data": behavior_data,
            "knowledge_mastery_data": knowledge_mastery_data,
            "time_pattern_data": time_pattern_data,
            "data_collection_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "period_days": analysis_period_days,
            },
        }

    async def _perform_ai_deep_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """执行AI驱动的深度分析."""
        analysis_prompt = f"""
        作为英语教学专家，请对以下学习数据进行深度分析：

        学习数据概览：
        - 学生数量：{len(data["students"])}
        - 训练记录：{len(data["training_data"])}
        - 分析周期：{data["data_collection_period"]["period_days"]}天

        训练数据统计：
        {json.dumps(data["training_data"], ensure_ascii=False, indent=2)[:1000]}...

        行为数据统计：
        {json.dumps(data["behavior_data"], ensure_ascii=False, indent=2)[:1000]}...

        请从以下维度进行分析：
        1. 班级整体学习水平评估
        2. 学习进度和掌握度分析
        3. 学习行为模式识别
        4. 知识点薄弱环节识别
        5. 学习效率和参与度评估
        6. 个体差异和分层建议

        请以JSON格式返回分析结果，包含：
        {{
            "overall_assessment": {{
                "class_level": "初级/中级/高级",
                "average_progress": 0.0-1.0,
                "engagement_level": "低/中/高",
                "learning_efficiency": 0.0-1.0
            }},
            "knowledge_analysis": {{
                "strong_areas": ["知识点1", "知识点2"],
                "weak_areas": ["知识点3", "知识点4"],
                "mastery_distribution": {{"excellent": 0, "good": 0, "average": 0, "poor": 0}}
            }},
            "behavior_patterns": {{
                "peak_learning_hours": ["时间段1", "时间段2"],
                "average_session_duration": 0,
                "learning_consistency": 0.0-1.0
            }},
            "individual_insights": [
                {{
                    "student_id": "学生ID",
                    "performance_level": "优秀/良好/一般/需要帮助",
                    "learning_style": "视觉型/听觉型/动手型",
                    "key_challenges": ["挑战1", "挑战2"],
                    "strengths": ["优势1", "优势2"]
                }}
            ],
            "teaching_recommendations": [
                "建议1", "建议2", "建议3"
            ]
        }}
        """

        success, ai_response, error = await self.deepseek_service.generate_completion(
            prompt=analysis_prompt,
            model=None,
            temperature=0.3,
            max_tokens=4096,
            user_id=None,
            task_type="learning_analysis",
        )

        if not success or not ai_response:
            logger.warning(f"AI分析失败，使用默认分析: {error}")
            return self._generate_fallback_analysis(data)

        return ai_response

    async def _generate_learning_predictions(
        self, data: dict[str, Any], ai_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """生成学习预测模型."""
        try:
            # 基于历史数据预测未来2-4周的学习趋势
            prediction_prompt = f"""
            基于以下学习数据和AI分析结果，预测学生未来2-4周的学习趋势：

            当前分析结果：
            {json.dumps(ai_analysis, ensure_ascii=False, indent=2)[:1500]}

            历史训练数据：
            {json.dumps(data["training_data"], ensure_ascii=False, indent=2)[:1000]}

            请预测：
            1. 班级整体进步趋势
            2. 个人学习轨迹预测
            3. 可能出现的学习困难
            4. 建议的干预时机

            返回JSON格式：
            {{
                "class_predictions": {{
                    "overall_trend": "上升/稳定/下降",
                    "expected_progress_rate": 0.0-1.0,
                    "predicted_challenges": ["挑战1", "挑战2"],
                    "intervention_recommendations": ["建议1", "建议2"]
                }},
                "individual_predictions": [
                    {{
                        "student_id": "学生ID",
                        "predicted_performance": "优秀/良好/一般/需要帮助",
                        "risk_level": "低/中/高",
                        "recommended_actions": ["行动1", "行动2"]
                    }}
                ],
                "timeline_predictions": {{
                    "week_1": {{"focus_areas": ["重点1"], "expected_outcomes": ["结果1"]}},
                    "week_2": {{"focus_areas": ["重点2"], "expected_outcomes": ["结果2"]}},
                    "week_3": {{"focus_areas": ["重点3"], "expected_outcomes": ["结果3"]}},
                    "week_4": {{"focus_areas": ["重点4"], "expected_outcomes": ["结果4"]}}
                }}
            }}
            """

            success, prediction_response, error = await self.deepseek_service.generate_completion(
                prompt=prediction_prompt,
                model=None,
                temperature=0.2,
                max_tokens=3072,
                user_id=None,
                task_type="learning_prediction",
            )

            if not success or not prediction_response:
                logger.warning(f"预测生成失败，使用默认预测: {error}")
                return self._generate_fallback_predictions(data)

            return prediction_response

        except Exception as e:
            logger.error(f"生成学习预测失败: {str(e)}")
            return self._generate_fallback_predictions(data)

    async def _assess_learning_risks(
        self, data: dict[str, Any], ai_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """评估学习风险和预警."""
        risk_students: list[dict[str, Any]] = []
        warning_indicators: list[str] = []

        # 分析训练数据中的风险指标
        for student_data in data.get("training_data", []):
            student_id = student_data.get("student_id")
            if not student_id:
                continue

            # 计算风险指标
            accuracy_rate = student_data.get("accuracy_rate", 0)
            consistency = student_data.get("consistency", 0)
            engagement = student_data.get("engagement_level", 0)

            risk_score = 0
            risk_factors = []

            # 准确率低于60%
            if accuracy_rate < 0.6:
                risk_score += 30
                risk_factors.append("准确率偏低")

            # 学习一致性差
            if consistency < 0.4:
                risk_score += 25
                risk_factors.append("学习不规律")

            # 参与度低
            if engagement < 0.3:
                risk_score += 20
                risk_factors.append("参与度不足")

            # 连续3天未完成训练
            if student_data.get("consecutive_missed_days", 0) >= 3:
                risk_score += 25
                risk_factors.append("连续缺席训练")

            if risk_score >= 50:  # 高风险阈值
                risk_students.append(
                    {
                        "student_id": student_id,
                        "risk_score": risk_score,
                        "risk_level": "高" if risk_score >= 70 else "中",
                        "risk_factors": risk_factors,
                        "recommended_interventions": self._generate_intervention_recommendations(
                            risk_factors
                        ),
                    }
                )

        return {
            "risk_assessment_summary": {
                "total_students": len(data.get("students", [])),
                "high_risk_count": len([s for s in risk_students if s["risk_level"] == "高"]),
                "medium_risk_count": len([s for s in risk_students if s["risk_level"] == "中"]),
                "overall_risk_level": self._calculate_overall_risk_level(risk_students),
            },
            "risk_students": risk_students,
            "warning_indicators": warning_indicators,
            "intervention_priority": sorted(
                risk_students, key=lambda x: x["risk_score"], reverse=True
            )[:5],
        }

    def _generate_intervention_recommendations(self, risk_factors: list[str]) -> list[str]:
        """生成干预建议."""
        recommendations = []

        if "准确率偏低" in risk_factors:
            recommendations.append("增加基础知识点复习")
            recommendations.append("提供个性化练习题")

        if "学习不规律" in risk_factors:
            recommendations.append("建立学习计划和提醒")
            recommendations.append("设置学习目标和奖励机制")

        if "参与度不足" in risk_factors:
            recommendations.append("增加互动性学习活动")
            recommendations.append("提供学习动机激励")

        if "连续缺席训练" in risk_factors:
            recommendations.append("及时联系学生了解情况")
            recommendations.append("提供补课和辅导支持")

        return recommendations

    def _calculate_overall_risk_level(self, risk_students: list[dict[str, Any]]) -> str:
        """计算整体风险水平."""
        if not risk_students:
            return "低"

        high_risk_count = len([s for s in risk_students if s["risk_level"] == "高"])
        total_risk_count = len(risk_students)

        if high_risk_count >= 3 or total_risk_count >= 5:
            return "高"
        elif high_risk_count >= 1 or total_risk_count >= 3:
            return "中"
        else:
            return "低"

    async def _generate_personalized_recommendations(
        self,
        data: dict[str, Any],
        ai_analysis: dict[str, Any],
        prediction_results: dict[str, Any],
    ) -> dict[str, Any]:
        """生成个性化教学建议."""
        try:
            recommendations_prompt = f"""
            基于学情分析和预测结果，为每个学生生成个性化教学建议：

            AI分析结果：
            {json.dumps(ai_analysis.get("individual_insights", []), ensure_ascii=False, indent=2)[:1000]}

            预测结果：
            {json.dumps(prediction_results.get("individual_predictions", []), ensure_ascii=False, indent=2)[:1000]}

            请为每个学生生成：
            1. 个性化学习路径
            2. 推荐的学习资源
            3. 学习方法建议
            4. 进度调整建议

            返回JSON格式：
            {{
                "class_level_recommendations": {{
                    "teaching_strategy_adjustments": ["策略1", "策略2"],
                    "content_focus_areas": ["重点1", "重点2"],
                    "pacing_recommendations": "加快/保持/放慢",
                    "resource_recommendations": ["资源1", "资源2"]
                }},
                "individual_recommendations": [
                    {{
                        "student_id": "学生ID",
                        "learning_path": {{
                            "current_level": "初级/中级/高级",
                            "target_level": "初级/中级/高级",
                            "recommended_progression": ["步骤1", "步骤2", "步骤3"]
                        }},
                        "resource_recommendations": {{
                            "priority_resources": ["资源1", "资源2"],
                            "supplementary_materials": ["材料1", "材料2"],
                            "practice_types": ["练习类型1", "练习类型2"]
                        }},
                        "learning_method_suggestions": ["方法1", "方法2"],
                        "progress_adjustments": {{
                            "difficulty_adjustment": "提高/保持/降低",
                            "pace_adjustment": "加快/保持/放慢",
                            "focus_areas": ["重点1", "重点2"]
                        }}
                    }}
                ]
            }}
            """

            (
                success,
                recommendations_response,
                error,
            ) = await self.deepseek_service.generate_completion(
                prompt=recommendations_prompt,
                model=None,
                temperature=0.3,
                max_tokens=4096,
                user_id=None,
                task_type="personalized_recommendations",
            )

            if not success or not recommendations_response:
                logger.warning(f"个性化建议生成失败，使用默认建议: {error}")
                return self._generate_fallback_recommendations(data)

            return recommendations_response

        except Exception as e:
            logger.error(f"生成个性化建议失败: {str(e)}")
            return self._generate_fallback_recommendations(data)

    async def _generate_overall_insights(
        self,
        ai_analysis: dict[str, Any],
        prediction_results: dict[str, Any],
        risk_assessment: dict[str, Any],
    ) -> dict[str, Any]:
        """生成整体洞察和建议."""
        return {
            "key_insights": [
                f"班级整体水平：{ai_analysis.get('overall_assessment', {}).get('class_level', '未知')}",
                f"学习参与度：{ai_analysis.get('overall_assessment', {}).get('engagement_level', '未知')}",
                f"风险学生数量：{risk_assessment.get('risk_assessment_summary', {}).get('high_risk_count', 0)}人",
                f"预测趋势：{prediction_results.get('class_predictions', {}).get('overall_trend', '未知')}",
            ],
            "priority_actions": [
                "关注高风险学生的学习状况",
                "加强薄弱知识点的教学",
                "调整教学策略以提高参与度",
                "实施个性化学习计划",
            ],
            "success_indicators": [
                "学生准确率提升至75%以上",
                "学习一致性达到60%以上",
                "高风险学生数量减少50%",
                "班级整体参与度提升",
            ],
        }

    # 辅助方法
    async def _collect_training_data(
        self,
        db: AsyncSession,
        student_ids: list[int],
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """收集训练数据."""
        training_data = []

        for student_id in student_ids:
            # 获取学生的训练记录
            records_result = await db.execute(
                select(TrainingRecord)
                .where(
                    and_(
                        TrainingRecord.student_id == student_id,
                        TrainingRecord.created_at >= start_time,
                        TrainingRecord.created_at <= end_time,
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
            )
            records = records_result.scalars().all()

            if records:
                # 计算统计指标
                total_records = len(records)
                correct_records = len([r for r in records if r.is_correct])
                accuracy_rate = correct_records / total_records if total_records > 0 else 0

                avg_time = (
                    sum(r.time_spent for r in records if r.time_spent) / total_records
                    if total_records > 0
                    else 0
                )

                training_data.append(
                    {
                        "student_id": student_id,
                        "total_attempts": total_records,
                        "correct_attempts": correct_records,
                        "accuracy_rate": accuracy_rate,
                        "average_time_per_question": avg_time,
                        "consistency": self._calculate_consistency(list(records)),
                        "engagement_level": min(total_records / 30, 1.0),  # 基于训练频率
                        "consecutive_missed_days": self._calculate_missed_days(
                            list(records), start_time, end_time
                        ),
                    }
                )

        return training_data

    async def _collect_behavior_data(
        self,
        db: AsyncSession,
        student_ids: list[int],
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """收集学习行为数据."""
        # 这里可以扩展收集更多行为数据
        return {
            "total_students_analyzed": len(student_ids),
            "analysis_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    async def _collect_knowledge_mastery_data(
        self, db: AsyncSession, student_ids: list[int], course_id: int
    ) -> dict[str, Any]:
        """收集知识点掌握数据."""
        # 这里可以扩展收集知识点掌握情况
        return {
            "course_id": course_id,
            "students_count": len(student_ids),
        }

    async def _collect_time_pattern_data(
        self,
        db: AsyncSession,
        student_ids: list[int],
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """收集时间模式数据."""
        # 这里可以扩展收集学习时间模式
        return {
            "analysis_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    def _calculate_consistency(self, records: list[Any]) -> float:
        """计算学习一致性."""
        if len(records) < 2:
            return 0.0

        # 简单的一致性计算：基于训练间隔的标准差
        dates = [r.created_at.date() for r in records]
        unique_dates = list(set(dates))

        if len(unique_dates) < 2:
            return 0.0

        # 计算训练天数的分布
        date_counts: dict[Any, int] = {}
        for date in dates:
            date_counts[date] = date_counts.get(date, 0) + 1

        # 一致性 = 1 - (标准差 / 平均值)
        counts = list(date_counts.values())
        if len(counts) > 1:
            mean_count = sum(counts) / len(counts)
            variance = sum((x - mean_count) ** 2 for x in counts) / len(counts)
            std_dev = variance**0.5
            consistency = max(0, 1 - (std_dev / mean_count if mean_count > 0 else 1))
            return min(consistency, 1.0)

        return 1.0

    def _calculate_missed_days(
        self, records: list[Any], start_time: datetime, end_time: datetime
    ) -> int:
        """计算连续缺席天数."""
        if not records:
            return (end_time - start_time).days

        # 获取最近的训练日期
        latest_record = max(records, key=lambda r: r.created_at)
        days_since_last = (end_time - latest_record.created_at).days

        return int(max(0, days_since_last))

    def _calculate_data_quality_score(self, data: dict[str, Any]) -> float:
        """计算数据质量评分."""
        score = 0.0

        # 基于数据完整性评分
        if data.get("training_data"):
            score += 0.4
        if data.get("behavior_data"):
            score += 0.2
        if data.get("knowledge_mastery_data"):
            score += 0.2
        if data.get("time_pattern_data"):
            score += 0.2

        return min(score, 1.0)

    def _generate_fallback_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """生成默认分析结果."""
        return {
            "overall_assessment": {
                "class_level": "中级",
                "average_progress": 0.6,
                "engagement_level": "中",
                "learning_efficiency": 0.65,
            },
            "knowledge_analysis": {
                "strong_areas": ["基础词汇", "语法结构"],
                "weak_areas": ["听力理解", "写作表达"],
                "mastery_distribution": {
                    "excellent": 2,
                    "good": 5,
                    "average": 8,
                    "poor": 3,
                },
            },
            "behavior_patterns": {
                "peak_learning_hours": ["19:00-21:00", "14:00-16:00"],
                "average_session_duration": 45,
                "learning_consistency": 0.6,
            },
            "individual_insights": [],
            "teaching_recommendations": [
                "加强听力训练",
                "增加写作练习",
                "保持当前教学节奏",
            ],
        }

    def _generate_fallback_predictions(self, data: dict[str, Any]) -> dict[str, Any]:
        """生成默认预测结果."""
        return {
            "class_predictions": {
                "overall_trend": "稳定",
                "expected_progress_rate": 0.7,
                "predicted_challenges": ["听力理解", "写作技巧"],
                "intervention_recommendations": ["增加听力练习", "强化写作指导"],
            },
            "individual_predictions": [],
            "timeline_predictions": {
                "week_1": {
                    "focus_areas": ["基础巩固"],
                    "expected_outcomes": ["准确率提升5%"],
                },
                "week_2": {
                    "focus_areas": ["听力强化"],
                    "expected_outcomes": ["听力理解改善"],
                },
                "week_3": {
                    "focus_areas": ["写作练习"],
                    "expected_outcomes": ["写作质量提升"],
                },
                "week_4": {
                    "focus_areas": ["综合复习"],
                    "expected_outcomes": ["整体水平提升"],
                },
            },
        }

    def _generate_fallback_recommendations(self, data: dict[str, Any]) -> dict[str, Any]:
        """生成默认个性化建议."""
        return {
            "class_level_recommendations": {
                "teaching_strategy_adjustments": ["增加互动环节", "强化实践练习"],
                "content_focus_areas": ["听力理解", "写作技巧"],
                "pacing_recommendations": "保持",
                "resource_recommendations": ["听力材料", "写作范文"],
            },
            "individual_recommendations": [],
        }
