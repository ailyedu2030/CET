# DeepSeek优化模块代码生成示例

## 📋 文档概述

本文档提供使用AI生成DeepSeek优化模块核心代码的具体示例，展示如何充分利用AI的代码生成能力来快速构建高质量的模块代码。

## 🤖 AI代码生成示例

### 1. 核心数据类生成

**AI提示词**：

```
请生成DeepSeek优化模块的核心数据类，要求：
1. 使用@dataclass装饰器和类型提示
2. 包含验证方法和序列化支持
3. 支持默认值和可选字段
4. 添加详细的文档字符串
5. 包含__post_init__方法进行验证

需要生成的类：
- OptimizationRequest（优化请求）
- OptimizationResult（优化结果）
- ModelConfig（模型配置）
- CacheConfig（缓存配置）
```

**AI生成的代码**：

```python
# deepseek_optimizer/core/models.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json
import hashlib
from datetime import datetime

class TaskType(Enum):
    """任务类型枚举"""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    REASONING = "reasoning"
    EXTRACTION = "extraction"
    MAPPING = "mapping"
    ALLOCATION = "allocation"

class ComplexityLevel(Enum):
    """复杂度级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ModelType(Enum):
    """模型类型枚举"""
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_REASONER = "deepseek-reasoner"

@dataclass
class OptimizationRequest:
    """
    优化请求数据类

    包含执行DeepSeek优化所需的所有参数和配置信息
    """
    content: str
    task_type: TaskType
    complexity: ComplexityLevel
    context: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """初始化后验证和设置默认值"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

        if self.request_id is None:
            self.request_id = self._generate_request_id()

        if self.context is None:
            self.context = {}

        if self.preferences is None:
            self.preferences = {}

        self._validate()

    def _generate_request_id(self) -> str:
        """生成唯一的请求ID"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        timestamp_str = self.timestamp.strftime("%Y%m%d%H%M%S") if self.timestamp else ""
        return f"req_{timestamp_str}_{content_hash}"

    def _validate(self):
        """验证请求数据的有效性"""
        if not self.content or not self.content.strip():
            raise ValueError("Content cannot be empty")

        if len(self.content) > 200000:  # 200K字符限制
            raise ValueError("Content exceeds maximum length of 200K characters")

        if self.user_id and len(self.user_id) > 100:
            raise ValueError("User ID exceeds maximum length")

        if self.tenant_id and len(self.tenant_id) > 100:
            raise ValueError("Tenant ID exceeds maximum length")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "task_type": self.task_type.value,
            "complexity": self.complexity.value,
            "context": self.context,
            "preferences": self.preferences,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationRequest':
        """从字典创建实例"""
        return cls(
            content=data["content"],
            task_type=TaskType(data["task_type"]),
            complexity=ComplexityLevel(data["complexity"]),
            context=data.get("context"),
            preferences=data.get("preferences"),
            user_id=data.get("user_id"),
            tenant_id=data.get("tenant_id"),
            request_id=data.get("request_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )

@dataclass
class OptimizationResult:
    """
    优化结果数据类

    包含DeepSeek优化处理的完整结果信息
    """
    success: bool
    content: str
    request_id: str
    reasoning_process: Optional[str] = None
    model_used: str = ""
    processing_time: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    quality_score: float = 0.0
    from_cache: bool = False
    cache_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """初始化后设置默认值"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

        if self.metadata is None:
            self.metadata = {}

        self._validate()

    def _validate(self):
        """验证结果数据的有效性"""
        if not self.request_id:
            raise ValueError("Request ID is required")

        if self.success and not self.content:
            raise ValueError("Content is required for successful results")

        if not self.success and not self.error_message:
            raise ValueError("Error message is required for failed results")

        if self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")

        if self.tokens_used < 0:
            raise ValueError("Tokens used cannot be negative")

        if self.cost < 0:
            raise ValueError("Cost cannot be negative")

        if not 0 <= self.quality_score <= 1:
            raise ValueError("Quality score must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "content": self.content,
            "request_id": self.request_id,
            "reasoning_process": self.reasoning_process,
            "model_used": self.model_used,
            "processing_time": self.processing_time,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "quality_score": self.quality_score,
            "from_cache": self.from_cache,
            "cache_key": self.cache_key,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationResult':
        """从字典创建实例"""
        return cls(
            success=data["success"],
            content=data["content"],
            request_id=data["request_id"],
            reasoning_process=data.get("reasoning_process"),
            model_used=data.get("model_used", ""),
            processing_time=data.get("processing_time", 0.0),
            tokens_used=data.get("tokens_used", 0),
            cost=data.get("cost", 0.0),
            quality_score=data.get("quality_score", 0.0),
            from_cache=data.get("from_cache", False),
            cache_key=data.get("cache_key"),
            metadata=data.get("metadata"),
            error_message=data.get("error_message"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )

@dataclass
class ModelConfig:
    """
    模型配置数据类

    定义DeepSeek模型的参数配置
    """
    name: str
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 0.9
    use_reasoning: bool = False
    timeout: int = 30
    retry_count: int = 3

    def __post_init__(self):
        """初始化后验证配置"""
        self._validate()

    def _validate(self):
        """验证配置参数的有效性"""
        if not self.name:
            raise ValueError("Model name is required")

        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")

        if not 1 <= self.max_tokens <= 8000:
            raise ValueError("Max tokens must be between 1 and 8000")

        if not 0 <= self.top_p <= 1:
            raise ValueError("Top_p must be between 0 and 1")

        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "use_reasoning": self.use_reasoning,
            "timeout": self.timeout,
            "retry_count": self.retry_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建实例"""
        return cls(**data)

@dataclass
class CacheConfig:
    """
    缓存配置数据类

    定义缓存系统的配置参数
    """
    backend: str = "memory"
    default_ttl: int = 3600
    max_size: int = 1000
    compression: bool = True
    redis_url: Optional[str] = None
    redis_db: int = 0
    key_prefix: str = "deepseek_optimizer"

    def __post_init__(self):
        """初始化后验证配置"""
        self._validate()

    def _validate(self):
        """验证缓存配置的有效性"""
        valid_backends = ["memory", "redis", "file"]
        if self.backend not in valid_backends:
            raise ValueError(f"Backend must be one of {valid_backends}")

        if self.default_ttl <= 0:
            raise ValueError("Default TTL must be positive")

        if self.max_size <= 0:
            raise ValueError("Max size must be positive")

        if self.backend == "redis" and not self.redis_url:
            raise ValueError("Redis URL is required for redis backend")

        if self.redis_db < 0:
            raise ValueError("Redis DB must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "backend": self.backend,
            "default_ttl": self.default_ttl,
            "max_size": self.max_size,
            "compression": self.compression,
            "redis_url": self.redis_url,
            "redis_db": self.redis_db,
            "key_prefix": self.key_prefix
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheConfig':
        """从字典创建实例"""
        return cls(**data)
```

