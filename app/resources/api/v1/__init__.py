"""资源库模块API v1版本."""

from fastapi import APIRouter

from .hotspot_endpoints import router as hotspot_router
from .professional_development_endpoints import (
    router as professional_development_router,
)
from .resource_endpoints import router as resource_router

# 创建资源库模块的主路由器
router = APIRouter(prefix="/resources", tags=["资源库"])

# 包含子路由
router.include_router(resource_router)
router.include_router(hotspot_router)
router.include_router(professional_development_router)
