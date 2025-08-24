"""规则管理服务 - 需求8：班级与课程规则管理."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.models.course_models import (
    RuleConfiguration,
    RuleExecutionLog,
    RuleMonitoring,
)
from app.courses.schemas.rule_schemas import (
    RuleConfigurationCreate,
    RuleConfigurationUpdate,
    RuleMonitoringCreate,
)

logger = logging.getLogger(__name__)


class RuleManagementService:
    """规则管理服务 - 需求8：班级与课程规则管理."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化规则管理服务."""
        self.db = db

    # ===== 规则配置管理 - 需求8.1 =====

    async def create_rule_configuration(
        self, rule_data: RuleConfigurationCreate, creator_id: int
    ) -> RuleConfiguration:
        """创建规则配置 - 需求8验收标准1."""
        try:
            # 检查规则名称是否已存在
            existing_rule = await self.db.execute(
                select(RuleConfiguration).where(RuleConfiguration.rule_name == rule_data.rule_name)
            )
            if existing_rule.scalar_one_or_none():
                raise ValueError(f"规则名称已存在: {rule_data.rule_name}")

            # 创建规则配置
            rule_config = RuleConfiguration(
                rule_name=rule_data.rule_name,
                rule_type=rule_data.rule_type,
                rule_category=rule_data.rule_category,
                rule_config=rule_data.rule_config,
                is_enabled=rule_data.is_enabled,
                is_strict=rule_data.is_strict,
                allow_exceptions=rule_data.allow_exceptions,
                scope_type=rule_data.scope_type,
                scope_config=rule_data.scope_config,
                description=rule_data.description,
                created_by=creator_id,
            )

            self.db.add(rule_config)
            await self.db.commit()
            await self.db.refresh(rule_config)

            # 记录规则创建日志
            await self._log_rule_execution(
                rule_config.id,
                "creation",
                "success",
                {"action": "rule_created", "rule_name": rule_data.rule_name},
                creator_id,
            )

            logger.info(f"规则配置创建成功: {rule_data.rule_name} (ID: {rule_config.id})")
            return rule_config

        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建规则配置失败: {str(e)}")
            raise

    async def update_rule_configuration(
        self, rule_id: int, rule_data: RuleConfigurationUpdate, updater_id: int
    ) -> RuleConfiguration:
        """更新规则配置 - 需求8验收标准1."""
        try:
            # 获取现有规则
            rule_config = await self.get_rule_configuration(rule_id)
            if not rule_config:
                raise ValueError("规则配置不存在")

            # 记录变更前的配置
            old_config = {
                "rule_config": rule_config.rule_config,
                "is_enabled": rule_config.is_enabled,
                "is_strict": rule_config.is_strict,
                "allow_exceptions": rule_config.allow_exceptions,
            }

            # 更新规则配置
            if rule_data.rule_config is not None:
                rule_config.rule_config = rule_data.rule_config
            if rule_data.is_enabled is not None:
                rule_config.is_enabled = rule_data.is_enabled
            if rule_data.is_strict is not None:
                rule_config.is_strict = rule_data.is_strict
            if rule_data.allow_exceptions is not None:
                rule_config.allow_exceptions = rule_data.allow_exceptions
            if rule_data.scope_config is not None:
                rule_config.scope_config = rule_data.scope_config
            if rule_data.description is not None:
                rule_config.description = rule_data.description

            rule_config.updated_by = updater_id
            rule_config.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(rule_config)

            # 记录规则更新日志
            await self._log_rule_execution(
                rule_id,
                "update",
                "success",
                {
                    "action": "rule_updated",
                    "old_config": old_config,
                    "new_config": {
                        "rule_config": rule_config.rule_config,
                        "is_enabled": rule_config.is_enabled,
                        "is_strict": rule_config.is_strict,
                        "allow_exceptions": rule_config.allow_exceptions,
                    },
                },
                updater_id,
            )

            logger.info(f"规则配置更新成功: {rule_config.rule_name} (ID: {rule_id})")
            return rule_config

        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新规则配置失败: {str(e)}")
            raise

    async def get_rule_configuration(self, rule_id: int) -> RuleConfiguration | None:
        """获取规则配置详情."""
        try:
            result = await self.db.execute(
                select(RuleConfiguration).where(RuleConfiguration.id == rule_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取规则配置失败: {str(e)}")
            return None

    async def list_rule_configurations(
        self,
        rule_type: str | None = None,
        rule_category: str | None = None,
        is_enabled: bool | None = None,
        scope_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RuleConfiguration]:
        """获取规则配置列表."""
        try:
            query = select(RuleConfiguration)

            # 添加筛选条件
            if rule_type:
                query = query.where(RuleConfiguration.rule_type == rule_type)
            if rule_category:
                query = query.where(RuleConfiguration.rule_category == rule_category)
            if is_enabled is not None:
                query = query.where(RuleConfiguration.is_enabled == is_enabled)
            if scope_type:
                query = query.where(RuleConfiguration.scope_type == scope_type)

            # 分页和排序
            query = query.order_by(desc(RuleConfiguration.created_at)).offset(offset).limit(limit)

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"获取规则配置列表失败: {str(e)}")
            return []

    async def delete_rule_configuration(self, rule_id: int, deleter_id: int) -> bool:
        """删除规则配置."""
        try:
            rule_config = await self.get_rule_configuration(rule_id)
            if not rule_config:
                raise ValueError("规则配置不存在")

            # 记录删除日志
            await self._log_rule_execution(
                rule_id,
                "deletion",
                "success",
                {"action": "rule_deleted", "rule_name": rule_config.rule_name},
                deleter_id,
            )

            await self.db.delete(rule_config)
            await self.db.commit()

            logger.info(f"规则配置删除成功: {rule_config.rule_name} (ID: {rule_id})")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除规则配置失败: {str(e)}")
            return False

    # ===== 规则验证与执行 - 需求8.2 =====

    async def validate_rule_compliance(
        self,
        rule_id: int,
        target_type: str,
        target_id: int,
        context: dict[str, Any],
        executor_id: int | None = None,
    ) -> dict[str, Any]:
        """验证规则合规性 - 需求8验收标准1&2."""
        try:
            rule_config = await self.get_rule_configuration(rule_id)
            if not rule_config:
                raise ValueError("规则配置不存在")

            if not rule_config.is_enabled:
                return {
                    "is_compliant": True,
                    "message": "规则已禁用，跳过验证",
                    "rule_name": rule_config.rule_name,
                }

            # 根据规则类型执行验证
            validation_result = await self._execute_rule_validation(
                rule_config, target_type, target_id, context
            )

            # 记录验证日志
            await self._log_rule_execution(
                rule_id,
                "validation",
                "success" if validation_result["is_compliant"] else "violation",
                {
                    "target_type": target_type,
                    "target_id": target_id,
                    "context": context,
                    "validation_result": validation_result,
                },
                executor_id,
                violation_details=validation_result.get("violations"),
            )

            return validation_result

        except Exception as e:
            logger.error(f"规则验证失败: {str(e)}")
            # 记录错误日志
            if rule_id:
                await self._log_rule_execution(
                    rule_id,
                    "validation",
                    "error",
                    {
                        "target_type": target_type,
                        "target_id": target_id,
                        "error": str(e),
                    },
                    executor_id,
                )
            return {
                "is_compliant": False,
                "message": f"规则验证失败: {str(e)}",
                "error": str(e),
            }

    async def _execute_rule_validation(
        self,
        rule_config: RuleConfiguration,
        target_type: str,
        target_id: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """执行具体的规则验证逻辑."""
        rule_category = rule_config.rule_category
        config = rule_config.rule_config

        if rule_category == "class_binding":
            return await self._validate_class_binding_rules(config, target_type, target_id, context)
        elif rule_category == "classroom_scheduling":
            return await self._validate_classroom_scheduling_rules(
                config, target_type, target_id, context
            )
        elif rule_category == "teacher_workload":
            return await self._validate_teacher_workload_rules(
                config, target_type, target_id, context
            )
        else:
            return {
                "is_compliant": True,
                "message": f"未知规则类型: {rule_category}",
                "warnings": [f"规则类型 {rule_category} 暂未实现验证逻辑"],
            }

    # ===== 规则执行日志 =====

    async def _log_rule_execution(
        self,
        rule_id: int,
        execution_type: str,
        execution_result: str,
        execution_context: dict[str, Any],
        executed_by: int | None = None,
        violation_details: dict[str, Any] | None = None,
        resolution_action: str | None = None,
        target_type: str = "unknown",
        target_id: int = 0,
    ) -> None:
        """记录规则执行日志."""
        try:
            log_entry = RuleExecutionLog(
                rule_id=rule_id,
                execution_type=execution_type,
                execution_result=execution_result,
                execution_context=execution_context,
                violation_details=violation_details,
                resolution_action=resolution_action,
                target_type=target_type,
                target_id=target_id,
                executed_by=executed_by,
                execution_time=datetime.utcnow(),
            )

            self.db.add(log_entry)
            await self.db.commit()

        except Exception as e:
            logger.error(f"记录规则执行日志失败: {str(e)}")
            # 不抛出异常，避免影响主要业务流程

    # ===== 具体规则验证逻辑 =====

    async def _validate_class_binding_rules(
        self,
        config: dict[str, Any],
        target_type: str,
        target_id: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """验证班级绑定规则 - 需求8验收标准1."""
        violations = []

        # 1班级↔1教师规则
        if config.get("one_class_one_teacher", True):
            if target_type == "class" and context.get("teacher_id"):
                # 检查班级是否已有教师
                if (
                    context.get("current_teacher_id")
                    and context["current_teacher_id"] != context["teacher_id"]
                ):
                    violations.append(
                        {
                            "rule": "one_class_one_teacher",
                            "message": "班级已分配教师，违反1班级↔1教师规则",
                            "current_teacher_id": context["current_teacher_id"],
                            "new_teacher_id": context["teacher_id"],
                        }
                    )

        # 1班级↔1课程规则
        if config.get("one_class_one_course", True):
            if target_type == "class" and context.get("course_id"):
                # 检查班级是否已绑定课程
                if (
                    context.get("current_course_id")
                    and context["current_course_id"] != context["course_id"]
                ):
                    violations.append(
                        {
                            "rule": "one_class_one_course",
                            "message": "班级已绑定课程，违反1班级↔1课程规则",
                            "current_course_id": context["current_course_id"],
                            "new_course_id": context["course_id"],
                        }
                    )

        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "rule_count": len(violations),
            "severity": "high" if len(violations) > 0 else "none",
            "message": (
                "班级绑定规则验证完成" if len(violations) == 0 else f"发现{len(violations)}个违规"
            ),
        }

    async def _validate_classroom_scheduling_rules(
        self,
        config: dict[str, Any],
        target_type: str,
        target_id: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """验证教室排课规则 - 需求8验收标准2."""
        violations = []

        # 单时段单教室规则
        if config.get("single_classroom_single_timeslot", True):
            if target_type == "classroom" and context.get("schedule"):
                # 检查时间冲突
                start_time = context["schedule"].get("start_time")
                end_time = context["schedule"].get("end_time")

                if start_time and end_time:
                    # 这里应该查询数据库检查冲突，简化处理
                    has_conflict = context.get("has_time_conflict", False)
                    if has_conflict:
                        violations.append(
                            {
                                "rule": "single_classroom_single_timeslot",
                                "message": "教室在该时段已被占用",
                                "start_time": start_time,
                                "end_time": end_time,
                                "conflicting_class": context.get("conflicting_class"),
                            }
                        )

        # 教室容量规则
        if config.get("classroom_capacity_check", True):
            max_capacity = config.get("max_capacity_ratio", 1.0)
            student_count = context.get("student_count", 0)
            classroom_capacity = context.get("classroom_capacity", 50)

            if student_count > classroom_capacity * max_capacity:
                violations.append(
                    {
                        "rule": "classroom_capacity_exceeded",
                        "message": f"学生数量({student_count})超出教室容量限制({classroom_capacity * max_capacity})",
                        "student_count": student_count,
                        "capacity_limit": classroom_capacity * max_capacity,
                    }
                )

        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "rule_count": len(violations),
            "severity": "high" if len(violations) > 0 else "none",
            "message": (
                "教室排课规则验证完成" if len(violations) == 0 else f"发现{len(violations)}个违规"
            ),
        }

    async def _validate_teacher_workload_rules(
        self,
        config: dict[str, Any],
        target_type: str,
        target_id: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """验证教师工作量规则."""
        violations = []

        # 最大班级数限制
        max_classes = config.get("max_classes_per_teacher", 5)
        current_classes = context.get("current_class_count", 0)

        if current_classes >= max_classes:
            violations.append(
                {
                    "rule": "max_classes_exceeded",
                    "message": f"教师班级数量({current_classes})达到上限({max_classes})",
                    "current_classes": current_classes,
                    "max_classes": max_classes,
                }
            )

        # 最大学生数限制
        max_students = config.get("max_students_per_teacher", 250)
        current_students = context.get("current_student_count", 0)

        if current_students >= max_students:
            violations.append(
                {
                    "rule": "max_students_exceeded",
                    "message": f"教师学生数量({current_students})达到上限({max_students})",
                    "current_students": current_students,
                    "max_students": max_students,
                }
            )

        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "rule_count": len(violations),
            "severity": "medium" if len(violations) > 0 else "none",
            "message": (
                "教师工作量规则验证完成" if len(violations) == 0 else f"发现{len(violations)}个违规"
            ),
        }

    # ===== 规则监控与维护 - 需求8.3 =====

    async def create_rule_monitoring(
        self, monitoring_data: RuleMonitoringCreate, creator_id: int
    ) -> RuleMonitoring:
        """创建规则监控记录 - 需求8验收标准3."""
        try:
            monitoring = RuleMonitoring(
                rule_id=monitoring_data.rule_id,
                monitoring_period=monitoring_data.monitoring_period,
                period_start=monitoring_data.period_start,
                period_end=monitoring_data.period_end,
                created_by=creator_id,
            )

            self.db.add(monitoring)
            await self.db.commit()
            await self.db.refresh(monitoring)

            logger.info(f"规则监控记录创建成功: 规则ID {monitoring_data.rule_id}")
            return monitoring

        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建规则监控记录失败: {str(e)}")
            raise

    async def update_rule_monitoring_statistics(
        self, rule_id: int, period_start: datetime, period_end: datetime
    ) -> dict[str, Any]:
        """更新规则监控统计 - 需求8验收标准3."""
        try:
            # 查询监控记录
            monitoring_query = select(RuleMonitoring).where(
                and_(
                    RuleMonitoring.rule_id == rule_id,
                    RuleMonitoring.period_start == period_start,
                    RuleMonitoring.period_end == period_end,
                )
            )
            monitoring_result = await self.db.execute(monitoring_query)
            monitoring = monitoring_result.scalar_one_or_none()

            if not monitoring:
                raise ValueError("监控记录不存在")

            # 统计执行日志
            log_query = select(RuleExecutionLog).where(
                and_(
                    RuleExecutionLog.rule_id == rule_id,
                    RuleExecutionLog.execution_time >= period_start,
                    RuleExecutionLog.execution_time <= period_end,
                )
            )
            log_result = await self.db.execute(log_query)
            logs = list(log_result.scalars().all())

            # 计算统计数据
            total_executions = len(logs)
            successful_executions = len([log for log in logs if log.execution_result == "success"])
            violation_count = len([log for log in logs if log.execution_result == "violation"])
            exception_count = len([log for log in logs if log.execution_result == "warning"])

            # 计算合规率
            compliance_rate = (
                successful_executions / total_executions if total_executions > 0 else 1.0
            )

            # 计算效果评分
            effectiveness_score = self._calculate_effectiveness_score(
                compliance_rate, violation_count, total_executions
            )

            # 生成优化建议
            optimization_suggestions = self._generate_optimization_suggestions(
                compliance_rate, violation_count, total_executions, logs
            )

            # 更新监控记录
            monitoring.total_executions = total_executions
            monitoring.successful_executions = successful_executions
            monitoring.violation_count = violation_count
            monitoring.exception_count = exception_count
            monitoring.compliance_rate = compliance_rate
            monitoring.effectiveness_score = effectiveness_score
            monitoring.optimization_suggestions = optimization_suggestions

            await self.db.commit()

            logger.info(f"规则监控统计更新成功: 规则ID {rule_id}, 合规率 {compliance_rate:.2%}")

            return {
                "rule_id": rule_id,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "violation_count": violation_count,
                "exception_count": exception_count,
                "compliance_rate": compliance_rate,
                "effectiveness_score": effectiveness_score,
                "optimization_suggestions": optimization_suggestions,
            }

        except Exception as e:
            logger.error(f"更新规则监控统计失败: {str(e)}")
            raise

    def _calculate_effectiveness_score(
        self, compliance_rate: float, violation_count: int, total_executions: int
    ) -> float:
        """计算规则效果评分."""
        # 基础分数基于合规率
        base_score = compliance_rate * 80

        # 根据违规频率调整
        if total_executions > 0:
            violation_rate = violation_count / total_executions
            if violation_rate < 0.05:  # 违规率低于5%
                base_score += 15
            elif violation_rate < 0.1:  # 违规率低于10%
                base_score += 10
            elif violation_rate < 0.2:  # 违规率低于20%
                base_score += 5

        # 根据执行次数调整（执行次数多说明规则被频繁使用）
        if total_executions > 100:
            base_score += 5
        elif total_executions > 50:
            base_score += 3

        return min(100.0, max(0.0, base_score))

    def _generate_optimization_suggestions(
        self,
        compliance_rate: float,
        violation_count: int,
        total_executions: int,
        logs: list[RuleExecutionLog],
    ) -> dict[str, Any]:
        """生成规则优化建议."""
        suggestions = []

        # 基于合规率的建议
        if compliance_rate < 0.8:
            suggestions.append(
                {
                    "type": "compliance_improvement",
                    "priority": "high",
                    "message": f"合规率较低({compliance_rate:.1%})，建议检查规则配置是否合理",
                    "action": "review_rule_configuration",
                }
            )

        # 基于违规次数的建议
        if violation_count > total_executions * 0.2:
            suggestions.append(
                {
                    "type": "violation_reduction",
                    "priority": "medium",
                    "message": f"违规次数较多({violation_count}次)，建议加强规则宣传和培训",
                    "action": "enhance_training",
                }
            )

        # 基于执行频率的建议
        if total_executions < 10:
            suggestions.append(
                {
                    "type": "usage_increase",
                    "priority": "low",
                    "message": "规则使用频率较低，建议检查规则是否被正确应用",
                    "action": "check_rule_application",
                }
            )

        # 基于错误模式的建议
        error_logs = [log for log in logs if log.execution_result == "error"]
        if len(error_logs) > 0:
            suggestions.append(
                {
                    "type": "error_handling",
                    "priority": "high",
                    "message": f"发现{len(error_logs)}个执行错误，建议检查规则逻辑",
                    "action": "fix_rule_logic",
                }
            )

        return {
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat(),
            "total_suggestions": len(suggestions),
        }
