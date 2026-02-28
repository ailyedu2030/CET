"""个性化学习建议服务 - 🔥需求21第三阶段个性化推荐核心实现.

个性化建议功能：
- 结合第二阶段精确自适应算法
- 基于AI分析结果生成具体改进方案
- 多维度个性化推荐
- 可执行的学习建议
- 动态调整建议策略
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import TrainingType
from app.training.services.ai_analysis_service import AIAnalysisService
from app.training.services.precise_adaptive_service import PreciseAdaptiveService

logger = logging.getLogger(__name__)


class PersonalizedRecommendationService:
    """个性化学习建议服务 - 结合AI分析和自适应算法的智能推荐."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai_analysis_service = AIAnalysisService(db)
        self.precise_adaptive_service = PreciseAdaptiveService(db)

        # 个性化推荐配置
        self.recommendation_config = {
            "recommendation_categories": [
                "difficulty_adjustment",  # 难度调整
                "learning_strategy",  # 学习策略
                "time_management",  # 时间管理
                "knowledge_reinforcement",  # 知识强化
                "motivation_enhancement",  # 动机提升
                "skill_development",  # 技能发展
            ],
            "priority_levels": {
                "critical": 1,  # 关键建议
                "important": 2,  # 重要建议
                "helpful": 3,  # 有用建议
                "optional": 4,  # 可选建议
            },
            "personalization_factors": {
                "learning_style_weight": 0.25,  # 学习风格权重
                "performance_level_weight": 0.25,  # 表现水平权重
                "progress_rate_weight": 0.20,  # 进步速度权重
                "engagement_level_weight": 0.15,  # 参与度权重
                "difficulty_preference_weight": 0.15,  # 难度偏好权重
            },
            "recommendation_limits": {
                "max_recommendations_per_category": 3,
                "max_total_recommendations": 10,
                "min_confidence_threshold": 0.6,
            },
        }

    async def generate_personalized_recommendations(
        self, student_id: int, training_type: TrainingType | None = None
    ) -> dict[str, Any]:
        """生成个性化学习建议."""
        try:
            logger.info(
                f"开始生成个性化学习建议: 学生{student_id}, 训练类型{training_type}"
            )

            # 1. 获取AI深度分析结果
            ai_analysis = (
                await self.ai_analysis_service.generate_comprehensive_analysis_report(
                    student_id, training_type
                )
            )

            if not ai_analysis.get("analysis_available"):
                return {
                    "recommendations_available": False,
                    "reason": "AI分析数据不足",
                    "minimum_requirements": ai_analysis.get("minimum_requirements", {}),
                }

            # 2. 获取精确自适应算法结果
            adaptive_results = {}
            if training_type:
                adaptive_results = (
                    await self.precise_adaptive_service.execute_precise_adjustment(
                        student_id, training_type
                    )
                )

            # 3. 生成多维度个性化建议
            recommendations = await self._generate_multi_dimensional_recommendations(
                student_id, ai_analysis, adaptive_results, training_type
            )

            # 4. 优先级排序和过滤
            prioritized_recommendations = self._prioritize_and_filter_recommendations(
                recommendations, ai_analysis
            )

            # 5. 生成执行计划
            execution_plan = self._generate_execution_plan(prioritized_recommendations)

            # 6. 计算个性化程度
            personalization_score = self._calculate_personalization_score(
                prioritized_recommendations, ai_analysis, adaptive_results
            )

            return {
                "recommendations_available": True,
                "student_id": student_id,
                "training_type": training_type.name if training_type else "ALL",
                "generation_timestamp": datetime.now(),
                # 核心推荐结果
                "recommendations": prioritized_recommendations,
                "execution_plan": execution_plan,
                # 个性化指标
                "personalization_score": personalization_score,
                "meets_personalization_target": personalization_score >= 0.80,
                # 基础数据
                "ai_analysis_summary": self._extract_analysis_summary(ai_analysis),
                "adaptive_algorithm_summary": self._extract_adaptive_summary(
                    adaptive_results
                ),
                # 元数据
                "recommendation_metadata": {
                    "total_recommendations": len(prioritized_recommendations),
                    "categories_covered": len(
                        {r["category"] for r in prioritized_recommendations}
                    ),
                    "average_confidence": (
                        sum(r["confidence"] for r in prioritized_recommendations)
                        / len(prioritized_recommendations)
                        if prioritized_recommendations
                        else 0
                    ),
                    "generation_method": "ai_adaptive_hybrid",
                },
            }

        except Exception as e:
            logger.error(f"生成个性化学习建议失败: {str(e)}")
            return {
                "recommendations_available": False,
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def _generate_multi_dimensional_recommendations(
        self,
        student_id: int,
        ai_analysis: dict[str, Any],
        adaptive_results: dict[str, Any],
        training_type: TrainingType | None,
    ) -> list[dict[str, Any]]:
        """生成多维度个性化建议."""
        recommendations = []

        try:
            # 1. 基于AI分析的建议
            ai_recommendations = self._generate_ai_based_recommendations(ai_analysis)
            recommendations.extend(ai_recommendations)

            # 2. 基于自适应算法的建议
            adaptive_recommendations = self._generate_adaptive_based_recommendations(
                adaptive_results
            )
            recommendations.extend(adaptive_recommendations)

            # 3. 基于学习模式的建议
            pattern_recommendations = self._generate_pattern_based_recommendations(
                ai_analysis
            )
            recommendations.extend(pattern_recommendations)

            # 4. 基于知识掌握度的建议
            mastery_recommendations = self._generate_mastery_based_recommendations(
                ai_analysis
            )
            recommendations.extend(mastery_recommendations)

            # 5. 基于学习效率的建议
            efficiency_recommendations = (
                self._generate_efficiency_based_recommendations(ai_analysis)
            )
            recommendations.extend(efficiency_recommendations)

            return recommendations

        except Exception as e:
            logger.error(f"生成多维度建议失败: {str(e)}")
            return []

    def _generate_ai_based_recommendations(
        self, ai_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """基于AI分析生成建议."""
        recommendations = []

        try:
            ai_insights = ai_analysis.get("ai_insights", {})
            ai_recommendations = ai_insights.get("personalized_recommendations", [])

            for i, rec in enumerate(ai_recommendations[:3]):  # 最多3个AI建议
                recommendations.append(
                    {
                        "id": f"ai_{i + 1}",
                        "category": "ai_insight",
                        "title": f"AI深度分析建议 {i + 1}",
                        "description": rec,
                        "priority": "important",
                        "confidence": ai_insights.get("confidence_score", 0.8),
                        "source": "deepseek_ai",
                        "actionable": True,
                        "estimated_impact": "high",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"生成AI建议失败: {str(e)}")
            return []

    def _generate_adaptive_based_recommendations(
        self, adaptive_results: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """基于自适应算法生成建议."""
        recommendations: list[dict[str, Any]] = []

        try:
            if not adaptive_results.get("adjustment_made"):
                return recommendations

            adjustment_type = adaptive_results.get("adjustment_type")
            current_accuracy = adaptive_results.get("current_accuracy", 0)
            algorithm_precision = adaptive_results.get("algorithm_precision", 0)
            personalization_score = adaptive_results.get("personalization_score", 0)

            # 基于调整类型生成建议
            if adjustment_type == "upgrade":
                recommendations.append(
                    {
                        "id": "adaptive_upgrade",
                        "category": "difficulty_adjustment",
                        "title": "难度提升建议",
                        "description": f"基于{current_accuracy:.1%}的优秀表现，建议提升训练难度以保持挑战性",
                        "priority": "important",
                        "confidence": algorithm_precision,
                        "source": "precise_adaptive_algorithm",
                        "actionable": True,
                        "estimated_impact": "medium",
                        "specific_actions": [
                            "尝试更高难度的练习题",
                            "增加复杂题型的比例",
                            "设置更具挑战性的目标",
                        ],
                    }
                )
            elif adjustment_type == "downgrade":
                recommendations.append(
                    {
                        "id": "adaptive_downgrade",
                        "category": "difficulty_adjustment",
                        "title": "难度调整建议",
                        "description": f"当前{current_accuracy:.1%}正确率偏低，建议适当降低难度巩固基础",
                        "priority": "critical",
                        "confidence": algorithm_precision,
                        "source": "precise_adaptive_algorithm",
                        "actionable": True,
                        "estimated_impact": "high",
                        "specific_actions": [
                            "回顾基础知识点",
                            "增加基础练习时间",
                            "寻求额外指导和帮助",
                        ],
                    }
                )

            # 基于个性化程度生成建议
            if personalization_score < 0.8:
                recommendations.append(
                    {
                        "id": "personalization_enhancement",
                        "category": "learning_strategy",
                        "title": "个性化学习策略优化",
                        "description": f"当前个性化程度{personalization_score:.1%}，建议调整学习方式以更好匹配个人特点",
                        "priority": "helpful",
                        "confidence": 0.8,
                        "source": "precise_adaptive_algorithm",
                        "actionable": True,
                        "estimated_impact": "medium",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"生成自适应建议失败: {str(e)}")
            return []

    def _generate_pattern_based_recommendations(
        self, ai_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """基于学习模式生成建议."""
        recommendations = []

        try:
            learning_patterns = ai_analysis.get("learning_patterns", {})
            learning_style = learning_patterns.get("learning_style", {})
            time_patterns = learning_patterns.get("time_patterns", {})

            # 基于学习风格的建议
            style_type = learning_style.get("primary_style", "unknown")
            if style_type == "visual_learner":
                recommendations.append(
                    {
                        "id": "visual_learning",
                        "category": "learning_strategy",
                        "title": "视觉学习策略优化",
                        "description": "您是视觉学习者，建议多使用图表、图像和视觉辅助材料",
                        "priority": "helpful",
                        "confidence": learning_patterns.get("confidence", 0.7),
                        "source": "learning_pattern_analysis",
                        "actionable": True,
                        "estimated_impact": "medium",
                        "specific_actions": [
                            "使用思维导图整理知识点",
                            "观看相关教学视频",
                            "制作知识点卡片",
                        ],
                    }
                )
            elif style_type == "auditory_learner":
                recommendations.append(
                    {
                        "id": "auditory_learning",
                        "category": "learning_strategy",
                        "title": "听觉学习策略优化",
                        "description": "您是听觉学习者，建议多进行口语练习和听力训练",
                        "priority": "helpful",
                        "confidence": learning_patterns.get("confidence", 0.7),
                        "source": "learning_pattern_analysis",
                        "actionable": True,
                        "estimated_impact": "medium",
                        "specific_actions": [
                            "大声朗读学习材料",
                            "参与讨论和对话练习",
                            "使用音频学习资源",
                        ],
                    }
                )

            # 基于时间模式的建议
            optimal_time = time_patterns.get("optimal_learning_time", "unknown")
            if optimal_time != "unknown":
                recommendations.append(
                    {
                        "id": "time_optimization",
                        "category": "time_management",
                        "title": "学习时间优化",
                        "description": f"根据您的学习模式，{optimal_time}是您的最佳学习时间",
                        "priority": "helpful",
                        "confidence": 0.8,
                        "source": "time_pattern_analysis",
                        "actionable": True,
                        "estimated_impact": "medium",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"生成模式建议失败: {str(e)}")
            return []

    def _generate_mastery_based_recommendations(
        self, ai_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """基于知识掌握度生成建议."""
        recommendations = []

        try:
            knowledge_mastery = ai_analysis.get("knowledge_mastery", {})
            weak_areas = knowledge_mastery.get("weak_areas", [])
            overall_score = knowledge_mastery.get("overall_mastery_score", 0)

            # 薄弱环节强化建议
            if weak_areas:
                recommendations.append(
                    {
                        "id": "weak_areas_reinforcement",
                        "category": "knowledge_reinforcement",
                        "title": "薄弱知识点强化",
                        "description": f"重点关注薄弱知识点：{', '.join(weak_areas[:3])}",
                        "priority": "critical" if overall_score < 0.6 else "important",
                        "confidence": knowledge_mastery.get("confidence", 0.8),
                        "source": "knowledge_mastery_analysis",
                        "actionable": True,
                        "estimated_impact": "high",
                        "specific_actions": [
                            f"针对{area}进行专项练习" for area in weak_areas[:3]
                        ]
                        + ["寻找相关学习资源", "制定专项学习计划"],
                    }
                )

            # 整体掌握度建议
            if overall_score < 0.7:
                recommendations.append(
                    {
                        "id": "overall_mastery_improvement",
                        "category": "knowledge_reinforcement",
                        "title": "整体知识掌握度提升",
                        "description": f"当前整体掌握度{overall_score:.1%}，建议系统性复习和练习",
                        "priority": "important",
                        "confidence": 0.9,
                        "source": "knowledge_mastery_analysis",
                        "actionable": True,
                        "estimated_impact": "high",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"生成掌握度建议失败: {str(e)}")
            return []

    def _generate_efficiency_based_recommendations(
        self, ai_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """基于学习效率生成建议."""
        recommendations = []

        try:
            efficiency_assessment = ai_analysis.get("efficiency_assessment", {})
            overall_efficiency = efficiency_assessment.get("overall_efficiency", 0)
            improvement_suggestions = efficiency_assessment.get(
                "improvement_suggestions", []
            )

            # 效率提升建议
            if overall_efficiency < 0.7:
                recommendations.append(
                    {
                        "id": "efficiency_improvement",
                        "category": "learning_strategy",
                        "title": "学习效率提升",
                        "description": f"当前学习效率{overall_efficiency:.1%}，建议优化学习方法",
                        "priority": "important",
                        "confidence": efficiency_assessment.get("confidence", 0.8),
                        "source": "efficiency_assessment",
                        "actionable": True,
                        "estimated_impact": "high",
                        "specific_actions": (
                            improvement_suggestions[:3]
                            if improvement_suggestions
                            else [
                                "制定明确的学习目标",
                                "消除学习环境干扰",
                                "采用番茄工作法等时间管理技巧",
                            ]
                        ),
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"生成效率建议失败: {str(e)}")
            return []

    def _prioritize_and_filter_recommendations(
        self, recommendations: list[dict[str, Any]], ai_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """优先级排序和过滤建议."""
        try:
            # 过滤低置信度建议
            limits: dict[str, Any] = self.recommendation_config["recommendation_limits"]
            min_confidence = limits["min_confidence_threshold"]
            filtered_recommendations = [
                rec
                for rec in recommendations
                if rec.get("confidence", 0) >= min_confidence
            ]

            # 按优先级和置信度排序
            priority_order: dict[str, int] = self.recommendation_config[
                "priority_levels"
            ]

            def sort_key(rec: dict[str, Any]) -> tuple[int, float]:
                priority_score = priority_order.get(rec.get("priority", "optional"), 5)
                confidence_score = rec.get("confidence", 0)
                return (
                    priority_score,
                    -confidence_score,
                )  # 优先级越低数字越小，置信度越高越好

            sorted_recommendations = sorted(filtered_recommendations, key=sort_key)

            # 限制每个类别的建议数量
            limits_2: dict[str, Any] = self.recommendation_config[
                "recommendation_limits"
            ]
            max_per_category = limits_2["max_recommendations_per_category"]
            category_counts: dict[str, int] = {}
            final_recommendations = []

            for rec in sorted_recommendations:
                category = rec.get("category", "other")
                if category_counts.get(category, 0) < max_per_category:
                    final_recommendations.append(rec)
                    category_counts[category] = category_counts.get(category, 0) + 1

            # 限制总建议数量
            limits_3: dict[str, Any] = self.recommendation_config[
                "recommendation_limits"
            ]
            max_total = limits_3["max_total_recommendations"]
            return final_recommendations[:max_total]

        except Exception as e:
            logger.error(f"优先级排序失败: {str(e)}")
            return recommendations

    def _generate_execution_plan(
        self, recommendations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """生成执行计划."""
        try:
            if not recommendations:
                return {"plan_available": False}

            # 按优先级分组
            critical_actions = [
                rec for rec in recommendations if rec.get("priority") == "critical"
            ]
            important_actions = [
                rec for rec in recommendations if rec.get("priority") == "important"
            ]
            helpful_actions = [
                rec for rec in recommendations if rec.get("priority") == "helpful"
            ]

            # 生成时间线
            timeline = []

            # 第一周：关键建议
            if critical_actions:
                timeline.append(
                    {
                        "period": "第1周",
                        "focus": "关键问题解决",
                        "actions": [
                            {
                                "title": action["title"],
                                "description": action["description"],
                                "specific_actions": action.get("specific_actions", []),
                            }
                            for action in critical_actions
                        ],
                    }
                )

            # 第二周：重要建议
            if important_actions:
                timeline.append(
                    {
                        "period": "第2-3周",
                        "focus": "重要改进实施",
                        "actions": [
                            {
                                "title": action["title"],
                                "description": action["description"],
                                "specific_actions": action.get("specific_actions", []),
                            }
                            for action in important_actions
                        ],
                    }
                )

            # 第三周及以后：有用建议
            if helpful_actions:
                timeline.append(
                    {
                        "period": "第4周及以后",
                        "focus": "持续优化",
                        "actions": [
                            {
                                "title": action["title"],
                                "description": action["description"],
                                "specific_actions": action.get("specific_actions", []),
                            }
                            for action in helpful_actions
                        ],
                    }
                )

            return {
                "plan_available": True,
                "timeline": timeline,
                "total_duration": "4周+",
                "success_metrics": [
                    "学习效率提升15%以上",
                    "知识掌握度提升10%以上",
                    "个性化程度达到80%以上",
                ],
                "review_schedule": [
                    {"period": "1周后", "focus": "关键问题解决效果评估"},
                    {"period": "3周后", "focus": "整体改进效果评估"},
                    {"period": "6周后", "focus": "长期效果跟踪"},
                ],
            }

        except Exception as e:
            logger.error(f"生成执行计划失败: {str(e)}")
            return {"plan_available": False, "error": str(e)}

    def _calculate_personalization_score(
        self,
        recommendations: list[dict[str, Any]],
        ai_analysis: dict[str, Any],
        adaptive_results: dict[str, Any],
    ) -> float:
        """计算个性化程度分数."""
        try:
            personalization_factors: list[float] = []

            # 1. 学习风格匹配度
            learning_patterns = ai_analysis.get("learning_patterns", {})
            style_confidence = learning_patterns.get("confidence", 0)
            style_based_recs = sum(
                1
                for rec in recommendations
                if "learning_strategy" in rec.get("category", "")
            )
            style_factor = min(
                1.0,
                style_confidence * (style_based_recs / max(len(recommendations), 1)),
            )
            personalization_factors.append(style_factor)

            # 2. 表现水平适应度
            efficiency_assessment = ai_analysis.get("efficiency_assessment", {})
            efficiency_level = efficiency_assessment.get("efficiency_level", "unknown")
            performance_factor = 0.8 if efficiency_level != "unknown" else 0.5
            personalization_factors.append(performance_factor)

            # 3. 自适应算法个性化程度
            adaptive_personalization = adaptive_results.get(
                "personalization_score", 0.5
            )
            personalization_factors.append(adaptive_personalization)

            # 4. 建议多样性
            categories = {rec.get("category", "other") for rec in recommendations}
            diversity_factor = min(1.0, len(categories) / 4)  # 4个类别为满分
            personalization_factors.append(diversity_factor)

            # 5. 置信度加权
            if recommendations:
                avg_confidence = sum(
                    rec.get("confidence", 0) for rec in recommendations
                ) / len(recommendations)
                personalization_factors.append(avg_confidence)

            # 加权计算
            weights: dict[str, float] = self.recommendation_config[
                "personalization_factors"
            ]
            weighted_score = (
                personalization_factors[0] * weights["learning_style_weight"]
                + personalization_factors[1] * weights["performance_level_weight"]
                + personalization_factors[2] * weights["progress_rate_weight"]
                + personalization_factors[3] * weights["engagement_level_weight"]
                + (
                    personalization_factors[4]
                    if len(personalization_factors) > 4
                    else 0.5
                )
                * weights["difficulty_preference_weight"]
            )

            result: float = min(1.0, weighted_score)
            return result

        except Exception as e:
            logger.error(f"计算个性化分数失败: {str(e)}")
            return 0.5

    def _extract_analysis_summary(self, ai_analysis: dict[str, Any]) -> dict[str, Any]:
        """提取AI分析摘要."""
        return {
            "analysis_available": ai_analysis.get("analysis_available", False),
            "overall_confidence": ai_analysis.get("confidence_metrics", {}).get(
                "overall_confidence", 0
            ),
            "key_insights": ai_analysis.get("ai_insights", {}).get(
                "ai_generated_insights", []
            )[:3],
            "analysis_duration": ai_analysis.get("analysis_duration", 0),
        }

    def _extract_adaptive_summary(
        self, adaptive_results: dict[str, Any]
    ) -> dict[str, Any]:
        """提取自适应算法摘要."""
        return {
            "adjustment_made": adaptive_results.get("adjustment_made", False),
            "adjustment_type": adaptive_results.get("adjustment_type"),
            "algorithm_precision": adaptive_results.get("algorithm_precision", 0),
            "personalization_score": adaptive_results.get("personalization_score", 0),
            "meets_targets": {
                "precision": adaptive_results.get("meets_precision_target", False),
                "personalization": adaptive_results.get(
                    "meets_personalization_target", False
                ),
            },
        }

    async def update_recommendation_feedback(
        self, student_id: int, recommendation_id: str, feedback: dict[str, Any]
    ) -> dict[str, Any]:
        """更新建议反馈."""
        try:
            # 这里可以实现反馈收集和学习机制
            # 暂时记录日志
            logger.info(
                f"收到建议反馈: 学生{student_id}, 建议{recommendation_id}, 反馈{feedback}"
            )

            return {
                "feedback_recorded": True,
                "recommendation_id": recommendation_id,
                "feedback": feedback,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"更新建议反馈失败: {str(e)}")
            return {"feedback_recorded": False, "error": str(e)}

    def get_recommendation_statistics(self, student_id: int) -> dict[str, Any]:
        """获取推荐统计信息."""
        try:
            # 这里可以实现推荐效果统计
            # 暂时返回基础统计
            return {
                "student_id": student_id,
                "total_recommendations_generated": 0,  # 从数据库或缓存获取
                "recommendations_followed": 0,  # 从反馈数据获取
                "average_effectiveness": 0.0,  # 从效果评估获取
                "last_generation_time": None,  # 最后生成时间
                "personalization_trend": "improving",  # 个性化趋势
            }

        except Exception as e:
            logger.error(f"获取推荐统计失败: {str(e)}")
            return {"error": str(e)}
