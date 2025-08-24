#!/usr/bin/env python3
"""调试教育系统测试."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.unit.shared.test_base_model_education_logic import (
    TestEducationModel,
)


def debug_permission_test() -> None:
    """调试权限控制测试."""
    print("调试权限控制测试...")

    try:
        # 创建者权限测试
        model = TestEducationModel(created_by=100, is_deleted=False)  # type: ignore[no-untyped-call]
        print(f"Model created_by: {model.created_by}")
        print(f"Model is_deleted: {model.is_deleted}")

        result1 = model.can_be_modified_by(100)
        print(f"Creator can modify: {result1}")

        result2 = model.can_be_modified_by(101)
        print(f"Other user can modify: {result2}")

        # 软删除记录权限测试
        model.soft_delete()
        print(f"After soft delete - is_deleted: {model.is_deleted}")

        result3 = model.can_be_modified_by(100)
        print(f"Creator can modify after delete: {result3}")

        result4 = model.can_be_modified_by(101)
        print(f"Other user can modify after delete: {result4}")

        print("✅ 权限控制测试通过")

    except Exception as e:
        print(f"❌ 权限控制测试失败: {e}")
        import traceback

        traceback.print_exc()


def debug_safe_update_test() -> None:
    """调试安全更新测试."""
    print("\n调试安全更新测试...")

    try:
        model = TestEducationModel(created_by=100, version=1)  # type: ignore[no-untyped-call]
        print(f"Initial version: {model.version}")

        # 有权限的安全更新
        update_data = {"difficulty_level": 3, "learning_points": 50}
        result = model.safe_update(update_data, user_id=100)

        print(f"Update result: {result}")
        print(f"Difficulty level: {model.difficulty_level}")
        print(f"Learning points: {model.learning_points}")
        print(f"Updated by: {model.updated_by}")
        print(f"New version: {model.version}")

        # 无权限的更新尝试
        model.soft_delete()
        result2 = model.safe_update({"difficulty_level": 4}, user_id=100)
        print(f"Update after delete result: {result2}")
        print(f"Difficulty level unchanged: {model.difficulty_level}")

        print("✅ 安全更新测试通过")

    except Exception as e:
        print(f"❌ 安全更新测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_permission_test()
    debug_safe_update_test()
