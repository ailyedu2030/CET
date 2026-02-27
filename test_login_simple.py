import asyncio
import os
import sys
from typing import Self

from app.core.database import AsyncSessionLocal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath("."))


async def test_simple_login() -> None:
    """简单测试登录功能."""
    print("🧪 开始简单测试登录功能...")

    async with AsyncSessionLocal() as db:
        try:
            # 测试导入
            print("📦 测试导入...")
            from app.users.schemas.auth_schemas import LoginRequest, LoginResponse
            from app.users.services.auth_service import AuthService

            print("✅ 导入成功！")

            # 直接调用认证服务
            print("🔐 测试认证服务...")
            auth_service = AuthService(db)

            result = await auth_service.authenticate_user(
                username="admin",
                password="admin123",
                user_type=None,
                ip_address="127.0.0.1",
                user_agent="test-script",
            )

            print("✅ 认证服务调用成功！")
            print(f"   结果类型: {type(result)}")
            print(f"   结果键: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            # 测试数据转换
            print("🔄 测试数据转换...")

            response = LoginResponse(
                access_token=result["tokens"]["access_token"],
                refresh_token=result["tokens"]["refresh_token"],
                token_type=result["tokens"]["token_type"],
                expires_in=result["tokens"]["expires_in"],
                user_info=result["user"],
            )

            print("✅ 响应数据转换成功！")
            print(f"   响应类型: {type(response)}")

            # 测试登录端点逻辑
            print("🌐 测试登录端点逻辑...")

            # 模拟登录请求
            login_data = LoginRequest(username="admin", password="admin123", user_type=None)

            # 模拟request对象
            class MockRequest:
                def __init__(self: Self) -> None:
                    self.client = type("obj", (object,), {"host": "127.0.0.1"})()
                    self.headers = {"user-agent": "test-script"}

            mock_request = MockRequest()

            # 获取客户端IP和User-Agent
            client_ip = getattr(mock_request.client, "host", "127.0.0.1")
            user_agent = mock_request.headers.get("user-agent", "unknown")

            print(f"   客户端IP: {client_ip}")
            print(f"   User-Agent: {user_agent}")

            # 调用认证服务
            result2 = await auth_service.authenticate_user(
                username=login_data.username,
                password=login_data.password,
                user_type=login_data.user_type.value if login_data.user_type else None,
                ip_address=client_ip,
                user_agent=user_agent,
            )

            print("✅ 端点逻辑测试成功！")

            # 转换数据结构以匹配LoginResponse
            response2 = LoginResponse(
                access_token=result2["tokens"]["access_token"],
                refresh_token=result2["tokens"]["refresh_token"],
                token_type=result2["tokens"]["token_type"],
                expires_in=result2["tokens"]["expires_in"],
                user_info=result2["user"],
            )

            print("✅ 完整流程测试成功！")
            print(f"   第二次响应类型: {type(response2)}")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_login())
