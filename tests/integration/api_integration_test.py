"""
英语四级学习系统 - API集成测试

测试各个API模块之间的集成，确保：
- API端点正确响应
- 数据流转正常
- 错误处理正确
- 认证授权有效
"""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from tests.fixtures.mock_services import get_mock_patches, reset_all_mocks
from tests.fixtures.test_data import get_test_user


class TestAPIIntegration:
    """API集成测试"""

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
    async def test_users(self, client: AsyncClient):
        """创建测试用户"""
        users = {}

        # 创建不同角色的用户
        for role in ["admin", "teacher", "student"]:
            user_data = get_test_user(role)
            user_data["username"] = f"test_{role}"
            user_data["email"] = f"test_{role}@test.com"

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
            users[role] = {
                "user_data": user_data,
                "token": token_data["access_token"],
                "user_id": register_response.json()["user_id"],
            }

        return users

    async def test_authentication_flow_integration(self, client: AsyncClient):
        """测试认证流程集成"""
        # 1. 用户注册
        user_data = get_test_user("student")
        register_response = await client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        register_result = register_response.json()
        user_id = register_result["user_id"]

        # 2. 邮箱验证（模拟）
        verification_response = await client.post(
            "/api/v1/auth/verify-email",
            json={"user_id": user_id, "verification_code": "123456"},
        )
        assert verification_response.status_code == status.HTTP_200_OK

        # 3. 用户登录
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"],
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        token_data = login_response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]

        # 4. 使用访问令牌访问受保护资源
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get(
            f"/api/v1/users/{user_id}/profile", headers=headers
        )
        assert profile_response.status_code == status.HTTP_200_OK

        # 5. 刷新令牌
        refresh_response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == status.HTTP_200_OK

        # 6. 登出
        logout_response = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK

        # 7. 验证令牌已失效
        invalid_access_response = await client.get(
            f"/api/v1/users/{user_id}/profile", headers=headers
        )
        assert invalid_access_response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_learning_workflow_integration(
        self, client: AsyncClient, test_users: dict[str, Any]
    ):
        """测试学习工作流集成"""
        student = test_users["student"]
        headers = {"Authorization": f"Bearer {student['token']}"}

        # 1. 获取推荐学习内容
        recommended_response = await client.get(
            "/api/v1/learning/recommended", headers=headers
        )
        assert recommended_response.status_code == status.HTTP_200_OK
        recommended_content = recommended_response.json()

        # 2. 选择学习内容并开始学习会话
        if recommended_content["items"]:
            content_id = recommended_content["items"][0]["id"]

            session_data = {"content_id": content_id, "learning_mode": "practice"}

            session_response = await client.post(
                "/api/v1/learning/sessions", json=session_data, headers=headers
            )
            assert session_response.status_code == status.HTTP_201_CREATED
            session = session_response.json()
            session_id = session["session_id"]

            # 3. 获取学习任务
            tasks_response = await client.get(
                f"/api/v1/learning/sessions/{session_id}/tasks", headers=headers
            )
            assert tasks_response.status_code == status.HTTP_200_OK
            tasks = tasks_response.json()

            # 4. 提交答案
            if tasks["items"]:
                task_id = tasks["items"][0]["task_id"]
                answer_data = {
                    "answers": [{"question_id": 1, "answer": "A", "time_spent": 30}]
                }

                submit_response = await client.post(
                    f"/api/v1/learning/sessions/{session_id}/tasks/{task_id}/submit",
                    json=answer_data,
                    headers=headers,
                )
                assert submit_response.status_code == status.HTTP_200_OK

            # 5. 完成学习会话
            complete_response = await client.post(
                f"/api/v1/learning/sessions/{session_id}/complete", headers=headers
            )
            assert complete_response.status_code == status.HTTP_200_OK

            # 6. 查看学习进度更新
            progress_response = await client.get(
                f"/api/v1/users/{student['user_id']}/progress", headers=headers
            )
            assert progress_response.status_code == status.HTTP_200_OK
            progress = progress_response.json()
            assert progress["sessions_completed"] > 0

    async def test_content_management_integration(
        self, client: AsyncClient, test_users: dict[str, Any]
    ):
        """测试内容管理集成"""
        teacher = test_users["teacher"]
        admin = test_users["admin"]

        teacher_headers = {"Authorization": f"Bearer {teacher['token']}"}
        admin_headers = {"Authorization": f"Bearer {admin['token']}"}

        # 1. 教师创建内容
        content_data = {
            "title": "集成测试词汇课程",
            "description": "用于集成测试的词汇课程",
            "content_type": "vocabulary",
            "difficulty_level": "intermediate",
            "estimated_duration": 30,
            "tags": ["test", "vocabulary"],
            "content_data": {
                "words": [
                    {
                        "word": "integration",
                        "meaning": "集成，整合",
                        "example": "System integration is important.",
                    }
                ]
            },
        }

        create_response = await client.post(
            "/api/v1/teacher/content", json=content_data, headers=teacher_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        content = create_response.json()
        content_id = content["content_id"]

        # 2. 管理员审核内容
        review_data = {"status": "approved", "review_notes": "内容质量良好"}

        review_response = await client.post(
            f"/api/v1/admin/content/{content_id}/review",
            json=review_data,
            headers=admin_headers,
        )
        assert review_response.status_code == status.HTTP_200_OK

        # 3. 发布内容
        publish_response = await client.post(
            f"/api/v1/teacher/content/{content_id}/publish", headers=teacher_headers
        )
        assert publish_response.status_code == status.HTTP_200_OK

        # 4. 学生可以看到发布的内容
        student = test_users["student"]
        student_headers = {"Authorization": f"Bearer {student['token']}"}

        content_list_response = await client.get(
            "/api/v1/learning/content",
            params={"content_type": "vocabulary"},
            headers=student_headers,
        )
        assert content_list_response.status_code == status.HTTP_200_OK
        content_list = content_list_response.json()

        # 验证创建的内容在列表中
        content_ids = [item["id"] for item in content_list["items"]]
        assert content_id in content_ids

    async def test_user_management_integration(
        self, client: AsyncClient, test_users: dict[str, Any]
    ):
        """测试用户管理集成"""
        admin = test_users["admin"]
        admin_headers = {"Authorization": f"Bearer {admin['token']}"}

        # 1. 管理员创建新用户
        new_user_data = {
            "username": "integration_test_user",
            "email": "integration_test@test.com",
            "password": "TestPassword123!",
            "full_name": "Integration Test User",
            "role": "student",
        }

        create_user_response = await client.post(
            "/api/v1/admin/users", json=new_user_data, headers=admin_headers
        )
        assert create_user_response.status_code == status.HTTP_201_CREATED
        created_user = create_user_response.json()
        user_id = created_user["user_id"]

        # 2. 新用户可以登录
        login_data = {
            "username": new_user_data["username"],
            "password": new_user_data["password"],
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        # 3. 管理员更新用户信息
        update_data = {"full_name": "Updated Integration Test User", "is_active": True}

        update_response = await client.put(
            f"/api/v1/admin/users/{user_id}", json=update_data, headers=admin_headers
        )
        assert update_response.status_code == status.HTTP_200_OK

        # 4. 验证更新生效
        user_detail_response = await client.get(
            f"/api/v1/admin/users/{user_id}", headers=admin_headers
        )
        assert user_detail_response.status_code == status.HTTP_200_OK
        user_detail = user_detail_response.json()
        assert user_detail["full_name"] == "Updated Integration Test User"

    async def test_social_features_integration(
        self, client: AsyncClient, test_users: dict[str, Any]
    ):
        """测试社交功能集成"""
        student1 = test_users["student"]
        headers1 = {"Authorization": f"Bearer {student1['token']}"}

        # 创建第二个学生用户
        user2_data = get_test_user("student")
        user2_data["username"] = "student2"
        user2_data["email"] = "student2@test.com"

        register_response = await client.post("/api/v1/auth/register", json=user2_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": user2_data["username"],
                "password": user2_data["password"],
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        student2_token = login_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {student2_token}"}

        # 1. 学生1创建学习小组
        group_data = {
            "name": "集成测试学习小组",
            "description": "用于测试的学习小组",
            "is_public": True,
        }

        group_response = await client.post(
            "/api/v1/social/groups", json=group_data, headers=headers1
        )
        assert group_response.status_code == status.HTTP_201_CREATED
        group = group_response.json()
        group_id = group["group_id"]

        # 2. 学生2加入小组
        join_response = await client.post(
            f"/api/v1/social/groups/{group_id}/join", headers=headers2
        )
        assert join_response.status_code == status.HTTP_200_OK

        # 3. 学生1发布动态
        post_data = {
            "content": "今天学习了新的词汇！",
            "type": "achievement",
            "visibility": "public",
        }

        post_response = await client.post(
            "/api/v1/social/posts", json=post_data, headers=headers1
        )
        assert post_response.status_code == status.HTTP_201_CREATED
        post = post_response.json()
        post_id = post["post_id"]

        # 4. 学生2点赞和评论
        like_response = await client.post(
            f"/api/v1/social/posts/{post_id}/like", headers=headers2
        )
        assert like_response.status_code == status.HTTP_200_OK

        comment_data = {"content": "太棒了！继续加油！"}
        comment_response = await client.post(
            f"/api/v1/social/posts/{post_id}/comments",
            json=comment_data,
            headers=headers2,
        )
        assert comment_response.status_code == status.HTTP_201_CREATED

        # 5. 验证社交互动数据
        post_detail_response = await client.get(
            f"/api/v1/social/posts/{post_id}", headers=headers1
        )
        assert post_detail_response.status_code == status.HTTP_200_OK
        post_detail = post_detail_response.json()
        assert post_detail["like_count"] > 0
        assert post_detail["comment_count"] > 0

    async def test_error_handling_integration(
        self, client: AsyncClient, test_users: dict[str, Any]
    ):
        """测试错误处理集成"""
        student = test_users["student"]
        headers = {"Authorization": f"Bearer {student['token']}"}

        # 1. 测试404错误
        not_found_response = await client.get(
            "/api/v1/learning/content/99999", headers=headers
        )
        assert not_found_response.status_code == status.HTTP_404_NOT_FOUND
        error_data = not_found_response.json()
        assert "detail" in error_data

        # 2. 测试400错误（无效数据）
        invalid_session_data = {
            "content_id": "invalid",  # 应该是数字
            "learning_mode": "invalid_mode",
        }

        bad_request_response = await client.post(
            "/api/v1/learning/sessions", json=invalid_session_data, headers=headers
        )
        assert bad_request_response.status_code == status.HTTP_400_BAD_REQUEST

        # 3. 测试401错误（未认证）
        unauthorized_response = await client.get("/api/v1/users/1/profile")
        assert unauthorized_response.status_code == status.HTTP_401_UNAUTHORIZED

        # 4. 测试403错误（权限不足）
        # 学生尝试访问管理员功能
        forbidden_response = await client.get("/api/v1/admin/users", headers=headers)
        assert forbidden_response.status_code == status.HTTP_403_FORBIDDEN

    async def test_data_consistency_integration(
        self, client: AsyncClient, test_users: dict[str, Any]
    ):
        """测试数据一致性集成"""
        student = test_users["student"]
        headers = {"Authorization": f"Bearer {student['token']}"}
        user_id = student["user_id"]

        # 1. 获取初始进度
        initial_progress_response = await client.get(
            f"/api/v1/users/{user_id}/progress", headers=headers
        )
        assert initial_progress_response.status_code == status.HTTP_200_OK
        initial_progress = initial_progress_response.json()
        initial_sessions = initial_progress["sessions_completed"]

        # 2. 完成一个学习会话
        session_data = {"content_id": 1, "learning_mode": "practice"}

        session_response = await client.post(
            "/api/v1/learning/sessions", json=session_data, headers=headers
        )
        assert session_response.status_code == status.HTTP_201_CREATED
        session = session_response.json()
        session_id = session["session_id"]

        # 完成会话
        complete_response = await client.post(
            f"/api/v1/learning/sessions/{session_id}/complete", headers=headers
        )
        assert complete_response.status_code == status.HTTP_200_OK

        # 3. 验证进度更新
        updated_progress_response = await client.get(
            f"/api/v1/users/{user_id}/progress", headers=headers
        )
        assert updated_progress_response.status_code == status.HTTP_200_OK
        updated_progress = updated_progress_response.json()

        # 验证会话计数增加
        assert updated_progress["sessions_completed"] == initial_sessions + 1

        # 4. 验证学习历史记录
        history_response = await client.get(
            f"/api/v1/users/{user_id}/learning-history", headers=headers
        )
        assert history_response.status_code == status.HTTP_200_OK
        history = history_response.json()

        # 验证历史记录包含新完成的会话
        session_ids = [session["session_id"] for session in history["sessions"]]
        assert session_id in session_ids
