"""向量数据库服务模块

提供统一的向量数据库接口，支持文档向量化、语义检索、
相似度搜索等功能。基于Milvus向量数据库实现。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.config.vector_config import vector_config

try:
    from app.shared.services.cache_service import CacheService
except ImportError:
    # 如果CacheService不可用，创建模拟类
    class CacheService:  # type: ignore[no-redef]
        async def get(self, key: str) -> Any:
            return None

        async def set(self, key: str, value: Any, ttl: int = 300) -> None:
            pass

        async def delete_pattern(self, pattern: str) -> None:
            pass


from app.shared.utils.embedding_utils import embedding_utils
from app.shared.utils.milvus_manager import milvus_manager
from app.shared.utils.similarity_calculator import (
    SimilarityResult,
    similarity_calculator,
)

logger = logging.getLogger(__name__)


class DocumentVector(BaseModel):
    """文档向量模型"""

    model_config = {"from_attributes": True}

    document_id: str = Field(..., description="文档ID")
    text: str = Field(..., description="文档文本")
    vector: list[float] = Field(..., description="向量数据")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    collection_type: str = Field(..., description="集合类型")
    embedding_model: str = Field(..., description="嵌入模型")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class SearchResult(BaseModel):
    """搜索结果模型"""

    model_config = {"from_attributes": True}

    document_id: str = Field(..., description="文档ID")
    text: str = Field(..., description="文档文本")
    score: float = Field(..., description="相似度分数")
    distance: float = Field(..., description="向量距离")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    rank: int = Field(..., description="排名")


class VectorSearchQuery(BaseModel):
    """向量搜索查询"""

    model_config = {"from_attributes": True}

    query_text: str = Field(..., description="查询文本")
    collection_type: str = Field(default="documents", description="集合类型")
    top_k: int = Field(default=10, description="返回结果数量")
    threshold: float = Field(default=0.0, description="相似度阈值")
    embedding_model: str = Field(default="openai", description="嵌入模型")
    filters: dict[str, Any] | None = Field(None, description="过滤条件")


class VectorDatabaseService:
    """向量数据库服务"""

    def __init__(self, db: AsyncSession, cache_service: CacheService | None = None) -> None:
        """初始化向量数据库服务"""
        self.db = db
        self.cache_service = cache_service
        self.milvus_manager = milvus_manager
        self.embedding_utils = embedding_utils
        self.similarity_calculator = similarity_calculator

        # 确保Milvus管理器已连接
        if not self.milvus_manager.is_connected:
            asyncio.create_task(self.milvus_manager.connect())

    async def add_documents(
        self,
        texts: list[str],
        collection_type: str = "documents",
        embedding_model: str = "openai",
        metadata: list[dict[str, Any]] | None = None,
        document_ids: list[str] | None = None,
    ) -> list[str]:
        """添加文档到向量数据库"""
        try:
            # 验证集合类型
            if not vector_config.is_collection_type_valid(collection_type):
                raise ValueError(f"Invalid collection type: {collection_type}")

            # 生成文档ID
            if not document_ids:
                document_ids = [str(uuid4()) for _ in texts]

            if len(document_ids) != len(texts):
                raise ValueError("Document IDs and texts length mismatch")

            # 生成向量
            logger.info(f"Generating embeddings for {len(texts)} documents")
            vectors = await self.embedding_utils.get_embeddings(texts, embedding_model)

            # 准备元数据
            if not metadata:
                metadata = [{}] * len(texts)

            # 添加文档信息到元数据
            enhanced_metadata = []
            for i, meta in enumerate(metadata):
                enhanced_meta = meta.copy()
                enhanced_meta.update(
                    {
                        "document_id": document_ids[i],
                        "embedding_model": embedding_model,
                        "created_at": datetime.now().isoformat(),
                        "text_length": len(texts[i]),
                    }
                )
                enhanced_metadata.append(enhanced_meta)

            # 插入到Milvus
            await self.milvus_manager.insert_vectors(
                collection_type=collection_type,
                texts=texts,
                vectors=vectors,
                metadata=enhanced_metadata,
            )

            # 保存文档向量信息到数据库
            for i, doc_id in enumerate(document_ids):
                doc_vector = DocumentVector(
                    document_id=doc_id,
                    text=texts[i],
                    vector=vectors[i],
                    metadata=enhanced_metadata[i],
                    collection_type=collection_type,
                    embedding_model=embedding_model,
                )
                await self._save_document_vector(doc_vector)

            # 清除相关缓存
            if self.cache_service and hasattr(self.cache_service, "delete_pattern"):
                await self.cache_service.delete_pattern(f"vector_search:{collection_type}:*")

            logger.info(f"Successfully added {len(texts)} documents to {collection_type}")
            return document_ids

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    async def search_similar_documents(self, query: VectorSearchQuery) -> list[SearchResult]:
        """搜索相似文档"""
        try:
            # 检查缓存
            cache_key = (
                f"vector_search:{query.collection_type}:{hash(query.query_text)}:{query.top_k}"
            )
            if self.cache_service:
                cached_results = await self.cache_service.get(cache_key)
                if cached_results:
                    return [SearchResult(**result) for result in cached_results]

            # 生成查询向量
            query_vector = await self.embedding_utils.get_single_embedding(
                query.query_text, query.embedding_model
            )

            # 执行向量搜索
            search_results = await self.milvus_manager.search_vectors(
                collection_type=query.collection_type,
                query_vectors=[query_vector],
                top_k=query.top_k,
                expr=self._build_filter_expression(query.filters),
            )

            # 格式化结果
            results = []
            if search_results and search_results[0]:
                for rank, hit in enumerate(search_results[0]):
                    if hit["score"] >= query.threshold:
                        result = SearchResult(
                            document_id=hit.get("metadata", {}).get("document_id", ""),
                            text=hit["text"],
                            score=hit["score"],
                            distance=hit["distance"],
                            metadata=self._parse_metadata(hit.get("metadata", "{}")),
                            rank=rank + 1,
                        )
                        results.append(result)

            # 缓存结果
            if self.cache_service and results:
                await self.cache_service.set(
                    cache_key,
                    [result.model_dump() for result in results],
                    ttl=300,  # 5分钟
                )

            logger.info(f"Found {len(results)} similar documents for query")
            return results

        except Exception as e:
            logger.error(f"Failed to search similar documents: {str(e)}")
            raise

    async def delete_documents(
        self, document_ids: list[str], collection_type: str = "documents"
    ) -> int:
        """删除文档"""
        try:
            # 构建删除表达式
            id_list = "', '".join(document_ids)
            expr = f'metadata like \'%"document_id": "{id_list}"%\''

            # 从Milvus删除
            result = await self.milvus_manager.delete_vectors(collection_type, expr)

            # 从数据库删除记录
            for doc_id in document_ids:
                await self._delete_document_vector(doc_id)

            # 清除缓存
            if self.cache_service and hasattr(self.cache_service, "delete_pattern"):
                await self.cache_service.delete_pattern(f"vector_search:{collection_type}:*")

            delete_count: int = result.get("delete_count", 0)
            logger.info(f"Deleted {delete_count} documents from {collection_type}")
            return delete_count

        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise

    async def get_collection_stats(self, collection_type: str) -> dict[str, Any]:
        """获取集合统计信息"""
        try:
            stats = await self.milvus_manager.get_collection_stats(collection_type)

            # 添加额外统计信息
            stats.update(
                {
                    "collection_config": vector_config.get_collection_config(collection_type),
                    "supported_models": self.embedding_utils.get_supported_models(),
                }
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            raise

    def _build_filter_expression(self, filters: dict[str, Any] | None) -> str | None:
        """构建过滤表达式"""
        if not filters:
            return None

        expressions = []
        for key, value in filters.items():
            if isinstance(value, str):
                expressions.append(f'metadata like \'%"{key}": "{value}"%\'')
            elif isinstance(value, int | float):
                expressions.append(f"metadata like '%\"{key}\": {value}%'")

        return " and ".join(expressions) if expressions else None

    def _parse_metadata(self, metadata_str: str) -> dict[str, Any]:
        """解析元数据字符串"""
        try:
            return json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            return {}

    async def compute_text_similarity(
        self, text1: str, text2: str, embedding_model: str = "openai"
    ) -> SimilarityResult:
        """计算文本语义相似度"""
        try:
            return await self.similarity_calculator.compute_semantic_similarity(
                text1, text2, embedding_model
            )
        except Exception as e:
            logger.error(f"Failed to compute text similarity: {str(e)}")
            raise

    async def find_duplicate_documents(
        self,
        collection_type: str = "documents",
        similarity_threshold: float = 0.95,
        batch_size: int = 100,
    ) -> list[tuple[str, str, float]]:
        """查找重复文档"""
        try:
            # 获取所有文档
            all_docs = await self._get_all_documents(collection_type, batch_size)

            duplicates = []
            for i in range(len(all_docs)):
                for j in range(i + 1, len(all_docs)):
                    doc1, doc2 = all_docs[i], all_docs[j]

                    # 计算相似度
                    similarity = await self.similarity_calculator.compute_vector_similarity(
                        doc1["vector"], doc2["vector"], "cosine"
                    )

                    if similarity.score >= similarity_threshold:
                        duplicates.append(
                            (doc1["document_id"], doc2["document_id"], similarity.score)
                        )

            logger.info(f"Found {len(duplicates)} duplicate pairs in {collection_type}")
            return duplicates

        except Exception as e:
            logger.error(f"Failed to find duplicate documents: {str(e)}")
            raise

    async def recommend_similar_content(
        self,
        document_id: str,
        collection_type: str = "documents",
        top_k: int = 5,
        exclude_self: bool = True,
    ) -> list[SearchResult]:
        """推荐相似内容"""
        try:
            # 获取文档向量
            doc_vector = await self._get_document_vector(document_id, collection_type)
            if not doc_vector:
                raise ValueError(f"Document {document_id} not found")

            # 搜索相似文档
            search_results = await self.milvus_manager.search_vectors(
                collection_type=collection_type,
                query_vectors=[doc_vector["vector"]],
                top_k=top_k + (1 if exclude_self else 0),
            )

            # 格式化结果
            results: list[SearchResult] = []
            if search_results and search_results[0]:
                for _rank, hit in enumerate(search_results[0]):
                    hit_doc_id = hit.get("metadata", {}).get("document_id", "")

                    # 排除自身
                    if exclude_self and hit_doc_id == document_id:
                        continue

                    if len(results) >= top_k:
                        break

                    result = SearchResult(
                        document_id=hit_doc_id,
                        text=hit["text"],
                        score=hit["score"],
                        distance=hit["distance"],
                        metadata=self._parse_metadata(hit.get("metadata", "{}")),
                        rank=len(results) + 1,
                    )
                    results.append(result)

            logger.info(f"Generated {len(results)} recommendations for document {document_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to recommend similar content: {str(e)}")
            raise

    async def batch_search(
        self,
        queries: list[str],
        collection_type: str = "documents",
        top_k: int = 10,
        embedding_model: str = "openai",
    ) -> list[list[SearchResult]]:
        """批量搜索"""
        try:
            # 生成查询向量
            query_vectors = await self.embedding_utils.get_embeddings(queries, embedding_model)

            # 执行批量搜索
            search_results = await self.milvus_manager.search_vectors(
                collection_type=collection_type,
                query_vectors=query_vectors,
                top_k=top_k,
            )

            # 格式化结果
            all_results = []
            for _i, query_results in enumerate(search_results):
                results = []
                for rank, hit in enumerate(query_results):
                    result = SearchResult(
                        document_id=hit.get("metadata", {}).get("document_id", ""),
                        text=hit["text"],
                        score=hit["score"],
                        distance=hit["distance"],
                        metadata=self._parse_metadata(hit.get("metadata", "{}")),
                        rank=rank + 1,
                    )
                    results.append(result)
                all_results.append(results)

            logger.info(f"Completed batch search for {len(queries)} queries")
            return all_results

        except Exception as e:
            logger.error(f"Failed to perform batch search: {str(e)}")
            raise

    async def get_vector_statistics(self, collection_type: str) -> dict[str, Any]:
        """获取向量统计信息"""
        try:
            # 获取基本统计
            stats = await self.get_collection_stats(collection_type)

            # 获取向量多样性分数
            sample_vectors = await self._sample_vectors(collection_type, 100)
            if sample_vectors:
                diversity_score = await self.similarity_calculator.compute_diversity_score(
                    sample_vectors, "cosine"
                )
                stats["diversity_score"] = diversity_score

            # 获取嵌入模型分布
            model_distribution = await self._get_embedding_model_distribution(collection_type)
            stats["embedding_model_distribution"] = model_distribution

            return stats

        except Exception as e:
            logger.error(f"Failed to get vector statistics: {str(e)}")
            raise

    # 辅助方法
    async def _get_all_documents(
        self, collection_type: str, batch_size: int
    ) -> list[dict[str, Any]]:
        """获取所有文档（分批）"""
        # TODO: 实现从Milvus获取所有文档的逻辑
        return []

    async def _get_document_vector(
        self, document_id: str, collection_type: str
    ) -> dict[str, Any] | None:
        """获取文档向量"""
        # TODO: 实现从Milvus获取特定文档向量的逻辑
        return None

    async def _sample_vectors(self, collection_type: str, sample_size: int) -> list[list[float]]:
        """采样向量"""
        # TODO: 实现向量采样逻辑
        return []

    async def _get_embedding_model_distribution(self, collection_type: str) -> dict[str, int]:
        """获取嵌入模型分布"""
        # TODO: 实现模型分布统计逻辑
        return {}

    # 数据库操作方法（需要根据实际数据库模型实现）
    async def _save_document_vector(self, doc_vector: DocumentVector) -> None:
        """保存文档向量到数据库"""
        # TODO: 实现数据库保存逻辑
        pass

    async def _delete_document_vector(self, document_id: str) -> None:
        """从数据库删除文档向量记录"""
        # TODO: 实现数据库删除逻辑
        pass


# 依赖注入函数
async def get_vector_database_service(
    db: AsyncSession, cache_service: CacheService | None = None
) -> VectorDatabaseService:
    """获取向量数据库服务实例"""
    return VectorDatabaseService(db, cache_service)
