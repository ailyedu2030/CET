"""
优先级队列服务

提供高性能的任务队列管理：
- 优先级队列调度
- 任务分发和负载均衡
- 队列监控和统计
- 死信队列处理
- 批量任务处理
"""

import asyncio
import json
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import PriorityLevel, TaskStatus


class QueueType(Enum):
    """队列类型"""

    HIGH_PRIORITY = "high_priority"  # 高优先级队列
    NORMAL_PRIORITY = "normal_priority"  # 普通优先级队列
    LOW_PRIORITY = "low_priority"  # 低优先级队列
    BATCH_PROCESSING = "batch_processing"  # 批处理队列
    DEAD_LETTER = "dead_letter"  # 死信队列


class TaskType(Enum):
    """任务类型"""

    AI_GRADING = "ai_grading"  # AI批改
    CONTENT_GENERATION = "content_generation"  # 内容生成
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    NOTIFICATION = "notification"  # 通知发送
    BACKUP = "backup"  # 数据备份
    CLEANUP = "cleanup"  # 清理任务


@dataclass
class QueueTask:
    """队列任务"""

    task_id: str
    task_type: TaskType
    priority: PriorityLevel
    payload: dict[str, Any]
    created_at: datetime
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 超时时间（秒）
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass
class QueueStats:
    """队列统计"""

    queue_type: QueueType
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_processing_time: float
    throughput: float  # 每秒处理任务数
    timestamp: datetime


@dataclass
class WorkerStats:
    """工作者统计"""

    worker_id: str
    tasks_processed: int
    tasks_failed: int
    average_processing_time: float
    last_activity: datetime
    is_active: bool


class TaskProcessor:
    """任务处理器基类"""

    async def process(self, task: QueueTask) -> dict[str, Any]:
        """处理任务"""
        raise NotImplementedError("子类必须实现process方法")

    async def validate(self, task: QueueTask) -> bool:
        """验证任务"""
        return True

    async def on_success(self, task: QueueTask, result: dict[str, Any]) -> None:
        """任务成功回调"""
        pass

    async def on_failure(self, task: QueueTask, error: Exception) -> None:
        """任务失败回调"""
        pass


