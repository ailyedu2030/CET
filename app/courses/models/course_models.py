"""课程管理相关的SQLAlchemy模型定义."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
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
from app.shared.models.enums import CourseShareLevel, CourseStatus, DifficultyLevel

if TYPE_CHECKING:
    from app.users.models import User


class Course(BaseModel):
    """课程模型 - 支持全生命周期管理."""

    __tablename__ = "courses"

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="课程名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="课程描述",
    )
    code: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="课程编码",
    )

    # 课程内容
    syllabus: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="教学大纲",
    )
    teaching_plan: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="教学计划",
    )
    resource_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="资源配置",
    )

    # 状态管理（筹备中→审核中→已上线→已归档）
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus),
        default=CourseStatus.PREPARING,
        nullable=False,
        index=True,
        comment="课程状态",
    )

    # 共享级别（私有/班级内共享/全校共享）
    share_level: Mapped[CourseShareLevel] = mapped_column(
        Enum(CourseShareLevel),
        default=CourseShareLevel.PRIVATE,
        nullable=False,
        comment="共享级别",
    )

    # 课程属性
    total_hours: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总学时",
    )
    target_audience: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="适用对象",
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel),
        default=DifficultyLevel.ELEMENTARY,
        nullable=False,
        comment="难度等级",
    )

    # 版本控制
    version: Mapped[str] = mapped_column(
        String(20),
        default="1.0",
        nullable=False,
        comment="课程版本",
    )
    parent_course_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        comment="模板课程ID",
    )

    # 审计信息
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )
    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审核者ID",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )

    # 统计数据
    student_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="学生人数",
    )
    completion_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="完成率",
    )

    # 关系
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    approver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[approved_by],
    )
    parent_course: Mapped["Course"] = relationship(
        "Course",
        remote_side="Course.id",
    )
    classes: Mapped[list["Class"]] = relationship(
        "Class",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """课程模型字符串表示."""
        return f"<Course(id={self.id}, name='{self.name}', status={self.status})>"


class Class(BaseModel):
    """班级模型 - 支持资源配置和规则管理."""

    __tablename__ = "classes"

    # 外键
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="课程ID",
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="教师ID",
    )

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="班级名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="班级描述",
    )
    code: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="班级编码",
    )

    # 班级配置
    max_students: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="最大学生数",
    )
    resource_allocation: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="资源分配",
    )
    class_rules: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="班级规则",
    )

    # 时间配置
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始日期",
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="结束日期",
    )
    schedule: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="课程表",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="preparing",
        nullable=False,
        comment="班级状态",
    )

    # 统计数据
    current_students: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前学生数",
    )
    completion_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="完成率",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="classes",
    )
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys=[teacher_id],
    )

    def __repr__(self) -> str:
        """班级模型字符串表示."""
        return f"<Class(id={self.id}, name='{self.name}', course_id={self.course_id})>"


class ClassResourceHistory(BaseModel):
    """班级资源变更历史模型 - 需求4：班级资源变更历史记录."""

    __tablename__ = "class_resource_history"

    # 外键
    class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        comment="班级ID",
    )
    changed_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="变更人ID",
    )

    # 变更信息
    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变更类型：create/update/delete/allocate",
    )
    old_allocation: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="变更前资源配置",
    )
    new_allocation: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="变更后资源配置",
    )
    change_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="变更原因",
    )

    # 时间信息
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="变更时间",
    )

    # 关系
    class_obj: Mapped["Class"] = relationship(
        "Class",
        foreign_keys=[class_id],
    )
    changer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[changed_by],
    )

    def __repr__(self) -> str:
        """班级资源变更历史模型字符串表示."""
        return f"<ClassResourceHistory(id={self.id}, class_id={self.class_id}, type={self.change_type})>"


class Resource(BaseModel):
    """资源模型 - 支持多种资源类型."""

    __tablename__ = "resources"

    # 外键
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="课程ID",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="资源名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="资源描述",
    )
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="资源类型",
    )

    # 资源配置
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="文件路径",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小",
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="文件类型",
    )
    url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="资源URL",
    )

    # 资源元数据
    resource_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="资源元数据",
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="资源标签",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否公开",
    )

    # 统计数据
    download_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="下载次数",
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="查看次数",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="resources",
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
    )

    def __repr__(self) -> str:
        """资源模型字符串表示."""
        return f"<Resource(id={self.id}, name='{self.name}', type={self.resource_type})>"


class Syllabus(BaseModel):
    """教学大纲模型 - 支持结构化教学计划."""

    __tablename__ = "syllabi"

    # 外键
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="课程ID",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    # 基础信息
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="大纲标题",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="大纲描述",
    )
    version: Mapped[str] = mapped_column(
        String(20),
        default="1.0",
        nullable=False,
        comment="大纲版本",
    )

    # 教学内容
    objectives: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="教学目标",
    )
    chapters: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="章节内容",
    )
    assessments: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="考核方式",
    )
    resources: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="参考资料",
    )

    # 时间安排
    total_weeks: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总周数",
    )
    total_hours: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="总学时",
    )
    schedule: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="进度安排",
    )

    # 状态信息
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否审核通过",
    )
    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审核者ID",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    approver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[approved_by],
    )

    def __repr__(self) -> str:
        """教学大纲模型字符串表示."""
        return f"<Syllabus(id={self.id}, title='{self.title}', course_id={self.course_id})>"


class CourseVersion(BaseModel):
    """课程版本历史模型 - 支持版本控制和回滚."""

    __tablename__ = "course_versions"

    # 外键
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="课程ID",
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    # 版本信息
    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="版本号",
    )
    version_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="版本名称",
    )
    change_log: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="版本变更说明",
    )

    # 快照数据
    snapshot_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="课程数据快照",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为当前激活版本",
    )
    is_backup: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为备份版本",
    )

    # 关系
    course: Mapped["Course"] = relationship("Course")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        """课程版本模型字符串表示."""
        return (
            f"<CourseVersion(id={self.id}, course_id={self.course_id}, version='{self.version}')>"
        )


class CourseTemplate(BaseModel):
    """课程模板模型 - 支持课程快速创建."""

    __tablename__ = "course_templates"

    # 外键
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )
    source_course_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        comment="源课程ID",
    )

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="模板名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述",
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="模板分类",
    )

    # 模板配置
    template_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="模板数据",
    )
    default_settings: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="默认设置",
    )

    # 使用统计
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="使用次数",
    )

    # 状态信息
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否公开",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    # 关系
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    source_course: Mapped["Course"] = relationship("Course", foreign_keys=[source_course_id])

    def __repr__(self) -> str:
        """课程模板模型字符串表示."""
        return f"<CourseTemplate(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"


class TeacherCoursePermission(BaseModel):
    """教师课程权限模型 - 需求5：多教师协作权限边界."""

    __tablename__ = "teacher_course_permissions"

    # 外键
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="教师ID",
    )
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="课程ID",
    )

    # 分配信息
    assigned_modules: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="分配的模块/章节",
    )
    permission_scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="权限范围：full_access/module_edit/module_only/view_all",
    )

    # 权限详情
    can_edit_content: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否可以编辑内容",
    )
    can_view_all_modules: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否可以查看所有模块",
    )
    can_manage_students: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否可以管理学生",
    )
    can_grade_assignments: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否可以评分作业",
    )

    # 关系
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys=[teacher_id],
    )
    course: Mapped["Course"] = relationship(
        "Course",
        foreign_keys=[course_id],
    )

    def __repr__(self) -> str:
        """教师课程权限模型字符串表示."""
        return f"<TeacherCoursePermission(teacher_id={self.teacher_id}, course_id={self.course_id}, scope={self.permission_scope})>"


class RuleConfiguration(BaseModel):
    """规则配置模型 - 需求8：班级与课程规则管理."""

    __tablename__ = "rule_configurations"

    # 规则基础信息
    rule_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="规则名称",
    )
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="规则类型：binding/scheduling/capacity/resource",
    )
    rule_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="规则分类：class_binding/classroom_scheduling/teacher_workload",
    )

    # 规则配置
    rule_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="规则配置参数",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )
    is_strict: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否严格执行",
    )
    allow_exceptions: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否允许例外",
    )

    # 适用范围
    scope_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="适用范围类型：global/campus/building/classroom_type",
    )
    scope_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="适用范围配置",
    )

    # 管理信息
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="创建人ID",
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="更新人ID",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="规则描述",
    )


class RuleExecutionLog(BaseModel):
    """规则执行日志模型 - 需求8：规则监控与维护."""

    __tablename__ = "rule_execution_logs"

    # 外键
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rule_configurations.id", ondelete="CASCADE"),
        nullable=False,
        comment="规则ID",
    )

    # 执行信息
    execution_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="执行类型：validation/enforcement/monitoring",
    )
    execution_result: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="执行结果：success/violation/error/warning",
    )
    execution_context: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="执行上下文",
    )

    # 违规信息
    violation_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="违规详情",
    )
    resolution_action: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="解决措施",
    )

    # 关联对象
    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="目标类型：class/teacher/classroom/course",
    )
    target_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="目标ID",
    )

    # 执行人
    executed_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="执行人ID",
    )
    execution_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="执行时间",
    )


class RuleMonitoring(BaseModel):
    """规则监控模型 - 需求8：规则监控与维护."""

    __tablename__ = "rule_monitoring"

    # 外键
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rule_configurations.id", ondelete="CASCADE"),
        nullable=False,
        comment="规则ID",
    )

    # 监控周期
    monitoring_period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="监控周期：daily/weekly/monthly",
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="周期开始时间",
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="周期结束时间",
    )

    # 监控统计
    total_executions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总执行次数",
    )
    successful_executions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="成功执行次数",
    )
    violation_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="违规次数",
    )
    exception_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="例外次数",
    )

    # 效果评估
    effectiveness_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="效果评分（0-100）",
    )
    compliance_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="合规率（0-1）",
    )

    # 优化建议
    optimization_suggestions: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="优化建议",
    )

    # 创建信息
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="创建人ID",
    )


class RuleExemptionRequest(BaseModel):
    """规则豁免申请模型 - 需求5：特殊情况规则豁免."""

    __tablename__ = "rule_exemption_requests"

    # 外键
    rule_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("rule_configurations.id", ondelete="CASCADE"),
        nullable=True,
        comment="规则ID",
    )
    course_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        comment="课程ID",
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="教师ID",
    )
    requested_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="申请人ID",
    )
    approved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审批人ID",
    )

    # 豁免信息
    exemption_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="豁免类型：workload/time_conflict/qualification/classroom",
    )
    exemption_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="豁免原因",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="状态：pending/approved/rejected",
    )
    approval_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="审批备注",
    )

    # 时间信息
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="申请时间",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审批时间",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
        foreign_keys=[course_id],
    )
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys=[teacher_id],
    )
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by],
    )
    approver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[approved_by],
    )

    def __repr__(self) -> str:
        """规则豁免申请模型字符串表示."""
        return f"<RuleExemptionRequest(id={self.id}, type={self.exemption_type}, status={self.status})>"


class CourseAssignmentHistory(BaseModel):
    """课程分配历史模型 - 需求5：课程分配历史记录."""

    __tablename__ = "course_assignment_history"

    # 外键
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="课程ID",
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="教师ID",
    )
    operated_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="操作人ID",
    )

    # 操作信息
    operation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="操作类型：course_assignment/course_multiple_classes/course_multiple_teachers",
    )
    operation_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="操作描述",
    )
    operation_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="操作数据",
    )

    # 时间信息
    operated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="操作时间",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
        foreign_keys=[course_id],
    )
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys=[teacher_id],
    )
    operator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[operated_by],
    )

    def __repr__(self) -> str:
        """课程分配历史模型字符串表示."""
        return f"<CourseAssignmentHistory(id={self.id}, course_id={self.course_id}, type={self.operation_type})>"
