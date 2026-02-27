"""AI智能批改系统 - 数据模式"""

from datetime import datetime

from pydantic import BaseModel, Field


class AI智能批改系统Base(BaseModel):
    """
    AI智能批改系统基础模式

    基于TODO第一优先级需求定义
    """

    name: str = Field(..., description="名称", max_length=255)
    description: str | None = Field(None, description="描述")


class AI智能批改系统Create(AI智能批改系统Base):
    """创建AI智能批改系统的请求模式"""


class AI智能批改系统Update(BaseModel):
    """更新AI智能批改系统的请求模式"""

    name: str | None = Field(None, description="名称", max_length=255)
    description: str | None = Field(None, description="描述")


class AI智能批改系统Response(AI智能批改系统Base):
    """
    AI智能批改系统响应模式
    """

    id: int = Field(..., description="ID")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class AI智能批改系统ListResponse(BaseModel):
    """
    AI智能批改系统列表响应模式
    """

    success: bool = Field(..., description="是否成功")
    data: list[AI智能批改系统Response] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
