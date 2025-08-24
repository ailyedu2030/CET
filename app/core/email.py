"""邮件服务 - 🔥需求20验收标准5."""

import logging
from typing import Any

from app.shared.tasks.email_tasks import send_email

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类 - 实现🔥需求20验收标准5."""

    def __init__(self) -> None:
        """初始化邮件服务."""
        pass

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> dict[str, Any]:
        """发送邮件."""
        try:
            # 使用Celery任务发送邮件
            result = send_email.apply_async(args=[to_email, subject, html_content, text_content])

            # 在开发环境中等待结果，生产环境中应该异步处理
            try:
                task_result = result.get(timeout=30)
                return {
                    "success": True,
                    "message": "邮件发送成功",
                    "result": task_result,
                }
            except Exception as e:
                logger.error(f"邮件发送失败: {str(e)}")
                return {
                    "success": False,
                    "error": "邮件发送失败",
                }

        except Exception as e:
            logger.error(f"邮件服务错误: {str(e)}")
            return {
                "success": False,
                "error": "邮件服务错误",
            }


# 全局邮件服务实例
email_service = EmailService()


def get_email_service() -> EmailService:
    """获取邮件服务实例."""
    return email_service
