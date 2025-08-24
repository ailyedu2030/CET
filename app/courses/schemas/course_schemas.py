"""课程管理相关的Pydantic schemas定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.shared.models.enums import CourseShareLevel, CourseStatus, DifficultyLevel


class CourseBase(BaseModel):
    """课程基础信息schema."""

    name: str = Field(..., min_length=1, max_length=200, description="课程名称")
    description: str | None = Field(None, description="课程描述")
    code: str | None = Field(None, max_length=50, description="课程编码")
    total_hours: int | None = Field(None, ge=1, description="总学时")
    target_audience: str | None = Field(None, max_length=200, description="适用对象")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.ELEMENTARY, description="难度等级")
    share_level: CourseShareLevel = Field(CourseShareLevel.PRIVATE, description="共享级别")
    syllabus: dict[str, Any] = Field(default_factory=dict, description="教学大纲")
    teaching_plan: dict[str, Any] = Field(default_factory=dict, description="教学计划")
    resource_config: dict[str, Any] = Field(default_factory=dict, description="资源配置")


class CourseCreate(CourseBase):
    """课程创建schema."""

    version: str = Field("1.0", max_length=20, description="课程版本")
    parent_course_id: int | None = Field(None, description="模板课程ID")


class CourseUpdate(BaseModel):
    """课程更新schema."""

    name: str | None = Field(None, min_length=1, max_length=200, description="课程名称")
    description: str | None = Field(None, description="课程描述")
    code: str | None = Field(None, max_length=50, description="课程编码")
    total_hours: int | None = Field(None, ge=1, description="总学时")
    target_audience: str | None = Field(None, max_length=200, description="适用对象")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    share_level: CourseShareLevel | None = Field(None, description="共享级别")
    syllabus: dict[str, Any] | None = Field(None, description="教学大纲")
    teaching_plan: dict[str, Any] | None = Field(None, description="教学计划")
    resource_config: dict[str, Any] | None = Field(None, description="资源配置")


class CourseStatusUpdate(BaseModel):
    """课程状态更新schema."""

    status: CourseStatus = Field(..., description="课程状态")
    change_log: str | None = Field(None, description="状态变更说明")


class CourseResponse(CourseBase):
    """课程响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="课程ID")
    status: CourseStatus = Field(..., description="课程状态")
    version: str = Field(..., description="课程版本")
    parent_course_id: int | None = Field(None, description="模板课程ID")
    created_by: int | None = Field(None, description="创建者ID")
    approved_by: int | None = Field(None, description="审核者ID")
    approved_at: datetime | None = Field(None, description="审核时间")
    student_count: int = Field(..., description="学生人数")
    completion_rate: float = Field(..., description="完成率")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CourseListResponse(BaseModel):
    """课程列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="课程ID")
    name: str = Field(..., description="课程名称")
    code: str | None = Field(None, description="课程编码")
    status: CourseStatus = Field(..., description="课程状态")
    difficulty_level: DifficultyLevel = Field(..., description="难度等级")
    share_level: CourseShareLevel = Field(..., description="共享级别")
    student_count: int = Field(..., description="学生人数")
    completion_rate: float = Field(..., description="完成率")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CourseVersionBase(BaseModel):
    """课程版本基础schema."""

    version: str = Field(..., max_length=20, description="版本号")
    version_name: str | None = Field(None, max_length=100, description="版本名称")
    change_log: str | None = Field(None, description="版本变更说明")


class CourseVersionCreate(CourseVersionBase):
    """课程版本创建schema."""

    pass


class CourseVersionResponse(CourseVersionBase):
    """课程版本响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="版本ID")
    course_id: int = Field(..., description="课程ID")
    created_by: int | None = Field(None, description="创建者ID")
    is_active: bool = Field(..., description="是否为当前激活版本")
    is_backup: bool = Field(..., description="是否为备份版本")
    created_at: datetime = Field(..., description="创建时间")


