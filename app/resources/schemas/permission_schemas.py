"""
权限管理Schema定义 - 需求11三级权限共享机制
符合设计文档技术要求：严格类型检查、完整数据验证
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """权限级别枚举"""
    PRIVATE = "private"
    CLASS = "class"
    PUBLIC = "public"

class ResourceType(str, Enum):
    """资源类型枚举"""
    VOCABULARY = "vocabulary"
    KNOWLEDGE = "knowledge"
    MATERIAL = "material"
    SYLLABUS = "syllabus"

class SharedWithConfig(BaseModel):
    """共享配置"""
    class_ids: list[int] | None = Field(None, description="共享班级ID列表")
    teacher_ids: list[int] | None = Field(None, description="共享教师ID列表")

class PermissionSettingRequest(BaseModel):
    """权限设置请求"""
    resource_type: ResourceType
    resource_id: int = Field(..., gt=0)
    permission: PermissionLevel
    shared_with: SharedWithConfig | None = None

    class Config:
        json_encoders = {
            ResourceType: lambda v: v.value,
            PermissionLevel: lambda v: v.value
        }

class PermissionSettingResponse(BaseModel):
    """权限设置响应"""
    success: bool = True
    message: str = "权限设置成功"
    resource_type: str
    resource_id: int
    permission: str
    shared_with: dict[str, Any] | None = None

class SharedResourceResponse(BaseModel):
    """共享资源响应"""
    id: int
    name: str
    resource_type: str
    course_id: int
    course_name: str
    owner_id: int
    owner_name: str
    permission: str
    description: str | None = None
    item_count: int = 0
    version: str = "1.0"
    created_at: str
    updated_at: str
    shared_at: str | None = None

class ResourcePermissionInfo(BaseModel):
    """资源权限信息"""
    resource_id: int
    resource_type: str
    resource_name: str
    permission: str
    can_read: bool = False
    can_write: bool = False
    can_share: bool = False
    can_delete: bool = False
    shared_with: dict[str, Any] | None = None

class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    resource_type: ResourceType
    resource_id: int = Field(..., gt=0)
    action: str = Field(..., description="操作类型: read, write, share, delete")

class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    allowed: bool
    reason: str | None = None
    resource_info: ResourcePermissionInfo | None = None
