"""学习成就系统服务 - 激励学生学习的游戏化成就体系."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.training.utils.gamification_utils import GamificationUtils
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class AchievementService:
    """学习成就系统服务 - 通过成就和徽章激励学生学习."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化成就系统服务."""
        self.db = db
        self.gamification_utils = GamificationUtils()

        # 成就类型配置
        self.achievement_types = {
            "learning_streak": {
                "name": "学习连击",
                "description": "连续学习天数",
                "levels": [3, 7, 15, 30, 60, 100],
                "rewards": [10, 25, 50, 100, 200, 500],
                "icon": "🔥",
            },
            "question_master": {
                "name": "题目大师",
                "description": "累计完成题目数量",
                "levels": [100, 500, 1000, 2000, 5000, 10000],
                "rewards": [20, 50, 100, 200, 500, 1000],
                "icon": "📚",
            },
            "accuracy_expert": {
                "name": "准确率专家",
                "description": "保持高准确率",
                "levels": [0.7, 0.75, 0.8, 0.85, 0.9, 0.95],
                "rewards": [30, 60, 120, 240, 480, 1000],
                "icon": "🎯",
            },
            "speed_demon": {
                "name": "速度恶魔",
                "description": "快速完成训练",
                "levels": [50, 100, 200, 500, 1000, 2000],
                "rewards": [15, 30, 60, 150, 300, 600],
                "icon": "⚡",
            },
            "social_butterfly": {
                "name": "社交达人",
                "description": "积极参与社交互动",
                "levels": [10, 25, 50, 100, 200, 500],
                "rewards": [25, 50, 100, 200, 400, 800],
                "icon": "🦋",
            },
            "knowledge_explorer": {
                "name": "知识探索者",
                "description": "学习不同类型的训练",
                "levels": [2, 3, 4, 5, 6, 7],
                "rewards": [40, 80, 160, 320, 640, 1280],
                "icon": "🔍",
            },
        }

        # 徽章配置
        self.badge_config = {
            "daily_champion": {
                "name": "每日冠军",
                "description": "单日学习时间超过2小时",
                "condition": "daily_study_time >= 120",
                "rarity": "common",
                "points": 50,
            },
            "perfect_score": {
                "name": "完美分数",
                "description": "单次训练获得满分",
                "condition": "session_score == 1.0",
                "rarity": "rare",
                "points": 100,
            },
            "early_bird": {
                "name": "早起鸟",
                "description": "早上6-8点完成学习",
                "condition": "study_time_range == 'early_morning'",
                "rarity": "uncommon",
                "points": 30,
            },
            "night_owl": {
                "name": "夜猫子",
                "description": "晚上10-12点完成学习",
                "condition": "study_time_range == 'late_night'",
                "rarity": "uncommon",
                "points": 30,
            },
            "comeback_king": {
                "name": "逆袭之王",
                "description": "从低分提升到高分",
                "condition": "score_improvement >= 0.3",
                "rarity": "epic",
                "points": 200,
            },
        }

    async def check_and_award_achievements(self, user_id: int) -> list[dict[str, Any]]:
        """检查并颁发成就."""
        try:
            awarded_achievements = []

            # 获取用户当前成就状态
            user_achievements = await self._get_user_achievements(user_id)

            # 检查各类成就
            for achievement_type, config in self.achievement_types.items():
                new_achievements = await self._check_achievement_type(
                    user_id, achievement_type, config, user_achievements
                )
                awarded_achievements.extend(new_achievements)

            # 检查徽章
            new_badges = await self._check_badges(user_id)
            awarded_achievements.extend(new_badges)

            # 保存新获得的成就
            if awarded_achievements:
                await self._save_achievements(user_id, awarded_achievements)

                # 发送成就通知
                await self._send_achievement_notifications(user_id, awarded_achievements)

            logger.info(f"用户 {user_id} 获得 {len(awarded_achievements)} 个新成就")
            return awarded_achievements

        except Exception as e:
            logger.error(f"检查成就失败: {str(e)}")
            raise

    async def get_user_achievements(self, user_id: int) -> dict[str, Any]:
        """获取用户成就信息."""
        try:
            # 获取用户基本信息
            user = await self.db.get(User, user_id)
            if not user:
                raise ValueError(f"用户不存在: {user_id}")

            # 获取成就列表
            achievements = await self._get_user_achievements(user_id)

            # 获取徽章列表
            badges = await self._get_user_badges(user_id)

            # 计算成就统计
            achievement_stats = await self._calculate_achievement_stats(achievements, badges)

            # 获取进度信息
            progress_info = await self._get_achievement_progress(user_id)

            # 获取排行榜位置
            leaderboard_position = await self._get_leaderboard_position(user_id)

            return {
                "user_id": user_id,
                "username": user.username,
                "achievements": achievements,
                "badges": badges,
                "stats": achievement_stats,
                "progress": progress_info,
                "leaderboard_position": leaderboard_position,
                "total_points": achievement_stats["total_points"],
                "achievement_level": self._calculate_achievement_level(
                    achievement_stats["total_points"]
                ),
                "next_level_points": self._get_next_level_points(achievement_stats["total_points"]),
            }

        except Exception as e:
            logger.error(f"获取用户成就失败: {str(e)}")
            raise

    async def get_achievement_leaderboard(
        self, limit: int = 50, achievement_type: str | None = None
    ) -> list[dict[str, Any]]:
        """获取成就排行榜."""
        try:
            # 获取排行榜数据
            leaderboard_data = await self._get_leaderboard_data(limit, achievement_type)

            # 添加排名信息
            for i, entry in enumerate(leaderboard_data):
                entry["rank"] = i + 1
                entry["achievement_level"] = self._calculate_achievement_level(
                    entry["total_points"]
                )

            return leaderboard_data

        except Exception as e:
            logger.error(f"获取成就排行榜失败: {str(e)}")
            raise

    async def create_custom_achievement(
        self, creator_id: int, achievement_data: dict[str, Any]
    ) -> dict[str, Any]:
        """创建自定义成就（管理员功能）."""
        try:
            # 验证创建者权限
            if not await self._verify_admin_permission(creator_id):
                raise ValueError("没有权限创建自定义成就")

            # 验证成就数据
            validated_data = await self._validate_achievement_data(achievement_data)

            # 生成成就ID
            achievement_id = await self._generate_achievement_id()

            # 创建自定义成就
            custom_achievement = {
                "achievement_id": achievement_id,
                "creator_id": creator_id,
                "name": validated_data["name"],
                "description": validated_data["description"],
                "icon": validated_data.get("icon", "🏆"),
                "rarity": validated_data.get("rarity", "custom"),
                "points": validated_data.get("points", 100),
                "condition": validated_data["condition"],
                "is_active": True,
                "created_at": datetime.now(),
                "awarded_count": 0,
            }

            # 保存自定义成就
            await self._save_custom_achievement(custom_achievement)

            logger.info(f"管理员 {creator_id} 创建自定义成就: {achievement_id}")
            return custom_achievement

        except Exception as e:
            logger.error(f"创建自定义成就失败: {str(e)}")
            raise

    async def get_achievement_analytics(self, days: int = 30) -> dict[str, Any]:
        """获取成就系统分析数据."""
        try:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 成就颁发统计
            achievement_stats = await self._get_achievement_statistics(start_date, end_date)

            # 用户参与度分析
            engagement_stats = await self._get_engagement_statistics(start_date, end_date)

            # 成就效果分析
            effectiveness_stats = await self._get_effectiveness_statistics(start_date, end_date)

            # 热门成就排行
            popular_achievements = await self._get_popular_achievements(start_date, end_date)

            return {
                "analysis_period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days,
                },
                "achievement_stats": achievement_stats,
                "engagement_stats": engagement_stats,
                "effectiveness_stats": effectiveness_stats,
                "popular_achievements": popular_achievements,
                "generated_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"获取成就分析失败: {str(e)}")
            raise

    # ==================== 私有方法 ====================

    async def _get_user_achievements(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户成就列表."""
        # TODO: 实现从数据库获取用户成就的逻辑
        return []

    async def _check_achievement_type(
        self,
        user_id: int,
        achievement_type: str,
        config: dict[str, Any],
        current_achievements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """检查特定类型的成就."""
        new_achievements = []

        # 获取当前该类型的最高等级
        current_level = self._get_current_achievement_level(achievement_type, current_achievements)

        # 获取用户数据
        user_data = await self._get_user_data_for_achievement(user_id, achievement_type)

        # 检查是否达到新等级
        for i, threshold in enumerate(config["levels"]):
            level = i + 1
            if level > current_level and self._check_achievement_condition(
                achievement_type, user_data, threshold
            ):
                achievement = {
                    "achievement_id": f"{achievement_type}_level_{level}",
                    "type": achievement_type,
                    "name": f"{config['name']} - 等级{level}",
                    "description": config["description"],
                    "level": level,
                    "icon": config["icon"],
                    "points": config["rewards"][i],
                    "threshold": threshold,
                    "achieved_at": datetime.now(),
                    "rarity": self._determine_rarity(level),
                }
                new_achievements.append(achievement)

        return new_achievements

    async def _check_badges(self, user_id: int) -> list[dict[str, Any]]:
        """检查徽章获得条件."""
        new_badges = []

        # 获取用户最近的学习数据
        recent_data = await self._get_recent_learning_data(user_id)

        # 检查各种徽章条件
        for badge_id, config in self.badge_config.items():
            if await self._check_badge_condition(user_id, badge_id, config, recent_data):
                badge = {
                    "badge_id": badge_id,
                    "name": config["name"],
                    "description": config["description"],
                    "rarity": config["rarity"],
                    "points": config["points"],
                    "achieved_at": datetime.now(),
                }
                new_badges.append(badge)

        return new_badges

    async def _save_achievements(self, user_id: int, achievements: list[dict[str, Any]]) -> None:
        """保存新获得的成就."""
        # TODO: 实现数据库保存逻辑
        logger.info(f"保存用户 {user_id} 的 {len(achievements)} 个新成就")

    async def _send_achievement_notifications(
        self, user_id: int, achievements: list[dict[str, Any]]
    ) -> None:
        """发送成就通知."""
        # TODO: 实现通知发送逻辑
        logger.info(f"发送成就通知给用户 {user_id}")

    async def _get_user_badges(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户徽章列表."""
        # TODO: 实现从数据库获取用户徽章的逻辑
        return []

    async def _calculate_achievement_stats(
        self, achievements: list[dict[str, Any]], badges: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """计算成就统计."""
        total_points = sum(a.get("points", 0) for a in achievements) + sum(
            b.get("points", 0) for b in badges
        )

        return {
            "total_achievements": len(achievements),
            "total_badges": len(badges),
            "total_points": total_points,
            "rare_achievements": len([a for a in achievements if a.get("rarity") == "rare"]),
            "epic_achievements": len([a for a in achievements if a.get("rarity") == "epic"]),
        }

    async def _get_achievement_progress(self, user_id: int) -> dict[str, Any]:
        """获取成就进度信息."""
        progress = {}

        for achievement_type, config in self.achievement_types.items():
            user_data = await self._get_user_data_for_achievement(user_id, achievement_type)
            current_value = self._get_achievement_current_value(achievement_type, user_data)

            # 找到下一个目标
            next_target = None
            for threshold in config["levels"]:
                threshold_value = (
                    float(threshold) if isinstance(threshold, int | float | str) else 0.0
                )
                if current_value < threshold_value:
                    next_target = threshold_value
                    break

            progress[achievement_type] = {
                "current_value": current_value,
                "next_target": next_target,
                "progress_percentage": (
                    (current_value / float(next_target) * 100) if next_target else 100
                ),
            }

        return progress

    async def _get_leaderboard_position(self, user_id: int) -> dict[str, Any]:
        """获取用户在排行榜中的位置."""
        # TODO: 实现排行榜位置计算逻辑
        return {"overall_rank": 15, "class_rank": 3, "total_users": 1000}

    def _calculate_achievement_level(self, total_points: int) -> str:
        """根据总积分计算成就等级."""
        if total_points >= 10000:
            return "传奇大师"
        elif total_points >= 5000:
            return "钻石学者"
        elif total_points >= 2000:
            return "黄金专家"
        elif total_points >= 1000:
            return "白银达人"
        elif total_points >= 500:
            return "青铜新星"
        else:
            return "初学者"

    def _get_next_level_points(self, current_points: int) -> int:
        """获取下一等级所需积分."""
        thresholds = [500, 1000, 2000, 5000, 10000]
        for threshold in thresholds:
            if current_points < threshold:
                return threshold - current_points
        return 0  # 已达到最高等级

    async def _get_leaderboard_data(
        self, limit: int, achievement_type: str | None
    ) -> list[dict[str, Any]]:
        """获取排行榜数据."""
        # TODO: 实现排行榜数据获取逻辑
        return []

    async def _verify_admin_permission(self, user_id: int) -> bool:
        """验证管理员权限."""
        # TODO: 实现权限验证逻辑
        return True

    async def _validate_achievement_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """验证成就数据."""
        required_fields = ["name", "description", "condition"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")
        return data

    async def _generate_achievement_id(self) -> str:
        """生成成就ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"custom_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def _save_custom_achievement(self, achievement: dict[str, Any]) -> None:
        """保存自定义成就."""
        # TODO: 实现数据库保存逻辑
        logger.info(f"保存自定义成就: {achievement['achievement_id']}")

    def _get_current_achievement_level(
        self, achievement_type: str, achievements: list[dict[str, Any]]
    ) -> int:
        """获取当前成就等级."""
        max_level = 0
        for achievement in achievements:
            if achievement.get("type") == achievement_type:
                level = achievement.get("level", 0)
                max_level = max(max_level, level)
        return max_level

    async def _get_user_data_for_achievement(
        self, user_id: int, achievement_type: str
    ) -> dict[str, Any]:
        """获取用户成就相关数据."""
        if achievement_type == "learning_streak":
            return {"streak_days": await self._calculate_learning_streak(user_id)}
        elif achievement_type == "question_master":
            return {"total_questions": await self._count_total_questions(user_id)}
        elif achievement_type == "accuracy_expert":
            return {"accuracy_rate": await self._calculate_accuracy_rate(user_id)}
        # 其他成就类型的数据获取
        return {}

    def _check_achievement_condition(
        self, achievement_type: str, user_data: dict[str, Any], threshold: Any
    ) -> bool:
        """检查成就条件是否满足."""
        if achievement_type == "learning_streak":
            return bool(user_data.get("streak_days", 0) >= threshold)
        elif achievement_type == "question_master":
            return bool(user_data.get("total_questions", 0) >= threshold)
        elif achievement_type == "accuracy_expert":
            return bool(user_data.get("accuracy_rate", 0) >= threshold)
        return False

    def _determine_rarity(self, level: int) -> str:
        """根据等级确定稀有度."""
        # 稀有度等级阈值常量
        LEGENDARY_THRESHOLD = 6
        EPIC_THRESHOLD = 4
        RARE_THRESHOLD = 2

        if level >= LEGENDARY_THRESHOLD:
            return "legendary"
        elif level >= EPIC_THRESHOLD:
            return "epic"
        elif level >= RARE_THRESHOLD:
            return "rare"
        else:
            return "common"

    async def _get_recent_learning_data(self, user_id: int) -> dict[str, Any]:
        """获取用户最近的学习数据."""
        # TODO: 实现最近学习数据获取逻辑
        return {}

    async def _check_badge_condition(
        self,
        user_id: int,
        badge_id: str,
        config: dict[str, Any],
        recent_data: dict[str, Any],
    ) -> bool:
        """检查徽章获得条件."""
        # TODO: 实现徽章条件检查逻辑
        return False

    def _get_achievement_current_value(
        self, achievement_type: str, user_data: dict[str, Any]
    ) -> float:
        """获取成就当前值."""
        if achievement_type == "learning_streak":
            return float(user_data.get("streak_days", 0))
        elif achievement_type == "question_master":
            return float(user_data.get("total_questions", 0))
        elif achievement_type == "accuracy_expert":
            return float(user_data.get("accuracy_rate", 0))
        return 0

    # 简化实现的统计方法
    async def _get_achievement_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        return {"total_awarded": 150, "daily_average": 5}

    async def _get_engagement_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        return {"active_users": 80, "engagement_rate": 0.75}

    async def _get_effectiveness_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        return {"motivation_increase": 0.25, "retention_improvement": 0.15}

    async def _get_popular_achievements(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        return []

    async def _calculate_learning_streak(self, user_id: int) -> int:
        return 5  # 简化实现

    async def _count_total_questions(self, user_id: int) -> int:
        return 250  # 简化实现

    async def _calculate_accuracy_rate(self, user_id: int) -> float:
        return 0.78  # 简化实现
