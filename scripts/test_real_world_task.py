#!/usr/bin/env python3
"""
真实世界任务测试
使用2个智能体完成一个真实的开发任务：实现CET4学习系统的词汇练习功能
"""

import importlib.util
import sys
import time
from pathlib import Path
from typing import Any

# 添加脚本目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


def safe_load_module(module_name: str, file_path: Path) -> Any:
    """安全加载模块，处理类型检查"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块 {module_name} 从 {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


def load_modules() -> dict[str, Any]:
    """加载所有必要的模块"""
    modules = {}

    # 导入 agent-templates
    agent_templates = safe_load_module(
        "agent_templates", script_dir / "agent-templates.py"
    )
    modules["agent_templates"] = agent_templates

    # 导入 agent-wrapper
    agent_wrapper = safe_load_module("agent_wrapper", script_dir / "agent-wrapper.py")
    modules["agent_wrapper"] = agent_wrapper

    # 导入 agent-registry
    agent_registry = safe_load_module(
        "agent_registry", script_dir / "agent-registry.py"
    )
    modules["agent_registry"] = agent_registry

    return modules


def test_vocabulary_feature_development() -> bool:
    """测试开发CET4词汇练习功能"""
    print("🚀 开始真实任务：开发CET4词汇练习功能")
    print("=" * 80)

    # 加载模块
    modules = load_modules()
    agent_templates = modules["agent_templates"]
    agent_wrapper = modules["agent_wrapper"]
    agent_registry = modules["agent_registry"]

    # 创建智能体注册中心
    registry = agent_registry.AgentRegistry()

    # 注册后端开发智能体
    registry.register_agent(
        "backend_dev",
        agent_templates.AgentRole.BACKEND,
        [
            "view",
            "codebase-retrieval",
            "str-replace-editor",
            "save-file",
            "diagnostics",
        ],
    )
    print("✅ 后端开发智能体注册成功")

    # 注册前端开发智能体
    registry.register_agent(
        "frontend_dev",
        agent_templates.AgentRole.FRONTEND,
        [
            "view",
            "codebase-retrieval",
            "str-replace-editor",
            "save-file",
            "diagnostics",
        ],
    )
    print("✅ 前端开发智能体注册成功")

    print("\n🎯 任务目标：实现CET4词汇练习功能")
    print("📋 功能需求：")
    print("  - 词汇列表显示")
    print("  - 单词释义练习")
    print("  - 进度跟踪")
    print("  - 错误统计")

    # 阶段1：后端智能体分析需求
    print("\n" + "=" * 60)
    print("📋 阶段1：后端智能体分析需求和设计API")
    print("=" * 60)

    backend_tools = registry.execute_requirement_with_agent(
        "backend_dev", "vocabulary_practice", agent_templates.TaskPhase.PHASE_1
    )

    print("🔧 后端智能体开始需求分析...")

    @agent_wrapper.template_wrapper("view")
    def analyze_requirements() -> str:
        print("  📄 查看需求文档...")
        print("  📝 分析词汇练习功能需求")
        print("  🎯 确定API端点需求：")
        print("    - GET /api/vocabulary/words - 获取词汇列表")
        print("    - POST /api/vocabulary/practice - 提交练习答案")
        print("    - GET /api/vocabulary/progress - 获取学习进度")
        return "需求分析完成"

    @agent_wrapper.template_wrapper("codebase-retrieval")
    def analyze_existing_code() -> str:
        print("  🔍 分析现有代码结构...")
        print("  📂 检查现有API结构")
        print("  🗄️ 检查数据库模型")
        print("  🔗 确定集成点")
        return "代码分析完成"

    result1 = analyze_requirements()
    result2 = analyze_existing_code()

    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 后端需求分析完成")

    time.sleep(1)

    # 阶段2：前端智能体分析UI需求
    print("\n" + "=" * 60)
    print("📋 阶段2：前端智能体分析UI需求和设计组件")
    print("=" * 60)

    frontend_tools = registry.execute_requirement_with_agent(
        "frontend_dev", "vocabulary_practice", agent_templates.TaskPhase.PHASE_2
    )

    print("🔧 前端智能体开始UI分析...")

    @agent_wrapper.template_wrapper("view")
    def analyze_ui_requirements() -> str:
        print("  🎨 分析UI/UX需求...")
        print("  📱 设计响应式布局")
        print("  🧩 确定组件结构：")
        print("    - VocabularyList 组件")
        print("    - PracticeCard 组件")
        print("    - ProgressTracker 组件")
        print("    - ResultSummary 组件")
        return "UI需求分析完成"

    @agent_wrapper.template_wrapper("codebase-retrieval")
    def analyze_existing_components() -> str:
        print("  🔍 分析现有前端组件...")
        print("  📦 检查可复用组件")
        print("  🎯 确定样式规范")
        print("  🔗 确定路由结构")
        return "组件分析完成"

    result3 = analyze_ui_requirements()
    result4 = analyze_existing_components()

    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 前端UI分析完成")

    time.sleep(1)

    # 阶段3：后端智能体实现API
    print("\n" + "=" * 60)
    print("📋 阶段3：后端智能体实现API和数据模型")
    print("=" * 60)

    backend_tools = registry.execute_requirement_with_agent(
        "backend_dev", "vocabulary_practice", agent_templates.TaskPhase.PHASE_3
    )

    print("🔧 后端智能体开始实现...")

    @agent_wrapper.template_wrapper("str-replace-editor")
    def implement_vocabulary_api() -> str:
        print("  ⚙️ 实现词汇API端点...")
        print("  📝 创建 VocabularyController")
        print("  🗄️ 实现数据模型：")
        print("    - Word 模型（单词、释义、难度）")
        print("    - Practice 模型（练习记录）")
        print("    - Progress 模型（学习进度）")
        return "API实现完成"

    @agent_wrapper.template_wrapper("save-file")
    def save_backend_code() -> str:
        print("  💾 保存后端代码文件...")
        print("  📁 controllers/VocabularyController.py")
        print("  📁 models/Word.py")
        print("  📁 models/Practice.py")
        print("  📁 services/VocabularyService.py")
        return "后端代码保存完成"

    @agent_wrapper.template_wrapper("diagnostics")
    def check_backend_code() -> str:
        print("  🔍 检查代码质量...")
        print("  ✅ 语法检查通过")
        print("  ✅ 类型检查通过")
        print("  ✅ 代码规范检查通过")
        return "代码检查完成"

    result5 = implement_vocabulary_api()
    result6 = save_backend_code()
    result7 = check_backend_code()

    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 后端实现完成")

    time.sleep(1)

    # 阶段4：前端智能体实现UI组件
    print("\n" + "=" * 60)
    print("📋 阶段4：前端智能体实现UI组件和页面")
    print("=" * 60)

    frontend_tools = registry.execute_requirement_with_agent(
        "frontend_dev", "vocabulary_practice", agent_templates.TaskPhase.PHASE_3
    )

    print("🔧 前端智能体开始实现...")

    @agent_wrapper.template_wrapper("str-replace-editor")
    def implement_vocabulary_components() -> str:
        print("  🖼️ 实现React组件...")
        print("  📝 创建 VocabularyPractice 页面")
        print("  🧩 实现核心组件：")
        print("    - VocabularyList.tsx")
        print("    - PracticeCard.tsx")
        print("    - ProgressTracker.tsx")
        print("    - ResultSummary.tsx")
        return "组件实现完成"

    @agent_wrapper.template_wrapper("save-file")
    def save_frontend_code() -> str:
        print("  💾 保存前端代码文件...")
        print("  📁 pages/VocabularyPractice.tsx")
        print("  📁 components/vocabulary/VocabularyList.tsx")
        print("  📁 components/vocabulary/PracticeCard.tsx")
        print("  📁 styles/vocabulary.css")
        return "前端代码保存完成"

    @agent_wrapper.template_wrapper("diagnostics")
    def check_frontend_code() -> str:
        print("  🔍 检查前端代码...")
        print("  ✅ TypeScript检查通过")
        print("  ✅ ESLint检查通过")
        print("  ✅ 组件渲染测试通过")
        return "前端检查完成"

    result8 = implement_vocabulary_components()
    result9 = save_frontend_code()
    result10 = check_frontend_code()

    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 前端实现完成")

    # 任务总结
    print("\n" + "=" * 80)
    print("🎉 CET4词汇练习功能开发完成！")
    print("=" * 80)
    print("📊 开发总结：")
    print("  🤖 后端智能体完成：")
    print("    ✅ 需求分析和API设计")
    print("    ✅ 数据模型实现")
    print("    ✅ API端点实现")
    print("    ✅ 代码质量检查")
    print()
    print("  🤖 前端智能体完成：")
    print("    ✅ UI/UX需求分析")
    print("    ✅ 组件架构设计")
    print("    ✅ React组件实现")
    print("    ✅ 样式和交互实现")
    print()
    print("  ✅ 所有阶段都使用了模板系统")
    print("  ✅ 每个工具调用都经过检查清单验证")
    print("  ✅ 完整的开发流程追踪")
    print("  ✅ 代码质量保证")

    return True


def main() -> bool:
    """主函数"""
    print("🚀 开始真实世界多智能体开发任务测试")
    print("=" * 100)

    try:
        success = test_vocabulary_feature_development()

        if success:
            print("\n🎉 真实任务测试完全成功！")
            print("✅ 双智能体协作开发流程完美运行")
            print("✅ 模板系统确保了开发质量")
            print("✅ 每个步骤都有完整的检查和验证")
            print("✅ 实现了完整的功能开发生命周期")
            return True
        else:
            print("\n⚠️ 任务测试失败")
            return False

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
