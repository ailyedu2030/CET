"""游戏化工具类 - 提供游戏化元素和激励机制的工具函数."""

import logging
import math
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class GamificationUtils:
    """游戏化工具类 - 实现各种游戏化机制和算法."""

    def __init__(self) -> None:
        """初始化游戏化工具."""
        # 等级系统配置
        self.level_config = {
            "base_exp": 100,  # 基础经验值
            "exp_multiplier": 1.5,  # 经验值倍数
            "max_level": 100,  # 最大等级
        }

        # 积分系统配置
        self.points_config = {
            "daily_login": 10,
            "complete_session": 20,
            "perfect_score": 50,
            "streak_bonus": 5,  # 连击奖励
            "social_interaction": 15,
            "achievement_unlock": 100,
        }

        # 连击系统配置
        self.streak_config = {
            "daily_streak": {"reset_hours": 24, "bonus_multiplier": 1.2},
            "perfect_streak": {"reset_threshold": 0.9, "bonus_multiplier": 1.5},
            "learning_streak": {"reset_hours": 48, "bonus_multiplier": 1.3},
        }

    def calculate_level_from_exp(self, total_exp: int) -> dict[str, Any]:
        """根据总经验值计算等级信息."""
        if total_exp <= 0:
            return {
                "level": 1,
                "current_exp": 0,
                "exp_to_next": self.level_config["base_exp"],
                "progress_percentage": 0.0,
            }

        level = 1
        exp_for_current_level = 0
        exp_for_next_level = self.level_config["base_exp"]

        # 计算当前等级
        while total_exp >= exp_for_next_level and level < self.level_config["max_level"]:
            level += 1
            exp_for_current_level = exp_for_next_level
            exp_for_next_level = int(
                self.level_config["base_exp"] * (self.level_config["exp_multiplier"] ** (level - 1))
            )

        # 计算当前等级的经验值
        current_level_exp = total_exp - exp_for_current_level
        exp_needed_for_next = exp_for_next_level - exp_for_current_level

        # 计算进度百分比
        progress_percentage = (
            (current_level_exp / exp_needed_for_next) * 100 if exp_needed_for_next > 0 else 100
        )

        return {
            "level": level,
            "current_exp": current_level_exp,
            "exp_to_next": exp_needed_for_next - current_level_exp,
            "progress_percentage": min(progress_percentage, 100.0),
            "total_exp": total_exp,
        }

    def calculate_exp_reward(
        self, base_activity: str, performance_data: dict[str, Any]
    ) -> dict[str, Any]:
        """计算经验值奖励."""
        base_exp = self.points_config.get(base_activity, 10)

        # 基础奖励
        reward: dict[str, Any] = {
            "base_exp": base_exp,
            "bonus_exp": 0,
            "total_exp": base_exp,
            "multipliers": [],
        }

        # 表现奖励
        if "accuracy" in performance_data:
            accuracy = performance_data["accuracy"]
            if accuracy >= 0.95:
                bonus = int(base_exp * 0.5)
                reward["bonus_exp"] = reward["bonus_exp"] + bonus
                reward["multipliers"].append({"type": "perfect_accuracy", "bonus": bonus})
            elif accuracy >= 0.8:
                bonus = int(base_exp * 0.2)
                reward["bonus_exp"] = reward["bonus_exp"] + bonus
                reward["multipliers"].append({"type": "high_accuracy", "bonus": bonus})

        # 速度奖励
        if "completion_time" in performance_data and "expected_time" in performance_data:
            time_ratio = performance_data["completion_time"] / performance_data["expected_time"]
            if time_ratio <= 0.7:  # 快速完成
                bonus = int(base_exp * 0.3)
                reward["bonus_exp"] = reward["bonus_exp"] + bonus
                reward["multipliers"].append({"type": "speed_bonus", "bonus": bonus})

        # 连击奖励
        if "streak_count" in performance_data:
            streak_bonus = self._calculate_streak_bonus(performance_data["streak_count"], base_exp)
            reward["bonus_exp"] = reward["bonus_exp"] + streak_bonus
            if streak_bonus > 0:
                reward["multipliers"].append({"type": "streak_bonus", "bonus": streak_bonus})

        # 难度奖励
        if "difficulty_level" in performance_data:
            difficulty_bonus = self._calculate_difficulty_bonus(
                performance_data["difficulty_level"], base_exp
            )
            reward["bonus_exp"] = reward["bonus_exp"] + difficulty_bonus
            if difficulty_bonus > 0:
                reward["multipliers"].append(
                    {"type": "difficulty_bonus", "bonus": difficulty_bonus}
                )

        reward["total_exp"] = reward["base_exp"] + reward["bonus_exp"]
        return reward

    def update_streak_counter(
        self,
        streak_type: str,
        current_streak: dict[str, Any],
        new_activity: dict[str, Any],
    ) -> dict[str, Any]:
        """更新连击计数器."""
        updated_streak = current_streak.copy()
        now = datetime.now()

        # 检查连击是否中断
        if self._is_streak_broken(streak_type, current_streak, new_activity, now):
            updated_streak = {
                "count": 1,
                "start_date": now,
                "last_activity": now,
                "best_streak": max(
                    current_streak.get("best_streak", 0), current_streak.get("count", 0)
                ),
                "total_activities": current_streak.get("total_activities", 0) + 1,
            }
        else:
            # 继续连击
            updated_streak.update(
                {
                    "count": current_streak.get("count", 0) + 1,
                    "last_activity": now,
                    "total_activities": current_streak.get("total_activities", 0) + 1,
                }
            )

            # 更新最佳连击记录
            if updated_streak["count"] > current_streak.get("best_streak", 0):
                updated_streak["best_streak"] = updated_streak["count"]

        return updated_streak

    def generate_motivational_message(
        self, user_data: dict[str, Any], context: str = "general"
    ) -> dict[str, Any]:
        """生成激励消息."""
        messages = {
            "level_up": [
                "🎉 恭喜升级！您的努力得到了回报！",
                "⭐ 新的等级，新的开始！继续加油！",
                "🚀 您又上了一个台阶！实力在不断提升！",
            ],
            "achievement": [
                "🏆 解锁新成就！您真是太棒了！",
                "💎 又一个里程碑！您的坚持令人敬佩！",
                "🌟 成就达成！您正在成为学习大师！",
            ],
            "streak": [
                "🔥 连击继续！保持这个节奏！",
                "⚡ 连胜记录刷新！您状态火热！",
                "💪 坚持就是胜利！连击奖励已到账！",
            ],
            "encouragement": [
                "📚 每一次练习都是进步的阶梯！",
                "🎯 专注当下，成就未来！",
                "💡 学习的路上，您从不孤单！",
            ],
            "comeback": [
                "🔄 失败是成功之母，继续努力！",
                "💪 跌倒了就爬起来，您可以的！",
                "🌈 风雨过后见彩虹，坚持下去！",
            ],
        }

        # 根据上下文选择消息类型
        message_type = context if context in messages else "general"
        if message_type == "general":
            # 根据用户数据智能选择消息类型
            if user_data.get("recent_level_up"):
                message_type = "level_up"
            elif user_data.get("recent_achievement"):
                message_type = "achievement"
            elif user_data.get("current_streak", 0) > 3:
                message_type = "streak"
            elif user_data.get("recent_performance", 0) < 0.6:
                message_type = "comeback"
            else:
                message_type = "encouragement"

        import random

        selected_messages = messages.get(message_type, messages["encouragement"])
        message = random.choice(selected_messages)

        return {
            "message": message,
            "type": message_type,
            "personalization": self._add_personalization(message, user_data),
            "generated_at": datetime.now(),
        }

    def calculate_leaderboard_position(
        self, user_score: float, all_scores: list[float]
    ) -> dict[str, Any]:
        """计算排行榜位置."""
        if not all_scores:
            return {"rank": 1, "total": 1, "percentile": 100.0}

        # 排序分数（降序）
        sorted_scores = sorted(all_scores, reverse=True)

        # 找到用户排名
        rank = 1
        for i, score in enumerate(sorted_scores):
            if score <= user_score:
                rank = i + 1
                break
        else:
            rank = len(sorted_scores) + 1

        # 计算百分位
        percentile = ((len(sorted_scores) - rank + 1) / len(sorted_scores)) * 100

        return {
            "rank": rank,
            "total": len(sorted_scores),
            "percentile": round(percentile, 1),
            "better_than": len(sorted_scores) - rank,
        }

    def generate_progress_visualization(self, progress_data: dict[str, Any]) -> dict[str, Any]:
        """生成进度可视化数据."""
        visualization: dict[str, Any] = {
            "charts": [],
            "indicators": [],
            "milestones": [],
        }

        # 等级进度条
        if "level_info" in progress_data:
            level_info = progress_data["level_info"]
            visualization["indicators"].append(
                {
                    "type": "level_progress",
                    "title": f"等级 {level_info['level']}",
                    "current": level_info["current_exp"],
                    "max": level_info["current_exp"] + level_info["exp_to_next"],
                    "percentage": level_info["progress_percentage"],
                    "color": "#4CAF50",
                }
            )

        # 学习时间趋势
        if "daily_time" in progress_data:
            daily_time = progress_data["daily_time"]
            visualization["charts"].append(
                {
                    "type": "line_chart",
                    "title": "每日学习时间",
                    "data": daily_time,
                    "x_axis": "日期",
                    "y_axis": "分钟",
                    "color": "#2196F3",
                }
            )

        # 准确率趋势
        if "accuracy_trend" in progress_data:
            accuracy_trend = progress_data["accuracy_trend"]
            visualization["charts"].append(
                {
                    "type": "area_chart",
                    "title": "准确率趋势",
                    "data": accuracy_trend,
                    "x_axis": "时间",
                    "y_axis": "准确率",
                    "color": "#FF9800",
                }
            )

        # 里程碑标记
        if "achievements" in progress_data:
            for achievement in progress_data["achievements"]:
                visualization["milestones"].append(
                    {
                        "date": achievement.get("achieved_at"),
                        "title": achievement.get("name"),
                        "description": achievement.get("description"),
                        "icon": achievement.get("icon", "🏆"),
                    }
                )

        return visualization

    # ==================== 私有方法 ====================

    def _calculate_streak_bonus(self, streak_count: int, base_exp: int) -> int:
        """计算连击奖励."""
        if streak_count <= 1:
            return 0

        # 连击奖励递增，但有上限
        bonus_rate = min(0.1 * math.log(streak_count), 0.5)
        return int(base_exp * bonus_rate)

    def _calculate_difficulty_bonus(self, difficulty_level: str, base_exp: int) -> int:
        """计算难度奖励."""
        difficulty_multipliers = {
            "easy": 0.0,
            "medium": 0.1,
            "hard": 0.2,
            "expert": 0.3,
        }

        multiplier = difficulty_multipliers.get(difficulty_level, 0.0)
        return int(base_exp * multiplier)

    def _is_streak_broken(
        self,
        streak_type: str,
        current_streak: dict[str, Any],
        new_activity: dict[str, Any],
        now: datetime,
    ) -> bool:
        """检查连击是否中断."""
        if not current_streak.get("last_activity"):
            return False

        last_activity = current_streak["last_activity"]
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)

        config = self.streak_config.get(streak_type, {})

        if streak_type == "daily_streak":
            # 每日连击：超过24小时未活动则中断
            reset_hours = config.get("reset_hours", 24)
            return bool((now - last_activity).total_seconds() > reset_hours * 3600)

        elif streak_type == "perfect_streak":
            # 完美连击：准确率低于阈值则中断
            threshold = config.get("reset_threshold", 0.9)
            return bool(new_activity.get("accuracy", 0) < threshold)

        elif streak_type == "learning_streak":
            # 学习连击：超过48小时未学习则中断
            reset_hours = config.get("reset_hours", 48)
            return bool((now - last_activity).total_seconds() > reset_hours * 3600)

        return False

    def _add_personalization(self, message: str, user_data: dict[str, Any]) -> str:
        """为消息添加个性化元素."""
        username = user_data.get("username", "学习者")
        level = user_data.get("level", 1)

        # 添加用户名和等级信息
        if "{username}" in message:
            message = message.replace("{username}", username)

        if "{level}" in message:
            message = message.replace("{level}", str(level))

        # 根据时间添加问候语
        hour = datetime.now().hour
        if 6 <= hour < 12:
            greeting = "早上好"
        elif 12 <= hour < 18:
            greeting = "下午好"
        else:
            greeting = "晚上好"

        return f"{greeting}，{username}！{message}"

    def calculate_engagement_score(self, activity_data: dict[str, Any]) -> float:
        """计算用户参与度分数."""
        # 基础参与度指标
        login_frequency = activity_data.get("login_frequency", 0)  # 登录频率
        session_duration = activity_data.get("avg_session_duration", 0)  # 平均会话时长
        completion_rate = activity_data.get("completion_rate", 0)  # 完成率
        social_interaction = activity_data.get("social_interactions", 0)  # 社交互动次数

        # 权重配置
        weights = {
            "login": 0.25,
            "duration": 0.25,
            "completion": 0.3,
            "social": 0.2,
        }

        # 标准化各项指标（0-1范围）
        normalized_login = min(login_frequency / 7, 1.0)  # 每周7次为满分
        normalized_duration = min(session_duration / 60, 1.0)  # 60分钟为满分
        normalized_completion = completion_rate  # 已经是0-1范围
        normalized_social = min(social_interaction / 10, 1.0)  # 每周10次互动为满分

        # 计算加权平均
        engagement_score = (
            normalized_login * weights["login"]
            + normalized_duration * weights["duration"]
            + normalized_completion * weights["completion"]
            + normalized_social * weights["social"]
        )

        return float(round(engagement_score, 3))

    def generate_challenge_suggestion(self, user_profile: dict[str, Any]) -> dict[str, Any]:
        """生成个性化挑战建议."""
        current_level = user_profile.get("level", 1)
        weak_areas = user_profile.get("weak_areas", [])
        preferences = user_profile.get("preferences", {})

        challenges = []

        # 基于薄弱环节的挑战
        for area in weak_areas[:2]:  # 最多2个薄弱环节
            challenges.append(
                {
                    "type": "improvement_challenge",
                    "title": f"提升{area}技能",
                    "description": f"专注练习{area}相关题目，提高准确率",
                    "target": "accuracy_improvement",
                    "duration_days": 7,
                    "reward_points": 100,
                    "difficulty": "适中",
                }
            )

        # 基于等级的挑战
        if current_level < 10:
            challenges.append(
                {
                    "type": "level_challenge",
                    "title": "新手冲刺",
                    "description": "连续7天完成学习任务",
                    "target": "consistency",
                    "duration_days": 7,
                    "reward_points": 150,
                    "difficulty": "简单",
                }
            )
        elif current_level < 30:
            challenges.append(
                {
                    "type": "level_challenge",
                    "title": "进阶挑战",
                    "description": "在一周内完成100道题目",
                    "target": "volume",
                    "duration_days": 7,
                    "reward_points": 200,
                    "difficulty": "适中",
                }
            )
        else:
            challenges.append(
                {
                    "type": "level_challenge",
                    "title": "大师挑战",
                    "description": "保持90%以上准确率完成高难度题目",
                    "target": "mastery",
                    "duration_days": 14,
                    "reward_points": 500,
                    "difficulty": "困难",
                }
            )

        # 社交挑战
        if preferences.get("social_learning", False):
            challenges.append(
                {
                    "type": "social_challenge",
                    "title": "学习伙伴",
                    "description": "与同学组队完成学习任务",
                    "target": "collaboration",
                    "duration_days": 14,
                    "reward_points": 250,
                    "difficulty": "适中",
                }
            )

        # 随机选择1-2个挑战
        import random

        selected_challenges = random.sample(challenges, min(2, len(challenges)))

        return {
            "challenges": selected_challenges,
            "recommendation_reason": "基于您的学习情况和偏好推荐",
            "generated_at": datetime.now(),
        }
