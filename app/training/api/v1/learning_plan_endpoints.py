"""学习计划管理API端点."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.training.schemas.learning_plan_schemas import (
    DifficultyAdjustmentResponse,
    GoalAchievementResponse,
    GoalCreateRequest,
    GoalProgressTrackingResponse,
    GoalProgressUpdateRequest,
    GoalResponse,
    GoalSuggestionResponse,
    LearningPlanConfigRequest,
    LearningPlanResponse,
    LearningStatisticsResponse,
    ProgressAlertResponse,
    ProgressMonitoringResponse,
    ProgressSummaryResponse,
    RealTimeProgressResponse,
)
from app.training.services.goal_setting_service import GoalSettingService
from app.training.services.learning_plan_service import LearningPlanService
from app.training.services.progress_monitoring_service import ProgressMonitoringService
from app.users.models.user_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-plan", tags=["学习计划管理"])


# ==================== 学习计划管理 ====================


@router.post("/generate", response_model=LearningPlanResponse)
async def generate_learning_plan(
    config: LearningPlanConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """生成个性化学习计划."""
    try:
        service = LearningPlanService(db)

        # 转换配置为字典
        plan_config = config.model_dump()

        # 生成学习计划
        plan_result = await service.generate_learning_plan(
            student_id=current_user.id, plan_config=plan_config
        )

        return LearningPlanResponse(**plan_result)

    except Exception as e:
        logger.error(f"生成学习计划失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成学习计划失败: {str(e)}",
        ) from e


@router.get("/current", response_model=LearningPlanResponse)
async def get_current_learning_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """获取当前学习计划."""
    try:
        service = LearningPlanService(db)

        plan_result = await service.get_learning_plan(student_id=current_user.id)

        if plan_result.get("status") == "no_plan":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到学习计划")

        return LearningPlanResponse(**plan_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习计划失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习计划失败: {str(e)}",
        ) from e


@router.put("/{plan_id}", response_model=LearningPlanResponse)
async def update_learning_plan(
    plan_id: int,
    updates: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """更新学习计划."""
    try:
        service = LearningPlanService(db)

        plan_result = await service.update_learning_plan(
            student_id=current_user.id, plan_id=plan_id, updates=updates
        )

        return LearningPlanResponse(**plan_result)

    except Exception as e:
        logger.error(f"更新学习计划失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新学习计划失败: {str(e)}",
        ) from e


@router.post("/{plan_id}/adjust-difficulty", response_model=DifficultyAdjustmentResponse)
async def adjust_plan_difficulty(
    plan_id: int,
    performance_data: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DifficultyAdjustmentResponse:
    """调整计划难度."""
    try:
        service = LearningPlanService(db)

        adjustment_result = await service.adjust_plan_difficulty(
            student_id=current_user.id,
            plan_id=plan_id,
            performance_data=performance_data,
        )

        return DifficultyAdjustmentResponse(**adjustment_result)

    except Exception as e:
        logger.error(f"调整计划难度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调整计划难度失败: {str(e)}",
        ) from e


@router.get("/statistics", response_model=LearningStatisticsResponse)
async def get_plan_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningStatisticsResponse:
    """获取学习计划统计."""
    try:
        service = LearningPlanService(db)

        stats_result = await service.get_plan_statistics(student_id=current_user.id, days=days)

        return LearningStatisticsResponse(**stats_result)

    except Exception as e:
        logger.error(f"获取计划统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取计划统计失败: {str(e)}",
        ) from e


# ==================== 目标设定管理 ====================


@router.post("/goals", response_model=GoalResponse)
async def create_learning_goal(
    goal_data: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalResponse:
    """创建学习目标."""
    try:
        service = GoalSettingService(db)

        goal_result = await service.create_learning_goal(
            student_id=current_user.id, goal_data=goal_data.model_dump()
        )

        return GoalResponse(**goal_result)

    except Exception as e:
        logger.error(f"创建学习目标失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建学习目标失败: {str(e)}",
        ) from e


@router.get("/goals", response_model=list[GoalResponse])
async def get_student_goals(
    goal_status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalResponse]:
    """获取学生目标列表."""
    try:
        service = GoalSettingService(db)

        goals = await service.get_student_goals(student_id=current_user.id, status=goal_status)

        return [GoalResponse(**goal) for goal in goals]

    except Exception as e:
        logger.error(f"获取学生目标失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学生目标失败: {str(e)}",
        ) from e


@router.put("/goals/{goal_id}/progress", response_model=dict[str, Any])
async def update_goal_progress(
    goal_id: int,
    progress_update: GoalProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新目标进度."""
    try:
        service = GoalSettingService(db)

        update_result = await service.update_goal_progress(
            goal_id=goal_id, progress_data=progress_update.model_dump()
        )

        return update_result

    except Exception as e:
        logger.error(f"更新目标进度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新目标进度失败: {str(e)}",
        ) from e


