"""学习算法工具类 - 自适应学习和智能推荐算法."""

import logging
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class LearningAlgorithm:
    """学习算法工具类 - 提供各种学习分析和推荐算法."""

    def __init__(self) -> None:
        """初始化学习算法工具."""
        # 算法参数配置
        self.algorithm_config = {
            "difficulty_adjustment": {
                "success_threshold": 0.8,  # 成功率阈值
                "failure_threshold": 0.4,  # 失败率阈值
                "adjustment_factor": 0.1,  # 调整因子
            },
            "spaced_repetition": {
                "initial_interval": 1,  # 初始间隔（天）
                "ease_factor": 2.5,  # 简易因子
                "min_ease_factor": 1.3,  # 最小简易因子
                "max_ease_factor": 4.0,  # 最大简易因子
            },
            "learning_curve": {
                "learning_rate": 0.1,  # 学习率
                "decay_rate": 0.01,  # 衰减率
                "plateau_threshold": 0.05,  # 平台期阈值
            },
        }

    def calculate_adaptive_difficulty(
        self, current_difficulty: float, performance_history: list[dict[str, Any]]
    ) -> float:
        """计算自适应难度."""
        try:
            if not performance_history:
                return current_difficulty

            # 计算最近表现
            recent_performance = performance_history[-10:]  # 最近10次
            success_rate = sum(1 for p in recent_performance if p["is_correct"]) / len(
                recent_performance
            )

            # 计算难度调整
            config = self.algorithm_config["difficulty_adjustment"]

            if success_rate >= config["success_threshold"]:
                # 表现良好，增加难度
                adjustment = config["adjustment_factor"]
            elif success_rate <= config["failure_threshold"]:
                # 表现不佳，降低难度
                adjustment = -config["adjustment_factor"]
            else:
                # 表现适中，保持难度
                adjustment = 0.0

            # 应用调整
            new_difficulty = current_difficulty + adjustment

            # 确保难度在合理范围内
            new_difficulty = max(0.1, min(1.0, new_difficulty))

            logger.debug(
                f"难度调整: {current_difficulty:.3f} → {new_difficulty:.3f}, "
                f"成功率: {success_rate:.3f}"
            )
            return new_difficulty

        except Exception as e:
            logger.error(f"计算自适应难度失败: {str(e)}")
            return current_difficulty

    def calculate_spaced_repetition_interval(
        self, previous_interval: int, performance_score: float, ease_factor: float
    ) -> tuple[int, float]:
        """计算间隔重复的下次复习间隔."""
        try:
            config = self.algorithm_config["spaced_repetition"]

            # 根据表现调整简易因子
            if performance_score >= 0.9:
                # 表现优秀
                ease_adjustment = 0.1
            elif performance_score >= 0.7:
                # 表现良好
                ease_adjustment = 0.0
            elif performance_score >= 0.5:
                # 表现一般
                ease_adjustment = -0.15
            else:
                # 表现不佳
                ease_adjustment = -0.2

            # 更新简易因子
            new_ease_factor = ease_factor + ease_adjustment
            new_ease_factor = max(
                config["min_ease_factor"],
                min(config["max_ease_factor"], new_ease_factor),
            )

            # 计算下次间隔
            if performance_score < 0.6:
                # 表现不佳，重置间隔
                next_interval = config["initial_interval"]
            else:
                # 根据简易因子计算间隔
                next_interval = max(1, int(previous_interval * new_ease_factor))

            logger.debug(
                f"间隔重复: 间隔 {previous_interval} → {next_interval} 天, "
                f"简易因子 {ease_factor:.2f} → {new_ease_factor:.2f}"
            )
            return int(next_interval), new_ease_factor

        except Exception as e:
            logger.error(f"计算间隔重复失败: {str(e)}")
            return previous_interval, ease_factor

    def analyze_learning_curve(self, performance_data: list[dict[str, Any]]) -> dict[str, Any]:
        """分析学习曲线."""
        try:
            if len(performance_data) < 5:
                return {"status": "insufficient_data"}

            # 提取性能数据
            scores = [p["score"] for p in performance_data]
            timestamps = [p["timestamp"] for p in performance_data]

            # 计算移动平均
            window_size = min(5, len(scores))
            moving_avg = self._calculate_moving_average(scores, window_size)

            # 分析趋势
            trend = self._analyze_trend(moving_avg)

            # 检测平台期
            plateau_detected = self._detect_plateau(moving_avg)

            # 预测未来表现
            predicted_score = self._predict_next_performance(scores)

            # 计算学习效率
            learning_efficiency = self._calculate_learning_efficiency(scores, timestamps)

            return {
                "status": "analyzed",
                "trend": trend,
                "plateau_detected": plateau_detected,
                "predicted_score": predicted_score,
                "learning_efficiency": learning_efficiency,
                "moving_average": moving_avg,
                "improvement_suggestions": self._generate_learning_suggestions(
                    trend, plateau_detected, learning_efficiency
                ),
            }

        except Exception as e:
            logger.error(f"分析学习曲线失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def cluster_learning_patterns(self, students_data: list[dict[str, Any]]) -> dict[str, Any]:
        """聚类学习模式."""
        try:
            if len(students_data) < 10:
                return {"status": "insufficient_data"}

            # 提取特征
            features = []
            student_ids = []

            for student in students_data:
                feature_vector = self._extract_learning_features(student)
                if feature_vector:
                    features.append(feature_vector)
                    student_ids.append(student["student_id"])

            if len(features) < 5:
                return {"status": "insufficient_features"}

            # 标准化特征
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(features)

            # K-means聚类
            n_clusters = min(5, len(features) // 3)  # 动态确定聚类数
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(normalized_features)

            # 分析聚类结果
            clusters = self._analyze_clusters(
                features, cluster_labels, student_ids, kmeans.cluster_centers_
            )

            return {
                "status": "clustered",
                "n_clusters": n_clusters,
                "clusters": clusters,
                "cluster_characteristics": self._describe_cluster_characteristics(clusters),
            }

        except Exception as e:
            logger.error(f"聚类学习模式失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def recommend_learning_strategy(
        self, student_profile: dict[str, Any], learning_history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """推荐学习策略."""
        try:
            # 分析学习风格
            learning_style = self._identify_learning_style(student_profile, learning_history)

            # 分析当前表现
            current_performance = self._analyze_current_performance(learning_history)

            # 识别薄弱环节
            weak_areas = self._identify_weak_areas(learning_history)

            # 生成个性化建议
            recommendations = self._generate_personalized_recommendations(
                learning_style, current_performance, weak_areas
            )

            return {
                "student_id": student_profile.get("student_id"),
                "learning_style": learning_style,
                "current_performance": current_performance,
                "weak_areas": weak_areas,
                "recommendations": recommendations,
                "confidence_score": self._calculate_recommendation_confidence(learning_history),
            }

        except Exception as e:
            logger.error(f"推荐学习策略失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ==================== 私有方法 ====================

    def _calculate_moving_average(self, data: list[float], window_size: int) -> list[float]:
        """计算移动平均."""
        if len(data) < window_size:
            return data

        moving_avg = []
        for i in range(len(data) - window_size + 1):
            avg = sum(data[i : i + window_size]) / window_size
            moving_avg.append(avg)

        return moving_avg

    def _analyze_trend(self, data: list[float]) -> str:
        """分析趋势."""
        if len(data) < 3:
            return "stable"

        # 计算线性回归斜率
        n = len(data)
        x = list(range(n))
        y = data

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.05:
            return "improving"
        elif slope < -0.05:
            return "declining"
        else:
            return "stable"

    def _detect_plateau(self, data: list[float]) -> bool:
        """检测平台期."""
        if len(data) < 5:
            return False

        # 检查最近5个数据点的变化
        recent_data = data[-5:]
        variance = np.var(recent_data)

        threshold = self.algorithm_config["learning_curve"]["plateau_threshold"]
        return bool(variance < threshold)

    def _predict_next_performance(self, scores: list[float]) -> float:
        """预测下次表现."""
        if len(scores) < 3:
            return scores[-1] if scores else 0.5

        # 简单的线性预测
        recent_scores = scores[-5:]
        trend = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
        predicted = recent_scores[-1] + trend

        return max(0.0, min(1.0, predicted))

    def _calculate_learning_efficiency(
        self, scores: list[float], timestamps: list[datetime]
    ) -> float:
        """计算学习效率."""
        if len(scores) < 2:
            return 0.5

        # 计算单位时间内的进步
        total_improvement = scores[-1] - scores[0]
        total_time = (timestamps[-1] - timestamps[0]).total_seconds() / 3600  # 小时

        if total_time <= 0:
            return 0.5

        efficiency = total_improvement / total_time
        return max(0.0, min(1.0, efficiency + 0.5))  # 归一化到[0,1]

    def _generate_learning_suggestions(
        self, trend: str, plateau_detected: bool, learning_efficiency: float
    ) -> list[str]:
        """生成学习建议."""
        suggestions = []

        if trend == "declining":
            suggestions.append("建议回顾基础知识，巩固薄弱环节")
            suggestions.append("适当降低学习强度，避免过度疲劳")
        elif trend == "stable" and plateau_detected:
            suggestions.append("尝试新的学习方法，突破学习平台期")
            suggestions.append("增加练习难度，挑战更高水平")
        elif trend == "improving":
            suggestions.append("保持当前学习节奏，继续努力")
            suggestions.append("可以适当增加学习强度")

        if learning_efficiency < 0.3:
            suggestions.append("建议优化学习方法，提高学习效率")
        elif learning_efficiency > 0.7:
            suggestions.append("学习效率很高，可以尝试更具挑战性的内容")

        return suggestions

    def _extract_learning_features(self, student_data: dict[str, Any]) -> list[float] | None:
        """提取学习特征."""
        try:
            features = []

            # 基础特征
            features.append(student_data.get("avg_score", 0.5))
            features.append(student_data.get("total_sessions", 0) / 100.0)  # 归一化
            features.append(student_data.get("avg_session_time", 0) / 3600.0)  # 小时

            # 学习模式特征
            features.append(student_data.get("consistency_score", 0.5))
            features.append(student_data.get("improvement_rate", 0.0))
            features.append(student_data.get("difficulty_preference", 0.5))

            return features if len(features) == 6 else None

        except Exception as e:
            logger.error(f"提取学习特征失败: {str(e)}")
            return None

    def _analyze_clusters(
        self,
        features: list[list[float]],
        labels: list[int],
        student_ids: list[int],
        centers: np.ndarray,
    ) -> dict[int, dict[str, Any]]:
        """分析聚类结果."""
        clusters = {}

        for cluster_id in set(labels):
            cluster_students = [
                student_ids[i] for i, label in enumerate(labels) if label == cluster_id
            ]
            cluster_features = [
                features[i] for i, label in enumerate(labels) if label == cluster_id
            ]

            # 计算聚类统计
            avg_features = np.mean(cluster_features, axis=0)

            clusters[cluster_id] = {
                "student_count": len(cluster_students),
                "student_ids": cluster_students,
                "avg_score": avg_features[0],
                "avg_sessions": avg_features[1] * 100,
                "avg_session_time": avg_features[2] * 3600,
                "consistency": avg_features[3],
                "improvement_rate": avg_features[4],
                "difficulty_preference": avg_features[5],
            }

        return clusters

    def _describe_cluster_characteristics(
        self, clusters: dict[int, dict[str, Any]]
    ) -> dict[int, str]:
        """描述聚类特征."""
        characteristics = {}

        for cluster_id, cluster_data in clusters.items():
            desc_parts = []

            if cluster_data["avg_score"] > 0.8:
                desc_parts.append("高分学习者")
            elif cluster_data["avg_score"] > 0.6:
                desc_parts.append("中等水平学习者")
            else:
                desc_parts.append("需要帮助的学习者")

            if cluster_data["consistency"] > 0.7:
                desc_parts.append("学习规律")
            else:
                desc_parts.append("学习不规律")

            if cluster_data["improvement_rate"] > 0.1:
                desc_parts.append("进步明显")
            elif cluster_data["improvement_rate"] < -0.1:
                desc_parts.append("需要关注")

            characteristics[cluster_id] = "、".join(desc_parts)

        return characteristics

    def _identify_learning_style(
        self, profile: dict[str, Any], history: list[dict[str, Any]]
    ) -> str:
        """识别学习风格."""
        # 简化的学习风格识别
        if not history:
            return "unknown"

        # 分析学习时间偏好
        session_times = [h.get("session_duration", 0) for h in history]
        avg_session_time = sum(session_times) / len(session_times)

        # 分析学习频率
        session_count = len(history)
        days_span = 30  # 假设30天内的数据
        frequency = session_count / days_span

        if avg_session_time > 3600 and frequency < 0.5:  # 长时间，低频率
            return "intensive_learner"
        elif avg_session_time < 1800 and frequency > 1.0:  # 短时间，高频率
            return "frequent_learner"
        else:
            return "balanced_learner"

    def _analyze_current_performance(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        """分析当前表现."""
        if not history:
            return {"status": "no_data"}

        recent_history = history[-10:]  # 最近10次
        scores = [h.get("score", 0) for h in recent_history]

        return {
            "avg_score": sum(scores) / len(scores),
            "trend": self._analyze_trend(scores),
            "consistency": np.std(scores) if len(scores) > 1 else 0,
            "recent_sessions": len(recent_history),
        }

    def _identify_weak_areas(self, history: list[dict[str, Any]]) -> list[str]:
        """识别薄弱环节."""
        weak_areas = []

        # 按题型分析表现
        type_performance: dict[str, list[float]] = {}
        for record in history:
            question_type = record.get("question_type", "unknown")
            score = record.get("score", 0)

            if question_type not in type_performance:
                type_performance[question_type] = []
            type_performance[question_type].append(score)

        # 找出表现较差的题型
        for q_type, scores in type_performance.items():
            if scores and sum(scores) / len(scores) < 0.6:
                weak_areas.append(q_type)

        return weak_areas

    def _generate_personalized_recommendations(
        self,
        learning_style: str,
        performance: dict[str, Any],
        weak_areas: list[str],
    ) -> list[str]:
        """生成个性化建议."""
        recommendations = []

        # 基于学习风格的建议
        if learning_style == "intensive_learner":
            recommendations.append("建议保持长时间深度学习的习惯")
        elif learning_style == "frequent_learner":
            recommendations.append("建议保持高频率短时间学习的节奏")

        # 基于表现的建议
        if performance.get("avg_score", 0) < 0.6:
            recommendations.append("建议加强基础练习，巩固基本知识")
        elif performance.get("avg_score", 0) > 0.8:
            recommendations.append("可以尝试更有挑战性的练习")

        # 基于薄弱环节的建议
        for weak_area in weak_areas:
            recommendations.append(f"建议重点练习{weak_area}类型题目")

        return recommendations

    def _calculate_recommendation_confidence(self, history: list[dict[str, Any]]) -> float:
        """计算推荐置信度."""
        if len(history) < 5:
            return 0.3
        elif len(history) < 20:
            return 0.6
        else:
            return 0.9
