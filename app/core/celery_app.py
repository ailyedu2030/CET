"""Celery应用配置和初始化."""

from celery import Celery

from app.core.config import settings

# 创建Celery实例
celery_app = Celery(
    "cet4_learning",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    include=[
        "app.shared.tasks.email_tasks",
        "app.ai.tasks",
        "app.training.tasks",
        "app.backup.tasks.backup_tasks",
    ],
)

# 配置任务设置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 结果过期时间1小时
    task_always_eager=settings.CELERY_EAGER_MODE,  # 测试环境同步执行
    task_eager_propagates=True,
    task_routes={
        "app.ai.tasks.*": {"queue": "ai_queue"},
        "app.training.tasks.*": {"queue": "training_queue"},
        "app.backup.tasks.*": {"queue": "backup_queue"},
        "app.shared.tasks.*": {"queue": "general_queue"},
    },
    task_default_queue="general_queue",
    task_queues={
        "ai_queue": {
            "exchange": "ai_queue",
            "routing_key": "ai_queue",
        },
        "training_queue": {
            "exchange": "training_queue",
            "routing_key": "training_queue",
        },
        "backup_queue": {
            "exchange": "backup_queue",
            "routing_key": "backup_queue",
        },
        "general_queue": {
            "exchange": "general_queue",
            "routing_key": "general_queue",
        },
    },
)

# 配置定时任务
celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "app.training.tasks.cleanup_expired_sessions",
        "schedule": 60.0 * 60,  # 每小时执行一次
    },
    "ai-service-health-check": {
        "task": "app.ai.tasks.health_check",
        "schedule": 60.0 * 5,  # 每5分钟检查一次
    },
    "update-user-statistics": {
        "task": "app.shared.tasks.update_user_statistics",
        "schedule": 60.0 * 30,  # 每30分钟更新一次
    },
    # 数据备份定时任务 - 需求9
    "daily-incremental-backup": {
        "task": "backup.daily_incremental",
        "schedule": 60.0 * 60 * 24,  # 每天执行一次
    },
    "weekly-full-backup": {
        "task": "backup.weekly_full",
        "schedule": 60.0 * 60 * 24 * 7,  # 每周执行一次
    },
    "cleanup-old-backups": {
        "task": "backup.cleanup_old_backups",
        "schedule": 60.0 * 60 * 24,  # 每天执行一次
    },
    "validate-backup-integrity": {
        "task": "backup.validate_backups",
        "schedule": 60.0 * 60 * 12,  # 每12小时执行一次
    },
    "execute-scheduled-backups": {
        "task": "backup.execute_scheduled",
        "schedule": 60.0 * 60,  # 每小时检查一次
    },
}
