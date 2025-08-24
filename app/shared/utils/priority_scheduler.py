"""
优先级调度器

提供智能的任务优先级调度和资源分配：
- 多级优先级队列
- 动态优先级调整
- 负载均衡算法
- 公平性保证
- 饥饿预防机制
"""

import asyncio
import heapq
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.shared.models.enums import PriorityLevel


class SchedulingAlgorithm(Enum):
    """调度算法"""

    FIFO = "fifo"  # 先进先出
    PRIORITY = "priority"  # 优先级调度
    ROUND_ROBIN = "round_robin"  # 轮转调度
    WEIGHTED_FAIR = "weighted_fair"  # 加权公平调度
    ADAPTIVE = "adaptive"  # 自适应调度


class TaskCategory(Enum):
    """任务类别"""

    INTERACTIVE = "interactive"  # 交互式任务
    BATCH = "batch"  # 批处理任务
    REAL_TIME = "real_time"  # 实时任务
    BACKGROUND = "background"  # 后台任务


@dataclass
class ScheduledTask:
    """调度任务"""

    task_id: str
    priority: PriorityLevel
    category: TaskCategory
    payload: dict[str, Any]
    created_at: datetime
    estimated_duration: float = 0.0  # 预估执行时间（秒）
    deadline: datetime | None = None  # 截止时间
    retry_count: int = 0
    max_retries: int = 3
    dependencies: list[str] = field(default_factory=list)  # 依赖任务ID
    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "ScheduledTask") -> bool:
        """优先级比较（用于堆排序）"""
        # 优先级数值越大，优先级越高
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value

        # 相同优先级时，按创建时间排序
        return self.created_at < other.created_at


