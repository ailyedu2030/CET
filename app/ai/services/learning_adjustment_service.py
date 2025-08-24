"""学情分析与教学调整服务.

根据设计文档第412-432行要求，整合使用设计文档要求的核心组件：
- LearningAnalyticsEngine (enhanced_learning_analytics.py)
- IntelligentTeachingAdjustmentEngine (intelligent_teaching_adjustment.py)
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.ai_models import LearningAnalysis, TeachingAdjustment
from app.ai.schemas.ai_schemas import (
    LearningAnalysisCreate,
    LearningAnalysisListResponse,
    LearningAnalysisRequest,
    LearningAnalysisResponse,
    TeachingAdjustmentCreate,
    TeachingAdjustmentListResponse,
    TeachingAdjustmentRequest,
    TeachingAdjustmentResponse,
    TeachingAdjustmentUpdate,
)
from app.ai.services.deepseek_service import get_deepseek_service
from app.ai.services.enhanced_learning_analytics import EnhancedLearningAnalytics
from app.ai.services.intelligent_teaching_adjustment import (
    IntelligentTeachingAdjustment,
)
from app.courses.models.course_models import Class, Course
from app.training.models.training_models import TrainingRecord, TrainingSession
from app.users.models.user_models import StudentProfile, User

logger = logging.getLogger(__name__)


class LearningAdjustmentService:
    """学情分析与教学调整服务.

    根据设计文档要求，整合使用核心AI组件。
    """

    def __init__(self) -> None:
        self.deepseek_service = get_deepseek_service()
        # 使用设计文档要求的核心组件
        self.learning_analytics = EnhancedLearningAnalytics()
        self.teaching_adjustment = IntelligentTeachingAdjustment()

    async def analyze_learning_progress(
        self,
        db: AsyncSession,
        request: LearningAnalysisRequest,
        teacher_id: int,
    ) -> LearningAnalysisResponse:
        """执行学情分析."""
        try:
            # 验证班级和课程权限
            await self._verify_class_permission(db, request.class_id, teacher_id)
            await self._verify_course_access(db, request.course_id, teacher_id)

            # 收集学习数据
            learning_data = await self._collect_learning_data(
                db, request.class_id, request.course_id, request
            )

            # 执行AI分析
            analysis_insights = await self._perform_ai_analysis(learning_data, request)

            # 创建分析记录
            analysis_create = LearningAnalysisCreate(
                class_id=request.class_id,
                course_id=request.course_id,
                teacher_id=teacher_id,
                analysis_type=request.analysis_type,
                analysis_period=request.analysis_period,
                student_count=learning_data["student_count"],
                analysis_data=learning_data,
                insights=analysis_insights["insights"],
                risk_students=analysis_insights["risk_students"],
                ai_generated=True,
                confidence_score=analysis_insights["confidence_score"],
            )

            analysis_record = await self._create_analysis_record(db, analysis_create)

            return LearningAnalysisResponse.model_validate(analysis_record)  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"学情分析失败: {str(e)}")
            raise

    async def generate_teaching_adjustments(
        self,
        db: AsyncSession,
        request: TeachingAdjustmentRequest,
        teacher_id: int,
    ) -> list[TeachingAdjustmentResponse]:
        """生成教学调整建议."""
        try:
            # 验证权限
            await self._verify_class_permission(db, request.class_id, teacher_id)

            # 如果有关联分析，获取分析数据
            analysis_data = None
            if request.learning_analysis_id:
                analysis_data = await self._get_analysis_data(db, request.learning_analysis_id)

            # 收集当前教学状态
            teaching_context = await self._collect_teaching_context(
                db, request.class_id, request.course_id, analysis_data
            )

            # 使用AI生成调整建议
            adjustment_suggestions = await self._generate_ai_adjustments(teaching_context, request)

            # 创建调整建议记录
            adjustments = []
            for suggestion in adjustment_suggestions:
                adjustment_create = TeachingAdjustmentCreate(
                    learning_analysis_id=request.learning_analysis_id,
                    class_id=request.class_id,
                    course_id=request.course_id,
                    teacher_id=teacher_id,
                    adjustment_type=suggestion["type"],
                    priority_level=suggestion["priority"],
                    title=suggestion["title"],
                    description=suggestion["description"],
                    adjustments=suggestion["adjustments"],
                    target_students=suggestion.get("target_students", []),
                    expected_outcome=suggestion.get("expected_outcome"),
                    implementation_timeline=suggestion.get("timeline"),
                    ai_generated=True,
                    confidence_score=suggestion["confidence"],
                    reasoning=suggestion.get("reasoning"),
                )

                adjustment_record = await self._create_adjustment_record(db, adjustment_create)
                adjustments.append(TeachingAdjustmentResponse.model_validate(adjustment_record))

            return adjustments

        except Exception as e:
            logger.error(f"生成教学调整建议失败: {str(e)}")
            raise

    async def get_analysis_by_id(
        self, db: AsyncSession, analysis_id: int, teacher_id: int | None = None
    ) -> LearningAnalysisResponse | None:
        """根据ID获取学情分析."""
        try:
            query = select(LearningAnalysis).where(LearningAnalysis.id == analysis_id)

            if teacher_id:
                query = query.where(LearningAnalysis.teacher_id == teacher_id)

            result = await db.execute(query)
            analysis = result.scalar_one_or_none()

            if analysis:
                return LearningAnalysisResponse.model_validate(analysis)  # type: ignore[no-any-return]
            return None

        except Exception as e:
            logger.error(f"获取学情分析失败: {str(e)}")
            raise

    async def get_analyses_list(
        self,
        db: AsyncSession,
        class_id: int | None = None,
        course_id: int | None = None,
        teacher_id: int | None = None,
        analysis_type: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> LearningAnalysisListResponse:
        """获取学情分析列表."""
        try:
            # 构建查询
            query = select(LearningAnalysis)

            # 添加过滤条件
            if class_id:
                query = query.where(LearningAnalysis.class_id == class_id)
            if course_id:
                query = query.where(LearningAnalysis.course_id == course_id)
            if teacher_id:
                query = query.where(LearningAnalysis.teacher_id == teacher_id)
            if analysis_type:
                query = query.where(LearningAnalysis.analysis_type == analysis_type)

            # 排序
            query = query.order_by(desc(LearningAnalysis.analysis_date))

            # 计算总数
            count_query = select(func.count(LearningAnalysis.id)).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            # 分页
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            result = await db.execute(query)
            analyses = result.scalars().all()

            return LearningAnalysisListResponse(
                analyses=[LearningAnalysisResponse.model_validate(a) for a in analyses],
                total=total,
                page=page,
                size=size,
            )

        except Exception as e:
            logger.error(f"获取学情分析列表失败: {str(e)}")
            raise

    async def get_adjustment_by_id(
        self, db: AsyncSession, adjustment_id: int, teacher_id: int | None = None
    ) -> TeachingAdjustmentResponse | None:
        """根据ID获取教学调整建议."""
        try:
            query = select(TeachingAdjustment).where(TeachingAdjustment.id == adjustment_id)

            if teacher_id:
                query = query.where(TeachingAdjustment.teacher_id == teacher_id)

            result = await db.execute(query)
            adjustment = result.scalar_one_or_none()

            if adjustment:
                return TeachingAdjustmentResponse.model_validate(adjustment)  # type: ignore[no-any-return]  # type: ignore[no-any-return]
            return None

        except Exception as e:
            logger.error(f"获取教学调整建议失败: {str(e)}")
            raise

    async def update_adjustment(
        self,
        db: AsyncSession,
        adjustment_id: int,
        update_data: TeachingAdjustmentUpdate,
        teacher_id: int,
    ) -> TeachingAdjustmentResponse | None:
        """更新教学调整建议."""
        try:
            # 获取现有记录
            result = await db.execute(
                select(TeachingAdjustment).where(
                    and_(
                        TeachingAdjustment.id == adjustment_id,
                        TeachingAdjustment.teacher_id == teacher_id,
                    )
                )
            )
            adjustment = result.scalar_one_or_none()

            if not adjustment:
                return None

            # 更新字段
            update_fields = update_data.model_dump(exclude_unset=True)
            for field, value in update_fields.items():
                setattr(adjustment, field, value)

            # 如果状态变为进行中，设置实施日期
            if (
                update_data.implementation_status == "in_progress"
                and not adjustment.implementation_date
            ):
                adjustment.implementation_date = datetime.utcnow()

            await db.commit()
            await db.refresh(adjustment)

            return TeachingAdjustmentResponse.model_validate(adjustment)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"更新教学调整建议失败: {str(e)}")
            raise

    async def get_adjustments_list(
        self,
        db: AsyncSession,
        class_id: int | None = None,
        course_id: int | None = None,
        teacher_id: int | None = None,
        adjustment_type: str | None = None,
        implementation_status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> TeachingAdjustmentListResponse:
        """获取教学调整建议列表."""
        try:
            # 构建查询
            query = select(TeachingAdjustment)

            # 添加过滤条件
            if class_id:
                query = query.where(TeachingAdjustment.class_id == class_id)
            if course_id:
                query = query.where(TeachingAdjustment.course_id == course_id)
            if teacher_id:
                query = query.where(TeachingAdjustment.teacher_id == teacher_id)
            if adjustment_type:
                query = query.where(TeachingAdjustment.adjustment_type == adjustment_type)
            if implementation_status:
                query = query.where(
                    TeachingAdjustment.implementation_status == implementation_status
                )

            # 排序
            query = query.order_by(desc(TeachingAdjustment.created_at))

            # 计算总数
            count_query = select(func.count(TeachingAdjustment.id)).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            # 分页
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            result = await db.execute(query)
            adjustments = result.scalars().all()

            return TeachingAdjustmentListResponse(
                adjustments=[TeachingAdjustmentResponse.model_validate(a) for a in adjustments],
                total=total,
                page=page,
                size=size,
            )

        except Exception as e:
            logger.error(f"获取教学调整建议列表失败: {str(e)}")
            raise

    # =================== 私有辅助方法 ===================

    async def _verify_class_permission(
        self, db: AsyncSession, class_id: int, teacher_id: int
    ) -> None:
        """验证班级权限."""
        result = await db.execute(
            select(Class).where(and_(Class.id == class_id, Class.teacher_id == teacher_id))
        )
        if not result.scalar_one_or_none():
            raise ValueError("无权限访问该班级")

    async def _verify_course_access(
        self, db: AsyncSession, course_id: int, teacher_id: int
    ) -> None:
        """验证课程访问权限."""
        result = await db.execute(
            select(Course).where(and_(Course.id == course_id, Course.created_by == teacher_id))
        )
        if not result.scalar_one_or_none():
            raise ValueError("无权限访问该课程")

    async def _collect_learning_data(
        self,
        db: AsyncSession,
        class_id: int,
        course_id: int,
        request: LearningAnalysisRequest,
    ) -> dict[str, Any]:
        """收集学习数据."""
        # 获取班级学生 - 使用StudentProfile模型
        students_result = await db.execute(
            select(StudentProfile).join(Class).where(Class.id == class_id)
        )
        students = students_result.scalars().all()

        if request.include_students:
            students = [s for s in students if s.user_id in request.include_students]

        student_ids = [s.user_id for s in students]

        # 收集测验数据
        quiz_data = await self._collect_quiz_data(db, course_id, student_ids)

        # 收集学习行为数据
        behavior_data = await self._collect_behavior_data(db, class_id, student_ids)

        return {
            "student_count": len(students),
            "student_ids": student_ids,
            "analysis_period": request.analysis_period,
            "quiz_performance": quiz_data,
            "learning_behavior": behavior_data,
            "collection_date": datetime.utcnow().isoformat(),
            "additional_params": request.additional_params or {},
        }

    async def _collect_quiz_data(
        self, db: AsyncSession, course_id: int, student_ids: list[int]
    ) -> dict[str, Any]:
        """收集测验数据."""
        # 获取课程相关班级的学生训练记录
        from app.courses.models.course_models import Class

        classes_result = await db.execute(select(Class).where(Class.course_id == course_id))
        classes = classes_result.scalars().all()

        if not classes:
            return {"total_quizzes": 0, "student_performance": {}}

        # 获取所有班级学生的训练记录
        records_result = await db.execute(
            select(TrainingRecord)
            .join(TrainingSession)
            .where(
                TrainingSession.student_id.in_(
                    select(User.id).where(
                        User.id.in_(
                            # 这里需要通过班级学生关联表查询，暂时简化
                            select(User.id).where(User.user_type == "student")
                        )
                    )
                )
            )
        )
        records = records_result.scalars().all()

        if not records:
            return {"total_quizzes": 0, "student_performance": {}}

        # 统计训练记录数据
        total_records = len(records)
        student_performance = {}

        for record in records:
            student_id = record.student_id
            if student_id not in student_performance:
                student_performance[student_id] = {
                    "total_attempts": 0,
                    "correct_answers": 0,
                    "average_score": 0.0,
                    "time_spent": 0,
                }

            student_performance[student_id]["total_attempts"] += 1
            if record.is_correct:
                student_performance[student_id]["correct_answers"] += 1
            student_performance[student_id]["average_score"] += record.score
            student_performance[student_id]["time_spent"] += record.time_spent

        # 计算平均值
        for student_id in student_performance:
            perf = student_performance[student_id]
            if perf["total_attempts"] > 0:
                perf["average_score"] /= perf["total_attempts"]

        return {
            "total_quizzes": total_records,
            "student_performance": student_performance,
        }

    async def _collect_behavior_data(
        self, db: AsyncSession, class_id: int, student_ids: list[int]
    ) -> dict[str, Any]:
        """收集学习行为数据."""
        # 这里可以收集学生的学习行为数据
        # 如登录频次、学习时长、资料浏览等
        return {
            "data_collection": "placeholder",
            "note": "学习行为数据收集功能待完善",
        }

    async def _perform_ai_analysis(
        self, learning_data: dict[str, Any], request: LearningAnalysisRequest
    ) -> dict[str, Any]:
        """执行AI分析."""
        # 构建分析提示
        prompt = self._build_analysis_prompt(learning_data, request)

        # 调用AI服务
        success, ai_response, error = await self.deepseek_service.generate_completion(
            prompt=prompt,
            model=None,
            temperature=0.3,  # 分析需要较低的随机性
            max_tokens=2048,
            user_id=None,
            task_type="learning_analysis",
        )

        if not success or not ai_response:
            raise ValueError(f"AI分析失败: {error}")

        try:
            # DeepSeek服务保证返回dict[str, Any]类型，直接处理
            return {
                "insights": ai_response.get("insights", []),
                "risk_students": ai_response.get("risk_students", []),
                "confidence_score": ai_response.get("confidence_score", 0.7),
                "recommendations": ai_response.get("recommendations", []),
            }
        except Exception as e:
            # 处理任何异常情况
            return {
                "insights": [f"分析过程出现错误: {str(e)}"],
                "risk_students": [],
                "confidence_score": 0.3,
                "recommendations": [],
            }

    def _build_analysis_prompt(
        self, learning_data: dict[str, Any], request: LearningAnalysisRequest
    ) -> str:
        """构建分析提示."""
        return f"""
