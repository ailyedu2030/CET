"""
资源库管理服务 - 需求33：资源库技术架构

实现功能：
1. 资源库CRUD操作
2. 文件上传和管理
3. 权限控制
4. 批量操作
5. 资源分类和标签管理
"""

import asyncio
import hashlib
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError,
)
from app.resources.models.resource_models import (
    PermissionLevel,
    ProcessingStatus,
    ResourceLibrary,
    ResourceType,
)
from app.resources.services.document_processing_service import DocumentProcessingService
from app.shared.services.cache_service import CacheService
from app.shared.utils.file_utils import FileUtils


class ResourceCreateRequest(BaseModel):
    """资源创建请求"""

    name: str
    resource_type: ResourceType
    category: str
    description: str | None = None
    permission_level: PermissionLevel = PermissionLevel.PRIVATE
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourceUpdateRequest(BaseModel):
    """资源更新请求"""

    name: str | None = None
    category: str | None = None
    description: str | None = None
    permission_level: PermissionLevel | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ResourceSearchRequest(BaseModel):
    """资源搜索请求"""

    query: str | None = None
    resource_type: ResourceType | None = None
    category: str | None = None
    permission_level: PermissionLevel | None = None
    tags: list[str] = Field(default_factory=list)
    created_by: int | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ResourceResponse(BaseModel):
    """资源响应模型"""

    id: int
    name: str
    resource_type: ResourceType
    category: str
    description: str | None
    file_path: str | None
    file_size: int | None
    file_format: str | None
    permission_level: PermissionLevel
    processing_status: ProcessingStatus
    vector_indexed: bool
    version: str
    download_count: int
    view_count: int
    rating: float
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: int
    created_at: datetime
    updated_at: datetime


class BatchOperationRequest(BaseModel):
    """批量操作请求"""

    resource_ids: list[int]
    operation: str  # delete, update_permission, add_tags, remove_tags
    parameters: dict[str, Any] = Field(default_factory=dict)


class BatchOperationResult(BaseModel):
    """批量操作结果"""

    total_count: int
    success_count: int
    failed_count: int
    failed_items: list[dict[str, Any]] = Field(default_factory=list)


