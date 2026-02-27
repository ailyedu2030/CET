"""用户模块依赖注入."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_db_session
from app.users.models.user_models import User
from app.users.services.auth_service import AuthService

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """获取当前用户依赖注入."""
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> User | None:
    """获取当前用户（可选）依赖注入."""
    if not credentials:
        return None

    try:
        auth_service = AuthService(db)
        return await auth_service.get_user_by_token(credentials.credentials)
    except Exception as e:
        logger.warning(f"User dependency error: {e}")
        return None


# 类型注解
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[User | None, Depends(get_current_user_optional)]
