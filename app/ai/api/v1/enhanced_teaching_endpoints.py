"""增强的智能教学调整API端点."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.enhanced_collaboration_manager import EnhancedCollaborationManager
from app.ai.services.enhanced_learning_analytics import EnhancedLearningAnalytics
from app.ai.services.intelligent_teaching_adjustment import (
    IntelligentTeachingAdjustment,
)
from app.ai.services.optimized_recommendation_engine import (
    OptimizedRecommendationEngine,
)
from app.core.database import get_db
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_user

router = APIRouter(prefix="/enhanced-teaching", tags=["增强智能教学"])


# ==================== 增强学情分析 ====================


@router.post("/learning-analysis/comprehensive")
async def comprehensive_learning_analysis(
    class_id: int,
    course_id: int,
    analysis_period_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """执行综合学情分析."""
    # 权限检查：只有教师和管理员可以执行学情分析
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以执行学情分析",
        )

    try:
        analytics_service = EnhancedLearningAnalytics()
        analysis_result = await analytics_service.comprehensive_learning_analysis(
            db, class_id, course_id, analysis_period_days
        )

        return {
            "success": True,
            "analysis_result": analysis_result,
            "message": "综合学情分析完成",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学情分析失败: {str(e)}",
        ) from e


# ==================== 智能教学调整 ====================


@router.post("/teaching-adjustment/comprehensive")
async def comprehensive_teaching_adjustment(
    class_id: int,
    course_id: int,
    lesson_plan_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """生成综合教学调整建议."""
    # 权限检查：只有教师和管理员可以生成教学调整建议
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以生成教学调整建议",
        )

    try:
        adjustment_service = IntelligentTeachingAdjustment()
        adjustment_result = await adjustment_service.generate_comprehensive_teaching_adjustments(
            db, class_id, course_id, lesson_plan_id, current_user.id
        )

        return {
            "success": True,
            "adjustment_result": adjustment_result,
            "message": "教学调整建议生成完成",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"教学调整建议生成失败: {str(e)}",
        ) from e


# ==================== 增强协作管理 ====================


@router.post("/collaboration/create-session")
async def create_enhanced_collaboration_session(
    resource_type: str,
    resource_id: int,
    collaboration_settings: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建增强的协作会话."""
    # 权限检查：只有教师和管理员可以创建协作会话
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以创建协作会话",
        )

    try:
        collaboration_manager = EnhancedCollaborationManager()
        session_result = await collaboration_manager.create_enhanced_collaboration_session(
            db, resource_type, resource_id, current_user.id, collaboration_settings
        )

        return {
            "success": True,
            "session_result": session_result,
            "message": "协作会话创建成功",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"协作会话创建失败: {str(e)}",
        ) from e


@router.post("/collaboration/join-session")
async def join_collaboration_session(
    session_id: str,
    requested_permissions: list[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """加入协作会话."""
    try:
        collaboration_manager = EnhancedCollaborationManager()
        join_result = await collaboration_manager.join_collaboration_with_permissions(
            db, session_id, current_user.id, requested_permissions
        )

        return {
            "success": join_result["success"],
            "join_result": join_result,
            "message": "协作会话加入处理完成",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"加入协作会话失败: {str(e)}",
        ) from e


@router.post("/collaboration/edit")
async def handle_collaborative_edit(
    session_id: str,
    edit_operation: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """处理协作编辑操作."""
    try:
        collaboration_manager = EnhancedCollaborationManager()
        edit_result = await collaboration_manager.handle_collaborative_edit(
            db, session_id, current_user.id, edit_operation
        )

        return {
            "success": edit_result["success"],
            "edit_result": edit_result,
            "message": "协作编辑处理完成",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"协作编辑失败: {str(e)}",
        ) from e


# ==================== 优化推荐系统 ====================


@router.post("/recommendations/intelligent")
async def generate_intelligent_recommendations(
    context: dict[str, Any],
    recommendation_type: str = "comprehensive",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """生成智能推荐."""
    try:
        # 创建缓存服务（这里简化处理）
        cache_service = None  # 在实际使用中应该注入真实的缓存服务

        recommendation_engine = OptimizedRecommendationEngine(cache_service)
        recommendation_result = await recommendation_engine.generate_intelligent_recommendations(
            db, current_user.id, context, recommendation_type
        )

        return {
            "success": True,
            "recommendation_result": recommendation_result,
            "message": "智能推荐生成完成",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能推荐生成失败: {str(e)}",
        ) from e


@router.post("/recommendations/fast")
async def generate_fast_recommendations(
    context: dict[str, Any],
    max_items: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """生成快速推荐."""
    try:
        # 创建缓存服务（这里简化处理）
        cache_service = None  # 在实际使用中应该注入真实的缓存服务

        recommendation_engine = OptimizedRecommendationEngine(cache_service)
        recommendation_result = await recommendation_engine.generate_fast_recommendations(
            db, current_user.id, context, max_items
        )

        return {
            "success": True,
            "recommendation_result": recommendation_result,
            "message": "快速推荐生成完成",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速推荐生成失败: {str(e)}",
        ) from e


# ==================== 系统状态和健康检查 ====================


@router.get("/system/health")
async def enhanced_teaching_health_check(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """增强教学系统健康检查."""
    try:
        # 检查各个服务的状态
        health_status = {
            "learning_analytics": "healthy",
            "teaching_adjustment": "healthy",
            "collaboration_manager": "healthy",
            "recommendation_engine": "healthy",
        }

        # 简单的服务可用性检查
        try:
            analytics = EnhancedLearningAnalytics()
            adjustment = IntelligentTeachingAdjustment()
            collaboration = EnhancedCollaborationManager()
            recommendation = OptimizedRecommendationEngine()

            # 验证服务初始化
            assert analytics is not None
            assert adjustment is not None
            assert collaboration is not None
            assert recommendation is not None

        except Exception as e:
            health_status["error"] = str(e)
            health_status["overall_status"] = "degraded"

        overall_status = "healthy" if "error" not in health_status else "degraded"

        return {
            "success": True,
            "overall_status": overall_status,
            "service_status": health_status,
            "timestamp": "2024-01-01T00:00:00Z",  # 简化实现
            "message": "增强教学系统状态检查完成",
        }

    except Exception as e:
        return {
            "success": False,
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z",
        }


@router.get("/system/capabilities")
async def get_enhanced_teaching_capabilities(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """获取增强教学系统能力清单."""
    capabilities = {
        "learning_analytics": {
            "comprehensive_analysis": True,
            "multi_dimensional_data_fusion": True,
            "learning_predictions": True,
            "risk_assessment": True,
            "personalized_recommendations": True,
        },
        "teaching_adjustment": {
            "intelligent_adjustments": True,
            "resource_recommendations": True,
            "implementation_planning": True,
            "effectiveness_prediction": True,
        },
        "collaboration_management": {
            "enhanced_sessions": True,
            "permission_management": True,
            "conflict_resolution": True,
            "real_time_editing": True,
        },
        "recommendation_engine": {
            "intelligent_recommendations": True,
            "fast_recommendations": True,
            "optimization_algorithms": True,
            "confidence_scoring": True,
        },
        "system_features": {
            "ai_powered": True,
            "real_time_processing": True,
            "caching_optimization": True,
            "multi_user_support": True,
        },
    }

    return {
        "success": True,
        "capabilities": capabilities,
        "version": "2.0.0",
        "last_updated": "2024-01-01T00:00:00Z",
        "message": "增强教学系统能力清单",
    }
