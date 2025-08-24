"""训练系统API v1版本."""

from fastapi import APIRouter

from .adaptive_learning_endpoints import router as adaptive_router
from .training_endpoints import router as training_router
from .training_workshop_endpoints import router as workshop_router

# 创建训练系统模块的主路由器
router = APIRouter(prefix="/training", tags=["训练系统"])

# 包含子路由
router.include_router(training_router)
router.include_router(adaptive_router)
router.include_router(workshop_router)