请根据以下学习数据进行{request.analysis_type}分析：

分析周期: {request.analysis_period}
学生人数: {learning_data["student_count"]}
测验数据: {json.dumps(learning_data["quiz_performance"], ensure_ascii=False)}

请分析以下方面：
1. 学习进度和表现趋势
2. 识别学习困难的学生
3. 发现共性问题和个性问题
4. 提供改进建议

请以JSON格式返回结果：
{{
    "insights": ["洞察1", "洞察2", ...],
    "risk_students": [学生ID列表],
    "confidence_score": 0.8,
    "recommendations": ["建议1", "建议2", ...]
}}
"""

    async def _generate_ai_adjustments(
        self, teaching_context: dict[str, Any], request: TeachingAdjustmentRequest
    ) -> list[dict[str, Any]]:
        """使用AI生成调整建议."""
        prompt = self._build_adjustment_prompt(teaching_context, request)

        success, ai_response, error = await self.deepseek_service.generate_completion(
            prompt=prompt,
            model=None,
            temperature=0.4,
            max_tokens=3072,
            user_id=None,
            task_type="teaching_adjustment",
        )

        if not success or not ai_response:
            raise ValueError(f"AI生成调整建议失败: {error}")

        try:
            # DeepSeek服务保证返回dict[str, Any]类型，直接处理
            # 使用明确的类型标注避免IDE类型推断差异
            raw_adjustments: Any = ai_response.get("adjustments")

            # 根据实际内容类型进行处理
            if raw_adjustments is None:
                # 无调整建议，返回空列表
                return []
            elif isinstance(raw_adjustments, list):
                # 如果已经是列表，直接返回
                return raw_adjustments
            else:
                # 如果是单个对象，包装成列表后返回
                return [raw_adjustments]

        except Exception as e:
            # 生成错误建议
            return [
                {
                    "type": request.adjustment_focus,
                    "priority": request.priority_level or "medium",
                    "title": f"{request.adjustment_focus}建议生成失败",
                    "description": f"生成过程出现错误: {str(e)}",
                    "adjustments": {"description": "请手动制定调整方案"},
                    "confidence": 0.3,
                }
            ]

    def _build_adjustment_prompt(
        self, teaching_context: dict[str, Any], request: TeachingAdjustmentRequest
    ) -> str:
        """构建调整建议提示."""
        return f"""
