"""数据分析器 - 学习数据深度分析和洞察生成."""

import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.shared.models.enums import DifficultyLevel, TrainingType


class DataAnalyzer:
    """学习数据分析器 - 提供深度数据分析和智能洞察."""

    def __init__(self) -> None:
        # 分析配置
        self.analysis_config = {
            "min_sessions_for_trend": 5,
            "min_questions_for_analysis": 20,
            "outlier_threshold": 2.0,  # 标准差倍数
            "correlation_threshold": 0.5,
        }

    def analyze_learning_effectiveness(
        self,
        sessions: list[dict[str, Any]],
        time_window_days: int = 30,
    ) -> dict[str, Any]:
        """
        分析学习效果.

        Args:
            sessions: 会话数据列表
            time_window_days: 分析时间窗口

        Returns:
            学习效果分析结果
        """
        if not sessions:
            return {"error": "没有足够的数据进行分析"}

        # 筛选时间范围内的数据
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        filtered_sessions = [
            s for s in sessions if s.get("created_at", datetime.min) >= cutoff_date
        ]

        # 基础统计分析
        basic_stats = self._calculate_basic_statistics(filtered_sessions)

        # 学习曲线分析
        learning_curve = self._analyze_learning_curve(filtered_sessions)

        # 效率分析
        efficiency_analysis = self._analyze_efficiency_patterns(filtered_sessions)

        # 难度适应性分析
        difficulty_adaptation = self._analyze_difficulty_adaptation(filtered_sessions)

        # 时间分布分析
        time_distribution = self._analyze_time_distribution(filtered_sessions)

        # 错误模式分析
        error_patterns = self._analyze_error_patterns(filtered_sessions)

        # 生成综合评分
        effectiveness_score = self._calculate_effectiveness_score(
            basic_stats, learning_curve, efficiency_analysis
        )

        return {
            "analysis_period": f"最近{time_window_days}天",
            "data_quality": self._assess_data_quality(filtered_sessions),
            "basic_statistics": basic_stats,
            "learning_curve": learning_curve,
            "efficiency_analysis": efficiency_analysis,
            "difficulty_adaptation": difficulty_adaptation,
            "time_distribution": time_distribution,
            "error_patterns": error_patterns,
            "effectiveness_score": effectiveness_score,
            "insights": self._generate_effectiveness_insights(
                basic_stats, learning_curve, efficiency_analysis, difficulty_adaptation
            ),
        }

    def compare_performance_periods(
        self,
        sessions: list[dict[str, Any]],
        period1_days: int = 30,
        period2_days: int = 30,
    ) -> dict[str, Any]:
        """
        比较不同时期的学习表现.

        Args:
            sessions: 会话数据列表
            period1_days: 第一个时期天数（最近）
            period2_days: 第二个时期天数（之前）

        Returns:
            时期对比分析结果
        """
        now = datetime.utcnow()

        # 分割时间段
        period1_start = now - timedelta(days=period1_days)
        period2_start = period1_start - timedelta(days=period2_days)

        period1_sessions = [
            s for s in sessions if period1_start <= s.get("created_at", datetime.min) <= now
        ]

        period2_sessions = [
            s
            for s in sessions
            if period2_start <= s.get("created_at", datetime.min) < period1_start
        ]

        if not period1_sessions or not period2_sessions:
            return {"error": "时间段内数据不足进行对比"}

        # 分别分析两个时期
        period1_stats = self._calculate_basic_statistics(period1_sessions)
        period2_stats = self._calculate_basic_statistics(period2_sessions)

        # 计算变化
        changes = self._calculate_period_changes(period1_stats, period2_stats)

        # 统计显著性检验
        significance_tests = self._perform_significance_tests(period1_sessions, period2_sessions)

        # 趋势分析
        trend_analysis = self._analyze_performance_trends(period1_sessions, period2_sessions)

        return {
            "comparison_periods": {
                "recent_period": f"最近{period1_days}天",
                "previous_period": f"之前{period2_days}天",
            },
            "period1_stats": period1_stats,
            "period2_stats": period2_stats,
            "changes": changes,
            "significance_tests": significance_tests,
            "trend_analysis": trend_analysis,
            "insights": self._generate_comparison_insights(changes, significance_tests),
        }

    def analyze_question_difficulty_distribution(
        self,
        questions: list[dict[str, Any]],
        student_responses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        分析题目难度分布和学生表现.

        Args:
            questions: 题目数据列表
            student_responses: 学生回答数据列表

        Returns:
            难度分布分析结果
        """
        if not questions or not student_responses:
            return {"error": "数据不足进行分析"}

        # 按题目ID组织回答数据
        responses_by_question = defaultdict(list)
        for response in student_responses:
            question_id = response.get("question_id")
            if question_id:
                responses_by_question[question_id].append(response)

        # 分析每个题目的实际难度
        question_analysis = []
        for question in questions:
            question_id = question.get("id")
            responses = responses_by_question.get(question_id, [])

            if responses:
                analysis = self._analyze_single_question_difficulty(question, responses)
                question_analysis.append(analysis)

        # 整体难度分布
        difficulty_distribution = self._calculate_difficulty_distribution(question_analysis)

        # 难度校准建议
        calibration_suggestions = self._generate_difficulty_calibration_suggestions(
            question_analysis
        )

        # 异常题目检测
        outlier_questions = self._detect_difficulty_outliers(question_analysis)

        return {
            "total_questions_analyzed": len(question_analysis),
            "difficulty_distribution": difficulty_distribution,
            "question_analysis": question_analysis,
            "calibration_suggestions": calibration_suggestions,
            "outlier_questions": outlier_questions,
            "insights": self._generate_difficulty_insights(
                difficulty_distribution, outlier_questions
            ),
        }

    def analyze_learning_patterns_by_type(
        self,
        sessions: list[dict[str, Any]],
        training_types: list[TrainingType] | None = None,
    ) -> dict[str, Any]:
        """
        按训练类型分析学习模式.

        Args:
            sessions: 会话数据列表
            training_types: 要分析的训练类型列表

        Returns:
            按类型的学习模式分析
        """
        if not sessions:
            return {"error": "没有数据进行分析"}

        if training_types is None:
            training_types = list(TrainingType)

        # 按训练类型分组
        sessions_by_type = defaultdict(list)
        for session in sessions:
            training_type = session.get("training_type")
            if training_type in training_types:
                sessions_by_type[training_type].append(session)

        # 分析每种类型
        type_analysis = {}
        for training_type in training_types:
            type_sessions = sessions_by_type[training_type]
            if type_sessions:
                analysis = self._analyze_single_type_patterns(training_type, type_sessions)
                type_analysis[training_type.value] = analysis

        # 跨类型比较
        cross_type_comparison = self._compare_across_types(type_analysis)

        # 类型推荐
        type_recommendations = self._generate_type_recommendations(type_analysis)

        return {
            "analyzed_types": [t.value for t in training_types],
            "type_analysis": type_analysis,
            "cross_type_comparison": cross_type_comparison,
            "type_recommendations": type_recommendations,
            "insights": self._generate_type_pattern_insights(type_analysis, cross_type_comparison),
        }

    def detect_learning_anomalies(
        self,
        sessions: list[dict[str, Any]],
        student_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        检测学习异常和潜在问题.

        Args:
            sessions: 会话数据列表
            student_profile: 学生档案信息

        Returns:
            异常检测结果
        """
        if len(sessions) < self.analysis_config["min_sessions_for_trend"]:
            return {"error": "数据不足进行异常检测"}

        # 性能异常检测
        performance_anomalies = self._detect_performance_anomalies(sessions)

        # 时间模式异常检测
        time_anomalies = self._detect_time_pattern_anomalies(sessions)

        # 学习行为异常检测
        behavior_anomalies = self._detect_behavior_anomalies(sessions)

        # 进度异常检测
        progress_anomalies = self._detect_progress_anomalies(sessions)

        # 综合风险评估
        risk_assessment = self._assess_learning_risks(
            performance_anomalies,
            time_anomalies,
            behavior_anomalies,
            progress_anomalies,
        )

        return {
            "anomaly_detection_summary": {
                "total_sessions_analyzed": len(sessions),
                "anomalies_detected": (
                    len(performance_anomalies)
                    + len(time_anomalies)
                    + len(behavior_anomalies)
                    + len(progress_anomalies)
                ),
            },
            "performance_anomalies": performance_anomalies,
            "time_anomalies": time_anomalies,
            "behavior_anomalies": behavior_anomalies,
            "progress_anomalies": progress_anomalies,
            "risk_assessment": risk_assessment,
            "recommendations": self._generate_anomaly_recommendations(
                performance_anomalies,
                time_anomalies,
                behavior_anomalies,
                progress_anomalies,
            ),
        }

    def generate_predictive_insights(
        self,
        sessions: list[dict[str, Any]],
        prediction_horizon_days: int = 30,
    ) -> dict[str, Any]:
        """
        生成预测性洞察.

        Args:
            sessions: 会话数据列表
            prediction_horizon_days: 预测时间范围

        Returns:
            预测性洞察结果
        """
        if len(sessions) < 10:
            return {"error": "数据不足进行预测分析"}

        # 学习轨迹预测
        trajectory_prediction = self._predict_learning_trajectory(sessions)

        # 表现预测
        performance_prediction = self._predict_future_performance(sessions)

        # 风险预测
        risk_prediction = self._predict_learning_risks(sessions)

        # 目标达成预测
        goal_achievement_prediction = self._predict_goal_achievement(sessions)

        # 个性化建议
        personalized_recommendations = self._generate_predictive_recommendations(
            trajectory_prediction, performance_prediction, risk_prediction
        )

        return {
            "prediction_horizon": f"{prediction_horizon_days}天",
            "confidence_level": self._calculate_prediction_confidence(sessions),
            "trajectory_prediction": trajectory_prediction,
            "performance_prediction": performance_prediction,
            "risk_prediction": risk_prediction,
            "goal_achievement_prediction": goal_achievement_prediction,
            "personalized_recommendations": personalized_recommendations,
        }

    # ==================== 私有辅助方法 ====================

    def _calculate_basic_statistics(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """计算基础统计数据."""
        if not sessions:
            return {}

        # 提取关键指标
        accuracies = [s.get("accuracy_rate", 0) for s in sessions]
        times = [
            s.get("total_time_seconds", 0) for s in sessions if s.get("total_time_seconds", 0) > 0
        ]
        questions = [s.get("total_questions", 0) for s in sessions]

        return {
            "session_count": len(sessions),
            "accuracy": {
                "mean": statistics.mean(accuracies) if accuracies else 0,
                "median": statistics.median(accuracies) if accuracies else 0,
                "std_dev": statistics.stdev(accuracies) if len(accuracies) > 1 else 0,
                "min": min(accuracies) if accuracies else 0,
                "max": max(accuracies) if accuracies else 0,
            },
            "time_per_session": {
                "mean": statistics.mean(times) if times else 0,
                "median": statistics.median(times) if times else 0,
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            },
            "questions_per_session": {
                "mean": statistics.mean(questions) if questions else 0,
                "median": statistics.median(questions) if questions else 0,
                "total": sum(questions),
            },
        }

    def _analyze_learning_curve(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析学习曲线."""
        if len(sessions) < 3:
            return {"trend": "数据不足"}

        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))

        # 计算移动平均
        window_size = min(5, len(sorted_sessions) // 3)
        moving_averages = []

        for i in range(len(sorted_sessions) - window_size + 1):
            window_sessions = sorted_sessions[i : i + window_size]
            avg_accuracy = sum(s.get("accuracy_rate", 0) for s in window_sessions) / window_size
            moving_averages.append(
                {
                    "session_index": i + window_size - 1,
                    "accuracy": avg_accuracy,
                    "date": window_sessions[-1].get("created_at"),
                }
            )

        # 计算趋势
        if len(moving_averages) >= 2:
            first_avg = moving_averages[0]["accuracy"]
            last_avg = moving_averages[-1]["accuracy"]
            trend_slope = (last_avg - first_avg) / len(moving_averages)

            if trend_slope > 0.01:
                trend = "上升"
            elif trend_slope < -0.01:
                trend = "下降"
            else:
                trend = "稳定"
        else:
            trend = "数据不足"

        return {
            "trend": trend,
            "trend_slope": trend_slope if "trend_slope" in locals() else 0,
            "moving_averages": moving_averages,
            "learning_velocity": self._calculate_learning_velocity(moving_averages),
        }

    def _calculate_learning_velocity(self, moving_averages: list[dict[str, Any]]) -> float:
        """计算学习速度."""
        if len(moving_averages) < 2:
            return 0.0

        # 计算准确率变化速度
        velocities = []
        for i in range(1, len(moving_averages)):
            prev_acc = moving_averages[i - 1]["accuracy"]
            curr_acc = moving_averages[i]["accuracy"]
            velocity = curr_acc - prev_acc
            velocities.append(velocity)

        return statistics.mean(velocities) if velocities else 0.0

    def _analyze_efficiency_patterns(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析效率模式."""
        if not sessions:
            return {}

        # 计算效率指标
        efficiency_scores = []
        for session in sessions:
            accuracy = session.get("accuracy_rate", 0)
            time_per_question = session.get("avg_time_per_question", 0)

            if time_per_question > 0:
                # 效率 = 准确率 / 相对时间
                efficiency = accuracy / (time_per_question / 60.0)  # 标准化到分钟
                efficiency_scores.append(efficiency)

        if not efficiency_scores:
            return {"error": "无法计算效率"}

        # 效率趋势
        efficiency_trend = self._calculate_trend(efficiency_scores)

        # 效率分布
        efficiency_quartiles = self._calculate_quartiles(efficiency_scores)

        return {
            "average_efficiency": statistics.mean(efficiency_scores),
            "efficiency_trend": efficiency_trend,
            "efficiency_distribution": efficiency_quartiles,
            "efficiency_consistency": (
                1.0 - (statistics.stdev(efficiency_scores) / statistics.mean(efficiency_scores))
                if len(efficiency_scores) > 1 and statistics.mean(efficiency_scores) > 0
                else 0
            ),
        }

    def _analyze_difficulty_adaptation(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析难度适应性."""
        # 按难度分组
        difficulty_groups = defaultdict(list)
        for session in sessions:
            difficulty = session.get("difficulty_level", DifficultyLevel.ELEMENTARY)
            difficulty_groups[difficulty].append(session.get("accuracy_rate", 0))

        # 计算各难度的表现
        difficulty_performance = {}
        for difficulty, accuracies in difficulty_groups.items():
            if accuracies:
                difficulty_name = (
                    difficulty.value if hasattr(difficulty, "value") else str(difficulty)
                )
                difficulty_performance[difficulty_name] = {
                    "session_count": len(accuracies),
                    "average_accuracy": statistics.mean(accuracies),
                    "consistency": (
                        1.0 - (statistics.stdev(accuracies) / statistics.mean(accuracies))
                        if len(accuracies) > 1 and statistics.mean(accuracies) > 0
                        else 0
                    ),
                }

        # 适应性评分
        adaptation_score = self._calculate_adaptation_score(difficulty_performance)

        return {
            "difficulty_performance": difficulty_performance,
            "adaptation_score": adaptation_score,
            "optimal_difficulty": self._suggest_optimal_difficulty(difficulty_performance),
        }

    def _calculate_adaptation_score(
        self, difficulty_performance: dict[str, dict[str, Any]]
    ) -> float:
        """计算难度适应性评分."""
        if not difficulty_performance:
            return 0.0

        # 基于各难度表现的综合评分
        total_score = 0.0
        total_weight = 0.0

        difficulty_weights = {
            "ELEMENTARY": 1.0,
            "INTERMEDIATE": 1.2,
            "ADVANCED": 1.5,
            "EXPERT": 2.0,
        }

        for difficulty, performance in difficulty_performance.items():
            weight = difficulty_weights.get(difficulty, 1.0)
            accuracy = performance["average_accuracy"]
            consistency = performance["consistency"]

            # 综合评分 = 准确率 * 一致性 * 难度权重
            score = accuracy * consistency * weight
            total_score += score
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _suggest_optimal_difficulty(self, difficulty_performance: dict[str, dict[str, Any]]) -> str:
        """建议最优难度."""
        if not difficulty_performance:
            return "ELEMENTARY"

        # 找到准确率在70%-85%之间的最高难度
        optimal_candidates = []
        for difficulty, performance in difficulty_performance.items():
            accuracy = performance["average_accuracy"]
            if 0.7 <= accuracy <= 0.85:
                optimal_candidates.append((difficulty, accuracy))

        if optimal_candidates:
            # 选择准确率最接近80%的难度
            optimal_candidates.sort(key=lambda x: abs(x[1] - 0.8))
            return optimal_candidates[0][0]

        # 如果没有合适的，选择准确率最高的
        best_difficulty = max(
            difficulty_performance.keys(),
            key=lambda d: difficulty_performance[d]["average_accuracy"],
        )
        return best_difficulty

    def _analyze_time_distribution(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析时间分布."""
        hour_counts: Counter[int] = Counter()
        weekday_counts: Counter[int] = Counter()
        session_durations = []

        for session in sessions:
            created_at = session.get("created_at")
            if created_at:
                hour_counts[created_at.hour] += 1
                weekday_counts[created_at.weekday()] += 1

            duration = session.get("total_time_seconds", 0)
            if duration > 0:
                session_durations.append(duration / 60.0)  # 转换为分钟

        # 最活跃时段
        peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
        peak_weekday = weekday_counts.most_common(1)[0][0] if weekday_counts else 0

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        return {
            "peak_learning_hour": peak_hour,
            "peak_learning_day": weekday_names[peak_weekday],
            "hour_distribution": dict(hour_counts),
            "weekday_distribution": {weekday_names[k]: v for k, v in weekday_counts.items()},
            "session_duration_stats": {
                "average_minutes": (statistics.mean(session_durations) if session_durations else 0),
                "median_minutes": (
                    statistics.median(session_durations) if session_durations else 0
                ),
            },
        }

    def _analyze_error_patterns(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析错误模式."""
        total_questions = sum(s.get("total_questions", 0) for s in sessions)
        total_correct = sum(s.get("correct_answers", 0) for s in sessions)
        total_errors = total_questions - total_correct

        if total_questions == 0:
            return {"error_rate": 0.0}

        error_rate = total_errors / total_questions

        # 错误趋势分析
        error_rates_by_session = []
        for session in sessions:
            session_questions = session.get("total_questions", 0)
            session_correct = session.get("correct_answers", 0)
            if session_questions > 0:
                session_error_rate = (session_questions - session_correct) / session_questions
                error_rates_by_session.append(session_error_rate)

        error_trend = self._calculate_trend(error_rates_by_session)

        return {
            "overall_error_rate": error_rate,
            "error_trend": error_trend,
            "error_consistency": (
                statistics.stdev(error_rates_by_session) if len(error_rates_by_session) > 1 else 0
            ),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """计算趋势."""
        if len(values) < 2:
            return "数据不足"

        # 简单线性趋势
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "稳定"

        slope = numerator / denominator

        if slope > 0.01:
            return "上升"
        elif slope < -0.01:
            return "下降"
        else:
            return "稳定"

    def _calculate_quartiles(self, values: list[float]) -> dict[str, float]:
        """计算四分位数."""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "q1": sorted_values[n // 4] if n >= 4 else sorted_values[0],
            "q2": statistics.median(sorted_values),
            "q3": sorted_values[3 * n // 4] if n >= 4 else sorted_values[-1],
        }

    def _calculate_effectiveness_score(
        self,
        basic_stats: dict[str, Any],
        learning_curve: dict[str, Any],
        efficiency_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """计算学习效果综合评分."""
        # 准确率评分 (40%)
        accuracy_score = basic_stats.get("accuracy", {}).get("mean", 0) * 0.4

        # 学习趋势评分 (30%)
        trend = learning_curve.get("trend", "稳定")
        trend_scores = {"上升": 0.3, "稳定": 0.2, "下降": 0.1, "数据不足": 0.15}
        trend_score = trend_scores.get(trend, 0.15)

        # 效率评分 (30%)
        efficiency = efficiency_analysis.get("average_efficiency", 0)
        efficiency_score = min(efficiency / 2.0, 1.0) * 0.3  # 标准化到0.3

        total_score = accuracy_score + trend_score + efficiency_score

        # 评级
        if total_score >= 0.8:
            rating = "优秀"
        elif total_score >= 0.6:
            rating = "良好"
        elif total_score >= 0.4:
            rating = "一般"
        else:
            rating = "需要改进"

        return {
            "total_score": total_score,
            "rating": rating,
            "component_scores": {
                "accuracy": accuracy_score,
                "trend": trend_score,
                "efficiency": efficiency_score,
            },
        }

    def _generate_effectiveness_insights(
        self,
        basic_stats: dict[str, Any],
        learning_curve: dict[str, Any],
        efficiency_analysis: dict[str, Any],
        difficulty_adaptation: dict[str, Any],
    ) -> list[str]:
        """生成学习效果洞察."""
        insights = []

        # 准确率洞察
        avg_accuracy = basic_stats.get("accuracy", {}).get("mean", 0)
        if avg_accuracy >= 0.85:
            insights.append("准确率表现优秀，学习效果显著")
        elif avg_accuracy >= 0.7:
            insights.append("准确率良好，继续保持")
        else:
            insights.append("准确率有待提高，建议调整学习策略")

        # 趋势洞察
        trend = learning_curve.get("trend", "")
        if trend == "上升":
            insights.append("学习进步明显，保持当前方法")
        elif trend == "下降":
            insights.append("近期表现下降，需要关注学习状态")

        # 效率洞察
        efficiency = efficiency_analysis.get("average_efficiency", 0)
        if efficiency >= 1.5:
            insights.append("学习效率很高，时间利用充分")
        elif efficiency < 0.8:
            insights.append("学习效率偏低，可以提高答题速度")

        # 适应性洞察
        adaptation_score = difficulty_adaptation.get("adaptation_score", 0)
        if adaptation_score >= 0.8:
            insights.append("难度适应性良好，挑战合适")
        elif adaptation_score < 0.5:
            insights.append("建议调整难度设置，找到最适合的挑战水平")

        return insights

    def _assess_data_quality(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """评估数据质量."""
        total_sessions = len(sessions)

        # 检查数据完整性
        complete_sessions = 0
        for session in sessions:
            if all(key in session for key in ["accuracy_rate", "total_questions", "created_at"]):
                complete_sessions += 1

        completeness = complete_sessions / total_sessions if total_sessions > 0 else 0

        # 数据量评估
        if total_sessions >= 20:
            volume_quality = "充足"
        elif total_sessions >= 10:
            volume_quality = "适中"
        elif total_sessions >= 5:
            volume_quality = "较少"
        else:
            volume_quality = "不足"

        return {
            "total_sessions": total_sessions,
            "completeness_rate": completeness,
            "volume_quality": volume_quality,
            "analysis_reliability": (
                "高"
                if completeness >= 0.8 and total_sessions >= 10
                else "中"
                if completeness >= 0.6
                else "低"
            ),
        }

    def _calculate_period_changes(
        self, period1_stats: dict[str, Any], period2_stats: dict[str, Any]
    ) -> dict[str, Any]:
        """计算时期变化."""
        # 准确率变化
        acc1 = period1_stats.get("accuracy", {}).get("mean", 0)
        acc2 = period2_stats.get("accuracy", {}).get("mean", 0)
        acc_change = ((acc1 - acc2) / acc2 * 100) if acc2 > 0 else 0

        # 会话数量变化
        sessions1 = period1_stats.get("session_count", 0)
        sessions2 = period2_stats.get("session_count", 0)
        session_change = ((sessions1 - sessions2) / sessions2 * 100) if sessions2 > 0 else 0

        # 题目数量变化
        questions1 = period1_stats.get("questions_per_session", {}).get("total", 0)
        questions2 = period2_stats.get("questions_per_session", {}).get("total", 0)
        question_change = ((questions1 - questions2) / questions2 * 100) if questions2 > 0 else 0

        return {
            "accuracy_change_percent": acc_change,
            "session_count_change_percent": session_change,
            "question_count_change_percent": question_change,
            "overall_trend": ("改善" if acc_change > 5 else "下降" if acc_change < -5 else "稳定"),
        }

    def _perform_significance_tests(
        self,
        period1_sessions: list[dict[str, Any]],
        period2_sessions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """执行统计显著性检验."""
        # 提取准确率数据
        acc1 = [s.get("accuracy_rate", 0) for s in period1_sessions]
        acc2 = [s.get("accuracy_rate", 0) for s in period2_sessions]

        if len(acc1) < 3 or len(acc2) < 3:
            return {"test": "样本量不足", "significant": False}

        # 简单的t检验近似
        mean1, mean2 = statistics.mean(acc1), statistics.mean(acc2)
        std1 = statistics.stdev(acc1) if len(acc1) > 1 else 0
        std2 = statistics.stdev(acc2) if len(acc2) > 1 else 0

        # 计算标准误差
        se = ((std1**2 / len(acc1)) + (std2**2 / len(acc2))) ** 0.5

        if se > 0:
            t_stat = abs(mean1 - mean2) / se
            # 简化的显著性判断（t > 2 近似为显著）
            significant = t_stat > 2.0
        else:
            significant = False

        return {
            "test": "准确率差异检验",
            "t_statistic": t_stat if "t_stat" in locals() else 0,
            "significant": significant,
            "interpretation": "显著差异" if significant else "无显著差异",
        }

    def _analyze_performance_trends(
        self,
        period1_sessions: list[dict[str, Any]],
        period2_sessions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """分析表现趋势."""

        # 计算各时期内部趋势
        def calculate_internal_trend(sessions: list[dict[str, Any]]) -> str:
            if len(sessions) < 3:
                return "数据不足"

            sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))
            accuracies = [s.get("accuracy_rate", 0) for s in sorted_sessions]

            first_half = accuracies[: len(accuracies) // 2]
            second_half = accuracies[len(accuracies) // 2 :]

            avg1 = statistics.mean(first_half)
            avg2 = statistics.mean(second_half)

            if avg2 > avg1 + 0.05:
                return "上升"
            elif avg2 < avg1 - 0.05:
                return "下降"
            else:
                return "稳定"

        period1_trend = calculate_internal_trend(period1_sessions)
        period2_trend = calculate_internal_trend(period2_sessions)

        return {
            "recent_period_trend": period1_trend,
            "previous_period_trend": period2_trend,
            "trend_consistency": period1_trend == period2_trend,
        }

    def _generate_comparison_insights(
        self, changes: dict[str, Any], significance_tests: dict[str, Any]
    ) -> list[str]:
        """生成对比洞察."""
        insights = []

        # 准确率变化洞察
        acc_change = changes.get("accuracy_change_percent", 0)
        significant = significance_tests.get("significant", False)

        if significant:
            if acc_change > 10:
                insights.append("准确率显著提升，学习效果明显改善")
            elif acc_change < -10:
                insights.append("准确率显著下降，需要调整学习策略")
        else:
            insights.append("两个时期表现基本稳定，无显著变化")

        # 活跃度变化洞察
        session_change = changes.get("session_count_change_percent", 0)
        if session_change > 20:
            insights.append("学习频率明显增加，学习积极性提高")
        elif session_change < -20:
            insights.append("学习频率有所下降，建议保持学习习惯")

        return insights

    def _analyze_single_question_difficulty(
        self, question: dict[str, Any], responses: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """分析单个题目的实际难度."""
        if not responses:
            return {"question_id": question.get("id"), "error": "无回答数据"}

        # 计算统计指标
        correct_count = sum(1 for r in responses if r.get("is_correct", False))
        total_count = len(responses)
        actual_difficulty = 1.0 - (correct_count / total_count)  # 错误率作为实际难度

        # 计算平均用时
        times = [r.get("time_spent", 0) for r in responses if r.get("time_spent", 0) > 0]
        avg_time = statistics.mean(times) if times else 0

        # 标记难度
        declared_difficulty = question.get("difficulty_level", DifficultyLevel.ELEMENTARY)

        return {
            "question_id": question.get("id"),
            "question_type": question.get("question_type"),
            "declared_difficulty": (
                declared_difficulty.value
                if hasattr(declared_difficulty, "value")
                else str(declared_difficulty)
            ),
            "actual_difficulty": actual_difficulty,
            "accuracy_rate": correct_count / total_count,
            "response_count": total_count,
            "average_time_seconds": avg_time,
            "difficulty_alignment": self._assess_difficulty_alignment(
                declared_difficulty, actual_difficulty
            ),
        }

    def _assess_difficulty_alignment(self, declared: DifficultyLevel, actual: float) -> str:
        """评估难度对齐程度."""
        # 将声明难度转换为数值
        difficulty_mapping = {
            DifficultyLevel.BEGINNER: 0.1,
            DifficultyLevel.ELEMENTARY: 0.2,
            DifficultyLevel.INTERMEDIATE: 0.4,
            DifficultyLevel.UPPER_INTERMEDIATE: 0.6,
            DifficultyLevel.ADVANCED: 0.8,
        }

        declared_score = difficulty_mapping.get(declared, 0.4)

        # 计算差异
        diff = abs(declared_score - actual)

        if diff <= 0.1:
            return "对齐良好"
        elif diff <= 0.2:
            return "基本对齐"
        elif diff <= 0.3:
            return "存在偏差"
        else:
            return "严重偏差"

    def _calculate_difficulty_distribution(
        self, question_analysis: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """计算难度分布."""
        if not question_analysis:
            return {}

        # 按声明难度分组
        declared_groups = defaultdict(list)
        for analysis in question_analysis:
            declared = analysis.get("declared_difficulty", "ELEMENTARY")
            actual = analysis.get("actual_difficulty", 0)
            declared_groups[declared].append(actual)

        # 计算各组统计
        distribution = {}
        for difficulty, actual_difficulties in declared_groups.items():
            distribution[difficulty] = {
                "count": len(actual_difficulties),
                "avg_actual_difficulty": statistics.mean(actual_difficulties),
                "std_dev": (
                    statistics.stdev(actual_difficulties) if len(actual_difficulties) > 1 else 0
                ),
            }

        return distribution

    def _generate_difficulty_calibration_suggestions(
        self, question_analysis: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成难度校准建议."""
        suggestions = []

        for analysis in question_analysis:
            alignment = analysis.get("difficulty_alignment", "")
            if alignment in ["存在偏差", "严重偏差"]:
                question_id = analysis.get("question_id")
                declared = analysis.get("declared_difficulty")
                actual = analysis.get("actual_difficulty", 0)

                # 建议新难度
                if actual < 0.3:
                    suggested = "ELEMENTARY"
                elif actual < 0.5:
                    suggested = "INTERMEDIATE"
                elif actual < 0.7:
                    suggested = "ADVANCED"
                else:
                    suggested = "EXPERT"

                suggestions.append(
                    {
                        "question_id": question_id,
                        "current_difficulty": declared,
                        "suggested_difficulty": suggested,
                        "reason": f"实际难度{actual:.2f}与声明难度不匹配",
                    }
                )

        return suggestions

    def _detect_difficulty_outliers(
        self, question_analysis: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """检测难度异常题目."""
        if not question_analysis:
            return []

        # 计算整体难度分布
        actual_difficulties = [a.get("actual_difficulty", 0) for a in question_analysis]
        mean_difficulty = statistics.mean(actual_difficulties)
        std_difficulty = (
            statistics.stdev(actual_difficulties) if len(actual_difficulties) > 1 else 0
        )

        outliers = []
        threshold = self.analysis_config["outlier_threshold"]

        for analysis in question_analysis:
            actual = analysis.get("actual_difficulty", 0)
            z_score = abs(actual - mean_difficulty) / std_difficulty if std_difficulty > 0 else 0

            if z_score > threshold:
                outliers.append(
                    {
                        **analysis,
                        "z_score": z_score,
                        "outlier_type": "过难" if actual > mean_difficulty else "过易",
                    }
                )

        return outliers

    def _generate_difficulty_insights(
        self,
        difficulty_distribution: dict[str, Any],
        outlier_questions: list[dict[str, Any]],
    ) -> list[str]:
        """生成难度分析洞察."""
        insights = []

        # 分布洞察
        if difficulty_distribution:
            total_questions = sum(d.get("count", 0) for d in difficulty_distribution.values())
            if total_questions > 0:
                insights.append(f"共分析{total_questions}道题目的难度分布")

        # 异常洞察
        outlier_count = len(outlier_questions)
        if outlier_count > 0:
            insights.append(f"发现{outlier_count}道难度异常题目，建议重新校准")
        else:
            insights.append("题目难度分布合理，无明显异常")

        # 校准建议
        too_easy = sum(1 for q in outlier_questions if q.get("outlier_type") == "过易")
        too_hard = sum(1 for q in outlier_questions if q.get("outlier_type") == "过难")

        if too_easy > 0:
            insights.append(f"{too_easy}道题目过于简单，建议提升难度")
        if too_hard > 0:
            insights.append(f"{too_hard}道题目过于困难，建议降低难度")

        return insights

    def _analyze_single_type_patterns(
        self, training_type: TrainingType, sessions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """分析单个训练类型的模式."""
        if not sessions:
            return {"error": "无数据"}

        # 基础统计
        basic_stats = self._calculate_basic_statistics(sessions)

        # 进步趋势
        progress_trend = self._analyze_learning_curve(sessions)

        # 时间模式
        time_patterns = self._analyze_time_distribution(sessions)

        return {
            "training_type": training_type.value,
            "session_count": len(sessions),
            "basic_statistics": basic_stats,
            "progress_trend": progress_trend,
            "time_patterns": time_patterns,
            "performance_rating": self._rate_type_performance(basic_stats, progress_trend),
        }

    def _rate_type_performance(
        self, basic_stats: dict[str, Any], progress_trend: dict[str, Any]
    ) -> str:
        """评级训练类型表现."""
        avg_accuracy = basic_stats.get("accuracy", {}).get("mean", 0)
        trend = progress_trend.get("trend", "稳定")

        if avg_accuracy >= 0.85 and trend == "上升":
            return "优秀"
        elif avg_accuracy >= 0.7 and trend in ["上升", "稳定"]:
            return "良好"
        elif avg_accuracy >= 0.6:
            return "一般"
        else:
            return "需要改进"

    def _compare_across_types(self, type_analysis: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """跨类型比较."""
        if len(type_analysis) < 2:
            return {"error": "类型数量不足进行比较"}

        # 找出最佳和最差表现
        type_scores = {}
        for type_name, analysis in type_analysis.items():
            accuracy = analysis.get("basic_statistics", {}).get("accuracy", {}).get("mean", 0)
            type_scores[type_name] = accuracy

        best_type = max(type_scores.keys(), key=lambda k: type_scores[k])
        worst_type = min(type_scores.keys(), key=lambda k: type_scores[k])

        # 计算差异
        performance_gap = type_scores[best_type] - type_scores[worst_type]

        return {
            "best_performing_type": best_type,
            "worst_performing_type": worst_type,
            "performance_gap": performance_gap,
            "type_rankings": sorted(type_scores.items(), key=lambda x: x[1], reverse=True),
        }

    def _generate_type_recommendations(self, type_analysis: dict[str, dict[str, Any]]) -> list[str]:
        """生成类型推荐."""
        recommendations = []

        for type_name, analysis in type_analysis.items():
            rating = analysis.get("performance_rating", "")
            accuracy = analysis.get("basic_statistics", {}).get("accuracy", {}).get("mean", 0)

            if rating == "需要改进":
                recommendations.append(f"建议加强{type_name}训练，当前准确率{accuracy:.1%}")
            elif rating == "优秀":
                recommendations.append(f"{type_name}表现优秀，可以挑战更高难度")

        return recommendations

    def _generate_type_pattern_insights(
        self,
        type_analysis: dict[str, dict[str, Any]],
        cross_type_comparison: dict[str, Any],
    ) -> list[str]:
        """生成类型模式洞察."""
        insights = []

        # 整体洞察
        total_types = len(type_analysis)
        insights.append(f"分析了{total_types}种训练类型的学习模式")

        # 比较洞察
        if "best_performing_type" in cross_type_comparison:
            best_type = cross_type_comparison["best_performing_type"]
            worst_type = cross_type_comparison["worst_performing_type"]
            gap = cross_type_comparison.get("performance_gap", 0)

            insights.append(f"最擅长{best_type}，最需要改进{worst_type}")
            if gap > 0.2:
                insights.append("不同类型间表现差异较大，建议针对性练习")

        return insights

    def _detect_performance_anomalies(self, sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """检测表现异常."""
        if len(sessions) < 5:
            return []

        # 计算准确率的统计特征
        accuracies = [s.get("accuracy_rate", 0) for s in sessions]
        mean_acc = statistics.mean(accuracies)
        std_acc = statistics.stdev(accuracies) if len(accuracies) > 1 else 0

        anomalies = []
        threshold = self.analysis_config["outlier_threshold"]

        for i, session in enumerate(sessions):
            accuracy = session.get("accuracy_rate", 0)
            if std_acc > 0:
                z_score = abs(accuracy - mean_acc) / std_acc
                if z_score > threshold:
                    anomalies.append(
                        {
                            "session_index": i,
                            "session_date": session.get("created_at"),
                            "accuracy": accuracy,
                            "z_score": z_score,
                            "anomaly_type": ("表现异常低" if accuracy < mean_acc else "表现异常高"),
                        }
                    )

        return anomalies

    def _detect_time_pattern_anomalies(
        self, sessions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """检测时间模式异常."""
        anomalies: list[dict[str, Any]] = []

        # 检测学习时间间隔异常
        session_dates = [s["created_at"] for s in sessions if s.get("created_at") is not None]
        if len(session_dates) < 3:
            return anomalies

        session_dates.sort()
        intervals = []
        for i in range(1, len(session_dates)):
            interval = (session_dates[i] - session_dates[i - 1]).total_seconds() / 3600  # 小时
            intervals.append(interval)

        if len(intervals) > 1:
            mean_interval = statistics.mean(intervals)
            std_interval = statistics.stdev(intervals)

            for i, interval in enumerate(intervals):
                if std_interval > 0:
                    z_score = abs(interval - mean_interval) / std_interval
                    if z_score > 2.0:  # 异常间隔
                        anomalies.append(
                            {
                                "interval_index": i,
                                "interval_hours": interval,
                                "z_score": z_score,
                                "anomaly_type": "学习间隔异常",
                            }
                        )

        return anomalies

    def _detect_behavior_anomalies(self, sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """检测行为异常."""
        anomalies = []

        # 检测答题时间异常
        times_per_question = []
        for session in sessions:
            total_time = session.get("total_time_seconds", 0)
            total_questions = session.get("total_questions", 0)
            if total_questions > 0 and total_time > 0:
                avg_time = total_time / total_questions
                times_per_question.append(avg_time)

        if len(times_per_question) > 1:
            mean_time = statistics.mean(times_per_question)
            std_time = statistics.stdev(times_per_question)

            for i, time_per_q in enumerate(times_per_question):
                if std_time > 0:
                    z_score = abs(time_per_q - mean_time) / std_time
                    if z_score > 2.0:
                        anomalies.append(
                            {
                                "session_index": i,
                                "avg_time_per_question": time_per_q,
                                "z_score": z_score,
                                "anomaly_type": "答题时间异常",
                            }
                        )

        return anomalies

    def _detect_progress_anomalies(self, sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """检测进度异常."""
        anomalies: list[dict[str, Any]] = []

        if len(sessions) < 5:
            return anomalies

        # 检测准确率突然下降
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))

        for i in range(2, len(sorted_sessions)):
            current_acc = sorted_sessions[i].get("accuracy_rate", 0)
            prev_acc = sorted_sessions[i - 1].get("accuracy_rate", 0)
            prev_prev_acc = sorted_sessions[i - 2].get("accuracy_rate", 0)

            # 连续两次下降且幅度较大
            if (
                prev_acc < prev_prev_acc
                and current_acc < prev_acc
                and (prev_prev_acc - current_acc) > 0.2
            ):
                anomalies.append(
                    {
                        "session_index": i,
                        "session_date": sorted_sessions[i].get("created_at"),
                        "accuracy_drop": prev_prev_acc - current_acc,
                        "anomaly_type": "进度倒退",
                    }
                )

        return anomalies

    def _assess_learning_risks(
        self,
        performance_anomalies: list[dict[str, Any]],
        time_anomalies: list[dict[str, Any]],
        behavior_anomalies: list[dict[str, Any]],
        progress_anomalies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """评估学习风险."""
        total_anomalies = (
            len(performance_anomalies)
            + len(time_anomalies)
            + len(behavior_anomalies)
            + len(progress_anomalies)
        )

        # 风险等级
        if total_anomalies >= 5:
            risk_level = "高"
        elif total_anomalies >= 3:
            risk_level = "中"
        elif total_anomalies >= 1:
            risk_level = "低"
        else:
            risk_level = "无"

        # 主要风险因素
        risk_factors = []
        if len(performance_anomalies) >= 2:
            risk_factors.append("表现不稳定")
        if len(time_anomalies) >= 2:
            risk_factors.append("学习时间不规律")
        if len(behavior_anomalies) >= 2:
            risk_factors.append("学习行为异常")
        if len(progress_anomalies) >= 1:
            risk_factors.append("学习进度倒退")

        return {
            "risk_level": risk_level,
            "total_anomalies": total_anomalies,
            "risk_factors": risk_factors,
            "intervention_needed": risk_level in ["高", "中"],
        }

    def _generate_anomaly_recommendations(
        self,
        performance_anomalies: list[dict[str, Any]],
        time_anomalies: list[dict[str, Any]],
        behavior_anomalies: list[dict[str, Any]],
        progress_anomalies: list[dict[str, Any]],
    ) -> list[str]:
        """生成异常处理建议."""
        recommendations = []

        if performance_anomalies:
            recommendations.append("表现波动较大，建议保持稳定的学习状态和环境")

        if time_anomalies:
            recommendations.append("学习时间不规律，建议制定固定的学习计划")

        if behavior_anomalies:
            recommendations.append("答题时间异常，建议调整答题节奏和策略")

        if progress_anomalies:
            recommendations.append("学习进度有倒退，建议回顾基础知识并调整难度")

        if not any(
            [
                performance_anomalies,
                time_anomalies,
                behavior_anomalies,
                progress_anomalies,
            ]
        ):
            recommendations.append("学习状态良好，继续保持当前的学习方式")

        return recommendations

    def _predict_learning_trajectory(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """预测学习轨迹."""
        if len(sessions) < 5:
            return {"error": "数据不足进行预测"}

        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))

        # 提取准确率趋势
        accuracies = [s.get("accuracy_rate", 0) for s in sorted_sessions]

        # 简单线性预测
        n = len(accuracies)
        x_values = list(range(n))

        # 计算线性回归参数
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(accuracies)

        numerator = sum((x_values[i] - x_mean) * (accuracies[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        if denominator > 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean

            # 预测未来5次会话
            future_predictions = []
            for i in range(1, 6):
                future_x = n + i
                predicted_accuracy = intercept + slope * future_x
                predicted_accuracy = max(0.0, min(1.0, predicted_accuracy))  # 限制在合理范围
                future_predictions.append(predicted_accuracy)

            return {
                "trend_slope": slope,
                "current_trajectory": (
                    "上升" if slope > 0.01 else "下降" if slope < -0.01 else "稳定"
                ),
                "future_predictions": future_predictions,
                "confidence": self._calculate_prediction_confidence(sessions),
            }

        return {"error": "无法计算趋势"}

    def _predict_future_performance(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """预测未来表现."""
        if len(sessions) < 3:
            return {"error": "数据不足"}

        recent_sessions = sessions[-5:]  # 最近5次会话
        recent_accuracy = statistics.mean([s.get("accuracy_rate", 0) for s in recent_sessions])

        # 基于最近表现预测
        if recent_accuracy >= 0.85:
            predicted_performance = "优秀"
            improvement_probability = 0.3
        elif recent_accuracy >= 0.7:
            predicted_performance = "良好"
            improvement_probability = 0.6
        elif recent_accuracy >= 0.6:
            predicted_performance = "一般"
            improvement_probability = 0.8
        else:
            predicted_performance = "需要改进"
            improvement_probability = 0.9

        return {
            "predicted_performance_level": predicted_performance,
            "improvement_probability": improvement_probability,
            "expected_accuracy_range": {
                "min": max(0.0, recent_accuracy - 0.1),
                "max": min(1.0, recent_accuracy + 0.1),
            },
        }

    def _predict_learning_risks(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """预测学习风险."""
        if len(sessions) < 5:
            return {"risk_level": "无法预测"}

        # 分析最近趋势
        recent_sessions = sessions[-5:]
        accuracies = [s.get("accuracy_rate", 0) for s in recent_sessions]

        # 计算趋势
        if len(accuracies) >= 2:
            trend = (accuracies[-1] - accuracies[0]) / len(accuracies)
        else:
            trend = 0

        # 计算变异性
        accuracy_std = statistics.stdev(accuracies) if len(accuracies) > 1 else 0

        # 风险评估
        risk_factors = []
        if trend < -0.1:
            risk_factors.append("准确率下降趋势")
        if accuracy_std > 0.2:
            risk_factors.append("表现不稳定")
        if statistics.mean(accuracies) < 0.6:
            risk_factors.append("整体表现偏低")

        # 综合风险等级
        if len(risk_factors) >= 2:
            risk_level = "高"
        elif len(risk_factors) == 1:
            risk_level = "中"
        else:
            risk_level = "低"

        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "intervention_recommended": len(risk_factors) >= 1,
        }

    def _predict_goal_achievement(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """预测目标达成."""
        if not sessions:
            return {"error": "无数据"}

        current_accuracy = statistics.mean([s.get("accuracy_rate", 0) for s in sessions[-3:]])

        # 设定目标（可配置）
        goals = {
            "达到80%准确率": 0.8,
            "达到90%准确率": 0.9,
            "保持稳定表现": current_accuracy,
        }

        predictions = {}
        for goal_name, target_accuracy in goals.items():
            if current_accuracy >= target_accuracy:
                probability = 0.8  # 已达到目标
                estimated_sessions = 0
            else:
                # 简单预测：基于当前趋势
                gap = target_accuracy - current_accuracy
                if gap <= 0.1:
                    probability = 0.7
                    estimated_sessions = 5
                elif gap <= 0.2:
                    probability = 0.5
                    estimated_sessions = 10
                else:
                    probability = 0.3
                    estimated_sessions = 20

            predictions[goal_name] = {
                "achievement_probability": probability,
                "estimated_sessions_needed": estimated_sessions,
                "current_progress": min(current_accuracy / target_accuracy, 1.0),
            }

        return predictions

    def _generate_predictive_recommendations(
        self,
        trajectory_prediction: dict[str, Any],
        performance_prediction: dict[str, Any],
        risk_prediction: dict[str, Any],
    ) -> list[str]:
        """生成预测性建议."""
        recommendations = []

        # 基于轨迹预测的建议
        trajectory = trajectory_prediction.get("current_trajectory", "")
        if trajectory == "下降":
            recommendations.append("预测显示学习轨迹下降，建议调整学习策略")
        elif trajectory == "上升":
            recommendations.append("学习轨迹良好，建议保持当前方法")

        # 基于表现预测的建议
        performance_level = performance_prediction.get("predicted_performance_level", "")
        if performance_level == "需要改进":
            recommendations.append("预测表现需要改进，建议加强基础练习")
        elif performance_level == "优秀":
            recommendations.append("预测表现优秀，可以挑战更高难度")

        # 基于风险预测的建议
        risk_level = risk_prediction.get("risk_level", "")
        if risk_level == "高":
            recommendations.append("检测到高风险，建议寻求学习指导")
        elif risk_level == "中":
            recommendations.append("存在一定风险，建议关注学习状态")

        return recommendations

    def _calculate_prediction_confidence(self, sessions: list[dict[str, Any]]) -> float:
        """计算预测置信度."""
        # 基于数据量和质量
        data_volume_score = min(len(sessions) / 20.0, 1.0)  # 20次会话为满分

        # 基于数据一致性
        if len(sessions) > 1:
            accuracies = [s.get("accuracy_rate", 0) for s in sessions]
            consistency_score = 1.0 - (statistics.stdev(accuracies) / statistics.mean(accuracies))
            consistency_score = max(0.0, min(1.0, consistency_score))
        else:
            consistency_score = 0.5

        # 综合置信度
        confidence = data_volume_score * 0.6 + consistency_score * 0.4

        return float(confidence)