### 2. 智能模型选择器生成

**AI提示词**：

```
请生成智能模型选择器类，要求：
1. 实现基于任务类型和复杂度的智能选择逻辑
2. 支持动态参数调整
3. 包含性能统计和学习能力
4. 提供配置验证和错误处理
5. 支持自定义选择策略

功能需求：
- 根据TaskType和ComplexityLevel选择最优模型
- 基于历史性能数据优化选择
- 支持A/B测试和策略切换
- 提供选择理由和置信度
```

**AI生成的代码**：

```python
# deepseek_optimizer/core/model_selector.py

from typing import Dict, Any, Optional, Tuple, List
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .models import TaskType, ComplexityLevel, ModelConfig, ModelType
from ..utils.exceptions import ModelSelectionError, ConfigurationError

logger = logging.getLogger(__name__)

class IntelligentModelSelector:
    """
    智能模型选择器

    基于任务特征、历史性能和配置策略智能选择最优的DeepSeek模型
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型选择器

        Args:
            config: 选择器配置字典
        """
        self.config = config
        self.performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.selection_matrix = self._build_selection_matrix()
        self.learning_enabled = config.get("enable_learning", True)
        self.min_samples_for_learning = config.get("min_samples_for_learning", 10)

        logger.info("Intelligent model selector initialized")

    def _build_selection_matrix(self) -> Dict[Tuple[TaskType, ComplexityLevel], Dict[str, Any]]:
        """构建基础选择矩阵"""
        return {
            # 分析任务
            (TaskType.ANALYSIS, ComplexityLevel.LOW): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.3,
                "max_tokens": 3000,
                "top_p": 0.8,
                "use_reasoning": False,
                "confidence": 0.9
            },
            (TaskType.ANALYSIS, ComplexityLevel.MEDIUM): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.5,
                "max_tokens": 4000,
                "top_p": 0.85,
                "use_reasoning": False,
                "confidence": 0.8
            },
            (TaskType.ANALYSIS, ComplexityLevel.HIGH): {
                "model": ModelType.DEEPSEEK_REASONER,
                "temperature": 0.6,
                "max_tokens": 4000,
                "top_p": 0.9,
                "use_reasoning": True,
                "confidence": 0.95
            },

            # 推理任务
            (TaskType.REASONING, ComplexityLevel.LOW): {
                "model": ModelType.DEEPSEEK_REASONER,
                "temperature": 0.5,
                "max_tokens": 3000,
                "top_p": 0.85,
                "use_reasoning": True,
                "confidence": 0.9
            },
            (TaskType.REASONING, ComplexityLevel.MEDIUM): {
                "model": ModelType.DEEPSEEK_REASONER,
                "temperature": 0.6,
                "max_tokens": 4000,
                "top_p": 0.9,
                "use_reasoning": True,
                "confidence": 0.95
            },
            (TaskType.REASONING, ComplexityLevel.HIGH): {
                "model": ModelType.DEEPSEEK_REASONER,
                "temperature": 0.6,
                "max_tokens": 5000,
                "top_p": 0.9,
                "use_reasoning": True,
                "confidence": 0.98
            },

            # 生成任务
            (TaskType.GENERATION, ComplexityLevel.LOW): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_p": 0.9,
                "use_reasoning": False,
                "confidence": 0.85
            },
            (TaskType.GENERATION, ComplexityLevel.MEDIUM): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.7,
                "max_tokens": 6000,
                "top_p": 0.95,
                "use_reasoning": False,
                "confidence": 0.8
            },
            (TaskType.GENERATION, ComplexityLevel.HIGH): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.8,
                "max_tokens": 8000,
                "top_p": 0.95,
                "use_reasoning": False,
                "confidence": 0.75
            },

            # 提取任务
            (TaskType.EXTRACTION, ComplexityLevel.LOW): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.2,
                "max_tokens": 2000,
                "top_p": 0.8,
                "use_reasoning": False,
                "confidence": 0.9
            },
            (TaskType.EXTRACTION, ComplexityLevel.MEDIUM): {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.3,
                "max_tokens": 3000,
                "top_p": 0.8,
                "use_reasoning": False,
                "confidence": 0.85
            },
            (TaskType.EXTRACTION, ComplexityLevel.HIGH): {
                "model": ModelType.DEEPSEEK_REASONER,
                "temperature": 0.4,
                "max_tokens": 4000,
                "top_p": 0.85,
                "use_reasoning": True,
                "confidence": 0.9
            }
        }

    def select_model(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        content_length: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """
        选择最优模型配置

        Args:
            task_type: 任务类型
            complexity: 复杂度级别
            content_length: 内容长度
            context: 额外上下文信息

        Returns:
            Tuple[ModelConfig, Dict[str, Any]]: 模型配置和选择元数据
        """
        try:
            # 获取基础配置
            base_config = self._get_base_config(task_type, complexity)

            # 基于内容长度调整
            adjusted_config = self._adjust_for_content_length(base_config, content_length)

            # 基于历史性能优化
            if self.learning_enabled:
                optimized_config = self._optimize_with_history(
                    adjusted_config, task_type, complexity
                )
            else:
                optimized_config = adjusted_config

            # 创建模型配置
            model_config = ModelConfig(
                name=optimized_config["model"].value,
                temperature=optimized_config["temperature"],
                max_tokens=optimized_config["max_tokens"],
                top_p=optimized_config["top_p"],
                use_reasoning=optimized_config["use_reasoning"]
            )

            # 选择元数据
            metadata = {
                "selection_reason": self._generate_selection_reason(
                    task_type, complexity, content_length
                ),
                "confidence": optimized_config["confidence"],
                "base_strategy": "matrix_lookup",
                "adjustments_applied": self._get_applied_adjustments(
                    base_config, optimized_config
                ),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(
                f"Selected model {model_config.name} for {task_type.value} "
                f"task with {complexity.value} complexity"
            )

            return model_config, metadata

        except Exception as e:
            logger.error(f"Model selection failed: {e}")
            raise ModelSelectionError(f"Failed to select model: {e}")

    def _get_base_config(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel
    ) -> Dict[str, Any]:
        """获取基础配置"""
        key = (task_type, complexity)
        if key not in self.selection_matrix:
            # 回退到默认配置
            logger.warning(f"No specific config for {key}, using default")
            return {
                "model": ModelType.DEEPSEEK_CHAT,
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_p": 0.9,
                "use_reasoning": False,
                "confidence": 0.5
            }
        return self.selection_matrix[key].copy()

    def _adjust_for_content_length(
        self,
        config: Dict[str, Any],
        content_length: int
    ) -> Dict[str, Any]:
        """基于内容长度调整配置"""
        adjusted = config.copy()

        if content_length > 50000:  # 长文档
            # 降低温度提高稳定性
            adjusted["temperature"] = max(0.2, adjusted["temperature"] - 0.1)
            # 增加输出长度
            adjusted["max_tokens"] = min(8000, adjusted["max_tokens"] + 1000)
            # 调整置信度
            adjusted["confidence"] *= 0.9

        elif content_length < 1000:  # 短文档
            # 可以稍微提高温度
            adjusted["temperature"] = min(1.0, adjusted["temperature"] + 0.1)
            # 减少输出长度
            adjusted["max_tokens"] = max(1000, adjusted["max_tokens"] - 500)

        return adjusted

    def _optimize_with_history(
        self,
        config: Dict[str, Any],
        task_type: TaskType,
        complexity: ComplexityLevel
    ) -> Dict[str, Any]:
        """基于历史性能优化配置"""
        history_key = f"{task_type.value}_{complexity.value}"
        history = self.performance_history.get(history_key, [])

        if len(history) < self.min_samples_for_learning:
            return config

        # 分析历史性能
        recent_history = history[-20:]  # 最近20次

        # 计算平均质量分数
        quality_scores = [h["quality_score"] for h in recent_history if h.get("quality_score")]
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)

            # 如果质量分数低于阈值，调整参数
            if avg_quality < 0.8:
                optimized = config.copy()

                # 如果当前使用chat模型且质量不佳，考虑切换到reasoner
                if config["model"] == ModelType.DEEPSEEK_CHAT:
                    optimized["model"] = ModelType.DEEPSEEK_REASONER
                    optimized["use_reasoning"] = True
                    optimized["temperature"] = max(0.3, optimized["temperature"] - 0.1)

                # 降低温度提高稳定性
                optimized["temperature"] = max(0.2, optimized["temperature"] - 0.05)

                logger.info(f"Optimized config based on history for {history_key}")
                return optimized

        return config

    def record_performance(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        model_used: str,
        quality_score: float,
        processing_time: float,
        success: bool
    ):
        """记录性能数据用于学习"""
        if not self.learning_enabled:
            return

        history_key = f"{task_type.value}_{complexity.value}"

        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "model_used": model_used,
            "quality_score": quality_score,
            "processing_time": processing_time,
            "success": success
        }

        self.performance_history[history_key].append(performance_record)

        # 保持历史记录在合理范围内
        max_history = self.config.get("max_history_records", 100)
        if len(self.performance_history[history_key]) > max_history:
            self.performance_history[history_key] = \
                self.performance_history[history_key][-max_history:]

        logger.debug(f"Recorded performance for {history_key}")

    def _generate_selection_reason(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        content_length: int
    ) -> str:
        """生成选择理由"""
        reasons = []

        if task_type == TaskType.REASONING:
            reasons.append("推理任务需要使用推理模型")
        elif complexity == ComplexityLevel.HIGH:
            reasons.append("高复杂度任务需要更强的模型能力")

        if content_length > 50000:
            reasons.append("长文档需要调整参数以提高稳定性")
        elif content_length < 1000:
            reasons.append("短文档可以使用更灵活的参数")

        if not reasons:
            reasons.append("基于任务类型和复杂度的标准选择")

        return "; ".join(reasons)

    def _get_applied_adjustments(
        self,
        base_config: Dict[str, Any],
        final_config: Dict[str, Any]
    ) -> List[str]:
        """获取应用的调整列表"""
        adjustments = []

        if base_config["temperature"] != final_config["temperature"]:
            adjustments.append(
                f"temperature: {base_config['temperature']} -> {final_config['temperature']}"
            )

        if base_config["max_tokens"] != final_config["max_tokens"]:
            adjustments.append(
                f"max_tokens: {base_config['max_tokens']} -> {final_config['max_tokens']}"
            )

        if base_config["model"] != final_config["model"]:
            adjustments.append(
                f"model: {base_config['model'].value} -> {final_config['model'].value}"
            )

        return adjustments

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = {}

        for key, history in self.performance_history.items():
            if not history:
                continue

            recent_history = history[-20:]

            quality_scores = [h["quality_score"] for h in recent_history if h.get("quality_score")]
            processing_times = [h["processing_time"] for h in recent_history]
            success_rate = sum(1 for h in recent_history if h["success"]) / len(recent_history)

            stats[key] = {
                "sample_count": len(recent_history),
                "avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                "avg_processing_time": statistics.mean(processing_times) if processing_times else 0,
                "success_rate": success_rate,
                "last_updated": recent_history[-1]["timestamp"] if recent_history else None
            }

        return stats
```

## 🔗 相关文档

- [DeepSeek优化模块开发计划](./deepseek-optimizer-module-development-plan.md)
- [DeepSeek优化策略](./deepseek-optimization-strategy.md)
- [实现代码示例](./deepseek-implementation-examples.md)

---

**文档版本**: v1.0  
**创建日期**: 2025-01-22  
**最后更新**: 2025-01-22
