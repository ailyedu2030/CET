"""错题分析服务 - 智能错题收集、分类和分析."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.resources.models.resource_models import KnowledgePoint
from app.shared.models.enums import TrainingType
from app.training.models.training_models import Question, TrainingRecord
from app.training.schemas.adaptive_learning_schemas import (
    ErrorPatternResponse,
    KnowledgeGapResponse,
)

logger = logging.getLogger(__name__)


class ErrorAnalysisService:
    """错题分析服务 - 智能错题收集、分类和强化推荐."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化错题分析服务."""
        self.db = db

        # 错误分类配置
        self.error_categories = {
            "grammar": {
                "name": "语法错误",
                "keywords": ["时态", "语态", "主谓一致", "从句", "非谓语"],
                "weight": 0.8,
            },
            "vocabulary": {
                "name": "词汇错误",
                "keywords": ["词义", "搭配", "拼写", "词性", "同义词"],
                "weight": 0.7,
            },
            "comprehension": {
                "name": "理解错误",
                "keywords": ["理解", "推理", "逻辑", "主旨", "细节"],
                "weight": 0.9,
            },
            "application": {
                "name": "应用错误",
                "keywords": ["运用", "表达", "写作", "翻译", "技巧"],
                "weight": 0.6,
            },
            "careless": {
                "name": "粗心错误",
                "keywords": ["粗心", "马虎", "看错", "漏看", "计算"],
                "weight": 0.3,
            },
        }

    async def collect_error_questions(
        self, student_id: int, days: int = 30
    ) -> list[dict[str, Any]]:
        """收集学生的错题."""
        try:
            # 查询指定时间内的错题记录
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = (
                select(TrainingRecord, Question)
                .join(Question, TrainingRecord.question_id == Question.id)
                .where(
                    and_(
                        TrainingRecord.student_id == student_id,
                        TrainingRecord.is_correct == False,  # noqa: E712
                        TrainingRecord.created_at >= cutoff_date,
                    )
                )
                .order_by(desc(TrainingRecord.created_at))
            )

            result = await self.db.execute(stmt)
            records = result.all()

            error_questions = []
            for record, question in records:
                error_data = {
                    "record_id": record.id,
                    "question_id": question.id,
                    "question_type": question.question_type,
                    "training_type": question.training_type,
                    "difficulty_level": question.difficulty_level,
                    "content": question.content,
                    "correct_answer": question.correct_answer,
                    "student_answer": record.student_answer,
                    "score": record.score,
                    "max_score": record.max_score,
                    "error_time": record.created_at,
                    "knowledge_points": question.knowledge_points,
                    "tags": question.tags,
                }
                error_questions.append(error_data)

            logger.info(f"收集到 {len(error_questions)} 道错题，学生ID: {student_id}")
            return error_questions

        except Exception as e:
            logger.error(f"收集错题失败: {str(e)}")
            return []

    async def categorize_errors(
        self, error_questions: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """对错题进行智能分类."""
        try:
            categorized_errors = defaultdict(list)

            for error in error_questions:
                # 基于问题类型的初步分类
                primary_category = self._classify_by_question_type(error)

                # 基于错误内容的细分类
                detailed_category = await self._classify_by_error_content(error)

                # 合并分类结果
                final_category = detailed_category or primary_category
                categorized_errors[final_category].append(error)

            # 按错误数量排序
            sorted_categories = dict(
                sorted(
                    categorized_errors.items(),
                    key=lambda x: len(x[1]),
                    reverse=True,
                )
            )

            logger.info(f"错题分类完成，共 {len(sorted_categories)} 个类别")
            return sorted_categories

        except Exception as e:
            logger.error(f"错题分类失败: {str(e)}")
            return {}

    async def analyze_error_patterns(self, student_id: int, days: int = 30) -> ErrorPatternResponse:
        """分析学生的错题模式."""
        try:
            error_questions = await self.collect_error_questions(student_id, days)
            categorized_errors = await self.categorize_errors(error_questions)

            # 分析错误频率
            error_frequency = {
                category: len(errors) for category, errors in categorized_errors.items()
            }

            # 分析错误趋势
            error_trend = await self._analyze_error_trend(student_id, days)

            # 识别薄弱知识点
            weak_knowledge_points = await self._identify_weak_knowledge_points(error_questions)

            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                categorized_errors, weak_knowledge_points
            )

            return ErrorPatternResponse(
                student_id=student_id,
                analysis_period_days=days,
                total_errors=len(error_questions),
                error_frequency=error_frequency,
                error_trend=error_trend,
                weak_knowledge_points=weak_knowledge_points,
                improvement_suggestions=improvement_suggestions,
                analysis_time=datetime.now(),
            )

        except Exception as e:
            logger.error(f"错题模式分析失败: {str(e)}")
            raise

    async def get_knowledge_gaps(self, student_id: int) -> list[KnowledgeGapResponse]:
        """识别学生的知识缺口."""
        try:
            # 获取学生的错题记录
            error_questions = await self.collect_error_questions(student_id, days=90)

            # 按知识点统计错误
            knowledge_errors = defaultdict(list)
            for error in error_questions:
                if error["knowledge_points"]:
                    for kp_id in error["knowledge_points"]:
                        knowledge_errors[kp_id].append(error)

            # 分析每个知识点的掌握情况
            knowledge_gaps = []
            for kp_id, errors in knowledge_errors.items():
                # 获取知识点信息
                kp = await self.db.get(KnowledgePoint, kp_id)
                if not kp:
                    continue

                # 计算错误率
                total_attempts = await self._get_knowledge_point_attempts(student_id, kp_id)
                error_rate = len(errors) / max(total_attempts, 1)

                # 分析错误类型分布
                error_types = self._analyze_error_types_for_knowledge_point(errors)

                # 评估掌握程度
                mastery_level = self._calculate_mastery_level(error_rate, len(errors))

                knowledge_gap = KnowledgeGapResponse(
                    knowledge_point_id=kp_id,
                    knowledge_point_title=kp.title,
                    difficulty_level=kp.difficulty_level,
                    total_attempts=total_attempts,
                    error_count=len(errors),
                    error_rate=error_rate,
                    mastery_level=mastery_level,
                    error_types=error_types,
                    last_error_time=max((error["error_time"] for error in errors), default=None),
                    improvement_priority=self._calculate_improvement_priority(
                        error_rate, kp.importance_score, len(errors)
                    ),
                )
                knowledge_gaps.append(knowledge_gap)

            # 按改进优先级排序
            knowledge_gaps.sort(key=lambda x: x.improvement_priority, reverse=True)

            logger.info(f"识别到 {len(knowledge_gaps)} 个知识缺口")
            return knowledge_gaps

        except Exception as e:
            logger.error(f"知识缺口分析失败: {str(e)}")
            return []

    async def generate_reinforcement_plan(
        self, student_id: int, knowledge_gaps: list[KnowledgeGapResponse]
    ) -> dict[str, Any]:
        """生成强化训练计划."""
        try:
            # 选择优先级最高的知识点
            priority_gaps = knowledge_gaps[:5]  # 最多处理5个优先知识点

            reinforcement_plan: dict[str, Any] = {
                "student_id": student_id,
                "plan_created_at": datetime.now(),
                "total_knowledge_gaps": len(knowledge_gaps),
                "priority_gaps": len(priority_gaps),
                "training_modules": [],
                "estimated_completion_days": 0,
            }

            total_days = 0
            for gap in priority_gaps:
                # 根据掌握程度确定训练强度
                training_intensity = self._determine_training_intensity(gap)

                # 生成训练模块
                training_module = {
                    "knowledge_point_id": gap.knowledge_point_id,
                    "knowledge_point_title": gap.knowledge_point_title,
                    "current_mastery_level": gap.mastery_level,
                    "target_mastery_level": "proficient",
                    "training_intensity": training_intensity,
                    "recommended_questions_per_day": training_intensity["daily_questions"],
                    "estimated_days": training_intensity["estimated_days"],
                    "focus_areas": self._identify_focus_areas(gap),
                    "training_methods": self._recommend_training_methods(gap),
                }

                reinforcement_plan["training_modules"].append(training_module)
                total_days = max(total_days, training_intensity["estimated_days"])

            reinforcement_plan["estimated_completion_days"] = total_days

            logger.info(f"生成强化训练计划，预计 {total_days} 天完成")
            return reinforcement_plan

        except Exception as e:
            logger.error(f"生成强化训练计划失败: {str(e)}")
            return {}

    # ==================== 私有方法 ====================

    def _classify_by_question_type(self, error: dict[str, Any]) -> str:
        """基于题目类型进行初步分类."""
        training_type = error["training_type"]

        if training_type == TrainingType.VOCABULARY:
            return "vocabulary"
        elif training_type == TrainingType.LISTENING:
            return "comprehension"
        elif training_type == TrainingType.READING:
            return "comprehension"
        elif training_type == TrainingType.WRITING:
            return "application"
        elif training_type == TrainingType.TRANSLATION:
            return "application"
        else:
            return "grammar"

    async def _classify_by_error_content(self, error: dict[str, Any]) -> str | None:
        """基于错误内容进行详细分类."""
        # 这里可以集成AI分析错误内容
        # 暂时返回None，使用基础分类
        return None

    async def _analyze_error_trend(self, student_id: int, days: int) -> dict[str, Any]:
        """分析错误趋势."""
        try:
            # 按天统计错误数量
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = (
                select(
                    func.date(TrainingRecord.created_at).label("error_date"),
                    func.count(TrainingRecord.id).label("error_count"),
                )
                .where(
                    and_(
                        TrainingRecord.student_id == student_id,
                        TrainingRecord.is_correct == False,  # noqa: E712
                        TrainingRecord.created_at >= cutoff_date,
                    )
                )
                .group_by(func.date(TrainingRecord.created_at))
                .order_by("error_date")
            )

            result = await self.db.execute(stmt)
            daily_errors = result.all()

            # 计算趋势
            if len(daily_errors) < 2:
                trend = "stable"
                trend_value = 0.0
            else:
                recent_avg = sum(row.error_count for row in daily_errors[-7:]) / min(
                    7, len(daily_errors)
                )
                early_avg = sum(row.error_count for row in daily_errors[:7]) / min(
                    7, len(daily_errors)
                )

                trend_value = (recent_avg - early_avg) / max(early_avg, 1)

                if trend_value > 0.1:
                    trend = "increasing"
                elif trend_value < -0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"

            return {
                "trend": trend,
                "trend_value": trend_value,
                "daily_errors": [
                    {"date": row.error_date, "count": row.error_count} for row in daily_errors
                ],
            }

        except Exception as e:
            logger.error(f"错误趋势分析失败: {str(e)}")
            return {"trend": "unknown", "trend_value": 0.0, "daily_errors": []}

    async def _identify_weak_knowledge_points(
        self, error_questions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """识别薄弱知识点."""
        knowledge_errors: dict[int, int] = defaultdict(int)

        for error in error_questions:
            if error["knowledge_points"]:
                for kp_id in error["knowledge_points"]:
                    knowledge_errors[kp_id] += 1

        # 获取知识点详细信息
        weak_points = []
        for kp_id, error_count in knowledge_errors.items():
            if error_count >= 2:  # 至少错误2次才认为是薄弱点
                kp = await self.db.get(KnowledgePoint, kp_id)
                if kp:
                    weak_points.append(
                        {
                            "knowledge_point_id": kp_id,
                            "title": kp.title,
                            "error_count": error_count,
                            "difficulty_level": kp.difficulty_level,
                            "importance_score": kp.importance_score,
                        }
                    )

        # 按错误次数排序
        weak_points.sort(key=lambda x: x.get("error_count", 0), reverse=True)  # type: ignore[arg-type,return-value]
        return weak_points[:10]  # 返回前10个薄弱点

    def _generate_improvement_suggestions(
        self,
        categorized_errors: dict[str, list[dict[str, Any]]],
        weak_knowledge_points: list[dict[str, Any]],
    ) -> list[str]:
        """生成改进建议."""
        suggestions = []

        # 基于错误类别的建议
        for category, errors in categorized_errors.items():
            if len(errors) >= 3:  # 错误次数较多的类别
                category_info = self.error_categories.get(category, {})
                category_name = category_info.get("name", category)
                suggestions.append(f"重点加强{category_name}的练习，已发现{len(errors)}个相关错误")

        # 基于薄弱知识点的建议
        for kp in weak_knowledge_points[:3]:  # 前3个薄弱点
            suggestions.append(f"加强'{kp['title']}'知识点的学习，错误次数: {kp['error_count']}")

        # 通用建议
        if not suggestions:
            suggestions.append("继续保持良好的学习状态，注意细心答题")

        return suggestions

    async def _get_knowledge_point_attempts(self, student_id: int, knowledge_point_id: int) -> int:
        """获取学生在某个知识点上的总尝试次数."""
        stmt = (
            select(func.count(TrainingRecord.id))
            .join(Question, TrainingRecord.question_id == Question.id)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    Question.knowledge_points.contains([knowledge_point_id]),
                )
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    def _analyze_error_types_for_knowledge_point(
        self, errors: list[dict[str, Any]]
    ) -> dict[str, int]:
        """分析知识点的错误类型分布."""
        error_types: dict[str, int] = defaultdict(int)

        for error in errors:
            error_type = self._classify_by_question_type(error)
            error_types[error_type] += 1

        return dict(error_types)

    def _calculate_mastery_level(self, error_rate: float, error_count: int) -> str:
        """计算掌握程度."""
        if error_rate <= 0.1 and error_count <= 1:
            return "proficient"
        elif error_rate <= 0.3 and error_count <= 3:
            return "developing"
        elif error_rate <= 0.5:
            return "basic"
        else:
            return "needs_improvement"

    def _calculate_improvement_priority(
        self, error_rate: float, importance_score: float, error_count: int
    ) -> float:
        """计算改进优先级."""
        # 综合考虑错误率、重要性和错误次数
        priority = (error_rate * 0.4 + importance_score * 0.4 + error_count * 0.2) * 100
        return min(priority, 100.0)

    def _determine_training_intensity(self, gap: KnowledgeGapResponse) -> dict[str, Any]:
        """确定训练强度."""
        mastery_level = gap.mastery_level

        if mastery_level == "needs_improvement":
            return {
                "level": "intensive",
                "daily_questions": 15,
                "estimated_days": 14,
                "review_frequency": "daily",
            }
        elif mastery_level == "basic":
            return {
                "level": "moderate",
                "daily_questions": 10,
                "estimated_days": 10,
                "review_frequency": "every_2_days",
            }
        elif mastery_level == "developing":
            return {
                "level": "light",
                "daily_questions": 5,
                "estimated_days": 7,
                "review_frequency": "every_3_days",
            }
        else:
            return {
                "level": "maintenance",
                "daily_questions": 3,
                "estimated_days": 5,
                "review_frequency": "weekly",
            }

    def _identify_focus_areas(self, gap: KnowledgeGapResponse) -> list[str]:
        """识别重点关注领域."""
        focus_areas = []

        # 基于错误类型确定关注点
        for error_type, count in gap.error_types.items():
            if count >= 2:
                focus_areas.append(f"{error_type}类型题目")

        if not focus_areas:
            focus_areas.append("基础概念理解")

        return focus_areas

    def _recommend_training_methods(self, gap: KnowledgeGapResponse) -> list[str]:
        """推荐训练方法."""
        methods = []

        if gap.mastery_level == "needs_improvement":
            methods.extend(["概念复习", "基础练习", "错题重做"])
        elif gap.mastery_level == "basic":
            methods.extend(["针对性练习", "知识点串联"])
        elif gap.mastery_level == "developing":
            methods.extend(["提高练习", "综合应用"])
        else:
            methods.extend(["巩固练习", "拓展应用"])

        return methods
