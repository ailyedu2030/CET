"""基础信息管理API端点 - 需求2：基础信息管理."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.services.basic_info_service import BasicInfoService
from app.users.utils.auth_decorators import get_current_active_user

router = APIRouter(prefix="/basic-info", tags=["基础信息管理"])


# ===== 请求/响应模型 =====


class StudentUpdateRequest(BaseModel):
    """学生信息更新请求."""

    real_name: str | None = None
    age: int | None = Field(None, ge=16, le=35)
    gender: str | None = None
    phone: str | None = None
    school: str | None = None
    department: str | None = None
    major: str | None = None
    grade: str | None = None
    class_name: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    parent_email: str | None = None
    notes: str | None = None


class StudentStatusUpdateRequest(BaseModel):
    """学生状态更新请求."""

    learning_status: str = Field(..., pattern="^(active|inactive|suspended|graduated)$")
    notes: str | None = None


class TeacherUpdateRequest(BaseModel):
    """教师信息更新请求."""

    real_name: str | None = None
    age: int | None = Field(None, ge=22, le=70)
    gender: str | None = None
    title: str | None = None
    subject: str | None = None
    phone: str | None = None
    introduction: str | None = None


class TeacherSalaryUpdateRequest(BaseModel):
    """教师薪酬更新请求."""

    hourly_rate: float = Field(..., ge=0)
    monthly_salary: float = Field(..., ge=0)


class TeacherQualificationReviewRequest(BaseModel):
    """教师资质审核请求."""

    qualification_status: str = Field(..., pattern="^(pending|approved|rejected|expired)$")
    notes: str | None = None


class ClassroomConflictCheckRequest(BaseModel):
    """教室冲突检查请求."""

    classroom_id: int
    start_time: datetime
    end_time: datetime
    exclude_schedule_id: int | None = None


# ===== 设备管理请求/响应模型 - 功能2 =====


class EquipmentCreateRequest(BaseModel):
    """设备创建请求."""

    name: str = Field(..., min_length=1, max_length=100)
    equipment_type: str = Field(..., pattern="^(projector|computer|audio|whiteboard|other)$")
    brand: str | None = Field(None, max_length=50)
    model: str | None = Field(None, max_length=100)
    serial_number: str | None = Field(None, max_length=100)
    purchase_date: datetime | None = None
    warranty_end_date: datetime | None = None
    specifications: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class EquipmentUpdateRequest(BaseModel):
    """设备更新请求."""

    name: str | None = Field(None, min_length=1, max_length=100)
    equipment_type: str | None = Field(
        None, pattern="^(projector|computer|audio|whiteboard|other)$"
    )
    brand: str | None = Field(None, max_length=50)
    model: str | None = Field(None, max_length=100)
    serial_number: str | None = Field(None, max_length=100)
    status: str | None = Field(None, pattern="^(normal|maintenance|repair|broken|retired)$")
    purchase_date: datetime | None = None
    warranty_end_date: datetime | None = None
    specifications: dict[str, Any] | None = None
    notes: str | None = None


class MaintenanceRecordCreateRequest(BaseModel):
    """维护记录创建请求."""

    maintenance_type: str = Field(..., pattern="^(routine|repair|upgrade|inspection)$")
    maintenance_date: datetime
    description: str = Field(..., min_length=1)
    cost: float = Field(default=0.0, ge=0)
    duration_hours: float = Field(default=0.0, ge=0)
    result: str = Field(default="completed", pattern="^(completed|failed|partial)$")
    next_maintenance_date: datetime | None = None
    notes: str | None = None
    maintainer_id: int | None = None


# ===== 学生信息管理端点 =====


@router.get("/students")
async def get_students(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str | None = Query(None, description="搜索关键词"),
    learning_status: str | None = Query(None, description="学习状态"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学生列表 - 需求2验收标准1."""
    # 权限检查：只有管理员可以访问
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问学生信息",
        )

    service = BasicInfoService(db)
    return await service.get_students(
        page=page,
        size=size,
        search=search,
        learning_status=learning_status,
    )


