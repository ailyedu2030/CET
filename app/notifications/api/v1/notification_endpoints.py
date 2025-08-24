"""通知系统API端点 - 需求16通知中枢接口实现."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.notifications.models.notification_models import (
    Notification,
    NotificationPreference,
)
from app.notifications.schemas.notification_schemas import (
    NotificationBatchCreate,
    NotificationCreate,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    NotificationStats,
    NotificationUpdate,
    ResourceAuditNotification,
    TeachingPlanChangeNotification,
    TrainingAnomalyAlert,
)
from app.notifications.services.notification_service import UnifiedNotificationService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import AuthRequired, create_permission_dependency


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> UnifiedNotificationService:
    """获取通知服务实例."""
    return UnifiedNotificationService(db)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["通知系统"])


# =================== 基础通知管理 ===================


@router.post(
    "/send",
    response_model=list[NotificationResponse],
    summary="发送通知",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["NOTIFICATION_SEND"]),
    ],
)
async def send_notification(
    notification_data: NotificationCreate,
    user_ids: list[int],
    channels: list[str] = Query(default=["in_app"], description="发送渠道"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """发送通知给指定用户."""
    try:
        notification_service = UnifiedNotificationService(db)
        results = await notification_service.send_notification(
            notification_data, user_ids, channels
        )
        return results
    except Exception as e:
        logger.error(f"发送通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送通知失败: {str(e)}",
        ) from e


@router.post(
    "/batch",
    summary="批量发送通知",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["NOTIFICATION_BATCH_SEND"]),
    ],
)
async def send_batch_notification(
    batch_data: NotificationBatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """批量发送通知 - 支持按班级批量发送."""
    try:
        notification_service = UnifiedNotificationService(db)
        result = await notification_service.send_batch_notification(batch_data)
        return result
    except Exception as e:
        logger.error(f"批量发送通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量发送通知失败: {str(e)}",
        ) from e


@router.get(
    "/list",
    response_model=NotificationListResponse,
    summary="获取通知列表",
    dependencies=[AuthRequired()],
)
async def get_notification_list(
    user_id: int = Query(default=None, description="用户ID"),
    notification_type: str = Query(default=None, description="通知类型"),
    is_read: bool = Query(default=None, description="是否已读"),
    priority: str = Query(default=None, description="优先级"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """获取通知列表."""
    try:
        # 构建查询条件
        conditions = []

        # 非管理员只能查看自己的通知
        if current_user.user_type.value != "admin":
            conditions.append(Notification.user_id == current_user.id)
        elif user_id:
            conditions.append(Notification.user_id == user_id)

        if notification_type:
            conditions.append(Notification.notification_type == notification_type)
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        if priority:
            conditions.append(Notification.priority == priority)

        # 查询总数
        count_query = select(Notification).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = len(count_result.fetchall())

        # 分页查询
        offset = (page - 1) * page_size
        query = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        notifications = result.scalars().all()

        # 转换为响应模式
        notification_responses = [
            NotificationResponse.model_validate(notification) for notification in notifications
        ]

        return NotificationListResponse(
            notifications=notification_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知列表失败: {str(e)}",
        ) from e


@router.put(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="更新通知状态",
    dependencies=[AuthRequired()],
)
async def update_notification(
    notification_id: int,
    update_data: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """更新通知状态（如标记为已读）."""
    try:
        # 查询通知
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知不存在",
            )

        # 权限检查：只能更新自己的通知或管理员权限
        if notification.user_id != current_user.id and current_user.user_type.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限更新此通知",
            )

        # 更新通知
        if update_data.is_read is not None:
            notification.is_read = update_data.is_read
        if update_data.read_at is not None:
            notification.read_at = update_data.read_at

        await db.commit()
        await db.refresh(notification)

        return NotificationResponse.model_validate(notification)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知失败: {str(e)}",
        ) from e


@router.delete(
    "/batch",
    summary="批量删除通知",
    dependencies=[AuthRequired()],
)
async def delete_notifications_batch(
    notification_ids: list[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """批量删除通知."""
    try:
        # 查询要删除的通知
        result = await db.execute(select(Notification).where(Notification.id.in_(notification_ids)))
        notifications = result.scalars().all()

        # 权限检查
        deleted_count = 0
        for notification in notifications:
            if notification.user_id == current_user.id or current_user.user_type.value == "admin":
                await db.delete(notification)
                deleted_count += 1

        await db.commit()

        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 条通知",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"批量删除通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除通知失败: {str(e)}",
        ) from e


# =================== 特定通知类型 - 需求16验收标准1 ===================


@router.post(
    "/teaching-plan-change",
    summary="发送教学计划变更通知",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["TEACHING_PLAN_MANAGE"]),
    ],
)
async def send_teaching_plan_change_notification(
    notification_data: TeachingPlanChangeNotification,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """发送教学计划变更通知 - 需求16验收标准1."""
    try:
        notification_service = UnifiedNotificationService(db)
        result = await notification_service.send_teaching_plan_change_notification(
            notification_data.plan_id,
            notification_data.change_type,
            notification_data.affected_classes,
            notification_data.change_details,
        )
        return result
    except Exception as e:
        logger.error(f"发送教学计划变更通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送教学计划变更通知失败: {str(e)}",
        ) from e


@router.post(
    "/training-anomaly-alert",
    summary="发送学生训练异常预警",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["TRAINING_MONITOR"]),
    ],
)
async def send_training_anomaly_alert(
    alert_data: TrainingAnomalyAlert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """发送学生训练异常预警 - 需求16验收标准1."""
    try:
        notification_service = UnifiedNotificationService(db)
        result = await notification_service.send_training_anomaly_alert(
            alert_data.student_id,
            alert_data.anomaly_type,
            alert_data.anomaly_details,
            alert_data.teacher_ids,
        )
        return result
    except Exception as e:
        logger.error(f"发送训练异常预警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送训练异常预警失败: {str(e)}",
        ) from e


@router.post(
    "/resource-audit",
    summary="发送资源审核状态提醒",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["RESOURCE_AUDIT"]),
    ],
)
async def send_resource_audit_notification(
    audit_data: ResourceAuditNotification,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """发送资源审核状态提醒 - 需求16验收标准1."""
    try:
        notification_service = UnifiedNotificationService(db)
        result = await notification_service.send_resource_audit_notification(
            audit_data.resource_id,
            audit_data.audit_status,
            audit_data.resource_type,
            audit_data.creator_id,
        )
        return result
    except Exception as e:
        logger.error(f"发送资源审核通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送资源审核通知失败: {str(e)}",
        ) from e


# =================== 通知偏好管理 ===================


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="获取通知偏好设置",
    dependencies=[AuthRequired()],
)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceResponse:
    """获取用户通知偏好设置."""
    try:
        result = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
        )
        preference = result.scalar_one_or_none()

        if not preference:
            # 创建默认偏好设置
            preference = NotificationPreference(user_id=current_user.id)
            db.add(preference)
            await db.commit()
            await db.refresh(preference)

        return NotificationPreferenceResponse.model_validate(preference)

    except Exception as e:
        logger.error(f"获取通知偏好失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知偏好失败: {str(e)}",
        ) from e


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="更新通知偏好设置",
    dependencies=[AuthRequired()],
)
async def update_notification_preferences(
    preference_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceResponse:
    """更新用户通知偏好设置."""
    try:
        result = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
        )
        preference = result.scalar_one_or_none()

        if not preference:
            # 创建新的偏好设置
            preference = NotificationPreference(
                user_id=current_user.id,
                **preference_data.model_dump(exclude_unset=True),
            )
            db.add(preference)
        else:
            # 更新现有偏好设置
            for field, value in preference_data.model_dump(exclude_unset=True).items():
                setattr(preference, field, value)

        await db.commit()
        await db.refresh(preference)

        return NotificationPreferenceResponse.model_validate(preference)

    except Exception as e:
        await db.rollback()
        logger.error(f"更新通知偏好失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知偏好失败: {str(e)}",
        ) from e


# =================== 通知统计 ===================


@router.get(
    "/stats",
    response_model=NotificationStats,
    summary="获取通知统计",
    dependencies=[AuthRequired()],
)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationStats:
    """获取用户通知统计信息."""
    try:
        # 查询用户的所有通知
        result = await db.execute(
            select(Notification).where(Notification.user_id == current_user.id)
        )
        notifications = result.scalars().all()

        # 统计数据
        total_notifications = len(notifications)
        unread_count = sum(1 for n in notifications if not n.is_read)
        read_count = total_notifications - unread_count

        # 按类型统计
        by_type: dict[str, int] = {}
        for notification in notifications:
            by_type[notification.notification_type] = (
                by_type.get(notification.notification_type, 0) + 1
            )

        # 按优先级统计
        by_priority: dict[str, int] = {}
        for notification in notifications:
            by_priority[notification.priority] = by_priority.get(notification.priority, 0) + 1

        # 按渠道统计
        by_channel: dict[str, int] = {}
        for notification in notifications:
            for channel in notification.channels:
                by_channel[channel] = by_channel.get(channel, 0) + 1

        # 最近活动（最近10条）
        recent_notifications = sorted(notifications, key=lambda x: x.created_at, reverse=True)[:10]
        recent_activity = [
            {
                "id": n.id,
                "title": n.title,
                "type": n.notification_type,
                "created_at": n.created_at,
                "is_read": n.is_read,
            }
            for n in recent_notifications
        ]

        return NotificationStats(
            total_notifications=total_notifications,
            unread_count=unread_count,
            read_count=read_count,
            by_type=by_type,
            by_priority=by_priority,
            by_channel=by_channel,
            recent_activity=recent_activity,
        )

    except Exception as e:
        logger.error(f"获取通知统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知统计失败: {str(e)}",
        ) from e


# =================== 协作通知端点 - 需求16验收标准2 ===================


@router.post("/collaboration/activity")
async def send_collaboration_notification(
    collaboration_type: str = Query(..., description="协作类型"),
    collaboration_id: int = Query(..., description="协作ID"),
    action: str = Query(..., description="操作类型"),
    participants: str = Query(..., description="参与者ID列表，逗号分隔"),
    details: dict[str, Any] | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    notification_service: UnifiedNotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """发送协作活动通知 - 需求16验收标准2."""
    try:
        participant_ids = [int(id.strip()) for id in participants.split(",") if id.strip()]

        result = await notification_service.send_collaboration_notification(
            collaboration_type=collaboration_type,
            collaboration_id=collaboration_id,
            action=action,
            participants=participant_ids,
            actor_id=current_user["id"],
            details=details or {},
        )

        return result
    except Exception as e:
        logger.error(f"发送协作通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送协作通知失败",
        ) from e


@router.post("/collaboration/lesson-plan/share")
async def send_lesson_plan_share_notification(
    plan_id: int = Query(..., description="教案ID"),
    plan_title: str = Query(..., description="教案标题"),
    share_level: str = Query(..., description="分享级别"),
    target_users: str = Query(..., description="目标用户ID列表，逗号分隔"),
    current_user: dict[str, Any] = Depends(get_current_user),
    notification_service: UnifiedNotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """发送教案分享通知 - 需求16验收标准2."""
    try:
        user_ids = [int(id.strip()) for id in target_users.split(",") if id.strip()]

        result = await notification_service.send_lesson_plan_share_notification(
            plan_id=plan_id,
            plan_title=plan_title,
            shared_by=current_user["id"],
            share_level=share_level,
            target_users=user_ids,
        )

        return result
    except Exception as e:
        logger.error(f"发送教案分享通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送教案分享通知失败",
        ) from e


@router.post("/collaboration/discussion/reply")
async def send_discussion_reply_notification(
    topic_id: int = Query(..., description="讨论话题ID"),
    topic_title: str = Query(..., description="讨论话题标题"),
    participants: str = Query(..., description="话题参与者ID列表，逗号分隔"),
    current_user: dict[str, Any] = Depends(get_current_user),
    notification_service: UnifiedNotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """发送讨论回复通知 - 需求16验收标准2."""
    try:
        participant_ids = [int(id.strip()) for id in participants.split(",") if id.strip()]

        result = await notification_service.send_discussion_reply_notification(
            topic_id=topic_id,
            topic_title=topic_title,
            reply_author=current_user["id"],
            topic_participants=participant_ids,
        )

        return result
    except Exception as e:
        logger.error(f"发送讨论回复通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送讨论回复通知失败",
        ) from e


# =================== WebSocket实时通知 ===================


@router.websocket("/ws/{user_id}")
async def websocket_notification_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket实时通知连接 - 设计文档接口实现."""
    import json
    import uuid

    from fastapi import WebSocketDisconnect

    from app.notifications.services.websocket_manager import websocket_manager

    connection_id = str(uuid.uuid4())

    # 建立连接
    connected = await websocket_manager.connect(websocket, user_id, connection_id)
    if not connected:
        await websocket.close(code=1000, reason="连接失败")
        return

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await websocket_manager.handle_client_message(
                    websocket, user_id, connection_id, message
                )
            except json.JSONDecodeError:
                logger.warning(f"收到无效JSON消息: {data}")
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {str(e)}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: user_id={user_id}, connection_id={connection_id}")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
    finally:
        await websocket_manager.disconnect(websocket, user_id, connection_id)


@router.get(
    "/websocket/stats",
    summary="获取WebSocket连接统计",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["SYSTEM_MONITOR"]),
    ],
)
async def get_websocket_stats(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """获取WebSocket连接统计信息."""
    from app.notifications.services.websocket_manager import websocket_manager

    try:
        stats = await websocket_manager.get_connection_stats()
        return {
            "success": True,
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"获取WebSocket统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取WebSocket统计失败: {str(e)}",
        ) from e
