"""班级管理相关的Pydantic schemas定义."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClassBase(BaseModel):
    """班级基础信息schema."""

    name: str = Field(..., min_length=1, max_length=200, description="班级名称")
    description: str | None = Field(None, description="班级描述")
    code: str | None = Field(None, max_length=50, description="班级编码")
    max_students: int = Field(50, ge=1, le=200, description="最大学生数")
    resource_allocation: dict[str, Any] = Field(default_factory=dict, description="资源分配")
    class_rules: dict[str, Any] = Field(default_factory=dict, description="班级规则")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
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
    max_students: int | None = Field(None, ge=1, le=200, description="最大学生数")
    resource_allocation: dict[str, Any] | None = Field(None, description="资源分配")
    class_rules: dict[str, Any] | None = Field(None, description="班级规则")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
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


class ClassBatchCreate(BaseModel):
    """批量创建班级schema."""

    course_id: int = Field(..., description="课程ID")
    teacher_id: int | None = Field(None, description="教师ID")
    class_prefix: str = Field(..., min_length=1, max_length=50, description="班级名称前缀")
    class_count: int = Field(..., ge=1, le=20, description="创建班级数量")
    max_students_per_class: int = Field(50, ge=1, le=200, description="每班最大学生数")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    schedule_template: dict[str, Any] = Field(default_factory=dict, description="课程表模板")


class ClassAssignmentRequest(BaseModel):
    """班级分配请求schema."""

    class_id: int = Field(..., description="班级ID")
    teacher_id: int = Field(..., description="教师ID")
    force_assign: bool = Field(False, description="是否强制分配（忽略冲突检测）")
    assignment_reason: str | None = Field(None, description="分配原因")


class ClassAssignmentResponse(BaseModel):
    """班级分配响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分配ID")
    class_id: int = Field(..., description="班级ID")
    teacher_id: int = Field(..., description="教师ID")
    assigned_at: datetime = Field(..., description="分配时间")
    assigned_by: int = Field(..., description="分配者ID")
    is_active: bool = Field(..., description="是否激活")
    assignment_reason: str | None = Field(None, description="分配原因")


class StudentEnrollmentRequest(BaseModel):
    """学生选课请求schema."""

    class_id: int = Field(..., description="班级ID")
    student_id: int = Field(..., description="学生ID")
    enrollment_type: str = Field("normal", description="选课类型")
    enrollment_reason: str | None = Field(None, description="选课原因")


class StudentEnrollmentResponse(BaseModel):
    """学生选课响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="选课ID")
    class_id: int = Field(..., description="班级ID")
    student_id: int = Field(..., description="学生ID")
    enrollment_status: str = Field(..., description="选课状态")
    enrolled_at: datetime = Field(..., description="选课时间")
    attendance_rate: float = Field(..., description="出勤率")
    average_score: float = Field(..., description="平均成绩")


class ClassConflictCheck(BaseModel):
    """班级冲突检测schema."""

    class_id: int | None = Field(None, description="班级ID（更新时需要）")
    teacher_id: int = Field(..., description="教师ID")
    course_id: int = Field(..., description="课程ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    schedule: dict[str, Any] = Field(..., description="课程表")


class ConflictCheckResult(BaseModel):
    """冲突检测结果schema."""

    has_conflict: bool = Field(..., description="是否存在冲突")
    conflict_type: str | None = Field(None, description="冲突类型")
    conflict_details: list[dict[str, Any]] = Field(default_factory=list, description="冲突详情")
    suggestions: list[str] = Field(default_factory=list, description="解决建议")


class ClassStatistics(BaseModel):
    """班级统计信息schema."""

    class_id: int = Field(..., description="班级ID")
    total_students: int = Field(..., description="学生总数")
    active_students: int = Field(..., description="活跃学生数")
    average_attendance: float = Field(..., description="平均出勤率")
    average_score: float = Field(..., description="平均成绩")
    completion_rate: float = Field(..., description="完成率")
    progress_distribution: dict[str, int] = Field(default_factory=dict, description="进度分布")
    performance_metrics: dict[str, float] = Field(default_factory=dict, description="表现指标")
