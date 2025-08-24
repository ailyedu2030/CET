"""课程管理服务 - 实现课程全生命周期管理."""

from datetime import datetime

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.courses.models import Course, CourseVersion
from app.courses.schemas.course_schemas import (
    CourseCreate,
    CourseStatusUpdate,
    CourseUpdate,
)
from app.shared.models.enums import CourseShareLevel, CourseStatus


class CourseService:
    """课程管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化课程服务."""
        self.db = db

    async def create_course(self, course_data: CourseCreate, creator_id: int) -> Course:
        """创建课程."""
        # 如果基于模板创建，获取模板数据
        if course_data.parent_course_id:
            parent_course = await self.get_course_by_id(course_data.parent_course_id)
            if parent_course:
                # 复制模板课程的配置
                course_data.syllabus = parent_course.syllabus
                course_data.teaching_plan = parent_course.teaching_plan
                course_data.resource_config = parent_course.resource_config

        # 创建课程
        course = Course(
            **course_data.model_dump(exclude={"parent_course_id"}),
            created_by=creator_id,
            parent_course_id=course_data.parent_course_id,
        )

        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)

        # 创建初始版本
        await self._create_initial_version(course, creator_id)

        return course  # type: ignore[no-any-return]

    async def get_course_by_id(self, course_id: int) -> Course | None:
        """根据ID获取课程."""
        stmt = (
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.creator),
                selectinload(Course.approver),
                selectinload(Course.classes),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_courses(
        self,
        skip: int = 0,
        limit: int = 100,
        status: CourseStatus | None = None,
        creator_id: int | None = None,
    ) -> list[Course]:
        """获取课程列表."""
        stmt = select(Course).options(selectinload(Course.creator))

        # 添加筛选条件
        if status:
            stmt = stmt.where(Course.status == status)
        if creator_id:
            stmt = stmt.where(Course.created_by == creator_id)

        # 排序和分页
        stmt = stmt.order_by(desc(Course.updated_at)).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_course(
        self, course_id: int, course_data: CourseUpdate, updater_id: int
    ) -> Course | None:
        """更新课程."""
        course = await self.get_course_by_id(course_id)
        if not course:
            return None

        # 更新前创建版本快照
        await self._create_version_snapshot(course, updater_id, "更新前备份")

        # 更新课程信息
        update_data = course_data.model_dump(exclude_unset=True)
        if update_data:
            stmt = (
                update(Course)
                .where(Course.id == course_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()

        return await self.get_course_by_id(course_id)

    async def update_course_status(
        self, course_id: int, status_data: CourseStatusUpdate, updater_id: int
    ) -> Course | None:
        """更新课程状态."""
        course = await self.get_course_by_id(course_id)
        if not course:
            return None

        # 验证状态流转的合法性
        if not self._is_valid_status_transition(course.status, status_data.status):
            raise ValueError(f"无效的状态流转: {course.status} -> {status_data.status}")

        # 创建状态变更版本记录
        await self._create_version_snapshot(
            course,
            updater_id,
            status_data.change_log or f"状态更新: {status_data.status}",
        )

        # 更新状态
        stmt = (
            update(Course)
            .where(Course.id == course_id)
            .values(
                status=status_data.status,
                updated_at=datetime.utcnow(),
                approved_by=(
                    updater_id
                    if status_data.status == CourseStatus.APPROVED
                    else course.approved_by
                ),
                approved_at=(
                    datetime.utcnow()
                    if status_data.status == CourseStatus.APPROVED
                    else course.approved_at
                ),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get_course_by_id(course_id)

    async def delete_course(self, course_id: int) -> bool:
        """删除课程（软删除）."""
        course = await self.get_course_by_id(course_id)
        if not course:
            return False

        # 软删除：更新状态为已删除
        stmt = (
            update(Course)
            .where(Course.id == course_id)
            .values(status=CourseStatus.DELETED, updated_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return True

    async def get_course_versions(self, course_id: int) -> list[CourseVersion]:
        """获取课程版本历史."""
        stmt = (
            select(CourseVersion)
            .where(CourseVersion.course_id == course_id)
            .options(selectinload(CourseVersion.creator))
            .order_by(desc(CourseVersion.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def rollback_course_version(
        self, course_id: int, version_id: int, rollback_user_id: int
    ) -> Course | None:
        """回滚到指定版本."""
        # 获取目标版本
        version_stmt = select(CourseVersion).where(
            and_(
                CourseVersion.id == version_id,
                CourseVersion.course_id == course_id,
            )
        )
        version_result = await self.db.execute(version_stmt)
        target_version = version_result.scalar_one_or_none()

        if not target_version:
            return None

        course = await self.get_course_by_id(course_id)
        if not course:
            return None

        # 创建回滚前的备份
        await self._create_version_snapshot(course, rollback_user_id, "回滚前备份")

        # 恢复数据
        snapshot_data = target_version.snapshot_data
        if snapshot_data:
            # 更新课程数据
            update_data = {
                "name": snapshot_data.get("name", course.name),
                "description": snapshot_data.get("description", course.description),
                "syllabus": snapshot_data.get("syllabus", course.syllabus),
                "teaching_plan": snapshot_data.get("teaching_plan", course.teaching_plan),
                "resource_config": snapshot_data.get("resource_config", course.resource_config),
                "updated_at": datetime.utcnow(),
            }

            stmt = update(Course).where(Course.id == course_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()

        return await self.get_course_by_id(course_id)

    async def duplicate_course(
        self, course_id: int, new_name: str, creator_id: int
    ) -> Course | None:
        """复制课程."""
        original_course = await self.get_course_by_id(course_id)
        if not original_course:
            return None

        # 创建课程副本
        course_data = CourseCreate(
            name=new_name,
            description=f"基于 {original_course.name} 创建的副本",
            code=None,  # 不复制课程编码
            total_hours=original_course.total_hours,
            target_audience=original_course.target_audience,
            difficulty_level=original_course.difficulty_level,
            share_level=original_course.share_level,
            syllabus=original_course.syllabus,
            teaching_plan=original_course.teaching_plan,
            resource_config=original_course.resource_config,
            version="1.0",
            parent_course_id=course_id,
        )

        return await self.create_course(course_data, creator_id)

    def _is_valid_status_transition(
        self, current_status: CourseStatus, new_status: CourseStatus
    ) -> bool:
        """验证状态流转的合法性."""
        # 定义合法的状态流转
        valid_transitions = {
            CourseStatus.PREPARING: [
                CourseStatus.UNDER_REVIEW,
                CourseStatus.DELETED,
            ],
            CourseStatus.UNDER_REVIEW: [
                CourseStatus.APPROVED,
                CourseStatus.PREPARING,
                CourseStatus.DELETED,
            ],
            CourseStatus.APPROVED: [
                CourseStatus.PUBLISHED,
                CourseStatus.UNDER_REVIEW,
                CourseStatus.DELETED,
            ],
            CourseStatus.PUBLISHED: [
                CourseStatus.SUSPENDED,
                CourseStatus.ARCHIVED,
                CourseStatus.DELETED,
            ],
            CourseStatus.SUSPENDED: [
                CourseStatus.PUBLISHED,
                CourseStatus.ARCHIVED,
                CourseStatus.DELETED,
            ],
            CourseStatus.ARCHIVED: [
                CourseStatus.PUBLISHED,
                CourseStatus.DELETED,
            ],
            CourseStatus.DELETED: [],  # 删除后不能转换到其他状态
        }

        return new_status in valid_transitions.get(current_status, [])

    async def _create_initial_version(self, course: Course, creator_id: int) -> None:
        """创建初始版本记录."""
        snapshot_data = {
            "name": course.name,
            "description": course.description,
            "syllabus": course.syllabus,
            "teaching_plan": course.teaching_plan,
            "resource_config": course.resource_config,
            "status": course.status.value,
            "version": course.version,
        }

        version = CourseVersion(
            course_id=course.id,
            created_by=creator_id,
            version=course.version,
            version_name="初始版本",
            change_log="课程创建",
            snapshot_data=snapshot_data,
            is_active=True,
        )

        self.db.add(version)
        await self.db.commit()

    async def _create_version_snapshot(
        self, course: Course, creator_id: int, change_log: str
    ) -> None:
        """创建版本快照."""
        # 先将当前激活版本设为非激活
        stmt = (
            update(CourseVersion)
            .where(
                and_(
                    CourseVersion.course_id == course.id,
                    CourseVersion.is_active == True,  # noqa: E712
                )
            )
            .values(is_active=False)
        )
        await self.db.execute(stmt)

        # 生成新版本号
        latest_version = await self._get_next_version(course.id)

        # 创建快照数据
        snapshot_data = {
            "name": course.name,
            "description": course.description,
            "syllabus": course.syllabus,
            "teaching_plan": course.teaching_plan,
            "resource_config": course.resource_config,
            "status": course.status.value,
            "version": course.version,
        }

        # 创建新版本记录
        version = CourseVersion(
            course_id=course.id,
            created_by=creator_id,
            version=latest_version,
            change_log=change_log,
            snapshot_data=snapshot_data,
            is_active=True,
            is_backup=True,
        )

        self.db.add(version)
        await self.db.commit()

    async def _get_next_version(self, course_id: int) -> str:
        """生成下一个版本号."""
        stmt = (
            select(CourseVersion.version)
            .where(CourseVersion.course_id == course_id)
            .order_by(desc(CourseVersion.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        latest_version = result.scalar_one_or_none()

        if not latest_version:
            return "1.0"

        # 简单的版本号递增逻辑 (例如: 1.0 -> 1.1 -> 1.2)
        try:
            parts = latest_version.split(".")
            major, minor = int(parts[0]), int(parts[1])
            return f"{major}.{minor + 1}"
        except (ValueError, IndexError):
            return "1.0"


class CoursePermissionService:
    """课程权限管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化权限服务."""
        self.db = db

    async def check_course_access(self, course_id: int, user_id: int, action: str) -> bool:
        """检查课程访问权限."""
        course = await self.db.get(Course, course_id)
        if not course:
            return False

        # 创建者拥有所有权限
        if course.created_by == user_id:
            return True

        # 根据共享级别判断权限
        if action == "read":
            # 读取权限基于共享级别
            return course.share_level in [
                CourseShareLevel.CLASS_SHARED,
                CourseShareLevel.SCHOOL_SHARED,
                CourseShareLevel.PUBLIC,
            ]

        # 其他操作需要是创建者或有特殊权限
        return False

    async def get_accessible_courses(self, user_id: int, user_role: str) -> list[Course]:
        """获取用户可访问的课程列表."""
        # 管理员可以访问所有课程
        if user_role == "admin":
            stmt = select(Course).where(Course.status != CourseStatus.DELETED)
        else:
            # 普通用户只能访问自己创建的和公开共享的课程
            stmt = select(Course).where(
                and_(
                    Course.status != CourseStatus.DELETED,
                    (
                        (Course.created_by == user_id)
                        | (
                            Course.share_level.in_(
                                [
                                    CourseShareLevel.SCHOOL_SHARED,
                                    CourseShareLevel.PUBLIC,
                                ]
                            )
                        )
                    ),
                )
            )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
