"""课程分配管理相关的Pydantic schemas定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TeacherWorkloadInfo(BaseModel):
    """教师工作量信息schema."""

    teacher_id: int = Field(..., description="教师ID")
    teacher_name: str = Field(..., description="教师姓名")
    current_classes: int = Field(..., description="当前班级数")
    max_classes: int = Field(5, description="最大班级数")
    total_students: int = Field(..., description="学生总数")
    workload_percentage: float = Field(..., description="工作量百分比")
    available_hours: int = Field(..., description="可用时间（小时）")
    expertise_match: dict[str, float] = Field(default_factory=dict, description="专业匹配度")


class CourseAssignmentRequest(BaseModel):
    """课程分配请求schema."""

    course_id: int = Field(..., description="课程ID")
    teacher_ids: list[int] = Field(..., description="候选教师ID列表")
    priority_factors: dict[str, float] = Field(default_factory=dict, description="优先级因子")
    force_assign: bool = Field(False, description="是否强制分配")
    assignment_reason: str | None = Field(None, description="分配原因")


class CourseAssignmentResponse(BaseModel):
    """课程分配响应schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分配ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    assigned_at: datetime = Field(..., description="分配时间")
    assigned_by: int = Field(..., description="分配者ID")
    is_active: bool = Field(..., description="是否激活")
    assignment_type: str = Field(..., description="分配类型")
    assignment_reason: str | None = Field(None, description="分配原因")
    workload_impact: float = Field(..., description="工作量影响")


class TeacherQualificationCheck(BaseModel):
    """教师资质检查schema."""

    teacher_id: int = Field(..., description="教师ID")
    course_id: int = Field(..., description="课程ID")
    qualification_level: str = Field(..., description="资质等级")
    expertise_areas: list[str] = Field(..., description="专业领域")
    experience_years: int = Field(..., description="教学经验年数")
    certification_status: str = Field(..., description="认证状态")


class QualificationCheckResult(BaseModel):
    """资质检查结果schema."""

    is_qualified: bool = Field(..., description="是否合格")
    qualification_score: float = Field(..., description="资质评分")
    missing_qualifications: list[str] = Field(default_factory=list, description="缺失的资质")
    recommendations: list[str] = Field(default_factory=list, description="建议")
    risk_level: str = Field(..., description="风险等级")


class WorkloadBalanceRequest(BaseModel):
    """工作量平衡请求schema."""

    department_id: int | None = Field(None, description="部门ID")
    teacher_ids: list[int] | None = Field(None, description="教师ID列表")
    semester: str | None = Field(None, description="学期")
    balance_strategy: str = Field("fair", description="平衡策略")
    max_deviation: float = Field(0.2, description="最大偏差")


class WorkloadBalanceResponse(BaseModel):
    """工作量平衡响应schema."""

    teacher_workloads: list[TeacherWorkloadInfo] = Field(..., description="教师工作量信息")
    balance_score: float = Field(..., description="平衡评分")
    recommendations: list[dict[str, Any]] = Field(default_factory=list, description="平衡建议")
    redistribution_plan: list[dict[str, Any]] = Field(
        default_factory=list, description="重分配计划"
    )


class TimeConflictCheck(BaseModel):
    """时间冲突检测schema."""

    teacher_id: int = Field(..., description="教师ID")
    new_schedule: dict[str, Any] = Field(..., description="新课程表")
    conflict_tolerance: int = Field(15, description="冲突容忍度（分钟）")
    check_type: str = Field("strict", description="检查类型")


class TimeConflictResult(BaseModel):
    """时间冲突检测结果schema."""

    has_conflict: bool = Field(..., description="是否存在冲突")
    conflict_count: int = Field(..., description="冲突数量")
    conflict_details: list[dict[str, Any]] = Field(default_factory=list, description="冲突详情")
    resolution_suggestions: list[dict[str, Any]] = Field(
        default_factory=list, description="解决建议"
    )
    alternative_schedules: list[dict[str, Any]] = Field(
        default_factory=list, description="替代时间表"
    )


class AssignmentRuleCheck(BaseModel):
    """分配规则检查schema."""

    assignment_type: str = Field(..., description="分配类型")
    source_id: int = Field(..., description="源ID（班级或课程）")
    target_id: int = Field(..., description="目标ID（教师或学生）")
    rule_exceptions: list[str] = Field(default_factory=list, description="规则例外")


class RuleCheckResult(BaseModel):
    """规则检查结果schema."""

    is_compliant: bool = Field(..., description="是否合规")
    violated_rules: list[str] = Field(default_factory=list, description="违反的规则")
    rule_severity: str = Field(..., description="规则严重性")
    exception_required: bool = Field(..., description="是否需要例外批准")
    approval_process: dict[str, Any] | None = Field(None, description="审批流程")


class AssignmentHistory(BaseModel):
    """分配历史记录schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    assignment_type: str = Field(..., description="分配类型")
    source_id: int = Field(..., description="源ID")
    target_id: int = Field(..., description="目标ID")
    operation: str = Field(..., description="操作类型")
    previous_value: dict[str, Any] | None = Field(None, description="之前的值")
    new_value: dict[str, Any] | None = Field(None, description="新的值")
    operator_id: int = Field(..., description="操作者ID")
    operation_reason: str | None = Field(None, description="操作原因")
    created_at: datetime = Field(..., description="操作时间")


class BulkAssignmentRequest(BaseModel):
    """批量分配请求schema."""

    assignment_type: str = Field(..., description="分配类型")
    assignments: list[dict[str, Any]] = Field(..., description="分配列表")
    batch_reason: str | None = Field(None, description="批量操作原因")
    conflict_handling: str = Field("stop_on_conflict", description="冲突处理策略")
    dry_run: bool = Field(False, description="是否仅进行预演")


class BulkAssignmentResponse(BaseModel):
    """批量分配响应schema."""

    batch_id: str = Field(..., description="批次ID")
    total_assignments: int = Field(..., description="总分配数")
    successful_assignments: int = Field(..., description="成功分配数")
    failed_assignments: int = Field(..., description="失败分配数")
    conflicts_detected: int = Field(..., description="检测到的冲突数")
    assignment_results: list[dict[str, Any]] = Field(
        default_factory=list, description="分配结果详情"
    )
    error_summary: dict[str, int] = Field(default_factory=dict, description="错误汇总")
