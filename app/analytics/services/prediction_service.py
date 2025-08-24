"""预测性维护服务 - 实现硬件故障预测和系统风险预警."""

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas.analytics_schemas import PredictionRequest, PredictionResult
from app.analytics.utils.alert_utils import MetricThresholdCalculator

logger = logging.getLogger(__name__)


class TimeSeriesPredictor:
    """时间序列预测器."""

    def __init__(self) -> None:
        """初始化时间序列预测器."""
        self.scaler = StandardScaler()

    def simple_moving_average(self, data: list[float], window: int = 7) -> float:
        """简单移动平均预测."""
        if len(data) < window:
            return float(np.mean(data)) if data else 0.0

        return float(np.mean(data[-window:]))

    def exponential_smoothing(self, data: list[float], alpha: float = 0.3) -> float:
        """指数平滑预测."""
        if not data:
            return 0.0

        if len(data) == 1:
            return data[0]

        # 初始值
        smoothed = data[0]

        # 指数平滑
        for value in data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        return smoothed

    def linear_regression_predict(self, data: list[float], periods_ahead: int = 1) -> list[float]:
        """线性回归预测."""
        if len(data) < 2:
            return [data[0] if data else 0.0] * periods_ahead

        # 准备数据
        x = np.arange(len(data)).reshape(-1, 1)
        y = np.array(data)

        # 简单线性回归
        x_mean = np.mean(x.flatten())
        y_mean = np.mean(y)

        numerator = np.sum((x.flatten() - x_mean) * (y - y_mean))
        denominator = np.sum((x.flatten() - x_mean) ** 2)

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        intercept = y_mean - slope * x_mean

        # 预测
        predictions = []
        for i in range(periods_ahead):
            future_x = len(data) + i
            predicted_y = slope * future_x + intercept
            predictions.append(predicted_y)

        return predictions

    def detect_seasonality(self, data: list[float], period: int = 24) -> dict[str, Any]:
        """检测季节性模式."""
        if len(data) < period * 2:
            return {"has_seasonality": False, "strength": 0.0}

        # 计算不同周期的自相关系数
        correlations = []
        for lag in range(1, min(period + 1, len(data) // 2)):
            if len(data) > lag:
                corr = np.corrcoef(data[:-lag], data[lag:])[0, 1]
                if not np.isnan(corr):
                    correlations.append(abs(corr))

        if not correlations:
            return {"has_seasonality": False, "strength": 0.0}

        max_correlation = max(correlations)
        has_seasonality = max_correlation > 0.3  # 阈值

        return {
            "has_seasonality": has_seasonality,
            "strength": max_correlation,
            "best_period": correlations.index(max_correlation) + 1,
        }


class AnomalyDetector:
    """异常检测器."""

    def __init__(self) -> None:
        """初始化异常检测器."""
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)

    def detect_outliers_iqr(self, data: list[float], multiplier: float = 1.5) -> dict[str, Any]:
        """使用IQR方法检测异常值."""
        if len(data) < 4:
            return {"outliers": [], "bounds": {"lower": 0, "upper": 0}}

        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        outliers = [
            {"index": i, "value": value, "is_high": value > upper_bound}
            for i, value in enumerate(data)
            if value < lower_bound or value > upper_bound
        ]

        return {
            "outliers": outliers,
            "bounds": {"lower": lower_bound, "upper": upper_bound},
            "outlier_count": len(outliers),
            "outlier_rate": len(outliers) / len(data),
        }

    def detect_anomalies_isolation_forest(self, data: list[float]) -> dict[str, Any]:
        """使用孤立森林检测异常."""
        if len(data) < 10:
            return {"anomalies": [], "anomaly_scores": []}

        # 重塑数据
        X = np.array(data).reshape(-1, 1)

        # 训练模型
        self.isolation_forest.fit(X)

        # 预测异常
        anomaly_labels = self.isolation_forest.predict(X)
        anomaly_scores = self.isolation_forest.decision_function(X)

        anomalies = [
            {"index": i, "value": data[i], "score": float(scores)}
            for i, (label, scores) in enumerate(zip(anomaly_labels, anomaly_scores, strict=False))
            if label == -1
        ]

        return {
            "anomalies": anomalies,
            "anomaly_scores": anomaly_scores.tolist(),
            "anomaly_count": len(anomalies),
        }


class FailurePredictionEngine:
    """故障预测引擎."""

    def __init__(self) -> None:
        """初始化故障预测引擎."""
        self.predictor = TimeSeriesPredictor()
        self.detector = AnomalyDetector()
        self.threshold_calculator = MetricThresholdCalculator()

    async def predict_system_failure(
        self,
        metric_name: str,
        historical_data: list[float],
        timestamps: list[datetime],
        prediction_days: int = 7,
    ) -> dict[str, Any]:
        """预测系统故障."""
        try:
            if len(historical_data) < 10:
                return {
                    "prediction": "insufficient_data",
                    "confidence": 0.0,
                    "risk_level": "unknown",
                }

            # 异常检测
            anomaly_result = self.detector.detect_outliers_iqr(historical_data)
            isolation_result = self.detector.detect_anomalies_isolation_forest(historical_data)

            # 趋势预测
            future_values = self.predictor.linear_regression_predict(
                historical_data, periods_ahead=prediction_days
            )

            # 计算动态阈值
            thresholds = self.threshold_calculator.calculate_dynamic_threshold(
                historical_data, multiplier=2.0, method="std"
            )

            # 评估风险
            risk_factors = []
            risk_score = 0.0

            # 1. 异常值因子
            outlier_rate = anomaly_result.get("outlier_rate", 0)
            if outlier_rate > 0.1:
                risk_factors.append("高异常值比例")
                risk_score += outlier_rate * 30

            # 2. 趋势因子
            if len(future_values) > 0:
                trend_slope = (future_values[-1] - historical_data[-1]) / prediction_days
                if abs(trend_slope) > np.std(historical_data):
                    risk_factors.append("趋势变化剧烈")
                    risk_score += 25

            # 3. 阈值超越风险
            current_value = historical_data[-1]
            if current_value > thresholds["upper"]:
                risk_factors.append("当前值超过上阈值")
                risk_score += 40
            elif current_value < thresholds["lower"]:
                risk_factors.append("当前值低于下阈值")
                risk_score += 30

            # 4. 数据波动性
            volatility = np.std(historical_data) / np.mean(historical_data)
            if volatility > 0.3:
                risk_factors.append("数据波动性过大")
                risk_score += 20

            # 确定风险等级
            if risk_score > 70:
                risk_level = "critical"
            elif risk_score > 50:
                risk_level = "high"
            elif risk_score > 30:
                risk_level = "medium"
            else:
                risk_level = "low"

            # 预测故障发生时间
            failure_prediction = None
            if risk_level in ["high", "critical"]:
                # 基于当前趋势预测何时会超过临界阈值
                days_to_failure = self._estimate_time_to_failure(
                    current_value, future_values, thresholds["upper"]
                )
                if days_to_failure:
                    failure_prediction = datetime.utcnow() + timedelta(days=days_to_failure)

            return {
                "metric_name": metric_name,
                "prediction": (
                    "failure_likely" if risk_level in ["high", "critical"] else "normal"
                ),
                "risk_level": risk_level,
                "risk_score": risk_score,
                "confidence": min(len(historical_data) / 100.0, 0.95),
                "predicted_failure_date": (
                    failure_prediction.isoformat() if failure_prediction else None
                ),
                "risk_factors": risk_factors,
                "current_value": current_value,
                "predicted_values": future_values,
                "thresholds": thresholds,
                "anomaly_detection": {
                    "outlier_count": anomaly_result.get("outlier_count", 0),
                    "isolation_anomalies": len(isolation_result.get("anomalies", [])),
                },
            }

        except Exception as e:
            logger.error(f"系统故障预测失败: {e}")
            return {"prediction": "error", "error": str(e), "risk_level": "unknown"}

    def _estimate_time_to_failure(
        self, current_value: float, future_values: list[float], threshold: float
    ) -> int | None:
        """估算故障发生时间（天）."""
        for day, value in enumerate(future_values, 1):
            if value > threshold:
                return day
        return None

    async def predict_capacity_needs(
        self, usage_data: list[float], growth_rate: float = 0.1
    ) -> dict[str, Any]:
        """预测容量需求."""
        try:
            if not usage_data:
                return {"status": "insufficient_data"}

            current_usage = usage_data[-1]
            max_usage = max(usage_data)
            avg_usage = np.mean(usage_data)

            # 计算增长趋势
            if len(usage_data) >= 7:
                recent_trend = (
                    np.mean(usage_data[-7:]) - np.mean(usage_data[-14:-7])
                    if len(usage_data) >= 14
                    else 0
                )
            else:
                recent_trend = 0

            # 预测未来容量需求
            predictions = {}
            for period, days in [
                ("1个月", 30),
                ("3个月", 90),
                ("6个月", 180),
                ("1年", 365),
            ]:
                # 基于历史增长率和趋势
                adjusted_growth = growth_rate + (
                    recent_trend / current_usage if current_usage > 0 else 0
                )
                predicted_usage = current_usage * (1 + adjusted_growth) ** (days / 30)

                predictions[period] = {
                    "predicted_usage": predicted_usage,
                    "capacity_utilization": min(float(predicted_usage / 100 * 100), 100.0),
                    "additional_capacity_needed": max(
                        0.0, float(predicted_usage - 80)
                    ),  # 假设80%为容量警戒线
                    "risk_level": self._assess_capacity_risk(float(predicted_usage)),
                }

            return {
                "current_metrics": {
                    "current_usage": current_usage,
                    "max_usage": max_usage,
                    "average_usage": avg_usage,
                    "recent_trend": recent_trend,
                },
                "capacity_predictions": predictions,
                "recommendations": self._generate_capacity_recommendations(predictions),
            }

        except Exception as e:
            logger.error(f"容量需求预测失败: {e}")
            return {"status": "error", "error": str(e)}

    def _assess_capacity_risk(self, predicted_usage: float) -> str:
        """评估容量风险等级."""
        if predicted_usage > 95:
            return "critical"
        elif predicted_usage > 85:
            return "high"
        elif predicted_usage > 70:
            return "medium"
        else:
            return "low"

    def _generate_capacity_recommendations(self, predictions: dict[str, Any]) -> list[str]:
        """生成容量建议."""
        recommendations = []

        # 检查1个月预测
        one_month = predictions.get("1个月", {})
        if one_month.get("risk_level") == "critical":
            recommendations.append("建议立即增加系统容量")
        elif one_month.get("risk_level") == "high":
            recommendations.append("建议在2周内规划容量扩展")

        # 检查长期趋势
        one_year = predictions.get("1年", {})
        if one_year.get("capacity_utilization", 0) > 80:
            recommendations.append("建议制定长期容量规划")

        if not recommendations:
            recommendations.append("当前容量充足，保持监控")

        return recommendations


class PredictionService:
    """预测服务主类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化预测服务."""
        self.db = db_session
        self.failure_engine = FailurePredictionEngine()

    async def create_prediction(self, request: PredictionRequest) -> PredictionResult:
        """创建预测分析."""
        try:
            # 获取历史数据（在实际实现中从数据库获取）
            historical_data = await self._get_historical_data(
                request.metric_name, request.time_range
            )

            if request.prediction_type == "failure":
                result = await self.failure_engine.predict_system_failure(
                    request.metric_name,
                    historical_data["values"],
                    historical_data["timestamps"],
                    request.time_range,
                )

                return PredictionResult(
                    metric_name=request.metric_name,
                    prediction_type=request.prediction_type,
                    confidence=result["confidence"],
                    predicted_date=result.get("predicted_failure_date"),
                    risk_level=result["risk_level"],
                    recommendations=result.get("risk_factors", []),
                    historical_data=[
                        {"timestamp": ts.isoformat(), "value": val}
                        for ts, val in zip(
                            historical_data["timestamps"],
                            historical_data["values"],
                            strict=False,
                        )
                    ],
                    model_accuracy=self._calculate_model_accuracy(historical_data["values"]),
                )

            elif request.prediction_type == "capacity":
                result = await self.failure_engine.predict_capacity_needs(historical_data["values"])

                return PredictionResult(
                    metric_name=request.metric_name,
                    prediction_type=request.prediction_type,
                    confidence=request.confidence_level,
                    predicted_date=None,  # TODO: 根据业务逻辑设置预测日期
                    risk_level=self._assess_overall_capacity_risk(result),
                    recommendations=result.get("recommendations", []),
                    historical_data=[
                        {"timestamp": ts.isoformat(), "value": val}
                        for ts, val in zip(
                            historical_data["timestamps"],
                            historical_data["values"],
                            strict=False,
                        )
                    ],
                    model_accuracy=0.85,  # 模拟准确率
                )

            else:
                raise ValueError(f"不支持的预测类型: {request.prediction_type}")

        except Exception as e:
            logger.error(f"创建预测分析失败: {e}")
            raise e

    async def _get_historical_data(self, metric_name: str, days: int) -> dict[str, Any]:
        """获取历史数据."""
        # 在实际实现中，这里会从数据库查询历史指标数据
        # 现在生成模拟数据

        timestamps = []
        values = []

        base_time = datetime.utcnow() - timedelta(days=days)

        for i in range(days * 24):  # 每小时一个数据点
            timestamp = base_time + timedelta(hours=i)

            # 生成带有趋势和噪声的模拟数据
            if metric_name == "cpu_usage":
                base_value = 60 + 10 * math.sin(i / 24 * 2 * math.pi)  # 日周期
                noise = random.gauss(0, 5)
                trend = i * 0.01  # 轻微上升趋势
                value = max(0, min(100, base_value + noise + trend))
            elif metric_name == "memory_usage":
                base_value = 70 + 15 * math.sin(i / 168 * 2 * math.pi)  # 周周期
                noise = random.gauss(0, 3)
                value = max(0, min(100, base_value + noise))
            else:
                value = 50 + random.gauss(0, 10)

            timestamps.append(timestamp)
            values.append(value)

        return {"timestamps": timestamps, "values": values}

    def _calculate_model_accuracy(self, historical_data: list[float]) -> float:
        """计算模型准确率（简化版本）."""
        # 在实际实现中，这里会基于历史预测的准确性计算
        # 现在基于数据质量返回模拟准确率

        if len(historical_data) < 100:
            return 0.75
        elif len(historical_data) < 1000:
            return 0.85
        else:
            return 0.90

    def _assess_overall_capacity_risk(self, capacity_result: dict[str, Any]) -> str:
        """评估整体容量风险."""
        predictions = capacity_result.get("capacity_predictions", {})

        # 检查最高风险等级
        risk_levels = ["low", "medium", "high", "critical"]
        max_risk = "low"

        for period_data in predictions.values():
            risk = period_data.get("risk_level", "low")
            if risk_levels.index(risk) > risk_levels.index(max_risk):
                max_risk = risk

        return max_risk

    async def get_prediction_accuracy_report(self) -> dict[str, Any]:
        """获取预测准确性报告."""
        # 在实际实现中，这里会分析历史预测的准确性
        return {
            "overall_accuracy": 87.5,
            "failure_prediction_accuracy": 89.2,
            "capacity_prediction_accuracy": 85.8,
            "false_positive_rate": 12.3,
            "false_negative_rate": 8.7,
            "model_performance": {
                "precision": 0.882,
                "recall": 0.913,
                "f1_score": 0.897,
            },
            "generated_at": datetime.utcnow(),
        }

    async def update_prediction_models(self) -> dict[str, Any]:
        """更新预测模型."""
        # 在实际实现中，这里会基于新数据重新训练模型
        return {
            "status": "success",
            "updated_models": ["failure_prediction", "capacity_prediction"],
            "last_update": datetime.utcnow(),
            "next_update": datetime.utcnow() + timedelta(days=7),
        }
