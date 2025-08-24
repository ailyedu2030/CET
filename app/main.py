"""英语四级学习系统 - FastAPI应用入口."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# 导入各模块的路由器
from app.ai.api.v1 import router as ai_router
from app.analytics.api.v1 import router as analytics_router
from app.core.api.v1.architecture_endpoints import router as architecture_router
from app.core.config import settings
from app.core.database import create_tables
from app.courses.api.v1 import router as courses_router
from app.resources.api.v1 import router as resources_router
from app.training.api.v1 import router as training_router
from app.users.api.v1 import router as users_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理."""
    # 启动时创建数据库表
    await create_tables()
    yield
    # 关闭时的清理工作


# 创建FastAPI应用实例
app = FastAPI(
    title="英语四级学习及教学系统",
    description="AI驱动的英语四级学习平台, 支持智能批改、个性化学习和教学管理",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 添加中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health")
async def health_check() -> dict[str, str]:
    """应用健康检查."""
    return {"status": "healthy", "service": "cet4-learning-system", "version": "1.0.0"}


# 根路径
@app.get("/")
async def root() -> dict[str, str]:
    """根路径欢迎信息."""
    return {
        "message": "英语四级学习及教学系统 API",
        "docs": "/docs",
        "health": "/health",
    }


# ==================== 模块路由注册 ====================

# 注册各模块路由到主应用
app.include_router(users_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(resources_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(architecture_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # 仅本地访问, 生产环境中通过反向代理
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
