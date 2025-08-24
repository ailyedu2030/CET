"""课程模板管理服务 - 实现课程模板的创建、管理和使用."""

from typing import Any

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.courses.models import Course, CourseTemplate
from app.courses.schemas.course_schemas import (
    CourseTemplateCreate,
    CourseTemplateUpdate,
)


class CourseTemplateService:
    """课程模板管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化模板服务."""
        self.db = db

    async def create_template(
        self, template_data: CourseTemplateCreate, creator_id: int
    ) -> CourseTemplate:
        """创建课程模板."""
        # 如果基于现有课程创建模板
        if template_data.source_course_id:
            source_course = await self.db.get(Course, template_data.source_course_id)
            if source_course:
                # 从源课程生成模板数据
                template_data.template_data = self._extract_template_data(source_course)
                if not template_data.default_settings:
                    template_data.default_settings = {
                        "difficulty_level": source_course.difficulty_level.value,
                        "share_level": source_course.share_level.value,
                        "total_hours": source_course.total_hours,
                    }

        # 创建模板
        template = CourseTemplate(
            **template_data.model_dump(),
            created_by=creator_id,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return template  # type: ignore[no-any-return]

    async def get_template_by_id(self, template_id: int) -> CourseTemplate | None:
        """根据ID获取模板."""
        stmt = (
            select(CourseTemplate)
            .where(CourseTemplate.id == template_id)
            .options(
                selectinload(CourseTemplate.creator),
                selectinload(CourseTemplate.source_course),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        is_public: bool | None = None,
        creator_id: int | None = None,
    ) -> list[CourseTemplate]:
        """获取模板列表."""
        stmt = select(CourseTemplate).options(selectinload(CourseTemplate.creator))

        # 添加筛选条件
        conditions = [CourseTemplate.is_active == True]  # noqa: E712

        if category:
            conditions.append(CourseTemplate.category == category)
        if is_public is not None:
            conditions.append(CourseTemplate.is_public == is_public)
        if creator_id:
            conditions.append(CourseTemplate.created_by == creator_id)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 按使用次数排序
        stmt = (
            stmt.order_by(desc(CourseTemplate.usage_count), desc(CourseTemplate.updated_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_public_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
    ) -> list[CourseTemplate]:
        """获取公开模板列表."""
        return await self.get_templates(skip=skip, limit=limit, category=category, is_public=True)

    async def get_popular_templates(
        self, limit: int = 10, category: str | None = None
    ) -> list[CourseTemplate]:
        """获取热门模板列表."""
        stmt = select(CourseTemplate).options(selectinload(CourseTemplate.creator))

        conditions = [
            CourseTemplate.is_active == True,  # noqa: E712
            CourseTemplate.is_public == True,  # noqa: E712
            CourseTemplate.usage_count > 0,
        ]

        if category:
            conditions.append(CourseTemplate.category == category)

        stmt = stmt.where(and_(*conditions)).order_by(desc(CourseTemplate.usage_count)).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_template(
        self, template_id: int, template_data: CourseTemplateUpdate
    ) -> CourseTemplate | None:
        """更新模板."""
        template = await self.get_template_by_id(template_id)
        if not template:
            return None

        # 更新模板信息
        update_data = template_data.model_dump(exclude_unset=True)
        if update_data:
            stmt = (
                update(CourseTemplate).where(CourseTemplate.id == template_id).values(**update_data)
            )
            await self.db.execute(stmt)
            await self.db.commit()

        return await self.get_template_by_id(template_id)

    async def delete_template(self, template_id: int) -> bool:
        """删除模板（软删除）."""
        template = await self.get_template_by_id(template_id)
        if not template:
            return False

        # 软删除：设为不激活
        stmt = (
            update(CourseTemplate).where(CourseTemplate.id == template_id).values(is_active=False)
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return True

    async def use_template(
        self, template_id: int, course_name: str, creator_id: int
    ) -> dict[str, Any] | None:
        """使用模板创建课程数据."""
        template = await self.get_template_by_id(template_id)
        if not template:
            return None

        # 增加使用计数
        await self._increment_usage_count(template_id)

        # 生成课程数据
        course_data = self._generate_course_from_template(template, course_name, creator_id)

        return course_data

    async def clone_template(
        self, template_id: int, new_name: str, creator_id: int
    ) -> CourseTemplate | None:
        """克隆模板."""
        original_template = await self.get_template_by_id(template_id)
        if not original_template:
            return None

        # 创建模板副本
        template_data = CourseTemplateCreate(
            name=new_name,
            description=f"基于 {original_template.name} 创建的副本",
            category=original_template.category,
            template_data=original_template.template_data.copy(),
            default_settings=original_template.default_settings.copy(),
            is_public=False,  # 克隆的模板默认为私有
            source_course_id=original_template.source_course_id,
        )

        return await self.create_template(template_data, creator_id)

    async def get_template_categories(self) -> list[str]:
        """获取模板分类列表."""
        stmt = (
            select(CourseTemplate.category)
            .distinct()
            .where(
                and_(
                    CourseTemplate.is_active == True,  # noqa: E712
                    CourseTemplate.category.isnot(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        categories = result.scalars().all()
        return [category for category in categories if category]

    async def _increment_usage_count(self, template_id: int) -> None:
        """增加模板使用次数."""
        stmt = (
            update(CourseTemplate)
            .where(CourseTemplate.id == template_id)
            .values(usage_count=CourseTemplate.usage_count + 1)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    def _extract_template_data(self, course: Course) -> dict[str, Any]:
        """从课程中提取模板数据."""
        return {
            "basic_info": {
                "description_template": course.description or "",
                "target_audience": course.target_audience,
                "total_hours": course.total_hours,
            },
            "syllabus_template": course.syllabus,
            "teaching_plan_template": course.teaching_plan,
            "resource_config_template": course.resource_config,
            "metadata": {
                "source_course_id": course.id,
                "source_course_name": course.name,
                "difficulty_level": course.difficulty_level.value,
                "share_level": course.share_level.value,
            },
        }

    def _generate_course_from_template(
        self, template: CourseTemplate, course_name: str, creator_id: int
    ) -> dict[str, Any]:
        """从模板生成课程数据."""
        template_data = template.template_data
        default_settings = template.default_settings

        return {
            "name": course_name,
            "description": template_data.get("basic_info", {}).get("description_template", ""),
            "target_audience": template_data.get("basic_info", {}).get("target_audience"),
            "total_hours": template_data.get("basic_info", {}).get("total_hours"),
            "difficulty_level": default_settings.get("difficulty_level", "elementary"),
            "share_level": default_settings.get("share_level", "private"),
            "syllabus": template_data.get("syllabus_template", {}),
            "teaching_plan": template_data.get("teaching_plan_template", {}),
            "resource_config": template_data.get("resource_config_template", {}),
            "version": "1.0",
            "created_by": creator_id,
            "template_id": template.id,
        }
