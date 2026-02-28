#!/usr/bin/env python3
"""初始化默认管理员用户脚本."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 注册所有模型以避免循环导入
from app.core.models_registry import register_all_models  # noqa: E402

register_all_models()

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.shared.models.enums import UserType  # noqa: E402
from app.users.models import Permission, Role, User  # noqa: E402
from app.users.utils.jwt_utils import jwt_manager  # noqa: E402


async def create_default_admin() -> User | None:
    """创建默认管理员用户."""
    print("🚀 开始初始化默认管理员用户...")

    # 获取数据库会话
    async with AsyncSessionLocal() as db:
        try:
            # 1. 检查是否已存在管理员用户
            stmt = select(User).where(User.user_type == UserType.ADMIN)
            result = await db.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print(f"✅ 管理员用户已存在: {existing_admin.username}")
                return existing_admin

            # 2. 创建默认管理员用户
            admin_user = User(
                username="admin",
                email="admin@cet4learning.com",
                password_hash=jwt_manager.hash_password("admin123"),
                user_type=UserType.ADMIN,
                is_active=True,
                is_verified=True,
            )

            db.add(admin_user)
            await db.flush()  # 获取用户ID

            print(f"✅ 创建默认管理员用户: {admin_user.username}")

            # 3. 初始化默认权限
            await create_default_permissions(db)

            # 4. 初始化默认角色
            await create_default_roles(db)

            # 5. 为管理员分配超级管理员角色
            stmt = select(Role).where(Role.code == "super_admin")
            result = await db.execute(stmt)
            super_admin_role = result.scalar_one_or_none()

            if super_admin_role:
                # 使用原生SQL插入关联关系
                from sqlalchemy import text

                await db.execute(
                    text(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
                    ),
                    {"user_id": admin_user.id, "role_id": super_admin_role.id},
                )
                print("✅ 为管理员分配超级管理员角色")

            await db.commit()

            print("🎉 默认管理员用户初始化完成！")
            print("   用户名: admin")
            print("   密码: admin123")
            print("   邮箱: admin@cet4learning.com")

            return admin_user

        except Exception as e:
            await db.rollback()
            print(f"❌ 初始化失败: {str(e)}")
            raise


async def create_default_permissions(db: AsyncSession) -> None:
    """创建默认权限."""
    default_permissions = [
        # 用户管理权限
        {"name": "查看用户", "code": "user:view", "module": "users", "action": "view"},
        {
            "name": "创建用户",
            "code": "user:create",
            "module": "users",
            "action": "create",
        },
        {"name": "编辑用户", "code": "user:edit", "module": "users", "action": "edit"},
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
        # 检查权限是否已存在
        stmt = select(Permission).where(Permission.code == perm_data["code"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            permission = Permission(
                name=perm_data["name"],
                code=perm_data["code"],
                module=perm_data["module"],
                action=perm_data["action"],
                is_active=True,
            )
            db.add(permission)

    print("✅ 默认权限创建完成")


async def create_default_roles(db: AsyncSession) -> None:
    """创建默认角色."""
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
        # 检查角色是否已存在
        stmt = select(Role).where(Role.code == role_data["code"])
        result = await db.execute(stmt)
        existing_role = result.scalar_one_or_none()

        if existing_role:
            continue

        # 创建角色
        permissions_list: list[str] = role_data.pop("permissions")
        role = Role(
            name=role_data["name"],
            code=role_data["code"],
            level=role_data["level"],
            description=role_data.get("description"),
            is_system=role_data.get("is_system", False),
            is_active=True,
        )
        db.add(role)
        await db.flush()  # 获取角色ID

        # 分配权限给角色
        if permissions_list == ["*"]:
            # 超级管理员获得所有权限
            stmt = select(Permission).where(Permission.is_active.is_(True))
            result = await db.execute(stmt)
            all_permissions = result.scalars().all()

            from sqlalchemy import text

            for permission in all_permissions:
                await db.execute(
                    text(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"
                    ),
                    {"role_id": role.id, "permission_id": permission.id},
                )
        else:
            # 分配指定权限
            from sqlalchemy import text

            for perm_code in permissions_list:
                stmt = select(Permission).where(Permission.code == perm_code)
                result = await db.execute(stmt)
                permission = result.scalar_one_or_none()

                if permission:
                    await db.execute(
                        text(
                            "INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"
                        ),
                        {"role_id": role.id, "permission_id": permission.id},
                    )

    print("✅ 默认角色创建完成")


async def main() -> None:
    """主函数."""
    try:
        await create_default_admin()
        print("\n🎉 初始化完成！现在可以使用以下账号登录：")
        print("   用户名: admin")
        print("   密码: admin123")

    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
