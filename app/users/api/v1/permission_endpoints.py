"""权限管理API端点 - 需求7：权限中枢管理."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.schemas.permission_schemas import (
    PermissionAssignRequest,
    PermissionCreateRequest,
    PermissionResponse,
    PermissionUpdateRequest,
    RoleCreateRequest,
    RoleResponse,
    UserRoleAssignRequest,
)
from app.users.services.permission_service import PermissionService
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permissions", tags=["权限管理"])


# ===== 权限管理端点 =====


@router.post("/", response_model=PermissionResponse)
async def create_permission(
    request: PermissionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    """创建权限 - 需求7验收标准1."""
    # 权限检查：只有超级管理员可以创建权限
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建权限",
        )

    try:
        service = PermissionService(db)
        permission = await service.create_permission(
            name=request.name,
            code=request.code,
            module=request.module,
            action=request.action,
            description=request.description,
            resource=request.resource,
        )

        logger.info(f"超级管理员 {current_user.id} 创建权限: {permission.code}")

        return PermissionResponse(
            id=permission.id,
            name=permission.name,
            code=permission.code,
            description=permission.description,
            module=permission.module,
            action=permission.action,
            resource=permission.resource,
            is_active=permission.is_active,
            created_at=permission.created_at,
            updated_at=permission.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"创建权限失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建权限失败",
        ) from e


@router.get("/", response_model=list[PermissionResponse])
async def get_permissions(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    module: str | None = Query(None, description="模块筛选"),
    is_active: bool | None = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionResponse]:
    """获取权限列表 - 需求7验收标准1."""
    # 权限检查：只有管理员可以查看权限列表
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看权限列表",
        )

    try:
        service = PermissionService(db)
        permissions = await service.list_permissions(
            offset=skip,
            limit=limit,
            module=module,
            is_active=is_active,
        )

        logger.info(f"管理员 {current_user.id} 查看权限列表")

        return [
            PermissionResponse(
                id=perm.id,
                name=perm.name,
                code=perm.code,
                description=perm.description,
                module=perm.module,
                action=perm.action,
                resource=perm.resource,
                is_active=perm.is_active,
                created_at=perm.created_at,
                updated_at=perm.updated_at,
            )
            for perm in permissions
        ]

    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限列表失败",
        ) from e


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    """获取权限详情 - 需求7验收标准1."""
    # 权限检查：只有管理员可以查看权限详情
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看权限详情",
        )

    try:
        service = PermissionService(db)
        permission = await service.get_permission_by_id(permission_id)

        if not permission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="权限不存在",
            )

        logger.info(f"管理员 {current_user.id} 查看权限详情: {permission.code}")

        return PermissionResponse(
            id=permission.id,
            name=permission.name,
            code=permission.code,
            description=permission.description,
            module=permission.module,
            action=permission.action,
            resource=permission.resource,
            is_active=permission.is_active,
            created_at=permission.created_at,
            updated_at=permission.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取权限详情失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限详情失败",
        ) from e


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int,
    request: PermissionUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    """更新权限 - 需求7验收标准1."""
    # 权限检查：只有超级管理员可以更新权限
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以更新权限",
        )

    try:
        service = PermissionService(db)
        permission = await service.update_permission(
            permission_id=permission_id,
            **request.model_dump(exclude_unset=True),
        )

        if not permission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="权限不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 更新权限: {permission.code}")

        return PermissionResponse(
            id=permission.id,
            name=permission.name,
            code=permission.code,
            description=permission.description,
            module=permission.module,
            action=permission.action,
            resource=permission.resource,
            is_active=permission.is_active,
            created_at=permission.created_at,
            updated_at=permission.updated_at,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"更新权限失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新权限失败",
        ) from e


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除权限 - 需求7验收标准1."""
    # 权限检查：只有超级管理员可以删除权限
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除权限",
        )

    try:
        service = PermissionService(db)
        success = await service.delete_permission(permission_id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="权限不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 删除权限: {permission_id}")

        return {
            "message": "权限删除成功",
            "permission_id": permission_id,
            "deleted_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除权限失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除权限失败",
        ) from e


