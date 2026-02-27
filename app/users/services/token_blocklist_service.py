"""Token blocklist service - 用于JWT令牌黑名单管理."""

import redis.asyncio as redis
from typing import Optional

from app.core.config import settings


class TokenBlocklistService:
    """Token blocklist service using Redis."""

    def __init__(self) -> None:
        """初始化token blocklist service."""
        self._redis_client: Optional[redis.Redis] = None

    @property
    def redis_client(self) -> redis.Redis:
        """获取Redis客户端（延迟初始化）."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis_client

    def _get_blocklist_key(self, jti: str) -> str:
        """获取blocklist key."""
        return f"token_blocklist:{jti}"

    async def add_to_blocklist(self, jti: str, expires_in: int) -> None:
        """将token JTI加入黑名单.

        Args:
            jti: JWT ID
            expires_in: 过期时间（秒）
        """
        key = self._get_blocklist_key(jti)
        await self.redis_client.setex(key, expires_in, "blocked")

    async def is_blocked(self, jti: str) -> bool:
        """检查token JTI是否在黑名单中.

        Args:
            jti: JWT ID

        Returns:
            True if blocked, False otherwise
        """
        key = self._get_blocklist_key(jti)
        return await self.redis_client.exists(key) > 0

    async def remove_from_blocklist(self, jti: str) -> None:
        """从黑名单中移除token JTI.

        Args:
            jti: JWT ID
        """
        key = self._get_blocklist_key(jti)
        await self.redis_client.delete(key)

    async def close(self) -> None:
        """关闭Redis连接."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None


# 全局单例
token_blocklist_service = TokenBlocklistService()
