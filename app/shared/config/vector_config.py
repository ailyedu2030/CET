"""Milvus向量数据库配置模块

提供Milvus向量数据库的配置管理，包括连接配置、集合配置、
索引配置和性能优化配置。
"""

import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, validator


@dataclass
class MilvusConnectionConfig:
    """Milvus连接配置"""

    host: str
    port: int = 19530
    user: str = ""
    password: str = ""
    secure: bool = False
    timeout: int = 30

    def __post_init__(self) -> None:
        """验证配置"""
        if not self.host:
            raise ValueError("Milvus host cannot be empty")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("Milvus port must be between 1 and 65535")


@dataclass
class CollectionConfig:
    """向量集合配置"""

    name: str
    dimension: int
    metric_type: str = "COSINE"
    description: str = ""
    auto_id: bool = True

    def __post_init__(self) -> None:
        """验证配置"""
        if not self.name:
            raise ValueError("Collection name cannot be empty")
        if self.dimension <= 0:
            raise ValueError("Dimension must be positive")
        if self.metric_type not in ["L2", "IP", "COSINE", "HAMMING", "JACCARD"]:
            raise ValueError(f"Invalid metric type: {self.metric_type}")


class IndexConfig(BaseModel):
    """索引配置"""

    model_config = {"from_attributes": True}

    index_type: str = Field(..., description="索引类型")
    metric_type: str = Field(..., description="距离度量类型")
    params: dict[str, Any] = Field(default_factory=dict, description="索引参数")

    @validator("index_type")
    def validate_index_type(cls, v: str) -> str:
        """验证索引类型"""
        valid_types = ["FLAT", "IVF_FLAT", "IVF_SQ8", "IVF_PQ", "HNSW", "ANNOY"]
        if v not in valid_types:
            raise ValueError(f"Invalid index type: {v}. Must be one of {valid_types}")
        return v

    @validator("metric_type")
    def validate_metric_type(cls, v: str) -> str:
        """验证距离度量类型"""
        valid_types = ["L2", "IP", "COSINE", "HAMMING", "JACCARD"]
        if v not in valid_types:
            raise ValueError(f"Invalid metric type: {v}. Must be one of {valid_types}")
        return v


class EmbeddingConfig(BaseModel):
    """向量化配置"""

    model_config = {"from_attributes": True}

    model_name: str = Field(..., description="嵌入模型名称")
    dimension: int = Field(..., description="向量维度")
    max_length: int = Field(default=512, description="最大文本长度")
    batch_size: int = Field(default=32, description="批处理大小")
    normalize: bool = Field(default=True, description="是否归一化")

    @validator("dimension")
    def validate_dimension(cls, v: int) -> int:
        """验证向量维度"""
        if v <= 0:
            raise ValueError("Dimension must be positive")
        return v

    @validator("max_length")
    def validate_max_length(cls, v: int) -> int:
        """验证最大长度"""
        if v <= 0:
            raise ValueError("Max length must be positive")
        return v


