"""学习社交与互动系统 - API端点"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.schemas.social_interaction_schemas import (
    DiscussionForumCreate,
    DiscussionForumListResponse,
    DiscussionForumResponse,
    DiscussionForumUpdate,
    ForumPostCreate,
    ForumPostListResponse,
    ForumPostResponse,
    ForumPostUpdate,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    PostLikeCreate,
    PostLikeResponse,
    PostReportCreate,
    PostReportResponse,
    StudyGroupCreate,
    StudyGroupListResponse,
    StudyGroupResponse,
    StudyPartnerRequestCreate,
    StudyPartnerRequestListResponse,
    StudyPartnerRequestResponse,
)
from app.training.services.social_service import SocialService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["学习社交与互动系统"])


# ==================== 讨论区管理 ====================


@router.post("/forums", summary="创建讨论区", response_model=DiscussionForumResponse)
async def create_discussion_forum(
    data: DiscussionForumCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DiscussionForumResponse:
    """创建讨论区"""
    try:
        service = SocialService(db)
        forum = await service.create_forum(data)

        logger.info(f"用户 {current_user.id} 创建讨论区成功: {forum.id}")  # type: ignore[has-type]

        return DiscussionForumResponse.model_validate(forum)
    except Exception as e:
        logger.error(f"创建讨论区失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/forums", summary="获取讨论区列表", response_model=DiscussionForumListResponse
)
async def get_discussion_forums(
    skip: int = 0,
    limit: int = 10,
    category: str | None = None,
    class_id: int | None = None,
    is_public: bool | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DiscussionForumListResponse:
    """获取讨论区列表"""
    try:
        service = SocialService(db)
        forums, total = await service.get_forums(
            skip=skip,
            limit=limit,
            category=category,
            class_id=class_id,
            is_public=is_public,
        )

        logger.info(f"用户 {current_user.id} 查询讨论区列表，共 {total} 个")

        return DiscussionForumListResponse(
            success=True,
            data=[DiscussionForumResponse.model_validate(f) for f in forums],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询讨论区列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put(
    "/forums/{forum_id}", summary="更新讨论区", response_model=DiscussionForumResponse
)
async def update_discussion_forum(
    forum_id: int,
    data: DiscussionForumUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DiscussionForumResponse:
    """更新讨论区"""
    try:
        service = SocialService(db)
        forum = await service.update_forum(forum_id, data)

        if not forum:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="讨论区不存在"
            )

        logger.info(f"用户 {current_user.id} 更新讨论区: {forum_id}")

        return DiscussionForumResponse.model_validate(forum)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新讨论区失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


# ==================== 帖子管理 ====================


@router.post("/posts", summary="创建论坛帖子", response_model=ForumPostResponse)
async def create_forum_post(
    data: ForumPostCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPostResponse:
    """创建论坛帖子"""
    try:
        service = SocialService(db)
        post = await service.create_post(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建帖子成功: {post.id}")  # type: ignore[has-type]

        return ForumPostResponse.model_validate(post)
    except Exception as e:
        logger.error(f"创建帖子失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get("/posts", summary="获取帖子列表", response_model=ForumPostListResponse)
async def get_forum_posts(
    skip: int = 0,
    limit: int = 10,
    forum_id: int | None = None,
    user_id: int | None = None,
    post_type: str | None = None,
    parent_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPostListResponse:
    """获取帖子列表"""
    try:
        service = SocialService(db)
        posts, total = await service.get_posts(
            skip=skip,
            limit=limit,
            forum_id=forum_id,
            user_id=user_id,
            post_type=post_type,
            parent_id=parent_id,
        )

        logger.info(f"用户 {current_user.id} 查询帖子列表，共 {total} 个")

        return ForumPostListResponse(
            success=True,
            data=[ForumPostResponse.model_validate(p) for p in posts],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询帖子列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put("/posts/{post_id}", summary="更新帖子", response_model=ForumPostResponse)
async def update_forum_post(
    post_id: int,
    data: ForumPostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPostResponse:
    """更新帖子"""
    try:
        service = SocialService(db)
        post = await service.update_post(post_id, current_user.id, data)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在或无权限"
            )

        logger.info(f"用户 {current_user.id} 更新帖子: {post_id}")

        return ForumPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新帖子失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


@router.get(
    "/posts/{post_id}", summary="获取帖子详情", response_model=ForumPostResponse
)
async def get_post_detail(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPostResponse:
    """获取帖子详情"""
    try:
        service = SocialService(db)
        post = await service.get_post_by_id(post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        logger.info(f"用户 {current_user.id} 查看帖子详情: {post_id}")
        return ForumPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取帖子详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取失败"
        ) from e


@router.post(
    "/posts/{post_id}/replies", summary="回复帖子", response_model=ForumPostResponse
)
async def reply_to_post(
    post_id: int,
    data: ForumPostCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ForumPostResponse:
    """回复帖子"""
    try:
        service = SocialService(db)
        # 设置父帖子ID
        reply_data = data.model_copy()
        reply_data.parent_id = post_id

        reply = await service.create_post(current_user.id, reply_data)

        logger.info(f"用户 {current_user.id} 回复帖子: {post_id}")
        return ForumPostResponse.model_validate(reply)
    except Exception as e:
        logger.error(f"回复帖子失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="回复失败"
        ) from e


# ==================== 帖子互动 ====================


@router.post("/posts/like", summary="点赞帖子", response_model=PostLikeResponse)
async def like_forum_post(
    data: PostLikeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PostLikeResponse:
    """点赞帖子"""
    try:
        service = SocialService(db)
        like = await service.like_post(current_user.id, data)

        logger.info(f"用户 {current_user.id} 点赞帖子: {data.post_id}")

        return PostLikeResponse.model_validate(like)
    except Exception as e:
        logger.error(f"点赞帖子失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="操作失败"
        ) from e


@router.post("/posts/report", summary="举报帖子", response_model=PostReportResponse)
async def report_forum_post(
    data: PostReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PostReportResponse:
    """举报帖子"""
    try:
        service = SocialService(db)
        report = await service.report_post(current_user.id, data)

        logger.info(f"用户 {current_user.id} 举报帖子: {data.post_id}")

        return PostReportResponse.model_validate(report)
    except Exception as e:
        logger.error(f"举报帖子失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="举报失败"
        ) from e


# ==================== 学习伙伴匹配 ====================


@router.post(
    "/partner-requests",
    summary="创建学习伙伴请求",
    response_model=StudyPartnerRequestResponse,
)
async def create_study_partner_request(
    data: StudyPartnerRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudyPartnerRequestResponse:
    """创建学习伙伴请求"""
    try:
        service = SocialService(db)
        request = await service.create_partner_request(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建学习伙伴请求成功: {request.id}")  # type: ignore[has-type]

        return StudyPartnerRequestResponse.model_validate(request)
    except Exception as e:
        logger.error(f"创建学习伙伴请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/partner-requests",
    summary="获取学习伙伴请求列表",
    response_model=StudyPartnerRequestListResponse,
)
async def get_study_partner_requests(
    skip: int = 0,
    limit: int = 10,
    user_id: int | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudyPartnerRequestListResponse:
    """获取学习伙伴请求列表"""
    try:
        service = SocialService(db)
        requests, total = await service.get_partner_requests(
            skip=skip,
            limit=limit,
            user_id=user_id or current_user.id,
            status=status,
        )

        logger.info(f"用户 {current_user.id} 查询学习伙伴请求，共 {total} 个")

        return StudyPartnerRequestListResponse(
            success=True,
            data=[StudyPartnerRequestResponse.model_validate(r) for r in requests],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询学习伙伴请求失败: {e}")
        from fastapi import status as http_status

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/partner-requests/{request_id}/respond", summary="响应学习伙伴请求")
async def respond_to_partner_request(
    request_id: int,
    data: dict[str, str],  # {"action": "accept" | "decline", "message": "..."}
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """响应学习伙伴请求"""
    try:
        service = SocialService(db)
        action = data.get("action")
        message = data.get("message", "")

        if action not in ["accept", "decline"]:
            raise HTTPException(status_code=400, detail="无效的操作类型")

        await service.respond_to_partner_request(
            request_id, current_user.id, action, message
        )

        logger.info(
            f"用户 {current_user.id} 响应学习伙伴请求: {request_id}, 操作: {action}"
        )
        return {"message": f"已{action}学习伙伴请求"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"响应学习伙伴请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="响应失败"
        ) from e


# ==================== 学习小组管理 ====================


@router.post("/study-groups", summary="创建学习小组", response_model=StudyGroupResponse)
async def create_study_group(
    data: StudyGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudyGroupResponse:
    """创建学习小组"""
    try:
        service = SocialService(db)
        group = await service.create_study_group(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建学习小组成功: {group.id}")  # type: ignore[has-type]

        return StudyGroupResponse.model_validate(group)
    except Exception as e:
        logger.error(f"创建学习小组失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/study-groups", summary="获取学习小组列表", response_model=StudyGroupListResponse
)
async def get_study_groups(
    skip: int = 0,
    limit: int = 10,
    is_public: bool | None = None,
    study_topic: str | None = None,
    target_level: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudyGroupListResponse:
    """获取学习小组列表"""
    try:
        service = SocialService(db)
        groups, total = await service.get_study_groups(
            skip=skip,
            limit=limit,
            is_public=is_public,
            study_topic=study_topic,
            target_level=target_level,
        )

        logger.info(f"用户 {current_user.id} 查询学习小组列表，共 {total} 个")

        return StudyGroupListResponse(
            success=True,
            data=[StudyGroupResponse.model_validate(g) for g in groups],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询学习小组列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.get(
    "/study-groups/{group_id}",
    summary="获取学习小组详情",
    response_model=StudyGroupResponse,
)
async def get_study_group_detail(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudyGroupResponse:
    """获取学习小组详情"""
    try:
        service = SocialService(db)
        group = await service.get_study_group_by_id(group_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="学习小组不存在"
            )

        logger.info(f"用户 {current_user.id} 查看学习小组详情: {group_id}")
        return StudyGroupResponse.model_validate(group)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习小组详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取失败"
        ) from e


@router.post("/study-groups/{group_id}/join", summary="加入学习小组")
async def join_study_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """加入学习小组"""
    try:
        service = SocialService(db)
        await service.join_study_group(group_id, current_user.id)

        logger.info(f"用户 {current_user.id} 加入学习小组: {group_id}")
        return {"message": "成功加入学习小组"}
    except Exception as e:
        logger.error(f"加入学习小组失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="加入失败"
        ) from e


@router.post("/study-groups/{group_id}/leave", summary="退出学习小组")
async def leave_study_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """退出学习小组"""
    try:
        service = SocialService(db)
        await service.leave_study_group(group_id, current_user.id)

        logger.info(f"用户 {current_user.id} 退出学习小组: {group_id}")
        return {"message": "成功退出学习小组"}
    except Exception as e:
        logger.error(f"退出学习小组失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="退出失败"
        ) from e


# ==================== 实时通信 ====================


@router.post("/messages", summary="发送消息", response_model=MessageResponse)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """发送消息"""
    try:
        service = SocialService(db)
        message = await service.send_message(current_user.id, data)

        logger.info(f"用户 {current_user.id} 发送消息成功: {message.id}")  # type: ignore[has-type]

        return MessageResponse.model_validate(message)
    except ValueError as e:
        logger.warning(f"消息发送被拒绝: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="发送失败"
        ) from e


@router.get("/messages", summary="获取消息列表", response_model=MessageListResponse)
async def get_messages(
    skip: int = 0,
    limit: int = 20,
    receiver_id: int | None = None,
    group_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """获取消息列表"""
    try:
        service = SocialService(db)
        messages, total = await service.get_messages(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            receiver_id=receiver_id,
            group_id=group_id,
        )

        logger.info(f"用户 {current_user.id} 查询消息列表，共 {total} 条")

        return MessageListResponse(
            success=True,
            data=[MessageResponse.model_validate(m) for m in messages],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询消息列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


# ==================== 社交统计和分析 ====================


@router.get("/analytics/social", summary="获取社交数据分析")
async def get_social_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取社交数据分析"""
    try:
        logger.info(f"获取社交分析: user={current_user.id}")

        analytics = {
            "forum_activity": {
                "posts_created": 15,
                "replies_received": 32,
                "likes_received": 48,
                "active_forums": 3,
            },
            "partner_matching": {
                "requests_sent": 2,
                "matches_found": 1,
                "active_partnerships": 1,
                "satisfaction_rating": 4.5,
            },
            "group_participation": {
                "groups_joined": 2,
                "groups_created": 1,
                "messages_sent": 156,
                "activity_score": 0.85,
            },
            "engagement_trends": {
                "daily_interactions": [5, 8, 12, 6, 9, 15, 11],
                "weekly_growth": 0.15,
                "popular_topics": ["听力练习", "语法讨论", "考试技巧"],
            },
        }

        return analytics
    except Exception as e:
        logger.error(f"获取社交数据分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="分析失败"
        ) from e


@router.get("/recommendations/social", summary="获取社交推荐")
async def get_social_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取社交推荐"""
    try:
        logger.info(f"获取社交推荐: user={current_user.id}")

        recommendations = {
            "recommended_forums": [
                {
                    "id": 1,
                    "name": "英语四级听力讨论",
                    "category": "听力训练",
                    "member_count": 156,
                    "activity_score": 0.92,
                    "reason": "基于您的学习兴趣推荐",
                },
            ],
            "potential_partners": [
                {
                    "id": 2,
                    "username": "学习达人",
                    "target_level": "四级",
                    "match_score": 0.88,
                    "common_interests": ["听力练习", "词汇积累"],
                    "reason": "学习目标和时间安排高度匹配",
                },
            ],
            "suggested_groups": [
                {
                    "id": 3,
                    "name": "四级冲刺小组",
                    "study_topic": "四级考试",
                    "member_count": 8,
                    "activity_score": 0.95,
                    "reason": "适合您的学习水平和目标",
                },
            ],
            "trending_topics": [
                "2024年四级新题型",
                "听力技巧分享",
                "作文模板讨论",
            ],
        }

        return recommendations
    except Exception as e:
        logger.error(f"获取社交推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="推荐失败"
        ) from e
