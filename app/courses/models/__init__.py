"""课程管理模块模型."""

from .course_models import (
    Class,
    ClassResourceHistory,
    Course,
    CourseAssignmentHistory,
    CourseTemplate,
    CourseVersion,
    Resource,
    RuleExemptionRequest,
    Syllabus,
    TeacherCoursePermission,
)

__all__ = [
    "Course",
    "Class",
    "ClassResourceHistory",
    "CourseAssignmentHistory",
    "CourseTemplate",
    "CourseVersion",
    "Resource",
    "RuleExemptionRequest",
    "Syllabus",
    "TeacherCoursePermission",
]
