"""
自定义报表系统服务

实现灵活的报表生成、数据导出、定时报表和可视化图表生成。
支持多种数据源、多种输出格式和自定义报表模板。
"""

import asyncio
import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.config import settings


class ReportType(Enum):
    """报表类型枚举"""

    LEARNING_PROGRESS = "learning_progress"  # 学习进度报表
    PERFORMANCE_ANALYSIS = "performance_analysis"  # 性能分析报表
    USER_ACTIVITY = "user_activity"  # 用户活动报表
    CONTENT_EFFECTIVENESS = "content_effectiveness"  # 内容效果报表
    SYSTEM_METRICS = "system_metrics"  # 系统指标报表
    FINANCIAL_SUMMARY = "financial_summary"  # 财务汇总报表
    CUSTOM_QUERY = "custom_query"  # 自定义查询报表


class OutputFormat(Enum):
    """输出格式枚举"""

    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    PNG = "png"  # 图表图片


class ScheduleFrequency(Enum):
    """调度频率枚举"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


@dataclass
class ReportFilter:
    """报表过滤条件"""

    start_date: datetime | None = None
    end_date: datetime | None = None
    user_ids: list[int] | None = None
    content_types: list[str] | None = None
    difficulty_levels: list[str] | None = None
    custom_filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportColumn:
    """报表列定义"""

    name: str
    display_name: str
    data_type: str  # string, number, date, boolean
    aggregation: str | None = None  # sum, avg, count, min, max
    format_pattern: str | None = None
    is_visible: bool = True


@dataclass
class ChartConfig:
    """图表配置"""

    chart_type: str  # line, bar, pie, scatter, heatmap
    x_axis: str
    y_axis: str | list[str]
    title: str
    width: int = 800
    height: int = 600
    color_scheme: str | None = None
    show_legend: bool = True
    show_grid: bool = True


@dataclass
class ReportTemplate:
    """报表模板"""

    template_id: str
    name: str
    description: str
    report_type: ReportType
    columns: list[ReportColumn]
    default_filters: ReportFilter
    charts: list[ChartConfig] = field(default_factory=list)
    layout: dict[str, Any] = field(default_factory=dict)
    created_by: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    is_public: bool = False


@dataclass
class ReportSchedule:
    """报表调度"""

    schedule_id: str
    template_id: str
    name: str
    frequency: ScheduleFrequency
    schedule_time: str  # HH:MM格式
    recipients: list[str]  # 邮箱列表
    output_formats: list[OutputFormat]
    filters: ReportFilter
    is_active: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None


@dataclass
class GeneratedReport:
    """生成的报表"""

    report_id: str
    template_id: str
    name: str
    generated_at: datetime
    filters_applied: ReportFilter
    data: list[dict[str, Any]]
    charts: list[dict[str, Any]] = field(default_factory=list)
    file_paths: dict[OutputFormat, str] = field(default_factory=dict)
    generation_time: float = 0.0  # 生成耗时（秒）


class CustomReportService:
    """自定义报表系统服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 报表模板存储
        self.templates: dict[str, ReportTemplate] = {}

        # 报表调度存储
        self.schedules: dict[str, ReportSchedule] = {}

        # 生成的报表存储
        self.generated_reports: dict[str, GeneratedReport] = {}

        # 报表输出目录
        self.output_dir = Path(getattr(settings, "REPORT_OUTPUT_DIR", "./reports"))
        self.output_dir.mkdir(exist_ok=True)

        # 初始化默认模板
        self._initialize_default_templates()

        # 启动调度任务
        asyncio.create_task(self._schedule_loop())

    def _initialize_default_templates(self) -> None:
        """初始化默认报表模板"""
        # 学习进度报表模板
        learning_progress_template = ReportTemplate(
            template_id="learning_progress_default",
            name="学习进度报表",
            description="展示学生学习进度和成绩变化",
            report_type=ReportType.LEARNING_PROGRESS,
            columns=[
                ReportColumn("user_id", "用户ID", "number"),
                ReportColumn("username", "用户名", "string"),
                ReportColumn("total_study_time", "总学习时长", "number", "sum", "0.0小时"),
                ReportColumn("sessions_count", "学习次数", "number", "count"),
                ReportColumn("avg_accuracy", "平均准确率", "number", "avg", "0.0%"),
                ReportColumn("progress_score", "进度评分", "number", "avg", "0.0"),
                ReportColumn(
                    "last_activity",
                    "最后活动",
                    "date",
                    format_pattern="YYYY-MM-DD HH:mm",
                ),
            ],
            default_filters=ReportFilter(
                start_date=datetime.now() - timedelta(days=30), end_date=datetime.now()
            ),
            charts=[
                ChartConfig(
                    chart_type="line",
                    x_axis="last_activity",
                    y_axis="progress_score",
                    title="学习进度趋势",
                ),
                ChartConfig(
                    chart_type="bar",
                    x_axis="username",
                    y_axis="total_study_time",
                    title="学习时长排行",
                ),
            ],
        )

        # 性能分析报表模板
        performance_template = ReportTemplate(
            template_id="performance_analysis_default",
            name="系统性能分析报表",
            description="系统性能指标和趋势分析",
            report_type=ReportType.PERFORMANCE_ANALYSIS,
            columns=[
                ReportColumn("timestamp", "时间", "date"),
                ReportColumn("cpu_usage", "CPU使用率", "number", "avg", "0.0%"),
                ReportColumn("memory_usage", "内存使用率", "number", "avg", "0.0%"),
                ReportColumn("response_time", "响应时间", "number", "avg", "0ms"),
                ReportColumn("active_users", "活跃用户数", "number", "max"),
                ReportColumn("api_calls", "API调用次数", "number", "sum"),
            ],
            default_filters=ReportFilter(
                start_date=datetime.now() - timedelta(days=7), end_date=datetime.now()
            ),
            charts=[
                ChartConfig(
                    chart_type="line",
                    x_axis="timestamp",
                    y_axis=["cpu_usage", "memory_usage"],
                    title="系统资源使用趋势",
                ),
                ChartConfig(
                    chart_type="line",
                    x_axis="timestamp",
                    y_axis="response_time",
                    title="响应时间趋势",
                ),
            ],
        )

        # 内容效果报表模板
        content_effectiveness_template = ReportTemplate(
            template_id="content_effectiveness_default",
            name="内容效果分析报表",
            description="教学内容效果和质量分析",
            report_type=ReportType.CONTENT_EFFECTIVENESS,
            columns=[
                ReportColumn("content_type", "内容类型", "string"),
                ReportColumn("total_sessions", "总会话数", "number", "sum"),
                ReportColumn("completion_rate", "完成率", "number", "avg", "0.0%"),
                ReportColumn("avg_score_improvement", "平均提升", "number", "avg", "0.0%"),
                ReportColumn("engagement_level", "参与度", "number", "avg", "0.0%"),
                ReportColumn("effectiveness_score", "效果评分", "number", "avg", "0.0"),
            ],
            default_filters=ReportFilter(
                start_date=datetime.now() - timedelta(days=30), end_date=datetime.now()
            ),
            charts=[
                ChartConfig(
                    chart_type="bar",
                    x_axis="content_type",
                    y_axis="effectiveness_score",
                    title="内容效果评分对比",
                ),
                ChartConfig(
                    chart_type="pie",
                    x_axis="content_type",
                    y_axis="total_sessions",
                    title="内容使用分布",
                ),
            ],
        )

        self.templates.update(
            {
                learning_progress_template.template_id: learning_progress_template,
                performance_template.template_id: performance_template,
                content_effectiveness_template.template_id: content_effectiveness_template,
            }
        )

    async def create_template(self, template: ReportTemplate) -> str:
        """创建报表模板"""
        self.templates[template.template_id] = template
        self.logger.info(f"创建报表模板: {template.name}")
        return template.template_id

    async def update_template(self, template_id: str, updates: dict[str, Any]) -> bool:
        """更新报表模板"""
        if template_id not in self.templates:
            return False

        template = self.templates[template_id]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        self.logger.info(f"更新报表模板: {template_id}")
        return True

    async def delete_template(self, template_id: str) -> bool:
        """删除报表模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            self.logger.info(f"删除报表模板: {template_id}")
            return True
        return False

    async def generate_report(
        self,
        template_id: str,
        filters: ReportFilter | None = None,
        output_formats: list[OutputFormat] | None = None,
    ) -> GeneratedReport:
        """生成报表"""
        if template_id not in self.templates:
            raise ValueError(f"报表模板不存在: {template_id}")

        template = self.templates[template_id]
        start_time = datetime.now()

        # 使用提供的过滤条件或默认过滤条件
        applied_filters = filters or template.default_filters

        # 生成报表数据
        report_data = await self._generate_report_data(template, applied_filters)

        # 生成图表
        charts = await self._generate_charts(template, report_data)

        # 创建报表对象
        report_id = f"{template_id}_{int(datetime.now().timestamp())}"
        report = GeneratedReport(
            report_id=report_id,
            template_id=template_id,
            name=f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            filters_applied=applied_filters,
            data=report_data,
            charts=charts,
            generation_time=(datetime.now() - start_time).total_seconds(),
        )

        # 生成输出文件
        if output_formats:
            for format_type in output_formats:
                file_path = await self._export_report(report, format_type)
                report.file_paths[format_type] = file_path

        # 存储报表
        self.generated_reports[report_id] = report

        self.logger.info(f"生成报表完成: {report.name}, 耗时: {report.generation_time:.2f}秒")
        return report

    async def _generate_report_data(
        self, template: ReportTemplate, filters: ReportFilter
    ) -> list[dict[str, Any]]:
        """生成报表数据"""
        # 这里应该根据报表类型和过滤条件从数据库或其他数据源获取数据
        # 暂时返回模拟数据

        if template.report_type == ReportType.LEARNING_PROGRESS:
            return [
                {
                    "user_id": 1,
                    "username": "张三",
                    "total_study_time": 25.5,
                    "sessions_count": 15,
                    "avg_accuracy": 0.85,
                    "progress_score": 78.5,
                    "last_activity": "2024-01-15 14:30:00",
                },
                {
                    "user_id": 2,
                    "username": "李四",
                    "total_study_time": 32.0,
                    "sessions_count": 20,
                    "avg_accuracy": 0.92,
                    "progress_score": 85.2,
                    "last_activity": "2024-01-15 16:45:00",
                },
            ]
        elif template.report_type == ReportType.PERFORMANCE_ANALYSIS:
            return [
                {
                    "timestamp": "2024-01-15 10:00:00",
                    "cpu_usage": 45.2,
                    "memory_usage": 62.8,
                    "response_time": 250,
                    "active_users": 125,
                    "api_calls": 1580,
                },
                {
                    "timestamp": "2024-01-15 11:00:00",
                    "cpu_usage": 52.1,
                    "memory_usage": 68.5,
                    "response_time": 280,
                    "active_users": 142,
                    "api_calls": 1720,
                },
            ]
        elif template.report_type == ReportType.CONTENT_EFFECTIVENESS:
            return [
                {
                    "content_type": "词汇训练",
                    "total_sessions": 450,
                    "completion_rate": 0.87,
                    "avg_score_improvement": 0.15,
                    "engagement_level": 0.82,
                    "effectiveness_score": 85.5,
                },
                {
                    "content_type": "语法练习",
                    "total_sessions": 320,
                    "completion_rate": 0.79,
                    "avg_score_improvement": 0.18,
                    "engagement_level": 0.75,
                    "effectiveness_score": 78.2,
                },
            ]
        else:
            return []

    async def _generate_charts(
        self, template: ReportTemplate, data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成图表数据"""
        charts = []

        for chart_config in template.charts:
            chart_data = {
                "type": chart_config.chart_type,
                "title": chart_config.title,
                "config": {
                    "width": chart_config.width,
                    "height": chart_config.height,
                    "show_legend": chart_config.show_legend,
                    "show_grid": chart_config.show_grid,
                },
            }

            # 提取图表数据
            if chart_config.chart_type in ["line", "bar"]:
                x_values = [row.get(chart_config.x_axis) for row in data]

                if isinstance(chart_config.y_axis, list):
                    # 多个Y轴
                    datasets = []
                    for y_axis in chart_config.y_axis:
                        y_values = [row.get(y_axis) for row in data]
                        datasets.append({"label": y_axis, "data": y_values})
                    chart_data["data"] = {"labels": x_values, "datasets": datasets}
                else:
                    # 单个Y轴
                    y_values = [row.get(chart_config.y_axis) for row in data]
                    chart_data["data"] = {
                        "labels": x_values,
                        "datasets": [{"label": chart_config.y_axis, "data": y_values}],
                    }

            elif chart_config.chart_type == "pie":
                labels = [row.get(chart_config.x_axis) for row in data]
                y_axis_key = (
                    chart_config.y_axis
                    if isinstance(chart_config.y_axis, str)
                    else chart_config.y_axis[0]
                )
                values = [row.get(y_axis_key) for row in data]
                chart_data["data"] = {"labels": labels, "values": values}

            charts.append(chart_data)

        return charts

    async def _export_report(self, report: GeneratedReport, format_type: OutputFormat) -> str:
        """导出报表文件"""
        file_name = f"{report.name}.{format_type.value}"
        file_path = self.output_dir / file_name

        if format_type == OutputFormat.CSV:
            await self._export_csv(report, file_path)
        elif format_type == OutputFormat.JSON:
            await self._export_json(report, file_path)
        elif format_type == OutputFormat.HTML:
            await self._export_html(report, file_path)
        # 其他格式的导出实现...

        return str(file_path)

    async def _export_csv(self, report: GeneratedReport, file_path: Path) -> None:
        """导出CSV格式"""
        if not report.data:
            return

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = report.data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report.data)

    async def _export_json(self, report: GeneratedReport, file_path: Path) -> None:
        """导出JSON格式"""
        export_data = {
            "report_info": {
                "id": report.report_id,
                "name": report.name,
                "generated_at": report.generated_at.isoformat(),
                "generation_time": report.generation_time,
            },
            "data": report.data,
            "charts": report.charts,
        }

        with open(file_path, "w", encoding="utf-8") as jsonfile:
            json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)

    async def _export_html(self, report: GeneratedReport, file_path: Path) -> None:
        """导出HTML格式"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.name}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .header {{ margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.name}</h1>
                <p>生成时间: {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>生成耗时: {report.generation_time:.2f}秒</p>
            </div>

            <h2>数据表格</h2>
            <table>
        """

        if report.data:
            # 表头
            headers = report.data[0].keys()
            html_content += "<tr>"
            for header in headers:
                html_content += f"<th>{header}</th>"
            html_content += "</tr>"

            # 数据行
            for row in report.data:
                html_content += "<tr>"
                for value in row.values():
                    html_content += f"<td>{value}</td>"
                html_content += "</tr>"

        html_content += """
            </table>
        </body>
        </html>
        """

        with open(file_path, "w", encoding="utf-8") as htmlfile:
            htmlfile.write(html_content)

    async def create_schedule(self, schedule: ReportSchedule) -> str:
        """创建报表调度"""
        # 计算下次运行时间
        schedule.next_run = self._calculate_next_run(schedule)

        self.schedules[schedule.schedule_id] = schedule
        self.logger.info(f"创建报表调度: {schedule.name}")
        return schedule.schedule_id

    def _calculate_next_run(self, schedule: ReportSchedule) -> datetime:
        """计算下次运行时间"""
        now = datetime.now()

        if schedule.frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(
                hour=int(schedule.schedule_time.split(":")[0]),
                minute=int(schedule.schedule_time.split(":")[1]),
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            # 每周一执行
            days_ahead = 0 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=int(schedule.schedule_time.split(":")[0]),
                minute=int(schedule.schedule_time.split(":")[1]),
                second=0,
                microsecond=0,
            )
        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            # 每月1号执行
            if now.day == 1:
                next_run = now.replace(
                    day=1,
                    hour=int(schedule.schedule_time.split(":")[0]),
                    minute=int(schedule.schedule_time.split(":")[1]),
                    second=0,
                    microsecond=0,
                )
                if next_run <= now:
                    next_month = now.replace(day=28) + timedelta(days=4)
                    next_run = next_month.replace(day=1)
            else:
                next_month = now.replace(day=28) + timedelta(days=4)
                next_run = next_month.replace(
                    day=1,
                    hour=int(schedule.schedule_time.split(":")[0]),
                    minute=int(schedule.schedule_time.split(":")[1]),
                    second=0,
                    microsecond=0,
                )
        else:
            next_run = now + timedelta(hours=1)  # 默认1小时后

        return next_run

    async def _schedule_loop(self) -> None:
        """调度循环"""
        while True:
            try:
                now = datetime.now()

                for schedule in self.schedules.values():
                    if schedule.is_active and schedule.next_run and now >= schedule.next_run:
                        # 执行调度任务
                        await self._execute_scheduled_report(schedule)

                        # 更新下次运行时间
                        schedule.last_run = now
                        schedule.next_run = self._calculate_next_run(schedule)

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                self.logger.error(f"调度循环错误: {e}")
                await asyncio.sleep(300)  # 出错后等待5分钟

    async def _execute_scheduled_report(self, schedule: ReportSchedule) -> None:
        """执行调度报表"""
        try:
            # 生成报表
            report = await self.generate_report(
                schedule.template_id, schedule.filters, schedule.output_formats
            )

            # 发送报表（这里应该实现邮件发送功能）
            self.logger.info(f"调度报表生成完成: {report.name}")

            # TODO: 实现邮件发送功能
            # await self._send_report_email(report, schedule.recipients)

        except Exception as e:
            self.logger.error(f"执行调度报表失败: {e}")

    async def get_templates(self) -> list[dict[str, Any]]:
        """获取所有报表模板"""
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "report_type": template.report_type.value,
                "created_at": template.created_at.isoformat(),
                "is_public": template.is_public,
            }
            for template in self.templates.values()
        ]

    async def get_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取生成的报表列表"""
        reports = sorted(
            self.generated_reports.values(), key=lambda r: r.generated_at, reverse=True
        )

        return [
            {
                "report_id": report.report_id,
                "name": report.name,
                "template_id": report.template_id,
                "generated_at": report.generated_at.isoformat(),
                "generation_time": report.generation_time,
                "data_count": len(report.data),
                "available_formats": list(report.file_paths.keys()),
            }
            for report in reports[:limit]
        ]

    async def get_service_stats(self) -> dict[str, Any]:
        """获取服务统计"""
        return {
            "templates_count": len(self.templates),
            "schedules_count": len(self.schedules),
            "generated_reports_count": len(self.generated_reports),
            "active_schedules": len([s for s in self.schedules.values() if s.is_active]),
            "output_directory": str(self.output_dir),
        }


# 全局自定义报表服务实例 - 延迟初始化
_custom_report_service: CustomReportService | None = None


def get_custom_report_service() -> CustomReportService:
    """获取自定义报表服务实例."""
    global _custom_report_service
    if _custom_report_service is None:
        _custom_report_service = CustomReportService()
    return _custom_report_service
