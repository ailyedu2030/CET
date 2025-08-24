"""数据库配置和连接管理."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.courses.models import *  # noqa: F401, F403

# 导入所有模型以确保表创建
from app.shared.models.base_model import Base  # noqa: F401
from app.training.models import *  # noqa: F401, F403
from app.users.models import *  # noqa: F401, F403

# 创建异步数据库引擎
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=0,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖注入."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_async_session() -> AsyncSession:
    """获取异步数据库会话（用于定时任务）."""
    return AsyncSessionLocal()


async def create_tables() -> None:
    """创建数据库表."""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def init_db() -> None:
    """初始化数据库."""
    await create_tables()


async def close_db() -> None:
    """关闭数据库连接."""
    await engine.dispose()
