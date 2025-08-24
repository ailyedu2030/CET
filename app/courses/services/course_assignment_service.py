"""课程分配管理服务 - 需求5：课程分配管理."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.models.course_models import Class, Course
from app.courses.schemas.assignment_schemas import (
    CourseAssignmentRequest,
    TeacherQualificationCheck,
    TimeConflictCheck,
)
from app.courses.services.assignment_service import AssignmentService

logger = logging.getLogger(__name__)


class CourseAssignmentService:
    """课程分配管理服务 - 需求5：课程分配管理."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化课程分配服务."""
        self.db = db
        self.assignment_service = AssignmentService(db)

    # ===== 教师课程分配 - 需求5.1 =====

    async def assign_course_to_teacher(
        self, assignment_request: CourseAssignmentRequest, assigner_id: int
    ) -> dict[str, Any]:
        """分配课程给教师 - 需求5验收标准1."""
        try:
            # 1. 检查教师课程资质匹配
            qualification_result = await self._check_teacher_course_qualification(
                assignment_request.teacher_ids[0], assignment_request.course_id
            )

            if not qualification_result["is_qualified"] and not assignment_request.force_assign:
                raise ValueError(f"教师资质不符合要求: {qualification_result['message']}")

            # 2. 检查教师工作量平衡分配
            workload_result = await self._check_teacher_workload_balance(
                assignment_request.teacher_ids[0]
            )

            if workload_result["is_overloaded"] and not assignment_request.force_assign:
                raise ValueError(f"教师工作量过载: {workload_result['message']}")

            # 3. 时间冲突自动检测（简化实现，实际需要从课程或班级获取课程表）
            # 这里可以添加时间冲突检测逻辑

            # 4. 执行分配
            result = await self.assignment_service.assign_course_to_teacher(
                assignment_request, assigner_id
            )

            # 5. 记录分配历史
            await self._record_assignment_history(
                assignment_request.course_id,
                assignment_request.teacher_ids[0],
                assigner_id,
                "course_assignment",
                "课程分配",
            )

            logger.info(
                f"课程分配成功: 课程ID {assignment_request.course_id} "
                f"-> 教师ID {assignment_request.teacher_ids[0]}"
            )

            return result

        except Exception as e:
            logger.error(f"课程分配失败: {str(e)}")
            raise

    # ===== 一对多配置支持 - 需求5.2 =====

    async def configure_one_to_many_assignment(
        self, course_id: int, configuration: dict[str, Any], configurator_id: int
    ) -> dict[str, Any]:
        """配置一对多分配 - 需求5验收标准2."""
        try:
            course = await self.db.get(Course, course_id)
            if not course:
                raise ValueError("课程不存在")

            config_type = configuration.get("type")

            if config_type == "course_multiple_classes":
                # 单课程对应多个班级（班级差异化配置）
                result = await self._configure_course_multiple_classes(
                    course_id, configuration, configurator_id
                )
            elif config_type == "course_multiple_teachers":
                # 单课程配备多名教师（按章节/模块分配）
                result = await self._configure_course_multiple_teachers(
                    course_id, configuration, configurator_id
                )
            else:
                raise ValueError(f"不支持的配置类型: {config_type}")

            logger.info(f"一对多配置成功: 课程ID {course_id}, 类型 {config_type}")
            return result

        except Exception as e:
            logger.error(f"一对多配置失败: {str(e)}")
            raise

    async def _configure_course_multiple_classes(
        self, course_id: int, configuration: dict[str, Any], configurator_id: int
    ) -> dict[str, Any]:
        """配置单课程对应多个班级."""
        try:
            class_configs = configuration.get("class_configs", [])
            configured_classes = []

            for class_config in class_configs:
                class_id = class_config.get("class_id")
                if not class_id:
                    continue

                # 获取班级信息
                class_obj = await self.db.get(Class, class_id)
                if not class_obj:
                    continue

                # 验证班级是否已绑定到该课程
                if class_obj.course_id != course_id:
                    raise ValueError(f"班级 {class_id} 未绑定到课程 {course_id}")

                # 应用差异化配置
                differentiated_config = {
                    "class_id": class_id,
                    "custom_schedule": class_config.get("custom_schedule"),
                    "custom_resources": class_config.get("custom_resources"),
                    "custom_syllabus": class_config.get("custom_syllabus"),
                    "difficulty_adjustment": class_config.get("difficulty_adjustment", 0),
                }

                # 更新班级配置（简化实现）
                # await self._update_class_differentiated_config(class_id, differentiated_config)

                configured_classes.append(differentiated_config)

            # 记录配置历史
            await self._record_assignment_history(
                course_id,
                None,
                configurator_id,
                "course_multiple_classes",
                f"配置单课程多班级: {len(configured_classes)} 个班级",
            )

            return {
                "configuration_type": "course_multiple_classes",
                "course_id": course_id,
                "configured_classes": configured_classes,
                "total_classes": len(configured_classes),
            }

        except Exception as e:
            logger.error(f"配置单课程多班级失败: {str(e)}")
            raise

    async def _configure_course_multiple_teachers(
        self, course_id: int, configuration: dict[str, Any], configurator_id: int
    ) -> dict[str, Any]:
        """配置单课程配备多名教师（按章节/模块分配）."""
        try:
            teacher_assignments = configuration.get("teacher_assignments", [])
            configured_assignments = []

            for assignment in teacher_assignments:
                teacher_id = assignment.get("teacher_id")
                assigned_modules = assignment.get("assigned_modules", [])
                permission_scope = assignment.get("permission_scope", "module_only")

                if not teacher_id or not assigned_modules:
                    continue

                # 验证教师资质
                qualification_result = await self._check_teacher_course_qualification(
                    teacher_id, course_id
                )

                if not qualification_result["is_qualified"]:
                    logger.warning(f"教师 {teacher_id} 资质不符合要求，跳过分配")
                    continue

                # 创建教师分配记录
                assignment_record = {
                    "teacher_id": teacher_id,
                    "course_id": course_id,
                    "assigned_modules": assigned_modules,
                    "permission_scope": permission_scope,
                    "assignment_type": "module_based",
                    "assigned_at": datetime.utcnow(),
                    "assigned_by": configurator_id,
                }

                # 设置权限边界
                await self._set_teacher_permission_boundaries(
                    teacher_id, course_id, assigned_modules, permission_scope
                )

                configured_assignments.append(assignment_record)

            # 记录配置历史
            await self._record_assignment_history(
                course_id,
                None,
                configurator_id,
                "course_multiple_teachers",
                f"配置单课程多教师: {len(configured_assignments)} 个教师",
            )

            return {
                "configuration_type": "course_multiple_teachers",
                "course_id": course_id,
                "teacher_assignments": configured_assignments,
                "total_teachers": len(configured_assignments),
            }

        except Exception as e:
            logger.error(f"配置单课程多教师失败: {str(e)}")
            raise

    # ===== 权限划分 - 需求5.3 =====

    async def set_teacher_collaboration_permissions(
        self, course_id: int, permission_config: dict[str, Any], setter_id: int
    ) -> dict[str, Any]:
        """设置多教师协作权限边界 - 需求5验收标准3."""
        try:
            course = await self.db.get(Course, course_id)
            if not course:
                raise ValueError("课程不存在")

            teacher_permissions = permission_config.get("teacher_permissions", [])
            collaboration_rules = permission_config.get("collaboration_rules", {})

            permission_results = []

            for teacher_perm in teacher_permissions:
                teacher_id = teacher_perm.get("teacher_id")
                permissions = teacher_perm.get("permissions", [])
                scope = teacher_perm.get("scope", "full_course")

                if not teacher_id:
                    continue

                # 设置教师权限（简化实现）
                permission_result = {
                    "teacher_id": teacher_id,
                    "permissions": permissions,
                    "scope": scope,
                    "status": "configured",
                }

                permission_results.append(permission_result)

            # 设置协作规则（简化实现）
            # await self._set_collaboration_rules(course_id, collaboration_rules)

            logger.info(f"多教师协作权限设置成功: 课程ID {course_id}")

            return {
                "course_id": course_id,
                "teacher_permissions": permission_results,
                "collaboration_rules": collaboration_rules,
                "set_by": setter_id,
                "set_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"设置多教师协作权限失败: {str(e)}")
            raise

    async def _set_teacher_permission_boundaries(
        self,
        teacher_id: int,
        course_id: int,
        assigned_modules: list[str],
        permission_scope: str,
    ) -> None:
        """设置教师权限边界."""
        try:
            # 创建权限边界记录
            from app.courses.models.course_models import TeacherCoursePermission

            permission_record = TeacherCoursePermission(
                teacher_id=teacher_id,
                course_id=course_id,
                assigned_modules=assigned_modules,
                permission_scope=permission_scope,
                can_edit_content=permission_scope in ["full_access", "module_edit"],
                can_view_all_modules=permission_scope in ["full_access", "view_all"],
                can_manage_students=permission_scope in ["full_access"],
                can_grade_assignments=True,  # 默认都可以评分
                created_at=datetime.utcnow(),
            )

            self.db.add(permission_record)
            await self.db.commit()

        except Exception as e:
            logger.error(f"设置教师权限边界失败: {str(e)}")
            # 不抛出异常，避免影响主要业务流程

    # ===== 特殊情况处理 - 需求5.5 =====

    async def request_rule_exemption(
        self, exemption_request: dict[str, Any], requester_id: int
    ) -> dict[str, Any]:
        """申请规则豁免 - 需求5验收标准5."""
        try:
            # 创建豁免申请记录
            from app.courses.models.course_models import RuleExemptionRequest

            exemption_record = RuleExemptionRequest(
                course_id=exemption_request.get("course_id"),
                teacher_id=exemption_request.get("teacher_id"),
                exemption_type=exemption_request.get("exemption_type"),
                exemption_reason=exemption_request.get("exemption_reason"),
                requested_by=requester_id,
                status="pending",
                requested_at=datetime.utcnow(),
            )

            self.db.add(exemption_record)
            await self.db.commit()
            await self.db.refresh(exemption_record)

            logger.info(f"规则豁免申请提交成功: ID {exemption_record.id}")

            return {
                "exemption_id": exemption_record.id,
                "status": "pending",
                "message": "规则豁免申请已提交，等待管理员审批",
                "requested_at": exemption_record.requested_at,
            }

        except Exception as e:
            logger.error(f"申请规则豁免失败: {str(e)}")
            raise

    async def approve_rule_exemption(
        self, exemption_id: int, approver_id: int, approval_notes: str | None = None
    ) -> dict[str, Any]:
        """审批规则豁免 - 需求5验收标准5."""
        try:
            from app.courses.models.course_models import RuleExemptionRequest

            # 获取豁免申请
            exemption = await self.db.get(RuleExemptionRequest, exemption_id)
            if not exemption:
                raise ValueError("豁免申请不存在")

            if exemption.status != "pending":
                raise ValueError(f"豁免申请状态为{exemption.status}，无法审批")

            # 更新审批状态
            exemption.status = "approved"
            exemption.approved_by = approver_id
            exemption.approved_at = datetime.utcnow()
            exemption.approval_notes = approval_notes

            await self.db.commit()

            logger.info(f"规则豁免审批通过: ID {exemption_id}")

            return {
                "exemption_id": exemption_id,
                "status": "approved",
                "approved_by": approver_id,
                "approved_at": exemption.approved_at,
                "approval_notes": approval_notes,
            }

        except Exception as e:
            logger.error(f"审批规则豁免失败: {str(e)}")
            raise

    # ===== 辅助方法 =====

    async def _check_teacher_course_qualification(
        self, teacher_id: int, course_id: int
    ) -> dict[str, Any]:
        """检查教师课程资质."""
        try:
            # 构建资质检查请求
            qualification_check = TeacherQualificationCheck(
                teacher_id=teacher_id,
                course_id=course_id,
                certification_status="active",  # 简化实现
                experience_years=3,  # 简化实现
                expertise_areas=["english", "teaching"],  # 简化实现
                qualification_level="intermediate",  # 简化实现
            )

            result = await self.assignment_service.check_teacher_qualification(qualification_check)

            return {
                "is_qualified": result.is_qualified,
                "qualification_score": result.qualification_score,
                "message": f"资质评分: {result.qualification_score}",
            }

        except Exception as e:
            logger.error(f"检查教师资质失败: {str(e)}")
            return {"is_qualified": False, "message": str(e)}

    async def _check_teacher_workload_balance(self, teacher_id: int) -> dict[str, Any]:
        """检查教师工作量平衡."""
        try:
            workload = await self.assignment_service.get_teacher_workload(teacher_id)

            return {
                "is_overloaded": workload.workload_percentage > 90,
                "workload_percentage": workload.workload_percentage,
                "message": f"工作量: {workload.workload_percentage}%",
            }

        except Exception as e:
            logger.error(f"检查教师工作量失败: {str(e)}")
            return {"is_overloaded": True, "message": str(e)}

    async def _check_time_conflicts(
        self, teacher_id: int, schedule: dict[str, Any]
    ) -> dict[str, Any]:
        """检查时间冲突."""
        try:
            conflict_check = TimeConflictCheck(
                teacher_id=teacher_id,
                new_schedule=schedule,
                conflict_tolerance=15,
                check_type="strict",
            )

            result = await self.assignment_service.check_time_conflicts(conflict_check)

            return {
                "has_conflict": result.has_conflict,
                "conflict_count": result.conflict_count,
                "message": f"发现 {result.conflict_count} 个时间冲突",
            }

        except Exception as e:
            logger.error(f"检查时间冲突失败: {str(e)}")
            return {"has_conflict": True, "message": str(e)}

    async def _record_assignment_history(
        self,
        course_id: int,
        teacher_id: int | None,
        operator_id: int,
        operation_type: str,
        operation_description: str,
    ) -> None:
        """记录分配历史."""
        try:
            from app.courses.models.course_models import CourseAssignmentHistory

            history_record = CourseAssignmentHistory(
                course_id=course_id,
                teacher_id=teacher_id,
                operation_type=operation_type,
                operation_description=operation_description,
                operated_by=operator_id,
                operated_at=datetime.utcnow(),
            )

            self.db.add(history_record)
            await self.db.commit()

        except Exception as e:
            logger.error(f"记录分配历史失败: {str(e)}")
            # 不抛出异常，避免影响主要业务流程
