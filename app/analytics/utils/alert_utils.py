"""告警系统工具类."""

import asyncio
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiohttp

from app.analytics.schemas.analytics_schemas import AlertLevel, AlertRecord, AlertRule
from app.core.config import settings


class AlertManager:
    """告警管理器类."""

    def __init__(self) -> None:
        """初始化告警管理器."""
        self.rules: list[AlertRule] = []
        self.active_alerts: dict[str, AlertRecord] = {}
        self.notification_channels: dict[str, Any] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则."""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """移除告警规则."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                return True
        return False

    def evaluate_rules(self, metrics: dict[str, float]) -> list[AlertRecord]:
        """评估告警规则."""
        new_alerts = []
        current_time = datetime.utcnow()

        for rule in self.rules:
            if not rule.enabled:
                continue

            metric_value = metrics.get(rule.metric_name)
            if metric_value is None:
                continue

            # 评估条件
            triggered = self._evaluate_condition(metric_value, rule.condition, rule.threshold)

            alert_id = f"{rule.name}_{rule.metric_name}"

            if triggered:
                # 检查是否已存在相同告警
                if alert_id not in self.active_alerts:
                    alert = AlertRecord(
                        id=alert_id,
                        rule_name=rule.name,
                        level=rule.level,
                        message=f"{rule.metric_name} {rule.condition} {rule.threshold} (当前值: {metric_value})",
                        metric_value=metric_value,
                        threshold=rule.threshold,
                        triggered_at=current_time,
                        status="active",
                        resolved_at=None,
                        acknowledgment=None,
                    )

                    self.active_alerts[alert_id] = alert
                    new_alerts.append(alert)
            else:
                # 如果条件不满足，解决已存在的告警
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]
                    alert.status = "resolved"
                    alert.resolved_at = current_time
                    del self.active_alerts[alert_id]

        return new_alerts

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估告警条件."""
        condition_map = {
            ">": value > threshold,
            ">=": value >= threshold,
            "<": value < threshold,
            "<=": value <= threshold,
            "==": value == threshold,
            "!=": value != threshold,
        }

        return condition_map.get(condition, False)

    def get_active_alerts(self, level: AlertLevel | None = None) -> list[AlertRecord]:
        """获取活跃告警."""
        alerts = list(self.active_alerts.values())

        if level:
            alerts = [alert for alert in alerts if alert.level == level]

        return sorted(alerts, key=lambda x: x.triggered_at, reverse=True)

    def acknowledge_alert(self, alert_id: str, user_id: int, comment: str = "") -> bool:
        """确认告警."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledgment = {
                "user_id": user_id,
                "comment": comment,
                "acknowledged_at": datetime.utcnow().isoformat(),
            }
            return True
        return False

    def suppress_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """抑制告警."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = "suppressed"
            # 这里可以添加定时器逻辑，在指定时间后重新激活
            return True
        return False


class NotificationChannel:
    """通知渠道基类."""

    async def send_notification(self, alert: AlertRecord, recipients: list[str]) -> bool:
        """发送通知."""
        raise NotImplementedError


class EmailNotifier(NotificationChannel):
    """邮件通知器."""

    def __init__(self) -> None:
        """初始化邮件通知器."""
        self.smtp_host = settings.EMAIL_HOST
        self.smtp_port = settings.EMAIL_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_FROM

    async def send_notification(self, alert: AlertRecord, recipients: list[str]) -> bool:
        """发送邮件通知."""
        try:
            # 创建邮件内容
            subject = f"[{alert.level.value.upper()}] {alert.rule_name} 告警"
            body = self._create_email_body(alert)

            # 异步发送邮件
            await self._send_email_async(subject, body, recipients)
            return True
        except Exception as e:
            print(f"发送邮件告警失败: {e}")
            return False

    def _create_email_body(self, alert: AlertRecord) -> str:
        """创建邮件正文."""
        return f"""
        告警详情：

        规则名称：{alert.rule_name}
        告警级别：{alert.level.value.upper()}
        告警消息：{alert.message}

        指标值：{alert.metric_value}
        阈值：{alert.threshold}
        触发时间：{alert.triggered_at}

        请及时处理此告警。

        ----
        英语四级学习系统监控
        """

    async def _send_email_async(self, subject: str, body: str, recipients: list[str]) -> None:
        """异步发送邮件."""
        loop = asyncio.get_event_loop()

        def send_email() -> None:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            # 添加正文
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

        await loop.run_in_executor(None, send_email)


class WebhookNotifier(NotificationChannel):
    """Webhook通知器."""

    def __init__(self, webhook_url: str) -> None:
        """初始化Webhook通知器."""
        self.webhook_url = webhook_url

    async def send_notification(self, alert: AlertRecord, recipients: list[str]) -> bool:
        """发送Webhook通知."""
        try:
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "level": alert.level.value,
                "message": alert.message,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "triggered_at": alert.triggered_at.isoformat(),
                "recipients": recipients,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success: bool = response.status == 200
                    return success

        except Exception as e:
            print(f"发送Webhook告警失败: {e}")
            return False


class SlackNotifier(NotificationChannel):
    """Slack通知器."""

    def __init__(self, webhook_url: str) -> None:
        """初始化Slack通知器."""
        self.webhook_url = webhook_url

    async def send_notification(self, alert: AlertRecord, recipients: list[str]) -> bool:
        """发送Slack通知."""
        try:
            # 根据告警级别设置颜色
            color_map = {
                AlertLevel.INFO: "#36a64f",  # green
                AlertLevel.WARNING: "#ff9500",  # orange
                AlertLevel.ERROR: "#ff0000",  # red
                AlertLevel.CRITICAL: "#8B0000",  # dark red
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.level, "#36a64f"),
                        "title": f"🚨 {alert.rule_name} 告警",
                        "fields": [
                            {
                                "title": "级别",
                                "value": alert.level.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "指标值",
                                "value": f"{alert.metric_value}",
                                "short": True,
                            },
                            {
                                "title": "阈值",
                                "value": f"{alert.threshold}",
                                "short": True,
                            },
                            {
                                "title": "触发时间",
                                "value": alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True,
                            },
                            {"title": "消息", "value": alert.message, "short": False},
                        ],
                        "footer": "英语四级学习系统监控",
                        "ts": int(alert.triggered_at.timestamp()),
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success: bool = response.status == 200
                    return success

        except Exception as e:
            print(f"发送Slack告警失败: {e}")
            return False


class AlertAggregator:
    """告警聚合器."""

    def __init__(self, aggregation_window: int = 300) -> None:
        """初始化告警聚合器."""
        self.aggregation_window = aggregation_window  # 聚合时间窗口（秒）
        self.alert_buffer: list[AlertRecord] = []

    def add_alert(self, alert: AlertRecord) -> None:
        """添加告警到聚合缓冲区."""
        self.alert_buffer.append(alert)

    def get_aggregated_alerts(self) -> dict[str, Any]:
        """获取聚合后的告警信息."""
        if not self.alert_buffer:
            return {}

        # 按级别分组
        level_counts: dict[str, int] = {}
        for alert in self.alert_buffer:
            level = alert.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        # 按规则分组
        rule_counts: dict[str, int] = {}
        for alert in self.alert_buffer:
            rule = alert.rule_name
            rule_counts[rule] = rule_counts.get(rule, 0) + 1

        # 获取最新和最旧的告警时间
        timestamps = [alert.triggered_at for alert in self.alert_buffer]
        oldest = min(timestamps)
        latest = max(timestamps)

        aggregated = {
            "total_alerts": len(self.alert_buffer),
            "level_distribution": level_counts,
            "rule_distribution": rule_counts,
            "time_range": {
                "oldest": oldest.isoformat(),
                "latest": latest.isoformat(),
                "duration_seconds": (latest - oldest).total_seconds(),
            },
            "critical_alerts": [
                alert for alert in self.alert_buffer if alert.level == AlertLevel.CRITICAL
            ],
        }

        return aggregated

    def clear_buffer(self) -> None:
        """清空聚合缓冲区."""
        self.alert_buffer.clear()


class MetricThresholdCalculator:
    """指标阈值计算器."""

    @staticmethod
    def calculate_dynamic_threshold(
        historical_data: list[float], multiplier: float = 2.0, method: str = "std"
    ) -> dict[str, float]:
        """计算动态阈值."""
        if not historical_data:
            return {"upper": 100.0, "lower": 0.0}

        import numpy as np

        data = np.array(historical_data)
        mean = np.mean(data)

        if method == "std":
            std = np.std(data)
            upper_threshold = mean + (multiplier * std)
            lower_threshold = max(0, mean - (multiplier * std))
        elif method == "percentile":
            upper_threshold = np.percentile(data, 95)
            lower_threshold = np.percentile(data, 5)
        else:  # iqr method
            q75, q25 = np.percentile(data, [75, 25])
            iqr = q75 - q25
            upper_threshold = q75 + (multiplier * iqr)
            lower_threshold = max(0, q25 - (multiplier * iqr))

        return {
            "upper": float(upper_threshold),
            "lower": float(lower_threshold),
            "mean": float(mean),
        }

    @staticmethod
    def detect_anomalies(
        current_value: float, historical_data: list[float], sensitivity: float = 2.0
    ) -> dict[str, Any]:
        """检测异常值."""
        if len(historical_data) < 10:  # 需要足够的历史数据
            return {"is_anomaly": False, "confidence": 0.0}

        import numpy as np

        data = np.array(historical_data)
        mean = np.mean(data)
        std = np.std(data)

        # 计算Z-score
        z_score = abs((current_value - mean) / std) if std > 0 else 0

        # 判断是否为异常
        is_anomaly = z_score > sensitivity
        confidence = min(z_score / sensitivity, 1.0) if sensitivity > 0 else 0.0

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "z_score": float(z_score),
            "threshold": sensitivity,
            "deviation_from_mean": float(current_value - mean),
        }


# 全局告警管理器实例
alert_manager = AlertManager()

# 预定义告警规则
DEFAULT_ALERT_RULES = [
    AlertRule(
        name="高CPU使用率",
        metric_name="cpu_usage",
        condition=">",
        threshold=80.0,
        level=AlertLevel.WARNING,
        notification_channels=["email"],
    ),
    AlertRule(
        name="内存使用率过高",
        metric_name="memory_usage",
        condition=">",
        threshold=85.0,
        level=AlertLevel.ERROR,
        notification_channels=["email", "slack"],
    ),
    AlertRule(
        name="磁盘空间不足",
        metric_name="disk_usage",
        condition=">",
        threshold=90.0,
        level=AlertLevel.CRITICAL,
        notification_channels=["email", "slack", "webhook"],
    ),
    AlertRule(
        name="数据库连接数过高",
        metric_name="db_connections",
        condition=">",
        threshold=50.0,
        level=AlertLevel.WARNING,
        notification_channels=["email"],
    ),
    AlertRule(
        name="API响应时间过长",
        metric_name="api_response_time",
        condition=">",
        threshold=2000.0,  # 2秒
        level=AlertLevel.ERROR,
        notification_channels=["email", "slack"],
    ),
]

# 初始化默认规则
for rule in DEFAULT_ALERT_RULES:
    alert_manager.add_rule(rule)
