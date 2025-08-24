"""分析模块API v1版本."""

from fastapi import APIRouter

from .alert_management_endpoints import router as alert_management_router
from .data_visualization_endpoints import router as data_visualization_router
from .enhanced_monitoring_endpoints import router as enhanced_monitoring_router
from .report_generation_endpoints import router as report_generation_router
from .system_monitoring_endpoints import router as system_monitoring_router

# 创建分析模块的主路由器
router = APIRouter(prefix="/analytics", tags=["数据分析"])

# 包含子路由
router.include_router(enhanced_monitoring_router)
router.include_router(system_monitoring_router)
router.include_router(report_generation_router)
router.include_router(data_visualization_router)
router.include_router(alert_management_router)
