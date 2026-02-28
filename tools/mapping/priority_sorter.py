#!/usr/bin/env python3
"""
修复优先级排序器
基于问题严重程度、影响范围和业务重要性对API修复任务进行优先级排序
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class IssueSeverity(Enum):
    """问题严重程度"""

    CRITICAL = "critical"  # 阻塞性问题
    HIGH = "high"  # 严重问题
    MEDIUM = "medium"  # 中等问题
    LOW = "low"  # 轻微问题


class ImpactScope(Enum):
    """影响范围"""

    SYSTEM_WIDE = "system_wide"  # 系统级影响
    MODULE_WIDE = "module_wide"  # 模块级影响
    FEATURE_SPECIFIC = "feature_specific"  # 功能级影响
    MINOR = "minor"  # 局部影响


class BusinessPriority(Enum):
    """业务优先级"""

    CORE_BUSINESS = "core_business"  # 核心业务
    IMPORTANT_FEATURE = "important_feature"  # 重要功能
    NICE_TO_HAVE = "nice_to_have"  # 锦上添花
    OPTIMIZATION = "optimization"  # 优化项


@dataclass
class IssueAnalysis:
    """问题分析结果"""

    issue_type: str
    description: str
    severity: IssueSeverity
    impact_scope: ImpactScope
    business_priority: BusinessPriority
    affected_apis: list[str]
    affected_requirements: list[str]
    estimated_fix_time: int  # 小时
    dependencies: list[str]
    risk_level: str


@dataclass
class FixTask:
    """修复任务"""

    task_id: str
    title: str
    description: str
    issues: list[IssueAnalysis]
    priority_score: float
    estimated_time: int
    dependencies: list[str]
    affected_requirements: list[str]
    fix_order: int


class PrioritySorter:
    """优先级排序器"""

    def __init__(self) -> None:
        self.issue_patterns = self._load_issue_patterns()
        self.business_weights = self._load_business_weights()

    def _load_issue_patterns(self) -> dict[str, dict[str, Any]]:
        """加载问题识别模式"""
        return {
            # 服务器错误模式
            "server_error": {
                "patterns": [
                    r"500.*Internal Server Error",
                    r"502.*Bad Gateway",
                    r"503.*Service Unavailable",
                ],
                "severity": IssueSeverity.CRITICAL,
                "impact_scope": ImpactScope.SYSTEM_WIDE,
                "keywords": ["服务器错误", "内部错误", "服务不可用"],
            },
            # 模块缺失模式
            "module_missing": {
                "patterns": [
                    r"ModuleNotFoundError",
                    r"No module named",
                    r"ImportError",
                ],
                "severity": IssueSeverity.CRITICAL,
                "impact_scope": ImpactScope.MODULE_WIDE,
                "keywords": ["模块缺失", "导入错误", "依赖缺失"],
            },
            # 认证问题模式
            "authentication_error": {
                "patterns": [
                    r"403.*Forbidden",
                    r"401.*Unauthorized",
                    r"Authentication.*failed",
                ],
                "severity": IssueSeverity.HIGH,
                "impact_scope": ImpactScope.FEATURE_SPECIFIC,
                "keywords": ["认证失败", "权限不足", "未授权"],
            },
            # API不存在模式
            "api_not_found": {
                "patterns": [r"404.*Not Found", r"Endpoint.*not found"],
                "severity": IssueSeverity.HIGH,
                "impact_scope": ImpactScope.FEATURE_SPECIFIC,
                "keywords": ["端点不存在", "路由未找到", "API缺失"],
            },
            # HTTP方法错误模式
            "method_not_allowed": {
                "patterns": [r"405.*Method Not Allowed"],
                "severity": IssueSeverity.MEDIUM,
                "impact_scope": ImpactScope.FEATURE_SPECIFIC,
                "keywords": ["方法不允许", "HTTP方法错误"],
            },
            # 参数验证错误模式
            "validation_error": {
                "patterns": [r"422.*Unprocessable Entity", r"Validation.*error"],
                "severity": IssueSeverity.MEDIUM,
                "impact_scope": ImpactScope.FEATURE_SPECIFIC,
                "keywords": ["参数验证失败", "数据格式错误"],
            },
            # 性能问题模式
            "performance_issue": {
                "patterns": [r"timeout", r"slow.*response", r"high.*latency"],
                "severity": IssueSeverity.MEDIUM,
                "impact_scope": ImpactScope.FEATURE_SPECIFIC,
                "keywords": ["响应超时", "性能缓慢", "延迟过高"],
            },
            # 连接问题模式
            "connection_error": {
                "patterns": [
                    r"Connection.*refused",
                    r"Connection.*timeout",
                    r"Network.*error",
                ],
                "severity": IssueSeverity.HIGH,
                "impact_scope": ImpactScope.MODULE_WIDE,
                "keywords": ["连接被拒绝", "连接超时", "网络错误"],
            },
        }

    def _load_business_weights(self) -> dict[str, float]:
        """加载业务权重配置"""
        return {
            # 需求业务权重
            "需求1": 0.95,  # 用户注册审核 - 核心业务
            "需求7": 0.95,  # 权限管理 - 核心业务
            "需求21": 0.90,  # 学生训练中心 - 核心业务
            "需求23": 0.90,  # 智能批改 - 核心业务
            "需求24": 0.85,  # AI分析 - 重要功能
            "需求14": 0.85,  # 教师智能调整 - 重要功能
            "需求35": 0.80,  # 高并发架构 - 重要功能
            "需求32": 0.80,  # 数据合规 - 重要功能
            # API路径业务权重
            "/api/v1/auth": 0.95,
            "/api/v1/users": 0.90,
            "/api/v1/training": 0.90,
            "/api/v1/ai": 0.85,
            "/api/v1/courses": 0.80,
            "/api/v1/resources": 0.75,
            "/api/v1/analytics": 0.70,
            "/api/v1/notifications": 0.65,
            # 问题类型权重
            "server_error": 1.0,
            "module_missing": 1.0,
            "connection_error": 0.9,
            "authentication_error": 0.8,
            "api_not_found": 0.8,
            "method_not_allowed": 0.6,
            "validation_error": 0.5,
            "performance_issue": 0.4,
        }

    def analyze_issues(self, mapping_report: dict[str, Any]) -> list[IssueAnalysis]:
        """分析问题并分类"""
        issues = []

        # 从映射报告中提取问题
        for req_id, requirement in mapping_report.get("requirements", {}).items():
            req_issues = requirement.get("issues", [])

            for issue_desc in req_issues:
                issue_analysis = self._analyze_single_issue(
                    issue_desc, req_id, requirement
                )
                if issue_analysis:
                    issues.append(issue_analysis)

        return issues

    def _analyze_single_issue(
        self, issue_desc: str, req_id: str, requirement: dict[str, Any]
    ) -> IssueAnalysis | None:
        """分析单个问题"""

        # 识别问题类型
        issue_type = self._identify_issue_type(issue_desc)
        if not issue_type:
            return None

        pattern_info = self.issue_patterns[issue_type]

        # 确定业务优先级
        business_priority = self._determine_business_priority(req_id, issue_desc)

        # 提取受影响的API
        affected_apis = self._extract_affected_apis(issue_desc, requirement)

        # 估算修复时间
        estimated_fix_time = self._estimate_fix_time(
            issue_type, pattern_info["severity"]
        )

        # 识别依赖关系
        dependencies = self._identify_dependencies(issue_type, affected_apis)

        # 评估风险等级
        risk_level = self._assess_risk_level(
            pattern_info["severity"], pattern_info["impact_scope"], business_priority
        )

        return IssueAnalysis(
            issue_type=issue_type,
            description=issue_desc,
            severity=pattern_info["severity"],
            impact_scope=pattern_info["impact_scope"],
            business_priority=business_priority,
            affected_apis=affected_apis,
            affected_requirements=[req_id],
            estimated_fix_time=estimated_fix_time,
            dependencies=dependencies,
            risk_level=risk_level,
        )

    def _identify_issue_type(self, issue_desc: str) -> str | None:
        """识别问题类型"""
        for issue_type, pattern_info in self.issue_patterns.items():
            # 检查正则模式
            for pattern in pattern_info["patterns"]:
                if re.search(pattern, issue_desc, re.IGNORECASE):
                    return issue_type

            # 检查关键词
            for keyword in pattern_info["keywords"]:
                if keyword in issue_desc:
                    return issue_type

        return None

    def _determine_business_priority(
        self, req_id: str, issue_desc: str
    ) -> BusinessPriority:
        """确定业务优先级"""
        # 基于需求ID的权重
        req_weight = self.business_weights.get(req_id, 0.5)

        # 基于API路径的权重
        api_weight = 0.5
        for api_path, weight in self.business_weights.items():
            if api_path.startswith("/api/") and api_path in issue_desc:
                api_weight = max(api_weight, weight)

        # 综合权重
        combined_weight = max(req_weight, api_weight)

        if combined_weight >= 0.9:
            return BusinessPriority.CORE_BUSINESS
        elif combined_weight >= 0.8:
            return BusinessPriority.IMPORTANT_FEATURE
        elif combined_weight >= 0.6:
            return BusinessPriority.NICE_TO_HAVE
        else:
            return BusinessPriority.OPTIMIZATION

    def _extract_affected_apis(
        self, issue_desc: str, requirement: dict[str, Any]
    ) -> list[str]:
        """提取受影响的API"""
        affected_apis = []

        # 从问题描述中提取API路径
        api_pattern = r"/api/v\d+/[^\s]+"
        matches = re.findall(api_pattern, issue_desc)
        affected_apis.extend(matches)

        # 从需求映射的API中提取
        mapped_apis = requirement.get("mapped_apis", [])
        for api in mapped_apis:
            if isinstance(api, dict) and "path" in api:
                affected_apis.append(api["path"])

        return list(set(affected_apis))

    def _estimate_fix_time(self, issue_type: str, severity: IssueSeverity) -> int:
        """估算修复时间（小时）"""
        base_times = {
            "server_error": 8,
            "module_missing": 4,
            "connection_error": 6,
            "authentication_error": 4,
            "api_not_found": 2,
            "method_not_allowed": 1,
            "validation_error": 2,
            "performance_issue": 6,
        }

        severity_multipliers = {
            IssueSeverity.CRITICAL: 1.5,
            IssueSeverity.HIGH: 1.2,
            IssueSeverity.MEDIUM: 1.0,
            IssueSeverity.LOW: 0.8,
        }

        base_time = base_times.get(issue_type, 4)
        multiplier = severity_multipliers.get(severity, 1.0)

        return int(base_time * multiplier)

    def _identify_dependencies(
        self, issue_type: str, affected_apis: list[str]
    ) -> list[str]:
        """识别依赖关系"""
        dependencies = []

        # 基于问题类型的依赖
        type_dependencies = {
            "module_missing": ["环境配置", "依赖安装"],
            "authentication_error": ["用户管理模块", "权限系统"],
            "connection_error": ["网络配置", "服务启动"],
            "server_error": ["错误日志分析", "代码调试"],
        }

        dependencies.extend(type_dependencies.get(issue_type, []))

        # 基于API路径的依赖
        for api in affected_apis:
            if "/auth" in api:
                dependencies.append("认证系统")
            elif "/users" in api:
                dependencies.append("用户管理模块")
            elif "/ai" in api:
                dependencies.append("AI服务集成")
            elif "/training" in api:
                dependencies.append("训练系统模块")

        return list(set(dependencies))

    def _assess_risk_level(
        self,
        severity: IssueSeverity,
        impact_scope: ImpactScope,
        business_priority: BusinessPriority,
    ) -> str:
        """评估风险等级"""
        risk_score = 0

        # 严重程度评分
        severity_scores = {
            IssueSeverity.CRITICAL: 4,
            IssueSeverity.HIGH: 3,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 1,
        }
        risk_score += severity_scores.get(severity, 2)

        # 影响范围评分
        scope_scores = {
            ImpactScope.SYSTEM_WIDE: 4,
            ImpactScope.MODULE_WIDE: 3,
            ImpactScope.FEATURE_SPECIFIC: 2,
            ImpactScope.MINOR: 1,
        }
        risk_score += scope_scores.get(impact_scope, 2)

        # 业务优先级评分
        priority_scores = {
            BusinessPriority.CORE_BUSINESS: 4,
            BusinessPriority.IMPORTANT_FEATURE: 3,
            BusinessPriority.NICE_TO_HAVE: 2,
            BusinessPriority.OPTIMIZATION: 1,
        }
        risk_score += priority_scores.get(business_priority, 2)

        # 风险等级判定
        if risk_score >= 10:
            return "极高"
        elif risk_score >= 8:
            return "高"
        elif risk_score >= 6:
            return "中"
        else:
            return "低"

    def create_fix_tasks(self, issues: list[IssueAnalysis]) -> list[FixTask]:
        """创建修复任务"""
        # 按问题类型和受影响的模块分组
        task_groups = self._group_issues_by_task(issues)

        fix_tasks = []
        task_id = 1

        for group_key, group_issues in task_groups.items():
            task = self._create_single_fix_task(task_id, group_key, group_issues)
            fix_tasks.append(task)
            task_id += 1

        # 计算优先级分数并排序
        for task in fix_tasks:
            task.priority_score = self._calculate_priority_score(task)

        # 按优先级排序
        fix_tasks.sort(key=lambda x: x.priority_score, reverse=True)

        # 分配执行顺序
        for i, task in enumerate(fix_tasks):
            task.fix_order = i + 1

        return fix_tasks

    def _group_issues_by_task(
        self, issues: list[IssueAnalysis]
    ) -> dict[str, list[IssueAnalysis]]:
        """按任务分组问题"""
        groups: dict[str, list[IssueAnalysis]] = {}

        for issue in issues:
            # 基于问题类型和影响范围分组
            if issue.severity == IssueSeverity.CRITICAL:
                group_key = f"critical_{issue.issue_type}"
            elif issue.impact_scope == ImpactScope.SYSTEM_WIDE:
                group_key = f"system_{issue.issue_type}"
            elif issue.impact_scope == ImpactScope.MODULE_WIDE:
                # 基于受影响的模块分组
                module = self._extract_module_from_apis(issue.affected_apis)
                group_key = f"module_{module}_{issue.issue_type}"
            else:
                group_key = f"feature_{issue.issue_type}"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(issue)

        return groups

    def _extract_module_from_apis(self, apis: list[str]) -> str:
        """从API路径提取模块名"""
        if not apis:
            return "unknown"

        # 提取最常见的模块
        modules = []
        for api in apis:
            parts = api.split("/")
            if len(parts) >= 4:  # /api/v1/module/...
                modules.append(parts[3])

        if modules:
            # 返回最常见的模块
            return max(set(modules), key=modules.count)
        else:
            return "unknown"

    def _create_single_fix_task(
        self, task_id: int, group_key: str, issues: list[IssueAnalysis]
    ) -> FixTask:
        """创建单个修复任务"""

        # 生成任务标题和描述
        title = self._generate_task_title(group_key, issues)
        description = self._generate_task_description(issues)

        # 计算总估算时间
        total_time = sum(issue.estimated_fix_time for issue in issues)

        # 收集所有依赖
        all_dependencies = []
        for issue in issues:
            all_dependencies.extend(issue.dependencies)
        unique_dependencies = list(set(all_dependencies))

        # 收集受影响的需求
        affected_requirements = []
        for issue in issues:
            affected_requirements.extend(issue.affected_requirements)
        unique_requirements = list(set(affected_requirements))

        return FixTask(
            task_id=f"TASK-{task_id:03d}",
            title=title,
            description=description,
            issues=issues,
            priority_score=0.0,  # 稍后计算
            estimated_time=total_time,
            dependencies=unique_dependencies,
            affected_requirements=unique_requirements,
            fix_order=0,  # 稍后分配
        )

    def _generate_task_title(self, group_key: str, issues: list[IssueAnalysis]) -> str:
        """生成任务标题"""
        if "critical" in group_key:
            return f"紧急修复：{issues[0].issue_type.replace('_', ' ').title()}"
        elif "system" in group_key:
            return f"系统级修复：{issues[0].issue_type.replace('_', ' ').title()}"
        elif "module" in group_key:
            module = group_key.split("_")[1]
            return f"{module.title()}模块修复"
        else:
            return f"功能修复：{issues[0].issue_type.replace('_', ' ').title()}"

    def _generate_task_description(self, issues: list[IssueAnalysis]) -> str:
        """生成任务描述"""
        descriptions = []

        for issue in issues:
            descriptions.append(f"- {issue.description}")

        return "\\n".join(descriptions)

    def _calculate_priority_score(self, task: FixTask) -> float:
        """计算优先级分数"""
        score = 0.0

        for issue in task.issues:
            # 严重程度权重
            severity_weights = {
                IssueSeverity.CRITICAL: 40,
                IssueSeverity.HIGH: 30,
                IssueSeverity.MEDIUM: 20,
                IssueSeverity.LOW: 10,
            }
            score += severity_weights.get(issue.severity, 20)

            # 影响范围权重
            scope_weights = {
                ImpactScope.SYSTEM_WIDE: 30,
                ImpactScope.MODULE_WIDE: 20,
                ImpactScope.FEATURE_SPECIFIC: 15,
                ImpactScope.MINOR: 5,
            }
            score += scope_weights.get(issue.impact_scope, 15)

            # 业务优先级权重
            business_weights = {
                BusinessPriority.CORE_BUSINESS: 30,
                BusinessPriority.IMPORTANT_FEATURE: 20,
                BusinessPriority.NICE_TO_HAVE: 10,
                BusinessPriority.OPTIMIZATION: 5,
            }
            score += business_weights.get(issue.business_priority, 15)

            # 受影响需求的业务权重
            for req_id in issue.affected_requirements:
                req_weight = self.business_weights.get(req_id, 0.5)
                score += req_weight * 10

        # 时间成本惩罚（时间越长，优先级稍微降低）
        time_penalty = min(task.estimated_time * 0.5, 10)
        score -= time_penalty

        return score

    def generate_priority_report(self, fix_tasks: list[FixTask]) -> dict[str, Any]:
        """生成优先级报告"""
        report: dict[str, Any] = {
            "summary": {
                "total_tasks": len(fix_tasks),
                "total_estimated_time": sum(task.estimated_time for task in fix_tasks),
                "critical_tasks": 0,
                "high_priority_tasks": 0,
                "medium_priority_tasks": 0,
                "low_priority_tasks": 0,
            },
            "execution_plan": [],
            "dependency_graph": {},
            "resource_allocation": {},
        }

        # 按优先级分类任务
        for task in fix_tasks:
            if task.priority_score >= 80:
                report["summary"]["critical_tasks"] += 1
                priority_level = "critical"
            elif task.priority_score >= 60:
                report["summary"]["high_priority_tasks"] += 1
                priority_level = "high"
            elif task.priority_score >= 40:
                report["summary"]["medium_priority_tasks"] += 1
                priority_level = "medium"
            else:
                report["summary"]["low_priority_tasks"] += 1
                priority_level = "low"

            # 执行计划
            task_plan = {
                "task_id": task.task_id,
                "title": task.title,
                "priority_level": priority_level,
                "priority_score": task.priority_score,
                "estimated_time": task.estimated_time,
                "fix_order": task.fix_order,
                "affected_requirements": task.affected_requirements,
                "dependencies": task.dependencies,
                "issues_count": len(task.issues),
            }
            report["execution_plan"].append(task_plan)

            # 依赖关系图
            report["dependency_graph"][task.task_id] = task.dependencies

        return report

    def save_priority_report(self, fix_tasks: list[FixTask], output_file: str) -> None:
        """保存优先级报告"""
        report = self.generate_priority_report(fix_tasks)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 优先级报告已保存: {output_file}")

    def print_execution_plan(self, fix_tasks: list[FixTask]) -> None:
        """打印执行计划"""
        print("\\n🎯 修复任务执行计划")
        print("=" * 60)

        for task in fix_tasks:
            priority_level = (
                "🔥 紧急"
                if task.priority_score >= 80
                else (
                    "⚡ 高"
                    if task.priority_score >= 60
                    else "📋 中" if task.priority_score >= 40 else "📝 低"
                )
            )

            print(f"\\n{task.fix_order}. {task.title}")
            print(f"   优先级: {priority_level} (分数: {task.priority_score:.1f})")
            print(f"   预估时间: {task.estimated_time}小时")
            print(f"   影响需求: {', '.join(task.affected_requirements)}")
            print(f"   问题数量: {len(task.issues)}个")
            if task.dependencies:
                print(f"   依赖: {', '.join(task.dependencies)}")


def main() -> int:
    """主函数"""
    print("🎯 开始修复优先级排序...")

    sorter = PrioritySorter()

    try:
        # 加载需求映射报告
        mapping_report_file = "tools/reports/requirement_mapping_report.json"
        if not Path(mapping_report_file).exists():
            print(f"❌ 需求映射报告不存在: {mapping_report_file}")
            print("请先运行 requirement_mapper.py 生成映射报告")
            return 1

        with open(mapping_report_file, encoding="utf-8") as f:
            mapping_report = json.load(f)

        print("✅ 已加载需求映射报告")

        # 分析问题
        issues = sorter.analyze_issues(mapping_report)
        print(f"✅ 已分析 {len(issues)} 个问题")

        # 创建修复任务
        fix_tasks = sorter.create_fix_tasks(issues)
        print(f"✅ 已创建 {len(fix_tasks)} 个修复任务")

        # 生成报告
        output_file = "tools/reports/priority_sorting_report.json"
        sorter.save_priority_report(fix_tasks, output_file)

        # 打印执行计划
        sorter.print_execution_plan(fix_tasks)

    except Exception as e:
        print(f"❌ 优先级排序过程出错: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
