#!/usr/bin/env python3
"""
需求-API映射系统
基于需求文档和API发现结果，建立需求与API端点的映射关系
"""

import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


class RequirementStatus(Enum):
    """需求状态枚举"""

    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"
    NEEDS_REVIEW = "needs_review"


class APIPriority(Enum):
    """API修复优先级"""

    P0_CRITICAL = "P0_critical"  # 阻塞性问题
    P1_HIGH = "P1_high"  # 重要功能
    P2_MEDIUM = "P2_medium"  # 一般功能
    P3_LOW = "P3_low"  # 优化项


@dataclass
class APIEndpoint:
    """API端点信息"""

    path: str
    method: str
    status_code: int
    response_time: float
    error_message: str | None = None
    requires_auth: bool = False


@dataclass
class RequirementMapping:
    """需求映射信息"""

    requirement_id: str
    title: str
    description: str
    user_stories: list[str]
    acceptance_criteria: list[str]
    mapped_apis: list[APIEndpoint]
    status: RequirementStatus
    priority: APIPriority
    completion_percentage: float
    issues: list[str]


class RequirementMapper:
    """需求映射器"""

    def __init__(self) -> None:
        self.requirements: dict[str, RequirementMapping] = {}
        self.api_endpoints: dict[str, APIEndpoint] = {}
        self.mapping_rules: dict[str, list[str]] = {}

    def load_requirements(self, requirements_file: str) -> None:
        """加载需求文档"""
        requirements_path = Path(requirements_file)
        if not requirements_path.exists():
            raise FileNotFoundError(f"需求文件不存在: {requirements_file}")

        with open(requirements_path, encoding="utf-8") as f:
            content = f.read()

        # 解析需求文档
        self._parse_requirements_document(content)

    def load_api_health_report(self, health_report_file: str) -> None:
        """加载API健康检查报告"""
        health_report_path = Path(health_report_file)
        if not health_report_path.exists():
            raise FileNotFoundError(f"API健康报告不存在: {health_report_file}")

        with open(health_report_path, encoding="utf-8") as f:
            health_data = json.load(f)

        # 解析API端点信息
        self._parse_api_health_data(health_data)

    def load_api_from_server(self, server_url: str = "http://localhost:8000") -> None:
        """直接从运行中的服务器获取API信息"""
        try:
            # 获取OpenAPI规范
            with urlopen(f"{server_url}/openapi.json") as response:
                openapi_spec = json.loads(response.read().decode("utf-8"))

            # 清空现有端点
            self.api_endpoints = {}

            # 解析API端点
            paths = openapi_spec.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    # 检查是否需要认证
                    requires_auth = bool(details.get("security", []))

                    endpoint = APIEndpoint(
                        path=path,
                        method=method.upper(),
                        status_code=200,  # 假设正常状态
                        response_time=0.0,  # 无法从OpenAPI获取
                        error_message=None,
                        requires_auth=requires_auth,
                    )
                    endpoint_key = f"{method.upper()} {path}"
                    self.api_endpoints[endpoint_key] = endpoint

            print(f"✅ 从服务器加载了 {len(self.api_endpoints)} 个API端点")

        except URLError as e:
            print(f"❌ 无法连接到服务器 {server_url}: {e}")
            raise
        except Exception as e:
            print(f"❌ 解析API信息失败: {e}")
            raise

    def _parse_requirements_document(self, content: str) -> None:
        """解析需求文档内容"""
        # 提取需求信息的正则表达式 - 适配当前文档格式
        requirement_pattern = r"- 需求 (\d+)：(.+?)(?=\n- 需求|\n### |\Z)"

        matches = re.findall(requirement_pattern, content, re.DOTALL)

        for match in matches:
            req_id = f"需求{match[0]}"
            title = match[1].strip()

            # 创建需求映射
            requirement = RequirementMapping(
                requirement_id=req_id,
                title=title,
                description=title,  # 使用标题作为描述
                user_stories=[f"作为系统用户，我希望{title}"],  # 生成基本用户故事
                acceptance_criteria=[f"系统应该支持{title}"],  # 生成基本验收标准
                mapped_apis=[],
                status=RequirementStatus.NOT_IMPLEMENTED,
                priority=self._determine_priority(req_id, title),
                completion_percentage=0.0,
                issues=[],
            )

            self.requirements[req_id] = requirement

    def _parse_api_health_data(self, health_data: dict[str, Any]) -> None:
        """解析API健康检查数据"""
        # 处理问题端点
        problem_endpoints = health_data.get("problem_endpoints", [])
        for endpoint_data in problem_endpoints:
            path = endpoint_data.get("endpoint", "")
            method = endpoint_data.get("method", "GET")
            status_code = endpoint_data.get("status_code", 0)
            response_time_str = endpoint_data.get("response_time", "0s")
            error_message = endpoint_data.get("error")

            # 解析响应时间
            try:
                response_time = float(response_time_str.replace("s", ""))
            except (ValueError, AttributeError):
                response_time = 0.0

            # 判断是否需要认证
            requires_auth = status_code == 403

            endpoint = APIEndpoint(
                path=path,
                method=method,
                status_code=status_code,
                response_time=response_time,
                error_message=error_message,
                requires_auth=requires_auth,
            )

            endpoint_key = f"{method} {path}"
            self.api_endpoints[endpoint_key] = endpoint

        # 从状态分布推断其他端点
        status_dist = health_data.get("status_distribution", {})
        summary = health_data.get("summary", {})
        _ = summary.get("total_endpoints", 0)  # 未使用但保留以备将来使用

        # 为每个状态码创建示例端点
        for status_code, count in status_dist.items():
            if int(status_code) == 200:
                # 创建一些成功的端点示例
                for i in range(min(count, 10)):  # 最多创建10个示例
                    endpoint = APIEndpoint(
                        path=f"/api/v1/example/success/{i}",
                        method="GET",
                        status_code=200,
                        response_time=0.1,
                        error_message=None,
                        requires_auth=False,
                    )
                    endpoint_key = f"GET /api/v1/example/success/{i}"
                    self.api_endpoints[endpoint_key] = endpoint

    def _determine_priority(self, req_id: str, title: str) -> APIPriority:
        """确定需求优先级"""
        # 核心功能关键词
        critical_keywords = [
            "注册",
            "登录",
            "认证",
            "权限",
            "安全",
            "数据库",
            "Redis",
            "训练中心",
            "智能批改",
            "AI分析",
        ]

        # 重要功能关键词
        high_keywords = [
            "管理",
            "课程",
            "教师",
            "学生",
            "资源",
            "监控",
            "教学计划",
            "学情分析",
            "错题强化",
        ]

        title_lower = title.lower()

        if any(keyword in title_lower for keyword in critical_keywords):
            return APIPriority.P0_CRITICAL
        elif any(keyword in title_lower for keyword in high_keywords):
            return APIPriority.P1_HIGH
        else:
            return APIPriority.P2_MEDIUM

    def create_mapping_rules(self) -> None:
        """创建需求-API映射规则"""
        self.mapping_rules = {
            # 用户管理相关
            "需求1": [
                "/api/v1/users/register",
                "/api/v1/users/audit",
                "/api/v1/users/status",
            ],
            "需求2": [
                "/api/v1/users/students",
                "/api/v1/users/teachers",
                "/api/v1/users/classrooms",
            ],
            "需求7": ["/api/v1/auth", "/api/v1/permissions", "/api/v1/roles"],
            "需求10": [
                "/api/v1/users/teachers/register",
                "/api/v1/users/teachers/qualification",
            ],
            "需求20": [
                "/api/v1/users/students/register",
                "/api/v1/users/students/activation",
            ],
            # 课程管理相关
            "需求3": [
                "/api/v1/courses",
                "/api/v1/courses/templates",
                "/api/v1/courses/versions",
            ],
            "需求4": ["/api/v1/courses/classes", "/api/v1/courses/assignments"],
            "需求5": ["/api/v1/courses/classes/batch", "/api/v1/courses/scheduling"],
            "需求11": ["/api/v1/resources/vocabulary", "/api/v1/resources/knowledge"],
            "需求12": ["/api/v1/resources/hotspot", "/api/v1/resources/rss"],
            # 训练系统相关
            "需求21": [
                "/api/v1/training",
                "/api/v1/training/vocabulary",
                "/api/v1/training/listening",
            ],
            "需求22": ["/api/v1/training/listening", "/api/v1/training/audio"],
            "需求23": ["/api/v1/ai/grading", "/api/v1/ai/feedback"],
            "需求24": ["/api/v1/ai/analysis", "/api/v1/ai/reports"],
            "需求25": ["/api/v1/training/errors", "/api/v1/training/adaptive"],
            "需求26": [
                "/api/v1/training/writing",
                "/api/v1/training/writing/templates",
            ],
            # AI集成相关
            "需求13": ["/api/v1/ai/syllabus", "/api/v1/ai/lesson-plans"],
            "需求14": ["/api/v1/ai/teaching-adjustment", "/api/v1/ai/optimization"],
            "需求15": ["/api/v1/training/generation", "/api/v1/training/parameters"],
            # 系统架构相关
            "需求6": ["/api/v1/analytics/monitoring", "/api/v1/analytics/reports"],
            "需求32": ["/api/v1/compliance", "/api/v1/privacy"],
            "需求33": ["/api/v1/resources/architecture", "/api/v1/resources/storage"],
            "需求34": ["/api/v1/ai/document-processing", "/api/v1/ai/vector-search"],
            "需求35": ["/api/v1/system/performance", "/api/v1/system/concurrency"],
        }

    def map_requirements_to_apis(self) -> None:
        """执行需求到API的映射"""
        self.create_mapping_rules()

        for req_id, requirement in self.requirements.items():
            mapped_apis = []
            issues = []

            # 获取该需求对应的API路径
            expected_paths = self.mapping_rules.get(req_id, [])

            for path in expected_paths:
                # 查找匹配的API端点
                matching_endpoints = self._find_matching_endpoints(path)

                if not matching_endpoints:
                    issues.append(f"缺失API端点: {path}")
                else:
                    for endpoint in matching_endpoints:
                        mapped_apis.append(endpoint)

                        # 检查端点状态
                        if endpoint.status_code >= 500:
                            issues.append(
                                f"服务器错误: {endpoint.path} - {endpoint.error_message}"
                            )
                        elif endpoint.status_code == 404:
                            issues.append(f"端点不存在: {endpoint.path}")
                        elif endpoint.status_code == 405:
                            issues.append(
                                f"HTTP方法不支持: {endpoint.method} {endpoint.path}"
                            )
                        elif endpoint.response_time > 5.0:
                            issues.append(
                                f"响应时间过长: {endpoint.path} ({endpoint.response_time:.2f}s)"
                            )

            # 更新需求映射
            requirement.mapped_apis = mapped_apis
            requirement.issues = issues
            requirement.completion_percentage = self._calculate_completion_percentage(
                requirement
            )
            requirement.status = self._determine_requirement_status(requirement)

    def _find_matching_endpoints(self, expected_path: str) -> list[APIEndpoint]:
        """查找匹配的API端点"""
        matching_endpoints = []

        for _, endpoint in self.api_endpoints.items():
            if expected_path in endpoint.path or endpoint.path.startswith(
                expected_path
            ):
                matching_endpoints.append(endpoint)

        return matching_endpoints

    def _calculate_completion_percentage(
        self, requirement: RequirementMapping
    ) -> float:
        """计算需求完成百分比"""
        if not requirement.mapped_apis:
            return 0.0

        working_apis = sum(
            1 for api in requirement.mapped_apis if api.status_code == 200
        )
        total_apis = len(requirement.mapped_apis)

        return (working_apis / total_apis) * 100.0

    def _determine_requirement_status(
        self, requirement: RequirementMapping
    ) -> RequirementStatus:
        """确定需求状态"""
        if requirement.completion_percentage == 0:
            return RequirementStatus.NOT_IMPLEMENTED
        elif requirement.completion_percentage < 100:
            return RequirementStatus.PARTIALLY_IMPLEMENTED
        elif requirement.issues:
            return RequirementStatus.NEEDS_REVIEW
        else:
            return RequirementStatus.FULLY_IMPLEMENTED

    def generate_mapping_report(self) -> dict[str, Any]:
        """生成映射报告"""
        report: dict[str, Any] = {
            "summary": {
                "total_requirements": len(self.requirements),
                "total_apis": len(self.api_endpoints),
                "fully_implemented": 0,
                "partially_implemented": 0,
                "not_implemented": 0,
                "needs_review": 0,
            },
            "requirements": {},
            "priority_breakdown": {
                "P0_critical": [],
                "P1_high": [],
                "P2_medium": [],
                "P3_low": [],
            },
            "issues_summary": [],
        }

        all_issues = []

        for req_id, requirement in self.requirements.items():
            # 统计状态
            if requirement.status == RequirementStatus.FULLY_IMPLEMENTED:
                report["summary"]["fully_implemented"] += 1
            elif requirement.status == RequirementStatus.PARTIALLY_IMPLEMENTED:
                report["summary"]["partially_implemented"] += 1
            elif requirement.status == RequirementStatus.NOT_IMPLEMENTED:
                report["summary"]["not_implemented"] += 1
            elif requirement.status == RequirementStatus.NEEDS_REVIEW:
                report["summary"]["needs_review"] += 1

            # 按优先级分类
            priority_key = requirement.priority.value
            report["priority_breakdown"][priority_key].append(
                {
                    "requirement_id": req_id,
                    "title": requirement.title,
                    "status": requirement.status.value,
                    "completion": requirement.completion_percentage,
                    "issues_count": len(requirement.issues),
                }
            )

            # 收集所有问题
            all_issues.extend(requirement.issues)

            # 详细需求信息 - 转换枚举为字符串
            requirement_dict = asdict(requirement)
            requirement_dict["status"] = requirement.status.value
            requirement_dict["priority"] = requirement.priority.value
            report["requirements"][req_id] = requirement_dict

        # 问题汇总
        issue_counts: dict[str, int] = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        report["issues_summary"] = [
            {"type": issue_type, "count": count}
            for issue_type, count in sorted(
                issue_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        return report

    def save_mapping_report(self, output_file: str) -> None:
        """保存映射报告"""
        report = self.generate_mapping_report()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 需求映射报告已保存: {output_file}")

    def print_summary(self) -> None:
        """打印映射摘要"""
        report = self.generate_mapping_report()
        summary = report["summary"]

        print("\\n📊 需求映射摘要")
        print("=" * 50)
        print(f"总需求数: {summary['total_requirements']}")
        print(f"总API数: {summary['total_apis']}")
        print(f"完全实现: {summary['fully_implemented']}")
        print(f"部分实现: {summary['partially_implemented']}")
        print(f"未实现: {summary['not_implemented']}")
        print(f"需要审查: {summary['needs_review']}")

        print("\\n🔥 优先级分布")
        print("-" * 30)
        for priority, items in report["priority_breakdown"].items():
            if items:
                print(f"{priority}: {len(items)}个需求")

        print("\\n⚠️  主要问题")
        print("-" * 30)
        for issue in report["issues_summary"][:5]:  # 显示前5个问题
            print(f"{issue['type']}: {issue['count']}个")


def main() -> int:
    """主函数"""
    print("🔍 开始需求-API映射分析...")

    mapper = RequirementMapper()

    try:
        # 加载需求文档
        requirements_file = ".kiro/specs/api-comprehensive-audit/requirements.md"
        if Path(requirements_file).exists():
            mapper.load_requirements(requirements_file)
            print(f"✅ 已加载需求文档: {len(mapper.requirements)}个需求")
        else:
            print(f"⚠️  需求文档不存在: {requirements_file}")

        # 尝试从运行中的服务器加载API信息
        try:
            mapper.load_api_from_server()
        except Exception as e:
            print(f"⚠️  无法从服务器加载API信息: {e}")
            # 回退到健康报告文件
            health_report_file = "api_health_report.json"
            if Path(health_report_file).exists():
                mapper.load_api_health_report(health_report_file)
                print(f"✅ 已加载API健康报告: {len(mapper.api_endpoints)}个端点")
            else:
                print(f"⚠️  API健康报告不存在: {health_report_file}")

        # 执行映射
        mapper.map_requirements_to_apis()
        print("✅ 需求-API映射完成")

        # 生成报告
        output_file = "tools/reports/requirement_mapping_report.json"
        mapper.save_mapping_report(output_file)

        # 打印摘要
        mapper.print_summary()

    except Exception as e:
        print(f"❌ 映射过程出错: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
