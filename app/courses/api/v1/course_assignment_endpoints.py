"""课程分配管理API端点 - 需求5：课程分配管理."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.courses.schemas.assignment_schemas import CourseAssignmentRequest
from app.courses.services.course_assignment_service import CourseAssignmentService
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/course-assignment", tags=["课程分配管理"])


@router.post("/assignments")
async def assign_course_to_teacher(
    assignment_request: CourseAssignmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """分配课程给教师 - 需求5验收标准1."""
    # 权限检查：只有管理员可以分配课程
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以分配课程",
        )

    try:
        service = CourseAssignmentService(db)
        result = await service.assign_course_to_teacher(assignment_request, current_user.id)

        logger.info(
            f"管理员 {current_user.id} 分配课程: "
            f"课程ID {assignment_request.course_id} -> 教师ID {assignment_request.teacher_ids[0]}"
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"分配课程失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配课程失败",
        ) from e


@router.post("/one-to-many-configuration")
async def configure_one_to_many_assignment(
    course_id: int = Query(..., description="课程ID"),
    configuration: dict[str, Any] = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """配置一对多分配 - 需求5验收标准2."""
    # 权限检查：只有管理员可以配置一对多分配
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以配置一对多分配",
        )

    try:
        service = CourseAssignmentService(db)
        result = await service.configure_one_to_many_assignment(
            course_id, configuration, current_user.id
        )

        logger.info(
            f"管理员 {current_user.id} 配置一对多分配: "
            f"课程ID {course_id}, 类型 {configuration.get('type')}"
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"配置一对多分配失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置一对多分配失败",
        ) from e


@router.post("/teacher-collaboration-permissions")
async def set_teacher_collaboration_permissions(
    course_id: int = Query(..., description="课程ID"),
    permission_config: dict[str, Any] = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """设置多教师协作权限边界 - 需求5验收标准3."""
    # 权限检查：只有管理员可以设置协作权限
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以设置协作权限",
        )

    try:
        service = CourseAssignmentService(db)
        result = await service.set_teacher_collaboration_permissions(
            course_id, permission_config, current_user.id
        )

        logger.info(f"管理员 {current_user.id} 设置多教师协作权限: 课程ID {course_id}")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"设置多教师协作权限失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置多教师协作权限失败",
        ) from e


@router.post("/rule-exemption-requests")
async def request_rule_exemption(
    exemption_request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """申请规则豁免 - 需求5验收标准5."""
    # 权限检查：管理员和教师可以申请规则豁免
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以申请规则豁免",
        )

    try:
        service = CourseAssignmentService(db)
        result = await service.request_rule_exemption(exemption_request, current_user.id)

        logger.info(
            f"用户 {current_user.id} 申请规则豁免: 类型 {exemption_request.get('exemption_type')}"
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"申请规则豁免失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="申请规则豁免失败",
        ) from e


@router.post("/rule-exemption-requests/{exemption_id}/approve")
async def approve_rule_exemption(
    exemption_id: int,
    approval_notes: str | None = Query(None, description="审批备注"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审批规则豁免 - 需求5验收标准5."""
    # 权限检查：只有管理员可以审批规则豁免
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审批规则豁免",
        )

    try:
        service = CourseAssignmentService(db)
        result = await service.approve_rule_exemption(exemption_id, current_user.id, approval_notes)

        logger.info(f"管理员 {current_user.id} 审批规则豁免: ID {exemption_id}")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"审批规则豁免失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审批规则豁免失败",
        ) from e


@router.post("/rule-exemption-requests/{exemption_id}/reject")
async def reject_rule_exemption(
    exemption_id: int,
    rejection_reason: str = Query(..., description="拒绝原因"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """拒绝规则豁免 - 需求5验收标准5."""
    # 权限检查：只有管理员可以拒绝规则豁免
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以拒绝规则豁免",
        )

    try:
        from app.courses.models.course_models import RuleExemptionRequest

        # 获取豁免申请
        exemption = await db.get(RuleExemptionRequest, exemption_id)
        if not exemption:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="豁免申请不存在",
            )

        if exemption.status != "pending":
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"豁免申请状态为{exemption.status}，无法拒绝",
            )

        # 更新拒绝状态
        exemption.status = "rejected"
        exemption.approved_by = current_user.id
        exemption.approved_at = datetime.utcnow()
        exemption.approval_notes = f"拒绝原因: {rejection_reason}"

        await db.commit()

        logger.info(f"管理员 {current_user.id} 拒绝规则豁免: ID {exemption_id}")

        return {
            "exemption_id": exemption_id,
            "status": "rejected",
            "rejected_by": current_user.id,
            "rejected_at": exemption.approved_at,
            "rejection_reason": rejection_reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拒绝规则豁免失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="拒绝规则豁免失败",
        ) from e


@router.get("/rule-exemption-requests")
async def get_rule_exemption_requests(
    status: str | None = Query(None, description="状态筛选"),
    course_id: int | None = Query(None, description="课程ID筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取规则豁免申请列表 - 需求5验收标准5."""
    # 权限检查：管理员可以查看所有申请，教师只能查看自己的申请
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看规则豁免申请",
        )

    try:
        from sqlalchemy import select

        from app.courses.models.course_models import RuleExemptionRequest

        # 构建查询
        query = select(RuleExemptionRequest)

        # 权限过滤
        if current_user.user_type == UserType.TEACHER:
            query = query.where(RuleExemptionRequest.requested_by == current_user.id)

        # 状态过滤
        if status:
            query = query.where(RuleExemptionRequest.status == status)

        # 课程过滤
        if course_id:
            query = query.where(RuleExemptionRequest.course_id == course_id)

        # 执行查询
        result = await db.execute(query)
        exemption_requests = result.scalars().all()

        # 转换为字典格式
        requests_data = []
        for request in exemption_requests:
            requests_data.append(
                {
                    "id": request.id,
                    "course_id": request.course_id,
                    "teacher_id": request.teacher_id,
                    "exemption_type": request.exemption_type,
                    "exemption_reason": request.exemption_reason,
                    "status": request.status,
                    "requested_by": request.requested_by,
                    "requested_at": request.requested_at,
                    "approved_by": request.approved_by,
                    "approved_at": request.approved_at,
                    "approval_notes": request.approval_notes,
                }
            )

        logger.info(f"用户 {current_user.id} 查看规则豁免申请列表: {len(requests_data)} 条记录")

        return {
            "exemption_requests": requests_data,
            "total_count": len(requests_data),
            "filters": {
                "status": status,
                "course_id": course_id,
            },
        }

    except Exception as e:
        logger.error(f"获取规则豁免申请列表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取规则豁免申请列表失败",
        ) from e
