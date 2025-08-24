"""学习计划生成器 - 智能生成个性化学习计划."""

import logging
from datetime import datetime
from typing import Any

from app.shared.models.enums import TrainingType

logger = logging.getLogger(__name__)


class PlanGenerator:
    """学习计划生成器 - 基于学生水平和目标生成个性化学习计划."""

    def __init__(self) -> None:
        """初始化计划生成器."""
        # 计划模板配置
        self.plan_templates = {
            "beginner": {
                "duration_weeks": 16,
                "daily_time_minutes": 45,
                "sessions_per_week": 4,
                "difficulty_progression": 0.05,
                "focus_areas": [TrainingType.VOCABULARY, TrainingType.LISTENING],
            },
            "basic": {
                "duration_weeks": 12,
                "daily_time_minutes": 60,
                "sessions_per_week": 5,
                "difficulty_progression": 0.08,
                "focus_areas": [
                    TrainingType.READING,
                    TrainingType.VOCABULARY,
                    TrainingType.LISTENING,
                ],
            },
            "intermediate": {
                "duration_weeks": 10,
                "daily_time_minutes": 75,
                "sessions_per_week": 5,
                "difficulty_progression": 0.1,
                "focus_areas": [
                    TrainingType.WRITING,
                    TrainingType.TRANSLATION,
                    TrainingType.READING,
                ],
            },
            "advanced": {
                "duration_weeks": 8,
                "daily_time_minutes": 90,
                "sessions_per_week": 6,
                "difficulty_progression": 0.12,
                "focus_areas": [TrainingType.WRITING, TrainingType.TRANSLATION],
            },
        }

        # 训练类型权重配置
        self.training_weights = {
            "beginner": {
                TrainingType.VOCABULARY: 0.4,
                TrainingType.LISTENING: 0.3,
                TrainingType.READING: 0.2,
                TrainingType.WRITING: 0.05,
                TrainingType.TRANSLATION: 0.05,
            },
            "basic": {
                TrainingType.VOCABULARY: 0.3,
                TrainingType.LISTENING: 0.25,
                TrainingType.READING: 0.25,
                TrainingType.WRITING: 0.1,
                TrainingType.TRANSLATION: 0.1,
            },
            "intermediate": {
                TrainingType.VOCABULARY: 0.2,
                TrainingType.LISTENING: 0.2,
                TrainingType.READING: 0.25,
                TrainingType.WRITING: 0.2,
                TrainingType.TRANSLATION: 0.15,
            },
            "advanced": {
                TrainingType.VOCABULARY: 0.15,
                TrainingType.LISTENING: 0.2,
                TrainingType.READING: 0.2,
                TrainingType.WRITING: 0.25,
                TrainingType.TRANSLATION: 0.2,
            },
        }

    async def generate_plan(
        self,
        student_id: int,
        student_level: dict[str, Any],
        learning_history: dict[str, Any],
        weak_areas: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """生成个性化学习计划."""
        try:
            # 确定学生水平
            level = student_level.get("overall_level", "beginner")

            # 获取计划模板
            template = self.plan_templates.get(level, self.plan_templates["beginner"])

            # 应用用户配置
            plan_config = self._merge_config(template, config)

            # 生成计划结构
            plan_structure = await self._generate_plan_structure(
                student_id, level, plan_config, weak_areas
            )

            # 生成每周计划
            weekly_plans = await self._generate_weekly_plans(
                plan_structure, student_level, weak_areas
            )

            # 生成每日任务
            daily_tasks = await self._generate_daily_tasks(weekly_plans, plan_config, student_level)

            # 设置复习计划
            review_schedule = await self._generate_review_schedule(plan_structure, plan_config)

            # 设置里程碑
            milestones = await self._generate_milestones(plan_structure, weekly_plans)

            # 生成完整计划
            learning_plan = {
                "plan_id": f"plan_{student_id}_{datetime.now().strftime('%Y%m%d')}",
                "student_id": student_id,
                "student_level": level,
                "plan_config": plan_config,
                "plan_structure": plan_structure,
                "weekly_plans": weekly_plans,
                "daily_tasks": daily_tasks,
                "review_schedule": review_schedule,
                "milestones": milestones,
                "created_at": datetime.now(),
                "status": "active",
            }

            logger.info(f"为学生 {student_id} 生成学习计划，水平: {level}")
            return learning_plan

        except Exception as e:
            logger.error(f"生成学习计划失败: {str(e)}")
            raise

    def _merge_config(
        self, template: dict[str, Any], user_config: dict[str, Any]
    ) -> dict[str, Any]:
        """合并配置."""
        merged = template.copy()

        # 应用用户自定义配置
        if "duration_weeks" in user_config:
            merged["duration_weeks"] = user_config["duration_weeks"]
        if "daily_study_time_minutes" in user_config:
            merged["daily_time_minutes"] = user_config["daily_study_time_minutes"]
        if "weekly_sessions" in user_config:
            merged["sessions_per_week"] = user_config["weekly_sessions"]

        return merged

    async def _generate_plan_structure(
        self,
        student_id: int,
        level: str,
        config: dict[str, Any],
        weak_areas: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """生成计划结构."""
        # 计算总体目标
        overall_goals = await self._define_overall_goals(level, config)

        # 分配训练类型权重
        training_allocation = await self._allocate_training_types(level, weak_areas)

        # 设置难度进阶
        difficulty_progression = await self._plan_difficulty_progression(level, config)

        # 计算时间分配
        time_allocation = await self._calculate_time_allocation(config, training_allocation)

        return {
            "overall_goals": overall_goals,
            "training_allocation": training_allocation,
            "difficulty_progression": difficulty_progression,
            "time_allocation": time_allocation,
            "duration_weeks": config["duration_weeks"],
            "total_sessions": config["duration_weeks"] * config["sessions_per_week"],
        }

    async def _generate_weekly_plans(
        self,
        plan_structure: dict[str, Any],
        student_level: dict[str, Any],
        weak_areas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """生成每周计划."""
        weekly_plans = []
        duration_weeks = plan_structure["duration_weeks"]

        for week in range(1, duration_weeks + 1):
            # 计算本周难度
            week_difficulty = self._calculate_week_difficulty(week, duration_weeks, plan_structure)

            # 分配本周训练类型
            week_training_types = self._allocate_week_training_types(
                week, plan_structure["training_allocation"], weak_areas
            )

            # 设置本周目标
            week_goals = self._set_week_goals(week, week_difficulty, week_training_types)

            # 计算本周时间分配
            week_time_allocation = self._calculate_week_time_allocation(
                plan_structure["time_allocation"], week_training_types
            )

            weekly_plan = {
                "week_number": week,
                "week_difficulty": week_difficulty,
                "training_types": week_training_types,
                "goals": week_goals,
                "time_allocation": week_time_allocation,
                "estimated_questions": self._estimate_week_questions(week_time_allocation),
            }

            weekly_plans.append(weekly_plan)

        return weekly_plans

    async def _generate_daily_tasks(
        self,
        weekly_plans: list[dict[str, Any]],
        config: dict[str, Any],
        student_level: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """生成每日任务."""
        daily_tasks = {}
        sessions_per_week = config["sessions_per_week"]

        for weekly_plan in weekly_plans:
            week_number = weekly_plan["week_number"]

            # 生成本周的每日任务
            week_tasks = []
            for day in range(1, sessions_per_week + 1):
                daily_task = self._generate_single_day_task(week_number, day, weekly_plan, config)
                week_tasks.append(daily_task)

            daily_tasks[f"week_{week_number}"] = week_tasks

        return daily_tasks

    async def _generate_review_schedule(
        self, plan_structure: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """生成复习计划."""
        # 设置复习频率
        review_frequency = {
            "daily_review": True,  # 每日复习
            "weekly_review": True,  # 每周复习
            "monthly_review": True,  # 每月复习
        }

        # 设置复习内容比例
        review_content_ratio = {
            "recent_errors": 0.4,  # 最近错题40%
            "weak_areas": 0.3,  # 薄弱环节30%
            "random_review": 0.3,  # 随机复习30%
        }

        # 计算复习时间分配
        daily_review_time = config["daily_time_minutes"] * 0.2  # 20%时间用于复习

        return {
            "review_frequency": review_frequency,
            "content_ratio": review_content_ratio,
            "daily_review_time_minutes": daily_review_time,
            "review_intervals": [1, 3, 7, 15, 30],  # 复习间隔天数
        }

    async def _generate_milestones(
        self, plan_structure: dict[str, Any], weekly_plans: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成里程碑."""
        milestones: list[dict[str, Any]] = []
        duration_weeks = plan_structure["duration_weeks"]

        # 每4周设置一个里程碑
        milestone_intervals = max(1, duration_weeks // 4)

        for i in range(1, duration_weeks + 1, milestone_intervals):
            milestone_week = min(i + milestone_intervals - 1, duration_weeks)

            milestone = {
                "milestone_id": len(milestones) + 1,
                "week_number": milestone_week,
                "title": f"第{milestone_week}周里程碑",
                "description": f"完成前{milestone_week}周的学习目标",
                "target_metrics": {
                    "completion_rate": 0.8,
                    "accuracy_rate": 0.75,
                    "consistency_score": 0.8,
                },
                "reward": self._generate_milestone_reward(len(milestones) + 1),
            }

            milestones.append(milestone)

        return milestones

    # ==================== 辅助方法 ====================

    async def _define_overall_goals(self, level: str, config: dict[str, Any]) -> dict[str, Any]:
        """定义总体目标."""
        level_goals = {
            "beginner": {
                "target_accuracy": 0.7,
                "target_speed": "slow",
                "vocabulary_target": 1000,
                "skill_focus": "基础技能建立",
            },
            "basic": {
                "target_accuracy": 0.75,
                "target_speed": "medium",
                "vocabulary_target": 2000,
                "skill_focus": "技能巩固提升",
            },
            "intermediate": {
                "target_accuracy": 0.8,
                "target_speed": "medium-fast",
                "vocabulary_target": 3000,
                "skill_focus": "综合能力发展",
            },
            "advanced": {
                "target_accuracy": 0.85,
                "target_speed": "fast",
                "vocabulary_target": 4000,
                "skill_focus": "高级技能精通",
            },
        }

        return level_goals.get(level, level_goals["beginner"])

    async def _allocate_training_types(
        self, level: str, weak_areas: list[dict[str, Any]]
    ) -> dict[str, float]:
        """分配训练类型权重."""
        base_weights = self.training_weights.get(level, self.training_weights["beginner"])
        adjusted_weights: dict[str, float] = {k.value: v for k, v in base_weights.items()}

        # 根据薄弱环节调整权重
        for weak_area in weak_areas:
            training_type_str = weak_area.get("training_type")
            if training_type_str and training_type_str in adjusted_weights:
                # 增加薄弱环节的权重
                boost = 0.1 * (1 if weak_area.get("priority") == "high" else 0.5)
                adjusted_weights[training_type_str] += boost

        # 归一化权重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

        return adjusted_weights

    async def _plan_difficulty_progression(
        self, level: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """规划难度进阶."""
        template = self.plan_templates.get(level, self.plan_templates["beginner"])
        progression_rate = template.get("difficulty_progression", 0.1)
        if not isinstance(progression_rate, int | float):
            progression_rate = 0.1

        # 计算每周难度
        duration_weeks = config["duration_weeks"]
        weekly_difficulties = []

        for week in range(1, duration_weeks + 1):
            # 线性增长，但有上限
            base_difficulty = 0.3 if level == "beginner" else 0.5
            week_difficulty = min(0.9, base_difficulty + float(week - 1) * progression_rate)
            weekly_difficulties.append(week_difficulty)

        return {
            "progression_rate": progression_rate,
            "weekly_difficulties": weekly_difficulties,
            "max_difficulty": max(weekly_difficulties),
        }

    async def _calculate_time_allocation(
        self, config: dict[str, Any], training_allocation: dict[str, float]
    ) -> dict[str, int]:
        """计算时间分配."""
        daily_time = config["daily_time_minutes"]
        time_allocation = {}

        for training_type, weight in training_allocation.items():
            allocated_time = int(daily_time * weight)
            time_allocation[training_type] = allocated_time

        return time_allocation

    def _calculate_week_difficulty(
        self, week: int, total_weeks: int, plan_structure: dict[str, Any]
    ) -> float:
        """计算本周难度."""
        difficulties = plan_structure["difficulty_progression"]["weekly_difficulties"]
        return float(difficulties[week - 1] if week <= len(difficulties) else difficulties[-1])

    def _allocate_week_training_types(
        self,
        week: int,
        base_allocation: dict[str, float],
        weak_areas: list[dict[str, Any]],
    ) -> dict[str, float]:
        """分配本周训练类型."""
        # 基础分配
        week_allocation = base_allocation.copy()

        # 每4周重点关注薄弱环节
        if week % 4 == 0 and weak_areas:
            weak_area = weak_areas[0]  # 最薄弱的环节
            training_type_str = weak_area.get("training_type")
            if training_type_str:
                try:
                    training_type = TrainingType(training_type_str)
                    if training_type in week_allocation:
                        # 本周额外关注薄弱环节
                        week_allocation[training_type] *= 1.5
                except ValueError:
                    pass

        # 归一化
        total = sum(week_allocation.values())
        if total > 0:
            week_allocation = {k: v / total for k, v in week_allocation.items()}

        return week_allocation

    def _set_week_goals(
        self, week: int, difficulty: float, training_types: dict[str, float]
    ) -> dict[str, Any]:
        """设置本周目标."""
        # 主要训练类型
        main_type = max(training_types.items(), key=lambda x: x[1])[0]

        return {
            "main_focus": main_type,
            "target_accuracy": max(0.6, 0.9 - difficulty * 0.2),
            "target_questions": int(50 + week * 5),  # 逐周增加
            "skill_goals": [f"提升{main_type}技能"],
        }

    def _calculate_week_time_allocation(
        self, base_allocation: dict[str, int], week_types: dict[str, float]
    ) -> dict[str, int]:
        """计算本周时间分配."""
        week_allocation = {}
        total_base_time = sum(base_allocation.values())

        for training_type, weight in week_types.items():
            allocated_time = int(total_base_time * weight)
            week_allocation[training_type] = allocated_time

        return week_allocation

    def _estimate_week_questions(self, time_allocation: dict[str, int]) -> dict[str, int]:
        """估算本周题目数量."""
        # 假设每分钟完成1题
        return dict(time_allocation)

    def _generate_single_day_task(
        self, week: int, day: int, weekly_plan: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """生成单日任务."""
        daily_time = config["daily_time_minutes"]

        # 从本周计划中分配任务
        week_training_types = weekly_plan["training_types"]
        main_type = max(week_training_types.items(), key=lambda x: x[1])[0]

        return {
            "day": day,
            "week": week,
            "total_time_minutes": daily_time,
            "main_training_type": main_type,
            "tasks": [
                {
                    "type": "warm_up",
                    "duration_minutes": 5,
                    "description": "热身练习",
                },
                {
                    "type": "main_training",
                    "duration_minutes": daily_time - 15,
                    "training_type": main_type,
                    "description": f"主要{main_type}训练",
                },
                {
                    "type": "review",
                    "duration_minutes": 10,
                    "description": "复习巩固",
                },
            ],
            "target_questions": daily_time,  # 假设每分钟1题
            "difficulty_level": weekly_plan["week_difficulty"],
        }

    def _generate_milestone_reward(self, milestone_number: int) -> dict[str, Any]:
        """生成里程碑奖励."""
        rewards = [
            {"type": "badge", "name": "学习新手", "description": "完成第一个里程碑"},
            {"type": "badge", "name": "坚持不懈", "description": "保持学习连续性"},
            {"type": "badge", "name": "进步明显", "description": "学习效果显著提升"},
            {"type": "badge", "name": "学习达人", "description": "完成高级学习目标"},
        ]

        reward_index = min(milestone_number - 1, len(rewards) - 1)
        return rewards[reward_index]
