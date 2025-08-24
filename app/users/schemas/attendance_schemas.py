"""考勤管理相关的Pydantic模型 - 需求2：考勤管理."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class AttendanceRecordCreateRequest(BaseModel):
    """创建考勤记录请求."""

    attendance_date: date = Field(..., description="考勤日期")
    attendance_type: str = Field(..., description="考勤类型：present/absent/late/leave")
    check_in_time: datetime | None = Field(None, description="签到时间")
    check_out_time: datetime | None = Field(None, description="签退时间")
    leave_type: str | None = Field(None, description="请假类型：sick/personal/emergency")
    leave_reason: str | None = Field(None, description="请假原因")
    notes: str | None = Field(None, description="备注信息")
    class_id: int | None = Field(None, description="班级ID")


class AttendanceRecordUpdateRequest(BaseModel):
    """更新考勤记录请求."""

    attendance_type: str | None = Field(None, description="考勤类型：present/absent/late/leave")
    check_in_time: datetime | None = Field(None, description="签到时间")
    check_out_time: datetime | None = Field(None, description="签退时间")
    leave_type: str | None = Field(None, description="请假类型：sick/personal/emergency")
    leave_reason: str | None = Field(None, description="请假原因")
    notes: str | None = Field(None, description="备注信息")


class LeaveApprovalRequest(BaseModel):
    """请假审批请求."""

    approved: bool = Field(..., description="是否批准")
    notes: str | None = Field(None, description="审批备注")


class AttendanceRecordResponse(BaseModel):
    """考勤记录响应."""

    id: int
    student_id: int
    attendance_date: date
    attendance_type: str
    check_in_time: datetime | None
    check_out_time: datetime | None
    leave_type: str | None
    leave_reason: str | None
    leave_approved: bool
    notes: str | None
    class_id: int | None


class AttendanceStatistics(BaseModel):
    """考勤统计."""

    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    leave_days: int
    attendance_rate: float | None = None


class AttendanceListResponse(BaseModel):
    """考勤记录列表响应."""

    items: list[AttendanceRecordResponse]
    total: int
    page: int
    size: int
    pages: int
    statistics: AttendanceStatistics


# ===== 学籍变动管理 =====


class EnrollmentChangeCreateRequest(BaseModel):
    """创建学籍变动请求."""

    change_type: str = Field(
        ...,
        description="变动类型：enrollment/suspension/withdrawal/transfer/graduation",
    )
    change_date: date = Field(..., description="变动日期")
    effective_date: date = Field(..., description="生效日期")
    new_status: str = Field(..., description="变动后状态")
    reason: str = Field(..., description="变动原因")
    approval_notes: str | None = Field(None, description="审批备注")
    supporting_documents: dict[str, Any] = Field(default_factory=dict, description="支持文档")


class EnrollmentChangeResponse(BaseModel):
    """学籍变动记录响应."""

    id: int
    student_id: int
    change_type: str
    change_date: date
    effective_date: date
    previous_status: str | None
    new_status: str
    reason: str
    approved_by: int | None
    approved_at: datetime | None
    approval_notes: str | None


class EnrollmentChangeListResponse(BaseModel):
    """学籍变动记录列表响应."""

    items: list[EnrollmentChangeResponse]
    total: int
    page: int
    size: int
    pages: int


# ===== 收费管理 =====


class BillingRecordCreateRequest(BaseModel):
    """创建收费记录请求."""

    billing_type: str = Field(..., description="收费类型：tuition/material/exam/refund")
    amount: float = Field(..., gt=0, description="金额")
    currency: str = Field(default="CNY", description="货币类型")
    billing_date: date = Field(..., description="收费日期")
    due_date: date | None = Field(None, description="到期日期")
    description: str = Field(..., description="收费描述")
    notes: str | None = Field(None, description="备注信息")


class PaymentProcessRequest(BaseModel):
    """支付处理请求."""

    payment_method: str = Field(..., description="支付方式：cash/card/transfer/alipay/wechat")
    transaction_id: str | None = Field(None, description="交易流水号")


class InvoiceGenerateRequest(BaseModel):
    """发票生成请求."""

    invoice_type: str = Field(default="electronic", description="发票类型：electronic/paper")
    company_name: str | None = Field(None, description="公司名称")
    tax_number: str | None = Field(None, description="税号")
    company_address: str | None = Field(None, description="公司地址")
    company_phone: str | None = Field(None, description="公司电话")
    bank_info: str | None = Field(None, description="银行信息")
    tax_rate: float = Field(default=0.0, ge=0, le=1, description="税率")


class BillingRecordResponse(BaseModel):
    """收费记录响应."""

    id: int
    student_id: int
    billing_type: str
    amount: float
    currency: str
    billing_date: date
    due_date: date | None
    payment_status: str
    payment_method: str | None
    payment_date: datetime | None
    transaction_id: str | None
    description: str
    notes: str | None


class BillingStatistics(BaseModel):
    """收费统计."""

    total_amount: float
    paid_amount: float
    pending_amount: float
    overdue_amount: float


class BillingListResponse(BaseModel):
    """收费记录列表响应."""

    items: list[BillingRecordResponse]
    total: int
    page: int
    size: int
    pages: int
    statistics: BillingStatistics


class InvoiceResponse(BaseModel):
    """发票响应."""

    id: int
    invoice_number: str
    billing_record_id: int
    invoice_date: date
    total_amount: float
    tax_amount: float
    tax_rate: float
    status: str
    company_name: str | None
    tax_number: str | None
