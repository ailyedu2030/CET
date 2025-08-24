"""自适应学习API端点 - 错题强化与自适应学习接口."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.schemas.adaptive_learning_schemas import (
    ErrorAnalysisResponse,
    ForgettingCurveResponse,
    KnowledgeGapResponse,
    LearningStrategyResponse,
    ReinforcementPlanResponse,
    ReviewScheduleResponse,
)
from app.training.services.error_analysis_service import ErrorAnalysisService
from app.training.services.forgetting_curve_service import ForgettingCurveService
from app.training.utils.knowledge_graph import KnowledgeGraph
from app.training.utils.learning_algorithm import LearningAlgorithm
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/adaptive-learning", tags=["自适应学习"])


# ==================== 错题分析端点 ====================


@router.get(
    "/error-analysis/{student_id}",
    response_model=ErrorAnalysisResponse,
    summary="获取学生错题分析",
    description="分析学生的错题模式，识别薄弱环节和改进建议",
)
async def get_error_analysis(
    student_id: int,
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ErrorAnalysisResponse:
    """获取学生错题分析."""
    try:
        # 权限检查：只能查看自己的数据或教师查看学生数据
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该学生的错题分析",
            )

        error_service = ErrorAnalysisService(db)
        analysis_result = await error_service.analyze_error_patterns(student_id, days)

        # 转换为ErrorAnalysisResponse格式
        return ErrorAnalysisResponse(
            student_id=analysis_result.student_id,
            analysis_period_days=analysis_result.analysis_period_days,
            total_errors=analysis_result.total_errors,
            error_categories=[],  # 简化处理
            error_frequency=analysis_result.error_frequency,
            error_trend=analysis_result.error_trend,
            weak_knowledge_points=analysis_result.weak_knowledge_points,
            improvement_suggestions=analysis_result.improvement_suggestions,
            analysis_time=analysis_result.analysis_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取错题分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="错题分析服务暂时不可用",
        ) from e


@router.get(
    "/knowledge-gaps/{student_id}",
    response_model=list[KnowledgeGapResponse],
    summary="获取知识缺口分析",
    description="识别学生的知识缺口，提供针对性学习建议",
)
async def get_knowledge_gaps(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeGapResponse]:
    """获取知识缺口分析."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该学生的知识缺口",
            )

        error_service = ErrorAnalysisService(db)
        knowledge_gaps = await error_service.get_knowledge_gaps(student_id)

        return knowledge_gaps

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识缺口失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="知识缺口分析服务暂时不可用",
        ) from e


@router.post(
    "/reinforcement-plan/{student_id}",
    response_model=ReinforcementPlanResponse,
    summary="生成强化训练计划",
    description="基于错题分析生成个性化强化训练计划",
)
async def generate_reinforcement_plan(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReinforcementPlanResponse:
    """生成强化训练计划."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限为该学生生成训练计划",
            )

        error_service = ErrorAnalysisService(db)

        # 获取知识缺口
        knowledge_gaps = await error_service.get_knowledge_gaps(student_id)

        # 生成强化计划
        plan_data = await error_service.generate_reinforcement_plan(student_id, knowledge_gaps)

        return ReinforcementPlanResponse(
            student_id=student_id,
            plan_created_at=datetime.now(),
            knowledge_gaps_count=len(knowledge_gaps),
            training_modules=plan_data.get("training_modules", []),
            estimated_completion_days=plan_data.get("estimated_completion_days", 0),
            priority_focus_areas=plan_data.get("priority_focus_areas", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成强化训练计划失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="强化训练计划生成服务暂时不可用",
        ) from e


# ==================== 遗忘曲线端点 ====================


@router.get(
    "/forgetting-curve/{student_id}/{question_id}",
    response_model=ForgettingCurveResponse,
    summary="获取遗忘曲线分析",
    description="分析特定题目的遗忘曲线，预测复习时间",
)
async def get_forgetting_curve(
    student_id: int,
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForgettingCurveResponse:
    """获取遗忘曲线分析."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该学生的遗忘曲线",
            )

        forgetting_service = ForgettingCurveService(db)
        curve_analysis = await forgetting_service.get_forgetting_curve_analysis(
            student_id, question_id
        )

        return curve_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取遗忘曲线失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="遗忘曲线分析服务暂时不可用",
        ) from e