@router.get("/students/{student_id}")
async def get_student_detail(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学生详细信息."""
    # 权限检查：管理员或学生本人
    if current_user.user_type != UserType.ADMIN and current_user.id != student_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="无权访问该学生信息")

    service = BasicInfoService(db)
    student = await service.get_student_detail(student_id)

    if not student:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="学生不存在")

    return {
        "id": student.id,
        "username": student.username,
        "email": student.email,
        "is_active": student.is_active,
        "profile": student.student_profile,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
    }


@router.put("/students/{student_id}")
async def update_student_info(
    student_id: int,
    request: StudentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新学生信息 - 需求2验收标准1."""
    # 权限检查：只有管理员可以更新
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新学生信息",
        )

    service = BasicInfoService(db)
    student_data = request.dict(exclude_unset=True)

    student = await service.update_student_info(student_id, student_data)
    if not student:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="学生不存在")

    return {
        "message": "学生信息更新成功",
        "student": {
            "id": student.id,
            "username": student.username,
            "profile": student.student_profile,
        },
    }


@router.put("/students/{student_id}/status")
async def update_student_status(
    student_id: int,
    request: StudentStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新学生学习状态 - 需求2验收标准1."""
    # 权限检查：只有管理员可以更新
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新学生状态",
        )

    service = BasicInfoService(db)
    success = await service.update_student_learning_status(
        student_id, request.learning_status, request.notes
    )

    if not success:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="学生不存在")

    return {
        "message": f"学生状态已更新为：{request.learning_status}",
        "status": request.learning_status,
    }


# ===== 教师信息管理端点 =====


@router.get("/teachers")
async def get_teachers(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str | None = Query(None, description="搜索关键词"),
    teaching_status: str | None = Query(None, description="教学状态"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取教师列表 - 需求2验收标准2."""
    # 权限检查：只有管理员可以访问
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问教师信息",
        )

    service = BasicInfoService(db)
    return await service.get_teachers(
        page=page,
        size=size,
        search=search,
        teaching_status=teaching_status,
    )


@router.get("/teachers/{teacher_id}")
async def get_teacher_detail(
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取教师详细信息."""
    # 权限检查：管理员或教师本人
    if current_user.user_type != UserType.ADMIN and current_user.id != teacher_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="无权访问该教师信息")

    service = BasicInfoService(db)
    teacher = await service.get_teacher_detail(teacher_id)

    if not teacher:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="教师不存在")

    return {
        "id": teacher.id,
        "username": teacher.username,
        "email": teacher.email,
        "is_active": teacher.is_active,
        "profile": teacher.teacher_profile,
        "created_at": teacher.created_at,
        "updated_at": teacher.updated_at,
    }


@router.put("/teachers/{teacher_id}")
async def update_teacher_info(
    teacher_id: int,
    request: TeacherUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新教师信息 - 需求2验收标准2."""
    # 权限检查：只有管理员可以更新
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新教师信息",
        )

    service = BasicInfoService(db)
    teacher_data = request.dict(exclude_unset=True)

    teacher = await service.update_teacher_info(teacher_id, teacher_data)
    if not teacher:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="教师不存在")

    return {
        "message": "教师信息更新成功",
        "teacher": {
            "id": teacher.id,
            "username": teacher.username,
            "profile": teacher.teacher_profile,
        },
    }


