"""管理员专用API端点 - 需求1-9：管理员端功能."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.models import User
from app.users.schemas.admin_schemas import (
    AdminDashboardResponse,
    BackupRestoreRequest,
    BackupRestoreResponse,
    ClassManagementRequest,
    ClassManagementResponse,
    CourseAssignmentRequest,
    CourseAssignmentResponse,
    CourseManagementStatsResponse,
    SystemMonitoringResponse,
    SystemRulesConfigRequest,
    SystemRulesConfigResponse,
    UserManagementStatsResponse,
)
from app.users.services.admin_service import AdminService
from app.users.utils.auth_decorators import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["管理员功能"])


# ===== 需求1：用户注册审核管理 - 管理员专用接口 =====


@router.get("/dashboard")
@require_admin
async def get_admin_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AdminDashboardResponse:
    """管理员仪表盘 - 需求1-9综合数据."""
    try:
        service = AdminService(db)
        dashboard_data = await service.get_admin_dashboard()

        logger.info(f"管理员 {current_user.id} 访问仪表盘")

        return AdminDashboardResponse(**dashboard_data)

    except Exception as e:
        logger.error(f"获取管理员仪表盘失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取仪表盘数据失败",
        ) from e


@router.get("/users/management-stats")
@require_admin
async def get_user_management_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserManagementStatsResponse:
    """用户管理统计 - 需求1,2综合统计."""
    try:
        service = AdminService(db)
        stats = await service.get_user_management_stats()

        logger.info(f"管理员 {current_user.id} 查看用户管理统计")

        return UserManagementStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取用户管理统计失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户管理统计失败",
        ) from e


@router.post("/users/{user_id}/activate")
@require_admin
async def activate_user_account(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """激活用户账号 - 需求1验收标准5."""
    try:
        service = AdminService(db)
        success = await service.activate_user_account(user_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="用户不存在或已激活",
            )

        logger.info(f"管理员 {current_user.id} 激活用户账号: {user_id}")

        return {
            "message": "用户账号激活成功",
            "user_id": user_id,
            "activated_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活用户账号失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活用户账号失败",
        ) from e


@router.post("/users/{user_id}/deactivate")
@require_admin
async def deactivate_user_account(
    user_id: int,
    reason: str = Query(..., description="停用原因"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """停用用户账号 - 需求1验收标准5."""
    try:
        service = AdminService(db)
        success = await service.deactivate_user_account(user_id, current_user.id, reason)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="用户不存在或已停用",
            )

        logger.info(f"管理员 {current_user.id} 停用用户账号: {user_id}, 原因: {reason}")

        return {
            "message": "用户账号停用成功",
            "user_id": user_id,
            "reason": reason,
            "deactivated_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停用用户账号失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用用户账号失败",
        ) from e


@router.post("/applications/{application_id}/notify-resubmit")
@require_admin
async def notify_resubmit_materials(
    application_id: int,
    message: str = Query(..., description="通知消息"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """通知用户补充材料 - 需求1验收标准6."""
    try:
        service = AdminService(db)
        success = await service.notify_resubmit_materials(application_id, message, current_user.id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="申请不存在",
            )

        logger.info(f"管理员 {current_user.id} 通知申请 {application_id} 补充材料")

        return {
            "message": "补充材料通知已发送",
            "application_id": application_id,
            "notification_message": message,
            "notified_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送补充材料通知失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送补充材料通知失败",
        ) from e


# ===== 需求3：课程全生命周期管理 =====


@router.get("/courses/management-stats")
@require_admin
async def get_course_management_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CourseManagementStatsResponse:
    """课程管理统计 - 需求3综合统计."""
    try:
        service = AdminService(db)
        stats = await service.get_course_management_stats()

        logger.info(f"管理员 {current_user.id} 查看课程管理统计")

        return CourseManagementStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取课程管理统计失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取课程管理统计失败",
        ) from e


@router.post("/courses/{course_id}/approve")
@require_admin
async def approve_course(
    course_id: int,
    notes: str = Query(None, description="审批备注"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审批课程 - 需求3验收标准3."""
    try:
        service = AdminService(db)
        success = await service.approve_course(course_id, current_user.id, notes)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="课程不存在或状态不允许审批",
            )

        logger.info(f"管理员 {current_user.id} 审批课程: {course_id}")

        return {
            "message": "课程审批成功",
            "course_id": course_id,
            "approved_by": current_user.id,
            "notes": notes,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"审批课程失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审批课程失败",
        ) from e


# ===== 需求4：班级管理与资源配置 =====


