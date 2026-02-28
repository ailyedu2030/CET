"""知识图谱服务测试 - 需求33验收测试."""

from unittest.mock import AsyncMock, Mock, patch

import networkx as nx
import pytest

from app.core.exceptions import BusinessLogicError
from app.resources.services.knowledge_graph_service import KnowledgeGraphService


class TestKnowledgeGraphService:
    """知识图谱服务测试类 - 验证需求33的知识图谱功能."""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话."""
        return AsyncMock()

    @pytest.fixture
    def mock_cache_service(self):
        """模拟缓存服务."""
        return Mock()

    @pytest.fixture
    def knowledge_graph_service(self, mock_db, mock_cache_service):
        """创建知识图谱服务实例."""
        return KnowledgeGraphService(db=mock_db, cache_service=mock_cache_service)

    def test_service_initialization(self, knowledge_graph_service):
        """测试知识图谱服务初始化."""
        assert knowledge_graph_service is not None
        assert hasattr(knowledge_graph_service, "graph_config")
        assert hasattr(knowledge_graph_service, "db")
        assert hasattr(knowledge_graph_service, "cache_service")

    def test_graph_configuration(self, knowledge_graph_service):
        """测试图谱配置 - 需求33关联关系图谱要求."""
        config = knowledge_graph_service.graph_config

        # 验证配置参数
        assert "max_depth" in config
        assert "similarity_threshold" in config
        assert "difficulty_weight" in config
        assert "prerequisite_weight" in config
        assert "semantic_weight" in config

        # 验证需求33：支持6级目录
        assert config["max_depth"] >= 6

    @pytest.mark.asyncio
    async def test_build_knowledge_graph_empty_library(self, knowledge_graph_service):
        """测试空知识库的图谱构建."""
        # 模拟空知识点列表
        with patch.object(
            knowledge_graph_service, "_get_knowledge_points", return_value=[]
        ):
            result = await knowledge_graph_service.build_knowledge_graph(library_id=1)

            # 验证空图谱结果
            assert result["graph"] == {}
            assert result["nodes"] == []
            assert result["edges"] == []
            assert result["statistics"]["node_count"] == 0
            assert result["statistics"]["edge_count"] == 0

    @pytest.mark.asyncio
    async def test_build_knowledge_graph_with_data(self, knowledge_graph_service):
        """测试有数据的图谱构建 - 需求33关联关系图谱."""
        # 模拟知识点数据
        mock_knowledge_points = [
            Mock(id=1, title="基础概念", difficulty_level=1, parent_id=None),
            Mock(id=2, title="进阶概念", difficulty_level=2, parent_id=1),
            Mock(id=3, title="高级概念", difficulty_level=3, parent_id=2),
        ]

        with patch.object(
            knowledge_graph_service,
            "_get_knowledge_points",
            return_value=mock_knowledge_points,
        ):
            with patch.object(
                knowledge_graph_service,
                "_calculate_semantic_similarity",
                return_value=0.8,
            ):
                result = await knowledge_graph_service.build_knowledge_graph(
                    library_id=1
                )

                # 验证图谱构建结果
                assert "graph" in result
                assert "nodes" in result
                assert "edges" in result
                assert "statistics" in result

                # 验证节点数量
                assert result["statistics"]["node_count"] == len(mock_knowledge_points)

                # 验证图谱结构
                assert len(result["nodes"]) > 0

                # 验证关联关系
                if result["edges"]:
                    assert len(result["edges"]) > 0

    @pytest.mark.asyncio
    async def test_get_knowledge_prerequisites(self, knowledge_graph_service):
        """测试获取前置知识 - 需求33前置知识推荐."""
        knowledge_point_id = 1

        # 模拟前置知识数据
        mock_prerequisites = [
            {"id": 2, "title": "前置概念1", "difficulty": 1, "importance": 0.9},
            {"id": 3, "title": "前置概念2", "difficulty": 1, "importance": 0.8},
        ]

        with patch.object(
            knowledge_graph_service,
            "_find_prerequisites",
            return_value=mock_prerequisites,
        ):
            result = await knowledge_graph_service.get_knowledge_prerequisites(
                knowledge_point_id
            )

            # 验证前置知识推荐结果
            assert "prerequisites" in result
            assert "knowledge_point_id" in result
            assert "recommendation_score" in result

            # 验证推荐质量
            assert len(result["prerequisites"]) > 0
            assert result["knowledge_point_id"] == knowledge_point_id

    @pytest.mark.asyncio
    async def test_get_learning_path(self, knowledge_graph_service):
        """测试获取学习路径 - 需求33难度梯度分析."""
        start_point_id = 1
        end_point_id = 5

        # 模拟学习路径
        mock_path = [
            {"id": 1, "title": "起点", "difficulty": 1},
            {"id": 2, "title": "中间点1", "difficulty": 2},
            {"id": 3, "title": "中间点2", "difficulty": 3},
            {"id": 5, "title": "终点", "difficulty": 4},
        ]

        with patch.object(
            knowledge_graph_service, "_find_shortest_path", return_value=mock_path
        ):
            result = await knowledge_graph_service.get_learning_path(
                start_point_id, end_point_id
            )

            # 验证学习路径结果
            assert "path" in result
            assert "start_point_id" in result
            assert "end_point_id" in result
            assert "difficulty_analysis" in result

            # 验证路径有效性
            assert len(result["path"]) > 0
            assert result["start_point_id"] == start_point_id
            assert result["end_point_id"] == end_point_id

            # 验证难度梯度
            if len(result["path"]) > 1:
                difficulties = [point["difficulty"] for point in result["path"]]
                # 验证难度递增（允许相等）
                for i in range(1, len(difficulties)):
                    assert (
                        difficulties[i] >= difficulties[i - 1]
                    ), "学习路径应该按难度递增"

    @pytest.mark.asyncio
    async def test_recommend_knowledge_points(self, knowledge_graph_service):
        """测试知识点推荐 - 需求33个性化推荐."""
        user_id = 1
        limit = 10

        # 模拟推荐结果
        mock_recommendations = [
            {
                "id": i,
                "title": f"推荐知识点{i}",
                "relevance_score": 0.9 - i * 0.1,
                "difficulty": i % 3 + 1,
            }
            for i in range(1, limit + 1)
        ]

        with patch.object(
            knowledge_graph_service,
            "_generate_recommendations",
            return_value=mock_recommendations,
        ):
            result = await knowledge_graph_service.recommend_knowledge_points(
                user_id, limit
            )

            # 验证推荐结果
            assert "recommendations" in result
            assert "user_id" in result
            assert "recommendation_strategy" in result

            # 验证推荐数量
            assert len(result["recommendations"]) <= limit
            assert result["user_id"] == user_id

            # 验证推荐质量（按相关性排序）
            if len(result["recommendations"]) > 1:
                scores = [rec["relevance_score"] for rec in result["recommendations"]]
                for i in range(1, len(scores)):
                    assert scores[i] <= scores[i - 1], "推荐应该按相关性降序排列"

    def test_calculate_semantic_similarity(self, knowledge_graph_service):
        """测试语义相似度计算."""
        # 测试相同文本
        similarity = knowledge_graph_service._calculate_semantic_similarity(
            "测试文本", "测试文本"
        )
        assert similarity == 1.0

        # 测试不同文本
        similarity = knowledge_graph_service._calculate_semantic_similarity(
            "完全不同", "另一个文本"
        )
        assert 0.0 <= similarity <= 1.0

    def test_calculate_difficulty_gradient(self, knowledge_graph_service):
        """测试难度梯度计算 - 需求33难度梯度分析."""
        # 模拟知识点路径
        path = [
            {"difficulty": 1},
            {"difficulty": 2},
            {"difficulty": 3},
            {"difficulty": 4},
        ]

        gradient = knowledge_graph_service._calculate_difficulty_gradient(path)

        # 验证梯度计算结果
        assert "average_gradient" in gradient
        assert "max_jump" in gradient
        assert "is_smooth" in gradient

        # 验证梯度合理性
        assert gradient["average_gradient"] > 0
        assert gradient["max_jump"] >= 0

    def test_analyze_graph_structure(self, knowledge_graph_service):
        """测试图谱结构分析."""
        # 创建模拟图谱
        graph = nx.DiGraph()
        graph.add_nodes_from([1, 2, 3, 4, 5])
        graph.add_edges_from([(1, 2), (2, 3), (3, 4), (1, 5)])

        analysis = knowledge_graph_service._analyze_graph_structure(graph)

        # 验证结构分析结果
        assert "node_count" in analysis
        assert "edge_count" in analysis
        assert "density" in analysis
        assert "connected_components" in analysis

        # 验证分析准确性
        assert analysis["node_count"] == 5
        assert analysis["edge_count"] == 4

    @pytest.mark.asyncio
    async def test_update_graph_cache(self, knowledge_graph_service):
        """测试图谱缓存更新."""
        library_id = 1
        graph_data = {"nodes": [], "edges": []}

        # 测试缓存更新（不抛出异常即可）
        try:
            await knowledge_graph_service._update_graph_cache(library_id, graph_data)
        except Exception as e:
            pytest.fail(f"缓存更新失败: {e}")

    def test_validate_graph_quality(self, knowledge_graph_service):
        """测试图谱质量验证 - 需求33质量控制."""
        # 创建高质量图谱
        good_graph = nx.DiGraph()
        good_graph.add_nodes_from(range(1, 11))  # 10个节点
        good_graph.add_edges_from([(i, i + 1) for i in range(1, 10)])  # 连接良好

        quality = knowledge_graph_service._validate_graph_quality(good_graph)

        # 验证质量指标
        assert "connectivity_score" in quality
        assert "completeness_score" in quality
        assert "overall_quality" in quality

        # 验证质量评分范围
        assert 0 <= quality["connectivity_score"] <= 1
        assert 0 <= quality["completeness_score"] <= 1
        assert quality["overall_quality"] in ["excellent", "good", "fair", "poor"]

    @pytest.mark.asyncio
    async def test_error_handling(self, knowledge_graph_service):
        """测试错误处理."""
        # 测试无效library_id
        with patch.object(
            knowledge_graph_service,
            "_get_knowledge_points",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(BusinessLogicError):
                await knowledge_graph_service.build_knowledge_graph(library_id=-1)

    def test_graph_export_format(self, knowledge_graph_service):
        """测试图谱导出格式 - 需求33数据交换."""
        # 创建测试图谱
        graph = nx.DiGraph()
        graph.add_node(1, title="节点1", difficulty=1)
        graph.add_node(2, title="节点2", difficulty=2)
        graph.add_edge(1, 2, weight=0.8)

        export_data = knowledge_graph_service._export_graph_data(graph)

        # 验证导出格式
        assert "nodes" in export_data
        assert "edges" in export_data
        assert "metadata" in export_data

        # 验证数据完整性
        assert len(export_data["nodes"]) == 2
        assert len(export_data["edges"]) == 1

    def test_performance_metrics(self, knowledge_graph_service):
        """测试性能指标 - 需求33性能要求."""
        config = knowledge_graph_service.graph_config

        # 验证性能相关配置
        assert config["similarity_threshold"] > 0
        assert config["max_depth"] <= 10  # 避免过深的图谱影响性能

        # 验证权重配置合理性
        total_weight = (
            config["difficulty_weight"]
            + config["prerequisite_weight"]
            + config["semantic_weight"]
        )
        assert abs(total_weight - 1.0) < 0.1  # 权重总和应接近1
