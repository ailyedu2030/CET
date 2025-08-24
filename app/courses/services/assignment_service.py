"""课程分配管理服务 - 实现教师课程分配、工作量平衡和冲突检测."""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.models import Class, Course
from app.courses.schemas.assignment_schemas import (
    BulkAssignmentRequest,
    BulkAssignmentResponse,
    CourseAssignmentRequest,
    QualificationCheckResult,
    TeacherQualificationCheck,
    TeacherWorkloadInfo,
    TimeConflictCheck,
    TimeConflictResult,
    WorkloadBalanceRequest,
    WorkloadBalanceResponse,
)
from app.courses.utils.conflict_detection_utils import ConflictDetectionUtils
from app.users.models import User


class AssignmentService:
    """课程分配管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化分配服务."""
        self.db = db

    async def assign_course_to_teacher(
        self, assignment_request: CourseAssignmentRequest, assigner_id: int
    ) -> dict[str, Any]:
        """分配课程给教师."""
        course = await self.db.get(Course, assignment_request.course_id)
        if not course:
            raise ValueError("课程不存在")

        # 评估候选教师
        teacher_evaluations = []
        for teacher_id in assignment_request.teacher_ids:
            evaluation = await self._evaluate_teacher_for_course(
                teacher_id, assignment_request.course_id
            )
            teacher_evaluations.append(evaluation)

        # 选择最佳教师
        best_teacher = self._select_best_teacher(
            teacher_evaluations, assignment_request.priority_factors
        )

        if not best_teacher and not assignment_request.force_assign:
            raise ValueError("没有找到合适的教师，且不允许强制分配")

        # 执行分配
        selected_teacher_id = (
            best_teacher["teacher_id"] if best_teacher else assignment_request.teacher_ids[0]
        )

        # 创建分配记录（这里简化，实际可能需要单独的分配表）
        assignment_record = {
            "course_id": assignment_request.course_id,
            "teacher_id": selected_teacher_id,
            "assigned_at": datetime.utcnow(),
            "assigned_by": assigner_id,
            "assignment_type": ("direct" if assignment_request.force_assign else "optimal"),
            "assignment_reason": assignment_request.assignment_reason,
            "evaluation_score": best_teacher["total_score"] if best_teacher else 0.0,
        }

        return assignment_record

    async def check_teacher_qualification(
        self, qualification_check: TeacherQualificationCheck
    ) -> QualificationCheckResult:
        """检查教师资质."""
        # 获取教师信息
        teacher = await self.db.get(User, qualification_check.teacher_id)
        if not teacher:
            raise ValueError("教师不存在")

        # 获取课程信息
        course = await self.db.get(Course, qualification_check.course_id)
        if not course:
            raise ValueError("课程不存在")

        # 基础资质检查
        qualification_score = 0.0
        missing_qualifications = []
        recommendations = []

        # 1. 检查认证状态
        if qualification_check.certification_status == "active":
            qualification_score += 30
        elif qualification_check.certification_status == "pending":
            qualification_score += 15
            missing_qualifications.append("教师认证待审核")
        else:
            missing_qualifications.append("缺少有效教师认证")

        # 2. 检查经验年数
        if qualification_check.experience_years >= 3:
            qualification_score += 25
        elif qualification_check.experience_years >= 1:
            qualification_score += 15
            recommendations.append("建议增加更多教学经验")
        else:
            missing_qualifications.append("教学经验不足（少于1年）")

        # 3. 检查专业匹配度
        course_requirements = self._get_course_requirements(course)
        expertise_match = self._calculate_expertise_match(
            qualification_check.expertise_areas, course_requirements
        )
        qualification_score += expertise_match * 25

        if expertise_match < 0.6:
            recommendations.append("建议补充相关专业知识")

        # 4. 检查资质等级
        required_level = course_requirements.get("required_level", "intermediate")
        if qualification_check.qualification_level == required_level:
            qualification_score += 20
        elif self._is_higher_qualification(qualification_check.qualification_level, required_level):
            qualification_score += 25
        else:
            missing_qualifications.append(f"资质等级不符合要求（需要{required_level}）")

        # 确定风险等级
        risk_level = "low"
        if qualification_score < 50:
            risk_level = "high"
        elif qualification_score < 70:
            risk_level = "medium"

        return QualificationCheckResult(
            is_qualified=qualification_score >= 60,
            qualification_score=qualification_score,
            missing_qualifications=missing_qualifications,
            recommendations=recommendations,
            risk_level=risk_level,
        )

    async def get_teacher_workload(self, teacher_id: int) -> TeacherWorkloadInfo:
        """获取教师工作量信息."""
        teacher = await self.db.get(User, teacher_id)
        if not teacher:
            raise ValueError("教师不存在")

        # 获取教师当前班级
        current_classes = await self._get_teacher_current_classes(teacher_id)

        # 计算工作量指标
        total_students = sum(class_obj.current_students for class_obj in current_classes)
        max_classes = 5  # 可配置
        current_class_count = len(current_classes)

        workload_percentage = (current_class_count / max_classes) * 0.6 + (
            total_students / (max_classes * 50)
        ) * 0.4

        # 计算可用时间
        available_hours = max(0, (max_classes - current_class_count) * 4)  # 每班级4小时

        # 计算专业匹配度
        expertise_match = await self._calculate_teacher_expertise_match(teacher_id)

        return TeacherWorkloadInfo(
            teacher_id=teacher_id,
            teacher_name=teacher.username,
            current_classes=current_class_count,
            max_classes=max_classes,
            total_students=total_students,
            workload_percentage=min(1.0, workload_percentage),
            available_hours=available_hours,
            expertise_match=expertise_match,
        )

    async def balance_workload(
        self, balance_request: WorkloadBalanceRequest
    ) -> WorkloadBalanceResponse:
        """平衡教师工作量."""
        # 获取目标教师列表
        target_teachers = await self._get_target_teachers(balance_request)

        # 获取所有教师的工作量信息
        teacher_workloads = []
        for teacher in target_teachers:
            workload = await self.get_teacher_workload(teacher.id)
            teacher_workloads.append(workload)

        # 计算平衡评分
        balance_score = self._calculate_balance_score(teacher_workloads)

        # 生成重分配建议
        recommendations = []
        redistribution_plan = []

        if balance_score < 0.8:  # 需要重新平衡
            recommendations = self._generate_balance_recommendations(teacher_workloads)
            redistribution_plan = await self._create_redistribution_plan(
                teacher_workloads, balance_request.balance_strategy
            )

        return WorkloadBalanceResponse(
            teacher_workloads=teacher_workloads,
            balance_score=balance_score,
            recommendations=recommendations,
            redistribution_plan=redistribution_plan,
        )

    async def check_time_conflicts(self, conflict_check: TimeConflictCheck) -> TimeConflictResult:
        """检查时间冲突."""
        # 获取教师现有课程安排
        existing_schedules = await self._get_teacher_schedules(conflict_check.teacher_id)

        # 使用冲突检测工具
        conflict_result = ConflictDetectionUtils.check_time_conflict(
            existing_schedules, conflict_check.new_schedule
        )

        # 生成解决建议
        resolution_suggestions = []
        if conflict_result["has_conflict"]:
            resolution_suggestions = self._generate_conflict_resolution_suggestions(
                conflict_result["conflicts"]
            )

        # 生成替代时间表
        alternative_schedules = await self._generate_alternative_schedules(
            conflict_check.new_schedule, existing_schedules
        )

        return TimeConflictResult(
            has_conflict=conflict_result["has_conflict"],
            conflict_count=conflict_result["conflict_count"],
            conflict_details=conflict_result["conflicts"],
            resolution_suggestions=resolution_suggestions,
            alternative_schedules=alternative_schedules,
        )

    async def bulk_assignment(self, bulk_request: BulkAssignmentRequest) -> BulkAssignmentResponse:
        """批量分配."""
        import uuid

        batch_id = str(uuid.uuid4())
        total_assignments = len(bulk_request.assignments)
        successful_assignments = 0
        failed_assignments = 0
        conflicts_detected = 0
        assignment_results = []
        error_summary: dict[str, int] = {}

        for assignment_data in bulk_request.assignments:
            try:
                # 预检查冲突（如果不是预演模式）
                if not bulk_request.dry_run:
                    conflict_check = await self._check_assignment_conflicts(assignment_data)

                    if conflict_check["has_conflict"]:
                        conflicts_detected += 1

                        if bulk_request.conflict_handling == "stop_on_conflict":
                            # 停止后续分配
                            assignment_results.append(
                                {
                                    "assignment": assignment_data,
                                    "status": "stopped",
                                    "reason": "批量操作遇到冲突已停止",
                                    "conflicts": conflict_check["conflicts"],
                                }
                            )
                            break
                        elif bulk_request.conflict_handling == "skip_on_conflict":
                            # 跳过此分配
                            assignment_results.append(
                                {
                                    "assignment": assignment_data,
                                    "status": "skipped",
                                    "reason": "跳过冲突分配",
                                    "conflicts": conflict_check["conflicts"],
                                }
                            )
                            continue

                # 执行分配
                if bulk_request.dry_run:
                    # 预演模式
                    assignment_results.append(
                        {
                            "assignment": assignment_data,
                            "status": "dry_run_success",
                            "reason": "预演模式执行成功",
                        }
                    )
                    successful_assignments += 1
                else:
                    # 实际执行
                    result = await self._execute_single_assignment(assignment_data)
                    assignment_results.append(
                        {
                            "assignment": assignment_data,
                            "status": "success",
                            "result": result,
                        }
                    )
                    successful_assignments += 1

            except Exception as e:
                failed_assignments += 1
                error_type = type(e).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1

                assignment_results.append(
                    {
                        "assignment": assignment_data,
                        "status": "failed",
                        "error": str(e),
                        "error_type": error_type,
                    }
                )

        return BulkAssignmentResponse(
            batch_id=batch_id,
            total_assignments=total_assignments,
            successful_assignments=successful_assignments,
            failed_assignments=failed_assignments,
            conflicts_detected=conflicts_detected,
            assignment_results=assignment_results,
            error_summary=error_summary,
        )

    async def _evaluate_teacher_for_course(self, teacher_id: int, course_id: int) -> dict[str, Any]:
        """评估教师是否适合教授课程."""
        teacher = await self.db.get(User, teacher_id)
        course = await self.db.get(Course, course_id)

        if not teacher or not course:
            return {"teacher_id": teacher_id, "total_score": 0.0, "suitable": False}

        # 获取教师工作量
        workload = await self.get_teacher_workload(teacher_id)

        # 计算评分
        scores = {
            "workload_score": max(0, 1.0 - workload.workload_percentage) * 30,
            "experience_score": min(30, workload.available_hours / 20 * 30),
            "expertise_score": sum(workload.expertise_match.values())
            / max(1, len(workload.expertise_match))
            * 40,
        }

        total_score = sum(scores.values())

        return {
            "teacher_id": teacher_id,
            "teacher_name": teacher.username,
            "total_score": total_score,
            "scores": scores,
            "suitable": total_score >= 60,
        }

    def _select_best_teacher(
        self, evaluations: list[dict[str, Any]], priority_factors: dict[str, float]
    ) -> dict[str, Any] | None:
        """选择最佳教师."""
        suitable_teachers = [e for e in evaluations if e["suitable"]]

        if not suitable_teachers:
            return None

        # 应用优先级因子调整评分
        for teacher in suitable_teachers:
            adjusted_score = teacher["total_score"]

            # 应用自定义权重
            if priority_factors:
                for factor, weight in priority_factors.items():
                    if factor in teacher["scores"]:
                        adjusted_score += teacher["scores"][factor] * weight

            teacher["adjusted_score"] = adjusted_score

        # 返回评分最高的教师
        return max(suitable_teachers, key=lambda x: x["adjusted_score"])

    def _get_course_requirements(self, course: Course) -> dict[str, Any]:
        """获取课程要求."""
        # 从课程信息中提取要求
        requirements = {
            "required_level": "intermediate",
            "expertise_areas": ["english", "teaching"],
            "min_experience": 1,
        }

        # 根据难度级别调整要求
        if course.difficulty_level.value >= 4:  # 高级课程
            requirements["required_level"] = "advanced"
            requirements["min_experience"] = 3

        return requirements

    def _calculate_expertise_match(
        self, teacher_expertise: list[str], course_requirements: dict[str, Any]
    ) -> float:
        """计算专业匹配度."""
        required_areas = course_requirements.get("expertise_areas", [])

        if not required_areas:
            return 1.0

        matched_areas = set(teacher_expertise) & set(required_areas)
        return len(matched_areas) / len(required_areas)

    def _is_higher_qualification(self, teacher_level: str, required_level: str) -> bool:
        """检查教师资质是否高于要求."""
        level_order = ["basic", "intermediate", "advanced", "expert"]

        try:
            teacher_index = level_order.index(teacher_level)
            required_index = level_order.index(required_level)
            return teacher_index > required_index
        except ValueError:
            return False

    async def _get_teacher_current_classes(self, teacher_id: int) -> list[Class]:
        """获取教师当前班级."""
        stmt = select(Class).where(
            and_(Class.teacher_id == teacher_id, Class.is_active == True)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _calculate_teacher_expertise_match(self, teacher_id: int) -> dict[str, float]:
        """计算教师专业匹配度."""
        # 这里应该基于教师的专业背景、教学记录等计算
        # 简化实现返回模拟数据
        return {
            "english_proficiency": 0.85,
            "teaching_methodology": 0.78,
            "subject_knowledge": 0.82,
            "technology_integration": 0.65,
        }

    async def _get_target_teachers(self, balance_request: WorkloadBalanceRequest) -> list[User]:
        """获取目标教师列表."""
        stmt = select(User).where(User.user_type == "teacher")

        if balance_request.teacher_ids:
            stmt = stmt.where(User.id.in_(balance_request.teacher_ids))

        # 这里可以添加部门筛选等条件

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _calculate_balance_score(self, workloads: list[TeacherWorkloadInfo]) -> float:
        """计算工作量平衡评分."""
        if not workloads:
            return 1.0

        # 计算工作量分布的标准差
        workload_percentages = [w.workload_percentage for w in workloads]
        mean_workload = sum(workload_percentages) / len(workload_percentages)

        variance = sum((w - mean_workload) ** 2 for w in workload_percentages) / len(
            workload_percentages
        )

        std_deviation = variance**0.5

        # 标准差越小，平衡性越好
        balance_score: float = max(0.0, 1.0 - std_deviation * 2)
        return balance_score

    def _generate_balance_recommendations(
        self, workloads: list[TeacherWorkloadInfo]
    ) -> list[dict[str, Any]]:
        """生成平衡建议."""
        recommendations = []

        # 找出工作量过重和过轻的教师
        overloaded_teachers = [w for w in workloads if w.workload_percentage > 0.9]
        underloaded_teachers = [w for w in workloads if w.workload_percentage < 0.5]

        if overloaded_teachers:
            recommendations.append(
                {
                    "type": "reduce_workload",
                    "message": f"建议减少{len(overloaded_teachers)}位教师的工作量",
                    "affected_teachers": [t.teacher_id for t in overloaded_teachers],
                }
            )

        if underloaded_teachers:
            recommendations.append(
                {
                    "type": "increase_workload",
                    "message": f"可以为{len(underloaded_teachers)}位教师增加工作量",
                    "affected_teachers": [t.teacher_id for t in underloaded_teachers],
                }
            )

        return recommendations

    async def _create_redistribution_plan(
        self, workloads: list[TeacherWorkloadInfo], strategy: str
    ) -> list[dict[str, Any]]:
        """创建重分配计划."""
        # 简化实现，实际应该基于具体策略生成详细的重分配计划
        redistribution_plan = []

        overloaded = [w for w in workloads if w.workload_percentage > 0.9]
        underloaded = [w for w in workloads if w.workload_percentage < 0.7]

        for overloaded_teacher in overloaded:
            if underloaded:
                target_teacher = underloaded[0]
                redistribution_plan.append(
                    {
                        "action": "transfer_class",
                        "from_teacher": overloaded_teacher.teacher_id,
                        "to_teacher": target_teacher.teacher_id,
                        "classes_to_transfer": 1,
                        "expected_impact": {
                            "from_workload_change": -0.15,
                            "to_workload_change": 0.15,
                        },
                    }
                )

        return redistribution_plan

    async def _get_teacher_schedules(self, teacher_id: int) -> list[dict[str, Any]]:
        """获取教师课程安排."""
        classes = await self._get_teacher_current_classes(teacher_id)

        schedules = []
        for class_obj in classes:
            if class_obj.schedule:
                schedules.append(
                    {
                        "class_id": class_obj.id,
                        **class_obj.schedule,
                    }
                )

        return schedules

    def _generate_conflict_resolution_suggestions(
        self, conflicts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成冲突解决建议."""
        suggestions = []

        for conflict in conflicts:
            suggestion = {
                "conflict_id": conflict.get("id"),
                "suggestion_type": "time_adjustment",
                "description": "建议调整课程时间以避免冲突",
                "priority": ("high" if conflict.get("overlap_duration", 0) > 60 else "medium"),
            }
            suggestions.append(suggestion)

        return suggestions

    async def _generate_alternative_schedules(
        self, new_schedule: dict[str, Any], existing_schedules: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成替代时间表."""
        # 简化实现，生成几个基本的替代方案
        alternatives = []

        # 方案1：延后1小时
        alt1 = new_schedule.copy()
        if "weekly_schedule" in alt1:
            for _day, sessions in alt1["weekly_schedule"].items():
                for session in sessions:
                    if session.get("start_time"):
                        # 简单的时间调整逻辑
                        current_hour = int(session["start_time"].split(":")[0])
                        session["start_time"] = f"{current_hour + 1:02d}:00"
                        session["end_time"] = f"{current_hour + 2:02d}:00"

        alternatives.append(
            {
                "alternative_id": 1,
                "description": "延后1小时开始",
                "schedule": alt1,
            }
        )

        return alternatives

    async def _check_assignment_conflicts(self, assignment_data: dict[str, Any]) -> dict[str, Any]:
        """检查单个分配的冲突."""
        # 简化实现
        return {
            "has_conflict": False,
            "conflicts": [],
        }

    async def _execute_single_assignment(self, assignment_data: dict[str, Any]) -> dict[str, Any]:
        """执行单个分配."""
        # 根据分配类型执行不同的操作
        assignment_type = assignment_data.get("type")

        if assignment_type == "class_teacher":
            # 分配教师到班级
            class_id = assignment_data["class_id"]
            teacher_id = assignment_data["teacher_id"]

            stmt = (
                update(Class)
                .where(Class.id == class_id)
                .values(teacher_id=teacher_id, updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()

            return {
                "assignment_type": assignment_type,
                "class_id": class_id,
                "teacher_id": teacher_id,
                "assigned_at": datetime.utcnow(),
            }

        # 其他分配类型...
        return {"status": "completed", "assignment_data": assignment_data}
