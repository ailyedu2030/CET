"""权限管理服务 - 处理角色和权限的增删改查业务逻辑."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.users.models import Permission, Role, User


class PermissionService:
    """权限管理服务类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化权限服务."""
        self.db = db_session

    # ===== 权限管理 =====

    async def create_permission(
        self,
        name: str,
        code: str,
        module: str,
        action: str,
        description: str | None = None,
        resource: str | None = None,
    ) -> Permission:
        """创建权限."""
        permission = Permission(
            name=name,
            code=code,
            description=description,
            module=module,
            action=action,
            resource=resource,
        )

        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)

        return permission

    async def get_permission_by_id(self, permission_id: int) -> Permission | None:
        """根据ID获取权限."""
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(stmt)
        permission: Permission | None = result.scalar_one_or_none()
        return permission

    async def get_permission_by_code(self, code: str) -> Permission | None:
        """根据代码获取权限."""
        stmt = select(Permission).where(Permission.code == code)
        result = await self.db.execute(stmt)
        permission: Permission | None = result.scalar_one_or_none()
        return permission

    async def list_permissions(
        self,
        module: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Permission]:
        """获取权限列表."""
        stmt = select(Permission)

        if module:
            stmt = stmt.where(Permission.module == module)

        if is_active is not None:
            stmt = stmt.where(Permission.is_active == is_active)

        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_permission(
        self,
        permission_id: int,
        updates: dict[str, Any],
    ) -> Permission | None:
        """更新权限."""
        permission = await self.get_permission_by_id(permission_id)
        if not permission:
            return None

        for key, value in updates.items():
            if hasattr(permission, key):
                setattr(permission, key, value)

        await self.db.commit()
        await self.db.refresh(permission)

        return permission

    async def delete_permission(self, permission_id: int) -> bool:
        """删除权限."""
        permission = await self.get_permission_by_id(permission_id)
        if not permission:
            return False

        await self.db.delete(permission)
        await self.db.commit()

        return True

    # ===== 角色管理 =====

    async def create_role(
        self,
        name: str,
        code: str,
        level: int = 0,
        description: str | None = None,
        is_system: bool = False,
    ) -> Role:
        """创建角色."""
        role = Role(
            name=name,
            code=code,
            description=description,
            level=level,
            is_system=is_system,
        )

        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)

        return role

    async def get_role_by_id(self, role_id: int) -> Role | None:
        """根据ID获取角色."""
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self.db.execute(stmt)
        role: Role | None = result.scalar_one_or_none()
        return role

    async def get_role_by_code(self, code: str) -> Role | None:
        """根据代码获取角色."""
        stmt = select(Role).where(Role.code == code).options(selectinload(Role.permissions))
        result = await self.db.execute(stmt)
        role: Role | None = result.scalar_one_or_none()
        return role

    async def list_roles(
        self,
        is_active: bool | None = None,
        is_system: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Role]:
        """获取角色列表."""
        stmt = select(Role).options(selectinload(Role.permissions))

        if is_active is not None:
            stmt = stmt.where(Role.is_active == is_active)

        if is_system is not None:
            stmt = stmt.where(Role.is_system == is_system)

        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_role(
        self,
        role_id: int,
        updates: dict[str, Any],
    ) -> Role | None:
        """更新角色."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return None

        for key, value in updates.items():
            if hasattr(role, key) and key != "permissions":  # 权限单独处理
                setattr(role, key, value)

        await self.db.commit()
        await self.db.refresh(role)

        return role

    async def delete_role(self, role_id: int) -> bool:
        """删除角色."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return False

        # 检查是否为系统内置角色
        if role.is_system:
            return False

        await self.db.delete(role)
        await self.db.commit()

        return True

    # ===== 角色权限关联管理 =====

    async def assign_permissions_to_role(
        self,
        role_id: int,
        permission_ids: list[int],
    ) -> bool:
        """给角色分配权限."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return False

        # 获取权限对象
        permissions = []
        for perm_id in permission_ids:
            permission = await self.get_permission_by_id(perm_id)
            if permission and permission.is_active:
                permissions.append(permission)

        # 替换角色权限
        role.permissions = permissions
        await self.db.commit()

        return True

    async def add_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
    ) -> bool:
        """给角色添加权限."""
        role = await self.get_role_by_id(role_id)
        permission = await self.get_permission_by_id(permission_id)

        if not role or not permission or not permission.is_active:
            return False

        # 检查是否已存在
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.commit()

        return True

    async def remove_permission_from_role(
        self,
        role_id: int,
        permission_id: int,
    ) -> bool:
        """从角色移除权限."""
        role = await self.get_role_by_id(role_id)
        permission = await self.get_permission_by_id(permission_id)

        if not role or not permission:
            return False

        if permission in role.permissions:
            role.permissions.remove(permission)
            await self.db.commit()

        return True

    # ===== 用户角色管理 =====

    async def assign_roles_to_user(
        self,
        user_id: int,
        role_ids: list[int],
    ) -> bool:
        """给用户分配角色."""
        # 获取用户
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if not user:
            return False

        # 获取角色对象
        roles = []
        for role_id in role_ids:
            role = await self.get_role_by_id(role_id)
            if role and role.is_active:
                roles.append(role)

        # 替换用户角色
        user.roles = roles
        await self.db.commit()

        return True

    async def add_role_to_user(
        self,
        user_id: int,
        role_id: int,
    ) -> bool:
        """给用户添加角色."""
        # 获取用户
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        role = await self.get_role_by_id(role_id)

        if not user or not role or not role.is_active:
            return False

        # 检查是否已存在
        if role not in user.roles:
            user.roles.append(role)
            await self.db.commit()

        return True

    async def remove_role_from_user(
        self,
        user_id: int,
        role_id: int,
    ) -> bool:
        """从用户移除角色."""
        # 获取用户
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        role = await self.get_role_by_id(role_id)

        if not user or not role:
            return False

        if role in user.roles:
            user.roles.remove(role)
            await self.db.commit()

        return True

    async def get_user_roles(self, user_id: int) -> list[Role]:
        """获取用户角色."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        return user.roles if user else []

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        """获取用户所有权限."""
        user_roles = await self.get_user_roles(user_id)
        permissions: list[Permission] = []

        for role in user_roles:
            permissions.extend(role.permissions)

        # 去重并返回
        unique_permissions = []
        seen_codes = set()
        for perm in permissions:
            if perm.code not in seen_codes:
                unique_permissions.append(perm)
                seen_codes.add(perm.code)

        return unique_permissions

    # ===== 初始化默认权限和角色 =====

    async def initialize_default_permissions(self) -> None:
        """初始化默认权限."""
        default_permissions = [
            # 用户管理权限
            {
                "name": "查看用户",
                "code": "user:view",
                "module": "users",
                "action": "view",
            },
            {
                "name": "创建用户",
                "code": "user:create",
                "module": "users",
                "action": "create",
            },
            {
                "name": "编辑用户",
                "code": "user:edit",
                "module": "users",
                "action": "edit",
            },
            {
                "name": "删除用户",
                "code": "user:delete",
                "module": "users",
                "action": "delete",
            },
            {
                "name": "审核用户",
                "code": "user:audit",
                "module": "users",
                "action": "audit",
            },
            # 课程管理权限
            {
                "name": "查看课程",
                "code": "course:view",
                "module": "courses",
                "action": "view",
            },
            {
                "name": "创建课程",
                "code": "course:create",
                "module": "courses",
                "action": "create",
            },
            {
                "name": "编辑课程",
                "code": "course:edit",
                "module": "courses",
                "action": "edit",
            },
            {
                "name": "删除课程",
                "code": "course:delete",
                "module": "courses",
                "action": "delete",
            },
            {
                "name": "发布课程",
                "code": "course:publish",
                "module": "courses",
                "action": "publish",
            },
            # 训练管理权限
            {
                "name": "查看训练",
                "code": "training:view",
                "module": "training",
                "action": "view",
            },
            {
                "name": "创建训练",
                "code": "training:create",
                "module": "training",
                "action": "create",
            },
            {
                "name": "编辑训练",
                "code": "training:edit",
                "module": "training",
                "action": "edit",
            },
            {
                "name": "删除训练",
                "code": "training:delete",
                "module": "training",
                "action": "delete",
            },
            # 系统管理权限
            {
                "name": "系统监控",
                "code": "system:monitor",
                "module": "system",
                "action": "monitor",
            },
            {
                "name": "系统配置",
                "code": "system:config",
                "module": "system",
                "action": "config",
            },
            {
                "name": "数据备份",
                "code": "system:backup",
                "module": "system",
                "action": "backup",
            },
        ]

        for perm_data in default_permissions:
            existing = await self.get_permission_by_code(perm_data["code"])
            if not existing:
                await self.create_permission(**perm_data)

    async def initialize_default_roles(self) -> None:
        """初始化默认角色."""
        # 确保权限已创建
        await self.initialize_default_permissions()

        default_roles = [
            {
                "name": "超级管理员",
                "code": "super_admin",
                "level": 100,
                "description": "系统超级管理员，拥有所有权限",
                "is_system": True,
                "permissions": ["*"],  # 所有权限
            },
            {
                "name": "管理员",
                "code": "admin",
                "level": 90,
                "description": "系统管理员",
                "is_system": True,
                "permissions": [
                    "user:view",
                    "user:create",
                    "user:edit",
                    "user:audit",
                    "course:view",
                    "course:create",
                    "course:edit",
                    "course:delete",
                    "training:view",
                    "training:create",
                    "training:edit",
                    "system:monitor",
                ],
            },
            {
                "name": "教师",
                "code": "teacher",
                "level": 50,
                "description": "教师角色",
                "is_system": True,
                "permissions": [
                    "course:view",
                    "course:create",
                    "course:edit",
                    "training:view",
                    "training:create",
                    "training:edit",
                ],
            },
            {
                "name": "学生",
                "code": "student",
                "level": 10,
                "description": "学生角色",
                "is_system": True,
                "permissions": ["training:view"],
            },
        ]

        for role_data in default_roles:
            role_code: str = role_data["code"]  # type: ignore[assignment]
            existing_role = await self.get_role_by_code(role_code)
            if existing_role:
                continue

            # 创建角色
            permissions_list = role_data.pop("permissions")
            role = await self.create_role(
                name=role_data["name"],  # type: ignore[arg-type]
                code=role_data["code"],  # type: ignore[arg-type]
                level=role_data["level"],  # type: ignore[arg-type]
                description=role_data.get("description"),  # type: ignore[arg-type]
                is_system=role_data.get("is_system", False),  # type: ignore[arg-type]
            )

            # 分配权限
            if permissions_list == ["*"]:
                # 分配所有权限给超级管理员
                all_permissions = await self.list_permissions(is_active=True)
                permission_ids = [perm.id for perm in all_permissions]
                await self.assign_permissions_to_role(role.id, permission_ids)
            else:
                # 分配指定权限
                permission_ids = []
                perm_codes: list[str] = permissions_list  # type: ignore[assignment]
                for perm_code in perm_codes:
                    perm = await self.get_permission_by_code(perm_code)
                    if perm:
                        permission_ids.append(perm.id)

                if permission_ids:
                    await self.assign_permissions_to_role(role.id, permission_ids)
