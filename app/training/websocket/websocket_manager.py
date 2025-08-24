"""WebSocket管理器 - 🔥需求21第三阶段实时推送核心实现.

WebSocket实时推送功能：
- 实时性能数据推送（延迟<1秒）
- 智能预警实时通知
- 学习进度实时更新
- 连接管理和心跳检测
- 多客户端支持
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.training.services.real_time_monitoring_service import RealTimeMonitoringService

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器."""

    def __init__(self) -> None:
        # 活跃连接：{student_id: {session_id: [websockets]}}
        self.active_connections: dict[int, dict[int, list[WebSocket]]] = {}

        # 连接元数据：{websocket: {student_id, session_id, connect_time}}
        self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}

        # 心跳任务
        self.heartbeat_tasks: dict[WebSocket, asyncio.Task[None]] = {}

        # 推送配置
        self.push_config = {
            "heartbeat_interval": 30,  # 30秒心跳间隔
            "max_connections_per_student": 5,  # 每个学生最多5个连接
            "connection_timeout": 300,  # 5分钟连接超时
            "push_interval": 1,  # 1秒推送间隔
        }

    async def connect(self, websocket: WebSocket, student_id: int, session_id: int) -> bool:
        """建立WebSocket连接."""
        try:
            await websocket.accept()

            # 检查连接数限制
            if not self._check_connection_limit(student_id):
                await websocket.close(code=1008, reason="连接数超限")
                return False

            # 添加连接
            if student_id not in self.active_connections:
                self.active_connections[student_id] = {}

            if session_id not in self.active_connections[student_id]:
                self.active_connections[student_id][session_id] = []

            self.active_connections[student_id][session_id].append(websocket)

            # 记录连接元数据
            self.connection_metadata[websocket] = {
                "student_id": student_id,
                "session_id": session_id,
                "connect_time": datetime.now(),
                "last_heartbeat": datetime.now(),
            }

            # 启动心跳任务
            heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket))
            self.heartbeat_tasks[websocket] = heartbeat_task

            logger.info(f"WebSocket连接建立: 学生{student_id}, 会话{session_id}")

            # 发送连接确认
            await self.send_personal_message(
                websocket,
                {
                    "type": "connection_established",
                    "student_id": student_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "实时监控连接已建立",
                },
            )

            return True

        except Exception as e:
            logger.error(f"WebSocket连接建立失败: {str(e)}")
            return False

    async def disconnect(self, websocket: WebSocket) -> None:
        """断开WebSocket连接."""
        try:
            if websocket not in self.connection_metadata:
                return

            metadata = self.connection_metadata[websocket]
            student_id = metadata["student_id"]
            session_id = metadata["session_id"]

            # 移除连接
            if (
                student_id in self.active_connections
                and session_id in self.active_connections[student_id]
            ):
                connections = self.active_connections[student_id][session_id]
                if websocket in connections:
                    connections.remove(websocket)

                # 清理空的会话连接
                if not connections:
                    del self.active_connections[student_id][session_id]

                # 清理空的学生连接
                if not self.active_connections[student_id]:
                    del self.active_connections[student_id]

            # 清理元数据
            del self.connection_metadata[websocket]

            # 取消心跳任务
            if websocket in self.heartbeat_tasks:
                self.heartbeat_tasks[websocket].cancel()
                del self.heartbeat_tasks[websocket]

            logger.info(f"WebSocket连接断开: 学生{student_id}, 会话{session_id}")

        except Exception as e:
            logger.error(f"WebSocket连接断开处理失败: {str(e)}")

    async def send_personal_message(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """发送个人消息."""
        try:
            await websocket.send_text(json.dumps(message, default=str, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送个人消息失败: {str(e)}")
            await self.disconnect(websocket)

    async def broadcast_to_session(
        self, student_id: int, session_id: int, message: dict[str, Any]
    ) -> None:
        """向特定会话的所有连接广播消息."""
        if (
            student_id not in self.active_connections
            or session_id not in self.active_connections[student_id]
        ):
            return

        connections = self.active_connections[student_id][session_id].copy()

        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message, default=str, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败: {str(e)}")
                await self.disconnect(websocket)

    async def broadcast_to_student(self, student_id: int, message: dict[str, Any]) -> None:
        """向学生的所有连接广播消息."""
        if student_id not in self.active_connections:
            return

        for _session_id, connections in self.active_connections[student_id].items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(json.dumps(message, default=str, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"广播消息失败: {str(e)}")
                    await self.disconnect(websocket)

    def _check_connection_limit(self, student_id: int) -> bool:
        """检查连接数限制."""
        if student_id not in self.active_connections:
            return True

        total_connections = sum(
            len(connections) for connections in self.active_connections[student_id].values()
        )

        return total_connections < self.push_config["max_connections_per_student"]

    async def _heartbeat_loop(self, websocket: WebSocket) -> None:
        """心跳循环."""
        try:
            while True:
                await asyncio.sleep(self.push_config["heartbeat_interval"])

                # 发送心跳
                await websocket.send_text(
                    json.dumps({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
                )

                # 更新心跳时间
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_heartbeat"] = datetime.now()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"心跳循环异常: {str(e)}")
            await self.disconnect(websocket)

    def get_connection_stats(self) -> dict[str, Any]:
        """获取连接统计信息."""
        total_connections = 0
        active_students = len(self.active_connections)
        active_sessions = 0

        for student_connections in self.active_connections.values():
            active_sessions += len(student_connections)
            for connections in student_connections.values():
                total_connections += len(connections)

        return {
            "total_connections": total_connections,
            "active_students": active_students,
            "active_sessions": active_sessions,
            "connection_limit_per_student": self.push_config["max_connections_per_student"],
            "heartbeat_interval": self.push_config["heartbeat_interval"],
        }


class RealTimePushService:
    """实时推送服务."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.connection_manager = ConnectionManager()
        self.monitoring_service = RealTimeMonitoringService(db)

        # 推送任务管理
        self.push_tasks: dict[str, asyncio.Task[None]] = {}

        # 推送配置
        self.push_config = {
            "metrics_push_interval": 1,  # 1秒推送间隔
            "alerts_push_immediate": True,  # 预警立即推送
            "batch_size": 10,  # 批量推送大小
            "max_queue_size": 100,  # 最大队列大小
        }

    async def start_real_time_push(self, student_id: int, session_id: int) -> bool:
        """启动实时推送."""
        try:
            # 初始化监控服务
            await self.monitoring_service.initialize_redis()

            # 启动监控
            monitoring_result = await self.monitoring_service.start_real_time_monitoring(
                student_id, session_id
            )

            if not monitoring_result.get("monitoring_started"):
                return False

            # 启动推送任务
            task_key = f"{student_id}:{session_id}"
            if task_key not in self.push_tasks:
                push_task = asyncio.create_task(self._push_loop(student_id, session_id))
                self.push_tasks[task_key] = push_task

            logger.info(f"实时推送启动: 学生{student_id}, 会话{session_id}")
            return True

        except Exception as e:
            logger.error(f"启动实时推送失败: {str(e)}")
            return False

    async def stop_real_time_push(self, student_id: int, session_id: int) -> None:
        """停止实时推送."""
        try:
            # 停止推送任务
            task_key = f"{student_id}:{session_id}"
            if task_key in self.push_tasks:
                self.push_tasks[task_key].cancel()
                del self.push_tasks[task_key]

            # 停止监控
            await self.monitoring_service.stop_real_time_monitoring(student_id, session_id)

            # 发送停止通知
            await self.connection_manager.broadcast_to_session(
                student_id,
                session_id,
                {
                    "type": "monitoring_stopped",
                    "student_id": student_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "实时监控已停止",
                },
            )

            logger.info(f"实时推送停止: 学生{student_id}, 会话{session_id}")

        except Exception as e:
            logger.error(f"停止实时推送失败: {str(e)}")

    async def _push_loop(self, student_id: int, session_id: int) -> None:
        """推送循环."""
        try:
            while True:
                # 采集实时指标
                metrics = await self.monitoring_service.collect_real_time_metrics(
                    student_id, session_id
                )

                if "error" not in metrics:
                    # 推送性能指标
                    await self.connection_manager.broadcast_to_session(
                        student_id,
                        session_id,
                        {
                            "type": "real_time_metrics",
                            "data": metrics,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                    # 检查并推送预警
                    if "alerts" in metrics and metrics["alerts"]:
                        await self._push_alerts(student_id, session_id, metrics["alerts"])

                # 等待下次推送
                await asyncio.sleep(self.push_config["metrics_push_interval"])

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"推送循环异常: {str(e)}")

    async def _push_alerts(
        self, student_id: int, session_id: int, alerts: list[dict[str, Any]]
    ) -> None:
        """推送预警信息."""
        try:
            for alert in alerts:
                await self.connection_manager.broadcast_to_session(
                    student_id,
                    session_id,
                    {
                        "type": "alert",
                        "data": alert,
                        "timestamp": datetime.now().isoformat(),
                        "urgent": alert.get("severity") == "critical",
                    },
                )

            logger.info(f"推送预警: 学生{student_id}, 会话{session_id}, 预警数量{len(alerts)}")

        except Exception as e:
            logger.error(f"推送预警失败: {str(e)}")

    async def handle_websocket_connection(
        self, websocket: WebSocket, student_id: int, session_id: int
    ) -> None:
        """处理WebSocket连接."""
        # 建立连接
        connected = await self.connection_manager.connect(websocket, student_id, session_id)
        if not connected:
            return

        # 启动实时推送
        await self.start_real_time_push(student_id, session_id)

        try:
            # 监听客户端消息
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理客户端消息
                await self._handle_client_message(websocket, student_id, session_id, message)

        except WebSocketDisconnect:
            logger.info(f"WebSocket客户端断开: 学生{student_id}, 会话{session_id}")
        except Exception as e:
            logger.error(f"WebSocket连接处理异常: {str(e)}")
        finally:
            # 清理连接
            await self.connection_manager.disconnect(websocket)
            await self.stop_real_time_push(student_id, session_id)

    async def _handle_client_message(
        self,
        websocket: WebSocket,
        student_id: int,
        session_id: int,
        message: dict[str, Any],
    ) -> None:
        """处理客户端消息."""
        try:
            message_type = message.get("type")

            if message_type == "ping":
                # 响应ping
                await self.connection_manager.send_personal_message(
                    websocket, {"type": "pong", "timestamp": datetime.now().isoformat()}
                )

            elif message_type == "request_metrics":
                # 请求当前指标
                metrics = await self.monitoring_service.collect_real_time_metrics(
                    student_id, session_id
                )
                await self.connection_manager.send_personal_message(
                    websocket,
                    {
                        "type": "current_metrics",
                        "data": metrics,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            elif message_type == "update_config":
                # 更新推送配置
                config = message.get("config", {})
                self._update_push_config(config)

                await self.connection_manager.send_personal_message(
                    websocket,
                    {
                        "type": "config_updated",
                        "config": self.push_config,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        except Exception as e:
            logger.error(f"处理客户端消息失败: {str(e)}")

    def _update_push_config(self, config: dict[str, Any]) -> None:
        """更新推送配置."""
        for key, value in config.items():
            if key in self.push_config:
                self.push_config[key] = value

    def get_push_stats(self) -> dict[str, Any]:
        """获取推送统计信息."""
        return {
            "active_push_tasks": len(self.push_tasks),
            "connection_stats": self.connection_manager.get_connection_stats(),
            "push_config": self.push_config,
            "service_status": "running",
        }


# 全局连接管理器实例
connection_manager = ConnectionManager()
