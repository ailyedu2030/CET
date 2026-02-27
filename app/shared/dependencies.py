"""共享依赖注入模块."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖注入."""
    async for session in get_db():
        yield session


# 类型注解
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
