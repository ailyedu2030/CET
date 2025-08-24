"""用户管理相关的SQLAlchemy模型定义."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel
from app.shared.models.enums import UserType

if TYPE_CHECKING:
    from app.training.models.training_models import (
        TrainingParameterTemplate,
        TrainingTask,
        TrainingTaskSubmission,
    )
    from app.users.models.permission_models import LoginSession, Role


class User(BaseModel):
    """用户基础模型 - 支持三种用户类型."""

    __tablename__ = "users"

    # 基础信息
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名",
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱地址",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希值",
    )
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType),
        nullable=False,
        index=True,
        comment="用户类型",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已验证",
    )

    # 登录统计
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )
    login_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="登录次数",
    )

    # 关系
    student_profile: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    teacher_profile: Mapped["TeacherProfile"] = relationship(
        "TeacherProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    registration_applications: Mapped[list["RegistrationApplication"]] = relationship(
        "RegistrationApplication",
        foreign_keys="RegistrationApplication.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 权限系统关系
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
    )
    login_sessions: Mapped[list["LoginSession"]] = relationship(
        "LoginSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 训练工坊关系 (需求15)
    training_parameter_templates: Mapped[list["TrainingParameterTemplate"]] = relationship(
        "TrainingParameterTemplate",
        foreign_keys="TrainingParameterTemplate.created_by",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    training_tasks: Mapped[list["TrainingTask"]] = relationship(
        "TrainingTask",
        foreign_keys="TrainingTask.teacher_id",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    training_task_submissions: Mapped[list["TrainingTaskSubmission"]] = relationship(
        "TrainingTaskSubmission",
        foreign_keys="TrainingTaskSubmission.student_id",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """用户模型字符串表示."""
        return f"<User(id={self.id}, username='{self.username}', type={self.user_type})>"


class StudentProfile(BaseModel):
    """学生档案模型 - 11项基础信息."""

    __tablename__ = "student_profiles"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="用户ID",
    )

    # 基础信息（需求要求的11项）
    real_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="真实姓名",
    )
    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="年龄",
    )
    gender: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="性别",
    )
    id_number: Mapped[str | None] = mapped_column(
        String(18),
        unique=True,
        nullable=True,
        comment="身份证号",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="手机号码",
    )
    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="紧急联系人姓名",
    )
    emergency_contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="紧急联系人电话",
    )
    school: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="学校",
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="院系",
    )
    major: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="专业",
    )
    grade: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="年级",
    )
    class_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="班级",
    )

    # 学习数据
    current_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="当前能力等级",
    )
    total_study_time: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总学习时长（分钟）",
    )
    total_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="总分数",
    )

    # 需求2：学习状态跟踪和成绩管理
    learning_status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        comment="学习状态：active/inactive/suspended/graduated",
    )
    enrollment_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="入学日期",
    )
    graduation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="毕业日期",
    )
    average_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="平均分数",
    )
    best_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="最高分数",
    )
    total_exercises: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总练习次数",
    )

    # 需求2：家长联系方式
    parent_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="家长姓名",
    )
    parent_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="家长电话",
    )
    parent_email: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="家长邮箱",
    )

    # 扩展信息
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="student_profile",
    )


class TeacherProfile(BaseModel):
    """教师档案模型 - 7项基础信息+资质材料."""

    __tablename__ = "teacher_profiles"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="用户ID",
    )

    # 基础信息（需求要求的7项）
    real_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="真实姓名",
    )
    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="年龄",
    )
    gender: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="性别",
    )
    title: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="职称",
    )
    subject: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="所授学科",
    )
    introduction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="自我介绍",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="联系电话",
    )

    # 资质材料（3类文件）
    teacher_certificate: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="教师证扫描件路径",
    )
    qualification_certificates: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="职业资格证书列表",
    )
    honor_certificates: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="荣誉证书列表",
    )

    # 教学数据统计
    total_teaching_hours: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总教学时长",
    )
    student_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="学生人数",
    )
    average_rating: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="平均评分",
    )

    # 需求2：教学状态跟踪
    teaching_status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        comment="教学状态：active/inactive/suspended/retired",
    )
    hire_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="入职日期",
    )
    contract_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="合同结束日期",
    )
    monthly_hours: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="月度课时统计",
    )
    total_evaluations: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="评价总数",
    )

    # 需求2：薪酬管理
    hourly_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="课时费（元/小时）",
    )
    monthly_salary: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="月度薪资",
    )
    total_salary_paid: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="累计已发薪资",
    )
    last_salary_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后发薪日期",
    )

    # 需求2：资质审核
    qualification_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="资质状态：pending/approved/rejected/expired",
    )
    last_review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后审核日期",
    )
    next_review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次审核日期（每年一次）",
    )
    qualification_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="资质审核备注",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="teacher_profile",
    )


class RegistrationApplication(BaseModel):
    """注册申请模型 - 支持审核流程."""

    __tablename__ = "registration_applications"

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="申请用户ID",
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审核员ID",
    )

    # 申请信息
    application_type: Mapped[UserType] = mapped_column(
        Enum(UserType),
        nullable=False,
        comment="申请类型",
    )
    application_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="申请数据",
    )
    submitted_documents: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="提交的文件列表",
    )

    # 审核信息
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="申请状态",
    )
    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="审核备注",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="registration_applications",
    )
    reviewer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reviewer_id],
    )

    def __repr__(self) -> str:
        """注册申请模型字符串表示."""
        return f"<RegistrationApplication(id={self.id}, type={self.application_type}, status={self.status})>"


class AttendanceRecord(BaseModel):
    """考勤记录模型 - 需求2：考勤管理系统."""

    __tablename__ = "attendance_records"

    # 外键
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )
    class_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="班级ID",
    )

    # 考勤信息
    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="考勤日期",
    )
    attendance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="考勤类型：present/absent/late/leave",
    )
    check_in_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="签到时间",
    )
    check_out_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="签退时间",
    )

    # 请假信息
    leave_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="请假类型：sick/personal/emergency",
    )
    leave_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="请假原因",
    )
    leave_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="请假是否批准",
    )
    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="批准人ID",
    )

    # 备注信息
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )
    recorded_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="记录人ID",
    )

    # 关系
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])
    recorder: Mapped["User | None"] = relationship("User", foreign_keys=[recorded_by])

    def __repr__(self) -> str:
        """考勤记录模型字符串表示."""
        return f"<AttendanceRecord(id={self.id}, student_id={self.student_id}, date={self.attendance_date}, type={self.attendance_type})>"


class StudentEnrollmentChange(BaseModel):
    """学籍变动记录模型 - 需求2：学籍变动管理."""

    __tablename__ = "student_enrollment_changes"

    # 外键
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )

    # 变动信息
    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变动类型：enrollment/suspension/withdrawal/transfer/graduation",
    )
    change_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="变动日期",
    )
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="生效日期",
    )

    # 变动详情
    previous_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="变动前状态",
    )
    new_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变动后状态",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="变动原因",
    )

    # 审批信息
    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审批人ID",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审批时间",
    )
    approval_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="审批备注",
    )

    # 相关文档
    supporting_documents: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="支持文档列表",
    )

    # 关系
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:
        """学籍变动记录模型字符串表示."""
        return f"<StudentEnrollmentChange(id={self.id}, student_id={self.student_id}, type={self.change_type}, date={self.change_date})>"


class BillingRecord(BaseModel):
    """收费记录模型 - 需求2：收费管理系统."""

    __tablename__ = "billing_records"

    # 外键
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )

    # 收费信息
    billing_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="收费类型：tuition/material/exam/refund",
    )
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="金额",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="CNY",
        nullable=False,
        comment="货币类型",
    )
    billing_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="收费日期",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="到期日期",
    )

    # 支付信息
    payment_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="支付状态：pending/paid/overdue/cancelled",
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="支付方式：cash/card/transfer/alipay/wechat",
    )
    payment_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="支付时间",
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="交易流水号",
    )

    # 描述信息
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="收费描述",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    # 操作信息
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID",
    )
    processed_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="处理人ID",
    )

    # 关系
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    processor: Mapped["User | None"] = relationship("User", foreign_keys=[processed_by])
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice", back_populates="billing_record", uselist=False
    )

    def __repr__(self) -> str:
        """收费记录模型字符串表示."""
        return f"<BillingRecord(id={self.id}, student_id={self.student_id}, type={self.billing_type}, amount={self.amount})>"


class Invoice(BaseModel):
    """发票模型 - 需求2：发票生成功能."""

    __tablename__ = "invoices"

    # 外键
    billing_record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("billing_records.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="收费记录ID",
    )

    # 发票信息
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="发票号码",
    )
    invoice_type: Mapped[str] = mapped_column(
        String(20),
        default="electronic",
        nullable=False,
        comment="发票类型：electronic/paper",
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="开票日期",
    )

    # 开票信息
    company_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="公司名称",
    )
    tax_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="税号",
    )
    company_address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="公司地址",
    )
    company_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="公司电话",
    )
    bank_info: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="银行信息",
    )

    # 发票内容
    total_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="发票总金额",
    )
    tax_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="税额",
    )
    tax_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="税率",
    )

    # 状态信息
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        comment="发票状态：draft/issued/cancelled",
    )
    issued_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="开票人ID",
    )
    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开票时间",
    )

    # 文件信息
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="发票文件路径",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小（字节）",
    )

    # 关系
    billing_record: Mapped["BillingRecord"] = relationship(
        "BillingRecord", back_populates="invoice"
    )
    issuer: Mapped["User | None"] = relationship("User", foreign_keys=[issued_by])

    def __repr__(self) -> str:
        """发票模型字符串表示."""
        return f"<Invoice(id={self.id}, number={self.invoice_number}, amount={self.total_amount})>"


class TeachingRecord(BaseModel):
    """教学记录模型 - 需求2：教学状态跟踪."""

    __tablename__ = "teaching_records"

    # 外键
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
    )

    # 课程信息
    course_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="课程名称",
    )
    course_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="课程类型：regular/makeup/trial/workshop",
    )
    teaching_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="授课时长（分钟）",
    )
    student_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="学生数量",
    )

    # 时间信息
    teaching_start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="教学开始时间",
    )
    teaching_end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="教学结束时间",
    )

    # 状态和评价
    teaching_status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",
        nullable=False,
        comment="教学状态：scheduled/ongoing/completed/cancelled",
    )
    teaching_rating: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="教学评分（1-5分）",
    )

    # 反馈和指标
    student_feedback: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="学生反馈",
    )
    effectiveness_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="教学效果指标",
    )

    # 备注信息
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID",
    )

    # 关系
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        """教学记录模型字符串表示."""
        return f"<TeachingRecord(id={self.id}, teacher_id={self.teacher_id}, course={self.course_name}, status={self.teaching_status})>"


class SalaryRecord(BaseModel):
    """薪酬记录模型 - 需求2：薪酬管理系统."""

    __tablename__ = "salary_records"

    # 外键
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
    )

    # 薪酬类型和周期
    salary_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="薪酬类型：base_salary/hourly_fee/bonus/allowance",
    )
    calculation_period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="计算周期开始",
    )
    calculation_period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="计算周期结束",
    )

    # 薪酬计算
    base_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="基础金额",
    )
    teaching_hours: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="课时数",
    )
    hourly_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="课时单价",
    )
    bonus_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="奖金金额",
    )
    deduction_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="扣除金额",
    )
    net_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="实发金额",
    )

    # 发放状态
    payment_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="发放状态：pending/paid/cancelled",
    )
    payment_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="发放时间",
    )

    # 审批信息
    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审批人ID",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审批时间",
    )

    # 备注信息
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID",
    )

    # 关系
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        """薪酬记录模型字符串表示."""
        return f"<SalaryRecord(id={self.id}, teacher_id={self.teacher_id}, type={self.salary_type}, amount={self.net_amount})>"


class QualificationReview(BaseModel):
    """资质审核模型 - 需求2：资质审核流程."""

    __tablename__ = "qualification_reviews"

    # 外键
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
    )

    # 审核信息
    review_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="审核类型：annual_review/certification/renewal",
    )
    review_cycle: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="审核周期：annual/biannual/triennial",
    )
    submission_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="提交日期",
    )

    # 提交材料
    submitted_materials: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="提交材料",
    )

    # 审核状态和结果
    review_status: Mapped[str] = mapped_column(
        String(20),
        default="submitted",
        nullable=False,
        comment="审核状态：submitted/under_review/approved/rejected",
    )
    review_result: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="审核结果：pass/conditional_pass/fail",
    )
    review_comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="审核意见",
    )

    # 有效期
    valid_from: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="有效期开始",
    )
    valid_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="有效期结束",
    )

    # 审核人员
    reviewer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审核人员ID",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )

    # 提交人员
    submitted_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="提交人员ID",
    )

    # 关系
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewer_id])
    submitter: Mapped["User | None"] = relationship("User", foreign_keys=[submitted_by])

    def __repr__(self) -> str:
        """资质审核模型字符串表示."""
        return f"<QualificationReview(id={self.id}, teacher_id={self.teacher_id}, type={self.review_type}, status={self.review_status})>"
