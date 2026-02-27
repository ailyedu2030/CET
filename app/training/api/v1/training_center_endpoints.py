"""学生综合训练中心 - API端点"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.schemas.training_center_schemas import (
    TrainingCenterCreate,
    TrainingCenterDashboard,
    TrainingCenterListResponse,
    TrainingCenterResponse,
    TrainingCenterUpdate,
)
from app.training.services.training_center_service import TrainingCenterService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["学生综合训练中心"])


# ==================== 训练中心管理 ====================


@router.get("/", summary="获取学生综合训练中心列表", response_model=TrainingCenterListResponse)
async def get_training_centers(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingCenterListResponse:
    """获取学生综合训练中心列表"""
    try:
        service = TrainingCenterService(db)
        training_centers, total = await service.get_training_centers(current_user.id, skip, limit)

        logger.info(f"用户 {current_user.id} 查询训练中心列表，共 {total} 个")

        return TrainingCenterListResponse(
            success=True,
            data=[TrainingCenterResponse.model_validate(tc) for tc in training_centers],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询训练中心列表失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败") from e


@router.post("/", summary="创建学生综合训练中心", response_model=TrainingCenterResponse)
async def create_training_center(
    data: TrainingCenterCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingCenterResponse:
    """创建学生综合训练中心"""
    try:
        service = TrainingCenterService(db)
        training_center = await service.create_training_center(current_user.id, data.model_dump())

        logger.info(f"用户 {current_user.id} 创建训练中心成功: {training_center['id']}")

        return TrainingCenterResponse.model_validate(training_center)
    except Exception as e:
        logger.error(f"创建训练中心失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败") from e


@router.get("/{center_id}", summary="获取学生综合训练中心详情", response_model=TrainingCenterResponse)
async def get_training_center_detail(
    center_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingCenterResponse:
    """获取学生综合训练中心详情"""
    try:
        service = TrainingCenterService(db)
        training_center = await service.get_training_center(current_user.id, center_id)

        if not training_center:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练中心不存在")

        logger.info(f"用户 {current_user.id} 查询训练中心详情: {center_id}")

        return TrainingCenterResponse.model_validate(training_center)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询训练中心详情失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败") from e


@router.put("/{center_id}", summary="更新学生综合训练中心", response_model=TrainingCenterResponse)
async def update_training_center(
    center_id: int,
    data: TrainingCenterUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingCenterResponse:
    """更新学生综合训练中心"""
    try:
        service = TrainingCenterService(db)
        training_center = await service.update_training_center(
            center_id, current_user.id, data.model_dump()
        )

        if not training_center:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练中心不存在")

        logger.info(f"用户 {current_user.id} 更新训练中心: {center_id}")

        return TrainingCenterResponse.model_validate(training_center)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新训练中心失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败") from e


@router.get("/{center_id}/dashboard", summary="获取训练中心仪表板", response_model=TrainingCenterDashboard)
async def get_training_center_dashboard(
    center_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingCenterDashboard:
    """获取训练中心仪表板"""
    try:
        service = TrainingCenterService(db)
        dashboard = await service.get_training_center_dashboard(center_id, current_user.id)


        logger.info(f"用户 {current_user.id} 查询训练中心仪表板: {center_id}")

        return TrainingCenterDashboard.model_validate(dashboard)
    except Exception as e:
        logger.error(f"查询训练中心仪表板失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败") from e


# ==================== 训练会话管理 ====================


@router.post("/{center_id}/sessions", summary="开始训练会话")
async def start_training_session(
    center_id: int,
    data: dict[str, str],  # 简化的训练模式选择
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """开始训练会话"""
    try:
        service = TrainingCenterService(db)

        # 模拟创建训练会话
        session_data = {"center_id": center_id, **data}
        session_result = await service.create_training_session_simple(current_user.id, session_data)
        session_id = session_result.get("id", 999)

        logger.info(f"用户 {current_user.id} 开始训练会话: {session_id}")

        return {"success": True, "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"开始训练会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="开始训练失败"
        ) from e


@router.put("/sessions/{session_id}", summary="提交训练答案")
async def submit_training_answers(
    session_id: int,
    data: dict[str, str],  # 简化的答案数据
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """提交训练答案"""
    try:
        service = TrainingCenterService(db)
        answer_data = {"session_id": session_id, **data}
        await service.submit_answers_simple(current_user.id, answer_data)

        logger.info(f"用户 {current_user.id} 提交训练答案: {session_id}")

        return {"success": True, "submitted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交训练答案失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交失败") from e


# ==================== 统计和推荐 ====================


@router.get("/{center_id}/statistics", summary="获取训练统计数据")
async def get_training_statistics(
    center_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, dict[str, int]]:
    """获取训练统计数据"""
    try:
        service = TrainingCenterService(db)
        stats = await service.get_training_statistics(center_id, current_user.id)

        logger.info(f"用户 {current_user.id} 查询训练统计: {center_id}")

        return {"data": stats}
    except Exception as e:
        logger.error(f"查询训练统计失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败") from e


@router.get("/{center_id}/recommendations", summary="获取个性化训练推荐")
async def get_training_recommendations(
    center_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, dict[str, str]]:
    """获取个性化训练推荐"""
    try:
        service = TrainingCenterService(db)
        recommendations = await service.get_personalized_recommendations(center_id, current_user.id)

        logger.info(f"用户 {current_user.id} 获取训练推荐: {center_id}")

        return {"data": recommendations}
    except Exception as e:
        logger.error(f"获取训练推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取推荐失败"
        ) from e


# ==================== 训练目标管理 ====================


@router.post("/{center_id}/goals", summary="创建训练目标")
async def create_training_goal(
    center_id: int,
    data: dict[str, str],  # 简化的目标数据
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """创建训练目标"""
    try:
        service = TrainingCenterService(db)
        goal_data = {"center_id": center_id, **data}
        goal_result = await service.create_goal_simple(current_user.id, goal_data)
        goal_id = goal_result.get("id", 999)

        logger.info(f"用户 {current_user.id} 创建训练目标: {goal_id}")

        return {"goal_id": goal_id}
    except Exception as e:
        logger.error(f"创建训练目标失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败") from e


@router.get("/{center_id}/goals", summary="获取训练目标列表")
async def get_training_goals(
    center_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[dict[str, str]]]:
    """获取训练目标列表"""
    try:
        service = TrainingCenterService(db)
        goals = await service.get_goals_simple(center_id, current_user.id)

        logger.info(f"用户 {current_user.id} 查询训练目标: {center_id}")

        return {"data": goals.get("goals", [])}
    except Exception as e:
        logger.error(f"查询训练目标失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败") from e
