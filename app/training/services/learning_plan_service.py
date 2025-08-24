"""学习计划服务 - 智能学习计划生成和管理."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import TrainingType
from app.training.models.training_models import TrainingRecord, TrainingSession
from app.training.utils.plan_generator import PlanGenerator
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class LearningPlanService:
    """学习计划服务 - 智能生成和管理个性化学习计划."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化学习计划服务."""
        self.db = db
        self.plan_generator = PlanGenerator()

        # 学习计划配置
        self.plan_config = {
            "default_duration_weeks": 12,  # 默认计划周期
            "daily_study_time_minutes": 60,  # 每日学习时间
            "weekly_sessions": 5,  # 每周学习次数
            "difficulty_progression": 0.1,  # 难度递增率
            "review_frequency_days": 7,  # 复习频率
        }

        # 训练类型权重配置
        self.training_weights = {
            TrainingType.VOCABULARY: 0.25,  # 词汇训练25%
            TrainingType.LISTENING: 0.20,  # 听力训练20%
            TrainingType.READING: 0.25,  # 阅读训练25%
            TrainingType.WRITING: 0.15,  # 写作训练15%
            TrainingType.TRANSLATION: 0.15,  # 翻译训练15%
        }

    async def generate_learning_plan(
        self, student_id: int, plan_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """生成个性化学习计划."""
        try:
            # 获取学生信息
            student = await self.db.get(User, student_id)
            if not student:
                raise ValueError(f"学生不存在: {student_id}")

            # 合并配置
            config = {**self.plan_config, **(plan_config or {})}

            # 分析学生当前水平
            student_level = await self._analyze_student_level(student_id)

            # 获取学习历史和偏好
            learning_history = await self._get_learning_history(student_id)

            # 识别薄弱环节
            weak_areas = await self._identify_weak_areas(student_id)

            # 生成学习计划
            plan_data = await self.plan_generator.generate_plan(
                student_id=student_id,
                student_level=student_level,
                learning_history=learning_history,
                weak_areas=weak_areas,
                config=config,
            )

            # 保存学习计划
            plan_id = await self._save_learning_plan(student_id, plan_data)

            logger.info(f"为学生 {student_id} 生成学习计划，计划ID: {plan_id}")
            return {
                "plan_id": plan_id,
                "student_id": student_id,
                "plan_data": plan_data,
                "generated_at": datetime.now(),
                "status": "active",
            }

        except Exception as e:
            logger.error(f"生成学习计划失败: {str(e)}")
            raise

    async def get_learning_plan(
        self, student_id: int, plan_id: int | None = None
    ) -> dict[str, Any]:
        """获取学习计划."""
        try:
            # 如果没有指定计划ID，获取最新的活跃计划
            if plan_id is None:
                plan_id = await self._get_latest_plan_id(student_id)

            if not plan_id:
                return {"status": "no_plan", "message": "未找到学习计划"}

            # 从数据库获取计划数据
            plan_data = await self._load_learning_plan(plan_id)

            # 计算计划进度
            progress = await self._calculate_plan_progress(student_id, plan_id)

            # 获取今日任务
            today_tasks = await self._get_today_tasks(student_id, plan_id)

            # 获取本周任务
            week_tasks = await self._get_week_tasks(student_id, plan_id)

            return {
                "plan_id": plan_id,
                "student_id": student_id,
                "plan_data": plan_data,
                "progress": progress,
                "today_tasks": today_tasks,
                "week_tasks": week_tasks,
                "status": "active",
            }

        except Exception as e:
            logger.error(f"获取学习计划失败: {str(e)}")
            raise

    async def update_learning_plan(
        self, student_id: int, plan_id: int, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """更新学习计划."""
        try:
            # 验证权限
            if not await self._verify_plan_ownership(student_id, plan_id):
                raise ValueError("无权限修改此学习计划")

            # 获取当前计划
            current_plan = await self._load_learning_plan(plan_id)

            # 应用更新
            updated_plan = await self._apply_plan_updates(current_plan, updates)

            # 验证更新后的计划
            await self._validate_plan_data(updated_plan)

            # 保存更新
            await self._update_learning_plan_data(plan_id, updated_plan)

            # 记录更新日志
            await self._log_plan_update(student_id, plan_id, updates)

            logger.info(f"学习计划更新成功: 学生{student_id}, 计划{plan_id}")
            return {
                "plan_id": plan_id,
                "student_id": student_id,
                "updated_plan": updated_plan,
                "updated_at": datetime.now(),
                "status": "updated",
            }

        except Exception as e:
            logger.error(f"更新学习计划失败: {str(e)}")
            raise

    async def adjust_plan_difficulty(
        self, student_id: int, plan_id: int, performance_data: dict[str, Any]
    ) -> dict[str, Any]:
        """根据学习表现调整计划难度."""
        try:
            # 分析表现数据
            performance_analysis = await self._analyze_performance(performance_data)

            # 计算难度调整建议
            adjustment_suggestions = await self._calculate_difficulty_adjustment(
                student_id, performance_analysis
            )

            # 应用难度调整
            if adjustment_suggestions["should_adjust"]:
                adjustment_data = {
                    "difficulty_adjustment": adjustment_suggestions["adjustment"],
                    "training_intensity": adjustment_suggestions["intensity"],
                    "focus_areas": adjustment_suggestions["focus_areas"],
                }

                await self.update_learning_plan(student_id, plan_id, adjustment_data)

                logger.info(
                    f"计划难度调整完成: 学生{student_id}, "
                    f"调整幅度{adjustment_suggestions['adjustment']}"
                )

            return {
                "plan_id": plan_id,
                "student_id": student_id,
                "performance_analysis": performance_analysis,
                "adjustment_applied": adjustment_suggestions["should_adjust"],
                "adjustment_details": adjustment_suggestions,
                "adjusted_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"调整计划难度失败: {str(e)}")
            raise

    async def get_plan_statistics(self, student_id: int, days: int = 30) -> dict[str, Any]:
        """获取学习计划统计数据."""
        try:
            # 获取时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 计划完成统计
            completion_stats = await self._calculate_completion_stats(
                student_id, start_date, end_date
            )

            # 学习时间统计
            time_stats = await self._calculate_time_stats(student_id, start_date, end_date)

            # 进度统计
            progress_stats = await self._calculate_progress_stats(student_id, start_date, end_date)

            # 效果统计
            effectiveness_stats = await self._calculate_effectiveness_stats(
                student_id, start_date, end_date
            )

            return {
                "student_id": student_id,
                "statistics_period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days,
                },
                "completion_stats": completion_stats,
                "time_stats": time_stats,
                "progress_stats": progress_stats,
                "effectiveness_stats": effectiveness_stats,
                "generated_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"获取计划统计失败: {str(e)}")
            raise

    # ==================== 私有方法 ====================

    async def _analyze_student_level(self, student_id: int) -> dict[str, Any]:
        """分析学生当前水平."""
        # 获取最近的训练记录
        stmt = (
            select(TrainingRecord)
            .where(TrainingRecord.student_id == student_id)
            .order_by(desc(TrainingRecord.created_at))
            .limit(50)
        )

        result = await self.db.execute(stmt)
        recent_records = result.scalars().all()

        if not recent_records:
            return {
                "overall_level": "beginner",
                "confidence": 0.5,
                "training_type_levels": {},
            }

        # 按训练类型分析水平
        type_levels = {}
        # TODO: 需要通过session关联获取training_type，这里简化处理
        for training_type in TrainingType:
            # 简化处理：假设所有记录都是同一类型
            if recent_records:
                avg_score = sum(r.score for r in recent_records) / len(recent_records)
                type_levels[training_type.value] = self._score_to_level(avg_score)

        # 计算整体水平
        overall_score = sum(r.score for r in recent_records) / len(recent_records)
        overall_level = self._score_to_level(overall_score)

        return {
            "overall_level": overall_level,
            "confidence": min(len(recent_records) / 50.0, 1.0),
            "training_type_levels": type_levels,
        }

    async def _get_learning_history(self, student_id: int) -> dict[str, Any]:
        """获取学习历史."""
        # 获取学习会话统计
        stmt = select(
            func.count(TrainingSession.id).label("total_sessions"),
        ).where(TrainingSession.student_id == student_id)

        result = await self.db.execute(stmt)
        session_stats = result.first()

        # 获取训练记录统计
        stmt = select(
            func.count(TrainingRecord.id).label("total_records"),
            func.avg(TrainingRecord.score).label("avg_score"),
            func.count(TrainingRecord.id).filter(TrainingRecord.is_correct).label("correct_count"),  # noqa: E712
        ).where(TrainingRecord.student_id == student_id)

        result = await self.db.execute(stmt)
        record_stats = result.first()

        return {
            "total_sessions": session_stats.total_sessions if session_stats else 0,
            "avg_session_duration": 0,  # TODO: 计算会话时长
            "total_study_time": 0,  # TODO: 计算总学习时间
            "total_questions": record_stats.total_records if record_stats else 0,
            "avg_score": record_stats.avg_score if record_stats else 0,
            "accuracy_rate": (record_stats.correct_count if record_stats else 0)
            / max(record_stats.total_records if record_stats else 1, 1),
        }

    async def _identify_weak_areas(self, student_id: int) -> list[dict[str, Any]]:
        """识别薄弱环节."""
        # 按训练类型统计错误率
        weak_areas = []

        for training_type in TrainingType:
            stmt = select(
                func.count(TrainingRecord.id).label("total"),
                func.count(TrainingRecord.id).filter(~TrainingRecord.is_correct).label("errors"),  # noqa: E712
                func.avg(TrainingRecord.score).label("avg_score"),
            ).where(
                and_(
                    TrainingRecord.student_id == student_id,
                    # TODO: 需要通过session关联获取training_type
                )
            )

            result = await self.db.execute(stmt)
            stats = result.first()

            if stats and stats.total and stats.total > 5:  # 至少有5次记录
                error_rate = (stats.errors or 0) / stats.total
                if error_rate > 0.3:  # 错误率超过30%
                    weak_areas.append(
                        {
                            "training_type": training_type.value,
                            "error_rate": error_rate,
                            "avg_score": stats.avg_score or 0,
                            "total_attempts": stats.total,
                            "priority": "high" if error_rate > 0.5 else "medium",
                        }
                    )

        # 按优先级排序
        weak_areas.sort(key=lambda x: x["error_rate"], reverse=True)
        return weak_areas

    def _score_to_level(self, score: float) -> str:
        """将分数转换为水平等级."""
        if score >= 0.9:
            return "advanced"
        elif score >= 0.7:
            return "intermediate"
        elif score >= 0.5:
            return "basic"
        else:
            return "beginner"

    async def _save_learning_plan(self, student_id: int, plan_data: dict[str, Any]) -> int:
        """保存学习计划到数据库."""
        # 这里应该保存到数据库，简化处理返回模拟ID
        # TODO: 实现实际的数据库保存逻辑
        return hash(f"{student_id}_{datetime.now().isoformat()}") % 1000000

    async def _get_latest_plan_id(self, student_id: int) -> int | None:
        """获取最新的计划ID."""
        # TODO: 实现从数据库获取最新计划ID的逻辑
        return 1  # 简化处理

    async def _load_learning_plan(self, plan_id: int) -> dict[str, Any]:
        """从数据库加载学习计划."""
        # TODO: 实现从数据库加载计划的逻辑
        return {"plan_id": plan_id, "status": "active"}

    async def _calculate_plan_progress(self, student_id: int, plan_id: int) -> dict[str, Any]:
        """计算计划进度."""
        # TODO: 实现进度计算逻辑
        return {"overall_progress": 0.6, "weekly_progress": 0.8}

    async def _get_today_tasks(self, student_id: int, plan_id: int) -> list[dict[str, Any]]:
        """获取今日任务."""
        # TODO: 实现今日任务获取逻辑
        return []

    async def _get_week_tasks(self, student_id: int, plan_id: int) -> list[dict[str, Any]]:
        """获取本周任务."""
        # TODO: 实现本周任务获取逻辑
        return []

    async def _verify_plan_ownership(self, student_id: int, plan_id: int) -> bool:
        """验证计划所有权."""
        # TODO: 实现所有权验证逻辑
        return True

    async def _apply_plan_updates(
        self, current_plan: dict[str, Any], updates: dict[str, Any]
    ) -> dict[str, Any]:
        """应用计划更新."""
        updated_plan = current_plan.copy()
        updated_plan.update(updates)
        return updated_plan

    async def _validate_plan_data(self, plan_data: dict[str, Any]) -> None:
        """验证计划数据."""
        # TODO: 实现计划数据验证逻辑
        pass

    async def _update_learning_plan_data(self, plan_id: int, plan_data: dict[str, Any]) -> None:
        """更新计划数据."""
        # TODO: 实现数据库更新逻辑
        pass

    async def _log_plan_update(
        self, student_id: int, plan_id: int, updates: dict[str, Any]
    ) -> None:
        """记录计划更新日志."""
        logger.info(f"计划更新: 学生{student_id}, 计划{plan_id}, 更新内容{updates}")

    async def _analyze_performance(self, performance_data: dict[str, Any]) -> dict[str, Any]:
        """分析学习表现."""
        # TODO: 实现表现分析逻辑
        return {"trend": "improving", "score": 0.75}

    async def _calculate_difficulty_adjustment(
        self, student_id: int, performance_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """计算难度调整建议."""
        # TODO: 实现难度调整计算逻辑
        return {
            "should_adjust": True,
            "adjustment": 0.1,
            "intensity": "moderate",
            "focus_areas": ["vocabulary"],
        }

    async def _calculate_completion_stats(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """计算完成统计."""
        # TODO: 实现完成统计逻辑
        return {"completion_rate": 0.8, "tasks_completed": 24, "tasks_total": 30}

    async def _calculate_time_stats(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """计算时间统计."""
        # TODO: 实现时间统计逻辑
        return {"total_time": 1800, "avg_daily_time": 60, "study_days": 20}

    async def _calculate_progress_stats(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """计算进度统计."""
        # TODO: 实现进度统计逻辑
        return {"progress_rate": 0.75, "milestones_reached": 3, "milestones_total": 4}

    async def _calculate_effectiveness_stats(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """计算效果统计."""
        # TODO: 实现效果统计逻辑
        return {
            "improvement_rate": 0.15,
            "accuracy_improvement": 0.1,
            "speed_improvement": 0.05,
        }