# ===== 角色管理端点 =====


@router.post("/roles/", response_model=RoleResponse)
async def create_role(
    request: RoleCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """创建角色 - 需求7验收标准1."""
    # 权限检查：只有超级管理员可以创建角色
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建角色",
        )

    try:
        service = PermissionService(db)
        role = await service.create_role(
            name=request.name,
            code=request.code,
            description=request.description,
            level=request.level,
        )

        logger.info(f"超级管理员 {current_user.id} 创建角色: {role.code}")

        return RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            level=role.level,
            is_active=role.is_active,
            is_system=role.is_system,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建角色失败",
        ) from e


@router.get("/roles/", response_model=list[RoleResponse])
async def get_roles(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    is_active: bool | None = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RoleResponse]:
    """获取角色列表 - 需求7验收标准1."""
    # 权限检查：只有管理员可以查看角色列表
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看角色列表",
        )

    try:
        service = PermissionService(db)
        roles = await service.list_roles(
            offset=skip,
            limit=limit,
            is_active=is_active,
        )

        logger.info(f"管理员 {current_user.id} 查看角色列表")

        return [
            RoleResponse(
                id=role.id,
                name=role.name,
                code=role.code,
                description=role.description,
                level=role.level,
                is_active=role.is_active,
                is_system=role.is_system,
                created_at=role.created_at,
                updated_at=role.updated_at,
            )
            for role in roles
        ]

    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色列表失败",
        ) from e


@router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: int,
    request: PermissionAssignRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """给角色分配权限 - 需求7验收标准2."""
    # 权限检查：只有超级管理员可以分配权限
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以分配权限",
        )

    try:
        service = PermissionService(db)
        success = await service.assign_permissions_to_role(
            role_id=role_id,
            permission_ids=request.permission_ids,
        )

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="角色不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 给角色 {role_id} 分配权限")

        return {
            "message": "权限分配成功",
            "role_id": role_id,
            "permission_ids": request.permission_ids,
            "assigned_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配权限失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配权限失败",
        ) from e


@router.post("/users/{user_id}/roles")
async def assign_roles_to_user(
    user_id: int,
    request: UserRoleAssignRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """给用户分配角色 - 需求7验收标准2."""
    # 权限检查：只有超级管理员可以分配角色
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以分配角色",
        )

    try:
        service = PermissionService(db)
        success = await service.assign_roles_to_user(
            user_id=user_id,
            role_ids=request.role_ids,
        )

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

        logger.info(f"超级管理员 {current_user.id} 给用户 {user_id} 分配角色")

        return {
            "message": "角色分配成功",
            "user_id": user_id,
            "role_ids": request.role_ids,
            "assigned_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配角色失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配角色失败",
        ) from e


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取用户权限 - 需求7验收标准3."""
    # 权限检查：管理员可以查看所有用户权限，用户只能查看自己的权限
    if current_user.user_type != UserType.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只能查看自己的权限",
        )

    try:
        service = PermissionService(db)
        permissions = await service.get_user_permissions(user_id)
        roles = await service.get_user_roles(user_id)

        logger.info(f"用户 {current_user.id} 查看用户 {user_id} 的权限")

        return {
            "user_id": user_id,
            "permissions": [
                {
                    "id": perm.id,
                    "name": perm.name,
                    "code": perm.code,
                    "module": perm.module,
                    "action": perm.action,
                    "resource": perm.resource,
                }
                for perm in permissions
            ],
            "roles": [
                {
                    "id": role.id,
                    "name": role.name,
                    "code": role.code,
                    "level": role.level,
                }
                for role in roles
            ],
        }

    except Exception as e:
        logger.error(f"获取用户权限失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户权限失败",
        ) from e
