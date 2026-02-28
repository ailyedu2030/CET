#!/usr/bin/env python3
"""
智能体注册系统
自动注册所有智能体并强制使用模板系统
"""

import inspect
from collections.abc import Callable
from typing import Any

from agent_templates import AgentRole, TaskPhase
from agent_wrapper import template_enforcer, template_wrapper


class AgentRegistry:
    """智能体注册中心"""

    def __init__(self) -> None:
        self.registered_agents: dict[str, Any] = {}
        self.tool_mappings: dict[str, Any] = {}
        self.auto_wrap_enabled = True

        # 定义需要自动包装的工具函数
        self.auto_wrap_tools = {
            "view": "view",
            "codebase-retrieval": "codebase_retrieval",
            "str-replace-editor": "str_replace_editor",
            "save-file": "save_file",
            "launch-process": "launch_process",
            "diagnostics": "diagnostics",
            "web-search": "web_search",
            "github-api": "github_api",
            "web-fetch": "web_fetch",
            "remove-files": "remove_files",
            "read-terminal": "read_terminal",
            "git-commit-retrieval": "git_commit_retrieval",
        }

    def register_agent(
        self, agent_name: str, agent_role: AgentRole, tools: list[str] | None = None
    ) -> None:
        """注册智能体"""
        if tools is None:
            tools = list(self.auto_wrap_tools.keys())

        agent_info = {
            "name": agent_name,
            "role": agent_role,
            "tools": tools,
            "wrapped_tools": {},
            "registered_at": None,
        }

        self.registered_agents[agent_name] = agent_info
        print(f"📝 已注册智能体: {agent_name} ({agent_role.value})")

        # 自动包装工具
        if self.auto_wrap_enabled:
            self._wrap_agent_tools(agent_name)

    def _wrap_agent_tools(self, agent_name: str) -> None:
        """为智能体包装工具"""
        agent_info = self.registered_agents[agent_name]

        for tool_name in agent_info["tools"]:
            if tool_name in self.auto_wrap_tools:
                # 创建包装后的工具函数
                wrapped_tool = self._create_wrapped_tool(tool_name, agent_name)
                agent_info["wrapped_tools"][tool_name] = wrapped_tool

                print(f"🔧 已为 {agent_name} 包装工具: {tool_name}")

    def _create_wrapped_tool(
        self, tool_name: str, agent_name: str
    ) -> Callable[..., Any]:
        """创建包装后的工具函数"""

        @template_wrapper(tool_name)
        def wrapped_tool(*args: Any, **kwargs: Any) -> Any:
            print(f"🤖 {agent_name} 调用工具: {tool_name}")

            # 这里应该调用真实的工具函数
            # 在实际环境中，这会是对Augment工具的真实调用
            return self._simulate_tool_call(tool_name, *args, **kwargs)

        return wrapped_tool  # type: ignore[no-any-return]

    def _simulate_tool_call(self, tool_name: str, *args: Any, **kwargs: Any) -> str:
        """模拟工具调用（在实际环境中替换为真实调用）"""
        print(f"  📞 模拟调用 {tool_name} with args={args}, kwargs={kwargs}")
        return f"模拟结果: {tool_name} 执行完成"

    def get_agent_tool(
        self, agent_name: str, tool_name: str
    ) -> Callable[..., Any] | None:
        """获取智能体的包装工具"""
        if agent_name in self.registered_agents:
            return self.registered_agents[agent_name]["wrapped_tools"].get(tool_name)  # type: ignore[no-any-return]
        return None

    def execute_requirement_with_agent(
        self, agent_name: str, requirement_id: str, phase: TaskPhase
    ) -> dict[str, Any]:
        """使用指定智能体执行需求"""
        if agent_name not in self.registered_agents:
            raise ValueError(f"智能体 {agent_name} 未注册")

        agent_info = self.registered_agents[agent_name]
        agent_role = agent_info["role"]

        # 启动模板执行
        template_enforcer.start_requirement_execution(requirement_id, phase, agent_role)

        print(f"\n🚀 {agent_name} 开始执行需求{requirement_id}的{phase.value}")

        # 返回智能体的工具集合，供后续使用
        return agent_info["wrapped_tools"]  # type: ignore[no-any-return]

    def create_agent_function(
        self, agent_name: str, requirement_id: str, phase: TaskPhase
    ) -> Callable[[], dict[str, Any]]:
        """创建智能体执行函数"""

        def agent_execution_function() -> dict[str, Any]:
            """智能体执行函数"""
            tools = self.execute_requirement_with_agent(
                agent_name, requirement_id, phase
            )

            # 这里可以添加具体的执行逻辑
            # 智能体会自动使用包装后的工具

            return tools

        return agent_execution_function

    def list_registered_agents(self) -> None:
        """列出所有注册的智能体"""
        print("\n🤖 已注册的智能体:")
        print("=" * 40)

        for agent_name, agent_info in self.registered_agents.items():
            print(f"📋 {agent_name}")
            print(f"  角色: {agent_info['role'].value}")
            print(f"  工具数: {len(agent_info['tools'])}")
            print(f"  已包装: {len(agent_info['wrapped_tools'])}")
            print()


