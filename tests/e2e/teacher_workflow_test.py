"""
英语四级学习系统 - 教师功能端到端测试

测试教师的完整教学流程，包括：
- 内容创建和管理
- 学生管理和指导
- 课程设计和发布
- 学习效果分析
- 互动教学功能
"""

from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from tests.fixtures.mock_services import get_mock_patches, reset_all_mocks
from tests.fixtures.test_data import get_test_user


class TestTeacherWorkflow:
    """教师功能端到端测试"""

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
    async def teacher_user_data(self):
        """教师用户数据"""
        return get_test_user("teacher")

    @pytest.fixture
    async def authenticated_teacher(
        self, client: AsyncClient, teacher_user_data: dict[str, Any]
    ):
        """已认证的教师用户"""
        # 注册教师用户
        register_response = await client.post(
            "/api/v1/auth/register", json=teacher_user_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # 登录获取token
        login_data = {
            "username": teacher_user_data["username"],
            "password": teacher_user_data["password"],
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        token_data = login_response.json()
        access_token = token_data["access_token"]

        # 设置认证头
        client.headers.update({"Authorization": f"Bearer {access_token}"})

        return {
            "user_data": teacher_user_data,
            "token": access_token,
            "user_id": register_response.json()["user_id"],
        }

    async def test_complete_teacher_workflow(
        self, client: AsyncClient, authenticated_teacher: dict[str, Any]
    ):
        """测试完整的教师工作流"""
        teacher_id = authenticated_teacher["user_id"]

        # 1. 内容创建和管理
        created_content = await self._test_content_creation_and_management(
            client, teacher_id
        )

        # 2. 课程设计和发布
        course = await self._test_course_design_and_publishing(
            client, teacher_id, created_content
        )

        # 3. 学生管理和指导
        await self._test_student_management_and_guidance(client, teacher_id, course)

        # 4. 学习效果分析
        await self._test_learning_analytics(client, teacher_id, course)

        # 5. 互动教学功能
        await self._test_interactive_teaching_features(client, teacher_id)

    async def _test_content_creation_and_management(
        self, client: AsyncClient, teacher_id: int
    ) -> list[dict[str, Any]]:
        """测试内容创建和管理"""
        created_content = []

        # 创建词汇内容
        vocabulary_content = {
            "title": "CET4核心词汇第一课",
            "description": "包含50个CET4高频词汇",
            "content_type": "vocabulary",
            "difficulty_level": "intermediate",
            "estimated_duration": 45,
            "tags": ["cet4", "vocabulary", "core"],
            "content_data": {
                "words": [
                    {
                        "word": "abandon",
                        "pronunciation": "/əˈbændən/",
                        "meanings": [
                            {
                                "part_of_speech": "verb",
                                "definition": "to give up completely",
                                "chinese_meaning": "放弃，抛弃",
                                "example": "They had to abandon their car in the snow.",
                            }
                        ],
                    },
                    {
                        "word": "ability",
                        "pronunciation": "/əˈbɪləti/",
                        "meanings": [
                            {
                                "part_of_speech": "noun",
                                "definition": "the capacity to do something",
                                "chinese_meaning": "能力，才能",
                                "example": "She has the ability to learn languages quickly.",
                            }
                        ],
                    },
                ],
                "exercises": [
                    {
                        "type": "multiple_choice",
                        "question": "What does 'abandon' mean?",
                        "options": [
                            "to give up",
                            "to continue",
                            "to start",
                            "to improve",
                        ],
                        "correct_answer": 0,
                        "explanation": "'Abandon' means to give up completely.",
                    }
                ],
            },
        }

        vocab_response = await client.post(
            "/api/v1/teacher/content", json=vocabulary_content
        )
        assert vocab_response.status_code == status.HTTP_201_CREATED
        vocab_content = vocab_response.json()
        created_content.append(vocab_content)

        # 创建听力内容
        listening_content = {
            "title": "日常对话听力练习",
            "description": "基础日常对话听力理解",
            "content_type": "listening",
            "difficulty_level": "beginner",
            "estimated_duration": 30,
            "tags": ["listening", "conversation", "daily"],
            "content_data": {
                "audio_url": "https://example.com/audio/conversation1.mp3",
                "transcript": "A: Good morning! How are you today? B: I'm fine, thank you. How about you?",
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question": "What time of day is it?",
                        "options": ["Morning", "Afternoon", "Evening", "Night"],
                        "correct_answer": 0,
                        "timestamp": 2.5,
                    }
                ],
            },
        }

        listening_response = await client.post(
            "/api/v1/teacher/content", json=listening_content
        )
        assert listening_response.status_code == status.HTTP_201_CREATED
        listening_content_result = listening_response.json()
        created_content.append(listening_content_result)

        # 更新内容
        content_id = vocab_content["content_id"]
        update_data = {
            "title": "CET4核心词汇第一课（更新版）",
            "description": "更新后的词汇课程，增加了更多例句",
        }

        update_response = await client.put(
            f"/api/v1/teacher/content/{content_id}", json=update_data
        )
        assert update_response.status_code == status.HTTP_200_OK

        # 获取教师创建的内容列表
        teacher_content_response = await client.get(
            "/api/v1/teacher/content", params={"created_by": teacher_id}
        )
        assert teacher_content_response.status_code == status.HTTP_200_OK
        teacher_content = teacher_content_response.json()
        assert len(teacher_content["items"]) >= 2

        return created_content

    async def _test_course_design_and_publishing(
        self, client: AsyncClient, teacher_id: int, content_list: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """测试课程设计和发布"""
        # 创建课程
        course_data = {
            "title": "CET4基础强化课程",
            "description": "针对CET4考试的基础强化训练课程",
            "category": "cet4_preparation",
            "difficulty_level": "intermediate",
            "estimated_duration": 1200,  # 20小时
            "max_students": 50,
            "tags": ["cet4", "foundation", "intensive"],
            "syllabus": [
                {
                    "week": 1,
                    "title": "词汇基础",
                    "content_ids": [
                        content["content_id"]
                        for content in content_list
                        if content["content_type"] == "vocabulary"
                    ],
                    "objectives": ["掌握100个核心词汇", "理解词汇用法"],
                },
                {
                    "week": 2,
                    "title": "听力训练",
                    "content_ids": [
                        content["content_id"]
                        for content in content_list
                        if content["content_type"] == "listening"
                    ],
                    "objectives": ["提高听力理解能力", "熟悉对话模式"],
                },
            ],
            "assessment_criteria": {
                "vocabulary_mastery": 30,
                "listening_comprehension": 25,
                "participation": 20,
                "assignments": 25,
            },
        }

        course_response = await client.post("/api/v1/teacher/courses", json=course_data)
        assert course_response.status_code == status.HTTP_201_CREATED
        course = course_response.json()
        course_id = course["course_id"]

        # 添加课程公告
        announcement_data = {
            "title": "课程开始通知",
            "content": "欢迎大家参加CET4基础强化课程！请按时完成作业。",
            "priority": "high",
            "send_notification": True,
        }

        announcement_response = await client.post(
            f"/api/v1/teacher/courses/{course_id}/announcements", json=announcement_data
        )
        assert announcement_response.status_code == status.HTTP_201_CREATED

        # 设置课程作业
        assignment_data = {
            "title": "第一周词汇作业",
            "description": "完成词汇练习并提交学习心得",
            "content_id": content_list[0]["content_id"],
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "max_score": 100,
            "submission_type": "text",
            "requirements": [
                "完成所有词汇练习",
                "写一篇200字的学习心得",
                "录制5个单词的发音",
            ],
        }

        assignment_response = await client.post(
            f"/api/v1/teacher/courses/{course_id}/assignments", json=assignment_data
        )
        assert assignment_response.status_code == status.HTTP_201_CREATED

        # 发布课程
        publish_response = await client.post(
            f"/api/v1/teacher/courses/{course_id}/publish"
        )
        assert publish_response.status_code == status.HTTP_200_OK

        return course

    async def _test_student_management_and_guidance(
        self, client: AsyncClient, teacher_id: int, course: dict[str, Any]
    ):
        """测试学生管理和指导"""
        course_id = course["course_id"]

        # 获取课程学生列表
        students_response = await client.get(
            f"/api/v1/teacher/courses/{course_id}/students"
        )
        assert students_response.status_code == status.HTTP_200_OK
        students = students_response.json()

        # 模拟添加学生到课程（通常由学生自己报名或管理员添加）
        student_data = {
            "student_ids": [1, 2, 3],  # 假设的学生ID
            "enrollment_type": "manual",
        }

        enroll_response = await client.post(
            f"/api/v1/teacher/courses/{course_id}/enroll", json=student_data
        )
        assert enroll_response.status_code == status.HTTP_200_OK

        # 查看学生学习进度
        student_id = 1
        progress_response = await client.get(
            f"/api/v1/teacher/courses/{course_id}/students/{student_id}/progress"
        )
        assert progress_response.status_code == status.HTTP_200_OK
        progress = progress_response.json()

        # 给学生提供个性化反馈
        feedback_data = {
            "student_id": student_id,
            "content": "你在词汇学习方面表现很好，建议加强听力练习。",
            "type": "encouragement",
            "suggestions": ["每天听英语新闻15分钟", "多做听力理解练习", "参与课堂讨论"],
        }

        feedback_response = await client.post(
            f"/api/v1/teacher/courses/{course_id}/feedback", json=feedback_data
        )
        assert feedback_response.status_code == status.HTTP_201_CREATED

        # 批改作业
        assignment_id = 1  # 假设的作业ID
        grading_data = {
            "student_id": student_id,
            "score": 85,
            "feedback": "作业完成得很好，词汇掌握扎实。建议在例句使用上多加练习。",
            "detailed_comments": [
                {
                    "section": "vocabulary_practice",
                    "score": 90,
                    "comment": "词汇掌握很好",
                },
                {"section": "pronunciation", "score": 80, "comment": "发音需要改进"},
            ],
        }

        grading_response = await client.post(
            f"/api/v1/teacher/assignments/{assignment_id}/grade", json=grading_data
        )
        assert grading_response.status_code == status.HTTP_200_OK

    async def _test_learning_analytics(
        self, client: AsyncClient, teacher_id: int, course: dict[str, Any]
    ):
        """测试学习效果分析"""
        course_id = course["course_id"]

        # 获取课程整体统计
        course_stats_response = await client.get(
            f"/api/v1/teacher/courses/{course_id}/analytics"
        )
        assert course_stats_response.status_code == status.HTTP_200_OK
        course_stats = course_stats_response.json()

        assert "enrollment_count" in course_stats
        assert "completion_rate" in course_stats
        assert "average_score" in course_stats
        assert "engagement_metrics" in course_stats

        # 获取学生表现分析
        performance_response = await client.get(
            f"/api/v1/teacher/courses/{course_id}/performance-analysis"
        )
        assert performance_response.status_code == status.HTTP_200_OK
        performance = performance_response.json()

        # 获取内容效果分析
        content_analytics_response = await client.get(
            "/api/v1/teacher/content/analytics", params={"course_id": course_id}
        )
        assert content_analytics_response.status_code == status.HTTP_200_OK
        content_analytics = content_analytics_response.json()

        # 生成学习报告
        report_data = {
            "report_type": "course_summary",
            "course_id": course_id,
            "period": "monthly",
            "include_individual_progress": True,
            "include_recommendations": True,
        }

        report_response = await client.post(
            "/api/v1/teacher/reports/generate", json=report_data
        )
        assert report_response.status_code == status.HTTP_201_CREATED
        report = report_response.json()

        # 获取报告状态
        report_id = report["report_id"]
        report_status_response = await client.get(
            f"/api/v1/teacher/reports/{report_id}/status"
        )
        assert report_status_response.status_code == status.HTTP_200_OK

    async def _test_interactive_teaching_features(
        self, client: AsyncClient, teacher_id: int
    ):
        """测试互动教学功能"""
        # 创建在线讨论
        discussion_data = {
            "title": "如何提高英语听力？",
            "content": "大家分享一下自己的听力学习经验吧！",
            "category": "learning_tips",
            "tags": ["listening", "tips", "discussion"],
        }

        discussion_response = await client.post(
            "/api/v1/teacher/discussions", json=discussion_data
        )
        assert discussion_response.status_code == status.HTTP_201_CREATED
        discussion = discussion_response.json()
        discussion_id = discussion["discussion_id"]

        # 参与讨论
        reply_data = {
            "content": "我建议大家多听英语播客，从简单的开始。",
            "parent_id": None,
        }

        reply_response = await client.post(
            f"/api/v1/teacher/discussions/{discussion_id}/replies", json=reply_data
        )
        assert reply_response.status_code == status.HTTP_201_CREATED

        # 创建直播课程
        live_session_data = {
            "title": "CET4听力技巧直播课",
            "description": "实时讲解听力技巧和练习",
            "scheduled_time": (datetime.now() + timedelta(hours=2)).isoformat(),
            "duration": 60,
            "max_participants": 100,
            "course_id": 1,  # 假设的课程ID
        }

        live_session_response = await client.post(
            "/api/v1/teacher/live-sessions", json=live_session_data
        )
        assert live_session_response.status_code == status.HTTP_201_CREATED

        # 创建问卷调查
        survey_data = {
            "title": "课程满意度调查",
            "description": "请对本课程进行评价",
            "questions": [
                {
                    "type": "rating",
                    "question": "您对课程内容的满意度？",
                    "scale": 5,
                    "required": True,
                },
                {
                    "type": "multiple_choice",
                    "question": "您最喜欢的学习内容类型？",
                    "options": ["词汇", "听力", "阅读", "写作"],
                    "required": True,
                },
                {"type": "text", "question": "您有什么改进建议？", "required": False},
            ],
            "anonymous": True,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        survey_response = await client.post("/api/v1/teacher/surveys", json=survey_data)
        assert survey_response.status_code == status.HTTP_201_CREATED

    async def test_teacher_collaboration_features(
        self, client: AsyncClient, authenticated_teacher: dict[str, Any]
    ):
        """测试教师协作功能"""
        teacher_id = authenticated_teacher["user_id"]

        # 创建教师小组
        group_data = {
            "name": "CET4教学研究小组",
            "description": "专注于CET4教学方法研究",
            "category": "research",
            "is_public": False,
        }

        group_response = await client.post("/api/v1/teacher/groups", json=group_data)
        assert group_response.status_code == status.HTTP_201_CREATED
        group = group_response.json()
        group_id = group["group_id"]

        # 邀请其他教师
        invite_data = {
            "teacher_ids": [2, 3],  # 假设的教师ID
            "message": "邀请您加入我们的教学研究小组",
        }

        invite_response = await client.post(
            f"/api/v1/teacher/groups/{group_id}/invite", json=invite_data
        )
        assert invite_response.status_code == status.HTTP_200_OK

        # 分享教学资源
        resource_data = {
            "title": "CET4词汇教学PPT",
            "description": "包含词汇教学方法和练习",
            "resource_type": "presentation",
            "file_url": "https://example.com/files/cet4-vocab.pptx",
            "tags": ["vocabulary", "teaching", "cet4"],
            "share_with_group": True,
            "group_id": group_id,
        }

        resource_response = await client.post(
            "/api/v1/teacher/resources", json=resource_data
        )
        assert resource_response.status_code == status.HTTP_201_CREATED

    async def test_teacher_professional_development(
        self, client: AsyncClient, authenticated_teacher: dict[str, Any]
    ):
        """测试教师专业发展功能"""
        teacher_id = authenticated_teacher["user_id"]

        # 查看可用的培训课程
        training_response = await client.get("/api/v1/teacher/training/courses")
        assert training_response.status_code == status.HTTP_200_OK

        # 报名参加培训
        enrollment_data = {
            "course_id": 1,  # 假设的培训课程ID
            "motivation": "希望提高在线教学技能",
        }

        enrollment_response = await client.post(
            "/api/v1/teacher/training/enroll", json=enrollment_data
        )
        assert enrollment_response.status_code == status.HTTP_201_CREATED

        # 获取教学统计和成就
        stats_response = await client.get(f"/api/v1/teacher/{teacher_id}/statistics")
        assert stats_response.status_code == status.HTTP_200_OK
        stats = stats_response.json()

        assert "courses_created" in stats
        assert "students_taught" in stats
        assert "content_created" in stats
        assert "teaching_rating" in stats