class QueueWorker:
    """队列工作者"""

    def __init__(
        self,
        worker_id: str,
        queue_service: "QueueService",
        processors: dict[TaskType, TaskProcessor],
    ) -> None:
        self.worker_id = worker_id
        self.queue_service = queue_service
        self.processors = processors
        self.logger = logging.getLogger(f"{__name__}.{worker_id}")

        self.is_running = False
        self.current_task: QueueTask | None = None
        self.stats = WorkerStats(
            worker_id=worker_id,
            tasks_processed=0,
            tasks_failed=0,
            average_processing_time=0.0,
            last_activity=datetime.utcnow(),
            is_active=False,
        )

        self.processing_times: deque[float] = deque(maxlen=100)

    async def start(self) -> None:
        """启动工作者"""
        if self.is_running:
            return

        self.is_running = True
        self.stats.is_active = True
        self.logger.info(f"工作者 {self.worker_id} 已启动")

        while self.is_running:
            try:
                # 获取任务
                task = await self.queue_service.get_next_task()
                if not task:
                    await asyncio.sleep(1)  # 没有任务时等待
                    continue

                # 处理任务
                await self._process_task(task)

            except Exception as e:
                self.logger.error(f"工作者循环错误: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """停止工作者"""
        self.is_running = False
        self.stats.is_active = False

        # 如果正在处理任务，等待完成
        if self.current_task:
            self.logger.info(f"等待当前任务完成: {self.current_task.task_id}")
            # 这里可以添加超时机制

        self.logger.info(f"工作者 {self.worker_id} 已停止")

    async def _process_task(self, task: QueueTask) -> None:
        """处理单个任务"""
        self.current_task = task
        start_time = time.time()

        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await self.queue_service.update_task_status(task)

            # 获取处理器
            processor = self.processors.get(task.task_type)
            if not processor:
                raise ValueError(f"未找到任务类型 {task.task_type} 的处理器")

            # 验证任务
            if not await processor.validate(task):
                raise ValueError("任务验证失败")

            # 处理任务
            result = await asyncio.wait_for(processor.process(task), timeout=task.timeout)

            # 任务成功
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.metadata["result"] = result

            await processor.on_success(task, result)
            await self.queue_service.update_task_status(task)

            self.stats.tasks_processed += 1
            self.logger.info(f"任务完成: {task.task_id}")

        except TimeoutError:
            # 任务超时
            task.status = TaskStatus.FAILED
            task.error_message = f"任务超时 ({task.timeout}秒)"
            await self._handle_task_failure(task)

        except Exception as e:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await self._handle_task_failure(task)

        finally:
            # 更新统计信息
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            self.stats.average_processing_time = sum(self.processing_times) / len(
                self.processing_times
            )
            self.stats.last_activity = datetime.utcnow()
            self.current_task = None

    async def _handle_task_failure(self, task: QueueTask) -> None:
        """处理任务失败"""
        try:
            processor = self.processors.get(task.task_type)
            if processor:
                await processor.on_failure(task, Exception(task.error_message or "未知错误"))

            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.scheduled_at = datetime.utcnow() + timedelta(
                    minutes=task.retry_count * 2
                )  # 指数退避
                await self.queue_service.requeue_task(task)
                self.logger.warning(
                    f"任务重试 ({task.retry_count}/{task.max_retries}): {task.task_id}"
                )
            else:
                # 移到死信队列
                await self.queue_service.move_to_dead_letter(task)
                self.logger.error(f"任务最终失败，移到死信队列: {task.task_id}")

            self.stats.tasks_failed += 1

        except Exception as e:
            self.logger.error(f"处理任务失败时出错: {e}")


class QueueService:
    """优先级队列服务"""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.logger = logging.getLogger(__name__)

        # 队列配置
        self.queue_configs = {
            QueueType.HIGH_PRIORITY: {"max_size": 1000, "batch_size": 1},
            QueueType.NORMAL_PRIORITY: {"max_size": 5000, "batch_size": 10},
            QueueType.LOW_PRIORITY: {"max_size": 10000, "batch_size": 50},
            QueueType.BATCH_PROCESSING: {"max_size": 2000, "batch_size": 100},
            QueueType.DEAD_LETTER: {"max_size": 1000, "batch_size": 1},
        }

        # 队列统计
        self.queue_stats: dict[QueueType, QueueStats] = {}

        # 工作者管理
        self.workers: dict[str, QueueWorker] = {}

        # 任务处理器注册
        self.processors: dict[TaskType, TaskProcessor] = {}

        # 初始化队列统计
        for queue_type in QueueType:
            self.queue_stats[queue_type] = QueueStats(
                queue_type=queue_type,
                total_tasks=0,
                pending_tasks=0,
                running_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                average_processing_time=0.0,
                throughput=0.0,
                timestamp=datetime.utcnow(),
            )

    def register_processor(self, task_type: TaskType, processor: TaskProcessor) -> None:
        """注册任务处理器"""
        self.processors[task_type] = processor
        self.logger.info(f"已注册任务处理器: {task_type.value}")

    async def enqueue_task(
        self,
        task_type: TaskType,
        payload: dict[str, Any],
        priority: PriorityLevel = PriorityLevel.NORMAL,
        scheduled_at: datetime | None = None,
        max_retries: int = 3,
        timeout: int = 300,
    ) -> str:
        """入队任务"""
        try:
            # 创建任务
            task = QueueTask(
                task_id=str(uuid.uuid4()),
                task_type=task_type,
                priority=priority,
                payload=payload,
                created_at=datetime.utcnow(),
                scheduled_at=scheduled_at,
                max_retries=max_retries,
                timeout=timeout,
            )

            # 选择队列
            queue_type = self._select_queue_by_priority(priority)

            # 序列化任务
            task_data = self._serialize_task(task)

            # 添加到Redis队列
            queue_key = f"queue:{queue_type.value}"

            if scheduled_at and scheduled_at > datetime.utcnow():
                # 延迟任务，添加到延迟队列
                delay_score = scheduled_at.timestamp()
                self.redis.zadd(f"{queue_key}:delayed", {task_data: delay_score})
            else:
                # 立即任务，根据优先级添加到队列
                if priority == PriorityLevel.HIGH:
                    self.redis.lpush(queue_key, task_data)  # 高优先级放在队列前面
                else:
                    self.redis.rpush(queue_key, task_data)  # 其他优先级放在队列后面

            # 更新统计
            self.queue_stats[queue_type].total_tasks += 1
            self.queue_stats[queue_type].pending_tasks += 1

            self.logger.info(f"任务已入队: {task.task_id} ({task_type.value}, {priority.value})")
            return task.task_id

        except Exception as e:
            self.logger.error(f"任务入队失败: {e}")
            raise

    async def get_next_task(self, worker_id: str | None = None) -> QueueTask | None:
        """获取下一个任务"""
        try:
            # 处理延迟任务
            await self._process_delayed_tasks()

            # 按优先级顺序检查队列
            queue_order = [
                QueueType.HIGH_PRIORITY,
                QueueType.NORMAL_PRIORITY,
                QueueType.LOW_PRIORITY,
                QueueType.BATCH_PROCESSING,
            ]

            for queue_type in queue_order:
                queue_key = f"queue:{queue_type.value}"

                # 从队列中获取任务
                task_data_raw = self.redis.lpop(queue_key)
                if task_data_raw and isinstance(task_data_raw, str | bytes):
                    task_data = task_data_raw
                    task = self._deserialize_task(task_data)

                    # 更新统计
                    self.queue_stats[queue_type].pending_tasks -= 1
                    self.queue_stats[queue_type].running_tasks += 1

                    return task

            return None

        except Exception as e:
            self.logger.error(f"获取任务失败: {e}")
            return None

    async def update_task_status(self, task: QueueTask) -> None:
        """更新任务状态"""
        try:
            # 将任务状态存储到Redis
            task_key = f"task:{task.task_id}"
            task_data = self._serialize_task(task)
            self.redis.setex(task_key, 86400, task_data)  # 24小时过期

            # 更新队列统计
            queue_type = self._select_queue_by_priority(task.priority)
            stats = self.queue_stats[queue_type]

            if task.status == TaskStatus.COMPLETED:
                stats.running_tasks -= 1
                stats.completed_tasks += 1

                # 更新平均处理时间
                if task.started_at and task.completed_at:
                    processing_time = (task.completed_at - task.started_at).total_seconds()
                    current_avg = stats.average_processing_time
                    total_completed = stats.completed_tasks
                    stats.average_processing_time = (
                        current_avg * (total_completed - 1) + processing_time
                    ) / total_completed

            elif task.status == TaskStatus.FAILED:
                stats.running_tasks -= 1
                stats.failed_tasks += 1

            stats.timestamp = datetime.utcnow()

        except Exception as e:
            self.logger.error(f"更新任务状态失败: {e}")

    async def requeue_task(self, task: QueueTask) -> None:
        """重新入队任务"""
        try:
            queue_type = self._select_queue_by_priority(task.priority)
            queue_key = f"queue:{queue_type.value}"
            task_data = self._serialize_task(task)

            if task.scheduled_at and task.scheduled_at > datetime.utcnow():
                # 延迟重试
                delay_score = task.scheduled_at.timestamp()
                self.redis.zadd(f"{queue_key}:delayed", {task_data: delay_score})
            else:
                # 立即重试，放在队列末尾
                self.redis.rpush(queue_key, task_data)

            # 更新统计
            self.queue_stats[queue_type].pending_tasks += 1

        except Exception as e:
            self.logger.error(f"重新入队任务失败: {e}")

    async def move_to_dead_letter(self, task: QueueTask) -> None:
        """移动到死信队列"""
        try:
            dead_letter_key = f"queue:{QueueType.DEAD_LETTER.value}"
            task_data = self._serialize_task(task)
            self.redis.rpush(dead_letter_key, task_data)

            # 更新统计
            self.queue_stats[QueueType.DEAD_LETTER].total_tasks += 1
            self.queue_stats[QueueType.DEAD_LETTER].pending_tasks += 1

            self.logger.error(f"任务移到死信队列: {task.task_id}")

        except Exception as e:
            self.logger.error(f"移动到死信队列失败: {e}")

    async def _process_delayed_tasks(self) -> None:
        """处理延迟任务"""
        try:
            current_time = time.time()

            for queue_type in QueueType:
                if queue_type == QueueType.DEAD_LETTER:
                    continue

                delayed_key = f"queue:{queue_type.value}:delayed"
                queue_key = f"queue:{queue_type.value}"

                # 获取到期的延迟任务
                expired_tasks_raw = self.redis.zrangebyscore(
                    delayed_key, 0, current_time, withscores=True
                )

                # 确保expired_tasks_raw是可迭代的
                if hasattr(expired_tasks_raw, "__iter__"):
                    expired_tasks = expired_tasks_raw
                else:
                    expired_tasks = []

                for task_data, _score in expired_tasks:
                    # 移动到正常队列
                    self.redis.rpush(queue_key, task_data)
                    self.redis.zrem(delayed_key, task_data)

        except Exception as e:
            self.logger.error(f"处理延迟任务失败: {e}")

    def _select_queue_by_priority(self, priority: PriorityLevel) -> QueueType:
        """根据优先级选择队列"""
        if priority == PriorityLevel.HIGH:
            return QueueType.HIGH_PRIORITY
        elif priority == PriorityLevel.LOW:
            return QueueType.LOW_PRIORITY
        else:
            return QueueType.NORMAL_PRIORITY

    def _serialize_task(self, task: QueueTask) -> str:
        """序列化任务"""
        task_dict = {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "priority": task.priority.value,
            "payload": task.payload,
            "created_at": task.created_at.isoformat(),
            "scheduled_at": (task.scheduled_at.isoformat() if task.scheduled_at else None),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (task.completed_at.isoformat() if task.completed_at else None),
            "status": task.status.value,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "timeout": task.timeout,
            "metadata": task.metadata,
            "error_message": task.error_message,
        }
        return json.dumps(task_dict)

    def _deserialize_task(self, task_data: str | bytes) -> QueueTask:
        """反序列化任务"""
        if isinstance(task_data, bytes):
            task_data = task_data.decode("utf-8")

        task_dict = json.loads(task_data)

        return QueueTask(
            task_id=task_dict["task_id"],
            task_type=TaskType(task_dict["task_type"]),
            priority=PriorityLevel(task_dict["priority"]),
            payload=task_dict["payload"],
            created_at=datetime.fromisoformat(task_dict["created_at"]),
            scheduled_at=(
                datetime.fromisoformat(task_dict["scheduled_at"])
                if task_dict["scheduled_at"]
                else None
            ),
            started_at=(
                datetime.fromisoformat(task_dict["started_at"]) if task_dict["started_at"] else None
            ),
            completed_at=(
                datetime.fromisoformat(task_dict["completed_at"])
                if task_dict["completed_at"]
                else None
            ),
            status=TaskStatus(task_dict["status"]),
            retry_count=task_dict["retry_count"],
            max_retries=task_dict["max_retries"],
            timeout=task_dict["timeout"],
            metadata=task_dict["metadata"],
            error_message=task_dict["error_message"],
        )

    async def create_worker(self, worker_id: str) -> QueueWorker:
        """创建工作者"""
        worker = QueueWorker(worker_id, self, self.processors)
        self.workers[worker_id] = worker
        return worker

    async def start_worker(self, worker_id: str) -> None:
        """启动工作者"""
        if worker_id in self.workers:
            await self.workers[worker_id].start()

    async def stop_worker(self, worker_id: str) -> None:
        """停止工作者"""
        if worker_id in self.workers:
            await self.workers[worker_id].stop()

    def get_queue_stats(self) -> dict[str, Any]:
        """获取队列统计"""
        try:
            stats_dict = {}

            for queue_type, stats in self.queue_stats.items():
                # 计算吞吐量
                if stats.completed_tasks > 0 and stats.average_processing_time > 0:
                    stats.throughput = 1.0 / stats.average_processing_time

                stats_dict[queue_type.value] = {
                    "total_tasks": stats.total_tasks,
                    "pending_tasks": stats.pending_tasks,
                    "running_tasks": stats.running_tasks,
                    "completed_tasks": stats.completed_tasks,
                    "failed_tasks": stats.failed_tasks,
                    "average_processing_time": stats.average_processing_time,
                    "throughput": stats.throughput,
                    "success_rate": (
                        stats.completed_tasks / (stats.completed_tasks + stats.failed_tasks)
                        if (stats.completed_tasks + stats.failed_tasks) > 0
                        else 0.0
                    ),
                }

            # 工作者统计
            worker_stats = {}
            for worker_id, worker in self.workers.items():
                worker_stats[worker_id] = {
                    "tasks_processed": worker.stats.tasks_processed,
                    "tasks_failed": worker.stats.tasks_failed,
                    "average_processing_time": worker.stats.average_processing_time,
                    "last_activity": worker.stats.last_activity.isoformat(),
                    "is_active": worker.stats.is_active,
                    "success_rate": (
                        worker.stats.tasks_processed
                        / (worker.stats.tasks_processed + worker.stats.tasks_failed)
                        if (worker.stats.tasks_processed + worker.stats.tasks_failed) > 0
                        else 0.0
                    ),
                }

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "queues": stats_dict,
                "workers": worker_stats,
                "total_workers": len(self.workers),
                "active_workers": len([w for w in self.workers.values() if w.stats.is_active]),
            }

        except Exception as e:
            self.logger.error(f"获取队列统计失败: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# 全局队列服务实例
_queue_service: QueueService | None = None


async def get_queue_service() -> QueueService:
    """获取队列服务实例"""
    global _queue_service

    if _queue_service is None:
        from app.core.database import get_db
        from app.core.redis import get_redis

        async for db in get_db():
            redis = await get_redis()
            _queue_service = QueueService(db, redis)
            break

    if _queue_service is None:
        raise RuntimeError("无法初始化队列服务")

    return _queue_service
