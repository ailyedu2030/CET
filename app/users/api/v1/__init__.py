"""用户管理API v1版本."""

from fastapi import APIRouter

from .activation_endpoints import router as activation_router
from .admin_endpoints import router as admin_router
from .audit_endpoints import router as audit_router
from .auth_endpoints import router as auth_router
from .backup_endpoints import router as backup_router
from .basic_info_endpoints import router as basic_info_router
from .mfa_endpoints import router as mfa_router
from .permission_endpoints import router as permission_router
from .registration_endpoints import router as registration_router
from .registration_verification_endpoints import (
    router as registration_verification_router,
)
from .restore_endpoints import router as restore_router

# 创建用户管理模块的主路由器
router = APIRouter(prefix="/users", tags=["用户管理"])

# 包含子路由
router.include_router(auth_router)
router.include_router(registration_router)
router.include_router(registration_verification_router)
router.include_router(activation_router)
router.include_router(basic_info_router)
router.include_router(permission_router)
router.include_router(admin_router)  # 管理员专用API
router.include_router(mfa_router)
router.include_router(audit_router)
router.include_router(backup_router)
router.include_router(restore_router)
