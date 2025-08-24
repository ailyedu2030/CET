"""班级管理服务 - 实现班级CRUD操作、资源配置和规则验证."""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.courses.models import Class, Course
from app.courses.schemas.class_schemas import (
    ClassBatchCreate,
    ClassConflictCheck,
    ClassCreate,
    ClassUpdate,
    ConflictCheckResult,
    StudentEnrollmentRequest,
)
from app.courses.utils.conflict_detection_utils import ConflictDetectionUtils


class ClassService:
    """班级管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化班级服务."""
        self.db = db

    async def create_class(self, class_data: ClassCreate, creator_id: int) -> Class:
        """创建班级."""
        # 验证课程存在
        course = await self.db.get(Course, class_data.course_id)
        if not course:
            raise ValueError("指定的课程不存在")

        # 检查绑定规则
        if class_data.teacher_id:
            await self._validate_class_teacher_binding(class_data.course_id, class_data.teacher_id)

        # 创建班级
        class_obj = Class(
            **class_data.model_dump(exclude={"teacher_id"}),
            teacher_id=class_data.teacher_id,
            status="preparing",
            current_students=0,
            completion_rate=0.0,
        )

        self.db.add(class_obj)
        await self.db.commit()
        await self.db.refresh(class_obj)

        return class_obj  # type: ignore[no-any-return]

    async def get_class_by_id(self, class_id: int) -> Class | None:
        """根据ID获取班级."""
        stmt = (
            select(Class)
            .where(Class.id == class_id)
            .options(
                selectinload(Class.course),
                selectinload(Class.teacher),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_classes(
        self,
        skip: int = 0,
        limit: int = 100,
        course_id: int | None = None,
        teacher_id: int | None = None,
        status: str | None = None,
    ) -> list[Class]:
        """获取班级列表."""
        stmt = select(Class).options(selectinload(Class.course), selectinload(Class.teacher))

        # 添加筛选条件
        conditions = []
        if course_id:
            conditions.append(Class.course_id == course_id)
        if teacher_id:
            conditions.append(Class.teacher_id == teacher_id)
        if status:
            conditions.append(Class.status == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 排序和分页
        stmt = stmt.order_by(desc(Class.updated_at)).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_class(self, class_id: int, class_data: ClassUpdate) -> Class | None:
        """更新班级."""
        class_obj = await self.get_class_by_id(class_id)
        if not class_obj:
            return None

        # 验证教师分配
        if class_data.teacher_id and class_data.teacher_id != class_obj.teacher_id:
            await self._validate_class_teacher_binding(class_obj.course_id, class_data.teacher_id)

        # 更新班级信息
        update_data = class_data.model_dump(exclude_unset=True)
        if update_data:
            stmt = (
                update(Class)
                .where(Class.id == class_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()

        return await self.get_class_by_id(class_id)

    async def delete_class(self, class_id: int) -> bool:
        """删除班级（软删除）."""
        class_obj = await self.get_class_by_id(class_id)
        if not class_obj:
            return False

        # 软删除：设为不活跃
        stmt = (
            update(Class)
            .where(Class.id == class_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return True

    async def batch_create_classes(
        self, batch_data: ClassBatchCreate, creator_id: int
    ) -> list[Class]:
        """批量创建班级."""
        # 验证课程存在
        course = await self.db.get(Course, batch_data.course_id)
        if not course:
            raise ValueError("指定的课程不存在")

        # 验证教师分配（如果指定）
        if batch_data.teacher_id:
            await self._validate_class_teacher_binding(batch_data.course_id, batch_data.teacher_id)

        created_classes = []

        for i in range(batch_data.class_count):
            class_name = f"{batch_data.class_prefix}{i + 1:02d}"  # 例如：英语A01, 英语A02
            class_code = f"{course.code or 'C'}{i + 1:03d}" if course.code else None

            class_obj = Class(
                name=class_name,
                code=class_code,
                course_id=batch_data.course_id,
                teacher_id=batch_data.teacher_id,
                max_students=batch_data.max_students_per_class,
                start_date=batch_data.start_date,
                end_date=batch_data.end_date,
                schedule=batch_data.schedule_template,
                status="preparing",
                current_students=0,
                completion_rate=0.0,
                is_active=True,
            )

            self.db.add(class_obj)
            created_classes.append(class_obj)

        await self.db.commit()

        # 刷新对象以获取ID
        for class_obj in created_classes:
            await self.db.refresh(class_obj)

        return created_classes

    async def assign_teacher_to_class(
        self, class_id: int, teacher_id: int, assigner_id: int
    ) -> Class | None:
        """分配教师到班级."""
        class_obj = await self.get_class_by_id(class_id)
        if not class_obj:
            return None

        # 验证绑定规则
        await self._validate_class_teacher_binding(class_obj.course_id, teacher_id)

        # 更新教师分配
        stmt = (
            update(Class)
            .where(Class.id == class_id)
            .values(teacher_id=teacher_id, updated_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get_class_by_id(class_id)

    async def enroll_student(self, enrollment_data: StudentEnrollmentRequest) -> dict[str, Any]:
        """学生选课."""
        # 检查班级容量
        class_obj = await self.get_class_by_id(enrollment_data.class_id)
        if not class_obj:
            raise ValueError("班级不存在")

        if class_obj.current_students >= class_obj.max_students:
            raise ValueError("班级已满员")

        # 检查学生是否已选此课
        existing_enrollment = await self._check_student_enrollment(
            enrollment_data.student_id, enrollment_data.class_id
        )
        if existing_enrollment:
            raise ValueError("学生已选择此班级")

        # 创建选课记录（这里简化处理，实际需要ClassStudent表）
        # 更新班级学生数
        stmt = (
            update(Class)
            .where(Class.id == enrollment_data.class_id)
            .values(
                current_students=Class.current_students + 1,
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return {
            "status": "success",
            "class_id": enrollment_data.class_id,
            "student_id": enrollment_data.student_id,
            "enrolled_at": datetime.utcnow(),
        }

    async def check_class_conflicts(
        self, conflict_check: ClassConflictCheck
    ) -> ConflictCheckResult:
        """检查班级冲突."""
        conflicts: list[dict[str, Any]] = []
        suggestions: list[str] = []

        # 获取教师现有课程安排
        if conflict_check.teacher_id:
            teacher_classes = await self._get_teacher_classes(conflict_check.teacher_id)

            # 检查时间冲突
            existing_schedules = [
                {
                    "class_id": tc.id,
                    "weekly_schedule": tc.schedule.get("weekly_schedule", {}),
                }
                for tc in teacher_classes
                if tc.id != conflict_check.class_id  # 排除当前班级
            ]

            time_conflict_result = ConflictDetectionUtils.check_time_conflict(
                existing_schedules,
                {"weekly_schedule": conflict_check.schedule.get("weekly_schedule", {})},
            )

            if time_conflict_result["has_conflict"]:
                conflicts.extend(time_conflict_result["conflicts"])
                suggestions.append("发现时间冲突，建议调整课程时间")

            # 检查工作量
            workload_result = ConflictDetectionUtils.check_teacher_workload(
                conflict_check.teacher_id,
                [{"student_count": tc.current_students} for tc in teacher_classes],
                {"student_count": 50},  # 假设新班级50人
            )

            if workload_result["is_overloaded"]:
                conflicts.append(
                    {
                        "type": "workload_conflict",
                        "message": "教师工作量过载",
                        "workload_metrics": workload_result["workload_metrics"],
                    }
                )
                suggestions.extend(workload_result["recommendations"])

        # 检查课程绑定规则
        if conflict_check.class_id:
            # 更新现有班级的规则检查
            binding_result = ConflictDetectionUtils.check_binding_rules(
                "class_teacher",
                {"course_id": conflict_check.course_id},
                {"teacher_id": conflict_check.teacher_id},
            )
        else:
            # 新建班级的规则检查
            binding_result = ConflictDetectionUtils.check_binding_rules(
                "class_teacher",
                {"course_id": conflict_check.course_id},
                {"teacher_id": conflict_check.teacher_id},
            )

        if not binding_result["is_compliant"]:
            conflicts.extend(
                [
                    {
                        "type": "binding_rule_violation",
                        "message": violation["message"],
                        "rule": violation["rule"],
                    }
                    for violation in binding_result["violations"]
                ]
            )

        # 确定冲突类型
        conflict_type = None
        if conflicts:
            if any(c["type"] == "time_conflict" for c in conflicts):
                conflict_type = "time_conflict"
            elif any(c["type"] == "workload_conflict" for c in conflicts):
                conflict_type = "workload_conflict"
            elif any(c["type"] == "binding_rule_violation" for c in conflicts):
                conflict_type = "rule_violation"
            else:
                conflict_type = "general_conflict"

        return ConflictCheckResult(
            has_conflict=len(conflicts) > 0,
            conflict_type=conflict_type,
            conflict_details=conflicts,
            suggestions=suggestions,
        )

    async def get_class_statistics(self, class_id: int) -> dict[str, Any] | None:
        """获取班级统计信息."""
        class_obj = await self.get_class_by_id(class_id)
        if not class_obj:
            return None

        # 计算统计信息（这里简化处理）
        statistics = {
            "class_id": class_id,
            "total_students": class_obj.current_students,
            "active_students": class_obj.current_students,  # 简化
            "average_attendance": 0.85,  # 模拟数据
            "average_score": 75.5,  # 模拟数据
            "completion_rate": class_obj.completion_rate,
            "progress_distribution": {
                "not_started": 2,
                "in_progress": 25,
                "completed": 20,
                "excellent": 3,
            },
            "performance_metrics": {
                "vocabulary_mastery": 0.72,
                "grammar_accuracy": 0.68,
                "speaking_fluency": 0.65,
                "listening_comprehension": 0.70,
            },
        }

        return statistics

    async def _validate_class_teacher_binding(self, course_id: int, teacher_id: int) -> None:
        """验证班级-教师绑定规则."""
        # 检查教师是否已分配此课程的其他班级（如果需要严格1对1）
        existing_assignments = await self._get_teacher_course_assignments(teacher_id, course_id)

        # 这里可以配置规则的严格程度
        max_classes_per_course = 3  # 允许一个教师教同一课程的多个班级

        if len(existing_assignments) >= max_classes_per_course:
            raise ValueError(
                f"教师已分配{len(existing_assignments)}个此课程的班级，"
                f"超出限制（{max_classes_per_course}）"
            )

    async def _get_teacher_classes(self, teacher_id: int) -> list[Class]:
        """获取教师的所有班级."""
        stmt = (
            select(Class)
            .where(and_(Class.teacher_id == teacher_id, Class.is_active))
            .options(selectinload(Class.course))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_teacher_course_assignments(self, teacher_id: int, course_id: int) -> list[Class]:
        """获取教师在特定课程的班级分配."""
        stmt = select(Class).where(
            and_(
                Class.teacher_id == teacher_id,
                Class.course_id == course_id,
                Class.is_active == True,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _check_student_enrollment(self, student_id: int, class_id: int) -> bool:
        """检查学生是否已选择指定班级."""
        # 这里需要查询ClassStudent表，简化处理返回False
        # 实际实现中需要查询class_students表
        return False


class ClassResourceService:
    """班级资源管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化资源服务."""
        self.db = db

    async def allocate_resources(
        self, class_id: int, resource_allocation: dict[str, Any]
    ) -> dict[str, Any]:
        """分配班级资源."""
        class_obj = await self.db.get(Class, class_id)
        if not class_obj:
            raise ValueError("班级不存在")

        # 验证资源配置
        validated_allocation = self._validate_resource_allocation(resource_allocation)

        # 更新资源分配
        stmt = (
            update(Class)
            .where(Class.id == class_id)
            .values(resource_allocation=validated_allocation, updated_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return {
            "class_id": class_id,
            "resource_allocation": validated_allocation,
            "allocated_at": datetime.utcnow(),
            "status": "success",
        }

    async def update_resource_allocation(
        self, class_id: int, resource_updates: dict[str, Any]
    ) -> dict[str, Any]:
        """更新资源分配."""
        class_obj = await self.db.get(Class, class_id)
        if not class_obj:
            raise ValueError("班级不存在")

        # 合并现有资源配置和更新
        current_allocation = class_obj.resource_allocation or {}
        updated_allocation = {**current_allocation, **resource_updates}

        # 验证更新后的配置
        validated_allocation = self._validate_resource_allocation(updated_allocation)

        # 更新数据库
        stmt = (
            update(Class)
            .where(Class.id == class_id)
            .values(
                resource_allocation=validated_allocation,
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return {
            "class_id": class_id,
            "previous_allocation": current_allocation,
            "updated_allocation": validated_allocation,
            "updated_at": datetime.utcnow(),
        }

    def _validate_resource_allocation(self, allocation: dict[str, Any]) -> dict[str, Any]:
        """验证资源分配配置."""
        validated = {}

        # 验证教室分配
        if "classroom" in allocation:
            classroom_config = allocation["classroom"]
            validated["classroom"] = {
                "room_id": classroom_config.get("room_id"),
                "capacity": classroom_config.get("capacity", 50),
                "equipment": classroom_config.get("equipment", []),
                "availability": classroom_config.get("availability", {}),
            }

        # 验证教学设备
        if "equipment" in allocation:
            equipment_list = allocation["equipment"]
            validated["equipment"] = [
                {
                    "type": item.get("type"),
                    "quantity": max(0, item.get("quantity", 1)),
                    "specifications": item.get("specifications", {}),
                }
                for item in equipment_list
                if item.get("type")
            ]

        # 验证教学资料
        if "materials" in allocation:
            materials_config = allocation["materials"]
            validated["materials"] = {
                "textbooks": materials_config.get("textbooks", []),
                "digital_resources": materials_config.get("digital_resources", []),
                "supplementary": materials_config.get("supplementary", []),
            }

        # 验证在线资源
        if "online_resources" in allocation:
            online_config = allocation["online_resources"]
            validated["online_resources"] = {
                "learning_platform": online_config.get("learning_platform"),
                "video_resources": online_config.get("video_resources", []),
                "interactive_tools": online_config.get("interactive_tools", []),
                "bandwidth_requirement": max(1, online_config.get("bandwidth_requirement", 10)),
            }

        return validated
