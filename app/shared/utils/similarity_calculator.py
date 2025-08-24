"""相似度计算器模块

提供多种相似度计算方法，支持向量相似度、文本相似度等。
"""

import asyncio
import logging
import math
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """相似度计算结果"""

    score: float
    metric: str
    details: dict[str, Any]


class SimilarityCalculator:
    """相似度计算器"""

    def __init__(self) -> None:
        """初始化相似度计算器"""
        self.supported_metrics = [
            "cosine",
            "euclidean",
            "manhattan",
            "dot_product",
            "jaccard",
            "hamming",
            "pearson",
            "spearman",
        ]

    async def compute_vector_similarity(
        self, vector1: list[float], vector2: list[float], metric: str = "cosine"
    ) -> SimilarityResult:
        """计算向量相似度"""
        if len(vector1) != len(vector2):
            raise ValueError("Vector dimensions must match")

        if metric not in self.supported_metrics:
            raise ValueError(f"Unsupported metric: {metric}")

        # 在线程池中执行计算密集型操作
        loop = asyncio.get_event_loop()
        score = await loop.run_in_executor(
            None, self._compute_vector_similarity_sync, vector1, vector2, metric
        )

        return SimilarityResult(
            score=score,
            metric=metric,
            details={
                "vector1_dim": len(vector1),
                "vector2_dim": len(vector2),
                "computation_method": "vector_similarity",
            },
        )

    def _compute_vector_similarity_sync(
        self, vector1: list[float], vector2: list[float], metric: str
    ) -> float:
        """同步计算向量相似度"""
        if metric == "cosine":
            return self._cosine_similarity(vector1, vector2)
        elif metric == "euclidean":
            return self._euclidean_distance(vector1, vector2)
        elif metric == "manhattan":
            return self._manhattan_distance(vector1, vector2)
        elif metric == "dot_product":
            return self._dot_product(vector1, vector2)
        elif metric == "pearson":
            return self._pearson_correlation(vector1, vector2)
        else:
            raise ValueError(f"Unsupported vector metric: {metric}")

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(v1, v2, strict=False))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _euclidean_distance(self, v1: list[float], v2: list[float]) -> float:
        """计算欧几里得距离（转换为相似度）"""
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2, strict=False)))
        # 转换为相似度（0-1范围）
        return 1 / (1 + distance)

    def _manhattan_distance(self, v1: list[float], v2: list[float]) -> float:
        """计算曼哈顿距离（转换为相似度）"""
        distance = sum(abs(a - b) for a, b in zip(v1, v2, strict=False))
        # 转换为相似度（0-1范围）
        return 1 / (1 + distance)

    def _dot_product(self, v1: list[float], v2: list[float]) -> float:
        """计算点积"""
        return sum(a * b for a, b in zip(v1, v2, strict=False))

    def _pearson_correlation(self, v1: list[float], v2: list[float]) -> float:
        """计算皮尔逊相关系数"""
        n = len(v1)
        if n == 0:
            return 0.0

        # 计算均值
        mean1 = sum(v1) / n
        mean2 = sum(v2) / n

        # 计算协方差和标准差
        numerator = sum((v1[i] - mean1) * (v2[i] - mean2) for i in range(n))
        sum_sq1 = sum((v1[i] - mean1) ** 2 for i in range(n))
        sum_sq2 = sum((v2[i] - mean2) ** 2 for i in range(n))

        denominator = math.sqrt(sum_sq1 * sum_sq2)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    async def compute_text_similarity(
        self, text1: str, text2: str, method: str = "jaccard"
    ) -> SimilarityResult:
        """计算文本相似度"""
        if method == "jaccard":
            score = await self._jaccard_similarity(text1, text2)
        elif method == "hamming":
            score = await self._hamming_similarity(text1, text2)
        elif method == "levenshtein":
            score = await self._levenshtein_similarity(text1, text2)
        else:
            raise ValueError(f"Unsupported text similarity method: {method}")

        return SimilarityResult(
            score=score,
            metric=method,
            details={
                "text1_length": len(text1),
                "text2_length": len(text2),
                "computation_method": "text_similarity",
            },
        )

    async def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """计算Jaccard相似度"""
        # 转换为词集合
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # 计算交集和并集
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        if union == 0:
            return 0.0

        return intersection / union

    async def _hamming_similarity(self, text1: str, text2: str) -> float:
        """计算汉明相似度"""
        # 填充到相同长度
        max_len = max(len(text1), len(text2))
        text1 = text1.ljust(max_len)
        text2 = text2.ljust(max_len)

        # 计算不同字符数
        differences = sum(c1 != c2 for c1, c2 in zip(text1, text2, strict=False))

        if max_len == 0:
            return 1.0

        # 转换为相似度
        return 1 - (differences / max_len)

    async def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """计算编辑距离相似度"""
        # 计算编辑距离
        distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))

        if max_len == 0:
            return 1.0

        # 转换为相似度
        return 1 - (distance / max_len)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    async def batch_compute_similarities(
        self,
        query_vector: list[float],
        candidate_vectors: list[list[float]],
        metric: str = "cosine",
        top_k: int | None = None,
    ) -> list[tuple[int, SimilarityResult]]:
        """批量计算相似度并排序"""
        results = []

        for i, candidate_vector in enumerate(candidate_vectors):
            similarity = await self.compute_vector_similarity(
                query_vector, candidate_vector, metric
            )
            results.append((i, similarity))

        # 按相似度排序
        results.sort(key=lambda x: x[1].score, reverse=True)

        # 返回top_k结果
        if top_k is not None:
            results = results[:top_k]

        return results

    async def compute_semantic_similarity(
        self, text1: str, text2: str, embedding_model: str = "openai"
    ) -> SimilarityResult:
        """计算语义相似度"""
        try:
            from app.shared.utils.embedding_utils import embedding_utils

            # 获取文本向量
            embeddings = await embedding_utils.get_embeddings([text1, text2], embedding_model)

            if len(embeddings) != 2:
                raise ValueError("Failed to generate embeddings")

            # 计算向量相似度
            similarity = await self.compute_vector_similarity(
                embeddings[0], embeddings[1], "cosine"
            )

            similarity.details.update(
                {
                    "embedding_model": embedding_model,
                    "computation_method": "semantic_similarity",
                }
            )

            return similarity

        except ImportError:
            # 如果embedding_utils不可用，使用文本相似度
            logger.warning("Embedding utils not available, falling back to text similarity")
            return await self.compute_text_similarity(text1, text2, "jaccard")

    async def find_most_similar(
        self,
        query: str | list[float],
        candidates: list[str | list[float]],
        metric: str = "cosine",
        threshold: float = 0.0,
    ) -> list[tuple[int, SimilarityResult]]:
        """找到最相似的候选项"""
        results = []

        for i, candidate in enumerate(candidates):
            if isinstance(query, str) and isinstance(candidate, str):
                # 文本相似度
                similarity = await self.compute_text_similarity(query, candidate, metric)
            elif isinstance(query, list) and isinstance(candidate, list):
                # 向量相似度
                similarity = await self.compute_vector_similarity(query, candidate, metric)
            else:
                raise ValueError("Query and candidates must be of the same type")

            if similarity.score >= threshold:
                results.append((i, similarity))

        # 按相似度排序
        results.sort(key=lambda x: x[1].score, reverse=True)

        return results

    def get_supported_metrics(self) -> list[str]:
        """获取支持的相似度度量"""
        return self.supported_metrics.copy()

    async def compute_diversity_score(
        self, vectors: list[list[float]], metric: str = "cosine"
    ) -> float:
        """计算向量集合的多样性分数"""
        if len(vectors) < 2:
            return 0.0

        total_similarity = 0.0
        count = 0

        # 计算所有向量对的相似度
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                similarity = await self.compute_vector_similarity(vectors[i], vectors[j], metric)
                total_similarity += similarity.score
                count += 1

        # 多样性 = 1 - 平均相似度
        average_similarity = total_similarity / count if count > 0 else 0.0
        return 1.0 - average_similarity


# 全局相似度计算器实例
similarity_calculator = SimilarityCalculator()
