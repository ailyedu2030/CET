"""规则管理相关的Pydantic模型 - 需求8：班级与课程规则管理."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ===== 规则配置相关模型 =====


class RuleConfigurationBase(BaseModel):
    """规则配置基础模型."""

    rule_name: str = Field(..., description="规则名称", max_length=100)
    rule_type: str = Field(
        ...,
        description="规则类型",
        pattern="^(binding|scheduling|capacity|resource)$",
    )
    rule_category: str = Field(
        ...,
        description="规则分类",
        pattern="^(class_binding|classroom_scheduling|teacher_workload)$",
    )
    rule_config: dict[str, Any] = Field(default_factory=dict, description="规则配置参数")
    is_enabled: bool = Field(True, description="是否启用")
    is_strict: bool = Field(True, description="是否严格执行")
    allow_exceptions: bool = Field(False, description="是否允许例外")
    scope_type: str = Field(
        ...,
        description="适用范围类型",
        pattern="^(global|campus|building|classroom_type)$",
    )
    scope_config: dict[str, Any] = Field(default_factory=dict, description="适用范围配置")
    description: str | None = Field(None, description="规则描述")


class RuleConfigurationCreate(RuleConfigurationBase):
    """创建规则配置请求模型."""

    pass


class RuleConfigurationUpdate(BaseModel):
    """更新规则配置请求模型."""

    rule_config: dict[str, Any] | None = Field(None, description="规则配置参数")
    is_enabled: bool | None = Field(None, description="是否启用")
    is_strict: bool | None = Field(None, description="是否严格执行")
    allow_exceptions: bool | None = Field(None, description="是否允许例外")
    scope_config: dict[str, Any] | None = Field(None, description="适用范围配置")
    description: str | None = Field(None, description="规则描述")


class RuleConfigurationResponse(RuleConfigurationBase):
    """规则配置响应模型."""

    id: int = Field(..., description="规则ID")
    created_by: int = Field(..., description="创建人ID")
    updated_by: int | None = Field(None, description="更新人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ===== 规则验证相关模型 =====


class RuleValidationRequest(BaseModel):
    """规则验证请求模型."""

    rule_id: int = Field(..., description="规则ID")
    target_type: str = Field(
        ...,
        description="目标类型",
        pattern="^(class|teacher|classroom|course)$",
    )
    target_id: int = Field(..., description="目标ID")
    context: dict[str, Any] = Field(default_factory=dict, description="验证上下文")


class RuleViolation(BaseModel):
    """规则违规模型."""

    rule: str = Field(..., description="违规规则")
    message: str = Field(..., description="违规消息")
    severity: str = Field(
        "medium",
        description="严重程度",
        pattern="^(low|medium|high|critical)$",
    )
    details: dict[str, Any] = Field(default_factory=dict, description="违规详情")


class RuleValidationResponse(BaseModel):
    """规则验证响应模型."""

    is_compliant: bool = Field(..., description="是否合规")
    rule_name: str | None = Field(None, description="规则名称")
    violations: list[RuleViolation] = Field(default_factory=list, description="违规列表")
    rule_count: int = Field(0, description="违规数量")
    severity: str = Field(
        "none",
        description="整体严重程度",
        pattern="^(none|low|medium|high|critical)$",
    )
    message: str = Field(..., description="验证消息")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")


# ===== 规则执行日志相关模型 =====


class RuleExecutionLogResponse(BaseModel):
    """规则执行日志响应模型."""

    id: int = Field(..., description="日志ID")
    rule_id: int = Field(..., description="规则ID")
    execution_type: str = Field(..., description="执行类型")
    execution_result: str = Field(..., description="执行结果")
    execution_context: dict[str, Any] = Field(..., description="执行上下文")
    violation_details: dict[str, Any] | None = Field(None, description="违规详情")
    resolution_action: str | None = Field(None, description="解决措施")
    target_type: str = Field(..., description="目标类型")
    target_id: int = Field(..., description="目标ID")
    executed_by: int | None = Field(None, description="执行人ID")
    execution_time: datetime = Field(..., description="执行时间")

    class Config:
        from_attributes = True


# ===== 规则监控相关模型 =====


class RuleMonitoringCreate(BaseModel):
    """创建规则监控请求模型."""

    rule_id: int = Field(..., description="规则ID")
    monitoring_period: str = Field(
        ...,
        description="监控周期",
        pattern="^(daily|weekly|monthly)$",
    )
    period_start: datetime = Field(..., description="周期开始时间")
    period_end: datetime = Field(..., description="周期结束时间")


class RuleMonitoringResponse(BaseModel):
    """规则监控响应模型."""

    id: int = Field(..., description="监控ID")
    rule_id: int = Field(..., description="规则ID")
    monitoring_period: str = Field(..., description="监控周期")
    period_start: datetime = Field(..., description="周期开始时间")
    period_end: datetime = Field(..., description="周期结束时间")
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    violation_count: int = Field(..., description="违规次数")
    exception_count: int = Field(..., description="例外次数")
    effectiveness_score: float | None = Field(None, description="效果评分")
    compliance_rate: float = Field(..., description="合规率")
    optimization_suggestions: dict[str, Any] | None = Field(None, description="优化建议")
    created_by: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ===== 规则统计相关模型 =====


class RuleStatisticsResponse(BaseModel):
    """规则统计响应模型."""

    rule_id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    violation_count: int = Field(..., description="违规次数")
    exception_count: int = Field(..., description="例外次数")
    compliance_rate: float = Field(..., description="合规率")
    effectiveness_score: float | None = Field(None, description="效果评分")
    last_execution: datetime | None = Field(None, description="最后执行时间")
    trend: str = Field(
        "stable",
        description="趋势",
        pattern="^(improving|stable|declining)$",
    )


class RuleOptimizationSuggestion(BaseModel):
    """规则优化建议模型."""

    type: str = Field(..., description="建议类型")
    priority: str = Field(
        ...,
        description="优先级",
        pattern="^(low|medium|high|critical)$",
    )
    message: str = Field(..., description="建议消息")
    action: str = Field(..., description="建议操作")
    expected_impact: str | None = Field(None, description="预期影响")


class RuleOptimizationResponse(BaseModel):
    """规则优化响应模型."""

    rule_id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    current_score: float = Field(..., description="当前评分")
    suggestions: list[RuleOptimizationSuggestion] = Field(..., description="优化建议列表")
    generated_at: datetime = Field(..., description="生成时间")
    total_suggestions: int = Field(..., description="建议总数")


# ===== 批量操作相关模型 =====


class BatchRuleValidationRequest(BaseModel):
    """批量规则验证请求模型."""

    validations: list[RuleValidationRequest] = Field(..., description="验证请求列表")
    stop_on_first_violation: bool = Field(False, description="遇到第一个违规时停止")


class BatchRuleValidationResponse(BaseModel):
    """批量规则验证响应模型."""

    total_validations: int = Field(..., description="总验证数")
    successful_validations: int = Field(..., description="成功验证数")
    violation_count: int = Field(..., description="违规总数")
    results: list[RuleValidationResponse] = Field(..., description="验证结果列表")
    overall_compliance: bool = Field(..., description="整体合规性")
    summary: dict[str, Any] = Field(..., description="汇总信息")


# ===== 规则模板相关模型 =====


class RuleTemplateResponse(BaseModel):
    """规则模板响应模型."""

    template_name: str = Field(..., description="模板名称")
    template_type: str = Field(..., description="模板类型")
    description: str = Field(..., description="模板描述")
    default_config: dict[str, Any] = Field(..., description="默认配置")
    required_fields: list[str] = Field(..., description="必填字段")
    optional_fields: list[str] = Field(..., description="可选字段")
    examples: list[dict[str, Any]] = Field(default_factory=list, description="配置示例")
