"""教案生成服务."""

import json
import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.models.ai_models import AISyllabus, CollaborativeSession, LessonPlan
from app.ai.schemas.ai_schemas import (
    CollaborationJoinRequest,
    CollaborationSessionResponse,
    CollaborationUpdateRequest,
    LessonPlanCreate,
    LessonPlanGenerationRequest,
    LessonPlanResponse,
    LessonPlanUpdate,
)
from app.ai.services.deepseek_service import get_deepseek_service
from app.ai.utils.content_generator import LessonPlanGenerator
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class LessonPlanService:
    """教案生成与管理服务."""

    def __init__(self) -> None:
        self.deepseek_service = get_deepseek_service()
        self.content_generator = LessonPlanGenerator()

    async def generate_lesson_plan(
        self,
        db: AsyncSession,
        request: LessonPlanGenerationRequest,
        teacher_id: int,
    ) -> LessonPlanResponse:
        """生成新的教案."""
        try:
            # 验证大纲存在
            syllabus = await self._get_syllabus(db, request.syllabus_id)
            if not syllabus:
                raise ValueError(f"大纲ID {request.syllabus_id} 不存在")

            # 验证教师权限
            teacher = await self._get_teacher(db, teacher_id)
            if not teacher:
                raise ValueError(f"教师ID {teacher_id} 不存在")

            # 检查该课时是否已存在教案
            existing = await self._get_lesson_plan_by_number(
                db, request.syllabus_id, request.lesson_number
            )
            if existing:
                raise ValueError(f"课时{request.lesson_number}已存在教案")

            # 准备大纲上下文信息
            syllabus_context = self._prepare_syllabus_context(syllabus, request.lesson_number)

            # 准备AI生成提示
            prompt = self.content_generator.prepare_prompt(
                lesson_number=request.lesson_number,
                title=request.title,
                duration_minutes=request.duration_minutes,
                student_level=request.student_level,
                focus_areas=request.focus_areas,
                syllabus_context=syllabus_context,
                class_size=request.class_size,
                available_resources=request.available_resources,
            )

            logger.info(f"为大纲{syllabus.title}生成课时{request.lesson_number}教案")

            # 调用AI生成内容
            (
                success,
                generated_content,
                error_msg,
            ) = await self.deepseek_service.generate_lesson_plan_content(
                prompt=prompt,
                user_id=teacher_id,
            )

            if not success or not generated_content:
                raise ValueError(f"AI生成失败: {error_msg}")

            # 验证和解析生成的内容
            is_valid, parsed_content, validation_error = (
                self.content_generator.validate_generated_content(generated_content)
            )

            if not is_valid or not parsed_content:
                raise ValueError(f"生成内容验证失败: {validation_error}")

            # 创建教案记录
            lesson_plan_create = LessonPlanCreate(
                title=request.title,
                syllabus_id=request.syllabus_id,
                lesson_number=request.lesson_number,
                duration_minutes=request.duration_minutes,
                learning_objectives=parsed_content["learning_objectives"],
                content_structure=parsed_content["content_structure"],
                teaching_methods=parsed_content["teaching_methods"],
                resources_needed=parsed_content["resources_needed"],
                assessment_methods=parsed_content["assessment"],
                homework_assignments=parsed_content.get("homework"),
            )

            lesson_plan = await self.create_lesson_plan(db, lesson_plan_create)

            logger.info(f"成功生成教案 ID: {lesson_plan.id}")
            return lesson_plan

        except Exception as e:
            logger.error(f"教案生成失败: {str(e)}")
            raise

    async def create_lesson_plan(
        self,
        db: AsyncSession,
        lesson_plan_data: LessonPlanCreate,
    ) -> LessonPlanResponse:
        """创建教案."""
        try:
            # 创建教案实例
            lesson_plan = LessonPlan(
                title=lesson_plan_data.title,
                syllabus_id=lesson_plan_data.syllabus_id,
                lesson_number=lesson_plan_data.lesson_number,
                duration_minutes=lesson_plan_data.duration_minutes,
                learning_objectives=lesson_plan_data.learning_objectives,
                content_structure=lesson_plan_data.content_structure,
                teaching_methods=lesson_plan_data.teaching_methods,
                resources_needed=lesson_plan_data.resources_needed,
                assessment_methods=lesson_plan_data.assessment_methods,
                homework_assignments=lesson_plan_data.homework_assignments,
                collaboration_log=[],
            )

            db.add(lesson_plan)
            await db.commit()
            await db.refresh(lesson_plan)

            return LessonPlanResponse.model_validate(lesson_plan)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"创建教案失败: {str(e)}")
            raise

    async def get_lesson_plan(
        self,
        db: AsyncSession,
        lesson_plan_id: int,
    ) -> LessonPlanResponse | None:
        """获取教案详情."""
        try:
            result = await db.execute(
                select(LessonPlan)
                .options(selectinload(LessonPlan.syllabus))
                .where(LessonPlan.id == lesson_plan_id)
            )

            lesson_plan = result.scalar_one_or_none()

            if lesson_plan:
                return LessonPlanResponse.model_validate(lesson_plan)  # type: ignore[no-any-return]  # type: ignore[no-any-return]

            return None

        except Exception as e:
            logger.error(f"获取教案失败: {str(e)}")
            raise

    async def update_lesson_plan(
        self,
        db: AsyncSession,
        lesson_plan_id: int,
        update_data: LessonPlanUpdate,
        user_id: int,
    ) -> LessonPlanResponse | None:
        """更新教案."""
        try:
            result = await db.execute(select(LessonPlan).where(LessonPlan.id == lesson_plan_id))

            lesson_plan = result.scalar_one_or_none()
            if not lesson_plan:
                return None

            # 更新字段
            update_fields = update_data.model_dump(exclude_unset=True)
            for field, value in update_fields.items():
                setattr(lesson_plan, field, value)

            # 记录协作日志
            collaboration_entry = {
                "timestamp": "now",
                "user_id": user_id,
                "action": "update",
                "changes": list(update_fields.keys()),
            }

            if not lesson_plan.collaboration_log:
                lesson_plan.collaboration_log = []

            lesson_plan.collaboration_log.append(collaboration_entry)

            await db.commit()
            await db.refresh(lesson_plan)

            return LessonPlanResponse.model_validate(lesson_plan)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"更新教案失败: {str(e)}")
            raise

    async def list_lesson_plans(
        self,
        db: AsyncSession,
        syllabus_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[LessonPlanResponse], int]:
        """获取教案列表."""
        try:
            query = select(LessonPlan).options(selectinload(LessonPlan.syllabus))

            if syllabus_id:
                query = query.where(LessonPlan.syllabus_id == syllabus_id)

            # 按课时编号排序
            query = query.order_by(LessonPlan.lesson_number)

            # 获取总数
            count_query = select(LessonPlan.id)
            if syllabus_id:
                count_query = count_query.where(LessonPlan.syllabus_id == syllabus_id)

            total_result = await db.execute(count_query)
            total = len(total_result.fetchall())

            # 分页
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            result = await db.execute(query)
            lesson_plans = result.scalars().all()

            return [LessonPlanResponse.model_validate(lp) for lp in lesson_plans], total

        except Exception as e:
            logger.error(f"获取教案列表失败: {str(e)}")
            raise

    async def delete_lesson_plan(
        self,
        db: AsyncSession,
        lesson_plan_id: int,
    ) -> bool:
        """删除教案."""
        try:
            result = await db.execute(select(LessonPlan).where(LessonPlan.id == lesson_plan_id))

            lesson_plan = result.scalar_one_or_none()
            if not lesson_plan:
                return False

            # 检查是否有关联的课程安排
            from app.ai.models.ai_models import LessonSchedule

            schedules_result = await db.execute(
                select(LessonSchedule.id).where(LessonSchedule.lesson_plan_id == lesson_plan_id)
            )

            if schedules_result.fetchone():
                raise ValueError("存在关联的课程安排，无法删除教案")

            await db.delete(lesson_plan)
            await db.commit()

            logger.info(f"删除教案 ID: {lesson_plan_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"删除教案失败: {str(e)}")
            raise

    async def create_collaboration_session(
        self,
        db: AsyncSession,
        lesson_plan_id: int,
        initiator_id: int,
    ) -> CollaborationSessionResponse:
        """创建协作会话."""
        try:
            # 验证教案存在
            lesson_plan = await self.get_lesson_plan(db, lesson_plan_id)
            if not lesson_plan:
                raise ValueError(f"教案ID {lesson_plan_id} 不存在")

            # 生成会话ID
            import uuid

            session_id = str(uuid.uuid4())

            # 创建协作会话
            session = CollaborativeSession(
                session_id=session_id,
                resource_type="lesson_plan",
                resource_id=lesson_plan_id,
                participants=[initiator_id],
                session_data=lesson_plan.model_dump(),
                is_active=True,
                conflict_resolution_log=[],
            )

            db.add(session)
            await db.commit()
            await db.refresh(session)

            return CollaborationSessionResponse.model_validate(session)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"创建协作会话失败: {str(e)}")
            raise

    async def join_collaboration_session(
        self,
        db: AsyncSession,
        request: CollaborationJoinRequest,
    ) -> CollaborationSessionResponse | None:
        """加入协作会话."""
        try:
            result = await db.execute(
                select(CollaborativeSession).where(
                    and_(
                        CollaborativeSession.session_id == request.session_id,
                        CollaborativeSession.is_active,
                    )
                )
            )

            session = result.scalar_one_or_none()
            if not session:
                return None

            # 添加参与者
            if request.user_id not in session.participants:
                session.participants.append(request.user_id)
                session.last_activity = "now"

                await db.commit()
                await db.refresh(session)

            return CollaborationSessionResponse.model_validate(session)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"加入协作会话失败: {str(e)}")
            raise

    async def update_collaboration_session(
        self,
        db: AsyncSession,
        request: CollaborationUpdateRequest,
        user_id: int,
    ) -> CollaborationSessionResponse | None:
        """更新协作会话."""
        try:
            result = await db.execute(
                select(CollaborativeSession).where(
                    CollaborativeSession.session_id == request.session_id
                )
            )

            session = result.scalar_one_or_none()
            if not session or user_id not in session.participants:
                return None

            # 更新会话数据
            self._apply_collaborative_update(
                session.session_data,
                request.operation_type,
                request.target_path,
                request.data,
            )

            # 记录协作日志
            session.conflict_resolution_log.append(
                {
                    "timestamp": request.timestamp.isoformat(),
                    "user_id": user_id,
                    "operation": request.operation_type,
                    "path": request.target_path,
                }
            )

            session.last_activity = request.timestamp

            await db.commit()
            await db.refresh(session)

            return CollaborationSessionResponse.model_validate(session)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"更新协作会话失败: {str(e)}")
            raise

    async def _get_syllabus(self, db: AsyncSession, syllabus_id: int) -> AISyllabus | None:
        """获取大纲信息."""
        result = await db.execute(select(AISyllabus).where(AISyllabus.id == syllabus_id))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def _get_teacher(self, db: AsyncSession, teacher_id: int) -> User | None:
        """获取教师信息."""
        result = await db.execute(select(User).where(User.id == teacher_id))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def _get_lesson_plan_by_number(
        self,
        db: AsyncSession,
        syllabus_id: int,
        lesson_number: int,
    ) -> LessonPlan | None:
        """根据课时编号获取教案."""
        result = await db.execute(
            select(LessonPlan).where(
                and_(
                    LessonPlan.syllabus_id == syllabus_id,
                    LessonPlan.lesson_number == lesson_number,
                )
            )
        )
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    def _prepare_syllabus_context(self, syllabus: AISyllabus, lesson_number: int) -> str:
        """准备大纲上下文信息."""
        context_parts = [
            f"课程大纲：{syllabus.title}",
            f"课程目标：{json.dumps(syllabus.content.get('objectives', []), ensure_ascii=False)}",
        ]

        # 查找对应的周次和课时信息
        weekly_plan = syllabus.content.get("weekly_plan", [])
        for week in weekly_plan:
            for lesson in week.get("lessons", []):
                if lesson.get("lesson_number") == lesson_number:
                    context_parts.extend(
                        [
                            f"所在周次：第{week.get('week')}周",
                            f"课时内容：{lesson.get('content', '')}",
                            f"重点：{', '.join(lesson.get('key_points', []))}",
                            f"难点：{', '.join(lesson.get('difficulties', []))}",
                        ]
                    )
                    break

        return "\n".join(context_parts)

    def _apply_collaborative_update(
        self,
        session_data: dict[str, Any],
        operation_type: str,
        target_path: str,
        data: dict[str, Any],
    ) -> None:
        """应用协作更新操作."""
        keys = target_path.split(".")
        current = session_data

        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        target_key = keys[-1]

        # 执行操作
        if operation_type == "update":
            current[target_key] = data
        elif operation_type == "insert":
            if target_key not in current:
                current[target_key] = []
            current[target_key].append(data)
        elif operation_type == "delete":
            if target_key in current:
                del current[target_key]


def get_lesson_plan_service() -> LessonPlanService:
    """获取教案服务实例."""
    return LessonPlanService()
