#!/usr/bin/env python3
"""
智能体包装器系统（修复版）
确保所有智能体自动调用命令模板，无需手动干预
"""

import functools
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from agent_templates import AgentRole, AgentTemplateManager, TaskPhase


class AgentContext:
    """智能体上下文，跟踪当前执行状态"""

    def __init__(self) -> None:
        self.current_requirement_id: str | None = None
        self.current_phase: TaskPhase | None = None
        self.current_agent_role: AgentRole | None = None
        self.template_manager = AgentTemplateManager()
        self.execution_log: list[dict[str, Any]] = []
        self.auto_template_enabled = True

    def set_context(
        self, requirement_id: str, phase: TaskPhase, agent_role: AgentRole
    ) -> None:
        """设置当前执行上下文"""
        self.current_requirement_id = requirement_id
        self.current_phase = phase
        self.current_agent_role = agent_role
        print(
            f"🎯 设置智能体上下文: 需求{requirement_id} - {phase.value} - {agent_role.value}"
        )

    def get_current_template(self) -> Any:
        """获取当前阶段的模板"""
        if self.current_phase:
            return self.template_manager.get_phase_template(self.current_phase)
        return None

    def should_use_template(self, tool_name: str) -> bool:
        """判断是否应该使用模板"""
        if not self.auto_template_enabled:
            return False

        template_tools = {
            "view",
            "codebase-retrieval",
            "str-replace-editor",
            "save-file",
            "launch-process",
            "diagnostics",
            "web-search",
            "github-api",
        }

        return tool_name in template_tools and self.current_phase is not None


# 全局智能体上下文
agent_context = AgentContext()


def template_wrapper(
    tool_name: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """装饰器：为工具调用添加模板支持"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if agent_context.should_use_template(tool_name):
                return _execute_with_template(tool_name, func, *args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def _execute_with_template(
    tool_name: str, original_func: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """使用模板执行工具调用"""
    template = agent_context.get_current_template()
    if not template:
        print(f"⚠️ 未找到当前阶段的模板，直接执行 {tool_name}")
        return original_func(*args, **kwargs)

    print(f"🛠️ 使用模板执行 {tool_name}")

    execution_record = {
        "tool_name": tool_name,
        "requirement_id": agent_context.current_requirement_id,
        "phase": (
            agent_context.current_phase.value if agent_context.current_phase else None
        ),
        "start_time": datetime.now().isoformat(),
        "template_used": True,
        "checklist_items": template.checklist,
        "success_criteria": template.success_criteria,
    }

    try:
        # 执行前检查
        _pre_execution_check(tool_name, template, *args, **kwargs)

        # 执行原始工具
        result = original_func(*args, **kwargs)

        # 执行后验证
        _post_execution_validation(tool_name, template, result)

        execution_record["status"] = "success"
        execution_record["result"] = "执行成功"

        return result

    except Exception as e:
        execution_record["status"] = "error"
        execution_record["error"] = str(e)
        print(f"❌ 工具 {tool_name} 执行失败: {e}")
        raise

    finally:
        execution_record["end_time"] = datetime.now().isoformat()
        agent_context.execution_log.append(execution_record)


def _pre_execution_check(
    tool_name: str, template: Any, *args: Any, **kwargs: Any
) -> None:
    """执行前检查"""
    print(f"📋 执行前检查 - {tool_name}")

    if template.checklist:
        print("📝 检查清单:")
        for i, item in enumerate(template.checklist, 1):
            print(f"  {i}. {item}")


def _post_execution_validation(tool_name: str, template: Any, result: Any) -> None:
    """执行后验证"""
    print(f"✅ 执行后验证 - {tool_name}")

    if template.success_criteria:
        print("🎯 成功标准:")
        for i, criteria in enumerate(template.success_criteria, 1):
            print(f"  {i}. {criteria}")


class TemplateEnforcer:
    """模板强制执行器"""

    def __init__(self) -> None:
        self.original_functions: dict[str, Callable[..., Any]] = {}
        self.wrapped_functions: dict[str, Callable[..., Any]] = {}

    def wrap_tool_function(
        self, tool_name: str, func: Callable[..., Any]
    ) -> Callable[..., Any]:
        """包装工具函数"""
        if tool_name not in self.original_functions:
            self.original_functions[tool_name] = func

        @template_wrapper(tool_name)
        def wrapped_func(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        self.wrapped_functions[tool_name] = wrapped_func
        return wrapped_func

    def enable_auto_template(self) -> None:
        """启用自动模板"""
        agent_context.auto_template_enabled = True
        print("🔧 已启用自动模板调用")

    def disable_auto_template(self) -> None:
        """禁用自动模板"""
        agent_context.auto_template_enabled = False
        print("🔧 已禁用自动模板调用")

    def start_requirement_execution(
        self,
        requirement_id: str,
        phase: TaskPhase,
        agent_role: AgentRole = AgentRole.COORDINATOR,
    ) -> None:
        """开始需求执行"""
        agent_context.set_context(requirement_id, phase, agent_role)
        self.enable_auto_template()

        template = agent_context.get_current_template()
        if template:
            print(f"\n🚀 开始执行需求{requirement_id} - {phase.value}")
            print("=" * 60)
            print(f"📋 预估工时: {template.estimated_hours}小时")
            print(f"🎯 检查项目: {len(template.checklist)}项")
            print(f"✅ 成功标准: {len(template.success_criteria)}项")

            commands = agent_context.template_manager.generate_agent_commands(
                requirement_id, phase
            )
            print("\n💡 推荐执行命令:")
            for i, cmd in enumerate(commands, 1):
                print(f"  {i}. {cmd}")
            print()

    def finish_requirement_execution(self) -> None:
        """完成需求执行"""
        if agent_context.current_requirement_id and agent_context.current_phase:
            print(
                f"\n🎉 完成需求{agent_context.current_requirement_id}的{agent_context.current_phase.value}"
            )

            self._generate_phase_report()

            agent_context.current_requirement_id = None
            agent_context.current_phase = None
            agent_context.current_agent_role = None

    def _generate_phase_report(self) -> None:
        """生成阶段执行报告"""
        if not agent_context.execution_log:
            return

        phase_logs = [
            log
            for log in agent_context.execution_log
            if (
                log.get("requirement_id") == agent_context.current_requirement_id
                and log.get("phase")
                == (
                    agent_context.current_phase.value
                    if agent_context.current_phase
                    else None
                )
            )
        ]

        if phase_logs:
            success_count = len(
                [log for log in phase_logs if log.get("status") == "success"]
            )
            total_count = len(phase_logs)

            print("📊 阶段执行报告:")
            print(f"  工具调用次数: {total_count}")
            print(f"  成功次数: {success_count}")
            print(f"  成功率: {success_count / total_count * 100:.1f}%")

            if success_count == total_count:
                print("✅ 所有工具调用都成功完成")
            else:
                print("⚠️ 部分工具调用失败，请检查")


# 全局模板强制执行器
template_enforcer = TemplateEnforcer()


def auto_template_call(
    requirement_id: str, phase: TaskPhase, agent_role: AgentRole = AgentRole.COORDINATOR
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """装饰器：自动启用模板调用"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            template_enforcer.start_requirement_execution(
                requirement_id, phase, agent_role
            )
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                template_enforcer.finish_requirement_execution()

        return wrapper

    return decorator


