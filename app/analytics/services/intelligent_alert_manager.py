"""智能告警管理系统 - 智能告警阈值调整、告警聚合和降噪."""

import logging
import statistics
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class IntelligentAlertManager:
    """智能告警管理器."""

    def __init__(self, db: AsyncSession, cache_service: CacheService | None = None) -> None:
        self.db = db
        self.cache_service = cache_service

        # 智能阈值配置
        self.adaptive_thresholds = {
            "cpu_usage": {
                "base_threshold": 80.0,
                "adaptive_range": (70.0, 90.0),
                "learning_window_hours": 24,
            },
            "memory_usage": {
                "base_threshold": 85.0,
                "adaptive_range": (75.0, 95.0),
                "learning_window_hours": 24,
            },
            "response_time": {
                "base_threshold": 1000.0,
                "adaptive_range": (500.0, 2000.0),
                "learning_window_hours": 12,
            },
            "error_rate": {
                "base_threshold": 1.0,
                "adaptive_range": (0.5, 5.0),
                "learning_window_hours": 6,
            },
        }

        # 告警聚合配置
        self.aggregation_rules = {
            "time_window_minutes": 5,
            "max_alerts_per_window": 10,
            "similarity_threshold": 0.8,
        }

        # 告警历史和状态
        self.alert_history: dict[str, list[dict[str, Any]]] = {}
        self.active_alerts: dict[str, dict[str, Any]] = {}
        self.suppressed_alerts: dict[str, dict[str, Any]] = {}

    async def intelligent_alert_processing(
        self, raw_alerts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """智能告警处理."""
        try:
            # 1. 智能阈值调整
            adjusted_alerts = await self._apply_adaptive_thresholds(raw_alerts)

            # 2. 告警去重和聚合
            aggregated_alerts = await self._aggregate_similar_alerts(adjusted_alerts)

            # 3. 告警降噪
            filtered_alerts = await self._apply_noise_reduction(aggregated_alerts)

            # 4. 告警优先级评估
            prioritized_alerts = await self._evaluate_alert_priorities(filtered_alerts)

            # 5. 预测性告警
            predictive_alerts = await self._generate_predictive_alerts()

            # 6. 告警路由和通知
            notification_plan = await self._plan_alert_notifications(prioritized_alerts)

            # 7. 更新告警状态
            await self._update_alert_states(prioritized_alerts)

            return {
                "processing_metadata": {
                    "processing_timestamp": datetime.now().isoformat(),
                    "raw_alerts_count": len(raw_alerts),
                    "processed_alerts_count": len(prioritized_alerts),
                    "suppressed_alerts_count": len(self.suppressed_alerts),
                },
                "raw_alerts": raw_alerts,
                "processed_alerts": prioritized_alerts,
                "predictive_alerts": predictive_alerts,
                "notification_plan": notification_plan,
                "alert_statistics": await self._generate_alert_statistics(),
                "threshold_adjustments": await self._get_threshold_adjustments(),
            }

        except Exception as e:
            logger.error(f"智能告警处理失败: {str(e)}")
            raise

    async def _apply_adaptive_thresholds(
        self, raw_alerts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """应用自适应阈值."""
        try:
            adjusted_alerts = []

            for alert in raw_alerts:
                alert_type = alert.get("type", "")
                current_value = alert.get("current_value", 0)

                # 获取自适应阈值
                adaptive_threshold = await self._calculate_adaptive_threshold(alert_type)

                # 检查是否应该触发告警
                if self._should_trigger_alert(alert_type, current_value, adaptive_threshold):
                    # 更新告警阈值
                    alert["adaptive_threshold"] = adaptive_threshold
                    alert["threshold_adjustment"] = adaptive_threshold - alert.get("threshold", 0)
                    alert["confidence_score"] = await self._calculate_alert_confidence(alert)

                    adjusted_alerts.append(alert)
                else:
                    # 记录被抑制的告警
                    self.suppressed_alerts[f"{alert_type}_{datetime.now().timestamp()}"] = {
                        "alert": alert,
                        "reason": "adaptive_threshold_not_met",
                        "adaptive_threshold": adaptive_threshold,
                        "suppressed_at": datetime.now().isoformat(),
                    }

            return adjusted_alerts

        except Exception as e:
            logger.error(f"应用自适应阈值失败: {str(e)}")
            return raw_alerts

    async def _calculate_adaptive_threshold(self, alert_type: str) -> float:
        """计算自适应阈值."""
        try:
            threshold_config = self.adaptive_thresholds.get(alert_type)
            if not threshold_config:
                return 0.0

            # 获取历史数据
            learning_window_raw = threshold_config.get("learning_window_hours", 24)
            try:
                if isinstance(learning_window_raw, int | float | str):
                    learning_window_hours = int(learning_window_raw)
                else:
                    learning_window_hours = 24
            except (ValueError, TypeError):
                learning_window_hours = 24
            historical_data = await self._get_historical_metrics(alert_type, learning_window_hours)

            if len(historical_data) < 10:  # 数据不足，使用基础阈值
                base_threshold = threshold_config.get("base_threshold", 0.0)
                try:
                    if isinstance(base_threshold, int | float | str) and base_threshold is not None:
                        return float(base_threshold)
                    else:
                        return 0.0
                except (ValueError, TypeError):
                    return 0.0

            # 计算统计指标
            mean_value = statistics.mean(historical_data)
            std_dev = statistics.stdev(historical_data) if len(historical_data) > 1 else 0
            p95_value = (
                statistics.quantiles(historical_data, n=20)[18]
                if len(historical_data) > 20
                else max(historical_data)
            )

            # 基于统计分析调整阈值
            adaptive_range_raw = threshold_config.get("adaptive_range", (0.0, 100.0))
            try:
                adaptive_range = (
                    (float(adaptive_range_raw[0]), float(adaptive_range_raw[1]))
                    if isinstance(adaptive_range_raw, list | tuple) and len(adaptive_range_raw) >= 2
                    else (0.0, 100.0)
                )
            except (ValueError, TypeError, IndexError):
                adaptive_range = (0.0, 100.0)
            base_threshold_raw = threshold_config.get("base_threshold", 0.0)
            try:
                if (
                    isinstance(base_threshold_raw, int | float | str)
                    and base_threshold_raw is not None
                ):
                    base_threshold = float(base_threshold_raw)
                else:
                    base_threshold = 0.0
            except (ValueError, TypeError):
                base_threshold = 0.0

            if alert_type in ["cpu_usage", "memory_usage"]:
                # 对于资源使用率，使用P95 + 1.5 * 标准差
                adaptive_threshold = min(p95_value + 1.5 * std_dev, adaptive_range[1])
            elif alert_type == "response_time":
                # 对于响应时间，使用P95 + 2 * 标准差
                adaptive_threshold = min(p95_value + 2 * std_dev, adaptive_range[1])
            elif alert_type == "error_rate":
                # 对于错误率，使用均值 + 3 * 标准差
                adaptive_threshold = min(mean_value + 3 * std_dev, adaptive_range[1])
            else:
                adaptive_threshold = base_threshold

            # 确保在合理范围内
            adaptive_threshold = max(adaptive_threshold, adaptive_range[0])

            return adaptive_threshold

        except Exception as e:
            logger.error(f"计算自适应阈值失败: {str(e)}")
            fallback_config = self.adaptive_thresholds.get(alert_type, {})
            fallback_threshold = fallback_config.get("base_threshold", 0.0)
            try:
                if (
                    isinstance(fallback_threshold, int | float | str)
                    and fallback_threshold is not None
                ):
                    return float(fallback_threshold)
                else:
                    return 0.0
            except (ValueError, TypeError):
                return 0.0

    async def _aggregate_similar_alerts(self, alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """聚合相似告警."""
        try:
            if not alerts:
                return []

            aggregated_alerts = []
            processed_indices = set()

            for i, alert in enumerate(alerts):
                if i in processed_indices:
                    continue

                # 查找相似告警
                similar_alerts = [alert]
                similar_indices = {i}

                for j, other_alert in enumerate(alerts[i + 1 :], i + 1):
                    if j in processed_indices:
                        continue

                    similarity = self._calculate_alert_similarity(alert, other_alert)
                    if similarity >= self.aggregation_rules["similarity_threshold"]:
                        similar_alerts.append(other_alert)
                        similar_indices.add(j)

                # 如果有相似告警，进行聚合
                if len(similar_alerts) > 1:
                    aggregated_alert = self._create_aggregated_alert(similar_alerts)
                    aggregated_alerts.append(aggregated_alert)
                else:
                    aggregated_alerts.append(alert)

                processed_indices.update(similar_indices)

            return aggregated_alerts

        except Exception as e:
            logger.error(f"聚合相似告警失败: {str(e)}")
            return alerts

    async def _apply_noise_reduction(self, alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """应用告警降噪."""
        try:
            filtered_alerts = []

            for alert in alerts:
                # 检查告警频率
                if await self._is_alert_too_frequent(alert):
                    self.suppressed_alerts[
                        f"frequent_{alert.get('type', 'unknown')}_{datetime.now().timestamp()}"
                    ] = {
                        "alert": alert,
                        "reason": "too_frequent",
                        "suppressed_at": datetime.now().isoformat(),
                    }
                    continue

                # 检查告警持续时间
                if await self._is_alert_too_short(alert):
                    self.suppressed_alerts[
                        f"short_{alert.get('type', 'unknown')}_{datetime.now().timestamp()}"
                    ] = {
                        "alert": alert,
                        "reason": "too_short_duration",
                        "suppressed_at": datetime.now().isoformat(),
                    }
                    continue

                # 检查告警置信度
                confidence = alert.get("confidence_score", 1.0)
                if confidence < 0.6:  # 低置信度告警
                    self.suppressed_alerts[
                        f"low_confidence_{alert.get('type', 'unknown')}_{datetime.now().timestamp()}"
                    ] = {
                        "alert": alert,
                        "reason": "low_confidence",
                        "confidence": confidence,
                        "suppressed_at": datetime.now().isoformat(),
                    }
                    continue

                filtered_alerts.append(alert)

            return filtered_alerts

        except Exception as e:
            logger.error(f"应用告警降噪失败: {str(e)}")
            return alerts

    async def _evaluate_alert_priorities(
        self, alerts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """评估告警优先级."""
        try:
            for alert in alerts:
                # 计算优先级分数
                priority_score = await self._calculate_priority_score(alert)

                # 设置优先级等级
                if priority_score >= 0.8:
                    priority_level = "critical"
                elif priority_score >= 0.6:
                    priority_level = "high"
                elif priority_score >= 0.4:
                    priority_level = "medium"
                else:
                    priority_level = "low"

                alert["priority_score"] = priority_score
                alert["priority_level"] = priority_level
                alert["escalation_required"] = priority_score >= 0.7

            # 按优先级排序
            alerts.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

            return alerts

        except Exception as e:
            logger.error(f"评估告警优先级失败: {str(e)}")
            return alerts

    async def _generate_predictive_alerts(self) -> list[dict[str, Any]]:
        """生成预测性告警."""
        try:
            predictive_alerts = []

            # 基于趋势分析生成预测告警
            for metric_type in [
                "cpu_usage",
                "memory_usage",
                "response_time",
                "error_rate",
            ]:
                trend_analysis = await self._analyze_metric_trend(metric_type)

                if trend_analysis.get("trend_direction") == "increasing":
                    trend_strength = trend_analysis.get("trend_strength", 0)

                    if trend_strength > 0.5:  # 强烈上升趋势
                        predicted_time = await self._predict_threshold_breach_time(
                            metric_type, trend_analysis
                        )

                        if predicted_time and predicted_time < 3600:  # 1小时内可能超阈值
                            predictive_alerts.append(
                                {
                                    "type": f"predictive_{metric_type}",
                                    "severity": "warning",
                                    "message": f"预测{metric_type}在{predicted_time / 60:.0f}分钟内可能超过阈值",
                                    "predicted_time_seconds": predicted_time,
                                    "trend_strength": trend_strength,
                                    "confidence": min(trend_strength, 0.9),
                                    "generated_at": datetime.now().isoformat(),
                                }
                            )

            return predictive_alerts

        except Exception as e:
            logger.error(f"生成预测性告警失败: {str(e)}")
            return []

    def _should_trigger_alert(
        self, alert_type: str, current_value: float, threshold: float
    ) -> bool:
        """判断是否应该触发告警."""
        if alert_type in ["cpu_usage", "memory_usage", "response_time"]:
            return current_value > threshold
        elif alert_type == "error_rate":
            return current_value > threshold
        else:
            return current_value > threshold

    def _calculate_alert_similarity(self, alert1: dict[str, Any], alert2: dict[str, Any]) -> float:
        """计算告警相似度."""
        # 简化的相似度计算
        type_match = 1.0 if alert1.get("type") == alert2.get("type") else 0.0
        severity_match = 1.0 if alert1.get("severity") == alert2.get("severity") else 0.5

        # 时间相似度
        time1 = alert1.get("timestamp", datetime.now().isoformat())
        time2 = alert2.get("timestamp", datetime.now().isoformat())

        try:
            dt1 = datetime.fromisoformat(time1.replace("Z", "+00:00"))
            dt2 = datetime.fromisoformat(time2.replace("Z", "+00:00"))
            time_diff = abs((dt1 - dt2).total_seconds())
            time_similarity = max(0, 1 - time_diff / 300)  # 5分钟内认为相似
        except Exception:
            time_similarity = 0.5

        return type_match * 0.5 + severity_match * 0.3 + time_similarity * 0.2

    def _create_aggregated_alert(self, similar_alerts: list[dict[str, Any]]) -> dict[str, Any]:
        """创建聚合告警."""
        if not similar_alerts:
            return {}

        base_alert = similar_alerts[0]

        return {
            "type": f"aggregated_{base_alert.get('type', 'unknown')}",
            "severity": base_alert.get("severity", "medium"),
            "message": f"聚合告警: {len(similar_alerts)}个相似的{base_alert.get('type', '未知')}告警",
            "aggregated_count": len(similar_alerts),
            "individual_alerts": similar_alerts,
            "first_occurrence": min(alert.get("timestamp", "") for alert in similar_alerts),
            "last_occurrence": max(alert.get("timestamp", "") for alert in similar_alerts),
            "confidence_score": statistics.mean(
                [alert.get("confidence_score", 1.0) for alert in similar_alerts]
            ),
            "created_at": datetime.now().isoformat(),
        }

    async def _calculate_alert_confidence(self, alert: dict[str, Any]) -> float:
        """计算告警置信度."""
        # 基于多个因素计算置信度
        base_confidence = 0.8

        # 基于历史数据调整
        alert_type = alert.get("type", "")
        historical_accuracy = await self._get_historical_alert_accuracy(alert_type)

        # 基于当前值与阈值的差距
        current_value_raw = alert.get("current_value", 0)
        threshold_raw = alert.get("threshold", 0)
        current_value = float(current_value_raw) if current_value_raw is not None else 0.0
        threshold = float(threshold_raw) if threshold_raw is not None else 0.0

        if threshold > 0:
            deviation_ratio = abs(current_value - threshold) / threshold
            deviation_confidence = min(deviation_ratio, 1.0)
        else:
            deviation_confidence = 0.5

        # 综合计算
        confidence = (
            float(base_confidence) * 0.4
            + float(historical_accuracy) * 0.3
            + float(deviation_confidence) * 0.3
        )

        return min(max(confidence, 0.0), 1.0)

    async def _calculate_priority_score(self, alert: dict[str, Any]) -> float:
        """计算告警优先级分数."""
        # 基础分数
        severity_scores = {"critical": 1.0, "high": 0.8, "medium": 0.6, "low": 0.4}
        base_score = severity_scores.get(alert.get("severity", "medium"), 0.6)

        # 置信度调整
        confidence_raw = alert.get("confidence_score", 1.0)
        confidence = float(confidence_raw) if confidence_raw is not None else 1.0

        # 业务影响调整
        business_impact = await self._assess_business_impact(alert)

        # 综合计算
        priority_score = float(base_score) * 0.4 + confidence * 0.3 + float(business_impact) * 0.3

        return min(max(priority_score, 0.0), 1.0)

    async def _assess_business_impact(self, alert: dict[str, Any]) -> float:
        """评估业务影响."""
        # 简化的业务影响评估
        alert_type = alert.get("type", "")

        impact_scores = {
            "high_error_rate": 0.9,
            "slow_api_response": 0.8,
            "high_cpu_usage": 0.6,
            "high_memory_usage": 0.7,
            "high_db_connections": 0.5,
        }

        return impact_scores.get(alert_type, 0.5)

    # 辅助方法的简化实现
    async def _get_historical_metrics(self, metric_type: str, hours: int) -> list[float]:
        """获取历史指标数据."""
        # 简化实现，返回模拟数据
        import random

        return [random.uniform(0, 100) for _ in range(50)]

    async def _get_historical_alert_accuracy(self, alert_type: str) -> float:
        """获取历史告警准确率."""
        # 简化实现
        return 0.85

    async def _is_alert_too_frequent(self, alert: dict[str, Any]) -> bool:
        """检查告警是否过于频繁."""
        # 简化实现
        return False

    async def _is_alert_too_short(self, alert: dict[str, Any]) -> bool:
        """检查告警持续时间是否过短."""
        # 简化实现
        return False

    async def _analyze_metric_trend(self, metric_type: str) -> dict[str, Any]:
        """分析指标趋势."""
        # 简化实现
        return {"trend_direction": "stable", "trend_strength": 0.3}

    async def _predict_threshold_breach_time(
        self, metric_type: str, trend_analysis: dict[str, Any]
    ) -> float | None:
        """预测阈值突破时间."""
        # 简化实现
        return 1800.0  # 30分钟

    async def _plan_alert_notifications(self, alerts: list[dict[str, Any]]) -> dict[str, Any]:
        """规划告警通知."""
        return {
            "immediate_notifications": len(
                [a for a in alerts if a.get("priority_level") == "critical"]
            ),
            "scheduled_notifications": len(
                [a for a in alerts if a.get("priority_level") in ["high", "medium"]]
            ),
            "notification_channels": ["email", "slack"],
        }

    async def _update_alert_states(self, alerts: list[dict[str, Any]]) -> None:
        """更新告警状态."""
        for alert in alerts:
            alert_id = f"{alert.get('type', 'unknown')}_{datetime.now().timestamp()}"
            self.active_alerts[alert_id] = alert

    async def _generate_alert_statistics(self) -> dict[str, Any]:
        """生成告警统计."""
        return {
            "active_alerts_count": len(self.active_alerts),
            "suppressed_alerts_count": len(self.suppressed_alerts),
            "total_processed": len(self.active_alerts) + len(self.suppressed_alerts),
        }

    async def _get_threshold_adjustments(self) -> dict[str, Any]:
        """获取阈值调整信息."""
        adjustments = {}
        for alert_type, config in self.adaptive_thresholds.items():
            current_threshold = await self._calculate_adaptive_threshold(alert_type)
            base_threshold_raw = config["base_threshold"]
            try:
                if (
                    isinstance(base_threshold_raw, int | float | str)
                    and base_threshold_raw is not None
                ):
                    base_threshold = float(base_threshold_raw)
                else:
                    base_threshold = 0.0
            except (ValueError, TypeError):
                base_threshold = 0.0
            adjustments[alert_type] = {
                "base_threshold": base_threshold,
                "current_threshold": current_threshold,
                "adjustment": current_threshold - base_threshold,
            }
        return adjustments
