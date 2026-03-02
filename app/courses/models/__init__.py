"""课程管理模块模型."""

from .course_models import (
    Class,
    ClassResourceHistory,
    ClassStudent,
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
    "ClassStudent",
    "CourseAssignmentHistory",
    "CourseTemplate",
    "CourseVersion",
    "Resource",
    "RuleExemptionRequest",
    "Syllabus",
    "TeacherCoursePermission",
]
