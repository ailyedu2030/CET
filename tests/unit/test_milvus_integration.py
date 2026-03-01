"""Milvus向量数据库集成测试

测试Milvus向量数据库的配置、连接、向量操作等功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.config.vector_config import (
    CollectionConfig,
    EmbeddingConfig,
    IndexConfig,
    vector_config,
)
from app.shared.services.vector_database_service import (
    SearchResult,
    VectorDatabaseService,
    VectorSearchQuery,
)
from app.shared.utils.embedding_utils import EmbeddingError, EmbeddingUtils
from app.shared.utils.milvus_manager import MilvusManager, MilvusManagerError
from app.shared.utils.similarity_calculator import (
    SimilarityCalculator,
    SimilarityResult,
)


class TestVectorConfig:
    """测试向量配置"""

    def test_vector_config_initialization(self):
        """测试向量配置初始化"""
        assert vector_config.connection is not None
        assert vector_config.collections is not None
        assert vector_config.indexes is not None
        assert vector_config.embeddings is not None
        assert vector_config.performance is not None

    def test_collection_config_validation(self):
        """测试集合配置验证"""
        # 有效配置
        config = CollectionConfig(
            name="test_collection", dimension=1536, metric_type="COSINE"
        )
        assert config.name == "test_collection"
        assert config.dimension == 1536
        assert config.metric_type == "COSINE"

        # 无效配置
        with pytest.raises(ValueError):
            CollectionConfig(name="", dimension=1536)

        with pytest.raises(ValueError):
            CollectionConfig(name="test", dimension=0)

        with pytest.raises(ValueError):
            CollectionConfig(name="test", dimension=1536, metric_type="INVALID")

    def test_index_config_validation(self):
        """测试索引配置验证"""
        # 有效配置
        config = IndexConfig(
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )
        assert config.index_type == "HNSW"
        assert config.metric_type == "COSINE"

        # 无效索引类型
        with pytest.raises(ValueError):
            IndexConfig(index_type="INVALID", metric_type="COSINE")

        # 无效度量类型
        with pytest.raises(ValueError):
            IndexConfig(index_type="HNSW", metric_type="INVALID")

    def test_embedding_config_validation(self):
        """测试嵌入配置验证"""
        # 有效配置
        config = EmbeddingConfig(
            model_name="text-embedding-ada-002", dimension=1536, max_length=8192
        )
        assert config.model_name == "text-embedding-ada-002"
        assert config.dimension == 1536

        # 无效维度
        with pytest.raises(ValueError):
            EmbeddingConfig(model_name="test", dimension=0)

        # 无效最大长度
        with pytest.raises(ValueError):
            EmbeddingConfig(model_name="test", dimension=1536, max_length=0)

    def test_config_getters(self):
        """测试配置获取方法"""
        # 获取集合配置
        doc_config = vector_config.get_collection_config("documents")
        assert doc_config is not None
        assert doc_config.name == "cet4_documents"

        # 获取索引配置
        hnsw_config = vector_config.get_index_config("hnsw")
        assert hnsw_config is not None
        assert hnsw_config.index_type == "HNSW"

        # 获取嵌入配置
        openai_config = vector_config.get_embedding_config("openai")
        assert openai_config is not None
        assert openai_config.model_name == "text-embedding-ada-002"

        # 无效类型
        assert vector_config.get_collection_config("invalid") is None
        assert vector_config.get_index_config("invalid") is None
        assert vector_config.get_embedding_config("invalid") is None


class TestMilvusManager:
    """测试Milvus管理器"""

    @pytest.fixture
    def manager(self):
        """创建Milvus管理器实例"""
        return MilvusManager("test_connection")

    @pytest.mark.asyncio
    async def test_connection_success(self, manager):
        """测试连接成功"""
        with patch("app.shared.utils.milvus_manager.connections") as mock_connections:
            mock_connections.connect = MagicMock()

            with patch.object(manager, "_test_connection", new_callable=AsyncMock):
                with patch.object(
                    manager, "_initialize_collections", new_callable=AsyncMock
                ):
                    result = await manager.connect()
                    assert result is True
                    assert manager.is_connected is True

    @pytest.mark.asyncio
    async def test_connection_failure(self, manager):
        """测试连接失败"""
        with patch("app.shared.utils.milvus_manager.connections") as mock_connections:
            mock_connections.connect.side_effect = Exception("Connection failed")

            result = await manager.connect()
            assert result is False
            assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_insert_vectors(self, manager):
        """测试插入向量"""
        manager._connected = True
        manager._collections = {"documents": MagicMock()}

        mock_collection = manager._collections["documents"]
        mock_collection.insert.return_value = MagicMock(insert_count=2)

        texts = ["Hello world", "Test document"]
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

        result = await manager.insert_vectors("documents", texts, vectors)

        assert "insert_count" in result
        mock_collection.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_vectors(self, manager):
        """测试搜索向量"""
        manager._connected = True
        manager._collections = {"documents": MagicMock()}

        mock_collection = manager._collections["documents"]
        mock_hit = MagicMock()
        mock_hit.id = 1
        mock_hit.distance = 0.1
        mock_hit.entity = {"text": "Test", "metadata": "{}", "timestamp": 123456}

        mock_collection.search.return_value = [[mock_hit]]

        query_vectors = [[0.1, 0.2, 0.3]]
        results = await manager.search_vectors("documents", query_vectors)

        assert len(results) == 1
        assert len(results[0]) == 1
        assert results[0][0]["text"] == "Test"
        assert results[0][0]["score"] == 0.9  # 1 - distance

    @pytest.mark.asyncio
    async def test_not_connected_error(self, manager):
        """测试未连接错误"""
        manager._connected = False

        with pytest.raises(MilvusManagerError):
            await manager.insert_vectors("documents", ["test"], [[0.1, 0.2]])

        with pytest.raises(MilvusManagerError):
            await manager.search_vectors("documents", [[0.1, 0.2]])


class TestEmbeddingUtils:
    """测试向量化工具"""

    @pytest.fixture
    def utils(self):
        """创建向量化工具实例"""
        return EmbeddingUtils()

    @pytest.mark.asyncio
    async def test_get_embeddings_openai(self, utils):
        """测试OpenAI向量化"""
        texts = ["Hello world", "Test document"]

        # 模拟OpenAI不可用，应该返回模拟向量
        embeddings = await utils.get_embeddings(texts, "openai")

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536  # OpenAI维度
        assert all(isinstance(emb, float) for emb in embeddings[0])

    @pytest.mark.asyncio
    async def test_get_embeddings_sentence_transformer(self, utils):
        """测试Sentence Transformer向量化"""
        texts = ["Hello world", "Test document"]

        # 模拟Sentence Transformers不可用，应该返回模拟向量
        embeddings = await utils.get_embeddings(texts, "sentence_transformer")

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384  # all-MiniLM-L6-v2维度

    @pytest.mark.asyncio
    async def test_get_single_embedding(self, utils):
        """测试单个文本向量化"""
        text = "Hello world"
        embedding = await utils.get_single_embedding(text, "openai")

        assert len(embedding) == 1536
        assert all(isinstance(emb, float) for emb in embedding)

    @pytest.mark.asyncio
    async def test_compute_similarity(self, utils):
        """测试相似度计算"""
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [0.0, 1.0, 0.0]

        # 余弦相似度
        similarity = await utils.compute_similarity(vector1, vector2, "cosine")
        assert similarity == 0.0  # 垂直向量

        # 点积
        dot_product = await utils.compute_similarity(vector1, vector2, "dot_product")
        assert dot_product == 0.0

        # 维度不匹配
        with pytest.raises(EmbeddingError):
            await utils.compute_similarity([1.0, 0.0], [1.0, 0.0, 0.0])

    def test_cache_operations(self, utils):
        """测试缓存操作"""
        # 初始缓存为空
        assert utils.get_cache_size() == 0

        # 清空缓存
        utils.clear_cache()
        assert utils.get_cache_size() == 0

    def test_supported_models(self, utils):
        """测试支持的模型"""
        models = utils.get_supported_models()
        assert "openai" in models
        assert "sentence_transformer" in models
        assert "chinese" in models

    def test_model_dimension(self, utils):
        """测试模型维度"""
        assert utils.get_model_dimension("openai") == 1536
        assert utils.get_model_dimension("sentence_transformer") == 384
        assert utils.get_model_dimension("chinese") == 768
        assert utils.get_model_dimension("invalid") == 0


class TestSimilarityCalculator:
    """测试相似度计算器"""

    @pytest.fixture
    def calculator(self):
        """创建相似度计算器实例"""
        return SimilarityCalculator()

    @pytest.mark.asyncio
    async def test_vector_similarity_cosine(self, calculator):
        """测试余弦相似度"""
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]

        result = await calculator.compute_vector_similarity(vector1, vector2, "cosine")

        assert isinstance(result, SimilarityResult)
        assert result.score == 1.0  # 相同向量
        assert result.metric == "cosine"

    @pytest.mark.asyncio
    async def test_vector_similarity_euclidean(self, calculator):
        """测试欧几里得距离"""
        vector1 = [0.0, 0.0, 0.0]
        vector2 = [1.0, 1.0, 1.0]

        result = await calculator.compute_vector_similarity(
            vector1, vector2, "euclidean"
        )

        assert isinstance(result, SimilarityResult)
        assert result.score > 0  # 转换为相似度
        assert result.metric == "euclidean"

    @pytest.mark.asyncio
    async def test_text_similarity_jaccard(self, calculator):
        """测试Jaccard相似度"""
        text1 = "hello world test"
        text2 = "hello world example"

        result = await calculator.compute_text_similarity(text1, text2, "jaccard")

        assert isinstance(result, SimilarityResult)
        assert 0 <= result.score <= 1
        assert result.metric == "jaccard"

    @pytest.mark.asyncio
    async def test_batch_compute_similarities(self, calculator):
        """测试批量相似度计算"""
        query_vector = [1.0, 0.0, 0.0]
        candidate_vectors = [
            [1.0, 0.0, 0.0],  # 相同
            [0.0, 1.0, 0.0],  # 垂直
            [-1.0, 0.0, 0.0],  # 相反
        ]

        results = await calculator.batch_compute_similarities(
            query_vector, candidate_vectors, "cosine", top_k=2
        )

        assert len(results) == 2  # top_k=2
        assert results[0][1].score >= results[1][1].score  # 按分数排序

    @pytest.mark.asyncio
    async def test_diversity_score(self, calculator):
        """测试多样性分数"""
        # 相同向量（低多样性）
        vectors = [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]]
        diversity = await calculator.compute_diversity_score(vectors, "cosine")
        assert diversity == 0.0  # 完全相同

        # 不同向量（高多样性）
        vectors = [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]
        diversity = await calculator.compute_diversity_score(vectors, "cosine")
        assert diversity > 0.5  # 较高多样性

    def test_supported_metrics(self, calculator):
        """测试支持的度量"""
        metrics = calculator.get_supported_metrics()
        assert "cosine" in metrics
        assert "euclidean" in metrics
        assert "jaccard" in metrics


class TestVectorDatabaseService:
    """测试向量数据库服务"""

    @pytest.fixture
    def service(self):
        """创建向量数据库服务实例"""
        mock_db = MagicMock()
        return VectorDatabaseService(mock_db)

    @pytest.mark.asyncio
    async def test_add_documents(self, service):
        """测试添加文档"""
        # 模拟依赖
        service.milvus_manager.insert_vectors = AsyncMock(
            return_value={"insert_count": 2}
        )
        service.embedding_utils.get_embeddings = AsyncMock(
            return_value=[[0.1, 0.2], [0.3, 0.4]]
        )
        service._save_document_vector = AsyncMock()

        texts = ["Hello world", "Test document"]
        result = await service.add_documents(texts, "documents", "openai")

        assert len(result) == 2  # 返回文档ID列表
        service.milvus_manager.insert_vectors.assert_called_once()
        service.embedding_utils.get_embeddings.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_similar_documents(self, service):
        """测试搜索相似文档"""
        # 模拟依赖
        service.embedding_utils.get_single_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )
        service.milvus_manager.search_vectors = AsyncMock(
            return_value=[
                [
                    {
                        "text": "Test document",
                        "score": 0.9,
                        "distance": 0.1,
                        "metadata": '{"document_id": "test-id"}',
                    }
                ]
            ]
        )

        query = VectorSearchQuery(
            query_text="Hello world", collection_type="documents", top_k=5
        )

        results = await service.search_similar_documents(query)

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].text == "Test document"
        assert results[0].score == 0.9

    @pytest.mark.asyncio
    async def test_compute_text_similarity(self, service):
        """测试文本相似度计算"""
        service.similarity_calculator.compute_semantic_similarity = AsyncMock(
            return_value=SimilarityResult(score=0.8, metric="cosine", details={})
        )

        result = await service.compute_text_similarity("Hello", "Hi", "openai")

        assert isinstance(result, SimilarityResult)
        assert result.score == 0.8
        assert result.metric == "cosine"

    @pytest.mark.asyncio
    async def test_invalid_collection_type(self, service):
        """测试无效集合类型"""
        with pytest.raises(ValueError):
            await service.add_documents(["test"], "invalid_collection")


if __name__ == "__main__":
    pytest.main([__file__])
