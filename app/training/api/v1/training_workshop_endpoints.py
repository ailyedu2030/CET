"""智能训练工坊API端点 - 需求15实现."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import UserType
from app.training.schemas.training_workshop_schemas import (
    TrainingParameterTemplateListResponse,
    TrainingParameterTemplateRequest,
    TrainingParameterTemplateResponse,
    TrainingTaskListResponse,
    TrainingTaskRequest,
    TrainingTaskResponse,
    TrainingWorkshopResponse,
    WeeklyTrainingRequest,
)
from app.training.services.analytics_service import AnalyticsService
from app.training.services.training_workshop_service import TrainingWorkshopService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

router = APIRouter(prefix="/training-workshop", tags=["智能训练工坊"])


# ==================== 权限检查辅助函数 ====================


def check_teacher_permission(current_user: User, class_id: int | None = None) -> None:
    """检查教师权限."""
    if current_user.user_type == UserType.ADMIN:
        return  # 管理员有所有权限

    if current_user.user_type != UserType.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以执行此操作",
        )

    # TODO: 这里可以添加更细粒度的班级权限检查
    # 检查教师是否有权限访问指定班级


def check_template_ownership(current_user: User, template_creator_id: int) -> None:
    """检查模板所有权."""
    if current_user.user_type == UserType.ADMIN:
        return  # 管理员可以访问所有模板

    if current_user.id != template_creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能操作自己创建的模板",
        )


# ==================== 训练参数模板管理 ====================


@router.post(
    "/parameter-templates",
    response_model=TrainingParameterTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建训练参数模板",
    description="教师创建训练参数模板，支持保存常用配置 - 需求15验收标准2",
)
async def create_parameter_template(
    template_data: TrainingParameterTemplateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingParameterTemplateResponse:
    """创建训练参数模板 - 需求15任务3.3权限控制."""
    # 权限检查：只有教师和管理员可以创建模板
    check_teacher_permission(current_user)

    try:
        service = TrainingWorkshopService(db)
        return await service.create_parameter_template(current_user.id, template_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建训练参数模板失败: {str(e)}",
        ) from e


@router.get(
    "/parameter-templates",
    response_model=TrainingParameterTemplateListResponse,
    summary="获取训练参数模板列表",
    description="获取教师的训练参数模板列表，支持分页 - 需求15验收标准2",
)
async def get_parameter_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingParameterTemplateListResponse:
    """获取训练参数模板列表 - 需求15任务3.3权限控制."""
    # 权限检查：只有教师和管理员可以访问模板
    check_teacher_permission(current_user)

    try:
        service = TrainingWorkshopService(db)
        result = await service.get_parameter_templates(current_user.id, page, page_size)
        return TrainingParameterTemplateListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练参数模板失败: {str(e)}",
        ) from e


@router.put(
    "/parameter-templates/{template_id}",
    response_model=TrainingParameterTemplateResponse,
    summary="更新训练参数模板",
    description="更新指定的训练参数模板 - 需求15验收标准2",
)
async def update_parameter_template(
    template_id: int,
    template_data: TrainingParameterTemplateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingParameterTemplateResponse:
    """更新训练参数模板."""
    if current_user.user_type.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以更新训练参数模板",
        )

    try:
        service = TrainingWorkshopService(db)
        return await service.update_parameter_template(template_id, current_user.id, template_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新训练参数模板失败: {str(e)}",
        ) from e


@router.delete(
    "/parameter-templates/{template_id}",
    response_model=TrainingWorkshopResponse,
    summary="删除训练参数模板",
    description="删除指定的训练参数模板 - 需求15验收标准2",
)
async def delete_parameter_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingWorkshopResponse:
    """删除训练参数模板."""
    if current_user.user_type.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以删除训练参数模板",
        )

    try:
        service = TrainingWorkshopService(db)
        success = await service.delete_parameter_template(template_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="训练参数模板不存在或无权限访问",
            )

        return TrainingWorkshopResponse(
            success=True,
            message="训练参数模板删除成功",
            data=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除训练参数模板失败: {str(e)}",
        ) from e


# ==================== 训练任务管理 ====================


@router.post(
    "/training-tasks",
    response_model=TrainingTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建训练任务",
    description="教师创建训练任务，支持即时发布和定时发布 - 需求15验收标准4",
)
async def create_training_task(
    task_data: TrainingTaskRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingTaskResponse:
    """创建训练任务."""
    if current_user.user_type.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以创建训练任务",
        )

    try:
        service = TrainingWorkshopService(db)
        return await service.create_training_task(current_user.id, task_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建训练任务失败: {str(e)}",
        ) from e


@router.get(
    "/training-tasks",
    response_model=TrainingTaskListResponse,
    summary="获取训练任务列表",
    description="获取教师的训练任务列表，支持按班级筛选 - 需求15验收标准4",
)
async def get_training_tasks(
    class_id: int | None = Query(None, description="班级ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingTaskListResponse:
    """获取训练任务列表."""
    if current_user.user_type.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以访问训练任务",
        )

    try:
        service = TrainingWorkshopService(db)
        result = await service.get_training_tasks(current_user.id, class_id, page, page_size)
        return TrainingTaskListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练任务失败: {str(e)}",
        ) from e


# ==================== 周训练配置 ====================


@router.post(
    "/weekly-training",
    response_model=TrainingTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建周训练配置",
    description="教师创建周训练配置，支持阅读理解和写作专项配置 - 需求15验收标准3",
)
async def create_weekly_training(
    weekly_data: WeeklyTrainingRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingTaskResponse:
    """创建周训练配置."""
    if current_user.user_type.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以创建周训练配置",
        )

    try:
        service = TrainingWorkshopService(db)
        return await service.create_weekly_training(current_user.id, weekly_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建周训练配置失败: {str(e)}",
        ) from e


# ==================== 训练数据分析 ====================


@router.get(
    "/analytics/class/{class_id}",
    response_model=dict[str, Any],
    summary="获取班级训练数据分析",
    description="获取指定班级的训练数据分析报告 - 需求15验收标准2",
)
async def get_class_training_analytics(
    class_id: int,
    start_date: str | None = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取班级训练数据分析 - 需求15任务3.3权限控制."""
    # 权限检查：只有教师和管理员可以查看数据分析
    check_teacher_permission(current_user, class_id)

    try:
        workshop_service = TrainingWorkshopService(db)
        _analytics_service = AnalyticsService(db)

        # 获取班级训练任务统计
        task_stats = await workshop_service.get_class_task_statistics(
            class_id, start_date, end_date
        )

        # 获取学生表现分析
        student_performance = await workshop_service.get_class_student_performance(
            class_id, start_date, end_date
        )

        # 获取风险学生识别
        risk_students = await workshop_service.identify_risk_students(class_id)

        # 获取训练效果分析
        effectiveness_analysis = await workshop_service.get_training_effectiveness(
            class_id, start_date, end_date
        )

        return {
            "class_id": class_id,
            "analysis_period": (
                f"{start_date} 至 {end_date}" if start_date and end_date else "全部时间"
            ),
            "task_statistics": task_stats,
            "student_performance": student_performance,
            "risk_students": risk_students,
            "effectiveness_analysis": effectiveness_analysis,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练数据分析失败: {str(e)}",
        ) from e
