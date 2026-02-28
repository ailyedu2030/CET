#!/usr/bin/env python3
"""运行教育系统业务逻辑测试."""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.unit.shared.test_base_model_education_logic import (
    TestEducationSystemBusinessLogic, TestEducationSystemIntegration)


def run_tests() -> bool:
    """运行所有教育系统测试."""
    print("🎓 Running Education System Business Logic Tests...")
    print("=" * 60)

    # 基础业务逻辑测试
    test_class = TestEducationSystemBusinessLogic()

    tests = [
        ("Learning metadata generation", test_class.test_learning_metadata_generation),
        ("User permission control", test_class.test_user_permission_control),
        ("Safe update mechanism", test_class.test_safe_update_mechanism),
        ("Audit log creation", test_class.test_audit_log_creation),
        (
            "Learning difficulty management",
            test_class.test_learning_difficulty_management,
        ),
        ("Learning points system", test_class.test_learning_points_system),
        ("Completion rate tracking", test_class.test_completion_rate_tracking),
        (
            "Soft delete education compliance",
            test_class.test_soft_delete_education_compliance,
        ),
        (
            "Version control optimistic locking",
            test_class.test_version_control_optimistic_locking,
        ),
        ("Data serialization for API", test_class.test_data_serialization_for_api),
        ("Education model inheritance", test_class.test_education_model_inheritance),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()  # type: ignore[no-untyped-call]
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1

    # 集成测试
    print("\n🔗 Running Integration Tests...")
    print("-" * 40)

    integration_test = TestEducationSystemIntegration()
    integration_tests = [
        (
            "Complete learning workflow",
            integration_test.test_complete_learning_workflow,
        ),
        (
            "Multi-user learning scenario",
            integration_test.test_multi_user_learning_scenario,
        ),
        (
            "Learning analytics data preparation",
            integration_test.test_learning_analytics_data_preparation,
        ),
    ]

    for test_name, test_func in integration_tests:
        try:
            test_func()  # type: ignore[no-untyped-call]
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1

    # 测试结果汇总
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All education system business logic tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
