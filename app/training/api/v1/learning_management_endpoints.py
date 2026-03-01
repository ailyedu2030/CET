"""学习计划与管理系统 - API端点"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.models.learning_plan_models import PlanStatus, TaskStatus
from app.training.schemas.learning_management_schemas import (
    LearningDashboard,
    LearningPlanCreate,
    LearningPlanListResponse,
    LearningPlanResponse,
    LearningPlanUpdate,
    LearningProgressCreate,
    LearningProgressListResponse,
    LearningProgressResponse,
    LearningReportCreate,
    LearningReportResponse,
    LearningStatistics,
    LearningTaskCreate,
    LearningTaskListResponse,
    LearningTaskResponse,
    LearningTaskUpdate,
)
from app.training.services.learning_management_service import LearningManagementService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["学习计划与管理系统"])


# ==================== 学习仪表板 ====================


@router.get("/dashboard", summary="获取学习仪表板", response_model=LearningDashboard)
async def get_learning_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningDashboard:
    """获取学习仪表板数据"""
    try:
        service = LearningManagementService(db)
        dashboard = await service.get_dashboard(current_user.id)

        logger.info(f"用户 {current_user.id} 获取学习仪表板")

        return dashboard
    except Exception as e:
        logger.error(f"获取学习仪表板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取仪表板失败"
        ) from e


@router.get("/statistics", summary="获取学习统计数据", response_model=LearningStatistics)
async def get_learning_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningStatistics:
    """获取用户学习统计数据"""
    try:
        service = LearningManagementService(db)
        statistics = await service.get_user_statistics(current_user.id)

        logger.info(f"用户 {current_user.id} 查询学习统计")

        return statistics
    except Exception as e:
        logger.error(f"查询学习统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


# ==================== 学习计划管理 ====================


@router.get("/plans", summary="获取学习计划列表", response_model=LearningPlanListResponse)
async def get_learning_plans(
    skip: int = 0,
    limit: int = 10,
    plan_status: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanListResponse:
    """获取用户的学习计划列表"""
    try:
        service = LearningManagementService(db)
        plans, total = await service.get_user_plans(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=PlanStatus(plan_status) if plan_status else None,
        )

        logger.info(f"用户 {current_user.id} 查询学习计划列表，共 {total} 个")

        return LearningPlanListResponse(
            success=True,
            data=[LearningPlanResponse.model_validate(p) for p in plans],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询学习计划列表失败: {e}")
        from fastapi import status as http_status

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/plans", summary="创建学习计划", response_model=LearningPlanResponse)
async def create_learning_plan(
    data: LearningPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """创建学习计划"""
    try:
        service = LearningManagementService(db)
        plan = await service.create_plan(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建学习计划成功: {plan.id}")  # type: ignore[has-type]

        return LearningPlanResponse.model_validate(plan)
    except Exception as e:
        logger.error(f"创建学习计划失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get("/plans/{plan_id}", summary="获取学习计划详情", response_model=LearningPlanResponse)
async def get_learning_plan_detail(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """获取学习计划详情"""
    try:
        service = LearningManagementService(db)
        plan = await service.get_plan(plan_id, current_user.id)

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="计划不存在")

        logger.info(f"用户 {current_user.id} 查询学习计划详情: {plan_id}")

        return LearningPlanResponse.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询学习计划详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put("/plans/{plan_id}", summary="更新学习计划", response_model=LearningPlanResponse)
async def update_learning_plan(
    plan_id: int,
    data: LearningPlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """更新学习计划"""
    try:
        service = LearningManagementService(db)
        plan = await service.update_plan(plan_id, current_user.id, data)

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="计划不存在")

        logger.info(f"用户 {current_user.id} 更新学习计划: {plan_id}")

        return LearningPlanResponse.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学习计划失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


@router.delete("/plans/{plan_id}", summary="删除学习计划")
async def delete_learning_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除学习计划"""
    try:
        service = LearningManagementService(db)
        success = await service.delete_plan(plan_id, current_user.id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="计划不存在")

        logger.info(f"用户 {current_user.id} 删除学习计划: {plan_id}")

        return {
            "success": True,
            "message": "删除成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除学习计划失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除失败"
        ) from e


# ==================== 学习任务管理 ====================


