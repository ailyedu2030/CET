"""冲突检测工具类 - 提供时间冲突、资源冲突和规则冲突检测功能."""

from datetime import date, datetime, time
from typing import Any


class ConflictDetectionUtils:
    """冲突检测工具类."""

    @staticmethod
    def check_time_conflict(
        existing_schedules: list[dict[str, Any]], new_schedule: dict[str, Any]
    ) -> dict[str, Any]:
        """检测时间冲突."""
        conflicts = []

        new_time_slots = ConflictDetectionUtils._parse_schedule(new_schedule)

        for existing in existing_schedules:
            existing_time_slots = ConflictDetectionUtils._parse_schedule(existing)

            # 检查每个时间段是否有重叠
            for new_slot in new_time_slots:
                for existing_slot in existing_time_slots:
                    if ConflictDetectionUtils._time_slots_overlap(new_slot, existing_slot):
                        conflicts.append(
                            {
                                "type": "time_conflict",
                                "new_slot": new_slot,
                                "existing_slot": existing_slot,
                                "existing_class_id": existing.get("class_id"),
                                "overlap_duration": ConflictDetectionUtils._calculate_overlap(
                                    new_slot, existing_slot
                                ),
                            }
                        )

        return {
            "has_conflict": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "severity": ConflictDetectionUtils._assess_conflict_severity(conflicts),
        }

    @staticmethod
    def check_teacher_workload(
        teacher_id: int,
        current_assignments: list[dict[str, Any]],
        new_assignment: dict[str, Any],
        max_classes: int = 5,
        max_students: int = 250,
    ) -> dict[str, Any]:
        """检查教师工作量."""
        current_class_count = len(current_assignments)
        current_student_count = sum(
            assignment.get("student_count", 0) for assignment in current_assignments
        )

        new_student_count = new_assignment.get("student_count", 0)

        # 计算工作量指标
        workload_metrics = {
            "current_classes": current_class_count,
            "new_total_classes": current_class_count + 1,
            "max_classes": max_classes,
            "current_students": current_student_count,
            "new_total_students": current_student_count + new_student_count,
            "max_students": max_students,
            "class_utilization": (current_class_count + 1) / max_classes,
            "student_utilization": (current_student_count + new_student_count) / max_students,
        }

        # 检查是否超载
        is_overloaded = (
            workload_metrics["new_total_classes"] > max_classes
            or workload_metrics["new_total_students"] > max_students
        )

        # 生成建议
        recommendations = []
        if workload_metrics["class_utilization"] > 0.8:
            recommendations.append("教师班级数接近上限，建议谨慎分配")
        if workload_metrics["student_utilization"] > 0.8:
            recommendations.append("教师学生数接近上限，建议考虑其他教师")
        if is_overloaded:
            recommendations.append("分配将导致超载，建议重新分配")

        return {
            "is_overloaded": is_overloaded,
            "workload_metrics": workload_metrics,
            "risk_level": ConflictDetectionUtils._calculate_workload_risk(workload_metrics),
            "recommendations": recommendations,
        }

    @staticmethod
    def check_binding_rules(
        assignment_type: str, source_data: dict[str, Any], target_data: dict[str, Any]
    ) -> dict[str, Any]:
        """检查绑定规则（1班级↔1教师、1班级↔1课程）."""
        violations = []

        if assignment_type == "class_teacher":
            # 检查班级是否已有教师
            if source_data.get("current_teacher_id"):
                violations.append(
                    {
                        "rule": "one_class_one_teacher",
                        "message": "班级已分配教师，违反1班级↔1教师规则",
                        "current_teacher_id": source_data["current_teacher_id"],
                        "new_teacher_id": target_data["teacher_id"],
                    }
                )

            # 检查教师是否已有此班级类型的课程
            if ConflictDetectionUtils._teacher_has_similar_class(
                target_data["teacher_id"], source_data["course_id"]
            ):
                violations.append(
                    {
                        "rule": "teacher_course_limit",
                        "message": "教师已有相同课程的班级，建议检查工作量",
                        "teacher_id": target_data["teacher_id"],
                        "course_id": source_data["course_id"],
                    }
                )

        elif assignment_type == "class_course":
            # 检查班级是否已绑定课程
            if source_data.get("current_course_id"):
                violations.append(
                    {
                        "rule": "one_class_one_course",
                        "message": "班级已绑定课程，违反1班级↔1课程规则",
                        "current_course_id": source_data["current_course_id"],
                        "new_course_id": target_data["course_id"],
                    }
                )

        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "rule_count": len(violations),
            "severity": "high" if len(violations) > 0 else "none",
        }

    @staticmethod
    def check_capacity_limits(
        class_data: dict[str, Any], new_enrollments: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """检查容量限制."""
        current_students = class_data.get("current_students", 0)
        max_students = class_data.get("max_students", 50)
        new_student_count = len(new_enrollments)

        projected_total = current_students + new_student_count

        capacity_check = {
            "current_students": current_students,
            "max_students": max_students,
            "new_enrollments": new_student_count,
            "projected_total": projected_total,
            "capacity_utilization": projected_total / max_students,
            "is_over_capacity": projected_total > max_students,
            "available_spots": max(0, max_students - current_students),
        }

        # 生成警告和建议
        warnings = []
        if capacity_check["capacity_utilization"] > 1.0:
            warnings.append("超出班级容量限制")
        elif capacity_check["capacity_utilization"] > 0.9:
            warnings.append("接近班级容量上限")
        elif capacity_check["capacity_utilization"] > 0.8:
            warnings.append("班级容量较满，建议关注")

        return {
            "capacity_check": capacity_check,
            "warnings": warnings,
            "can_enroll": not capacity_check["is_over_capacity"],
        }

    @staticmethod
    def detect_schedule_conflicts(
        schedules: list[dict[str, Any]], tolerance_minutes: int = 15
    ) -> dict[str, Any]:
        """检测多个课程表之间的冲突."""
        all_conflicts = []

        for i, schedule1 in enumerate(schedules):
            for j, schedule2 in enumerate(schedules[i + 1 :], i + 1):
                conflict_result = ConflictDetectionUtils.check_time_conflict([schedule1], schedule2)

                if conflict_result["has_conflict"]:
                    for conflict in conflict_result["conflicts"]:
                        all_conflicts.append(
                            {
                                **conflict,
                                "schedule1_id": schedule1.get("id"),
                                "schedule2_id": schedule2.get("id"),
                                "conflict_index": (i, j),
                            }
                        )

        return {
            "total_conflicts": len(all_conflicts),
            "conflicts": all_conflicts,
            "conflict_matrix": ConflictDetectionUtils._build_conflict_matrix(
                schedules, all_conflicts
            ),
            "recommendations": ConflictDetectionUtils._generate_conflict_recommendations(
                all_conflicts
            ),
        }

    @staticmethod
    def _parse_schedule(schedule: dict[str, Any]) -> list[dict[str, Any]]:
        """解析课程表为时间段列表."""
        time_slots = []

        # 支持多种课程表格式
        if "weekly_schedule" in schedule:
            for day, sessions in schedule["weekly_schedule"].items():
                for session in sessions:
                    time_slots.append(
                        {
                            "day": day,
                            "start_time": session.get("start_time"),
                            "end_time": session.get("end_time"),
                            "location": session.get("location"),
                        }
                    )
        elif "time_slots" in schedule:
            time_slots = schedule["time_slots"]
        else:
            # 尝试直接解析
            if "day" in schedule and "start_time" in schedule:
                time_slots.append(schedule)

        return time_slots

    @staticmethod
    def _time_slots_overlap(slot1: dict[str, Any], slot2: dict[str, Any]) -> bool:
        """检查两个时间段是否重叠."""
        # 检查是否同一天
        if slot1.get("day") != slot2.get("day"):
            return False

        # 解析时间
        start1 = ConflictDetectionUtils._parse_time(slot1.get("start_time"))
        end1 = ConflictDetectionUtils._parse_time(slot1.get("end_time"))
        start2 = ConflictDetectionUtils._parse_time(slot2.get("start_time"))
        end2 = ConflictDetectionUtils._parse_time(slot2.get("end_time"))

        if not all([start1, end1, start2, end2]):
            return False

        # 检查时间重叠 (这里start1, end1, start2, end2都不是None)
        assert start1 is not None and end1 is not None and start2 is not None and end2 is not None
        return start1 < end2 and start2 < end1

    @staticmethod
    def _parse_time(time_str: str | None) -> time | None:
        """解析时间字符串."""
        if not time_str:
            return None

        try:
            if isinstance(time_str, str):
                # 支持多种时间格式
                if ":" in time_str:
                    time_parts = time_str.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    return time(hour, minute)
                else:
                    # 假设是24小时制的数字
                    hour = int(time_str) // 100
                    minute = int(time_str) % 100
                    return time(hour, minute)
        except (ValueError, IndexError):
            pass

        return None

    @staticmethod
    def _calculate_overlap(slot1: dict[str, Any], slot2: dict[str, Any]) -> int:
        """计算重叠时间（分钟）."""
        start1 = ConflictDetectionUtils._parse_time(slot1.get("start_time"))
        end1 = ConflictDetectionUtils._parse_time(slot1.get("end_time"))
        start2 = ConflictDetectionUtils._parse_time(slot2.get("start_time"))
        end2 = ConflictDetectionUtils._parse_time(slot2.get("end_time"))

        if not all([start1, end1, start2, end2]):
            return 0

        # 计算重叠开始和结束时间 (这里start1, end1, start2, end2都不是None)
        assert start1 is not None and end1 is not None and start2 is not None and end2 is not None
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start >= overlap_end:
            return 0

        # 计算重叠分钟数
        overlap_delta = datetime.combine(date.today(), overlap_end) - datetime.combine(
            date.today(), overlap_start
        )
        return int(overlap_delta.total_seconds() / 60)

    @staticmethod
    def _assess_conflict_severity(conflicts: list[dict[str, Any]]) -> str:
        """评估冲突严重性."""
        if not conflicts:
            return "none"

        total_overlap = sum(conflict.get("overlap_duration", 0) for conflict in conflicts)

        if total_overlap > 120:  # 超过2小时
            return "critical"
        elif total_overlap > 60:  # 超过1小时
            return "high"
        elif total_overlap > 15:  # 超过15分钟
            return "medium"
        else:
            return "low"

    @staticmethod
    def _calculate_workload_risk(metrics: dict[str, float]) -> str:
        """计算工作量风险等级."""
        class_risk = metrics["class_utilization"]
        student_risk = metrics["student_utilization"]

        max_risk = max(class_risk, student_risk)

        if max_risk >= 1.0:
            return "critical"
        elif max_risk >= 0.9:
            return "high"
        elif max_risk >= 0.8:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _teacher_has_similar_class(teacher_id: int, course_id: int) -> bool:
        """检查教师是否已有相似课程的班级."""
        # 这里需要查询数据库，暂时返回False
        # 在实际实现中，应该查询数据库检查教师的现有分配
        return False

    @staticmethod
    def _build_conflict_matrix(
        schedules: list[dict[str, Any]], conflicts: list[dict[str, Any]]
    ) -> list[list[bool]]:
        """构建冲突矩阵."""
        n = len(schedules)
        matrix = [[False] * n for _ in range(n)]

        for conflict in conflicts:
            i, j = conflict["conflict_index"]
            matrix[i][j] = True
            matrix[j][i] = True

        return matrix

    @staticmethod
    def _generate_conflict_recommendations(
        conflicts: list[dict[str, Any]],
    ) -> list[str]:
        """生成冲突解决建议."""
        recommendations: list[str] = []

        if not conflicts:
            return recommendations

        # 按冲突类型分组
        time_conflicts = [c for c in conflicts if c["type"] == "time_conflict"]

        if time_conflicts:
            recommendations.append(f"发现{len(time_conflicts)}个时间冲突，建议调整课程时间")

            # 分析高峰时段
            peak_times: dict[str, int] = {}
            for conflict in time_conflicts:
                start_time = conflict.get("new_slot", {}).get("start_time")
                if start_time:
                    peak_times[start_time] = peak_times.get(start_time, 0) + 1

            if peak_times:
                most_conflicted = max(peak_times, key=lambda x: peak_times[x])
                recommendations.append(f"时间段{most_conflicted}冲突最多，建议避开此时段")

        return recommendations
