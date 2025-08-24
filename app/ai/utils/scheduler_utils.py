"""
AI调度工具类

提供智能调度算法和工具函数：
- 负载均衡算法
- 优先级队列管理
- 时间窗口调度
- 资源分配优化
"""

import heapq
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class SchedulingAlgorithm(Enum):
    """调度算法类型"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    ADAPTIVE = "adaptive"


class Priority(Enum):
    """请求优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScheduledTask:
    """调度任务"""

    task_id: str
    priority: Priority
    estimated_duration: float
    deadline: datetime | None
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: datetime | None = None

    def __lt__(self, other: "ScheduledTask") -> bool:
        """优先级队列排序"""
        # 优先级高的先执行
        if self.priority != other.priority:
            return self.priority.value > other.priority.value

        # 相同优先级按截止时间排序
        if self.deadline and other.deadline:
            return self.deadline < other.deadline

        # 没有截止时间的按创建时间排序
        return self.created_at < other.created_at


@dataclass
class ResourceNode:
    """资源节点"""

    node_id: str
    capacity: int
    current_load: int = 0
    success_rate: float = 1.0
    average_response_time: float = 1.0
    last_used: datetime = field(default_factory=datetime.utcnow)
    weight: float = 1.0
    is_available: bool = True


class PriorityQueue:
    """优先级队列管理器"""

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self.queue: list[ScheduledTask] = []
        self.task_map: dict[str, ScheduledTask] = {}
        self.logger = logging.getLogger(__name__)

    def add_task(self, task: ScheduledTask) -> bool:
        """添加任务到队列"""
        try:
            if len(self.queue) >= self.max_size:
                # 队列满时，移除优先级最低的任务
                if task.priority.value <= self.queue[0].priority.value:
                    self.logger.warning(f"队列已满，拒绝低优先级任务: {task.task_id}")
                    return False

                # 移除优先级最低的任务
                removed_task = heapq.heappop(self.queue)
                del self.task_map[removed_task.task_id]
                self.logger.info(f"移除低优先级任务: {removed_task.task_id}")

            heapq.heappush(self.queue, task)
            self.task_map[task.task_id] = task

            self.logger.debug(f"任务已加入队列: {task.task_id}, 优先级: {task.priority.name}")
            return True

        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            return False

    def get_next_task(self) -> ScheduledTask | None:
        """获取下一个任务"""
        try:
            if not self.queue:
                return None

            task = heapq.heappop(self.queue)
            del self.task_map[task.task_id]

            return task

        except Exception as e:
            self.logger.error(f"获取任务失败: {e}")
            return None

    def remove_task(self, task_id: str) -> bool:
        """移除指定任务"""
        try:
            if task_id not in self.task_map:
                return False

            task = self.task_map[task_id]
            self.queue.remove(task)
            heapq.heapify(self.queue)
            del self.task_map[task_id]

            self.logger.debug(f"任务已移除: {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"移除任务失败: {e}")
            return False

    def get_queue_status(self) -> dict[str, Any]:
        """获取队列状态"""
        priority_counts = {p.name: 0 for p in Priority}

        for task in self.queue:
            priority_counts[task.priority.name] += 1

        return {
            "total_tasks": len(self.queue),
            "max_size": self.max_size,
            "utilization": len(self.queue) / self.max_size,
            "priority_distribution": priority_counts,
            "oldest_task_age": (
                (datetime.utcnow() - min(task.created_at for task in self.queue)).total_seconds()
                if self.queue
                else 0
            ),
        }


class LoadBalancer:
    """负载均衡器"""

    def __init__(self, algorithm: SchedulingAlgorithm = SchedulingAlgorithm.ADAPTIVE) -> None:
        self.algorithm = algorithm
        self.nodes: list[ResourceNode] = []
        self.round_robin_index = 0
        self.logger = logging.getLogger(__name__)

        # 自适应算法参数
        self.adaptation_window = timedelta(minutes=5)
        self.performance_history: dict[str, list[tuple[datetime, float]]] = {}

    def add_node(self, node: ResourceNode) -> None:
        """添加资源节点"""
        self.nodes.append(node)
        self.performance_history[node.node_id] = []
        self.logger.info(f"添加资源节点: {node.node_id}")

    def remove_node(self, node_id: str) -> bool:
        """移除资源节点"""
        try:
            self.nodes = [n for n in self.nodes if n.node_id != node_id]
            if node_id in self.performance_history:
                del self.performance_history[node_id]

            self.logger.info(f"移除资源节点: {node_id}")
            return True

        except Exception as e:
            self.logger.error(f"移除节点失败: {e}")
            return False

    def select_node(self, task: ScheduledTask) -> ResourceNode | None:
        """选择最优节点"""
        try:
            available_nodes = [
                n for n in self.nodes if n.is_available and n.current_load < n.capacity
            ]

            if not available_nodes:
                self.logger.warning("没有可用的资源节点")
                return None

            if self.algorithm == SchedulingAlgorithm.ROUND_ROBIN:
                return self._round_robin_select(available_nodes)
            elif self.algorithm == SchedulingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(available_nodes)
            elif self.algorithm == SchedulingAlgorithm.LEAST_CONNECTIONS:
                return self._least_connections_select(available_nodes)
            elif self.algorithm == SchedulingAlgorithm.RESPONSE_TIME:
                return self._response_time_select(available_nodes)
            elif self.algorithm == SchedulingAlgorithm.ADAPTIVE:
                return self._adaptive_select(available_nodes, task)

        except Exception as e:
            self.logger.error(f"节点选择失败: {e}")
            return available_nodes[0] if available_nodes else None

    def _round_robin_select(self, nodes: list[ResourceNode]) -> ResourceNode:
        """轮询选择"""
        node = nodes[self.round_robin_index % len(nodes)]
        self.round_robin_index += 1
        return node

    def _weighted_round_robin_select(self, nodes: list[ResourceNode]) -> ResourceNode:
        """加权轮询选择"""
        # 根据权重计算选择概率
        total_weight = sum(n.weight for n in nodes)
        if total_weight == 0:
            return nodes[0]

        random_value = random.uniform(0, total_weight)
        current_weight = 0

        for node in nodes:
            current_weight += node.weight
            if random_value <= current_weight:
                return node

        return nodes[-1]

    def _least_connections_select(self, nodes: list[ResourceNode]) -> ResourceNode:
        """最少连接选择"""
        return min(nodes, key=lambda n: n.current_load)

    def _response_time_select(self, nodes: list[ResourceNode]) -> ResourceNode:
        """响应时间选择"""
        return min(nodes, key=lambda n: n.average_response_time)

    def _adaptive_select(self, nodes: list[ResourceNode], task: ScheduledTask) -> ResourceNode:
        """自适应选择"""
        # 综合考虑多个因素的评分
        scored_nodes = []

        for node in nodes:
            score = self._calculate_node_score(node, task)
            scored_nodes.append((node, score))

        # 选择得分最高的节点
        best_node = max(scored_nodes, key=lambda x: x[1])[0]
        return best_node

    def _calculate_node_score(self, node: ResourceNode, task: ScheduledTask) -> float:
        """计算节点综合得分"""
        try:
            # 基础得分
            score = 1.0

            # 负载因子 (40%)
            load_factor = 1.0 - (node.current_load / node.capacity)
            score += load_factor * 0.4

            # 成功率因子 (30%)
            score += node.success_rate * 0.3

            # 响应时间因子 (20%)
            # 响应时间越短得分越高
            response_factor = 1.0 / (1.0 + node.average_response_time)
            score += response_factor * 0.2

            # 优先级匹配因子 (10%)
            if task.priority == Priority.CRITICAL and node.weight > 1.0:
                score += 0.1

            # 历史性能因子
            recent_performance = self._get_recent_performance(node.node_id)
            if recent_performance:
                score *= recent_performance

            return max(0.0, score)

        except Exception as e:
            self.logger.error(f"计算节点得分失败: {e}")
            return 0.0

    def _get_recent_performance(self, node_id: str) -> float:
        """获取节点最近性能"""
        try:
            if node_id not in self.performance_history:
                return 1.0

            history = self.performance_history[node_id]
            cutoff_time = datetime.utcnow() - self.adaptation_window

            # 过滤最近的性能数据
            recent_data = [(t, p) for t, p in history if t >= cutoff_time]

            if not recent_data:
                return 1.0

            # 计算平均性能
            avg_performance = sum(p for _, p in recent_data) / len(recent_data)
            return avg_performance

        except Exception as e:
            self.logger.error(f"获取节点性能失败: {e}")
            return 1.0

    def update_node_performance(self, node_id: str, performance: float) -> None:
        """更新节点性能"""
        try:
            if node_id not in self.performance_history:
                self.performance_history[node_id] = []

            # 添加性能记录
            self.performance_history[node_id].append((datetime.utcnow(), performance))

            # 清理过期数据
            cutoff_time = datetime.utcnow() - self.adaptation_window * 2
            self.performance_history[node_id] = [
                (t, p) for t, p in self.performance_history[node_id] if t >= cutoff_time
            ]

        except Exception as e:
            self.logger.error(f"更新节点性能失败: {e}")

    def get_load_distribution(self) -> dict[str, Any]:
        """获取负载分布"""
        try:
            total_capacity = sum(n.capacity for n in self.nodes)
            total_load = sum(n.current_load for n in self.nodes)

            node_stats = []
            for node in self.nodes:
                node_stats.append(
                    {
                        "node_id": node.node_id,
                        "capacity": node.capacity,
                        "current_load": node.current_load,
                        "utilization": (
                            node.current_load / node.capacity if node.capacity > 0 else 0
                        ),
                        "success_rate": node.success_rate,
                        "average_response_time": node.average_response_time,
                        "weight": node.weight,
                        "is_available": node.is_available,
                    }
                )

            return {
                "total_nodes": len(self.nodes),
                "available_nodes": len([n for n in self.nodes if n.is_available]),
                "total_capacity": total_capacity,
                "total_load": total_load,
                "overall_utilization": (total_load / total_capacity if total_capacity > 0 else 0),
                "algorithm": self.algorithm.value,
                "node_stats": node_stats,
            }

        except Exception as e:
            self.logger.error(f"获取负载分布失败: {e}")
            return {}


class TimeWindowScheduler:
    """时间窗口调度器"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 时间窗口配置
        self.peak_hours = list(range(9, 21))  # 9:00-21:00
        self.off_peak_hours = list(range(0, 8)) + list(range(22, 24))  # 00:00-08:00, 22:00-24:00

        # 调度策略
        self.peak_capacity_limit = 0.8  # 高峰期容量限制
        self.off_peak_boost = 1.2  # 错峰期容量提升

    def should_schedule_now(
        self, task: ScheduledTask, current_load: float
    ) -> tuple[bool, datetime | None]:
        """判断是否应该立即调度"""
        try:
            current_hour = datetime.utcnow().hour

            # 关键任务总是立即调度
            if task.priority == Priority.CRITICAL:
                return True, None

            # 检查截止时间
            if task.deadline and task.deadline <= datetime.utcnow() + timedelta(hours=1):
                return True, None

            # 错峰时段优先调度
            if current_hour in self.off_peak_hours:
                return True, None

            # 高峰时段检查负载
            if current_hour in self.peak_hours:
                if current_load < self.peak_capacity_limit:
                    return True, None
                else:
                    # 延迟到错峰时段
                    next_off_peak = self._get_next_off_peak_time()
                    return False, next_off_peak

            # 其他时段正常调度
            return True, None

        except Exception as e:
            self.logger.error(f"调度判断失败: {e}")
            return True, None

    def _get_next_off_peak_time(self) -> datetime:
        """获取下一个错峰时间"""
        now = datetime.utcnow()

        # 如果当前时间在22点之前，调度到22点
        if now.hour < 22:
            return now.replace(hour=22, minute=0, second=0, microsecond=0)
        else:
            # 调度到明天凌晨
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_optimal_schedule_time(self, task: ScheduledTask) -> datetime:
        """获取最优调度时间"""
        try:
            should_schedule, suggested_time = self.should_schedule_now(task, 0.5)  # 假设中等负载

            if should_schedule:
                return datetime.utcnow()
            elif suggested_time:
                return suggested_time
            else:
                # 默认延迟1小时
                return datetime.utcnow() + timedelta(hours=1)

        except Exception as e:
            self.logger.error(f"获取最优调度时间失败: {e}")
            return datetime.utcnow()

    def calculate_time_window_factor(self, schedule_time: datetime) -> float:
        """计算时间窗口因子"""
        try:
            hour = schedule_time.hour

            if hour in self.off_peak_hours:
                return self.off_peak_boost
            elif hour in self.peak_hours:
                return self.peak_capacity_limit
            else:
                return 1.0

        except Exception:
            return 1.0


def create_task_from_request(
    request_id: str,
    priority: Priority,
    payload: dict[str, Any],
    deadline: datetime | None = None,
    estimated_duration: float = 5.0,
) -> ScheduledTask:
    """从请求创建调度任务"""
    return ScheduledTask(
        task_id=request_id,
        priority=priority,
        estimated_duration=estimated_duration,
        deadline=deadline,
        payload=payload,
    )


def calculate_priority_from_request(request_data: dict[str, Any]) -> Priority:
    """从请求数据计算优先级"""
    try:
        # 检查显式优先级
        if "priority" in request_data:
            priority_str = request_data["priority"].lower()
            if priority_str == "critical":
                return Priority.CRITICAL
            elif priority_str == "high":
                return Priority.HIGH
            elif priority_str == "low":
                return Priority.LOW

        # 根据请求类型推断优先级
        request_type = request_data.get("type", "").lower()
        if request_type in ["grading", "批改"]:
            return Priority.HIGH
        elif request_type in ["translation", "翻译"]:
            return Priority.NORMAL
        elif request_type in ["analysis", "分析"]:
            return Priority.NORMAL

        # 根据用户类型推断优先级
        user_type = request_data.get("user_type", "").lower()
        if user_type == "teacher":
            return Priority.HIGH
        elif user_type == "admin":
            return Priority.CRITICAL

        return Priority.NORMAL

    except Exception:
        return Priority.NORMAL
