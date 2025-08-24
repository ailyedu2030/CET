"""基础任务类定义."""

import traceback
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app

logger = get_task_logger(__name__)


class BaseTask(Task):  # type: ignore[misc]
    """基础任务类 - 提供错误处理和重试机制."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600  # 最大退避时间10分钟
    retry_jitter = True

    def on_success(
        self, retval: Any, task_id: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> None:
        """任务成功完成时的回调."""
        logger.info(
            f"Task {self.name} succeeded",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "result": str(retval)[:200],  # 限制日志长度
            },
        )

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """任务失败时的回调."""
        logger.error(
            f"Task {self.name} failed: {str(exc)}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "traceback": traceback.format_exc(),
            },
        )

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """任务重试时的回调."""
        logger.warning(
            f"Task {self.name} retrying: {str(exc)}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "retry_count": self.request.retries,
            },
        )

    def apply_async(
        self,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
        **options: Any,
    ) -> Any:
        """重写apply_async以添加默认选项."""
        # 设置默认的任务选项
        default_options = {
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 0.2,
                "interval_max": 0.2,
            },
        }
        default_options.update(options)

        return super().apply_async(args, kwargs, **default_options)


# 设置Celery应用的基础任务类
celery_app.Task = BaseTask
