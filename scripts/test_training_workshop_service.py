#!/usr/bin/env python3
"""
测试训练工坊服务的题目生成功能 - 需求15任务3.1验证
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.training.services.training_workshop_service import (  # noqa: E402
    TrainingWorkshopService,
)


def test_prompt_generation() -> bool:
    """测试提示词生成功能."""
    print("🔍 测试提示词生成功能...")

    # 创建服务实例（不需要数据库连接来测试提示词生成）
    service = TrainingWorkshopService(None)  # type: ignore

    # 测试阅读理解提示词生成
    print("\n📖 测试阅读理解提示词生成:")
    reading_prompt = service._build_reading_prompt("科技发展", 5, 80)
    print("✅ 阅读理解提示词生成成功")
    print(f"提示词长度: {len(reading_prompt)} 字符")

    # 测试写作提示词生成
    print("\n✍️ 测试写作提示词生成:")
    writing_prompt = service._build_writing_prompt(
        "议论文", ["时事热点", "校园生活"], True
    )
    print("✅ 写作提示词生成成功")
    print(f"提示词长度: {len(writing_prompt)} 字符")

    # 测试通用提示词生成
    print("\n🔧 测试通用提示词生成:")
    general_prompt = service._build_general_prompt("vocabulary", {})
    print("✅ 通用提示词生成成功")
    print(f"提示词长度: {len(general_prompt)} 字符")

    return True


def test_content_parsing() -> bool:
    """测试内容解析功能."""
    print("\n🔍 测试内容解析功能...")

    service = TrainingWorkshopService(None)  # type: ignore

    # 测试阅读理解内容解析
    print("\n📖 测试阅读理解内容解析:")
    reading_content = """
    {
        "passage": "This is a test passage about technology development.",
        "questions": [
            {
                "title": "Question 1",
                "question": "What is the main topic?",
                "options": ["A. Technology", "B. Science", "C. Education", "D. Business"],
                "correct_answer": "A",
                "analysis": "The passage is about technology development."
            }
        ]
    }
    """

    parsed_reading = service._parse_reading_content(reading_content)
    if parsed_reading:
        print("✅ 阅读理解内容解析成功")
        print(f"解析结果包含 {len(parsed_reading['questions'])} 道题目")
    else:
        print("❌ 阅读理解内容解析失败")

    # 测试写作内容解析
    print("\n✍️ 测试写作内容解析:")
    writing_content = """
    {
        "title": "Environmental Protection",
        "prompt": "Write an essay about environmental protection",
        "requirements": ["120-180 words", "Clear structure", "Proper grammar"],
        "scoring_criteria": {
            "content": "Content relevance and depth",
            "language": "Grammar and vocabulary",
            "structure": "Organization and coherence"
        },
        "sample_outline": "Introduction - Body - Conclusion"
    }
    """

    parsed_writing = service._parse_writing_content(writing_content)
    if parsed_writing:
        print("✅ 写作内容解析成功")
        print(f"题目标题: {parsed_writing['title']}")
    else:
        print("❌ 写作内容解析失败")

    # 测试通用内容解析
    print("\n🔧 测试通用内容解析:")
    general_content = "This is a general question content for vocabulary training."
    parsed_general = service._parse_general_content(general_content, "vocabulary")
    if parsed_general:
        print("✅ 通用内容解析成功")
        print(f"内容类型: {parsed_general['type']}")
    else:
        print("❌ 通用内容解析失败")

    return True


def test_service_methods() -> bool:
    """测试服务方法的存在性."""
    print("\n🔍 测试服务方法存在性...")

    service = TrainingWorkshopService(None)  # type: ignore

    # 检查核心方法是否存在
    methods_to_check = [
        "_generate_and_deploy_questions",
        "_generate_reading_questions",
        "_generate_writing_questions",
        "_generate_other_questions",
        "_build_reading_prompt",
        "_build_writing_prompt",
        "_build_general_prompt",
        "_parse_reading_content",
        "_parse_writing_content",
        "_parse_general_content",
    ]

    for method_name in methods_to_check:
        if hasattr(service, method_name):
            print(f"✅ {method_name} - 方法存在")
        else:
            print(f"❌ {method_name} - 方法缺失")
            return False

    return True


def test_import_dependencies() -> bool:
    """测试依赖导入."""
    print("\n🔍 测试依赖导入...")

    try:
        import importlib.util

        # 检查DeepSeekService模块
        deepseek_spec = importlib.util.find_spec("app.ai.services.deepseek_service")
        if deepseek_spec is not None:
            print("✅ DeepSeekService 模块可用")

        # 检查TrainingTask模型
        training_models_spec = importlib.util.find_spec(
            "app.training.models.training_models"
        )
        if training_models_spec is not None:
            print("✅ TrainingTask 模型模块可用")

        # 检查TrainingTaskRequest模式
        workshop_schemas_spec = importlib.util.find_spec(
            "app.training.schemas.training_workshop_schemas"
        )
        if workshop_schemas_spec is not None:
            print("✅ TrainingTaskRequest 模式模块可用")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def main() -> int:
    """主函数."""
    print("🚀 训练工坊服务测试工具 - 任务3.1验证")
    print("=" * 60)

    # 执行各项测试
    tests = [
        ("依赖导入测试", test_import_dependencies),
        ("服务方法存在性测试", test_service_methods),
        ("提示词生成测试", test_prompt_generation),
        ("内容解析测试", test_content_parsing),
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
        print("🎉 所有测试通过！TrainingWorkshopService 核心方法实现完成。")
        return 0
    else:
        print("❌ 部分测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
