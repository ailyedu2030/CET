"""SQLAlchemy基础模型定义."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy基础模型类."""

    pass


class TimestampMixin:
    """时间戳混入类 - 自动管理创建和更新时间."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """创建时间."""
        return mapped_column(
            DateTime(timezone=True),
            default=datetime.utcnow,
            nullable=False,
            comment="创建时间",
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime | None]:
        """更新时间."""
        return mapped_column(
            DateTime(timezone=True),
            onupdate=datetime.utcnow,
            nullable=True,
            comment="更新时间",
        )


class BaseModel(Base, TimestampMixin):
    """基础模型类 - 包含ID和时间戳."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
    )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self) -> str:
        """模型字符串表示."""
        attrs = []
        for column in self.__table__.columns:
            attrs.append(f"{column.name}={getattr(self, column.name)!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"
