"""审计日志器

提供结构化的安全审计日志记录功能，支持多种日志级别和输出格式。
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """审计事件类型"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    ADMIN_ACTION = "admin_action"
    SECURITY_EVENT = "security_event"
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    API_ERROR = "api_error"
    SYSTEM_EVENT = "system_event"


class AuditLevel(Enum):
    """审计级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """审计事件"""

    event_type: AuditEventType
    level: AuditLevel
    timestamp: float
    event_id: str
    user_id: str | None
    client_ip: str | None
    user_agent: str | None
    resource: str | None
    action: str | None
    result: str | None
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["level"] = self.level.value
        data["timestamp_iso"] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))


class AuditLogger:
    """审计日志器"""

    def __init__(
        self,
        log_file: str | None = None,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        enable_console: bool = True,
        enable_file: bool = True,
        log_level: str = "INFO",
    ) -> None:
        """初始化审计日志器

        Args:
            log_file: 日志文件路径
            max_file_size: 最大文件大小
            backup_count: 备份文件数量
            enable_console: 启用控制台输出
            enable_file: 启用文件输出
            log_level: 日志级别
        """
        self.log_file = log_file or "logs/audit.log"
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file

        # 创建日志目录
        if self.enable_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        # 设置日志器
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # 清除现有处理器
        self.logger.handlers.clear()

        # 添加文件处理器
        if self.enable_file:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # 添加控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                "%(asctime)s - AUDIT - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # 事件缓存
        self._event_cache: list[AuditEvent] = []
        self._cache_lock = asyncio.Lock()
        self._max_cache_size = 1000

    async def log_event(self, event: AuditEvent) -> None:
        """记录审计事件"""
        try:
            # 记录到日志文件
            log_message = event.to_json()

            if event.level == AuditLevel.CRITICAL:
                self.logger.critical(log_message)
            elif event.level == AuditLevel.ERROR:
                self.logger.error(log_message)
            elif event.level == AuditLevel.WARNING:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)

            # 添加到缓存
            async with self._cache_lock:
                self._event_cache.append(event)

                # 限制缓存大小
                if len(self._event_cache) > self._max_cache_size:
                    self._event_cache = self._event_cache[-self._max_cache_size :]

        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")

    async def log_authentication_event(self, data: dict[str, Any]) -> None:
        """记录认证事件"""
        event = AuditEvent(
            event_type=AuditEventType.AUTHENTICATION,
            level=AuditLevel.INFO,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("method"),
            result=data.get("result", "unknown"),
            details=data,
        )
        await self.log_event(event)

    async def log_authorization_event(self, data: dict[str, Any]) -> None:
        """记录授权事件"""
        event = AuditEvent(
            event_type=AuditEventType.AUTHORIZATION,
            level=AuditLevel.INFO,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("method"),
            result=data.get("result", "unknown"),
            details=data,
        )
        await self.log_event(event)

    async def log_data_access(self, data: dict[str, Any]) -> None:
        """记录数据访问事件"""
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            level=AuditLevel.INFO,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("access_type"),
            result="success",
            details=data,
        )
        await self.log_event(event)

    async def log_admin_action(self, data: dict[str, Any]) -> None:
        """记录管理员操作事件"""
        event = AuditEvent(
            event_type=AuditEventType.ADMIN_ACTION,
            level=AuditLevel.WARNING,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("method"),
            result="success",
            details=data,
        )
        await self.log_event(event)

    async def log_security_event(self, data: dict[str, Any]) -> None:
        """记录安全事件"""
        # 根据事件类型确定级别
        event_type = data.get("event_type", "unknown")
        if event_type in ["sql_injection", "xss_attack", "csrf_attack"]:
            level = AuditLevel.CRITICAL
        elif event_type in ["rate_limit_exceeded", "suspicious_activity"]:
            level = AuditLevel.WARNING
        else:
            level = AuditLevel.ERROR

        event = AuditEvent(
            event_type=AuditEventType.SECURITY_EVENT,
            level=level,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=event_type,
            result="blocked",
            details=data,
        )
        await self.log_event(event)

    async def log_api_request(self, data: dict[str, Any]) -> None:
        """记录API请求事件"""
        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            level=AuditLevel.INFO,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("method"),
            result="request",
            details=data,
        )
        await self.log_event(event)

    async def log_api_response(self, data: dict[str, Any]) -> None:
        """记录API响应事件"""
        # 根据状态码确定级别
        status_code = data.get("status_code", 200)
        if status_code >= 500:
            level = AuditLevel.ERROR
        elif status_code >= 400:
            level = AuditLevel.WARNING
        else:
            level = AuditLevel.INFO

        event = AuditEvent(
            event_type=AuditEventType.API_RESPONSE,
            level=level,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("method"),
            result=str(status_code),
            details=data,
        )
        await self.log_event(event)

    async def log_api_error(self, data: dict[str, Any]) -> None:
        """记录API错误事件"""
        event = AuditEvent(
            event_type=AuditEventType.API_ERROR,
            level=AuditLevel.ERROR,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("path"),
            action=data.get("method"),
            result="error",
            details=data,
        )
        await self.log_event(event)

    async def log_system_event(self, data: dict[str, Any]) -> None:
        """记录系统事件"""
        event = AuditEvent(
            event_type=AuditEventType.SYSTEM_EVENT,
            level=AuditLevel.INFO,
            timestamp=data.get("timestamp", time.time()),
            event_id=self._generate_event_id(),
            user_id=data.get("user_id"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            resource=data.get("resource"),
            action=data.get("action"),
            result=data.get("result", "success"),
            details=data,
        )
        await self.log_event(event)

    def _generate_event_id(self) -> str:
        """生成事件ID"""
        import uuid

        return str(uuid.uuid4())

    async def get_recent_events(
        self,
        limit: int = 100,
        event_type: AuditEventType | None = None,
        level: AuditLevel | None = None,
    ) -> list[AuditEvent]:
        """获取最近的审计事件"""
        async with self._cache_lock:
            events = self._event_cache.copy()

        # 过滤事件
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if level:
            events = [e for e in events if e.level == level]

        # 按时间倒序排列
        events.sort(key=lambda x: x.timestamp, reverse=True)

        return events[:limit]

    async def get_statistics(self) -> dict[str, Any]:
        """获取审计统计信息"""
        async with self._cache_lock:
            events = self._event_cache.copy()

        stats: dict[str, Any] = {
            "total_events": len(events),
            "by_type": {},
            "by_level": {},
            "recent_24h": 0,
        }

        current_time = time.time()
        day_ago = current_time - 86400  # 24小时前

        for event in events:
            # 按类型统计
            event_type = event.event_type.value
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

            # 按级别统计
            level = event.level.value
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

            # 24小时内事件
            if event.timestamp > day_ago:
                stats["recent_24h"] += 1

        return stats


# 全局审计日志器实例
audit_logger = AuditLogger()
