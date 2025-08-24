"""认证相关的Pydantic模式定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.models.enums import UserType


class LoginRequest(BaseModel):
    """登录请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    user_type: UserType | None = Field(None, description="用户类型")
    remember_me: bool = Field(default=False, description="记住登录状态")


class LoginResponse(BaseModel):
    """登录响应模式."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user_info: "UserInfo" = Field(..., description="用户信息")


class UserInfo(BaseModel):
    """用户信息模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    user_type: UserType = Field(..., description="用户类型")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模式."""

    refresh_token: str = Field(..., description="刷新令牌")
    session_token: str = Field(..., description="会话令牌")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模式."""

    access_token: str = Field(..., description="新访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    old_password: str = Field(..., min_length=6, max_length=128, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认新密码")


class LogoutRequest(BaseModel):
    """登出请求模式."""

    session_token: str = Field(..., description="会话令牌")


class UserProfile(BaseModel):
    """用户档案模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    user_type: UserType = Field(..., description="用户类型")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    last_login: datetime | None = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 档案信息（根据用户类型动态填充）
    profile_data: dict[str, Any] | None = Field(None, description="档案数据")


class PasswordChangeRequest(BaseModel):
    """修改密码请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    old_password: str = Field(..., min_length=6, max_length=128, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认新密码")


class ProfileUpdateRequest(BaseModel):
    """档案更新请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    email: EmailStr | None = Field(None, description="邮箱地址")
    profile_data: dict[str, Any] | None = Field(None, description="档案数据")
