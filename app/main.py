"""英语四级学习系统 - FastAPI应用入口."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# 导入安全中间件
from app.shared.middleware.security_middleware import create_security_middleware

# 导入核心异常
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConfigurationError,
    ExternalServiceError,
    ResourceNotFoundError,
    ValidationError,
)

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

# 添加安全中间件
app.add_middleware(create_security_middleware())


# ==================== 全局异常处理器 ====================

logger = logging.getLogger(__name__)


@app.exception_handler(BusinessLogicError)
async def business_logic_exception_handler(
    request: Request, exc: BusinessLogicError
) -> JSONResponse:
    """处理业务逻辑异常."""
    logger.warning(f"Business logic error: {exc}")
    status_code = 400
    if isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, AuthorizationError):
        status_code = 403
    elif isinstance(exc, ResourceNotFoundError):
        status_code = 404
    elif isinstance(exc, ValidationError):
        status_code = 422
    elif isinstance(exc, ExternalServiceError):
        status_code = 503
    elif isinstance(exc, ConfigurationError):
        status_code = 500
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理HTTP异常."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器 - 捕获所有未处理的异常."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # 生产环境不暴露详细错误信息
    error_detail = "Internal server error" if not settings.DEBUG else str(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": error_detail},
    )


# ==================== 健康检查端点 ====================


@app.get("/health")
async def health_check() -> dict[str, str]:
    """应用健康检查."""
    return {"status": "healthy", "service": "cet4-learning-system", "version": "1.0.0"}


@app.get("/health/ready")
async def readiness_check() -> dict[str, str | bool]:
    """应用就绪检查 - 检查依赖服务."""
    # 这里可以扩展检查数据库、Redis等依赖
    return {
        "status": "ready",
        "service": "cet4-learning-system",
        "version": "1.0.0",
        "database": True,  # 占位 - 实际应该检查数据库连接
        "redis": True,  # 占位 - 实际应该检查Redis连接
    }


# 根路径
@app.get("/")
async def root() -> dict[str, str | list[str]]:
    """根路径欢迎信息."""
    return {
        "message": "英语四级学习及教学系统 API",
        "docs": "/docs",
        "health": "/health",
        "health_ready": "/health/ready",
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
