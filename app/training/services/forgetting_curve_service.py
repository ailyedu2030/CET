"""遗忘曲线服务 - 基于艾宾浩斯遗忘曲线的智能复习推荐."""

import logging
import math
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.training.models.training_models import Question, TrainingRecord
from app.training.schemas.adaptive_learning_schemas import (
    ForgettingCurveResponse,
    ReviewScheduleResponse,
)

logger = logging.getLogger(__name__)


class ForgettingCurveService:
    """遗忘曲线服务 - 科学的记忆管理和复习调度."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化遗忘曲线服务."""
        self.db = db

        # 艾宾浩斯遗忘曲线参数
        self.forgetting_curve_params = {
            "initial_retention": 1.0,  # 初始记忆保持率
            "decay_constant": 0.5,  # 衰减常数
            "review_boost": 0.3,  # 复习增强系数
            "mastery_threshold": 0.8,  # 掌握阈值
            "review_threshold": 0.6,  # 复习阈值
        }

        # 复习间隔配置（天）
        self.review_intervals = {
            "first_review": 1,  # 第一次复习
            "second_review": 3,  # 第二次复习
            "third_review": 7,  # 第三次复习
            "fourth_review": 15,  # 第四次复习
            "fifth_review": 30,  # 第五次复习
            "maintenance": 60,  # 维护性复习
        }

    async def calculate_retention_rate(self, student_id: int, question_id: int) -> float:
        """计算当前记忆保持率."""
        try:
            # 获取学生对该题目的学习记录
            learning_records = await self._get_learning_records(student_id, question_id)

            if not learning_records:
                return 0.0

            # 计算基于遗忘曲线的保持率
            current_time = datetime.now()
            total_retention = 0.0

            for record in learning_records:
                # 计算时间间隔（天）
                time_elapsed = (current_time - record.created_at).total_seconds() / 86400

                # 计算初始记忆强度
                initial_strength = self._calculate_initial_strength(record)

                # 应用遗忘曲线公式：R(t) = e^(-t/S)
                retention = math.exp(-time_elapsed / initial_strength)

                # 累积保持率（考虑多次学习的叠加效应）
                total_retention += retention * (1 - total_retention)

            # 确保保持率在合理范围内
            final_retention = min(max(total_retention, 0.0), 1.0)

            logger.debug(
                f"计算记忆保持率: 学生{student_id}, 题目{question_id}, 保持率{final_retention:.3f}"
            )
            return final_retention

        except Exception as e:
            logger.error(f"计算记忆保持率失败: {str(e)}")
            return 0.0

    async def get_review_schedule(
        self, student_id: int, days_ahead: int = 7
    ) -> ReviewScheduleResponse:
        """获取复习计划."""
        try:
            # 获取需要复习的题目
            review_items = await self._identify_review_items(student_id)

            # 按优先级排序
            prioritized_items = await self._prioritize_review_items(review_items)

            # 生成未来几天的复习计划
            daily_schedule = {}
            for day in range(days_ahead):
                target_date = datetime.now() + timedelta(days=day)
                daily_items = self._schedule_daily_reviews(prioritized_items, target_date, day)
                daily_schedule[target_date.strftime("%Y-%m-%d")] = daily_items

            # 计算统计信息
            total_items = len(prioritized_items)
            urgent_items = len([item for item in prioritized_items if item["priority"] == "urgent"])

            return ReviewScheduleResponse(
                student_id=student_id,
                schedule_period_days=days_ahead,
                total_review_items=total_items,
                urgent_review_items=urgent_items,
                daily_schedule=daily_schedule,
                generated_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"生成复习计划失败: {str(e)}")
            raise

    async def update_memory_strength(
        self, student_id: int, question_id: int, performance_score: float
    ) -> dict[str, Any]:
        """更新记忆强度."""
        try:
            # 获取当前记忆状态
            current_retention = await self.calculate_retention_rate(student_id, question_id)

            # 计算新的记忆强度
            performance_factor = max(0.1, min(1.0, performance_score))
            strength_boost = self.forgetting_curve_params["review_boost"] * performance_factor

            # 更新记忆强度（考虑遗忘和复习的综合效应）
            new_retention = min(1.0, current_retention + strength_boost)

            # 计算下次复习时间
            next_review_date = self._calculate_next_review_date(new_retention, performance_score)

            # 评估掌握程度
            mastery_level = self._evaluate_mastery_level(new_retention, performance_score)

            memory_update = {
                "student_id": student_id,
                "question_id": question_id,
                "previous_retention": current_retention,
                "new_retention": new_retention,
                "performance_score": performance_score,
                "strength_boost": strength_boost,
                "next_review_date": next_review_date,
                "mastery_level": mastery_level,
                "updated_at": datetime.now(),
            }

            logger.info(
                f"更新记忆强度: 学生{student_id}, 题目{question_id}, "
                f"保持率{current_retention:.3f}→{new_retention:.3f}"
            )
            return memory_update

        except Exception as e:
            logger.error(f"更新记忆强度失败: {str(e)}")
            return {}

    async def get_forgetting_curve_analysis(
        self, student_id: int, question_id: int
    ) -> ForgettingCurveResponse:
        """获取遗忘曲线分析."""
        try:
            # 获取学习历史
            learning_records = await self._get_learning_records(student_id, question_id)

            if not learning_records:
                return ForgettingCurveResponse(
                    student_id=student_id,
                    question_id=question_id,
                    current_retention=0.0,
                    learning_sessions=0,
                    curve_data=[],
                    next_review_date=datetime.now() + timedelta(days=1),
                    mastery_status="not_started",
                    analysis_time=datetime.now(),
                )

            # 计算当前保持率
            current_retention = await self.calculate_retention_rate(student_id, question_id)

            # 生成遗忘曲线数据点
            curve_data = self._generate_curve_data(learning_records)

            # 预测下次复习时间
            next_review_date = self._calculate_next_review_date(current_retention, 0.8)

            # 评估掌握状态
            mastery_status = self._evaluate_mastery_level(current_retention, 0.8)

            return ForgettingCurveResponse(
                student_id=student_id,
                question_id=question_id,
                current_retention=current_retention,
                learning_sessions=len(learning_records),
                curve_data=curve_data,
                next_review_date=next_review_date,
                mastery_status=mastery_status,
                analysis_time=datetime.now(),
            )

        except Exception as e:
            logger.error(f"遗忘曲线分析失败: {str(e)}")
            raise

    # ==================== 私有方法 ====================

    async def _get_learning_records(
        self, student_id: int, question_id: int
    ) -> list[TrainingRecord]:
        """获取学习记录."""
        stmt = (
            select(TrainingRecord)
            .where(
                and_(
                    TrainingRecord.student_id == student_id,
                    TrainingRecord.question_id == question_id,
                )
            )
            .order_by(TrainingRecord.created_at)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _calculate_initial_strength(self, record: TrainingRecord) -> float:
        """计算初始记忆强度."""
        # 基于答题表现计算记忆强度
        accuracy = record.score / max(getattr(record, "max_score", 100), 1)

        # 基础强度
        base_strength = 1.0

        # 根据准确率调整
        if accuracy >= 0.9:
            strength_multiplier = 3.0  # 高准确率，记忆更持久
        elif accuracy >= 0.7:
            strength_multiplier = 2.0
        elif accuracy >= 0.5:
            strength_multiplier = 1.5
        else:
            strength_multiplier = 1.0  # 低准确率，记忆较弱

        return base_strength * strength_multiplier

    async def _identify_review_items(self, student_id: int) -> list[dict[str, Any]]:
        """识别需要复习的题目."""
        # 获取学生的所有学习记录
        stmt = (
            select(TrainingRecord, Question)
            .join(Question, TrainingRecord.question_id == Question.id)
            .where(TrainingRecord.student_id == student_id)
            .order_by(desc(TrainingRecord.created_at))
        )

        result = await self.db.execute(stmt)
        records = result.all()

        review_items = []
        processed_questions = set()

        for record, question in records:
            if question.id in processed_questions:
                continue
            processed_questions.add(question.id)

            # 计算当前保持率
            retention_rate = await self.calculate_retention_rate(student_id, question.id)

            # 判断是否需要复习
            if retention_rate < self.forgetting_curve_params["review_threshold"]:
                review_items.append(
                    {
                        "question_id": question.id,
                        "question": question,
                        "last_record": record,
                        "retention_rate": retention_rate,
                        "days_since_last_review": (datetime.now() - record.created_at).days,
                    }
                )

        return review_items

    async def _prioritize_review_items(
        self, review_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """对复习项目进行优先级排序."""
        for item in review_items:
            # 计算优先级分数
            retention_urgency = 1.0 - item["retention_rate"]  # 保持率越低越紧急
            time_urgency = min(item["days_since_last_review"] / 30.0, 1.0)  # 时间越长越紧急

            priority_score = retention_urgency * 0.7 + time_urgency * 0.3

            # 分配优先级等级
            if priority_score >= 0.8:
                priority = "urgent"
            elif priority_score >= 0.6:
                priority = "high"
            elif priority_score >= 0.4:
                priority = "medium"
            else:
                priority = "low"

            item["priority_score"] = priority_score
            item["priority"] = priority

        # 按优先级分数排序
        review_items.sort(key=lambda x: x["priority_score"], reverse=True)
        return review_items

    def _schedule_daily_reviews(
        self,
        prioritized_items: list[dict[str, Any]],
        target_date: datetime,
        day_offset: int,
    ) -> list[dict[str, Any]]:
        """安排每日复习项目."""
        daily_items = []

        # 根据日期偏移确定每日复习数量
        if day_offset == 0:  # 今天
            max_items = 15
        elif day_offset <= 2:  # 近期
            max_items = 10
        else:  # 远期
            max_items = 5

        # 选择优先级最高的项目
        for item in prioritized_items[:max_items]:
            daily_items.append(
                {
                    "question_id": item["question_id"],
                    "priority": item["priority"],
                    "retention_rate": item["retention_rate"],
                    "estimated_time_minutes": 3,  # 预估复习时间
                }
            )

        return daily_items

    def _calculate_next_review_date(
        self, retention_rate: float, performance_score: float
    ) -> datetime:
        """计算下次复习时间."""
        # 基于保持率和表现确定复习间隔
        if retention_rate >= 0.9 and performance_score >= 0.9:
            interval_days = self.review_intervals["maintenance"]
        elif retention_rate >= 0.8:
            interval_days = self.review_intervals["fifth_review"]
        elif retention_rate >= 0.7:
            interval_days = self.review_intervals["fourth_review"]
        elif retention_rate >= 0.6:
            interval_days = self.review_intervals["third_review"]
        elif retention_rate >= 0.4:
            interval_days = self.review_intervals["second_review"]
        else:
            interval_days = self.review_intervals["first_review"]

        return datetime.now() + timedelta(days=interval_days)

    def _evaluate_mastery_level(self, retention_rate: float, performance_score: float) -> str:
        """评估掌握程度."""
        if retention_rate >= 0.9 and performance_score >= 0.9:
            return "mastered"
        elif retention_rate >= 0.8 and performance_score >= 0.8:
            return "proficient"
        elif retention_rate >= 0.6 and performance_score >= 0.6:
            return "developing"
        elif retention_rate >= 0.4:
            return "basic"
        else:
            return "needs_review"

    def _generate_curve_data(self, learning_records: list[TrainingRecord]) -> list[dict[str, Any]]:
        """生成遗忘曲线数据点."""
        curve_data: list[dict[str, Any]] = []

        if not learning_records:
            return curve_data

        # 以第一次学习为起点
        start_time = learning_records[0].created_at
        current_time = datetime.now()

        # 生成时间点（每天一个数据点）
        total_days = (current_time - start_time).days + 1

        for day in range(min(total_days, 30)):  # 最多显示30天的数据
            target_time = start_time + timedelta(days=day)

            # 计算该时间点的理论保持率
            retention = self._calculate_theoretical_retention(learning_records, target_time)

            curve_data.append(
                {
                    "day": day,
                    "date": target_time.strftime("%Y-%m-%d"),
                    "retention_rate": retention,
                }
            )

        return curve_data

    def _calculate_theoretical_retention(
        self, learning_records: list[TrainingRecord], target_time: datetime
    ) -> float:
        """计算理论保持率."""
        total_retention = 0.0

        for record in learning_records:
            if record.created_at <= target_time:
                # 计算时间间隔
                time_elapsed = (target_time - record.created_at).total_seconds() / 86400

                # 计算记忆强度
                initial_strength = self._calculate_initial_strength(record)

                # 应用遗忘曲线
                retention = math.exp(-time_elapsed / initial_strength)

                # 累积效应
                total_retention += retention * (1 - total_retention)

        return min(max(total_retention, 0.0), 1.0)
