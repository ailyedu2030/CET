#!/usr/bin/env python3
"""
智能体执行器
基于命令模板执行标准化的智能体任务
"""

# 导入模板管理器
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 动态导入agent-templates模块
spec = importlib.util.spec_from_file_location(
    "agent_templates", Path(__file__).parent / "agent-templates.py"
)
if spec is not None and spec.loader is not None:
    agent_templates_module = importlib.util.module_from_spec(spec)
    sys.modules["agent_templates"] = agent_templates_module
    spec.loader.exec_module(agent_templates_module)
    from agent_templates import AgentRole, AgentTemplateManager, TaskPhase
else:
    raise ImportError("无法加载 agent_templates 模块")


class AgentExecutor:
    """智能体执行器"""

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.todo_file = self.project_root / "todo"
        self.template_manager = AgentTemplateManager()
        self.execution_log: list[dict[str, Any]] = []

    def execute_phase(
        self, requirement_id: str, phase: TaskPhase, agent_role: AgentRole = AgentRole.COORDINATOR
    ) -> dict[str, Any]:
        """执行指定阶段的任务"""
        print(f"\n🚀 开始执行需求{requirement_id}的{phase.value}")
        print("=" * 60)

        # 获取模板
        template = self.template_manager.get_phase_template(phase)
        if not template:
            return {"success": False, "error": f"未找到{phase.value}的模板"}

        # 生成命令
        commands = self.template_manager.generate_agent_commands(requirement_id, phase)
        checklist = self.template_manager.generate_checklist(phase)
        success_criteria = self.template_manager.generate_success_criteria(phase)

        execution_result = {
            "requirement_id": requirement_id,
            "phase": phase.value,
            "agent_role": agent_role.value,
            "start_time": datetime.now().isoformat(),
            "commands": commands,
            "checklist": checklist,
            "success_criteria": success_criteria,
            "status": "in_progress",
            "results": [],
        }

        print(f"📋 检查清单 ({len(checklist)}项):")
        for i, item in enumerate(checklist, 1):
            print(f"  {i}. {item}")

        print(f"\n🎯 成功标准 ({len(success_criteria)}项):")
        for i, criteria in enumerate(success_criteria, 1):
            print(f"  {i}. {criteria}")

        print(f"\n⚡ 执行命令 ({len(commands)}个):")
        for i, cmd in enumerate(commands, 1):
            print(f"  {i}. {cmd}")

            # 这里是实际执行命令的地方
            # 在真实环境中，这里会调用相应的工具和API
            result = self._simulate_command_execution(cmd, requirement_id)
            execution_result["results"].append(result)

            if result["success"]:
                print(f"     ✅ 成功: {result['message']}")
            else:
                print(f"     ❌ 失败: {result['error']}")

        # 更新执行状态
        execution_result["end_time"] = datetime.now().isoformat()
        execution_result["status"] = (
            "completed" if all(r["success"] for r in execution_result["results"]) else "failed"
        )

        # 记录执行日志
        self.execution_log.append(execution_result)

        print(f"\n📊 阶段执行结果: {execution_result['status']}")
        print(f"⏱️ 预估时间: {template.estimated_hours}小时")

        return execution_result

    def _simulate_command_execution(self, command: str, requirement_id: str) -> dict[str, Any]:
        """模拟命令执行（在实际环境中替换为真实的工具调用）"""
        # 这里模拟不同命令的执行结果
        if "view" in command:
            return {
                "success": True,
                "message": f"成功查看文档: {command}",
                "data": f"模拟文档内容 for 需求{requirement_id}",
            }
        elif "search" in command:
            return {
                "success": True,
                "message": f"成功搜索: {command}",
                "data": f"找到需求{requirement_id}的相关信息",
            }
        elif "check" in command:
            return {
                "success": True,
                "message": f"检查完成: {command}",
                "data": f"需求{requirement_id}无冲突",
            }
        elif "confirm" in command:
            return {
                "success": True,
                "message": f"确认完成: {command}",
                "data": f"需求{requirement_id}实施方案已确认",
            }
        elif "assess" in command:
            return {
                "success": True,
                "message": f"评估完成: {command}",
                "data": f"需求{requirement_id}现状评估结果",
            }
        elif "implement" in command:
            return {
                "success": True,
                "message": f"实现完成: {command}",
                "data": f"需求{requirement_id}代码实现完成",
            }
        else:
            return {
                "success": True,
                "message": f"命令执行完成: {command}",
                "data": f"需求{requirement_id}处理结果",
            }

    def execute_full_requirement(
        self, requirement_id: str, requirement_title: str
    ) -> dict[str, Any]:
        """执行完整需求的所有5个阶段"""
        print(f"\n🎯 开始执行需求{requirement_id}：{requirement_title}")
        print("=" * 80)

        full_result: dict[str, Any] = {
            "requirement_id": requirement_id,
            "requirement_title": requirement_title,
            "start_time": datetime.now().isoformat(),
            "phases": [],
            "total_estimated_hours": 0,
            "status": "in_progress",
        }

        # 执行所有5个阶段
        for phase in TaskPhase:
            phase_result = self.execute_phase(requirement_id, phase)
            full_result["phases"].append(phase_result)

            template = self.template_manager.get_phase_template(phase)
            if template:
                full_result["total_estimated_hours"] += template.estimated_hours

            # 如果某个阶段失败，停止执行
            if phase_result.get("status") != "completed":
                full_result["status"] = "failed"
                print(f"\n❌ 需求{requirement_id}执行失败，停止在{phase.value}")
                break
        else:
            full_result["status"] = "completed"
            print(f"\n✅ 需求{requirement_id}全部阶段执行完成")

        full_result["end_time"] = datetime.now().isoformat()

        # 更新todo文件
        self._update_todo_file(requirement_id, full_result["status"])

        return full_result

    def _update_todo_file(self, requirement_id: str, status: str) -> None:
        """更新todo文件中的任务状态"""
        if not self.todo_file.exists():
            return

        try:
            content = self.todo_file.read_text(encoding="utf-8")

            # 查找需求对应的任务
            pattern = rf"### [^#]*需求\s*{requirement_id}[：:]([^\n]*)"

            if status == "completed":
                # 将所有子任务标记为完成
                content = content.replace("- [ ]", "- [x]")
                print(f"📝 已更新todo文件：需求{requirement_id}标记为完成")
            elif status == "failed":
                # 将当前任务标记为阻塞
                content = content.replace("- [ ]", "- [!]")
                print(f"📝 已更新todo文件：需求{requirement_id}标记为阻塞")

            self.todo_file.write_text(content, encoding="utf-8")

        except Exception as e:
            print(f"❌ 更新todo文件失败: {e}")

    def generate_execution_report(self) -> str:
        """生成执行报告"""
        if not self.execution_log:
            return "暂无执行记录"

        report = f"""
# 智能体执行报告

## 📊 执行统计
- 总执行次数: {len(self.execution_log)}
- 成功次数: {len([log for log in self.execution_log if log["status"] == "completed"])}
- 失败次数: {len([log for log in self.execution_log if log["status"] == "failed"])}

## 📋 执行详情
"""

        for log in self.execution_log:
            report += f"""
### 需求{log["requirement_id"]} - {log["phase"]}
- 状态: {log["status"]}
- 开始时间: {log["start_time"]}
- 结束时间: {log.get("end_time", "未完成")}
- 命令数: {len(log["commands"])}
- 成功率: {len([r for r in log["results"] if r["success"]]) / len(log["results"]) * 100:.1f}%
"""

        return report

    def save_execution_log(self, filename: str = "agent_execution_log.json") -> None:
        """保存执行日志"""
        log_file = self.project_root / filename
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.execution_log, f, indent=2, ensure_ascii=False)
        print(f"📄 执行日志已保存: {log_file}")


