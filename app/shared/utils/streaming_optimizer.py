"""
流式输出优化器

提供高效的流式数据处理和优化：
- 流式数据分块处理
- 自适应缓冲区管理
- 压缩和编码优化
- 网络传输优化
- 实时性能监控
"""

import asyncio
import gzip
import json
import logging
import time
from collections import deque
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class StreamingMode(Enum):
    """流式模式"""

    REAL_TIME = "real_time"  # 实时模式
    BUFFERED = "buffered"  # 缓冲模式
    ADAPTIVE = "adaptive"  # 自适应模式


class CompressionType(Enum):
    """压缩类型"""

    NONE = "none"  # 无压缩
    GZIP = "gzip"  # GZIP压缩
    DEFLATE = "deflate"  # Deflate压缩


@dataclass
class StreamChunk:
    """流数据块"""

    chunk_id: str
    data: Any
    timestamp: datetime
    size: int
    compressed: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class StreamingConfig:
    """流式配置"""

    chunk_size: int = 1024  # 块大小（字节）
    buffer_size: int = 10  # 缓冲区大小（块数）
    compression_threshold: int = 512  # 压缩阈值（字节）
    compression_type: CompressionType = CompressionType.GZIP
    mode: StreamingMode = StreamingMode.ADAPTIVE
    max_latency: float = 0.2  # 最大延迟（秒）
    enable_metrics: bool = True


@dataclass
class StreamingMetrics:
    """流式指标"""

    total_chunks: int = 0
    total_bytes: int = 0
    compressed_chunks: int = 0
    compression_ratio: float = 0.0
    average_latency: float = 0.0
    throughput: float = 0.0  # 字节/秒
    error_count: int = 0
    timestamp: datetime | None = None


class StreamBuffer:
    """流缓冲区"""

    def __init__(self, max_size: int = 10) -> None:
        self.max_size = max_size
        self.buffer: deque[StreamChunk] = deque(maxlen=max_size)
        self.total_size = 0
        self.last_flush = time.time()

    def add_chunk(self, chunk: StreamChunk) -> None:
        """添加数据块"""
        # 如果缓冲区满了，移除最旧的块
        if len(self.buffer) >= self.max_size:
            old_chunk = self.buffer.popleft()
            self.total_size -= old_chunk.size

        self.buffer.append(chunk)
        self.total_size += chunk.size

    def get_chunks(self, max_chunks: int | None = None) -> list[StreamChunk]:
        """获取数据块"""
        if max_chunks is None:
            chunks = list(self.buffer)
            self.buffer.clear()
            self.total_size = 0
        else:
            chunks = []
            for _ in range(min(max_chunks, len(self.buffer))):
                chunk = self.buffer.popleft()
                chunks.append(chunk)
                self.total_size -= chunk.size

        return chunks

    def should_flush(self, max_latency: float) -> bool:
        """检查是否应该刷新缓冲区"""
        if not self.buffer:
            return False

        # 基于时间的刷新
        if time.time() - self.last_flush > max_latency:
            return True

        # 基于大小的刷新
        if len(self.buffer) >= self.max_size:
            return True

        return False

    def flush(self) -> list[StreamChunk]:
        """刷新缓冲区"""
        chunks = self.get_chunks()
        self.last_flush = time.time()
        return chunks

    def is_empty(self) -> bool:
        """检查缓冲区是否为空"""
        return len(self.buffer) == 0

    def get_size(self) -> int:
        """获取缓冲区大小"""
        return self.total_size


