"""质量监控服务 - AI生成内容的质量监控和评估."""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# from app.ai.models.ai_models import QualityMonitoringLog  # 暂时注释，模型不存在
from app.ai.utils.text_utils import calculate_text_similarity

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """质量指标"""

    ACCURACY = "accuracy"  # 准确性
    RELEVANCE = "relevance"  # 相关性
    CLARITY = "clarity"  # 清晰度
    COMPLETENESS = "completeness"  # 完整性
    CONSISTENCY = "consistency"  # 一致性


class QualityLevel(Enum):
    """质量等级"""

    EXCELLENT = "excellent"  # 优秀 (90-100)
    GOOD = "good"  # 良好 (70-89)
    FAIR = "fair"  # 一般 (50-69)
    POOR = "poor"  # 较差 (30-49)
    UNACCEPTABLE = "unacceptable"  # 不可接受 (0-29)


class QualityMonitoringService:
    """质量监控服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 质量阈值配置
        self.quality_thresholds = {
            QualityLevel.EXCELLENT: 90.0,
            QualityLevel.GOOD: 70.0,
            QualityLevel.FAIR: 50.0,
            QualityLevel.POOR: 30.0,
            QualityLevel.UNACCEPTABLE: 0.0,
        }

        # 质量权重配置
        self.metric_weights = {
            QualityMetric.ACCURACY: 0.3,
            QualityMetric.RELEVANCE: 0.25,
            QualityMetric.CLARITY: 0.2,
            QualityMetric.COMPLETENESS: 0.15,
            QualityMetric.CONSISTENCY: 0.1,
        }

    async def evaluate_content_quality(
        self,
        db: AsyncSession,
        content: str,
        content_type: str,
        reference_content: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """评估内容质量"""
        try:
            context = context or {}

            # 计算各项质量指标
            metrics = {}

            # 1. 准确性评估
            metrics[QualityMetric.ACCURACY] = await self._evaluate_accuracy(
                content, reference_content, context
            )

            # 2. 相关性评估
            metrics[QualityMetric.RELEVANCE] = await self._evaluate_relevance(content, context)

            # 3. 清晰度评估
            metrics[QualityMetric.CLARITY] = await self._evaluate_clarity(content)

            # 4. 完整性评估
            metrics[QualityMetric.COMPLETENESS] = await self._evaluate_completeness(
                content, content_type, context
            )

            # 5. 一致性评估
            metrics[QualityMetric.CONSISTENCY] = await self._evaluate_consistency(
                content, reference_content
            )

            # 计算综合质量分数
            overall_score = self._calculate_overall_score(metrics)

            # 确定质量等级
            quality_level = self._determine_quality_level(overall_score)

            # 生成改进建议
            suggestions = self._generate_improvement_suggestions(metrics, content_type)

            # 记录监控日志
            await self._log_quality_monitoring(
                db, content_type, overall_score, quality_level, metrics
            )

            return {
                "overall_score": overall_score,
                "quality_level": quality_level.value,
                "metrics": {metric.value: score for metric, score in metrics.items()},
                "suggestions": suggestions,
                "is_acceptable": quality_level != QualityLevel.UNACCEPTABLE,
                "evaluated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"质量评估失败: {e}")
            return {
                "overall_score": 0.0,
                "quality_level": QualityLevel.UNACCEPTABLE.value,
                "metrics": {},
                "suggestions": ["质量评估失败，请检查内容"],
                "is_acceptable": False,
                "evaluated_at": datetime.utcnow().isoformat(),
            }

    async def _evaluate_accuracy(
        self, content: str, reference: str | None, context: dict[str, Any]
    ) -> float:
        """评估准确性"""
        if not reference:
            # 无参考内容时，基于内容本身的逻辑一致性评估
            return self._evaluate_logical_consistency(content)

        # 有参考内容时，计算相似度
        similarity = calculate_text_similarity(content, reference)
        return min(similarity * 100, 100.0)

    async def _evaluate_relevance(self, content: str, context: dict[str, Any]) -> float:
        """评估相关性"""
        topic = context.get("topic", "")
        keywords = context.get("keywords", [])

        if not topic and not keywords:
            return 70.0  # 默认中等相关性

        relevance_score = 0.0

        # 主题相关性
        if topic and topic.lower() in content.lower():
            relevance_score += 40.0

        # 关键词相关性
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in content.lower())
            keyword_score = (keyword_matches / len(keywords)) * 60.0
            relevance_score += keyword_score

        return min(relevance_score, 100.0)

    async def _evaluate_clarity(self, content: str) -> float:
        """评估清晰度"""
        clarity_score = 80.0  # 基础分数

        # 句子长度检查
        sentences = content.split("。")
        avg_sentence_length = (
            sum(len(s.strip()) for s in sentences) / len(sentences) if sentences else 0
        )

        if avg_sentence_length > 100:  # 句子过长
            clarity_score -= 15.0
        elif avg_sentence_length < 10:  # 句子过短
            clarity_score -= 10.0

        # 标点符号使用
        punctuation_count = sum(1 for char in content if char in "，。！？；：")
        if punctuation_count < len(content) * 0.05:  # 标点符号过少
            clarity_score -= 10.0

        # 重复词汇检查
        words = content.split()
        unique_words = set(words)
        if len(unique_words) < len(words) * 0.6:  # 重复词汇过多
            clarity_score -= 15.0

        return max(0.0, min(clarity_score, 100.0))

    async def _evaluate_completeness(
        self, content: str, content_type: str, context: dict[str, Any]
    ) -> float:
        """评估完整性"""
        completeness_score = 70.0  # 基础分数

        # 内容长度检查
        content_length = len(content.strip())

        if content_type == "question":
            if content_length < 20:
                completeness_score -= 30.0
            elif content_length > 500:
                completeness_score += 10.0
        elif content_type == "answer":
            if content_length < 50:
                completeness_score -= 25.0
            elif content_length > 200:
                completeness_score += 15.0
        elif content_type == "explanation":
            if content_length < 100:
                completeness_score -= 20.0
            elif content_length > 300:
                completeness_score += 10.0

        # 结构完整性检查
        required_elements = context.get("required_elements", [])
        if required_elements:
            present_elements = sum(1 for element in required_elements if element in content)
            structure_score = (present_elements / len(required_elements)) * 30.0
            completeness_score += structure_score - 15.0  # 调整基础分数

        return max(0.0, min(completeness_score, 100.0))

    async def _evaluate_consistency(self, content: str, reference: str | None) -> float:
        """评估一致性"""
        if not reference:
            return self._evaluate_internal_consistency(content)

        # 与参考内容的一致性
        similarity = calculate_text_similarity(content, reference)
        return similarity * 100

    def _evaluate_logical_consistency(self, content: str) -> float:
        """评估逻辑一致性"""
        # 简化的逻辑一致性检查
        consistency_score = 75.0

        # 检查矛盾表述
        contradiction_patterns = [
            ("是", "不是"),
            ("正确", "错误"),
            ("可以", "不可以"),
            ("应该", "不应该"),
            ("会", "不会"),
        ]

        for pos, neg in contradiction_patterns:
            if pos in content and neg in content:
                consistency_score -= 10.0

        return max(0.0, min(consistency_score, 100.0))

    def _evaluate_internal_consistency(self, content: str) -> float:
        """评估内部一致性"""
        # 检查内容内部的一致性
        sentences = content.split("。")
        if len(sentences) < 2:
            return 80.0  # 单句内容默认一致

        # 简化的一致性检查：检查句子间的主题一致性
        consistency_score = 85.0

        # 这里可以添加更复杂的一致性检查逻辑
        # 目前使用简化版本

        return consistency_score

    def _calculate_overall_score(self, metrics: dict[QualityMetric, float]) -> float:
        """计算综合质量分数"""
        weighted_sum = 0.0
        total_weight = 0.0

        for metric, score in metrics.items():
            weight = self.metric_weights.get(metric, 0.0)
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        for level, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return level
        return QualityLevel.UNACCEPTABLE

    def _generate_improvement_suggestions(
        self, metrics: dict[QualityMetric, float], content_type: str
    ) -> list[str]:
        """生成改进建议"""
        suggestions = []

        for metric, score in metrics.items():
            if score < 60.0:  # 分数较低的指标
                if metric == QualityMetric.ACCURACY:
                    suggestions.append("建议检查内容的准确性，确保信息正确")
                elif metric == QualityMetric.RELEVANCE:
                    suggestions.append("建议增强内容与主题的相关性")
                elif metric == QualityMetric.CLARITY:
                    suggestions.append("建议改善表达的清晰度，使用更简洁的语言")
                elif metric == QualityMetric.COMPLETENESS:
                    suggestions.append("建议补充更多详细信息，使内容更完整")
                elif metric == QualityMetric.CONSISTENCY:
                    suggestions.append("建议检查内容的一致性，避免矛盾表述")

        if not suggestions:
            suggestions.append("内容质量良好，继续保持")

        return suggestions

    async def _log_quality_monitoring(
        self,
        db: AsyncSession,
        content_type: str,
        overall_score: float,
        quality_level: QualityLevel,
        metrics: dict[QualityMetric, float],
    ) -> None:
        """记录质量监控日志"""
        try:
            # 暂时使用日志记录，而不是数据库存储
            # 因为 QualityMonitoringLog 模型不存在
            log_data = {
                "content_type": content_type,
                "overall_score": overall_score,
                "quality_level": quality_level.value,
                "accuracy_score": metrics.get(QualityMetric.ACCURACY, 0.0),
                "relevance_score": metrics.get(QualityMetric.RELEVANCE, 0.0),
                "clarity_score": metrics.get(QualityMetric.CLARITY, 0.0),
                "completeness_score": metrics.get(QualityMetric.COMPLETENESS, 0.0),
                "consistency_score": metrics.get(QualityMetric.CONSISTENCY, 0.0),
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.logger.info(f"质量监控日志: {log_data}")

        except Exception as e:
            self.logger.error(f"记录质量监控日志失败: {e}")


def get_quality_monitoring_service() -> QualityMonitoringService:
    """获取质量监控服务实例"""
    return QualityMonitoringService()
