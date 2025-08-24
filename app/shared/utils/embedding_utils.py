"""向量化工具模块

提供文本向量化功能，支持多种嵌入模型和批量处理。
"""

import asyncio
import hashlib
import logging
from typing import Any

from app.shared.config.vector_config import EmbeddingConfig, vector_config

logger = logging.getLogger(__name__)

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingError(Exception):
    """向量化异常"""

    pass


class EmbeddingUtils:
    """向量化工具类"""

    def __init__(self) -> None:
        """初始化向量化工具"""
        self.config = vector_config
        self._models: dict[str, Any] = {}
        self._cache: dict[str, list[float]] = {}

    async def get_embeddings(
        self,
        texts: list[str],
        model_type: str = "openai",
        batch_size: int | None = None,
    ) -> list[list[float]]:
        """获取文本向量"""
        if not texts:
            return []

        embedding_config = self.config.get_embedding_config(model_type)
        if not embedding_config:
            raise EmbeddingError(f"Unknown embedding model type: {model_type}")

        # 使用配置的批处理大小
        if batch_size is None:
            batch_size = embedding_config.batch_size

        # 分批处理
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = await self._get_batch_embeddings(
                batch_texts, model_type, embedding_config
            )
            all_embeddings.extend(batch_embeddings)

        logger.info(f"Generated embeddings for {len(texts)} texts using {model_type}")
        return all_embeddings

    async def _get_batch_embeddings(
        self, texts: list[str], model_type: str, config: EmbeddingConfig
    ) -> list[list[float]]:
        """获取批量文本向量"""
        # 检查缓存
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text, model_type)
            if cache_key in self._cache:
                cached_embeddings.append((i, self._cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # 获取未缓存的向量
        if uncached_texts:
            if model_type == "openai":
                new_embeddings = await self._get_openai_embeddings(uncached_texts, config)
            elif model_type == "sentence_transformer":
                new_embeddings = await self._get_sentence_transformer_embeddings(
                    uncached_texts, config
                )
            elif model_type == "chinese":
                new_embeddings = await self._get_chinese_embeddings(uncached_texts, config)
            else:
                raise EmbeddingError(f"Unsupported model type: {model_type}")

            # 缓存新向量
            for text, embedding in zip(uncached_texts, new_embeddings, strict=False):
                cache_key = self._get_cache_key(text, model_type)
                self._cache[cache_key] = embedding
        else:
            new_embeddings = []

        # 合并结果
        result: list[list[float] | None] = [None] * len(texts)

        # 填入缓存的向量
        for i, embedding in cached_embeddings:
            result[i] = embedding

        # 填入新向量
        for i, embedding in zip(uncached_indices, new_embeddings, strict=False):
            result[i] = embedding

        return [emb for emb in result if emb is not None]

    async def _get_openai_embeddings(
        self, texts: list[str], config: EmbeddingConfig
    ) -> list[list[float]]:
        """获取OpenAI向量"""
        if not OPENAI_AVAILABLE:
            # 返回模拟向量
            logger.warning("OpenAI not available, returning mock embeddings")
            return [[0.0] * config.dimension for _ in texts]

        try:
            # 截断过长文本
            truncated_texts = [
                text[: config.max_length] if len(text) > config.max_length else text
                for text in texts
            ]

            # 调用OpenAI API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: openai.Embedding.create(input=truncated_texts, model=config.model_name),
            )

            # 提取向量
            embeddings = [item["embedding"] for item in response["data"]]

            # 归一化（如果需要）
            if config.normalize:
                embeddings = [self._normalize_vector(emb) for emb in embeddings]

            return embeddings

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            raise EmbeddingError(f"OpenAI embedding failed: {str(e)}") from e

    async def _get_sentence_transformer_embeddings(
        self, texts: list[str], config: EmbeddingConfig
    ) -> list[list[float]]:
        """获取Sentence Transformer向量"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            # 返回模拟向量
            logger.warning("Sentence Transformers not available, returning mock embeddings")
            return [[0.0] * config.dimension for _ in texts]

        try:
            # 加载模型
            model = await self._load_sentence_transformer_model(config.model_name)

            # 截断过长文本
            truncated_texts = [
                text[: config.max_length] if len(text) > config.max_length else text
                for text in texts
            ]

            # 生成向量
            loop = asyncio.get_event_loop()
            embeddings_result = await loop.run_in_executor(
                None,
                model.encode,
                truncated_texts,
                {"normalize_embeddings": config.normalize},
            )

            # 确保返回正确的类型
            if hasattr(embeddings_result, "tolist"):
                result_list: list[list[float]] = embeddings_result.tolist()
                return result_list
            else:
                return list(embeddings_result)

        except Exception as e:
            logger.error(f"Sentence Transformer embedding failed: {str(e)}")
            raise EmbeddingError(f"Sentence Transformer embedding failed: {str(e)}") from e

    async def _get_chinese_embeddings(
        self, texts: list[str], config: EmbeddingConfig
    ) -> list[list[float]]:
        """获取中文向量"""
        # 使用Sentence Transformer的中文模型
        return await self._get_sentence_transformer_embeddings(texts, config)

    async def _load_sentence_transformer_model(self, model_name: str) -> Any:
        """加载Sentence Transformer模型"""
        if model_name not in self._models:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(None, SentenceTransformer, model_name)
                self._models[model_name] = model
            else:
                # 创建模拟模型
                class MockModel:
                    def encode(self, texts: list[str], options: dict[str, Any]) -> Any:
                        import numpy as np

                        # 返回模拟向量
                        dimension = 384  # all-MiniLM-L6-v2的维度
                        return np.random.random((len(texts), dimension))

                self._models[model_name] = MockModel()

        return self._models[model_name]

    def _normalize_vector(self, vector: list[float]) -> list[float]:
        """归一化向量"""
        import math

        # 计算向量长度
        length = math.sqrt(sum(x * x for x in vector))

        # 避免除零
        if length == 0:
            return vector

        # 归一化
        return [x / length for x in vector]

    def _get_cache_key(self, text: str, model_type: str) -> str:
        """生成缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{model_type}:{text_hash}"

    async def get_single_embedding(self, text: str, model_type: str = "openai") -> list[float]:
        """获取单个文本向量"""
        embeddings = await self.get_embeddings([text], model_type)
        return embeddings[0] if embeddings else []

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("Embedding cache cleared")

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)

    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表"""
        return list(self.config.embeddings.keys())

    def get_model_dimension(self, model_type: str) -> int:
        """获取模型向量维度"""
        config = self.config.get_embedding_config(model_type)
        return config.dimension if config else 0

    async def compute_similarity(
        self, vector1: list[float], vector2: list[float], metric: str = "cosine"
    ) -> float:
        """计算向量相似度"""
        if len(vector1) != len(vector2):
            raise EmbeddingError("Vector dimensions mismatch")

        if metric == "cosine":
            return self._cosine_similarity(vector1, vector2)
        elif metric == "euclidean":
            return self._euclidean_distance(vector1, vector2)
        elif metric == "dot_product":
            return self._dot_product(vector1, vector2)
        else:
            raise EmbeddingError(f"Unsupported similarity metric: {metric}")

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """计算余弦相似度"""
        import math

        dot_product = sum(a * b for a, b in zip(v1, v2, strict=False))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _euclidean_distance(self, v1: list[float], v2: list[float]) -> float:
        """计算欧几里得距离"""
        import math

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2, strict=False)))

    def _dot_product(self, v1: list[float], v2: list[float]) -> float:
        """计算点积"""
        return sum(a * b for a, b in zip(v1, v2, strict=False))

    async def batch_compute_similarities(
        self,
        query_vector: list[float],
        vectors: list[list[float]],
        metric: str = "cosine",
    ) -> list[float]:
        """批量计算相似度"""
        similarities = []
        for vector in vectors:
            similarity = await self.compute_similarity(query_vector, vector, metric)
            similarities.append(similarity)

        return similarities


# 全局向量化工具实例
embedding_utils = EmbeddingUtils()
