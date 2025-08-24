"""向量数据库集成服务 - Milvus向量数据库管理和操作."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from app.ai.services.deepseek_embedding_service import DeepSeekEmbeddingService
from app.resources.utils.milvus_client import MilvusClient
from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class VectorService:
    """向量数据库集成服务 - 管理文档向量化和检索."""

    def __init__(self, cache_service: CacheService | None = None) -> None:
        """初始化向量服务."""
        self.cache_service = cache_service
        self.milvus_client = MilvusClient()
        self.embedding_service = DeepSeekEmbeddingService(cache_service)

        # 向量配置
        self.vector_config = {
            "dimension": 1536,  # DeepSeek embedding维度
            "index_type": "IVF_FLAT",  # 索引类型
            "metric_type": "L2",  # 距离度量
            "nlist": 1024,  # 聚类中心数量
        }

        # 集合配置
        self.collection_config = {
            "documents": {
                "name": "document_vectors",
                "description": "文档向量集合",
                "fields": [
                    {
                        "name": "id",
                        "type": "int64",
                        "is_primary": True,
                        "auto_id": True,
                    },
                    {"name": "document_id", "type": "int64"},
                    {"name": "chunk_id", "type": "int64"},
                    {"name": "vector", "type": "float_vector", "dimension": 1536},
                    {"name": "content", "type": "varchar", "max_length": 65535},
                    {"name": "metadata", "type": "varchar", "max_length": 65535},
                ],
            }
        }

    async def initialize_collections(self) -> bool:
        """初始化向量集合."""
        try:
            # 连接Milvus
            await self.milvus_client.connect()

            # 创建文档向量集合
            collection_name: str = str(self.collection_config["documents"]["name"])
            if not await self.milvus_client.has_collection(collection_name):
                fields_config: list[dict[str, Any]] = [
                    dict(field) if isinstance(field, dict) else {}
                    for field in self.collection_config["documents"]["fields"]
                ]
                description: str = str(self.collection_config["documents"]["description"])
                await self.milvus_client.create_collection(
                    collection_name=collection_name,
                    fields=fields_config,
                    description=description,
                )

                # 创建索引
                await self.milvus_client.create_index(
                    collection_name=collection_name,
                    field_name="vector",
                    index_params={
                        "index_type": self.vector_config["index_type"],
                        "metric_type": self.vector_config["metric_type"],
                        "params": {"nlist": self.vector_config["nlist"]},
                    },
                )

                logger.info(f"Created collection: {collection_name}")

            # 加载集合到内存
            await self.milvus_client.load_collection(collection_name)

            logger.info("Vector collections initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize collections: {str(e)}")
            return False

    async def insert_document_vectors(self, document_id: int, chunks: list[dict[str, Any]]) -> bool:
        """插入文档向量."""
        try:
            collection_name: str = str(self.collection_config["documents"]["name"])

            # 准备向量化任务
            vectorization_tasks = []
            for chunk in chunks:
                task = self.embedding_service.vectorize_text(chunk["content"])
                vectorization_tasks.append(task)

            # 批量向量化
            vectors = await asyncio.gather(*vectorization_tasks, return_exceptions=True)

            # 准备插入数据
            insert_data = []
            for i, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False)):
                if isinstance(vector, Exception):
                    logger.error(f"Vectorization failed for chunk {i}: {str(vector)}")
                    continue

                insert_data.append(
                    {
                        "document_id": document_id,
                        "chunk_id": chunk.get("chunk_id", i),
                        "vector": vector,
                        "content": chunk["content"][:65535],  # 限制长度
                        "metadata": str(chunk.get("metadata", {}))[:65535],
                    }
                )

            if not insert_data:
                logger.warning(f"No valid vectors to insert for document {document_id}")
                return False

            # 插入向量
            result = await self.milvus_client.insert(
                collection_name=collection_name, data=insert_data
            )

            logger.info(
                f"Inserted {len(insert_data)} vectors for document {document_id}, "
                f"insert_count: {result.insert_count if result else 0}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to insert document vectors: {str(e)}")
            return False

    async def search_similar_vectors(
        self, query_text: str, top_k: int = 10, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """搜索相似向量."""
        try:
            # 向量化查询文本
            query_vector = await self.embedding_service.vectorize_text(query_text)

            # 构建搜索参数
            search_params = {
                "metric_type": self.vector_config["metric_type"],
                "params": {"nprobe": 16},
            }

            # 构建过滤表达式
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if key == "document_id" and isinstance(value, int):
                        filter_conditions.append(f"document_id == {value}")
                    elif key == "document_ids" and isinstance(value, list):
                        ids_str = ",".join(map(str, value))
                        filter_conditions.append(f"document_id in [{ids_str}]")

                if filter_conditions:
                    filter_expr = " and ".join(filter_conditions)

            # 执行搜索
            collection_name: str = str(self.collection_config["documents"]["name"])
            results = await self.milvus_client.search(
                collection_name=collection_name,
                vectors=[query_vector],
                vector_field="vector",
                search_params=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["document_id", "chunk_id", "content", "metadata"],
            )

            # 处理搜索结果
            search_results = []
            if results and len(results) > 0:
                for hit in results[0]:  # 只有一个查询向量
                    search_results.append(
                        {
                            "id": hit.id,
                            "document_id": hit.entity.get("document_id"),
                            "chunk_id": hit.entity.get("chunk_id"),
                            "content": hit.entity.get("content"),
                            "metadata": hit.entity.get("metadata"),
                            "distance": hit.distance,
                            "similarity_score": 1.0 / (1.0 + hit.distance),  # 转换为相似度分数
                        }
                    )

            logger.info(
                f"Vector search completed: query_length={len(query_text)}, "
                f"results_count={len(search_results)}"
            )
            return search_results

        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []

    async def delete_document_vectors(self, document_id: int) -> bool:
        """删除文档向量."""
        try:
            collection_name: str = str(self.collection_config["documents"]["name"])

            # 删除指定文档的所有向量
            delete_expr = f"document_id == {document_id}"
            await self.milvus_client.delete(collection_name=collection_name, expr=delete_expr)

            logger.info(f"Deleted vectors for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document vectors: {str(e)}")
            return False

    async def get_collection_stats(self) -> dict[str, Any]:
        """获取集合统计信息."""
        try:
            collection_name: str = str(self.collection_config["documents"]["name"])

            # 获取集合信息
            stats = await self.milvus_client.get_collection_stats(collection_name)

            return {
                "collection_name": collection_name,
                "total_entities": stats.get("row_count", 0),
                "indexed": stats.get("indexed", False),
                "last_updated": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    async def update_document_vectors(self, document_id: int, chunks: list[dict[str, Any]]) -> bool:
        """更新文档向量."""
        try:
            # 先删除旧向量
            await self.delete_document_vectors(document_id)

            # 插入新向量
            return await self.insert_document_vectors(document_id, chunks)

        except Exception as e:
            logger.error(f"Failed to update document vectors: {str(e)}")
            return False

    async def batch_search_vectors(
        self, queries: list[str], top_k: int = 10, filters: dict[str, Any] | None = None
    ) -> list[list[dict[str, Any]]]:
        """批量向量搜索."""
        try:
            # 批量向量化查询
            vectorization_tasks = [
                self.embedding_service.vectorize_text(query) for query in queries
            ]
            query_vectors = await asyncio.gather(*vectorization_tasks, return_exceptions=True)

            # 过滤有效向量
            valid_vectors = []
            valid_indices = []
            for i, vector in enumerate(query_vectors):
                if not isinstance(vector, Exception):
                    valid_vectors.append(vector)
                    valid_indices.append(i)

            if not valid_vectors:
                logger.warning("No valid query vectors for batch search")
                return [[] for _ in queries]

            # 构建搜索参数
            search_params = {
                "metric_type": self.vector_config["metric_type"],
                "params": {"nprobe": 16},
            }

            # 构建过滤表达式
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if key == "document_id" and isinstance(value, int):
                        filter_conditions.append(f"document_id == {value}")
                    elif key == "document_ids" and isinstance(value, list):
                        ids_str = ",".join(map(str, value))
                        filter_conditions.append(f"document_id in [{ids_str}]")

                if filter_conditions:
                    filter_expr = " and ".join(filter_conditions)

            # 执行批量搜索
            collection_name: str = str(self.collection_config["documents"]["name"])
            valid_vectors_list: list[list[float]] = [
                v for v in valid_vectors if isinstance(v, list)
            ]
            results = await self.milvus_client.search(
                collection_name=collection_name,
                vectors=valid_vectors_list,
                vector_field="vector",
                search_params=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["document_id", "chunk_id", "content", "metadata"],
            )

            # 处理搜索结果
            all_results: list[list[dict[str, Any]]] = [[] for _ in queries]

            for result_idx, result in enumerate(results):
                original_idx = valid_indices[result_idx]
                search_results = []

                for hit in result:
                    search_results.append(
                        {
                            "id": hit.id,
                            "document_id": hit.entity.get("document_id"),
                            "chunk_id": hit.entity.get("chunk_id"),
                            "content": hit.entity.get("content"),
                            "metadata": hit.entity.get("metadata"),
                            "distance": hit.distance,
                            "similarity_score": 1.0 / (1.0 + hit.distance),
                        }
                    )

                all_results[original_idx] = search_results

            logger.info(f"Batch vector search completed: {len(queries)} queries")
            return all_results

        except Exception as e:
            logger.error(f"Batch vector search failed: {str(e)}")
            return [[] for _ in queries]

    async def close(self) -> None:
        """关闭连接."""
        try:
            await self.milvus_client.close()
            logger.info("Vector service closed")
        except Exception as e:
            logger.error(f"Failed to close vector service: {str(e)}")
