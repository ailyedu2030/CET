"""AI API v1版本路由."""

from fastapi import APIRouter

from .ai_endpoints import router as ai_router
from .enhanced_teaching_endpoints import router as enhanced_teaching_router
from .grading_endpoints import router as grading_router

# 创建AI集成模块的主路由器
router = APIRouter(prefix="/ai", tags=["AI集成"])

# 包含子路由
router.include_router(ai_router)
router.include_router(grading_router)
router.include_router(enhanced_teaching_router)
