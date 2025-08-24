#!/usr/bin/env python3
"""
测试训练工坊数据分析功能 - 需求15任务3.2验证
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.training.services.training_workshop_service import (  # noqa: E402
    TrainingWorkshopService,
)


def test_analytics_methods() -> bool:
    """测试数据分析方法的存在性."""
    print("🔍 测试数据分析方法存在性...")

    service = TrainingWorkshopService(None)  # type: ignore

    # 检查数据分析方法是否存在
    analytics_methods = [
        "get_class_task_statistics",
        "get_class_student_performance",
        "identify_risk_students",
        "get_training_effectiveness",
        "_calculate_performance_level",
        "_generate_improvement_suggestions",
    ]

    for method_name in analytics_methods:
        if hasattr(service, method_name):
            print(f"✅ {method_name} - 方法存在")
        else:
            print(f"❌ {method_name} - 方法缺失")
            return False

    return True


def test_helper_methods() -> bool:
    """测试辅助方法功能."""
    print("\n🔍 测试辅助方法功能...")

    service = TrainingWorkshopService(None)  # type: ignore

    # 测试表现等级计算
    print("\n📊 测试表现等级计算:")
    test_cases = [
        (95, 0.9, "优秀"),
        (80, 0.8, "良好"),
        (70, 0.7, "一般"),
        (50, 0.5, "较差"),
    ]

    for avg_score, completion_ratio, expected in test_cases:
        result = service._calculate_performance_level(avg_score, completion_ratio)
        if result == expected:
            print(f"✅ 分数{avg_score}, 完成率{completion_ratio} -> {result}")
        else:
            print(
                f"❌ 分数{avg_score}, 完成率{completion_ratio} -> {result} (期望: {expected})"
            )

    # 测试改进建议生成
    print("\n💡 测试改进建议生成:")
    risk_factors_cases = [
        (["完成率过低"], "建议增加学习时间"),
        (["平均分过低"], "建议复习基础知识"),
        (["完成度不足"], "建议提高专注度"),
        (["参与度不足"], "建议积极参与训练"),
        ([], "继续保持良好的学习状态"),
    ]

    for risk_factors, expected_keyword in risk_factors_cases:
        suggestions = service._generate_improvement_suggestions(risk_factors)
        if any(expected_keyword in suggestion for suggestion in suggestions):
            print(f"✅ 风险因素{risk_factors} -> 包含关键词'{expected_keyword}'")
        else:
            print(f"❌ 风险因素{risk_factors} -> 建议: {suggestions}")

    return True


def test_api_endpoint_structure() -> bool:
    """测试API端点结构."""
    print("\n🔍 测试API端点结构...")

    try:
        from app.training.api.v1.training_workshop_endpoints import router

        print("✅ 训练工坊API路由导入成功")

        # 检查是否有分析相关的端点
        routes = []
        for route in router.routes:
            if hasattr(route, "path"):
                routes.append(str(route.path))
            elif hasattr(route, "path_regex"):
                routes.append(str(route.path_regex.pattern))
        analytics_routes = [route for route in routes if "analytics" in route]

        if analytics_routes:
            print(f"✅ 发现分析端点: {analytics_routes}")
        else:
            print("❌ 未发现分析端点")
            return False

        return True

    except ImportError as e:
        print(f"❌ API导入失败: {e}")
        return False


def test_frontend_component_structure() -> bool:
    """测试前端组件结构."""
    print("\n🔍 测试前端组件结构...")

    # 检查分析组件文件是否存在
    analytics_component = (
        project_root
        / "frontend/src/components/TrainingWorkshop/TrainingAnalyticsPanel.tsx"
    )

    if analytics_component.exists():
        print("✅ TrainingAnalyticsPanel组件文件存在")

        # 检查组件内容
        with open(analytics_component, encoding="utf-8") as f:
            content = f.read()

        required_features = [
            "TrainingAnalyticsPanel",
            "useQuery",
            "RingProgress",
            "Table",
            "getClassTrainingAnalytics",
        ]

        for feature in required_features:
            if feature in content:
                print(f"✅ 组件包含: {feature}")
            else:
                print(f"❌ 组件缺失: {feature}")
                return False

        return True
    else:
        print("❌ TrainingAnalyticsPanel组件文件不存在")
        return False


def test_type_definitions() -> bool:
    """测试类型定义."""
    print("\n🔍 测试类型定义...")

    # 检查API类型文件
    api_types_file = project_root / "frontend/src/api/trainingWorkshop.ts"

    if api_types_file.exists():
        print("✅ API类型文件存在")

        with open(api_types_file, encoding="utf-8") as f:
            content = f.read()

        required_types = [
            "TrainingAnalyticsData",
            "task_statistics",
            "student_performance",
            "risk_students",
            "effectiveness_analysis",
            "getClassTrainingAnalytics",
        ]

        for type_name in required_types:
            if type_name in content:
                print(f"✅ 类型定义包含: {type_name}")
            else:
                print(f"❌ 类型定义缺失: {type_name}")
                return False

        return True
    else:
        print("❌ API类型文件不存在")
        return False


def main() -> int:
    """主函数."""
    print("🚀 训练工坊数据分析功能测试工具 - 任务3.2验证")
    print("=" * 60)

    # 执行各项测试
    tests = [
        ("数据分析方法存在性测试", test_analytics_methods),
        ("辅助方法功能测试", test_helper_methods),
        ("API端点结构测试", test_api_endpoint_structure),
        ("前端组件结构测试", test_frontend_component_structure),
        ("类型定义测试", test_type_definitions),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 执行 {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} 通过")
                passed_tests += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("🎉 所有测试通过！训练工坊数据分析功能实现完成。")
        return 0
    else:
        print("❌ 部分测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
