"""
英语四级学习系统 - 学生功能端到端测试

测试学生从注册到完整学习流程的所有功能，包括：
- 用户注册和登录
- 个人资料设置
- 学习内容浏览和学习
- 进度跟踪和成就系统
- 社交学习功能
"""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from tests.fixtures.mock_services import get_mock_patches, reset_all_mocks
from tests.fixtures.test_data import get_test_user


class TestStudentWorkflow:
    """学生功能端到端测试"""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """测试前后的设置和清理"""
        # 重置所有Mock服务
        reset_all_mocks()

        # 应用Mock补丁
        self.mock_patches = get_mock_patches()
        for patch in self.mock_patches:
            patch.start()

        yield

        # 停止Mock补丁
        for patch in self.mock_patches:
            patch.stop()

    @pytest.fixture
    async def client(self):
        """异步HTTP客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def test_student_data(self):
        """测试学生数据"""
        return get_test_user("student")

    @pytest.fixture
    async def authenticated_student(
        self, client: AsyncClient, test_student_data: dict[str, Any]
    ):
        """已认证的学生用户"""
        # 注册用户
        register_response = await client.post(
            "/api/v1/auth/register", json=test_student_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # 登录获取token
        login_data = {
            "username": test_student_data["username"],
            "password": test_student_data["password"],
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        token_data = login_response.json()
        access_token = token_data["access_token"]

        # 设置认证头
        client.headers.update({"Authorization": f"Bearer {access_token}"})

        return {
            "user_data": test_student_data,
            "token": access_token,
            "user_id": register_response.json()["user_id"],
        }

    async def test_complete_student_learning_journey(
        self, client: AsyncClient, authenticated_student: dict[str, Any]
    ):
        """测试完整的学生学习旅程"""
        user_data = authenticated_student["user_data"]
        user_id = authenticated_student["user_id"]

        # 1. 完善个人资料
        await self._test_profile_setup(client, user_id)

        # 2. 浏览学习内容
        available_content = await self._test_browse_content(client)

        # 3. 开始学习会话
        learning_session = await self._test_start_learning_session(
            client, available_content[0]
        )

        # 4. 完成学习任务
        await self._test_complete_learning_tasks(client, learning_session)

        # 5. 查看学习进度
        await self._test_view_learning_progress(client, user_id)

        # 6. 参与社交学习
        await self._test_social_learning_features(client, user_id)

        # 7. 查看成就和排行榜
        await self._test_achievements_and_leaderboard(client, user_id)

    async def _test_profile_setup(self, client: AsyncClient, user_id: int):
        """测试个人资料设置"""
        # 获取当前资料
        profile_response = await client.get(f"/api/v1/users/{user_id}/profile")
        assert profile_response.status_code == status.HTTP_200_OK

        # 更新个人资料
        profile_update = {
            "target_score": 550,
            "current_score": 400,
            "study_time_per_day": 60,
            "preferred_study_time": "evening",
            "learning_goals": ["pass_cet4", "improve_speaking"],
        }

        update_response = await client.put(
            f"/api/v1/users/{user_id}/profile", json=profile_update
        )
        assert update_response.status_code == status.HTTP_200_OK

        # 验证更新结果
        updated_profile = update_response.json()
        assert updated_profile["target_score"] == 550
        assert "pass_cet4" in updated_profile["learning_goals"]

    async def _test_browse_content(self, client: AsyncClient) -> list[dict[str, Any]]:
        """测试浏览学习内容"""
        # 获取推荐内容
        recommended_response = await client.get("/api/v1/learning/recommended")
        assert recommended_response.status_code == status.HTTP_200_OK
        recommended_content = recommended_response.json()
        assert len(recommended_content) > 0

        # 按类型筛选内容
        vocabulary_response = await client.get(
            "/api/v1/learning/content",
            params={"content_type": "vocabulary", "limit": 10},
        )
        assert vocabulary_response.status_code == status.HTTP_200_OK
        vocabulary_content = vocabulary_response.json()

        # 搜索特定内容
        search_response = await client.get(
            "/api/v1/learning/search", params={"query": "basic vocabulary", "limit": 5}
        )
        assert search_response.status_code == status.HTTP_200_OK
        search_results = search_response.json()

        return recommended_content["items"]

    async def _test_start_learning_session(
        self, client: AsyncClient, content: dict[str, Any]
    ) -> dict[str, Any]:
        """测试开始学习会话"""
        content_id = content["id"]

        # 开始学习会话
        session_data = {"content_id": content_id, "learning_mode": "practice"}

        session_response = await client.post(
            "/api/v1/learning/sessions", json=session_data
        )
        assert session_response.status_code == status.HTTP_201_CREATED

        session = session_response.json()
        assert session["content_id"] == content_id
        assert session["status"] == "active"

        return session

    async def _test_complete_learning_tasks(
        self, client: AsyncClient, session: dict[str, Any]
    ):
        """测试完成学习任务"""
        session_id = session["session_id"]

        # 获取学习任务
        tasks_response = await client.get(
            f"/api/v1/learning/sessions/{session_id}/tasks"
        )
        assert tasks_response.status_code == status.HTTP_200_OK
        tasks = tasks_response.json()

        # 完成每个任务
        for task in tasks["items"]:
            task_id = task["task_id"]

            # 提交答案
            answer_data = {
                "answers": [
                    {"question_id": 1, "answer": "A", "time_spent": 30},
                    {"question_id": 2, "answer": "correct answer", "time_spent": 45},
                ]
            }

            submit_response = await client.post(
                f"/api/v1/learning/sessions/{session_id}/tasks/{task_id}/submit",
                json=answer_data,
            )
            assert submit_response.status_code == status.HTTP_200_OK

            # 获取反馈
            feedback_response = await client.get(
                f"/api/v1/learning/sessions/{session_id}/tasks/{task_id}/feedback"
            )
            assert feedback_response.status_code == status.HTTP_200_OK
            feedback = feedback_response.json()
            assert "score" in feedback
            assert "suggestions" in feedback

        # 完成学习会话
        complete_response = await client.post(
            f"/api/v1/learning/sessions/{session_id}/complete"
        )
        assert complete_response.status_code == status.HTTP_200_OK

        completion_data = complete_response.json()
        assert completion_data["status"] == "completed"
        assert "final_score" in completion_data

    async def _test_view_learning_progress(self, client: AsyncClient, user_id: int):
        """测试查看学习进度"""
        # 获取总体进度
        progress_response = await client.get(f"/api/v1/users/{user_id}/progress")
        assert progress_response.status_code == status.HTTP_200_OK
        progress = progress_response.json()

        assert "total_study_time" in progress
        assert "sessions_completed" in progress
        assert "average_score" in progress
        assert "learning_streak" in progress

        # 获取详细统计
        stats_response = await client.get(f"/api/v1/users/{user_id}/statistics")
        assert stats_response.status_code == status.HTTP_200_OK
        stats = stats_response.json()

        assert "daily_stats" in stats
        assert "weekly_stats" in stats
        assert "content_type_breakdown" in stats

        # 获取学习历史
        history_response = await client.get(
            f"/api/v1/users/{user_id}/learning-history", params={"limit": 20}
        )
        assert history_response.status_code == status.HTTP_200_OK
        history = history_response.json()
        assert "sessions" in history

    async def _test_social_learning_features(self, client: AsyncClient, user_id: int):
        """测试社交学习功能"""
        # 加入学习小组
        group_data = {
            "name": "CET4备考小组",
            "description": "一起备考CET4",
            "is_public": True,
        }

        group_response = await client.post("/api/v1/social/groups", json=group_data)
        assert group_response.status_code == status.HTTP_201_CREATED
        group = group_response.json()
        group_id = group["group_id"]

        # 发布学习动态
        post_data = {
            "content": "今天学习了50个新单词！",
            "type": "achievement",
            "visibility": "public",
        }

        post_response = await client.post("/api/v1/social/posts", json=post_data)
        assert post_response.status_code == status.HTTP_201_CREATED
        post = post_response.json()

        # 点赞和评论
        like_response = await client.post(
            f"/api/v1/social/posts/{post['post_id']}/like"
        )
        assert like_response.status_code == status.HTTP_200_OK

        comment_data = {"content": "太棒了！继续加油！"}
        comment_response = await client.post(
            f"/api/v1/social/posts/{post['post_id']}/comments", json=comment_data
        )
        assert comment_response.status_code == status.HTTP_201_CREATED

        # 参与讨论
        discussion_data = {
            "title": "如何提高听力水平？",
            "content": "大家有什么好的听力练习方法吗？",
            "tags": ["listening", "tips"],
        }

        discussion_response = await client.post(
            f"/api/v1/social/groups/{group_id}/discussions", json=discussion_data
        )
        assert discussion_response.status_code == status.HTTP_201_CREATED

    async def _test_achievements_and_leaderboard(
        self, client: AsyncClient, user_id: int
    ):
        """测试成就和排行榜功能"""
        # 获取用户成就
        achievements_response = await client.get(
            f"/api/v1/users/{user_id}/achievements"
        )
        assert achievements_response.status_code == status.HTTP_200_OK
        achievements = achievements_response.json()

        assert "unlocked" in achievements
        assert "available" in achievements
        assert "total_points" in achievements

        # 查看排行榜
        leaderboard_response = await client.get("/api/v1/leaderboard")
        assert leaderboard_response.status_code == status.HTTP_200_OK
        leaderboard = leaderboard_response.json()

        assert "daily" in leaderboard
        assert "weekly" in leaderboard
        assert "monthly" in leaderboard

        # 查看个人排名
        ranking_response = await client.get(f"/api/v1/users/{user_id}/ranking")
        assert ranking_response.status_code == status.HTTP_200_OK
        ranking = ranking_response.json()

        assert "current_rank" in ranking
        assert "total_users" in ranking
        assert "percentile" in ranking

    async def test_vocabulary_learning_workflow(
        self, client: AsyncClient, authenticated_student: dict[str, Any]
    ):
        """测试词汇学习工作流"""
        # 获取词汇列表
        vocab_response = await client.get(
            "/api/v1/vocabulary/words", params={"limit": 20}
        )
        assert vocab_response.status_code == status.HTTP_200_OK
        words = vocab_response.json()

        # 开始词汇练习
        practice_data = {
            "word_ids": [word["word_id"] for word in words["items"][:10]],
            "practice_type": "recognition",
        }

        practice_response = await client.post(
            "/api/v1/vocabulary/practice", json=practice_data
        )
        assert practice_response.status_code == status.HTTP_201_CREATED
        practice_session = practice_response.json()

        # 完成词汇练习
        session_id = practice_session["session_id"]
        answers = [
            {"word_id": word["word_id"], "answer": "correct", "confidence": 0.8}
            for word in words["items"][:10]
        ]

        submit_response = await client.post(
            f"/api/v1/vocabulary/practice/{session_id}/submit",
            json={"answers": answers},
        )
        assert submit_response.status_code == status.HTTP_200_OK

        result = submit_response.json()
        assert "score" in result
        assert "mastered_words" in result
        assert "review_words" in result

    async def test_adaptive_learning_system(
        self, client: AsyncClient, authenticated_student: dict[str, Any]
    ):
        """测试自适应学习系统"""
        user_id = authenticated_student["user_id"]

        # 获取个性化推荐
        recommendations_response = await client.get(
            f"/api/v1/adaptive/recommendations/{user_id}"
        )
        assert recommendations_response.status_code == status.HTTP_200_OK
        recommendations = recommendations_response.json()

        assert "content_recommendations" in recommendations
        assert "difficulty_adjustment" in recommendations
        assert "learning_path" in recommendations

        # 更新学习偏好
        preferences_data = {
            "preferred_difficulty": "intermediate",
            "learning_style": "visual",
            "focus_areas": ["vocabulary", "listening"],
        }

        preferences_response = await client.put(
            f"/api/v1/adaptive/preferences/{user_id}", json=preferences_data
        )
        assert preferences_response.status_code == status.HTTP_200_OK

        # 获取更新后的推荐
        updated_recommendations_response = await client.get(
            f"/api/v1/adaptive/recommendations/{user_id}"
        )
        assert updated_recommendations_response.status_code == status.HTTP_200_OK
        updated_recommendations = updated_recommendations_response.json()

        # 验证推荐内容已根据偏好调整
        assert updated_recommendations != recommendations

    async def test_error_handling_and_edge_cases(
        self, client: AsyncClient, authenticated_student: dict[str, Any]
    ):
        """测试错误处理和边界情况"""
        user_id = authenticated_student["user_id"]

        # 测试访问不存在的内容
        invalid_content_response = await client.get("/api/v1/learning/content/99999")
        assert invalid_content_response.status_code == status.HTTP_404_NOT_FOUND

        # 测试提交无效的学习会话
        invalid_session_data = {"content_id": 99999, "learning_mode": "invalid_mode"}

        invalid_session_response = await client.post(
            "/api/v1/learning/sessions", json=invalid_session_data
        )
        assert invalid_session_response.status_code == status.HTTP_400_BAD_REQUEST

        # 测试超出限制的请求
        large_request_response = await client.get(
            "/api/v1/vocabulary/words",
            params={"limit": 10000},  # 超出合理限制
        )
        assert large_request_response.status_code == status.HTTP_400_BAD_REQUEST

        # 测试并发学习会话限制
        concurrent_sessions = []
        for _i in range(5):  # 尝试创建多个并发会话
            session_response = await client.post(
                "/api/v1/learning/sessions",
                json={"content_id": 1, "learning_mode": "practice"},
            )
            if session_response.status_code == status.HTTP_201_CREATED:
                concurrent_sessions.append(session_response.json())

        # 验证并发会话限制
        assert len(concurrent_sessions) <= 3  # 假设最多允许3个并发会话
