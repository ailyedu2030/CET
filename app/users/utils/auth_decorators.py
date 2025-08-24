"""认证和权限装饰器 - 用于保护API端点."""

from collections.abc import Callable
from functools import wraps
from typing import Annotated, Any, TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.models import User
from app.users.services.auth_service import AuthService
from app.users.utils.jwt_utils import jwt_manager

# 类型变量
F = TypeVar("F", bound=Callable[..., Any])

# HTTP Bearer 方案
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """获取当前认证用户的依赖函数."""
    # 验证令牌
    payload = jwt_manager.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户信息
    try:
        auth_service = AuthService(db)
        user = await auth_service._get_user_by_id(int(payload.get("user_id", 0)))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用",
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前活跃用户的依赖函数."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前已验证用户的依赖函数."""
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户未验证")
    return current_user


# 创建依赖函数的工厂函数
def AuthRequired(
    require_verified: bool = True,
    require_active: bool = True,
) -> Any:
    """创建认证依赖的工厂函数."""
    # 暂时返回简单的依赖
    return Depends(get_current_user)


# 保持向后兼容的AuthRequired装饰器类
class _AuthRequiredDecorator:
    """认证要求装饰器类."""

    def __init__(
        self,
        require_verified: bool = True,
        require_active: bool = True,
    ) -> None:
        """初始化认证装饰器."""
        self.require_verified = require_verified
        self.require_active = require_active

    def __call__(self, func: F) -> F:
        """装饰器调用."""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 从kwargs中获取认证凭据
            credentials = kwargs.get("credentials")
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证凭据缺失",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 验证令牌
            payload = jwt_manager.verify_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的认证令牌",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 获取用户信息
            db_session = kwargs.get("db")
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="数据库连接失败",
                )

            auth_service = AuthService(db_session)
            user = await auth_service.get_user_by_token(credentials.credentials)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 检查用户状态
            if self.require_active and not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账户已被禁用",
                )

            if self.require_verified and not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账户未验证",
                )

            # 将用户信息添加到kwargs中
            kwargs["current_user"] = user
            kwargs["token_payload"] = payload

            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]


class PermissionRequired:
    """权限要求装饰器类."""

    def __init__(
        self,
        required_permission: str | None = None,
        required_role: str | None = None,
        required_permissions: list[str] | None = None,
        require_all_permissions: bool = False,
    ) -> None:
        """初始化权限装饰器."""
        self.required_permission = required_permission
        self.required_role = required_role
        self.required_permissions = required_permissions or []
        self.require_all_permissions = require_all_permissions

    def __call__(self, func: F) -> F:
        """装饰器调用."""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取当前用户（应该由AuthRequired装饰器设置）
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户认证信息缺失",
                )

            # 获取数据库会话
            db_session = kwargs.get("db")
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="数据库连接失败",
                )

            auth_service = AuthService(db_session)

            # 检查单个权限
            if self.required_permission:
                has_permission = await auth_service.verify_user_permission(
                    current_user.id, self.required_permission
                )
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要权限: {self.required_permission}",
                    )

            # 检查角色
            if self.required_role:
                has_role = await auth_service.verify_user_role(current_user.id, self.required_role)
                if not has_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要角色: {self.required_role}",
                    )

            # 检查多个权限
            if self.required_permissions:
                permission_checks = []
                for perm in self.required_permissions:
                    has_perm = await auth_service.verify_user_permission(current_user.id, perm)
                    permission_checks.append(has_perm)

                if self.require_all_permissions:
                    # 需要所有权限
                    if not all(permission_checks):
                        missing_perms = [
                            perm
                            for perm, has in zip(
                                self.required_permissions,
                                permission_checks,
                                strict=False,
                            )
                            if not has
                        ]
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"缺少必要权限: {', '.join(missing_perms)}",
                        )
                else:
                    # 需要任一权限
                    if not any(permission_checks):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"缺少必要权限: {', '.join(self.required_permissions)}",
                        )

            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]


class AdminRequired:
    """管理员权限装饰器类."""

    def __call__(self, func: F) -> F:
        """装饰器调用."""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户认证信息缺失",
                )

            # 获取数据库会话
            db_session = kwargs.get("db")
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="数据库连接失败",
                )

            auth_service = AuthService(db_session)

            # 检查是否为管理员
            is_admin = await auth_service.verify_user_role(
                current_user.id, "admin"
            ) or await auth_service.verify_user_role(current_user.id, "super_admin")

            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要管理员权限",
                )

            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]


async def get_current_admin_user(
    current_user: Any = Depends(get_current_user), db: Any = Depends(get_db)
) -> Any:
    """获取当前管理员用户依赖注入函数."""
    auth_service = AuthService(db)

    # 检查是否为管理员
    is_admin = await auth_service.verify_user_role(
        current_user.id, "admin"
    ) or await auth_service.verify_user_role(current_user.id, "super_admin")

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return current_user


async def get_current_super_admin_user(
    current_user: Any = Depends(get_current_user), db: Any = Depends(get_db)
) -> Any:
    """获取当前超级管理员用户依赖注入函数 - 需求9权限控制."""
    auth_service = AuthService(db)

    # 检查是否为超级管理员
    is_super_admin = await auth_service.verify_user_role(current_user.id, "super_admin")

    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )

    return current_user


def create_permission_dependency(permissions: list[str], require_all: bool = True) -> Any:
    """创建权限检查依赖函数.

    Args:
        permissions: 需要的权限列表
        require_all: 是否需要所有权限，False表示只需要其中一个

    Returns:
        FastAPI依赖函数
    """

    async def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """权限检查依赖函数."""
        auth_service = AuthService(db)

        # 检查权限
        permission_checks = []
        for perm in permissions:
            has_perm = await auth_service.verify_user_permission(current_user.id, perm)
            permission_checks.append(has_perm)

        if require_all:
            # 需要所有权限
            if not all(permission_checks):
                missing_perms = [
                    perm
                    for perm, has in zip(permissions, permission_checks, strict=False)
                    if not has
                ]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要权限: {', '.join(missing_perms)}",
                )
        else:
            # 需要任一权限
            if not any(permission_checks):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要权限: {', '.join(permissions)}",
                )

        return current_user

    return Depends(permission_dependency)


# 装饰器实例
auth_required = AuthRequired()
permission_required = PermissionRequired
admin_required = AdminRequired()


def require_admin(func: F) -> F:
    """简单的管理员权限装饰器函数."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 从依赖注入中获取当前用户
        current_user = None
        for value in kwargs.values():
            if isinstance(value, User):
                current_user = value
                break

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户认证信息缺失",
            )

        # 检查用户类型
        from app.shared.models.enums import UserType

        if current_user.user_type != UserType.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限",
            )

        return await func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
