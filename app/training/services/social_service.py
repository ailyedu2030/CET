"""学习社交与互动系统 - 服务层"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.training.models.social_models import (
    DiscussionForumModel,
    ForumPostModel,
    MessageModel,
    PostLikeModel,
    PostReportModel,
    StudyGroupMembershipModel,
    StudyGroupModel,
    StudyPartnerMatchModel,
    StudyPartnerRequestModel,
)
from app.training.schemas.social_interaction_schemas import (
    DiscussionForumCreate,
    DiscussionForumUpdate,
    ForumPostCreate,
    ForumPostUpdate,
    MessageCreate,
    PostLikeCreate,
    PostReportCreate,
    StudyGroupCreate,
    StudyPartnerRequestCreate,
)

logger = logging.getLogger(__name__)


class SocialService:
    """
    学习社交与互动服务类

    实现班级讨论区功能、学习伙伴匹配系统、安全策略和内容审核等
    """

    def __init__(self: "SocialService", db: AsyncSession) -> None:
        self.db = db

    # ==================== 讨论区管理 ====================

    async def create_forum(
        self: "SocialService", data: DiscussionForumCreate
    ) -> DiscussionForumModel:
        """创建讨论区"""
        logger.info(f"创建讨论区: {data.name}")

        forum = DiscussionForumModel(
            name=data.name,
            description=data.description,
            category=data.category,
            class_id=data.class_id,
            course_id=data.course_id,
            is_public=data.is_public,
            allow_anonymous=data.allow_anonymous,
            require_approval=data.require_approval,
        )

        self.db.add(forum)
        await self.db.commit()
        await self.db.refresh(forum)

        logger.info(f"讨论区创建成功: ID={forum.id}")  # type: ignore[has-type]
        return forum

    async def get_forums(
        self: "SocialService",
        skip: int = 0,
        limit: int = 10,
        category: str | None = None,
        class_id: int | None = None,
        is_public: bool | None = None,
    ) -> tuple[list[DiscussionForumModel], int]:
        """获取讨论区列表"""
        logger.info("查询讨论区列表")

        # 构建查询条件
        conditions: list[Any] = [DiscussionForumModel.is_active.is_(True)]
        if category:
            conditions.append(DiscussionForumModel.category == category)
        if class_id:
            conditions.append(DiscussionForumModel.class_id == class_id)
        if is_public is not None:
            conditions.append(DiscussionForumModel.is_public.is_(is_public))

        # 查询总数
        count_query = select(func.count(DiscussionForumModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(DiscussionForumModel)
            .where(and_(*conditions))
            .order_by(desc(DiscussionForumModel.last_activity_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        forums = result.scalars().all()

        return list(forums), total

    async def update_forum(
        self: "SocialService", forum_id: int, data: DiscussionForumUpdate
    ) -> DiscussionForumModel | None:
        """更新讨论区"""
        logger.info(f"更新讨论区: {forum_id}")

        query = select(DiscussionForumModel).where(DiscussionForumModel.id == forum_id)  # type: ignore
        result = await self.db.execute(query)
        forum = result.scalar_one_or_none()

        if not forum:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(forum, field, value)

        forum.updated_at = datetime.utcnow()  # type: ignore
        await self.db.commit()
        await self.db.refresh(forum)

        logger.info(f"讨论区更新成功: ID={forum.id}")  # type: ignore
        return forum

    # ==================== 帖子管理 ====================

    async def create_post(
        self: "SocialService", user_id: int, data: ForumPostCreate
    ) -> ForumPostModel:
        """创建论坛帖子"""
        logger.info(f"用户 {user_id} 创建帖子: {data.title}")

        # 内容审核
        is_approved = await self._moderate_content(data.content)

        post = ForumPostModel(
            forum_id=data.forum_id,
            user_id=user_id,
            parent_id=data.parent_id,
            title=data.title,
            content=data.content,
            post_type=data.post_type,
            attachments=data.attachments,
            images=data.images,
            tags=data.tags,
            difficulty_level=data.difficulty_level,
            is_anonymous=data.is_anonymous,
            anonymous_name=data.anonymous_name,
            status="published" if is_approved else "pending",
        )

        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)

        # 更新论坛统计
        await self._update_forum_stats(data.forum_id)

        logger.info(f"帖子创建成功: ID={post.id}")  # type: ignore
        return post

    async def get_posts(
        self: "SocialService",
        skip: int = 0,
        limit: int = 10,
        forum_id: int | None = None,
        user_id: int | None = None,
        post_type: str | None = None,
        parent_id: int | None = None,
    ) -> tuple[list[ForumPostModel], int]:
        """获取帖子列表"""
        logger.info("查询帖子列表")

        # 构建查询条件
        conditions = [ForumPostModel.status == "published"]
        if forum_id:
            conditions.append(ForumPostModel.forum_id == forum_id)
        if user_id:
            conditions.append(ForumPostModel.user_id == user_id)
        if post_type:
            conditions.append(ForumPostModel.post_type == post_type)
        if parent_id is not None:
            conditions.append(ForumPostModel.parent_id == parent_id)

        # 查询总数
        count_query = select(func.count(ForumPostModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(ForumPostModel)
            .where(and_(*conditions))
            .options(selectinload(ForumPostModel.forum))
            .order_by(desc(ForumPostModel.created_at))  # type: ignore
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def update_post(
        self: "SocialService", post_id: int, user_id: int, data: ForumPostUpdate
    ) -> ForumPostModel | None:
        """更新帖子"""
        logger.info(f"用户 {user_id} 更新帖子: {post_id}")

        query = select(ForumPostModel).where(
            and_(
                ForumPostModel.id == post_id,  # type: ignore[has-type]
                ForumPostModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        # 如果内容更新，重新审核
        if "content" in update_data:
            is_approved = await self._moderate_content(str(post.content))
            post.status = "published" if is_approved else "pending"

        post.updated_at = datetime.utcnow()  # type: ignore
        await self.db.commit()
        await self.db.refresh(post)

        logger.info(f"帖子更新成功: ID={post.id}")  # type: ignore
        return post

    async def get_post_by_id(self: "SocialService", post_id: int) -> ForumPostModel | None:
        """根据ID获取帖子详情"""
        logger.info(f"查询帖子详情: {post_id}")

        query = (
            select(ForumPostModel)
            .where(
                and_(
                    ForumPostModel.id == post_id,  # type: ignore[has-type]
                    ForumPostModel.status == "published",
                )
            )
            .options(
                selectinload(ForumPostModel.forum),  # 预加载论坛信息
                selectinload(ForumPostModel.likes),  # 预加载点赞信息
                selectinload(ForumPostModel.replies),  # 预加载回复信息
            )
        )

        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if post:
            logger.info(f"帖子详情查询成功: ID={post.id}")  # type: ignore[has-type]
        else:
            logger.warning(f"帖子不存在或未发布: {post_id}")

        return post

    # ==================== 帖子互动 ====================

    async def like_post(self: "SocialService", user_id: int, data: PostLikeCreate) -> PostLikeModel:
        """点赞帖子"""
        logger.info(f"用户 {user_id} 点赞帖子: {data.post_id}")

        # 检查是否已点赞
        existing_query = select(PostLikeModel).where(
            and_(
                PostLikeModel.post_id == data.post_id,
                PostLikeModel.user_id == user_id,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_like = existing_result.scalar_one_or_none()

        if existing_like:
            # 取消点赞
            await self.db.delete(existing_like)
            await self.db.commit()

            # 更新帖子点赞数
            await self._update_post_like_count(data.post_id)

            logger.info(f"取消点赞成功: 帖子 {data.post_id}")
            return existing_like

        # 创建新点赞
        like = PostLikeModel(
            post_id=data.post_id,
            user_id=user_id,
            like_type=data.like_type,
        )

        self.db.add(like)
        await self.db.commit()
        await self.db.refresh(like)

        # 更新帖子点赞数
        await self._update_post_like_count(data.post_id)

        logger.info(f"点赞成功: ID={like.id}")  # type: ignore
        return like

    async def report_post(
        self: "SocialService", user_id: int, data: PostReportCreate
    ) -> PostReportModel:
        """举报帖子"""
        logger.info(f"用户 {user_id} 举报帖子: {data.post_id}")

        report = PostReportModel(
            post_id=data.post_id,
            reporter_id=user_id,
            reason=data.reason,
            description=data.description,
            evidence=data.evidence,
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        # 如果举报数量过多，自动隐藏帖子
        await self._check_post_reports(data.post_id)

        logger.info(f"举报提交成功: ID={report.id}")  # type: ignore
        return report

    # ==================== 学习伙伴匹配 ====================

    async def create_partner_request(
        self: "SocialService", user_id: int, data: StudyPartnerRequestCreate
    ) -> StudyPartnerRequestModel:
        """创建学习伙伴请求"""
        logger.info(f"用户 {user_id} 创建学习伙伴请求")

        request = StudyPartnerRequestModel(
            requester_id=user_id,
            target_level=data.target_level,
            study_goals=data.study_goals,
            preferred_schedule=data.preferred_schedule,
            study_style=data.study_style,
            introduction=data.introduction,
            interests=data.interests,
            contact_preferences=data.contact_preferences,
            max_partners=data.max_partners,
            auto_match=data.auto_match,
            location_preference=data.location_preference,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        # 如果开启自动匹配，立即进行匹配
        if data.auto_match:
            await self._auto_match_partners(request.id)  # type: ignore[has-type]

        logger.info(f"学习伙伴请求创建成功: ID={request.id}")  # type: ignore[has-type]
        return request

    async def get_partner_requests(
        self: "SocialService",
        skip: int = 0,
        limit: int = 10,
        user_id: int | None = None,
        status: str | None = None,
    ) -> tuple[list[StudyPartnerRequestModel], int]:
        """获取学习伙伴请求列表"""
        logger.info("查询学习伙伴请求列表")

        # 构建查询条件
        conditions: list[Any] = [StudyPartnerRequestModel.is_active.is_(True)]
        if user_id:
            conditions.append(StudyPartnerRequestModel.requester_id == user_id)
        if status:
            conditions.append(StudyPartnerRequestModel.status == status)

        # 查询总数
        count_query = select(func.count(StudyPartnerRequestModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(StudyPartnerRequestModel)
            .where(and_(*conditions))
            .order_by(desc(StudyPartnerRequestModel.created_at))  # type: ignore
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        requests = result.scalars().all()

        return list(requests), total

    async def respond_to_partner_request(
        self: "SocialService", request_id: int, user_id: int, action: str, message: str = ""
    ) -> None:
        """响应学习伙伴匹配"""
        logger.info(f"用户 {user_id} 响应学习伙伴匹配: {request_id}, 操作: {action}")

        # 验证操作类型
        if action not in ["accept", "decline"]:
            raise ValueError("无效的操作类型，只支持 accept 或 decline")

        # 查询学习伙伴匹配记录
        match_query = select(StudyPartnerMatchModel).where(
            and_(
                StudyPartnerMatchModel.id == request_id,  # type: ignore[has-type]
                StudyPartnerMatchModel.status == "pending",
            )
        )
        match_result = await self.db.execute(match_query)
        partner_match = match_result.scalar_one_or_none()

        if not partner_match:
            raise ValueError("学习伙伴匹配不存在或已处理")

        # 检查权限：只有匹配的伙伴可以响应
        if partner_match.partner_id != user_id:  # type: ignore[has-type]
            raise ValueError("您没有权限响应此匹配")

        # 更新匹配状态
        if action == "accept":
            partner_match.accepted_by_partner = True  # type: ignore[has-type]
            partner_match.status = "accepted"  # type: ignore[has-type]
        else:
            partner_match.accepted_by_partner = False  # type: ignore[has-type]
            partner_match.status = "declined"  # type: ignore[has-type]

        partner_match.updated_at = datetime.utcnow()  # type: ignore[has-type]
        await self.db.commit()

        # 如果接受匹配，可以创建学习伙伴关系或发送通知
        if action == "accept":
            await self._create_partner_relationship(partner_match)

        action_text = "接受" if action == "accept" else "拒绝"
        logger.info(f"用户 {user_id} {action_text}了学习伙伴匹配: {request_id}")

    # ==================== 学习小组管理 ====================

    async def create_study_group(
        self: "SocialService", user_id: int, data: StudyGroupCreate
    ) -> StudyGroupModel:
        """创建学习小组"""
        logger.info(f"用户 {user_id} 创建学习小组: {data.name}")

        group = StudyGroupModel(
            creator_id=user_id,
            name=data.name,
            description=data.description,
            avatar_url=data.avatar_url,
            study_topic=data.study_topic,
            target_level=data.target_level,
            study_schedule=data.study_schedule,
            max_members=data.max_members,
            is_public=data.is_public,
            require_approval=data.require_approval,
        )

        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)

        # 创建者自动加入小组
        membership = StudyGroupMembershipModel(
            group_id=group.id,  # type: ignore[has-type]
            user_id=user_id,
            role="creator",
        )

        self.db.add(membership)
        await self.db.commit()

        logger.info(f"学习小组创建成功: ID={group.id}")  # type: ignore[has-type]
        return group

    async def get_study_groups(
        self: "SocialService",
        skip: int = 0,
        limit: int = 10,
        is_public: bool | None = None,
        study_topic: str | None = None,
        target_level: str | None = None,
    ) -> tuple[list[StudyGroupModel], int]:
        """获取学习小组列表"""
        logger.info("查询学习小组列表")

        # 构建查询条件
        conditions: list[Any] = [StudyGroupModel.is_active.is_(True)]
        if is_public is not None:
            conditions.append(StudyGroupModel.is_public.is_(is_public))
        if study_topic:
            conditions.append(StudyGroupModel.study_topic == study_topic)
        if target_level:
            conditions.append(StudyGroupModel.target_level == target_level)

        # 查询总数
        count_query = select(func.count(StudyGroupModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(StudyGroupModel)
            .where(and_(*conditions))
            .order_by(desc(StudyGroupModel.activity_score))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        groups = result.scalars().all()

        return list(groups), total

    async def get_study_group_by_id(self: "SocialService", group_id: int) -> StudyGroupModel | None:
        """根据ID获取学习小组详情"""
        logger.info(f"查询学习小组详情: {group_id}")

        query = (
            select(StudyGroupModel)
            .where(
                and_(
                    StudyGroupModel.id == group_id,  # type: ignore[has-type]
                    StudyGroupModel.is_active.is_(True),
                )
            )
            .options(
                selectinload(StudyGroupModel.memberships),  # 预加载成员信息
            )
        )

        result = await self.db.execute(query)
        group = result.scalar_one_or_none()

        if group:
            logger.info(f"学习小组详情查询成功: ID={group.id}")  # type: ignore[has-type]
        else:
            logger.warning(f"学习小组不存在: {group_id}")

        return group

    async def join_study_group(self: "SocialService", group_id: int, user_id: int) -> None:
        """用户加入学习小组"""
        logger.info(f"用户 {user_id} 申请加入学习小组: {group_id}")

        # 检查学习小组是否存在
        group_query = select(StudyGroupModel).where(
            and_(
                StudyGroupModel.id == group_id,  # type: ignore[has-type]
                StudyGroupModel.is_active.is_(True),
            )
        )
        group_result = await self.db.execute(group_query)
        group = group_result.scalar_one_or_none()

        if not group:
            raise ValueError("学习小组不存在或已被删除")

        # 检查是否已经是成员
        existing_query = select(StudyGroupMembershipModel).where(
            and_(
                StudyGroupMembershipModel.group_id == group_id,
                StudyGroupMembershipModel.user_id == user_id,
                StudyGroupMembershipModel.status == "active",
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_membership = existing_result.scalar_one_or_none()

        if existing_membership:
            raise ValueError("您已经是该学习小组的成员")

        # 检查小组是否已满员
        member_count_query = select(func.count(StudyGroupMembershipModel.id)).where(  # type: ignore[has-type]
            and_(
                StudyGroupMembershipModel.group_id == group_id,
                StudyGroupMembershipModel.status == "active",
            )
        )
        member_count_result = await self.db.execute(member_count_query)
        current_member_count = member_count_result.scalar() or 0

        if current_member_count >= group.max_members:  # type: ignore[has-type]
            raise ValueError("学习小组已满员")

        # 创建成员关系
        membership = StudyGroupMembershipModel(
            group_id=group_id,
            user_id=user_id,
            role="member",
            status="active" if not group.require_approval else "pending",  # type: ignore[has-type]
        )

        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)

        # 更新小组成员数量
        await self._update_group_member_count(group_id)

        status_msg = "加入成功" if not group.require_approval else "申请已提交，等待审核"  # type: ignore[has-type]
        logger.info(f"用户 {user_id} {status_msg}: 学习小组 {group_id}")

    async def leave_study_group(self: "SocialService", group_id: int, user_id: int) -> None:
        """用户退出学习小组"""
        logger.info(f"用户 {user_id} 申请退出学习小组: {group_id}")

        # 检查成员关系是否存在
        membership_query = select(StudyGroupMembershipModel).where(
            and_(
                StudyGroupMembershipModel.group_id == group_id,
                StudyGroupMembershipModel.user_id == user_id,
                StudyGroupMembershipModel.status == "active",
            )
        )
        membership_result = await self.db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()

        if not membership:
            raise ValueError("您不是该学习小组的成员")

        # 检查是否为创建者
        if membership.role == "creator":  # type: ignore[has-type]
            # 检查是否还有其他成员
            other_members_query = select(func.count(StudyGroupMembershipModel.id)).where(  # type: ignore[has-type]
                and_(
                    StudyGroupMembershipModel.group_id == group_id,
                    StudyGroupMembershipModel.user_id != user_id,
                    StudyGroupMembershipModel.status == "active",
                )
            )
            other_members_result = await self.db.execute(other_members_query)
            other_member_count = other_members_result.scalar() or 0

            if other_member_count > 0:
                raise ValueError("作为创建者，请先转让小组管理权或解散小组")

        # 标记成员关系为非活跃
        membership.status = "inactive"  # type: ignore[has-type]
        membership.left_at = datetime.utcnow()  # type: ignore[has-type]
        await self.db.commit()

        # 更新小组成员数量
        await self._update_group_member_count(group_id)

        logger.info(f"用户 {user_id} 成功退出学习小组: {group_id}")

    # ==================== 实时通信 ====================

    async def send_message(
        self: "SocialService", user_id: int, data: MessageCreate
    ) -> MessageModel:
        """发送消息"""
        logger.info(f"用户 {user_id} 发送消息")

        # 内容审核
        is_approved = await self._moderate_content(data.content)

        if not is_approved:
            raise ValueError("消息内容不符合社区规范")

        message = MessageModel(
            sender_id=user_id,
            receiver_id=data.receiver_id,
            group_id=data.group_id,
            content=data.content,
            message_type=data.message_type,
            attachments=data.attachments,
            reply_to_id=data.reply_to_id,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        logger.info(f"消息发送成功: ID={message.id}")  # type: ignore
        return message

    async def get_messages(
        self: "SocialService",
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        receiver_id: int | None = None,
        group_id: int | None = None,
    ) -> tuple[list[MessageModel], int]:
        """获取消息列表"""
        logger.info(f"用户 {user_id} 查询消息列表")

        # 构建查询条件
        conditions: list[Any] = [MessageModel.is_deleted.is_(False)]

        if receiver_id:
            # 私聊消息
            conditions.append(
                and_(
                    MessageModel.receiver_id == receiver_id,
                    MessageModel.sender_id == user_id,
                )
                | and_(
                    MessageModel.receiver_id == user_id,
                    MessageModel.sender_id == receiver_id,
                )
            )
        elif group_id:
            # 群组消息
            conditions.append(MessageModel.group_id == group_id)
        else:
            # 用户所有消息
            conditions.append(
                (MessageModel.sender_id == user_id) | (MessageModel.receiver_id == user_id)
            )

        # 查询总数
        count_query = select(func.count(MessageModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(MessageModel)
            .where(and_(*conditions))
            .order_by(desc(MessageModel.created_at))  # type: ignore
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages), total

    # ==================== 私有辅助方法 ====================

    async def _moderate_content(self: "SocialService", content: str) -> bool:
        """内容审核"""
        # 可以集成第三方内容审核API或自建审核系统

        # 简单的关键词过滤
        banned_words = ["垃圾", "广告", "骗子"]
        content_lower = content.lower()

        for word in banned_words:
            if word in content_lower:
                return False

        return True

    async def _update_forum_stats(self: "SocialService", forum_id: int) -> None:
        """更新论坛统计"""
        # 查询帖子数量
        post_count_query = select(func.count(ForumPostModel.id)).where(  # type: ignore
            ForumPostModel.forum_id == forum_id
        )
        post_count_result = await self.db.execute(post_count_query)
        post_count = post_count_result.scalar() or 0

        # 更新论坛统计
        forum_query = select(DiscussionForumModel).where(DiscussionForumModel.id == forum_id)  # type: ignore
        forum_result = await self.db.execute(forum_query)
        forum = forum_result.scalar_one_or_none()

        if forum:
            forum.post_count = post_count
            forum.last_activity_at = datetime.utcnow()
            await self.db.commit()

    async def _update_post_like_count(self: "SocialService", post_id: int) -> None:
        """更新帖子点赞数"""
        # 查询点赞数量
        like_count_query = select(func.count(PostLikeModel.id)).where(  # type: ignore
            PostLikeModel.post_id == post_id
        )
        like_count_result = await self.db.execute(like_count_query)
        like_count = like_count_result.scalar() or 0

        # 更新帖子点赞数
        post_query = select(ForumPostModel).where(ForumPostModel.id == post_id)  # type: ignore
        post_result = await self.db.execute(post_query)
        post = post_result.scalar_one_or_none()

        if post:
            post.like_count = like_count
            await self.db.commit()

    async def _check_post_reports(self: "SocialService", post_id: int) -> None:
        """检查帖子举报数量"""
        # 查询举报数量
        report_count_query = select(func.count(PostReportModel.id)).where(  # type: ignore
            PostReportModel.post_id == post_id
        )
        report_count_result = await self.db.execute(report_count_query)
        report_count = report_count_result.scalar() or 0

        # 如果举报数量超过阈值，自动隐藏帖子
        if report_count >= 5:
            post_query = select(ForumPostModel).where(ForumPostModel.id == post_id)  # type: ignore
            post_result = await self.db.execute(post_query)
            post = post_result.scalar_one_or_none()

            if post:
                post.status = "reported"
                await self.db.commit()

    async def _auto_match_partners(self: "SocialService", request_id: int) -> None:
        """自动匹配学习伙伴"""
        logger.info("Method implemented")
        # 可以基于学习目标、时间安排、地理位置等因素进行匹配
        logger.info(f"开始自动匹配学习伙伴: 请求 {request_id}")

    async def _update_group_member_count(self: "SocialService", group_id: int) -> None:
        """更新学习小组成员数量"""
        # 查询活跃成员数量
        member_count_query = select(func.count(StudyGroupMembershipModel.id)).where(  # type: ignore[has-type]
            and_(
                StudyGroupMembershipModel.group_id == group_id,
                StudyGroupMembershipModel.status == "active",
            )
        )
        member_count_result = await self.db.execute(member_count_query)
        current_member_count = member_count_result.scalar() or 0

        # 更新小组成员数量
        group_query = select(StudyGroupModel).where(StudyGroupModel.id == group_id)  # type: ignore[has-type]
        group_result = await self.db.execute(group_query)
        group = group_result.scalar_one_or_none()

        if group:
            group.member_count = current_member_count  # type: ignore[has-type]
            group.last_activity_at = datetime.utcnow()  # type: ignore[has-type]
            await self.db.commit()

    async def _create_partner_relationship(
        self: "SocialService", partner_match: StudyPartnerMatchModel
    ) -> None:
        """创建学习伙伴关系"""
        # 可以创建专门的学习伙伴表或在用户关系表中记录

        # 获取请求信息
        request_query = select(StudyPartnerRequestModel).where(
            StudyPartnerRequestModel.id == partner_match.request_id  # type: ignore[has-type]
        )
        request_result = await self.db.execute(request_query)
        partner_request = request_result.scalar_one_or_none()

        if partner_request:
            logger.info(
                f"创建学习伙伴关系: {partner_request.requester_id} <-> {partner_match.partner_id}"  # type: ignore[has-type]
            )
