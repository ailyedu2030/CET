"""课程版本控制工具类 - 提供版本比较、差异分析和合并功能."""

import json
from datetime import datetime
from typing import Any


class VersionUtils:
    """版本控制工具类."""

    @staticmethod
    def compare_versions(
        version1_data: dict[str, Any], version2_data: dict[str, Any]
    ) -> dict[str, Any]:
        """比较两个版本的差异."""
        diff_result: dict[str, Any] = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {},
        }

        all_keys = set(version1_data.keys()) | set(version2_data.keys())

        for key in all_keys:
            if key not in version1_data:
                # 新增字段
                diff_result["added"][key] = version2_data[key]
            elif key not in version2_data:
                # 删除字段
                diff_result["removed"][key] = version1_data[key]
            else:
                # 比较字段值
                val1 = version1_data[key]
                val2 = version2_data[key]

                if isinstance(val1, dict) and isinstance(val2, dict):
                    # 递归比较字典
                    nested_diff = VersionUtils.compare_versions(val1, val2)
                    if any(nested_diff[category] for category in ["added", "removed", "modified"]):
                        diff_result["modified"][key] = nested_diff
                    else:
                        diff_result["unchanged"][key] = val1
                elif val1 != val2:
                    # 值不同
                    diff_result["modified"][key] = {
                        "old_value": val1,
                        "new_value": val2,
                    }
                else:
                    # 值相同
                    diff_result["unchanged"][key] = val1

        return diff_result

    @staticmethod
    def generate_change_summary(diff_result: dict[str, Any]) -> str:
        """生成变更摘要."""
        summary_parts = []

        if diff_result["added"]:
            added_count = len(diff_result["added"])
            summary_parts.append(f"新增 {added_count} 个字段")

        if diff_result["removed"]:
            removed_count = len(diff_result["removed"])
            summary_parts.append(f"删除 {removed_count} 个字段")

        if diff_result["modified"]:
            modified_count = len(diff_result["modified"])
            summary_parts.append(f"修改 {modified_count} 个字段")

        if not summary_parts:
            return "无变更"

        return "、".join(summary_parts)

    @staticmethod
    def extract_key_changes(diff_result: dict[str, Any]) -> list[str]:
        """提取关键变更信息."""
        changes = []

        # 检查重要字段的变更
        important_fields = ["name", "description", "syllabus", "teaching_plan"]

        for field in important_fields:
            if field in diff_result["modified"]:
                changes.append(f"{field}已修改")
            elif field in diff_result["added"]:
                changes.append(f"新增{field}")
            elif field in diff_result["removed"]:
                changes.append(f"删除{field}")

        return changes

    @staticmethod
    def merge_versions(
        base_data: dict[str, Any],
        version1_data: dict[str, Any],
        version2_data: dict[str, Any],
        merge_strategy: str = "latest_wins",
    ) -> dict[str, Any]:
        """合并多个版本."""
        merged_data = base_data.copy()

        if merge_strategy == "latest_wins":
            # 最新版本优先策略
            merged_data.update(version2_data)
            # 如果version2没有某些字段，但version1有，则使用version1的
            for key, value in version1_data.items():
                if key not in version2_data:
                    merged_data[key] = value

        elif merge_strategy == "manual":
            # 手动合并策略（需要人工干预）
            conflicts = {}

            all_keys = set(base_data.keys()) | set(version1_data.keys()) | set(version2_data.keys())

            for key in all_keys:
                base_val = base_data.get(key)
                val1 = version1_data.get(key)
                val2 = version2_data.get(key)

                if val1 == val2:
                    # 两个版本一致
                    if val1 is not None:
                        merged_data[key] = val1
                elif base_val == val1:
                    # version1没有变更，使用version2
                    if val2 is not None:
                        merged_data[key] = val2
                elif base_val == val2:
                    # version2没有变更，使用version1
                    if val1 is not None:
                        merged_data[key] = val1
                else:
                    # 存在冲突，需要人工解决
                    conflicts[key] = {
                        "base": base_val,
                        "version1": val1,
                        "version2": val2,
                    }

            if conflicts:
                merged_data["_merge_conflicts"] = conflicts

        return merged_data

    @staticmethod
    def validate_version_data(version_data: dict[str, Any]) -> dict[str, list[str]]:
        """验证版本数据的完整性."""
        errors: dict[str, list[str]] = {}
        warnings: list[str] = []

        # 检查必需字段
        required_fields = ["name", "syllabus", "teaching_plan"]
        for field in required_fields:
            if field not in version_data or not version_data[field]:
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"缺少必需字段: {field}")

        # 检查数据类型
        type_checks: dict[str, type | tuple[type, ...]] = {
            "name": str,
            "description": (str, type(None)),
            "syllabus": dict,
            "teaching_plan": dict,
            "resource_config": dict,
        }

        for field, expected_type in type_checks.items():
            if field in version_data:
                if not isinstance(version_data[field], expected_type):
                    if field not in errors:
                        errors[field] = []
                    errors[field].append(f"字段类型错误: {field}")

        # 检查数据完整性
        if "syllabus" in version_data and isinstance(version_data["syllabus"], dict):
            syllabus = version_data["syllabus"]
            if not syllabus.get("objectives"):
                warnings.append("教学大纲缺少教学目标")
            if not syllabus.get("chapters"):
                warnings.append("教学大纲缺少章节内容")

        if warnings:
            errors["_warnings"] = warnings

        return errors

    @staticmethod
    def create_version_snapshot(course_data: dict[str, Any]) -> dict[str, Any]:
        """创建版本快照."""
        snapshot = {
            "snapshot_time": datetime.utcnow().isoformat(),
            "data": course_data.copy(),
            "checksum": VersionUtils._calculate_checksum(course_data),
        }
        return snapshot

    @staticmethod
    def verify_snapshot_integrity(snapshot: dict[str, Any]) -> bool:
        """验证快照完整性."""
        if "data" not in snapshot or "checksum" not in snapshot:
            return False

        calculated_checksum: str = VersionUtils._calculate_checksum(snapshot["data"])
        return bool(calculated_checksum == snapshot["checksum"])

    @staticmethod
    def _calculate_checksum(data: dict[str, Any]) -> str:
        """计算数据校验和."""
        import hashlib

        # 将数据序列化为JSON字符串（确保键的顺序一致）
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)

        # 计算MD5校验和
        return hashlib.md5(json_str.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_version_report(
        current_version: dict[str, Any],
        previous_versions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """生成版本报告."""
        report: dict[str, Any] = {
            "current_version": current_version,
            "version_count": len(previous_versions) + 1,
            "change_history": [],
            "key_metrics": {
                "total_changes": 0,
                "major_changes": 0,
                "minor_changes": 0,
            },
        }

        change_history: list[dict[str, Any]] = []
        key_metrics: dict[str, int] = {
            "total_changes": 0,
            "major_changes": 0,
            "minor_changes": 0,
        }

        for i, prev_version in enumerate(previous_versions):
            diff = VersionUtils.compare_versions(prev_version["data"], current_version)
            change_summary = VersionUtils.generate_change_summary(diff)
            key_changes = VersionUtils.extract_key_changes(diff)

            change_count = len(diff["added"]) + len(diff["removed"]) + len(diff["modified"])

            # 判断变更级别
            is_major_change = any(
                field in diff["modified"] for field in ["name", "syllabus", "teaching_plan"]
            )

            change_history.append(
                {
                    "version_index": i,
                    "change_summary": change_summary,
                    "key_changes": key_changes,
                    "change_count": change_count,
                    "is_major_change": is_major_change,
                    "timestamp": prev_version.get("snapshot_time"),
                }
            )

            key_metrics["total_changes"] += change_count
            if is_major_change:
                key_metrics["major_changes"] += 1
            else:
                key_metrics["minor_changes"] += 1

        # 更新报告
        report["change_history"] = change_history
        report["key_metrics"] = key_metrics

        return report
