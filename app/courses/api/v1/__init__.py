"""课程管理模块API v1版本."""

from fastapi import APIRouter

from .assignment_endpoints import router as assignment_router
from .class_endpoints import router as class_router
from .class_management_endpoints import router as class_management_router
from .course_assignment_endpoints import router as course_assignment_router
from .course_endpoints import router as course_router
from .rule_endpoints import router as rule_router
from .syllabus_approval_endpoints import router as syllabus_approval_router

# 创建课程管理模块的主路由器
router = APIRouter(prefix="/courses", tags=["课程管理"])

# 包含子路由
router.include_router(course_router)
router.include_router(class_router)
router.include_router(class_management_router)
router.include_router(course_assignment_router)
router.include_router(assignment_router)
router.include_router(rule_router)
router.include_router(syllabus_approval_router)
