"""WebSocket连接管理器 - 需求16实时通知功能."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from app.notifications.schemas.notification_schemas import (
    NotificationResponse,
    WebSocketConnectionInfo,
    WebSocketNotificationMessage,
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """WebSocket连接管理器 - 实时通知核心."""

    def __init__(self) -> None:
        """初始化连接管理器."""
        # 活跃连接: user_id -> Set[WebSocket]
        self.active_connections: dict[int, set[WebSocket]] = {}
        # 连接信息: connection_id -> ConnectionInfo
        self.connection_info: dict[str, WebSocketConnectionInfo] = {}
        # 心跳任务
        self.heartbeat_tasks: dict[str, asyncio.Task[None]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: str,
    ) -> bool:
        """建立WebSocket连接."""
        try:
            await websocket.accept()

            # 添加到活跃连接
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)

            # 记录连接信息
            self.connection_info[connection_id] = WebSocketConnectionInfo(
                user_id=user_id,
                connection_id=connection_id,
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
            )

            # 启动心跳检测
            self.heartbeat_tasks[connection_id] = asyncio.create_task(
                self._heartbeat_monitor(websocket, connection_id)
            )

            logger.info(f"用户 {user_id} WebSocket连接建立: {connection_id}")

            # 发送连接确认消息
            await self._send_to_connection(
                websocket,
                {
                    "type": "connection_established",
                    "connection_id": connection_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return True

        except Exception as e:
            logger.error(f"WebSocket连接失败: {str(e)}")
            return False

    async def disconnect(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: str,
    ) -> None:
        """断开WebSocket连接."""
        try:
            # 从活跃连接中移除
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # 清理连接信息
            if connection_id in self.connection_info:
                del self.connection_info[connection_id]

            # 取消心跳任务
            if connection_id in self.heartbeat_tasks:
                self.heartbeat_tasks[connection_id].cancel()
                del self.heartbeat_tasks[connection_id]

            logger.info(f"用户 {user_id} WebSocket连接断开: {connection_id}")

        except Exception as e:
            logger.error(f"WebSocket断开处理失败: {str(e)}")

    async def send_notification_to_user(
        self,
        user_id: int,
        notification: NotificationResponse,
    ) -> bool:
        """向指定用户发送实时通知."""
        if user_id not in self.active_connections:
            logger.debug(f"用户 {user_id} 没有活跃的WebSocket连接")
            return False

        message = WebSocketNotificationMessage(
            type="notification",
            notification=notification,
        )

        success_count = 0
        total_connections = len(self.active_connections[user_id])

        for websocket in self.active_connections[user_id].copy():
            try:
                await self._send_to_connection(
                    websocket,
                    message.model_dump(mode="json"),
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"向用户 {user_id} 发送通知失败: {str(e)}")
                # 移除失效连接
                self.active_connections[user_id].discard(websocket)

        logger.info(f"向用户 {user_id} 发送通知: {success_count}/{total_connections} 连接成功")
        return success_count > 0

    async def send_notification_to_users(
        self,
        user_ids: list[int],
        notification: NotificationResponse,
    ) -> dict[int, bool]:
        """向多个用户发送实时通知."""
        results = {}

        for user_id in user_ids:
            results[user_id] = await self.send_notification_to_user(user_id, notification)

        return results

    async def broadcast_system_message(
        self,
        message: dict[str, Any],
        exclude_users: list[int] | None = None,
    ) -> int:
        """广播系统消息."""
        exclude_users = exclude_users or []
        sent_count = 0

        for user_id, connections in self.active_connections.items():
            if user_id in exclude_users:
                continue

            for websocket in connections.copy():
                try:
                    await self._send_to_connection(websocket, message)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"广播消息失败: {str(e)}")
                    connections.discard(websocket)

        logger.info(f"系统消息广播完成: {sent_count} 个连接")
        return sent_count

    async def send_training_realtime_update(
        self,
        user_id: int,
        training_data: dict[str, Any],
    ) -> bool:
        """发送训练实时更新 - 设计文档WebSocket接口."""
        message = {
            "type": "training_update",
            "data": training_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self._send_to_user(user_id, message)

    async def send_analytics_update(
        self,
        user_id: int,
        analytics_data: dict[str, Any],
    ) -> bool:
        """发送学情数据推送 - 设计文档WebSocket接口."""
        message = {
            "type": "analytics_update",
            "data": analytics_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self._send_to_user(user_id, message)

    async def handle_client_message(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: str,
        message: dict[str, Any],
    ) -> None:
        """处理客户端消息."""
        try:
            message_type = message.get("type")

            if message_type == "heartbeat":
                await self._handle_heartbeat(connection_id)
            elif message_type == "mark_read":
                notification_id = message.get("notification_id")
                if notification_id is not None:
                    await self._handle_mark_read(user_id, int(notification_id))
            elif message_type == "subscribe":
                await self._handle_subscription(user_id, message.get("channels", []))
            else:
                logger.warning(f"未知消息类型: {message_type}")

        except Exception as e:
            logger.error(f"处理客户端消息失败: {str(e)}")

    async def get_connection_stats(self) -> dict[str, Any]:
        """获取连接统计信息."""
        total_connections = sum(
            len(connections) for connections in self.active_connections.values()
        )
        active_users = len(self.active_connections)

        # 按用户统计连接数
        user_connections = {
            user_id: len(connections) for user_id, connections in self.active_connections.items()
        }

        return {
            "total_connections": total_connections,
            "active_users": active_users,
            "user_connections": user_connections,
            "connection_info": {
                conn_id: info.model_dump() for conn_id, info in self.connection_info.items()
            },
        }

    async def cleanup_stale_connections(self) -> int:
        """清理失效连接."""
        cleaned_count = 0
        current_time = datetime.utcnow()

        for connection_id, info in list(self.connection_info.items()):
            # 检查心跳超时（5分钟）
            if (current_time - info.last_heartbeat).total_seconds() > 300:
                user_id = info.user_id

                # 查找对应的WebSocket连接并移除
                if user_id in self.active_connections:
                    for websocket in list(self.active_connections[user_id]):
                        try:
                            await websocket.close()
                        except Exception:
                            pass
                        self.active_connections[user_id].discard(websocket)

                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]

                # 清理连接信息
                del self.connection_info[connection_id]

                # 取消心跳任务
                if connection_id in self.heartbeat_tasks:
                    self.heartbeat_tasks[connection_id].cancel()
                    del self.heartbeat_tasks[connection_id]

                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个失效连接")

        return cleaned_count

    # =================== 私有方法 ===================

    async def _send_to_connection(
        self,
        websocket: WebSocket,
        message: dict[str, Any],
    ) -> None:
        """向指定连接发送消息."""
        await websocket.send_text(json.dumps(message, default=str))

    async def _send_to_user(
        self,
        user_id: int,
        message: dict[str, Any],
    ) -> bool:
        """向指定用户发送消息."""
        if user_id not in self.active_connections:
            return False

        success_count = 0
        for websocket in self.active_connections[user_id].copy():
            try:
                await self._send_to_connection(websocket, message)
                success_count += 1
            except Exception as e:
                logger.warning(f"发送消息失败: {str(e)}")
                self.active_connections[user_id].discard(websocket)

        return success_count > 0

    async def _heartbeat_monitor(
        self,
        websocket: WebSocket,
        connection_id: str,
    ) -> None:
        """心跳监控任务."""
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒发送心跳

                if connection_id not in self.connection_info:
                    break

                try:
                    await self._send_to_connection(
                        websocket,
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                except Exception:
                    # 连接已断开
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"心跳监控任务失败: {str(e)}")

    async def _handle_heartbeat(self, connection_id: str) -> None:
        """处理心跳响应."""
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_heartbeat = datetime.utcnow()

    async def _handle_mark_read(self, user_id: int, notification_id: int) -> None:
        """处理标记已读消息."""
        # 这里可以调用通知服务来更新数据库
        logger.info(f"用户 {user_id} 标记通知 {notification_id} 为已读")

    async def _handle_subscription(self, user_id: int, channels: list[str]) -> None:
        """处理订阅频道消息."""
        logger.info(f"用户 {user_id} 订阅频道: {channels}")


# 全局WebSocket管理器实例
websocket_manager = WebSocketConnectionManager()
