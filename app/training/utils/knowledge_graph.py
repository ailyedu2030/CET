"""知识图谱工具类 - 知识点关联分析和学习路径规划."""

import logging
from collections import deque
from typing import Any

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.resources.models.resource_models import KnowledgePoint

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """知识图谱工具类 - 构建和分析知识点关联网络."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化知识图谱."""
        self.db = db
        self.graph = nx.DiGraph()  # 有向图，表示知识点依赖关系
        self.knowledge_points: dict[int, Any] = {}  # 知识点缓存

    async def build_knowledge_graph(self, course_id: int | None = None) -> None:
        """构建知识图谱."""
        try:
            # 获取知识点数据
            await self._load_knowledge_points(course_id)

            # 构建图结构
            await self._build_graph_structure()

            # 计算图属性
            self._calculate_graph_metrics()

            logger.info(
                f"知识图谱构建完成: {self.graph.number_of_nodes()} 个节点, "
                f"{self.graph.number_of_edges()} 条边"
            )

        except Exception as e:
            logger.error(f"构建知识图谱失败: {str(e)}")
            raise

    async def find_learning_path(
        self, start_knowledge_id: int, target_knowledge_id: int
    ) -> list[dict[str, Any]]:
        """查找学习路径."""
        try:
            if not self.graph.has_node(start_knowledge_id) or not self.graph.has_node(
                target_knowledge_id
            ):
                logger.warning("起始或目标知识点不存在于图中")
                return []

            # 使用最短路径算法
            try:
                path = nx.shortest_path(self.graph, start_knowledge_id, target_knowledge_id)
            except nx.NetworkXNoPath:
                logger.info("未找到直接路径，尝试查找间接路径")
                path = await self._find_indirect_path(start_knowledge_id, target_knowledge_id)

            # 构建详细路径信息
            detailed_path = []
            for i, kp_id in enumerate(path):
                kp = self.knowledge_points.get(kp_id)
                if kp:
                    step_info = {
                        "step": i + 1,
                        "knowledge_point_id": kp_id,
                        "title": kp.title,
                        "difficulty_level": kp.difficulty_level,
                        "estimated_time": kp.estimated_time,
                        "importance_score": kp.importance_score,
                        "prerequisites": list(self.graph.predecessors(kp_id)),
                        "dependents": list(self.graph.successors(kp_id)),
                    }
                    detailed_path.append(step_info)

            logger.info(f"找到学习路径，共 {len(detailed_path)} 个步骤")
            return detailed_path

        except Exception as e:
            logger.error(f"查找学习路径失败: {str(e)}")
            return []

    async def analyze_knowledge_dependencies(self, knowledge_id: int) -> dict[str, Any]:
        """分析知识点依赖关系."""
        try:
            if not self.graph.has_node(knowledge_id):
                return {}

            # 获取前置知识点（依赖）
            prerequisites = list(self.graph.predecessors(knowledge_id))
            prerequisite_details = [
                self._get_knowledge_point_info(kp_id) for kp_id in prerequisites
            ]

            # 获取后续知识点（被依赖）
            dependents = list(self.graph.successors(knowledge_id))
            dependent_details = [self._get_knowledge_point_info(kp_id) for kp_id in dependents]

            # 计算依赖深度
            dependency_depth = self._calculate_dependency_depth(knowledge_id)

            # 分析关键路径
            critical_paths = self._find_critical_paths(knowledge_id)

            # 计算影响范围
            influence_scope = self._calculate_influence_scope(knowledge_id)

            return {
                "knowledge_point_id": knowledge_id,
                "prerequisites": prerequisite_details,
                "dependents": dependent_details,
                "dependency_depth": dependency_depth,
                "critical_paths": critical_paths,
                "influence_scope": influence_scope,
                "centrality_score": self._calculate_centrality(knowledge_id),
            }

        except Exception as e:
            logger.error(f"分析知识点依赖关系失败: {str(e)}")
            return {}

    async def recommend_next_knowledge_points(
        self, student_id: int, mastered_knowledge_ids: list[int]
    ) -> list[dict[str, Any]]:
        """推荐下一个学习的知识点."""
        try:
            # 获取学生的学习历史
            learning_history = await self._get_student_learning_history(student_id)

            # 找到可以学习的知识点（前置条件已满足）
            available_points = []
            for kp_id in self.graph.nodes():
                if kp_id not in mastered_knowledge_ids:
                    prerequisites = list(self.graph.predecessors(kp_id))

                    # 检查前置条件是否满足
                    if all(prereq in mastered_knowledge_ids for prereq in prerequisites):
                        kp_info = self._get_knowledge_point_info(kp_id)
                        if kp_info:
                            # 计算推荐分数
                            recommendation_score = self._calculate_recommendation_score(
                                kp_id, mastered_knowledge_ids, learning_history
                            )

                            kp_info["recommendation_score"] = recommendation_score
                            kp_info["readiness_level"] = self._assess_readiness_level(
                                kp_id, mastered_knowledge_ids
                            )
                            available_points.append(kp_info)

            # 按推荐分数排序
            available_points.sort(key=lambda x: x["recommendation_score"], reverse=True)

            logger.info(f"推荐 {len(available_points)} 个可学习知识点")
            return available_points[:10]  # 返回前10个推荐

        except Exception as e:
            logger.error(f"推荐知识点失败: {str(e)}")
            return []

    async def detect_knowledge_gaps(
        self, student_id: int, target_knowledge_ids: list[int]
    ) -> list[dict[str, Any]]:
        """检测知识缺口."""
        try:
            # 获取学生已掌握的知识点
            mastered_points = await self._get_mastered_knowledge_points(student_id)

            knowledge_gaps = []
            for target_id in target_knowledge_ids:
                if target_id not in mastered_points:
                    # 找到到达目标知识点需要的所有前置知识点
                    required_prerequisites = self._get_all_prerequisites(target_id)

                    # 找出缺失的前置知识点
                    missing_prerequisites = [
                        kp_id for kp_id in required_prerequisites if kp_id not in mastered_points
                    ]

                    if missing_prerequisites:
                        gap_info = {
                            "target_knowledge_id": target_id,
                            "target_title": self.knowledge_points[target_id].title,
                            "missing_prerequisites": [
                                self._get_knowledge_point_info(kp_id)
                                for kp_id in missing_prerequisites
                            ],
                            "gap_size": len(missing_prerequisites),
                            "estimated_learning_time": sum(
                                self.knowledge_points[kp_id].estimated_time
                                for kp_id in missing_prerequisites
                                if kp_id in self.knowledge_points
                            ),
                            "priority_score": self._calculate_gap_priority(
                                target_id, missing_prerequisites
                            ),
                        }
                        knowledge_gaps.append(gap_info)

            # 按优先级排序
            knowledge_gaps.sort(key=lambda x: x["priority_score"], reverse=True)

            logger.info(f"检测到 {len(knowledge_gaps)} 个知识缺口")
            return knowledge_gaps

        except Exception as e:
            logger.error(f"检测知识缺口失败: {str(e)}")
            return []

    # ==================== 私有方法 ====================

    async def _load_knowledge_points(self, course_id: int | None = None) -> None:
        """加载知识点数据."""
        stmt = select(KnowledgePoint)
        # KnowledgePoint模型没有course_id字段，通过library_id关联
        # 如果需要按课程过滤，需要通过ResourceLibrary关联
        if course_id:
            # 暂时跳过课程过滤，加载所有知识点
            pass

        result = await self.db.execute(stmt)
        knowledge_points = result.scalars().all()

        self.knowledge_points = {kp.id: kp for kp in knowledge_points}
        logger.info(f"加载了 {len(self.knowledge_points)} 个知识点")

    async def _build_graph_structure(self) -> None:
        """构建图结构."""
        # 添加节点
        for kp_id, kp in self.knowledge_points.items():
            self.graph.add_node(
                kp_id,
                title=kp.title,
                difficulty=kp.difficulty_level,
                importance=kp.importance_score,
                estimated_time=kp.estimated_time,
            )

        # 添加边（依赖关系）
        for kp_id, kp in self.knowledge_points.items():
            if kp.prerequisite_points:
                for prereq_id in kp.prerequisite_points:
                    if prereq_id in self.knowledge_points:
                        self.graph.add_edge(prereq_id, kp_id)

    def _calculate_graph_metrics(self) -> None:
        """计算图的度量指标."""
        # 计算中心性指标
        self.centrality_scores = nx.betweenness_centrality(self.graph)
        self.pagerank_scores = nx.pagerank(self.graph)

        # 计算连通性
        self.strongly_connected = nx.is_strongly_connected(self.graph)
        self.weakly_connected = nx.is_weakly_connected(self.graph)

    async def _find_indirect_path(self, start_id: int, target_id: int) -> list[int]:
        """查找间接路径."""
        # 使用BFS查找可能的路径
        visited = set()
        queue = deque([(start_id, [start_id])])

        while queue:
            current_id, path = queue.popleft()

            if current_id == target_id:
                return path

            if current_id in visited:
                continue
            visited.add(current_id)

            # 探索相邻节点
            for neighbor in self.graph.successors(current_id):
                if neighbor not in visited and len(path) < 10:  # 限制路径长度
                    queue.append((neighbor, path + [neighbor]))

        return []  # 未找到路径

    def _get_knowledge_point_info(self, kp_id: int) -> dict[str, Any] | None:
        """获取知识点信息."""
        kp = self.knowledge_points.get(kp_id)
        if not kp:
            return None

        return {
            "knowledge_point_id": kp_id,
            "title": kp.title,
            "difficulty_level": kp.difficulty_level,
            "importance_score": kp.importance_score,
            "estimated_time": kp.estimated_time,
            "is_core": kp.is_core,
        }

    def _calculate_dependency_depth(self, knowledge_id: int) -> int:
        """计算依赖深度."""
        try:
            # 计算到根节点的最长路径
            depths = []
            for root in [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]:
                try:
                    path_length = nx.shortest_path_length(self.graph, root, knowledge_id)
                    depths.append(path_length)
                except nx.NetworkXNoPath:
                    continue

            return max(depths) if depths else 0
        except Exception:
            return 0

    def _find_critical_paths(self, knowledge_id: int) -> list[list[int]]:
        """查找关键路径."""
        critical_paths = []

        # 找到所有到达该知识点的路径
        for root in [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]:
            try:
                path = nx.shortest_path(self.graph, root, knowledge_id)
                if len(path) > 1:
                    critical_paths.append(path)
            except nx.NetworkXNoPath:
                continue

        return critical_paths[:5]  # 返回前5条关键路径

    def _calculate_influence_scope(self, knowledge_id: int) -> int:
        """计算影响范围."""
        # 计算从该知识点可达的所有节点数量
        reachable = nx.descendants(self.graph, knowledge_id)
        return len(reachable)

    def _calculate_centrality(self, knowledge_id: int) -> float:
        """计算中心性分数."""
        return float(self.centrality_scores.get(knowledge_id, 0.0))

    async def _get_student_learning_history(self, student_id: int) -> dict[int, float]:
        """获取学生学习历史."""
        # 简化处理，返回空字典
        # TODO: 实现基于学习记录的知识点掌握度分析
        # stmt = select(TrainingRecord).where(TrainingRecord.student_id == student_id)
        # result = await self.db.execute(stmt)
        # records = result.scalars().all()

        return {}

    def _calculate_recommendation_score(
        self, kp_id: int, mastered_ids: list[int], learning_history: dict[int, float]
    ) -> float:
        """计算推荐分数."""
        kp = self.knowledge_points[kp_id]

        # 基础分数（重要性）
        base_score = kp.importance_score

        # 难度调整
        difficulty_factor = {
            "beginner": 1.2,
            "intermediate": 1.0,
            "advanced": 0.8,
            "expert": 0.6,
        }.get(kp.difficulty_level, 1.0)

        # 前置条件满足度
        prerequisites = list(self.graph.predecessors(kp_id))
        prerequisite_factor = 1.0 if all(p in mastered_ids for p in prerequisites) else 0.5

        # 中心性加权
        centrality_factor = 1.0 + float(self.centrality_scores.get(kp_id, 0.0))

        return float(base_score * difficulty_factor * prerequisite_factor * centrality_factor)

    def _assess_readiness_level(self, kp_id: int, mastered_ids: list[int]) -> str:
        """评估准备程度."""
        prerequisites = list(self.graph.predecessors(kp_id))

        if not prerequisites:
            return "ready"

        mastered_prereqs = sum(1 for p in prerequisites if p in mastered_ids)
        readiness_ratio = mastered_prereqs / len(prerequisites)

        if readiness_ratio >= 1.0:
            return "ready"
        elif readiness_ratio >= 0.8:
            return "mostly_ready"
        elif readiness_ratio >= 0.5:
            return "partially_ready"
        else:
            return "not_ready"

    async def _get_mastered_knowledge_points(self, student_id: int) -> set[int]:
        """获取学生已掌握的知识点."""
        # 这里需要根据学习记录判断掌握程度
        # 简化处理，返回空集合
        return set()

    def _get_all_prerequisites(self, knowledge_id: int) -> list[int]:
        """获取所有前置知识点."""
        all_prerequisites = []
        visited = set()

        def dfs(kp_id: int) -> None:
            if kp_id in visited:
                return
            visited.add(kp_id)

            for prereq in self.graph.predecessors(kp_id):
                all_prerequisites.append(prereq)
                dfs(prereq)

        dfs(knowledge_id)
        return list(set(all_prerequisites))

    def _calculate_gap_priority(self, target_id: int, missing_prerequisites: list[int]) -> float:
        """计算缺口优先级."""
        target_kp = self.knowledge_points[target_id]

        # 目标重要性
        importance_score = target_kp.importance_score

        # 缺口大小（越小优先级越高）
        gap_penalty = len(missing_prerequisites) * 0.1

        # 学习时间（越短优先级越高）
        time_penalty = (
            sum(
                self.knowledge_points[kp_id].estimated_time
                for kp_id in missing_prerequisites
                if kp_id in self.knowledge_points
            )
            * 0.01
        )

        return float(importance_score - gap_penalty - time_penalty)
