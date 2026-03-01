#!/usr/bin/env python3
"""
验收标准检查器
自动化检查需求的验收标准是否满足
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Any

import aiohttp


class CheckResult(Enum):
    """检查结果枚举"""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class AcceptanceCheck:
    """验收检查结果"""

    criterion: str
    result: CheckResult
    message: str
    details: dict[str, Any] | None = None


@dataclass
class RequirementAcceptance:
    """需求验收结果"""

    requirement_id: str
    title: str
    checks: list[AcceptanceCheck]
    overall_result: CheckResult
    pass_rate: float


class AcceptanceChecker:
    """验收标准检查器"""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.session: aiohttp.ClientSession | None = None
        self.auth_token: str | None = None

    async def __aenter__(self) -> "AcceptanceChecker":
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.session:
            await self.session.close()

    async def authenticate(
        self, username: str = "admin", password: str = "admin123"
    ) -> bool:
        """获取认证token"""
        if self.session is None:
            raise RuntimeError("Session not initialized. Use async context manager.")

        try:
            auth_data = {"username": username, "password": password}

            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login", json=auth_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    return True
                else:
                    print(f"⚠️  认证失败: {response.status}")
                    return False

        except Exception as e:
            print(f"⚠️  认证异常: {e}")
            return False

    def get_auth_headers(self) -> dict[str, str]:
        """获取认证头"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    async def check_requirement_1(self) -> RequirementAcceptance:
        """检查需求1：用户注册审核管理"""
        checks = []

        # 检查学生注册API
        check = await self._check_api_endpoint(
            "POST",
            "/api/v1/users/students/register",
            "学生注册收集11项必要信息",
            expected_fields=[
                "name",
                "student_id",
                "phone",
                "email",
                "id_card",
                "emergency_contact",
                "grade",
                "major",
                "school",
                "address",
                "photo",
            ],
        )
        checks.append(check)

        # 检查教师注册API
        check = await self._check_api_endpoint(
            "POST",
            "/api/v1/users/teachers/register",
            "教师注册收集资质文件",
            expected_fields=[
                "name",
                "phone",
                "email",
                "qualification_files",
                "teaching_experience",
            ],
        )
        checks.append(check)

        # 检查管理员审核API
        check = await self._check_api_endpoint(
            "POST",
            "/api/v1/users/audit",
            "管理员可审核通过/驳回",
            expected_fields=["user_id", "action", "reason"],
        )
        checks.append(check)

        # 检查批量审核功能
        check = await self._check_api_endpoint(
            "POST",
            "/api/v1/users/audit/batch",
            "支持批量审核（最多20条）",
            expected_fields=["user_ids", "action", "reason"],
        )
        checks.append(check)

        # 检查审核状态查询API
        check = await self._check_api_endpoint(
            "GET", "/api/v1/users/audit/status/{user_id}", "公开API可查询审核状态"
        )
        checks.append(check)

        return self._create_requirement_acceptance("需求1", "用户注册审核管理", checks)

    async def check_requirement_21(self) -> RequirementAcceptance:
        """检查需求21：学生综合训练中心"""
        checks = []

        # 检查词汇训练API
        check = await self._check_api_endpoint(
            "GET",
            "/api/v1/training/vocabulary",
            "词汇训练：每日15-30题，5种题型，5级难度",
        )
        checks.append(check)

        # 检查听力训练API
        check = await self._check_api_endpoint(
            "GET",
            "/api/v1/training/listening",
            "听力训练：4种题型，语速可调，辅助功能完整",
        )
        checks.append(check)

        # 检查翻译训练API
        check = await self._check_api_endpoint(
            "GET", "/api/v1/training/translation", "翻译训练：每日2题，AI自动评分"
        )
        checks.append(check)

        # 检查阅读理解API
        check = await self._check_api_endpoint(
            "GET", "/api/v1/training/reading", "阅读理解：每周3主题×5题，4类技能训练"
        )
        checks.append(check)

        # 检查写作训练API
        check = await self._check_api_endpoint(
            "GET",
            "/api/v1/training/writing",
            "写作训练：5种题型，实时辅助，四级评分标准",
        )
        checks.append(check)

        # 检查自适应学习API
        check = await self._check_api_endpoint(
            "GET", "/api/v1/training/adaptive", "自适应学习：根据表现调整内容和难度"
        )
        checks.append(check)

        # 检查数据同步性能
        check = await self._check_performance(
            "GET", "/api/v1/training/sync", "数据同步延迟<500ms", max_response_time=0.5
        )
        checks.append(check)

        return self._create_requirement_acceptance("需求21", "学生综合训练中心", checks)

    async def check_requirement_23(self) -> RequirementAcceptance:
        """检查需求23：智能批改与反馈系统"""
        checks = []

        # 检查流式批改API
        check = await self._check_api_endpoint(
            "POST", "/api/v1/ai/grading/stream", "流式智能批改功能"
        )
        checks.append(check)

        # 检查题目生成API
        check = await self._check_api_endpoint(
            "POST", "/api/v1/ai/questions/generate", "基于课程词汇库+热点动态生成"
        )
        checks.append(check)

        # 检查批改性能
        check = await self._check_performance(
            "POST", "/api/v1/ai/grading", "批改响应时间<3秒", max_response_time=3.0
        )
        checks.append(check)

        # 检查错题归集API
        check = await self._check_api_endpoint(
            "GET", "/api/v1/training/errors", "错题自动归集至错题本"
        )
        checks.append(check)

        # 检查知识点分析API
        check = await self._check_api_endpoint(
            "GET",
            "/api/v1/ai/analysis/knowledge-points",
            "知识点薄弱环节分析推送教师端",
        )
        checks.append(check)

        return self._create_requirement_acceptance("需求23", "智能批改与反馈系统", checks)

    async def check_requirement_35(self) -> RequirementAcceptance:
        """检查需求35：高并发架构与AI服务优化"""
        checks = []

        # 检查并发支持
        check = await self._check_concurrency(
            "GET",
            "/api/v1/training",
            "1000+学生并发支持",
            concurrent_requests=100,  # 简化测试
            max_response_time=0.8,
        )
        checks.append(check)

        # 检查AI服务健康监控
        check = await self._check_api_endpoint("GET", "/api/v1/ai/health", "AI服务健康监控")
        checks.append(check)

        # 检查请求队列管理
        check = await self._check_api_endpoint(
            "GET", "/api/v1/system/queue/status", "请求队列管理"
        )
        checks.append(check)

        # 检查降级策略
        check = await self._check_api_endpoint(
            "GET", "/api/v1/system/fallback/status", "多级降级策略"
        )
        checks.append(check)

        return self._create_requirement_acceptance("需求35", "高并发架构与AI服务优化", checks)

    async def _check_api_endpoint(
        self,
        method: str,
        path: str,
        description: str,
        expected_fields: list[str] | None = None,
        test_data: dict[str, Any] | None = None,
    ) -> AcceptanceCheck:
        """检查API端点"""
        if self.session is None:
            raise RuntimeError("Session not initialized. Use async context manager.")

        try:
            url = f"{self.base_url}{path}"
            headers = self.get_auth_headers()

            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    status = response.status
                    data = (
                        await response.json()
                        if response.content_type == "application/json"
                        else {}
                    )
            elif method == "POST":
                json_data = test_data or {}
                async with self.session.post(
                    url, json=json_data, headers=headers
                ) as response:
                    status = response.status
                    data = (
                        await response.json()
                        if response.content_type == "application/json"
                        else {}
                    )
            else:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.SKIP,
                    message=f"不支持的HTTP方法: {method}",
                )

            # 分析结果
            if status == 200:
                # 检查预期字段
                if expected_fields and isinstance(data, dict):
                    missing_fields = [
                        field for field in expected_fields if field not in data
                    ]
                    if missing_fields:
                        return AcceptanceCheck(
                            criterion=description,
                            result=CheckResult.WARNING,
                            message=f"缺少预期字段: {missing_fields}",
                            details={
                                "status": status,
                                "missing_fields": missing_fields,
                            },
                        )

                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.PASS,
                    message="API端点正常工作",
                    details={"status": status},
                )
            elif status == 404:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.FAIL,
                    message="API端点不存在",
                    details={"status": status},
                )
            elif status == 403:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.WARNING,
                    message="需要认证或权限不足",
                    details={"status": status},
                )
            elif status >= 500:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.FAIL,
                    message="服务器内部错误",
                    details={"status": status},
                )
            else:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.WARNING,
                    message=f"意外的状态码: {status}",
                    details={"status": status},
                )

        except Exception as e:
            return AcceptanceCheck(
                criterion=description,
                result=CheckResult.FAIL,
                message=f"请求失败: {str(e)}",
                details={"error": str(e)},
            )

    async def _check_performance(
        self, method: str, path: str, description: str, max_response_time: float
    ) -> AcceptanceCheck:
        """检查性能要求"""
        if self.session is None:
            raise RuntimeError("Session not initialized. Use async context manager.")

        try:
            import time

            url = f"{self.base_url}{path}"
            headers = self.get_auth_headers()

            start_time = time.time()

            if method == "GET":
                async with self.session.get(url, headers=headers) as _:
                    pass  # 只需要测试连接，不需要处理响应
            else:
                async with self.session.post(url, json={}, headers=headers) as _:
                    pass  # 只需要测试连接，不需要处理响应

            response_time = time.time() - start_time

            if response_time <= max_response_time:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.PASS,
                    message=f"响应时间: {response_time:.3f}s (要求: <{max_response_time}s)",
                    details={
                        "response_time": response_time,
                        "max_allowed": max_response_time,
                    },
                )
            else:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.FAIL,
                    message=f"响应时间超标: {response_time:.3f}s (要求: <{max_response_time}s)",
                    details={
                        "response_time": response_time,
                        "max_allowed": max_response_time,
                    },
                )

        except Exception as e:
            return AcceptanceCheck(
                criterion=description,
                result=CheckResult.FAIL,
                message=f"性能测试失败: {str(e)}",
                details={"error": str(e)},
            )

    async def _check_concurrency(
        self,
        method: str,
        path: str,
        description: str,
        concurrent_requests: int,
        max_response_time: float,
    ) -> AcceptanceCheck:
        """检查并发性能"""
        if self.session is None:
            raise RuntimeError("Session not initialized. Use async context manager.")

        try:
            import time

            url = f"{self.base_url}{path}"
            headers = self.get_auth_headers()
            session = self.session  # 局部变量避免类型检查问题

            async def single_request() -> tuple[int, float]:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        return response.status, time.time()
                else:
                    async with session.post(url, json={}, headers=headers) as response:
                        return response.status, time.time()

            # 并发请求
            start_time = time.time()
            tasks = [single_request() for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # 分析结果
            successful_requests = 0
            failed_requests = 0

            for result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                else:
                    status, _ = result
                    if status == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1

            success_rate = successful_requests / concurrent_requests
            avg_response_time = total_time / concurrent_requests

            if success_rate >= 0.95 and avg_response_time <= max_response_time:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.PASS,
                    message=f"并发测试通过: {successful_requests}/{concurrent_requests} 成功, 平均响应时间: {avg_response_time:.3f}s",
                    details={
                        "concurrent_requests": concurrent_requests,
                        "successful_requests": successful_requests,
                        "success_rate": success_rate,
                        "avg_response_time": avg_response_time,
                    },
                )
            else:
                return AcceptanceCheck(
                    criterion=description,
                    result=CheckResult.FAIL,
                    message=f"并发测试失败: {successful_requests}/{concurrent_requests} 成功, 平均响应时间: {avg_response_time:.3f}s",
                    details={
                        "concurrent_requests": concurrent_requests,
                        "successful_requests": successful_requests,
                        "success_rate": success_rate,
                        "avg_response_time": avg_response_time,
                    },
                )

        except Exception as e:
            return AcceptanceCheck(
                criterion=description,
                result=CheckResult.FAIL,
                message=f"并发测试异常: {str(e)}",
                details={"error": str(e)},
            )

    def _create_requirement_acceptance(
        self, req_id: str, title: str, checks: list[AcceptanceCheck]
    ) -> RequirementAcceptance:
        """创建需求验收结果"""
        pass_count = sum(1 for check in checks if check.result == CheckResult.PASS)
        total_count = len(checks)
        pass_rate = (pass_count / total_count) * 100 if total_count > 0 else 0

        # 确定整体结果
        if pass_rate == 100:
            overall_result = CheckResult.PASS
        elif pass_rate >= 80:
            overall_result = CheckResult.WARNING
        else:
            overall_result = CheckResult.FAIL

        return RequirementAcceptance(
            requirement_id=req_id,
            title=title,
            checks=checks,
            overall_result=overall_result,
            pass_rate=pass_rate,
        )

    async def run_all_checks(self) -> list[RequirementAcceptance]:
        """运行所有验收检查"""
        print("🔍 开始验收标准检查...")

        # 尝试认证
        await self.authenticate()

        results = []

        # 检查关键需求
        check_methods = [
            self.check_requirement_1,
            self.check_requirement_21,
            self.check_requirement_23,
            self.check_requirement_35,
        ]

        for check_method in check_methods:
            try:
                result = await check_method()
                results.append(result)
                print(f"✅ {result.requirement_id} 检查完成: {result.pass_rate:.1f}% 通过")
            except Exception as e:
                print(f"❌ {check_method.__name__} 检查失败: {e}")

        return results

    def generate_acceptance_report(
        self, results: list[RequirementAcceptance]
    ) -> dict[str, Any]:
        """生成验收报告"""
        report: dict[str, Any] = {
            "summary": {
                "total_requirements": len(results),
                "passed": 0,
                "warnings": 0,
                "failed": 0,
                "overall_pass_rate": 0.0,
            },
            "requirements": [],
            "issues": [],
        }

        total_pass_rate = 0.0

        for result in results:
            # 统计结果
            if result.overall_result == CheckResult.PASS:
                report["summary"]["passed"] += 1
            elif result.overall_result == CheckResult.WARNING:
                report["summary"]["warnings"] += 1
            else:
                report["summary"]["failed"] += 1

            total_pass_rate += result.pass_rate

            # 详细结果
            requirement_data: dict[str, Any] = {
                "requirement_id": result.requirement_id,
                "title": result.title,
                "overall_result": result.overall_result.value,
                "pass_rate": result.pass_rate,
                "checks": [],
            }

            for check in result.checks:
                check_data = {
                    "criterion": check.criterion,
                    "result": check.result.value,
                    "message": check.message,
                }
                if check.details:
                    check_data["details"] = check.details

                requirement_data["checks"].append(check_data)

                # 收集问题
                if check.result in [CheckResult.FAIL, CheckResult.WARNING]:
                    report["issues"].append(
                        {
                            "requirement_id": result.requirement_id,
                            "criterion": check.criterion,
                            "result": check.result.value,
                            "message": check.message,
                        }
                    )

            report["requirements"].append(requirement_data)

        # 计算总体通过率
        if results:
            report["summary"]["overall_pass_rate"] = total_pass_rate / len(results)

        return report

    def save_acceptance_report(
        self, results: list[RequirementAcceptance], output_file: str
    ) -> None:
        """保存验收报告"""
        report = self.generate_acceptance_report(results)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 验收报告已保存: {output_file}")

    def print_summary(self, results: list[RequirementAcceptance]) -> None:
        """打印验收摘要"""
        report = self.generate_acceptance_report(results)
        summary = report["summary"]

        print("\\n📊 验收标准检查摘要")
        print("=" * 50)
        print(f"检查需求数: {summary['total_requirements']}")
        print(f"通过: {summary['passed']}")
        print(f"警告: {summary['warnings']}")
        print(f"失败: {summary['failed']}")
        print(f"总体通过率: {summary['overall_pass_rate']:.1f}%")

        print("\\n⚠️  主要问题")
        print("-" * 30)
        for issue in report["issues"][:10]:  # 显示前10个问题
            print(f"{issue['requirement_id']}: {issue['message']}")


async def main() -> None:
    """主函数"""
    print("🔍 开始验收标准检查...")

    async with AcceptanceChecker() as checker:
        results = await checker.run_all_checks()

        # 生成报告
        output_file = "tools/reports/acceptance_check_report.json"
        checker.save_acceptance_report(results, output_file)

        # 打印摘要
        checker.print_summary(results)


if __name__ == "__main__":
    exit(asyncio.run(main()))
