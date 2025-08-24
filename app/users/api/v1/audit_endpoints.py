"""权限审计与监控API端点 - 需求7：权限中枢管理."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.schemas.audit_schemas import (
    AuditLogResponse,
    PermissionAuditRequest,
    PermissionAuditResponse,
    SecurityEventResponse,
    UserActivityResponse,
)
from app.users.services.audit_service import AuditService
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["权限审计"])


# ===== 操作日志审计端点 =====


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    start_date: str | None = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    user_id: int | None = Query(None, description="用户ID筛选"),
    action_type: str | None = Query(None, description="操作类型筛选"),
    resource_type: str | None = Query(None, description="资源类型筛选"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    """获取操作日志 - 需求7验收标准4."""
    # 权限检查：只有管理员可以查看审计日志
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看审计日志",
        )

    try:
        service = AuditService(db)
        logs = await service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            limit=limit,
            offset=offset,
        )

        logger.info(f"管理员 {current_user.id} 查看审计日志")

        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                username=log.username,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                timestamp=log.timestamp,
                success=log.success,
                error_message=log.error_message,
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f"获取审计日志失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取审计日志失败",
        ) from e


# ===== 权限变更审计端点 =====


@router.get("/permissions", response_model=list[PermissionAuditResponse])
async def get_permission_audit_logs(
    request: PermissionAuditRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionAuditResponse]:
    """获取权限变更日志 - 需求7验收标准4."""
    # 权限检查：只有管理员可以查看权限审计日志
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看权限审计日志",
        )

    try:
        service = AuditService(db)
        logs = await service.get_permission_audit_logs(
            user_id=request.user_id,
            permission_code=request.permission_code,
            change_type=request.change_type,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset,
        )

        logger.info(f"管理员 {current_user.id} 查看权限变更日志")

        return [
            PermissionAuditResponse(
                id=log.id,
                user_id=log.user_id,
                username=log.username,
                permission_code=log.permission_code,
                permission_name=log.permission_name,
                change_type=log.change_type,
                old_value=log.old_value,
                new_value=log.new_value,
                changed_by=log.changed_by,
                changed_by_username=log.changed_by_username,
                reason=log.reason,
                timestamp=log.timestamp,
                ip_address=log.ip_address,
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f"获取权限变更日志失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限变更日志失败",
        ) from e


# ===== 异常访问检测端点 =====


@router.get("/security-events", response_model=list[SecurityEventResponse])
async def get_security_events(
    event_type: str | None = Query(None, description="事件类型筛选"),
    severity: str | None = Query(None, description="严重级别筛选"),
    start_date: str | None = Query(None, description="开始日期"),
    end_date: str | None = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SecurityEventResponse]:
    """获取安全事件 - 需求7验收标准4."""
    # 权限检查：只有管理员可以查看安全事件
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看安全事件",
        )

    try:
        service = AuditService(db)
        events = await service.get_security_events(
            event_type=event_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        logger.info(f"管理员 {current_user.id} 查看安全事件")

        return [
            SecurityEventResponse(
                id=event.id,
                event_type=event.event_type,
                severity=event.severity,
                user_id=event.user_id,
                username=event.username,
                description=event.description,
                details=event.details,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                timestamp=event.timestamp,
                resolved=event.resolved,
                resolved_by=event.resolved_by,
                resolved_at=event.resolved_at,
            )
            for event in events
        ]

    except Exception as e:
        logger.error(f"获取安全事件失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全事件失败",
        ) from e


# ===== 权限使用统计端点 =====


@router.get("/statistics")
async def get_permission_statistics(
    time_range: str = Query("7d", description="时间范围", regex="^(1d|7d|30d|90d)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取权限使用统计 - 需求7验收标准4."""
    # 权限检查：只有管理员可以查看权限统计
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看权限统计",
        )

    try:
        service = AuditService(db)
        statistics = await service.get_permission_statistics(time_range)

        logger.info(f"管理员 {current_user.id} 查看权限使用统计")

        return {
            "time_range": time_range,
            "statistics": statistics,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取权限统计失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限统计失败",
        ) from e


# ===== 用户活动监控端点 =====


@router.get("/user-activity", response_model=list[UserActivityResponse])
async def get_user_activity(
    user_id: int | None = Query(None, description="用户ID筛选"),
    activity_type: str | None = Query(None, description="活动类型筛选"),
    start_date: str | None = Query(None, description="开始日期"),
    end_date: str | None = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserActivityResponse]:
    """获取用户活动记录 - 需求7验收标准4."""
    # 权限检查：管理员可以查看所有用户活动，用户只能查看自己的活动
    if current_user.user_type != UserType.ADMIN and user_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只能查看自己的活动记录",
        )

    try:
        service = AuditService(db)
        activities = await service.get_user_activity(
            user_id=user_id or current_user.id,
            activity_type=activity_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        logger.info(f"用户 {current_user.id} 查看用户活动记录")

        return [
            UserActivityResponse(
                id=activity.id,
                user_id=activity.user_id,
                username=activity.username,
                activity_type=activity.activity_type,
                description=activity.description,
                details=activity.details,
                ip_address=activity.ip_address,
                user_agent=activity.user_agent,
                timestamp=activity.timestamp,
                session_id=activity.session_id,
            )
            for activity in activities
        ]

    except Exception as e:
        logger.error(f"获取用户活动记录失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户活动记录失败",
        ) from e


# ===== 审计报告生成端点 =====


@router.post("/reports/generate")
async def generate_audit_report(
    report_type: str = Query(
        ...,
        description="报告类型",
        regex="^(permission_changes|security_events|user_activity|comprehensive)$",
    ),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    format: str = Query("json", description="报告格式", regex="^(json|csv|pdf)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """生成审计报告 - 需求7验收标准4."""
    # 权限检查：只有管理员可以生成审计报告
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以生成审计报告",
        )

    try:
        service = AuditService(db)
        report = await service.generate_audit_report(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            format=format,
            generated_by=current_user.id,
        )

        logger.info(f"管理员 {current_user.id} 生成审计报告: {report_type}")

        return {
            "report_id": report["report_id"],
            "report_type": report_type,
            "format": format,
            "start_date": start_date,
            "end_date": end_date,
            "generated_by": current_user.id,
            "generated_at": datetime.now().isoformat(),
            "file_path": report.get("file_path"),
            "download_url": report.get("download_url"),
            "summary": report.get("summary"),
        }

    except Exception as e:
        logger.error(f"生成审计报告失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成审计报告失败",
        ) from e
