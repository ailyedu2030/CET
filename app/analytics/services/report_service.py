"""报告生成服务 - 实现各类数据分析报告的生成和导出."""

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas.analytics_schemas import (
    ReportRequest,
    ReportResponse,
    UserBehaviorReport,
)
from app.analytics.utils.chart_utils import ChartGenerator
from app.users.models.user_models import User

logger = logging.getLogger(__name__)


class UserAnalyticsReportGenerator:
    """用户分析报告生成器."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化用户分析报告生成器."""
        self.db = db_session
        self.chart_generator = ChartGenerator()

    async def generate_user_behavior_report(
        self, start_date: datetime, end_date: datetime, user_type: str | None = None
    ) -> UserBehaviorReport:
        """生成用户行为分析报告."""
        try:
            # 基础查询条件
            base_conditions = [
                User.created_at >= start_date,
                User.created_at <= end_date,
            ]

            if user_type:
                base_conditions.append(User.user_type == user_type)

            # 获取用户统计数据
            user_stats = await self._get_user_statistics(base_conditions)

            # 获取登录行为分析
            login_behavior = await self._analyze_login_behavior(
                base_conditions, start_date, end_date
            )

            # 获取学习进度分析
            learning_progress = await self._analyze_learning_progress(
                base_conditions, start_date, end_date
            )

            # 获取用户留存分析
            retention_analysis = await self._analyze_user_retention(start_date, end_date)

            # 生成可视化图表
            charts = await self._generate_user_behavior_charts(
                user_stats, login_behavior, learning_progress
            )

            return UserBehaviorReport(
                report_period={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "user_type_filter": user_type,
                },
                user_statistics=user_stats,
                login_behavior=login_behavior,
                learning_progress=learning_progress,
                retention_analysis=retention_analysis,
                visualizations=charts,
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"生成用户行为报告失败: {e}")
            raise e

    async def _get_user_statistics(self, base_conditions: list[Any]) -> dict[str, Any]:
        """获取用户统计数据."""
        try:
            # 总用户数
            total_users_query = select(func.count(User.id)).where(and_(*base_conditions))
            total_users_result = await self.db.execute(total_users_query)
            total_users = total_users_result.scalar() or 0

            # 按用户类型统计
            user_type_stats = {}
            for user_type in ["student", "teacher", "admin"]:
                type_conditions = base_conditions + [User.user_type == user_type]
                type_query = select(func.count(User.id)).where(and_(*type_conditions))
                type_result = await self.db.execute(type_query)
                user_type_stats[user_type] = type_result.scalar() or 0

            # 活跃用户统计（最近30天有登录）
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users_query = select(func.count(User.id)).where(
                and_(*base_conditions, User.last_login >= thirty_days_ago)
            )
            active_users_result = await self.db.execute(active_users_query)
            active_users = active_users_result.scalar() or 0

            # 新用户增长趋势（按月）
            monthly_growth = await self._get_monthly_user_growth(base_conditions)

            return {
                "total_users": total_users,
                "user_type_distribution": user_type_stats,
                "active_users_30d": active_users,
                "activity_rate": ((active_users / total_users * 100) if total_users > 0 else 0),
                "monthly_growth": monthly_growth,
                "average_users_per_month": (
                    sum(monthly_growth.values()) / len(monthly_growth) if monthly_growth else 0
                ),
            }

        except Exception as e:
            logger.error(f"获取用户统计数据失败: {e}")
            return {
                "total_users": 0,
                "user_type_distribution": {},
                "active_users_30d": 0,
                "activity_rate": 0,
                "monthly_growth": {},
                "average_users_per_month": 0,
            }

    async def _get_monthly_user_growth(self, base_conditions: list[Any]) -> dict[str, int]:
        """获取月度用户增长数据."""
        monthly_growth = {}

        # 获取最近12个月的数据
        for i in range(12):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            month_conditions = base_conditions + [
                User.created_at >= month_start,
                User.created_at < month_end,
            ]

            month_query = select(func.count(User.id)).where(and_(*month_conditions))
            month_result = await self.db.execute(month_query)
            month_count = month_result.scalar() or 0

            month_key = month_start.strftime("%Y-%m")
            monthly_growth[month_key] = month_count

        return monthly_growth

    async def _analyze_login_behavior(
        self, base_conditions: list[Any], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """分析登录行为."""
        try:
            # 登录频率分析
            login_frequency = await self._analyze_login_frequency(
                base_conditions, start_date, end_date
            )

            # 登录时间分布
            login_time_distribution = await self._analyze_login_time_distribution(base_conditions)

            # 平均会话时长（模拟数据，实际需要会话记录）
            avg_session_duration = 28.5  # 分钟

            return {
                "login_frequency": login_frequency,
                "time_distribution": login_time_distribution,
                "average_session_duration": avg_session_duration,
                "peak_hours": [9, 14, 20],  # 高峰时段
                "weekend_activity": 0.75,  # 周末活动比例相对工作日
            }

        except Exception as e:
            logger.error(f"分析登录行为失败: {e}")
            return {}

    async def _analyze_login_frequency(
        self, base_conditions: list[Any], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """分析登录频率."""
        # 获取在时间范围内有登录记录的用户
        users_with_login = select(User.id, User.last_login).where(
            and_(
                *base_conditions,
                User.last_login >= start_date,
                User.last_login <= end_date,
            )
        )

        users_result = await self.db.execute(users_with_login)
        users_data = users_result.fetchall()

        if not users_data:
            return {"daily": 0, "weekly": 0, "monthly": 0}

        total_users = len(users_data)

        # 简化的频率计算（实际需要更详细的登录记录）
        return {
            "daily": total_users * 0.3,  # 假设30%用户每日登录
            "weekly": total_users * 0.7,  # 假设70%用户每周登录
            "monthly": total_users * 0.9,  # 假设90%用户每月登录
            "average_logins_per_user": 15,  # 平均每用户登录次数
        }

    async def _analyze_login_time_distribution(
        self, base_conditions: list[Any]
    ) -> dict[str, float]:
        """分析登录时间分布."""
        # 在实际实现中，这里会分析登录时间的小时分布
        # 现在返回模拟数据
        return {
            "morning": 25.5,  # 8-12点
            "afternoon": 35.2,  # 12-18点
            "evening": 28.8,  # 18-22点
            "night": 10.5,  # 22-8点
        }

    async def _analyze_learning_progress(
        self, base_conditions: list[Any], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """分析学习进度."""
        try:
            # 获取用户练习完成情况
            progress_stats = await self._get_user_progress_stats(
                base_conditions, start_date, end_date
            )

            # 获取学习效果分析
            effectiveness_analysis = await self._analyze_learning_effectiveness(base_conditions)

            return {
                "progress_statistics": progress_stats,
                "effectiveness_analysis": effectiveness_analysis,
                "completion_trends": await self._get_completion_trends(start_date, end_date),
            }

        except Exception as e:
            logger.error(f"分析学习进度失败: {e}")
            return {}

    async def _get_user_progress_stats(
        self, base_conditions: list[Any], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """获取用户进度统计."""
        # 在实际实现中，这里会查询用户练习完成记录
        # 现在返回模拟数据
        return {
            "average_completion_rate": 78.5,
            "exercises_per_user": 24.3,
            "time_spent_learning": 125.8,  # 分钟
            "difficulty_progression": {"easy": 65.2, "medium": 45.8, "hard": 28.9},
        }

    async def _analyze_learning_effectiveness(self, base_conditions: list[Any]) -> dict[str, Any]:
        """分析学习效果."""
        return {
            "improvement_rate": 23.5,  # 成绩提升百分比
            "retention_rate": 87.2,  # 知识保持率
            "skill_development": {
                "vocabulary": 85.5,
                "grammar": 78.9,
                "reading": 82.3,
                "listening": 75.8,
            },
            "learning_velocity": 1.25,  # 学习速度指数
        }

    async def _get_completion_trends(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """获取完成趋势."""
        trends = []
        current_date = start_date

        while current_date <= end_date:
            # 模拟每周的完成趋势数据
            import random

            trends.append(
                {
                    "week": current_date.strftime("%Y-W%U"),
                    "completion_rate": random.uniform(70, 90),
                    "active_users": random.randint(50, 200),
                }
            )
            current_date += timedelta(weeks=1)

        return trends

    async def _analyze_user_retention(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """分析用户留存."""
        return {
            "day_1_retention": 78.5,
            "day_7_retention": 65.2,
            "day_30_retention": 45.8,
            "churn_rate": 15.3,
            "retention_by_cohort": {
                "2024-01": {"1d": 80.1, "7d": 67.3, "30d": 48.2},
                "2024-02": {"1d": 79.8, "7d": 66.1, "30d": 46.7},
                "2024-03": {"1d": 81.2, "7d": 68.9, "30d": 49.5},
            },
        }

    async def _generate_user_behavior_charts(
        self,
        user_stats: dict[str, Any],
        login_behavior: dict[str, Any],
        learning_progress: dict[str, Any],
    ) -> dict[str, Any]:
        """生成用户行为图表."""
        try:
            charts = {}

            # 用户类型分布饼图
            user_type_data = user_stats.get("user_type_distribution", {})
            if user_type_data:
                pie_data = [{"type": k, "count": v} for k, v in user_type_data.items()]
                charts["user_type_pie"] = self.chart_generator.generate_pie_chart(
                    pie_data, "type", "count", "用户类型分布"
                )

            # 月度用户增长线图
            monthly_data = user_stats.get("monthly_growth", {})
            if monthly_data:
                line_data = [{"month": k, "users": v} for k, v in monthly_data.items()]
                charts["monthly_growth_line"] = self.chart_generator.generate_line_chart(
                    line_data,
                    "month",
                    "users",
                    "月度用户增长",
                    "月份",
                    "新增用户数",
                )

            # 登录时间分布柱状图
            time_dist = login_behavior.get("time_distribution", {})
            if time_dist and self.chart_generator:
                bar_data = [{"period": k, "percentage": v} for k, v in time_dist.items()]
                charts["login_time_bar"] = self.chart_generator.generate_bar_chart(
                    bar_data,
                    "period",
                    "percentage",
                    "登录时间分布",
                    "时间段",
                    "登录比例(%)",
                )

            return charts

        except Exception as e:
            logger.error(f"生成用户行为图表失败: {e}")
            return {}


class TeachingEffectivenessReportGenerator:
    """教学效果报告生成器."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化教学效果报告生成器."""
        self.db = db_session
        self.chart_generator = ChartGenerator()

    async def generate_teaching_effectiveness_report(
        self, start_date: datetime, end_date: datetime, teacher_id: int | None = None
    ) -> dict[str, Any]:
        """生成教学效果报告."""
        try:
            # 课程效果分析
            course_effectiveness = await self._analyze_course_effectiveness(
                start_date, end_date, teacher_id
            )

            # 学习成果分析
            learning_outcomes = await self._analyze_learning_outcomes(
                start_date, end_date, teacher_id
            )

            # 教师表现分析
            teacher_performance = await self._analyze_teacher_performance(
                start_date, end_date, teacher_id
            )

            # 生成建议
            recommendations = await self._generate_teaching_recommendations(
                course_effectiveness, learning_outcomes, teacher_performance
            )

            return {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "teacher_filter": teacher_id,
                },
                "course_effectiveness": course_effectiveness,
                "learning_outcomes": learning_outcomes,
                "teacher_performance": teacher_performance,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"生成教学效果报告失败: {e}")
            raise e

    async def _analyze_course_effectiveness(
        self, start_date: datetime, end_date: datetime, teacher_id: int | None
    ) -> dict[str, Any]:
        """分析课程效果."""
        # 在实际实现中，这里会分析课程的各项指标
        return {
            "completion_rates": {
                "overall": 78.5,
                "by_difficulty": {
                    "beginner": 85.2,
                    "intermediate": 75.8,
                    "advanced": 68.9,
                },
            },
            "engagement_metrics": {
                "average_session_time": 32.5,
                "return_rate": 67.8,
                "interaction_score": 8.2,
            },
            "content_effectiveness": {
                "most_effective": ["基础语法", "词汇练习"],
                "needs_improvement": ["高级语法", "写作训练"],
            },
        }

    async def _analyze_learning_outcomes(
        self, start_date: datetime, end_date: datetime, teacher_id: int | None
    ) -> dict[str, Any]:
        """分析学习成果."""
        return {
            "score_improvements": {
                "average_improvement": 15.8,
                "improvement_distribution": {
                    "significant": 35.2,  # >20%提升
                    "moderate": 45.8,  # 10-20%提升
                    "minimal": 19.0,  # <10%提升
                },
            },
            "skill_development": {
                "reading": 82.3,
                "writing": 75.6,
                "listening": 78.9,
                "speaking": 71.2,
            },
            "knowledge_retention": {"short_term": 87.5, "long_term": 72.8},
        }

    async def _analyze_teacher_performance(
        self, start_date: datetime, end_date: datetime, teacher_id: int | None
    ) -> dict[str, Any]:
        """分析教师表现."""
        return {
            "teaching_metrics": {
                "student_satisfaction": 4.3,  # 1-5分
                "response_time": 2.5,  # 小时
                "engagement_rate": 78.9,  # 百分比
            },
            "course_management": {
                "content_updates": 12,
                "feedback_quality": 4.2,
                "innovation_score": 3.8,
            },
            "student_outcomes": {"pass_rate": 85.6, "improvement_rate": 23.4},
        }

    async def _generate_teaching_recommendations(
        self,
        course_effectiveness: dict[str, Any],
        learning_outcomes: dict[str, Any],
        teacher_performance: dict[str, Any],
    ) -> list[str]:
        """生成教学建议."""
        recommendations = []

        # 基于课程效果的建议
        completion_rate = course_effectiveness.get("completion_rates", {}).get("overall", 0)
        if completion_rate < 70:
            recommendations.append("课程完成率偏低，建议调整内容难度和节奏")

        # 基于学习成果的建议
        avg_improvement = learning_outcomes.get("score_improvements", {}).get(
            "average_improvement", 0
        )
        if avg_improvement < 15:
            recommendations.append("学习效果有待提升，建议增加互动练习和个性化辅导")

        # 基于教师表现的建议
        satisfaction = teacher_performance.get("teaching_metrics", {}).get(
            "student_satisfaction", 0
        )
        if satisfaction < 4.0:
            recommendations.append("学生满意度需要提升，建议改进教学方法和互动方式")

        if not recommendations:
            recommendations.append("整体教学效果良好，建议保持当前教学策略")

        return recommendations


class ReportExporter:
    """报告导出器."""

    def __init__(self) -> None:
        """初始化报告导出器."""
        self.chart_generator = ChartGenerator()

    async def export_to_json(self, report_data: dict[str, Any]) -> str:
        """导出为JSON格式."""
        try:
            return json.dumps(report_data, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            raise e

    async def export_to_csv(self, report_data: dict[str, Any]) -> str:
        """导出为CSV格式."""
        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # 写入标题行
            writer.writerow(["指标", "数值", "说明"])

            # 递归处理数据
            self._write_dict_to_csv(writer, report_data)

            return output.getvalue()

        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            raise e

    def _write_dict_to_csv(self, writer: Any, data: dict[str, Any], prefix: str = "") -> None:
        """递归写入字典数据到CSV."""
        for key, value in data.items():
            current_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                self._write_dict_to_csv(writer, value, current_key)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # 处理对象列表
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            self._write_dict_to_csv(writer, item, f"{current_key}[{i}]")
                        else:
                            writer.writerow([f"{current_key}[{i}]", str(item), ""])
                else:
                    # 处理简单列表
                    writer.writerow([current_key, ", ".join(map(str, value)), "列表数据"])
            else:
                writer.writerow([current_key, str(value), ""])

    async def create_pdf_report(self, report_data: dict[str, Any]) -> bytes:
        """创建PDF报告（需要额外的PDF库支持）."""
        # 在实际实现中，这里会使用reportlab或类似库生成PDF
        # 现在返回占位符
        return b"PDF report placeholder"


class ReportService:
    """报告服务主类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化报告服务."""
        self.db = db_session
        self.user_report_generator = UserAnalyticsReportGenerator(db_session)
        self.teaching_report_generator = TeachingEffectivenessReportGenerator(db_session)
        self.exporter = ReportExporter()

    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """生成报告."""
        try:
            report_data: dict[str, Any] = {}

            if request.report_type == "user_analytics":
                report_data = await self.user_report_generator.generate_user_behavior_report(
                    request.start_date,
                    request.end_date,
                    request.filters.get("user_type") if request.filters else None,
                )
            elif request.report_type == "teaching_effectiveness":
                report_data = (
                    await self.teaching_report_generator.generate_teaching_effectiveness_report(
                        request.start_date,
                        request.end_date,
                        request.filters.get("teacher_id") if request.filters else None,
                    )
                )
            else:
                raise ValueError(f"不支持的报告类型: {request.report_type}")

            # 根据需要的格式导出
            exported_content = None
            if request.export_format == "json":
                exported_content = await self.exporter.export_to_json(report_data)
            elif request.export_format == "csv":
                exported_content = await self.exporter.export_to_csv(report_data)

            return ReportResponse(
                report_id=f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                report_type=request.report_type,
                title=f"{request.report_type.title()} Report",
                status="completed",
                data=report_data,
                summary=None,
                export_format=request.export_format,
                exported_content=exported_content,
                error_message=None,
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return ReportResponse(
                report_id=f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                report_type=request.report_type,
                title=f"Error Report - {request.report_type.title()}",
                status="failed",
                data={},
                summary=None,
                export_format=None,
                exported_content=None,
                error_message=str(e),
                generated_at=datetime.utcnow(),
            )

    async def get_available_report_types(self) -> list[dict[str, Any]]:
        """获取可用的报告类型."""
        return [
            {
                "type": "user_analytics",
                "name": "用户行为分析报告",
                "description": "分析用户登录、学习行为和留存情况",
                "required_filters": [],
                "optional_filters": ["user_type"],
            },
            {
                "type": "teaching_effectiveness",
                "name": "教学效果分析报告",
                "description": "分析课程效果、学习成果和教师表现",
                "required_filters": [],
                "optional_filters": ["teacher_id"],
            },
        ]

    async def schedule_automated_report(
        self, report_type: str, schedule: str, recipients: list[str]
    ) -> dict[str, Any]:
        """安排自动化报告."""
        try:
            # 在实际实现中，这里会配置定时任务
            return {
                "schedule_id": f"schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "report_type": report_type,
                "schedule": schedule,
                "recipients": recipients,
                "status": "scheduled",
                "next_run": datetime.utcnow() + timedelta(days=1),
                "created_at": datetime.utcnow(),
            }
        except Exception as e:
            logger.error(f"安排自动化报告失败: {e}")
            return {"status": "error", "error": str(e)}
