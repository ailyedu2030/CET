"""智能报表生成API端点 - 需求6：智能报表生成."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas.analytics_schemas import ReportRequest
from app.analytics.services.custom_report_service import CustomReportService
from app.analytics.services.report_service import ReportService
from app.core.database import get_db
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["智能报表生成"])


@router.post("/generate")
async def generate_report(
    report_request: ReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """生成智能报表 - 需求6验收标准3."""
    # 权限检查：只有管理员可以生成报表
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以生成报表",
        )

    try:
        service = ReportService(db)
        report_response = await service.generate_report(report_request)

        logger.info(f"管理员 {current_user.id} 生成报表: {report_request.report_type}")

        return {
            "report_id": report_response.report_id,
            "report_type": report_response.report_type,
            "title": report_response.title,
            "status": report_response.status,
            "data": report_response.data,
            "summary": report_response.summary,
            "export_format": report_response.export_format,
            "exported_content": report_response.exported_content,
            "error_message": report_response.error_message,
            "generated_at": report_response.generated_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"生成报表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成报表失败",
        ) from e


@router.get("/types")
async def get_available_report_types(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取可用的报表类型 - 需求6验收标准3."""
    # 权限检查：只有管理员可以查看报表类型
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看报表类型",
        )

    try:
        service = ReportService(db)
        report_types = await service.get_available_report_types()

        logger.info(f"管理员 {current_user.id} 查看可用报表类型")

        return {
            "report_types": report_types,
            "total_count": len(report_types),
        }

    except Exception as e:
        logger.error(f"获取报表类型失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报表类型失败",
        ) from e


@router.post("/schedule")
async def schedule_automated_report(
    report_type: str = Query(..., description="报表类型"),
    schedule: str = Query(..., description="调度规则"),
    recipients: list[str] = Query(..., description="接收人邮箱列表"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """安排自动化报表 - 需求6验收标准3."""
    # 权限检查：只有管理员可以安排自动化报表
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以安排自动化报表",
        )

    try:
        service = ReportService(db)
        schedule_result = await service.schedule_automated_report(report_type, schedule, recipients)

        logger.info(f"管理员 {current_user.id} 安排自动化报表: {report_type}")

        return schedule_result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"安排自动化报表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="安排自动化报表失败",
        ) from e


@router.get("/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取报表模板列表 - 需求6验收标准3."""
    # 权限检查：只有管理员可以查看报表模板
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看报表模板",
        )

    try:
        service = CustomReportService()
        templates = await service.get_templates()

        logger.info(f"管理员 {current_user.id} 查看报表模板列表")

        return {
            "templates": templates,
            "total_count": len(templates),
        }

    except Exception as e:
        logger.error(f"获取报表模板失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报表模板失败",
        ) from e


