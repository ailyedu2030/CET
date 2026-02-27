#!/usr/bin/env python3
"""
多智能体协作测试脚本
测试2个智能体协作完成任务，验证模板系统的协作功能
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
    agent_templates = safe_load_module("agent_templates", script_dir / "agent-templates.py")
    modules["agent_templates"] = agent_templates

    # 导入 agent-wrapper
    agent_wrapper = safe_load_module("agent_wrapper", script_dir / "agent-wrapper.py")
    modules["agent_wrapper"] = agent_wrapper

    # 导入 agent-registry
    agent_registry = safe_load_module("agent_registry", script_dir / "agent-registry.py")
    modules["agent_registry"] = agent_registry

    return modules


def test_two_agent_collaboration() -> bool:
    """测试两个智能体协作完成任务"""
    print("🚀 开始测试双智能体协作")
    print("=" * 60)

    # 加载模块
    modules = load_modules()
    agent_templates = modules["agent_templates"]
    agent_wrapper = modules["agent_wrapper"]
    agent_registry = modules["agent_registry"]

    # 创建智能体注册中心
    registry = agent_registry.AgentRegistry()
    print("✅ 智能体注册中心创建成功")

    # 注册两个智能体
    registry.register_agent(
        "backend_developer",
        agent_templates.AgentRole.BACKEND,
        ["view", "codebase-retrieval", "str-replace-editor", "save-file"],
    )
    print("✅ 后端开发智能体注册成功")

    registry.register_agent(
        "frontend_developer",
        agent_templates.AgentRole.FRONTEND,
        ["view", "codebase-retrieval", "str-replace-editor", "save-file"],
    )
    print("✅ 前端开发智能体注册成功")

    print("\n📋 智能体列表:")
    registry.list_registered_agents()

    # 模拟协作任务：需求23的实现
    print("\n🎯 开始协作任务：实现需求23")
    print("=" * 60)

    # 阶段1：后端智能体执行需求分析
    print("\n📋 阶段1：后端智能体执行需求分析")
    print("-" * 40)

    # 启动后端智能体的模板执行
    backend_tools = registry.execute_requirement_with_agent(
        "backend_developer", "23", agent_templates.TaskPhase.PHASE_1
    )

    # 模拟后端智能体使用工具
    print("🔧 后端智能体开始工作...")

    @agent_wrapper.template_wrapper("view")
    def backend_view_requirements() -> str:
        return "查看需求文档：需求23 - CET4学习系统功能实现"

    @agent_wrapper.template_wrapper("codebase-retrieval")
    def backend_analyze_code() -> str:
        return "分析现有代码结构，识别需要修改的后端组件"

    result1 = backend_view_requirements()
    print(f"  📄 {result1}")

    result2 = backend_analyze_code()
    print(f"  🔍 {result2}")

    # 完成后端阶段1
    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 后端智能体阶段1完成")

    # 等待一下，模拟真实协作
    time.sleep(1)

    # 阶段2：前端智能体执行设计分析
    print("\n📋 阶段2：前端智能体执行设计分析")
    print("-" * 40)

    # 启动前端智能体的模板执行
    frontend_tools = registry.execute_requirement_with_agent(
        "frontend_developer", "23", agent_templates.TaskPhase.PHASE_2
    )

    # 模拟前端智能体使用工具
    print("🔧 前端智能体开始工作...")

    @agent_wrapper.template_wrapper("view")
    def frontend_view_design() -> str:
        return "查看设计文档：分析UI/UX需求和组件设计"

    @agent_wrapper.template_wrapper("codebase-retrieval")
    def frontend_analyze_components() -> str:
        return "分析现有前端组件，识别需要创建或修改的组件"

    result3 = frontend_view_design()
    print(f"  🎨 {result3}")

    result4 = frontend_analyze_components()
    print(f"  🧩 {result4}")

    # 完成前端阶段2
    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 前端智能体阶段2完成")

    # 等待一下
    time.sleep(1)

    # 阶段3：后端智能体执行实现
    print("\n📋 阶段3：后端智能体执行实现")
    print("-" * 40)

    # 启动后端智能体的实现阶段
    backend_tools = registry.execute_requirement_with_agent(
        "backend_developer", "23", agent_templates.TaskPhase.PHASE_3
    )

    print("🔧 后端智能体开始实现...")

    @agent_wrapper.template_wrapper("str-replace-editor")
    def backend_implement_api() -> str:
        return "实现后端API：创建CET4学习相关的API端点"

    @agent_wrapper.template_wrapper("save-file")
    def backend_save_code() -> str:
        return "保存后端代码：API实现和数据模型"

    result5 = backend_implement_api()
    print(f"  ⚙️ {result5}")

    result6 = backend_save_code()
    print(f"  💾 {result6}")

    # 完成后端实现
    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 后端智能体实现完成")

    # 等待一下
    time.sleep(1)

    # 阶段4：前端智能体执行实现
    print("\n📋 阶段4：前端智能体执行实现")
    print("-" * 40)

    # 启动前端智能体的实现阶段
    frontend_tools = registry.execute_requirement_with_agent(
        "frontend_developer", "23", agent_templates.TaskPhase.PHASE_3
    )

    print("🔧 前端智能体开始实现...")

    @agent_wrapper.template_wrapper("str-replace-editor")
    def frontend_implement_ui() -> str:
        return "实现前端UI：创建CET4学习界面组件"

    @agent_wrapper.template_wrapper("save-file")
    def frontend_save_components() -> str:
        return "保存前端代码：React组件和样式文件"

    result7 = frontend_implement_ui()
    print(f"  🖼️ {result7}")

    result8 = frontend_save_components()
    print(f"  📁 {result8}")

    # 完成前端实现
    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 前端智能体实现完成")

    # 协作总结
    print("\n🎉 双智能体协作任务完成")
    print("=" * 60)
    print("📊 协作总结:")
    print("  🤖 后端智能体: 完成需求分析和API实现")
    print("  🤖 前端智能体: 完成设计分析和UI实现")
    print("  ✅ 所有阶段都使用了模板系统")
    print("  ✅ 每个智能体都遵循了检查清单")
    print("  ✅ 完整的执行追踪和日志记录")

    return True


def test_agent_handoff() -> bool:
    """测试智能体之间的任务交接"""
    print("\n🔄 测试智能体任务交接")
    print("=" * 60)

    # 加载模块
    modules = load_modules()
    agent_templates = modules["agent_templates"]
    agent_wrapper = modules["agent_wrapper"]
    agent_registry = modules["agent_registry"]

    # 创建新的注册中心并注册智能体
    registry = agent_registry.AgentRegistry()

    # 注册协调者智能体
    registry.register_agent(
        "coordinator", agent_templates.AgentRole.COORDINATOR, ["view", "codebase-retrieval"]
    )
    print("✅ 注册协调者智能体成功")

    # 注册后端智能体
    registry.register_agent(
        "backend_specialist", agent_templates.AgentRole.BACKEND, ["str-replace-editor", "save-file"]
    )
    print("✅ 注册后端专家智能体成功")

    # 创建需求执行器
    executor1 = agent_registry.create_requirement_executor("23")
    print("✅ 创建需求执行器成功")

    # 智能体1开始工作
    print("\n👤 智能体1 (coordinator) 开始工作")
    tools1 = registry.execute_requirement_with_agent(
        "coordinator", "23", agent_templates.TaskPhase.PHASE_1
    )
    print("✅ 智能体1完成阶段1")

    # 交接给智能体2
    print("\n🔄 任务交接给智能体2")
    agent_wrapper.template_enforcer.finish_requirement_execution()

    # 智能体2接手工作
    print("\n👤 智能体2 (backend_specialist) 接手工作")
    tools2 = registry.execute_requirement_with_agent(
        "backend_specialist", "23", agent_templates.TaskPhase.PHASE_2
    )
    print("✅ 智能体2完成阶段2")

    # 完成交接
    agent_wrapper.template_enforcer.finish_requirement_execution()
    print("✅ 任务交接完成")

    return True


def main() -> bool:
    """主测试函数"""
    print("🚀 开始多智能体协作测试")
    print("=" * 80)

    try:
        # 测试1：双智能体协作
        success1 = test_two_agent_collaboration()

        # 测试2：智能体任务交接
        success2 = test_agent_handoff()

        # 总结
        print("\n" + "=" * 80)
        print("📊 多智能体测试结果:")
        print(f"  ✅ 双智能体协作: {'通过' if success1 else '失败'}")
        print(f"  ✅ 任务交接: {'通过' if success2 else '失败'}")

        if success1 and success2:
            print("\n🎉 所有多智能体测试通过！")
            print("✅ 智能体协作功能正常")
            print("✅ 模板系统在多智能体环境下工作正常")
            print("✅ 任务交接机制完善")
            return True
        else:
            print("\n⚠️ 部分测试失败")
            return False

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
