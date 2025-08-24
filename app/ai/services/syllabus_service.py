"""大纲生成服务."""

import json
import logging
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.models.ai_models import AISyllabus
from app.ai.schemas.ai_schemas import (
    SyllabusCreate,
    SyllabusGenerationRequest,
    SyllabusResponse,
    SyllabusUpdate,
)
from app.ai.services.deepseek_service import get_deepseek_service
from app.ai.utils.content_generator import SyllabusGenerator
from app.courses.models.course_models import Course
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class SyllabusService:
    """大纲生成与管理服务."""

    def __init__(self) -> None:
        self.deepseek_service = get_deepseek_service()
        self.content_generator = SyllabusGenerator()

    async def generate_syllabus(
        self,
        db: AsyncSession,
        request: SyllabusGenerationRequest,
        teacher_id: int,
    ) -> SyllabusResponse:
        """生成新的教学大纲."""
        try:
            # 验证课程存在
            course = await self._get_course(db, request.course_id)
            if not course:
                raise ValueError(f"课程ID {request.course_id} 不存在")

            # 验证教师权限
            teacher = await self._get_teacher(db, teacher_id)
            if not teacher:
                raise ValueError(f"教师ID {teacher_id} 不存在")

            # 准备AI生成提示
            prompt = self.content_generator.prepare_prompt(
                title=request.title,
                objectives=request.course_objectives,
                total_hours=request.target_hours,
                difficulty_level=request.difficulty_level,
                source_materials=request.source_materials,
                special_requirements=request.special_requirements,
            )

            logger.info(f"为课程{course.name}生成大纲，教师: {teacher.username}")

            # 调用AI生成内容
            (
                success,
                generated_content,
                error_msg,
            ) = await self.deepseek_service.generate_syllabus_content(
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

            # 创建大纲记录
            syllabus_create = SyllabusCreate(
                title=request.title,
                course_id=request.course_id,
                content=parsed_content,
                version="1.0.0",
                ai_generated=True,
                source_materials=request.source_materials,
            )

            syllabus = await self.create_syllabus(db, syllabus_create, teacher_id)

            logger.info(f"成功生成大纲 ID: {syllabus.id}")
            return syllabus

        except Exception as e:
            logger.error(f"大纲生成失败: {str(e)}")
            raise

    async def create_syllabus(
        self,
        db: AsyncSession,
        syllabus_data: SyllabusCreate,
        teacher_id: int,
    ) -> SyllabusResponse:
        """创建大纲."""
        try:
            # 检查同一课程是否已有相同版本的大纲
            existing = await db.execute(
                select(AISyllabus).where(
                    and_(
                        AISyllabus.course_id == syllabus_data.course_id,
                        AISyllabus.version == syllabus_data.version,
                        AISyllabus.teacher_id == teacher_id,
                    )
                )
            )

            if existing.scalar_one_or_none():
                # 自动递增版本号
                syllabus_data.version = await self._get_next_version(
                    db, syllabus_data.course_id, teacher_id
                )

            # 创建大纲实例
            syllabus = AISyllabus(
                title=syllabus_data.title,
                course_id=syllabus_data.course_id,
                teacher_id=teacher_id,
                content=syllabus_data.content,
                version=syllabus_data.version,
                ai_generated=syllabus_data.ai_generated,
                source_materials=syllabus_data.source_materials,
                status="draft",
            )

            db.add(syllabus)
            await db.commit()
            await db.refresh(syllabus)

            return SyllabusResponse.model_validate(syllabus)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"创建大纲失败: {str(e)}")
            raise

    async def get_syllabus(
        self,
        db: AsyncSession,
        syllabus_id: int,
        teacher_id: int | None = None,
    ) -> SyllabusResponse | None:
        """获取大纲详情."""
        try:
            query = (
                select(AISyllabus)
                .options(
                    selectinload(AISyllabus.course),
                    selectinload(AISyllabus.teacher),
                )
                .where(AISyllabus.id == syllabus_id)
            )

            # 如果指定了教师ID，添加权限过滤
            if teacher_id:
                query = query.where(AISyllabus.teacher_id == teacher_id)

            result = await db.execute(query)
            syllabus = result.scalar_one_or_none()

            if syllabus:
                return SyllabusResponse.model_validate(syllabus)  # type: ignore[no-any-return]

            return None

        except Exception as e:
            logger.error(f"获取大纲失败: {str(e)}")
            raise

    async def update_syllabus(
        self,
        db: AsyncSession,
        syllabus_id: int,
        update_data: SyllabusUpdate,
        teacher_id: int,
    ) -> SyllabusResponse | None:
        """更新大纲."""
        try:
            # 获取现有大纲
            result = await db.execute(
                select(AISyllabus).where(
                    and_(
                        AISyllabus.id == syllabus_id,
                        AISyllabus.teacher_id == teacher_id,
                    )
                )
            )

            syllabus = result.scalar_one_or_none()
            if not syllabus:
                return None

            # 更新字段
            update_fields = update_data.model_dump(exclude_unset=True)
            for field, value in update_fields.items():
                setattr(syllabus, field, value)

            # 如果内容有变更，自动更新版本
            if "content" in update_fields:
                syllabus.version = await self._get_next_version(db, syllabus.course_id, teacher_id)

            await db.commit()
            await db.refresh(syllabus)

            return SyllabusResponse.model_validate(syllabus)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"更新大纲失败: {str(e)}")
            raise

    async def list_syllabi(
        self,
        db: AsyncSession,
        course_id: int | None = None,
        teacher_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[SyllabusResponse], int]:
        """获取大纲列表."""
        try:
            # 构建查询
            query = select(AISyllabus).options(
                selectinload(AISyllabus.course),
                selectinload(AISyllabus.teacher),
            )

            # 添加过滤条件
            if course_id:
                query = query.where(AISyllabus.course_id == course_id)
            if teacher_id:
                query = query.where(AISyllabus.teacher_id == teacher_id)
            if status:
                query = query.where(AISyllabus.status == status)

            # 排序
            query = query.order_by(desc(AISyllabus.updated_at))

            # 获取总数
            count_query = select(AISyllabus.id)
            if course_id:
                count_query = count_query.where(AISyllabus.course_id == course_id)
            if teacher_id:
                count_query = count_query.where(AISyllabus.teacher_id == teacher_id)
            if status:
                count_query = count_query.where(AISyllabus.status == status)

            total_result = await db.execute(count_query)
            total = len(total_result.fetchall())

            # 分页
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            result = await db.execute(query)
            syllabi = result.scalars().all()

            return [SyllabusResponse.model_validate(s) for s in syllabi], total

        except Exception as e:
            logger.error(f"获取大纲列表失败: {str(e)}")
            raise

    async def delete_syllabus(
        self,
        db: AsyncSession,
        syllabus_id: int,
        teacher_id: int,
    ) -> bool:
        """删除大纲."""
        try:
            result = await db.execute(
                select(AISyllabus).where(
                    and_(
                        AISyllabus.id == syllabus_id,
                        AISyllabus.teacher_id == teacher_id,
                    )
                )
            )

            syllabus = result.scalar_one_or_none()
            if not syllabus:
                return False

            # 检查是否有关联的教案
            from app.ai.models.ai_models import LessonPlan

            lesson_plans_result = await db.execute(
                select(LessonPlan.id).where(LessonPlan.syllabus_id == syllabus_id)
            )

            if lesson_plans_result.fetchone():
                raise ValueError("存在关联的教案，无法删除大纲")

            await db.delete(syllabus)
            await db.commit()

            logger.info(f"删除大纲 ID: {syllabus_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"删除大纲失败: {str(e)}")
            raise

    async def approve_syllabus(
        self,
        db: AsyncSession,
        syllabus_id: int,
        approver_id: int,
    ) -> SyllabusResponse | None:
        """审批大纲."""
        try:
            result = await db.execute(select(AISyllabus).where(AISyllabus.id == syllabus_id))

            syllabus = result.scalar_one_or_none()
            if not syllabus:
                return None

            if syllabus.status not in ["draft", "review"]:
                raise ValueError(f"大纲状态为{syllabus.status}，无法审批")

            syllabus.status = "approved"

            await db.commit()
            await db.refresh(syllabus)

            logger.info(f"大纲 ID: {syllabus_id} 已审批通过")
            return SyllabusResponse.model_validate(syllabus)  # type: ignore[no-any-return]

        except Exception as e:
            await db.rollback()
            logger.error(f"审批大纲失败: {str(e)}")
            raise

    async def get_syllabus_versions(
        self,
        db: AsyncSession,
        course_id: int,
        teacher_id: int | None = None,
    ) -> list[SyllabusResponse]:
        """获取大纲版本历史."""
        try:
            query = select(AISyllabus).where(AISyllabus.course_id == course_id)

            if teacher_id:
                query = query.where(AISyllabus.teacher_id == teacher_id)

            query = query.order_by(desc(AISyllabus.created_at))

            result = await db.execute(query)
            syllabi = result.scalars().all()

            return [SyllabusResponse.model_validate(s) for s in syllabi]

        except Exception as e:
            logger.error(f"获取大纲版本失败: {str(e)}")
            raise

    async def _get_course(self, db: AsyncSession, course_id: int) -> Course | None:
        """获取课程信息."""
        result = await db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def _get_teacher(self, db: AsyncSession, teacher_id: int) -> User | None:
        """获取教师信息."""
        result = await db.execute(select(User).where(User.id == teacher_id))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def _get_next_version(
        self,
        db: AsyncSession,
        course_id: int,
        teacher_id: int,
    ) -> str:
        """获取下一个版本号."""
        result = await db.execute(
            select(AISyllabus.version)
            .where(
                and_(
                    AISyllabus.course_id == course_id,
                    AISyllabus.teacher_id == teacher_id,
                )
            )
            .order_by(desc(AISyllabus.created_at))
            .limit(1)
        )

        latest_version = result.scalar_one_or_none()

        if not latest_version:
            return "1.0.0"

        # 简单的版本递增逻辑
        try:
            major, minor, patch = map(int, latest_version.split("."))
            return f"{major}.{minor}.{patch + 1}"
        except (ValueError, AttributeError):
            return "1.0.1"

    async def regenerate_syllabus_section(
        self,
        db: AsyncSession,
        syllabus_id: int,
        section_path: str,
        teacher_id: int,
        additional_requirements: str | None = None,
    ) -> SyllabusResponse | None:
        """重新生成大纲的特定部分."""
        try:
            # 获取现有大纲
            syllabus = await self.get_syllabus(db, syllabus_id, teacher_id)
            if not syllabus:
                return None

            # 构建针对特定部分的提示
            section_prompt = f"""
请重新生成教学大纲中的"{section_path}"部分。

当前大纲内容：
{json.dumps(syllabus.content, ensure_ascii=False, indent=2)}

附加要求：
{additional_requirements or "无"}

请只返回该部分的更新内容，格式与原始结构保持一致。
"""

            (
                success,
                generated_content,
                error_msg,
            ) = await self.deepseek_service.generate_syllabus_content(
                prompt=section_prompt,
                user_id=teacher_id,
            )

            if not success:
                raise ValueError(f"AI生成失败: {error_msg}")

            # 解析生成的内容并更新大纲
            try:
                if generated_content is None:
                    raise ValueError("生成内容为空")
                section_data = json.loads(generated_content)

                # 更新大纲内容的特定部分
                content = syllabus.content.copy()
                self._update_nested_dict(content, section_path, section_data)

                # 保存更新
                update_data = SyllabusUpdate(
                    title=None,
                    content=content,
                    version=None,
                    status=None,
                    source_materials=None,
                )
                return await self.update_syllabus(db, syllabus_id, update_data, teacher_id)

            except json.JSONDecodeError as e:
                raise ValueError("生成内容格式错误") from e

        except Exception as e:
            logger.error(f"重新生成大纲部分失败: {str(e)}")
            raise

    def _update_nested_dict(self, target_dict: dict[str, Any], path: str, value: Any) -> None:
        """更新嵌套字典的特定路径."""
        keys = path.split(".")
        current = target_dict

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


def get_syllabus_service() -> SyllabusService:
    """获取大纲服务实例."""
    return SyllabusService()
