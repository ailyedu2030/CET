"""词汇库管理服务."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.resources.models.resource_models import ResourceLibrary, VocabularyItem
from app.resources.schemas.resource_schemas import (
    VocabularyBatchImport,
    VocabularyItemCreate,
    VocabularyItemUpdate,
    VocabularySearchRequest,
)
from app.shared.models.enums import DifficultyLevel


class VocabularyService:
    """词汇库管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_vocabulary_item(
        self, vocabulary_data: VocabularyItemCreate, user_id: int
    ) -> VocabularyItem:
        """创建词汇条目."""
        # 检查资源库是否存在
        library = await self._get_library_by_id(vocabulary_data.library_id)
        if not library:
            raise ValueError(f"Resource library {vocabulary_data.library_id} not found")

        # 检查词汇是否已存在
        existing = await self._check_vocabulary_exists(
            vocabulary_data.library_id, vocabulary_data.word
        )
        if existing:
            raise ValueError(f"Vocabulary '{vocabulary_data.word}' already exists")

        # 创建词汇条目
        vocabulary_item = VocabularyItem(**vocabulary_data.model_dump())
        self.db.add(vocabulary_item)
        await self.db.commit()
        await self.db.refresh(vocabulary_item)

        # 更新资源库统计
        await self._update_library_stats(vocabulary_data.library_id)

        return vocabulary_item

    async def get_vocabulary_item(self, vocabulary_id: int) -> VocabularyItem | None:
        """获取词汇条目."""
        stmt = select(VocabularyItem).where(VocabularyItem.id == vocabulary_id)
        result = await self.db.execute(stmt)
        vocabulary_item: VocabularyItem | None = result.scalar_one_or_none()
        return vocabulary_item

    async def update_vocabulary_item(
        self,
        vocabulary_id: int,
        vocabulary_data: VocabularyItemUpdate,
        user_id: int,
    ) -> VocabularyItem | None:
        """更新词汇条目."""
        vocabulary_item = await self.get_vocabulary_item(vocabulary_id)
        if not vocabulary_item:
            return None

        # 更新字段
        for field, value in vocabulary_data.model_dump(exclude_unset=True).items():
            setattr(vocabulary_item, field, value)

        await self.db.commit()
        await self.db.refresh(vocabulary_item)
        return vocabulary_item

    async def delete_vocabulary_item(self, vocabulary_id: int, user_id: int) -> bool:
        """删除词汇条目."""
        vocabulary_item = await self.get_vocabulary_item(vocabulary_id)
        if not vocabulary_item:
            return False

        library_id = vocabulary_item.library_id
        await self.db.delete(vocabulary_item)
        await self.db.commit()

        # 更新资源库统计
        await self._update_library_stats(library_id)
        return True

    async def search_vocabularies(
        self, search_request: VocabularySearchRequest
    ) -> tuple[list[VocabularyItem], int]:
        """搜索词汇条目."""
        # 构建查询
        stmt = select(VocabularyItem)

        # 添加筛选条件
        if search_request.library_id:
            stmt = stmt.where(VocabularyItem.library_id == search_request.library_id)

        if search_request.keyword:
            keyword = f"%{search_request.keyword}%"
            stmt = stmt.where(
                or_(
                    VocabularyItem.word.ilike(keyword),
                    VocabularyItem.chinese_meaning.ilike(keyword),
                    VocabularyItem.english_meaning.ilike(keyword),
                )
            )

        if search_request.difficulty_level:
            stmt = stmt.where(VocabularyItem.difficulty_level == search_request.difficulty_level)

        if search_request.tags:
            # 使用PostgreSQL的JSON操作符
            for tag in search_request.tags:
                stmt = stmt.where(VocabularyItem.tags.op("@>")([tag]))

        if search_request.is_key_word is not None:
            stmt = stmt.where(VocabularyItem.is_key_word == search_request.is_key_word)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total: int = total_result.scalar() or 0

        # 添加排序
        if search_request.sort_by == "word":
            order_col = VocabularyItem.word
        elif search_request.sort_by == "difficulty_level":
            order_col = VocabularyItem.difficulty_level
        elif search_request.sort_by == "frequency":
            order_col = VocabularyItem.frequency
        elif search_request.sort_by == "mastery_level":
            order_col = VocabularyItem.mastery_level
        else:
            order_col = VocabularyItem.created_at

        if search_request.sort_order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)

        # 分页
        offset = (search_request.page - 1) * search_request.page_size
        stmt = stmt.offset(offset).limit(search_request.page_size)

        # 执行查询
        result = await self.db.execute(stmt)
        vocabularies = list(result.scalars().all())

        return vocabularies, total

    async def batch_import_vocabularies(
        self, import_data: VocabularyBatchImport, user_id: int
    ) -> dict[str, Any]:
        """批量导入词汇."""
        # 检查资源库是否存在
        library = await self._get_library_by_id(import_data.library_id)
        if not library:
            raise ValueError(f"Resource library {import_data.library_id} not found")

        results: dict[str, Any] = {
            "total": len(import_data.items),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        for item_data in import_data.items:
            try:
                # 检查词汇是否已存在
                existing = await self._check_vocabulary_exists(
                    import_data.library_id, item_data.word
                )

                if existing:
                    if import_data.overwrite_existing:
                        # 更新现有词汇
                        for field, value in item_data.model_dump().items():
                            if value is not None:
                                setattr(existing, field, value)
                        results["success"] += 1
                    else:
                        results["skipped"] += 1
                        continue
                else:
                    # 创建新词汇
                    vocabulary_item = VocabularyItem(
                        library_id=import_data.library_id,
                        **item_data.model_dump(),
                    )
                    self.db.add(vocabulary_item)
                    results["success"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Word '{item_data.word}': {str(e)}")

        await self.db.commit()

        # 更新资源库统计
        await self._update_library_stats(import_data.library_id)

        return results

    async def get_vocabulary_statistics(self, library_id: int | None = None) -> dict[str, Any]:
        """获取词汇统计信息."""
        stmt = select(VocabularyItem)
        if library_id:
            stmt = stmt.where(VocabularyItem.library_id == library_id)

        result = await self.db.execute(stmt)
        vocabularies = list(result.scalars().all())

        # 统计不同难度级别的词汇数量
        difficulty_stats = {}
        for level in DifficultyLevel:
            difficulty_stats[level.value] = sum(
                1 for v in vocabularies if v.difficulty_level == level
            )

        # 统计掌握程度
        mastery_levels = [v.mastery_level for v in vocabularies]
        avg_mastery = sum(mastery_levels) / len(mastery_levels) if mastery_levels else 0

        # 关键词统计
        key_words_count = sum(1 for v in vocabularies if v.is_key_word)

        # 频率统计
        high_frequency_count = sum(1 for v in vocabularies if v.frequency > 100)
        medium_frequency_count = sum(1 for v in vocabularies if 50 <= v.frequency <= 100)
        low_frequency_count = sum(1 for v in vocabularies if v.frequency < 50)

        return {
            "total_count": len(vocabularies),
            "difficulty_distribution": difficulty_stats,
            "average_mastery_level": float(avg_mastery),
            "key_words_count": key_words_count,
            "frequency_distribution": {
                "high": high_frequency_count,
                "medium": medium_frequency_count,
                "low": low_frequency_count,
            },
            "review_statistics": {
                "total_reviews": sum(v.review_count for v in vocabularies),
                "average_reviews": (
                    sum(v.review_count for v in vocabularies) / len(vocabularies)
                    if vocabularies
                    else 0
                ),
            },
        }

    async def update_mastery_level(
        self, vocabulary_id: int, mastery_level: float, user_id: int
    ) -> bool:
        """更新词汇掌握程度."""
        vocabulary_item = await self.get_vocabulary_item(vocabulary_id)
        if not vocabulary_item:
            return False

        vocabulary_item.mastery_level = mastery_level
        vocabulary_item.review_count += 1
        await self.db.commit()
        return True

    async def get_review_schedule(
        self, library_id: int, user_id: int, limit: int = 50
    ) -> list[VocabularyItem]:
        """获取复习计划 - 根据掌握程度推荐需要复习的词汇."""
        # 优先复习掌握程度低的词汇
        stmt = (
            select(VocabularyItem)
            .where(VocabularyItem.library_id == library_id)
            .order_by(VocabularyItem.mastery_level.asc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_library_by_id(self, library_id: int) -> ResourceLibrary | None:
        """获取资源库."""
        stmt = select(ResourceLibrary).where(ResourceLibrary.id == library_id)
        result = await self.db.execute(stmt)
        library: ResourceLibrary | None = result.scalar_one_or_none()
        return library

    async def _check_vocabulary_exists(self, library_id: int, word: str) -> VocabularyItem | None:
        """检查词汇是否已存在."""
        stmt = select(VocabularyItem).where(
            and_(VocabularyItem.library_id == library_id, VocabularyItem.word == word)
        )
        result = await self.db.execute(stmt)
        vocabulary_item: VocabularyItem | None = result.scalar_one_or_none()
        return vocabulary_item

    async def _update_library_stats(self, library_id: int) -> None:
        """更新资源库统计信息."""
        # 更新资源库统计信息（如果需要可以添加统计字段到模型）
        # 暂时跳过，因为ResourceLibrary模型没有total_items字段
        pass
