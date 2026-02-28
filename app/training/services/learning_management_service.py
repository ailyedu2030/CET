"""学习计划与管理系统 - 服务层"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.training.models.learning_plan_models import (
    LearningPlanModel,
    LearningProgressModel,
    LearningReminderModel,
    LearningReportModel,
    LearningTaskModel,
    PlanStatus,
    TaskStatus,
)
from app.training.schemas.learning_management_schemas import (
    LearningDashboard,
    LearningPlanCreate,
    LearningPlanUpdate,
    LearningProgressCreate,
    LearningReportCreate,
    LearningStatistics,
    LearningTaskCreate,
    LearningTaskUpdate,
)

logger = logging.getLogger(__name__)


class LearningManagementService:
    """
    学习计划与管理系统服务类

    实现个人学习中心界面、学习数据管理和导出、进度跟踪和可视化等功能
    """

    def __init__(self: "LearningManagementService", db: AsyncSession) -> None:
        self.db = db

    # ==================== 学习计划管理 ====================

    async def create_plan(
        self: "LearningManagementService", user_id: int, data: LearningPlanCreate
    ) -> LearningPlanModel:
        """创建学习计划"""
        logger.info(f"用户 {user_id} 创建学习计划: {data.plan_name}")

        plan = LearningPlanModel(
            user_id=user_id,
            plan_name=data.plan_name,
            plan_description=data.plan_description,
            plan_type=data.plan_type,
            start_date=data.start_date,
            end_date=data.end_date,
            estimated_hours=data.estimated_hours,
            learning_goals=data.learning_goals,
            target_score=data.target_score,
            priority_level=data.priority_level,
            daily_study_time=data.daily_study_time,
            study_schedule=data.study_schedule,
            reminder_settings=data.reminder_settings,
            status=PlanStatus.DRAFT,
        )

        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        logger.info(f"学习计划创建成功: ID={plan.id}")  # type: ignore[has-type]
        return plan

    async def get_user_plans(
        self: "LearningManagementService",
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        status: PlanStatus | None = None,
    ) -> tuple[list[LearningPlanModel], int]:
        """获取用户的学习计划列表"""
        logger.info(f"查询用户 {user_id} 的学习计划")

        # 构建查询条件
        conditions = [LearningPlanModel.user_id == user_id]
        if status:
            conditions.append(LearningPlanModel.status == status)

        # 查询总数
        count_query = select(func.count(LearningPlanModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(LearningPlanModel)
            .where(and_(*conditions))
            .options(selectinload(LearningPlanModel.tasks))
            .order_by(desc(LearningPlanModel.created_at))  # type: ignore[has-type]
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        plans = result.scalars().all()

        return list(plans), total

    async def get_plan(
        self: "LearningManagementService", plan_id: int, user_id: int
    ) -> LearningPlanModel | None:
        """获取学习计划详情"""
        logger.info(f"查询学习计划详情: {plan_id}")

        query = (
            select(LearningPlanModel)
            .where(
                and_(
                    LearningPlanModel.id == plan_id,  # type: ignore[has-type]
                    LearningPlanModel.user_id == user_id,
                )
            )
            .options(
                selectinload(LearningPlanModel.tasks),
                selectinload(LearningPlanModel.progress_records),
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_plan(
        self: "LearningManagementService",
        plan_id: int,
        user_id: int,
        data: LearningPlanUpdate,
    ) -> LearningPlanModel | None:
        """更新学习计划"""
        logger.info(f"用户 {user_id} 更新学习计划: {plan_id}")

        plan = await self.get_plan(plan_id, user_id)
        if not plan:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        plan.updated_at = datetime.utcnow()  # type: ignore[has-type]
        await self.db.commit()
        await self.db.refresh(plan)

        logger.info(f"学习计划更新成功: ID={plan.id}")  # type: ignore[has-type]
        return plan

    # ==================== 学习任务管理 ====================

    async def create_task(
        self: "LearningManagementService", user_id: int, data: LearningTaskCreate
    ) -> LearningTaskModel:
        """创建学习任务"""
        logger.info(f"用户 {user_id} 创建学习任务: {data.task_name}")

        task = LearningTaskModel(
            plan_id=data.plan_id,
            user_id=user_id,
            task_name=data.task_name,
            task_description=data.task_description,
            task_type=data.task_type,
            scheduled_date=data.scheduled_date,
            due_date=data.due_date,
            estimated_minutes=data.estimated_minutes,
            task_content=data.task_content,
            resources=data.resources,
            requirements=data.requirements,
            difficulty_level=data.difficulty_level,
            status=TaskStatus.PENDING,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # 更新计划的任务统计
        await self._update_plan_task_stats(data.plan_id)

        logger.info(f"学习任务创建成功: ID={task.id}")  # type: ignore[has-type]
        return task

    async def get_user_tasks(
        self: "LearningManagementService",
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        plan_id: int | None = None,
        status: TaskStatus | None = None,
        date_filter: str | None = None,
    ) -> tuple[list[LearningTaskModel], int]:
        """获取用户的学习任务列表"""
        logger.info(f"查询用户 {user_id} 的学习任务")

        # 构建查询条件
        conditions = [LearningTaskModel.user_id == user_id]
        if plan_id:
            conditions.append(LearningTaskModel.plan_id == plan_id)
        if status:
            conditions.append(LearningTaskModel.status == status)

        # 日期过滤
        if date_filter == "today":
            today = datetime.now().date()
            conditions.append(func.date(LearningTaskModel.scheduled_date) == today)
        elif date_filter == "upcoming":
            today = datetime.now().date()
            conditions.append(func.date(LearningTaskModel.scheduled_date) > today)
        elif date_filter == "overdue":
            now = datetime.now()
            conditions.append(
                and_(
                    LearningTaskModel.due_date < now,
                    LearningTaskModel.status != TaskStatus.COMPLETED,
                )
            )

        # 查询总数
        count_query = select(func.count(LearningTaskModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(LearningTaskModel)
            .where(and_(*conditions))
            .options(selectinload(LearningTaskModel.plan))
            .order_by(LearningTaskModel.scheduled_date)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def update_task(
        self: "LearningManagementService",
        task_id: int,
        user_id: int,
        data: LearningTaskUpdate,
    ) -> LearningTaskModel | None:
        """更新学习任务"""
        logger.info(f"用户 {user_id} 更新学习任务: {task_id}")

        query = select(LearningTaskModel).where(
            and_(
                LearningTaskModel.id == task_id,  # type: ignore[has-type]
                LearningTaskModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # 如果任务完成，设置完成时间
        if data.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()

        task.updated_at = datetime.utcnow()  # type: ignore[has-type]
        await self.db.commit()
        await self.db.refresh(task)

        # 更新计划的任务统计
        await self._update_plan_task_stats(int(task.plan_id))

        logger.info(f"学习任务更新成功: ID={task.id}")  # type: ignore[has-type]
        return task

    # ==================== 学习进度管理 ====================

    async def record_progress(
        self: "LearningManagementService", user_id: int, data: LearningProgressCreate
    ) -> LearningProgressModel:
        """记录学习进度"""
        logger.info(f"用户 {user_id} 记录学习进度")

        progress = LearningProgressModel(
            user_id=user_id,
            plan_id=data.plan_id,
            record_date=data.record_date,
            study_minutes=data.study_minutes,
            tasks_completed=data.tasks_completed,
            listening_score=data.listening_score,
            reading_score=data.reading_score,
            writing_score=data.writing_score,
            overall_score=data.overall_score,
            login_count=data.login_count,
            practice_count=data.practice_count,
            mistake_count=data.mistake_count,
            focus_level=data.focus_level,
            satisfaction_level=data.satisfaction_level,
            difficulty_perception=data.difficulty_perception,
            notes=data.notes,
            achievements=data.achievements,
        )

        self.db.add(progress)
        await self.db.commit()
        await self.db.refresh(progress)

        logger.info(f"学习进度记录成功: ID={progress.id}")  # type: ignore[has-type]
        return progress

    async def get_user_progress(
        self: "LearningManagementService",
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        plan_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[LearningProgressModel], int]:
        """获取用户的学习进度记录"""
        logger.info(f"查询用户 {user_id} 的学习进度")

        # 构建查询条件
        conditions = [LearningProgressModel.user_id == user_id]
        if plan_id:
            conditions.append(LearningProgressModel.plan_id == plan_id)
        if start_date:
            conditions.append(LearningProgressModel.record_date >= start_date)
        if end_date:
            conditions.append(LearningProgressModel.record_date <= end_date)

        # 查询总数
        count_query = select(func.count(LearningProgressModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(LearningProgressModel)
            .where(and_(*conditions))
            .order_by(desc(LearningProgressModel.record_date))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        progress_records = result.scalars().all()

        return list(progress_records), total

    # ==================== 私有辅助方法 ====================

    async def _update_plan_task_stats(
        self: "LearningManagementService", plan_id: int
    ) -> None:
        """更新计划的任务统计"""
        # 查询任务统计
        total_query = select(func.count(LearningTaskModel.id)).where(  # type: ignore[has-type]
            LearningTaskModel.plan_id == plan_id
        )
        total_result = await self.db.execute(total_query)
        total_tasks = total_result.scalar() or 0

        completed_query = select(func.count(LearningTaskModel.id)).where(  # type: ignore[has-type]
            and_(
                LearningTaskModel.plan_id == plan_id,
                LearningTaskModel.status == TaskStatus.COMPLETED,
            )
        )
        completed_result = await self.db.execute(completed_query)
        completed_tasks = completed_result.scalar() or 0

        overdue_query = select(func.count(LearningTaskModel.id)).where(  # type: ignore[has-type]
            and_(
                LearningTaskModel.plan_id == plan_id,
                LearningTaskModel.due_date < datetime.utcnow(),
                LearningTaskModel.status != TaskStatus.COMPLETED,
            )
        )
        overdue_result = await self.db.execute(overdue_query)
        overdue_tasks = overdue_result.scalar() or 0

        # 更新计划统计
        plan_query = select(LearningPlanModel).where(LearningPlanModel.id == plan_id)  # type: ignore[has-type]
        plan_result = await self.db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()

        if plan:
            plan.total_tasks = total_tasks
            plan.completed_tasks = completed_tasks
            plan.overdue_tasks = overdue_tasks
            plan.completion_rate = (
                completed_tasks / total_tasks if total_tasks > 0 else 0.0
            )
            await self.db.commit()

    # ==================== 学习仪表板 ====================

    async def get_dashboard(
        self: "LearningManagementService", user_id: int
    ) -> LearningDashboard:
        """获取学习仪表板数据"""
        logger.info(f"生成用户 {user_id} 的学习仪表板")

        # 获取今日任务
        today_tasks, _ = await self.get_user_tasks(
            user_id=user_id,
            limit=10,
            date_filter="today",
        )

        # 获取即将到来的任务
        upcoming_tasks, _ = await self.get_user_tasks(
            user_id=user_id,
            limit=5,
            date_filter="upcoming",
        )

        # 获取逾期任务
        overdue_tasks, _ = await self.get_user_tasks(
            user_id=user_id,
            limit=5,
            date_filter="overdue",
        )

        # 获取最近进度
        recent_progress, _ = await self.get_user_progress(
            user_id=user_id,
            limit=7,
            start_date=datetime.now() - timedelta(days=7),
        )

        # 获取进行中的计划
        active_plans, _ = await self.get_user_plans(
            user_id=user_id,
            limit=5,
            status=PlanStatus.ACTIVE,
        )

        # 计算统计数据
        statistics = await self.get_user_statistics(user_id)

        from app.training.schemas.learning_management_schemas import (
            LearningPlanResponse,
            LearningProgressResponse,
            LearningTaskResponse,
        )

        return LearningDashboard(
            today_tasks=[LearningTaskResponse.model_validate(t) for t in today_tasks],
            upcoming_tasks=[
                LearningTaskResponse.model_validate(t) for t in upcoming_tasks
            ],
            overdue_tasks=[
                LearningTaskResponse.model_validate(t) for t in overdue_tasks
            ],
            recent_progress=[
                LearningProgressResponse.model_validate(p) for p in recent_progress
            ],
            active_plans=[LearningPlanResponse.model_validate(p) for p in active_plans],
            statistics=statistics,
            achievements=["连续学习3天", "完成5个任务"],
            recommendations=["建议增加听力练习", "保持每日学习习惯"],
        )

    async def get_user_statistics(
        self: "LearningManagementService", user_id: int
    ) -> LearningStatistics:
        """获取用户学习统计数据"""
        logger.info(f"计算用户 {user_id} 的学习统计")

        # 查询计划统计
        total_plans_query = select(func.count(LearningPlanModel.id)).where(  # type: ignore[has-type]
            LearningPlanModel.user_id == user_id
        )
        total_plans_result = await self.db.execute(total_plans_query)
        total_plans = total_plans_result.scalar() or 0

        active_plans_query = select(func.count(LearningPlanModel.id)).where(  # type: ignore[has-type]
            and_(
                LearningPlanModel.user_id == user_id,
                LearningPlanModel.status == PlanStatus.ACTIVE,
            )
        )
        active_plans_result = await self.db.execute(active_plans_query)
        active_plans = active_plans_result.scalar() or 0

        completed_plans_query = select(func.count(LearningPlanModel.id)).where(  # type: ignore[has-type]
            and_(
                LearningPlanModel.user_id == user_id,
                LearningPlanModel.status == PlanStatus.COMPLETED,
            )
        )
        completed_plans_result = await self.db.execute(completed_plans_query)
        completed_plans = completed_plans_result.scalar() or 0

        # 查询任务统计
        total_tasks_query = select(func.count(LearningTaskModel.id)).where(  # type: ignore[has-type]
            LearningTaskModel.user_id == user_id
        )
        total_tasks_result = await self.db.execute(total_tasks_query)
        total_tasks = total_tasks_result.scalar() or 0

        completed_tasks_query = select(func.count(LearningTaskModel.id)).where(  # type: ignore[has-type]
            and_(
                LearningTaskModel.user_id == user_id,
                LearningTaskModel.status == TaskStatus.COMPLETED,
            )
        )
        completed_tasks_result = await self.db.execute(completed_tasks_query)
        completed_tasks = completed_tasks_result.scalar() or 0

        overdue_tasks_query = select(func.count(LearningTaskModel.id)).where(  # type: ignore[has-type]
            and_(
                LearningTaskModel.user_id == user_id,
                LearningTaskModel.due_date < datetime.utcnow(),
                LearningTaskModel.status != TaskStatus.COMPLETED,
            )
        )
        overdue_tasks_result = await self.db.execute(overdue_tasks_query)
        overdue_tasks = overdue_tasks_result.scalar() or 0

        # 查询学习时间统计
        total_study_time_query = select(
            func.sum(LearningProgressModel.study_minutes)
        ).where(LearningProgressModel.user_id == user_id)
        total_study_time_result = await self.db.execute(total_study_time_query)
        total_study_time = total_study_time_result.scalar() or 0

        # 计算平均完成率
        if total_plans > 0:
            completion_rate_query = select(
                func.avg(LearningPlanModel.completion_rate)
            ).where(LearningPlanModel.user_id == user_id)
            completion_rate_result = await self.db.execute(completion_rate_query)
            average_completion_rate = completion_rate_result.scalar() or 0.0
        else:
            average_completion_rate = 0.0

        return LearningStatistics(
            total_study_time=int(total_study_time),
            total_plans=total_plans,
            active_plans=active_plans,
            completed_plans=completed_plans,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            average_completion_rate=float(average_completion_rate),
            study_streak=0,  # 需要时间序列分析
            weekly_study_time=[],  # 需要时间序列分析
            monthly_progress={},  # 需要时间序列分析
            skill_progress={},  # 需要从TrainingType枚举统计
        )

    # ==================== 学习报告生成 ====================

    async def create_report(
        self: "LearningManagementService", user_id: int, data: LearningReportCreate
    ) -> LearningReportModel:
        """创建学习报告"""
        logger.info(f"用户 {user_id} 创建学习报告: {data.report_name}")

        report = LearningReportModel(
            user_id=user_id,
            plan_id=data.plan_id,
            report_name=data.report_name,
            report_type=data.report_type,
            report_period=data.report_period,
            start_date=data.start_date,
            end_date=data.end_date,
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        # 异步生成报告内容
        await self._generate_report_content(report)

        logger.info(f"学习报告创建成功: ID={report.id}")  # type: ignore[has-type]
        return report

    async def _generate_report_content(
        self: "LearningManagementService", report: LearningReportModel
    ) -> None:
        """生成报告内容"""
        try:
            # 获取报告期间的数据
            progress_records, _ = await self.get_user_progress(
                user_id=int(report.user_id),
                plan_id=int(report.plan_id) if report.plan_id else None,
                start_date=report.start_date,  # type: ignore[arg-type]
                end_date=report.end_date,  # type: ignore[arg-type]
                limit=1000,
            )

            tasks, _ = await self.get_user_tasks(
                user_id=int(report.user_id),
                plan_id=int(report.plan_id) if report.plan_id else None,
                limit=1000,
            )

            # 计算汇总数据
            total_study_time = sum(p.study_minutes for p in progress_records)
            total_tasks_completed = sum(p.tasks_completed for p in progress_records)
            completed_tasks = len(
                [t for t in tasks if t.status == TaskStatus.COMPLETED]
            )

            summary_data = {
                "total_study_time": total_study_time,
                "total_tasks_completed": total_tasks_completed,
                "completed_tasks": completed_tasks,
                "average_daily_study": total_study_time / 7 if progress_records else 0,
            }

            # 生成详细数据
            detailed_data = {
                "daily_progress": [
                    {
                        "date": p.record_date.isoformat(),
                        "study_minutes": p.study_minutes,
                        "tasks_completed": p.tasks_completed,
                        "scores": {
                            "listening": p.listening_score,
                            "reading": p.reading_score,
                            "writing": p.writing_score,
                            "overall": p.overall_score,
                        },
                    }
                    for p in progress_records
                ],
                "task_completion": [
                    {
                        "task_name": t.task_name,
                        "status": t.status,
                        "completion_rate": t.completion_rate,
                        "actual_minutes": t.actual_minutes,
                    }
                    for t in tasks
                ],
            }

            # 生成图表数据
            charts_data = {
                "study_time_trend": [p.study_minutes for p in progress_records],
                "score_trend": [
                    p.overall_score for p in progress_records if p.overall_score
                ],
                "task_completion_rate": [t.completion_rate for t in tasks],
            }

            # 生成洞察和建议
            insights = []
            recommendations = []

            if total_study_time > 0:
                insights.append(f"报告期间总学习时间: {total_study_time} 分钟")
                insights.append(f"平均每日学习时间: {total_study_time / 7:.1f} 分钟")

            if completed_tasks > 0:
                insights.append(f"完成任务数: {completed_tasks}")
                completion_rate = completed_tasks / len(tasks) if tasks else 0
                insights.append(f"任务完成率: {completion_rate:.1%}")

            if total_study_time < 300:  # 少于5小时
                recommendations.append("建议增加每日学习时间")

            if completed_tasks < len(tasks) * 0.8:
                recommendations.append("建议提高任务完成率")

            # 更新报告
            report.summary_data = summary_data
            report.detailed_data = detailed_data
            report.charts_data = charts_data
            report.insights = insights
            report.recommendations = recommendations
            report.is_generated = True
            report.generation_time = datetime.utcnow()

            await self.db.commit()

        except Exception as e:
            logger.error(f"生成报告内容失败: {e}")

    async def _calculate_statistics(
        self: "LearningManagementService", user_id: int
    ) -> LearningStatistics:
        """计算用户学习统计数据"""
        return await self.get_user_statistics(user_id)

    # ==================== 学习数据导出 ====================

    async def export_user_data(
        self: "LearningManagementService",
        user_id: int,
        format: str = "excel",
        date_range: str | None = None,
        include_details: bool = True,
    ) -> dict[str, Any]:
        """导出用户学习数据"""
        logger.info(f"导出用户 {user_id} 学习数据，格式: {format}")

        try:
            # 计算日期范围
            end_date = datetime.utcnow()
            if date_range == "7d":
                start_date = end_date - timedelta(days=7)
            elif date_range == "30d":
                start_date = end_date - timedelta(days=30)
            elif date_range == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = None

            # 获取学习数据
            export_data = {
                "user_id": user_id,
                "export_format": format,
                "date_range": date_range,
                "generated_at": datetime.utcnow().isoformat(),
            }

            # 获取学习计划数据
            plans_query = select(LearningPlanModel).where(
                LearningPlanModel.user_id == user_id
            )
            if start_date:
                plans_query = plans_query.where(LearningPlanModel.created_at >= start_date)  # type: ignore[has-type]

            plans_result = await self.db.execute(plans_query)
            plans = plans_result.scalars().all()

            # 获取学习任务数据
            tasks_query = select(LearningTaskModel).where(
                LearningTaskModel.user_id == user_id
            )
            if start_date:
                tasks_query = tasks_query.where(LearningTaskModel.created_at >= start_date)  # type: ignore[has-type]

            tasks_result = await self.db.execute(tasks_query)
            tasks = tasks_result.scalars().all()

            # 获取学习进度数据
            progress_query = select(LearningProgressModel).where(
                LearningProgressModel.user_id == user_id
            )
            if start_date:
                progress_query = progress_query.where(
                    LearningProgressModel.record_date >= start_date
                )

            progress_result = await self.db.execute(progress_query)
            progress_records = progress_result.scalars().all()

            # 构建导出数据
            export_data.update(
                {
                    "plans_count": len(plans),
                    "tasks_count": len(tasks),
                    "progress_records_count": len(progress_records),
                    "summary": {
                        "total_study_time": sum(
                            p.study_minutes for p in progress_records
                        ),
                        "completed_tasks": len(
                            [t for t in tasks if t.status == TaskStatus.COMPLETED]
                        ),
                        "active_plans": len(
                            [p for p in plans if p.status == PlanStatus.ACTIVE]
                        ),
                    },
                }
            )

            if include_details:
                export_data.update(
                    {
                        "plans": [
                            {
                                "id": p.id,  # type: ignore[has-type]
                                "name": p.plan_name,
                                "type": p.plan_type.value,
                                "status": p.status.value,
                                "start_date": p.start_date.isoformat(),
                                "end_date": p.end_date.isoformat(),
                                "target_score": p.target_score,
                                "created_at": p.created_at.isoformat(),  # type: ignore[has-type]
                            }
                            for p in plans
                        ],
                        "tasks": [
                            {
                                "id": t.id,  # type: ignore[has-type]
                                "title": t.task_name,  # 修正属性名
                                "type": t.task_type,  # 修正属性名
                                "status": t.status,  # 修正属性名
                                "priority": t.difficulty_level,  # 修正属性名
                                "due_date": (
                                    t.due_date.isoformat() if t.due_date else None
                                ),
                                "completed_at": (
                                    t.completed_at.isoformat()
                                    if t.completed_at
                                    else None
                                ),
                            }
                            for t in tasks
                        ],
                        "progress": [
                            {
                                "date": p.record_date.isoformat(),
                                "study_minutes": p.study_minutes,
                                "tasks_completed": p.tasks_completed,
                                "overall_score": p.overall_score,
                            }
                            for p in progress_records
                        ],
                    }
                )

            # 模拟文件生成（实际应用中应该生成真实文件）
            file_name = f"learning_data_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"

            return {
                "download_url": f"/api/v1/files/download/{file_name}",
                "file_name": file_name,
                "file_size": len(str(export_data)),  # 模拟文件大小
                "generated_at": export_data["generated_at"],
                "data": export_data,
            }

        except Exception as e:
            logger.error(f"导出用户数据失败: {e}")
            raise

    # ==================== 学习提醒管理 ====================

    async def get_user_reminders(
        self: "LearningManagementService",
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        reminder_type: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """获取用户学习提醒列表"""
        logger.info(f"获取用户 {user_id} 学习提醒列表")

        try:
            # 构建查询
            query = select(LearningReminderModel).where(
                LearningReminderModel.user_id == user_id
            )

            # 根据类型过滤
            if reminder_type:
                query = query.where(
                    LearningReminderModel.reminder_type == reminder_type
                )

            # 获取总数
            count_query = select(func.count(LearningReminderModel.id)).where(  # type: ignore[has-type]
                LearningReminderModel.user_id == user_id
            )
            if reminder_type:
                count_query = count_query.where(
                    LearningReminderModel.reminder_type == reminder_type
                )

            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0

            # 分页查询
            query = query.offset(skip).limit(limit).order_by(desc(LearningReminderModel.created_at))  # type: ignore[has-type]
            result = await self.db.execute(query)
            reminders_models = result.scalars().all()

            # 转换为字典格式
            reminders = [
                {
                    "id": reminder.id,  # type: ignore[has-type]
                    "user_id": reminder.user_id,  # type: ignore[has-type]
                    "title": reminder.reminder_name,  # type: ignore[has-type]
                    "content": reminder.message or "",  # type: ignore[has-type]
                    "reminder_type": reminder.reminder_type or "custom",  # type: ignore[has-type]
                    "reminder_time": (
                        reminder.reminder_time.strftime("%H:%M")
                        if reminder.reminder_time
                        else "09:00"
                    ),  # type: ignore[has-type]
                    "is_active": reminder.is_active,  # type: ignore[has-type]
                    "created_at": reminder.created_at.isoformat(),  # type: ignore[has-type]
                }
                for reminder in reminders_models
            ]

            return reminders, total

        except Exception as e:
            logger.error(f"获取学习提醒列表失败: {e}")
            raise

    async def create_reminder(
        self: "LearningManagementService", user_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """创建学习提醒"""
        logger.info(f"用户 {user_id} 创建学习提醒")

        try:
            # 创建提醒模型
            reminder_model = LearningReminderModel(
                user_id=user_id,
                reminder_name=data.get("title", "学习提醒"),
                message=data.get("content", ""),
                reminder_type=data.get("reminder_type", "custom"),
                frequency="daily",  # 默认每日
                is_active=data.get("is_active", True),
            )

            # 处理提醒时间
            reminder_time_str = data.get("reminder_time", "09:00")
            if reminder_time_str:
                try:
                    # 解析时间字符串 (HH:MM)
                    hour, minute = map(int, reminder_time_str.split(":"))
                    reminder_time = datetime.utcnow().replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    reminder_model.reminder_time = reminder_time
                except ValueError:
                    logger.warning(f"无效的提醒时间格式: {reminder_time_str}")

            # 保存到数据库
            self.db.add(reminder_model)
            await self.db.commit()
            await self.db.refresh(reminder_model)

            # 返回创建的提醒数据
            reminder = {
                "id": reminder_model.id,  # type: ignore[has-type]
                "user_id": reminder_model.user_id,  # type: ignore[has-type]
                "title": reminder_model.reminder_name,  # type: ignore[has-type]
                "content": reminder_model.message or "",  # type: ignore[has-type]
                "reminder_type": reminder_model.reminder_type or "custom",  # type: ignore[has-type]
                "reminder_time": (
                    reminder_model.reminder_time.strftime("%H:%M")
                    if reminder_model.reminder_time
                    else "09:00"
                ),  # type: ignore[has-type]
                "is_active": reminder_model.is_active,  # type: ignore[has-type]
                "created_at": reminder_model.created_at.isoformat(),  # type: ignore[has-type]
            }

            return reminder

        except Exception as e:
            logger.error(f"创建学习提醒失败: {e}")
            await self.db.rollback()
            raise

    async def update_reminder(
        self: "LearningManagementService",
        reminder_id: int,
        user_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """更新学习提醒"""
        logger.info(f"用户 {user_id} 更新学习提醒: {reminder_id}")

        try:
            # 查找提醒
            query = select(LearningReminderModel).where(
                and_(
                    LearningReminderModel.id == reminder_id,  # type: ignore[has-type]
                    LearningReminderModel.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            reminder_model = result.scalar_one_or_none()

            if not reminder_model:
                return None

            # 更新字段
            if "title" in data:
                reminder_model.reminder_name = data["title"]  # type: ignore[has-type]
            if "content" in data:
                reminder_model.message = data["content"]  # type: ignore[has-type]
            if "reminder_type" in data:
                reminder_model.reminder_type = data["reminder_type"]  # type: ignore[has-type]
            if "is_active" in data:
                reminder_model.is_active = data["is_active"]  # type: ignore[has-type]

            # 处理提醒时间
            if "reminder_time" in data:
                reminder_time_str = data["reminder_time"]
                try:
                    hour, minute = map(int, reminder_time_str.split(":"))
                    reminder_time = datetime.utcnow().replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    reminder_model.reminder_time = reminder_time  # type: ignore[has-type]
                except ValueError:
                    logger.warning(f"无效的提醒时间格式: {reminder_time_str}")

            # 保存更新
            await self.db.commit()
            await self.db.refresh(reminder_model)

            # 返回更新后的提醒数据
            reminder = {
                "id": reminder_model.id,  # type: ignore[has-type]
                "user_id": reminder_model.user_id,  # type: ignore[has-type]
                "title": reminder_model.reminder_name,  # type: ignore[has-type]
                "content": reminder_model.message or "",  # type: ignore[has-type]
                "reminder_type": reminder_model.reminder_type or "custom",  # type: ignore[has-type]
                "reminder_time": (
                    reminder_model.reminder_time.strftime("%H:%M")
                    if reminder_model.reminder_time
                    else "09:00"
                ),  # type: ignore[has-type]
                "is_active": reminder_model.is_active,  # type: ignore[has-type]
                "updated_at": reminder_model.updated_at.isoformat(),  # type: ignore[has-type]
            }

            return reminder

        except Exception as e:
            logger.error(f"更新学习提醒失败: {e}")
            await self.db.rollback()
            raise

    async def delete_reminder(
        self: "LearningManagementService", reminder_id: int, user_id: int
    ) -> bool:
        """删除学习提醒"""
        logger.info(f"用户 {user_id} 删除学习提醒: {reminder_id}")

        try:
            # 查找提醒
            query = select(LearningReminderModel).where(
                and_(
                    LearningReminderModel.id == reminder_id,  # type: ignore[has-type]
                    LearningReminderModel.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            reminder_model = result.scalar_one_or_none()

            if not reminder_model:
                return False

            # 删除提醒
            await self.db.delete(reminder_model)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"删除学习提醒失败: {e}")
            await self.db.rollback()
            raise

    # ==================== 课程表查看 ====================

    async def get_user_schedule(
        self: "LearningManagementService", user_id: int, week_offset: int = 0
    ) -> dict[str, Any]:
        """获取用户课程表"""
        logger.info(f"获取用户 {user_id} 课程表，周偏移: {week_offset}")

        # 计算目标周的日期范围
        today = datetime.utcnow().date()
        week_start = (
            today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        )
        week_end = week_start + timedelta(days=6)

        # 获取该周的学习任务
        tasks_query = (
            select(LearningTaskModel)
            .where(
                and_(
                    LearningTaskModel.user_id == user_id,
                    LearningTaskModel.due_date >= week_start,
                    LearningTaskModel.due_date <= week_end,
                )
            )
            .order_by(LearningTaskModel.due_date, LearningTaskModel.difficulty_level.desc())  # type: ignore[has-type]
        )

        tasks_result = await self.db.execute(tasks_query)
        tasks = tasks_result.scalars().all()

        # 构建课程表数据
        schedule: dict[str, Any] = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "week_offset": week_offset,
            "days": [],
        }

        # 按天组织任务
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_tasks = [
                {
                    "id": t.id,  # type: ignore[has-type]
                    "title": t.task_name,  # 修正属性名
                    "type": t.task_type,  # 修正属性名
                    "status": t.status,  # 修正属性名
                    "priority": t.difficulty_level,  # 修正属性名
                    "estimated_minutes": t.estimated_minutes,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in tasks
                if t.due_date and t.due_date.date() == day_date
            ]

            schedule["days"].append(
                {
                    "date": day_date.isoformat(),
                    "day_name": day_date.strftime("%A"),
                    "is_today": day_date == today,
                    "tasks": day_tasks,
                    "total_tasks": len(day_tasks),
                    "estimated_time": sum(
                        t.get("estimated_minutes", 0) for t in day_tasks
                    ),
                }
            )

        return schedule

    # ==================== 删除操作 ====================

    async def delete_plan(
        self: "LearningManagementService", plan_id: int, user_id: int
    ) -> bool:
        """删除学习计划"""
        logger.info(f"删除用户 {user_id} 的学习计划: {plan_id}")

        try:
            # 检查计划是否存在且属于用户
            plan_query = select(LearningPlanModel).where(
                and_(LearningPlanModel.id == plan_id, LearningPlanModel.user_id == user_id)  # type: ignore[has-type]
            )
            plan_result = await self.db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()

            if not plan:
                return False

            # 删除计划（级联删除相关任务）
            await self.db.delete(plan)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"删除学习计划失败: {e}")
            await self.db.rollback()
            raise

    async def delete_task(
        self: "LearningManagementService", task_id: int, user_id: int
    ) -> bool:
        """删除学习任务"""
        logger.info(f"删除用户 {user_id} 的学习任务: {task_id}")

        try:
            # 检查任务是否存在且属于用户
            task_query = select(LearningTaskModel).where(
                and_(LearningTaskModel.id == task_id, LearningTaskModel.user_id == user_id)  # type: ignore[has-type]
            )
            task_result = await self.db.execute(task_query)
            task = task_result.scalar_one_or_none()

            if not task:
                return False

            # 删除任务
            await self.db.delete(task)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"删除学习任务失败: {e}")
            await self.db.rollback()
            raise
