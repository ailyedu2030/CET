"""AI智能批改系统 - 数据模型"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.shared.models.base_model import BaseModel


class AI智能批改系统Model(BaseModel):
    """
    AI智能批改系统数据模型

    基于TODO第一优先级需求实现
    """

    __tablename__ = "grading"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(255), nullable=False, comment="名称")
    description: str | None = Column(Text, comment="描述")
    status: str = Column(String(50), default="active", comment="状态")

    # 时间戳
    created_at: datetime = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<AI智能批改系统Model(id={self.id}, name={self.name})>"