@dataclass
class SchedulingMetrics:
    """调度指标"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_wait_time: float = 0.0
    average_execution_time: float = 0.0
    throughput: float = 0.0  # 任务/秒
    fairness_index: float = 0.0  # 公平性指数
    starvation_count: int = 0  # 饥饿任务数
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ResourcePool:
    """资源池"""

    pool_id: str
    capacity: int  # 最大并发任务数
    current_load: int = 0
    task_categories: list[TaskCategory] = field(default_factory=list)
    performance_factor: float = 1.0  # 性能因子


class PriorityScheduler:
    """优先级调度器"""

    def __init__(
        self,
        algorithm: SchedulingAlgorithm = SchedulingAlgorithm.ADAPTIVE,
        max_concurrent_tasks: int = 10,
    ) -> None:
        self.algorithm = algorithm
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(__name__)

        # 任务队列（多级优先级）
        self.task_queues: dict[PriorityLevel, list[ScheduledTask]] = {
            level: [] for level in PriorityLevel
        }

        # 运行中的任务
        self.running_tasks: dict[str, ScheduledTask] = {}

        # 已完成的任务历史
        self.completed_tasks: deque[ScheduledTask] = deque(maxlen=1000)

        # 任务等待时间记录
        self.wait_times: dict[str, float] = {}

        # 资源池管理
        self.resource_pools: dict[str, ResourcePool] = {}

        # 调度指标
        self.metrics = SchedulingMetrics()

        # 公平性统计
        self.category_stats: dict[TaskCategory, dict[str, Any]] = defaultdict(
            lambda: {
                "submitted": 0,
                "completed": 0,
                "total_wait_time": 0.0,
                "total_execution_time": 0.0,
            }
        )

        # 饥饿预防
        self.starvation_threshold = 300.0  # 5分钟
        self.aging_factor = 1.1  # 老化因子

        # 调度器状态
        self.is_running = False
        self.scheduler_task: asyncio.Task[None] | None = None

    def add_resource_pool(self, pool: ResourcePool) -> None:
        """添加资源池"""
        self.resource_pools[pool.pool_id] = pool
        self.logger.info(f"添加资源池: {pool.pool_id}, 容量: {pool.capacity}")

    async def submit_task(self, task: ScheduledTask) -> str:
        """提交任务"""
        try:
            # 检查依赖关系
            if not await self._check_dependencies(task):
                raise ValueError(f"任务依赖未满足: {task.dependencies}")

            # 选择合适的队列
            priority_queue = self.task_queues[task.priority]

            # 添加到队列
            heapq.heappush(priority_queue, task)

            # 记录提交时间
            self.wait_times[task.task_id] = time.time()

            # 更新统计
            self.metrics.total_tasks += 1
            self.category_stats[task.category]["submitted"] += 1

            self.logger.info(
                f"任务已提交: {task.task_id} "
                f"(优先级: {task.priority.name}, 类别: {task.category.name})"
            )

            return task.task_id

        except Exception as e:
            self.logger.error(f"提交任务失败: {e}")
            raise

    async def start_scheduler(self) -> None:
        """启动调度器"""
        if self.is_running:
            return

        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("优先级调度器已启动")

    async def stop_scheduler(self) -> None:
        """停止调度器"""
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        self.logger.info("优先级调度器已停止")

    async def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self.is_running:
            try:
                # 检查是否有可用资源
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue

                # 获取下一个任务
                next_task = await self._get_next_task()
                if not next_task:
                    await asyncio.sleep(0.1)
                    continue

                # 执行任务
                await self._execute_task(next_task)

            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(1)

    async def _get_next_task(self) -> ScheduledTask | None:
        """获取下一个要执行的任务"""
        try:
            # 应用饥饿预防机制
            await self._apply_aging()

            # 根据算法选择任务
            if self.algorithm == SchedulingAlgorithm.PRIORITY:
                return await self._get_priority_task()
            elif self.algorithm == SchedulingAlgorithm.ROUND_ROBIN:
                return await self._get_round_robin_task()
            elif self.algorithm == SchedulingAlgorithm.WEIGHTED_FAIR:
                return await self._get_weighted_fair_task()
            elif self.algorithm == SchedulingAlgorithm.ADAPTIVE:
                return await self._get_adaptive_task()
            else:  # FIFO
                return await self._get_fifo_task()

        except Exception as e:
            self.logger.error(f"获取下一个任务失败: {e}")
            return None

    async def _get_priority_task(self) -> ScheduledTask | None:
        """基于优先级获取任务"""
        # 按优先级从高到低检查队列
        for priority in sorted(PriorityLevel, key=lambda x: x.value, reverse=True):
            queue = self.task_queues[priority]
            if queue:
                return heapq.heappop(queue)
        return None

    async def _get_round_robin_task(self) -> ScheduledTask | None:
        """轮转调度获取任务"""
        # 简化的轮转实现：在各优先级间轮转
        for priority in PriorityLevel:
            queue = self.task_queues[priority]
            if queue:
                return heapq.heappop(queue)
        return None

    async def _get_weighted_fair_task(self) -> ScheduledTask | None:
        """加权公平调度获取任务"""
        # 根据任务类别的权重选择
        category_weights = {
            TaskCategory.REAL_TIME: 4,
            TaskCategory.INTERACTIVE: 3,
            TaskCategory.BATCH: 2,
            TaskCategory.BACKGROUND: 1,
        }

        # 计算各类别的积分
        category_scores = {}
        for category, weight in category_weights.items():
            stats = self.category_stats[category]
            if stats["submitted"] > 0:
                completion_rate = stats["completed"] / stats["submitted"]
                # 完成率低的类别获得更高积分
                category_scores[category] = weight * (1.0 - completion_rate)

        # 选择积分最高的类别
        if not category_scores:
            return await self._get_priority_task()

        target_category = max(category_scores, key=lambda x: category_scores[x])

        # 在目标类别中选择任务
        for priority in sorted(PriorityLevel, key=lambda x: x.value, reverse=True):
            queue = self.task_queues[priority]
            for i, task in enumerate(queue):
                if task.category == target_category:
                    return queue.pop(i)

        # 如果目标类别没有任务，回退到优先级调度
        return await self._get_priority_task()

    async def _get_adaptive_task(self) -> ScheduledTask | None:
        """自适应调度获取任务"""
        # 根据当前系统状态选择最佳策略
        current_load = len(self.running_tasks) / self.max_concurrent_tasks

        if current_load > 0.8:
            # 高负载：优先处理高优先级任务
            return await self._get_priority_task()
        elif current_load < 0.3:
            # 低负载：使用公平调度
            return await self._get_weighted_fair_task()
        else:
            # 中等负载：混合策略
            if time.time() % 2 < 1:
                return await self._get_priority_task()
            else:
                return await self._get_weighted_fair_task()

    async def _get_fifo_task(self) -> ScheduledTask | None:
        """先进先出获取任务"""
        earliest_task = None
        earliest_time = None

        for queue in self.task_queues.values():
            for task in queue:
                if earliest_time is None or task.created_at < earliest_time:
                    earliest_task = task
                    earliest_time = task.created_at

        if earliest_task:
            # 从对应队列中移除
            queue = self.task_queues[earliest_task.priority]
            queue.remove(earliest_task)
            heapq.heapify(queue)  # 重新堆化

        return earliest_task

    async def _apply_aging(self) -> None:
        """应用老化机制防止饥饿"""
        current_time = time.time()

        for priority_level, queue in self.task_queues.items():
            for task in queue:
                wait_time = current_time - self.wait_times.get(task.task_id, current_time)

                # 如果等待时间超过阈值，提升优先级
                if wait_time > self.starvation_threshold:
                    if task.priority != PriorityLevel.HIGH:
                        # 移动到更高优先级队列
                        queue.remove(task)
                        heapq.heapify(queue)

                        # 提升优先级
                        if task.priority == PriorityLevel.LOW:
                            new_priority = PriorityLevel.NORMAL
                        else:
                            new_priority = PriorityLevel.HIGH

                        task.priority = new_priority
                        heapq.heappush(self.task_queues[new_priority], task)

                        self.metrics.starvation_count += 1
                        self.logger.warning(
                            f"任务 {task.task_id} 因饥饿提升优先级: "
                            f"{priority_level.name} -> {new_priority.name}"
                        )

    async def _execute_task(self, task: ScheduledTask) -> None:
        """执行任务"""
        try:
            # 记录开始执行时间
            start_time = time.time()
            wait_time = start_time - self.wait_times.get(task.task_id, start_time)

            # 添加到运行中任务
            self.running_tasks[task.task_id] = task

            self.logger.info(f"开始执行任务: {task.task_id}")

            # 创建任务执行协程
            execution_task = asyncio.create_task(self._run_task(task))

            # 等待任务完成
            await execution_task

            # 记录完成时间
            end_time = time.time()
            execution_time = end_time - start_time

            # 更新统计
            self._update_completion_stats(task, wait_time, execution_time)

            self.logger.info(
                f"任务完成: {task.task_id} (等待: {wait_time:.2f}s, 执行: {execution_time:.2f}s)"
            )

        except Exception as e:
            self.logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
            self.metrics.failed_tasks += 1
            self.category_stats[task.category]["completed"] += 1  # 也算作完成

        finally:
            # 从运行中任务移除
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # 清理等待时间记录
            if task.task_id in self.wait_times:
                del self.wait_times[task.task_id]

    async def _run_task(self, task: ScheduledTask) -> None:
        """运行具体任务（模拟）"""
        # 这里应该调用实际的任务处理器
        # 目前只是模拟执行
        execution_time = task.estimated_duration or 1.0
        await asyncio.sleep(execution_time)

    def _update_completion_stats(
        self, task: ScheduledTask, wait_time: float, execution_time: float
    ) -> None:
        """更新完成统计"""
        # 添加到已完成任务
        self.completed_tasks.append(task)

        # 更新全局指标
        self.metrics.completed_tasks += 1

        # 更新平均等待时间
        total_completed = self.metrics.completed_tasks
        current_avg_wait = self.metrics.average_wait_time
        self.metrics.average_wait_time = (
            current_avg_wait * (total_completed - 1) + wait_time
        ) / total_completed

        # 更新平均执行时间
        current_avg_exec = self.metrics.average_execution_time
        self.metrics.average_execution_time = (
            current_avg_exec * (total_completed - 1) + execution_time
        ) / total_completed

        # 更新类别统计
        category_stats = self.category_stats[task.category]
        category_stats["completed"] += 1
        category_stats["total_wait_time"] += wait_time
        category_stats["total_execution_time"] += execution_time

        # 计算吞吐量
        if hasattr(self, "_start_time"):
            elapsed_time = time.time() - self._start_time
            if elapsed_time > 0:
                self.metrics.throughput = self.metrics.completed_tasks / elapsed_time
        else:
            self._start_time: float = time.time()

        # 计算公平性指数
        self._calculate_fairness_index()

        self.metrics.timestamp = datetime.utcnow()

    def _calculate_fairness_index(self) -> None:
        """计算公平性指数（Jain's Fairness Index）"""
        if not self.category_stats:
            self.metrics.fairness_index = 1.0
            return

        # 计算各类别的完成率
        completion_rates = []
        for stats in self.category_stats.values():
            if stats["submitted"] > 0:
                rate = stats["completed"] / stats["submitted"]
                completion_rates.append(rate)

        if not completion_rates:
            self.metrics.fairness_index = 1.0
            return

        # Jain's Fairness Index
        n = len(completion_rates)
        sum_rates = sum(completion_rates)
        sum_squares = sum(rate**2 for rate in completion_rates)

        if sum_squares > 0:
            self.metrics.fairness_index = (sum_rates**2) / (n * sum_squares)
        else:
            self.metrics.fairness_index = 1.0

    async def _check_dependencies(self, task: ScheduledTask) -> bool:
        """检查任务依赖"""
        if not task.dependencies:
            return True

        # 检查依赖任务是否已完成
        completed_task_ids = {t.task_id for t in self.completed_tasks}
        for dep_id in task.dependencies:
            if dep_id not in completed_task_ids:
                return False

        return True

    def get_metrics(self) -> SchedulingMetrics:
        """获取调度指标"""
        return self.metrics

    def get_queue_status(self) -> dict[str, Any]:
        """获取队列状态"""
        status: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm": self.algorithm.value,
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "queue_lengths": {},
            "category_stats": {},
        }

        # 队列长度统计
        for priority, queue in self.task_queues.items():
            status["queue_lengths"][priority.name] = len(queue)

        # 类别统计
        for category, stats in self.category_stats.items():
            if stats["submitted"] > 0:
                avg_wait = (
                    stats["total_wait_time"] / stats["completed"] if stats["completed"] > 0 else 0.0
                )
                avg_exec = (
                    stats["total_execution_time"] / stats["completed"]
                    if stats["completed"] > 0
                    else 0.0
                )
                completion_rate = stats["completed"] / stats["submitted"]

                category_status: dict[str, Any] = {
                    "submitted": stats["submitted"],
                    "completed": stats["completed"],
                    "completion_rate": completion_rate,
                    "average_wait_time": avg_wait,
                    "average_execution_time": avg_exec,
                }
                status["category_stats"][category.name] = category_status

        return status

    def clear_completed_tasks(self) -> int:
        """清理已完成任务历史"""
        count = len(self.completed_tasks)
        self.completed_tasks.clear()
        return count


