"""课程分配模型 - 需求5：活跃的课程分配记录."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.courses.models.course_models import Course
    from app.users.models import User


class AssignmentStatus(str, Enum):
    """分配状态枚举."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CourseAssignment(BaseModel):
    """课程分配模型 - 需求5：活跃的课程分配记录."""

    __tablename__ = "course_assignments"

    # 外键
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID",
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="教师ID",
    )
    assigned_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="分配人ID",
    )

    # 分配信息
    status: Mapped[AssignmentStatus] = mapped_column(
        SQLEnum(AssignmentStatus),
        nullable=False,
        default=AssignmentStatus.PENDING,
        comment="分配状态",
    )
    assignment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        comment="分配类型: manual/automatic",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="分配备注",
    )

    # 时间信息
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="分配时间",
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="确认时间",
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间",
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="结束时间",
    )
    confirmation_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="确认截止时间",
    )

    # 工作量信息
    workload_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="预计工作量(小时)",
    )
    student_capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="学生容量",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
        foreign_keys=[course_id],
        back_populates="teacher_assignments",
    )
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys=[teacher_id],
        back_populates="course_assignments",
    )
    assigner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_by],
    )

    def __repr__(self) -> str:
        return (
            f"<CourseAssignment(id={self.id}, course_id={self.course_id}, "
            f"teacher_id={self.teacher_id}, status={self.status})>"
        )
