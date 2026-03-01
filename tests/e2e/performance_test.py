"""
英语四级学习系统 - 性能压力测试

测试系统在高负载下的性能表现，包括：
- 并发用户访问测试
- API响应时间测试
- 数据库性能测试
- 内存和CPU使用率测试
- 系统稳定性测试
"""

import asyncio
import statistics
import time
from typing import Any

import psutil
import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from tests.fixtures.mock_services import get_mock_patches, reset_all_mocks
from tests.fixtures.test_data import get_test_user


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.cpu_usage = []
        self.memory_usage = []

    def add_response_time(self, response_time: float):
        """添加响应时间"""
        self.response_times.append(response_time)

    def add_error(self):
        """添加错误计数"""
        self.error_count += 1

    def add_success(self):
        """添加成功计数"""
        self.success_count += 1

    def start_monitoring(self):
        """开始监控"""
        self.start_time = time.time()

    def stop_monitoring(self):
        """停止监控"""
        self.end_time = time.time()

    def record_system_metrics(self):
        """记录系统指标"""
        self.cpu_usage.append(psutil.cpu_percent())
        self.memory_usage.append(psutil.virtual_memory().percent)

    def get_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        total_requests = self.success_count + self.error_count
        duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )

        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate": (
                self.error_count / total_requests if total_requests > 0 else 0
            ),
            "duration": duration,
            "requests_per_second": total_requests / duration if duration > 0 else 0,
            "response_times": {
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
                "avg": (
                    statistics.mean(self.response_times) if self.response_times else 0
                ),
                "median": (
                    statistics.median(self.response_times) if self.response_times else 0
                ),
                "p95": (
                    statistics.quantiles(self.response_times, n=20)[18]
                    if len(self.response_times) >= 20
                    else 0
                ),
                "p99": (
                    statistics.quantiles(self.response_times, n=100)[98]
                    if len(self.response_times) >= 100
                    else 0
                ),
            },
            "system_metrics": {
                "avg_cpu_usage": (
                    statistics.mean(self.cpu_usage) if self.cpu_usage else 0
                ),
                "max_cpu_usage": max(self.cpu_usage) if self.cpu_usage else 0,
                "avg_memory_usage": (
                    statistics.mean(self.memory_usage) if self.memory_usage else 0
                ),
                "max_memory_usage": max(self.memory_usage) if self.memory_usage else 0,
            },
        }


