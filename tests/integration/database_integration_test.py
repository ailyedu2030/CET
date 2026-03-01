"""
英语四级学习系统 - 数据库集成测试

测试数据库操作的集成，包括：
- 数据库连接和事务
- 数据模型关系
- 查询性能
- 数据一致性
- 并发操作
"""

import asyncio
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.content import LearningContent
from app.models.learning import LearningProgress, LearningSession
from app.models.user import User
from app.models.vocabulary import UserVocabularyProgress, Vocabulary
from tests.fixtures.test_data import get_test_user, test_data_generator


class TestDatabaseIntegration:
    """数据库集成测试"""

    @pytest.fixture
    async def db_session(self):
        """数据库会话"""
        async with get_session() as session:
            yield session

    @pytest.fixture
    async def test_user_data(self):
        """测试用户数据"""
        return get_test_user("student")

    async def test_database_connection_and_basic_operations(
        self, db_session: AsyncSession
    ):
        """测试数据库连接和基本操作"""
        # 测试数据库连接
        result = await db_session.execute(text("SELECT 1 as test"))
        assert result.scalar() == 1

        # 测试事务
        await db_session.execute(text("BEGIN"))
        await db_session.execute(text("SELECT 1"))
        await db_session.execute(text("COMMIT"))

    async def test_user_model_operations(
        self, db_session: AsyncSession, test_user_data: dict[str, Any]
    ):
        """测试用户模型操作"""
        # 创建用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            hashed_password="hashed_password_here",
            role=test_user_data["role"],
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 验证用户创建
        assert user.user_id is not None
        assert user.username == test_user_data["username"]
        assert user.created_at is not None

        # 更新用户
        user.full_name = "Updated Name"
        await db_session.commit()
        await db_session.refresh(user)

        assert user.full_name == "Updated Name"
        assert user.updated_at is not None

        # 查询用户
        found_user = await db_session.get(User, user.user_id)
        assert found_user is not None
        assert found_user.username == test_user_data["username"]

        return user

    async def test_content_model_operations(self, db_session: AsyncSession):
        """测试内容模型操作"""
        # 创建学习内容
        content_data = test_data_generator.generate_learning_content("vocabulary", 1)[0]

        content = LearningContent(
            title=content_data["title"],
            description=content_data["description"],
            content_type=content_data["content_type"],
            difficulty_level=content_data["difficulty_level"],
            estimated_duration=content_data["estimated_duration"],
            tags=content_data["tags"],
            created_by=1,  # 假设的创建者ID
            content_data=content_data.get("content_data", {}),
        )

        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)

        # 验证内容创建
        assert content.content_id is not None
        assert content.title == content_data["title"]
        assert content.content_type == content_data["content_type"]

        return content

    async def test_learning_session_operations(self, db_session: AsyncSession):
        """测试学习会话操作"""
        # 首先创建用户和内容
        user = await self.test_user_model_operations(
            db_session, get_test_user("student")
        )
        content = await self.test_content_model_operations(db_session)

        # 创建学习会话
        session = LearningSession(
            user_id=user.user_id,
            content_id=content.content_id,
            content_type=content.content_type,
            start_time=datetime.utcnow(),
            status="active",
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # 验证会话创建
        assert session.session_id is not None
        assert session.user_id == user.user_id
        assert session.content_id == content.content_id
        assert session.status == "active"

        # 完成会话
        session.end_time = datetime.utcnow()
        session.status = "completed"
        session.completion_rate = 0.95
        session.accuracy_rate = 0.88
        session.score = 85

        await db_session.commit()
        await db_session.refresh(session)

        # 验证会话更新
        assert session.status == "completed"
        assert session.end_time is not None
        assert session.score == 85

        return session

    async def test_vocabulary_operations(self, db_session: AsyncSession):
        """测试词汇操作"""
        # 创建词汇
        vocab_data = test_data_generator.generate_vocabulary_data(1)[0]

        vocabulary = Vocabulary(
            word=vocab_data["word"],
            pronunciation=vocab_data["pronunciation"],
            meanings=vocab_data["meanings"],
            difficulty_level=vocab_data["difficulty_level"],
            frequency=vocab_data["frequency"],
            tags=vocab_data["tags"],
        )

        db_session.add(vocabulary)
        await db_session.commit()
        await db_session.refresh(vocabulary)

        # 验证词汇创建
        assert vocabulary.word_id is not None
        assert vocabulary.word == vocab_data["word"]

        # 创建用户词汇进度
        user = await self.test_user_model_operations(
            db_session, get_test_user("student")
        )

        user_vocab_progress = UserVocabularyProgress(
            user_id=user.user_id,
            word_id=vocabulary.word_id,
            mastery_level=0.7,
            last_reviewed=datetime.utcnow(),
            review_count=3,
            correct_count=2,
        )

        db_session.add(user_vocab_progress)
        await db_session.commit()
        await db_session.refresh(user_vocab_progress)

        # 验证用户词汇进度
        assert user_vocab_progress.user_id == user.user_id
        assert user_vocab_progress.word_id == vocabulary.word_id
        assert user_vocab_progress.mastery_level == 0.7

        return vocabulary, user_vocab_progress

    async def test_learning_progress_operations(self, db_session: AsyncSession):
        """测试学习进度操作"""
        # 创建用户和学习会话
        user = await self.test_user_model_operations(
            db_session, get_test_user("student")
        )
        session = await self.test_learning_session_operations(db_session)

        # 创建学习进度
        progress = LearningProgress(
            user_id=user.user_id,
            content_type="vocabulary",
            total_study_time=1800,  # 30分钟
            sessions_completed=1,
            average_score=85.0,
            last_activity=datetime.utcnow(),
        )

        db_session.add(progress)
        await db_session.commit()
        await db_session.refresh(progress)

        # 验证进度创建
        assert progress.user_id == user.user_id
        assert progress.content_type == "vocabulary"
        assert progress.sessions_completed == 1

        # 更新进度
        progress.total_study_time += 900  # 增加15分钟
        progress.sessions_completed += 1
        progress.average_score = (progress.average_score + 90) / 2  # 新的平均分

        await db_session.commit()
        await db_session.refresh(progress)

        # 验证进度更新
        assert progress.total_study_time == 2700
        assert progress.sessions_completed == 2
        assert progress.average_score == 87.5

        return progress

    async def test_complex_queries_and_relationships(self, db_session: AsyncSession):
        """测试复杂查询和关系"""
        # 创建测试数据
        user = await self.test_user_model_operations(
            db_session, get_test_user("student")
        )
        content = await self.test_content_model_operations(db_session)
        session = await self.test_learning_session_operations(db_session)

        # 测试用户的学习会话查询
        from sqlalchemy import select

        # 查询用户的所有学习会话
        stmt = select(LearningSession).where(LearningSession.user_id == user.user_id)
        result = await db_session.execute(stmt)
        user_sessions = result.scalars().all()

        assert len(user_sessions) > 0
        assert user_sessions[0].user_id == user.user_id

        # 查询特定内容类型的会话
        stmt = select(LearningSession).where(
            LearningSession.user_id == user.user_id,
            LearningSession.content_type == "vocabulary",
        )
        result = await db_session.execute(stmt)
        vocab_sessions = result.scalars().all()

        assert len(vocab_sessions) > 0

        # 查询用户的学习统计
        stmt = select(LearningProgress).where(LearningProgress.user_id == user.user_id)
        result = await db_session.execute(stmt)
        user_progress = result.scalars().all()

        assert len(user_progress) > 0

    async def test_transaction_rollback(self, db_session: AsyncSession):
        """测试事务回滚"""
        # 开始事务
        user_data = get_test_user("student")
        user_data["username"] = "rollback_test_user"

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password="hashed_password",
            role=user_data["role"],
        )

        db_session.add(user)
        await db_session.flush()  # 刷新但不提交

        # 验证用户在当前事务中存在
        assert user.user_id is not None

        # 回滚事务
        await db_session.rollback()

        # 验证用户不存在
        from sqlalchemy import select

        stmt = select(User).where(User.username == user_data["username"])
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert found_user is None

    async def test_concurrent_operations(self, db_session: AsyncSession):
        """测试并发操作"""

        # 创建多个并发任务
        async def create_user_session(session_num: int):
            async with get_session() as session:
                user_data = get_test_user("student")
                user_data["username"] = f"concurrent_user_{session_num}"
                user_data["email"] = f"concurrent_user_{session_num}@test.com"

                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password="hashed_password",
                    role=user_data["role"],
                )

                session.add(user)
                await session.commit()
                return user.user_id

        # 并发创建用户
        tasks = [create_user_session(i) for i in range(5)]
        user_ids = await asyncio.gather(*tasks)

        # 验证所有用户都创建成功
        assert len(user_ids) == 5
        assert all(user_id is not None for user_id in user_ids)

        # 验证用户在数据库中存在
        from sqlalchemy import select

        for i, user_id in enumerate(user_ids):
            stmt = select(User).where(User.user_id == user_id)
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()

            assert user is not None
            assert user.username == f"concurrent_user_{i}"

    async def test_database_constraints_and_validation(self, db_session: AsyncSession):
        """测试数据库约束和验证"""
        # 测试唯一约束
        user_data = get_test_user("student")

        # 创建第一个用户
        user1 = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password="hashed_password",
            role=user_data["role"],
        )

        db_session.add(user1)
        await db_session.commit()

        # 尝试创建相同用户名的用户（应该失败）
        user2 = User(
            username=user_data["username"],  # 相同用户名
            email="different@test.com",
            full_name="Different Name",
            hashed_password="hashed_password",
            role=user_data["role"],
        )

        db_session.add(user2)

        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):  # 应该抛出唯一约束异常
            await db_session.commit()

        await db_session.rollback()

    async def test_query_performance(self, db_session: AsyncSession):
        """测试查询性能"""
        import time

        # 创建大量测试数据
        users = []
        for i in range(100):
            user_data = get_test_user("student")
            user_data["username"] = f"perf_test_user_{i}"
            user_data["email"] = f"perf_test_user_{i}@test.com"

            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password="hashed_password",
                role=user_data["role"],
            )
            users.append(user)

        db_session.add_all(users)
        await db_session.commit()

        # 测试查询性能
        from sqlalchemy import select

        # 简单查询
        start_time = time.time()
        stmt = select(User).limit(10)
        result = await db_session.execute(stmt)
        users_list = result.scalars().all()
        simple_query_time = time.time() - start_time

        assert len(users_list) == 10
        assert simple_query_time < 0.1  # 应该在100ms内完成

        # 复杂查询
        start_time = time.time()
        stmt = (
            select(User)
            .where(User.role == "student", User.is_active)
            .order_by(User.created_at.desc())
            .limit(20)
        )
        result = await db_session.execute(stmt)
        filtered_users = result.scalars().all()
        complex_query_time = time.time() - start_time

        assert len(filtered_users) <= 20
        assert complex_query_time < 0.2  # 应该在200ms内完成

    async def test_data_integrity_and_consistency(self, db_session: AsyncSession):
        """测试数据完整性和一致性"""
        # 创建用户和相关数据
        user = await self.test_user_model_operations(
            db_session, get_test_user("student")
        )
        content = await self.test_content_model_operations(db_session)

        # 创建学习会话
        session = LearningSession(
            user_id=user.user_id,
            content_id=content.content_id,
            content_type=content.content_type,
            start_time=datetime.utcnow(),
            status="active",
        )

        db_session.add(session)
        await db_session.commit()

        # 创建学习进度
        progress = LearningProgress(
            user_id=user.user_id,
            content_type=content.content_type,
            total_study_time=1800,
            sessions_completed=1,
            average_score=85.0,
            last_activity=datetime.utcnow(),
        )

        db_session.add(progress)
        await db_session.commit()

        # 验证数据一致性
        from sqlalchemy import func, select

        # 验证用户的会话数量与进度记录一致
        stmt = select(func.count(LearningSession.session_id)).where(
            LearningSession.user_id == user.user_id,
            LearningSession.content_type == content.content_type,
        )
        result = await db_session.execute(stmt)
        session_count = result.scalar()

        stmt = select(LearningProgress).where(
            LearningProgress.user_id == user.user_id,
            LearningProgress.content_type == content.content_type,
        )
        result = await db_session.execute(stmt)
        progress_record = result.scalar_one()

        assert session_count == progress_record.sessions_completed
