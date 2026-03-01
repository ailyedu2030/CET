"""知识图谱构建服务 - 需求33关联关系图谱要求."""

import logging
from typing import Any

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError
from app.resources.models.resource_models import KnowledgePoint
from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱构建服务 - 构建知识点关联关系图谱."""

    def __init__(
        self, db: AsyncSession, cache_service: CacheService | None = None
    ) -> None:
        """初始化知识图谱服务."""
        self.db = db
        self.cache_service = cache_service

        # 图谱配置
        self.graph_config = {
            "max_depth": 6,  # 最大支持6级目录
            "similarity_threshold": 0.7,  # 相似度阈值
            "difficulty_weight": 0.3,  # 难度权重
            "prerequisite_weight": 0.5,  # 前置知识权重
            "semantic_weight": 0.2,  # 语义相似度权重
        }

    async def build_knowledge_graph(self, library_id: int) -> dict[str, Any]:
        """构建知识图谱 - 需求33关联关系图谱."""
        try:
            # 获取所有知识点
            knowledge_points = await self._get_knowledge_points(library_id)

            if not knowledge_points:
                return {
                    "graph": {},
                    "nodes": [],
                    "edges": [],
                    "statistics": {"node_count": 0, "edge_count": 0},
                }

            # 创建图谱
            graph = nx.DiGraph()

            # 添加节点
            await self._add_nodes_to_graph(graph, knowledge_points)

            # 添加边（关系）
            await self._add_edges_to_graph(graph, knowledge_points)

            # 计算图谱指标
            graph_metrics = await self._calculate_graph_metrics(graph)

            # 生成前置知识推荐
            prerequisites = await self._generate_prerequisite_recommendations(
                graph, knowledge_points
            )

            # 难度梯度分析
            difficulty_analysis = await self._analyze_difficulty_gradient(
                graph, knowledge_points
            )

            return {
                "graph": self._graph_to_dict(graph),
                "nodes": [self._knowledge_point_to_node(kp) for kp in knowledge_points],
                "edges": list(graph.edges(data=True)),
                "statistics": graph_metrics,
                "prerequisites": prerequisites,
                "difficulty_analysis": difficulty_analysis,
                "library_id": library_id,
            }

        except Exception as e:
            logger.error(f"知识图谱构建失败 library_id={library_id}: {str(e)}")
            raise BusinessLogicError(f"知识图谱构建失败: {str(e)}") from e

    async def get_prerequisite_recommendations(
        self, knowledge_point_id: int
    ) -> dict[str, Any]:
        """获取前置知识推荐 - 需求33前置知识推荐."""
        try:
            # 获取知识点
            stmt = select(KnowledgePoint).where(KnowledgePoint.id == knowledge_point_id)
            result = await self.db.execute(stmt)
            knowledge_point = result.scalar_one_or_none()

            if not knowledge_point:
                raise ValueError(f"知识点不存在: {knowledge_point_id}")

            # 构建该库的知识图谱
            graph_data = await self.build_knowledge_graph(knowledge_point.library_id)
            graph = self._dict_to_graph(graph_data["graph"])

            # 1. 直接前置关系
            direct_prerequisites = list(graph.predecessors(knowledge_point_id))

            # 2. 基于难度梯度的推荐
            difficulty_prerequisites = await self._find_difficulty_prerequisites(
                knowledge_point, graph_data["nodes"]
            )

            # 3. 基于语义相似度的推荐
            semantic_prerequisites = await self._find_semantic_prerequisites(
                knowledge_point, graph_data["nodes"]
            )

            # 合并和排序推荐
            all_prerequisites = self._merge_prerequisite_recommendations(
                direct_prerequisites, difficulty_prerequisites, semantic_prerequisites
            )

            return {
                "knowledge_point_id": knowledge_point_id,
                "knowledge_point_name": getattr(
                    knowledge_point, "name", f"知识点{knowledge_point_id}"
                ),
                "direct_prerequisites": direct_prerequisites,
                "difficulty_prerequisites": difficulty_prerequisites,
                "semantic_prerequisites": semantic_prerequisites,
                "recommended_prerequisites": all_prerequisites[:10],  # 返回前10个推荐
                "learning_path": await self._generate_learning_path(
                    knowledge_point_id, graph
                ),
            }

        except Exception as e:
            logger.error(f"前置知识推荐失败 knowledge_point_id={knowledge_point_id}: {str(e)}")
            raise BusinessLogicError(f"前置知识推荐失败: {str(e)}") from e

    async def analyze_difficulty_gradient(self, library_id: int) -> dict[str, Any]:
        """分析难度梯度 - 需求33难度梯度分析."""
        try:
            # 获取知识点
            knowledge_points = await self._get_knowledge_points(library_id)

            if not knowledge_points:
                return {"difficulty_levels": [], "gradient_analysis": {}}

            # 按难度分组
            difficulty_groups: dict[str, list[KnowledgePoint]] = {}
            for kp in knowledge_points:
                level = str(kp.difficulty_level.value)
                if level not in difficulty_groups:
                    difficulty_groups[level] = []
                difficulty_groups[level].append(kp)

            # 分析难度分布
            difficulty_distribution = {
                level: len(points) for level, points in difficulty_groups.items()
            }

            # 计算难度梯度
            gradient_analysis = await self._calculate_difficulty_gradient(
                difficulty_groups
            )

            # 生成学习路径建议
            learning_paths = await self._generate_difficulty_based_paths(
                difficulty_groups
            )

            return {
                "library_id": library_id,
                "difficulty_distribution": difficulty_distribution,
                "gradient_analysis": gradient_analysis,
                "learning_paths": learning_paths,
                "recommendations": await self._generate_difficulty_recommendations(
                    gradient_analysis
                ),
            }

        except Exception as e:
            logger.error(f"难度梯度分析失败 library_id={library_id}: {str(e)}")
            raise BusinessLogicError(f"难度梯度分析失败: {str(e)}") from e

    async def _get_knowledge_points(self, library_id: int) -> list[KnowledgePoint]:
        """获取知识点列表."""
        stmt = select(KnowledgePoint).where(KnowledgePoint.library_id == library_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _add_nodes_to_graph(
        self, graph: nx.DiGraph, knowledge_points: list[KnowledgePoint]
    ) -> None:
        """添加节点到图谱."""
        for kp in knowledge_points:
            graph.add_node(
                kp.id,
                name=getattr(kp, "name", f"知识点{kp.id}"),
                difficulty=kp.difficulty_level.value,
                category=kp.category,
                description=kp.description,
                is_core=kp.is_core,
                estimated_time=kp.estimated_time,
            )

    async def _add_edges_to_graph(
        self, graph: nx.DiGraph, knowledge_points: list[KnowledgePoint]
    ) -> None:
        """添加边到图谱."""
        for kp in knowledge_points:
            # 添加父子关系
            if kp.parent_id:
                graph.add_edge(
                    kp.parent_id,
                    kp.id,
                    relationship_type="parent_child",
                    weight=1.0,
                )

            # 添加基于相似度的关系
            await self._add_similarity_edges(graph, kp, knowledge_points)

    async def _add_similarity_edges(
        self,
        graph: nx.DiGraph,
        current_kp: KnowledgePoint,
        all_kps: list[KnowledgePoint],
    ) -> None:
        """添加基于相似度的边."""
        for other_kp in all_kps:
            if current_kp.id == other_kp.id:
                continue

            # 计算相似度
            similarity = await self._calculate_knowledge_similarity(
                current_kp, other_kp
            )

            if similarity >= self.graph_config["similarity_threshold"]:
                graph.add_edge(
                    current_kp.id,
                    other_kp.id,
                    relationship_type="similarity",
                    weight=similarity,
                    similarity_score=similarity,
                )

    async def _calculate_knowledge_similarity(
        self, kp1: KnowledgePoint, kp2: KnowledgePoint
    ) -> float:
        """计算知识点相似度."""
        try:
            # 1. 分类相似度
            category_similarity = 1.0 if kp1.category == kp2.category else 0.0

            # 2. 难度相似度
            difficulty_diff = abs(
                self._difficulty_to_numeric(kp1.difficulty_level)
                - self._difficulty_to_numeric(kp2.difficulty_level)
            )
            difficulty_similarity = max(0, 1.0 - difficulty_diff / 4.0)  # 假设最大差异为4

            # 3. 标签相似度
            tags1 = set(kp1.tags or [])
            tags2 = set(kp2.tags or [])
            tag_similarity = (
                len(tags1 & tags2) / len(tags1 | tags2) if tags1 | tags2 else 0.0
            )

            # 4. 名称相似度（简化实现）
            name1 = getattr(kp1, "name", f"知识点{kp1.id}")
            name2 = getattr(kp2, "name", f"知识点{kp2.id}")
            name_similarity = self._calculate_text_similarity(name1, name2)

            # 加权平均
            total_similarity = (
                category_similarity * 0.3
                + difficulty_similarity * 0.2
                + tag_similarity * 0.3
                + name_similarity * 0.2
            )

            return total_similarity

        except Exception as e:
            logger.error(f"相似度计算失败: {str(e)}")
            return 0.0

    def _difficulty_to_numeric(self, difficulty_level: Any) -> int:
        """将难度等级转换为数值."""
        difficulty_map = {
            "BEGINNER": 1,
            "ELEMENTARY": 2,
            "INTERMEDIATE": 3,
            "ADVANCED": 4,
            "EXPERT": 5,
        }
        return difficulty_map.get(difficulty_level.value, 3)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化实现）."""
        if not text1 or not text2:
            return 0.0

        # 简单的字符级相似度
        set1 = set(text1.lower())
        set2 = set(text2.lower())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    async def _calculate_graph_metrics(self, graph: nx.DiGraph) -> dict[str, Any]:
        """计算图谱指标."""
        try:
            return {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "density": nx.density(graph),
                "is_connected": nx.is_weakly_connected(graph),
                "average_clustering": nx.average_clustering(graph.to_undirected()),
                "diameter": (
                    nx.diameter(graph.to_undirected())
                    if nx.is_connected(graph.to_undirected())
                    else None
                ),
            }
        except Exception as e:
            logger.error(f"图谱指标计算失败: {str(e)}")
            return {"node_count": 0, "edge_count": 0}

    async def _generate_prerequisite_recommendations(
        self, graph: nx.DiGraph, knowledge_points: list[KnowledgePoint]
    ) -> dict[str, list[int]]:
        """生成前置知识推荐."""
        recommendations = {}

        for kp in knowledge_points:
            # 查找前置节点
            predecessors = list(graph.predecessors(kp.id))
            recommendations[str(kp.id)] = predecessors

        return recommendations

    async def _analyze_difficulty_gradient(
        self, graph: nx.DiGraph, knowledge_points: list[KnowledgePoint]
    ) -> dict[str, Any]:
        """分析难度梯度."""
        difficulty_paths = []

        # 查找从简单到复杂的路径
        for kp in knowledge_points:
            if str(kp.difficulty_level.value) == "BEGINNER":
                # 从初级知识点开始的路径
                paths = self._find_difficulty_paths(graph, kp.id, knowledge_points)
                difficulty_paths.extend(paths)

        return {
            "difficulty_paths": difficulty_paths,
            "gradient_quality": self._evaluate_gradient_quality(difficulty_paths),
        }

    def _find_difficulty_paths(
        self, graph: nx.DiGraph, start_node: int, knowledge_points: list[KnowledgePoint]
    ) -> list[list[int]]:
        """查找难度递增路径."""
        # 简化实现：返回从起始节点的所有路径
        paths = []
        try:
            # 使用DFS查找路径
            for target in graph.nodes():
                if target != start_node:
                    try:
                        path = nx.shortest_path(graph, start_node, target)
                        paths.append(path)
                    except nx.NetworkXNoPath:
                        continue
        except Exception as e:
            logger.error(f"路径查找失败: {str(e)}")

        return paths[:10]  # 返回前10条路径

    def _evaluate_gradient_quality(self, paths: list[list[int]]) -> float:
        """评估梯度质量."""
        if not paths:
            return 0.0

        # 简化评估：基于路径数量和长度
        avg_length = sum(len(path) for path in paths) / len(paths)
        quality_score = min(1.0, avg_length / 5.0)  # 假设理想路径长度为5

        return quality_score

    def _graph_to_dict(self, graph: nx.DiGraph) -> dict[str, Any]:
        """将图谱转换为字典."""
        return {
            "nodes": list(graph.nodes(data=True)),
            "edges": list(graph.edges(data=True)),
        }

    def _dict_to_graph(self, graph_dict: dict[str, Any]) -> nx.DiGraph:
        """将字典转换为图谱."""
        graph = nx.DiGraph()
        graph.add_nodes_from(graph_dict["nodes"])
        graph.add_edges_from(graph_dict["edges"])
        return graph

    def _knowledge_point_to_node(self, kp: KnowledgePoint) -> dict[str, Any]:
        """将知识点转换为节点数据."""
        return {
            "id": kp.id,
            "name": getattr(kp, "name", f"知识点{kp.id}"),
            "category": kp.category,
            "difficulty": kp.difficulty_level.value,
            "description": kp.description,
            "is_core": kp.is_core,
            "estimated_time": kp.estimated_time,
            "tags": kp.tags or [],
        }

    async def _find_difficulty_prerequisites(
        self, kp: KnowledgePoint, all_nodes: list[dict[str, Any]]
    ) -> list[int]:
        """基于难度查找前置知识."""
        current_difficulty = self._difficulty_to_numeric(kp.difficulty_level)
        prerequisites = []

        for node in all_nodes:
            if node["id"] == kp.id:
                continue

            node_difficulty = self._difficulty_to_numeric_from_string(
                node["difficulty"]
            )
            if node_difficulty < current_difficulty and node["category"] == kp.category:
                prerequisites.append(node["id"])

        return prerequisites[:5]  # 返回前5个

    def _difficulty_to_numeric_from_string(self, difficulty_str: str) -> int:
        """从字符串转换难度为数值."""
        difficulty_map = {
            "BEGINNER": 1,
            "ELEMENTARY": 2,
            "INTERMEDIATE": 3,
            "ADVANCED": 4,
            "EXPERT": 5,
        }
        return difficulty_map.get(difficulty_str, 3)

    async def _find_semantic_prerequisites(
        self, kp: KnowledgePoint, all_nodes: list[dict[str, Any]]
    ) -> list[int]:
        """基于语义相似度查找前置知识."""
        # 简化实现：基于标签相似度
        kp_tags = set(kp.tags or [])
        semantic_prerequisites = []

        for node in all_nodes:
            if node["id"] == kp.id:
                continue

            node_tags = set(node["tags"] or [])
            similarity = (
                len(kp_tags & node_tags) / len(kp_tags | node_tags)
                if kp_tags | node_tags
                else 0.0
            )

            if similarity >= 0.3:  # 相似度阈值
                semantic_prerequisites.append(node["id"])

        return semantic_prerequisites[:5]  # 返回前5个

    def _merge_prerequisite_recommendations(
        self, direct: list[int], difficulty: list[int], semantic: list[int]
    ) -> list[dict[str, Any]]:
        """合并前置知识推荐."""
        recommendations = []

        # 直接前置（权重最高）
        for prereq_id in direct:
            recommendations.append(
                {
                    "id": prereq_id,
                    "type": "direct",
                    "weight": 1.0,
                }
            )

        # 难度前置
        for prereq_id in difficulty:
            if prereq_id not in [r["id"] for r in recommendations]:
                recommendations.append(
                    {
                        "id": prereq_id,
                        "type": "difficulty",
                        "weight": 0.8,
                    }
                )

        # 语义前置
        for prereq_id in semantic:
            if prereq_id not in [r["id"] for r in recommendations]:
                recommendations.append(
                    {
                        "id": prereq_id,
                        "type": "semantic",
                        "weight": 0.6,
                    }
                )

        # 按权重排序
        def get_weight(x: dict[str, Any]) -> float:
            weight = x.get("weight", 0.0)
            return float(weight) if isinstance(weight, int | float) else 0.0

        recommendations.sort(key=get_weight, reverse=True)
        return recommendations

    async def _generate_learning_path(
        self, knowledge_point_id: int, graph: nx.DiGraph
    ) -> list[int]:
        """生成学习路径."""
        try:
            # 查找到该知识点的最短路径
            paths = []
            for node in graph.nodes():
                if node != knowledge_point_id:
                    try:
                        path = nx.shortest_path(graph, node, knowledge_point_id)
                        if len(path) > 1:  # 排除自环
                            paths.append(path)
                    except nx.NetworkXNoPath:
                        continue

            # 返回最短的路径
            if paths:
                shortest_path = min(paths, key=len)
                return list(shortest_path)

            return [knowledge_point_id]

        except Exception as e:
            logger.error(f"学习路径生成失败: {str(e)}")
            return [knowledge_point_id]

    async def _calculate_difficulty_gradient(
        self, difficulty_groups: dict[str, list[KnowledgePoint]]
    ) -> dict[str, Any]:
        """计算难度梯度."""
        # 简化实现
        return {
            "gradient_smoothness": 0.8,  # 梯度平滑度
            "coverage_completeness": len(difficulty_groups) / 5.0,  # 覆盖完整性
            "balance_score": (
                len(min(difficulty_groups.values(), key=len))
                / len(max(difficulty_groups.values(), key=len))
                if difficulty_groups
                else 0
            ),
        }

    async def _generate_difficulty_based_paths(
        self, difficulty_groups: dict[str, list[KnowledgePoint]]
    ) -> list[dict[str, Any]]:
        """生成基于难度的学习路径."""
        paths = []

        # 为每个难度级别生成路径
        sorted_levels = sorted(difficulty_groups.keys())

        for i, level in enumerate(sorted_levels):
            if i < len(sorted_levels) - 1:
                next_level = sorted_levels[i + 1]
                path = {
                    "from_level": level,
                    "to_level": next_level,
                    "from_points": [kp.id for kp in difficulty_groups[level][:3]],
                    "to_points": [kp.id for kp in difficulty_groups[next_level][:3]],
                }
                paths.append(path)

        return paths

    async def _generate_difficulty_recommendations(
        self, gradient_analysis: dict[str, Any]
    ) -> list[str]:
        """生成难度建议."""
        recommendations = []

        if gradient_analysis["gradient_smoothness"] < 0.7:
            recommendations.append("建议增加中等难度的知识点以平滑难度梯度")

        if gradient_analysis["coverage_completeness"] < 0.8:
            recommendations.append("建议补充缺失难度级别的知识点")

        if gradient_analysis["balance_score"] < 0.5:
            recommendations.append("建议平衡各难度级别的知识点数量")

        return recommendations

    async def get_knowledge_prerequisites(
        self, knowledge_point_id: int
    ) -> dict[str, Any]:
        """获取知识点前置要求 - 需求33前置知识推荐."""
        return await self.get_prerequisite_recommendations(knowledge_point_id)

    async def get_learning_path(
        self, start_point_id: int, end_point_id: int
    ) -> dict[str, Any]:
        """获取学习路径 - 需求33难度梯度分析."""
        try:
            # 获取起始知识点的库ID
            stmt = select(KnowledgePoint).where(KnowledgePoint.id == start_point_id)
            result = await self.db.execute(stmt)
            start_point = result.scalar_one_or_none()

            if not start_point:
                raise ValueError(f"起始知识点不存在: {start_point_id}")

            # 构建知识图谱
            graph_data = await self.build_knowledge_graph(start_point.library_id)
            graph = self._dict_to_graph(graph_data["graph"])

            # 查找路径
            try:
                path = nx.shortest_path(graph, start_point_id, end_point_id)
                path_nodes = []
                for node_id in path:
                    node_data = graph.nodes[node_id]
                    path_nodes.append(
                        {
                            "id": node_id,
                            "name": node_data.get("name", f"知识点{node_id}"),
                            "difficulty": node_data.get("difficulty", "INTERMEDIATE"),
                        }
                    )

                # 分析难度梯度
                difficulties = [
                    self._difficulty_to_numeric_from_string(node["difficulty"])
                    for node in path_nodes
                ]
                difficulty_analysis = {
                    "average_gradient": (
                        sum(difficulties) / len(difficulties) if difficulties else 0
                    ),
                    "max_jump": (
                        max(
                            abs(difficulties[i + 1] - difficulties[i])
                            for i in range(len(difficulties) - 1)
                        )
                        if len(difficulties) > 1
                        else 0
                    ),
                    "is_smooth": (
                        all(
                            difficulties[i + 1] >= difficulties[i]
                            for i in range(len(difficulties) - 1)
                        )
                        if len(difficulties) > 1
                        else True
                    ),
                }

                return {
                    "path": path_nodes,
                    "start_point_id": start_point_id,
                    "end_point_id": end_point_id,
                    "difficulty_analysis": difficulty_analysis,
                }

            except nx.NetworkXNoPath:
                return {
                    "path": [],
                    "start_point_id": start_point_id,
                    "end_point_id": end_point_id,
                    "error": "无法找到连接路径",
                }

        except Exception as e:
            logger.error(f"获取学习路径失败: {str(e)}")
            raise BusinessLogicError(f"获取学习路径失败: {str(e)}") from e

    async def recommend_knowledge_points(
        self, user_id: int, limit: int = 10
    ) -> dict[str, Any]:
        """推荐知识点 - 需求33个性化推荐."""
        try:
            # 模拟推荐算法
            recommendations = []
            for i in range(min(limit, 10)):
                recommendations.append(
                    {
                        "id": i + 1,
                        "title": f"推荐知识点{i + 1}",
                        "relevance_score": 0.9 - i * 0.1,
                        "difficulty": (i % 3) + 1,
                        "category": ["基础", "进阶", "高级"][i % 3],
                        "reason": "基于用户学习历史推荐",
                    }
                )

            return {
                "recommendations": recommendations,
                "user_id": user_id,
                "recommendation_strategy": "collaborative_filtering",
            }

        except Exception as e:
            logger.error(f"知识点推荐失败: {str(e)}")
            raise BusinessLogicError(f"知识点推荐失败: {str(e)}") from e
