"""提醒工具类 - 智能学习提醒和通知管理."""

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class ReminderUtils:
    """提醒工具类 - 创建和管理各种学习提醒."""

    def __init__(self) -> None:
        """初始化提醒工具."""
        # 提醒类型配置
        self.reminder_types = {
            "study_reminder": {
                "name": "学习提醒",
                "default_message": "该学习了！保持学习习惯很重要。",
                "priority": "medium",
                "frequency": "daily",
            },
            "goal_deadline": {
                "name": "目标截止提醒",
                "default_message": "您的学习目标即将到期，请抓紧时间完成。",
                "priority": "high",
                "frequency": "once",
            },
            "performance_alert": {
                "name": "表现预警",
                "default_message": "最近的学习表现需要关注，建议调整学习策略。",
                "priority": "high",
                "frequency": "as_needed",
            },
            "consistency_reminder": {
                "name": "一致性提醒",
                "default_message": "保持规律的学习习惯有助于提高学习效果。",
                "priority": "medium",
                "frequency": "weekly",
            },
            "milestone_celebration": {
                "name": "里程碑庆祝",
                "default_message": "恭喜您达成学习里程碑！继续保持优秀表现。",
                "priority": "low",
                "frequency": "milestone",
            },
            "review_reminder": {
                "name": "复习提醒",
                "default_message": "是时候复习之前学过的内容了。",
                "priority": "medium",
                "frequency": "scheduled",
            },
            "break_reminder": {
                "name": "休息提醒",
                "default_message": "您已经学习了很长时间，建议适当休息。",
                "priority": "low",
                "frequency": "session_based",
            },
        }

        # 优先级配置
        self.priority_levels = {
            "low": {"score": 1, "urgency": "不紧急", "color": "green"},
            "medium": {"score": 2, "urgency": "一般", "color": "yellow"},
            "high": {"score": 3, "urgency": "紧急", "color": "red"},
            "critical": {"score": 4, "urgency": "非常紧急", "color": "red"},
        }

        # 发送渠道配置
        self.delivery_channels = {
            "in_app": {"name": "应用内通知", "enabled": True},
            "email": {"name": "邮件通知", "enabled": False},
            "sms": {"name": "短信通知", "enabled": False},
            "push": {"name": "推送通知", "enabled": True},
        }

    async def create_reminder(
        self,
        student_id: int,
        reminder_type: str,
        message: str | None = None,
        priority: str = "medium",
        scheduled_time: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建提醒."""
        try:
            # 验证提醒类型
            if reminder_type not in self.reminder_types:
                raise ValueError(f"无效的提醒类型: {reminder_type}")

            # 获取类型配置
            type_config = self.reminder_types[reminder_type]

            # 生成提醒ID
            reminder_id = self._generate_reminder_id(student_id, reminder_type)

            # 构建提醒数据
            reminder = {
                "reminder_id": reminder_id,
                "student_id": student_id,
                "reminder_type": reminder_type,
                "title": type_config["name"],
                "message": message or type_config["default_message"],
                "priority": priority,
                "priority_score": self.priority_levels[priority]["score"],
                "scheduled_time": scheduled_time or datetime.now(),
                "created_at": datetime.now(),
                "status": "pending",
                "delivery_channels": self._determine_delivery_channels(priority),
                "metadata": metadata or {},
            }

            # 保存提醒
            await self._save_reminder(reminder)

            # 如果是即时提醒，立即发送
            if scheduled_time is None or scheduled_time <= datetime.now():
                await self._send_reminder(reminder)

            logger.info(f"创建提醒: 学生{student_id}, 类型{reminder_type}, 优先级{priority}")
            return reminder

        except Exception as e:
            logger.error(f"创建提醒失败: {str(e)}")
            raise

    async def create_study_reminder(
        self, student_id: int, preferred_time: str = "evening"
    ) -> dict[str, Any]:
        """创建学习提醒."""
        # 根据偏好时间计算提醒时间
        reminder_time = self._calculate_study_reminder_time(preferred_time)

        # 个性化消息
        message = await self._generate_personalized_study_message(student_id)

        return await self.create_reminder(
            student_id=student_id,
            reminder_type="study_reminder",
            message=message,
            priority="medium",
            scheduled_time=reminder_time,
            metadata={"preferred_time": preferred_time},
        )

    async def create_goal_deadline_reminder(
        self, student_id: int, goal_id: int, goal_title: str, days_remaining: int
    ) -> dict[str, Any]:
        """创建目标截止提醒."""
        # 根据剩余天数确定优先级
        if days_remaining <= 1:
            priority = "critical"
        elif days_remaining <= 3:
            priority = "high"
        elif days_remaining <= 7:
            priority = "medium"
        else:
            priority = "low"

        # 生成消息
        message = f"您的目标「{goal_title}」还有{days_remaining}天到期，请抓紧时间完成。"

        return await self.create_reminder(
            student_id=student_id,
            reminder_type="goal_deadline",
            message=message,
            priority=priority,
            metadata={"goal_id": goal_id, "days_remaining": days_remaining},
        )

    async def create_performance_alert(
        self, student_id: int, performance_issue: str, suggestion: str
    ) -> dict[str, Any]:
        """创建表现预警."""
        message = f"学习表现提醒：{performance_issue}。建议：{suggestion}"

        return await self.create_reminder(
            student_id=student_id,
            reminder_type="performance_alert",
            message=message,
            priority="high",
            metadata={"issue": performance_issue, "suggestion": suggestion},
        )

    async def create_milestone_celebration(
        self, student_id: int, milestone_title: str, achievement: str
    ) -> dict[str, Any]:
        """创建里程碑庆祝提醒."""
        message = f"🎉 恭喜您达成里程碑「{milestone_title}」！{achievement}"

        return await self.create_reminder(
            student_id=student_id,
            reminder_type="milestone_celebration",
            message=message,
            priority="low",
            metadata={"milestone_title": milestone_title, "achievement": achievement},
        )

    async def create_review_reminder(
        self, student_id: int, review_content: str, review_type: str = "general"
    ) -> dict[str, Any]:
        """创建复习提醒."""
        message = f"复习时间到了！建议复习：{review_content}"

        # 计算复习时间（通常在学习时间前30分钟）
        review_time = await self._calculate_review_time(student_id)

        return await self.create_reminder(
            student_id=student_id,
            reminder_type="review_reminder",
            message=message,
            priority="medium",
            scheduled_time=review_time,
            metadata={"review_content": review_content, "review_type": review_type},
        )

    async def create_break_reminder(
        self, student_id: int, study_duration_minutes: int
    ) -> dict[str, Any]:
        """创建休息提醒."""
        if study_duration_minutes >= 90:
            message = "您已经连续学习了很长时间，建议休息15-20分钟，保护视力和大脑。"
            priority = "medium"
        elif study_duration_minutes >= 60:
            message = "学习1小时了，建议休息10分钟，喝点水，活动一下。"
            priority = "low"
        else:
            return {}  # 不需要休息提醒

        return await self.create_reminder(
            student_id=student_id,
            reminder_type="break_reminder",
            message=message,
            priority=priority,
            metadata={"study_duration": study_duration_minutes},
        )

    async def get_pending_reminders(self, student_id: int) -> list[dict[str, Any]]:
        """获取待处理的提醒."""
        try:
            # 从数据库获取待处理提醒
            reminders = await self._load_pending_reminders(student_id)

            # 按优先级和时间排序
            reminders.sort(
                key=lambda x: (x["priority_score"], x["scheduled_time"]), reverse=True
            )

            return reminders

        except Exception as e:
            logger.error(f"获取待处理提醒失败: {str(e)}")
            return []

    async def mark_reminder_as_read(self, reminder_id: str) -> bool:
        """标记提醒为已读."""
        try:
            await self._update_reminder_status(reminder_id, "read")
            logger.info(f"提醒已标记为已读: {reminder_id}")
            return True

        except Exception as e:
            logger.error(f"标记提醒已读失败: {str(e)}")
            return False

    async def dismiss_reminder(self, reminder_id: str) -> bool:
        """忽略提醒."""
        try:
            await self._update_reminder_status(reminder_id, "dismissed")
            logger.info(f"提醒已忽略: {reminder_id}")
            return True

        except Exception as e:
            logger.error(f"忽略提醒失败: {str(e)}")
            return False

    async def get_reminder_statistics(
        self, student_id: int, days: int = 30
    ) -> dict[str, Any]:
        """获取提醒统计."""
        try:
            # 获取指定时间内的提醒数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            reminders = await self._load_reminders_in_period(
                student_id, start_date, end_date
            )

            # 统计各类型提醒数量
            type_counts: dict[str, int] = {}
            for reminder in reminders:
                reminder_type = reminder["reminder_type"]
                type_counts[reminder_type] = type_counts.get(reminder_type, 0) + 1

            # 统计优先级分布
            priority_counts: dict[str, int] = {}
            for reminder in reminders:
                priority = reminder["priority"]
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            # 统计响应率
            total_reminders = len(reminders)
            read_reminders = len([r for r in reminders if r["status"] == "read"])
            response_rate = read_reminders / max(total_reminders, 1)

            return {
                "student_id": student_id,
                "period_days": days,
                "total_reminders": total_reminders,
                "type_distribution": type_counts,
                "priority_distribution": priority_counts,
                "response_rate": response_rate,
                "most_common_type": (
                    max(type_counts.items(), key=lambda x: x[1])[0]
                    if type_counts
                    else None
                ),
                "statistics_generated_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"获取提醒统计失败: {str(e)}")
            return {}

    # ==================== 私有方法 ====================

    def _generate_reminder_id(self, student_id: int, reminder_type: str) -> str:
        """生成提醒ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"reminder_{student_id}_{reminder_type}_{timestamp}"

    def _determine_delivery_channels(self, priority: str) -> list[str]:
        """确定发送渠道."""
        channels = ["in_app"]  # 默认应用内通知

        if priority in ["high", "critical"]:
            channels.append("push")  # 高优先级添加推送

        if priority == "critical":
            channels.append("email")  # 关键优先级添加邮件

        return channels

    async def _save_reminder(self, reminder: dict[str, Any]) -> None:
        """保存提醒到数据库."""
        # TODO: 实现数据库保存逻辑
        logger.info(f"保存提醒: {reminder['reminder_id']}")

    async def _send_reminder(self, reminder: dict[str, Any]) -> None:
        """发送提醒."""
        # TODO: 实现实际的提醒发送逻辑
        logger.info(
            f"发送提醒: {reminder['reminder_id']}, 渠道: {reminder['delivery_channels']}"
        )

    def _calculate_study_reminder_time(self, preferred_time: str) -> datetime:
        """计算学习提醒时间."""
        now = datetime.now()

        # 时间偏好映射
        time_mapping = {
            "morning": 8,  # 上午8点
            "afternoon": 14,  # 下午2点
            "evening": 19,  # 晚上7点
            "night": 21,  # 晚上9点
        }

        target_hour = time_mapping.get(preferred_time, 19)

        # 如果今天的时间已过，安排到明天
        target_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)

        return target_time

    async def _generate_personalized_study_message(self, student_id: int) -> str:
        """生成个性化学习消息."""
        # TODO: 基于学生数据生成个性化消息
        messages = [
            "今天的学习目标等着您呢！",
            "坚持学习，每天进步一点点！",
            "学习时间到了，让我们开始吧！",
            "保持学习习惯，成功就在前方！",
        ]

        # 简化处理，随机选择一条消息
        import random

        return random.choice(messages)

    async def _calculate_review_time(self, student_id: int) -> datetime:
        """计算复习时间."""
        # TODO: 基于学生的学习习惯计算最佳复习时间
        # 简化处理，设置为1小时后
        return datetime.now() + timedelta(hours=1)

    async def _load_pending_reminders(self, student_id: int) -> list[dict[str, Any]]:
        """加载待处理提醒."""
        # TODO: 实现从数据库加载提醒的逻辑
        return []

    async def _update_reminder_status(self, reminder_id: str, status: str) -> None:
        """更新提醒状态."""
        # TODO: 实现数据库更新逻辑
        logger.info(f"更新提醒状态: {reminder_id} -> {status}")

    async def _load_reminders_in_period(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """加载指定时期的提醒."""
        # TODO: 实现从数据库加载指定时期提醒的逻辑
        return []