基于以下教学情况，请生成具体的教学调整建议：

调整重点: {request.adjustment_focus}
当前问题: {request.current_issues or "需要分析识别"}
教学上下文: {json.dumps(teaching_context, ensure_ascii=False)}

请生成3-5个具体可行的调整建议，以JSON格式返回：
{{
    "adjustments": [
        {{
            "type": "调整类型",
            "priority": "high/medium/low",
            "title": "建议标题",
            "description": "详细说明",
            "adjustments": {{"具体": "调整方案"}},
            "target_students": [目标学生ID列表],
            "expected_outcome": "预期效果",
            "timeline": "实施时间线",
            "confidence": 0.8,
            "reasoning": "建议依据"
        }}
    ]
}}
"""

    async def _collect_teaching_context(
        self,
        db: AsyncSession,
        class_id: int,
        course_id: int,
        analysis_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """收集教学上下文信息."""
        # 获取班级信息
        class_result = await db.execute(select(Class).where(Class.id == class_id))
        class_obj = class_result.scalar_one_or_none()

        # 获取课程信息
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        course = course_result.scalar_one_or_none()

        # 获取班级学生数量（通过current_students字段）
        student_count = class_obj.current_students if class_obj else 0

        context = {
            "class_info": {
                "id": class_obj.id if class_obj else None,
                "name": class_obj.name if class_obj else None,
                "student_count": student_count,
            },
            "course_info": {
                "id": course.id if course else None,
                "name": course.name if course else None,
                "description": course.description if course else None,
            },
            "analysis_insights": (analysis_data.get("insights", []) if analysis_data else []),
            "current_date": datetime.utcnow().isoformat(),
        }

        return context

    async def _get_analysis_data(self, db: AsyncSession, analysis_id: int) -> dict[str, Any] | None:
        """获取分析数据."""
        result = await db.execute(
            select(LearningAnalysis).where(LearningAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            return {
                "insights": analysis.insights,
                "risk_students": analysis.risk_students,
                "analysis_data": analysis.analysis_data,
            }
        return None

    async def _create_analysis_record(
        self, db: AsyncSession, analysis_data: LearningAnalysisCreate
    ) -> LearningAnalysis:
        """创建分析记录."""
        analysis = LearningAnalysis(**analysis_data.model_dump())
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis

    async def _create_adjustment_record(
        self, db: AsyncSession, adjustment_data: TeachingAdjustmentCreate
    ) -> TeachingAdjustment:
        """创建调整建议记录."""
        adjustment = TeachingAdjustment(**adjustment_data.model_dump())
        db.add(adjustment)
        await db.commit()
        await db.refresh(adjustment)
        return adjustment


def get_learning_adjustment_service() -> LearningAdjustmentService:
    """获取学情分析与教学调整服务实例."""
    return LearningAdjustmentService()
