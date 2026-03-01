#!/usr/bin/env python3
"""
智能体调度器
基于命令模板自动分配和调度多个智能体执行任务
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from agent_executor import AgentExecutor
except ImportError:
    # 尝试使用带连字符的文件名
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "agent_executor", Path(__file__).parent / "agent-executor.py"
    )
    if spec is not None and spec.loader is not None:
        agent_executor_module = importlib.util.module_from_spec(spec)
        sys.modules["agent_executor"] = agent_executor_module
        spec.loader.exec_module(agent_executor_module)
        from agent_executor import AgentExecutor
    else:
        raise ImportError("无法加载 agent_executor 模块") from None

from agent_templates import AgentRole, AgentTemplateManager, TaskPhase


@dataclass
class AgentInstance:
    """智能体实例"""

    id: str
    role: AgentRole
    name: str
    status: str = "idle"  # idle, working, blocked
    current_tasks: list[str] | None = None
    max_concurrent_tasks: int = 2

    def __post_init__(self: "AgentInstance") -> None:
        if self.current_tasks is None:
            self.current_tasks = []

    @property
    def is_available(self: "AgentInstance") -> bool:
        return (
            len(self.current_tasks or []) < self.max_concurrent_tasks
            and self.status != "blocked"
        )

    @property
    def load_factor(self: "AgentInstance") -> float:
        return len(self.current_tasks or []) / self.max_concurrent_tasks


class AgentScheduler:
    """智能体调度器"""

    def __init__(self: "AgentScheduler", project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "config" / "agent-templates.json"
        self.template_manager = AgentTemplateManager()
        self.priority_queue: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: [], 5: []}
        self.executor = AgentExecutor(project_root)

        # 加载配置
        self.config = self._load_config()

        # 初始化智能体实例
        self.agent_instances: dict[str, AgentInstance] = {}
        self._initialize_agent_instances()

        # 任务队列
        self.task_queue: list[dict[str, Any]] = []
        self.completed_tasks: list[dict[str, Any]] = []
        self.failed_tasks: list[dict[str, Any]] = []

    def _load_config(self: "AgentScheduler") -> dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]
        return {}

    def _initialize_agent_instances(self: "AgentScheduler") -> None:
        """初始化智能体实例"""
        agent_roles_config = self.config.get("agent_roles", {})

        for role_name, role_config in agent_roles_config.items():
            try:
                role = AgentRole(role_name.lower())
                max_tasks = role_config.get("max_concurrent_tasks", 2)

                # 为每个角色创建实例
                instance_id = f"{role_name.lower()}_1"
                instance = AgentInstance(
                    id=instance_id,
                    role=role,
                    name=role_config["name"],
                    max_concurrent_tasks=max_tasks,
                )
                self.agent_instances[instance_id] = instance

            except ValueError:
                print(f"⚠️ 未知的智能体角色: {role_name}")

    def add_requirement_to_queue(
        self: "AgentScheduler",
        requirement_id: str,
        requirement_title: str,
        priority: int = 1,
    ) -> None:
        """添加需求到任务队列"""
        # 为需求的每个阶段创建任务
        for phase in TaskPhase:
            task = {
                "id": f"req_{requirement_id}_phase_{list(TaskPhase).index(phase) + 1}",
                "requirement_id": requirement_id,
                "requirement_title": requirement_title,
                "phase": phase,
                "priority": priority,
                "status": "queued",
                "assigned_agent": None,
                "created_time": datetime.now().isoformat(),
                "dependencies": self._get_task_dependencies(requirement_id, phase),
            }
            self.task_queue.append(task)

        print(f"📋 已添加需求{requirement_id}的5个阶段任务到队列")

    def _get_task_dependencies(
        self: "AgentScheduler", requirement_id: str, phase: TaskPhase
    ) -> list[str]:
        """获取任务依赖关系"""
        dependencies = []

        # 同一需求内的阶段依赖
        current_phase_index = list(TaskPhase).index(phase)
        if current_phase_index > 0:
            prev_phase_index = current_phase_index - 1
            prev_task_id = f"req_{requirement_id}_phase_{prev_phase_index + 1}"
            dependencies.append(prev_task_id)

        # 跨需求的依赖关系（基于需求文档中的依赖）
        requirement_dependencies = {
            "24": ["23"],  # 需求24依赖需求23
            "25": ["23", "24"],  # 需求25依赖需求23和24
            "30": ["24"],  # 需求30依赖需求24
            # 可以根据需要添加更多依赖关系
        }

        if requirement_id in requirement_dependencies:
            for dep_req in requirement_dependencies[requirement_id]:
                # 只有当依赖需求的相同阶段完成后，当前任务才能开始
                dep_task_id = f"req_{dep_req}_phase_{current_phase_index + 1}"
                dependencies.append(dep_task_id)

        return dependencies

    def assign_task_to_agent(
        self: "AgentScheduler", task: dict[str, Any]
    ) -> str | None:
        """将任务分配给最合适的智能体"""
        # 获取任务的阶段模板
        template = self.template_manager.get_phase_template(task["phase"])
        if not template:
            return None

        # 查找可用的智能体实例
        available_agents = [
            agent
            for agent in self.agent_instances.values()
            if agent.is_available and agent.role == template.agent_role
        ]

        if not available_agents:
            return None

        # 选择负载最低的智能体
        best_agent = min(available_agents, key=lambda x: x.load_factor)

        # 分配任务
        task["assigned_agent"] = best_agent.id
        task["status"] = "assigned"
        if best_agent.current_tasks is None:
            best_agent.current_tasks = []
        best_agent.current_tasks.append(task["id"])
        best_agent.status = "working"

        print(f"📋 任务 {task['id']} 分配给 {best_agent.name}")
        return best_agent.id

    def can_execute_task(self: "AgentScheduler", task: dict[str, Any]) -> bool:
        """检查任务是否可以执行（依赖是否满足）"""
        for dep_task_id in task["dependencies"]:
            # 检查依赖任务是否已完成
            dep_completed = any(
                t["id"] == dep_task_id and t["status"] == "completed"
                for t in self.completed_tasks
            )
            if not dep_completed:
                return False
        return True

    def execute_next_tasks(self: "AgentScheduler") -> list[dict[str, Any]]:
        """执行下一批可执行的任务"""
        executed_tasks = []

        # 找到所有可执行的任务
        executable_tasks = [
            task
            for task in self.task_queue
            if task["status"] == "queued" and self.can_execute_task(task)
        ]

        # 按优先级排序
        executable_tasks.sort(key=lambda x: x["priority"], reverse=True)

        for task in executable_tasks:
            # 尝试分配智能体
            agent_id = self.assign_task_to_agent(task)
            if agent_id:
                # 执行任务
                result = self.executor.execute_phase(
                    task["requirement_id"], task["phase"]
                )

                # 更新任务状态
                task["execution_result"] = result
                task["end_time"] = datetime.now().isoformat()

                if result.get("status") == "completed":
                    task["status"] = "completed"
                    self.completed_tasks.append(task)
                    print(f"✅ 任务 {task['id']} 执行成功")
                else:
                    task["status"] = "failed"
                    self.failed_tasks.append(task)
                    print(f"❌ 任务 {task['id']} 执行失败")

                # 从队列中移除
                self.task_queue.remove(task)

                # 释放智能体
                agent = self.agent_instances[agent_id]
                if (
                    agent.current_tasks is not None
                    and task["id"] in agent.current_tasks
                ):
                    agent.current_tasks.remove(task["id"])
                if not (agent.current_tasks or []):
                    agent.status = "idle"

                executed_tasks.append(task)

        return executed_tasks

    def run_scheduler(
        self: "AgentScheduler", max_iterations: int = 100
    ) -> dict[str, Any]:
        """运行调度器直到所有任务完成"""
        print("\n🚀 启动智能体调度器")
        print(f"📊 队列中有 {len(self.task_queue)} 个任务")
        print("=" * 60)

        iteration = 0
        while self.task_queue and iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 第 {iteration} 轮调度")

            executed_tasks = self.execute_next_tasks()

            if not executed_tasks:
                print("⏸️ 没有可执行的任务，等待依赖完成...")
                break

            print(f"📊 本轮执行了 {len(executed_tasks)} 个任务")
            print(f"📊 剩余队列: {len(self.task_queue)} 个任务")

        # 生成最终报告
        result = {
            "total_tasks": len(self.completed_tasks)
            + len(self.failed_tasks)
            + len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "pending_tasks": len(self.task_queue),
            "iterations": iteration,
            "success_rate": (
                len(self.completed_tasks)
                / (len(self.completed_tasks) + len(self.failed_tasks))
                * 100
                if (len(self.completed_tasks) + len(self.failed_tasks)) > 0
                else 0
            ),
        }

        print("\n📊 调度完成统计:")
        print(f"  总任务数: {result['total_tasks']}")
        print(f"  已完成: {result['completed_tasks']}")
        print(f"  失败: {result['failed_tasks']}")
        print(f"  待处理: {result['pending_tasks']}")
        print(f"  成功率: {result['success_rate']:.1f}%")

        return result

    def schedule_by_priority(
        self: "AgentScheduler", priority_level: int = 1
    ) -> dict[str, Any]:
        """基于优先级调度任务执行"""
        print(f"\n🎯 开始执行第{priority_level}优先级任务")
        print("=" * 50)

        # 获取指定优先级的模板
        priority_templates = self.template_manager.get_priority_templates(
            priority_level
        )

        if not priority_templates:
            print(f"⚠️ 未找到第{priority_level}优先级的任务模板")
            return {"success": False, "message": "No templates found"}

        # 为每个模板创建任务
        scheduled_tasks = []
        for template in priority_templates:
            task_id = f"priority{priority_level}_{template.name.split('：')[1] if '：' in template.name else template.name}"

            # 添加到任务队列
            task = {
                "id": task_id,
                "template_name": template.name,
                "description": template.description,
                "agent_role": template.agent_role,
                "commands": template.commands,
                "checklist": template.checklist,
                "success_criteria": template.success_criteria,
                "estimated_hours": template.estimated_hours,
                "priority": priority_level,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }

            self.task_queue.append(task)
            scheduled_tasks.append(task_id)
            print(f"✅ 已添加任务: {template.name} (预估{template.estimated_hours}小时)")

        print(f"\n📋 第{priority_level}优先级任务调度完成:")
        print(f"  添加任务数: {len(scheduled_tasks)}")
        print(f"  预估总工时: {sum(t.estimated_hours for t in priority_templates)}小时")

        # 执行调度
        return self.run_scheduler()

    def schedule_all_priorities(self: "AgentScheduler") -> dict[str, Any]:
        """按优先级顺序执行所有任务"""
        print("\n🚀 开始按优先级执行所有任务")
        print("=" * 50)

        total_results: dict[str, Any] = {
            "priorities": {},
            "total_tasks": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_hours": 0,
        }

        # 按优先级顺序执行
        for priority in [1, 2, 3, 4, 5]:
            print(f"\n🎯 执行第{priority}优先级任务...")

            # 清空当前队列
            self.task_queue = []
            self.completed_tasks = []
            self.failed_tasks = []

            # 调度当前优先级任务
            result = self.schedule_by_priority(priority)

            # 记录结果
            total_results["priorities"][priority] = result
            total_results["total_tasks"] += result.get("total_tasks", 0)
            total_results["total_completed"] += result.get("completed_tasks", 0)
            total_results["total_failed"] += result.get("failed_tasks", 0)

            # 计算工时
            priority_templates = self.template_manager.get_priority_templates(priority)
            priority_hours = sum(t.estimated_hours for t in priority_templates)
            total_results["total_hours"] += priority_hours

            print(f"✅ 第{priority}优先级完成 - 成功率: {result.get('success_rate', 0):.1f}%")

        # 计算总体成功率
        total_results["overall_success_rate"] = (
            total_results["total_completed"]
            / (total_results["total_completed"] + total_results["total_failed"])
            * 100
            if (total_results["total_completed"] + total_results["total_failed"]) > 0
            else 0
        )

        print("\n🎉 所有优先级任务执行完成!")
        print(f"  总任务数: {total_results['total_tasks']}")
        print(f"  总完成数: {total_results['total_completed']}")
        print(f"  总失败数: {total_results['total_failed']}")
        print(f"  总工时: {total_results['total_hours']}小时")
        print(f"  总体成功率: {total_results['overall_success_rate']:.1f}%")

        return total_results

    def show_agent_status(self: "AgentScheduler") -> None:
        """显示所有智能体状态"""
        print("\n🤖 智能体状态:")
        print("=" * 40)

        for agent in self.agent_instances.values():
            load_percent = agent.load_factor * 100
            status_icon = (
                "🟢"
                if agent.status == "idle"
                else "🔄"
                if agent.status == "working"
                else "🔴"
            )

            print(f"{status_icon} {agent.name}")
            current_task_count = len(agent.current_tasks or [])
            print(
                f"  负载: {current_task_count}/{agent.max_concurrent_tasks} ({load_percent:.0f}%)"
            )
            print(f"  状态: {agent.status}")

            if agent.current_tasks:
                print(f"  当前任务: {', '.join(agent.current_tasks)}")


def main() -> None:
    """主函数"""
    if len(sys.argv) < 2:
        print("智能体调度器 - 基于TODO优先级的任务调度系统")
        print("=" * 60)
        print("用法:")
        print("  python agent-scheduler.py <模式> [参数]")
        print("")
        print("模式:")
        print("  priority <级别>     - 执行指定优先级任务 (1-5)")
        print("  all                 - 按优先级顺序执行所有任务")
        print("  requirements <ID>   - 执行指定需求ID (传统模式)")
        print("")
        print("示例:")
        print("  python agent-scheduler.py priority 1")
        print("  python agent-scheduler.py all")
        print("  python agent-scheduler.py requirements 23,24,25")
        return

    mode = sys.argv[1].lower()
    scheduler = AgentScheduler()

    if mode == "priority":
        # 优先级模式
        if len(sys.argv) < 3:
            print("❌ 请指定优先级级别 (1-5)")
            return

        try:
            priority_level = int(sys.argv[2])
            if priority_level not in [1, 2, 3, 4, 5]:
                print("❌ 优先级级别必须是 1-5")
                return
        except ValueError:
            print("❌ 优先级级别必须是数字")
            return

        print(f"🎯 执行第{priority_level}优先级任务")
        scheduler.show_agent_status()
        result = scheduler.schedule_by_priority(priority_level)
        scheduler.show_agent_status()
        print(f"\n🎉 第{priority_level}优先级任务完成！成功率: {result.get('success_rate', 0):.1f}%")

    elif mode == "all":
        # 全部优先级模式
        print("🚀 按优先级顺序执行所有任务")
        scheduler.show_agent_status()
        result = scheduler.schedule_all_priorities()
        scheduler.show_agent_status()
        print(f"\n🎉 所有任务完成！总体成功率: {result.get('overall_success_rate', 0):.1f}%")

    elif mode == "requirements":
        # 传统需求ID模式
        if len(sys.argv) < 3:
            print("❌ 请指定需求ID")
            return

        requirement_arg = sys.argv[2]
        requirement_ids = []

        if "-" in requirement_arg:
            # 范围格式：23-25
            start, end = requirement_arg.split("-")
            requirement_ids = [str(i) for i in range(int(start), int(end) + 1)]
        else:
            # 列表格式：23,24,25
            requirement_ids = requirement_arg.split(",")

        # 添加需求到队列
        for req_id in requirement_ids:
            scheduler.add_requirement_to_queue(req_id.strip(), f"需求{req_id.strip()}")

        # 显示智能体状态
        scheduler.show_agent_status()

        # 运行调度器
        result = scheduler.run_scheduler()

        # 显示最终状态
        scheduler.show_agent_status()

        print(f"\n🎉 需求调度完成！成功率: {result.get('success_rate', 0):.1f}%")

    else:
        print(f"❌ 未知模式: {mode}")
        print("支持的模式: priority, all, requirements")


if __name__ == "__main__":
    main()
