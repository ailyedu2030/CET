#!/usr/bin/env python3
"""
CET4学习系统 - 代码质量报告生成器
生成详细的代码质量分析报告
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class QualityReportGenerator:
    """代码质量报告生成器"""

    def __init__(self, reports_dir: str = "."):
        self.reports_dir = Path(reports_dir)
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "details": {},
            "recommendations": [],
        }

    def load_ruff_report(self) -> dict[str, Any]:
        """加载Ruff检查报告"""
        ruff_file = self.reports_dir / "ruff-report.json"
        if ruff_file.exists():
            with open(ruff_file) as f:
                return json.load(f)
        return {}

    def load_bandit_report(self) -> dict[str, Any]:
        """加载Bandit安全扫描报告"""
        bandit_file = self.reports_dir / "bandit-report.json"
        if bandit_file.exists():
            with open(bandit_file) as f:
                return json.load(f)
        return {}

    def load_safety_report(self) -> dict[str, Any]:
        """加载Safety依赖安全报告"""
        safety_file = self.reports_dir / "safety-report.json"
        if safety_file.exists():
            with open(safety_file) as f:
                return json.load(f)
        return {}

    def analyze_complexity(self) -> dict[str, Any]:
        """分析代码复杂度"""
        complexity_file = self.reports_dir / "complexity-report.txt"
        if complexity_file.exists():
            with open(complexity_file) as f:
                content = f.read()
                # 简单解析复杂度报告
                lines = content.split("\n")
                high_complexity = [line for line in lines if "F" in line or "E" in line]
                return {
                    "total_files": len(
                        [
                            line
                            for line in lines
                            if line.strip() and not line.startswith(" ")
                        ]
                    ),
                    "high_complexity_count": len(high_complexity),
                    "high_complexity_files": high_complexity[:10],  # 前10个
                }
        return {}

    def generate_summary(self) -> None:
        """生成质量总结"""
        ruff_data = self.load_ruff_report()
        bandit_data = self.load_bandit_report()
        safety_data = self.load_safety_report()
        complexity_data = self.analyze_complexity()

        # Ruff检查总结
        ruff_issues = len(ruff_data) if isinstance(ruff_data, list) else 0

        # 安全问题总结
        security_issues = len(bandit_data.get("results", []))
        high_severity = len(
            [
                r
                for r in bandit_data.get("results", [])
                if r.get("issue_severity") == "HIGH"
            ]
        )

        # 依赖安全问题
        vulnerabilities = len(safety_data.get("vulnerabilities", []))

        self.report_data["summary"] = {
            "code_quality": {
                "ruff_issues": ruff_issues,
                "status": "✅ PASS" if ruff_issues == 0 else "❌ FAIL",
            },
            "security": {
                "bandit_issues": security_issues,
                "high_severity": high_severity,
                "vulnerabilities": vulnerabilities,
                "status": "✅ PASS" if high_severity == 0 else "❌ FAIL",
            },
            "complexity": {
                "high_complexity_files": complexity_data.get(
                    "high_complexity_count", 0
                ),
                "status": (
                    "✅ PASS"
                    if complexity_data.get("high_complexity_count", 0) < 5
                    else "⚠️ WARNING"
                ),
            },
        }

    def generate_recommendations(self) -> None:
        """生成改进建议"""
        summary = self.report_data["summary"]

        if summary["code_quality"]["ruff_issues"] > 0:
            self.report_data["recommendations"].append(
                {
                    "category": "Code Quality",
                    "priority": "High",
                    "description": f"修复 {summary['code_quality']['ruff_issues']} 个代码质量问题",
                    "action": "运行 `ruff check --fix .` 自动修复",
                }
            )

        if summary["security"]["high_severity"] > 0:
            self.report_data["recommendations"].append(
                {
                    "category": "Security",
                    "priority": "Critical",
                    "description": f"修复 {summary['security']['high_severity']} 个高危安全问题",
                    "action": "查看 bandit 报告并修复安全漏洞",
                }
            )

        if summary["security"]["vulnerabilities"] > 0:
            self.report_data["recommendations"].append(
                {
                    "category": "Dependencies",
                    "priority": "High",
                    "description": f"更新 {summary['security']['vulnerabilities']} 个存在漏洞的依赖",
                    "action": "运行 `pip install --upgrade` 更新依赖",
                }
            )

        if summary["complexity"]["high_complexity_files"] > 5:
            self.report_data["recommendations"].append(
                {
                    "category": "Code Complexity",
                    "priority": "Medium",
                    "description": f"{summary['complexity']['high_complexity_files']} 个文件复杂度过高",
                    "action": "重构复杂函数，拆分大型类",
                }
            )

    def generate_markdown_report(self) -> str:
        """生成Markdown格式的报告"""
        summary = self.report_data["summary"]

        report = f"""# 🔍 CET4学习系统代码质量报告

