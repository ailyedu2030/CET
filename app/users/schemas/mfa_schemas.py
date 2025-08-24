"""多因素认证相关的Pydantic模型 - 需求7：权限中枢管理."""

from pydantic import BaseModel, Field, validator

# ===== 短信验证相关Schema =====


class SMSVerificationRequest(BaseModel):
    """短信验证码发送请求模型."""

    phone_number: str = Field(..., min_length=11, max_length=11, description="手机号码")
    purpose: str = Field(
        "login",
        description="验证目的",
        pattern="^(login|register|reset_password|bind_phone)$",
    )

    @validator("phone_number")
    def validate_phone_number(cls, v: str) -> str:
        """验证手机号码格式."""
        if not v.isdigit():
            raise ValueError("手机号码只能包含数字")
        if not v.startswith(("13", "14", "15", "16", "17", "18", "19")):
            raise ValueError("手机号码格式不正确")
        return v


# ===== 邮箱验证相关Schema =====


class EmailVerificationRequest(BaseModel):
    """邮箱验证码发送请求模型."""

    email: str = Field(..., description="邮箱地址")
    purpose: str = Field(
        "login",
        description="验证目的",
        pattern="^(login|register|reset_password|bind_email)$",
    )

    @validator("email")
    def validate_email(cls, v: str) -> str:
        """验证邮箱格式."""
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("邮箱格式不正确")
        return v.lower()


# ===== 验证码验证相关Schema =====


class VerificationCodeRequest(BaseModel):
    """验证码验证请求模型."""

    target: str = Field(..., description="验证目标（手机号或邮箱）")
    verification_code: str = Field(..., min_length=6, max_length=6, description="验证码")
    purpose: str = Field("login", description="验证目的")

    @validator("verification_code")
    def validate_verification_code(cls, v: str) -> str:
        """验证验证码格式."""
        if not v.isdigit():
            raise ValueError("验证码只能包含数字")
        return v


class VerificationResponse(BaseModel):
    """验证响应模型."""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    expires_in: int | None = Field(None, description="过期时间（秒）")
    masked_target: str | None = Field(None, description="掩码后的目标")
    verified_user_id: int | None = Field(None, description="验证成功的用户ID")
    remaining_attempts: int | None = Field(None, description="剩余尝试次数")


# ===== MFA会话相关Schema =====


class MFASessionRequest(BaseModel):
    """MFA会话创建请求模型."""

    mfa_method: str = Field(..., description="MFA方法", pattern="^(sms|email|totp|backup_code)$")
    session_duration_minutes: int = Field(30, ge=5, le=120, description="会话持续时间（分钟）")


class MFASessionResponse(BaseModel):
    """MFA会话响应模型."""

    success: bool = Field(..., description="是否成功")
    mfa_token: str = Field(..., description="MFA令牌")
    expires_in: int = Field(..., description="过期时间（秒）")
    mfa_method: str = Field(..., description="MFA方法")


# ===== MFA配置相关Schema =====


class MFAConfigRequest(BaseModel):
    """MFA配置请求模型."""

    enable_mfa: bool = Field(..., description="是否启用MFA")
    primary_method: str = Field(..., description="主要MFA方法", pattern="^(sms|email|totp)$")
    backup_methods: list[str] = Field([], description="备用MFA方法")
    require_for_admin: bool = Field(True, description="管理员操作是否需要MFA")


class MFAConfigResponse(BaseModel):
    """MFA配置响应模型."""

    user_id: int = Field(..., description="用户ID")
    mfa_enabled: bool = Field(..., description="是否启用MFA")
    primary_method: str | None = Field(None, description="主要MFA方法")
    backup_methods: list[str] = Field([], description="备用MFA方法")
    configured_methods: list[str] = Field([], description="已配置的方法")
    require_for_admin: bool = Field(..., description="管理员操作是否需要MFA")
    last_updated: str | None = Field(None, description="最后更新时间")


# ===== TOTP相关Schema =====


class TOTPSetupRequest(BaseModel):
    """TOTP设置请求模型."""

    user_id: int = Field(..., description="用户ID")
    app_name: str = Field("CET4学习系统", description="应用名称")