@router.post("/custom/generate")
async def generate_custom_report(
    template_id: str = Query(..., description="模板ID"),
    output_formats: list[str] = Query(["json"], description="输出格式列表"),
    filters: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """生成自定义报表 - 需求6验收标准3."""
    # 权限检查：只有管理员可以生成自定义报表
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以生成自定义报表",
        )

    try:
        from app.analytics.services.custom_report_service import (
            OutputFormat,
            ReportFilter,
        )

        service = CustomReportService()

        # 转换输出格式
        output_format_enums = []
        for fmt in output_formats:
            try:
                output_format_enums.append(OutputFormat(fmt))
            except ValueError as e:
                raise ValueError(f"不支持的输出格式: {fmt}") from e

        # 构建过滤条件
        report_filter = None
        if filters:
            report_filter = ReportFilter(
                start_date=datetime.fromisoformat(filters.get("start_date", "2024-01-01")),
                end_date=datetime.fromisoformat(
                    filters.get("end_date", datetime.now().isoformat())
                ),
                user_ids=filters.get("user_ids", []),
                content_types=filters.get("content_types", []),
                difficulty_levels=filters.get("difficulty_levels", []),
                custom_filters=filters.get("custom_filters", {}),
            )

        # 生成报表
        generated_report = await service.generate_report(
            template_id, report_filter, output_format_enums
        )

        logger.info(f"管理员 {current_user.id} 生成自定义报表: {template_id}")

        return {
            "report_id": generated_report.report_id,
            "template_id": generated_report.template_id,
            "name": generated_report.name,
            "generated_at": generated_report.generated_at.isoformat(),
            "filters_applied": {
                "start_date": (
                    generated_report.filters_applied.start_date.isoformat()
                    if generated_report.filters_applied.start_date
                    else None
                ),
                "end_date": (
                    generated_report.filters_applied.end_date.isoformat()
                    if generated_report.filters_applied.end_date
                    else None
                ),
                "user_ids": generated_report.filters_applied.user_ids,
                "content_types": generated_report.filters_applied.content_types,
                "difficulty_levels": generated_report.filters_applied.difficulty_levels,
                "custom_filters": generated_report.filters_applied.custom_filters,
            },
            "data": generated_report.data,
            "charts": [
                {
                    "chart_type": chart.get("chart_type", ""),
                    "title": chart.get("title", ""),
                    "x_axis": chart.get("x_axis", ""),
                    "y_axis": chart.get("y_axis", ""),
                    "data": chart.get("data", {}),
                }
                for chart in generated_report.charts
            ],
            "file_paths": generated_report.file_paths,
            "generation_time": generated_report.generation_time,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"生成自定义报表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成自定义报表失败",
        ) from e


@router.get("/schedules")
async def get_report_schedules(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取报表调度列表 - 需求6验收标准3."""
    # 权限检查：只有管理员可以查看报表调度
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看报表调度",
        )

    try:
        service = CustomReportService()
        schedules = list(service.schedules.values())

        logger.info(f"管理员 {current_user.id} 查看报表调度列表")

        return {
            "schedules": [
                {
                    "schedule_id": schedule.schedule_id,
                    "template_id": schedule.template_id,
                    "name": schedule.name,
                    "frequency": schedule.frequency.value,
                    "schedule_time": schedule.schedule_time,
                    "recipients": schedule.recipients,
                    "output_formats": [fmt.value for fmt in schedule.output_formats],
                    "is_active": schedule.is_active,
                    "last_run": (schedule.last_run.isoformat() if schedule.last_run else None),
                    "next_run": (schedule.next_run.isoformat() if schedule.next_run else None),
                }
                for schedule in schedules
            ],
            "total_count": len(schedules),
        }

    except Exception as e:
        logger.error(f"获取报表调度列表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报表调度列表失败",
        ) from e


@router.post("/schedules/{schedule_id}/run")
async def run_scheduled_report(
    schedule_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """手动执行调度报表 - 需求6验收标准3."""
    # 权限检查：只有管理员可以执行调度报表
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行调度报表",
        )

    try:
        service = CustomReportService()
        await service._execute_scheduled_report(service.schedules[schedule_id])

        logger.info(f"管理员 {current_user.id} 手动执行调度报表: {schedule_id}")

        return {
            "schedule_id": schedule_id,
            "status": "executed",
            "executed_by": current_user.id,
            "executed_at": datetime.now().isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"执行调度报表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="执行调度报表失败",
        ) from e


@router.get("/history")
async def get_report_history(
    limit: int = Query(50, description="返回记录数限制", ge=1, le=200),
    offset: int = Query(0, description="偏移量", ge=0),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取报表生成历史 - 需求6验收标准3."""
    # 权限检查：只有管理员可以查看报表历史
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看报表历史",
        )

    try:
        service = CustomReportService()
        reports = service.generated_reports

        # 应用分页
        paginated_reports = list(reports.values())[offset : offset + limit]

        logger.info(f"管理员 {current_user.id} 查看报表生成历史")

        return {
            "reports": [
                {
                    "report_id": report.report_id,
                    "template_id": report.template_id,
                    "name": report.name,
                    "generated_at": report.generated_at.isoformat(),
                    "generation_time": report.generation_time,
                    "file_paths": report.file_paths,
                }
                for report in paginated_reports
            ],
            "total_count": len(reports),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"获取报表历史失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报表历史失败",
        ) from e
