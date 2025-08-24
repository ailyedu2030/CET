"""教室和设施管理相关的SQLAlchemy模型定义 - 需求2：基础信息管理."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel


class Campus(BaseModel):
    """校区模型 - 支持多校区管理."""

    __tablename__ = "campuses"

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="校区名称",
    )
    address: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="校区地址",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="校区描述",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )

    # 关系
    buildings: Mapped[list["Building"]] = relationship(
        "Building",
        back_populates="campus",
        cascade="all, delete-orphan",
    )


class Building(BaseModel):
    """楼栋模型 - 校区下的楼栋管理."""

    __tablename__ = "buildings"

    # 外键
    campus_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="CASCADE"),
        nullable=False,
        comment="校区ID",
    )

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="楼栋名称",
    )
    building_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="楼号",
    )
    floors: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="楼层数",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="楼栋描述",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )

    # 关系
    campus: Mapped["Campus"] = relationship(
        "Campus",
        back_populates="buildings",
    )
    classrooms: Mapped[list["Classroom"]] = relationship(
        "Classroom",
        back_populates="building",
        cascade="all, delete-orphan",
    )


class Classroom(BaseModel):
    """教室模型 - 需求2：教室信息管理."""

    __tablename__ = "classrooms"

    # 外键
    building_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        comment="楼栋ID",
    )

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="教室名称",
    )
    room_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="教室编号",
    )
    floor: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="楼层",
    )

    # 需求2：容量配置
    capacity: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="座位数",
    )
    area: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="教室面积（平方米）",
    )

    # 需求2：多媒体设备标记
    equipment_list: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="设备列表：{设备类型: {数量, 状态, 型号}}",
    )
    has_projector: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有投影仪",
    )
    has_computer: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有电脑",
    )
    has_audio: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有音响设备",
    )
    has_whiteboard: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否有白板",
    )

    # 需求2：可用状态与时间设置
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否可用",
    )
    available_start_time: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="可用开始时间（HH:MM）",
    )
    available_end_time: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="可用结束时间（HH:MM）",
    )
    available_days: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="可用日期配置：{周一: true, 周二: false, ...}",
    )

    # 状态信息
    maintenance_status: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
        comment="维护状态：normal/maintenance/repair/unavailable",
    )
    last_maintenance_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后维护日期",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    # 关系
    building: Mapped["Building"] = relationship(
        "Building",
        back_populates="classrooms",
    )
    schedules: Mapped[list["ClassroomSchedule"]] = relationship(
        "ClassroomSchedule",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    equipment_items: Mapped[list["Equipment"]] = relationship(
        "Equipment",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )


class ClassroomSchedule(BaseModel):
    """教室排课表模型 - 需求2：冲突检测."""

    __tablename__ = "classroom_schedules"

    # 外键
    classroom_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        comment="教室ID",
    )
    course_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="课程ID（预留外键）",
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="教师ID",
    )

    # 排课信息
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="课程标题",
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="开始时间",
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="结束时间",
    )
    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="星期几（1-7）",
    )

    # 重复设置
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否重复",
    )
    recurrence_pattern: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="重复模式：weekly/biweekly/monthly",
    )
    recurrence_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="重复结束日期",
    )

    # 状态信息
    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",
        nullable=False,
        comment="状态：scheduled/cancelled/completed",
    )
    student_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="学生人数",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    # 关系
    classroom: Mapped["Classroom"] = relationship(
        "Classroom",
        back_populates="schedules",
    )


class Equipment(BaseModel):
    """设备模型 - 功能2：教室设备详细管理."""

    __tablename__ = "equipment"

    # 外键
    classroom_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        comment="教室ID",
    )

    # 基础信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="设备名称",
    )
    equipment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="设备类型：projector/computer/audio/whiteboard/other",
    )
    brand: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="品牌",
    )
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="型号",
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="序列号",
    )

    # 状态信息
    status: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
        comment="设备状态：normal/maintenance/repair/broken/retired",
    )
    purchase_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="购买日期",
    )
    warranty_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="保修结束日期",
    )
    last_maintenance_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后维护日期",
    )
    next_maintenance_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次维护日期",
    )

    # 使用统计
    total_usage_hours: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总使用时长（小时）",
    )
    monthly_usage_hours: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="月度使用时长（小时）",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="故障次数",
    )

    # 扩展信息
    specifications: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="设备规格参数",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    # 关系
    classroom: Mapped["Classroom"] = relationship(
        "Classroom",
        back_populates="equipment_items",
    )
    maintenance_records: Mapped[list["EquipmentMaintenanceRecord"]] = relationship(
        "EquipmentMaintenanceRecord",
        back_populates="equipment",
        cascade="all, delete-orphan",
    )


class EquipmentMaintenanceRecord(BaseModel):
    """设备维护记录模型 - 功能2：设备维护管理."""

    __tablename__ = "equipment_maintenance_records"

    # 外键
    equipment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
        comment="设备ID",
    )
    maintainer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="维护人员ID",
    )

    # 维护信息
    maintenance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="维护类型：routine/repair/upgrade/inspection",
    )
    maintenance_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="维护日期",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="维护描述",
    )
    cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="维护费用",
    )
    duration_hours: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="维护时长（小时）",
    )

    # 结果信息
    result: Mapped[str] = mapped_column(
        String(20),
        default="completed",
        nullable=False,
        comment="维护结果：completed/failed/partial",
    )
    next_maintenance_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="建议下次维护日期",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="维护备注",
    )

    # 关系
    equipment: Mapped["Equipment"] = relationship(
        "Equipment",
        back_populates="maintenance_records",
    )
