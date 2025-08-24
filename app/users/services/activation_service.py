"""用户激活服务 - 🔥需求20验收标准5."""

import logging
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import EmailService
from app.shared.services.cache_service import CacheService
from app.users.models import User

logger = logging.getLogger(__name__)


class ActivationService:
    """用户激活服务 - 实现🔥需求20验收标准5."""

    def __init__(
        self, db: AsyncSession, cache_service: CacheService, email_service: EmailService
    ) -> None:
        self.db = db
        self.cache = cache_service
        self.email = email_service

    async def generate_activation_link(
        self,
        user_id: int,
        email: str,
        base_url: str = "http://localhost:5173",
    ) -> dict[str, Any]:
        """生成激活链接 - 🔥需求20验收标准5."""
        try:
            # 1. 生成激活令牌
            activation_token = self._generate_activation_token()

            # 2. 存储激活令牌到缓存（24小时有效期）
            token_key = f"activation_token:{activation_token}"
            token_data = {
                "user_id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
            }
            await self.cache.set(token_key, token_data, ttl=86400)  # 24小时

            # 3. 构建激活链接
            activation_link = f"{base_url}/activate/{activation_token}"

            logger.info(f"为用户 {user_id} 生成激活链接")

            return {
                "success": True,
                "activation_token": activation_token,
                "activation_link": activation_link,
                "expires_in": 86400,  # 24小时
            }

        except Exception as e:
            logger.error(f"生成激活链接失败: {str(e)}")
            return {
                "success": False,
                "error": "生成激活链接失败",
            }

    async def send_activation_email(
        self,
        user_id: int,
        email: str,
        username: str,
        base_url: str = "http://localhost:5173",
    ) -> dict[str, Any]:
        """发送激活邮件 - 🔥需求20验收标准5."""
        try:
            # 1. 生成激活链接
            link_result = await self.generate_activation_link(user_id, email, base_url)
            if not link_result["success"]:
                return link_result

            activation_link = link_result["activation_link"]

            # 2. 构建邮件内容
            subject = "英语四级学习系统 - 账号激活"
            html_content = self._build_activation_email_html(username, activation_link)
            text_content = self._build_activation_email_text(username, activation_link)

            # 3. 发送邮件
            email_result = await self.email.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

            if not email_result["success"]:
                return {
                    "success": False,
                    "error": "发送激活邮件失败",
                }

            # 4. 记录发送日志
            await self._log_activation_email_sent(user_id, email)

            logger.info(f"激活邮件发送成功: {email}")

            return {
                "success": True,
                "message": "激活邮件发送成功",
                "expires_in": 86400,  # 24小时
            }

        except Exception as e:
            logger.error(f"发送激活邮件失败: {str(e)}")
            return {
                "success": False,
                "error": "发送激活邮件失败",
            }

    async def activate_user(self, activation_token: str) -> dict[str, Any]:
        """激活用户账号 - 🔥需求20验收标准5."""
        try:
            # 1. 验证激活令牌
            token_key = f"activation_token:{activation_token}"
            token_data = await self.cache.get(token_key)

            if not token_data:
                return {
                    "success": False,
                    "error": "激活链接无效或已过期",
                }

            user_id = token_data["user_id"]
            email = token_data["email"]

            # 2. 获取用户信息
            stmt = select(User).where(User.id == user_id, User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return {
                    "success": False,
                    "error": "用户不存在",
                }

            if user.is_active and user.is_verified:
                return {
                    "success": False,
                    "error": "账号已激活",
                }

            # 3. 激活用户账号
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=True,
                    is_verified=True,
                    verified_at=datetime.utcnow(),
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()

            # 4. 删除激活令牌
            await self.cache.delete(token_key)

            # 5. 记录激活日志
            await self._log_user_activated(user_id, email)

            logger.info(f"用户激活成功: {user_id} ({email})")

            return {
                "success": True,
                "message": "账号激活成功",
                "user_id": user_id,
                "username": user.username,
            }

        except Exception as e:
            logger.error(f"激活用户失败: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": "激活失败，请稍后重试",
            }

    async def resend_activation_email(
        self,
        email: str,
        base_url: str = "http://localhost:5173",
    ) -> dict[str, Any]:
        """重发激活邮件 - 🔥需求20验收标准5."""
        try:
            # 1. 查找用户
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return {
                    "success": False,
                    "error": "邮箱地址不存在",
                }

            if user.is_active and user.is_verified:
                return {
                    "success": False,
                    "error": "账号已激活",
                }

            # 2. 检查重发频率限制
            rate_limit_key = f"activation_email_rate_limit:{email}"
            last_send_time = await self.cache.get(rate_limit_key)

            if last_send_time:
                return {
                    "success": False,
                    "error": "发送过于频繁，请稍后重试",
                }

            # 3. 发送激活邮件
            email_result = await self.send_activation_email(user.id, email, user.username, base_url)

            if email_result["success"]:
                # 4. 设置重发频率限制（5分钟）
                await self.cache.set(rate_limit_key, "sent", ttl=300)

            return email_result

        except Exception as e:
            logger.error(f"重发激活邮件失败: {str(e)}")
            return {
                "success": False,
                "error": "重发激活邮件失败",
            }

    def _generate_activation_token(self, length: int = 32) -> str:
        """生成激活令牌."""
        return secrets.token_urlsafe(length)

    def _build_activation_email_html(self, username: str, activation_link: str) -> str:
        """构建激活邮件HTML内容."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>账号激活</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">英语四级学习系统 - 账号激活</h2>

                <p>亲爱的 {username}，</p>

                <p>恭喜您！您的注册申请已通过审核。请点击下方链接激活您的账号：</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{activation_link}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        激活账号
                    </a>
                </div>

                <p>或者复制以下链接到浏览器地址栏：</p>
                <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
                    {activation_link}
                </p>

                <p><strong>重要提醒：</strong></p>
                <ul>
                    <li>此激活链接有效期为24小时</li>
                    <li>激活后即可登录系统开始学习</li>
                    <li>如链接过期，可在登录页面申请重发</li>
                </ul>

                <p>如有任何问题，请联系系统管理员。</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px;">
                    此邮件由系统自动发送，请勿回复。<br>
                    英语四级学习系统
                </p>
            </div>
        </body>
        </html>
        """

    def _build_activation_email_text(self, username: str, activation_link: str) -> str:
        """构建激活邮件文本内容."""
        return f"""
英语四级学习系统 - 账号激活

亲爱的 {username}，

恭喜您！您的注册申请已通过审核。请访问以下链接激活您的账号：

{activation_link}

重要提醒：
- 此激活链接有效期为24小时
- 激活后即可登录系统开始学习
- 如链接过期，可在登录页面申请重发

如有任何问题，请联系系统管理员。

此邮件由系统自动发送，请勿回复。
英语四级学习系统
        """

    async def _log_activation_email_sent(self, user_id: int, email: str) -> None:
        """记录激活邮件发送日志."""
        try:
            log_key = f"activation_email_log:{user_id}:{int(datetime.utcnow().timestamp())}"
            log_data = {
                "user_id": user_id,
                "email": email,
                "action": "email_sent",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.cache.set(log_key, log_data, ttl=604800)  # 7天
        except Exception as e:
            logger.error(f"记录激活邮件日志失败: {str(e)}")

    async def _log_user_activated(self, user_id: int, email: str) -> None:
        """记录用户激活日志."""
        try:
            log_key = f"activation_log:{user_id}:{int(datetime.utcnow().timestamp())}"
            log_data = {
                "user_id": user_id,
                "email": email,
                "action": "user_activated",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.cache.set(log_key, log_data, ttl=604800)  # 7天
        except Exception as e:
            logger.error(f"记录用户激活日志失败: {str(e)}")
