"""
资源库API路由 - 需求33、34：资源库技术架构和大规模文档处理

实现功能：
1. 资源CRUD接口
2. 文件上传接口
3. 文档处理接口
4. 向量检索接口
5. 批量操作接口
"""

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError,
)
from app.resources.services.document_processing_service import DocumentProcessingService
from app.resources.services.resource_library_service import (
    BatchOperationRequest,
    ResourceCreateRequest,
    ResourceSearchRequest,
    ResourceUpdateRequest,
)
from app.resources.services.vector_search_service import (
    SearchQuery,
    VectorSearchService,
)
from app.shared.dependencies import get_current_user
from app.shared.models.enums import PermissionLevel, ResourceType
from app.shared.services.cache_service import CacheService

if TYPE_CHECKING:
    from app.resources.services.resource_library_service import ResourceLibraryService

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


# 依赖注入
async def get_resource_service(
    db: AsyncSession = Depends(get_db),
) -> "ResourceLibraryService":
    """获取资源库服务"""
    from redis import Redis

    from app.resources.services.resource_library_service import ResourceLibraryService

    # 创建Redis连接 (这里需要根据实际配置调整)
    redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)
    cache_service = CacheService(db, redis_client)
    document_processing_service = DocumentProcessingService(db, None, cache_service)
    return ResourceLibraryService(db, cache_service, document_processing_service)


async def get_vector_search_service(
    db: AsyncSession = Depends(get_db),
) -> VectorSearchService:
    """获取向量检索服务"""
    from redis import Redis

    redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)
    cache_service = CacheService(db, redis_client)
    return VectorSearchService(db, cache_service)


async def get_document_processing_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentProcessingService:
    """获取文档处理服务"""
    from redis import Redis

    redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)
    cache_service = CacheService(db, redis_client)
    return DocumentProcessingService(db, None, cache_service)


