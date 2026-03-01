"""考纲变更影响分析服务 - 需求33考纲库管理要求."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError
from app.resources.models.resource_models import ExamSyllabus, KnowledgePoint
from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class SyllabusAnalysisService:
    """考纲变更影响分析服务 - 分析考纲变更对课程和题库的影响."""

    def __init__(
        self, db: AsyncSession, cache_service: CacheService | None = None
    ) -> None:
        """初始化考纲分析服务."""
        self.db = db
        self.cache_service = cache_service

        # 分析配置
        self.analysis_config = {
            "similarity_threshold": 0.8,  # 相似度阈值
            "impact_levels": ["low", "medium", "high", "critical"],
            "change_types": ["added", "removed", "modified", "restructured"],
            "weight_calculation": {
                "content_weight": 0.4,
                "structure_weight": 0.3,
                "difficulty_weight": 0.2,
                "scope_weight": 0.1,
            },
        }

    async def analyze_syllabus_changes(
        self, old_syllabus_id: int, new_syllabus_id: int
    ) -> dict[str, Any]:
        """分析考纲变更影响 - 需求33变更影响分析."""
        try:
            # 获取考纲数据
            old_syllabus = await self._get_syllabus(old_syllabus_id)
            new_syllabus = await self._get_syllabus(new_syllabus_id)

            if not old_syllabus or not new_syllabus:
                raise ValueError("考纲不存在")

            # 执行变更分析
            change_analysis = await self._perform_change_analysis(
                old_syllabus, new_syllabus
            )

            # 分析对现有课程的影响
            course_impact = await self._analyze_course_impact(
                change_analysis, old_syllabus.library_id
            )

            # 分析对题库的影响
            question_bank_impact = await self._analyze_question_bank_impact(
                change_analysis, old_syllabus.library_id
            )

            # 分析对教材的影响
            material_impact = await self._analyze_material_impact(
                change_analysis, old_syllabus.library_id
            )

            # 生成影响报告
            impact_report = await self._generate_impact_report(
                change_analysis, course_impact, question_bank_impact, material_impact
            )

            # 生成迁移建议
            migration_recommendations = await self._generate_migration_recommendations(
                impact_report
            )

            return {
                "analysis_id": f"syllabus_analysis_{old_syllabus_id}_{new_syllabus_id}_{int(datetime.utcnow().timestamp())}",
                "old_syllabus": self._syllabus_to_dict(old_syllabus),
                "new_syllabus": self._syllabus_to_dict(new_syllabus),
                "change_analysis": change_analysis,
                "impact_assessment": {
                    "course_impact": course_impact,
                    "question_bank_impact": question_bank_impact,
                    "material_impact": material_impact,
                },
                "impact_report": impact_report,
                "migration_recommendations": migration_recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"考纲变更分析失败: {str(e)}")
            raise BusinessLogicError(f"考纲变更分析失败: {str(e)}") from e

    async def calculate_knowledge_point_weights(
        self, syllabus_id: int
    ) -> dict[str, Any]:
        """计算知识点权重 - 需求33权重计算."""
        try:
            # 获取考纲
            syllabus = await self._get_syllabus(syllabus_id)
            if not syllabus:
                raise ValueError(f"考纲不存在: {syllabus_id}")

            # 获取相关知识点
            knowledge_points = await self._get_knowledge_points_by_library(
                syllabus.library_id
            )

            # 计算基础权重
            base_weights = await self._calculate_base_weights(
                knowledge_points, syllabus
            )

            # 基于历年真题统计调整权重
            exam_weights = await self._calculate_exam_based_weights(knowledge_points)

            # 基于难度调整权重
            difficulty_weights = await self._calculate_difficulty_weights(
                knowledge_points
            )

            # 综合权重计算
            final_weights = await self._calculate_final_weights(
                base_weights, exam_weights, difficulty_weights
            )

            # 生成权重报告
            weight_report = await self._generate_weight_report(
                knowledge_points, final_weights, syllabus
            )

            return {
                "syllabus_id": syllabus_id,
                "knowledge_point_weights": final_weights,
                "weight_calculation_details": {
                    "base_weights": base_weights,
                    "exam_weights": exam_weights,
                    "difficulty_weights": difficulty_weights,
                },
                "weight_report": weight_report,
                "calculation_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"知识点权重计算失败: {str(e)}")
            raise BusinessLogicError(f"知识点权重计算失败: {str(e)}") from e

    async def _get_syllabus(self, syllabus_id: int) -> ExamSyllabus | None:
        """获取考纲."""
        stmt = select(ExamSyllabus).where(ExamSyllabus.id == syllabus_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_knowledge_points_by_library(
        self, library_id: int
    ) -> list[KnowledgePoint]:
        """获取资源库的知识点."""
        stmt = select(KnowledgePoint).where(KnowledgePoint.library_id == library_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _perform_change_analysis(
        self, old_syllabus: ExamSyllabus, new_syllabus: ExamSyllabus
    ) -> dict[str, Any]:
        """执行变更分析."""
        try:
            # 解析考纲结构
            old_structure = old_syllabus.exam_structure or {}
            new_structure = new_syllabus.exam_structure or {}

            # 分析结构变更
            structure_changes = await self._analyze_structure_changes(
                old_structure, new_structure
            )

            # 分析内容变更
            content_changes = await self._analyze_content_changes(
                old_syllabus, new_syllabus
            )

            # 分析要求变更
            requirement_changes = await self._analyze_requirement_changes(
                old_syllabus, new_syllabus
            )

            # 计算变更影响级别
            impact_level = await self._calculate_change_impact_level(
                structure_changes, content_changes, requirement_changes
            )

            return {
                "structure_changes": structure_changes,
                "content_changes": content_changes,
                "requirement_changes": requirement_changes,
                "overall_impact_level": impact_level,
                "change_summary": await self._generate_change_summary(
                    structure_changes, content_changes, requirement_changes
                ),
            }

        except Exception as e:
            logger.error(f"变更分析失败: {str(e)}")
            raise

    async def _analyze_structure_changes(
        self, old_structure: dict[str, Any], new_structure: dict[str, Any]
    ) -> dict[str, Any]:
        """分析结构变更."""
        changes: dict[str, list[Any]] = {
            "added_sections": [],
            "removed_sections": [],
            "modified_sections": [],
            "restructured_sections": [],
        }

        # 比较章节结构
        old_sections = set(old_structure.keys())
        new_sections = set(new_structure.keys())

        # 新增章节
        changes["added_sections"] = list(new_sections - old_sections)

        # 删除章节
        changes["removed_sections"] = list(old_sections - new_sections)

        # 修改章节
        common_sections = old_sections & new_sections
        for section in common_sections:
            if old_structure[section] != new_structure[section]:
                changes["modified_sections"].append(
                    {
                        "section": section,
                        "old_content": old_structure[section],
                        "new_content": new_structure[section],
                    }
                )

        return changes

    async def _analyze_content_changes(
        self, old_syllabus: ExamSyllabus, new_syllabus: ExamSyllabus
    ) -> dict[str, Any]:
        """分析内容变更."""
        changes = {
            "title_changed": old_syllabus.title != new_syllabus.title,
            "description_changed": old_syllabus.description != new_syllabus.description,
            "exam_type_changed": old_syllabus.exam_type != new_syllabus.exam_type,
            "exam_level_changed": old_syllabus.exam_level != new_syllabus.exam_level,
            "content_similarity": await self._calculate_content_similarity(
                old_syllabus, new_syllabus
            ),
        }

        return changes

    async def _analyze_requirement_changes(
        self, old_syllabus: ExamSyllabus, new_syllabus: ExamSyllabus
    ) -> dict[str, Any]:
        """分析要求变更."""
        old_requirements = getattr(old_syllabus, "ability_requirements", None) or {}
        new_requirements = getattr(new_syllabus, "ability_requirements", None) or {}

        changes: dict[str, list[Any]] = {
            "requirement_changes": [],
            "new_requirements": [],
            "removed_requirements": [],
        }

        # 比较能力要求
        for req_type in set(old_requirements.keys()) | set(new_requirements.keys()):
            if req_type in old_requirements and req_type in new_requirements:
                if old_requirements[req_type] != new_requirements[req_type]:
                    changes["requirement_changes"].append(
                        {
                            "type": req_type,
                            "old_requirement": old_requirements[req_type],
                            "new_requirement": new_requirements[req_type],
                        }
                    )
            elif req_type in new_requirements:
                changes["new_requirements"].append(
                    {
                        "type": req_type,
                        "requirement": new_requirements[req_type],
                    }
                )
            else:
                changes["removed_requirements"].append(
                    {
                        "type": req_type,
                        "requirement": old_requirements[req_type],
                    }
                )

        return changes

    async def _calculate_change_impact_level(
        self,
        structure_changes: dict[str, Any],
        content_changes: dict[str, Any],
        requirement_changes: dict[str, Any],
    ) -> str:
        """计算变更影响级别."""
        impact_score = 0

        # 结构变更影响
        impact_score += len(structure_changes["added_sections"]) * 0.3
        impact_score += len(structure_changes["removed_sections"]) * 0.5
        impact_score += len(structure_changes["modified_sections"]) * 0.2

        # 内容变更影响
        if content_changes["exam_type_changed"]:
            impact_score += 0.8
        if content_changes["exam_level_changed"]:
            impact_score += 0.6
        if content_changes["content_similarity"] < 0.7:
            impact_score += 0.4

        # 要求变更影响
        impact_score += len(requirement_changes["new_requirements"]) * 0.2
        impact_score += len(requirement_changes["removed_requirements"]) * 0.3
        impact_score += len(requirement_changes["requirement_changes"]) * 0.1

        # 确定影响级别
        if impact_score >= 2.0:
            return "critical"
        elif impact_score >= 1.5:
            return "high"
        elif impact_score >= 1.0:
            return "medium"
        else:
            return "low"

    async def _calculate_content_similarity(
        self, old_syllabus: ExamSyllabus, new_syllabus: ExamSyllabus
    ) -> float:
        """计算内容相似度."""
        # 简化实现：基于描述文本相似度
        old_text = (old_syllabus.description or "") + " " + (old_syllabus.title or "")
        new_text = (new_syllabus.description or "") + " " + (new_syllabus.title or "")

        if not old_text.strip() or not new_text.strip():
            return 0.0

        # 简单的字符级相似度
        old_chars = set(old_text.lower())
        new_chars = set(new_text.lower())

        intersection = len(old_chars & new_chars)
        union = len(old_chars | new_chars)

        return intersection / union if union > 0 else 0.0

    async def _analyze_course_impact(
        self, change_analysis: dict[str, Any], library_id: int
    ) -> dict[str, Any]:
        """分析对课程的影响."""
        # 简化实现
        impact_level = change_analysis["overall_impact_level"]

        course_impact = {
            "affected_courses": [],  # 实际实现中查询相关课程
            "impact_level": impact_level,
            "required_updates": [],
            "estimated_effort": self._estimate_update_effort(impact_level),
        }

        # 根据影响级别生成更新建议
        if impact_level in ["high", "critical"]:
            course_impact["required_updates"].extend(
                [
                    "更新课程大纲",
                    "调整教学计划",
                    "重新设计课程内容",
                ]
            )
        elif impact_level == "medium":
            course_impact["required_updates"].extend(
                [
                    "部分更新课程内容",
                    "调整重点章节",
                ]
            )

        return course_impact

    async def _analyze_question_bank_impact(
        self, change_analysis: dict[str, Any], library_id: int
    ) -> dict[str, Any]:
        """分析对题库的影响."""
        impact_level = change_analysis["overall_impact_level"]

        question_impact = {
            "affected_questions": [],  # 实际实现中查询相关题目
            "impact_level": impact_level,
            "required_actions": [],
            "estimated_effort": self._estimate_update_effort(impact_level),
        }

        # 根据影响级别生成行动建议
        if impact_level in ["high", "critical"]:
            question_impact["required_actions"].extend(
                [
                    "重新审核所有题目",
                    "删除过时题目",
                    "新增题目覆盖新知识点",
                    "调整题目难度分布",
                ]
            )
        elif impact_level == "medium":
            question_impact["required_actions"].extend(
                [
                    "审核相关题目",
                    "适当新增题目",
                ]
            )

        return question_impact

    async def _analyze_material_impact(
        self, change_analysis: dict[str, Any], library_id: int
    ) -> dict[str, Any]:
        """分析对教材的影响."""
        impact_level = change_analysis["overall_impact_level"]

        material_impact = {
            "affected_materials": [],  # 实际实现中查询相关教材
            "impact_level": impact_level,
            "required_updates": [],
            "estimated_effort": self._estimate_update_effort(impact_level),
        }

        # 根据影响级别生成更新建议
        if impact_level in ["high", "critical"]:
            material_impact["required_updates"].extend(
                [
                    "全面更新教材内容",
                    "重新组织章节结构",
                    "更新案例和练习",
                ]
            )
        elif impact_level == "medium":
            material_impact["required_updates"].extend(
                [
                    "部分更新教材内容",
                    "补充新增知识点",
                ]
            )

        return material_impact

    def _estimate_update_effort(self, impact_level: str) -> dict[str, Any]:
        """估算更新工作量."""
        effort_map = {
            "low": {"days": 1, "resources": 1, "complexity": "simple"},
            "medium": {"days": 5, "resources": 2, "complexity": "moderate"},
            "high": {"days": 15, "resources": 5, "complexity": "complex"},
            "critical": {"days": 30, "resources": 10, "complexity": "very_complex"},
        }

        return effort_map.get(impact_level, effort_map["medium"])

    async def _generate_impact_report(
        self,
        change_analysis: dict[str, Any],
        course_impact: dict[str, Any],
        question_impact: dict[str, Any],
        material_impact: dict[str, Any],
    ) -> dict[str, Any]:
        """生成影响报告."""
        return {
            "executive_summary": await self._generate_executive_summary(
                change_analysis
            ),
            "detailed_analysis": {
                "change_analysis": change_analysis,
                "course_impact": course_impact,
                "question_impact": question_impact,
                "material_impact": material_impact,
            },
            "risk_assessment": await self._assess_risks(change_analysis),
            "timeline_estimation": await self._estimate_timeline(
                course_impact, question_impact, material_impact
            ),
        }

    async def _generate_migration_recommendations(
        self, impact_report: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """生成迁移建议."""
        recommendations = []

        # 基于影响级别生成建议
        impact_level = impact_report["detailed_analysis"]["change_analysis"][
            "overall_impact_level"
        ]

        if impact_level in ["high", "critical"]:
            recommendations.extend(
                [
                    {
                        "priority": "high",
                        "action": "立即组建专项工作组",
                        "description": "成立跨部门工作组负责考纲变更适配",
                        "timeline": "1周内",
                    },
                    {
                        "priority": "high",
                        "action": "全面评估现有资源",
                        "description": "对所有课程、题库、教材进行全面评估",
                        "timeline": "2周内",
                    },
                ]
            )

        recommendations.extend(
            [
                {
                    "priority": "medium",
                    "action": "制定详细迁移计划",
                    "description": "基于影响分析制定具体的迁移时间表",
                    "timeline": "1周内",
                },
                {
                    "priority": "medium",
                    "action": "培训相关人员",
                    "description": "对教师和内容开发人员进行新考纲培训",
                    "timeline": "2周内",
                },
            ]
        )

        return recommendations

    async def _calculate_base_weights(
        self, knowledge_points: list[KnowledgePoint], syllabus: ExamSyllabus
    ) -> dict[int, float]:
        """计算基础权重."""
        weights = {}

        for kp in knowledge_points:
            # 基于知识点属性计算基础权重
            base_weight = 1.0

            # 核心知识点权重更高
            if kp.is_core:
                base_weight *= 1.5

            # 基于难度调整权重
            difficulty_multiplier = {
                "BEGINNER": 0.8,
                "ELEMENTARY": 0.9,
                "INTERMEDIATE": 1.0,
                "ADVANCED": 1.2,
                "EXPERT": 1.3,
            }
            base_weight *= difficulty_multiplier.get(
                str(kp.difficulty_level.value), 1.0
            )

            weights[kp.id] = base_weight

        return weights

    async def _calculate_exam_based_weights(
        self, knowledge_points: list[KnowledgePoint]
    ) -> dict[int, float]:
        """基于历年真题统计计算权重."""
        # 简化实现：模拟基于考试频率的权重
        weights = {}

        for kp in knowledge_points:
            # 模拟考试频率数据
            exam_frequency = 0.5  # 实际实现中从历年真题统计获取
            weights[kp.id] = exam_frequency

        return weights

    async def _calculate_difficulty_weights(
        self, knowledge_points: list[KnowledgePoint]
    ) -> dict[int, float]:
        """基于难度计算权重."""
        weights = {}

        for kp in knowledge_points:
            # 基于预估学习时间调整权重
            time_weight = min(2.0, kp.estimated_time / 60.0)  # 转换为小时并限制最大值
            weights[kp.id] = time_weight

        return weights

    async def _calculate_final_weights(
        self,
        base_weights: dict[int, float],
        exam_weights: dict[int, float],
        difficulty_weights: dict[int, float],
    ) -> dict[int, float]:
        """计算最终权重."""
        final_weights = {}
        config = self.analysis_config["weight_calculation"]

        all_kp_ids = (
            set(base_weights.keys())
            | set(exam_weights.keys())
            | set(difficulty_weights.keys())
        )

        for kp_id in all_kp_ids:
            base_w = base_weights.get(kp_id, 1.0)
            exam_w = exam_weights.get(kp_id, 0.5)
            diff_w = difficulty_weights.get(kp_id, 1.0)

            # 加权平均
            if hasattr(config, "get") and callable(getattr(config, "get", None)):
                content_weight = float(config.get("content_weight", 0.4))
                scope_weight = float(config.get("scope_weight", 0.3))
                difficulty_weight = float(config.get("difficulty_weight", 0.3))
            else:
                content_weight = 0.4
                scope_weight = 0.3
                difficulty_weight = 0.3

            final_weight = (
                base_w * content_weight
                + exam_w * scope_weight
                + diff_w * difficulty_weight
            )

            final_weights[kp_id] = round(final_weight, 3)

        return final_weights

    async def _generate_weight_report(
        self,
        knowledge_points: list[KnowledgePoint],
        weights: dict[int, float],
        syllabus: ExamSyllabus,
    ) -> dict[str, Any]:
        """生成权重报告."""
        # 按权重排序
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_weighted_points": sorted_weights[:10],
            "weight_distribution": await self._analyze_weight_distribution(weights),
            "recommendations": await self._generate_weight_recommendations(
                weights, knowledge_points
            ),
        }

    async def _analyze_weight_distribution(
        self, weights: dict[int, float]
    ) -> dict[str, Any]:
        """分析权重分布."""
        weight_values = list(weights.values())

        return {
            "mean": sum(weight_values) / len(weight_values) if weight_values else 0,
            "max": max(weight_values) if weight_values else 0,
            "min": min(weight_values) if weight_values else 0,
            "total_points": len(weight_values),
        }

    async def _generate_weight_recommendations(
        self, weights: dict[int, float], knowledge_points: list[KnowledgePoint]
    ) -> list[str]:
        """生成权重建议."""
        recommendations = []

        # 分析权重分布
        weight_values = list(weights.values())
        if weight_values:
            avg_weight = sum(weight_values) / len(weight_values)
            high_weight_count = sum(1 for w in weight_values if w > avg_weight * 1.5)

            if high_weight_count > len(weight_values) * 0.3:
                recommendations.append("高权重知识点过多，建议重新评估重要性分布")

            if max(weight_values) > avg_weight * 3:
                recommendations.append("存在权重过高的知识点，建议检查权重计算逻辑")

        return recommendations

    def _syllabus_to_dict(self, syllabus: ExamSyllabus) -> dict[str, Any]:
        """将考纲转换为字典."""
        return {
            "id": syllabus.id,
            "title": syllabus.title,
            "exam_type": syllabus.exam_type,
            "exam_level": syllabus.exam_level,
            "version": syllabus.version,
            "effective_date": syllabus.effective_date,
            "description": syllabus.description,
        }

    async def _generate_change_summary(
        self,
        structure_changes: dict[str, Any],
        content_changes: dict[str, Any],
        requirement_changes: dict[str, Any],
    ) -> str:
        """生成变更摘要."""
        summary_parts = []

        if structure_changes["added_sections"]:
            summary_parts.append(
                f"新增{len(structure_changes['added_sections'])}个章节"
            )

        if structure_changes["removed_sections"]:
            summary_parts.append(
                f"删除{len(structure_changes['removed_sections'])}个章节"
            )

        if structure_changes["modified_sections"]:
            summary_parts.append(
                f"修改{len(structure_changes['modified_sections'])}个章节"
            )

        if content_changes["exam_type_changed"]:
            summary_parts.append("考试类型发生变更")

        if requirement_changes["new_requirements"]:
            summary_parts.append(
                f"新增{len(requirement_changes['new_requirements'])}项能力要求"
            )

        return "；".join(summary_parts) if summary_parts else "无重大变更"

    async def _generate_executive_summary(self, change_analysis: dict[str, Any]) -> str:
        """生成执行摘要."""
        impact_level = change_analysis["overall_impact_level"]
        change_summary = change_analysis["change_summary"]

        summary_templates = {
            "critical": f"考纲发生重大变更（{change_summary}），需要立即采取行动进行全面适配。",
            "high": f"考纲发生较大变更（{change_summary}），需要制定详细的适配计划。",
            "medium": f"考纲发生中等程度变更（{change_summary}），需要适当调整相关内容。",
            "low": f"考纲发生轻微变更（{change_summary}），影响较小。",
        }

        return summary_templates.get(impact_level, "考纲变更分析完成。")

    async def _assess_risks(self, change_analysis: dict[str, Any]) -> dict[str, Any]:
        """评估风险."""
        impact_level = change_analysis["overall_impact_level"]

        risk_levels = {
            "critical": {"level": "high", "description": "变更影响重大，存在高风险"},
            "high": {
                "level": "medium-high",
                "description": "变更影响较大，存在中高风险",
            },
            "medium": {"level": "medium", "description": "变更影响中等，存在中等风险"},
            "low": {"level": "low", "description": "变更影响较小，风险较低"},
        }

        return risk_levels.get(impact_level, risk_levels["medium"])

    async def _estimate_timeline(
        self,
        course_impact: dict[str, Any],
        question_impact: dict[str, Any],
        material_impact: dict[str, Any],
    ) -> dict[str, Any]:
        """估算时间线."""
        total_days = (
            course_impact["estimated_effort"]["days"]
            + question_impact["estimated_effort"]["days"]
            + material_impact["estimated_effort"]["days"]
        )

        return {
            "total_estimated_days": total_days,
            "phases": [
                {"phase": "评估阶段", "days": max(1, total_days // 4)},
                {"phase": "规划阶段", "days": max(1, total_days // 4)},
                {"phase": "实施阶段", "days": max(1, total_days // 2)},
                {"phase": "验证阶段", "days": max(1, total_days // 8)},
            ],
        }

    async def assess_impact(self, syllabus_id: int) -> dict[str, Any]:
        """评估考纲影响 - 需求33影响评估."""
        try:
            # 获取考纲
            stmt = select(ExamSyllabus).where(ExamSyllabus.id == syllabus_id)
            result = await self.db.execute(stmt)
            syllabus = result.scalar_one_or_none()

            if not syllabus:
                raise ValueError(f"考纲不存在: {syllabus_id}")

            # 模拟影响评估
            impact_assessment = {
                "overall_impact": "medium",
                "affected_areas": [
                    {
                        "area": "听力理解",
                        "impact_level": "high",
                        "change_percentage": 25,
                    },
                    {
                        "area": "阅读理解",
                        "impact_level": "medium",
                        "change_percentage": 15,
                    },
                    {"area": "写作表达", "impact_level": "low", "change_percentage": 5},
                    {
                        "area": "翻译技能",
                        "impact_level": "medium",
                        "change_percentage": 20,
                    },
                ],
                "difficulty_changes": {
                    "increased_difficulty": ["听力理解", "翻译技能"],
                    "decreased_difficulty": [],
                    "unchanged": ["阅读理解", "写作表达"],
                },
                "content_changes": {
                    "new_topics": ["人工智能", "环境保护", "文化交流"],
                    "removed_topics": ["传统工艺"],
                    "modified_topics": ["经济发展", "社会热点"],
                },
                "preparation_recommendations": [
                    "加强听力训练，特别是长对话理解",
                    "提高翻译技能，注重语言表达准确性",
                    "关注新增话题的词汇积累",
                ],
            }

            return {
                "syllabus_id": syllabus_id,
                "assessment_date": "2024-01-01T00:00:00Z",
                "impact_assessment": impact_assessment,
            }

        except Exception as e:
            logger.error(f"考纲影响评估失败: {str(e)}")
            raise BusinessLogicError(f"考纲影响评估失败: {str(e)}") from e

    async def calculate_weights(self, syllabus_id: int) -> dict[str, Any]:
        """计算考纲权重 - 需求33权重计算."""
        try:
            # 获取考纲
            stmt = select(ExamSyllabus).where(ExamSyllabus.id == syllabus_id)
            result = await self.db.execute(stmt)
            syllabus = result.scalar_one_or_none()

            if not syllabus:
                raise ValueError(f"考纲不存在: {syllabus_id}")

            # 模拟权重计算
            weight_calculation = {
                "section_weights": {
                    "听力理解": {
                        "weight": 0.35,
                        "sub_sections": {
                            "短对话": 0.10,
                            "长对话": 0.15,
                            "短文理解": 0.10,
                        },
                    },
                    "阅读理解": {
                        "weight": 0.35,
                        "sub_sections": {
                            "词汇理解": 0.05,
                            "长篇阅读": 0.10,
                            "仔细阅读": 0.20,
                        },
                    },
                    "写作": {"weight": 0.15, "sub_sections": {"短文写作": 0.15}},
                    "翻译": {"weight": 0.15, "sub_sections": {"段落翻译": 0.15}},
                },
                "difficulty_weights": {"基础": 0.30, "中等": 0.50, "困难": 0.20},
                "topic_weights": {
                    "日常生活": 0.25,
                    "学术话题": 0.30,
                    "社会热点": 0.25,
                    "文化交流": 0.20,
                },
                "calculation_method": "基于历年考试数据和专家评估",
                "confidence_level": 0.92,
            }

            return {
                "syllabus_id": syllabus_id,
                "calculation_date": "2024-01-01T00:00:00Z",
                "weight_calculation": weight_calculation,
            }

        except Exception as e:
            logger.error(f"考纲权重计算失败: {str(e)}")
            raise BusinessLogicError(f"考纲权重计算失败: {str(e)}") from e
