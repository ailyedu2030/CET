"""系统监控API端点 - 需求6：系统监控与数据决策支持."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.services.system_monitoring_service import SystemMonitoringService
from app.core.database import get_db
from app.shared.models.enums import UserType
from app.shared.services.cache_service import CacheService, get_cache_service
from app.users.models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["系统监控"])


@router.get("/teaching/dashboard")
async def get_teaching_monitoring_dashboard(
    period_days: int = Query(7, ge=1, le=365, description="监控周期天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取教学监控看板 - 需求6：教学监控."""
    # 权限检查：只有管理员可以查看教学监控看板
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看教学监控看板",
        )

    try:
        service = SystemMonitoringService(db, cache_service)
        dashboard_data = await service.get_teaching_monitoring_dashboard(period_days)

        logger.info(f"管理员 {current_user.id} 查看了教学监控看板")
        return dashboard_data

    except Exception as e:
        logger.error(f"获取教学监控看板失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取教学监控看板失败",
        ) from e


@router.get("/system/operations")
async def get_system_operations_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取系统运维监控 - 需求6：系统运维监控."""
    # 权限检查：只有管理员可以查看系统运维监控
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看系统运维监控",
        )

    try:
        service = SystemMonitoringService(db, cache_service)
        monitoring_data = await service.get_system_operations_monitoring()

        logger.info(f"管理员 {current_user.id} 查看了系统运维监控")
        return monitoring_data

    except Exception as e:
        logger.error(f"获取系统运维监控失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统运维监控失败",
        ) from e


@router.get("/predictive/maintenance")
async def get_predictive_maintenance_analysis(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取预测性维护分析 - 需求6：预测性维护."""
    # 权限检查：只有管理员可以查看预测性维护分析
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看预测性维护分析",
        )

    try:
        service = SystemMonitoringService(db, cache_service)
        analysis_data = await service.get_predictive_maintenance_analysis()

        logger.info(f"管理员 {current_user.id} 查看了预测性维护分析")
        return analysis_data

    except Exception as e:
        logger.error(f"获取预测性维护分析失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取预测性维护分析失败",
        ) from e


@router.get("/comprehensive/report")
async def generate_comprehensive_monitoring_report(
    period_days: int = Query(7, ge=1, le=365, description="报告周期天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """生成综合监控报告 - 需求6：数据可视化和报告."""
    # 权限检查：只有管理员可以生成综合监控报告
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以生成综合监控报告",
        )

    try:
        service = SystemMonitoringService(db, cache_service)
        report_data = await service.generate_comprehensive_monitoring_report(period_days)

        logger.info(f"管理员 {current_user.id} 生成了综合监控报告")
        return report_data

    except Exception as e:
        logger.error(f"生成综合监控报告失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成综合监控报告失败",
        ) from e


@router.get("/health/check")
async def system_health_check(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """系统健康检查 - 需求6：系统监控."""
    # 权限检查：只有管理员可以进行系统健康检查
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以进行系统健康检查",
        )

    try:
        service = SystemMonitoringService(db, cache_service)

        # 获取应用健康状态
        health_data = await service._get_application_health()

        # 获取API使用统计
        api_stats = await service._get_deepseek_api_stats()

        # 简化的健康检查响应
        health_status = {
            "status": health_data.get("status", "unknown"),
            "health_score": health_data.get("overall_health_score", 0),
            "server_resources": health_data.get("server_resources", {}),
            "api_health": {
                "success_rate": api_stats.get("success_rate_percent", 0),
                "total_calls": api_stats.get("total_calls", 0),
                "warnings": api_stats.get("warnings", []),
            },
            "warnings": health_data.get("warnings", []),
            "timestamp": health_data.get("timestamp"),
        }

        logger.info(f"管理员 {current_user.id} 进行了系统健康检查")
        return health_status

    except Exception as e:
        logger.error(f"系统健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系统健康检查失败",
        ) from e


@router.get("/alerts/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取当前活跃告警 - 需求6：异常阈值告警."""
    # 权限检查：只有管理员可以查看活跃告警
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看活跃告警",
        )

    try:
        service = SystemMonitoringService(db, cache_service)

        # 获取系统监控数据
        system_monitoring = await service.get_system_operations_monitoring()
        teaching_dashboard = await service.get_teaching_monitoring_dashboard(1)  # 最近1天

        # 收集所有告警
        all_alerts = []
        all_alerts.extend(system_monitoring.get("alerts", []))
        all_alerts.extend(teaching_dashboard.get("alerts", []))

        # 按严重程度排序
        all_alerts.sort(
            key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x.get("severity", "info"), 2)
        )

        alert_summary = {
            "total_alerts": len(all_alerts),
            "critical_alerts": len([a for a in all_alerts if a.get("severity") == "critical"]),
            "warning_alerts": len([a for a in all_alerts if a.get("severity") == "warning"]),
            "info_alerts": len([a for a in all_alerts if a.get("severity") == "info"]),
            "alerts": all_alerts[:20],  # 返回最多20个告警
            "last_updated": system_monitoring.get("last_updated"),
        }

        logger.info(f"管理员 {current_user.id} 查看了活跃告警")
        return alert_summary

    except Exception as e:
        logger.error(f"获取活跃告警失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取活跃告警失败",
        ) from e
