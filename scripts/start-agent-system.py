#!/usr/bin/env python3
"""
智能体系统启动脚本
自动初始化并确保所有智能体使用模板系统
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# 添加脚本目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


# 安全的模块加载函数
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


# 延迟导入以避免循环依赖
def get_agent_modules() -> tuple[Any, Any]:
    # 导入依赖模块
    agent_templates = safe_load_module(
        "agent_templates", script_dir / "agent-templates.py"
    )
    safe_load_module("agent_wrapper", script_dir / "agent-wrapper.py")
    agent_registry = safe_load_module(
        "agent_registry", script_dir / "agent-registry.py"
    )

    return agent_registry.create_requirement_executor, agent_registry.init_agent_system


# 直接导入TaskPhase以避免类型检查问题
def get_task_phase() -> Any:
    agent_templates = safe_load_module(
        "agent_templates", script_dir / "agent-templates.py"
    )
    return agent_templates.TaskPhase


TaskPhase = get_task_phase()


class AgentSystemManager:
    """智能体系统管理器"""

    def __init__(self: "AgentSystemManager", project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "config" / "agent-system.json"
        self.system_initialized = False
        self.active_executors: dict[str, Any] = {}
        self.config: dict[str, Any] = {}

        # 获取延迟导入的模块
        self.create_requirement_executor, self.init_agent_system = get_agent_modules()

    def initialize_system(self: "AgentSystemManager") -> None:
        """初始化智能体系统"""
        if self.system_initialized:
            print("✅ 智能体系统已初始化")
            return

        print("🚀 启动智能体系统...")
        print("=" * 50)

        # 初始化智能体注册中心
        self.registry = self.init_agent_system()

        # 加载配置
        self._load_system_config()

        # 设置环境变量
        self._setup_environment()

        # 创建必要的目录
        self._create_directories()

        self.system_initialized = True
        print("✅ 智能体系统启动完成")
        print()

        # 显示使用说明
        self._show_usage_instructions()

    def _load_system_config(self: "AgentSystemManager") -> None:
        """加载系统配置"""
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as f:
                config = json.load(f)
                print(f"📋 已加载配置文件: {self.config_file}")
        else:
            # 创建默认配置
            config = self._create_default_config()
            self._save_config(config)
            print(f"📋 已创建默认配置: {self.config_file}")

        self.config = config

    def _create_default_config(self: "AgentSystemManager") -> dict[str, Any]:
        """创建默认配置"""
        return {
            "system": {
                "auto_template_enabled": True,
                "log_level": "INFO",
                "max_concurrent_agents": 5,
                "execution_timeout": 1800,
            },
            "agents": {
                "coordinator": {
                    "enabled": True,
                    "max_tasks": 5,
                    "tools": [
                        "view",
                        "codebase-retrieval",
                        "str-replace-editor",
                        "save-file",
                    ],
                },
                "backend_agent": {
                    "enabled": True,
                    "max_tasks": 2,
                    "tools": [
                        "str-replace-editor",
                        "save-file",
                        "launch-process",
                        "diagnostics",
                    ],
                },
                "frontend_agent": {
                    "enabled": True,
                    "max_tasks": 2,
                    "tools": ["str-replace-editor", "save-file", "view", "diagnostics"],
                },
                "devops_agent": {
                    "enabled": True,
                    "max_tasks": 1,
                    "tools": ["launch-process", "view", "str-replace-editor"],
                },
                "qa_agent": {
                    "enabled": True,
                    "max_tasks": 3,
                    "tools": ["launch-process", "diagnostics", "view"],
                },
            },
            "requirements": {
                "priority_order": ["23", "24", "25", "26", "27", "28", "29", "30"],
                "parallel_execution": True,
                "dependency_check": True,
            },
        }

    def _save_config(self: "AgentSystemManager", config: dict[str, Any]) -> None:
        """保存配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _setup_environment(self: "AgentSystemManager") -> None:
        """设置环境变量"""
        os.environ["AGENT_SYSTEM_ENABLED"] = "true"
        os.environ["AUTO_TEMPLATE_ENABLED"] = str(
            self.config["system"]["auto_template_enabled"]
        ).lower()
        print("🔧 已设置环境变量")

    def _create_directories(self: "AgentSystemManager") -> None:
        """创建必要的目录"""
        directories = [
            self.project_root / "logs" / "agents",
            self.project_root / "temp" / "agent_work",
            self.project_root / "reports" / "execution",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        print("📁 已创建工作目录")

    def _show_usage_instructions(self: "AgentSystemManager") -> None:
        """显示使用说明"""
        print("📖 使用说明:")
        print("=" * 30)
        print("1. 执行单个需求:")
        print("   python start-agent-system.py execute 23")
        print()
        print("2. 执行需求的特定阶段:")
        print("   python start-agent-system.py execute 23 --phase phase1")
        print()
        print("3. 批量执行需求:")
        print("   python start-agent-system.py batch 23-25")
        print()
        print("4. 查看系统状态:")
        print("   python start-agent-system.py status")
        print()
        print("5. 停止系统:")
        print("   python start-agent-system.py stop")
        print()

    def execute_requirement(
        self: "AgentSystemManager",
        requirement_id: str,
        phase: str | None = None,
        agent_name: str = "coordinator",
    ) -> dict[str, Any] | None:
        """执行需求"""
        if not self.system_initialized:
            self.initialize_system()

        print(f"🎯 开始执行需求{requirement_id}")

        # 强制现有代码检查（如果配置启用）
        if self.config.get("system", {}).get("force_existing_code_check", False):
            print("🔍 执行强制现有代码检查...")
            self._force_existing_code_check(requirement_id)

        # 创建需求执行器
        executor = self.create_requirement_executor(requirement_id)
        self.active_executors[requirement_id] = executor

        if phase:
            # 执行特定阶段
            phase_map = {
                "phase1": TaskPhase.PHASE_1,
                "phase2": TaskPhase.PHASE_2,
                "phase3": TaskPhase.PHASE_3,
                "phase4": TaskPhase.PHASE_4,
                "phase5": TaskPhase.PHASE_5,
            }

            if phase in phase_map:
                # 显示阶段模板要求
                self._show_phase_template_requirements(requirement_id, phase_map[phase])

                tools = executor.execute_phase(phase_map[phase], agent_name)
                print(f"✅ 需求{requirement_id}的{phase}执行完成")
                return tools  # type: ignore[no-any-return]
            else:
                print(f"❌ 无效的阶段: {phase}")
                return None
        else:
            # 执行所有阶段
            results = {}
            for phase_enum in TaskPhase:
                phase_name = f"phase{list(TaskPhase).index(phase_enum) + 1}"
                print(f"\n📋 执行阶段: {phase_name}")

                tools = executor.execute_phase(phase_enum, agent_name)
                results[phase_name] = tools

                executor.finish_phase()

            print(f"✅ 需求{requirement_id}的所有阶段执行完成")
            return results

    def _force_existing_code_check(
        self: "AgentSystemManager", requirement_id: str
    ) -> None:
        """强制现有代码检查，防止重复开发"""
        print(f"🔍 检查需求{requirement_id}的现有实现...")

        # 加载模板系统
        agent_templates = safe_load_module(
            "agent_templates", script_dir / "agent-templates.py"
        )
        template_manager = agent_templates.AgentTemplateManager()

        # 使用现有代码检查模板
        existing_code_template = template_manager.get_template("existing_code_check")
        if existing_code_template:
            print("📋 执行现有代码检查清单:")
            for item in existing_code_template.checklist:
                print(f"  ✓ {item}")

            print("\n🎯 成功标准:")
            for criterion in existing_code_template.success_criteria:
                print(f"  ✓ {criterion}")

        # 输出关键提醒
        print("\n⚠️  关键原则:")
        print("⚠️  1. 必须使用codebase-retrieval工具全面搜索现有实现")
        print("⚠️  2. 严格按照requirements.md和design.md的要求执行")
        print("⚠️  3. 前后端必须完整实现，不允许部分实现")
        print("⚠️  4. 如发现现有功能，优化现有代码而非创建新文件")
        print("⚠️  5. 严格遵循DRY原则，避免重复开发")
        print("⚠️  6. 所有实现必须通过验收标准的逐条验证")

    def _show_phase_template_requirements(
        self: "AgentSystemManager", requirement_id: str, phase_enum: Any
    ) -> None:
        """显示阶段模板要求"""
        # 加载模板系统
        agent_templates = safe_load_module(
            "agent_templates", script_dir / "agent-templates.py"
        )
        template_manager = agent_templates.AgentTemplateManager()

        template = template_manager.get_phase_template(phase_enum)
        if template:
            print(f"\n📋 {template.name}模板要求:")
            print(f"   📝 描述: {template.description}")
            print(f"   ⏱️  预估时间: {template.estimated_hours}小时")
            print(f"   🎯 智能体角色: {template.agent_role.value}")

            print("\n   📋 检查清单:")
            for i, item in enumerate(template.checklist, 1):
                print(f"     {i}. {item}")

            print("\n   ✅ 成功标准:")
            for i, criterion in enumerate(template.success_criteria, 1):
                print(f"     {i}. {criterion}")

            print("\n   🔧 模板命令:")
            commands = template_manager.generate_agent_commands(
                requirement_id, phase_enum
            )
            for i, cmd in enumerate(commands, 1):
                print(f"     {i}. {cmd}")

            print("\n" + "=" * 80)

    def batch_execute(
        self: "AgentSystemManager", requirement_range: str
    ) -> dict[str, Any]:
        """批量执行需求"""
        if not self.system_initialized:
            self.initialize_system()

        # 解析需求范围
        if "-" in requirement_range:
            start, end = requirement_range.split("-")
            requirement_ids = [str(i) for i in range(int(start), int(end) + 1)]
        else:
            requirement_ids = requirement_range.split(",")

        print(f"🚀 批量执行需求: {', '.join(requirement_ids)}")

        results = {}
        for req_id in requirement_ids:
            try:
                result = self.execute_requirement(req_id.strip())
                results[req_id] = {"status": "success", "result": result}
            except Exception as e:
                results[req_id] = {"status": "error", "error": str(e)}
                print(f"❌ 需求{req_id}执行失败: {e}")

        return results

    def show_status(self: "AgentSystemManager") -> None:
        """显示系统状态"""
        print("📊 智能体系统状态")
        print("=" * 30)
        print(f"系统初始化: {'✅' if self.system_initialized else '❌'}")
        print(
            f"自动模板: {'✅' if self.config.get('system', {}).get('auto_template_enabled') else '❌'}"
        )
        print(f"活跃执行器: {len(self.active_executors)}")

        if hasattr(self, "registry"):
            print(f"注册智能体: {len(self.registry.registered_agents)}")

            for name, info in self.registry.registered_agents.items():
                print(f"  🤖 {name}: {info['role'].value}")

    def stop_system(self: "AgentSystemManager") -> None:
        """停止系统"""
        print("🛑 停止智能体系统...")

        # 完成所有活跃的执行器
        for req_id, executor in self.active_executors.items():
            try:
                executor.finish_phase()
                print(f"✅ 已完成需求{req_id}的执行")
            except Exception as e:
                print(f"⚠️ 需求{req_id}停止时出错: {e}")

        self.active_executors.clear()
        self.system_initialized = False

        print("✅ 智能体系统已停止")

    def generate_requirement_template(
        self: "AgentSystemManager", requirement_id: str, requirement_title: str
    ) -> None:
        """生成需求模板"""
        print(f"📋 生成需求{requirement_id}的详细模板...")

        # 加载模板系统
        agent_templates = safe_load_module(
            "agent_templates", script_dir / "agent-templates.py"
        )
        template_manager = agent_templates.AgentTemplateManager()

        # 生成详细模板
        template_content = template_manager.generate_requirement_specific_template(
            requirement_id, requirement_title
        )

        # 保存到文件
        template_file = Path(f"requirement_{requirement_id}_template.md")
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(template_content)

        print(f"✅ 模板已生成并保存到: {template_file}")
        print("📄 模板内容预览:")
        print("=" * 80)
        print(
            template_content[:1000] + "..."
            if len(template_content) > 1000
            else template_content
        )
        print("=" * 80)


def main() -> None:
    """主函数"""
    manager = AgentSystemManager()

    if len(sys.argv) < 2:
        # 默认初始化系统
        manager.initialize_system()
        return

    command = sys.argv[1].lower()

    if command == "execute":
        if len(sys.argv) < 3:
            print("❌ 请指定需求ID")
            return

        requirement_id = sys.argv[2]
        phase = None
        agent_name = "coordinator"

        # 解析可选参数
        for i in range(3, len(sys.argv)):
            if sys.argv[i] == "--phase" and i + 1 < len(sys.argv):
                phase = sys.argv[i + 1]
            elif sys.argv[i] == "--agent" and i + 1 < len(sys.argv):
                agent_name = sys.argv[i + 1]

        manager.execute_requirement(requirement_id, phase, agent_name)

    elif command == "batch":
        if len(sys.argv) < 3:
            print("❌ 请指定需求范围")
            return

        requirement_range = sys.argv[2]
        manager.batch_execute(requirement_range)

    elif command == "status":
        manager.show_status()

    elif command == "stop":
        manager.stop_system()

    elif command == "init":
        manager.initialize_system()

    elif command == "template":
        if len(sys.argv) < 4:
            print("❌ 请指定需求ID和标题")
            print("用法: python start-agent-system.py template <需求ID> <需求标题>")
            return

        requirement_id = sys.argv[2]
        requirement_title = sys.argv[3]
        manager.generate_requirement_template(requirement_id, requirement_title)

    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: execute, batch, status, stop, init, template")


if __name__ == "__main__":
    main()
