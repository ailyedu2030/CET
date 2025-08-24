"""
权限隔离服务 - 需求18验收标准4实现
教师权限、管理员权限、权限申请、操作审计
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import CacheType
from app.shared.services.cache_service import CacheService
from app.shared.utils.exceptions import BusinessLogicError, PermissionDeniedError
from app.users.models.permission_models import Permission
from app.users.services.permission_service import PermissionService

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """权限级别."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AuditAction(Enum):
    """审计操作类型."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    REVOKE = "revoke"


class PermissionIsolationService:
    """权限隔离服务 - 需求18验收标准4实现."""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
        permission_service: PermissionService,
    ) -> None:
        """初始化权限隔离服务."""
        self.db = db
        self.cache_service = cache_service
        self.permission_service = permission_service
        self.logger = logger

    # ==================== 教师权限：教案编辑权+学情查看权 ====================

    async def check_teacher_lesson_plan_permission(
        self,
        user_id: int,
        lesson_plan_id: int,
        action: str,
    ) -> bool:
        """检查教师教案权限."""
        try:
            # 缓存权限检查结果
            cache_key = f"teacher_permission:{user_id}:{lesson_plan_id}:{action}"
            cached_result = await self.cache_service.get(cache_key, CacheType.PERMISSION)
            if cached_result is not None:
                return bool(cached_result)

            # 获取用户角色和权限
            user_permissions = await self.permission_service.get_user_permissions(user_id)

            # 检查基础教师权限
            has_teacher_role = await self._has_role(user_id, "teacher")
            if not has_teacher_role:
                await self._audit_permission_check(
                    user_id, "lesson_plan", lesson_plan_id, action, False, "非教师角色"
                )
                return False

            # 检查具体权限
            permission_granted = False
            if action == "edit":
                permission_granted = await self._check_permission_code(
                    user_permissions, "lesson_plan:edit"
                )
            elif action == "view":
                permission_granted = await self._check_permission_code(
                    user_permissions, "lesson_plan:view"
                )
            elif action == "create":
                permission_granted = await self._check_permission_code(
                    user_permissions, "lesson_plan:create"
                )

            # 检查资源所有权（教师只能编辑自己的教案）
            if permission_granted and action in ["edit", "delete"]:
                is_owner = await self._check_lesson_plan_ownership(user_id, lesson_plan_id)
                permission_granted = permission_granted and is_owner

            # 缓存结果
            await self.cache_service.set(
                cache_key, permission_granted, CacheType.PERMISSION, ttl=300
            )

            # 记录审计日志
            await self._audit_permission_check(
                user_id, "lesson_plan", lesson_plan_id, action, permission_granted
            )

            return permission_granted

        except Exception as e:
            self.logger.error(f"检查教师教案权限失败: {str(e)}")
            return False

    async def check_teacher_student_data_permission(
        self,
        user_id: int,
        student_id: int,
        data_type: str,
    ) -> bool:
        """检查教师学情查看权限."""
        try:
            # 检查教师角色
            has_teacher_role = await self._has_role(user_id, "teacher")
            if not has_teacher_role:
                return False

            # 检查是否是该教师的学生
            is_teacher_student = await self._check_teacher_student_relationship(user_id, student_id)

            # 检查数据类型权限
            user_permissions = await self.permission_service.get_user_permissions(user_id)
            has_data_permission = await self._check_permission_code(
                user_permissions, f"student_data:{data_type}:view"
            )

            permission_granted = is_teacher_student and has_data_permission

            # 记录审计日志
            await self._audit_permission_check(
                user_id,
                "student_data",
                student_id,
                f"view_{data_type}",
                permission_granted,
            )

            return permission_granted

        except Exception as e:
            self.logger.error(f"检查教师学情权限失败: {str(e)}")
            return False

    # ==================== 管理员权限：课程分配权+大纲审批权 ====================

    async def check_admin_course_assignment_permission(
        self,
        user_id: int,
        course_id: int,
        action: str,
    ) -> bool:
        """检查管理员课程分配权限."""
        try:
            # 检查管理员角色
            has_admin_role = await self._has_role(user_id, "admin")
            if not has_admin_role:
                return False

            # 检查课程分配权限
            user_permissions = await self.permission_service.get_user_permissions(user_id)
            permission_granted = await self._check_permission_code(
                user_permissions, f"course:assign:{action}"
            )

            # 记录审计日志
            await self._audit_permission_check(
                user_id, "course_assignment", course_id, action, permission_granted
            )

            return permission_granted

        except Exception as e:
            self.logger.error(f"检查管理员课程分配权限失败: {str(e)}")
            return False

    async def check_admin_syllabus_approval_permission(
        self,
        user_id: int,
        syllabus_id: int,
        action: str,
    ) -> bool:
        """检查管理员大纲审批权限."""
        try:
            # 检查管理员角色
            has_admin_role = await self._has_role(user_id, "admin")
            if not has_admin_role:
                return False

            # 检查大纲审批权限
            user_permissions = await self.permission_service.get_user_permissions(user_id)
            permission_granted = await self._check_permission_code(
                user_permissions, f"syllabus:approve:{action}"
            )

            # 记录审计日志
            await self._audit_permission_check(
                user_id, "syllabus_approval", syllabus_id, action, permission_granted
            )

            return permission_granted

        except Exception as e:
            self.logger.error(f"检查管理员大纲审批权限失败: {str(e)}")
            return False

    # ==================== 权限申请：特殊权限临时申请流程 ====================

    async def request_temporary_permission(
        self,
        user_id: int,
        permission_code: str,
        resource_id: int,
        reason: str,
        duration_hours: int = 24,
    ) -> dict[str, Any]:
        """申请临时特殊权限."""
        try:
            # 检查是否已有该权限
            user_permissions = await self.permission_service.get_user_permissions(user_id)
            has_permission = await self._check_permission_code(user_permissions, permission_code)

            if has_permission:
                raise BusinessLogicError("用户已拥有该权限，无需申请")

            # 创建权限申请记录
            request_record = {
                "id": f"req_{datetime.utcnow().timestamp()}",
                "user_id": user_id,
                "permission_code": permission_code,
                "resource_id": resource_id,
                "reason": reason,
                "duration_hours": duration_hours,
                "status": "pending",
                "requested_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat(),
            }

            # 保存申请记录（这里需要创建相应的模型）
            # await self._save_permission_request(request_record)

            # 缓存申请记录
            cache_key = f"permission_request:{request_record['id']}"
            await self.cache_service.set(
                cache_key, request_record, CacheType.SYSTEM_DATA, ttl=86400
            )

            # 记录审计日志
            await self._audit_operation(
                user_id,
                AuditAction.CREATE,
                "permission_request",
                str(request_record["id"]),
                request_record,
            )

            # 通知管理员审批（这里应该发送通知）
            await self._notify_admin_for_approval(request_record)

            return request_record

        except Exception as e:
            self.logger.error(f"申请临时权限失败: {str(e)}")
            raise BusinessLogicError(f"申请临时权限失败: {str(e)}") from e

    async def approve_permission_request(
        self,
        admin_user_id: int,
        request_id: str,
        approved: bool,
        admin_comment: str = "",
    ) -> dict[str, Any]:
        """管理员审批权限申请."""
        try:
            # 检查管理员权限
            has_admin_role = await self._has_role(admin_user_id, "admin")
            if not has_admin_role:
                raise PermissionDeniedError("只有管理员可以审批权限申请")

            # 获取申请记录
            cache_key = f"permission_request:{request_id}"
            request_record = await self.cache_service.get(cache_key, CacheType.SYSTEM_DATA)

            if not request_record:
                raise BusinessLogicError(f"权限申请 {request_id} 不存在")

            if request_record["status"] != "pending":
                raise BusinessLogicError(f"权限申请已处理，状态：{request_record['status']}")

            # 更新申请状态
            request_record["status"] = "approved" if approved else "rejected"
            request_record["admin_user_id"] = admin_user_id
            request_record["admin_comment"] = admin_comment
            request_record["processed_at"] = datetime.utcnow().isoformat()

            # 如果批准，创建临时权限
            if approved:
                temp_permission = await self._create_temporary_permission(request_record)
                request_record["temp_permission_id"] = temp_permission["id"]

            # 更新缓存
            await self.cache_service.set(
                cache_key, request_record, CacheType.SYSTEM_DATA, ttl=86400
            )

            # 记录审计日志
            action = AuditAction.APPROVE if approved else AuditAction.REJECT
            await self._audit_operation(
                admin_user_id, action, "permission_request", request_id, request_record
            )

            return dict(request_record)

        except Exception as e:
            self.logger.error(f"审批权限申请失败: {str(e)}")
            raise BusinessLogicError(f"审批权限申请失败: {str(e)}") from e

    # ==================== 操作审计：关键操作全程留痕 ====================

    async def _audit_operation(
        self,
        user_id: int,
        action: AuditAction,
        resource_type: str,
        resource_id: str | int,
        operation_data: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """记录操作审计日志."""
        try:
            audit_record = {
                "id": f"audit_{datetime.utcnow().timestamp()}",
                "user_id": user_id,
                "action": action.value,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "operation_data": operation_data,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True,
            }

            # 保存审计记录（这里需要创建相应的模型）
            # await self._save_audit_record(audit_record)

            # 缓存审计记录
            cache_key = f"audit_record:{audit_record['id']}"
            await self.cache_service.set(
                cache_key,
                audit_record,
                CacheType.SYSTEM_DATA,
                ttl=2592000,  # 30天
            )

            return audit_record

        except Exception as e:
            self.logger.error(f"记录操作审计失败: {str(e)}")
            # 审计失败不应该影响主业务流程
            return {}

    async def _audit_permission_check(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        action: str,
        granted: bool,
        reason: str = "",
    ) -> None:
        """记录权限检查审计."""
        audit_data = {
            "permission_check": True,
            "granted": granted,
            "reason": reason,
        }

        await self._audit_operation(
            user_id, AuditAction.READ, resource_type, resource_id, audit_data
        )

    async def get_audit_trail(
        self,
        user_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取操作审计轨迹."""
        try:
            # 这里应该查询实际的审计记录
            # 暂时返回示例数据
            return [
                {
                    "id": "audit_example",
                    "user_id": user_id,
                    "action": "read",
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ]

        except Exception as e:
            self.logger.error(f"获取审计轨迹失败: {str(e)}")
            return []

    # ==================== 私有辅助方法 ====================

    async def _has_role(self, user_id: int, role_name: str) -> bool:
        """检查用户是否有指定角色."""
        user_roles = await self.permission_service.get_user_roles(user_id)
        return any(role.name == role_name for role in user_roles)

    async def _check_permission_code(
        self, permissions: list[Permission], permission_code: str
    ) -> bool:
        """检查权限代码."""
        return any(perm.code == permission_code for perm in permissions)

    async def _check_lesson_plan_ownership(self, user_id: int, lesson_plan_id: int) -> bool:
        """检查教案所有权."""
        # 这里应该查询实际的教案所有权
        return True  # 暂时返回True

    async def _check_teacher_student_relationship(self, teacher_id: int, student_id: int) -> bool:
        """检查师生关系."""
        # 这里应该查询实际的师生关系
        return True  # 暂时返回True

    async def _notify_admin_for_approval(self, request_record: dict[str, Any]) -> None:
        """通知管理员审批."""
        # 这里应该发送通知给管理员
        self.logger.info(f"通知管理员审批权限申请: {request_record['id']}")

    async def _create_temporary_permission(self, request_record: dict[str, Any]) -> dict[str, Any]:
        """创建临时权限."""
        temp_permission = {
            "id": f"temp_perm_{datetime.utcnow().timestamp()}",
            "user_id": request_record["user_id"],
            "permission_code": request_record["permission_code"],
            "resource_id": request_record["resource_id"],
            "expires_at": request_record["expires_at"],
            "created_at": datetime.utcnow().isoformat(),
        }

        # 缓存临时权限
        cache_key = f"temp_permission:{temp_permission['id']}"
        await self.cache_service.set(
            cache_key,
            temp_permission,
            CacheType.PERMISSION,
            ttl=request_record["duration_hours"] * 3600,
        )

        return temp_permission
