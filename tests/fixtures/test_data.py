"""
英语四级学习系统 - 测试数据生成器

提供端到端测试所需的各种测试数据，包括用户、内容、学习记录等。
使用Faker库生成真实感的测试数据。
"""

import random
from datetime import timedelta
from typing import Any

from faker import Faker
from faker.providers import date_time, internet, lorem, person

# 初始化Faker，支持中文
fake = Faker(["zh_CN", "en_US"])
fake.add_provider(internet)
fake.add_provider(lorem)
fake.add_provider(person)
fake.add_provider(date_time)


class TestDataGenerator:
    """测试数据生成器"""

    def __init__(self, seed: int | None = None):
        """初始化生成器

        Args:
            seed: 随机种子，用于生成可重复的测试数据
        """
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate_user_data(
        self, role: str = "student", count: int = 1
    ) -> list[dict[str, Any]]:
        """生成用户测试数据

        Args:
            role: 用户角色 (admin, teacher, student)
            count: 生成数量

        Returns:
            用户数据列表
        """
        users = []

        for i in range(count):
            user_data = {
                "username": fake.user_name() + f"_{i}",
                "email": fake.email(),
                "password": "Test123456!",  # 统一测试密码
                "full_name": fake.name(),
                "phone": fake.phone_number(),
                "role": role,
                "is_active": True,
                "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
                "profile": {
                    "avatar": fake.image_url(),
                    "bio": fake.text(max_nb_chars=200),
                    "location": fake.city(),
                    "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=50),
                    "gender": random.choice(["male", "female", "other"]),
                    "education_level": random.choice(
                        ["high_school", "bachelor", "master", "phd"]
                    ),
                    "english_level": random.choice(
                        ["beginner", "intermediate", "advanced"]
                    ),
                    "learning_goals": random.sample(
                        [
                            "pass_cet4",
                            "improve_speaking",
                            "business_english",
                            "academic_writing",
                            "daily_communication",
                        ],
                        k=random.randint(1, 3),
                    ),
                },
            }

            # 根据角色添加特定字段
            if role == "teacher":
                user_data["profile"].update(
                    {
                        "teaching_experience": random.randint(1, 20),
                        "specializations": random.sample(
                            [
                                "vocabulary",
                                "grammar",
                                "listening",
                                "speaking",
                                "reading",
                                "writing",
                                "translation",
                            ],
                            k=random.randint(2, 4),
                        ),
                        "certifications": random.sample(
                            ["TESOL", "TEFL", "CELTA", "TKT", "专八"],
                            k=random.randint(1, 3),
                        ),
                    }
                )
            elif role == "student":
                user_data["profile"].update(
                    {
                        "target_score": random.randint(425, 650),
                        "current_score": random.randint(300, 500),
                        "study_time_per_day": random.randint(30, 180),  # 分钟
                        "preferred_study_time": random.choice(
                            ["morning", "afternoon", "evening", "night"]
                        ),
                    }
                )

            users.append(user_data)

        return users

    def generate_vocabulary_data(self, count: int = 50) -> list[dict[str, Any]]:
        """生成词汇测试数据"""
        vocabularies = []

        # 预定义的CET4词汇示例
        sample_words = [
            {"word": "abandon", "meaning": "放弃，抛弃", "phonetic": "/əˈbændən/"},
            {"word": "ability", "meaning": "能力，才能", "phonetic": "/əˈbɪləti/"},
            {"word": "abroad", "meaning": "在国外，到国外", "phonetic": "/əˈbrɔːd/"},
            {"word": "absence", "meaning": "缺席，不在", "phonetic": "/ˈæbsəns/"},
            {
                "word": "absolute",
                "meaning": "绝对的，完全的",
                "phonetic": "/ˈæbsəluːt/",
            },
            {
                "word": "academic",
                "meaning": "学术的，学院的",
                "phonetic": "/ˌækəˈdemɪk/",
            },
            {"word": "accept", "meaning": "接受，承认", "phonetic": "/əkˈsept/"},
            {"word": "access", "meaning": "接近，进入", "phonetic": "/ˈækses/"},
            {"word": "accident", "meaning": "事故，意外", "phonetic": "/ˈæksɪdənt/"},
            {"word": "accompany", "meaning": "陪伴，伴随", "phonetic": "/əˈkʌmpəni/"},
        ]

        for i in range(count):
            if i < len(sample_words):
                base_word = sample_words[i]
            else:
                base_word = {
                    "word": fake.word(),
                    "meaning": fake.sentence(nb_words=3),
                    "phonetic": f"/ˈ{fake.word()}/",
                }

            vocabulary = {
                "word": base_word["word"],
                "pronunciation": base_word["phonetic"],
                "meanings": [
                    {
                        "part_of_speech": random.choice(
                            ["noun", "verb", "adjective", "adverb"]
                        ),
                        "definition": base_word["meaning"],
                        "example": fake.sentence(),
                        "chinese_meaning": base_word["meaning"],
                    }
                ],
                "difficulty_level": random.choice(
                    ["beginner", "intermediate", "advanced"]
                ),
                "frequency": random.randint(1, 100),
                "tags": random.sample(
                    ["cet4", "common", "academic", "business"], k=random.randint(1, 3)
                ),
                "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
                "audio_url": f"https://example.com/audio/{base_word['word']}.mp3",
                "image_url": fake.image_url() if random.choice([True, False]) else None,
            }

            vocabularies.append(vocabulary)

        return vocabularies

    def generate_learning_content(
        self, content_type: str, count: int = 10
    ) -> list[dict[str, Any]]:
        """生成学习内容测试数据

        Args:
            content_type: 内容类型 (vocabulary, listening, reading, writing, translation)
            count: 生成数量
        """
        contents = []

        for i in range(count):
            base_content = {
                "title": fake.sentence(nb_words=6),
                "description": fake.text(max_nb_chars=300),
                "content_type": content_type,
                "difficulty_level": random.choice(
                    ["beginner", "intermediate", "advanced"]
                ),
                "estimated_duration": random.randint(10, 60),  # 分钟
                "tags": random.sample(
                    [
                        "grammar",
                        "vocabulary",
                        "pronunciation",
                        "comprehension",
                        "writing",
                        "speaking",
                        "listening",
                        "reading",
                    ],
                    k=random.randint(2, 4),
                ),
                "created_by": random.randint(1, 10),  # 教师ID
                "created_at": fake.date_time_between(start_date="-6m", end_date="now"),
                "is_published": random.choice([True, False]),
                "view_count": random.randint(0, 1000),
                "like_count": random.randint(0, 100),
            }

            # 根据内容类型添加特定字段
            if content_type == "vocabulary":
                base_content.update(
                    {
                        "word_count": random.randint(10, 50),
                        "vocabulary_list": random.sample(
                            range(1, 100), k=random.randint(10, 30)
                        ),
                    }
                )
            elif content_type == "listening":
                base_content.update(
                    {
                        "audio_url": f"https://example.com/audio/listening_{i}.mp3",
                        "transcript": fake.text(max_nb_chars=500),
                        "questions": self._generate_questions(
                            "listening", random.randint(5, 10)
                        ),
                    }
                )
            elif content_type == "reading":
                base_content.update(
                    {
                        "passage": fake.text(max_nb_chars=1000),
                        "word_count": random.randint(200, 800),
                        "questions": self._generate_questions(
                            "reading", random.randint(5, 15)
                        ),
                    }
                )
            elif content_type == "writing":
                base_content.update(
                    {
                        "prompt": fake.text(max_nb_chars=200),
                        "requirements": {
                            "min_words": random.randint(100, 200),
                            "max_words": random.randint(300, 500),
                            "format": random.choice(
                                ["essay", "letter", "report", "story"]
                            ),
                        },
                        "sample_answer": fake.text(max_nb_chars=800),
                    }
                )

            contents.append(base_content)

        return contents

    def _generate_questions(
        self, question_type: str, count: int
    ) -> list[dict[str, Any]]:
        """生成题目数据"""
        questions = []

        for i in range(count):
            question = {
                "question_id": i + 1,
                "question_text": fake.sentence() + "?",
                "question_type": random.choice(
                    ["multiple_choice", "true_false", "fill_blank"]
                ),
                "points": random.randint(1, 5),
            }

            if question["question_type"] == "multiple_choice":
                options = [fake.sentence(nb_words=4) for _ in range(4)]
                question.update(
                    {
                        "options": options,
                        "correct_answer": random.choice(["A", "B", "C", "D"]),
                        "explanation": fake.sentence(),
                    }
                )
            elif question["question_type"] == "true_false":
                question.update(
                    {
                        "correct_answer": random.choice([True, False]),
                        "explanation": fake.sentence(),
                    }
                )
            else:  # fill_blank
                question.update(
                    {
                        "correct_answer": fake.word(),
                        "hints": [fake.word() for _ in range(2)],
                    }
                )

            questions.append(question)

        return questions

    def generate_learning_session_data(
        self, user_id: int, count: int = 20
    ) -> list[dict[str, Any]]:
        """生成学习会话测试数据"""
        sessions = []

        for _i in range(count):
            start_time = fake.date_time_between(start_date="-3m", end_date="now")
            duration = random.randint(300, 3600)  # 5分钟到1小时

            session = {
                "user_id": user_id,
                "content_id": random.randint(1, 50),
                "content_type": random.choice(
                    ["vocabulary", "listening", "reading", "writing"]
                ),
                "start_time": start_time,
                "end_time": start_time + timedelta(seconds=duration),
                "duration": duration,
                "completion_rate": random.uniform(0.3, 1.0),
                "accuracy_rate": random.uniform(0.4, 0.95),
                "score": random.randint(60, 100),
                "answers": self._generate_session_answers(),
                "feedback": {
                    "strengths": random.sample(
                        ["vocabulary", "grammar", "pronunciation", "comprehension"],
                        k=random.randint(1, 2),
                    ),
                    "weaknesses": random.sample(
                        ["spelling", "grammar", "vocabulary", "speed"],
                        k=random.randint(0, 2),
                    ),
                    "suggestions": [
                        fake.sentence() for _ in range(random.randint(1, 3))
                    ],
                },
            }

            sessions.append(session)

        return sessions

    def _generate_session_answers(self) -> list[dict[str, Any]]:
        """生成会话答题记录"""
        answers = []
        question_count = random.randint(5, 15)

        for i in range(question_count):
            answer = {
                "question_id": i + 1,
                "user_answer": fake.word(),
                "correct_answer": fake.word(),
                "is_correct": random.choice([True, False]),
                "time_spent": random.randint(10, 120),  # 秒
                "attempts": random.randint(1, 3),
            }
            answers.append(answer)

        return answers

    def generate_achievement_data(self, user_id: int) -> list[dict[str, Any]]:
        """生成成就测试数据"""
        achievements = [
            {
                "achievement_id": "first_login",
                "name": "初来乍到",
                "description": "完成首次登录",
                "icon": "🎉",
                "points": 10,
                "unlocked_at": fake.date_time_between(start_date="-3m", end_date="now"),
            },
            {
                "achievement_id": "vocabulary_master",
                "name": "词汇大师",
                "description": "掌握100个单词",
                "icon": "📚",
                "points": 50,
                "unlocked_at": fake.date_time_between(start_date="-2m", end_date="now"),
            },
            {
                "achievement_id": "daily_learner",
                "name": "每日学习者",
                "description": "连续学习7天",
                "icon": "🔥",
                "points": 30,
                "unlocked_at": fake.date_time_between(start_date="-1m", end_date="now"),
            },
        ]

        # 随机选择已解锁的成就
        unlocked_count = random.randint(1, len(achievements))
        return random.sample(achievements, k=unlocked_count)

    def generate_test_scenario_data(self) -> dict[str, Any]:
        """生成完整的测试场景数据"""
        return {
            "admin_users": self.generate_user_data("admin", 2),
            "teacher_users": self.generate_user_data("teacher", 5),
            "student_users": self.generate_user_data("student", 20),
            "vocabularies": self.generate_vocabulary_data(100),
            "learning_contents": {
                "vocabulary": self.generate_learning_content("vocabulary", 10),
                "listening": self.generate_learning_content("listening", 8),
                "reading": self.generate_learning_content("reading", 8),
                "writing": self.generate_learning_content("writing", 6),
            },
        }


# 全局测试数据生成器实例
test_data_generator = TestDataGenerator(seed=42)  # 固定种子确保可重复性


def get_test_user(role: str = "student") -> dict[str, Any]:
    """获取单个测试用户"""
    return test_data_generator.generate_user_data(role, 1)[0]


def get_test_vocabulary() -> dict[str, Any]:
    """获取单个测试词汇"""
    return test_data_generator.generate_vocabulary_data(1)[0]


def get_test_learning_content(content_type: str = "vocabulary") -> dict[str, Any]:
    """获取单个测试学习内容"""
    return test_data_generator.generate_learning_content(content_type, 1)[0]


def get_complete_test_scenario() -> dict[str, Any]:
    """获取完整的测试场景数据"""
    return test_data_generator.generate_test_scenario_data()
