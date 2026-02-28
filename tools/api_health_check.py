#!/usr/bin/env python3
"""
API健康检查脚本
用于测试所有API端点的可用性和响应状态
"""

import logging

logger = logging.getLogger(__name__)
import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class APITestResult:
    endpoint: str
    method: str
    status_code: int
    response_time: float
    error: str = None
    success: bool = False


class APIHealthChecker:
    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.results: list[APITestResult] = []

    async def test_endpoint(
        self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET"
    ) -> APITestResult:
        """测试单个API端点"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            async with session.request(
                method, url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_time = time.time() - start_time

                # 读取响应内容（但不处理，只是为了完整测试）
                try:
                    await response.text()
                except Exception as e:
                    logger.warning(f"Failed to read response text: {e}")

                return APITestResult(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status,
                    response_time=response_time,
                    success=response.status < 500,  # 5xx错误认为是失败
                )

        except TimeoutError:
            return APITestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=time.time() - start_time,
                error="Timeout",
                success=False,
            )
        except Exception as e:
            return APITestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=time.time() - start_time,
                error=str(e),
                success=False,
            )

    async def load_endpoints_from_file(self, file_path: str) -> list[str]:
        """从文件加载API端点列表"""
        try:
            with open(file_path) as f:
                endpoints = [
                    line.strip().strip('"')
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
            return endpoints
        except FileNotFoundError:
            print(f"端点文件 {file_path} 未找到")
            return []

    async def run_health_check(
        self, endpoints_file: str = "api_endpoints.txt"
    ) -> dict[str, Any]:
        """运行完整的API健康检查"""
        print("🔍 开始API健康检查...")

        # 加载端点列表
        endpoints = await self.load_endpoints_from_file(endpoints_file)
        if not endpoints:
            print("❌ 未找到API端点列表")
            return {}

        print(f"📋 发现 {len(endpoints)} 个API端点")

        # 创建HTTP会话
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            # 并发测试所有端点
            tasks = []
            for endpoint in endpoints:
                # 根据端点类型选择HTTP方法
                method = self.guess_http_method(endpoint)
                task = self.test_endpoint(session, endpoint, method)
                tasks.append(task)

            # 执行所有测试
            print("🚀 开始并发测试API端点...")
            self.results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常结果
            processed_results = []
            for result in self.results:
                if isinstance(result, Exception):
                    processed_results.append(
                        APITestResult(
                            endpoint="unknown",
                            method="GET",
                            status_code=0,
                            response_time=0,
                            error=str(result),
                            success=False,
                        )
                    )
                else:
                    processed_results.append(result)

            self.results = processed_results

        return self.generate_report()

    def guess_http_method(self, endpoint: str) -> str:
        """根据端点路径猜测HTTP方法"""
        if any(
            keyword in endpoint.lower()
            for keyword in ["create", "register", "login", "submit", "generate"]
        ):
            return "POST"
        elif any(
            keyword in endpoint.lower() for keyword in ["update", "edit", "modify"]
        ):
            return "PUT"
        elif any(keyword in endpoint.lower() for keyword in ["delete", "remove"]):
            return "DELETE"
        else:
            return "GET"

    def generate_report(self) -> dict[str, Any]:
        """生成健康检查报告"""
        if not self.results:
            return {}

        total_endpoints = len(self.results)
        successful_endpoints = sum(1 for r in self.results if r.success)
        failed_endpoints = total_endpoints - successful_endpoints

        # 按状态码分组
        status_groups: dict[int, list[APITestResult]] = {}
        for result in self.results:
            status = result.status_code
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)

        # 计算平均响应时间
        avg_response_time = sum(r.response_time for r in self.results) / total_endpoints

        # 识别问题端点
        problem_endpoints = [r for r in self.results if not r.success]

        report = {
            "summary": {
                "total_endpoints": total_endpoints,
                "successful_endpoints": successful_endpoints,
                "failed_endpoints": failed_endpoints,
                "success_rate": f"{(successful_endpoints / total_endpoints) * 100:.1f}%",
                "average_response_time": f"{avg_response_time:.3f}s",
            },
            "status_distribution": {
                str(status): len(results) for status, results in status_groups.items()
            },
            "problem_endpoints": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "error": r.error,
                    "response_time": f"{r.response_time:.3f}s",
                }
                for r in problem_endpoints[:20]  # 只显示前20个问题端点
            ],
            "performance_analysis": {
                "fast_endpoints": len(
                    [r for r in self.results if r.response_time < 0.1]
                ),
                "medium_endpoints": len(
                    [r for r in self.results if 0.1 <= r.response_time < 0.5]
                ),
                "slow_endpoints": len(
                    [r for r in self.results if r.response_time >= 0.5]
                ),
            },
        }

        return report

    def print_report(self, report: dict[str, Any]) -> None:
        """打印健康检查报告"""
        print("\n" + "=" * 60)
        print("📊 API健康检查报告")
        print("=" * 60)

        summary = report.get("summary", {})
        print("📈 总体统计:")
        print(f"   • 总端点数: {summary.get('total_endpoints', 0)}")
        print(f"   • 成功端点: {summary.get('successful_endpoints', 0)}")
        print(f"   • 失败端点: {summary.get('failed_endpoints', 0)}")
        print(f"   • 成功率: {summary.get('success_rate', '0%')}")
        print(f"   • 平均响应时间: {summary.get('average_response_time', '0s')}")

        print("\n🔍 状态码分布:")
        status_dist = report.get("status_distribution", {})
        for status, count in sorted(status_dist.items()):
            status_name = self.get_status_name(int(status) if status.isdigit() else 0)
            print(f"   • {status} ({status_name}): {count} 个端点")

        print("\n⚡ 性能分析:")
        perf = report.get("performance_analysis", {})
        print(f"   • 快速响应 (<0.1s): {perf.get('fast_endpoints', 0)} 个")
        print(f"   • 中等响应 (0.1-0.5s): {perf.get('medium_endpoints', 0)} 个")
        print(f"   • 慢速响应 (>0.5s): {perf.get('slow_endpoints', 0)} 个")

        problem_endpoints = report.get("problem_endpoints", [])
        if problem_endpoints:
            print("\n❌ 问题端点 (前20个):")
            for i, endpoint in enumerate(problem_endpoints, 1):
                print(f"   {i}. {endpoint['method']} {endpoint['endpoint']}")
                print(
                    f"      状态码: {endpoint['status_code']}, 响应时间: {endpoint['response_time']}"
                )
                if endpoint["error"]:
                    print(f"      错误: {endpoint['error']}")

        print("\n" + "=" * 60)

    def get_status_name(self, status_code: int) -> str:
        """获取HTTP状态码名称"""
        status_names = {
            200: "OK",
            201: "Created",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            422: "Unprocessable Entity",
            500: "Internal Server Error",
            0: "Connection Error",
        }
        return status_names.get(status_code, "Unknown")

    async def save_report(
        self, report: dict[str, Any], filename: str = "api_health_report.json"
    ) -> None:
        """保存报告到文件"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📄 报告已保存到: {filename}")


async def main() -> None:
    """主函数"""
    checker = APIHealthChecker()

    # 运行健康检查
    report = await checker.run_health_check()

    if report:
        # 打印报告
        checker.print_report(report)

        # 保存报告
        await checker.save_report(report)

        # 生成建议
        print("\n💡 建议:")
        summary = report.get("summary", {})
        success_rate = float(summary.get("success_rate", "0%").rstrip("%"))

        if success_rate >= 90:
            print("   ✅ API健康状况良好，可以开始详细审查")
        elif success_rate >= 70:
            print("   ⚠️  部分API存在问题，建议优先修复失败的端点")
        else:
            print("   🚨 API健康状况较差，需要全面检查和修复")

        print("   📋 下一步：基于此报告开始需求1-40的API审查工作")
    else:
        print("❌ 健康检查失败，请检查服务器状态")


if __name__ == "__main__":
    asyncio.run(main())
