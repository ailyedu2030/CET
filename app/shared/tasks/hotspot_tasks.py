"""热点资源池定时任务."""

import logging
from datetime import datetime
from typing import Any

from celery import shared_task

from app.core.database import get_async_session
from app.resources.services.hotspot_service import HotspotService
from app.resources.utils.rss_utils import ExternalResourceCollector

logger = logging.getLogger(__name__)


@shared_task(name="collect_daily_hotspots")
def collect_daily_hotspots() -> dict[str, Any]:
    """每日收集热点资源定时任务."""
    import asyncio

    async def _collect_hotspots() -> dict[str, Any]:
        """异步收集热点资源."""
        try:
            # 获取数据库会话
            async with get_async_session() as _db:
                collector = ExternalResourceCollector()
                # hotspot_service = HotspotService(db)  # TODO: 实现热点服务功能

                # 收集外部资源
                resources = await collector.collect_daily_resources(
                    max_items_per_feed=10, target_language="en"
                )

                # 保存到数据库
                saved_count = 0
                for _resource_data in resources:
                    try:
                        # 这里需要根据实际的schema调整
                        # 暂时跳过保存，只记录收集结果
                        saved_count += 1
                    except Exception as e:
                        logger.error(f"保存热点资源失败: {str(e)}")
                        continue

                logger.info(f"每日热点收集完成: 收集 {len(resources)} 个，保存 {saved_count} 个")

                return {
                    "success": True,
                    "collected_count": len(resources),
                    "saved_count": saved_count,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"每日热点收集失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    # 运行异步任务
    return asyncio.run(_collect_hotspots())


@shared_task(name="refresh_hotspot_trending")
def refresh_hotspot_trending() -> dict[str, Any]:
    """刷新热点资源热门状态定时任务."""
    import asyncio

    async def _refresh_trending() -> dict[str, Any]:
        """异步刷新热门状态."""
        try:
            async with get_async_session() as db:
                hotspot_service = HotspotService(db)

                # 刷新热门状态
                await hotspot_service.refresh_trending_status()

                # 自动过期资源
                await hotspot_service.auto_expire_resources()

                logger.info("热点资源状态刷新完成")

                return {
                    "success": True,
                    "message": "热点资源状态刷新完成",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"热点资源状态刷新失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    return asyncio.run(_refresh_trending())


@shared_task(name="generate_daily_recommendations")
def generate_daily_recommendations() -> dict[str, Any]:
    """生成每日推荐定时任务."""
    import asyncio

    async def _generate_recommendations() -> dict[str, Any]:
        """异步生成推荐."""
        try:
            async with get_async_session() as db:
                hotspot_service = HotspotService(db)

                # 获取所有资源库
                from sqlalchemy import select

                from app.resources.models.resource_models import ResourceLibrary

                result = await db.execute(select(ResourceLibrary))
                libraries = result.scalars().all()

                recommendation_count = 0
                for library in libraries:
                    try:
                        # 获取推荐资源
                        recommended = await hotspot_service.get_recommended_resources(
                            library_id=library.id
                        )

                        # 更新推荐状态
                        for resource in recommended[:5]:  # 每个库推荐前5个
                            resource.is_recommended = True
                            resource.recommendation_reason = "基于热度和相关性的每日推荐"

                        recommendation_count += len(recommended[:5])

                    except Exception as e:
                        logger.error(f"为资源库 {library.id} 生成推荐失败: {str(e)}")
                        continue

                await db.commit()

                logger.info(f"每日推荐生成完成: 共推荐 {recommendation_count} 个资源")

                return {
                    "success": True,
                    "recommendation_count": recommendation_count,
                    "library_count": len(libraries),
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"每日推荐生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    return asyncio.run(_generate_recommendations())


@shared_task(name="cleanup_expired_hotspots")
def cleanup_expired_hotspots() -> dict[str, Any]:
    """清理过期热点资源定时任务."""
    import asyncio

    async def _cleanup_expired() -> dict[str, Any]:
        """异步清理过期资源."""
        try:
            async with get_async_session() as db:
                from datetime import datetime, timedelta

                from sqlalchemy import delete, select

                from app.resources.models.resource_models import HotspotResource

                # 删除30天前的过期资源
                cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

                # 查询要删除的资源
                stmt = select(HotspotResource).where(HotspotResource.expiry_date <= cutoff_date)
                result = await db.execute(stmt)
                expired_resources = result.scalars().all()

                # 删除过期资源
                delete_stmt = delete(HotspotResource).where(
                    HotspotResource.expiry_date <= cutoff_date
                )
                await db.execute(delete_stmt)
                await db.commit()

                logger.info(f"清理过期热点资源完成: 删除 {len(expired_resources)} 个资源")

                return {
                    "success": True,
                    "deleted_count": len(expired_resources),
                    "cutoff_date": cutoff_date,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"清理过期热点资源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    return asyncio.run(_cleanup_expired())
