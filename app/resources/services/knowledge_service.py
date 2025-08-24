"""知识点库管理服务."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.resources.models.resource_models import KnowledgePoint, ResourceLibrary
from app.resources.schemas.resource_schemas import (
    KnowledgePointCreate,
    KnowledgePointSearchRequest,
    KnowledgePointUpdate,
)
from app.shared.models.enums import DifficultyLevel


class KnowledgeService:
    """知识点库管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_knowledge_point(
        self, knowledge_data: KnowledgePointCreate, user_id: int
    ) -> KnowledgePoint:
        """创建知识点."""
        # 检查资源库是否存在
        library = await self._get_library_by_id(knowledge_data.library_id)
        if not library:
            raise ValueError(f"Resource library {knowledge_data.library_id} not found")

        # 如果有父知识点，检查是否存在
        if knowledge_data.parent_id:
            parent = await self.get_knowledge_point(knowledge_data.parent_id)
            if not parent:
                raise ValueError(f"Parent knowledge point {knowledge_data.parent_id} not found")
            # 检查父知识点是否属于同一资源库
            if parent.library_id != knowledge_data.library_id:
                raise ValueError("Parent knowledge point must belong to the same library")

        # 检查知识点标题是否已存在（同一资源库内）
        existing = await self._check_knowledge_point_exists(
            knowledge_data.library_id, knowledge_data.title, knowledge_data.parent_id
        )
        if existing:
            raise ValueError(f"Knowledge point '{knowledge_data.title}' already exists")

        # 创建知识点
        knowledge_point = KnowledgePoint(**knowledge_data.model_dump())
        self.db.add(knowledge_point)
        await self.db.commit()
        await self.db.refresh(knowledge_point)

        # 更新资源库统计
        await self._update_library_stats(knowledge_data.library_id)

        return knowledge_point

    async def get_knowledge_point(
        self, knowledge_id: int, include_children: bool = False
    ) -> KnowledgePoint | None:
        """获取知识点."""
        stmt = select(KnowledgePoint).where(KnowledgePoint.id == knowledge_id)

        if include_children:
            stmt = stmt.options(selectinload(KnowledgePoint.children))

        result = await self.db.execute(stmt)
        knowledge_point: KnowledgePoint | None = result.scalar_one_or_none()
        return knowledge_point

    async def update_knowledge_point(
        self,
        knowledge_id: int,
        knowledge_data: KnowledgePointUpdate,
        user_id: int,
    ) -> KnowledgePoint | None:
        """更新知识点."""
        knowledge_point = await self.get_knowledge_point(knowledge_id)
        if not knowledge_point:
            return None

        # 更新字段
        for field, value in knowledge_data.model_dump(exclude_unset=True).items():
            setattr(knowledge_point, field, value)

        await self.db.commit()
        await self.db.refresh(knowledge_point)
        return knowledge_point

    async def delete_knowledge_point(self, knowledge_id: int, user_id: int) -> bool:
        """删除知识点（级联删除子知识点）."""
        knowledge_point = await self.get_knowledge_point(knowledge_id, include_children=True)
        if not knowledge_point:
            return False

        library_id = knowledge_point.library_id
        await self.db.delete(knowledge_point)
        await self.db.commit()

        # 更新资源库统计
        await self._update_library_stats(library_id)
        return True

    async def search_knowledge_points(
        self, search_request: KnowledgePointSearchRequest
    ) -> tuple[list[KnowledgePoint], int]:
        """搜索知识点."""
        # 构建查询
        stmt = select(KnowledgePoint)

        # 添加筛选条件
        if search_request.library_id:
            stmt = stmt.where(KnowledgePoint.library_id == search_request.library_id)

        if search_request.keyword:
            keyword = f"%{search_request.keyword}%"
            stmt = stmt.where(
                or_(
                    KnowledgePoint.title.ilike(keyword),
                    KnowledgePoint.content.ilike(keyword),
                    KnowledgePoint.description.ilike(keyword),
                )
            )

        if search_request.category:
            stmt = stmt.where(KnowledgePoint.category == search_request.category)

        if search_request.difficulty_level:
            stmt = stmt.where(KnowledgePoint.difficulty_level == search_request.difficulty_level)

        if search_request.is_core is not None:
            stmt = stmt.where(KnowledgePoint.is_core == search_request.is_core)

        if search_request.parent_id is not None:
            stmt = stmt.where(KnowledgePoint.parent_id == search_request.parent_id)

        if search_request.tags:
            # 使用PostgreSQL的JSON操作符
            for tag in search_request.tags:
                stmt = stmt.where(KnowledgePoint.tags.op("@>")([tag]))

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total: int = total_result.scalar() or 0

        # 添加排序
        if search_request.sort_by == "title":
            order_col = KnowledgePoint.title
        elif search_request.sort_by == "difficulty_level":
            order_col = KnowledgePoint.difficulty_level
        elif search_request.sort_by == "estimated_time":
            order_col = KnowledgePoint.estimated_time
        elif search_request.sort_by == "importance_score":
            order_col = KnowledgePoint.importance_score
        else:
            order_col = KnowledgePoint.importance_score

        if search_request.sort_order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)

        # 分页
        offset = (search_request.page - 1) * search_request.page_size
        stmt = stmt.offset(offset).limit(search_request.page_size)

        # 执行查询
        result = await self.db.execute(stmt)
        knowledge_points = list(result.scalars().all())

        return knowledge_points, total

    async def get_knowledge_tree(
        self, library_id: int, parent_id: int | None = None
    ) -> list[dict[str, Any]]:
        """获取知识点树形结构 - 优化版本，避免N+1查询."""
        # 一次性获取所有知识点，避免N+1查询
        stmt = (
            select(KnowledgePoint)
            .where(KnowledgePoint.library_id == library_id)
            .order_by(KnowledgePoint.importance_score.desc())
        )

        result = await self.db.execute(stmt)
        all_knowledge_points = list(result.scalars().all())

        # 构建父子关系映射
        children_map: dict[int | None, list[KnowledgePoint]] = {}
        for kp in all_knowledge_points:
            if kp.parent_id not in children_map:
                children_map[kp.parent_id] = []
            children_map[kp.parent_id].append(kp)

        def build_tree_recursive(current_parent_id: int | None) -> list[dict[str, Any]]:
            """递归构建树形结构."""
            if current_parent_id not in children_map:
                return []

            tree = []
            for kp in children_map[current_parent_id]:
                children = build_tree_recursive(kp.id)
                tree.append(
                    {
                        "id": kp.id,
                        "title": kp.title,
                        "category": kp.category,
                        "difficulty_level": kp.difficulty_level,
                        "importance_score": kp.importance_score,
                        "is_core": kp.is_core,
                        "estimated_time": kp.estimated_time,
                        "children": children,
                    }
                )
            return tree

        return build_tree_recursive(parent_id)

    async def get_prerequisite_chain(self, knowledge_id: int) -> list[KnowledgePoint]:
        """获取知识点的前置依赖链."""
        knowledge_point = await self.get_knowledge_point(knowledge_id)
        if not knowledge_point or not knowledge_point.prerequisite_points:
            return []

        # 获取前置知识点
        prerequisite_ids = knowledge_point.prerequisite_points
        stmt = select(KnowledgePoint).where(KnowledgePoint.id.in_(prerequisite_ids))
        result = await self.db.execute(stmt)
        prerequisites = list(result.scalars().all())

        # 递归获取前置知识点的前置依赖
        all_prerequisites = list(prerequisites)
        for prereq in prerequisites:
            chain = await self.get_prerequisite_chain(prereq.id)
            all_prerequisites.extend(chain)

        # 去重并按重要性排序
        seen = set()
        unique_prerequisites = []
        for kp in all_prerequisites:
            if kp.id not in seen:
                seen.add(kp.id)
                unique_prerequisites.append(kp)

        unique_prerequisites.sort(key=lambda x: x.importance_score, reverse=True)
        return unique_prerequisites

    async def get_related_knowledge_points(self, knowledge_id: int) -> list[KnowledgePoint]:
        """获取相关知识点."""
        knowledge_point = await self.get_knowledge_point(knowledge_id)
        if not knowledge_point or not knowledge_point.related_points:
            return []

        related_ids = knowledge_point.related_points
        stmt = (
            select(KnowledgePoint)
            .where(KnowledgePoint.id.in_(related_ids))
            .order_by(KnowledgePoint.importance_score.desc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_learning_path(
        self, library_id: int, target_knowledge_id: int
    ) -> list[dict[str, Any]]:
        """生成学习路径."""
        target = await self.get_knowledge_point(target_knowledge_id)
        if not target or target.library_id != library_id:
            return []

        # 获取前置知识点
        prerequisites = await self.get_prerequisite_chain(target_knowledge_id)

        # 构建学习路径
        path = []

        # 添加前置知识点
        for i, kp in enumerate(prerequisites):
            path.append(
                {
                    "step": i + 1,
                    "knowledge_point_id": kp.id,
                    "title": kp.title,
                    "difficulty_level": kp.difficulty_level,
                    "estimated_time": kp.estimated_time,
                    "importance_score": kp.importance_score,
                    "is_core": kp.is_core,
                    "type": "prerequisite",
                }
            )

        # 添加目标知识点
        path.append(
            {
                "step": len(path) + 1,
                "knowledge_point_id": target.id,
                "title": target.title,
                "difficulty_level": target.difficulty_level,
                "estimated_time": target.estimated_time,
                "importance_score": target.importance_score,
                "is_core": target.is_core,
                "type": "target",
            }
        )

        # 添加相关知识点作为扩展学习
        related = await self.get_related_knowledge_points(target_knowledge_id)
        for kp in related[:3]:  # 最多添加3个相关知识点
            path.append(
                {
                    "step": len(path) + 1,
                    "knowledge_point_id": kp.id,
                    "title": kp.title,
                    "difficulty_level": kp.difficulty_level,
                    "estimated_time": kp.estimated_time,
                    "importance_score": kp.importance_score,
                    "is_core": kp.is_core,
                    "type": "extension",
                }
            )

        return path

    async def get_knowledge_statistics(self, library_id: int | None = None) -> dict[str, Any]:
        """获取知识点统计信息."""
        stmt = select(KnowledgePoint)
        if library_id:
            stmt = stmt.where(KnowledgePoint.library_id == library_id)

        result = await self.db.execute(stmt)
        knowledge_points = list(result.scalars().all())

        # 统计不同难度级别的知识点数量
        difficulty_stats = {}
        for level in DifficultyLevel:
            difficulty_stats[level.value] = sum(
                1 for kp in knowledge_points if kp.difficulty_level == level
            )

        # 分类统计
        category_stats: dict[str, int] = {}
        for kp in knowledge_points:
            category = kp.category or "未分类"
            category_stats[category] = category_stats.get(category, 0) + 1

        # 核心知识点统计
        core_count = sum(1 for kp in knowledge_points if kp.is_core)

        # 重要性分布
        importance_scores = [kp.importance_score for kp in knowledge_points]
        avg_importance = sum(importance_scores) / len(importance_scores) if importance_scores else 0

        # 预估学习时间统计
        total_time = sum(kp.estimated_time for kp in knowledge_points)
        avg_time = total_time / len(knowledge_points) if knowledge_points else 0

        return {
            "total_count": len(knowledge_points),
            "difficulty_distribution": difficulty_stats,
            "category_distribution": category_stats,
            "core_knowledge_count": core_count,
            "average_importance_score": float(avg_importance),
            "total_estimated_time": total_time,
            "average_estimated_time": float(avg_time),
            "knowledge_with_prerequisites": sum(
                1 for kp in knowledge_points if kp.prerequisite_points
            ),
            "knowledge_with_exercises": sum(1 for kp in knowledge_points if kp.exercises),
        }

    async def _get_library_by_id(self, library_id: int) -> ResourceLibrary | None:
        """获取资源库."""
        stmt = select(ResourceLibrary).where(ResourceLibrary.id == library_id)
        result = await self.db.execute(stmt)
        library: ResourceLibrary | None = result.scalar_one_or_none()
        return library

    async def _check_knowledge_point_exists(
        self, library_id: int, title: str, parent_id: int | None
    ) -> KnowledgePoint | None:
        """检查知识点是否已存在."""
        stmt = select(KnowledgePoint).where(
            and_(
                KnowledgePoint.library_id == library_id,
                KnowledgePoint.title == title,
                KnowledgePoint.parent_id == parent_id,
            )
        )
        result = await self.db.execute(stmt)
        knowledge_point: KnowledgePoint | None = result.scalar_one_or_none()
        return knowledge_point

    async def _update_library_stats(self, library_id: int) -> None:
        """更新资源库统计信息."""
        # 更新资源库统计信息（如果需要可以添加统计字段到模型）
        # 暂时跳过，因为ResourceLibrary模型没有total_items字段
        pass
