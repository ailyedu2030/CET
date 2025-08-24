"""权限管理相关的Pydantic模型 - 需求7：权限中枢管理."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ===== 权限相关Schema =====


class PermissionCreateRequest(BaseModel):
    """创建权限请求模型."""

    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    module: str = Field(..., min_length=1, max_length=50, description="所属模块")
    action: str = Field(..., min_length=1, max_length=50, description="操作类型")
    description: str | None = Field(None, max_length=500, description="权限描述")
    resource: str | None = Field(None, max_length=100, description="资源类型")


class PermissionUpdateRequest(BaseModel):
    """更新权限请求模型."""

    name: str | None = Field(None, min_length=1, max_length=100, description="权限名称")
    description: str | None = Field(None, max_length=500, description="权限描述")
    is_active: bool | None = Field(None, description="是否激活")


class PermissionResponse(BaseModel):
    """权限响应模型."""

    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: str | None = Field(None, description="权限描述")
    module: str = Field(..., description="所属模块")
    action: str = Field(..., description="操作类型")
    resource: str | None = Field(None, description="资源类型")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# ===== 角色相关Schema =====


class RoleCreateRequest(BaseModel):
    """创建角色请求模型."""

    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    description: str | None = Field(None, max_length=500, description="角色描述")
    level: int = Field(0, ge=0, le=100, description="角色等级")


class RoleUpdateRequest(BaseModel):
    """更新角色请求模型."""

    name: str | None = Field(None, min_length=1, max_length=50, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    level: int | None = Field(None, ge=0, le=100, description="角色等级")
    is_active: bool | None = Field(None, description="是否激活")


class RoleResponse(BaseModel):
    """角色响应模型."""

    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    description: str | None = Field(None, description="角色描述")
    level: int = Field(..., description="角色等级")
    is_active: bool = Field(..., description="是否激活")
    is_system: bool = Field(..., description="是否系统角色")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")

    class Config:
        """Pydantic配置."""

        from_attributes = True


# ===== 用户角色分配相关Schema =====


class UserRoleAssignRequest(BaseModel):
    """用户角色分配请求模型."""

    role_ids: list[int] = Field(..., min_length=1, description="角色ID列表")


class PermissionAssignRequest(BaseModel):
    """权限分配请求模型."""

    permission_ids: list[int] = Field(..., min_length=1, description="权限ID列表")


class UserPermissionResponse(BaseModel):
    """用户权限响应模型."""

    user_id: int = Field(..., description="用户ID")
    permissions: list[dict[str, Any]] = Field(..., description="权限列表")
    roles: list[dict[str, Any]] = Field(..., description="角色列表")


# ===== 权限检查相关Schema =====


class PermissionCheckRequest(BaseModel):
    """权限检查请求模型."""

    user_id: int = Field(..., description="用户ID")
    permission_code: str = Field(..., description="权限代码")
    resource_id: str | None = Field(None, description="资源ID")


class PermissionCheckResponse(BaseModel):
    """权限检查响应模型."""

    user_id: int = Field(..., description="用户ID")
    permission_code: str = Field(..., description="权限代码")
    has_permission: bool = Field(..., description="是否有权限")
    reason: str | None = Field(None, description="权限检查原因")


# ===== 权限统计相关Schema =====


class PermissionStatsResponse(BaseModel):
    """权限统计响应模型."""

    total_permissions: int = Field(..., description="总权限数")
    active_permissions: int = Field(..., description="激活权限数")
    total_roles: int = Field(..., description="总角色数")
    active_roles: int = Field(..., description="激活角色数")
    total_users_with_roles: int = Field(..., description="有角色的用户数")


# ===== 多级权限体系相关Schema =====


class AdminRoleCreateRequest(BaseModel):
    """管理员角色创建请求模型 - 需求7验收标准1."""

    role_type: str = Field(
        ...,
        description="管理员角色类型",
        pattern="^(super_admin|academic_admin|audit_admin)$",
    )
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    permissions: list[str] = Field(..., description="权限代码列表")


class RoleHierarchyResponse(BaseModel):
    """角色层级响应模型 - 需求7验收标准1."""

    role_id: int = Field(..., description="角色ID")
    role_name: str = Field(..., description="角色名称")
    role_code: str = Field(..., description="角色代码")
    level: int = Field(..., description="角色等级")
    parent_roles: list[dict[str, Any]] = Field(..., description="父级角色")
    child_roles: list[dict[str, Any]] = Field(..., description="子级角色")
    permissions: list[dict[str, Any]] = Field(..., description="权限列表")


# ===== 权限继承相关Schema =====


class PermissionInheritanceRequest(BaseModel):
    """权限继承请求模型 - 需求7验收标准2."""

    parent_role_id: int = Field(..., description="父角色ID")
    child_role_id: int = Field(..., description="子角色ID")
    inherit_all: bool = Field(True, description="是否继承所有权限")
    specific_permissions: list[str] | None = Field(None, description="特定权限代码列表")


class PermissionInheritanceResponse(BaseModel):
    """权限继承响应模型 - 需求7验收标准2."""

    parent_role: dict[str, Any] = Field(..., description="父角色信息")
    child_role: dict[str, Any] = Field(..., description="子角色信息")
    inherited_permissions: list[dict[str, Any]] = Field(..., description="继承的权限")
    inheritance_rules: dict[str, Any] = Field(..., description="继承规则")


# ===== 数据访问权限相关Schema =====


class DataAccessPermissionRequest(BaseModel):
    """数据访问权限请求模型 - 需求7验收标准2."""

    user_id: int = Field(..., description="用户ID")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    access_level: str = Field(
        ...,
        description="访问级别",
        pattern="^(read|write|delete|admin)$",
    )
    scope: str = Field(
        ...,
        description="访问范围",
        pattern="^(personal|department|school|system)$",
    )


class DataAccessPermissionResponse(BaseModel):
    """数据访问权限响应模型 - 需求7验收标准2."""

    user_id: int = Field(..., description="用户ID")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    access_level: str = Field(..., description="访问级别")
    scope: str = Field(..., description="访问范围")
    granted: bool = Field(..., description="是否授权")
    reason: str | None = Field(None, description="授权原因")
    expires_at: datetime | None = Field(None, description="过期时间")


# ===== 动态权限相关Schema =====


class DynamicPermissionRequest(BaseModel):
    """动态权限请求模型 - 需求7验收标准2."""

    user_id: int = Field(..., description="用户ID")
    permission_code: str = Field(..., description="权限代码")
    context: dict[str, Any] = Field(..., description="权限上下文")
    duration_minutes: int | None = Field(None, ge=1, description="权限持续时间（分钟）")


class DynamicPermissionResponse(BaseModel):
    """动态权限响应模型 - 需求7验收标准2."""

    user_id: int = Field(..., description="用户ID")
    permission_code: str = Field(..., description="权限代码")
    granted: bool = Field(..., description="是否授权")
    context: dict[str, Any] = Field(..., description="权限上下文")
    granted_at: datetime = Field(..., description="授权时间")
    expires_at: datetime | None = Field(None, description="过期时间")
    session_id: str | None = Field(None, description="会话ID")
