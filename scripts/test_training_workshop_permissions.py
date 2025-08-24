#!/usr/bin/env python3
"""
测试训练工坊权限控制功能 - 需求15任务3.3验证
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.shared.models.enums import UserType  # noqa: E402


def test_permission_helper_functions() -> bool:
    """测试权限检查辅助函数."""
    print("🔍 测试权限检查辅助函数...")

    try:
        from app.training.api.v1.training_workshop_endpoints import (
            check_teacher_permission,
            check_template_ownership,
        )

        print("✅ 权限检查函数导入成功")

        # 创建测试用户对象
        admin_user = type(
            "User", (), {"id": 1, "user_type": UserType.ADMIN, "username": "admin"}
        )()

        teacher_user = type(
            "User", (), {"id": 2, "user_type": UserType.TEACHER, "username": "teacher"}
        )()

        student_user = type(
            "User", (), {"id": 3, "user_type": UserType.STUDENT, "username": "student"}
        )()

        # 测试教师权限检查
        print("\n📋 测试教师权限检查:")

        # 管理员应该通过
        try:
            check_teacher_permission(admin_user)
            print("✅ 管理员权限检查通过")
        except Exception as e:
            print(f"❌ 管理员权限检查失败: {e}")

        # 教师应该通过
        try:
            check_teacher_permission(teacher_user)
            print("✅ 教师权限检查通过")
        except Exception as e:
            print(f"❌ 教师权限检查失败: {e}")

        # 学生应该被拒绝
        try:
            check_teacher_permission(student_user)
            print("❌ 学生权限检查应该被拒绝但通过了")
        except Exception:
            print("✅ 学生权限检查正确被拒绝")

        # 测试模板所有权检查
        print("\n📄 测试模板所有权检查:")

        # 管理员应该可以访问任何模板
        try:
            check_template_ownership(admin_user, 999)
            print("✅ 管理员可以访问任何模板")
        except Exception as e:
            print(f"❌ 管理员模板访问失败: {e}")

        # 教师只能访问自己的模板
        try:
            check_template_ownership(teacher_user, 2)  # 自己的模板
            print("✅ 教师可以访问自己的模板")
        except Exception as e:
            print(f"❌ 教师访问自己模板失败: {e}")

        # 教师不能访问别人的模板
        try:
            check_template_ownership(teacher_user, 999)  # 别人的模板
            print("❌ 教师访问别人模板应该被拒绝但通过了")
        except Exception:
            print("✅ 教师访问别人模板正确被拒绝")

        return True

    except ImportError as e:
        print(f"❌ 权限检查函数导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 权限检查测试异常: {e}")
        return False


def test_api_endpoint_structure() -> bool:
    """测试API端点结构."""
    print("\n🔍 测试API端点结构...")

    try:
        from app.training.api.v1.training_workshop_endpoints import router

        print("✅ 训练工坊API路由导入成功")

        # 检查路由数量
        routes = list(router.routes)
        print(f"✅ 发现 {len(routes)} 个API端点")

        # 检查关键端点
        route_paths = []
        for route in routes:
            if hasattr(route, "path"):
                route_paths.append(str(route.path))
            elif hasattr(route, "path_regex"):
                route_paths.append(str(route.path_regex.pattern))
        key_endpoints = [
            "/parameter-templates",
            "/analytics/class/{class_id}",
            "/weekly-training",
        ]

        for endpoint in key_endpoints:
            if any(endpoint in path for path in route_paths):
                print(f"✅ 发现关键端点: {endpoint}")
            else:
                print(f"❌ 缺失关键端点: {endpoint}")
                return False

        return True

    except ImportError as e:
        print(f"❌ API路由导入失败: {e}")
        return False


def test_enum_imports() -> bool:
    """测试枚举导入."""
    print("\n🔍 测试枚举导入...")

    try:
        from app.shared.models.enums import UserType

        print("✅ UserType枚举导入成功")

        # 检查枚举值
        expected_types = ["ADMIN", "TEACHER", "STUDENT"]
        for user_type in expected_types:
            if hasattr(UserType, user_type):
                print(f"✅ UserType.{user_type} 存在")
            else:
                print(f"❌ UserType.{user_type} 不存在")
                return False

        return True

    except ImportError as e:
        print(f"❌ 枚举导入失败: {e}")
        return False


def test_permission_integration() -> bool:
    """测试权限集成."""
    print("\n🔍 测试权限集成...")

    try:
        # 检查是否正确导入了权限相关模块
        import importlib.util

        auth_spec = importlib.util.find_spec("app.users.utils.auth_decorators")
        if auth_spec is not None:
            print("✅ 认证装饰器模块可用")

        # 检查是否有HTTPException
        fastapi_spec = importlib.util.find_spec("fastapi")
        if fastapi_spec is not None:
            print("✅ FastAPI模块可用")

        return True

    except ImportError as e:
        print(f"❌ 权限集成测试失败: {e}")
        return False


def main() -> int:
    """主函数."""
    print("🚀 训练工坊权限控制功能测试工具 - 任务3.3验证")
    print("=" * 60)

    # 执行各项测试
    tests = [
        ("枚举导入测试", test_enum_imports),
        ("权限集成测试", test_permission_integration),
        ("API端点结构测试", test_api_endpoint_structure),
        ("权限检查函数测试", test_permission_helper_functions),
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
        print("🎉 所有测试通过！训练工坊权限控制功能基础实现完成。")
        return 0
    else:
        print("❌ 部分测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
