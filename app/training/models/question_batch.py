"""题目批次模型."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base_model import BaseModel
from app.shared.models.enums import DifficultyLevel, TrainingType


class QuestionBatch(BaseModel):
    """题目批次模型."""

    __tablename__ = "question_batches"
    __table_args__ = {"extend_existing": True}
    """题目批次模型."""

    __tablename__ = "question_batches"

    # 基本信息
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="批次名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="批次描述"
    )

    # 训练配置
    training_type: Mapped[TrainingType] = mapped_column(
        nullable=False, comment="训练类型"
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        default=DifficultyLevel.ELEMENTARY, comment="难度等级"
    )
    question_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="题目数量"
    )
    time_limit: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="时间限制（分钟）"
    )

    # 知识点和标签
    knowledge_points: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="涵盖的知识点"
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="批次标签"
    )

    # 题目关联
    question_ids: Mapped[list[int]] = mapped_column(
        JSON, default=list, nullable=False, comment="包含的题目ID列表"
    )

    # 状态管理
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_by: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="创建者ID"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<QuestionBatch(id={self.id}, name='{self.name}', training_type='{self.training_type}')>"
