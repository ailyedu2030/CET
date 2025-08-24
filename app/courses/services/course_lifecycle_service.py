"""课程全生命周期管理服务 - 需求3：课程全生命周期管理."""

import logging
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.courses.models.course_models import Course, CourseVersion
from app.courses.schemas.course_schemas import (
    CourseCreate,
    CourseStatusUpdate,
    CourseUpdate,
)
from app.courses.services.course_service import CourseService
from app.shared.models.enums import CourseStatus

logger = logging.getLogger(__name__)


class CourseLifecycleService:
    """课程全生命周期管理服务 - 需求3：课程全生命周期管理."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化课程生命周期服务."""
        self.db = db
        self.course_service = CourseService(db)

    # ===== 课程创建和基础管理 - 需求3.1 =====

    async def create_course(self, course_data: CourseCreate, creator_id: int) -> Course:
        """创建课程 - 需求3验收标准1."""
        try:
            # 调用基础服务创建课程（状态默认为PREPARING）
            course = await self.course_service.create_course(course_data, creator_id)

            logger.info(f"课程创建成功: {course.name} (ID: {course.id})")
            return course

        except Exception as e:
            logger.error(f"创建课程失败: {str(e)}")
            raise

    async def update_course(
        self, course_id: int, course_data: CourseUpdate, updater_id: int
    ) -> Course | None:
        """更新课程 - 需求3验收标准1."""
        try:
            course = await self.course_service.update_course(course_id, course_data, updater_id)

            if course:
                logger.info(f"课程更新成功: {course.name} (ID: {course.id})")

            return course

        except Exception as e:
            logger.error(f"更新课程失败: {str(e)}")
            raise

    async def delete_course(self, course_id: int) -> bool:
        """删除课程 - 需求3验收标准1."""
        try:
            success = await self.course_service.delete_course(course_id)

            if success:
                logger.info(f"课程删除成功: ID {course_id}")

            return success

        except Exception as e:
            logger.error(f"删除课程失败: {str(e)}")
            raise

    # ===== 状态流转管理 - 需求3.2 =====

    async def transition_course_status(
        self, course_id: int, status_data: CourseStatusUpdate, updater_id: int
    ) -> Course | None:
        """课程状态流转 - 需求3验收标准2：筹备中→审核中→已上线→已归档."""
        try:
            course = await self.course_service.get_course_by_id(course_id)
            if not course:
                return None

            # 记录状态变更前的信息
            old_status = course.status

            # 执行状态更新
            updated_course = await self.course_service.update_course_status(
                course_id, status_data, updater_id
            )

            if updated_course:
                logger.info(
                    f"课程状态流转成功: {course.name} ({old_status} → {status_data.status})"
                )

            return updated_course

        except Exception as e:
            logger.error(f"课程状态流转失败: {str(e)}")
            raise

    async def get_course_status_history(self, course_id: int) -> list[dict[str, Any]]:
        """获取课程状态变更历史."""
        try:
            versions = await self.course_service.get_course_versions(course_id)

            status_history = []
            for version in versions:
                if version.snapshot_data and "status" in version.snapshot_data:
                    status_history.append(
                        {
                            "version": version.version,
                            "status": version.snapshot_data["status"],
                            "change_log": version.change_log,
                            "changed_at": version.created_at,
                            "changed_by": version.created_by,
                        }
                    )

            return status_history

        except Exception as e:
            logger.error(f"获取状态历史失败: {str(e)}")
            return []

    # ===== 审批流程管理 - 需求3.3 =====

    async def submit_for_review(
        self, course_id: int, submitter_id: int, review_notes: str | None = None
    ) -> Course | None:
        """提交课程审核 - 需求3验收标准3."""
        try:
            course = await self.course_service.get_course_by_id(course_id)
            if not course:
                return None

            # 验证当前状态是否可以提交审核
            if course.status != CourseStatus.PREPARING:
                raise ValueError(f"课程状态为{course.status}，无法提交审核")

            # 更新状态为审核中
            status_data = CourseStatusUpdate(
                status=CourseStatus.UNDER_REVIEW,
                change_log=review_notes or "提交审核",
            )

            updated_course = await self.transition_course_status(
                course_id, status_data, submitter_id
            )

            if updated_course:
                logger.info(f"课程提交审核成功: {course.name} (ID: {course.id})")

            return updated_course

        except Exception as e:
            logger.error(f"提交课程审核失败: {str(e)}")
            raise

    async def approve_course(
        self, course_id: int, approver_id: int, approval_notes: str | None = None
    ) -> Course | None:
        """审核通过课程 - 需求3验收标准3."""
        try:
            course = await self.course_service.get_course_by_id(course_id)
            if not course:
                return None

            # 验证当前状态是否可以审核
            if course.status != CourseStatus.UNDER_REVIEW:
                raise ValueError(f"课程状态为{course.status}，无法审核")

            # 更新状态为已审核
            status_data = CourseStatusUpdate(
                status=CourseStatus.APPROVED,
                change_log=approval_notes or "审核通过",
            )

            updated_course = await self.transition_course_status(
                course_id, status_data, approver_id
            )

            if updated_course:
                logger.info(f"课程审核通过: {course.name} (ID: {course.id})")

            return updated_course

        except Exception as e:
            logger.error(f"课程审核失败: {str(e)}")
            raise

    async def reject_course(
        self, course_id: int, reviewer_id: int, rejection_reason: str
    ) -> Course | None:
        """审核拒绝课程 - 需求3验收标准3."""
        try:
            course = await self.course_service.get_course_by_id(course_id)
            if not course:
                return None

            # 验证当前状态是否可以拒绝
            if course.status != CourseStatus.UNDER_REVIEW:
                raise ValueError(f"课程状态为{course.status}，无法拒绝")

            # 更新状态回到筹备中
            status_data = CourseStatusUpdate(
                status=CourseStatus.PREPARING,
                change_log=f"审核拒绝: {rejection_reason}",
            )

            updated_course = await self.transition_course_status(
                course_id, status_data, reviewer_id
            )

            if updated_course:
                logger.info(f"课程审核拒绝: {course.name} (ID: {course.id})")

            return updated_course

        except Exception as e:
            logger.error(f"课程审核拒绝失败: {str(e)}")
            raise

    # ===== 模板管理 - 需求3.4 =====

    async def create_course_from_template(
        self, template_id: int, course_name: str, creator_id: int
    ) -> Course | None:
        """基于模板创建课程 - 需求3验收标准4."""
        try:
            # 获取模板课程
            template_course = await self.course_service.get_course_by_id(template_id)
            if not template_course:
                raise ValueError("模板课程不存在")

            # 创建课程数据
            course_data = CourseCreate(
                name=course_name,
                description=template_course.description,
                code=None,
                syllabus=template_course.syllabus,
                teaching_plan=template_course.teaching_plan,
                resource_config=template_course.resource_config,
                total_hours=template_course.total_hours,
                target_audience=template_course.target_audience,
                difficulty_level=template_course.difficulty_level,
                share_level=template_course.share_level,
                version="1.0",
                parent_course_id=template_id,
            )

            # 创建新课程
            new_course = await self.create_course(course_data, creator_id)

            logger.info(f"基于模板创建课程成功: {course_name} (模板: {template_course.name})")

            return new_course

        except Exception as e:
            logger.error(f"基于模板创建课程失败: {str(e)}")
            raise

    # ===== 版本控制 - 需求3.6 =====

    async def get_course_versions(self, course_id: int) -> list[CourseVersion]:
        """获取课程版本历史 - 需求3验收标准6."""
        try:
            return await self.course_service.get_course_versions(course_id)

        except Exception as e:
            logger.error(f"获取课程版本失败: {str(e)}")
            return []

    async def rollback_course_version(
        self, course_id: int, version_id: int, rollback_user_id: int
    ) -> Course | None:
        """回滚课程版本 - 需求3验收标准6."""
        try:
            course = await self.course_service.rollback_course_version(
                course_id, version_id, rollback_user_id
            )

            if course:
                logger.info(f"课程版本回滚成功: {course.name} (ID: {course.id})")

            return course

        except Exception as e:
            logger.error(f"课程版本回滚失败: {str(e)}")
            raise

    # ===== 权限管理 - 需求3.7 =====

    async def get_courses_by_permission(
        self, user_id: int, user_role: str, status_filter: CourseStatus | None = None
    ) -> list[Course]:
        """根据权限获取课程列表 - 需求3验收标准7."""
        try:
            # 构建查询
            query = select(Course).options(
                selectinload(Course.creator),
                selectinload(Course.approver),
            )

            # 根据用户角色过滤
            if user_role == "admin":
                # 管理员可以查看所有课程
                pass
            elif user_role == "teacher":
                # 教师只能查看自己创建的课程和公开课程
                query = query.where(
                    (Course.created_by == user_id)
                    | (Course.share_level.in_(["class_shared", "school_shared", "public"]))
                )
            else:
                # 学生只能查看公开课程
                query = query.where(Course.share_level.in_(["school_shared", "public"]))

            # 状态过滤
            if status_filter:
                query = query.where(Course.status == status_filter)

            # 排除已删除的课程
            query = query.where(Course.status != CourseStatus.DELETED)

            # 按创建时间倒序
            query = query.order_by(desc(Course.created_at))

            result = await self.db.execute(query)
            courses = list(result.scalars().all())

            logger.info(f"获取课程列表成功: 用户{user_id}, 角色{user_role}, 数量{len(courses)}")
            return courses

        except Exception as e:
            logger.error(f"获取课程列表失败: {str(e)}")
            return []
