"""
英语四级学习系统 - 管理员功能端到端测试

测试管理员的完整管理流程，包括：
- 用户管理
- 内容管理
- 系统配置
- 数据分析和报表
- 系统监控
"""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from tests.fixtures.mock_services import get_mock_patches, reset_all_mocks
from tests.fixtures.test_data import get_test_user


class TestAdminWorkflow:
    """管理员功能端到端测试"""

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
    async def admin_user_data(self):
        """管理员用户数据"""
        return get_test_user("admin")

    @pytest.fixture
    async def authenticated_admin(
        self, client: AsyncClient, admin_user_data: dict[str, Any]
    ):
        """已认证的管理员用户"""
        # 注册管理员用户
        register_response = await client.post(
            "/api/v1/auth/register", json=admin_user_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # 登录获取token
        login_data = {
            "username": admin_user_data["username"],
            "password": admin_user_data["password"],
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        token_data = login_response.json()
        access_token = token_data["access_token"]

        # 设置认证头
        client.headers.update({"Authorization": f"Bearer {access_token}"})

        return {
            "user_data": admin_user_data,
            "token": access_token,
            "user_id": register_response.json()["user_id"],
        }

    async def test_complete_admin_workflow(
        self, client: AsyncClient, authenticated_admin: dict[str, Any]
    ):
        """测试完整的管理员工作流"""
        # 1. 用户管理
        await self._test_user_management(client)

        # 2. 内容管理
        await self._test_content_management(client)

        # 3. 系统配置
        await self._test_system_configuration(client)

        # 4. 数据分析和报表
        await self._test_analytics_and_reports(client)

        # 5. 系统监控
        await self._test_system_monitoring(client)

    async def _test_user_management(self, client: AsyncClient):
        """测试用户管理功能"""
        # 获取用户列表
        users_response = await client.get("/api/v1/admin/users", params={"limit": 50})
        assert users_response.status_code == status.HTTP_200_OK
        users = users_response.json()
        assert "items" in users
        assert "total" in users

        # 搜索用户
        search_response = await client.get(
            "/api/v1/admin/users/search", params={"query": "test", "role": "student"}
        )
        assert search_response.status_code == status.HTTP_200_OK

        # 创建新用户
        new_user_data = {
            "username": "admin_created_user",
            "email": "admin_created@test.com",
            "password": "TempPassword123!",
            "full_name": "Admin Created User",
            "role": "student",
        }

        create_user_response = await client.post(
            "/api/v1/admin/users", json=new_user_data
        )
        assert create_user_response.status_code == status.HTTP_201_CREATED
        created_user = create_user_response.json()
        user_id = created_user["user_id"]

        # 更新用户信息
        update_data = {
            "full_name": "Updated User Name",
            "is_active": True,
            "role": "student",
        }

        update_response = await client.put(
            f"/api/v1/admin/users/{user_id}", json=update_data
        )
        assert update_response.status_code == status.HTTP_200_OK

        # 重置用户密码
        reset_password_response = await client.post(
            f"/api/v1/admin/users/{user_id}/reset-password"
        )
        assert reset_password_response.status_code == status.HTTP_200_OK

        # 禁用/启用用户
        disable_response = await client.post(f"/api/v1/admin/users/{user_id}/disable")
        assert disable_response.status_code == status.HTTP_200_OK

        enable_response = await client.post(f"/api/v1/admin/users/{user_id}/enable")
        assert enable_response.status_code == status.HTTP_200_OK

        # 获取用户详细信息
        user_detail_response = await client.get(f"/api/v1/admin/users/{user_id}")
        assert user_detail_response.status_code == status.HTTP_200_OK
        user_detail = user_detail_response.json()
        assert user_detail["full_name"] == "Updated User Name"

    async def _test_content_management(self, client: AsyncClient):
        """测试内容管理功能"""
        # 获取内容列表
        content_response = await client.get(
            "/api/v1/admin/content", params={"limit": 20}
        )
        assert content_response.status_code == status.HTTP_200_OK
        content_list = content_response.json()

        # 创建新的学习内容
        new_content_data = {
            "title": "管理员创建的词汇课程",
            "description": "这是一个测试词汇课程",
            "content_type": "vocabulary",
            "difficulty_level": "intermediate",
            "estimated_duration": 30,
            "tags": ["test", "vocabulary", "intermediate"],
            "content_data": {
                "words": [
                    {
                        "word": "administration",
                        "meaning": "管理，行政",
                        "example": "The administration of the company is very efficient.",
                    }
                ]
            },
        }

        create_content_response = await client.post(
            "/api/v1/admin/content", json=new_content_data
        )
        assert create_content_response.status_code == status.HTTP_201_CREATED
        created_content = create_content_response.json()
        content_id = created_content["content_id"]

        # 更新内容
        update_content_data = {
            "title": "更新后的词汇课程",
            "description": "更新后的描述",
            "is_published": True,
        }

        update_content_response = await client.put(
            f"/api/v1/admin/content/{content_id}", json=update_content_data
        )
        assert update_content_response.status_code == status.HTTP_200_OK

        # 审核内容
        review_data = {"status": "approved", "review_notes": "内容质量良好，批准发布"}

        review_response = await client.post(
            f"/api/v1/admin/content/{content_id}/review", json=review_data
        )
        assert review_response.status_code == status.HTTP_200_OK

        # 批量操作
        batch_data = {"content_ids": [content_id], "action": "publish"}

        batch_response = await client.post(
            "/api/v1/admin/content/batch", json=batch_data
        )
        assert batch_response.status_code == status.HTTP_200_OK

        # 删除内容
        delete_response = await client.delete(f"/api/v1/admin/content/{content_id}")
        assert delete_response.status_code == status.HTTP_200_OK

    async def _test_system_configuration(self, client: AsyncClient):
        """测试系统配置功能"""
        # 获取系统配置
        config_response = await client.get("/api/v1/admin/config")
        assert config_response.status_code == status.HTTP_200_OK
        config = config_response.json()

        # 更新系统配置
        config_update = {
            "site_name": "CET4学习系统",
            "max_concurrent_sessions": 3,
            "session_timeout": 3600,
            "email_notifications": True,
            "maintenance_mode": False,
            "features": {
                "ai_tutor": True,
                "social_learning": True,
                "gamification": True,
            },
        }

        update_config_response = await client.put(
            "/api/v1/admin/config", json=config_update
        )
        assert update_config_response.status_code == status.HTTP_200_OK

        # 管理AI服务配置
        ai_config_data = {
            "api_keys": ["test-key-1", "test-key-2"],
            "model_settings": {"temperature": 0.7, "max_tokens": 2000},
            "rate_limits": {"requests_per_minute": 60, "requests_per_hour": 1000},
        }

        ai_config_response = await client.put(
            "/api/v1/admin/config/ai", json=ai_config_data
        )
        assert ai_config_response.status_code == status.HTTP_200_OK

        # 配置邮件服务
        email_config_data = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test@test.com",
            "use_tls": True,
            "from_email": "noreply@cet4learning.com",
        }

        email_config_response = await client.put(
            "/api/v1/admin/config/email", json=email_config_data
        )
        assert email_config_response.status_code == status.HTTP_200_OK

    async def _test_analytics_and_reports(self, client: AsyncClient):
        """测试数据分析和报表功能"""
        # 获取系统统计概览
        stats_response = await client.get("/api/v1/admin/analytics/overview")
        assert stats_response.status_code == status.HTTP_200_OK
        stats = stats_response.json()

        assert "total_users" in stats
        assert "active_users" in stats
        assert "total_sessions" in stats
        assert "content_count" in stats

        # 获取用户活动分析
        user_activity_response = await client.get(
            "/api/v1/admin/analytics/user-activity", params={"period": "7d"}
        )
        assert user_activity_response.status_code == status.HTTP_200_OK
        user_activity = user_activity_response.json()

        # 获取学习效果分析
        effectiveness_response = await client.get(
            "/api/v1/admin/analytics/learning-effectiveness",
            params={"content_type": "vocabulary"},
        )
        assert effectiveness_response.status_code == status.HTTP_200_OK
        effectiveness = effectiveness_response.json()

        # 生成自定义报表
        report_data = {
            "report_type": "user_progress",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "filters": {"user_role": "student", "content_type": "vocabulary"},
            "output_format": "json",
        }

        report_response = await client.post(
            "/api/v1/admin/reports/generate", json=report_data
        )
        assert report_response.status_code == status.HTTP_201_CREATED
        report = report_response.json()
        assert "report_id" in report

        # 获取报表状态
        report_id = report["report_id"]
        report_status_response = await client.get(
            f"/api/v1/admin/reports/{report_id}/status"
        )
        assert report_status_response.status_code == status.HTTP_200_OK

        # 下载报表
        download_response = await client.get(
            f"/api/v1/admin/reports/{report_id}/download"
        )
        assert download_response.status_code == status.HTTP_200_OK

    async def _test_system_monitoring(self, client: AsyncClient):
        """测试系统监控功能"""
        # 获取系统健康状态
        health_response = await client.get("/api/v1/admin/monitoring/health")
        assert health_response.status_code == status.HTTP_200_OK
        health = health_response.json()

        assert "database" in health
        assert "redis" in health
        assert "ai_service" in health
        assert "storage" in health

        # 获取系统性能指标
        metrics_response = await client.get("/api/v1/admin/monitoring/metrics")
        assert metrics_response.status_code == status.HTTP_200_OK
        metrics = metrics_response.json()

        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "active_connections" in metrics
        assert "response_time" in metrics

        # 获取错误日志
        logs_response = await client.get(
            "/api/v1/admin/monitoring/logs", params={"level": "error", "limit": 50}
        )
        assert logs_response.status_code == status.HTTP_200_OK
        logs = logs_response.json()

        # 获取API使用统计
        api_stats_response = await client.get(
            "/api/v1/admin/monitoring/api-usage", params={"period": "24h"}
        )
        assert api_stats_response.status_code == status.HTTP_200_OK
        api_stats = api_stats_response.json()

        # 设置监控告警
        alert_data = {
            "name": "高CPU使用率告警",
            "metric": "cpu_usage",
            "threshold": 80,
            "operator": "greater_than",
            "notification_channels": ["email", "slack"],
        }

        alert_response = await client.post(
            "/api/v1/admin/monitoring/alerts", json=alert_data
        )
        assert alert_response.status_code == status.HTTP_201_CREATED

    async def test_admin_permissions_and_security(
        self, client: AsyncClient, authenticated_admin: dict[str, Any]
    ):
        """测试管理员权限和安全功能"""
        # 测试权限管理
        permissions_response = await client.get("/api/v1/admin/permissions")
        assert permissions_response.status_code == status.HTTP_200_OK

        # 测试角色管理
        roles_response = await client.get("/api/v1/admin/roles")
        assert roles_response.status_code == status.HTTP_200_OK

        # 创建新角色
        role_data = {
            "name": "content_moderator",
            "description": "内容审核员",
            "permissions": ["content.read", "content.review", "content.moderate"],
        }

        create_role_response = await client.post("/api/v1/admin/roles", json=role_data)
        assert create_role_response.status_code == status.HTTP_201_CREATED

        # 分配角色给用户
        assign_role_data = {"user_id": 1, "role_name": "content_moderator"}

        assign_response = await client.post(
            "/api/v1/admin/users/assign-role", json=assign_role_data
        )
        assert assign_response.status_code == status.HTTP_200_OK

        # 查看安全日志
        security_logs_response = await client.get(
            "/api/v1/admin/security/logs", params={"event_type": "login", "limit": 100}
        )
        assert security_logs_response.status_code == status.HTTP_200_OK

    async def test_data_backup_and_maintenance(
        self, client: AsyncClient, authenticated_admin: dict[str, Any]
    ):
        """测试数据备份和维护功能"""
        # 创建数据备份
        backup_data = {
            "backup_type": "full",
            "include_user_data": True,
            "include_content": True,
            "include_logs": False,
        }

        backup_response = await client.post(
            "/api/v1/admin/maintenance/backup", json=backup_data
        )
        assert backup_response.status_code == status.HTTP_201_CREATED
        backup = backup_response.json()
        backup_id = backup["backup_id"]

        # 获取备份状态
        backup_status_response = await client.get(
            f"/api/v1/admin/maintenance/backup/{backup_id}/status"
        )
        assert backup_status_response.status_code == status.HTTP_200_OK

        # 获取备份列表
        backups_response = await client.get("/api/v1/admin/maintenance/backups")
        assert backups_response.status_code == status.HTTP_200_OK

        # 数据库维护
        maintenance_data = {
            "operation": "optimize",
            "tables": ["users", "learning_sessions", "content"],
        }

        maintenance_response = await client.post(
            "/api/v1/admin/maintenance/database", json=maintenance_data
        )
        assert maintenance_response.status_code == status.HTTP_200_OK

        # 清理临时数据
        cleanup_response = await client.post("/api/v1/admin/maintenance/cleanup")
        assert cleanup_response.status_code == status.HTTP_200_OK

    async def test_admin_error_handling(
        self, client: AsyncClient, authenticated_admin: dict[str, Any]
    ):
        """测试管理员功能的错误处理"""
        # 测试访问不存在的用户
        invalid_user_response = await client.get("/api/v1/admin/users/99999")
        assert invalid_user_response.status_code == status.HTTP_404_NOT_FOUND

        # 测试无效的配置更新
        invalid_config = {
            "max_concurrent_sessions": -1,  # 无效值
            "session_timeout": "invalid",  # 无效类型
        }

        invalid_config_response = await client.put(
            "/api/v1/admin/config", json=invalid_config
        )
        assert invalid_config_response.status_code == status.HTTP_400_BAD_REQUEST

        # 测试权限不足的操作
        # 这里应该测试非管理员用户尝试访问管理员功能
        # 由于当前是管理员身份，这个测试需要在其他测试中实现
