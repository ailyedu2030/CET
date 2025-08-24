"""班级管理API端点 - 实现班级CRUD操作、资源配置和批量管理接口."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.courses.schemas.class_schemas import (
    ClassBatchCreate,
    ClassConflictCheck,
    ClassCreate,
    ClassListResponse,
    ClassResponse,
    ClassStatistics,
    ClassUpdate,
    ConflictCheckResult,
    StudentEnrollmentRequest,
    StudentEnrollmentResponse,
)
from app.courses.services.class_service import ClassResourceService, ClassService
from app.users.utils.auth_decorators import AuthRequired

router = APIRouter()


# 班级基础管理端点
@router.post("/classes/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClassResponse:
    """创建班级."""
    class_service = ClassService(db)

    try:
        class_obj = await class_service.create_class(class_data, current_user["id"])
        return ClassResponse.model_validate(class_obj)  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClassResponse:
    """获取班级详情."""
    class_service = ClassService(db)

    class_obj = await class_service.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )

    # 检查访问权限（简化处理）
    if (
        current_user.get("role") not in ["admin", "teacher"]
        and class_obj.teacher_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此班级",
        )

    return ClassResponse.model_validate(class_obj)  # type: ignore[no-any-return]


@router.get("/classes/", response_model=list[ClassListResponse])
async def get_classes(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    course_id: int | None = Query(None, description="课程ID筛选"),
    teacher_id: int | None = Query(None, description="教师ID筛选"),
    status: str | None = Query(None, description="状态筛选"),
) -> list[ClassListResponse]:
    """获取班级列表."""
    class_service = ClassService(db)

    # 根据用户角色调整筛选条件
    if current_user.get("role") == "teacher" and not teacher_id:
        teacher_id = current_user["id"]

    classes = await class_service.get_classes(
        skip=skip,
        limit=limit,
        course_id=course_id,
        teacher_id=teacher_id,
        status=status,
    )

    return [ClassListResponse.model_validate(class_obj) for class_obj in classes]


@router.put("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClassResponse:
    """更新班级."""
    class_service = ClassService(db)

    # 检查权限
    class_obj = await class_service.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )

    if current_user.get("role") != "admin" and class_obj.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此班级",
        )

    try:
        updated_class = await class_service.update_class(class_id, class_data)
        if not updated_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在",
            )

        return ClassResponse.model_validate(updated_class)  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """删除班级."""
    class_service = ClassService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除班级",
        )

    success = await class_service.delete_class(class_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )


# 批量操作端点
@router.post("/classes/batch", response_model=list[ClassResponse])
async def batch_create_classes(
    batch_data: ClassBatchCreate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ClassResponse]:
    """批量创建班级."""
    class_service = ClassService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以批量创建班级",
        )

    try:
        classes = await class_service.batch_create_classes(batch_data, current_user["id"])
        return [ClassResponse.model_validate(class_obj) for class_obj in classes]  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 教师分配端点
@router.post("/classes/{class_id}/assign-teacher", response_model=ClassResponse)
async def assign_teacher_to_class(
    class_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher_id: int = Query(..., description="教师ID"),
) -> ClassResponse:
    """分配教师到班级."""
    class_service = ClassService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以分配教师",
        )

    try:
        updated_class = await class_service.assign_teacher_to_class(
            class_id, teacher_id, current_user["id"]
        )
        if not updated_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在",
            )

        return ClassResponse.model_validate(updated_class)  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 学生选课端点
@router.post("/classes/{class_id}/enroll", response_model=StudentEnrollmentResponse)
async def enroll_student(
    class_id: int,
    enrollment_data: StudentEnrollmentRequest,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentEnrollmentResponse:
    """学生选课."""
    class_service = ClassService(db)

    # 验证班级ID一致性
    if enrollment_data.class_id != class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="路径中的班级ID与请求数据不一致",
        )

    # 检查权限
    if current_user.get("role") == "student" and enrollment_data.student_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="学生只能为自己选课",
        )

    try:
        result = await class_service.enroll_student(enrollment_data)
        return StudentEnrollmentResponse(
            id=0,  # 简化处理，实际需要返回真实的选课记录ID
            class_id=result["class_id"],
            student_id=result["student_id"],
            enrollment_status="active",
            enrolled_at=result["enrolled_at"],
            attendance_rate=0.0,
            average_score=0.0,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 冲突检测端点
@router.post("/classes/conflict-check", response_model=ConflictCheckResult)
async def check_class_conflicts(
    conflict_check: ClassConflictCheck,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConflictCheckResult:
    """检查班级冲突."""
    class_service = ClassService(db)

    # 检查权限
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以进行冲突检测",
        )

    try:
        result = await class_service.check_class_conflicts(conflict_check)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 统计信息端点
@router.get("/classes/{class_id}/statistics", response_model=ClassStatistics)
async def get_class_statistics(
    class_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClassStatistics:
    """获取班级统计信息."""
    class_service = ClassService(db)

    # 检查权限
    class_obj = await class_service.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )

    if (
        current_user.get("role") not in ["admin", "teacher"]
        and class_obj.teacher_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问班级统计信息",
        )

    statistics = await class_service.get_class_statistics(class_id)
    if not statistics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无法获取班级统计信息",
        )

    return ClassStatistics(**statistics)


# 资源管理端点
@router.post("/classes/{class_id}/resources")
async def allocate_class_resources(
    class_id: int,
    resource_allocation: dict[str, Any],
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """分配班级资源."""
    resource_service = ClassResourceService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以分配资源",
        )

    try:
        result = await resource_service.allocate_resources(class_id, resource_allocation)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/classes/{class_id}/resources")
async def update_class_resources(
    class_id: int,
    resource_updates: dict[str, Any],
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """更新班级资源配置."""
    resource_service = ClassResourceService(db)

    # 检查权限
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以更新资源配置",
        )

    try:
        result = await resource_service.update_resource_allocation(class_id, resource_updates)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/classes/{class_id}/resources")
async def get_class_resources(
    class_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """获取班级资源配置."""
    class_service = ClassService(db)

    class_obj = await class_service.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )

    # 检查权限
    if (
        current_user.get("role") not in ["admin", "teacher"]
        and class_obj.teacher_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问班级资源信息",
        )

    return {
        "class_id": class_id,
        "resource_allocation": class_obj.resource_allocation,
        "last_updated": class_obj.updated_at,
    }


# 课程表管理端点
@router.put("/classes/{class_id}/schedule")
async def update_class_schedule(
    class_id: int,
    schedule: dict[str, Any],
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """更新班级课程表."""
    class_service = ClassService(db)

    # 检查权限
    class_obj = await class_service.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )

    if current_user.get("role") != "admin" and class_obj.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改班级课程表",
        )

    try:
        # 更新课程表
        class_update = ClassUpdate(
            name=None,
            description=None,
            code=None,
            max_students=None,
            resource_allocation=None,
            class_rules=None,
            start_date=None,
            end_date=None,
            schedule=schedule,
            teacher_id=None,
            is_active=None,
            status=None,
        )
        updated_class = await class_service.update_class(class_id, class_update)

        if not updated_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在",
            )

        return {
            "class_id": class_id,
            "schedule": updated_class.schedule,
            "updated_at": updated_class.updated_at,
            "message": "课程表更新成功",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/classes/{class_id}/schedule")
async def get_class_schedule(
    class_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """获取班级课程表."""
    class_service = ClassService(db)

    class_obj = await class_service.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在",
        )

    return {
        "class_id": class_id,
        "schedule": class_obj.schedule,
        "start_date": class_obj.start_date,
        "end_date": class_obj.end_date,
        "last_updated": class_obj.updated_at,
    }