class TestPerformance:
    """性能测试类"""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """测试前后的设置和清理"""
        reset_all_mocks()

        self.mock_patches = get_mock_patches()
        for patch in self.mock_patches:
            patch.start()

        yield

        for patch in self.mock_patches:
            patch.stop()

    @pytest.fixture
    async def client(self):
        """异步HTTP客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def authenticated_users(self, client: AsyncClient):
        """创建多个已认证用户"""
        users = []

        for i in range(10):  # 创建10个测试用户
            user_data = get_test_user("student")
            user_data["username"] = f"test_user_{i}"
            user_data["email"] = f"test_user_{i}@test.com"

            # 注册用户
            register_response = await client.post(
                "/api/v1/auth/register", json=user_data
            )
            assert register_response.status_code == status.HTTP_201_CREATED

            # 登录获取token
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"],
            }
            login_response = await client.post("/api/v1/auth/login", data=login_data)
            assert login_response.status_code == status.HTTP_200_OK

            token_data = login_response.json()
            users.append(
                {
                    "user_data": user_data,
                    "token": token_data["access_token"],
                    "user_id": register_response.json()["user_id"],
                }
            )

        return users

    async def test_concurrent_user_load(
        self, authenticated_users: list[dict[str, Any]]
    ):
        """测试并发用户负载"""
        metrics = PerformanceMetrics()
        metrics.start_monitoring()

        # 并发用户数量配置
        concurrent_users = [10, 50, 100, 200]

        for user_count in concurrent_users:
            print(f"\n测试 {user_count} 个并发用户...")

            # 创建并发任务
            tasks = []
            for i in range(user_count):
                user = authenticated_users[i % len(authenticated_users)]
                task = self._simulate_user_session(user, metrics)
                tasks.append(task)

            # 执行并发任务
            start_time = time.time()
            await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # 记录系统指标
            metrics.record_system_metrics()

            print(
                f"完成 {user_count} 个并发用户测试，耗时: {end_time - start_time:.2f}秒"
            )

        metrics.stop_monitoring()

        # 验证性能指标
        summary = metrics.get_summary()
        print("\n性能测试摘要:")
        print(f"总请求数: {summary['total_requests']}")
        print(f"成功率: {(1 - summary['error_rate']) * 100:.2f}%")
        print(f"平均响应时间: {summary['response_times']['avg']:.3f}秒")
        print(f"95%响应时间: {summary['response_times']['p95']:.3f}秒")
        print(f"QPS: {summary['requests_per_second']:.2f}")

        # 性能断言
        assert summary["error_rate"] < 0.05  # 错误率小于5%
        assert summary["response_times"]["avg"] < 2.0  # 平均响应时间小于2秒
        assert summary["response_times"]["p95"] < 5.0  # 95%响应时间小于5秒
        assert summary["system_metrics"]["avg_cpu_usage"] < 80  # 平均CPU使用率小于80%
        assert (
            summary["system_metrics"]["avg_memory_usage"] < 80
        )  # 平均内存使用率小于80%

    async def _simulate_user_session(
        self, user: dict[str, Any], metrics: PerformanceMetrics
    ):
        """模拟用户会话"""
        headers = {"Authorization": f"Bearer {user['token']}"}

        async with AsyncClient(
            app=app, base_url="http://test", headers=headers
        ) as client:
            try:
                # 1. 获取用户资料
                start_time = time.time()
                profile_response = await client.get(
                    f"/api/v1/users/{user['user_id']}/profile"
                )
                metrics.add_response_time(time.time() - start_time)

                if profile_response.status_code == 200:
                    metrics.add_success()
                else:
                    metrics.add_error()

                # 2. 浏览学习内容
                start_time = time.time()
                content_response = await client.get("/api/v1/learning/recommended")
                metrics.add_response_time(time.time() - start_time)

                if content_response.status_code == 200:
                    metrics.add_success()
                else:
                    metrics.add_error()

                # 3. 开始学习会话
                session_data = {"content_id": 1, "learning_mode": "practice"}

                start_time = time.time()
                session_response = await client.post(
                    "/api/v1/learning/sessions", json=session_data
                )
                metrics.add_response_time(time.time() - start_time)

                if session_response.status_code == 201:
                    metrics.add_success()
                else:
                    metrics.add_error()

                # 4. 查看学习进度
                start_time = time.time()
                progress_response = await client.get(
                    f"/api/v1/users/{user['user_id']}/progress"
                )
                metrics.add_response_time(time.time() - start_time)

                if progress_response.status_code == 200:
                    metrics.add_success()
                else:
                    metrics.add_error()

            except Exception as e:
                metrics.add_error()
                print(f"用户会话错误: {e}")

    async def test_api_response_time_benchmarks(
        self, authenticated_users: list[dict[str, Any]]
    ):
        """测试API响应时间基准"""
        user = authenticated_users[0]
        headers = {"Authorization": f"Bearer {user['token']}"}

        # 定义API端点和期望的响应时间
        api_benchmarks = [
            ("/api/v1/health", 0.1),  # 健康检查应该在100ms内
            ("/api/v1/learning/recommended", 0.5),  # 推荐内容应该在500ms内
            ("/api/v1/vocabulary/words", 0.3),  # 词汇列表应该在300ms内
            (f"/api/v1/users/{user['user_id']}/profile", 0.2),  # 用户资料应该在200ms内
            (f"/api/v1/users/{user['user_id']}/progress", 0.4),  # 学习进度应该在400ms内
        ]

        async with AsyncClient(
            app=app, base_url="http://test", headers=headers
        ) as client:
            for endpoint, expected_time in api_benchmarks:
                # 多次测试取平均值
                response_times = []

                for _ in range(10):
                    start_time = time.time()
                    response = await client.get(endpoint)
                    response_time = time.time() - start_time
                    response_times.append(response_time)

                    assert response.status_code in [
                        200,
                        201,
                    ], f"API {endpoint} 返回错误状态码"

                avg_response_time = statistics.mean(response_times)
                print(
                    f"API {endpoint}: 平均响应时间 {avg_response_time:.3f}秒 (期望 < {expected_time}秒)"
                )

                # 响应时间断言
                assert (
                    avg_response_time < expected_time
                ), f"API {endpoint} 响应时间超出预期"

    async def test_database_performance(
        self, authenticated_users: list[dict[str, Any]]
    ):
        """测试数据库性能"""
        user = authenticated_users[0]
        headers = {"Authorization": f"Bearer {user['token']}"}

        async with AsyncClient(
            app=app, base_url="http://test", headers=headers
        ) as client:
            # 测试大量数据查询
            start_time = time.time()
            large_query_response = await client.get(
                "/api/v1/vocabulary/words", params={"limit": 1000}  # 查询大量数据
            )
            query_time = time.time() - start_time

            assert large_query_response.status_code == 200
            assert query_time < 2.0, f"大量数据查询时间过长: {query_time:.3f}秒"

            # 测试复杂查询
            start_time = time.time()
            complex_query_response = await client.get(
                "/api/v1/learning/search",
                params={
                    "query": "vocabulary",
                    "difficulty": "intermediate",
                    "content_type": "vocabulary",
                    "limit": 50,
                },
            )
            complex_query_time = time.time() - start_time

            assert complex_query_response.status_code == 200
            assert (
                complex_query_time < 1.0
            ), f"复杂查询时间过长: {complex_query_time:.3f}秒"

    async def test_memory_leak_detection(
        self, authenticated_users: list[dict[str, Any]]
    ):
        """测试内存泄漏检测"""
        initial_memory = psutil.virtual_memory().percent

        # 执行大量操作
        for round_num in range(5):
            print(f"内存测试轮次 {round_num + 1}/5")

            tasks = []
            for user in authenticated_users:
                task = self._memory_intensive_operations(user)
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # 强制垃圾回收
            import gc

            gc.collect()

            current_memory = psutil.virtual_memory().percent
            memory_increase = current_memory - initial_memory

            print(f"内存使用率: {current_memory:.2f}% (增长: {memory_increase:.2f}%)")

            # 内存增长不应该超过20%
            assert (
                memory_increase < 20
            ), f"检测到可能的内存泄漏，内存增长: {memory_increase:.2f}%"

    async def _memory_intensive_operations(self, user: dict[str, Any]):
        """内存密集型操作"""
        headers = {"Authorization": f"Bearer {user['token']}"}

        async with AsyncClient(
            app=app, base_url="http://test", headers=headers
        ) as client:
            # 执行多种操作
            operations = [
                client.get("/api/v1/learning/recommended"),
                client.get("/api/v1/vocabulary/words", params={"limit": 100}),
                client.get(f"/api/v1/users/{user['user_id']}/progress"),
                client.get(f"/api/v1/users/{user['user_id']}/statistics"),
                client.post(
                    "/api/v1/learning/sessions",
                    json={"content_id": 1, "learning_mode": "practice"},
                ),
            ]

            await asyncio.gather(*operations, return_exceptions=True)

    async def test_stress_test_breaking_point(
        self, authenticated_users: list[dict[str, Any]]
    ):
        """压力测试 - 寻找系统极限"""
        print("\n开始压力测试，寻找系统极限...")

        # 逐步增加负载直到系统无法承受
        concurrent_levels = [50, 100, 200, 500, 1000]

        for level in concurrent_levels:
            print(f"\n测试并发级别: {level}")

            metrics = PerformanceMetrics()
            metrics.start_monitoring()

            # 创建高并发任务
            tasks = []
            for i in range(level):
                user = authenticated_users[i % len(authenticated_users)]
                task = self._stress_test_operation(user, metrics)
                tasks.append(task)

            try:
                # 设置超时时间
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=30.0
                )
            except TimeoutError:
                print(f"并发级别 {level} 超时，系统可能已达到极限")
                break

            metrics.stop_monitoring()
            summary = metrics.get_summary()

            print(f"错误率: {summary['error_rate'] * 100:.2f}%")
            print(f"平均响应时间: {summary['response_times']['avg']:.3f}秒")
            print(f"QPS: {summary['requests_per_second']:.2f}")

            # 如果错误率超过20%或响应时间超过10秒，认为达到极限
            if summary["error_rate"] > 0.2 or summary["response_times"]["avg"] > 10.0:
                print(f"系统在并发级别 {level} 达到极限")
                break

    async def _stress_test_operation(
        self, user: dict[str, Any], metrics: PerformanceMetrics
    ):
        """压力测试操作"""
        headers = {"Authorization": f"Bearer {user['token']}"}

        try:
            async with AsyncClient(
                app=app, base_url="http://test", headers=headers
            ) as client:
                start_time = time.time()
                response = await client.get("/api/v1/learning/recommended")
                response_time = time.time() - start_time

                metrics.add_response_time(response_time)

                if response.status_code == 200:
                    metrics.add_success()
                else:
                    metrics.add_error()

        except Exception:
            metrics.add_error()

    async def test_long_running_stability(
        self, authenticated_users: list[dict[str, Any]]
    ):
        """长时间运行稳定性测试"""
        print("\n开始长时间运行稳定性测试（5分钟）...")

        metrics = PerformanceMetrics()
        metrics.start_monitoring()

        end_time = time.time() + 300  # 运行5分钟

        while time.time() < end_time:
            # 创建适中的负载
            tasks = []
            for i in range(20):  # 20个并发用户
                user = authenticated_users[i % len(authenticated_users)]
                task = self._simulate_user_session(user, metrics)
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # 记录系统指标
            metrics.record_system_metrics()

            # 短暂休息
            await asyncio.sleep(1)

        metrics.stop_monitoring()
        summary = metrics.get_summary()

        print("\n长时间运行测试结果:")
        print(f"总运行时间: {summary['duration']:.2f}秒")
        print(f"总请求数: {summary['total_requests']}")
        print(f"错误率: {summary['error_rate'] * 100:.2f}%")
        print(f"平均响应时间: {summary['response_times']['avg']:.3f}秒")

        # 稳定性断言
        assert summary["error_rate"] < 0.02, "长时间运行错误率过高"
        assert summary["response_times"]["avg"] < 1.0, "长时间运行响应时间过长"