# 全局智能体注册中心
agent_registry = AgentRegistry()


def register_agent_auto(
    agent_name: str, agent_role: AgentRole, tools: list[str] | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """自动注册智能体的装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # 注册智能体
        agent_registry.register_agent(agent_name, agent_role, tools)

        # 返回原函数（可以添加额外的包装逻辑）
        return func

    return decorator


def ensure_template_usage() -> None:
    """确保模板使用的全局函数"""

    # 检查当前模块中是否有工具调用
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_locals = frame.f_back.f_locals
        caller_globals = frame.f_back.f_globals

        # 检查是否在智能体上下文中
        if hasattr(template_enforcer, "agent_context"):
            if not template_enforcer.agent_context.auto_template_enabled:
                print("⚠️ 检测到工具调用但模板未启用，自动启用模板")
                template_enforcer.enable_auto_template()


def init_agent_system() -> AgentRegistry:
    """初始化智能体系统"""
    print("🔧 初始化智能体系统...")

    # 注册默认智能体
    agent_registry.register_agent("coordinator", AgentRole.COORDINATOR)
    agent_registry.register_agent("backend_agent", AgentRole.BACKEND)
    agent_registry.register_agent("frontend_agent", AgentRole.FRONTEND)
    agent_registry.register_agent("devops_agent", AgentRole.DEVOPS)
    agent_registry.register_agent("qa_agent", AgentRole.QA)

    print("✅ 智能体系统初始化完成")

    return agent_registry


def create_requirement_executor(requirement_id: str) -> Any:
    """创建需求执行器"""

    class RequirementExecutor:
        def __init__(self, req_id: str) -> None:
            self.requirement_id = req_id
            self.current_phase: TaskPhase | None = None
            self.current_agent: str | None = None

        def execute_phase(
            self, phase: TaskPhase, agent_name: str = "coordinator"
        ) -> dict[str, Any]:
            """执行指定阶段"""
            self.current_phase = phase
            self.current_agent = agent_name

            # 获取智能体工具
            tools = agent_registry.execute_requirement_with_agent(
                agent_name, self.requirement_id, phase
            )

            return tools

        def finish_phase(self) -> None:
            """完成当前阶段"""
            if self.current_phase:
                template_enforcer.finish_requirement_execution()
                print(
                    f"✅ 需求{self.requirement_id}的{self.current_phase.value}执行完成"
                )
                self.current_phase = None
                self.current_agent = None

    return RequirementExecutor(requirement_id)


def main() -> None:
    """演示智能体注册系统"""
    print("智能体注册系统演示")
    print("=" * 30)

    # 初始化系统
    registry = init_agent_system()

    # 列出注册的智能体
    registry.list_registered_agents()

    # 创建需求执行器
    executor = create_requirement_executor("23")

    # 执行阶段1
    tools = executor.execute_phase(TaskPhase.PHASE_1, "coordinator")

    # 模拟使用工具
    if "view" in tools:
        tools["view"](".kiro/specs/cet4-learning-system/requirements.md")

    if "codebase-retrieval" in tools:
        tools["codebase-retrieval"]("需求23相关代码")

    # 完成阶段
    executor.finish_phase()


if __name__ == "__main__":
    main()