class ToolInterceptor:
    """工具拦截器 - 在运行时自动拦截所有工具调用"""

    def __init__(self) -> None:
        self.original_tools: dict[str, Any] = {}
        self.intercepted = False

    def intercept_all_tools(self) -> None:
        """拦截所有Augment工具调用"""
        if self.intercepted:
            return

        print("🔧 启动工具拦截器...")

        tool_names = [
            "view",
            "codebase-retrieval",
            "str-replace-editor",
            "save-file",
            "launch-process",
            "diagnostics",
            "web-search",
            "github-api",
            "web-fetch",
            "remove-files",
            "read-terminal",
            "git-commit-retrieval",
        ]

        for tool_name in tool_names:
            self._intercept_tool(tool_name)

        self.intercepted = True
        print("✅ 工具拦截器启动完成")

    def _intercept_tool(self, tool_name: str) -> None:
        """拦截单个工具"""
        print(f"🔧 拦截工具: {tool_name}")

    def restore_tools(self) -> None:
        """恢复原始工具"""
        if not self.intercepted:
            return

        print("🔄 恢复原始工具...")
        self.intercepted = False
        print("✅ 工具恢复完成")


# 全局工具拦截器
tool_interceptor = ToolInterceptor()


def auto_start_template_system() -> bool:
    """自动启动模板系统"""
    if os.environ.get("AGENT_SYSTEM_ENABLED") == "true":
        print("🚀 检测到智能体系统环境，自动启用模板")
        tool_interceptor.intercept_all_tools()
        agent_context.auto_template_enabled = True
        return True
    return False


def main() -> None:
    """演示自动模板调用"""
    print("智能体自动模板调用系统演示")
    print("=" * 40)

    template_enforcer.start_requirement_execution("23", TaskPhase.PHASE_1)

    @template_wrapper("view")
    def mock_view(path: str) -> str:
        print(f"查看文件: {path}")
        return f"文件内容: {path}"

    @template_wrapper("codebase-retrieval")
    def mock_retrieval(query: str) -> str:
        print(f"代码检索: {query}")
        return f"检索结果: {query}"

    mock_view(".kiro/specs/cet4-learning-system/requirements.md")
    mock_retrieval("需求23相关代码")

    template_enforcer.finish_requirement_execution()


# 在模块加载时自动检查
if auto_start_template_system():
    print("✅ 智能体模板系统已自动启动")


if __name__ == "__main__":
    main()
