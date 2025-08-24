"""成本优化服务 - AI服务成本控制和优化."""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.ai_models import CostOptimizationLog
from app.shared.models.enums import AIModelType

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """优化策略类型"""

    PEAK_AVOIDANCE = "peak_avoidance"  # 避峰策略
    REQUEST_BATCHING = "request_batching"  # 请求批处理
    INTELLIGENT_CACHING = "intelligent_caching"  # 智能缓存
    MODEL_SELECTION = "model_selection"  # 模型选择
    CONTENT_COMPRESSION = "content_compression"  # 内容压缩


class CostOptimizationService:
    """成本优化服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 成本阈值配置
        self.cost_thresholds = {
            "low": 10.0,
            "medium": 50.0,
            "high": 200.0,
            "critical": 500.0,
        }

        # 错峰时段配置
        self.off_peak_hours = list(range(0, 8)) + list(range(22, 24))
        self.peak_hours = list(range(9, 21))

    async def optimize_request(
        self,
        db: AsyncSession,
        prompt: str,
        model_type: AIModelType = AIModelType.DEEPSEEK_CHAT,
        priority: str = "normal",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """优化单个请求"""
        try:
            # 估算原始成本
            original_cost = self._estimate_cost(prompt, max_tokens, model_type)

            # 选择优化策略
            strategy = await self._select_optimization_strategy(prompt, model_type, priority)

            # 应用优化
            optimized_params = await self._apply_optimization(
                prompt, model_type, max_tokens, temperature, strategy
            )

            # 计算优化后成本
            optimized_cost = self._estimate_cost(
                optimized_params["prompt"],
                optimized_params["max_tokens"],
                optimized_params["model_type"],
            )

            # 记录优化日志
            await self._log_optimization(db, strategy, original_cost, optimized_cost)

            return {
                "optimized_params": optimized_params,
                "cost_savings": original_cost - optimized_cost,
                "savings_percentage": (
                    ((original_cost - optimized_cost) / original_cost * 100)
                    if original_cost > 0
                    else 0
                ),
                "strategy": strategy.value,
            }

        except Exception as e:
            self.logger.error(f"请求优化失败: {e}")
            # 返回原始参数
            return {
                "optimized_params": {
                    "prompt": prompt,
                    "model_type": model_type,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                "cost_savings": 0,
                "savings_percentage": 0,
                "strategy": "none",
            }

    def _estimate_cost(self, prompt: str, max_tokens: int, model_type: AIModelType) -> float:
        """估算请求成本"""
        # 简化的成本估算逻辑
        input_tokens = len(prompt.split()) * 1.3  # 粗略估算

        # DeepSeek定价 (示例价格)
        if model_type == AIModelType.DEEPSEEK_CHAT:
            input_price = 0.0014 / 1000  # $0.0014 per 1K tokens
            output_price = 0.0028 / 1000  # $0.0028 per 1K tokens
        else:
            input_price = 0.0014 / 1000
            output_price = 0.0028 / 1000

        return (input_tokens * input_price) + (max_tokens * output_price)

    async def _select_optimization_strategy(
        self, prompt: str, model_type: AIModelType, priority: str
    ) -> OptimizationStrategy:
        """选择优化策略"""
        current_hour = datetime.now().hour

        # 根据时间和优先级选择策略
        if priority == "low" and current_hour in self.peak_hours:
            return OptimizationStrategy.PEAK_AVOIDANCE
        elif len(prompt) > 1000:
            return OptimizationStrategy.CONTENT_COMPRESSION
        else:
            return OptimizationStrategy.INTELLIGENT_CACHING

    async def _apply_optimization(
        self,
        prompt: str,
        model_type: AIModelType,
        max_tokens: int,
        temperature: float,
        strategy: OptimizationStrategy,
    ) -> dict[str, Any]:
        """应用优化策略"""
        optimized_params = {
            "prompt": prompt,
            "model_type": model_type,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if strategy == OptimizationStrategy.CONTENT_COMPRESSION:
            # 压缩提示内容
            optimized_params["prompt"] = self._compress_prompt(prompt)
        elif strategy == OptimizationStrategy.MODEL_SELECTION:
            # 选择更经济的模型
            optimized_params["model_type"] = AIModelType.DEEPSEEK_CHAT
        elif strategy == OptimizationStrategy.PEAK_AVOIDANCE:
            # 降低优先级，延迟处理
            optimized_params["priority"] = "low"

        return optimized_params

    def _compress_prompt(self, prompt: str) -> str:
        """压缩提示内容"""
        # 简单的压缩逻辑：移除多余空格和换行
        compressed = " ".join(prompt.split())
        return compressed[: min(len(compressed), 2000)]  # 限制长度

    async def _log_optimization(
        self,
        db: AsyncSession,
        strategy: OptimizationStrategy,
        original_cost: float,
        optimized_cost: float,
    ) -> None:
        """记录优化日志"""
        try:
            log_entry = CostOptimizationLog(
                strategy=strategy.value,
                original_cost=original_cost,
                optimized_cost=optimized_cost,
                savings=original_cost - optimized_cost,
                savings_percentage=(
                    ((original_cost - optimized_cost) / original_cost * 100)
                    if original_cost > 0
                    else 0
                ),
            )

            db.add(log_entry)
            await db.commit()

        except Exception as e:
            self.logger.error(f"记录优化日志失败: {e}")
            await db.rollback()


def get_cost_optimization_service() -> CostOptimizationService:
    """获取成本优化服务实例"""
    return CostOptimizationService()
