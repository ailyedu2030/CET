"""邮件发送相关任务."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.config import settings

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="send_email")  # type: ignore[misc]
def send_email(
    self: Any,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> dict[str, Any]:
    """发送单个邮件任务."""
    try:
        # 创建邮件对象
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email

        # 添加文本内容
        if text_content:
            text_part = MIMEText(text_content, "plain", "utf-8")
            msg.attach(text_part)

        # 添加HTML内容
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # 发送邮件
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()
            if settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD:
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)

            server.send_message(msg)

        logger.info(f"邮件发送成功: {to_email}")
        return {
            "status": "success",
            "to_email": to_email,
            "subject": subject,
        }

    except Exception as exc:
        logger.error(f"邮件发送失败: {to_email}, 错误: {str(exc)}")
        # 重试机制会自动触发
        raise


@celery_app.task(bind=True, name="send_bulk_email")  # type: ignore[misc]
def send_bulk_email(
    self: Any,
    email_list: list[dict[str, str]],
    subject: str,
    html_template: str,
    text_template: str | None = None,
) -> dict[str, Any]:
    """批量发送邮件任务.

    Args:
        email_list: 邮件列表，格式为 [{"email": "user@example.com", "name": "User Name", **context}]
        subject: 邮件主题
        html_template: HTML邮件模板
        text_template: 文本邮件模板（可选）
    """
    success_count = 0
    failed_count = 0
    failed_emails = []

    for email_data in email_list:
        try:
            to_email = email_data["email"]

            # 渲染邮件内容（简单的字符串替换，实际项目中应使用模板引擎）
            html_content = html_template
            text_content = text_template

            for key, value in email_data.items():
                placeholder = f"{{{key}}}"
                html_content = html_content.replace(placeholder, str(value))
                if text_content:
                    text_content = text_content.replace(placeholder, str(value))

            # 发送单个邮件
            result = send_email.apply_async(
                args=[to_email, subject, html_content, text_content],
                retry=False,  # 批量发送中不重试单个邮件
            )

            # 等待结果（短时间）
            try:
                result.get(timeout=30)
                success_count += 1
            except Exception as e:
                failed_count += 1
                failed_emails.append({"email": to_email, "error": str(e)})

        except Exception as e:
            failed_count += 1
            failed_emails.append({"email": email_data.get("email", "unknown"), "error": str(e)})

    bulk_result: dict[str, Any] = {
        "status": "completed",
        "total": len(email_list),
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_emails": failed_emails,
    }

    if failed_count > 0:
        logger.warning(f"批量邮件发送部分失败: {failed_count}/{len(email_list)}")
    else:
        logger.info(f"批量邮件发送全部成功: {success_count}")

    return bulk_result


@celery_app.task(bind=True, name="send_notification_email")  # type: ignore[misc]
def send_notification_email(
    self: Any,
    user_id: int,
    notification_type: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """发送通知邮件任务.

    Args:
        user_id: 用户ID
        notification_type: 通知类型
        context: 邮件上下文数据
    """
    try:
        # 这里应该从数据库获取用户信息和邮件模板
        # 为了简化，现在使用硬编码

        email_templates = {
            "registration_approved": {
                "subject": "注册申请已通过",
                "html": "<h1>恭喜！</h1><p>您的注册申请已通过审核，现在可以登录系统了。</p>",
                "text": "恭喜！您的注册申请已通过审核，现在可以登录系统了。",
            },
            "registration_rejected": {
                "subject": "注册申请被拒绝",
                "html": "<h1>很抱歉</h1><p>您的注册申请未通过审核。拒绝原因：{reason}</p>",
                "text": "很抱歉，您的注册申请未通过审核。拒绝原因：{reason}",
            },
            "password_reset": {
                "subject": "密码重置请求",
                "html": "<h1>密码重置</h1><p>请点击以下链接重置密码：<a href='{reset_link}'>重置密码</a></p>",
                "text": "请访问以下链接重置密码：{reset_link}",
            },
        }

        template = email_templates.get(notification_type)
        if not template:
            raise ValueError(f"未知的通知类型: {notification_type}")

        # 这里应该从数据库获取用户邮箱
        user_email = context.get("user_email", "user@example.com")

        # 渲染模板
        subject = template["subject"]
        html_content = template["html"]
        text_content = template["text"]

        for key, value in context.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))

        # 发送邮件
        result = send_email.apply_async(
            args=[user_email, subject, html_content, text_content]
        ).get()

        # 确保返回正确的类型
        if isinstance(result, dict):
            return result
        else:
            return {"status": "error", "message": "Unexpected result type"}

    except Exception as exc:
        logger.error(
            f"通知邮件发送失败: user_id={user_id}, type={notification_type}, 错误: {str(exc)}"
        )
        raise