class TOTPSetupResponse(BaseModel):
    """TOTP设置响应模型."""

    secret: str = Field(..., description="TOTP密钥")
    qr_code_url: str = Field(..., description="二维码URL")
    backup_codes: list[str] = Field(..., description="备用代码")
    setup_instructions: str = Field(..., description="设置说明")


class TOTPVerificationRequest(BaseModel):
    """TOTP验证请求模型."""

    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP代码")

    @validator("totp_code")
    def validate_totp_code(cls, v: str) -> str:
        """验证TOTP代码格式."""
        if not v.isdigit():
            raise ValueError("TOTP代码只能包含数字")
        return v


# ===== 备用代码相关Schema =====


class BackupCodeRequest(BaseModel):
    """备用代码请求模型."""

    backup_code: str = Field(..., min_length=8, max_length=16, description="备用代码")


class BackupCodeResponse(BaseModel):
    """备用代码响应模型."""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    remaining_codes: int | None = Field(None, description="剩余备用代码数量")


# ===== MFA状态相关Schema =====


class MFAStatusResponse(BaseModel):
    """MFA状态响应模型."""

    user_id: int = Field(..., description="用户ID")
    mfa_enabled: bool = Field(..., description="是否启用MFA")
    available_methods: list[str] = Field(..., description="可用的MFA方法")
    configured_methods: list[str] = Field(..., description="已配置的MFA方法")
    last_mfa_verification: str | None = Field(None, description="最后MFA验证时间")
    session_valid: bool = Field(False, description="当前会话是否已通过MFA验证")


# ===== MFA审计相关Schema =====


class MFALogRequest(BaseModel):
    """MFA日志查询请求模型."""

    user_id: int | None = Field(None, description="用户ID")
    method: str | None = Field(None, description="MFA方法")
    start_date: str | None = Field(None, description="开始日期")
    end_date: str | None = Field(None, description="结束日期")
    success_only: bool = Field(False, description="只查询成功记录")


class MFALogResponse(BaseModel):
    """MFA日志响应模型."""

    log_id: str = Field(..., description="日志ID")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    method: str = Field(..., description="MFA方法")
    action: str = Field(..., description="操作类型")
    success: bool = Field(..., description="是否成功")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    timestamp: str = Field(..., description="时间戳")
    details: dict[str, str] | None = Field(None, description="详细信息")


# ===== 单点登录相关Schema =====


class SSOLoginRequest(BaseModel):
    """SSO登录请求模型."""

    provider: str = Field(..., description="SSO提供商", pattern="^(wechat|dingtalk|ldap)$")
    auth_code: str = Field(..., description="授权码")
    redirect_uri: str | None = Field(None, description="重定向URI")


class SSOLoginResponse(BaseModel):
    """SSO登录响应模型."""

    success: bool = Field(..., description="是否成功")
    access_token: str | None = Field(None, description="访问令牌")
    refresh_token: str | None = Field(None, description="刷新令牌")
    user_info: dict[str, str] | None = Field(None, description="用户信息")
    requires_mfa: bool = Field(False, description="是否需要MFA")
    mfa_methods: list[str] = Field([], description="可用的MFA方法")


# ===== 会话超时控制相关Schema =====


class SessionTimeoutRequest(BaseModel):
    """会话超时配置请求模型."""

    timeout_minutes: int = Field(..., ge=5, le=480, description="超时时间（分钟）")
    warning_minutes: int = Field(..., ge=1, le=60, description="警告时间（分钟）")
    auto_extend: bool = Field(False, description="是否自动延期")


class SessionTimeoutResponse(BaseModel):
    """会话超时配置响应模型."""

    user_id: int = Field(..., description="用户ID")
    timeout_minutes: int = Field(..., description="超时时间（分钟）")
    warning_minutes: int = Field(..., description="警告时间（分钟）")
    auto_extend: bool = Field(..., description="是否自动延期")
    current_session_expires_at: str | None = Field(None, description="当前会话过期时间")
    last_activity: str | None = Field(None, description="最后活动时间")
