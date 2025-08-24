"""JWT认证工具类 - 提供JWT令牌的生成、验证和解析功能."""

import secrets
from datetime import datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings
from app.shared.models.enums import UserType

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTManager:
    """JWT管理器 - 处理JWT令牌的完整生命周期."""

    def __init__(self) -> None:
        """初始化JWT管理器."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """创建访问令牌."""
        to_encode = data.copy()

        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        token: str = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """创建刷新令牌."""
        to_encode = data.copy()

        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        token: str = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """验证令牌."""
        try:
            payload: dict[str, Any] = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            return payload
        except ExpiredSignatureError:
            return None
        except (DecodeError, InvalidTokenError):
            return None

    def decode_token(self, token: str) -> dict[str, Any]:
        """解码令牌（不验证过期时间）."""
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            return payload
        except (DecodeError, InvalidTokenError):
            return {}

    def create_token_pair(
        self,
        user_id: int,
        username: str,
        user_type: UserType,
        roles: list[str] | None = None,
    ) -> dict[str, str]:
        """创建访问令牌和刷新令牌对."""
        token_data = {
            "sub": str(user_id),
            "username": username,
            "user_type": user_type.value,
            "roles": roles or [],
        }

        access_token = self.create_access_token(data=token_data)
        refresh_token = self.create_refresh_token(data={"sub": str(user_id), "username": username})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str) -> str | None:
        """使用刷新令牌生成新的访问令牌."""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        # 验证令牌类型
        if payload.get("type") != "refresh":
            return None

        # 创建新的访问令牌
        new_token_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
        }

        access_token: str = self.create_access_token(data=new_token_data)
        return access_token

    @staticmethod
    def generate_session_token() -> str:
        """生成安全的会话令牌."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码."""
        hashed: str = pwd_context.hash(password)
        return hashed

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码."""
        result: bool = pwd_context.verify(plain_password, hashed_password)
        return result

    @staticmethod
    def generate_reset_token() -> str:
        """生成密码重置令牌."""
        return secrets.token_urlsafe(32)


class PermissionChecker:
    """权限检查器 - 提供权限验证功能."""

    @staticmethod
    def check_permission(
        user_permissions: list[str],
        required_permission: str,
    ) -> bool:
        """检查用户是否有指定权限."""
        return required_permission in user_permissions

    @staticmethod
    def check_role(
        user_roles: list[str],
        required_role: str,
    ) -> bool:
        """检查用户是否有指定角色."""
        return required_role in user_roles

    @staticmethod
    def check_any_permission(
        user_permissions: list[str],
        required_permissions: list[str],
    ) -> bool:
        """检查用户是否有任一指定权限."""
        return any(perm in user_permissions for perm in required_permissions)

    @staticmethod
    def check_all_permissions(
        user_permissions: list[str],
        required_permissions: list[str],
    ) -> bool:
        """检查用户是否有所有指定权限."""
        return all(perm in user_permissions for perm in required_permissions)

    @staticmethod
    def check_user_level(
        user_level: int,
        required_level: int,
    ) -> bool:
        """检查用户等级是否满足要求."""
        return user_level >= required_level

    @staticmethod
    def is_admin(user_roles: list[str]) -> bool:
        """检查用户是否为管理员."""
        return "admin" in user_roles or "super_admin" in user_roles

    @staticmethod
    def is_teacher(user_roles: list[str]) -> bool:
        """检查用户是否为教师."""
        return "teacher" in user_roles

    @staticmethod
    def is_student(user_roles: list[str]) -> bool:
        """检查用户是否为学生."""
        return "student" in user_roles


# 创建全局实例
jwt_manager = JWTManager()
permission_checker = PermissionChecker()
