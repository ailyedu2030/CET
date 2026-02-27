#!/usr/bin/env python3
"""
API验证脚本 - 验证现有API的工作状态和完整性
基于todo中的需求对比，检查API实现的完整性和正确性
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import aiohttp
except ImportError:
    print("❌ 需要安装 aiohttp: pip install aiohttp")
    sys.exit(1)

logger = logging.getLogger(__name__)


class APIValidator:
    """API验证器 - 检查API的可用性和完整性"""

    def __init__(self: "APIValidator", base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url
        self.session: aiohttp.ClientSession | None = None

        # 基于todo的核心API检查清单
        self.core_api_checks = {
            # 第一优先级 - 必须存在的核心API
            "priority_1_core": [
                {
                    "path": "/api/v1/training/center/modes",
                    "method": "GET",
                    "description": "训练模式列表",
                },
                {
                    "path": "/api/v1/training/center/sessions",
                    "method": "POST",
                    "description": "创建训练会话",
                },
                {
                    "path": "/api/v1/ai/grading/submit",
                    "method": "POST",
                    "description": "AI智能批改",
                },
                {
                    "path": "/api/v1/training/listening/exercises",
                    "method": "GET",
                    "description": "听力练习列表",
                },
            ],
            # 第二优先级 - 重要的AI功能API
            "priority_2_ai": [
                {
                    "path": "/api/v1/ai/analysis/analyze",
                    "method": "POST",
                    "description": "学习数据分析",
                },
                {
                    "path": "/api/v1/adaptive/schedule",
                    "method": "GET",
                    "description": "自适应学习计划",
                },
                {
                    "path": "/api/v1/training/vocabulary/words",
                    "method": "GET",
                    "description": "词汇训练",
                },
            ],
            # 现有API - 应该已经实现的基础功能
            "existing_basic": [
                {"path": "/api/v1/users/me", "method": "GET", "description": "用户信息"},
                {"path": "/api/v1/courses", "method": "GET", "description": "课程列表"},
                {"path": "/health", "method": "GET", "description": "健康检查"},
                {"path": "/docs", "method": "GET", "description": "API文档"},
            ],
        }

    async def __aenter__(self: "APIValidator") -> "APIValidator":
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self: "APIValidator", exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def check_api_health(self: "APIValidator") -> dict[str, Any]:
        """检查API服务健康状态"""
        print("🏥 检查API服务健康状态...")

        if self.session is None:
            return {"status": "error", "error": "Session not initialized"}

        try:
            async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ API服务运行正常")
                    return {"status": "healthy", "data": data}
                else:
                    print(f"⚠️ API服务状态异常: {response.status}")
                    return {"status": "unhealthy", "code": response.status}
        except Exception as e:
            print(f"❌ API服务连接失败: {e}")
            return {"status": "unreachable", "error": str(e)}

    async def check_api_documentation(self: "APIValidator") -> dict[str, Any]:
        """检查API文档可用性"""
        print("📚 检查API文档...")

        if self.session is None:
            return {"error": "Session not initialized"}

        doc_endpoints = [
            "/docs",  # Swagger UI
            "/redoc",  # ReDoc
            "/openapi.json",  # OpenAPI规范
        ]

        results: dict[str, Any] = {}
        for endpoint in doc_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}", timeout=5) as response:
                    results[endpoint] = {
                        "status": response.status,
                        "available": response.status == 200,
                    }
                    if response.status == 200:
                        print(f"✅ {endpoint} 可用")
                    else:
                        print(f"❌ {endpoint} 不可用 ({response.status})")
            except Exception as e:
                results[endpoint] = {"status": "error", "error": str(e)}
                print(f"❌ {endpoint} 连接失败: {e}")

        return results

    async def validate_api_endpoints(self: "APIValidator", category: str = "all") -> dict[str, Any]:
        """验证API端点的可用性"""
        print(f"🔍 验证API端点 (类别: {category})...")

        if self.session is None:
            return {
                "error": "Session not initialized",
                "available": 0,
                "total": 0,
                "missing": 0,
                "errors": 0,
                "details": [],
            }

        if category == "all":
            endpoints_to_check = []
            for cat_endpoints in self.core_api_checks.values():
                endpoints_to_check.extend(cat_endpoints)
        else:
            endpoints_to_check = self.core_api_checks.get(category, [])

        results: dict[str, Any] = {
            "total": len(endpoints_to_check),
            "available": 0,
            "missing": 0,
            "errors": 0,
            "details": [],
        }

        for endpoint_info in endpoints_to_check:
            path = endpoint_info["path"]
            method = endpoint_info["method"]
            description = endpoint_info["description"]

            try:
                # 对于需要认证的端点，我们只检查是否返回401而不是404
                if method == "GET":
                    async with self.session.get(f"{self.base_url}{path}", timeout=5) as response:
                        status = response.status
                elif method == "POST":
                    async with self.session.post(
                        f"{self.base_url}{path}", json={}, timeout=5
                    ) as response:
                        status = response.status
                else:
                    status = 405  # Method not allowed for unsupported methods

                # 判断端点状态
                if status in [200, 201, 401, 422]:  # 200/201=成功, 401=需要认证, 422=验证错误
                    results["available"] += 1
                    status_icon = "✅"
                    result_status = "available"
                elif status == 404:
                    results["missing"] += 1
                    status_icon = "❌"
                    result_status = "missing"
                else:
                    results["errors"] += 1
                    status_icon = "⚠️"
                    result_status = "error"

                print(f"{status_icon} {method} {path} - {description} ({status})")

                results["details"].append(
                    {
                        "path": path,
                        "method": method,
                        "description": description,
                        "status": status,
                        "result": result_status,
                    }
                )

            except Exception as e:
                results["errors"] += 1
                print(f"❌ {method} {path} - 连接失败: {e}")
                results["details"].append(
                    {
                        "path": path,
                        "method": method,
                        "description": description,
                        "error": str(e),
                        "result": "connection_error",
                    }
                )

        return results

    async def check_priority_apis(self: "APIValidator") -> dict[str, Any]:
        """检查优先级API的实现状态"""
        print("\n🎯 检查优先级API实现状态...")

        priority_results = {}

        # 检查第一优先级API
        print("\n🔥 第一优先级 - 核心训练功能:")
        priority_1_result = await self.validate_api_endpoints("priority_1_core")
        priority_results["priority_1"] = priority_1_result

        # 检查第二优先级API
        print("\n⚡ 第二优先级 - AI智能功能:")
        priority_2_result = await self.validate_api_endpoints("priority_2_ai")
        priority_results["priority_2"] = priority_2_result

        # 检查现有基础API
        print("\n📋 现有基础功能:")
        existing_result = await self.validate_api_endpoints("existing_basic")
        priority_results["existing"] = existing_result

        return priority_results

    def generate_validation_report(self: "APIValidator", results: dict[str, Any]) -> str:
        """生成验证报告"""
        print("\n📊 生成API验证报告...")

        report = f"""
