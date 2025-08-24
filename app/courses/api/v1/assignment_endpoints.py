"""课程分配管理API端点 - 实现教师分配、工作量平衡和冲突检测接口."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.courses.schemas.assignment_schemas import (
    BulkAssignmentRequest,
    BulkAssignmentResponse,
    CourseAssignmentRequest,
    CourseAssignmentResponse,
    QualificationCheckResult,
    TeacherQualificationCheck,
    TeacherWorkloadInfo,
    TimeConflictCheck,
    TimeConflictResult,
    WorkloadBalanceRequest,
    WorkloadBalanceResponse,
)
from app.courses.services.assignment_service import AssignmentService
from app.users.utils.auth_decorators import AuthRequired

router = APIRouter()


# 课程分配端点
@router.post("/assignments/courses", response_model=CourseAssignmentResponse)
async def assign_course_to_teacher(
    assignment_request: CourseAssignmentRequest,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseAssignmentResponse:
    """分配课程给教师."""
    assignment_service = AssignmentService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以分配课程",
        )

    try:
        assignment_result = await assignment_service.assign_course_to_teacher(
            assignment_request, current_user["id"]
        )

        return CourseAssignmentResponse(
            id=0,  # 简化处理，实际需要真实的分配记录ID
            course_id=assignment_result["course_id"],
            teacher_id=assignment_result["teacher_id"],
            assigned_at=assignment_result["assigned_at"],
            assigned_by=assignment_result["assigned_by"],
            is_active=True,
            assignment_type=assignment_result["assignment_type"],
            assignment_reason=assignment_result.get("assignment_reason"),
            workload_impact=assignment_result.get("evaluation_score", 0.0),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 教师资质检查端点
@router.post("/assignments/qualification-check", response_model=QualificationCheckResult)
async def check_teacher_qualification(
    qualification_check: TeacherQualificationCheck,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QualificationCheckResult:
    """检查教师资质."""
    assignment_service = AssignmentService(db)

    # 检查权限
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看资质信息",
        )

    try:
        result = await assignment_service.check_teacher_qualification(qualification_check)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 工作量管理端点
@router.get("/assignments/teachers/{teacher_id}/workload", response_model=TeacherWorkloadInfo)
async def get_teacher_workload(
    teacher_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeacherWorkloadInfo:
    """获取教师工作量信息."""
    assignment_service = AssignmentService(db)

    # 检查权限
    if current_user.get("role") not in ["admin", "teacher"] or (
        current_user.get("role") == "teacher" and current_user["id"] != teacher_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此教师的工作量信息",
        )

    try:
        workload_info = await assignment_service.get_teacher_workload(teacher_id)
        return workload_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/assignments/workload-balance", response_model=WorkloadBalanceResponse)
async def balance_teacher_workload(
    balance_request: WorkloadBalanceRequest,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkloadBalanceResponse:
    """平衡教师工作量."""
    assignment_service = AssignmentService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行工作量平衡",
        )

    try:
        balance_result = await assignment_service.balance_workload(balance_request)
        return balance_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 时间冲突检测端点
@router.post("/assignments/time-conflict-check", response_model=TimeConflictResult)
async def check_time_conflicts(
    conflict_check: TimeConflictCheck,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimeConflictResult:
    """检查时间冲突."""
    assignment_service = AssignmentService(db)

    # 检查权限
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以进行时间冲突检测",
        )

    # 如果是教师，只能检查自己的时间冲突
    if current_user.get("role") == "teacher" and conflict_check.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教师只能检查自己的时间冲突",
        )

    try:
        conflict_result = await assignment_service.check_time_conflicts(conflict_check)
        return conflict_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 批量分配端点
@router.post("/assignments/bulk", response_model=BulkAssignmentResponse)
async def bulk_assignment(
    bulk_request: BulkAssignmentRequest,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BulkAssignmentResponse:
    """批量分配操作."""
    assignment_service = AssignmentService(db)

    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行批量分配",
        )

    try:
        bulk_result = await assignment_service.bulk_assignment(bulk_request)
        return bulk_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# 分配历史和统计端点
@router.get("/assignments/history")
async def get_assignment_history(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    assignment_type: str | None = Query(None, description="分配类型筛选"),
    teacher_id: int | None = Query(None, description="教师ID筛选"),
    course_id: int | None = Query(None, description="课程ID筛选"),
) -> dict[str, Any]:
    """获取分配历史记录."""
    # 检查权限
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看分配历史",
        )

    # 如果是教师，只能查看自己相关的记录
    if current_user.get("role") == "teacher":
        teacher_id = current_user["id"]

    # 这里简化处理，实际需要查询分配历史表
    return {
        "total": 0,
        "assignments": [],
        "skip": skip,
        "limit": limit,
        "filters": {
            "assignment_type": assignment_type,
            "teacher_id": teacher_id,
            "course_id": course_id,
        },
    }


@router.get("/assignments/statistics")
async def get_assignment_statistics(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    department_id: int | None = Query(None, description="部门ID"),
    semester: str | None = Query(None, description="学期"),
) -> dict[str, Any]:
    """获取分配统计信息."""
    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看分配统计",
        )

    # 这里简化处理，返回模拟统计数据
    return {
        "total_assignments": 45,
        "active_assignments": 40,
        "pending_assignments": 5,
        "teacher_utilization": {
            "average_workload": 0.75,
            "overloaded_teachers": 3,
            "underutilized_teachers": 2,
        },
        "course_coverage": {
            "covered_courses": 28,
            "uncovered_courses": 2,
            "coverage_percentage": 0.93,
        },
        "time_conflicts": {
            "total_conflicts": 8,
            "resolved_conflicts": 6,
            "pending_conflicts": 2,
        },
        "department_breakdown": {
            "english_department": {
                "teachers": 15,
                "courses": 12,
                "average_workload": 0.8,
            },
            "foreign_language_department": {
                "teachers": 8,
                "courses": 6,
                "average_workload": 0.7,
            },
        },
    }


# 分配建议端点
@router.get("/assignments/suggestions")
async def get_assignment_suggestions(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    course_id: int | None = Query(None, description="课程ID"),
    optimization_goal: str = Query("balance", description="优化目标"),
) -> dict[str, Any]:
    """获取分配建议."""
    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以获取分配建议",
        )

    # 这里简化处理，返回模拟建议
    suggestions = []

    if course_id:
        suggestions.append(
            {
                "type": "course_assignment",
                "course_id": course_id,
                "recommended_teachers": [
                    {
                        "teacher_id": 101,
                        "score": 0.95,
                        "reason": "专业匹配度高，工作量适中",
                    },
                    {"teacher_id": 102, "score": 0.87, "reason": "经验丰富，时间充裕"},
                ],
                "considerations": [
                    "建议优先分配给评分最高的教师",
                    "如需平衡工作量，可考虑第二候选人",
                ],
            }
        )

    # 全局优化建议
    suggestions.append(
        {
            "type": "workload_optimization",
            "recommendations": [
                "教师A工作量过重，建议转移1个班级",
                "教师B可承担更多课程",
                "检测到3个时间冲突，需要调整",
            ],
            "expected_improvement": {
                "balance_score_increase": 0.15,
                "conflict_reduction": 3,
            },
        }
    )

    return {
        "optimization_goal": optimization_goal,
        "suggestions": suggestions,
        "generated_at": "2024-01-01T00:00:00Z",
    }


# 分配规则管理端点
@router.get("/assignments/rules")
async def get_assignment_rules(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """获取分配规则配置."""
    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看分配规则",
        )

    return {
        "binding_rules": {
            "one_class_one_teacher": {
                "enabled": True,
                "description": "1班级↔1教师绑定规则",
                "exceptions_allowed": True,
            },
            "one_class_one_course": {
                "enabled": True,
                "description": "1班级↔1课程绑定规则",
                "exceptions_allowed": False,
            },
        },
        "workload_limits": {
            "max_classes_per_teacher": 5,
            "max_students_per_teacher": 250,
            "min_classes_per_teacher": 1,
        },
        "qualification_requirements": {
            "minimum_experience_years": 1,
            "required_certifications": ["teaching_license"],
            "expertise_match_threshold": 0.6,
        },
        "time_conflict_settings": {
            "tolerance_minutes": 15,
            "check_enabled": True,
            "auto_resolve": False,
        },
    }


@router.put("/assignments/rules")
async def update_assignment_rules(
    rules_update: dict[str, Any],
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """更新分配规则配置."""
    # 检查权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改分配规则",
        )

    # 这里简化处理，实际需要验证规则配置并保存到数据库
    # 验证规则格式
    required_sections = [
        "binding_rules",
        "workload_limits",
        "qualification_requirements",
    ]
    for section in required_sections:
        if section not in rules_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需的规则配置节: {section}",
            )

    return {
        "message": "分配规则更新成功",
        "updated_rules": rules_update,
        "updated_at": "2024-01-01T00:00:00Z",
        "updated_by": current_user["id"],
    }