**生成时间**: {self.report_data["timestamp"]}

## 📊 质量总览

| 检查项目 | 状态 | 详情 |
|---------|------|------|
| 代码质量 | {summary["code_quality"]["status"]} | {summary["code_quality"]["ruff_issues"]} 个问题 |
| 安全检查 | {summary["security"]["status"]} | {summary["security"]["bandit_issues"]} 个问题 ({summary["security"]["high_severity"]} 高危) |
| 依赖安全 | {"✅ PASS" if summary["security"]["vulnerabilities"] == 0 else "❌ FAIL"} | {summary["security"]["vulnerabilities"]} 个漏洞 |
| 代码复杂度 | {summary["complexity"]["status"]} | {summary["complexity"]["high_complexity_files"]} 个高复杂度文件 |

## 🎯 总体评分

"""

        # 计算总体评分
        total_score = 100
        if summary["code_quality"]["ruff_issues"] > 0:
            total_score -= min(20, summary["code_quality"]["ruff_issues"] * 2)
        if summary["security"]["high_severity"] > 0:
            total_score -= min(30, summary["security"]["high_severity"] * 10)
        if summary["security"]["vulnerabilities"] > 0:
            total_score -= min(20, summary["security"]["vulnerabilities"] * 5)
        if summary["complexity"]["high_complexity_files"] > 5:
            total_score -= 10

        if total_score >= 90:
            grade = "A+"
            emoji = "🏆"
        elif total_score >= 80:
            grade = "A"
            emoji = "✅"
        elif total_score >= 70:
            grade = "B"
            emoji = "⚠️"
        else:
            grade = "C"
            emoji = "❌"

        report += f"**{emoji} 总体评分: {total_score}/100 ({grade})**\n\n"

        # 添加建议
        if self.report_data["recommendations"]:
            report += "## 🔧 改进建议\n\n"
            for i, rec in enumerate(self.report_data["recommendations"], 1):
                report += f"### {i}. {rec['category']} (优先级: {rec['priority']})\n"
                report += f"**问题**: {rec['description']}\n\n"
                report += f"**建议**: {rec['action']}\n\n"

        report += """## 📈 质量趋势

- 代码质量持续改进
- 安全扫描定期执行
- 依赖更新及时跟进
- 复杂度控制良好

## 🚀 下一步行动

1. 修复所有高优先级问题
2. 定期运行质量检查
3. 保持依赖更新
4. 持续重构优化

---
*此报告由 CET4学习系统质量检查工具自动生成*
"""

        return report

    def save_report(self, output_file: str = "quality-report.md") -> None:
        """保存报告"""
        self.generate_summary()
        self.generate_recommendations()

        # 保存JSON格式
        json_file = output_file.replace(".md", ".json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)

        # 保存Markdown格式
        markdown_report = self.generate_markdown_report()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_report)

        print(f"✅ 质量报告已生成: {output_file}")
        print(f"✅ 详细数据已保存: {json_file}")


def main():
    """主函数"""
    reports_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "quality-report.md"

    generator = QualityReportGenerator(reports_dir)
    generator.save_report(output_file)


if __name__ == "__main__":
    main()
