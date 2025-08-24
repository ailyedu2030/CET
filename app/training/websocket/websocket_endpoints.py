"""WebSocket端点 - 🔥需求21第三阶段实时推送API实现.

WebSocket端点功能：
- 实时性能监控连接
- 智能预警推送
- 学习进度实时更新
- 连接状态管理
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import UserType
from app.training.websocket.websocket_manager import (
    RealTimePushService,
    connection_manager,
)
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

router = APIRouter(tags=["实时监控WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/real-time-monitoring/{student_id}/{session_id}")
async def websocket_real_time_monitoring(
    websocket: WebSocket,
    student_id: int,
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """实时性能监控WebSocket连接."""
    logger.info(f"WebSocket连接请求: 学生{student_id}, 会话{session_id}")

    # 创建实时推送服务
    push_service = RealTimePushService(db)

    # 处理WebSocket连接
    await push_service.handle_websocket_connection(websocket, student_id, session_id)


@router.get(
    "/ws/connection-stats",
    summary="获取WebSocket连接统计",
    description="获取当前WebSocket连接的统计信息",
    response_description="连接统计数据",
)
async def get_websocket_connection_stats(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取WebSocket连接统计信息."""
    try:
        stats = connection_manager.get_connection_stats()

        return {"success": True, "data": stats, "message": "WebSocket连接统计获取成功"}

    except Exception as e:
        logger.error(f"获取WebSocket连接统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取连接统计失败: {str(e)}") from e


@router.post(
    "/ws/broadcast-message",
    summary="广播消息到WebSocket连接",
    description="向指定学生或会话广播消息",
    response_description="广播结果",
)
async def broadcast_websocket_message(
    student_id: int,
    message: dict[str, Any],
    session_id: int = None,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """广播消息到WebSocket连接."""
    try:
        # 验证权限（管理员或本人）
        if current_user.id != student_id and current_user.user_type != UserType.ADMIN:
            raise HTTPException(status_code=403, detail="无权限访问其他用户的连接")

        # 添加发送者信息
        message.update({"sender": "system", "sender_id": current_user.id, "broadcast_time": "now"})

        # 广播消息
        if session_id:
            await connection_manager.broadcast_to_session(student_id, session_id, message)
            target = f"学生{student_id}的会话{session_id}"
        else:
            await connection_manager.broadcast_to_student(student_id, message)
            target = f"学生{student_id}的所有连接"

        return {
            "success": True,
            "message": f"消息已广播到{target}",
            "target": {
                "student_id": student_id,
                "session_id": session_id,
            },
        }

    except Exception as e:
        logger.error(f"广播WebSocket消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"广播消息失败: {str(e)}") from e


@router.get(
    "/ws/active-connections/{student_id}",
    summary="获取学生的活跃连接",
    description="获取指定学生的所有活跃WebSocket连接信息",
    response_description="活跃连接信息",
)
async def get_student_active_connections(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取学生的活跃连接信息."""
    try:
        # 验证权限
        if current_user.id != student_id and current_user.user_type != UserType.ADMIN:
            raise HTTPException(status_code=403, detail="无权限访问其他用户的连接信息")

        # 获取连接信息
        connections_info = []

        if student_id in connection_manager.active_connections:
            for session_id, websockets in connection_manager.active_connections[student_id].items():
                for websocket in websockets:
                    if websocket in connection_manager.connection_metadata:
                        metadata = connection_manager.connection_metadata[websocket]
                        connections_info.append(
                            {
                                "session_id": session_id,
                                "connect_time": metadata["connect_time"],
                                "last_heartbeat": metadata["last_heartbeat"],
                                "connection_id": id(websocket),  # 使用对象ID作为连接标识
                            }
                        )

        return {
            "success": True,
            "data": {
                "student_id": student_id,
                "total_connections": len(connections_info),
                "connections": connections_info,
                "connection_limit": connection_manager.push_config["max_connections_per_student"],
            },
            "message": f"学生{student_id}的活跃连接信息获取成功",
        }

    except Exception as e:
        logger.error(f"获取学生活跃连接失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取活跃连接失败: {str(e)}") from e


@router.delete(
    "/ws/disconnect/{student_id}",
    summary="断开学生的WebSocket连接",
    description="强制断开指定学生的所有或特定会话的WebSocket连接",
    response_description="断开连接结果",
)
async def disconnect_student_websockets(
    student_id: int,
    session_id: int = None,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """断开学生的WebSocket连接."""
    try:
        # 验证权限（仅管理员可以强制断开连接）
        if current_user.user_type != UserType.ADMIN:
            raise HTTPException(status_code=403, detail="仅管理员可以强制断开连接")

        disconnected_count = 0

        if student_id in connection_manager.active_connections:
            if session_id:
                # 断开特定会话的连接
                if session_id in connection_manager.active_connections[student_id]:
                    websockets = connection_manager.active_connections[student_id][
                        session_id
                    ].copy()
                    for websocket in websockets:
                        await connection_manager.disconnect(websocket)
                        await websocket.close(code=1000, reason="管理员强制断开")
                        disconnected_count += 1
            else:
                # 断开学生的所有连接
                for session_websockets in connection_manager.active_connections[
                    student_id
                ].values():
                    websockets = session_websockets.copy()
                    for websocket in websockets:
                        await connection_manager.disconnect(websocket)
                        await websocket.close(code=1000, reason="管理员强制断开")
                        disconnected_count += 1

        target = f"学生{student_id}" + (f"的会话{session_id}" if session_id else "的所有连接")

        return {
            "success": True,
            "message": f"已断开{target}，共{disconnected_count}个连接",
            "disconnected_count": disconnected_count,
            "target": {
                "student_id": student_id,
                "session_id": session_id,
            },
        }

    except Exception as e:
        logger.error(f"断开WebSocket连接失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"断开连接失败: {str(e)}") from e


@router.get(
    "/ws/health-check",
    summary="WebSocket服务健康检查",
    description="检查WebSocket服务的健康状态",
    response_description="健康状态信息",
)
async def websocket_health_check() -> dict[str, Any]:
    """WebSocket服务健康检查."""
    try:
        stats = connection_manager.get_connection_stats()

        # 检查服务状态
        health_status = "healthy"
        issues = []

        # 检查连接数是否过多
        if stats["total_connections"] > 100:
            health_status = "warning"
            issues.append("连接数较多，可能影响性能")

        # 检查活跃学生数
        if stats["active_students"] > 50:
            health_status = "warning"
            issues.append("活跃学生数较多")

        return {
            "success": True,
            "data": {
                "status": health_status,
                "stats": stats,
                "issues": issues,
                "timestamp": "now",
                "service_version": "1.0.0",
            },
            "message": f"WebSocket服务状态: {health_status}",
        }

    except Exception as e:
        logger.error(f"WebSocket健康检查失败: {str(e)}")
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "now",
            },
            "message": "WebSocket服务异常",
        }


# WebSocket测试端点
@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket) -> None:
    """WebSocket测试端点."""
    await websocket.accept()

    try:
        await websocket.send_text("WebSocket连接测试成功")

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        logger.info("WebSocket测试连接断开")
    except Exception as e:
        logger.error(f"WebSocket测试异常: {str(e)}")
        await websocket.close()
