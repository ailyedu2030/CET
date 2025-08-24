"""向量工具类 - 向量操作和计算的工具函数."""

import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class VectorUtils:
    """向量工具类 - 提供向量操作和计算功能."""

    @staticmethod
    def cosine_similarity(vector1: list[float], vector2: list[float]) -> float:
        """计算余弦相似度."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            # 转换为numpy数组
            v1 = np.array(vector1)
            v2 = np.array(vector2)

            # 计算余弦相似度
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {str(e)}")
            return 0.0

    @staticmethod
    def euclidean_distance(vector1: list[float], vector2: list[float]) -> float:
        """计算欧几里得距离."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            # 转换为numpy数组
            v1 = np.array(vector1)
            v2 = np.array(vector2)

            # 计算欧几里得距离
            distance = np.linalg.norm(v1 - v2)
            return float(distance)

        except Exception as e:
            logger.error(f"Euclidean distance calculation failed: {str(e)}")
            return float("inf")

    @staticmethod
    def manhattan_distance(vector1: list[float], vector2: list[float]) -> float:
        """计算曼哈顿距离."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            distance = sum(abs(a - b) for a, b in zip(vector1, vector2, strict=False))
            return float(distance)

        except Exception as e:
            logger.error(f"Manhattan distance calculation failed: {str(e)}")
            return float("inf")

    @staticmethod
    def normalize_vector(vector: list[float]) -> list[float]:
        """向量归一化."""
        try:
            v = np.array(vector)
            norm = np.linalg.norm(v)

            if norm == 0:
                return vector

            normalized = v / norm
            return list(normalized.tolist())

        except Exception as e:
            logger.error(f"Vector normalization failed: {str(e)}")
            return vector

    @staticmethod
    def vector_magnitude(vector: list[float]) -> float:
        """计算向量模长."""
        try:
            v = np.array(vector)
            magnitude = np.linalg.norm(v)
            return float(magnitude)

        except Exception as e:
            logger.error(f"Vector magnitude calculation failed: {str(e)}")
            return 0.0

    @staticmethod
    def dot_product(vector1: list[float], vector2: list[float]) -> float:
        """计算向量点积."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            v1 = np.array(vector1)
            v2 = np.array(vector2)

            dot_prod = np.dot(v1, v2)
            return float(dot_prod)

        except Exception as e:
            logger.error(f"Dot product calculation failed: {str(e)}")
            return 0.0

    @staticmethod
    def vector_add(vector1: list[float], vector2: list[float]) -> list[float]:
        """向量加法."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            v1 = np.array(vector1)
            v2 = np.array(vector2)

            result = v1 + v2
            return list(result.tolist())

        except Exception as e:
            logger.error(f"Vector addition failed: {str(e)}")
            return vector1

    @staticmethod
    def vector_subtract(vector1: list[float], vector2: list[float]) -> list[float]:
        """向量减法."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            v1 = np.array(vector1)
            v2 = np.array(vector2)

            result = v1 - v2
            return list(result.tolist())

        except Exception as e:
            logger.error(f"Vector subtraction failed: {str(e)}")
            return vector1

    @staticmethod
    def scalar_multiply(vector: list[float], scalar: float) -> list[float]:
        """标量乘法."""
        try:
            v = np.array(vector)
            result = v * scalar
            return list(result.tolist())

        except Exception as e:
            logger.error(f"Scalar multiplication failed: {str(e)}")
            return vector

    @staticmethod
    def vector_mean(vectors: list[list[float]]) -> list[float]:
        """计算向量均值."""
        try:
            if not vectors:
                return []

            # 检查维度一致性
            dimension = len(vectors[0])
            for vector in vectors:
                if len(vector) != dimension:
                    raise ValueError("向量维度不一致")

            # 计算均值
            vectors_array = np.array(vectors)
            mean_vector = np.mean(vectors_array, axis=0)
            return list(mean_vector.tolist())

        except Exception as e:
            logger.error(f"Vector mean calculation failed: {str(e)}")
            return vectors[0] if vectors else []

    @staticmethod
    def find_most_similar(
        query_vector: list[float], candidate_vectors: list[list[float]], top_k: int = 5
    ) -> list[tuple[int, float]]:
        """找到最相似的向量."""
        try:
            similarities = []

            for i, candidate in enumerate(candidate_vectors):
                similarity = VectorUtils.cosine_similarity(query_vector, candidate)
                similarities.append((i, similarity))

            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)

            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Finding most similar vectors failed: {str(e)}")
            return []

    @staticmethod
    def cluster_vectors(vectors: list[list[float]], num_clusters: int = 5) -> dict[str, Any]:
        """简单的向量聚类."""
        try:
            if not vectors or num_clusters <= 0:
                return {"clusters": [], "centroids": []}

            # 使用K-means聚类（简化实现）
            vectors_array = np.array(vectors)

            # 随机初始化聚类中心
            np.random.seed(42)
            centroids = vectors_array[np.random.choice(len(vectors), num_clusters, replace=False)]

            max_iterations = 100
            for _iteration in range(max_iterations):
                # 分配点到最近的聚类中心
                distances = np.sqrt(((vectors_array - centroids[:, np.newaxis]) ** 2).sum(axis=2))
                closest_cluster = np.argmin(distances, axis=0)

                # 更新聚类中心
                new_centroids = np.array(
                    [vectors_array[closest_cluster == k].mean(axis=0) for k in range(num_clusters)]
                )

                # 检查收敛
                if np.allclose(centroids, new_centroids):
                    break

                centroids = new_centroids

            # 组织结果
            clusters: list[list[int]] = [[] for _ in range(num_clusters)]
            for i, cluster_id in enumerate(closest_cluster):
                clusters[cluster_id].append(i)

            return {
                "clusters": clusters,
                "centroids": list(centroids.tolist()),
                "iterations": 1,  # 简化实现，返回固定值
            }

        except Exception as e:
            logger.error(f"Vector clustering failed: {str(e)}")
            return {"clusters": [], "centroids": []}

    @staticmethod
    def calculate_vector_stats(vectors: list[list[float]]) -> dict[str, Any]:
        """计算向量统计信息."""
        try:
            if not vectors:
                return {}

            vectors_array = np.array(vectors)

            return {
                "count": len(vectors),
                "dimension": len(vectors[0]),
                "mean_magnitude": float(np.mean([np.linalg.norm(v) for v in vectors_array])),
                "std_magnitude": float(np.std([np.linalg.norm(v) for v in vectors_array])),
                "min_magnitude": float(np.min([np.linalg.norm(v) for v in vectors_array])),
                "max_magnitude": float(np.max([np.linalg.norm(v) for v in vectors_array])),
                "mean_vector": np.mean(vectors_array, axis=0).tolist(),
                "std_vector": np.std(vectors_array, axis=0).tolist(),
            }

        except Exception as e:
            logger.error(f"Vector statistics calculation failed: {str(e)}")
            return {}

    @staticmethod
    def is_valid_vector(vector: Any, expected_dimension: int | None = None) -> bool:
        """验证向量有效性."""
        try:
            # 检查是否为列表
            if not isinstance(vector, list):
                return False

            # 检查是否为空
            if not vector:
                return False

            # 检查所有元素是否为数字
            for element in vector:
                if not isinstance(element, int | float):
                    return False
                if math.isnan(element) or math.isinf(element):
                    return False

            # 检查维度
            if expected_dimension is not None and len(vector) != expected_dimension:
                return False

            return True

        except Exception as e:
            logger.error(f"Vector validation failed: {str(e)}")
            return False

    @staticmethod
    def generate_random_vector(dimension: int, mean: float = 0.0, std: float = 1.0) -> list[float]:
        """生成随机向量."""
        try:
            np.random.seed()  # 使用当前时间作为种子
            vector = np.random.normal(mean, std, dimension)
            return list(vector.tolist())

        except Exception as e:
            logger.error(f"Random vector generation failed: {str(e)}")
            return [0.0] * dimension

    @staticmethod
    def interpolate_vectors(
        vector1: list[float], vector2: list[float], alpha: float = 0.5
    ) -> list[float]:
        """向量插值."""
        try:
            if len(vector1) != len(vector2):
                raise ValueError("向量维度不匹配")

            if not 0 <= alpha <= 1:
                raise ValueError("插值参数alpha必须在[0,1]范围内")

            v1 = np.array(vector1)
            v2 = np.array(vector2)

            interpolated = (1 - alpha) * v1 + alpha * v2
            return list(interpolated.tolist())

        except Exception as e:
            logger.error(f"Vector interpolation failed: {str(e)}")
            return vector1

    @staticmethod
    def batch_cosine_similarity(
        query_vector: list[float], vectors: list[list[float]]
    ) -> list[float]:
        """批量计算余弦相似度."""
        try:
            if not vectors:
                return []

            query_array = np.array(query_vector)
            vectors_array = np.array(vectors)

            # 归一化
            query_norm = np.linalg.norm(query_array)
            vectors_norms = np.linalg.norm(vectors_array, axis=1)

            if query_norm == 0:
                return [0.0] * len(vectors)

            # 计算点积
            dot_products = np.dot(vectors_array, query_array)

            # 计算余弦相似度
            similarities = dot_products / (query_norm * vectors_norms)

            # 处理除零情况
            similarities = np.nan_to_num(similarities, nan=0.0)

            return list(similarities.tolist())

        except Exception as e:
            logger.error(f"Batch cosine similarity calculation failed: {str(e)}")
            return [0.0] * len(vectors)

    @staticmethod
    def reduce_dimension_pca(
        vectors: list[list[float]], target_dimension: int
    ) -> list[list[float]]:
        """使用PCA降维."""
        try:
            if not vectors or target_dimension <= 0:
                return vectors

            vectors_array = np.array(vectors)
            original_dim = vectors_array.shape[1]

            if target_dimension >= original_dim:
                return vectors

            # 中心化数据
            mean_vector = np.mean(vectors_array, axis=0)
            centered_data = vectors_array - mean_vector

            # 计算协方差矩阵
            cov_matrix = np.cov(centered_data.T)

            # 特征值分解
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

            # 按特征值排序
            sorted_indices = np.argsort(eigenvalues)[::-1]
            top_eigenvectors = eigenvectors[:, sorted_indices[:target_dimension]]

            # 投影到新空间
            reduced_vectors = np.dot(centered_data, top_eigenvectors)

            return [list(row) for row in reduced_vectors.tolist()]

        except Exception as e:
            logger.error(f"PCA dimension reduction failed: {str(e)}")
            return vectors
