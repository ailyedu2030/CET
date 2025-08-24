"""进度跟踪器 - 学习进度监控和里程碑管理."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.shared.models.enums import DifficultyLevel, TrainingType


class ProgressTracker:
    """学习进度跟踪器 - 监控学生学习进度和成就."""

    def __init__(self) -> None:
        # 里程碑配置
        self.milestones = {
            "first_session": {"name": "初次尝试", "description": "完成第一个训练会话"},
            "daily_streak_3": {"name": "坚持三天", "description": "连续学习3天"},
            "daily_streak_7": {"name": "一周坚持", "description": "连续学习7天"},
            "daily_streak_30": {"name": "月度坚持", "description": "连续学习30天"},
            "accuracy_80": {"name": "准确达人", "description": "单次会话准确率达到80%"},
            "accuracy_90": {"name": "精准射手", "description": "单次会话准确率达到90%"},
            "questions_100": {"name": "百题挑战", "description": "累计完成100道题目"},
            "questions_500": {"name": "五百强者", "description": "累计完成500道题目"},
            "questions_1000": {"name": "千题大师", "description": "累计完成1000道题目"},
            "all_types_mastery": {
                "name": "全能选手",
                "description": "掌握所有训练类型",
            },
            "difficulty_advanced": {
                "name": "高级挑战者",
                "description": "完成高级难度训练",
            },
            "speed_master": {
                "name": "速度大师",
                "description": "平均答题时间低于标准时间50%",
            },
        }

        # 等级配置
        self.level_thresholds = [
            0,
            100,
            250,
            500,
            1000,
            2000,
            3500,
            5500,
            8000,
            12000,
            17000,
        ]  # 经验值阈值

        # 经验值计算权重
        self.exp_weights = {
            "correct_answer": 10,
            "difficulty_bonus": 5,  # 每个难度等级额外奖励
            "speed_bonus": 3,  # 快速完成奖励
            "streak_bonus": 2,  # 连续正确奖励
            "first_try_bonus": 5,  # 首次尝试正确奖励
        }

    def calculate_session_progress(
        self,
        session_data: dict[str, Any],
        historical_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        计算单次会话的进度数据.

        Args:
            session_data: 会话数据
            historical_data: 历史数据

        Returns:
            进度计算结果
        """
        # 基础统计
        total_questions = session_data.get("total_questions", 0)
        correct_answers = session_data.get("correct_answers", 0)
        total_time = session_data.get("total_time_seconds", 0)
        difficulty_level = session_data.get("difficulty_level", DifficultyLevel.ELEMENTARY)

        # 计算准确率
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0.0

        # 计算平均用时
        avg_time_per_question = total_time / total_questions if total_questions > 0 else 0.0

        # 计算经验值
        exp_gained = self._calculate_experience_points(session_data)

        # 检查里程碑
        milestones_achieved = self._check_milestones(session_data, historical_data)

        # 计算等级变化
        level_info = self._calculate_level_change(exp_gained, historical_data)

        # 计算学习效率
        efficiency_score = self._calculate_efficiency_score(
            accuracy_rate, avg_time_per_question, difficulty_level
        )

        # 生成进度建议
        suggestions = self._generate_progress_suggestions(
            accuracy_rate, avg_time_per_question, difficulty_level, historical_data
        )

        return {
            "session_summary": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy_rate": accuracy_rate,
                "total_time_seconds": total_time,
                "avg_time_per_question": avg_time_per_question,
                "difficulty_level": difficulty_level,
            },
            "progress_metrics": {
                "exp_gained": exp_gained,
                "efficiency_score": efficiency_score,
                "milestones_achieved": milestones_achieved,
                "level_info": level_info,
            },
            "recommendations": suggestions,
        }

    def track_learning_streak(
        self,
        student_id: int,
        session_date: datetime,
        historical_sessions: list[datetime],
    ) -> dict[str, Any]:
        """
        跟踪学习连续性.

        Args:
            student_id: 学生ID
            session_date: 会话日期
            historical_sessions: 历史会话日期列表

        Returns:
            连续性统计
        """
        # 按日期排序
        all_dates = sorted(set([session_date] + historical_sessions))

        # 计算当前连续天数
        current_streak = self._calculate_current_streak(all_dates)

        # 计算最长连续天数
        max_streak = self._calculate_max_streak(all_dates)

        # 计算本周/本月学习天数
        week_days = self._count_days_in_period(all_dates, days=7)
        month_days = self._count_days_in_period(all_dates, days=30)

        # 预测下次学习时间
        next_session_prediction = self._predict_next_session(all_dates)

        return {
            "current_streak": current_streak,
            "max_streak": max_streak,
            "week_study_days": week_days,
            "month_study_days": month_days,
            "total_study_days": len({d.date() for d in all_dates}),
            "next_session_prediction": next_session_prediction,
            "streak_status": self._get_streak_status(current_streak),
        }

    def analyze_learning_patterns(
        self,
        sessions: list[dict[str, Any]],
        time_window_days: int = 30,
    ) -> dict[str, Any]:
        """
        分析学习模式.

        Args:
            sessions: 会话列表
            time_window_days: 分析时间窗口

        Returns:
            学习模式分析
        """
        if not sessions:
            return {"error": "没有足够的数据进行分析"}

        # 时间模式分析
        time_patterns = self._analyze_time_patterns(sessions)

        # 难度进展分析
        difficulty_progression = self._analyze_difficulty_progression(sessions)

        # 训练类型偏好分析
        type_preferences = self._analyze_type_preferences(sessions)

        # 表现趋势分析
        performance_trends = self._analyze_performance_trends(sessions)

        # 学习效率分析
        efficiency_analysis = self._analyze_efficiency_trends(sessions)

        return {
            "analysis_period": f"最近{time_window_days}天",
            "total_sessions": len(sessions),
            "patterns": {
                "time_patterns": time_patterns,
                "difficulty_progression": difficulty_progression,
                "type_preferences": type_preferences,
                "performance_trends": performance_trends,
                "efficiency_analysis": efficiency_analysis,
            },
            "insights": self._generate_pattern_insights(
                time_patterns, difficulty_progression, performance_trends
            ),
        }

    def calculate_mastery_level(
        self,
        training_type: TrainingType,
        recent_sessions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        计算特定训练类型的掌握程度.

        Args:
            training_type: 训练类型
            recent_sessions: 最近的会话数据

        Returns:
            掌握程度分析
        """
        if not recent_sessions:
            return {"mastery_level": "未开始", "confidence": 0.0}

        # 筛选相关会话
        relevant_sessions = [s for s in recent_sessions if s.get("training_type") == training_type]

        if not relevant_sessions:
            return {"mastery_level": "未开始", "confidence": 0.0}

        # 计算各项指标
        avg_accuracy = sum(s.get("accuracy_rate", 0) for s in relevant_sessions) / len(
            relevant_sessions
        )
        avg_difficulty = self._calculate_avg_difficulty(relevant_sessions)
        consistency_score = self._calculate_consistency_score(relevant_sessions)
        improvement_rate = self._calculate_improvement_rate(relevant_sessions)

        # 计算综合掌握度
        mastery_score = (
            avg_accuracy * 0.4
            + avg_difficulty * 0.3
            + consistency_score * 0.2
            + improvement_rate * 0.1
        )

        # 确定掌握等级
        mastery_level = self._determine_mastery_level(mastery_score)

        # 计算置信度
        confidence = min(len(relevant_sessions) / 10.0, 1.0)  # 至少需要10次会话才能完全置信

        return {
            "mastery_level": mastery_level,
            "mastery_score": mastery_score,
            "confidence": confidence,
            "metrics": {
                "average_accuracy": avg_accuracy,
                "average_difficulty": avg_difficulty,
                "consistency_score": consistency_score,
                "improvement_rate": improvement_rate,
            },
            "session_count": len(relevant_sessions),
            "recommendations": self._generate_mastery_recommendations(
                mastery_level, avg_accuracy, avg_difficulty
            ),
        }

    def generate_progress_report(
        self,
        student_id: int,
        period_days: int = 30,
        all_sessions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        生成综合进度报告.

        Args:
            student_id: 学生ID
            period_days: 报告周期
            all_sessions: 所有会话数据

        Returns:
            综合进度报告
        """
        if not all_sessions:
            all_sessions = []

        # 筛选时间范围内的会话
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        recent_sessions = [
            s for s in all_sessions if s.get("created_at", datetime.min) >= cutoff_date
        ]

        # 总体统计
        total_stats = self._calculate_total_statistics(recent_sessions)

        # 学习连续性
        session_dates = [
            s["created_at"] for s in recent_sessions if s.get("created_at") is not None
        ]
        streak_info = self.track_learning_streak(student_id, datetime.utcnow(), session_dates)

        # 各训练类型掌握情况
        mastery_by_type = {}
        for training_type in TrainingType:
            mastery_by_type[training_type.value] = self.calculate_mastery_level(
                training_type, recent_sessions
            )

        # 学习模式分析
        pattern_analysis = self.analyze_learning_patterns(recent_sessions, period_days)

        # 成就和里程碑
        achievements = self._calculate_achievements(all_sessions)

        # 进度预测
        progress_prediction = self._predict_future_progress(recent_sessions)

        return {
            "report_info": {
                "student_id": student_id,
                "period_days": period_days,
                "generated_at": datetime.utcnow(),
                "sessions_analyzed": len(recent_sessions),
            },
            "overall_statistics": total_stats,
            "learning_streak": streak_info,
            "mastery_by_type": mastery_by_type,
            "learning_patterns": pattern_analysis,
            "achievements": achievements,
            "progress_prediction": progress_prediction,
            "recommendations": self._generate_comprehensive_recommendations(
                total_stats, streak_info, mastery_by_type, pattern_analysis
            ),
        }

    # ==================== 私有辅助方法 ====================

    def _calculate_experience_points(self, session_data: dict[str, Any]) -> int:
        """计算经验值."""
        exp = 0

        # 基础经验（正确答案）
        correct_answers = session_data.get("correct_answers", 0)
        exp += correct_answers * self.exp_weights["correct_answer"]

        # 难度奖励
        difficulty_level = session_data.get("difficulty_level", DifficultyLevel.ELEMENTARY)
        difficulty_multiplier = {
            DifficultyLevel.BEGINNER: 0.5,
            DifficultyLevel.ELEMENTARY: 1,
            DifficultyLevel.INTERMEDIATE: 2,
            DifficultyLevel.UPPER_INTERMEDIATE: 3,
            DifficultyLevel.ADVANCED: 4,
        }[difficulty_level]
        exp += correct_answers * self.exp_weights["difficulty_bonus"] * difficulty_multiplier

        # 速度奖励
        avg_time = session_data.get("avg_time_per_question", 0)
        if avg_time > 0 and avg_time < 30:  # 快速完成（少于30秒）
            exp += correct_answers * self.exp_weights["speed_bonus"]

        # 连续正确奖励
        consecutive_correct = session_data.get("consecutive_correct", 0)
        if consecutive_correct >= 5:
            exp += self.exp_weights["streak_bonus"] * (consecutive_correct - 4)

        return int(exp)

    def _check_milestones(
        self, session_data: dict[str, Any], historical_data: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """检查里程碑达成."""
        achieved = []

        if not historical_data:
            historical_data = {}

        # 首次会话
        if historical_data.get("total_sessions", 0) == 0:
            achieved.append({"milestone": "first_session", **self.milestones["first_session"]})

        # 准确率里程碑
        accuracy = session_data.get("accuracy_rate", 0)
        if accuracy >= 0.9 and not historical_data.get("achieved_accuracy_90"):
            achieved.append({"milestone": "accuracy_90", **self.milestones["accuracy_90"]})
        elif accuracy >= 0.8 and not historical_data.get("achieved_accuracy_80"):
            achieved.append({"milestone": "accuracy_80", **self.milestones["accuracy_80"]})

        # 题目数量里程碑
        total_questions = historical_data.get("total_questions_answered", 0) + session_data.get(
            "total_questions", 0
        )
        if total_questions >= 1000 and not historical_data.get("achieved_questions_1000"):
            achieved.append({"milestone": "questions_1000", **self.milestones["questions_1000"]})
        elif total_questions >= 500 and not historical_data.get("achieved_questions_500"):
            achieved.append({"milestone": "questions_500", **self.milestones["questions_500"]})
        elif total_questions >= 100 and not historical_data.get("achieved_questions_100"):
            achieved.append({"milestone": "questions_100", **self.milestones["questions_100"]})

        return achieved

    def _calculate_level_change(
        self, exp_gained: int, historical_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """计算等级变化."""
        current_exp = historical_data.get("total_experience", 0) if historical_data else 0
        new_exp = current_exp + exp_gained

        current_level = self._exp_to_level(current_exp)
        new_level = self._exp_to_level(new_exp)

        return {
            "current_level": current_level,
            "new_level": new_level,
            "level_up": new_level > current_level,
            "exp_gained": exp_gained,
            "total_exp": new_exp,
            "exp_to_next_level": self._exp_to_next_level(new_exp),
        }

    def _exp_to_level(self, exp: int) -> int:
        """经验值转换为等级."""
        for level, threshold in enumerate(self.level_thresholds):
            if exp < threshold:
                return max(0, level - 1)
        return len(self.level_thresholds) - 1

    def _exp_to_next_level(self, current_exp: int) -> int:
        """计算到下一等级所需经验值."""
        current_level = self._exp_to_level(current_exp)
        if current_level >= len(self.level_thresholds) - 1:
            return 0  # 已达到最高等级

        next_threshold = self.level_thresholds[current_level + 1]
        return next_threshold - current_exp

    def _calculate_efficiency_score(
        self, accuracy: float, avg_time: float, difficulty: DifficultyLevel
    ) -> float:
        """计算学习效率分数."""
        # 基础效率（准确率）
        efficiency = accuracy

        # 时间效率调整
        if avg_time > 0:
            # 假设标准时间为60秒
            time_efficiency = min(60.0 / avg_time, 2.0)  # 最多2倍奖励
            efficiency *= 1.0 + time_efficiency * 0.2  # 时间效率最多增加40%

        # 难度调整
        difficulty_bonus = {
            DifficultyLevel.BEGINNER: 0.9,
            DifficultyLevel.ELEMENTARY: 1.0,
            DifficultyLevel.INTERMEDIATE: 1.1,
            DifficultyLevel.UPPER_INTERMEDIATE: 1.2,
            DifficultyLevel.ADVANCED: 1.3,
        }[difficulty]

        efficiency *= difficulty_bonus

        return min(efficiency, 2.0)  # 限制最大效率分数

    def _generate_progress_suggestions(
        self,
        accuracy: float,
        avg_time: float,
        difficulty: DifficultyLevel,
        historical_data: dict[str, Any] | None,
    ) -> list[str]:
        """生成进度建议."""
        suggestions = []

        # 准确率建议
        if accuracy < 0.6:
            suggestions.append("建议降低难度，巩固基础知识")
        elif accuracy > 0.9:
            suggestions.append("表现优秀！可以尝试更高难度的挑战")

        # 速度建议
        if avg_time > 120:
            suggestions.append("可以通过更多练习提高答题速度")
        elif avg_time < 20:
            suggestions.append("答题速度很快，注意保持准确性")

        # 难度建议
        if difficulty == DifficultyLevel.ELEMENTARY and accuracy > 0.8:
            suggestions.append("可以尝试中级难度题目")
        elif difficulty == DifficultyLevel.ADVANCED and accuracy < 0.7:
            suggestions.append("建议回到高级难度巩固基础")

        # 历史对比建议
        if historical_data:
            prev_accuracy = historical_data.get("recent_avg_accuracy", 0)
            if accuracy > prev_accuracy + 0.1:
                suggestions.append("进步明显！继续保持这个学习节奏")
            elif accuracy < prev_accuracy - 0.1:
                suggestions.append("最近表现有所下降，建议调整学习策略")

        return suggestions

    def _calculate_current_streak(self, dates: list[datetime]) -> int:
        """计算当前连续学习天数."""
        if not dates:
            return 0

        # 转换为日期并排序
        date_set = sorted({d.date() for d in dates}, reverse=True)

        streak = 0
        current_date = datetime.utcnow().date()

        for date in date_set:
            if date == current_date or date == current_date - timedelta(days=streak):
                streak += 1
                current_date = date
            else:
                break

        return streak

    def _calculate_max_streak(self, dates: list[datetime]) -> int:
        """计算最长连续学习天数."""
        if not dates:
            return 0

        date_set = sorted({d.date() for d in dates})

        max_streak = 1
        current_streak = 1

        for i in range(1, len(date_set)):
            if date_set[i] == date_set[i - 1] + timedelta(days=1):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    def _count_days_in_period(self, dates: list[datetime], days: int) -> int:
        """计算指定时间段内的学习天数."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_dates = [d for d in dates if d >= cutoff]
        return len({d.date() for d in recent_dates})

    def _predict_next_session(self, dates: list[datetime]) -> dict[str, Any]:
        """预测下次学习时间."""
        if len(dates) < 2:
            return {"prediction": "数据不足", "confidence": 0.0}

        # 计算平均间隔
        sorted_dates = sorted(dates)
        intervals = []
        for i in range(1, len(sorted_dates)):
            interval = (sorted_dates[i] - sorted_dates[i - 1]).total_seconds() / 3600  # 小时
            intervals.append(interval)

        avg_interval = sum(intervals) / len(intervals)
        last_session = max(dates)

        predicted_time = last_session + timedelta(hours=avg_interval)

        # 计算置信度（基于间隔的一致性）
        variance = sum((interval - avg_interval) ** 2 for interval in intervals) / len(intervals)
        confidence = max(0.0, 1.0 - (variance / (avg_interval**2)))

        return {
            "predicted_datetime": predicted_time,
            "average_interval_hours": avg_interval,
            "confidence": confidence,
        }

    def _get_streak_status(self, streak: int) -> str:
        """获取连续学习状态描述."""
        if streak == 0:
            return "尚未开始"
        elif streak < 3:
            return "刚刚起步"
        elif streak < 7:
            return "良好开端"
        elif streak < 30:
            return "坚持不懈"
        else:
            return "学习达人"

    def _analyze_time_patterns(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析时间模式."""
        if not sessions:
            return {}

        hour_counts: defaultdict[int, int] = defaultdict(int)
        weekday_counts: defaultdict[int, int] = defaultdict(int)

        for session in sessions:
            created_at = session.get("created_at")
            if created_at:
                hour_counts[created_at.hour] += 1
                weekday_counts[created_at.weekday()] += 1

        # 找出最活跃时段
        peak_hour = max(hour_counts.keys(), key=lambda h: hour_counts[h]) if hour_counts else 0
        peak_weekday = (
            max(weekday_counts.keys(), key=lambda w: weekday_counts[w]) if weekday_counts else 0
        )

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        return {
            "peak_hour": peak_hour,
            "peak_weekday": weekday_names[peak_weekday],
            "hour_distribution": dict(hour_counts),
            "weekday_distribution": {weekday_names[k]: v for k, v in weekday_counts.items()},
        }

    def _analyze_difficulty_progression(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析难度进展."""
        if not sessions:
            return {}

        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))

        difficulty_progression = []
        for session in sorted_sessions:
            difficulty = session.get("difficulty_level", DifficultyLevel.ELEMENTARY)
            accuracy = session.get("accuracy_rate", 0)
            difficulty_progression.append(
                {
                    "date": session.get("created_at"),
                    "difficulty": (
                        difficulty.value if hasattr(difficulty, "value") else str(difficulty)
                    ),
                    "accuracy": accuracy,
                }
            )

        # 计算趋势
        if len(difficulty_progression) >= 2:
            first_half = difficulty_progression[: len(difficulty_progression) // 2]
            second_half = difficulty_progression[len(difficulty_progression) // 2 :]

            avg_difficulty_early = sum(
                self._difficulty_to_score(d["difficulty"]) for d in first_half
            ) / len(first_half)
            avg_difficulty_recent = sum(
                self._difficulty_to_score(d["difficulty"]) for d in second_half
            ) / len(second_half)

            trend = "上升" if avg_difficulty_recent > avg_difficulty_early else "稳定"
        else:
            trend = "数据不足"

        return {
            "progression": difficulty_progression,
            "trend": trend,
        }

    def _difficulty_to_score(self, difficulty: str) -> float:
        """难度转换为分数."""
        mapping = {
            "ELEMENTARY": 1.0,
            "INTERMEDIATE": 2.0,
            "ADVANCED": 3.0,
            "EXPERT": 4.0,
        }
        return mapping.get(difficulty, 1.0)

    def _analyze_type_preferences(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析训练类型偏好."""
        type_counts: defaultdict[str, int] = defaultdict(int)
        type_accuracy = defaultdict(list)

        for session in sessions:
            training_type = session.get("training_type")
            accuracy = session.get("accuracy_rate", 0)

            if training_type:
                type_name = (
                    training_type.value if hasattr(training_type, "value") else str(training_type)
                )
                type_counts[type_name] += 1
                type_accuracy[type_name].append(accuracy)

        # 计算平均准确率
        type_avg_accuracy = {
            t: sum(accuracies) / len(accuracies) for t, accuracies in type_accuracy.items()
        }

        # 找出最喜欢和最擅长的类型
        most_practiced = (
            max(type_counts.keys(), key=lambda t: type_counts[t]) if type_counts else None
        )
        best_performance = (
            max(type_avg_accuracy.keys(), key=lambda t: type_avg_accuracy[t])
            if type_avg_accuracy
            else None
        )

        return {
            "type_counts": dict(type_counts),
            "type_avg_accuracy": type_avg_accuracy,
            "most_practiced": most_practiced,
            "best_performance": best_performance,
        }

    def _analyze_performance_trends(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析表现趋势."""
        if len(sessions) < 3:
            return {"trend": "数据不足"}

        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))

        # 计算移动平均
        window_size = min(5, len(sorted_sessions) // 2)
        accuracies = [s.get("accuracy_rate", 0) for s in sorted_sessions]

        early_avg = sum(accuracies[:window_size]) / window_size
        recent_avg = sum(accuracies[-window_size:]) / window_size

        # 确定趋势
        if recent_avg > early_avg + 0.05:
            trend = "明显进步"
        elif recent_avg > early_avg:
            trend = "稳步提升"
        elif recent_avg < early_avg - 0.05:
            trend = "需要关注"
        else:
            trend = "基本稳定"

        return {
            "trend": trend,
            "early_average": early_avg,
            "recent_average": recent_avg,
            "improvement_rate": (
                (recent_avg - early_avg) / early_avg * 100 if early_avg > 0 else 0
            ),
        }

    def _analyze_efficiency_trends(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析效率趋势."""
        if not sessions:
            return {}

        efficiency_scores = []
        for session in sessions:
            accuracy = session.get("accuracy_rate", 0)
            avg_time = session.get("avg_time_per_question", 0)
            difficulty = session.get("difficulty_level", DifficultyLevel.ELEMENTARY)

            efficiency = self._calculate_efficiency_score(accuracy, avg_time, difficulty)
            efficiency_scores.append(efficiency)

        if len(efficiency_scores) >= 2:
            recent_efficiency = sum(efficiency_scores[-3:]) / min(3, len(efficiency_scores))
            early_efficiency = sum(efficiency_scores[:3]) / min(3, len(efficiency_scores))

            trend = "提升" if recent_efficiency > early_efficiency else "稳定"
        else:
            trend = "数据不足"

        return {
            "average_efficiency": sum(efficiency_scores) / len(efficiency_scores),
            "trend": trend,
            "efficiency_scores": efficiency_scores,
        }

    def _generate_pattern_insights(
        self,
        time_patterns: dict[str, Any],
        difficulty_progression: dict[str, Any],
        performance_trends: dict[str, Any],
    ) -> list[str]:
        """生成模式洞察."""
        insights = []

        # 时间模式洞察
        if time_patterns.get("peak_hour"):
            peak_hour = time_patterns["peak_hour"]
            if 6 <= peak_hour <= 9:
                insights.append("您是早晨学习型，建议保持这个良好习惯")
            elif 19 <= peak_hour <= 22:
                insights.append("您习惯晚间学习，注意保证充足睡眠")

        # 难度进展洞察
        if difficulty_progression.get("trend") == "上升":
            insights.append("难度挑战逐步提升，学习进步明显")

        # 表现趋势洞察
        trend = performance_trends.get("trend", "")
        if trend == "明显进步":
            insights.append("学习效果显著，继续保持当前方法")
        elif trend == "需要关注":
            insights.append("近期表现有所下降，建议调整学习策略")

        return insights

    def _calculate_total_statistics(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """计算总体统计."""
        if not sessions:
            return {
                "total_sessions": 0,
                "total_questions": 0,
                "total_correct": 0,
                "average_accuracy": 0.0,
                "total_time_hours": 0.0,
            }

        total_sessions = len(sessions)
        total_questions = sum(s.get("total_questions", 0) for s in sessions)
        total_correct = sum(s.get("correct_answers", 0) for s in sessions)
        total_time = sum(s.get("total_time_seconds", 0) for s in sessions)

        average_accuracy = total_correct / total_questions if total_questions > 0 else 0.0

        return {
            "total_sessions": total_sessions,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "average_accuracy": average_accuracy,
            "total_time_hours": total_time / 3600.0,
        }

    def _calculate_avg_difficulty(self, sessions: list[dict[str, Any]]) -> float:
        """计算平均难度."""
        if not sessions:
            return 0.0

        difficulty_scores = []
        for session in sessions:
            difficulty = session.get("difficulty_level", DifficultyLevel.ELEMENTARY)
            score = self._difficulty_to_score(
                difficulty.value if hasattr(difficulty, "value") else str(difficulty)
            )
            difficulty_scores.append(score)

        return sum(difficulty_scores) / len(difficulty_scores)

    def _calculate_consistency_score(self, sessions: list[dict[str, Any]]) -> float:
        """计算一致性分数."""
        if len(sessions) < 2:
            return 0.0

        accuracies = [s.get("accuracy_rate", 0) for s in sessions]
        avg_accuracy = sum(accuracies) / len(accuracies)

        # 计算标准差
        variance = sum((acc - avg_accuracy) ** 2 for acc in accuracies) / len(accuracies)
        std_dev = variance**0.5

        # 一致性分数（标准差越小，一致性越高）
        consistency = max(0.0, 1.0 - std_dev)

        return float(consistency)

    def _calculate_improvement_rate(self, sessions: list[dict[str, Any]]) -> float:
        """计算改进率."""
        if len(sessions) < 2:
            return 0.0

        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", datetime.min))

        # 比较前后期表现
        first_half = sorted_sessions[: len(sorted_sessions) // 2]
        second_half = sorted_sessions[len(sorted_sessions) // 2 :]

        early_avg = sum(s.get("accuracy_rate", 0) for s in first_half) / len(first_half)
        recent_avg = sum(s.get("accuracy_rate", 0) for s in second_half) / len(second_half)

        improvement_rate = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0.0

        return max(-1.0, min(1.0, improvement_rate))  # 限制在-100%到100%之间

    def _determine_mastery_level(self, mastery_score: float) -> str:
        """确定掌握等级."""
        if mastery_score >= 0.9:
            return "精通"
        elif mastery_score >= 0.8:
            return "熟练"
        elif mastery_score >= 0.7:
            return "掌握"
        elif mastery_score >= 0.6:
            return "理解"
        elif mastery_score >= 0.4:
            return "入门"
        else:
            return "初学"

    def _generate_mastery_recommendations(
        self, mastery_level: str, avg_accuracy: float, avg_difficulty: float
    ) -> list[str]:
        """生成掌握度建议."""
        recommendations = []

        if mastery_level in ["初学", "入门"]:
            recommendations.append("建议从基础题目开始，循序渐进")
            recommendations.append("多做练习，熟悉题型特点")
        elif mastery_level in ["理解", "掌握"]:
            recommendations.append("可以尝试更高难度的挑战")
            recommendations.append("注意总结错误，巩固薄弱环节")
        elif mastery_level in ["熟练", "精通"]:
            recommendations.append("表现优秀！可以挑战专家级难度")
            recommendations.append("考虑帮助其他同学，教学相长")

        if avg_accuracy < 0.7:
            recommendations.append("建议降低难度，提高准确率")
        elif avg_accuracy > 0.9:
            recommendations.append("准确率很高，可以提升答题速度")

        return recommendations

    def _calculate_achievements(self, all_sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """计算成就和里程碑."""
        achievements: dict[str, Any] = {
            "unlocked": [],
            "progress": {},
            "total_exp": 0,
            "current_level": 0,
        }

        if not all_sessions:
            return achievements

        # 计算总经验值
        total_exp = sum(self._calculate_experience_points(session) for session in all_sessions)
        achievements["total_exp"] = total_exp
        achievements["current_level"] = self._exp_to_level(total_exp)

        # 检查各种成就
        total_questions = sum(s.get("total_questions", 0) for s in all_sessions)
        max_accuracy = max((s.get("accuracy_rate", 0) for s in all_sessions), default=0)

        # 题目数量成就
        if total_questions >= 1000:
            achievements["unlocked"].append("千题大师")
        elif total_questions >= 500:
            achievements["unlocked"].append("五百强者")
        elif total_questions >= 100:
            achievements["unlocked"].append("百题挑战")

        # 准确率成就
        if max_accuracy >= 0.9:
            achievements["unlocked"].append("精准射手")
        elif max_accuracy >= 0.8:
            achievements["unlocked"].append("准确达人")

        # 进度跟踪
        achievements["progress"] = {
            "questions_to_next_milestone": max(0, 100 - (total_questions % 100)),
            "exp_to_next_level": self._exp_to_next_level(total_exp),
        }

        return achievements

    def _predict_future_progress(self, recent_sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """预测未来进度."""
        if len(recent_sessions) < 3:
            return {"prediction": "数据不足进行预测"}

        # 计算学习速度趋势
        sessions_per_week = len(recent_sessions) / 4.0  # 假设是最近4周的数据
        questions_per_session = sum(s.get("total_questions", 0) for s in recent_sessions) / len(
            recent_sessions
        )

        # 预测下个月的进度
        predicted_sessions = sessions_per_week * 4
        predicted_questions = predicted_sessions * questions_per_session

        # 预测准确率趋势
        recent_accuracies = [s.get("accuracy_rate", 0) for s in recent_sessions[-5:]]
        if len(recent_accuracies) >= 2:
            accuracy_trend = (recent_accuracies[-1] - recent_accuracies[0]) / len(recent_accuracies)
            predicted_accuracy = min(1.0, max(0.0, recent_accuracies[-1] + accuracy_trend * 4))
        else:
            predicted_accuracy = sum(recent_accuracies) / len(recent_accuracies)

        return {
            "next_month_prediction": {
                "estimated_sessions": int(predicted_sessions),
                "estimated_questions": int(predicted_questions),
                "predicted_accuracy": predicted_accuracy,
            },
            "confidence": min(len(recent_sessions) / 10.0, 0.8),  # 基于数据量的置信度
        }

    def _generate_comprehensive_recommendations(
        self,
        total_stats: dict[str, Any],
        streak_info: dict[str, Any],
        mastery_by_type: dict[str, Any],
        pattern_analysis: dict[str, Any],
    ) -> list[str]:
        """生成综合建议."""
        recommendations = []

        # 基于总体统计的建议
        avg_accuracy = total_stats.get("average_accuracy", 0)
        if avg_accuracy < 0.6:
            recommendations.append("整体准确率偏低，建议从基础题目开始练习")
        elif avg_accuracy > 0.85:
            recommendations.append("整体表现优秀，可以挑战更高难度")

        # 基于学习连续性的建议
        current_streak = streak_info.get("current_streak", 0)
        if current_streak == 0:
            recommendations.append("建议建立每日学习习惯，坚持练习")
        elif current_streak < 7:
            recommendations.append("学习习惯良好，继续保持连续性")
        else:
            recommendations.append("学习习惯优秀！继续保持这个节奏")

        # 基于掌握情况的建议
        weak_types = []
        strong_types = []
        for type_name, mastery_info in mastery_by_type.items():
            mastery_level = mastery_info.get("mastery_level", "")
            if mastery_level in ["初学", "入门"]:
                weak_types.append(type_name)
            elif mastery_level in ["熟练", "精通"]:
                strong_types.append(type_name)

        if weak_types:
            recommendations.append(f"建议加强{', '.join(weak_types[:2])}类型的练习")
        if strong_types:
            recommendations.append(f"在{', '.join(strong_types[:2])}方面表现优秀，可以挑战更高难度")

        return recommendations