@router.post("/classes")
@require_admin
async def create_class(
    request: ClassManagementRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClassManagementResponse:
    """创建班级 - 需求4验收标准1."""
    try:
        service = AdminService(db)
        class_data = request.model_dump(exclude_unset=True)
        class_obj = await service.create_class(class_data, current_user.id)

        logger.info(f"管理员 {current_user.id} 创建班级: {class_obj.id}")

        return ClassManagementResponse(
            id=class_obj.id,
            name=class_obj.name,
            code=class_obj.code,
            course_id=class_obj.course_id,
            teacher_id=class_obj.teacher_id,
            classroom_id=class_obj.classroom_id,
            capacity=class_obj.capacity,
            min_students=class_obj.min_students,
            max_students=class_obj.max_students,
            start_date=class_obj.start_date,
            end_date=class_obj.end_date,
            status=class_obj.status,
            created_at=class_obj.created_at,
            updated_at=class_obj.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"创建班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建班级失败",
        ) from e


@router.post("/classes/batch-create")
@require_admin
async def batch_create_classes(
    course_id: int = Query(..., description="课程ID"),
    class_count: int = Query(..., ge=1, le=10, description="班级数量"),
    name_prefix: str = Query(..., description="班级名称前缀"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """批量创建班级 - 需求4验收标准2."""
    try:
        service = AdminService(db)
        classes = await service.batch_create_classes(
            course_id, class_count, name_prefix, current_user.id
        )

        logger.info(f"管理员 {current_user.id} 批量创建 {class_count} 个班级")

        return {
            "message": f"成功创建 {len(classes)} 个班级",
            "course_id": course_id,
            "created_classes": [
                {
                    "id": cls.id,
                    "name": cls.name,
                    "code": cls.code,
                }
                for cls in classes
            ],
            "created_by": current_user.id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"批量创建班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量创建班级失败",
        ) from e


# ===== 需求5：课程分配管理 =====


@router.post("/courses/{course_id}/assign-teacher")
@require_admin
async def assign_course_to_teacher(
    course_id: int,
    request: CourseAssignmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CourseAssignmentResponse:
    """分配课程给教师 - 需求5验收标准1."""
    try:
        service = AdminService(db)
        assignment = await service.assign_course_to_teacher(
            course_id, request.teacher_id, current_user.id, request.notes
        )

        logger.info(f"管理员 {current_user.id} 分配课程 {course_id} 给教师 {request.teacher_id}")

        return CourseAssignmentResponse(
            id=assignment.id,
            course_id=assignment.course_id,
            teacher_id=assignment.teacher_id,
            assigned_by=assignment.assigned_by,
            assigned_at=assignment.assigned_at,
            status=assignment.status,
            notes=assignment.notes,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"分配课程失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配课程失败",
        ) from e


@router.get("/courses/{course_id}/assignment-conflicts")
@require_admin
async def check_course_assignment_conflicts(
    course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """检查课程分配冲突 - 需求5验收标准1."""
    try:
        service = AdminService(db)
        conflicts = await service.check_course_assignment_conflicts(course_id, teacher_id)

        logger.info(f"管理员 {current_user.id} 检查课程分配冲突")

        return {
            "course_id": course_id,
            "teacher_id": teacher_id,
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
        }

    except Exception as e:
        logger.error(f"检查课程分配冲突失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查课程分配冲突失败",
        ) from e


# ===== 需求6：系统监控与数据决策支持 =====


@router.get("/monitoring/system")
@require_admin
async def get_system_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SystemMonitoringResponse:
    """系统监控数据 - 需求6验收标准2."""
    try:
        service = AdminService(db)
        monitoring_data = await service.get_system_monitoring()

        logger.info(f"管理员 {current_user.id} 查看系统监控")

        return SystemMonitoringResponse(**monitoring_data)

    except Exception as e:
        logger.error(f"获取系统监控数据失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统监控数据失败",
        ) from e


@router.post("/reports/generate")
@require_admin
async def generate_admin_report(
    report_type: str = Query(..., description="报告类型"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """生成管理员报告 - 需求6验收标准3."""
    try:
        service = AdminService(db)
        report = await service.generate_admin_report(
            report_type, start_date, end_date, current_user.id
        )

        logger.info(f"管理员 {current_user.id} 生成 {report_type} 报告")

        return {
            "message": "报告生成成功",
            "report_type": report_type,
            "report_id": report.get("report_id"),
            "file_path": report.get("file_path"),
            "generated_by": current_user.id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"生成管理员报告失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成管理员报告失败",
        ) from e


# ===== 需求8：班级与课程规则管理 =====


@router.get("/system/rules")
@require_admin
async def get_system_rules(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SystemRulesConfigResponse:
    """获取系统规则配置 - 需求8验收标准1."""
    try:
        service = AdminService(db)
        rules = await service.get_system_rules()

        logger.info(f"管理员 {current_user.id} 查看系统规则配置")

        return SystemRulesConfigResponse(**rules)

    except Exception as e:
        logger.error(f"获取系统规则配置失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统规则配置失败",
        ) from e


@router.put("/system/rules")
@require_admin
async def update_system_rules(
    request: SystemRulesConfigRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新系统规则配置 - 需求8验收标准1."""
    try:
        service = AdminService(db)
        rules_data = request.model_dump(exclude_unset=True)
        success = await service.update_system_rules(rules_data, current_user.id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="更新系统规则失败",
            )

        logger.info(f"管理员 {current_user.id} 更新系统规则配置")

        return {
            "message": "系统规则配置更新成功",
            "updated_by": current_user.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统规则配置失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统规则配置失败",
        ) from e


@router.post("/system/rules/exemption")
@require_admin
async def create_rule_exemption(
    rule_type: str = Query(..., description="规则类型"),
    target_id: int = Query(..., description="目标ID"),
    reason: str = Query(..., description="豁免原因"),
    duration_days: int = Query(None, description="豁免天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建规则豁免 - 需求8验收标准1."""
    try:
        service = AdminService(db)
        exemption = await service.create_rule_exemption(
            rule_type, target_id, reason, duration_days, current_user.id
        )

        logger.info(f"管理员 {current_user.id} 创建规则豁免: {rule_type}")

        return {
            "message": "规则豁免创建成功",
            "exemption_id": exemption.id,
            "rule_type": rule_type,
            "target_id": target_id,
            "reason": reason,
            "created_by": current_user.id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"创建规则豁免失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建规则豁免失败",
        ) from e


# ===== 需求9：数据备份与恢复 =====


@router.post("/backup/create")
@require_admin
async def create_backup(
    backup_type: str = Query(..., description="备份类型: full/incremental"),
    description: str = Query(None, description="备份描述"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BackupRestoreResponse:
    """创建数据备份 - 需求9验收标准1."""
    try:
        service = AdminService(db)
        backup = await service.create_backup(backup_type, description, current_user.id)

        logger.info(f"超级管理员 {current_user.id} 创建 {backup_type} 备份")

        return BackupRestoreResponse(
            id=backup.id,
            backup_type=backup.backup_type,
            status=backup.status,
            file_path=backup.file_path,
            file_size=backup.file_size,
            description=backup.description,
            created_by=backup.created_by,
            created_at=backup.created_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"创建数据备份失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建数据备份失败",
        ) from e


@router.get("/backup/list")
@require_admin
async def list_backups(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    backup_type: str = Query(None, description="备份类型筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取备份列表 - 需求9验收标准1."""
    try:
        service = AdminService(db)
        backups = await service.list_backups(page, size, backup_type)

        logger.info(f"超级管理员 {current_user.id} 查看备份列表")

        return backups

    except Exception as e:
        logger.error(f"获取备份列表失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取备份列表失败",
        ) from e


@router.post("/backup/{backup_id}/restore")
@require_admin
async def restore_from_backup(
    backup_id: int,
    request: BackupRestoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """从备份恢复数据 - 需求9验收标准2."""
    try:
        service = AdminService(db)
        restore_result = await service.restore_from_backup(
            backup_id, request.restore_modules, current_user.id
        )

        logger.info(f"超级管理员 {current_user.id} 从备份 {backup_id} 恢复数据")

        return {
            "message": "数据恢复操作已启动",
            "backup_id": backup_id,
            "restore_modules": request.restore_modules,
            "restore_job_id": restore_result.get("job_id"),
            "estimated_duration": restore_result.get("estimated_duration"),
            "restored_by": current_user.id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"数据恢复失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据恢复失败",
        ) from e


@router.get("/backup/{backup_id}/verify")
@require_admin
async def verify_backup(
    backup_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """验证备份完整性 - 需求9验收标准1."""
    try:
        service = AdminService(db)
        verification_result = await service.verify_backup(backup_id)

        logger.info(f"超级管理员 {current_user.id} 验证备份 {backup_id}")

        return {
            "backup_id": backup_id,
            "is_valid": verification_result.get("is_valid"),
            "verification_details": verification_result.get("details"),
            "verified_by": current_user.id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"验证备份失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证备份失败",
        ) from e