class StreamingOptimizer:
    """流式输出优化器"""

    def __init__(self, config: StreamingConfig | None = None) -> None:
        self.config = config or StreamingConfig()
        self.logger = logging.getLogger(__name__)

        # 缓冲区管理
        self.buffer = StreamBuffer(self.config.buffer_size)

        # 性能指标
        self.metrics = StreamingMetrics(timestamp=datetime.utcnow())
        self.latency_history: deque[float] = deque(maxlen=100)

        # 压缩器
        self.compressor = self._get_compressor()

        # 自适应参数
        self.adaptive_chunk_size = self.config.chunk_size
        self.adaptive_buffer_size = self.config.buffer_size

    def _get_compressor(self) -> Callable[[bytes], bytes] | None:
        """获取压缩器"""
        if self.config.compression_type == CompressionType.GZIP:
            return gzip.compress
        elif self.config.compression_type == CompressionType.DEFLATE:
            import zlib

            return zlib.compress
        else:
            return None

    async def process_stream(
        self, data_generator: AsyncGenerator[Any, None]
    ) -> AsyncGenerator[StreamChunk, None]:
        """处理流式数据"""
        chunk_counter = 0

        try:
            async for data in data_generator:
                start_time = time.time()

                # 创建数据块
                chunk = await self._create_chunk(data, chunk_counter)
                chunk_counter += 1

                # 根据模式处理
                if self.config.mode == StreamingMode.REAL_TIME:
                    # 实时模式：立即输出
                    yield chunk
                elif self.config.mode == StreamingMode.BUFFERED:
                    # 缓冲模式：添加到缓冲区
                    self.buffer.add_chunk(chunk)
                    if self.buffer.should_flush(self.config.max_latency):
                        for buffered_chunk in self.buffer.flush():
                            yield buffered_chunk
                elif self.config.mode == StreamingMode.ADAPTIVE:
                    # 自适应模式：根据性能动态调整
                    await self._adaptive_processing(chunk)
                    if self.buffer.should_flush(self.config.max_latency):
                        for buffered_chunk in self.buffer.flush():
                            yield buffered_chunk

                # 更新性能指标
                if self.config.enable_metrics:
                    latency = time.time() - start_time
                    self._update_metrics(chunk, latency)

        except Exception as e:
            self.logger.error(f"流处理错误: {e}")
            self.metrics.error_count += 1
            raise

        finally:
            # 刷新剩余缓冲区
            if not self.buffer.is_empty():
                for chunk in self.buffer.flush():
                    yield chunk

    async def _create_chunk(self, data: Any, chunk_id: int) -> StreamChunk:
        """创建数据块"""
        # 序列化数据
        if isinstance(data, dict | list):
            serialized_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        elif isinstance(data, str):
            serialized_data = data.encode("utf-8")
        elif isinstance(data, bytes):
            serialized_data = data
        else:
            serialized_data = str(data).encode("utf-8")

        # 计算原始大小
        original_size = len(serialized_data)

        # 压缩处理
        compressed = False
        if self.compressor and original_size > self.config.compression_threshold:
            try:
                compressed_data = self.compressor(serialized_data)
                if len(compressed_data) < original_size:
                    serialized_data = compressed_data
                    compressed = True
                    self.metrics.compressed_chunks += 1
            except Exception as e:
                self.logger.warning(f"压缩失败: {e}")

        # 创建数据块
        chunk = StreamChunk(
            chunk_id=f"chunk_{chunk_id}",
            data=serialized_data,
            timestamp=datetime.utcnow(),
            size=len(serialized_data),
            compressed=compressed,
            metadata={
                "original_size": original_size,
                "compression_ratio": (len(serialized_data) / original_size if compressed else 1.0),
            },
        )

        return chunk

    async def _adaptive_processing(self, chunk: StreamChunk) -> None:
        """自适应处理"""
        # 根据当前性能调整参数
        if self.metrics.average_latency > self.config.max_latency * 1.5:
            # 延迟过高，减少缓冲区大小
            self.adaptive_buffer_size = max(1, self.adaptive_buffer_size - 1)
            self.buffer.max_size = self.adaptive_buffer_size
        elif self.metrics.average_latency < self.config.max_latency * 0.5:
            # 延迟较低，可以增加缓冲区大小
            self.adaptive_buffer_size = min(20, self.adaptive_buffer_size + 1)
            self.buffer.max_size = self.adaptive_buffer_size

        # 根据吞吐量调整块大小
        if self.metrics.throughput > 0:
            target_throughput = 1024 * 1024  # 1MB/s
            if self.metrics.throughput < target_throughput * 0.8:
                # 吞吐量低，增加块大小
                self.adaptive_chunk_size = min(8192, self.adaptive_chunk_size * 1.2)
            elif self.metrics.throughput > target_throughput * 1.2:
                # 吞吐量高，可以减少块大小以降低延迟
                self.adaptive_chunk_size = max(256, self.adaptive_chunk_size * 0.8)

        # 添加到缓冲区
        self.buffer.add_chunk(chunk)

    def _update_metrics(self, chunk: StreamChunk, latency: float) -> None:
        """更新性能指标"""
        self.metrics.total_chunks += 1
        self.metrics.total_bytes += chunk.size
        self.latency_history.append(latency)

        # 计算平均延迟
        if self.latency_history:
            self.metrics.average_latency = sum(self.latency_history) / len(self.latency_history)

        # 计算压缩比
        if self.metrics.total_chunks > 0:
            self.metrics.compression_ratio = (
                self.metrics.compressed_chunks / self.metrics.total_chunks
            )

        # 计算吞吐量
        current_time = time.time()
        if hasattr(self, "_start_time"):
            elapsed_time = current_time - self._start_time
            if elapsed_time > 0:
                self.metrics.throughput = self.metrics.total_bytes / elapsed_time
        else:
            self._start_time: float = current_time

        self.metrics.timestamp = datetime.utcnow()

    async def optimize_for_network(self, chunks: list[StreamChunk]) -> list[StreamChunk]:
        """网络传输优化"""
        optimized_chunks = []

        for chunk in chunks:
            # 网络优化处理
            optimized_chunk = await self._optimize_chunk_for_network(chunk)
            optimized_chunks.append(optimized_chunk)

        return optimized_chunks

    async def _optimize_chunk_for_network(self, chunk: StreamChunk) -> StreamChunk:
        """优化单个数据块用于网络传输"""
        # 添加网络传输元数据
        if chunk.metadata is None:
            chunk.metadata = {}

        chunk.metadata.update(
            {
                "network_optimized": True,
                "transfer_encoding": "chunked",
                "content_encoding": (
                    self.config.compression_type.value if chunk.compressed else "identity"
                ),
            }
        )

        return chunk

    def get_metrics(self) -> StreamingMetrics:
        """获取性能指标"""
        return self.metrics

    def reset_metrics(self) -> None:
        """重置性能指标"""
        self.metrics = StreamingMetrics(timestamp=datetime.utcnow())
        self.latency_history.clear()
        if hasattr(self, "_start_time"):
            delattr(self, "_start_time")

    def get_optimization_suggestions(self) -> list[str]:
        """获取优化建议"""
        suggestions = []

        # 基于延迟的建议
        if self.metrics.average_latency > self.config.max_latency:
            suggestions.append("考虑减少缓冲区大小或启用实时模式以降低延迟")

        # 基于压缩的建议
        if self.metrics.compression_ratio < 0.1:
            suggestions.append("考虑调整压缩阈值或压缩算法以提高压缩效率")

        # 基于吞吐量的建议
        if self.metrics.throughput > 0:
            target_throughput = 1024 * 1024  # 1MB/s
            if self.metrics.throughput < target_throughput * 0.5:
                suggestions.append("考虑增加块大小或优化数据序列化以提高吞吐量")

        # 基于错误率的建议
        if self.metrics.error_count > 0:
            error_rate = self.metrics.error_count / max(1, self.metrics.total_chunks)
            if error_rate > 0.01:  # 1%错误率
                suggestions.append("错误率较高，建议检查数据格式和网络连接")

        return suggestions

    async def create_test_stream(
        self, data_count: int = 100, data_size: int = 1024
    ) -> AsyncGenerator[dict[str, Any], None]:
        """创建测试数据流"""
        for i in range(data_count):
            test_data = {
                "id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "data": "x" * data_size,  # 填充数据
                "metadata": {"test": True, "sequence": i},
            }
            yield test_data
            await asyncio.sleep(0.01)  # 模拟数据生成间隔


