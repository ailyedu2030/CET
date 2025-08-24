"""基础信息管理服务 - 需求2：基础信息管理."""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.models.enums import UserType
from app.users.models import (
    Building,
    Campus,
    Classroom,
    ClassroomSchedule,
    Equipment,
    EquipmentMaintenanceRecord,
    StudentProfile,
    TeacherProfile,
    User,
)

logger = logging.getLogger(__name__)

# 导入新的模型


class BasicInfoService:
    """基础信息管理服务 - 实现需求2的所有验收标准."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ===== 学生信息管理 =====

    async def get_students(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        learning_status: str | None = None,
    ) -> dict[str, Any]:
        """获取学生列表 - 需求2验收标准1."""
        offset = (page - 1) * size

        # 构建查询
        query = (
            select(User)
            .options(selectinload(User.student_profile))
            .where(User.user_type == UserType.STUDENT)
        )

        # 搜索条件
        if search:
            query = query.where(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    StudentProfile.real_name.ilike(f"%{search}%"),
                )
            )

        # 学习状态过滤
        if learning_status:
            query = query.join(StudentProfile).where(
                StudentProfile.learning_status == learning_status
            )

        # 分页
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        students = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": students,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def get_student_detail(self, student_id: int) -> User | None:
        """获取学生详细信息."""
        query = (
            select(User)
            .options(selectinload(User.student_profile))
            .where(and_(User.id == student_id, User.user_type == UserType.STUDENT))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_student_info(
        self, student_id: int, student_data: dict[str, Any]
    ) -> User | None:
        """更新学生信息 - 需求2验收标准1."""
        student = await self.get_student_detail(student_id)
        if not student or not student.student_profile:
            return None

        # 更新学生档案信息
        profile = student.student_profile
        for key, value in student_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(student)

        logger.info(f"Updated student info for user {student_id}")
        return student

    async def update_student_learning_status(
        self, student_id: int, status: str, notes: str | None = None
    ) -> bool:
        """更新学生学习状态 - 需求2验收标准1."""
        student = await self.get_student_detail(student_id)
        if not student or not student.student_profile:
            return False

        profile = student.student_profile
        profile.learning_status = status
        if notes:
            profile.notes = notes

        # 根据状态设置相关日期
        if status == "graduated":
            profile.graduation_date = datetime.now()
        elif status == "active" and not profile.enrollment_date:
            profile.enrollment_date = datetime.now()

        profile.updated_at = datetime.now()
        await self.db.commit()

        logger.info(f"Updated learning status for student {student_id} to {status}")
        return True

    # ===== 教师信息管理 =====

    async def get_teachers(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        teaching_status: str | None = None,
    ) -> dict[str, Any]:
        """获取教师列表 - 需求2验收标准2."""
        offset = (page - 1) * size

        # 构建查询
        query = (
            select(User)
            .options(selectinload(User.teacher_profile))
            .where(User.user_type == UserType.TEACHER)
        )

        # 搜索条件
        if search:
            query = query.where(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    TeacherProfile.real_name.ilike(f"%{search}%"),
                )
            )

        # 教学状态过滤
        if teaching_status:
            query = query.join(TeacherProfile).where(
                TeacherProfile.teaching_status == teaching_status
            )

        # 分页
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        teachers = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": teachers,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def get_teacher_detail(self, teacher_id: int) -> User | None:
        """获取教师详细信息."""
        query = (
            select(User)
            .options(selectinload(User.teacher_profile))
            .where(and_(User.id == teacher_id, User.user_type == UserType.TEACHER))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_teacher_info(
        self, teacher_id: int, teacher_data: dict[str, Any]
    ) -> User | None:
        """更新教师信息 - 需求2验收标准2."""
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher or not teacher.teacher_profile:
            return None

        # 更新教师档案信息
        profile = teacher.teacher_profile
        for key, value in teacher_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(teacher)

        logger.info(f"Updated teacher info for user {teacher_id}")
        return teacher

    async def update_teacher_salary(
        self, teacher_id: int, hourly_rate: float, monthly_salary: float
    ) -> bool:
        """更新教师薪酬 - 需求2验收标准2."""
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher or not teacher.teacher_profile:
            return False

        profile = teacher.teacher_profile
        profile.hourly_rate = hourly_rate
        profile.monthly_salary = monthly_salary
        profile.updated_at = datetime.now()

        await self.db.commit()

        logger.info(f"Updated salary for teacher {teacher_id}")
        return True

    async def process_teacher_qualification_review(
        self, teacher_id: int, status: str, notes: str | None = None
    ) -> bool:
        """处理教师资质审核 - 需求2验收标准2."""
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher or not teacher.teacher_profile:
            return False

        profile = teacher.teacher_profile
        profile.qualification_status = status
        profile.last_review_date = datetime.now()

        # 设置下次审核日期（每年一次）
        if status == "approved":
            profile.next_review_date = datetime.now() + timedelta(days=365)

        if notes:
            profile.qualification_notes = notes

        profile.updated_at = datetime.now()
        await self.db.commit()

        logger.info(f"Updated qualification status for teacher {teacher_id} to {status}")
        return True

    # ===== 教室信息管理 =====

    async def get_campuses(self) -> list[Campus]:
        """获取校区列表."""
        query = select(Campus).where(Campus.is_active)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_buildings(self, campus_id: int | None = None) -> list[Building]:
        """获取楼栋列表."""
        query = select(Building).where(Building.is_active)
        if campus_id:
            query = query.where(Building.campus_id == campus_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_classrooms(
        self,
        building_id: int | None = None,
        is_available: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """获取教室列表 - 需求2验收标准3."""
        offset = (page - 1) * size

        query = select(Classroom).options(selectinload(Classroom.building))

        if building_id:
            query = query.where(Classroom.building_id == building_id)

        if is_available is not None:
            query = query.where(Classroom.is_available == is_available)

        # 分页
        total_query = query
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        classrooms = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": classrooms,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def check_classroom_conflict(
        self,
        classroom_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_schedule_id: int | None = None,
    ) -> bool:
        """检查教室排期冲突 - 需求2验收标准5."""
        query = select(ClassroomSchedule).where(
            and_(
                ClassroomSchedule.classroom_id == classroom_id,
                ClassroomSchedule.status == "scheduled",
                or_(
                    and_(
                        ClassroomSchedule.start_time <= start_time,
                        ClassroomSchedule.end_time > start_time,
                    ),
                    and_(
                        ClassroomSchedule.start_time < end_time,
                        ClassroomSchedule.end_time >= end_time,
                    ),
                    and_(
                        ClassroomSchedule.start_time >= start_time,
                        ClassroomSchedule.end_time <= end_time,
                    ),
                ),
            )
        )

        if exclude_schedule_id:
            query = query.where(ClassroomSchedule.id != exclude_schedule_id)

        result = await self.db.execute(query)
        conflicts = result.scalars().all()

        return len(conflicts) > 0

    # ===== 设备管理 - 功能2 =====

    async def get_classroom_equipment(
        self, classroom_id: int, page: int = 1, size: int = 20
    ) -> dict[str, Any]:
        """获取教室设备列表 - 功能2：设备管理."""
        offset = (page - 1) * size

        query = (
            select(Equipment)
            .where(Equipment.classroom_id == classroom_id)
            .order_by(Equipment.equipment_type, Equipment.name)
        )

        # 分页
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        equipment_list = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": equipment_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def get_equipment_detail(self, equipment_id: int) -> Equipment | None:
        """获取设备详细信息."""
        query = (
            select(Equipment)
            .options(
                selectinload(Equipment.classroom),
                selectinload(Equipment.maintenance_records),
            )
            .where(Equipment.id == equipment_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_equipment(
        self, classroom_id: int, equipment_data: dict[str, Any]
    ) -> Equipment:
        """创建设备 - 功能2：设备管理."""
        equipment = Equipment(
            classroom_id=classroom_id,
            **equipment_data,
        )

        self.db.add(equipment)
        await self.db.commit()
        await self.db.refresh(equipment)

        # 更新教室的设备标记
        await self._update_classroom_equipment_flags(classroom_id)

        logger.info(f"Created equipment {equipment.id} for classroom {classroom_id}")
        return equipment

    async def update_equipment(
        self, equipment_id: int, equipment_data: dict[str, Any]
    ) -> Equipment | None:
        """更新设备信息 - 功能2：设备管理."""
        equipment = await self.get_equipment_detail(equipment_id)
        if not equipment:
            return None

        for key, value in equipment_data.items():
            if hasattr(equipment, key):
                setattr(equipment, key, value)

        equipment.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(equipment)

        # 更新教室的设备标记
        await self._update_classroom_equipment_flags(equipment.classroom_id)

        logger.info(f"Updated equipment {equipment_id}")
        return equipment

    async def delete_equipment(self, equipment_id: int) -> bool:
        """删除设备 - 功能2：设备管理."""
        equipment = await self.get_equipment_detail(equipment_id)
        if not equipment:
            return False

        classroom_id = equipment.classroom_id
        await self.db.delete(equipment)
        await self.db.commit()

        # 更新教室的设备标记
        await self._update_classroom_equipment_flags(classroom_id)

        logger.info(f"Deleted equipment {equipment_id}")
        return True

    async def _update_classroom_equipment_flags(self, classroom_id: int) -> None:
        """更新教室的设备标记字段."""
        # 查询教室的所有设备
        query = select(Equipment).where(
            and_(
                Equipment.classroom_id == classroom_id,
                Equipment.status.in_(["normal", "maintenance"]),
            )
        )
        result = await self.db.execute(query)
        equipment_list = result.scalars().all()

        # 统计设备类型
        equipment_types = {eq.equipment_type for eq in equipment_list}

        # 更新教室的设备标记
        classroom_query = select(Classroom).where(Classroom.id == classroom_id)
        classroom_result = await self.db.execute(classroom_query)
        classroom = classroom_result.scalar_one_or_none()

        if classroom:
            classroom.has_projector = "projector" in equipment_types
            classroom.has_computer = "computer" in equipment_types
            classroom.has_audio = "audio" in equipment_types
            classroom.has_whiteboard = "whiteboard" in equipment_types

            # 更新设备列表JSON字段
            equipment_dict: dict[str, Any] = {}
            for eq in equipment_list:
                if eq.equipment_type not in equipment_dict:
                    equipment_dict[eq.equipment_type] = {
                        "count": 0,
                        "normal": 0,
                        "maintenance": 0,
                        "items": [],
                    }

                # 类型安全的更新
                eq_type_data = equipment_dict[eq.equipment_type]
                eq_type_data["count"] = eq_type_data["count"] + 1

                if eq.status in eq_type_data:
                    eq_type_data[eq.status] = eq_type_data[eq.status] + 1

                eq_type_data["items"].append(
                    {
                        "id": eq.id,
                        "name": eq.name,
                        "brand": eq.brand,
                        "model": eq.model,
                        "status": eq.status,
                    }
                )

            classroom.equipment_list = equipment_dict
            await self.db.commit()

    # ===== 设备维护记录管理 - 功能2 =====

    async def get_equipment_maintenance_records(
        self, equipment_id: int, page: int = 1, size: int = 20
    ) -> dict[str, Any]:
        """获取设备维护记录 - 功能2：维护记录管理."""
        offset = (page - 1) * size

        query = (
            select(EquipmentMaintenanceRecord)
            .where(EquipmentMaintenanceRecord.equipment_id == equipment_id)
            .order_by(EquipmentMaintenanceRecord.maintenance_date.desc())
        )

        # 分页
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": records,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def create_maintenance_record(
        self, equipment_id: int, record_data: dict[str, Any]
    ) -> EquipmentMaintenanceRecord:
        """创建维护记录 - 功能2：维护记录管理."""
        record = EquipmentMaintenanceRecord(
            equipment_id=equipment_id,
            **record_data,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        # 更新设备的维护日期
        equipment = await self.get_equipment_detail(equipment_id)
        if equipment:
            equipment.last_maintenance_date = record.maintenance_date
            if record.next_maintenance_date:
                equipment.next_maintenance_date = record.next_maintenance_date
            await self.db.commit()

        logger.info(f"Created maintenance record {record.id} for equipment {equipment_id}")
        return record

    async def get_equipment_statistics(self, classroom_id: int | None = None) -> dict[str, Any]:
        """获取设备使用统计 - 功能2：使用统计."""
        query = select(Equipment)
        if classroom_id:
            query = query.where(Equipment.classroom_id == classroom_id)

        result = await self.db.execute(query)
        equipment_list = result.scalars().all()

        # 统计数据
        total_equipment = len(equipment_list)
        status_stats: dict[str, int] = {}
        type_stats: dict[str, int] = {}
        usage_stats = {
            "total_usage_hours": 0,
            "average_usage_hours": 0,
            "total_failures": 0,
        }

        for eq in equipment_list:
            # 状态统计
            status_stats[eq.status] = status_stats.get(eq.status, 0) + 1

            # 类型统计
            type_stats[eq.equipment_type] = type_stats.get(eq.equipment_type, 0) + 1

            # 使用统计
            usage_stats["total_usage_hours"] += eq.total_usage_hours
            usage_stats["total_failures"] += eq.failure_count

        if total_equipment > 0:
            usage_stats["average_usage_hours"] = usage_stats["total_usage_hours"] / total_equipment

        return {
            "total_equipment": total_equipment,
            "status_statistics": status_stats,
            "type_statistics": type_stats,
            "usage_statistics": usage_stats,
        }

    # ===== 考勤管理系统 - 需求2：考勤管理 =====

    async def get_student_attendance(
        self,
        student_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """获取学生考勤记录 - 需求2：考勤管理."""
        from app.users.models.user_models import AttendanceRecord

        offset = (page - 1) * size

        # 构建查询
        query = select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)

        # 日期范围过滤
        if start_date:
            query = query.where(AttendanceRecord.attendance_date >= start_date)
        if end_date:
            query = query.where(AttendanceRecord.attendance_date <= end_date)

        # 排序和分页
        query = query.order_by(AttendanceRecord.attendance_date.desc())
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        # 统计数据
        stats_query = select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
        if start_date:
            stats_query = stats_query.where(AttendanceRecord.attendance_date >= start_date)
        if end_date:
            stats_query = stats_query.where(AttendanceRecord.attendance_date <= end_date)

        stats_result = await self.db.execute(stats_query)
        all_records = stats_result.scalars().all()

        attendance_stats = {
            "total_days": len(all_records),
            "present_days": len([r for r in all_records if r.attendance_type == "present"]),
            "absent_days": len([r for r in all_records if r.attendance_type == "absent"]),
            "late_days": len([r for r in all_records if r.attendance_type == "late"]),
            "leave_days": len([r for r in all_records if r.attendance_type == "leave"]),
        }

        if attendance_stats["total_days"] > 0:
            attendance_stats["attendance_rate"] = (
                attendance_stats["present_days"] / attendance_stats["total_days"]
            ) * 100

        return {
            "items": [
                {
                    "id": record.id,
                    "attendance_date": record.attendance_date,
                    "attendance_type": record.attendance_type,
                    "check_in_time": record.check_in_time,
                    "check_out_time": record.check_out_time,
                    "leave_type": record.leave_type,
                    "leave_reason": record.leave_reason,
                    "leave_approved": record.leave_approved,
                    "notes": record.notes,
                }
                for record in records
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "statistics": attendance_stats,
        }

    async def create_attendance_record(
        self,
        student_id: int,
        attendance_data: dict[str, Any],
        recorded_by: int | None = None,
    ) -> dict[str, Any]:
        """创建考勤记录 - 需求2：考勤管理."""
        from app.users.models.user_models import AttendanceRecord

        # 检查学生是否存在
        student = await self.get_student_detail(student_id)
        if not student:
            raise ValueError(f"学生不存在: {student_id}")

        # 检查当天是否已有记录
        existing_record = await self.db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.attendance_date == attendance_data["attendance_date"],
                )
            )
        )
        if existing_record.scalar_one_or_none():
            raise ValueError("该学生当天已有考勤记录")

        # 创建考勤记录
        record = AttendanceRecord(
            student_id=student_id,
            recorded_by=recorded_by,
            **attendance_data,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        logger.info(f"Created attendance record {record.id} for student {student_id}")
        return {
            "id": record.id,
            "student_id": record.student_id,
            "attendance_date": record.attendance_date,
            "attendance_type": record.attendance_type,
            "check_in_time": record.check_in_time,
            "check_out_time": record.check_out_time,
            "leave_type": record.leave_type,
            "leave_reason": record.leave_reason,
            "leave_approved": record.leave_approved,
            "notes": record.notes,
        }

    async def update_attendance_record(
        self, record_id: int, attendance_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """更新考勤记录 - 需求2：考勤管理."""
        from app.users.models.user_models import AttendanceRecord

        record = await self.db.get(AttendanceRecord, record_id)
        if not record:
            return None

        # 更新字段
        for key, value in attendance_data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        record.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(record)

        logger.info(f"Updated attendance record {record_id}")
        return {
            "id": record.id,
            "student_id": record.student_id,
            "attendance_date": record.attendance_date,
            "attendance_type": record.attendance_type,
            "check_in_time": record.check_in_time,
            "check_out_time": record.check_out_time,
            "leave_type": record.leave_type,
            "leave_reason": record.leave_reason,
            "leave_approved": record.leave_approved,
            "notes": record.notes,
        }

    async def approve_leave_request(
        self, record_id: int, approved: bool, approved_by: int, notes: str | None = None
    ) -> bool:
        """审批请假申请 - 需求2：考勤管理."""
        from app.users.models.user_models import AttendanceRecord

        record = await self.db.get(AttendanceRecord, record_id)
        if not record or record.attendance_type != "leave":
            return False

        record.leave_approved = approved
        record.approved_by = approved_by
        if notes:
            record.notes = f"{record.notes or ''}\n审批备注: {notes}"
        record.updated_at = datetime.now()

        await self.db.commit()
        logger.info(
            f"Leave request {record_id} {'approved' if approved else 'rejected'} by {approved_by}"
        )
        return True

    # ===== 学籍变动管理 - 需求2：学籍变动管理 =====

    async def create_enrollment_change(
        self,
        student_id: int,
        change_data: dict[str, Any],
        approved_by: int | None = None,
    ) -> dict[str, Any]:
        """创建学籍变动记录 - 需求2：学籍变动管理."""
        from app.users.models.user_models import StudentEnrollmentChange

        # 检查学生是否存在
        student = await self.get_student_detail(student_id)
        if not student:
            raise ValueError(f"学生不存在: {student_id}")

        # 获取当前状态
        current_status = (
            student.student_profile.learning_status if student.student_profile else "unknown"
        )

        # 创建学籍变动记录
        change_record = StudentEnrollmentChange(
            student_id=student_id,
            previous_status=current_status,
            approved_by=approved_by,
            **change_data,
        )

        self.db.add(change_record)
        await self.db.commit()
        await self.db.refresh(change_record)

        # 如果变动已生效，更新学生状态
        if change_record.effective_date <= date.today() and student.student_profile:
            student.student_profile.learning_status = change_record.new_status
            student.student_profile.updated_at = datetime.now()
            await self.db.commit()

        logger.info(f"Created enrollment change {change_record.id} for student {student_id}")
        return {
            "id": change_record.id,
            "student_id": change_record.student_id,
            "change_type": change_record.change_type,
            "change_date": change_record.change_date,
            "effective_date": change_record.effective_date,
            "previous_status": change_record.previous_status,
            "new_status": change_record.new_status,
            "reason": change_record.reason,
            "approved_by": change_record.approved_by,
            "approved_at": change_record.approved_at,
        }

    async def get_enrollment_changes(
        self, student_id: int | None = None, page: int = 1, size: int = 20
    ) -> dict[str, Any]:
        """获取学籍变动记录 - 需求2：学籍变动管理."""
        from app.users.models.user_models import StudentEnrollmentChange

        offset = (page - 1) * size

        # 构建查询
        query = select(StudentEnrollmentChange)
        if student_id:
            query = query.where(StudentEnrollmentChange.student_id == student_id)

        # 排序和分页
        query = query.order_by(StudentEnrollmentChange.change_date.desc())
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": [
                {
                    "id": record.id,
                    "student_id": record.student_id,
                    "change_type": record.change_type,
                    "change_date": record.change_date,
                    "effective_date": record.effective_date,
                    "previous_status": record.previous_status,
                    "new_status": record.new_status,
                    "reason": record.reason,
                    "approved_by": record.approved_by,
                    "approved_at": record.approved_at,
                    "approval_notes": record.approval_notes,
                }
                for record in records
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    # ===== 收费管理系统 - 需求2：收费管理 =====

    async def create_billing_record(
        self,
        student_id: int,
        billing_data: dict[str, Any],
        created_by: int | None = None,
    ) -> dict[str, Any]:
        """创建收费记录 - 需求2：收费管理."""
        from app.users.models.user_models import BillingRecord

        # 检查学生是否存在
        student = await self.get_student_detail(student_id)
        if not student:
            raise ValueError(f"学生不存在: {student_id}")

        # 创建收费记录
        billing_record = BillingRecord(
            student_id=student_id,
            created_by=created_by,
            **billing_data,
        )

        self.db.add(billing_record)
        await self.db.commit()
        await self.db.refresh(billing_record)

        logger.info(f"Created billing record {billing_record.id} for student {student_id}")
        return {
            "id": billing_record.id,
            "student_id": billing_record.student_id,
            "billing_type": billing_record.billing_type,
            "amount": billing_record.amount,
            "currency": billing_record.currency,
            "billing_date": billing_record.billing_date,
            "due_date": billing_record.due_date,
            "payment_status": billing_record.payment_status,
            "payment_method": billing_record.payment_method,
            "payment_date": billing_record.payment_date,
            "transaction_id": billing_record.transaction_id,
            "description": billing_record.description,
            "notes": billing_record.notes,
        }

    async def get_billing_records(
        self,
        student_id: int | None = None,
        payment_status: str | None = None,
        billing_type: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """获取收费记录 - 需求2：收费管理."""
        from app.users.models.user_models import BillingRecord

        offset = (page - 1) * size

        # 构建查询
        query = select(BillingRecord)
        if student_id:
            query = query.where(BillingRecord.student_id == student_id)
        if payment_status:
            query = query.where(BillingRecord.payment_status == payment_status)
        if billing_type:
            query = query.where(BillingRecord.billing_type == billing_type)

        # 排序和分页
        query = query.order_by(BillingRecord.billing_date.desc())
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        # 统计数据
        stats_result = await self.db.execute(total_query)
        all_records = stats_result.scalars().all()

        billing_stats = {
            "total_amount": sum(r.amount for r in all_records),
            "paid_amount": sum(r.amount for r in all_records if r.payment_status == "paid"),
            "pending_amount": sum(r.amount for r in all_records if r.payment_status == "pending"),
            "overdue_amount": sum(r.amount for r in all_records if r.payment_status == "overdue"),
        }

        return {
            "items": [
                {
                    "id": record.id,
                    "student_id": record.student_id,
                    "billing_type": record.billing_type,
                    "amount": record.amount,
                    "currency": record.currency,
                    "billing_date": record.billing_date,
                    "due_date": record.due_date,
                    "payment_status": record.payment_status,
                    "payment_method": record.payment_method,
                    "payment_date": record.payment_date,
                    "transaction_id": record.transaction_id,
                    "description": record.description,
                    "notes": record.notes,
                }
                for record in records
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "statistics": billing_stats,
        }

    async def process_payment(
        self,
        billing_record_id: int,
        payment_data: dict[str, Any],
        processed_by: int | None = None,
    ) -> dict[str, Any]:
        """处理支付 - 需求2：收费管理."""
        from app.users.models.user_models import BillingRecord

        billing_record = await self.db.get(BillingRecord, billing_record_id)
        if not billing_record:
            raise ValueError(f"收费记录不存在: {billing_record_id}")

        if billing_record.payment_status == "paid":
            raise ValueError("该记录已支付")

        # 更新支付信息
        billing_record.payment_status = "paid"
        billing_record.payment_method = payment_data.get("payment_method")
        billing_record.payment_date = datetime.now()
        billing_record.transaction_id = payment_data.get("transaction_id")
        billing_record.processed_by = processed_by
        billing_record.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(billing_record)

        logger.info(f"Payment processed for billing record {billing_record_id}")
        return {
            "id": billing_record.id,
            "student_id": billing_record.student_id,
            "amount": billing_record.amount,
            "payment_status": billing_record.payment_status,
            "payment_method": billing_record.payment_method,
            "payment_date": billing_record.payment_date,
            "transaction_id": billing_record.transaction_id,
        }

    async def generate_invoice(
        self,
        billing_record_id: int,
        invoice_data: dict[str, Any],
        issued_by: int | None = None,
    ) -> dict[str, Any]:
        """生成发票 - 需求2：发票生成."""
        from app.users.models.user_models import BillingRecord, Invoice

        billing_record = await self.db.get(BillingRecord, billing_record_id)
        if not billing_record:
            raise ValueError(f"收费记录不存在: {billing_record_id}")

        if billing_record.payment_status != "paid":
            raise ValueError("只能为已支付的记录开具发票")

        # 检查是否已有发票
        existing_invoice = await self.db.execute(
            select(Invoice).where(Invoice.billing_record_id == billing_record_id)
        )
        if existing_invoice.scalar_one_or_none():
            raise ValueError("该记录已开具发票")

        # 生成发票号码
        import uuid

        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        # 创建发票
        invoice = Invoice(
            billing_record_id=billing_record_id,
            invoice_number=invoice_number,
            invoice_date=date.today(),
            total_amount=billing_record.amount,
            issued_by=issued_by,
            issued_at=datetime.now(),
            status="issued",
            **invoice_data,
        )

        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)

        logger.info(
            f"Generated invoice {invoice.invoice_number} for billing record {billing_record_id}"
        )
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "billing_record_id": invoice.billing_record_id,
            "invoice_date": invoice.invoice_date,
            "total_amount": invoice.total_amount,
            "tax_amount": invoice.tax_amount,
            "tax_rate": invoice.tax_rate,
            "status": invoice.status,
            "company_name": invoice.company_name,
            "tax_number": invoice.tax_number,
        }

    # ===== 教学状态跟踪系统 - 需求2：教学状态跟踪 =====

    async def get_teacher_teaching_records(
        self,
        teacher_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """获取教师教学记录 - 需求2：教学状态跟踪."""
        from app.users.models.user_models import TeachingRecord

        offset = (page - 1) * size

        # 构建查询
        query = select(TeachingRecord).where(TeachingRecord.teacher_id == teacher_id)

        # 日期范围过滤
        if start_date:
            query = query.where(TeachingRecord.teaching_start_time >= start_date)
        if end_date:
            query = query.where(TeachingRecord.teaching_start_time <= end_date)

        # 排序和分页
        query = query.order_by(TeachingRecord.teaching_start_time.desc())
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": [
                {
                    "id": record.id,
                    "teacher_id": record.teacher_id,
                    "course_name": record.course_name,
                    "course_type": record.course_type,
                    "teaching_duration": record.teaching_duration,
                    "student_count": record.student_count,
                    "teaching_start_time": record.teaching_start_time,
                    "teaching_end_time": record.teaching_end_time,
                    "teaching_status": record.teaching_status,
                    "teaching_rating": record.teaching_rating,
                    "student_feedback": record.student_feedback,
                    "effectiveness_metrics": record.effectiveness_metrics,
                    "notes": record.notes,
                }
                for record in records
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def create_teaching_record(
        self,
        teacher_id: int,
        teaching_data: dict[str, Any],
        created_by: int | None = None,
    ) -> dict[str, Any]:
        """创建教学记录 - 需求2：教学状态跟踪."""
        from app.users.models.user_models import TeachingRecord

        # 检查教师是否存在
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher:
            raise ValueError(f"教师不存在: {teacher_id}")

        # 创建教学记录
        record = TeachingRecord(
            teacher_id=teacher_id,
            created_by=created_by,
            **teaching_data,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        logger.info(f"Created teaching record {record.id} for teacher {teacher_id}")
        return {
            "id": record.id,
            "teacher_id": record.teacher_id,
            "course_name": record.course_name,
            "course_type": record.course_type,
            "teaching_duration": record.teaching_duration,
            "student_count": record.student_count,
            "teaching_start_time": record.teaching_start_time,
            "teaching_end_time": record.teaching_end_time,
            "teaching_status": record.teaching_status,
            "teaching_rating": record.teaching_rating,
            "student_feedback": record.student_feedback,
            "effectiveness_metrics": record.effectiveness_metrics,
            "notes": record.notes,
        }

    async def update_teaching_record(
        self, record_id: int, teaching_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """更新教学记录 - 需求2：教学状态跟踪."""
        from app.users.models.user_models import TeachingRecord

        record = await self.db.get(TeachingRecord, record_id)
        if not record:
            return None

        # 更新字段
        for key, value in teaching_data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        record.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(record)

        logger.info(f"Updated teaching record {record_id}")
        return {
            "id": record.id,
            "teacher_id": record.teacher_id,
            "course_name": record.course_name,
            "course_type": record.course_type,
            "teaching_duration": record.teaching_duration,
            "student_count": record.student_count,
            "teaching_start_time": record.teaching_start_time,
            "teaching_end_time": record.teaching_end_time,
            "teaching_status": record.teaching_status,
            "teaching_rating": record.teaching_rating,
            "student_feedback": record.student_feedback,
            "effectiveness_metrics": record.effectiveness_metrics,
            "notes": record.notes,
        }

    async def get_teaching_statistics(
        self, teacher_id: int, period: str = "month"
    ) -> dict[str, Any]:
        """获取教学统计数据 - 需求2：教学状态跟踪."""
        from app.users.models.user_models import TeachingRecord

        # 计算时间范围
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "quarter":
            start_date = now - timedelta(days=90)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # 默认一个月

        # 查询教学记录
        query = select(TeachingRecord).where(
            and_(
                TeachingRecord.teacher_id == teacher_id,
                TeachingRecord.teaching_start_time >= start_date,
            )
        )
        result = await self.db.execute(query)
        records = result.scalars().all()

        # 计算统计数据
        total_classes = len(records)
        completed_classes = len([r for r in records if r.teaching_status == "completed"])
        cancelled_classes = len([r for r in records if r.teaching_status == "cancelled"])
        total_hours = sum(r.teaching_duration for r in records) / 60  # 转换为小时
        total_students = sum(r.student_count for r in records)

        # 计算平均评分
        rated_records = [r for r in records if r.teaching_rating is not None]
        average_rating = (
            sum(r.teaching_rating for r in rated_records) / len(rated_records)
            if rated_records
            else None
        )

        # 按课程类型统计
        course_type_stats = {}
        for record in records:
            course_type = record.course_type
            if course_type not in course_type_stats:
                course_type_stats[course_type] = {"count": 0, "hours": 0}
            course_type_stats[course_type]["count"] += 1
            course_type_stats[course_type]["hours"] += record.teaching_duration / 60

        return {
            "period": period,
            "total_classes": total_classes,
            "completed_classes": completed_classes,
            "cancelled_classes": cancelled_classes,
            "completion_rate": (completed_classes / total_classes if total_classes > 0 else 0),
            "total_hours": round(total_hours, 2),
            "total_students": total_students,
            "average_rating": round(average_rating, 2) if average_rating else None,
            "course_type_statistics": course_type_stats,
        }

    # ===== 薪酬管理系统 - 需求2：薪酬管理 =====

    async def calculate_teacher_salary(
        self, teacher_id: int, period_start: date, period_end: date
    ) -> dict[str, Any]:
        """计算教师薪酬 - 需求2：薪酬管理."""
        from app.users.models.user_models import TeachingRecord

        # 检查教师是否存在
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher:
            raise ValueError(f"教师不存在: {teacher_id}")

        # 查询指定期间的教学记录
        query = select(TeachingRecord).where(
            and_(
                TeachingRecord.teacher_id == teacher_id,
                TeachingRecord.teaching_start_time >= period_start,
                TeachingRecord.teaching_start_time <= period_end,
                TeachingRecord.teaching_status == "completed",
            )
        )
        result = await self.db.execute(query)
        teaching_records = result.scalars().all()

        # 计算课时数和基础数据
        total_hours = (
            sum(record.teaching_duration for record in teaching_records) / 60
        )  # 转换为小时
        total_classes = len(teaching_records)

        # 从教师档案获取基础薪酬信息（假设存储在teacher_profile中）
        teacher_profile = teacher.teacher_profile
        base_hourly_rate = 100.0  # 默认课时费，实际应从配置或教师档案获取

        if teacher_profile and hasattr(teacher_profile, "hourly_rate"):
            base_hourly_rate = teacher_profile.hourly_rate or base_hourly_rate

        # 计算基础课时费
        base_amount = total_hours * base_hourly_rate

        # 计算奖金（基于教学评分）
        rated_records = [r for r in teaching_records if r.teaching_rating is not None]
        average_rating = (
            sum(r.teaching_rating for r in rated_records) / len(rated_records)
            if rated_records
            else 0
        )

        # 奖金计算：评分4.5以上给予10%奖金，4.0-4.5给予5%奖金
        bonus_rate = 0.0
        if average_rating >= 4.5:
            bonus_rate = 0.1
        elif average_rating >= 4.0:
            bonus_rate = 0.05

        bonus_amount = base_amount * bonus_rate

        # 计算扣除（暂时为0，可根据实际业务需求扩展）
        deduction_amount = 0.0

        # 计算实发金额
        net_amount = base_amount + bonus_amount - deduction_amount

        return {
            "teacher_id": teacher_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_hours": round(total_hours, 2),
            "total_classes": total_classes,
            "hourly_rate": base_hourly_rate,
            "base_amount": round(base_amount, 2),
            "average_rating": round(average_rating, 2) if average_rating > 0 else None,
            "bonus_rate": bonus_rate,
            "bonus_amount": round(bonus_amount, 2),
            "deduction_amount": round(deduction_amount, 2),
            "net_amount": round(net_amount, 2),
        }

    async def create_salary_record(
        self,
        teacher_id: int,
        salary_data: dict[str, Any],
        created_by: int | None = None,
    ) -> dict[str, Any]:
        """创建薪酬记录 - 需求2：薪酬管理."""
        from app.users.models.user_models import SalaryRecord

        # 检查教师是否存在
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher:
            raise ValueError(f"教师不存在: {teacher_id}")

        # 创建薪酬记录
        salary_record = SalaryRecord(
            teacher_id=teacher_id,
            created_by=created_by,
            **salary_data,
        )

        self.db.add(salary_record)
        await self.db.commit()
        await self.db.refresh(salary_record)

        logger.info(f"Created salary record {salary_record.id} for teacher {teacher_id}")
        return {
            "id": salary_record.id,
            "teacher_id": salary_record.teacher_id,
            "salary_type": salary_record.salary_type,
            "calculation_period_start": salary_record.calculation_period_start,
            "calculation_period_end": salary_record.calculation_period_end,
            "base_amount": salary_record.base_amount,
            "teaching_hours": salary_record.teaching_hours,
            "hourly_rate": salary_record.hourly_rate,
            "bonus_amount": salary_record.bonus_amount,
            "deduction_amount": salary_record.deduction_amount,
            "net_amount": salary_record.net_amount,
            "payment_status": salary_record.payment_status,
            "payment_date": salary_record.payment_date,
            "notes": salary_record.notes,
        }

    async def get_salary_records(
        self,
        teacher_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """查询薪酬记录 - 需求2：薪酬管理."""
        from app.users.models.user_models import SalaryRecord

        offset = (page - 1) * size

        # 构建查询
        query = select(SalaryRecord)
        if teacher_id:
            query = query.where(SalaryRecord.teacher_id == teacher_id)
        if status:
            query = query.where(SalaryRecord.payment_status == status)

        # 排序和分页
        query = query.order_by(SalaryRecord.calculation_period_start.desc())
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        # 统计数据
        stats_result = await self.db.execute(total_query)
        all_records = stats_result.scalars().all()

        salary_stats = {
            "total_amount": sum(r.net_amount for r in all_records),
            "paid_amount": sum(r.net_amount for r in all_records if r.payment_status == "paid"),
            "pending_amount": sum(
                r.net_amount for r in all_records if r.payment_status == "pending"
            ),
            "total_records": len(all_records),
        }

        return {
            "items": [
                {
                    "id": record.id,
                    "teacher_id": record.teacher_id,
                    "salary_type": record.salary_type,
                    "calculation_period_start": record.calculation_period_start,
                    "calculation_period_end": record.calculation_period_end,
                    "base_amount": record.base_amount,
                    "teaching_hours": record.teaching_hours,
                    "hourly_rate": record.hourly_rate,
                    "bonus_amount": record.bonus_amount,
                    "deduction_amount": record.deduction_amount,
                    "net_amount": record.net_amount,
                    "payment_status": record.payment_status,
                    "payment_date": record.payment_date,
                    "approved_by": record.approved_by,
                    "approved_at": record.approved_at,
                    "notes": record.notes,
                }
                for record in records
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "statistics": salary_stats,
        }

    async def process_salary_payment(
        self,
        record_id: int,
        payment_data: dict[str, Any],
        processed_by: int | None = None,
    ) -> dict[str, Any]:
        """处理薪酬发放 - 需求2：薪酬管理."""
        from app.users.models.user_models import SalaryRecord

        salary_record = await self.db.get(SalaryRecord, record_id)
        if not salary_record:
            raise ValueError(f"薪酬记录不存在: {record_id}")

        if salary_record.payment_status == "paid":
            raise ValueError("该薪酬记录已发放")

        # 更新发放信息
        salary_record.payment_status = "paid"
        salary_record.payment_date = datetime.now()
        salary_record.approved_by = processed_by
        salary_record.approved_at = datetime.now()

        # 更新备注信息
        if payment_data.get("notes"):
            salary_record.notes = f"{salary_record.notes or ''}\n发放备注: {payment_data['notes']}"

        salary_record.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(salary_record)

        logger.info(f"Salary payment processed for record {record_id}")
        return {
            "id": salary_record.id,
            "teacher_id": salary_record.teacher_id,
            "net_amount": salary_record.net_amount,
            "payment_status": salary_record.payment_status,
            "payment_date": salary_record.payment_date,
            "approved_by": salary_record.approved_by,
            "approved_at": salary_record.approved_at,
        }

    # ===== 资质审核流程 - 需求2：资质审核 =====

    async def create_qualification_review(
        self,
        teacher_id: int,
        review_data: dict[str, Any],
        submitted_by: int | None = None,
    ) -> dict[str, Any]:
        """创建资质审核 - 需求2：资质审核流程."""
        from app.users.models.user_models import QualificationReview

        # 检查教师是否存在
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher:
            raise ValueError(f"教师不存在: {teacher_id}")

        # 创建资质审核记录
        review_record = QualificationReview(
            teacher_id=teacher_id,
            submitted_by=submitted_by,
            **review_data,
        )

        self.db.add(review_record)
        await self.db.commit()
        await self.db.refresh(review_record)

        logger.info(f"Created qualification review {review_record.id} for teacher {teacher_id}")
        return {
            "id": review_record.id,
            "teacher_id": review_record.teacher_id,
            "review_type": review_record.review_type,
            "review_cycle": review_record.review_cycle,
            "submission_date": review_record.submission_date,
            "submitted_materials": review_record.submitted_materials,
            "review_status": review_record.review_status,
            "review_result": review_record.review_result,
            "review_comments": review_record.review_comments,
            "valid_from": review_record.valid_from,
            "valid_until": review_record.valid_until,
        }

    async def get_qualification_reviews(
        self,
        teacher_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """查询资质审核记录 - 需求2：资质审核流程."""
        from app.users.models.user_models import QualificationReview

        offset = (page - 1) * size

        # 构建查询
        query = select(QualificationReview)
        if teacher_id:
            query = query.where(QualificationReview.teacher_id == teacher_id)
        if status:
            query = query.where(QualificationReview.review_status == status)

        # 排序和分页
        query = query.order_by(QualificationReview.submission_date.desc())
        total_query = query
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.db.execute(query)
        records = result.scalars().all()

        total_result = await self.db.execute(total_query)
        total = len(total_result.scalars().all())

        return {
            "items": [
                {
                    "id": record.id,
                    "teacher_id": record.teacher_id,
                    "review_type": record.review_type,
                    "review_cycle": record.review_cycle,
                    "submission_date": record.submission_date,
                    "submitted_materials": record.submitted_materials,
                    "review_status": record.review_status,
                    "review_result": record.review_result,
                    "review_comments": record.review_comments,
                    "valid_from": record.valid_from,
                    "valid_until": record.valid_until,
                    "reviewer_id": record.reviewer_id,
                    "reviewed_at": record.reviewed_at,
                }
                for record in records
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def process_qualification_review(
        self, review_id: int, review_data: dict[str, Any], reviewer_id: int
    ) -> dict[str, Any]:
        """处理资质审核流程 - 需求2：资质审核流程."""
        from app.users.models.user_models import QualificationReview

        review_record = await self.db.get(QualificationReview, review_id)
        if not review_record:
            raise ValueError(f"资质审核记录不存在: {review_id}")

        if review_record.review_status in ["approved", "rejected"]:
            raise ValueError("该审核记录已完成处理")

        # 更新审核信息
        review_record.review_status = review_data.get("review_status", "under_review")
        review_record.review_result = review_data.get("review_result")
        review_record.review_comments = review_data.get("review_comments")
        review_record.reviewer_id = reviewer_id
        review_record.reviewed_at = datetime.now()

        # 如果审核通过，设置有效期
        if review_record.review_status == "approved":
            review_record.valid_from = review_data.get("valid_from", date.today())
            review_record.valid_until = review_data.get("valid_until")

        review_record.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(review_record)

        logger.info(f"Qualification review {review_id} processed by {reviewer_id}")
        return {
            "id": review_record.id,
            "teacher_id": review_record.teacher_id,
            "review_type": review_record.review_type,
            "review_status": review_record.review_status,
            "review_result": review_record.review_result,
            "review_comments": review_record.review_comments,
            "valid_from": review_record.valid_from,
            "valid_until": review_record.valid_until,
            "reviewer_id": review_record.reviewer_id,
            "reviewed_at": review_record.reviewed_at,
        }

    async def get_teacher_qualifications(self, teacher_id: int) -> dict[str, Any]:
        """获取教师资质状态 - 需求2：资质审核流程."""
        from app.users.models.user_models import QualificationReview

        # 检查教师是否存在
        teacher = await self.get_teacher_detail(teacher_id)
        if not teacher:
            raise ValueError(f"教师不存在: {teacher_id}")

        # 查询所有已批准的资质审核记录
        query = select(QualificationReview).where(
            and_(
                QualificationReview.teacher_id == teacher_id,
                QualificationReview.review_status == "approved",
            )
        )
        result = await self.db.execute(query)
        approved_reviews = result.scalars().all()

        # 按审核类型分组
        qualifications: dict[str, dict[str, Any]] = {}
        current_date = date.today()

        for review in approved_reviews:
            review_type = review.review_type
            is_valid = (
                review.valid_from <= current_date <= review.valid_until
                if review.valid_from and review.valid_until
                else True
            )

            if review_type not in qualifications or (
                review.reviewed_at
                and qualifications[review_type]["reviewed_at"]
                and review.reviewed_at > qualifications[review_type]["reviewed_at"]
            ):
                qualifications[review_type] = {
                    "id": review.id,
                    "review_type": review.review_type,
                    "review_cycle": review.review_cycle,
                    "review_result": review.review_result,
                    "valid_from": review.valid_from,
                    "valid_until": review.valid_until,
                    "is_valid": is_valid,
                    "reviewed_at": review.reviewed_at,
                    "reviewer_id": review.reviewer_id,
                }

        # 统计信息
        total_qualifications = len(qualifications)
        valid_qualifications = len([q for q in qualifications.values() if q["is_valid"]])
        expired_qualifications = total_qualifications - valid_qualifications

        return {
            "teacher_id": teacher_id,
            "qualifications": list(qualifications.values()),
            "summary": {
                "total_qualifications": total_qualifications,
                "valid_qualifications": valid_qualifications,
                "expired_qualifications": expired_qualifications,
                "qualification_status": (
                    "qualified" if valid_qualifications > 0 else "unqualified"
                ),
            },
        }