class CourseTemplateBase(BaseModel):
    """课程模板基础schema."""

    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: str | None = Field(None, description="模板描述")
    category: str | None = Field(None, max_length=50, description="模板分类")
    template_data: dict[str, Any] = Field(..., description="模板数据")
    default_settings: dict[str, Any] = Field(default_factory=dict, description="默认设置")
    is_public: bool = Field(False, description="是否公开")


class CourseTemplateCreate(CourseTemplateBase):
    """课程模板创建schema."""

    source_course_id: int | None = Field(None, description="源课程ID")


class CourseTemplateUpdate(BaseModel):
    """课程模板更新schema."""

    name: str | None = Field(None, min_length=1, max_length=200, description="模板名称")
    description: str | None = Field(None, description="模板描述")
    category: str | None = Field(None, max_length=50, description="模板分类")
    template_data: dict[str, Any] | None = Field(None, description="模板数据")
    default_settings: dict[str, Any] | None = Field(None, description="默认设置")
    is_public: bool | None = Field(None, description="是否公开")
    is_active: bool | None = Field(None, description="是否激活")


class CourseTemplateResponse(CourseTemplateBase):
    """课程模板响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="模板ID")
    created_by: int | None = Field(None, description="创建者ID")
    source_course_id: int | None = Field(None, description="源课程ID")
    usage_count: int = Field(..., description="使用次数")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CourseTemplateListResponse(BaseModel):
    """课程模板列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    category: str | None = Field(None, description="模板分类")
    usage_count: int = Field(..., description="使用次数")
    is_public: bool = Field(..., description="是否公开")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")


class ClassBase(BaseModel):
    """班级基础信息schema."""

    name: str = Field(..., min_length=1, max_length=200, description="班级名称")
    description: str | None = Field(None, description="班级描述")
    code: str | None = Field(None, max_length=50, description="班级编码")
    max_students: int = Field(50, ge=1, description="最大学生数")
    resource_allocation: dict[str, Any] = Field(default_factory=dict, description="资源分配")
    class_rules: dict[str, Any] = Field(default_factory=dict, description="班级规则")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    schedule: dict[str, Any] = Field(default_factory=dict, description="课程表")


class ClassCreate(ClassBase):
    """班级创建schema."""

    course_id: int = Field(..., description="课程ID")
    teacher_id: int | None = Field(None, description="教师ID")


class ClassUpdate(BaseModel):
    """班级更新schema."""

    name: str | None = Field(None, min_length=1, max_length=200, description="班级名称")
    description: str | None = Field(None, description="班级描述")
    code: str | None = Field(None, max_length=50, description="班级编码")
    max_students: int | None = Field(None, ge=1, description="最大学生数")
    resource_allocation: dict[str, Any] | None = Field(None, description="资源分配")
    class_rules: dict[str, Any] | None = Field(None, description="班级规则")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    schedule: dict[str, Any] | None = Field(None, description="课程表")
    teacher_id: int | None = Field(None, description="教师ID")
    is_active: bool | None = Field(None, description="是否激活")
    status: str | None = Field(None, description="班级状态")


class ClassResponse(ClassBase):
    """班级响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="班级ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int | None = Field(None, description="教师ID")
    is_active: bool = Field(..., description="是否激活")
    status: str = Field(..., description="班级状态")
    current_students: int = Field(..., description="当前学生数")
    completion_rate: float = Field(..., description="完成率")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ClassListResponse(BaseModel):
    """班级列表响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="班级ID")
    name: str = Field(..., description="班级名称")
    code: str | None = Field(None, description="班级编码")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int | None = Field(None, description="教师ID")
    current_students: int = Field(..., description="当前学生数")
    max_students: int = Field(..., description="最大学生数")
    is_active: bool = Field(..., description="是否激活")
    status: str = Field(..., description="班级状态")
    created_at: datetime = Field(..., description="创建时间")