@router.put("/teachers/{teacher_id}/salary")
async def update_teacher_salary(
    teacher_id: int,
    request: TeacherSalaryUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新教师薪酬 - 需求2验收标准2."""
    # 权限检查：只有管理员可以更新
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新教师薪酬",
        )

    service = BasicInfoService(db)
    success = await service.update_teacher_salary(
        teacher_id, request.hourly_rate, request.monthly_salary
    )

    if not success:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="教师不存在")

    return {
        "message": "教师薪酬更新成功",
        "hourly_rate": request.hourly_rate,
        "monthly_salary": request.monthly_salary,
    }


@router.put("/teachers/{teacher_id}/qualification")
async def review_teacher_qualification(
    teacher_id: int,
    request: TeacherQualificationReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """教师资质审核 - 需求2验收标准2."""
    # 权限检查：只有管理员可以审核
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以进行资质审核",
        )

    service = BasicInfoService(db)
    success = await service.process_teacher_qualification_review(
        teacher_id, request.qualification_status, request.notes
    )

    if not success:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="教师不存在")

    return {
        "message": f"教师资质状态已更新为：{request.qualification_status}",
        "status": request.qualification_status,
    }


# ===== 教室信息管理端点 =====


@router.get("/campuses")
async def get_campuses(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取校区列表."""
    service = BasicInfoService(db)
    campuses = await service.get_campuses()

    return {
        "campuses": [
            {
                "id": campus.id,
                "name": campus.name,
                "address": campus.address,
                "description": campus.description,
            }
            for campus in campuses
        ]
    }


@router.get("/buildings")
async def get_buildings(
    campus_id: int | None = Query(None, description="校区ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取楼栋列表."""
    service = BasicInfoService(db)
    buildings = await service.get_buildings(campus_id)

    return {
        "buildings": [
            {
                "id": building.id,
                "campus_id": building.campus_id,
                "name": building.name,
                "building_number": building.building_number,
                "floors": building.floors,
            }
            for building in buildings
        ]
    }


@router.get("/classrooms")
async def get_classrooms(
    building_id: int | None = Query(None, description="楼栋ID"),
    is_available: bool | None = Query(None, description="是否可用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取教室列表 - 需求2验收标准3."""
    service = BasicInfoService(db)
    return await service.get_classrooms(
        building_id=building_id,
        is_available=is_available,
        page=page,
        size=size,
    )


@router.post("/classrooms/check-conflict")
async def check_classroom_conflict(
    request: ClassroomConflictCheckRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """检查教室排期冲突 - 需求2验收标准5."""
    # 权限检查：管理员和教师可以检查
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="无权检查教室冲突")

    service = BasicInfoService(db)
    has_conflict = await service.check_classroom_conflict(
        classroom_id=request.classroom_id,
        start_time=request.start_time,
        end_time=request.end_time,
        exclude_schedule_id=request.exclude_schedule_id,
    )

    return {
        "has_conflict": has_conflict,
        "message": "该时间段教室已被占用" if has_conflict else "该时间段教室可用",
        "classroom_id": request.classroom_id,
        "start_time": request.start_time,
        "end_time": request.end_time,
    }


# ===== 设备管理端点 - 功能2 =====


@router.get("/classrooms/{classroom_id}/equipment")
async def get_classroom_equipment(
    classroom_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取教室设备列表 - 功能2：设备管理."""
    service = BasicInfoService(db)
    return await service.get_classroom_equipment(
        classroom_id=classroom_id,
        page=page,
        size=size,
    )


@router.post("/classrooms/{classroom_id}/equipment")
async def create_equipment(
    classroom_id: int,
    request: EquipmentCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建设备 - 功能2：设备管理."""
    # 权限检查：只有管理员可以创建设备
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN, detail="只有管理员可以创建设备"
        )

    service = BasicInfoService(db)
    equipment_data = request.dict(exclude_unset=True)

    equipment = await service.create_equipment(classroom_id, equipment_data)

    return {
        "message": "设备创建成功",
        "equipment": {
            "id": equipment.id,
            "name": equipment.name,
            "equipment_type": equipment.equipment_type,
            "status": equipment.status,
        },
    }


@router.get("/equipment/{equipment_id}")
async def get_equipment_detail(
    equipment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取设备详细信息."""
    service = BasicInfoService(db)
    equipment = await service.get_equipment_detail(equipment_id)

    if not equipment:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="设备不存在")

    return {
        "id": equipment.id,
        "classroom_id": equipment.classroom_id,
        "name": equipment.name,
        "equipment_type": equipment.equipment_type,
        "brand": equipment.brand,
        "model": equipment.model,
        "serial_number": equipment.serial_number,
        "status": equipment.status,
        "purchase_date": equipment.purchase_date,
        "warranty_end_date": equipment.warranty_end_date,
        "last_maintenance_date": equipment.last_maintenance_date,
        "next_maintenance_date": equipment.next_maintenance_date,
        "total_usage_hours": equipment.total_usage_hours,
        "monthly_usage_hours": equipment.monthly_usage_hours,
        "failure_count": equipment.failure_count,
        "specifications": equipment.specifications,
        "notes": equipment.notes,
        "classroom": equipment.classroom,
        "maintenance_records": equipment.maintenance_records,
        "created_at": equipment.created_at,
        "updated_at": equipment.updated_at,
    }


@router.put("/equipment/{equipment_id}")
async def update_equipment(
    equipment_id: int,
    request: EquipmentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新设备信息 - 功能2：设备管理."""
    # 权限检查：只有管理员可以更新设备
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新设备信息",
        )

    service = BasicInfoService(db)
    equipment_data = request.dict(exclude_unset=True)

    equipment = await service.update_equipment(equipment_id, equipment_data)
    if not equipment:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="设备不存在")

    return {
        "message": "设备信息更新成功",
        "equipment": {
            "id": equipment.id,
            "name": equipment.name,
            "equipment_type": equipment.equipment_type,
            "status": equipment.status,
        },
    }


@router.delete("/equipment/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除设备 - 功能2：设备管理."""
    # 权限检查：只有管理员可以删除设备
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN, detail="只有管理员可以删除设备"
        )

    service = BasicInfoService(db)
    success = await service.delete_equipment(equipment_id)

    if not success:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="设备不存在")

    return {
        "message": "设备删除成功",
    }


# ===== 设备维护记录管理端点 - 功能2 =====


@router.get("/equipment/{equipment_id}/maintenance-records")
async def get_equipment_maintenance_records(
    equipment_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取设备维护记录 - 功能2：维护记录管理."""
    service = BasicInfoService(db)
    return await service.get_equipment_maintenance_records(
        equipment_id=equipment_id,
        page=page,
        size=size,
    )


@router.post("/equipment/{equipment_id}/maintenance-records")
async def create_maintenance_record(
    equipment_id: int,
    request: MaintenanceRecordCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建维护记录 - 功能2：维护记录管理."""
    # 权限检查：管理员和维护人员可以创建维护记录
    if current_user.user_type not in [UserType.ADMIN]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建维护记录",
        )

    service = BasicInfoService(db)
    record_data = request.dict(exclude_unset=True)

    # 如果没有指定维护人员，使用当前用户
    if not record_data.get("maintainer_id"):
        record_data["maintainer_id"] = current_user.id

    record = await service.create_maintenance_record(equipment_id, record_data)

    return {
        "message": "维护记录创建成功",
        "record": {
            "id": record.id,
            "equipment_id": record.equipment_id,
            "maintenance_type": record.maintenance_type,
            "maintenance_date": record.maintenance_date,
            "result": record.result,
        },
    }


# ===== 设备统计端点 - 功能2 =====


@router.get("/equipment/statistics")
async def get_equipment_statistics(
    classroom_id: int | None = Query(None, description="教室ID（可选）"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取设备使用统计 - 功能2：使用统计."""
    service = BasicInfoService(db)
    return await service.get_equipment_statistics(classroom_id)


# ===== 考勤管理端点 - 需求2：考勤管理 =====


@router.get("/students/{student_id}/attendance")
async def get_student_attendance(
    student_id: int,
    start_date: str | None = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学生考勤记录 - 需求2：考勤管理."""
    # 权限检查：只有管理员和教师可以查看考勤
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看考勤记录",
        )

    service = BasicInfoService(db)

    # 转换日期参数
    from datetime import date

    start_date_obj = date.fromisoformat(start_date) if start_date else None
    end_date_obj = date.fromisoformat(end_date) if end_date else None

    return await service.get_student_attendance(
        student_id=student_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        page=page,
        size=size,
    )


@router.post("/students/{student_id}/attendance")
async def create_attendance_record(
    student_id: int,
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建考勤记录 - 需求2：考勤管理."""
    # 权限检查：只有管理员和教师可以创建考勤记录
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以创建考勤记录",
        )

    service = BasicInfoService(db)

    try:
        # 转换日期字符串
        if "attendance_date" in request:
            from datetime import date

            request["attendance_date"] = date.fromisoformat(request["attendance_date"])

        record = await service.create_attendance_record(
            student_id=student_id,
            attendance_data=request,
            recorded_by=current_user.id,
        )
        return {
            "message": "考勤记录创建成功",
            "record": record,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/attendance/{record_id}")
async def update_attendance_record(
    record_id: int,
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新考勤记录 - 需求2：考勤管理."""
    # 权限检查：只有管理员和教师可以更新考勤记录
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以更新考勤记录",
        )

    service = BasicInfoService(db)
    record = await service.update_attendance_record(record_id, request)

    if not record:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="考勤记录不存在",
        )

    return {
        "message": "考勤记录更新成功",
        "record": record,
    }


@router.post("/attendance/{record_id}/approve")
async def approve_leave_request(
    record_id: int,
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审批请假申请 - 需求2：考勤管理."""
    # 权限检查：只有管理员和教师可以审批请假
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以审批请假",
        )

    service = BasicInfoService(db)
    success = await service.approve_leave_request(
        record_id=record_id,
        approved=request.get("approved", False),
        approved_by=current_user.id,
        notes=request.get("notes"),
    )

    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="请假记录不存在或不是请假类型",
        )

    return {
        "message": "请假审批完成",
        "approved": request.get("approved", False),
    }


# ===== 教学状态跟踪端点 - 需求2：教学状态跟踪 =====


@router.get("/teachers/{teacher_id}/teaching-records")
async def get_teacher_teaching_records(
    teacher_id: int,
    start_date: str | None = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取教师教学记录 - 需求2：教学状态跟踪."""
    # 权限检查：只有管理员和教师本人可以查看教学记录
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看教学记录",
        )

    # 教师只能查看自己的记录
    if current_user.user_type == UserType.TEACHER and current_user.id != teacher_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="教师只能查看自己的教学记录",
        )

    service = BasicInfoService(db)

    # 转换日期参数
    from datetime import date

    start_date_obj = date.fromisoformat(start_date) if start_date else None
    end_date_obj = date.fromisoformat(end_date) if end_date else None

    return await service.get_teacher_teaching_records(
        teacher_id=teacher_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        page=page,
        size=size,
    )


@router.post("/teachers/{teacher_id}/teaching-records")
async def create_teaching_record(
    teacher_id: int,
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建教学记录 - 需求2：教学状态跟踪."""
    # 权限检查：只有管理员和教师可以创建教学记录
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以创建教学记录",
        )

    service = BasicInfoService(db)

    try:
        # 转换时间字符串
        if "teaching_start_time" in request:
            from datetime import datetime

            request["teaching_start_time"] = datetime.fromisoformat(request["teaching_start_time"])
        if "teaching_end_time" in request:
            from datetime import datetime

            request["teaching_end_time"] = datetime.fromisoformat(request["teaching_end_time"])

        record = await service.create_teaching_record(
            teacher_id=teacher_id,
            teaching_data=request,
            created_by=current_user.id,
        )
        return {
            "message": "教学记录创建成功",
            "record": record,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/teaching-records/{record_id}")
async def update_teaching_record(
    record_id: int,
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新教学记录 - 需求2：教学状态跟踪."""
    # 权限检查：只有管理员和教师可以更新教学记录
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以更新教学记录",
        )

    service = BasicInfoService(db)

    # 转换时间字符串
    if "teaching_start_time" in request:
        from datetime import datetime

        request["teaching_start_time"] = datetime.fromisoformat(request["teaching_start_time"])
    if "teaching_end_time" in request:
        from datetime import datetime

        request["teaching_end_time"] = datetime.fromisoformat(request["teaching_end_time"])

    record = await service.update_teaching_record(record_id, request)

    if not record:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="教学记录不存在",
        )

    return {
        "message": "教学记录更新成功",
        "record": record,
    }


@router.get("/teachers/{teacher_id}/teaching-statistics")
async def get_teaching_statistics(
    teacher_id: int,
    period: str = Query("month", description="统计周期：week/month/quarter/year"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取教学统计数据 - 需求2：教学状态跟踪."""
    # 权限检查：只有管理员和教师本人可以查看教学统计
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看教学统计",
        )

    # 教师只能查看自己的统计
    if current_user.user_type == UserType.TEACHER and current_user.id != teacher_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="教师只能查看自己的教学统计",
        )

    service = BasicInfoService(db)
    return await service.get_teaching_statistics(teacher_id=teacher_id, period=period)
