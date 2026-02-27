"""通知系统的Celery任务."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_config import celery_app
from app.core.database import async_session_maker
from app.notifications.models.notification_models import (
    Notification,
    NotificationHistory,
)

logger = logging.getLogger(__name__)


@celery_app.task(name="cleanup_old_notifications")
def cleanup_old_notifications_task() -> dict[str, int]:
    """清理过期的通知和通知历史记录."""
    import asyncio

    async def _cleanup():
        async with async_session_maker() as session:
            # 计算90天前的日期
            cutoff_date = datetime.utcnow() - timedelta(days=90)

            # 清理通知历史
            delete_history_stmt = delete(NotificationHistory).where(
                NotificationHistory.created_at < cutoff_date
            )
            history_result = await session.execute(delete_history_stmt)
            history_deleted = history_result.rowcount

            # 清理已读通知（30天前）
            read_cutoff = datetime.utcnow() - timedelta(days=30)
            delete_notifications_stmt = delete(Notification).where(
                Notification.is_read == True,
                Notification.created_at < read_cutoff,  # noqa: E712
            )
            notifications_result = await session.execute(delete_notifications_stmt)
            notifications_deleted = notifications_result.rowcount

            await session.commit()

            return {
                "history_deleted": history_deleted,
                "notifications_deleted": notifications_deleted,
            }

    return asyncio.run(_cleanup())
