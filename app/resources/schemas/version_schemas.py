"""
版本控制Schema定义 - 需求11 Git-like版本管理
符合设计文档技术要求：严格类型检查、完整数据验证
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """变更类型枚举"""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class ResourceVersionResponse(BaseModel):
    """资源版本响应"""

    id: int
    resource_type: str
    resource_id: int
    version: str
    description: str | None
    change_summary: str | None = None
    created_by: int
    creator_name: str
    created_at: str
    is_active: bool = False
    parent_version_id: int | None = None
    content_hash: str | None = None
    file_size: int | None = None


class VersionChangeDetail(BaseModel):
    """版本变更详情"""

    field: str
    change_type: ChangeType
    old_value: Any | None = None
    new_value: Any | None = None
    description: str | None = None


class VersionComparisonResponse(BaseModel):
    """版本对比响应"""

    source_version: ResourceVersionResponse
    target_version: ResourceVersionResponse
    changes: list[VersionChangeDetail]
    summary: dict[str, int] = Field(
        default_factory=lambda: {"added": 0, "modified": 0, "deleted": 0}
    )


class RollbackRequest(BaseModel):
    """回滚请求"""

    version_id: int = Field(..., gt=0, description="目标版本ID")
    reason: str = Field(..., min_length=1, max_length=500, description="回滚原因")
    create_backup: bool = Field(True, description="是否创建当前版本备份")


class RollbackResponse(BaseModel):
    """回滚响应"""

    success: bool = True
    message: str = "回滚成功"
    new_version: str
    backup_version_id: int | None = None
    rollback_details: dict[str, Any] = Field(default_factory=dict)


class VersionCreateRequest(BaseModel):
    """创建版本请求"""

    description: str = Field(..., min_length=1, max_length=500)
    change_summary: str | None = Field(None, max_length=1000)
    content_data: dict[str, Any] = Field(..., description="版本内容数据")


class VersionCreateResponse(BaseModel):
    """创建版本响应"""

    version_id: int
    version: str
    created_at: str
    content_hash: str


class VersionListRequest(BaseModel):
    """版本列表请求"""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    include_inactive: bool = Field(False, description="是否包含非活跃版本")


class VersionListResponse(BaseModel):
    """版本列表响应"""

    versions: list[ResourceVersionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
