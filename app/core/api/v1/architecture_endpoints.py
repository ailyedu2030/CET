"""
需求18系统架构API端点
提供双核驱动架构、动态调整机制、权限隔离、数据贯通、标准化对接的API接口
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import get_deepseek_service
from app.core.services.data_integration_service import DataIntegrationService
from app.core.services.dual_core_architecture_service import DualCoreArchitectureService
from app.core.services.dynamic_adjustment_service import DynamicAdjustmentService
from app.core.services.permission_isolation_service import PermissionIsolationService
from app.core.services.standardization_service import StandardizationService
from app.shared.dependencies import get_db_session
from app.shared.services.cache_service import get_cache_service
from app.users.dependencies import get_current_user
from app.users.models.user_models import User
from app.users.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/architecture", tags=["系统架构"])


# ==================== 双核驱动架构API ====================


@router.get("/resource-base")
async def get_teaching_resource_base(
    subject: str | None = None,
    grade: str | None = None,
    use_cache: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """获取教学资源底座数据."""
    try:
        cache_service = await get_cache_service()
        ai_service = get_deepseek_service()

        dual_core_service = DualCoreArchitectureService(db, cache_service, ai_service)

        resource_base = await dual_core_service.get_teaching_resource_base(
            subject=subject,
            grade=grade,
            use_cache=use_cache,
        )

        return {
            "success": True,
            "data": resource_base,
            "message": "成功获取教学资源底座",
        }

    except Exception as e:
        logger.error(f"获取教学资源底座失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取教学资源底座失败: {str(e)}",
        ) from e


@router.post("/resource-base/update")
async def update_resource_base_incremental(
    resource_updates: list[dict[str, Any]],
    hotspot_updates: list[dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """增量更新教学资源底座."""
    try:
        cache_service = await get_cache_service()
        ai_service = get_deepseek_service()

        dual_core_service = DualCoreArchitectureService(db, cache_service, ai_service)

        update_result = await dual_core_service.update_resource_base_incremental(
            resource_updates=resource_updates,
            hotspot_updates=hotspot_updates,
        )

        return {
            "success": True,
            "data": update_result,
            "message": "成功增量更新教学资源底座",
        }

    except Exception as e:
        logger.error(f"增量更新教学资源底座失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"增量更新失败: {str(e)}",
        ) from e


@router.post("/teaching-content/generate")
async def generate_intelligent_teaching_content(
    syllabus_data: dict[str, Any],
    resource_base: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """基于大纲和资源底座生成智能教学内容."""
    try:
        cache_service = await get_cache_service()
        ai_service = get_deepseek_service()

        dual_core_service = DualCoreArchitectureService(db, cache_service, ai_service)

        teaching_content = await dual_core_service.generate_intelligent_teaching_content(
            syllabus_data=syllabus_data,
            resource_base=resource_base,
            user_id=current_user.id,
        )

        return {
            "success": True,
            "data": teaching_content,
            "message": "成功生成智能教学内容",
        }

    except Exception as e:
        logger.error(f"生成智能教学内容失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成智能教学内容失败: {str(e)}",
        ) from e


# ==================== 动态调整机制API ====================


@router.post("/lesson-plan/evolve")
async def evolve_lesson_plan_automatically(
    lesson_plan_id: int,
    student_mastery_data: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """根据学生掌握度自动演进教案内容."""
    try:
        cache_service = await get_cache_service()
        ai_service = get_deepseek_service()

        dynamic_service = DynamicAdjustmentService(db, cache_service, ai_service)

        evolution_result = await dynamic_service.evolve_lesson_plan_automatically(
            lesson_plan_id=lesson_plan_id,
            student_mastery_data=student_mastery_data,
            user_id=current_user.id,
        )

        return {
            "success": True,
            "data": evolution_result,
            "message": "成功自动演进教案内容",
        }

    except Exception as e:
        logger.error(f"教案自动演进失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"教案自动演进失败: {str(e)}",
        ) from e


@router.post("/questions/generate")
async def generate_intelligent_questions(
    teaching_progress: dict[str, Any],
    difficulty_level: str,
    question_count: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """根据教学进度智能匹配生成训练题目."""
    try:
        cache_service = await get_cache_service()
        ai_service = get_deepseek_service()

        dynamic_service = DynamicAdjustmentService(db, cache_service, ai_service)

        questions_result = await dynamic_service.generate_intelligent_questions(
            teaching_progress=teaching_progress,
            difficulty_level=difficulty_level,
            question_count=question_count,
            user_id=current_user.id,
        )

        return {
            "success": True,
            "data": questions_result,
            "message": "成功生成智能题目",
        }

    except Exception as e:
        logger.error(f"智能题目生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能题目生成失败: {str(e)}",
        ) from e


@router.post("/analysis/weekly")
async def weekly_automatic_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """系统每周自动分析数据，提供调整建议."""
    try:
        cache_service = await get_cache_service()
        ai_service = get_deepseek_service()

        dynamic_service = DynamicAdjustmentService(db, cache_service, ai_service)

        analysis_result = await dynamic_service.weekly_automatic_analysis(
            teacher_id=current_user.id,
        )

        return {
            "success": True,
            "data": analysis_result,
            "message": "成功完成每周自动分析",
        }

    except Exception as e:
        logger.error(f"每周自动分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"每周自动分析失败: {str(e)}",
        ) from e


# ==================== 权限隔离API ====================


@router.get("/permission/check/teacher/lesson-plan")
async def check_teacher_lesson_plan_permission(
    lesson_plan_id: int,
    action: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """检查教师教案权限."""
    try:
        cache_service = await get_cache_service()
        permission_service = PermissionService(db)

        isolation_service = PermissionIsolationService(db, cache_service, permission_service)

        has_permission = await isolation_service.check_teacher_lesson_plan_permission(
            user_id=current_user.id,
            lesson_plan_id=lesson_plan_id,
            action=action,
        )

        return {
            "success": True,
            "data": {"has_permission": has_permission},
            "message": "权限检查完成",
        }

    except Exception as e:
        logger.error(f"教师教案权限检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"权限检查失败: {str(e)}",
        ) from e


@router.post("/permission/request")
async def request_temporary_permission(
    permission_code: str,
    resource_id: int,
    reason: str,
    duration_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """申请临时特殊权限."""
    try:
        cache_service = await get_cache_service()
        permission_service = PermissionService(db)

        isolation_service = PermissionIsolationService(db, cache_service, permission_service)

        request_result = await isolation_service.request_temporary_permission(
            user_id=current_user.id,
            permission_code=permission_code,
            resource_id=resource_id,
            reason=reason,
            duration_hours=duration_hours,
        )

        return {
            "success": True,
            "data": request_result,
            "message": "权限申请提交成功",
        }

    except Exception as e:
        logger.error(f"申请临时权限失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申请临时权限失败: {str(e)}",
        ) from e


# ==================== 数据贯通API ====================


@router.post("/knowledge/integrate")
async def integrate_knowledge_points(
    teaching_design_data: dict[str, Any],
    error_analysis_data: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """知识点库贯通，同时支撑教学设计和错题分析."""
    try:
        cache_service = await get_cache_service()

        integration_service = DataIntegrationService(db, cache_service)

        integration_result = await integration_service.integrate_knowledge_points(
            teaching_design_data=teaching_design_data,
            error_analysis_data=error_analysis_data,
        )

        return {
            "success": True,
            "data": integration_result,
            "message": "成功完成知识点库贯通",
        }

    except Exception as e:
        logger.error(f"知识点库贯通失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识点库贯通失败: {str(e)}",
        ) from e


# ==================== 标准化对接API ====================


@router.post("/textbook/validate-isbn")
async def validate_textbook_isbn(
    isbn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """验证教材ISBN规范."""
    try:
        cache_service = await get_cache_service()

        standardization_service = StandardizationService(db, cache_service)

        validation_result = await standardization_service.validate_textbook_isbn(isbn=isbn)

        return {
            "success": True,
            "data": validation_result,
            "message": "ISBN验证完成",
        }

    except Exception as e:
        logger.error(f"ISBN验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ISBN验证失败: {str(e)}",
        ) from e


@router.post("/writing/score")
async def standardize_writing_score(
    writing_content: str,
    scoring_criteria: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """标准化写作评分，对接CET-4标准."""
    try:
        cache_service = await get_cache_service()

        standardization_service = StandardizationService(db, cache_service)

        scoring_result = await standardization_service.standardize_writing_score(
            writing_content=writing_content,
            scoring_criteria=scoring_criteria,
        )

        return {
            "success": True,
            "data": scoring_result,
            "message": "写作评分完成",
        }

    except Exception as e:
        logger.error(f"写作评分失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写作评分失败: {str(e)}",
        ) from e
