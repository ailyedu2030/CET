"""用户注册相关的Pydantic模式定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator

from app.shared.models.enums import UserType


class StudentRegistrationRequest(BaseModel):
    """学生注册请求模式 - 11项必要信息."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # 基本账户信息
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: EmailStr = Field(..., description="邮箱地址")

    # 学生档案信息（需求要求的11项）
    real_name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    age: int | None = Field(None, ge=16, le=100, description="年龄")
    gender: str | None = Field(None, pattern=r"^(男|女|其他)$", description="性别")
    id_number: str | None = Field(None, min_length=18, max_length=18, description="身份证号")
    phone: str | None = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号码")
    emergency_contact_name: str | None = Field(None, max_length=50, description="紧急联系人姓名")
    emergency_contact_phone: str | None = Field(
        None, pattern=r"^1[3-9]\d{9}$", description="紧急联系人电话"
    )
    school: str | None = Field(None, max_length=100, description="学校")
    department: str | None = Field(None, max_length=100, description="院系")
    major: str | None = Field(None, max_length=100, description="专业")
    grade: str | None = Field(None, max_length=20, description="年级")
    class_name: str | None = Field(None, max_length=50, description="班级")

    @validator("id_number")
    def validate_id_number(cls, v: str | None) -> str | None:
        """验证身份证号格式."""
        if v is None:
            return v

        if len(v) != 18:
            raise ValueError("身份证号必须为18位")

        # 简单的身份证号格式验证
        if not v[:17].isdigit() or v[-1] not in "0123456789Xx":
            raise ValueError("身份证号格式不正确")

        return v


class TeacherRegistrationRequest(BaseModel):
    """教师注册请求模式 - 7项基础信息+资质材料."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # 基本账户信息
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: EmailStr = Field(..., description="邮箱地址")

    # 教师档案信息（需求要求的7项）
    real_name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    age: int | None = Field(None, ge=22, le=100, description="年龄")
    gender: str | None = Field(None, pattern=r"^(男|女|其他)$", description="性别")
    title: str | None = Field(None, max_length=50, description="职称")
    subject: str | None = Field(None, max_length=100, description="所授学科")
    introduction: str | None = Field(None, max_length=1000, description="自我介绍")
    phone: str | None = Field(None, pattern=r"^1[3-9]\d{9}$", description="联系电话")

    # 资质材料文件（3类文件）
    teacher_certificate: str | None = Field(None, max_length=500, description="教师证扫描件路径")
    qualification_certificates: list[str] = Field(
        default_factory=list, description="职业资格证书文件路径列表"
    )
    honor_certificates: list[str] = Field(default_factory=list, description="荣誉证书文件路径列表")


class RegistrationApplicationResponse(BaseModel):
    """注册申请响应模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="申请ID")
    user_id: int = Field(..., description="用户ID")
    application_type: UserType = Field(..., description="申请类型")
    status: str = Field(..., description="申请状态")
    submitted_at: datetime = Field(..., description="提交时间")
    reviewed_at: datetime | None = Field(None, description="审核时间")
    reviewer_id: int | None = Field(None, description="审核员ID")
    review_notes: str | None = Field(None, description="审核备注")


class RegistrationApplicationDetail(BaseModel):
    """注册申请详情模式."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="申请ID")
    user_id: int = Field(..., description="用户ID")
    application_type: UserType = Field(..., description="申请类型")
    application_data: dict[str, Any] = Field(..., description="申请数据")
    submitted_documents: dict[str, Any] = Field(..., description="提交的文件列表")
    status: str = Field(..., description="申请状态")
    submitted_at: datetime = Field(..., description="提交时间")
    reviewed_at: datetime | None = Field(None, description="审核时间")
    reviewer_id: int | None = Field(None, description="审核员ID")
    review_notes: str | None = Field(None, description="审核备注")

    # 申请人信息
    username: str = Field(..., description="申请人用户名")
    email: EmailStr = Field(..., description="申请人邮箱")


class ApplicationReviewRequest(BaseModel):
    """申请审核请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    action: str = Field(
        ...,
        pattern=r"^(approve|reject)$",
        description="审核动作：approve-通过，reject-驳回",
    )
    review_notes: str | None = Field(None, max_length=500, description="审核备注")


class BatchReviewRequest(BaseModel):
    """批量审核请求模式."""

    model_config = ConfigDict(validate_assignment=True)

    application_ids: list[int] = Field(
        description="申请ID列表（最多20条）", min_length=1, max_length=20
    )
    action: str = Field(
        ...,
        pattern=r"^(approve|reject)$",
        description="审核动作：approve-通过，reject-驳回",
    )
    review_notes: str | None = Field(None, max_length=500, description="审核备注")


class RegistrationStatusResponse(BaseModel):
    """注册状态查询响应模式."""

    model_config = ConfigDict(from_attributes=True)

    application_id: int = Field(..., description="申请ID")
    status: str = Field(..., description="申请状态")
    status_description: str = Field(..., description="状态描述")
    submitted_at: datetime = Field(..., description="提交时间")
    reviewed_at: datetime | None = Field(None, description="审核时间")
    estimated_review_time: str | None = Field(None, description="预计审核时间")


class ApplicationListFilter(BaseModel):
    """申请列表过滤器模式."""

    model_config = ConfigDict(validate_assignment=True)

    application_type: UserType | None = Field(None, description="申请类型")
    status: str | None = Field(None, description="申请状态")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")


class ApplicationListResponse(BaseModel):
    """申请列表响应模式."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: list[RegistrationApplicationResponse] = Field(..., description="申请列表")


class RegistrationSuccessResponse(BaseModel):
    """注册成功响应模式."""

    model_config = ConfigDict(from_attributes=True)

    application_id: int = Field(..., description="申请ID")
    message: str = Field(..., description="成功消息")
    estimated_review_time: str = Field(..., description="预计审核时间")
    status_check_url: str = Field(..., description="状态查询URL")