# 资源管理接口
@router.post("/", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: ResourceCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    创建资源

    - **name**: 资源名称
    - **resource_type**: 资源类型 (textbook, syllabus, vocabulary, hotspot)
    - **category**: 资源分类
    - **description**: 资源描述
    - **permission_level**: 权限级别 (private, class_shared, public)
    """
    try:
        result = await service.create_resource(request, current_user["id"])
        return {
            "success": True,
            "data": result.dict(),
            "message": "Resource created successfully",
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Create resource failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{resource_id}", response_model=dict[str, Any])
async def get_resource(
    resource_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    获取资源详情

    - **resource_id**: 资源ID
    """
    try:
        result = await service.get_resource(resource_id, current_user["id"])
        return {
            "success": True,
            "data": result.dict(),
            "message": "Resource retrieved successfully",
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Get resource failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.put("/{resource_id}", response_model=dict[str, Any])
async def update_resource(
    resource_id: int,
    request: ResourceUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    更新资源

    - **resource_id**: 资源ID
    - **name**: 资源名称（可选）
    - **category**: 资源分类（可选）
    - **description**: 资源描述（可选）
    - **permission_level**: 权限级别（可选）
    """
    try:
        result = await service.update_resource(resource_id, request, current_user["id"])
        return {
            "success": True,
            "data": result.dict(),
            "message": "Resource updated successfully",
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Update resource failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete("/{resource_id}", response_model=dict[str, Any])
async def delete_resource(
    resource_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    删除资源

    - **resource_id**: 资源ID
    """
    try:
        await service.delete_resource(resource_id, current_user["id"])
        return {"success": True, "message": "Resource deleted successfully"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Delete resource failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/", response_model=dict[str, Any])
async def search_resources(
    query: str | None = Query(None, description="搜索关键词"),
    resource_type: ResourceType | None = Query(None, description="资源类型"),
    category: str | None = Query(None, description="资源分类"),
    permission_level: PermissionLevel | None = Query(None, description="权限级别"),
    created_by: int | None = Query(None, description="创建者ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    搜索资源

    - **query**: 搜索关键词
    - **resource_type**: 资源类型过滤
    - **category**: 分类过滤
    - **permission_level**: 权限级别过滤
    - **created_by**: 创建者过滤
    - **page**: 页码
    - **page_size**: 每页大小
    - **sort_by**: 排序字段
    - **sort_order**: 排序方向
    """
    try:
        request = ResourceSearchRequest(
            query=query,
            resource_type=resource_type,
            category=category,
            permission_level=permission_level,
            created_by=created_by,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        result = await service.search_resources(request, current_user["id"])
        return {
            "success": True,
            "data": result,
            "message": "Resources retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Search resources failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# 文件上传接口
@router.post("/upload", response_model=dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    resource_type: ResourceType = Form(...),
    category: str = Form(...),
    description: str | None = Form(None),
    permission_level: PermissionLevel = Form(PermissionLevel.PRIVATE),
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    上传文件并创建资源

    - **file**: 上传的文件
    - **name**: 资源名称
    - **resource_type**: 资源类型
    - **category**: 资源分类
    - **description**: 资源描述
    - **permission_level**: 权限级别
    """
    try:
        # 1. 读取文件内容
        file_content = await file.read()

        # 2. 上传文件
        if file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required"
            )
        file_path = await service.upload_file(file_content, file.filename)

        # 3. 创建资源记录
        create_request = ResourceCreateRequest(
            name=name,
            resource_type=resource_type,
            category=category,
            description=description,
            permission_level=permission_level,
        )

        result = await service.create_resource(create_request, current_user["id"], file_path)

        return {
            "success": True,
            "data": {
                "resource": result.dict(),
                "file_info": {
                    "filename": file.filename,
                    "size": len(file_content),
                    "content_type": file.content_type,
                },
            },
            "message": "File uploaded and resource created successfully",
        }

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{resource_id}/download")
async def download_file(
    resource_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> FileResponse:
    """
    下载资源文件

    - **resource_id**: 资源ID
    """
    try:
        # 1. 获取资源信息
        resource = await service.get_resource(resource_id, current_user["id"])

        if not resource.file_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        # 2. 返回文件
        return FileResponse(
            path=resource.file_path,
            filename=resource.name,
            media_type="application/octet-stream",
        )

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# 文档处理接口
@router.post("/{resource_id}/process", response_model=dict[str, Any])
async def process_document(
    resource_id: int,
    force_reprocess: bool = Query(False, description="是否强制重新处理"),
    current_user: dict[str, Any] = Depends(get_current_user),
    service: DocumentProcessingService = Depends(get_document_processing_service),
) -> dict[str, Any]:
    """
    处理文档 - 智能切分、向量化、AI分析

    - **resource_id**: 资源ID
    - **force_reprocess**: 是否强制重新处理
    """
    try:
        # 异步处理文档
        asyncio.create_task(service.process_large_document(resource_id, force_reprocess))

        return {
            "success": True,
            "data": {"resource_id": resource_id, "processing_started": True},
            "message": "Document processing started",
        }

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{resource_id}/processing-status", response_model=dict[str, Any])
async def get_processing_status(
    resource_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    获取文档处理状态

    - **resource_id**: 资源ID
    """
    try:
        resource = await service.get_resource(resource_id, current_user["id"])

        return {
            "success": True,
            "data": {
                "resource_id": resource_id,
                "processing_status": resource.processing_status,
                "vector_indexed": resource.vector_indexed,
            },
            "message": "Processing status retrieved successfully",
        }

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Get processing status failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post("/{resource_id}/generate-syllabus", response_model=dict[str, Any])
async def generate_syllabus(
    resource_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: DocumentProcessingService = Depends(get_document_processing_service),
) -> dict[str, Any]:
    """
    生成教学大纲 - 多阶段AI处理

    - **resource_id**: 资源ID
    """
    try:
        result = await service.process_ultra_long_document(resource_id)

        return {
            "success": True,
            "data": {
                "resource_id": resource_id,
                "syllabus": result.generated_syllabus,
                "lesson_plan": result.generated_lesson_plan,
                "processing_metadata": result.processing_metadata,
            },
            "message": "Syllabus generated successfully",
        }

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Generate syllabus failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# 向量检索接口
@router.post("/search/vector", response_model=dict[str, Any])
async def vector_search(
    query_text: str = Form(...),
    query_type: str = Form("hybrid", regex="^(vector|keyword|semantic|hybrid)$"),
    top_k: int = Form(20, ge=1, le=100),
    similarity_threshold: float = Form(0.75, ge=0.0, le=1.0),
    enable_rerank: bool = Form(True),
    current_user: dict[str, Any] = Depends(get_current_user),
    service: VectorSearchService = Depends(get_vector_search_service),
) -> dict[str, Any]:
    """
    向量检索 - 混合检索策略

    - **query_text**: 查询文本
    - **query_type**: 查询类型 (vector, keyword, semantic, hybrid)
    - **top_k**: 返回结果数量
    - **similarity_threshold**: 相似度阈值
    - **enable_rerank**: 是否启用智能重排序
    """
    try:
        search_query = SearchQuery(
            query_text=query_text,
            query_type=query_type,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            enable_rerank=enable_rerank,
        )

        result = await service.hybrid_search(search_query)

        return {
            "success": True,
            "data": result.dict(),
            "message": "Vector search completed successfully",
        }

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/search/similar/{resource_id}", response_model=dict[str, Any])
async def find_similar_resources(
    resource_id: int,
    top_k: int = Query(10, ge=1, le=50),
    current_user: dict[str, Any] = Depends(get_current_user),
    resource_service: "ResourceLibraryService" = Depends(get_resource_service),
    search_service: VectorSearchService = Depends(get_vector_search_service),
) -> dict[str, Any]:
    """
    查找相似资源

    - **resource_id**: 资源ID
    - **top_k**: 返回结果数量
    """
    try:
        # 1. 获取资源信息
        resource = await resource_service.get_resource(resource_id, current_user["id"])

        # 2. 使用资源名称和描述作为查询
        query_text = f"{resource.name} {resource.description or ''}"

        search_query = SearchQuery(
            query_text=query_text,
            query_type="vector",
            top_k=top_k + 1,  # +1 to exclude self
            similarity_threshold=0.6,
            enable_rerank=True,
        )

        result = await search_service.hybrid_search(search_query)

        # 3. 过滤掉自身
        filtered_results = [r for r in result.results if r.resource_id != resource_id][:top_k]

        return {
            "success": True,
            "data": {
                "query_resource": resource.dict(),
                "similar_resources": filtered_results,
                "total_found": len(filtered_results),
            },
            "message": "Similar resources found successfully",
        }

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Find similar resources failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# 批量操作接口
@router.post("/batch", response_model=dict[str, Any])
async def batch_operation(
    request: BatchOperationRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    批量操作

    - **resource_ids**: 资源ID列表
    - **operation**: 操作类型 (delete, update_permission, add_tags, remove_tags)
    - **parameters**: 操作参数
    """
    try:
        result = await service.batch_operation(request, current_user["id"])

        return {
            "success": True,
            "data": result.dict(),
            "message": f"Batch operation '{request.operation}' completed",
        }

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Batch operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# 统计接口
@router.get("/stats/overview", response_model=dict[str, Any])
async def get_resource_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    service: "ResourceLibraryService" = Depends(get_resource_service),
) -> dict[str, Any]:
    """
    获取资源统计概览

    返回资源总数、类型分布、处理状态等统计信息
    """
    try:
        # 这里应该实现统计逻辑
        # 暂时返回模拟数据
        stats = {
            "total_resources": 1000,
            "by_type": {
                "textbook": 300,
                "syllabus": 200,
                "vocabulary": 400,
                "hotspot": 100,
            },
            "by_status": {
                "pending": 50,
                "processing": 20,
                "completed": 900,
                "failed": 30,
            },
            "by_permission": {
                "private": 600,
                "class_shared": 300,
                "public": 100,
            },
            "storage_stats": {
                "total_size_gb": 50.5,
                "vector_count": 500000,
                "indexed_resources": 870,
            },
        }

        return {
            "success": True,
            "data": stats,
            "message": "Resource statistics retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Get resource stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/milvus/stats", response_model=dict[str, Any])
async def get_milvus_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    service: VectorSearchService = Depends(get_vector_search_service),
) -> dict[str, Any]:
    """
    获取Milvus向量数据库统计信息

    返回集合统计、索引状态等信息
    """
    try:
        stats = await service.get_collection_stats()

        return {
            "success": True,
            "data": stats,
            "message": "Milvus statistics retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Get Milvus stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
