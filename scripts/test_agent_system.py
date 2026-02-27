#!/usr/bin/env python3
"""
智能体模板系统测试脚本
验证所有核心功能是否正常工作
"""

import sys
from pathlib import Path
from typing import Any

# 添加脚本目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


def safe_load_module(module_name: str, file_path: Path) -> Any:
    """安全加载模块，处理类型检查"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块 {module_name} 从 {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


def test_imports() -> bool:
    """测试所有模块是否能正确导入"""
    print("🔍 测试模块导入...")

    try:
        # 导入 agent-templates
        agent_templates = safe_load_module("agent_templates", script_dir / "agent-templates.py")
        AgentTemplateManager = agent_templates.AgentTemplateManager
        TaskPhase = agent_templates.TaskPhase
        AgentRole = agent_templates.AgentRole
        print("✅ agent-templates 导入成功")
    except Exception as e:
        print(f"❌ agent-templates 导入失败: {e}")
        return False

    try:
        # 导入 agent-wrapper
        agent_wrapper = safe_load_module("agent_wrapper", script_dir / "agent-wrapper.py")
        AgentContext = agent_wrapper.AgentContext
        template_enforcer = agent_wrapper.template_enforcer
        template_wrapper = agent_wrapper.template_wrapper
        print("✅ agent-wrapper 导入成功")
    except Exception as e:
        print(f"❌ agent-wrapper 导入失败: {e}")
        return False

    try:
        # 导入 agent-registry
        agent_registry = safe_load_module("agent_registry", script_dir / "agent-registry.py")
        AgentRegistry = agent_registry.AgentRegistry
        init_agent_system = agent_registry.init_agent_system
        print("✅ agent-registry 导入成功")
    except Exception as e:
        print(f"❌ agent-registry 导入失败: {e}")
        return False

    try:
        # 导入 agent-executor
        agent_executor = safe_load_module("agent_executor", script_dir / "agent-executor.py")
        AgentExecutor = agent_executor.AgentExecutor
        print("✅ agent-executor 导入成功")
    except Exception as e:
        print(f"❌ agent-executor 导入失败: {e}")
        return False

    try:
        # 导入 agent-scheduler
        agent_scheduler = safe_load_module("agent_scheduler", script_dir / "agent-scheduler.py")
        AgentScheduler = agent_scheduler.AgentScheduler
        print("✅ agent-scheduler 导入成功")
    except Exception as e:
        print(f"❌ agent-scheduler 导入失败: {e}")
        return False

    try:
        # 导入 start-agent-system
        start_agent_system = safe_load_module(
            "start_agent_system", script_dir / "start-agent-system.py"
        )
        AgentSystemManager = start_agent_system.AgentSystemManager
        print("✅ start-agent-system 导入成功")
    except Exception as e:
        print(f"❌ start-agent-system 导入失败: {e}")
        return False

    return True


def test_template_manager() -> bool:
    """测试模板管理器功能"""
    print("\n🔍 测试模板管理器...")

    try:
        # 导入模块
        agent_templates = safe_load_module("agent_templates", script_dir / "agent-templates.py")

        manager = agent_templates.AgentTemplateManager()
        print("✅ 模板管理器创建成功")

        # 测试获取模板
        template = manager.get_phase_template(agent_templates.TaskPhase.PHASE_1)
        if template:
            print(f"✅ 获取阶段1模板成功: {template.name}")
        else:
            print("❌ 获取阶段1模板失败")
            return False

        # 测试生成命令
        commands = manager.generate_agent_commands("23", agent_templates.TaskPhase.PHASE_1)
        if commands:
            print(f"✅ 生成命令成功，共{len(commands)}个命令")
        else:
            print("❌ 生成命令失败")
            return False

        return True
    except Exception as e:
        print(f"❌ 模板管理器测试失败: {e}")
        return False


def test_agent_context() -> bool:
    """测试智能体上下文功能"""
    print("\n🔍 测试智能体上下文...")

    try:
        from agent_templates import AgentRole, TaskPhase
        from agent_wrapper import AgentContext

        context = AgentContext()
        print("✅ 智能体上下文创建成功")

        # 测试设置上下文
        context.set_context("23", TaskPhase.PHASE_1, AgentRole.COORDINATOR)
        print("✅ 设置上下文成功")

        # 测试获取模板
        template = context.get_current_template()
        if template:
            print(f"✅ 获取当前模板成功: {template.name}")
        else:
            print("❌ 获取当前模板失败")
            return False

        # 测试工具检查
        should_use = context.should_use_template("view")
        print(f"✅ 工具检查功能正常: view工具 -> {should_use}")

        return True
    except Exception as e:
        print(f"❌ 智能体上下文测试失败: {e}")
        return False


def test_agent_registry() -> bool:
    """测试智能体注册系统"""
    print("\n🔍 测试智能体注册系统...")

    try:
        from agent_registry import AgentRegistry
        from agent_templates import AgentRole

        registry = AgentRegistry()
        print("✅ 智能体注册中心创建成功")

        # 测试注册智能体
        registry.register_agent("test_agent", AgentRole.COORDINATOR, ["view", "codebase-retrieval"])
        print("✅ 智能体注册成功")

        # 测试获取工具
        tool = registry.get_agent_tool("test_agent", "view")
        if tool:
            print("✅ 获取智能体工具成功")
        else:
            print("❌ 获取智能体工具失败")
            return False

        return True
    except Exception as e:
        print(f"❌ 智能体注册系统测试失败: {e}")
        return False


def test_template_wrapper() -> bool:
    """测试模板包装器功能"""
    print("\n🔍 测试模板包装器...")

    try:
        from agent_templates import AgentRole, TaskPhase
        from agent_wrapper import template_enforcer, template_wrapper

        # 设置执行上下文
        template_enforcer.start_requirement_execution(
            "23", TaskPhase.PHASE_1, AgentRole.COORDINATOR
        )
        print("✅ 启动需求执行成功")

        # 测试包装器装饰器
        @template_wrapper("test_tool")
        def test_function(arg1: str, arg2: str = "default") -> str:
            return f"测试函数调用: {arg1}, {arg2}"

        # 调用包装后的函数
        result = test_function("test_arg", arg2="test_value")
        print(f"✅ 包装器功能正常: {result}")

        # 完成执行
        template_enforcer.finish_requirement_execution()
        print("✅ 完成需求执行成功")

        return True
    except Exception as e:
        print(f"❌ 模板包装器测试失败: {e}")
        return False


def test_system_integration() -> bool:
    """测试系统集成功能"""
    print("\n🔍 测试系统集成...")

    try:
        from start_agent_system import AgentSystemManager

        # 创建系统管理器
        manager = AgentSystemManager(".")
        print("✅ 系统管理器创建成功")

        # 测试系统初始化
        manager.initialize_system()
        print("✅ 系统初始化成功")

        # 测试状态显示
        manager.show_status()
        print("✅ 状态显示成功")

        return True
    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")
        return False


def main() -> bool:
    """主测试函数"""
    print("🚀 开始测试智能体自动调用模板系统")
    print("=" * 60)

    tests = [
        ("模块导入", test_imports),
        ("模板管理器", test_template_manager),
        ("智能体上下文", test_agent_context),
        ("智能体注册", test_agent_registry),
        ("模板包装器", test_template_wrapper),
        ("系统集成", test_system_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！智能体自动调用模板系统工作正常！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
