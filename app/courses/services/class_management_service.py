"""班级管理与资源配置服务 - 需求4：班级管理与资源配置."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.models.course_models import Class, Course
from app.courses.schemas.class_schemas import (
    ClassBatchCreate,
    ClassCreate,
    ClassUpdate,
)
from app.courses.services.class_service import ClassResourceService, ClassService

logger = logging.getLogger(__name__)


class ClassManagementService:
    """班级管理与资源配置服务 - 需求4：班级管理与资源配置."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化班级管理服务."""
        self.db = db
        self.class_service = ClassService(db)
        self.resource_service = ClassResourceService(db)

    # ===== 班级基础管理 - 需求4.1 =====

    async def create_class(self, class_data: ClassCreate, creator_id: int) -> Class:
        """创建班级 - 需求4验收标准1."""
        try:
            # 调用基础服务创建班级
            class_obj = await self.class_service.create_class(class_data, creator_id)

            # 记录资源变更历史
            await self._record_resource_change(
                class_obj.id,
                "create",
                {},
                class_obj.resource_allocation,
                creator_id,
                "班级创建",
            )

            logger.info(f"班级创建成功: {class_obj.name} (ID: {class_obj.id})")
            return class_obj

        except Exception as e:
            logger.error(f"创建班级失败: {str(e)}")
            raise

    async def update_class(
        self, class_id: int, class_data: ClassUpdate, updater_id: int
    ) -> Class | None:
        """更新班级 - 需求4验收标准1."""
        try:
            # 获取更新前的班级信息
            old_class = await self.class_service.get_class_by_id(class_id)
            if not old_class:
                return None

            old_resource_allocation = old_class.resource_allocation or {}

            # 执行更新
            updated_class = await self.class_service.update_class(class_id, class_data)

            if updated_class:
                # 检查资源配置是否有变更
                new_resource_allocation = updated_class.resource_allocation or {}
                if old_resource_allocation != new_resource_allocation:
                    await self._record_resource_change(
                        class_id,
                        "update",
                        old_resource_allocation,
                        new_resource_allocation,
                        updater_id,
                        "班级信息更新",
                    )

                logger.info(f"班级更新成功: {updated_class.name} (ID: {class_id})")

            return updated_class

        except Exception as e:
            logger.error(f"更新班级失败: {str(e)}")
            raise

    async def delete_class(self, class_id: int, deleter_id: int) -> bool:
        """删除班级 - 需求4验收标准1."""
        try:
            # 获取删除前的班级信息
            class_obj = await self.class_service.get_class_by_id(class_id)
            if not class_obj:
                return False

            old_resource_allocation = class_obj.resource_allocation or {}

            # 执行删除
            success = await self.class_service.delete_class(class_id)

            if success:
                # 记录资源变更历史
                await self._record_resource_change(
                    class_id,
                    "delete",
                    old_resource_allocation,
                    {},
                    deleter_id,
                    "班级删除",
                )

                logger.info(f"班级删除成功: {class_obj.name} (ID: {class_id})")

            return success

        except Exception as e:
            logger.error(f"删除班级失败: {str(e)}")
            raise

    # ===== 基于课程模板创建班级 - 需求4.2 =====

    async def create_class_from_course_template(
        self, course_id: int, class_name: str, creator_id: int, **kwargs: Any
    ) -> Class:
        """基于课程模板创建班级 - 需求4验收标准2."""
        try:
            # 获取课程模板
            course = await self.db.get(Course, course_id)
            if not course:
                raise ValueError("课程模板不存在")

            # 从课程模板提取配置
            template_config = {
                "resource_allocation": course.resource_config or {},
                "max_students": kwargs.get("max_students", 50),
                "schedule": kwargs.get("schedule", {}),
                "start_date": kwargs.get("start_date"),
                "end_date": kwargs.get("end_date"),
                "description": kwargs.get("description", f"基于课程 {course.name} 创建的班级"),
            }

            # 创建班级数据
            class_data = ClassCreate(
                name=class_name,
                course_id=course_id,
                teacher_id=kwargs.get("teacher_id"),
                **template_config,
            )

            # 创建班级
            class_obj = await self.create_class(class_data, creator_id)

            logger.info(f"基于课程模板创建班级成功: {class_name} (课程: {course.name})")

            return class_obj

        except Exception as e:
            logger.error(f"基于课程模板创建班级失败: {str(e)}")
            raise

    async def batch_create_classes_from_template(
        self, batch_data: ClassBatchCreate, creator_id: int
    ) -> list[Class]:
        """批量创建班级 - 需求4验收标准2."""
        try:
            # 调用基础服务批量创建
            created_classes = await self.class_service.batch_create_classes(batch_data, creator_id)

            # 为每个班级记录资源变更历史
            for class_obj in created_classes:
                await self._record_resource_change(
                    class_obj.id,
                    "create",
                    {},
                    class_obj.resource_allocation,
                    creator_id,
                    f"批量创建班级 ({batch_data.class_prefix})",
                )

            logger.info(
                f"批量创建班级成功: {len(created_classes)} 个班级 (前缀: {batch_data.class_prefix})"
            )

            return created_classes

        except Exception as e:
            logger.error(f"批量创建班级失败: {str(e)}")
            raise

    # ===== 资源配置管理 - 需求4.3 =====

    async def allocate_class_resources(
        self, class_id: int, resource_allocation: dict[str, Any], allocator_id: int
    ) -> dict[str, Any]:
        """分配班级资源 - 需求4验收标准3."""
        try:
            # 获取当前资源配置
            class_obj = await self.class_service.get_class_by_id(class_id)
            if not class_obj:
                raise ValueError("班级不存在")

            old_allocation = class_obj.resource_allocation or {}

            # 执行资源分配
            result = await self.resource_service.allocate_resources(class_id, resource_allocation)

            # 记录资源变更历史
            await self._record_resource_change(
                class_id,
                "allocate",
                old_allocation,
                resource_allocation,
                allocator_id,
                "资源分配",
            )

            logger.info(f"班级资源分配成功: 班级ID {class_id}")
            return result

        except Exception as e:
            logger.error(f"分配班级资源失败: {str(e)}")
            raise

    async def update_class_resources(
        self, class_id: int, resource_updates: dict[str, Any], updater_id: int
    ) -> dict[str, Any]:
        """更新班级资源配置 - 需求4验收标准3."""
        try:
            # 获取当前资源配置
            class_obj = await self.class_service.get_class_by_id(class_id)
            if not class_obj:
                raise ValueError("班级不存在")

            old_allocation = class_obj.resource_allocation or {}

            # 执行资源更新
            result = await self.resource_service.update_resource_allocation(
                class_id, resource_updates
            )

            # 获取更新后的配置
            updated_class = await self.class_service.get_class_by_id(class_id)
            new_allocation = updated_class.resource_allocation if updated_class else {}

            # 记录资源变更历史
            await self._record_resource_change(
                class_id,
                "update",
                old_allocation,
                new_allocation,
                updater_id,
                "资源配置更新",
            )

            logger.info(f"班级资源更新成功: 班级ID {class_id}")
            return result

        except Exception as e:
            logger.error(f"更新班级资源失败: {str(e)}")
            raise

    # ===== 资源变更历史 - 需求4.4 =====

    async def get_resource_change_history(self, class_id: int) -> list[dict[str, Any]]:
        """获取班级资源变更历史 - 需求4验收标准4."""
        try:
            from app.courses.models.course_models import ClassResourceHistory

            # 查询资源变更历史
            stmt = (
                select(ClassResourceHistory)
                .where(ClassResourceHistory.class_id == class_id)
                .order_by(desc(ClassResourceHistory.changed_at))
            )

            result = await self.db.execute(stmt)
            history_records = result.scalars().all()

            # 转换为字典格式
            history = []
            for record in history_records:
                history.append(
                    {
                        "id": record.id,
                        "change_type": record.change_type,
                        "old_allocation": record.old_allocation,
                        "new_allocation": record.new_allocation,
                        "changed_by": record.changed_by,
                        "changed_at": record.changed_at,
                        "change_reason": record.change_reason,
                    }
                )

            return history

        except Exception as e:
            logger.error(f"获取资源变更历史失败: {str(e)}")
            return []

    async def _record_resource_change(
        self,
        class_id: int,
        change_type: str,
        old_allocation: dict[str, Any],
        new_allocation: dict[str, Any],
        changed_by: int,
        change_reason: str,
    ) -> None:
        """记录资源变更历史."""
        try:
            from app.courses.models.course_models import ClassResourceHistory

            # 创建变更记录
            history_record = ClassResourceHistory(
                class_id=class_id,
                change_type=change_type,
                old_allocation=old_allocation,
                new_allocation=new_allocation,
                changed_by=changed_by,
                change_reason=change_reason,
                changed_at=datetime.utcnow(),
            )

            self.db.add(history_record)
            await self.db.commit()

        except Exception as e:
            logger.error(f"记录资源变更历史失败: {str(e)}")
            # 不抛出异常，避免影响主要业务流程

    # ===== 绑定规则管理 - 需求4.5 =====

    async def get_classes_by_binding_rules(
        self, course_id: int | None = None, teacher_id: int | None = None
    ) -> list[Class]:
        """根据绑定规则获取班级列表 - 需求4验收标准5."""
        try:
            return await self.class_service.get_classes(
                course_id=course_id,
                teacher_id=teacher_id,
            )

        except Exception as e:
            logger.error(f"获取班级列表失败: {str(e)}")
            return []

    async def validate_class_binding_rules(
        self, class_id: int, teacher_id: int | None = None, course_id: int | None = None
    ) -> dict[str, Any]:
        """验证班级绑定规则 - 需求4验收标准5."""
        try:
            # 获取班级信息
            class_obj = await self.class_service.get_class_by_id(class_id)
            if not class_obj:
                raise ValueError("班级不存在")

            # 验证教师绑定规则
            if teacher_id and teacher_id != class_obj.teacher_id:
                await self.class_service._validate_class_teacher_binding(
                    class_obj.course_id, teacher_id
                )

            # 验证课程绑定规则
            if course_id and course_id != class_obj.course_id:
                # 检查是否违反1班级↔1课程规则
                if class_obj.course_id:
                    raise ValueError("班级已绑定课程，违反1班级↔1课程规则")

            return {
                "is_valid": True,
                "message": "绑定规则验证通过",
                "class_id": class_id,
                "current_teacher_id": class_obj.teacher_id,
                "current_course_id": class_obj.course_id,
            }

        except Exception as e:
            logger.error(f"验证绑定规则失败: {str(e)}")
            return {
                "is_valid": False,
                "message": str(e),
                "class_id": class_id,
            }
