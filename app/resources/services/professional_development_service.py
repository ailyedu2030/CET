"""专业发展支持服务 - 需求17实现."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import ColumnElement

from app.resources.models.professional_development_models import (
    CertificationMaterial,
    CommunityPost,
    LearningProgress,
    NotificationSettings,
    ResearchUpdate,
    TrainingEnrollment,
    TrainingResource,
)
from app.resources.schemas.professional_development_schemas import (
    NotificationSettingsUpdate,
)
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class ProfessionalDevelopmentService:
    """专业发展支持服务类."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化服务."""
        self.db = db

    # ==================== 培训资源管理 ====================

    async def get_training_resources(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """获取培训资源列表."""
        try:
            # 构建查询条件
            conditions = [TrainingResource.is_active == True]  # noqa: E712

            if category:
                conditions.append(TrainingResource.category == category)

            if difficulty:
                conditions.append(TrainingResource.difficulty == difficulty)

            if search:
                search_condition = or_(
                    TrainingResource.title.ilike(f"%{search}%"),
                    TrainingResource.description.ilike(f"%{search}%"),
                    TrainingResource.instructor.ilike(f"%{search}%"),
                )
                conditions.append(search_condition)

            # 查询总数
            count_query = select(func.count(TrainingResource.id)).where(and_(*conditions))
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # 查询数据
            offset = (page - 1) * page_size
            query = (
                select(TrainingResource)
                .where(and_(*conditions))
                .order_by(desc(TrainingResource.created_at))
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(query)
            resources = result.scalars().all()

            # 如果提供了用户ID，查询用户的报名状态和进度
            resource_data = []
            for resource in resources:
                resource_dict = {
                    "id": resource.id,
                    "title": resource.title,
                    "description": resource.description,
                    "category": resource.category,
                    "duration": resource.duration,
                    "difficulty": resource.difficulty.value,
                    "instructor": resource.instructor,
                    "enrolled_count": resource.enrolled_count,
                    "rating": resource.rating,
                    "rating_count": resource.rating_count,
                    "tags": resource.tags,
                    "created_at": resource.created_at,
                    "updated_at": resource.updated_at,
                    "is_enrolled": False,
                    "progress": 0.0,
                }

                if user_id:
                    enrollment_query = select(TrainingEnrollment).where(
                        and_(
                            TrainingEnrollment.training_id == resource.id,
                            TrainingEnrollment.user_id == user_id,
                        )
                    )
                    enrollment_result = await self.db.execute(enrollment_query)
                    enrollment = enrollment_result.scalar_one_or_none()

                    if enrollment:
                        resource_dict["is_enrolled"] = True
                        resource_dict["progress"] = enrollment.progress

                resource_data.append(resource_dict)

            # 获取分类列表
            categories_query = select(TrainingResource.category.distinct()).where(
                TrainingResource.is_active == True  # noqa: E712
            )
            categories_result = await self.db.execute(categories_query)
            categories = [cat for cat in categories_result.scalars().all() if cat]

            return {
                "resources": resource_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"Get training resources failed: {str(e)}")
            raise

    async def enroll_training(
        self,
        training_id: int,
        user_id: int,
        motivation: str | None = None,
    ) -> dict[str, Any]:
        """报名培训课程."""
        try:
            # 检查培训是否存在
            training_query = select(TrainingResource).where(TrainingResource.id == training_id)
            training_result = await self.db.execute(training_query)
            training = training_result.scalar_one_or_none()

            if not training:
                raise ValueError("培训课程不存在")

            # 检查是否已经报名
            existing_query = select(TrainingEnrollment).where(
                and_(
                    TrainingEnrollment.training_id == training_id,
                    TrainingEnrollment.user_id == user_id,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                raise ValueError("您已经报名了该培训课程")

            # 创建报名记录
            enrollment = TrainingEnrollment(
                training_id=training_id,
                user_id=user_id,
                motivation=motivation,
                enrolled_at=datetime.utcnow(),
            )

            self.db.add(enrollment)

            # 更新培训的报名人数
            training.enrolled_count += 1

            await self.db.commit()

            return {
                "enrollment_id": enrollment.id,
                "training_title": training.title,
                "enrolled_at": enrollment.enrolled_at,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Enroll training failed: {str(e)}")
            raise

    async def get_training_progress(
        self,
        training_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """获取培训进度."""
        try:
            query = select(TrainingEnrollment).where(
                and_(
                    TrainingEnrollment.training_id == training_id,
                    TrainingEnrollment.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            enrollment = result.scalar_one_or_none()

            if not enrollment:
                raise ValueError("未找到报名记录")

            return {
                "progress": enrollment.progress,
                "completed_lessons": enrollment.completed_lessons,
                "total_lessons": enrollment.total_lessons,
                "last_accessed_at": enrollment.last_accessed_at,
            }

        except Exception as e:
            logger.error(f"Get training progress failed: {str(e)}")
            raise

    # ==================== 认证辅导材料 ====================

    async def get_certification_materials(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        material_type: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """获取认证辅导材料列表."""
        try:
            # 构建查询条件
            conditions = [CertificationMaterial.is_active == True]  # noqa: E712

            if category:
                conditions.append(CertificationMaterial.category == category)

            if material_type:
                conditions.append(CertificationMaterial.type == material_type)

            if search:
                search_condition = or_(
                    CertificationMaterial.title.ilike(f"%{search}%"),
                    CertificationMaterial.description.ilike(f"%{search}%"),
                )
                conditions.append(search_condition)

            # 查询总数
            count_query = select(func.count(CertificationMaterial.id)).where(and_(*conditions))
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # 查询数据
            offset = (page - 1) * page_size
            query = (
                select(CertificationMaterial)
                .where(and_(*conditions))
                .order_by(desc(CertificationMaterial.created_at))
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(query)
            materials = result.scalars().all()

            # 获取分类列表
            categories_query = select(CertificationMaterial.category.distinct()).where(
                CertificationMaterial.is_active == True  # noqa: E712
            )
            categories_result = await self.db.execute(categories_query)
            categories = [cat for cat in categories_result.scalars().all() if cat]

            return {
                "materials": [
                    {
                        "id": material.id,
                        "title": material.title,
                        "description": material.description,
                        "type": material.type,
                        "category": material.category,
                        "file_url": material.file_url,
                        "file_size": material.file_size,
                        "file_format": material.file_format,
                        "download_count": material.download_count,
                        "rating": material.rating,
                        "rating_count": material.rating_count,
                        "is_free": material.is_free,
                        "tags": material.tags,
                        "created_at": material.created_at,
                        "updated_at": material.updated_at,
                    }
                    for material in materials
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"Get certification materials failed: {str(e)}")
            raise

    async def download_certification_material(
        self,
        material_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """下载认证材料."""
        try:
            # 检查材料是否存在
            query = select(CertificationMaterial).where(CertificationMaterial.id == material_id)
            result = await self.db.execute(query)
            material = result.scalar_one_or_none()

            if not material:
                raise ValueError("认证材料不存在")

            if not material.file_url:
                raise ValueError("该材料暂无下载链接")

            # 更新下载次数
            material.download_count += 1
            await self.db.commit()

            return {
                "download_url": material.file_url,
                "file_name": material.title,
                "file_size": material.file_size,
                "file_format": material.file_format,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Download certification material failed: {str(e)}")
            raise

    # ==================== 社区交流平台 ====================

    async def get_community_posts(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        sort_by: str = "latest",
        search: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """获取社区帖子列表."""
        try:
            # 构建查询条件
            conditions = []

            if category:
                conditions.append(CommunityPost.category == category)

            if search:
                search_condition = or_(
                    CommunityPost.title.ilike(f"%{search}%"),
                    CommunityPost.content.ilike(f"%{search}%"),
                )
                conditions.append(search_condition)

            # 查询总数
            count_query = select(func.count(CommunityPost.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))

            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # 构建排序
            order_by: ColumnElement[Any]
            if sort_by == "popular":
                order_by = desc(CommunityPost.likes)
            elif sort_by == "replies":
                order_by = desc(CommunityPost.replies)
            else:
                order_by = desc(CommunityPost.created_at)

            # 查询数据
            offset = (page - 1) * page_size
            query = (
                select(CommunityPost)
                .options(selectinload(CommunityPost.author).selectinload(User.teacher_profile))
                .order_by(order_by)
                .offset(offset)
                .limit(page_size)
            )

            if conditions:
                query = query.where(and_(*conditions))

            result = await self.db.execute(query)
            posts = result.scalars().all()

            # 获取分类列表
            categories_query = select(CommunityPost.category.distinct())
            categories_result = await self.db.execute(categories_query)
            categories = [cat for cat in categories_result.scalars().all() if cat]

            return {
                "posts": [
                    {
                        "id": post.id,
                        "title": post.title,
                        "content": post.content,
                        "category": post.category,
                        "author": {
                            "id": post.author.id,
                            "name": (
                                post.author.teacher_profile.real_name
                                if post.author.teacher_profile
                                else post.author.username
                            ),
                            "avatar": (
                                getattr(post.author.teacher_profile, "avatar", None)
                                if post.author.teacher_profile
                                else None
                            ),
                            "title": (
                                getattr(post.author.teacher_profile, "title", None)
                                if post.author.teacher_profile
                                else None
                            ),
                        },
                        "likes": post.likes,
                        "replies": post.replies,
                        "views": post.views,
                        "is_pinned": post.is_pinned,
                        "is_locked": post.is_locked,
                        "is_featured": post.is_featured,
                        "tags": post.tags,
                        "created_at": post.created_at,
                        "updated_at": post.updated_at,
                        "is_liked": False,  # TODO: 实现用户点赞状态查询
                        "is_bookmarked": False,  # TODO: 实现用户收藏状态查询
                    }
                    for post in posts
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"Get community posts failed: {str(e)}")
            raise

    async def create_community_post(
        self,
        author_id: int,
        title: str,
        content: str,
        category: str,
        tags: list[str],
    ) -> CommunityPost:
        """创建社区帖子."""
        try:
            post = CommunityPost(
                author_id=author_id,
                title=title,
                content=content,
                category=category,
                tags=tags,
            )

            self.db.add(post)
            await self.db.commit()
            await self.db.refresh(post)

            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create community post failed: {str(e)}")
            raise

    async def like_community_post(
        self,
        post_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """点赞社区帖子."""
        try:
            # 检查帖子是否存在
            query = select(CommunityPost).where(CommunityPost.id == post_id)
            result = await self.db.execute(query)
            post = result.scalar_one_or_none()

            if not post:
                raise ValueError("帖子不存在")

            # TODO: 实现用户点赞状态管理
            # 这里简化处理，直接增加点赞数
            post.likes += 1
            await self.db.commit()

            return {
                "is_liked": True,
                "likes": post.likes,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Like community post failed: {str(e)}")
            raise

    # ==================== 研究动态推送 ====================

    async def get_research_updates(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        importance: str | None = None,
    ) -> dict[str, Any]:
        """获取研究动态列表."""
        try:
            # 构建查询条件
            conditions = [ResearchUpdate.is_active == True]  # noqa: E712

            if category:
                conditions.append(ResearchUpdate.category == category)

            if importance:
                conditions.append(ResearchUpdate.importance == importance)

            # 查询总数
            count_query = select(func.count(ResearchUpdate.id)).where(and_(*conditions))
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # 查询数据
            offset = (page - 1) * page_size
            query = (
                select(ResearchUpdate)
                .where(and_(*conditions))
                .order_by(desc(ResearchUpdate.published_at))
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(query)
            updates = result.scalars().all()

            # 获取分类列表
            categories_query = select(ResearchUpdate.category.distinct()).where(
                ResearchUpdate.is_active == True  # noqa: E712
            )
            categories_result = await self.db.execute(categories_query)
            categories = [cat for cat in categories_result.scalars().all() if cat]

            return {
                "updates": [
                    {
                        "id": update.id,
                        "title": update.title,
                        "summary": update.summary,
                        "source": update.source,
                        "category": update.category,
                        "importance": update.importance,
                        "published_at": update.published_at,
                        "source_url": update.source_url,
                        "read_count": update.read_count,
                        "bookmark_count": update.bookmark_count,
                        "tags": update.tags,
                        "created_at": update.created_at,
                        "updated_at": update.updated_at,
                        "is_bookmarked": False,  # TODO: 实现用户收藏状态查询
                    }
                    for update in updates
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"Get research updates failed: {str(e)}")
            raise

    async def bookmark_research_update(
        self,
        update_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """收藏研究动态."""
        try:
            # 检查研究动态是否存在
            query = select(ResearchUpdate).where(ResearchUpdate.id == update_id)
            result = await self.db.execute(query)
            update = result.scalar_one_or_none()

            if not update:
                raise ValueError("研究动态不存在")

            # TODO: 实现用户收藏状态管理
            # 这里简化处理，直接增加收藏数
            update.bookmark_count += 1
            await self.db.commit()

            return {
                "is_bookmarked": True,
                "bookmark_count": update.bookmark_count,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Bookmark research update failed: {str(e)}")
            raise

    # ==================== 通知设置 ====================

    async def get_notification_settings(self, user_id: int) -> NotificationSettings:
        """获取通知设置."""
        try:
            query = select(NotificationSettings).where(NotificationSettings.user_id == user_id)
            result = await self.db.execute(query)
            settings = result.scalar_one_or_none()

            if not settings:
                # 创建默认设置
                settings = NotificationSettings(user_id=user_id)
                self.db.add(settings)
                await self.db.commit()
                await self.db.refresh(settings)

            return settings

        except Exception as e:
            logger.error(f"Get notification settings failed: {str(e)}")
            raise

    async def update_notification_settings(
        self,
        user_id: int,
        settings: NotificationSettingsUpdate,
    ) -> NotificationSettings:
        """更新通知设置."""
        try:
            # 获取现有设置
            existing_settings = await self.get_notification_settings(user_id)

            # 更新设置
            for field, value in settings.model_dump(exclude_unset=True).items():
                setattr(existing_settings, field, value)

            await self.db.commit()
            await self.db.refresh(existing_settings)

            return existing_settings

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update notification settings failed: {str(e)}")
            raise

    # ==================== 统计和推荐 ====================

    async def get_learning_stats(self, user_id: int) -> dict[str, Any]:
        """获取个人学习统计."""
        try:
            # 获取或创建学习进度记录
            query = select(LearningProgress).where(LearningProgress.user_id == user_id)
            result = await self.db.execute(query)
            progress = result.scalar_one_or_none()

            if not progress:
                progress = LearningProgress(
                    user_id=user_id,
                    last_updated_at=datetime.utcnow(),
                )
                self.db.add(progress)
                await self.db.commit()
                await self.db.refresh(progress)

            # 计算完成率
            completion_rate = 0.0
            if progress.total_trainings > 0:
                completion_rate = (progress.completed_trainings / progress.total_trainings) * 100

            return {
                "total_trainings": progress.total_trainings,
                "completed_trainings": progress.completed_trainings,
                "total_study_hours": progress.total_study_hours,
                "certifications_earned": progress.certifications_earned,
                "community_contributions": progress.community_contributions,
                "research_articles_read": progress.research_articles_read,
                "completion_rate": completion_rate,
                "average_rating": 0.0,  # TODO: 计算平均评分
            }

        except Exception as e:
            logger.error(f"Get learning stats failed: {str(e)}")
            raise

    async def get_personalized_recommendations(self, user_id: int) -> dict[str, Any]:
        """获取个性化推荐."""
        try:
            # TODO: 实现基于用户历史的推荐算法
            # 这里提供简化的推荐逻辑

            # 推荐热门培训
            training_query = (
                select(TrainingResource)
                .where(TrainingResource.is_active == True)  # noqa: E712
                .order_by(desc(TrainingResource.rating))
                .limit(5)
            )
            training_result = await self.db.execute(training_query)
            recommended_trainings = training_result.scalars().all()

            # 推荐热门材料
            material_query = (
                select(CertificationMaterial)
                .where(CertificationMaterial.is_active == True)  # noqa: E712
                .order_by(desc(CertificationMaterial.rating))
                .limit(5)
            )
            material_result = await self.db.execute(material_query)
            recommended_materials = material_result.scalars().all()

            # 推荐热门帖子
            post_query = (
                select(CommunityPost)
                .options(selectinload(CommunityPost.author).selectinload(User.teacher_profile))
                .order_by(desc(CommunityPost.likes))
                .limit(5)
            )
            post_result = await self.db.execute(post_query)
            recommended_posts = post_result.scalars().all()

            # 推荐重要研究
            research_query = (
                select(ResearchUpdate)
                .where(
                    and_(
                        ResearchUpdate.is_active == True,  # noqa: E712
                        ResearchUpdate.importance == "high",
                    )
                )
                .order_by(desc(ResearchUpdate.published_at))
                .limit(5)
            )
            research_result = await self.db.execute(research_query)
            recommended_research = research_result.scalars().all()

            return {
                "recommended_trainings": [
                    {
                        "id": training.id,
                        "title": training.title,
                        "description": training.description,
                        "category": training.category,
                        "rating": training.rating,
                        "enrolled_count": training.enrolled_count,
                    }
                    for training in recommended_trainings
                ],
                "recommended_materials": [
                    {
                        "id": material.id,
                        "title": material.title,
                        "description": material.description,
                        "category": material.category,
                        "rating": material.rating,
                        "download_count": material.download_count,
                    }
                    for material in recommended_materials
                ],
                "recommended_posts": [
                    {
                        "id": post.id,
                        "title": post.title,
                        "category": post.category,
                        "author": {
                            "id": post.author.id,
                            "name": (
                                post.author.teacher_profile.real_name
                                if post.author.teacher_profile
                                else post.author.username
                            ),
                        },
                        "likes": post.likes,
                        "replies": post.replies,
                    }
                    for post in recommended_posts
                ],
                "recommended_research": [
                    {
                        "id": research.id,
                        "title": research.title,
                        "summary": research.summary,
                        "source": research.source,
                        "importance": research.importance,
                        "published_at": research.published_at,
                    }
                    for research in recommended_research
                ],
            }

        except Exception as e:
            logger.error(f"Get personalized recommendations failed: {str(e)}")
            raise
