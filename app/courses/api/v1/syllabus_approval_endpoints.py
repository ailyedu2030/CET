"""教学大纲审批API端点 - 需求3：课程全生命周期管理."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas.ai_schemas import SyllabusResponse
from app.ai.services.syllabus_service import SyllabusService
from app.core.database import get_db
from app.courses.services.course_lifecycle_service import CourseLifecycleService
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/syllabus-approval", tags=["教学大纲审批"])


class SyllabusApprovalRequest:
    """大纲审批请求."""

    def __init__(self, action: str, notes: str | None = None) -> None:
        """初始化审批请求."""
        self.action = action  # "approve" 或 "reject"
        self.notes = notes


@router.get("/syllabi/pending")
async def get_pending_syllabi(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
) -> dict[str, Any]:
    """获取待审批的教学大纲列表 - 需求3验收标准3."""
    # 权限检查：只有管理员可以查看待审批大纲
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看待审批大纲",
        )

    try:
        syllabus_service = SyllabusService()

        # 获取待审批的大纲（状态为 "review"）
        syllabi, total = await syllabus_service.list_syllabi(
            db=db,
            status="review",
            page=page,
            size=size,
        )

        logger.info(f"管理员 {current_user.id} 查看了待审批大纲列表")

        return {
            "syllabi": syllabi,
            "total": total,
            "page": page,
            "size": size,
            "message": f"获取到 {len(syllabi)} 个待审批大纲",
        }

    except Exception as e:
        logger.error(f"获取待审批大纲失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取待审批大纲失败",
        ) from e


@router.post("/syllabi/{syllabus_id}/approve")
async def approve_syllabus(
    syllabus_id: int,
    notes: str = Query("", description="审批备注"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SyllabusResponse:
    """审批通过教学大纲 - 需求3验收标准3."""
    # 权限检查：只有管理员可以审批大纲
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审批大纲",
        )

    try:
        syllabus_service = SyllabusService()

        # 执行审批
        result = await syllabus_service.approve_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            approver_id=current_user.id,
        )

        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="大纲不存在或无法审批",
            )

        logger.info(f"管理员 {current_user.id} 审批通过大纲 {syllabus_id}")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"审批大纲失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审批大纲失败",
        ) from e


@router.post("/syllabi/{syllabus_id}/reject")
async def reject_syllabus(
    syllabus_id: int,
    rejection_reason: str = Query(..., description="拒绝原因"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审批拒绝教学大纲 - 需求3验收标准3."""
    # 权限检查：只有管理员可以审批大纲
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审批大纲",
        )

    try:
        syllabus_service = SyllabusService()

        # 获取大纲信息
        syllabus = await syllabus_service.get_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            teacher_id=None,  # 管理员可以查看所有大纲
        )

        if not syllabus:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="大纲不存在",
            )

        # 检查状态
        if syllabus.status != "review":
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"大纲状态为{syllabus.status}，无法拒绝",
            )

        # 执行拒绝操作（将状态改回draft）
        from app.ai.schemas.ai_schemas import SyllabusUpdate

        update_data = SyllabusUpdate(
            status="draft",
            title=None,
            content=None,
            version=None,
            source_materials=None,
        )

        result = await syllabus_service.update_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            update_data=update_data,
            teacher_id=syllabus.teacher_id,
        )

        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="拒绝大纲失败",
            )

        logger.info(f"管理员 {current_user.id} 拒绝大纲 {syllabus_id}，原因: {rejection_reason}")

        return {
            "message": "大纲审批拒绝成功",
            "syllabus_id": syllabus_id,
            "rejection_reason": rejection_reason,
            "status": "draft",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拒绝大纲失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="拒绝大纲失败",
        ) from e


@router.get("/syllabi/{syllabus_id}")
async def get_syllabus_for_review(
    syllabus_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SyllabusResponse:
    """获取大纲详情用于审批 - 需求3验收标准3."""
    # 权限检查：只有管理员可以查看待审批大纲
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看待审批大纲",
        )

    try:
        syllabus_service = SyllabusService()

        # 获取大纲详情（管理员可以查看所有大纲）
        result = await syllabus_service.get_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            teacher_id=None,  # 管理员可以查看所有大纲
        )

        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="大纲不存在",
            )

        logger.info(f"管理员 {current_user.id} 查看大纲 {syllabus_id} 详情")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取大纲详情失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取大纲详情失败",
        ) from e


@router.get("/courses/{course_id}/approval-status")
async def get_course_approval_status(
    course_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取课程审批状态 - 需求3验收标准2,3."""
    # 权限检查：只有管理员可以查看课程审批状态
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看课程审批状态",
        )

    try:
        lifecycle_service = CourseLifecycleService(db)

        # 获取课程状态历史
        status_history = await lifecycle_service.get_course_status_history(course_id)

        # 获取课程基本信息
        course = await lifecycle_service.course_service.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="课程不存在",
            )

        # 获取相关大纲信息
        syllabus_service = SyllabusService()
        syllabi, _ = await syllabus_service.list_syllabi(
            db=db,
            course_id=course_id,
        )

        logger.info(f"管理员 {current_user.id} 查看课程 {course_id} 审批状态")

        return {
            "course_id": course_id,
            "course_name": course.name,
            "current_status": course.status.value,
            "status_history": status_history,
            "syllabi": syllabi,
            "can_approve": course.status.value == "under_review",
            "can_reject": course.status.value == "under_review",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程审批状态失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取课程审批状态失败",
        ) from e


@router.post("/courses/{course_id}/approve")
async def approve_course(
    course_id: int,
    approval_notes: str = Query("", description="审批备注"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审批通过课程 - 需求3验收标准3."""
    # 权限检查：只有管理员可以审批课程
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审批课程",
        )

    try:
        lifecycle_service = CourseLifecycleService(db)

        # 执行课程审批
        result = await lifecycle_service.approve_course(
            course_id=course_id,
            approver_id=current_user.id,
            approval_notes=approval_notes,
        )

        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="课程不存在或无法审批",
            )

        logger.info(f"管理员 {current_user.id} 审批通过课程 {course_id}")

        return {
            "message": "课程审批通过",
            "course_id": course_id,
            "course_name": result.name,
            "new_status": result.status.value,
            "approval_notes": approval_notes,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"审批课程失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审批课程失败",
        ) from e


@router.post("/courses/{course_id}/reject")
async def reject_course(
    course_id: int,
    rejection_reason: str = Query(..., description="拒绝原因"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审批拒绝课程 - 需求3验收标准3."""
    # 权限检查：只有管理员可以审批课程
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审批课程",
        )

    try:
        lifecycle_service = CourseLifecycleService(db)

        # 执行课程拒绝
        result = await lifecycle_service.reject_course(
            course_id=course_id,
            reviewer_id=current_user.id,
            rejection_reason=rejection_reason,
        )

        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="课程不存在或无法拒绝",
            )

        logger.info(f"管理员 {current_user.id} 拒绝课程 {course_id}，原因: {rejection_reason}")

        return {
            "message": "课程审批拒绝",
            "course_id": course_id,
            "course_name": result.name,
            "new_status": result.status.value,
            "rejection_reason": rejection_reason,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"拒绝课程失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="拒绝课程失败",
        ) from e
