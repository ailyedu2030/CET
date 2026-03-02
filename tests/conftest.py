"""CET 教育平台测试共享夹具和配置."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试数据库URL - 使用内存SQLite或测试PostgreSQL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# 测试会话工厂
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环夹具."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator:
    """测试数据库夹具 - 创建表."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_db: Any) -> AsyncGenerator[AsyncSession, None]:
    """数据库会话夹具."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def override_get_db(db_session: AsyncSession) -> AsyncGenerator:
    """覆盖get_db依赖以使用测试数据库."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """测试用户数据."""
    return {
        "username": f"test_user_{uuid4().hex[:8]}",
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "full_name": "测试用户",
        "hashed_password": "hashed_password_here",
        "role": "student",
        "is_active": True,
    }


@pytest.fixture
def test_teacher_data() -> dict[str, Any]:
    """测试教师数据."""
    return {
        "username": f"test_teacher_{uuid4().hex[:8]}",
        "email": f"teacher_{uuid4().hex[:8]}@example.com",
        "full_name": "测试教师",
        "hashed_password": "hashed_password_here",
        "role": "teacher",
        "is_active": True,
    }


@pytest.fixture
def test_admin_data() -> dict[str, Any]:
    """测试管理员数据."""
    return {
        "username": f"test_admin_{uuid4().hex[:8]}",
        "email": f"admin_{uuid4().hex[:8]}@example.com",
        "full_name": "测试管理员",
        "hashed_password": "hashed_password_here",
        "role": "admin",
        "is_active": True,
    }


@pytest.fixture
def test_competition_data() -> dict[str, Any]:
    """测试竞赛数据."""
    now = datetime.utcnow()
    return {
        "competition_id": f"comp_{uuid4().hex[:8]}",
        "title": "测试竞赛",
        "description": "这是一个测试竞赛",
        "competition_type": "speed_challenge",
        "difficulty_level": "intermediate",
        "start_time": now + timedelta(days=1),
        "end_time": now + timedelta(days=2),
        "registration_deadline": now + timedelta(hours=12),
        "organizer_id": 1,
        "max_participants": 100,
        "status": "upcoming",
    }


@pytest.fixture
def test_achievement_data() -> dict[str, Any]:
    """测试成就数据."""
    return {
        "achievement_id": f"ach_{uuid4().hex[:8]}",
        "title": "测试成就",
        "description": "这是一个测试成就",
        "achievement_type": "completion",
        "criteria": {"type": "completion", "target": 10},
        "points": 100,
        "badge": "test_badge",
        "is_active": True,
    }


@pytest.fixture
def test_goal_data() -> dict[str, Any]:
    """测试学习目标数据."""
    now = datetime.utcnow()
    return {
        "goal_id": f"goal_{uuid4().hex[:8]}",
        "user_id": 1,
        "title": "测试学习目标",
        "description": "这是一个测试学习目标",
        "goal_type": "vocabulary",
        "target_value": 100,
        "current_value": 0,
        "start_date": now.date(),
        "end_date": (now + timedelta(days=30)).date(),
        "status": "active",
    }


@pytest.fixture
def test_learning_plan_data() -> dict[str, Any]:
    """测试学习计划数据."""
    now = datetime.utcnow()
    return {
        "plan_id": f"plan_{uuid4().hex[:8]}",
        "user_id": 1,
        "title": "测试学习计划",
        "description": "这是一个测试学习计划",
        "plan_type": "weekly",
        "start_date": now.date(),
        "end_date": (now + timedelta(days=7)).date(),
        "daily_goals": {"vocabulary": 20, "reading": 1},
        "status": "active",
    }


@pytest.fixture
def mock_file_metadata() -> dict[str, Any]:
    """模拟文件元数据."""
    return {
        "file_id": f"file_{uuid4().hex[:8]}",
        "original_name": "test_document.pdf",
        "object_name": f"uploads/{uuid4().hex}/test_document.pdf",
        "bucket_type": "documents",
        "file_size": 1024000,
        "content_type": "application/pdf",
        "file_hash": "test_hash_12345",
        "upload_time": datetime.utcnow(),
        "uploaded_by": "test_user",
        "access_level": "private",
        "version": 1,
        "is_deleted": False,
        "metadata": {"category": "learning"},
    }


@pytest.fixture
def sample_questions() -> list[dict[str, Any]]:
    """示例题目数据."""
    return [
        {
            "question_id": f"q_{uuid4().hex[:8]}",
            "question_type": "multiple_choice",
            "difficulty_level": "easy",
            "content": "这是一个测试题目？",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "correct_answer": "A",
            "explanation": "这是解释",
            "tags": ["vocabulary", "beginner"],
        },
        {
            "question_id": f"q_{uuid4().hex[:8]}",
            "question_type": "true_false",
            "difficulty_level": "easy",
            "content": "这是一个判断题？",
            "correct_answer": True,
            "explanation": "这是解释",
            "tags": ["grammar", "beginner"],
        },
    ]


@pytest.fixture
def test_time_range() -> tuple[datetime, datetime]:
    """测试时间范围."""
    now = datetime.utcnow()
    return now - timedelta(days=7), now


@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession) -> None:
    """测试数据库连接."""
    result = await db_session.execute(text("SELECT 1 as test"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_transaction_rollback(db_session: AsyncSession) -> None:
    """测试事务回滚."""
    # 这里可以添加具体的事务测试
    assert True
