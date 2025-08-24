"""热点资源池API端点 - 实现RSS订阅源管理和热点推荐接口."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.resources.schemas.hotspot_schemas import (
    HotspotResourceResponse,
)
from app.resources.schemas.resource_schemas import (
    HotspotResourceCreate,
    HotspotResourceSearchRequest,
    HotspotResourceUpdate,
)
from app.resources.services.hotspot_service import HotspotService
from app.resources.utils.rss_utils import ExternalResourceCollector
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_user

router = APIRouter(prefix="/hotspots", tags=["热点资源池"])


# ==================== RSS订阅源管理 ====================


@router.post("/rss-feeds/collect", response_model=dict[str, Any])
async def collect_rss_resources(
    max_items_per_feed: int = Query(5, ge=1, le=20),
    target_language: str = Query("en", description="目标语言"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """从RSS源收集热点资源."""
    # 权限检查：只有教师和管理员可以收集RSS资源
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以收集RSS资源",
        )

    try:
        collector = ExternalResourceCollector()
        resources = await collector.collect_daily_resources(
            max_items_per_feed=max_items_per_feed,
            target_language=target_language,
        )

        return {
            "success": True,
            "collected_count": len(resources),
            "resources": resources[:10],  # 只返回前10个作为预览
            "message": f"成功收集 {len(resources)} 个热点资源",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收集RSS资源失败: {str(e)}",
        ) from e


@router.get("/daily-recommendations", response_model=dict[str, Any])
async def get_daily_recommendations(
    library_id: int = Query(..., description="资源库ID"),
    limit: int = Query(10, ge=1, le=50),
    difficulty_level: str | None = Query(None, description="难度级别"),
    topics: list[str] | None = Query(None, description="话题筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取每日热点推荐."""
    try:
        hotspot_service = HotspotService(db)

        # 构建用户偏好
        user_preferences = {}
        if difficulty_level:
            user_preferences["difficulty_level"] = difficulty_level
        if topics:
            user_preferences["topics"] = topics

        # 获取推荐资源
        recommended_resources = await hotspot_service.get_recommended_resources(
            library_id=library_id,
            user_preferences=user_preferences,
        )

        # 获取热门资源
        trending_resources = await hotspot_service.get_trending_resources(
            library_id=library_id,
            limit=limit // 2,
        )

        return {
            "success": True,
            "recommended_resources": [
                {
                    "id": resource.id,
                    "title": resource.title,
                    "source_type": resource.source_type,
                    "difficulty_level": resource.difficulty_level,
                    "topics": resource.topics,
                    "popularity_score": resource.popularity_score,
                    "recommendation_reason": resource.recommendation_reason,
                }
                for resource in recommended_resources[: limit // 2]
            ],
            "trending_resources": [
                {
                    "id": resource.id,
                    "title": resource.title,
                    "source_type": resource.source_type,
                    "view_count": resource.view_count,
                    "popularity_score": resource.popularity_score,
                }
                for resource in trending_resources
            ],
            "total_count": len(recommended_resources) + len(trending_resources),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每日推荐失败: {str(e)}",
        ) from e


# ==================== 热点资源管理 ====================


@router.post("/resources", response_model=HotspotResourceResponse)
async def create_hotspot_resource(
    hotspot_data: HotspotResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HotspotResourceResponse:
    """创建热点资源."""
    # 权限检查：只有教师和管理员可以创建热点资源
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以创建热点资源",
        )

    try:
        hotspot_service = HotspotService(db)
        hotspot_resource = await hotspot_service.create_hotspot_resource(
            hotspot_data, current_user.id
        )
        return HotspotResourceResponse.model_validate(hotspot_resource)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建热点资源失败: {str(e)}",
        ) from e


@router.get("/resources/{hotspot_id}", response_model=HotspotResourceResponse)
async def get_hotspot_resource(
    hotspot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HotspotResourceResponse:
    """获取热点资源详情."""
    try:
        hotspot_service = HotspotService(db)
        hotspot_resource = await hotspot_service.get_hotspot_resource(hotspot_id)

        if not hotspot_resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="热点资源不存在",
            )

        # 记录访问
        await hotspot_service.update_engagement_metrics(hotspot_id, "view", current_user.id)

        return HotspotResourceResponse.model_validate(hotspot_resource)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热点资源失败: {str(e)}",
        ) from e


@router.put("/resources/{hotspot_id}", response_model=HotspotResourceResponse)
async def update_hotspot_resource(
    hotspot_id: int,
    hotspot_data: HotspotResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HotspotResourceResponse:
    """更新热点资源."""
    # 权限检查：只有教师和管理员可以更新热点资源
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以更新热点资源",
        )

    try:
        hotspot_service = HotspotService(db)
        hotspot_resource = await hotspot_service.update_hotspot_resource(
            hotspot_id, hotspot_data, current_user.id
        )

        if not hotspot_resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="热点资源不存在",
            )

        return HotspotResourceResponse.model_validate(hotspot_resource)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新热点资源失败: {str(e)}",
        ) from e


@router.delete("/resources/{hotspot_id}")
async def delete_hotspot_resource(
    hotspot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除热点资源."""
    # 权限检查：只有教师和管理员可以删除热点资源
    if current_user.user_type.value not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以删除热点资源",
        )

    try:
        hotspot_service = HotspotService(db)
        success = await hotspot_service.delete_hotspot_resource(hotspot_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="热点资源不存在",
            )

        return {"success": True, "message": "热点资源删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除热点资源失败: {str(e)}",
        ) from e


# ==================== 搜索和筛选 ====================


@router.post("/resources/search", response_model=dict[str, Any])
async def search_hotspot_resources(
    search_request: HotspotResourceSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """搜索热点资源."""
    try:
        hotspot_service = HotspotService(db)
        resources, total_count = await hotspot_service.search_hotspot_resources(search_request)

        return {
            "success": True,
            "resources": [
                HotspotResourceResponse.model_validate(resource).model_dump()
                for resource in resources
            ],
            "total_count": total_count,
            "page": search_request.page,
            "page_size": search_request.page_size,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索热点资源失败: {str(e)}",
        ) from e
