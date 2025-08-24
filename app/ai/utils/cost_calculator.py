"""
AI成本计算器

提供精确的成本计算和预测功能：
- Token使用量计算
- 成本估算和预测
- 成本优化建议
- 预算管理工具
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.shared.models.enums import AIModelType


class CostModel(Enum):
    """成本模型"""

    PAY_PER_TOKEN = "pay_per_token"
    SUBSCRIPTION = "subscription"
    HYBRID = "hybrid"


class TokenType(Enum):
    """Token类型"""

    INPUT = "input"
    OUTPUT = "output"
    TOTAL = "total"


@dataclass
class ModelPricing:
    """模型定价"""

    model_type: AIModelType
    input_price_per_1k: float  # 每1000个输入token的价格
    output_price_per_1k: float  # 每1000个输出token的价格
    context_window: int  # 上下文窗口大小
    max_output_tokens: int  # 最大输出token数
    currency: str = "USD"


@dataclass
class UsageCost:
    """使用成本"""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model_type: AIModelType
    timestamp: datetime


@dataclass
class CostPrediction:
    """成本预测"""

    predicted_daily_cost: float
    predicted_monthly_cost: float
    confidence_level: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    factors: dict[str, float]


class CostCalculator:
    """成本计算器"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 模型定价配置
        self.model_pricing = {
            AIModelType.DEEPSEEK_CHAT: ModelPricing(
                model_type=AIModelType.DEEPSEEK_CHAT,
                input_price_per_1k=0.0014,  # $0.0014 per 1K input tokens
                output_price_per_1k=0.0028,  # $0.0028 per 1K output tokens
                context_window=32768,
                max_output_tokens=4096,
            ),
            AIModelType.DEEPSEEK_CODER: ModelPricing(
                model_type=AIModelType.DEEPSEEK_CODER,
                input_price_per_1k=0.0014,
                output_price_per_1k=0.0028,
                context_window=16384,
                max_output_tokens=4096,
            ),
            AIModelType.DEEPSEEK_LITE: ModelPricing(
                model_type=AIModelType.DEEPSEEK_LITE,
                input_price_per_1k=0.0007,  # 假设轻量版本价格更低
                output_price_per_1k=0.0014,
                context_window=8192,
                max_output_tokens=2048,
            ),
        }

        # 汇率配置（如果需要支持多币种）
        self.exchange_rates = {
            "USD": 1.0,
            "CNY": 7.2,  # 假设汇率
            "EUR": 0.85,
        }

        # 成本优化阈值
        self.optimization_thresholds = {
            "daily_limit": 100.0,  # 每日成本限制
            "hourly_limit": 10.0,  # 每小时成本限制
            "high_cost_per_request": 0.5,  # 单次请求高成本阈值
            "efficiency_threshold": 0.1,  # 效率阈值
        }

    def estimate_tokens(
        self, text: str, model_type: AIModelType = AIModelType.DEEPSEEK_CHAT
    ) -> int:
        """估算文本的token数量"""
        try:
            # 简单的token估算（实际应用中应该使用更精确的tokenizer）

            # 中文字符通常1个字符 = 1-2个token
            chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")

            # 英文单词通常1个单词 = 1-2个token
            english_words = len([word for word in text.split() if word.isascii()])

            # 其他字符
            other_chars = (
                len(text)
                - chinese_chars
                - sum(len(word) for word in text.split() if word.isascii())
            )

            # 估算token数
            estimated_tokens = int(
                chinese_chars * 1.5  # 中文字符
                + english_words * 1.3  # 英文单词
                + other_chars * 0.5  # 其他字符
            )

            return max(1, estimated_tokens)

        except Exception as e:
            self.logger.error(f"Token估算失败: {e}")
            # 回退到简单估算
            return max(1, len(text) // 4)

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_type: AIModelType = AIModelType.DEEPSEEK_CHAT,
    ) -> UsageCost:
        """计算使用成本"""
        try:
            if model_type not in self.model_pricing:
                self.logger.warning(f"未知模型类型: {model_type}, 使用默认定价")
                model_type = AIModelType.DEEPSEEK_CHAT

            pricing = self.model_pricing[model_type]

            # 计算成本
            input_cost = (input_tokens / 1000) * pricing.input_price_per_1k
            output_cost = (output_tokens / 1000) * pricing.output_price_per_1k
            total_cost = input_cost + output_cost
            total_tokens = input_tokens + output_tokens

            return UsageCost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                model_type=model_type,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            self.logger.error(f"成本计算失败: {e}")
            return UsageCost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                model_type=model_type,
                timestamp=datetime.utcnow(),
            )

    def estimate_request_cost(
        self,
        prompt: str,
        max_output_tokens: int,
        model_type: AIModelType = AIModelType.DEEPSEEK_CHAT,
    ) -> UsageCost:
        """估算请求成本"""
        try:
            input_tokens = self.estimate_tokens(prompt, model_type)

            # 估算实际输出token数（通常比max_tokens少）
            estimated_output_tokens = min(max_output_tokens, int(max_output_tokens * 0.8))

            return self.calculate_cost(input_tokens, estimated_output_tokens, model_type)

        except Exception as e:
            self.logger.error(f"请求成本估算失败: {e}")
            return self.calculate_cost(0, 0, model_type)

    def calculate_batch_cost(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """计算批量请求成本"""
        try:
            total_cost = 0.0
            total_tokens = 0
            model_costs = {}

            cost_details: list[dict[str, Any]] = []

            for request in requests:
                prompt = request.get("prompt", "")
                max_tokens = request.get("max_tokens", 1000)
                model_type = AIModelType(request.get("model_type", AIModelType.DEEPSEEK_CHAT.value))

                cost = self.estimate_request_cost(prompt, max_tokens, model_type)

                total_cost += cost.total_cost
                total_tokens += cost.total_tokens

                # 按模型统计
                model_name = model_type.value
                if model_name not in model_costs:
                    model_costs[model_name] = {
                        "count": 0,
                        "total_cost": 0.0,
                        "total_tokens": 0,
                    }

                model_costs[model_name]["count"] += 1
                model_costs[model_name]["total_cost"] += cost.total_cost
                model_costs[model_name]["total_tokens"] += cost.total_tokens

                cost_details.append(
                    {
                        "request_index": len(cost_details),
                        "model_type": model_name,
                        "input_tokens": cost.input_tokens,
                        "output_tokens": cost.output_tokens,
                        "total_cost": cost.total_cost,
                    }
                )

            return {
                "total_requests": len(requests),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "average_cost_per_request": (total_cost / len(requests) if requests else 0),
                "model_breakdown": model_costs,
                "cost_details": cost_details,
            }

        except Exception as e:
            self.logger.error(f"批量成本计算失败: {e}")
            return {}

    def predict_daily_cost(
        self, historical_usage: list[UsageCost], days_ahead: int = 1
    ) -> CostPrediction:
        """预测未来成本"""
        try:
            if not historical_usage:
                return CostPrediction(
                    predicted_daily_cost=0.0,
                    predicted_monthly_cost=0.0,
                    confidence_level=0.0,
                    trend_direction="stable",
                    factors={},
                )

            # 按日期分组
            daily_costs = {}
            for usage in historical_usage:
                date = usage.timestamp.date()
                if date not in daily_costs:
                    daily_costs[date] = 0.0
                daily_costs[date] += usage.total_cost

            if not daily_costs:
                return CostPrediction(
                    predicted_daily_cost=0.0,
                    predicted_monthly_cost=0.0,
                    confidence_level=0.0,
                    trend_direction="stable",
                    factors={},
                )

            # 计算趋势
            sorted_dates = sorted(daily_costs.keys())
            costs = [daily_costs[date] for date in sorted_dates]

            # 简单线性回归预测
            n = len(costs)
            if n < 2:
                predicted_daily = costs[0] if costs else 0.0
                trend = "stable"
            else:
                # 计算趋势斜率
                x_values = list(range(n))
                x_mean = sum(x_values) / n
                y_mean = sum(costs) / n

                numerator = sum(
                    (x - x_mean) * (y - y_mean) for x, y in zip(x_values, costs, strict=False)
                )
                denominator = sum((x - x_mean) ** 2 for x in x_values)

                if denominator == 0:
                    slope = 0
                else:
                    slope = numerator / denominator

                intercept = y_mean - slope * x_mean

                # 预测未来成本
                predicted_daily = slope * (n + days_ahead - 1) + intercept
                predicted_daily = max(0, predicted_daily)

                # 判断趋势方向
                if slope > 0.1:
                    trend = "increasing"
                elif slope < -0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"

            # 计算置信度
            if n >= 7:
                # 计算预测误差
                recent_costs = costs[-7:]
                avg_recent = sum(recent_costs) / len(recent_costs)
                variance = sum((cost - avg_recent) ** 2 for cost in recent_costs) / len(
                    recent_costs
                )
                confidence = max(
                    0.0,
                    min(1.0, 1.0 - (variance / avg_recent) if avg_recent > 0 else 0.0),
                )
            else:
                confidence = 0.5  # 数据不足时的默认置信度

            # 计算月成本
            predicted_monthly = predicted_daily * 30

            # 分析影响因子
            factors: dict[str, float] = self._analyze_cost_factors(historical_usage)

            return CostPrediction(
                predicted_daily_cost=predicted_daily,
                predicted_monthly_cost=predicted_monthly,
                confidence_level=confidence,
                trend_direction=trend,
                factors=factors,
            )

        except Exception as e:
            self.logger.error(f"成本预测失败: {e}")
            return CostPrediction(
                predicted_daily_cost=0.0,
                predicted_monthly_cost=0.0,
                confidence_level=0.0,
                trend_direction="stable",
                factors={},
            )

    def _analyze_cost_factors(self, historical_usage: list[UsageCost]) -> dict[str, float]:
        """分析成本影响因子"""
        try:
            factors: dict[str, float] = {}

            if not historical_usage:
                return factors

            # 模型使用分布
            model_usage = {}
            total_cost = sum(usage.total_cost for usage in historical_usage)

            for usage in historical_usage:
                model_name = usage.model_type.value
                if model_name not in model_usage:
                    model_usage[model_name] = 0.0
                model_usage[model_name] += usage.total_cost

            # 计算各模型成本占比
            for model, cost in model_usage.items():
                factors[f"model_{model}_ratio"] = cost / total_cost if total_cost > 0 else 0

            # 时间分布分析
            hourly_costs = {}
            for usage in historical_usage:
                hour = usage.timestamp.hour
                if hour not in hourly_costs:
                    hourly_costs[hour] = 0.0
                hourly_costs[hour] += usage.total_cost

            # 峰值时段成本占比
            peak_hours = list(range(9, 21))
            peak_cost = sum(hourly_costs.get(hour, 0) for hour in peak_hours)
            factors["peak_hours_ratio"] = peak_cost / total_cost if total_cost > 0 else 0

            # 平均请求成本
            if historical_usage:
                factors["avg_request_cost"] = total_cost / len(historical_usage)

            # Token效率
            total_tokens = sum(usage.total_tokens for usage in historical_usage)
            if total_tokens > 0:
                factors["cost_per_token"] = total_cost / total_tokens

            return factors

        except Exception as e:
            self.logger.error(f"成本因子分析失败: {e}")
            return {}

    def get_cost_optimization_suggestions(
        self, current_usage: list[UsageCost], predicted_cost: CostPrediction
    ) -> list[str]:
        """获取成本优化建议"""
        try:
            suggestions = []

            # 检查预测成本是否超过阈值
            if predicted_cost.predicted_daily_cost > self.optimization_thresholds["daily_limit"]:
                suggestions.append(
                    f"预测日成本 ${predicted_cost.predicted_daily_cost:.2f} "
                    f"超过限制 ${self.optimization_thresholds['daily_limit']:.2f}，"
                    "建议启用成本控制措施"
                )

            # 分析趋势
            if predicted_cost.trend_direction == "increasing":
                suggestions.append("成本呈上升趋势，建议优化请求策略或使用更经济的模型")

            # 分析模型使用
            if "model_DEEPSEEK_CHAT_ratio" in predicted_cost.factors:
                chat_ratio = predicted_cost.factors["model_DEEPSEEK_CHAT_ratio"]
                if chat_ratio > 0.8:
                    suggestions.append("主要使用高成本模型，考虑在适当场景使用轻量版本")

            # 分析时间分布
            if "peak_hours_ratio" in predicted_cost.factors:
                peak_ratio = predicted_cost.factors["peak_hours_ratio"]
                if peak_ratio > 0.7:
                    suggestions.append("大部分请求在高峰时段，建议启用错峰调度")

            # 分析请求效率
            if "avg_request_cost" in predicted_cost.factors:
                avg_cost = predicted_cost.factors["avg_request_cost"]
                if avg_cost > self.optimization_thresholds["high_cost_per_request"]:
                    suggestions.append("单次请求成本较高，建议优化prompt长度或使用缓存")

            # 分析token效率
            if "cost_per_token" in predicted_cost.factors:
                cost_per_token = predicted_cost.factors["cost_per_token"]
                if cost_per_token > self.optimization_thresholds["efficiency_threshold"]:
                    suggestions.append("Token使用效率较低，建议压缩输入内容或优化输出长度")

            # 通用建议
            if not suggestions:
                suggestions.append("成本控制良好，建议继续监控使用情况")

            return suggestions

        except Exception as e:
            self.logger.error(f"生成优化建议失败: {e}")
            return ["无法生成优化建议，请检查系统状态"]

    def calculate_savings_potential(
        self, current_usage: list[UsageCost], optimization_strategies: list[str]
    ) -> dict[str, float]:
        """计算节省潜力"""
        try:
            if not current_usage:
                return {}

            total_current_cost = sum(usage.total_cost for usage in current_usage)
            savings_potential = {}

            # 模型优化节省
            high_cost_model_usage = sum(
                usage.total_cost
                for usage in current_usage
                if usage.model_type == AIModelType.DEEPSEEK_CHAT
            )

            if "model_optimization" in optimization_strategies:
                # 假设30%的高成本模型请求可以用轻量模型替代，节省50%成本
                potential_savings = high_cost_model_usage * 0.3 * 0.5
                savings_potential["model_optimization"] = potential_savings

            # 错峰调度节省
            if "peak_avoidance" in optimization_strategies:
                # 假设错峰调度可以节省20%成本
                potential_savings = total_current_cost * 0.2
                savings_potential["peak_avoidance"] = potential_savings

            # 缓存优化节省
            if "caching" in optimization_strategies:
                # 假设缓存可以减少30%的重复请求
                potential_savings = total_current_cost * 0.3
                savings_potential["caching"] = potential_savings

            # 内容压缩节省
            if "content_compression" in optimization_strategies:
                # 假设内容压缩可以减少15%的token使用
                potential_savings = total_current_cost * 0.15
                savings_potential["content_compression"] = potential_savings

            # 计算总节省潜力（避免重复计算）
            total_savings = min(sum(savings_potential.values()), total_current_cost * 0.6)
            savings_potential["total_potential"] = total_savings

            return savings_potential

        except Exception as e:
            self.logger.error(f"计算节省潜力失败: {e}")
            return {}

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """货币转换"""
        try:
            if from_currency == to_currency:
                return amount

            if from_currency not in self.exchange_rates or to_currency not in self.exchange_rates:
                self.logger.warning(f"不支持的货币: {from_currency} -> {to_currency}")
                return amount

            # 转换为USD再转换为目标货币
            usd_amount = amount / self.exchange_rates[from_currency]
            target_amount = usd_amount * self.exchange_rates[to_currency]

            return target_amount

        except Exception as e:
            self.logger.error(f"货币转换失败: {e}")
            return amount

    def get_cost_breakdown_report(
        self, usage_data: list[UsageCost], period_days: int = 30
    ) -> dict[str, Any]:
        """生成成本分解报告"""
        try:
            if not usage_data:
                return {}

            total_cost = sum(usage.total_cost for usage in usage_data)
            total_tokens = sum(usage.total_tokens for usage in usage_data)

            # 按模型分组
            model_breakdown = {}
            for usage in usage_data:
                model_name = usage.model_type.value
                if model_name not in model_breakdown:
                    model_breakdown[model_name] = {
                        "count": 0,
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "avg_cost_per_request": 0.0,
                    }

                model_breakdown[model_name]["count"] += 1
                model_breakdown[model_name]["total_cost"] += usage.total_cost
                model_breakdown[model_name]["total_tokens"] += usage.total_tokens

            # 计算平均值
            for model_data in model_breakdown.values():
                if model_data["count"] > 0:
                    model_data["avg_cost_per_request"] = (
                        model_data["total_cost"] / model_data["count"]
                    )

            # 按日期分组
            daily_costs = {}
            for usage in usage_data:
                date_str = usage.timestamp.date().isoformat()
                if date_str not in daily_costs:
                    daily_costs[date_str] = 0.0
                daily_costs[date_str] += usage.total_cost

            # 按小时分组
            hourly_costs = {}
            for usage in usage_data:
                hour = usage.timestamp.hour
                if hour not in hourly_costs:
                    hourly_costs[hour] = 0.0
                hourly_costs[hour] += usage.total_cost

            return {
                "period_days": period_days,
                "total_requests": len(usage_data),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "average_cost_per_request": total_cost / len(usage_data),
                "average_cost_per_token": (total_cost / total_tokens if total_tokens > 0 else 0),
                "model_breakdown": model_breakdown,
                "daily_costs": daily_costs,
                "hourly_distribution": hourly_costs,
                "peak_hour_cost": max(hourly_costs.values()) if hourly_costs else 0,
                "off_peak_savings_potential": self._calculate_off_peak_savings(hourly_costs),
            }

        except Exception as e:
            self.logger.error(f"生成成本报告失败: {e}")
            return {}

    def _calculate_off_peak_savings(self, hourly_costs: dict[int, float]) -> float:
        """计算错峰节省潜力"""
        try:
            peak_hours = list(range(9, 21))

            peak_cost = sum(hourly_costs.get(hour, 0) for hour in peak_hours)
            # 假设错峰时段有20%的成本优势
            potential_savings = peak_cost * 0.2
            return potential_savings

        except Exception:
            return 0.0


# 全局成本计算器实例
_cost_calculator: CostCalculator | None = None


def get_cost_calculator() -> CostCalculator:
    """获取成本计算器实例"""
    global _cost_calculator

    if _cost_calculator is None:
        _cost_calculator = CostCalculator()

    return _cost_calculator