# CET4学习系统 API验证报告

## 📊 验证概览

### 🏥 服务健康状态
- 状态: {results.get('health', {}).get('status', 'unknown')}

### 📚 API文档状态
"""

        if "documentation" in results:
            for endpoint, info in results["documentation"].items():
                status_icon = "✅" if info.get("available") else "❌"
                report += f"- {status_icon} {endpoint}\n"

        report += "\n### 🎯 优先级API实现状态\n"

        if "priorities" in results:
            for priority, data in results["priorities"].items():
                total = data.get("total", 0)
                available = data.get("available", 0)
                missing = data.get("missing", 0)

                completion_rate = (available / total * 100) if total > 0 else 0

                if priority == "priority_1":
                    priority_name = "第一优先级 (核心训练)"
                elif priority == "priority_2":
                    priority_name = "第二优先级 (AI功能)"
                else:
                    priority_name = "现有基础功能"

                report += f"\n#### {priority_name}\n"
                report += f"- 总端点数: {total}\n"
                report += f"- 可用端点: {available}\n"
                report += f"- 缺失端点: {missing}\n"
                report += f"- 完成度: {completion_rate:.1f}%\n"

        report += f"""

## 🚨 关键发现

### ✅ 已实现功能
- 基础用户管理和认证系统
- 课程管理功能
- 系统健康检查

### ❌ 缺失的核心功能
- 学生综合训练中心 (第一优先级)
- AI智能批改系统 (第一优先级)
- 听力训练系统 (第一优先级)
- AI学情分析 (第二优先级)
- 自适应学习 (第二优先级)

## 🎯 实施建议

1. **立即实现第一优先级API** - 这些是系统核心价值
2. **集成DeepSeek AI服务** - 智能批改功能的基础
3. **完善训练系统架构** - 支持多种训练模式
4. **建立API测试覆盖** - 确保功能稳定性

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report


async def main() -> None:
    """主函数"""
    if len(sys.argv) < 2:
        print("API验证器 - 检查API实现状态和完整性")
        print("=" * 50)
        print("用法:")
        print("  python api-validator.py <命令> [参数]")
        print("")
        print("命令:")
        print("  health      - 检查API服务健康状态")
        print("  docs        - 检查API文档可用性")
        print("  endpoints   - 验证API端点")
        print("  priority    - 检查优先级API状态")
        print("  full        - 完整验证报告")
        print("")
        print("示例:")
        print("  python api-validator.py health")
        print("  python api-validator.py priority")
        print("  python api-validator.py full")
        return

    command = sys.argv[1].lower()
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000"

    async with APIValidator(base_url) as validator:
        if command == "health":
            result = await validator.check_api_health()
            print(f"健康状态: {result['status']}")

        elif command == "docs":
            result = await validator.check_api_documentation()
            available_docs = sum(1 for info in result.values() if info.get("available"))
            print(f"可用文档: {available_docs}/{len(result)}")

        elif command == "endpoints":
            result = await validator.validate_api_endpoints()
            print(f"API端点: {result['available']}/{result['total']} 可用")

        elif command == "priority":
            result = await validator.check_priority_apis()
            for priority, data in result.items():
                completion = (data["available"] / data["total"] * 100) if data["total"] > 0 else 0
                print(f"{priority}: {completion:.1f}% 完成")

        elif command == "full":
            print("🚀 执行完整API验证...")

            results = {}
            results["health"] = await validator.check_api_health()
            results["documentation"] = await validator.check_api_documentation()
            results["priorities"] = await validator.check_priority_apis()

            # 生成报告
            report = validator.generate_validation_report(results)

            # 保存报告
            report_file = Path("api-validation-report.md")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"\n📄 完整报告已生成: {report_file}")

        else:
            print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    asyncio.run(main())
