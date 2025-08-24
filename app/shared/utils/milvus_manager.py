"""Milvus向量数据库管理器

提供Milvus向量数据库的连接管理、集合操作、索引管理等功能。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from app.shared.config.vector_config import CollectionConfig, vector_config

logger = logging.getLogger(__name__)

try:
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        connections,
        utility,
    )

    MILVUS_AVAILABLE = True
except ImportError:
    # 如果Milvus不可用，创建模拟类
    class connections:  # type: ignore[no-redef]
        @staticmethod
        def connect(*args: Any, **kwargs: Any) -> None:
            pass

        @staticmethod
        def disconnect(*args: Any, **kwargs: Any) -> None:
            pass

        @staticmethod
        def list_connections() -> list[str]:
            return ["default"]

    class Collection:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.name = kwargs.get("name", "mock_collection")

        def insert(self, data: list[dict[str, Any]]) -> Any:
            return {"insert_count": len(data)}

        def search(self, *args: Any, **kwargs: Any) -> list[Any]:
            return []

        def query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            return []

        def delete(self, *args: Any, **kwargs: Any) -> Any:
            return {"delete_count": 1}

        def load(self) -> None:
            pass

        def release(self) -> None:
            pass

        def create_index(self, *args: Any, **kwargs: Any) -> None:
            pass

        def drop_index(self) -> None:
            pass

        @property
        def num_entities(self) -> int:
            return 0

    class CollectionSchema:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class FieldSchema:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class DataType:  # type: ignore[no-redef]
        INT64 = "INT64"
        VARCHAR = "VARCHAR"
        FLOAT_VECTOR = "FLOAT_VECTOR"

    class utility:  # type: ignore[no-redef]
        @staticmethod
        def has_collection(name: str) -> bool:
            return True

        @staticmethod
        def drop_collection(name: str) -> None:
            pass

        @staticmethod
        def list_collections() -> list[str]:
            return []

    MILVUS_AVAILABLE = False


class MilvusManagerError(Exception):
    """Milvus管理器异常"""

    pass


class MilvusManager:
    """Milvus向量数据库管理器"""

    def __init__(self, connection_alias: str = "default") -> None:
        """初始化Milvus管理器"""
        self.config = vector_config
        self.connection_alias = connection_alias
        self._connected = False
        self._collections: dict[str, Collection] = {}

    async def connect(self) -> bool:
        """连接到Milvus服务器"""
        try:
            connection_config = self.config.connection

            # 在线程池中执行同步连接操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                connections.connect,
                self.connection_alias,
                connection_config.host,
                connection_config.port,
                connection_config.user,
                connection_config.password,
            )

            # 测试连接
            await self._test_connection()

            # 初始化集合
            await self._initialize_collections()

            self._connected = True
            logger.info(
                f"Successfully connected to Milvus at {connection_config.host}:{connection_config.port}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            self._connected = False
            return False

    async def _test_connection(self) -> None:
        """测试Milvus连接"""
        try:
            loop = asyncio.get_event_loop()
            collections = await loop.run_in_executor(None, utility.list_collections)
            logger.debug(f"Connected to Milvus, found {len(collections)} collections")
        except Exception as e:
            raise MilvusManagerError(f"Connection test failed: {str(e)}") from e

    async def _initialize_collections(self) -> None:
        """初始化向量集合"""
        loop = asyncio.get_event_loop()

        for collection_type, collection_config in self.config.collections.items():
            try:
                # 检查集合是否存在
                collection_exists = await loop.run_in_executor(
                    None, utility.has_collection, collection_config.name
                )

                if not collection_exists:
                    # 创建集合
                    await self._create_collection(collection_config)
                    logger.info(f"Created collection: {collection_config.name}")

                # 加载集合到内存
                collection = Collection(collection_config.name)
                await loop.run_in_executor(None, collection.load)
                self._collections[collection_type] = collection

            except Exception as e:
                logger.error(f"Failed to initialize collection {collection_config.name}: {str(e)}")
                raise MilvusManagerError(f"Collection initialization failed: {str(e)}") from e

    async def _create_collection(self, config: CollectionConfig) -> None:
        """创建向量集合"""
        try:
            # 定义字段架构
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=config.auto_id,
                ),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=config.dimension),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="timestamp", dtype=DataType.INT64),
            ]

            # 创建集合架构
            schema = CollectionSchema(fields=fields, description=config.description)

            # 在线程池中创建集合
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: Collection(name=config.name, schema=schema, using=self.connection_alias),
            )

            # 创建索引
            await self._create_index(config.name, config.metric_type)

        except Exception as e:
            logger.error(f"Failed to create collection {config.name}: {str(e)}")
            raise MilvusManagerError(f"Collection creation failed: {str(e)}") from e

    async def _create_index(self, collection_name: str, metric_type: str) -> None:
        """为集合创建索引"""
        try:
            collection = Collection(collection_name)

            # 获取默认索引配置
            index_config = self.config.get_index_config(self.config.get_default_index_type())
            if not index_config:
                raise MilvusManagerError("Default index config not found")

            # 创建向量字段索引
            index_params = {
                "index_type": index_config.index_type,
                "metric_type": metric_type,
                "params": index_config.params,
            }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, collection.create_index, "vector", index_params)

            logger.info(f"Created index for collection {collection_name}")

        except Exception as e:
            logger.error(f"Failed to create index for {collection_name}: {str(e)}")
            raise MilvusManagerError(f"Index creation failed: {str(e)}") from e

    async def insert_vectors(
        self,
        collection_type: str,
        texts: list[str],
        vectors: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """插入向量数据"""
        if not self._connected:
            raise MilvusManagerError("Not connected to Milvus")

        if collection_type not in self._collections:
            raise MilvusManagerError(f"Collection type {collection_type} not found")

        if len(texts) != len(vectors):
            raise MilvusManagerError("Texts and vectors length mismatch")

        try:
            collection = self._collections[collection_type]

            # 准备数据
            current_time = int(datetime.now().timestamp() * 1000)
            data = {
                "text": texts,
                "vector": vectors,
                "metadata": [
                    str(meta) if meta else "{}" for meta in (metadata or [{}] * len(texts))
                ],
                "timestamp": [current_time] * len(texts),
            }

            # 插入数据
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, collection.insert, data)

            logger.info(f"Inserted {len(texts)} vectors into {collection_type}")
            return {
                "insert_count": (
                    result.insert_count if hasattr(result, "insert_count") else len(texts)
                ),
                "primary_keys": (result.primary_keys if hasattr(result, "primary_keys") else []),
            }

        except Exception as e:
            logger.error(f"Failed to insert vectors: {str(e)}")
            raise MilvusManagerError(f"Vector insertion failed: {str(e)}") from e

    async def search_vectors(
        self,
        collection_type: str,
        query_vectors: list[list[float]],
        top_k: int = 10,
        search_params: dict[str, Any] | None = None,
        expr: str | None = None,
    ) -> list[list[dict[str, Any]]]:
        """搜索相似向量"""
        if not self._connected:
            raise MilvusManagerError("Not connected to Milvus")

        if collection_type not in self._collections:
            raise MilvusManagerError(f"Collection type {collection_type} not found")

        try:
            collection = self._collections[collection_type]

            # 获取搜索参数
            if not search_params:
                index_type = self.config.get_default_index_type()
                search_params = self.config.get_search_params(index_type)

            # 执行搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                collection.search,
                query_vectors,
                "vector",
                search_params,
                top_k,
                expr,
                ["text", "metadata", "timestamp"],
            )

            # 格式化结果
            formatted_results = []
            for result in results:
                hits = []
                for hit in result:
                    hits.append(
                        {
                            "id": hit.id,
                            "distance": hit.distance,
                            "score": 1 - hit.distance if hit.distance <= 1 else 0,
                            "text": hit.entity.get("text", ""),
                            "metadata": hit.entity.get("metadata", "{}"),
                            "timestamp": hit.entity.get("timestamp", 0),
                        }
                    )
                formatted_results.append(hits)

            logger.info(f"Searched {len(query_vectors)} vectors in {collection_type}")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}")
            raise MilvusManagerError(f"Vector search failed: {str(e)}") from e

    async def delete_vectors(self, collection_type: str, expr: str) -> dict[str, Any]:
        """删除向量数据"""
        if not self._connected:
            raise MilvusManagerError("Not connected to Milvus")

        if collection_type not in self._collections:
            raise MilvusManagerError(f"Collection type {collection_type} not found")

        try:
            collection = self._collections[collection_type]

            # 删除数据
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, collection.delete, expr)

            logger.info(f"Deleted vectors from {collection_type} with expr: {expr}")
            return {"delete_count": (result.delete_count if hasattr(result, "delete_count") else 0)}

        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise MilvusManagerError(f"Vector deletion failed: {str(e)}") from e

    async def get_collection_stats(self, collection_type: str) -> dict[str, Any]:
        """获取集合统计信息"""
        if not self._connected:
            raise MilvusManagerError("Not connected to Milvus")

        if collection_type not in self._collections:
            raise MilvusManagerError(f"Collection type {collection_type} not found")

        try:
            collection = self._collections[collection_type]

            # 获取统计信息
            loop = asyncio.get_event_loop()
            num_entities = await loop.run_in_executor(None, lambda: collection.num_entities)

            return {
                "name": collection.name,
                "num_entities": num_entities,
                "collection_type": collection_type,
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            raise MilvusManagerError(f"Collection stats failed: {str(e)}") from e

    async def disconnect(self) -> None:
        """断开连接"""
        try:
            # 释放所有集合
            for collection in self._collections.values():
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, collection.release)

            # 断开连接
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, connections.disconnect, self.connection_alias)

            self._connected = False
            self._collections.clear()
            logger.info("Disconnected from Milvus")

        except Exception as e:
            logger.error(f"Failed to disconnect from Milvus: {str(e)}")

    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    def get_collection_names(self) -> list[str]:
        """获取所有集合名称"""
        return list(self._collections.keys())


# 全局Milvus管理器实例
milvus_manager = MilvusManager()
