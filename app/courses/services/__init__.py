"""课程管理模块services."""

from .assignment_service import AssignmentService
from .class_service import ClassResourceService, ClassService
from .course_service import CoursePermissionService, CourseService
from .template_service import CourseTemplateService

__all__ = [
    "CourseService",
    "CoursePermissionService",
    "CourseTemplateService",
    "ClassService",
    "ClassResourceService",
    "AssignmentService",
]