# 全局流式优化器实例
_streaming_optimizer: StreamingOptimizer | None = None


def get_streaming_optimizer(
    config: StreamingConfig | None = None,
) -> StreamingOptimizer:
    """获取流式优化器实例"""
    global _streaming_optimizer

    if _streaming_optimizer is None or config is not None:
        _streaming_optimizer = StreamingOptimizer(config)

    return _streaming_optimizer


# 便捷函数
async def optimize_stream(
    data_generator: AsyncGenerator[Any, None],
    config: StreamingConfig | None = None,
) -> AsyncGenerator[StreamChunk, None]:
    """优化数据流的便捷函数"""
    optimizer = get_streaming_optimizer(config)
    async for chunk in optimizer.process_stream(data_generator):
        yield chunk


async def create_real_time_stream(
    data_generator: AsyncGenerator[Any, None],
) -> AsyncGenerator[StreamChunk, None]:
    """创建实时数据流"""
    config = StreamingConfig(mode=StreamingMode.REAL_TIME, buffer_size=1)
    async for chunk in optimize_stream(data_generator, config):
        yield chunk


async def create_buffered_stream(
    data_generator: AsyncGenerator[Any, None], buffer_size: int = 10
) -> AsyncGenerator[StreamChunk, None]:
    """创建缓冲数据流"""
    config = StreamingConfig(mode=StreamingMode.BUFFERED, buffer_size=buffer_size, max_latency=0.5)
    async for chunk in optimize_stream(data_generator, config):
        yield chunk