@router.get("/tasks", summary="获取学习任务列表", response_model=LearningTaskListResponse)
async def get_learning_tasks(
    skip: int = 0,
    limit: int = 10,
    plan_id: int | None = None,
    task_status: str | None = None,
    date_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningTaskListResponse:
    """获取用户的学习任务列表"""
    try:
        service = LearningManagementService(db)
        tasks, total = await service.get_user_tasks(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            plan_id=plan_id,
            status=TaskStatus(task_status) if task_status else None,
            date_filter=date_filter,
        )

        logger.info(f"用户 {current_user.id} 查询学习任务列表，共 {total} 个")

        return LearningTaskListResponse(
            success=True,
            data=[LearningTaskResponse.model_validate(t) for t in tasks],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询学习任务列表失败: {e}")
        from fastapi import status as http_status

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/tasks", summary="创建学习任务", response_model=LearningTaskResponse)
async def create_learning_task(
    data: LearningTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningTaskResponse:
    """创建学习任务"""
    try:
        service = LearningManagementService(db)
        task = await service.create_task(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建学习任务成功: {task.id}")  # type: ignore[has-type]

        return LearningTaskResponse.model_validate(task)
    except Exception as e:
        logger.error(f"创建学习任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.put("/tasks/{task_id}", summary="更新学习任务", response_model=LearningTaskResponse)
async def update_learning_task(
    task_id: int,
    data: LearningTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningTaskResponse:
    """更新学习任务"""
    try:
        service = LearningManagementService(db)
        task = await service.update_task(task_id, current_user.id, data)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        logger.info(f"用户 {current_user.id} 更新学习任务: {task_id}")

        return LearningTaskResponse.model_validate(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学习任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


@router.delete("/tasks/{task_id}", summary="删除学习任务")
async def delete_learning_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除学习任务"""
    try:
        service = LearningManagementService(db)
        success = await service.delete_task(task_id, current_user.id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        logger.info(f"用户 {current_user.id} 删除学习任务: {task_id}")

        return {
            "success": True,
            "message": "删除成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除学习任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除失败"
        ) from e


# ==================== 学习进度管理 ====================


@router.post("/progress", summary="记录学习进度", response_model=LearningProgressResponse)
async def record_learning_progress(
    data: LearningProgressCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningProgressResponse:
    """记录学习进度"""
    try:
        service = LearningManagementService(db)
        progress = await service.record_progress(current_user.id, data)

        logger.info(f"用户 {current_user.id} 记录学习进度成功: {progress.id}")  # type: ignore[has-type]

        return LearningProgressResponse.model_validate(progress)
    except Exception as e:
        logger.error(f"记录学习进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="记录失败"
        ) from e


@router.get(
    "/progress", summary="获取学习进度列表", response_model=LearningProgressListResponse
)
async def get_learning_progress(
    skip: int = 0,
    limit: int = 10,
    plan_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningProgressListResponse:
    """获取用户的学习进度记录"""
    try:
        service = LearningManagementService(db)
        progress_records, total = await service.get_user_progress(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            plan_id=plan_id,
        )

        logger.info(f"用户 {current_user.id} 查询学习进度记录，共 {total} 条")

        return LearningProgressListResponse(
            success=True,
            data=[LearningProgressResponse.model_validate(p) for p in progress_records],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询学习进度记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


# ==================== 学习报告管理 ====================


@router.post("/reports", summary="创建学习报告", response_model=LearningReportResponse)
async def create_learning_report(
    data: LearningReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningReportResponse:
    """创建学习报告"""
    try:
        service = LearningManagementService(db)
        report = await service.create_report(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建学习报告成功: {report.id}")  # type: ignore[has-type]

        return LearningReportResponse.model_validate(report)
    except Exception as e:
        logger.error(f"创建学习报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


# ==================== 学习数据导出 ====================


@router.get("/export/data", summary="导出学习数据")
async def export_learning_data(
    format: str = "excel",  # excel, csv, pdf
    date_range: str | None = None,  # 7d, 30d, 90d, all
    include_details: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """导出学习数据报告"""
    try:
        service = LearningManagementService(db)

        # 获取用户学习数据
        export_data = await service.export_user_data(
            user_id=current_user.id,
            format=format,
            date_range=date_range,
            include_details=include_details,
        )

        logger.info(f"用户 {current_user.id} 导出学习数据，格式: {format}")

        return {
            "success": True,
            "download_url": export_data.get("download_url"),
            "file_name": export_data.get("file_name"),
            "file_size": export_data.get("file_size"),
            "generated_at": export_data.get("generated_at"),
        }
    except Exception as e:
        logger.error(f"导出学习数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="导出失败"
        ) from e


# ==================== 学习提醒管理 ====================


@router.get("/reminders", summary="获取学习提醒列表")
async def get_learning_reminders(
    skip: int = 0,
    limit: int = 10,
    reminder_type: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取用户的学习提醒列表"""
    try:
        service = LearningManagementService(db)
        reminders, total = await service.get_user_reminders(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            reminder_type=reminder_type,
        )

        logger.info(f"用户 {current_user.id} 查询学习提醒列表，共 {total} 个")

        return {
            "success": True,
            "data": reminders,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"查询学习提醒列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/reminders", summary="创建学习提醒")
async def create_learning_reminder(
    data: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建学习提醒"""
    try:
        service = LearningManagementService(db)
        reminder = await service.create_reminder(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建学习提醒成功")

        return {
            "success": True,
            "data": reminder,
        }
    except Exception as e:
        logger.error(f"创建学习提醒失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.put("/reminders/{reminder_id}", summary="更新学习提醒")
async def update_learning_reminder(
    reminder_id: int,
    data: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新学习提醒"""
    try:
        service = LearningManagementService(db)
        reminder = await service.update_reminder(reminder_id, current_user.id, data)

        if not reminder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提醒不存在")

        logger.info(f"用户 {current_user.id} 更新学习提醒: {reminder_id}")

        return {
            "success": True,
            "data": reminder,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学习提醒失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


@router.delete("/reminders/{reminder_id}", summary="删除学习提醒")
async def delete_learning_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除学习提醒"""
    try:
        service = LearningManagementService(db)
        success = await service.delete_reminder(reminder_id, current_user.id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提醒不存在")

        logger.info(f"用户 {current_user.id} 删除学习提醒: {reminder_id}")

        return {
            "success": True,
            "message": "删除成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除学习提醒失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除失败"
        ) from e


# ==================== 课程表查看 ====================


@router.get("/schedule", summary="获取课程表")
async def get_learning_schedule(
    week_offset: int = 0,  # 周偏移量，0为当前周，1为下周，-1为上周
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取用户的课程表"""
    try:
        service = LearningManagementService(db)
        schedule = await service.get_user_schedule(
            user_id=current_user.id,
            week_offset=week_offset,
        )

        logger.info(f"用户 {current_user.id} 查询课程表，周偏移: {week_offset}")

        return {
            "success": True,
            "data": schedule,
        }
    except Exception as e:
        logger.error(f"查询课程表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e
