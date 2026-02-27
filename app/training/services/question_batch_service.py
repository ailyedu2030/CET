"""题目批次管理服务."""

import logging
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import DifficultyLevel, TrainingType
from app.training.models.training_models import QuestionBatch
from app.training.schemas.training_schemas import (
    PaginatedResponse,
    QuestionBatchListResponse,
    QuestionBatchRequest,
    QuestionBatchResponse,
)

logger = logging.getLogger(__name__)


class QuestionBatchService:
    """题目批次管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_question_batch(
        self, request: QuestionBatchRequest, created_by: int
    ) -> QuestionBatchResponse:
        """创建题目批次."""
        try:
            # 创建题目批次
            batch = QuestionBatch(
                name=request.name,
                description=request.description,
                training_type=request.training_type,
                difficulty_level=request.difficulty_level,
                question_count=request.question_count,
                time_limit=request.time_limit,
                knowledge_points=request.knowledge_points,
                tags=request.tags,
                is_active=True,
                created_by=created_by,
            )

            self.db.add(batch)
            await self.db.commit()
            await self.db.refresh(batch)

            logger.info(f"成功创建题目批次: {batch.id}")

            return QuestionBatchResponse(
                id=batch.id,
                name=batch.name,
                description=batch.description,
                training_type=batch.training_type,
                difficulty_level=batch.difficulty_level,
                question_count=batch.question_count,
                time_limit=batch.time_limit,
                knowledge_points=batch.knowledge_points,
                tags=batch.tags,
                is_active=batch.is_active,
                created_by=batch.created_by,
                created_at=batch.created_at,
                updated_at=batch.updated_at,
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建题目批次失败: {str(e)}")
            raise

    async def get_question_batches(
        self,
        training_type: TrainingType | None = None,
        difficulty_level: DifficultyLevel | None = None,
        page: int = 1,
        page_size: int = 20,
        created_by: int | None = None,
    ) -> QuestionBatchListResponse:
        """获取题目批次列表."""
        try:
            # 构建查询条件
            conditions = [QuestionBatch.is_active == True]  # noqa: E712

            if training_type:
                conditions.append(QuestionBatch.training_type == training_type)

            if difficulty_level:
                conditions.append(QuestionBatch.difficulty_level == difficulty_level)

            if created_by:
                conditions.append(QuestionBatch.created_by == created_by)

            # 查询总数
            count_query = select(func.count(QuestionBatch.id)).where(and_(*conditions))
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # 查询数据
            offset = (page - 1) * page_size
            query = (
                select(QuestionBatch)
                .where(and_(*conditions))
                .order_by(QuestionBatch.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(query)
            batches = result.scalars().all()

            # 构建响应
            batch_responses = []
            for batch in batches:
                batch_responses.append(
                    QuestionBatchResponse(
                        id=batch.id,
                        name=batch.name,
                        description=batch.description,
                        training_type=batch.training_type,
                        difficulty_level=batch.difficulty_level,
                        question_count=batch.question_count,
                        time_limit=batch.time_limit,
                        knowledge_points=batch.knowledge_points,
                        tags=batch.tags,
                        is_active=batch.is_active,
                        created_by=batch.created_by,
                        created_at=batch.created_at,
                        updated_at=batch.updated_at,
                    )
                )

            pagination = PaginatedResponse(
                page=page,
                size=page_size,
                total=total,
                pages=(total + page_size - 1) // page_size,
                page_size=page_size,
                total_items=total,
                total_pages=(total + page_size - 1) // page_size,
            )

            return QuestionBatchListResponse(batches=batch_responses, pagination=pagination)

        except Exception as e:
            logger.error(f"获取题目批次列表失败: {str(e)}")
            raise

    async def get_question_batch_by_id(self, batch_id: int) -> QuestionBatchResponse | None:
        """根据ID获取题目批次."""
        try:
            query = select(QuestionBatch).where(
                and_(QuestionBatch.id == batch_id, QuestionBatch.is_active == True)  # noqa: E712
            )
            result = await self.db.execute(query)
            batch = result.scalar_one_or_none()

            if not batch:
                return None

            return QuestionBatchResponse(
                id=batch.id,
                name=batch.name,
                description=batch.description,
                training_type=batch.training_type,
                difficulty_level=batch.difficulty_level,
                question_count=batch.question_count,
                time_limit=batch.time_limit,
                knowledge_points=batch.knowledge_points,
                tags=batch.tags,
                is_active=batch.is_active,
                created_by=batch.created_by,
                created_at=batch.created_at,
                updated_at=batch.updated_at,
            )

        except Exception as e:
            logger.error(f"获取题目批次失败: {str(e)}")
            raise

    async def update_question_batch(
        self, batch_id: int, request: QuestionBatchRequest, updated_by: int
    ) -> QuestionBatchResponse | None:
        """更新题目批次."""
        try:
            query = select(QuestionBatch).where(
                and_(QuestionBatch.id == batch_id, QuestionBatch.is_active == True)  # noqa: E712
            )
            result = await self.db.execute(query)
            batch = result.scalar_one_or_none()

            if not batch:
                return None

            # 更新字段
            batch.name = request.name
            batch.description = request.description
            batch.training_type = request.training_type
            batch.difficulty_level = request.difficulty_level
            batch.question_count = request.question_count
            batch.time_limit = request.time_limit
            batch.knowledge_points = request.knowledge_points
            batch.tags = request.tags
            batch.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(batch)

            logger.info(f"成功更新题目批次: {batch.id}")

            return QuestionBatchResponse(
                id=batch.id,
                name=batch.name,
                description=batch.description,
                training_type=batch.training_type,
                difficulty_level=batch.difficulty_level,
                question_count=batch.question_count,
                time_limit=batch.time_limit,
                knowledge_points=batch.knowledge_points,
                tags=batch.tags,
                is_active=batch.is_active,
                created_by=batch.created_by,
                created_at=batch.created_at,
                updated_at=batch.updated_at,
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新题目批次失败: {str(e)}")
            raise

    async def delete_question_batch(self, batch_id: int) -> bool:
        """删除题目批次（软删除）."""
        try:
            query = select(QuestionBatch).where(
                and_(QuestionBatch.id == batch_id, QuestionBatch.is_active == True)  # noqa: E712
            )
            result = await self.db.execute(query)
            batch = result.scalar_one_or_none()

            if not batch:
                return False

            # 软删除
            batch.is_active = False
            batch.updated_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"成功删除题目批次: {batch.id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除题目批次失败: {str(e)}")
            raise

    async def batch_create_question_batches(
        self, requests: list[QuestionBatchRequest], created_by: int
    ) -> list[QuestionBatchResponse]:
        """批量创建题目批次."""
        try:
            batch_responses = []

            for request in requests:
                batch = QuestionBatch(
                    name=request.name,
                    description=request.description,
                    training_type=request.training_type,
                    difficulty_level=request.difficulty_level,
                    question_count=request.question_count,
                    time_limit=request.time_limit,
                    knowledge_points=request.knowledge_points,
                    tags=request.tags,
                    is_active=True,
                    created_by=created_by,
                )

                self.db.add(batch)

            await self.db.commit()

            # 刷新所有批次并构建响应
            for batch in self.db.new:
                if isinstance(batch, QuestionBatch):
                    await self.db.refresh(batch)
                    batch_responses.append(
                        QuestionBatchResponse(
                            id=batch.id,
                            name=batch.name,
                            description=batch.description,
                            training_type=batch.training_type,
                            difficulty_level=batch.difficulty_level,
                            question_count=batch.question_count,
                            time_limit=batch.time_limit,
                            knowledge_points=batch.knowledge_points,
                            tags=batch.tags,
                            is_active=batch.is_active,
                            created_by=batch.created_by,
                            created_at=batch.created_at,
                            updated_at=batch.updated_at,
                        )
                    )

            logger.info(f"成功批量创建 {len(batch_responses)} 个题目批次")
            return batch_responses

        except Exception as e:
            await self.db.rollback()
            logger.error(f"批量创建题目批次失败: {str(e)}")
            raise
