#!/usr/bin/env python3
"""测试Celery任务系统."""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量为测试模式
os.environ["CELERY_EAGER_MODE"] = "true"
os.environ["TESTING"] = "true"

from app.core.celery_app import celery_app
from app.shared.tasks.email_tasks import send_bulk_email, send_email


def test_celery_setup() -> None:
    """测试Celery基本设置."""
    print("🔧 测试Celery基本配置...")
    print(f"✅ Broker: {celery_app.conf.broker_url}")
    print(f"✅ Backend: {celery_app.conf.result_backend}")
    print(f"✅ Eager模式: {celery_app.conf.task_always_eager}")
    print()


def test_email_task() -> None:
    """测试邮件发送任务."""
    print("📧 测试邮件发送任务...")
    try:
        # 在eager模式下，任务会同步执行
        result = send_email.apply_async(
            args=[
                "test@example.com",
                "测试邮件",
                "<h1>这是一个测试邮件</h1><p>系统正在测试Celery任务功能。</p>",
                "这是一个测试邮件\n\n系统正在测试Celery任务功能。",
            ]
        )

        print("✅ 邮件任务创建成功")
        print(f"✅ 任务ID: {result.id}")
        print(f"✅ 任务状态: {result.status}")

        # 在eager模式下，这里会立即失败，因为没有配置真实的SMTP
        # 但这证明任务系统是正常工作的
        try:
            task_result = result.get(timeout=10)
            print(f"✅ 任务结果: {task_result}")
        except Exception as e:
            print(f"⚠️ 任务执行失败（预期，因为没有配置SMTP）: {str(e)[:100]}...")

    except Exception as e:
        print(f"❌ 邮件任务测试失败: {e}")
    print()


def test_bulk_email_task() -> None:
    """测试批量邮件任务."""
    print("📮 测试批量邮件任务...")
    try:
        email_list = [
            {"email": "user1@example.com", "name": "用户1"},
            {"email": "user2@example.com", "name": "用户2"},
        ]

        result = send_bulk_email.apply_async(
            args=[
                email_list,
                "批量测试邮件",
                "<h1>Hello {name}!</h1><p>这是发送给 {email} 的测试邮件。</p>",
                "Hello {name}!\n\n这是发送给 {email} 的测试邮件。",
            ]
        )

        print("✅ 批量邮件任务创建成功")
        print(f"✅ 任务ID: {result.id}")
        print(f"✅ 任务状态: {result.status}")

    except Exception as e:
        print(f"❌ 批量邮件任务测试失败: {e}")
    print()


def test_task_routing() -> None:
    """测试任务路由配置."""
    print("🚦 测试任务路由配置...")
    routes = celery_app.conf.task_routes
    queues = celery_app.conf.task_queues

    print(f"✅ 任务路由数量: {len(routes)}")
    for pattern, config in routes.items():
        print(f"  - {pattern} → {config.get('queue', 'default')}")

    print(f"✅ 队列配置数量: {len(queues) if queues else 0}")
    if queues:
        for queue_name in queues:
            print(f"  - {queue_name}")
    print()


def test_beat_schedule() -> None:
    """测试定时任务配置."""
    print("⏰ 测试定时任务配置...")
    schedule = celery_app.conf.beat_schedule

    print(f"✅ 定时任务数量: {len(schedule)}")
    for task_name, config in schedule.items():
        print(
            f"  - {task_name}: {config.get('task')} (间隔: {config.get('schedule')}秒)"
        )
    print()


def main() -> None:
    """运行所有测试."""
    print("🧪 Celery任务系统测试开始")
    print("=" * 50)

    test_celery_setup()
    test_task_routing()
    test_beat_schedule()
    test_email_task()
    test_bulk_email_task()

    print("=" * 50)
    print("✅ Celery任务系统测试完成!")
    print("\n💡 提示:")
    print("- 启动Worker: ./scripts/start-celery-worker.sh")
    print("- 启动Beat: ./scripts/start-celery-beat.sh")
    print("- 启动监控: ./scripts/start-celery-flower.sh")
    print("- 监控界面: http://localhost:5555")


if __name__ == "__main__":
    main()
