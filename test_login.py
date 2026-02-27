#!/usr/bin/env python3
"""测试登录功能的脚本."""

import asyncio
import sys
from pathlib import Path

from app.core.database import AsyncSessionLocal
from app.users.services.auth_service import AuthService

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_login() -> None:
    """测试登录功能."""
    print("🧪 开始测试登录功能...")

    async with AsyncSessionLocal() as db:
        try:
            # 首先检查用户是否存在
            from sqlalchemy import select

            from app.users.models import User

            stmt = select(User).where(User.username == "admin")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                print("❌ 用户不存在")
                return

            print(f"✅ 找到用户: {user.username}, ID: {user.id}, 类型: {user.user_type}")

            # 测试密码验证
            from app.users.utils.jwt_utils import jwt_manager

            is_valid = jwt_manager.verify_password("admin123", user.password_hash)
            print(f"✅ 密码验证: {'通过' if is_valid else '失败'}")

            if not is_valid:
                return

            # 测试认证服务
            service = AuthService(db)

            result = await service.authenticate_user(
                username="admin",
                password="admin123",
                user_type=None,
                ip_address="127.0.0.1",
                user_agent="test-script",
            )

            print("✅ 登录成功！")
            print(f"   结果类型: {type(result)}")
            print(f"   结果内容: {result}")

        except Exception as e:
            print(f"❌ 登录失败: {str(e)}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_login())
