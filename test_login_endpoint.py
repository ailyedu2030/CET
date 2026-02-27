import asyncio
import os
import sys
from typing import Self

from app.core.database import AsyncSessionLocal
from app.users.services.auth_service import AuthService

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath("."))


async def test_login_endpoint() -> None:
    """直接测试登录端点逻辑."""
    print("🧪 开始测试登录端点逻辑...")

    async with AsyncSessionLocal() as db:
        try:
            # 模拟登录端点的逻辑
            from app.users.schemas.auth_schemas import LoginRequest

            # 创建登录请求数据
            login_data = LoginRequest(username="admin", password="admin123", user_type=None)

            # 模拟request对象
            class MockRequest:
                def __init__(self: Self) -> None:
                    self.client = type("obj", (object,), {"host": "127.0.0.1"})()
                    self.headers = {"user-agent": "test-script"}

            mock_request = MockRequest()

            # 直接调用认证服务
            auth_service = AuthService(db)

            # 获取客户端IP和User-Agent
            client_ip = getattr(mock_request.client, "host", "127.0.0.1")
            user_agent = mock_request.headers.get("user-agent", "unknown")

            # 调用认证服务
            result = await auth_service.authenticate_user(
                username=login_data.username,
                password=login_data.password,
                user_type=getattr(login_data, "user_type", None),
                ip_address=client_ip,
                user_agent=user_agent,
            )

            print("✅ 认证服务调用成功！")
            print(f"   结果类型: {type(result)}")
            print(f"   结果: {result}")

            # 测试数据转换
            from app.users.schemas.auth_schemas import LoginResponse

            response = LoginResponse(
                access_token=result["tokens"]["access_token"],
                refresh_token=result["tokens"]["refresh_token"],
                token_type=result["tokens"]["token_type"],
                expires_in=result["tokens"]["expires_in"],
                user_info=result["user"],
            )

            print("✅ 响应数据转换成功！")
            print(f"   响应类型: {type(response)}")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_login_endpoint())