@router.get(
    "/review-schedule/{student_id}",
    response_model=ReviewScheduleResponse,
    summary="获取复习计划",
    description="基于遗忘曲线生成个性化复习计划",
)
async def get_review_schedule(
    student_id: int,
    days_ahead: int = Query(7, ge=1, le=30, description="计划天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewScheduleResponse:
    """获取复习计划."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该学生的复习计划",
            )

        forgetting_service = ForgettingCurveService(db)
        review_schedule = await forgetting_service.get_review_schedule(student_id, days_ahead)

        return review_schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取复习计划失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="复习计划生成服务暂时不可用",
        ) from e


@router.post(
    "/update-memory-strength/{student_id}/{question_id}",
    summary="更新记忆强度",
    description="根据学习表现更新题目的记忆强度",
)
async def update_memory_strength(
    student_id: int,
    question_id: int,
    performance_score: float = Query(..., ge=0.0, le=1.0, description="表现分数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新记忆强度."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限更新该学生的记忆强度",
            )

        forgetting_service = ForgettingCurveService(db)
        memory_update = await forgetting_service.update_memory_strength(
            student_id, question_id, performance_score
        )

        return {
            "status": "success",
            "message": "记忆强度更新成功",
            "memory_update": memory_update,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新记忆强度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="记忆强度更新服务暂时不可用",
        ) from e


# ==================== 学习策略推荐端点 ====================


@router.get(
    "/learning-strategy/{student_id}",
    response_model=LearningStrategyResponse,
    summary="获取学习策略推荐",
    description="基于学习历史推荐个性化学习策略",
)
async def get_learning_strategy(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningStrategyResponse:
    """获取学习策略推荐."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该学生的学习策略",
            )

        # 获取学生档案和学习历史
        student_profile = {"student_id": student_id}  # 简化处理
        learning_history: list[dict[str, Any]] = []  # 需要从数据库获取

        # 使用学习算法生成推荐
        learning_algorithm = LearningAlgorithm()
        strategy_recommendation = learning_algorithm.recommend_learning_strategy(
            student_profile, learning_history
        )

        return LearningStrategyResponse(
            student_id=student_id,
            learning_style=strategy_recommendation.get("learning_style", "unknown"),
            current_performance=strategy_recommendation.get("current_performance", {}),
            weak_areas=strategy_recommendation.get("weak_areas", []),
            recommendations=strategy_recommendation.get("recommendations", []),
            confidence_score=strategy_recommendation.get("confidence_score", 0.5),
            generated_at=datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习策略失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="学习策略推荐服务暂时不可用",
        ) from e


# ==================== 知识图谱端点 ====================


@router.get(
    "/learning-path/{start_knowledge_id}/{target_knowledge_id}",
    summary="获取学习路径",
    description="基于知识图谱规划从起始知识点到目标知识点的学习路径",
)
async def get_learning_path(
    start_knowledge_id: int,
    target_knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学习路径."""
    try:
        knowledge_graph = KnowledgeGraph(db)

        # 构建知识图谱
        await knowledge_graph.build_knowledge_graph()

        # 查找学习路径
        learning_path = await knowledge_graph.find_learning_path(
            start_knowledge_id, target_knowledge_id
        )

        return {
            "start_knowledge_id": start_knowledge_id,
            "target_knowledge_id": target_knowledge_id,
            "path_length": len(learning_path),
            "learning_path": learning_path,
            "estimated_total_time": sum(step.get("estimated_time", 0) for step in learning_path),
        }

    except Exception as e:
        logger.error(f"获取学习路径失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="学习路径规划服务暂时不可用",
        ) from e


@router.get(
    "/knowledge-dependencies/{knowledge_id}",
    summary="获取知识点依赖关系",
    description="分析知识点的前置依赖和后续关联",
)
async def get_knowledge_dependencies(
    knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取知识点依赖关系."""
    try:
        knowledge_graph = KnowledgeGraph(db)

        # 构建知识图谱
        await knowledge_graph.build_knowledge_graph()

        # 分析依赖关系
        dependencies = await knowledge_graph.analyze_knowledge_dependencies(knowledge_id)

        return dependencies

    except Exception as e:
        logger.error(f"获取知识点依赖关系失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="知识点依赖分析服务暂时不可用",
        ) from e


@router.get(
    "/next-knowledge-points/{student_id}",
    summary="推荐下一个学习知识点",
    description="基于学生当前掌握情况推荐下一个应该学习的知识点",
)
async def get_next_knowledge_points(
    student_id: int,
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """推荐下一个学习知识点."""
    try:
        # 权限检查
        if current_user.id != student_id and getattr(current_user, "role", "student") not in [
            "teacher",
            "admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该学生的知识点推荐",
            )

        knowledge_graph = KnowledgeGraph(db)

        # 构建知识图谱
        await knowledge_graph.build_knowledge_graph()

        # 获取已掌握的知识点（简化处理）
        mastered_knowledge_ids: list[int] = []  # 需要从学习记录中获取

        # 推荐下一个知识点
        recommendations = await knowledge_graph.recommend_next_knowledge_points(
            student_id, mastered_knowledge_ids
        )

        return {
            "student_id": student_id,
            "mastered_count": len(mastered_knowledge_ids),
            "recommendations": recommendations[:limit],
            "total_available": len(recommendations),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"推荐知识点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="知识点推荐服务暂时不可用",
        ) from e