def main() -> None:
    """主函数 - 演示智能体执行器使用"""
    if len(sys.argv) < 2:
        print("智能体执行器")
        print("=" * 30)
        print("用法:")
        print("  python agent-executor.py <需求ID> [阶段]")
        print("  python agent-executor.py 23          # 执行需求23的所有阶段")
        print("  python agent-executor.py 23 phase1   # 只执行需求23的阶段1")
        print("\n可用阶段:")
        for phase in TaskPhase:
            print(f"  - phase{list(TaskPhase).index(phase) + 1}: {phase.value}")
        return

    requirement_id = sys.argv[1]
    phase_arg = sys.argv[2] if len(sys.argv) > 2 else None

    executor = AgentExecutor()

    if phase_arg:
        # 执行单个阶段
        phase_map = {
            "phase1": TaskPhase.PHASE_1,
            "phase2": TaskPhase.PHASE_2,
            "phase3": TaskPhase.PHASE_3,
            "phase4": TaskPhase.PHASE_4,
            "phase5": TaskPhase.PHASE_5,
        }

        if phase_arg in phase_map:
            result = executor.execute_phase(requirement_id, phase_map[phase_arg])
            print(f"\n📊 执行结果: {result['status']}")
        else:
            print(f"❌ 无效的阶段: {phase_arg}")
    else:
        # 执行完整需求
        result = executor.execute_full_requirement(requirement_id, f"需求{requirement_id}")
        print(f"\n📊 总体结果: {result['status']}")
        print(f"⏱️ 总预估时间: {result['total_estimated_hours']}小时")

    # 生成报告
    report = executor.generate_execution_report()
    print(report)

    # 保存日志
    executor.save_execution_log()


if __name__ == "__main__":
    main()