# 全局调度器实例
_priority_scheduler: PriorityScheduler | None = None


def get_priority_scheduler(
    algorithm: SchedulingAlgorithm = SchedulingAlgorithm.ADAPTIVE,
    max_concurrent_tasks: int = 10,
) -> PriorityScheduler:
    """获取优先级调度器实例"""
    global _priority_scheduler

    if _priority_scheduler is None:
        _priority_scheduler = PriorityScheduler(algorithm, max_concurrent_tasks)

    return _priority_scheduler


# 便捷函数
async def schedule_task(
    task_id: str,
    priority: PriorityLevel,
    category: TaskCategory,
    payload: dict[str, Any],
    estimated_duration: float = 0.0,
    deadline: datetime | None = None,
) -> str:
    """调度任务的便捷函数"""
    scheduler = get_priority_scheduler()

    task = ScheduledTask(
        task_id=task_id,
        priority=priority,
        category=category,
        payload=payload,
        created_at=datetime.utcnow(),
        estimated_duration=estimated_duration,
        deadline=deadline,
    )

    return await scheduler.submit_task(task)


async def schedule_high_priority_task(task_id: str, payload: dict[str, Any]) -> str:
    """调度高优先级任务"""
    return await schedule_task(task_id, PriorityLevel.HIGH, TaskCategory.INTERACTIVE, payload)


async def schedule_batch_task(task_id: str, payload: dict[str, Any]) -> str:
    """调度批处理任务"""
    return await schedule_task(task_id, PriorityLevel.NORMAL, TaskCategory.BATCH, payload)
