"""共享任务模块."""

from .base_task import BaseTask
from .email_tasks import send_bulk_email, send_email

__all__ = [
    "BaseTask",
    "send_email",
    "send_bulk_email",
]