class VectorConfig:
    """Milvus向量数据库配置管理器"""

    def __init__(self) -> None:
        """初始化配置"""
        self.connection = self._load_connection_config()
        self.collections = self._load_collection_configs()
        self.indexes = self._load_index_configs()
        self.embeddings = self._load_embedding_configs()
        self.performance = self._load_performance_config()

    def _load_connection_config(self) -> MilvusConnectionConfig:
        """加载连接配置"""
        return MilvusConnectionConfig(
            host=os.getenv("MILVUS_HOST", "localhost"),
            port=int(os.getenv("MILVUS_PORT", "19530")),
            user=os.getenv("MILVUS_USER", ""),
            password=os.getenv("MILVUS_PASSWORD", ""),
            secure=os.getenv("MILVUS_SECURE", "false").lower() == "true",
            timeout=int(os.getenv("MILVUS_TIMEOUT", "30")),
        )

    def _load_collection_configs(self) -> dict[str, CollectionConfig]:
        """加载集合配置"""
        return {
            "documents": CollectionConfig(
                name="cet4_documents",
                dimension=1536,  # OpenAI text-embedding-ada-002
                metric_type="COSINE",
                description="文档向量集合",
                auto_id=True,
            ),
            "questions": CollectionConfig(
                name="cet4_questions",
                dimension=1536,
                metric_type="COSINE",
                description="题目向量集合",
                auto_id=True,
            ),
            "resources": CollectionConfig(
                name="cet4_resources",
                dimension=1536,
                metric_type="COSINE",
                description="学习资源向量集合",
                auto_id=True,
            ),
            "knowledge": CollectionConfig(
                name="cet4_knowledge",
                dimension=1536,
                metric_type="COSINE",
                description="知识点向量集合",
                auto_id=True,
            ),
        }

    def _load_index_configs(self) -> dict[str, IndexConfig]:
        """加载索引配置"""
        return {
            "hnsw": IndexConfig(
                index_type="HNSW",
                metric_type="COSINE",
                params={"M": 16, "efConstruction": 200},
            ),
            "ivf_flat": IndexConfig(
                index_type="IVF_FLAT", metric_type="COSINE", params={"nlist": 1024}
            ),
            "ivf_pq": IndexConfig(
                index_type="IVF_PQ",
                metric_type="COSINE",
                params={"nlist": 1024, "m": 8, "nbits": 8},
            ),
        }

    def _load_embedding_configs(self) -> dict[str, EmbeddingConfig]:
        """加载向量化配置"""
        return {
            "openai": EmbeddingConfig(
                model_name="text-embedding-ada-002",
                dimension=1536,
                max_length=8192,
                batch_size=100,
                normalize=True,
            ),
            "sentence_transformer": EmbeddingConfig(
                model_name="all-MiniLM-L6-v2",
                dimension=384,
                max_length=512,
                batch_size=32,
                normalize=True,
            ),
            "chinese": EmbeddingConfig(
                model_name="text2vec-base-chinese",
                dimension=768,
                max_length=512,
                batch_size=32,
                normalize=True,
            ),
        }

    def _load_performance_config(self) -> dict[str, Any]:
        """加载性能配置"""
        config: dict[str, Any] = {
            "search_params": {
                "hnsw": {"ef": 64},
                "ivf_flat": {"nprobe": 10},
                "ivf_pq": {"nprobe": 10},
            },
            "batch_size": int(os.getenv("MILVUS_BATCH_SIZE", "1000")),
            "timeout": int(os.getenv("MILVUS_SEARCH_TIMEOUT", "10")),
            "consistency_level": os.getenv("MILVUS_CONSISTENCY_LEVEL", "Strong"),
            "replica_number": int(os.getenv("MILVUS_REPLICA_NUMBER", "1")),
            "resource_groups": ["default"],
            "cache_size": int(os.getenv("MILVUS_CACHE_SIZE", "2048")),  # MB
        }
        return config

    def get_collection_config(self, collection_type: str) -> CollectionConfig | None:
        """获取集合配置"""
        return self.collections.get(collection_type)

    def get_index_config(self, index_type: str) -> IndexConfig | None:
        """获取索引配置"""
        return self.indexes.get(index_type)

    def get_embedding_config(self, model_type: str) -> EmbeddingConfig | None:
        """获取向量化配置"""
        return self.embeddings.get(model_type)

    def get_search_params(self, index_type: str) -> dict[str, Any]:
        """获取搜索参数"""
        params: dict[str, Any] = self.performance["search_params"].get(index_type, {})
        return params

    def get_collection_name(self, collection_type: str) -> str:
        """获取集合名称"""
        config = self.get_collection_config(collection_type)
        return config.name if config else f"cet4_{collection_type}"

    def is_collection_type_valid(self, collection_type: str) -> bool:
        """检查集合类型是否有效"""
        return collection_type in self.collections

    def get_default_index_type(self) -> str:
        """获取默认索引类型"""
        return "hnsw"  # HNSW通常提供最好的性能平衡

    def get_default_embedding_model(self) -> str:
        """获取默认向量化模型"""
        return "openai"  # OpenAI embedding通常质量最高


# 全局配置实例
vector_config = VectorConfig()