@router.get("/goals/suggestions", response_model=list[GoalSuggestionResponse])
async def get_goal_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalSuggestionResponse]:
    """获取目标建议."""
    try:
        service = GoalSettingService(db)

        suggestions = await service.suggest_goals(student_id=current_user.id)

        return [GoalSuggestionResponse(**suggestion) for suggestion in suggestions]

    except Exception as e:
        logger.error(f"获取目标建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目标建议失败: {str(e)}",
        ) from e


@router.post("/goals/{goal_id}/evaluate", response_model=GoalAchievementResponse)
async def evaluate_goal_achievement(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalAchievementResponse:
    """评估目标达成情况."""
    try:
        service = GoalSettingService(db)

        evaluation_result = await service.evaluate_goal_achievement(goal_id=goal_id)

        return GoalAchievementResponse(**evaluation_result)

    except Exception as e:
        logger.error(f"评估目标达成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"评估目标达成失败: {str(e)}",
        ) from e


# ==================== 进度监控 ====================


@router.get("/progress/monitor", response_model=ProgressMonitoringResponse)
async def monitor_student_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgressMonitoringResponse:
    """监控学生学习进度."""
    try:
        service = ProgressMonitoringService(db)

        monitoring_result = await service.monitor_student_progress(student_id=current_user.id)

        return ProgressMonitoringResponse(**monitoring_result)

    except Exception as e:
        logger.error(f"监控学生进度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"监控学生进度失败: {str(e)}",
        ) from e


@router.get("/progress/realtime", response_model=RealTimeProgressResponse)
async def get_realtime_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RealTimeProgressResponse:
    """获取实时学习进度."""
    try:
        service = ProgressMonitoringService(db)

        realtime_result = await service.get_real_time_progress(student_id=current_user.id)

        return RealTimeProgressResponse(**realtime_result)

    except Exception as e:
        logger.error(f"获取实时进度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实时进度失败: {str(e)}",
        ) from e


@router.get("/progress/goals/{goal_id}", response_model=GoalProgressTrackingResponse)
async def track_goal_progress(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalProgressTrackingResponse:
    """跟踪目标进度."""
    try:
        service = ProgressMonitoringService(db)

        tracking_result = await service.track_goal_progress(
            student_id=current_user.id, goal_id=goal_id
        )

        return GoalProgressTrackingResponse(**tracking_result)

    except Exception as e:
        logger.error(f"跟踪目标进度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"跟踪目标进度失败: {str(e)}",
        ) from e


@router.get("/progress/alerts", response_model=list[ProgressAlertResponse])
async def get_progress_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProgressAlertResponse]:
    """获取进度预警."""
    try:
        service = ProgressMonitoringService(db)

        alerts = await service.generate_progress_alerts(student_id=current_user.id)

        return [ProgressAlertResponse(**alert) for alert in alerts]

    except Exception as e:
        logger.error(f"获取进度预警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取进度预警失败: {str(e)}",
        ) from e


@router.get("/progress/summary", response_model=ProgressSummaryResponse)
async def get_progress_summary(
    period_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgressSummaryResponse:
    """获取进度总结."""
    try:
        service = ProgressMonitoringService(db)

        summary_result = await service.get_progress_summary(
            student_id=current_user.id, period_days=period_days
        )

        return ProgressSummaryResponse(**summary_result)

    except Exception as e:
        logger.error(f"获取进度总结失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取进度总结失败: {str(e)}",
        ) from e
