"""Celery配置参数."""

from typing import Any

from app.core.config import settings


class CeleryConfig:
    """Celery配置类."""

    # 任务序列化
    task_serializer = "json"
    accept_content = ["json"]
    result_serializer = "json"

    # 时区配置
    timezone = "Asia/Shanghai"
    enable_utc = True

    # 任务执行配置
    task_track_started = True
    task_time_limit = 30 * 60  # 30分钟任务超时
    task_soft_time_limit = 25 * 60  # 25分钟软超时
    task_acks_late = True
    task_reject_on_worker_lost = True

    # Worker配置
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False

    # 结果后端配置
    result_expires = 3600  # 结果保留1小时
    result_backend_transport_options = {
        "master_name": "mymaster",
    }

    # 任务路由配置
    task_routes: dict[str, dict[str, Any]] = {
        "app.ai.tasks.*": {"queue": "ai_queue"},
        "app.training.tasks.*": {"queue": "training_queue"},
        "app.shared.tasks.*": {"queue": "general_queue"},
    }

    # 队列配置
    task_default_queue = "general_queue"
    task_queues = {
        "ai_queue": {
            "exchange": "ai_queue",
            "routing_key": "ai_queue",
        },
        "training_queue": {
            "exchange": "training_queue",
            "routing_key": "training_queue",
        },
        "general_queue": {
            "exchange": "general_queue",
            "routing_key": "general_queue",
        },
    }

    # 监控配置
    task_send_sent_event = True
    worker_send_task_events = True

    # 重试配置
    task_annotations = {
        "*": {"rate_limit": "100/m"},
        "app.ai.tasks.*": {
            "rate_limit": "10/m",  # AI任务限制更严格
            "max_retries": 3,
            "default_retry_delay": 60,
        },
        "app.training.tasks.*": {
            "rate_limit": "50/m",
            "max_retries": 2,
        },
    }

    # 定时任务配置
    beat_schedule = {
        # 每日凌晨2点收集热点资源
        "collect-daily-hotspots": {
            "task": "collect_daily_hotspots",
            "schedule": 60.0 * 60.0 * 2,  # 每2小时执行一次（开发环境）
            # "schedule": crontab(hour=2, minute=0),  # 生产环境使用
        },
        # 每小时刷新热门状态
        "refresh-hotspot-trending": {
            "task": "refresh_hotspot_trending",
            "schedule": 60.0 * 60.0,  # 每小时执行一次
        },
        # 每日早上8点生成推荐
        "generate-daily-recommendations": {
            "task": "generate_daily_recommendations",
            "schedule": 60.0 * 60.0 * 8,  # 每8小时执行一次（开发环境）
            # "schedule": crontab(hour=8, minute=0),  # 生产环境使用
        },
        # 每周清理过期资源
        "cleanup-expired-hotspots": {
            "task": "cleanup_expired_hotspots",
            "schedule": 60.0 * 60.0 * 24 * 7,  # 每周执行一次
        },
    }

    # 安全配置
    worker_hijack_root_logger = False
    worker_log_color = False if settings.ENVIRONMENT == "production" else True

    @property
    def broker_url(self) -> str:
        """获取消息代理URL."""
        return str(settings.REDIS_URL)

    @property
    def result_backend(self) -> str:
        """获取结果后端URL."""
        return str(settings.REDIS_URL)
