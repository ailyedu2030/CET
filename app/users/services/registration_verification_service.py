"""注册验证码服务 - 🔥需求20验收标准3."""

import logging
import random
import string
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RegistrationVerificationService:
    """注册验证码服务 - 实现🔥需求20验收标准3."""

    def __init__(self, db: AsyncSession | None, cache_service: CacheService) -> None:
        self.db = db
        self.cache = cache_service

    async def send_sms_verification_code(
        self,
        phone_number: str,
        purpose: str = "register",
    ) -> dict[str, Any]:
        """发送注册短信验证码 - 🔥需求20验收标准3."""
        try:
            # 1. 检查发送频率限制（60秒内重发限制）
            rate_limit_key = f"sms_rate_limit:{phone_number}"
            last_send_time = await self.cache.get(rate_limit_key)

            current_time = int(time.time())
            if last_send_time:
                time_diff = current_time - int(last_send_time)
                if time_diff < 60:  # 60秒限制
                    remaining_time = 60 - time_diff
                    return {
                        "success": False,
                        "error": f"发送过于频繁，请{remaining_time}秒后重试",
                    }

            # 2. 检查每日发送次数限制
            daily_count_key = f"sms_daily_count:{phone_number}:{current_time // 86400}"
            daily_count = await self.cache.get(daily_count_key) or 0
            if int(daily_count) >= 10:  # 每日最多10次
                return {
                    "success": False,
                    "error": "今日发送次数已达上限，请明日再试",
                }

            # 3. 生成6位数字验证码
            verification_code = self._generate_verification_code()

            # 4. 存储验证码到缓存（5分钟有效期）
            code_key = f"sms_code:{phone_number}:{purpose}"
            await self.cache.set(code_key, verification_code, ttl=300)  # 5分钟

            # 5. 存储验证码尝试次数
            attempts_key = f"sms_attempts:{phone_number}:{purpose}"
            await self.cache.set(attempts_key, 0, ttl=300)  # 5分钟

            # 6. 更新发送频率限制
            await self.cache.set(rate_limit_key, current_time, ttl=60)  # 60秒

            # 7. 更新每日发送次数
            await self.cache.set(daily_count_key, int(daily_count) + 1, ttl=86400)  # 24小时

            # 8. 这里应该调用实际的短信服务API
            # 目前使用模拟实现
            logger.info(f"发送注册短信验证码到 {phone_number}: {verification_code}")

            # 9. 生成掩码手机号
            masked_phone = self._mask_phone_number(phone_number)

            return {
                "success": True,
                "message": "验证码发送成功",
                "expires_in": 300,  # 5分钟
                "masked_target": masked_phone,
            }

        except Exception as e:
            logger.error(f"发送注册短信验证码失败: {str(e)}")
            return {
                "success": False,
                "error": "发送失败，请稍后重试",
            }

    async def verify_sms_code(
        self,
        phone_number: str,
        verification_code: str,
        purpose: str = "register",
    ) -> dict[str, Any]:
        """验证注册短信验证码 - 🔥需求20验收标准3."""
        try:
            # 1. 获取存储的验证码
            code_key = f"sms_code:{phone_number}:{purpose}"
            stored_code = await self.cache.get(code_key)

            if not stored_code:
                return {
                    "success": False,
                    "error": "验证码已过期或不存在",
                }

            # 2. 检查验证尝试次数
            attempts_key = f"sms_attempts:{phone_number}:{purpose}"
            attempts = await self.cache.get(attempts_key) or 0
            attempts = int(attempts)

            if attempts >= 3:  # 最多3次尝试
                # 删除验证码
                await self.cache.delete(code_key)
                await self.cache.delete(attempts_key)
                return {
                    "success": False,
                    "error": "验证次数过多，请重新获取验证码",
                }

            # 3. 验证验证码
            if verification_code != stored_code:
                # 增加尝试次数
                await self.cache.set(attempts_key, attempts + 1, ttl=300)
                remaining_attempts = 2 - attempts
                return {
                    "success": False,
                    "error": "验证码错误",
                    "remaining_attempts": remaining_attempts,
                }

            # 4. 验证成功，清理缓存
            await self.cache.delete(code_key)
            await self.cache.delete(attempts_key)

            # 5. 标记手机号已验证（用于注册流程）
            verified_key = f"phone_verified:{phone_number}"
            await self.cache.set(verified_key, "true", ttl=1800)  # 30分钟有效

            logger.info(f"注册短信验证码验证成功: {phone_number}")

            return {
                "success": True,
                "message": "验证成功",
                "verified_user_id": None,  # 注册流程中还没有用户ID
            }

        except Exception as e:
            logger.error(f"验证注册短信验证码失败: {str(e)}")
            return {
                "success": False,
                "error": "验证失败，请稍后重试",
            }

    async def is_phone_verified(self, phone_number: str) -> bool:
        """检查手机号是否已验证."""
        try:
            verified_key = f"phone_verified:{phone_number}"
            result = await self.cache.get(verified_key)
            return result == "true"
        except Exception:
            return False

    async def get_verification_status(self, phone_number: str) -> dict[str, Any]:
        """获取验证码发送状态."""
        try:
            # 检查发送频率限制
            rate_limit_key = f"sms_rate_limit:{phone_number}"
            last_send_time = await self.cache.get(rate_limit_key)

            current_time = int(time.time())
            can_send = True
            next_send_time = None

            if last_send_time:
                time_diff = current_time - int(last_send_time)
                if time_diff < 60:
                    can_send = False
                    next_send_time = current_time + (60 - time_diff)

            # 检查每日发送次数
            daily_count_key = f"sms_daily_count:{phone_number}:{current_time // 86400}"
            daily_count = await self.cache.get(daily_count_key) or 0
            remaining_attempts = max(0, 10 - int(daily_count))

            if remaining_attempts == 0:
                can_send = False

            return {
                "can_send": can_send,
                "next_send_time": next_send_time,
                "remaining_attempts": remaining_attempts,
            }

        except Exception as e:
            logger.error(f"获取验证状态失败: {str(e)}")
            return {
                "can_send": True,
                "next_send_time": None,
                "remaining_attempts": 10,
            }

    def _generate_verification_code(self, length: int = 6) -> str:
        """生成数字验证码."""
        return "".join(random.choices(string.digits, k=length))

    def _mask_phone_number(self, phone_number: str) -> str:
        """生成掩码手机号."""
        if len(phone_number) == 11:
            return f"{phone_number[:3]}****{phone_number[-4:]}"
        return phone_number