class ResourceLibraryService:
    """资源库管理服务 - 支持TB级存储和百万级文档管理"""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
        document_processing_service: DocumentProcessingService,
    ) -> None:
        self.db = db
        self.cache_service = cache_service
        self.document_processing_service = document_processing_service
        self.file_utils = FileUtils()

        # 配置
        self.upload_base_path = Path("uploads/resources")
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".txt",
            ".md",
            ".html",
            ".epub",
        }

    async def create_resource(
        self,
        request: ResourceCreateRequest,
        created_by: int,
        file_path: str | None = None,
    ) -> ResourceResponse:
        """
        创建资源

        Args:
            request: 创建请求
            created_by: 创建者ID
            file_path: 文件路径（可选）

        Returns:
            ResourceResponse: 创建的资源
        """
        try:
            # 1. 验证请求
            await self._validate_create_request(request, file_path)

            # 2. 处理文件信息
            file_info = {}
            if file_path:
                file_info = await self._process_file_info(file_path)

            # 3. 创建资源记录
            resource = ResourceLibrary(
                name=request.name,
                resource_type=request.resource_type,
                category=request.category,
                description=request.description,
                file_path=file_path,
                file_size=file_info.get("size"),
                file_format=file_info.get("format"),
                permission_level=request.permission_level,
                processing_status=ProcessingStatus.PENDING,
                vector_indexed=False,
                version="1.0",
                download_count=0,
                view_count=0,
                rating=0.0,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(resource)
            await self.db.commit()
            await self.db.refresh(resource)

            # 4. 异步处理文档（如果有文件）
            if file_path and file_info.get("format") in [
                ".pdf",
                ".doc",
                ".docx",
                ".txt",
            ]:
                asyncio.create_task(self._async_process_document(resource.id, file_path))

            # 5. 清理缓存
            await self._clear_resource_cache()

            logger.info(
                f"Resource created successfully: {resource.id}",
                extra={
                    "resource_name": request.name,
                    "resource_type": request.resource_type,
                    "created_by": created_by,
                    "has_file": file_path is not None,
                },
            )

            return await self._to_response_model(resource)

        except Exception as e:
            logger.error(
                f"Failed to create resource: {str(e)}",
                extra={
                    "request": request.dict(),
                    "created_by": created_by,
                    "error": str(e),
                },
            )
            raise BusinessLogicError(f"Failed to create resource: {str(e)}") from e

    async def get_resource(self, resource_id: int, user_id: int | None = None) -> ResourceResponse:
        """
        获取资源详情

        Args:
            resource_id: 资源ID
            user_id: 用户ID（用于权限检查）

        Returns:
            ResourceResponse: 资源详情
        """
        try:
            # 1. 缓存检查
            cache_key = f"resource:{resource_id}"
            cached_resource = await self.cache_service.get(cache_key)
            if cached_resource:
                resource_data: ResourceResponse = ResourceResponse.model_validate(cached_resource)
                # 权限检查
                if await self._check_resource_permission(resource_data, user_id):
                    # 更新查看次数
                    asyncio.create_task(self._increment_view_count(resource_id))
                    return resource_data
                else:
                    raise ValueError("Access denied to this resource")

            # 2. 数据库查询
            stmt = select(ResourceLibrary).where(ResourceLibrary.id == resource_id)
            result = await self.db.execute(stmt)
            resource = result.scalar_one_or_none()

            if not resource:
                raise ResourceNotFoundError(f"Resource {resource_id} not found")

            # 3. 权限检查
            resource_response = await self._to_response_model(resource)
            if not await self._check_resource_permission(resource_response, user_id):
                raise ValueError("Access denied to this resource")

            # 4. 缓存结果
            await self.cache_service.set(
                cache_key,
                resource_response.dict(),
                ttl=3600,  # 1小时
            )

            # 5. 更新查看次数
            asyncio.create_task(self._increment_view_count(resource_id))

            return resource_response

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to get resource {resource_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to get resource: {str(e)}") from e

    async def update_resource(
        self, resource_id: int, request: ResourceUpdateRequest, user_id: int
    ) -> ResourceResponse:
        """
        更新资源

        Args:
            resource_id: 资源ID
            request: 更新请求
            user_id: 用户ID

        Returns:
            ResourceResponse: 更新后的资源
        """
        try:
            # 1. 获取资源
            stmt = select(ResourceLibrary).where(ResourceLibrary.id == resource_id)
            result = await self.db.execute(stmt)
            resource = result.scalar_one_or_none()

            if not resource:
                raise ResourceNotFoundError(f"Resource {resource_id} not found")

            # 2. 权限检查
            if not await self._check_update_permission(resource, user_id):
                raise ValueError("No permission to update this resource")

            # 3. 更新字段
            update_data = {}
            if request.name is not None:
                update_data["name"] = request.name
            if request.category is not None:
                update_data["category"] = request.category
            if request.description is not None:
                update_data["description"] = request.description
            if request.permission_level is not None:
                update_data["permission_level"] = request.permission_level
            if request.metadata is not None:
                update_data["metadata"] = request.metadata

            update_data["updated_at"] = datetime.utcnow()

            # 4. 执行更新
            stmt = (
                update(ResourceLibrary)
                .where(ResourceLibrary.id == resource_id)
                .values(**update_data)
            )
            await self.db.execute(stmt)
            await self.db.commit()

            # 5. 清理缓存
            await self._clear_resource_cache(resource_id)

            # 6. 获取更新后的资源
            updated_resource = await self.get_resource(resource_id, user_id)

            logger.info(
                f"Resource updated successfully: {resource_id}",
                extra={
                    "resource_id": resource_id,
                    "updated_by": user_id,
                    "updates": update_data,
                },
            )

            return updated_resource

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update resource {resource_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update resource: {str(e)}") from e

    async def delete_resource(self, resource_id: int, user_id: int) -> bool:
        """
        删除资源

        Args:
            resource_id: 资源ID
            user_id: 用户ID

        Returns:
            bool: 删除是否成功
        """
        try:
            # 1. 获取资源
            stmt = select(ResourceLibrary).where(ResourceLibrary.id == resource_id)
            result = await self.db.execute(stmt)
            resource = result.scalar_one_or_none()

            if not resource:
                raise ResourceNotFoundError(f"Resource {resource_id} not found")

            # 2. 权限检查
            if not await self._check_delete_permission(resource, user_id):
                raise ValueError("No permission to delete this resource")

            # 3. 删除文件
            if resource.file_path and os.path.exists(resource.file_path):
                try:
                    os.remove(resource.file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete file {resource.file_path}: {str(e)}")

            # 4. 删除数据库记录
            await self.db.delete(resource)
            await self.db.commit()

            # 5. 清理缓存
            await self._clear_resource_cache(resource_id)

            logger.info(
                f"Resource deleted successfully: {resource_id}",
                extra={"resource_id": resource_id, "deleted_by": user_id},
            )

            return True

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete resource {resource_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to delete resource: {str(e)}") from e

    async def search_resources(
        self, request: ResourceSearchRequest, user_id: int | None = None
    ) -> dict[str, Any]:
        """
        搜索资源

        Args:
            request: 搜索请求
            user_id: 用户ID

        Returns:
            dict: 搜索结果
        """
        try:
            # 1. 构建查询条件
            conditions = []

            # 权限过滤
            if user_id:
                conditions.append(
                    or_(
                        ResourceLibrary.permission_level == PermissionLevel.PUBLIC,
                        ResourceLibrary.created_by == user_id,
                    )
                )
            else:
                conditions.append(ResourceLibrary.permission_level == PermissionLevel.PUBLIC)

            # 其他过滤条件
            if request.resource_type:
                conditions.append(ResourceLibrary.resource_type == request.resource_type)
            if request.category:
                conditions.append(ResourceLibrary.category.ilike(f"%{request.category}%"))
            if request.permission_level:
                conditions.append(ResourceLibrary.permission_level == request.permission_level)
            if request.created_by:
                conditions.append(ResourceLibrary.created_by == request.created_by)

            # 文本搜索
            if request.query:
                text_conditions = [
                    ResourceLibrary.name.ilike(f"%{request.query}%"),
                    ResourceLibrary.description.ilike(f"%{request.query}%"),
                ]
                conditions.append(or_(*text_conditions))

            # 2. 构建查询
            stmt = select(ResourceLibrary).where(and_(*conditions))

            # 排序
            if request.sort_by == "name":
                order_col = ResourceLibrary.name
            elif request.sort_by == "created_at":
                order_col = ResourceLibrary.created_at
            elif request.sort_by == "updated_at":
                order_col = ResourceLibrary.updated_at
            elif request.sort_by == "view_count":
                order_col = ResourceLibrary.view_count
            elif request.sort_by == "rating":
                order_col = ResourceLibrary.rating
            else:
                order_col = ResourceLibrary.created_at

            if request.sort_order == "desc":
                stmt = stmt.order_by(desc(order_col))
            else:
                stmt = stmt.order_by(order_col)

            # 3. 分页
            total_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await self.db.execute(total_stmt)
            total_count = total_result.scalar() or 0

            offset = (request.page - 1) * request.page_size
            stmt = stmt.offset(offset).limit(request.page_size)

            # 4. 执行查询
            result = await self.db.execute(stmt)
            resources = result.scalars().all()

            # 5. 转换为响应模型
            resource_responses = []
            for resource in resources:
                resource_response = await self._to_response_model(resource)
                resource_responses.append(resource_response)

            # 6. 构建响应
            response = {
                "resources": resource_responses,
                "pagination": {
                    "page": request.page,
                    "page_size": request.page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + request.page_size - 1) // request.page_size,
                },
                "filters": {
                    "resource_type": request.resource_type,
                    "category": request.category,
                    "permission_level": request.permission_level,
                    "created_by": request.created_by,
                },
            }

            logger.info(
                "Resource search completed",
                extra={
                    "query": request.query,
                    "total_found": total_count,
                    "page": request.page,
                    "user_id": user_id,
                },
            )

            return response

        except Exception as e:
            logger.error(f"Resource search failed: {str(e)}")
            raise BusinessLogicError(f"Resource search failed: {str(e)}") from e

    async def upload_file(
        self, file_content: bytes, filename: str, resource_id: int | None = None
    ) -> str:
        """
        上传文件

        Args:
            file_content: 文件内容
            filename: 文件名
            resource_id: 资源ID（可选）

        Returns:
            str: 文件路径
        """
        try:
            # 1. 验证文件
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise ValueError(f"File type {file_extension} not allowed")

            if len(file_content) > self.max_file_size:
                raise ValueError(f"File size exceeds limit of {self.max_file_size} bytes")

            # 2. 生成文件路径
            file_hash = hashlib.md5(file_content).hexdigest()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file_hash}_{filename}"

            # 创建目录结构
            upload_dir = self.upload_base_path / datetime.now().strftime("%Y/%m/%d")
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / safe_filename

            # 3. 保存文件
            with open(file_path, "wb") as f:
                f.write(file_content)

            # 4. 验证文件完整性
            with open(file_path, "rb") as f:
                saved_content = f.read()
                if hashlib.md5(saved_content).hexdigest() != file_hash:
                    os.remove(file_path)
                    raise BusinessLogicError("File integrity check failed")

            logger.info(
                f"File uploaded successfully: {file_path}",
                extra={
                    "filename": filename,
                    "file_size": len(file_content),
                    "resource_id": resource_id,
                },
            )

            return str(file_path)

        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise BusinessLogicError(f"File upload failed: {str(e)}") from e

    async def batch_operation(
        self, request: BatchOperationRequest, user_id: int
    ) -> BatchOperationResult:
        """
        批量操作

        Args:
            request: 批量操作请求
            user_id: 用户ID

        Returns:
            BatchOperationResult: 操作结果
        """
        try:
            results = BatchOperationResult(
                total_count=len(request.resource_ids), success_count=0, failed_count=0
            )

            for resource_id in request.resource_ids:
                try:
                    if request.operation == "delete":
                        await self.delete_resource(resource_id, user_id)
                    elif request.operation == "update_permission":
                        permission_level = request.parameters.get("permission_level")
                        if permission_level:
                            update_request = ResourceUpdateRequest(
                                permission_level=PermissionLevel(permission_level)
                            )
                            await self.update_resource(resource_id, update_request, user_id)
                    else:
                        raise ValueError(f"Unknown operation: {request.operation}")

                    results.success_count += 1

                except Exception as e:
                    results.failed_count += 1
                    results.failed_items.append({"resource_id": resource_id, "error": str(e)})

            logger.info(
                f"Batch operation completed: {request.operation}",
                extra={
                    "operation": request.operation,
                    "total_count": results.total_count,
                    "success_count": results.success_count,
                    "failed_count": results.failed_count,
                },
            )

            return results

        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            raise BusinessLogicError(f"Batch operation failed: {str(e)}") from e

    # 私有方法
    async def _validate_create_request(
        self, request: ResourceCreateRequest, file_path: str | None
    ) -> None:
        """验证创建请求"""
        if not request.name.strip():
            raise ValueError("Resource name cannot be empty")

        if len(request.name) > 200:
            raise ValueError("Resource name too long")

        if file_path and not os.path.exists(file_path):
            raise ValueError("File does not exist")

    async def _process_file_info(self, file_path: str) -> dict[str, Any]:
        """处理文件信息"""
        file_stat = os.stat(file_path)
        file_extension = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)

        return {
            "size": file_stat.st_size,
            "format": file_extension,
            "mime_type": mime_type,
        }

    async def _async_process_document(self, resource_id: int, file_path: str) -> None:
        """异步处理文档"""
        try:
            await self.document_processing_service.process_large_document(resource_id)
        except Exception as e:
            logger.error(f"Document processing failed for resource {resource_id}: {str(e)}")

    async def _to_response_model(self, resource: ResourceLibrary) -> ResourceResponse:
        """转换为响应模型"""
        return ResourceResponse(
            id=resource.id,
            name=resource.name,
            resource_type=resource.resource_type,
            category=resource.category,
            description=resource.description,
            file_path=resource.file_path,
            file_size=resource.file_size,
            file_format=resource.file_format,
            permission_level=resource.permission_level,
            processing_status=resource.processing_status,
            vector_indexed=resource.vector_indexed,
            version=resource.version,
            download_count=resource.download_count,
            view_count=resource.view_count,
            rating=resource.rating,
            tags=[],  # 需要从其他表获取
            metadata={},  # 需要从其他表获取
            created_by=resource.created_by,
            created_at=resource.created_at,
            updated_at=resource.updated_at or resource.created_at,
        )

    async def _check_resource_permission(
        self, resource: ResourceResponse, user_id: int | None
    ) -> bool:
        """检查资源访问权限"""
        if resource.permission_level == PermissionLevel.PUBLIC:
            return True
        if user_id and resource.created_by == user_id:
            return True
        # 这里可以添加更复杂的权限逻辑
        return False

    async def _check_update_permission(self, resource: ResourceLibrary, user_id: int) -> bool:
        """检查更新权限"""
        return bool(resource.created_by == user_id)

    async def _check_delete_permission(self, resource: ResourceLibrary, user_id: int) -> bool:
        """检查删除权限"""
        return bool(resource.created_by == user_id)

    async def _increment_view_count(self, resource_id: int) -> None:
        """增加查看次数"""
        try:
            stmt = (
                update(ResourceLibrary)
                .where(ResourceLibrary.id == resource_id)
                .values(view_count=ResourceLibrary.view_count + 1)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to increment view count for resource {resource_id}: {str(e)}")

    async def _clear_resource_cache(self, resource_id: int | None = None) -> None:
        """清理资源缓存"""
        try:
            if resource_id:
                await self.cache_service.delete(f"resource:{resource_id}")
            else:
                # 清理所有资源相关缓存（模拟实现）
                # await self.cache_service.delete_pattern("resource:*")
                pass
        except Exception as e:
            logger.error(f"Failed to clear resource cache: {str(e)}")
