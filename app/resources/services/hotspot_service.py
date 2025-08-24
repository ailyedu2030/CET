"""热点资源池管理服务."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.resources.models.resource_models import HotspotResource, ResourceLibrary
from app.resources.schemas.resource_schemas import (
    HotspotResourceCreate,
    HotspotResourceSearchRequest,
    HotspotResourceUpdate,
)
from app.shared.models.enums import DifficultyLevel


class HotspotService:
    """热点资源池管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_hotspot_resource(
        self, hotspot_data: HotspotResourceCreate, user_id: int
    ) -> HotspotResource:
        """创建热点资源."""
        # 检查资源库是否存在
        library = await self._get_library_by_id(hotspot_data.library_id)
        if not library:
            raise ValueError(f"Resource library {hotspot_data.library_id} not found")

        # 自动计算热度分数
        popularity_score = await self._calculate_popularity_score(hotspot_data)

        # 自动计算相关性分数
        relevance_score = await self._calculate_relevance_score(
            hotspot_data, hotspot_data.library_id
        )

        # 创建热点资源
        hotspot_dict = hotspot_data.model_dump()
        hotspot_dict.update(
            {
                "popularity_score": popularity_score,
                "relevance_score": relevance_score,
                "engagement_rate": 0.0,  # 初始参与度为0
            }
        )

        hotspot_resource = HotspotResource(**hotspot_dict)
        self.db.add(hotspot_resource)
        await self.db.commit()
        await self.db.refresh(hotspot_resource)

        # 更新资源库统计
        await self._update_library_stats(hotspot_data.library_id)

        return hotspot_resource

    async def get_hotspot_resource(self, hotspot_id: int) -> HotspotResource | None:
        """获取热点资源."""
        stmt = select(HotspotResource).where(HotspotResource.id == hotspot_id)
        result = await self.db.execute(stmt)
        hotspot_resource: HotspotResource | None = result.scalar_one_or_none()
        return hotspot_resource

    async def update_hotspot_resource(
        self,
        hotspot_id: int,
        hotspot_data: HotspotResourceUpdate,
        user_id: int,
    ) -> HotspotResource | None:
        """更新热点资源."""
        hotspot_resource = await self.get_hotspot_resource(hotspot_id)
        if not hotspot_resource:
            return None

        # 更新字段
        for field, value in hotspot_data.model_dump(exclude_unset=True).items():
            setattr(hotspot_resource, field, value)

        # 重新计算分数
        if any(
            field in hotspot_data.model_dump(exclude_unset=True)
            for field in ["topics", "keywords", "source_type"]
        ):
            hotspot_resource.relevance_score = await self._calculate_relevance_score(
                hotspot_data, hotspot_resource.library_id
            )

        await self.db.commit()
        await self.db.refresh(hotspot_resource)
        return hotspot_resource

    async def delete_hotspot_resource(self, hotspot_id: int, user_id: int) -> bool:
        """删除热点资源."""
        hotspot_resource = await self.get_hotspot_resource(hotspot_id)
        if not hotspot_resource:
            return False

        library_id = hotspot_resource.library_id
        await self.db.delete(hotspot_resource)
        await self.db.commit()

        # 更新资源库统计
        await self._update_library_stats(library_id)
        return True

    async def search_hotspot_resources(
        self, search_request: HotspotResourceSearchRequest
    ) -> tuple[list[HotspotResource], int]:
        """搜索热点资源."""
        # 构建查询
        stmt = select(HotspotResource)

        # 添加筛选条件
        if search_request.library_id:
            stmt = stmt.where(HotspotResource.library_id == search_request.library_id)

        if search_request.keyword:
            keyword = f"%{search_request.keyword}%"
            stmt = stmt.where(
                or_(
                    HotspotResource.title.ilike(keyword),
                    HotspotResource.content_preview.ilike(keyword),
                    HotspotResource.author.ilike(keyword),
                )
            )

        if search_request.source_type:
            stmt = stmt.where(HotspotResource.source_type == search_request.source_type)

        if search_request.language:
            stmt = stmt.where(HotspotResource.language == search_request.language)

        if search_request.difficulty_level:
            stmt = stmt.where(HotspotResource.difficulty_level == search_request.difficulty_level)

        if search_request.topics:
            # 使用PostgreSQL的JSON操作符
            for topic in search_request.topics:
                stmt = stmt.where(HotspotResource.topics.op("@>")([topic]))

        if search_request.is_trending is not None:
            stmt = stmt.where(HotspotResource.is_trending == search_request.is_trending)

        if search_request.is_recommended is not None:
            stmt = stmt.where(HotspotResource.is_recommended == search_request.is_recommended)

        # 过滤未过期的资源
        current_date = datetime.now().strftime("%Y-%m-%d")
        stmt = stmt.where(
            or_(
                HotspotResource.expiry_date.is_(None),
                HotspotResource.expiry_date > current_date,
            )
        )

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total: int = total_result.scalar() or 0

        # 添加排序
        if search_request.sort_by == "title":
            order_col = HotspotResource.title
        elif search_request.sort_by == "view_count":
            order_col = HotspotResource.view_count
        elif search_request.sort_by == "publish_date":
            order_col = HotspotResource.publish_date
        elif search_request.sort_by == "relevance_score":
            order_col = HotspotResource.relevance_score
        elif search_request.sort_by == "engagement_rate":
            order_col = HotspotResource.engagement_rate
        else:
            order_col = HotspotResource.popularity_score

        if search_request.sort_order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)

        # 分页
        offset = (search_request.page - 1) * search_request.page_size
        stmt = stmt.offset(offset).limit(search_request.page_size)

        # 执行查询
        result = await self.db.execute(stmt)
        hotspots = list(result.scalars().all())

        return hotspots, total

    async def get_trending_resources(
        self, library_id: int | None = None, limit: int = 10
    ) -> list[HotspotResource]:
        """获取热门资源."""
        stmt = select(HotspotResource).where(HotspotResource.is_trending)

        if library_id:
            stmt = stmt.where(HotspotResource.library_id == library_id)

        stmt = stmt.order_by(
            desc(HotspotResource.popularity_score),
            desc(HotspotResource.view_count),
        ).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recommended_resources(
        self, library_id: int, user_preferences: dict[str, Any] | None = None
    ) -> list[HotspotResource]:
        """获取推荐资源."""
        stmt = select(HotspotResource).where(
            and_(
                HotspotResource.library_id == library_id,
                HotspotResource.is_recommended,
            )
        )

        # 根据用户偏好进一步筛选
        if user_preferences:
            if "difficulty_level" in user_preferences:
                stmt = stmt.where(
                    HotspotResource.difficulty_level == user_preferences["difficulty_level"]
                )
            if "topics" in user_preferences:
                for topic in user_preferences["topics"]:
                    stmt = stmt.where(HotspotResource.topics.op("@>")([topic]))
            if "language" in user_preferences:
                stmt = stmt.where(HotspotResource.language == user_preferences["language"])

        stmt = stmt.order_by(
            desc(HotspotResource.relevance_score),
            desc(HotspotResource.popularity_score),
        ).limit(20)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_engagement_metrics(
        self,
        hotspot_id: int,
        action: str,
        user_id: int | None = None,
    ) -> bool:
        """更新参与度指标."""
        hotspot_resource = await self.get_hotspot_resource(hotspot_id)
        if not hotspot_resource:
            return False

        # 根据操作类型更新对应指标
        if action == "view":
            hotspot_resource.view_count += 1
        elif action == "like":
            hotspot_resource.like_count += 1
        elif action == "share":
            hotspot_resource.share_count += 1
        elif action == "comment":
            hotspot_resource.comment_count += 1

        # 重新计算参与度
        total_interactions = (
            hotspot_resource.like_count
            + hotspot_resource.share_count
            + hotspot_resource.comment_count
        )

        if hotspot_resource.view_count > 0:
            hotspot_resource.engagement_rate = total_interactions / hotspot_resource.view_count

        # 重新计算热度分数
        hotspot_resource.popularity_score = await self._calculate_popularity_from_metrics(
            hotspot_resource
        )

        await self.db.commit()
        return True

    async def refresh_trending_status(self) -> None:
        """刷新热门状态 - 定期任务."""
        # 获取最近7天的热点资源
        _seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        # 重置所有资源的热门状态
        stmt = select(HotspotResource)
        result = await self.db.execute(stmt)
        all_hotspots = list(result.scalars().all())

        for hotspot in all_hotspots:
            # 计算是否为热门
            is_trending = (
                hotspot.popularity_score > 0.7
                and hotspot.engagement_rate > 0.1
                and hotspot.view_count > 100
            )

            hotspot.is_trending = is_trending

        await self.db.commit()

    async def auto_expire_resources(self) -> None:
        """自动过期资源 - 定期任务."""
        current_date = datetime.now().strftime("%Y-%m-%d")

        stmt = select(HotspotResource).where(
            and_(
                HotspotResource.expiry_date.is_not(None),
                HotspotResource.expiry_date <= current_date,
            )
        )

        result = await self.db.execute(stmt)
        expired_resources = list(result.scalars().all())

        for resource in expired_resources:
            resource.is_trending = False
            resource.is_recommended = False

        await self.db.commit()

    async def get_hotspot_statistics(self, library_id: int | None = None) -> dict[str, Any]:
        """获取热点资源统计信息."""
        stmt = select(HotspotResource)
        if library_id:
            stmt = stmt.where(HotspotResource.library_id == library_id)

        result = await self.db.execute(stmt)
        hotspots = list(result.scalars().all())

        # 来源类型分布
        source_stats: dict[str, int] = {}
        for hotspot in hotspots:
            source_type = hotspot.source_type
            source_stats[source_type] = source_stats.get(source_type, 0) + 1

        # 语言分布
        language_stats: dict[str, int] = {}
        for hotspot in hotspots:
            language = hotspot.language
            language_stats[language] = language_stats.get(language, 0) + 1

        # 难度分布
        difficulty_stats = {}
        for level in DifficultyLevel:
            difficulty_stats[level.value] = sum(1 for h in hotspots if h.difficulty_level == level)

        # 热门和推荐统计
        trending_count = sum(1 for h in hotspots if h.is_trending)
        recommended_count = sum(1 for h in hotspots if h.is_recommended)

        # 参与度统计
        total_views = sum(h.view_count for h in hotspots)
        total_likes = sum(h.like_count for h in hotspots)
        total_shares = sum(h.share_count for h in hotspots)
        total_comments = sum(h.comment_count for h in hotspots)

        avg_popularity = (
            sum(h.popularity_score for h in hotspots) / len(hotspots) if hotspots else 0
        )
        avg_relevance = sum(h.relevance_score for h in hotspots) / len(hotspots) if hotspots else 0
        avg_engagement = sum(h.engagement_rate for h in hotspots) / len(hotspots) if hotspots else 0

        return {
            "total_count": len(hotspots),
            "trending_count": trending_count,
            "recommended_count": recommended_count,
            "source_distribution": source_stats,
            "language_distribution": language_stats,
            "difficulty_distribution": difficulty_stats,
            "engagement_metrics": {
                "total_views": total_views,
                "total_likes": total_likes,
                "total_shares": total_shares,
                "total_comments": total_comments,
                "average_popularity_score": float(avg_popularity),
                "average_relevance_score": float(avg_relevance),
                "average_engagement_rate": float(avg_engagement),
            },
        }

    async def _calculate_popularity_score(self, hotspot_data: HotspotResourceCreate) -> float:
        """计算热度分数."""
        score = 0.0

        # 基于来源类型的权重
        source_weights = {
            "news": 0.8,
            "paper": 0.9,
            "blog": 0.6,
            "video": 0.7,
            "podcast": 0.5,
        }
        score += source_weights.get(hotspot_data.source_type, 0.5)

        # 基于内容长度
        if hotspot_data.full_content:
            content_length = len(hotspot_data.full_content)
            if content_length > 2000:
                score += 0.3
            elif content_length > 1000:
                score += 0.2
            else:
                score += 0.1

        # 基于关键词数量
        if hotspot_data.keywords:
            keyword_count = len(hotspot_data.keywords)
            score += min(keyword_count * 0.1, 0.5)

        # 基于话题数量
        if hotspot_data.topics:
            topic_count = len(hotspot_data.topics)
            score += min(topic_count * 0.1, 0.3)

        # 基于语法点
        if hotspot_data.grammar_points:
            grammar_count = len(hotspot_data.grammar_points)
            score += min(grammar_count * 0.05, 0.2)

        return min(score, 1.0)

    async def _calculate_relevance_score(self, hotspot_data: Any, library_id: int) -> float:
        """计算相关性分数."""
        # 这里可以基于资源库的主要话题、用户历史偏好等计算相关性
        # 暂时返回基础分数
        score = 0.5

        # 基于话题匹配度（需要与资源库的主要话题比较）
        if hasattr(hotspot_data, "topics") and hotspot_data.topics:
            score += min(len(hotspot_data.topics) * 0.1, 0.3)

        # 基于难度适配性
        if hasattr(hotspot_data, "difficulty_level"):
            score += 0.2  # 暂时固定加分

        return min(score, 1.0)

    async def _calculate_popularity_from_metrics(self, hotspot: HotspotResource) -> float:
        """基于指标计算热度分数."""
        score = 0.0

        # 浏览量权重
        if hotspot.view_count > 0:
            view_score = min(hotspot.view_count / 1000, 0.4)
            score += view_score

        # 点赞权重
        if hotspot.like_count > 0:
            like_score = min(hotspot.like_count / 100, 0.3)
            score += like_score

        # 分享权重
        if hotspot.share_count > 0:
            share_score = min(hotspot.share_count / 50, 0.2)
            score += share_score

        # 评论权重
        if hotspot.comment_count > 0:
            comment_score = min(hotspot.comment_count / 20, 0.1)
            score += comment_score

        return min(score, 1.0)

    async def _get_library_by_id(self, library_id: int) -> ResourceLibrary | None:
        """获取资源库."""
        stmt = select(ResourceLibrary).where(ResourceLibrary.id == library_id)
        result = await self.db.execute(stmt)
        library: ResourceLibrary | None = result.scalar_one_or_none()
        return library

    async def _update_library_stats(self, library_id: int) -> None:
        """更新资源库统计信息."""
        # 更新资源库统计信息（如果需要可以添加统计字段到模型）
        # 暂时跳过，因为ResourceLibrary模型没有total_items字段
        pass
