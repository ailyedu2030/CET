"""专业发展支持API端点 - 需求17实现."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.resources.schemas.professional_development_schemas import (
    CommunityPostCreate,
    CommunityPostResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    TrainingEnrollmentCreate,
)
from app.resources.services.professional_development_service import (
    ProfessionalDevelopmentService,
)
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/professional-development", tags=["专业发展支持"])


# ==================== 培训资源管理 ====================


@router.get("/training/resources", response_model=dict[str, Any])
async def get_training_resources(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: str | None = Query(None, description="分类筛选"),
    difficulty: str | None = Query(None, description="难度筛选"),
    search: str | None = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取培训资源列表."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_training_resources(
            page=page,
            page_size=page_size,
            category=category,
            difficulty=difficulty,
            search=search,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "data": result,
            "message": "获取培训资源列表成功",
        }
    except Exception as e:
        logger.error(f"Get training resources failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取培训资源列表失败: {str(e)}",
        ) from e


@router.post("/training/{training_id}/enroll", response_model=dict[str, Any])
async def enroll_training(
    training_id: int,
    enrollment_data: TrainingEnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """报名培训课程."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.enroll_training(
            training_id=training_id,
            user_id=current_user.id,
            motivation=enrollment_data.motivation,
        )
        return {
            "success": True,
            "data": result,
            "message": "报名成功",
        }
    except Exception as e:
        logger.error(f"Enroll training failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报名失败: {str(e)}",
        ) from e


@router.get("/training/{training_id}/progress", response_model=dict[str, Any])
async def get_training_progress(
    training_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取培训进度."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_training_progress(
            training_id=training_id,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "data": result,
            "message": "获取培训进度成功",
        }
    except Exception as e:
        logger.error(f"Get training progress failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取培训进度失败: {str(e)}",
        ) from e


# ==================== 认证辅导材料 ====================


@router.get("/certification/materials", response_model=dict[str, Any])
async def get_certification_materials(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: str | None = Query(None, description="分类筛选"),
    type: str | None = Query(None, description="类型筛选"),
    search: str | None = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取认证辅导材料列表."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_certification_materials(
            page=page,
            page_size=page_size,
            category=category,
            material_type=type,
            search=search,
        )
        return {
            "success": True,
            "data": result,
            "message": "获取认证材料列表成功",
        }
    except Exception as e:
        logger.error(f"Get certification materials failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取认证材料列表失败: {str(e)}",
        ) from e


@router.post("/certification/materials/{material_id}/download", response_model=dict[str, Any])
async def download_certification_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """下载认证材料."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.download_certification_material(
            material_id=material_id,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "data": result,
            "message": "获取下载链接成功",
        }
    except Exception as e:
        logger.error(f"Download certification material failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}",
        ) from e


# ==================== 社区交流平台 ====================


@router.get("/community/posts", response_model=dict[str, Any])
async def get_community_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: str | None = Query(None, description="分类筛选"),
    sort_by: str = Query("latest", description="排序方式"),
    search: str | None = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取社区帖子列表."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_community_posts(
            page=page,
            page_size=page_size,
            category=category,
            sort_by=sort_by,
            search=search,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "data": result,
            "message": "获取社区帖子列表成功",
        }
    except Exception as e:
        logger.error(f"Get community posts failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取社区帖子列表失败: {str(e)}",
        ) from e


@router.post("/community/posts", response_model=CommunityPostResponse)
async def create_community_post(
    post_data: CommunityPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityPostResponse:
    """创建社区帖子."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.create_community_post(
            author_id=current_user.id,
            title=post_data.title,
            content=post_data.content,
            category=post_data.category,
            tags=post_data.tags,
        )
        return CommunityPostResponse.model_validate(result)
    except Exception as e:
        logger.error(f"Create community post failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建帖子失败: {str(e)}",
        ) from e


@router.post("/community/posts/{post_id}/like", response_model=dict[str, Any])
async def like_community_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """点赞社区帖子."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.like_community_post(
            post_id=post_id,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "data": result,
            "message": "操作成功",
        }
    except Exception as e:
        logger.error(f"Like community post failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"点赞失败: {str(e)}",
        ) from e


# ==================== 研究动态推送 ====================


@router.get("/research/updates", response_model=dict[str, Any])
async def get_research_updates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: str | None = Query(None, description="分类筛选"),
    importance: str | None = Query(None, description="重要性筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取研究动态列表."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_research_updates(
            page=page,
            page_size=page_size,
            category=category,
            importance=importance,
        )
        return {
            "success": True,
            "data": result,
            "message": "获取研究动态列表成功",
        }
    except Exception as e:
        logger.error(f"Get research updates failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取研究动态列表失败: {str(e)}",
        ) from e


@router.post("/research/updates/{update_id}/bookmark", response_model=dict[str, Any])
async def bookmark_research_update(
    update_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """收藏研究动态."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.bookmark_research_update(
            update_id=update_id,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "data": result,
            "message": "操作成功",
        }
    except Exception as e:
        logger.error(f"Bookmark research update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收藏失败: {str(e)}",
        ) from e


# ==================== 通知设置 ====================


@router.get("/notifications/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationSettingsResponse:
    """获取通知设置."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_notification_settings(user_id=current_user.id)
        return NotificationSettingsResponse.model_validate(result)
    except Exception as e:
        logger.error(f"Get notification settings failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知设置失败: {str(e)}",
        ) from e


@router.put("/notifications/settings", response_model=dict[str, Any])
async def update_notification_settings(
    settings: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新通知设置."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.update_notification_settings(
            user_id=current_user.id,
            settings=settings,
        )
        return {
            "success": True,
            "data": result,
            "message": "更新通知设置成功",
        }
    except Exception as e:
        logger.error(f"Update notification settings failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知设置失败: {str(e)}",
        ) from e


# ==================== 统计和推荐 ====================


@router.get("/stats/learning", response_model=dict[str, Any])
async def get_learning_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取个人学习统计."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_learning_stats(user_id=current_user.id)
        return {
            "success": True,
            "data": result,
            "message": "获取学习统计成功",
        }
    except Exception as e:
        logger.error(f"Get learning stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习统计失败: {str(e)}",
        ) from e


@router.get("/recommendations", response_model=dict[str, Any])
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取个性化推荐."""
    try:
        service = ProfessionalDevelopmentService(db)
        result = await service.get_personalized_recommendations(user_id=current_user.id)
        return {
            "success": True,
            "data": result,
            "message": "获取个性化推荐成功",
        }
    except Exception as e:
        logger.error(f"Get personalized recommendations failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取个性化推荐失败: {str(e)}",
        ) from e
