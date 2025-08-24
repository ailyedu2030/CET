"""学生综合训练中心核心服务."""

import json
import random
from datetime import datetime
from typing import Any, cast

from sqlalchemy import Float, and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.models.enums import (
    DifficultyLevel,
    GradingStatus,
    QuestionType,
    TrainingType,
)
from app.training.models.training_models import (
    Question,
    TrainingRecord,
    TrainingSession,
)
from app.training.schemas.training_schemas import (
    GradingResult,
    QuestionFilter,
    QuestionResponse,
    SubmitAnswerRequest,
    TrainingSessionRequest,
    TrainingSessionResponse,
)


class TrainingCenterService:
    """学生综合训练中心核心服务 - 五大训练模块实现."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化训练中心服务."""
        self.db = db
        self.deepseek_service = DeepSeekService()

    # ==================== 训练会话管理 ====================

    async def create_training_session(
        self, student_id: int, session_data: TrainingSessionRequest
    ) -> TrainingSessionResponse:
        """创建新的训练会话."""
        session = TrainingSession(
            student_id=student_id,
            session_name=session_data.session_name,
            session_type=session_data.session_type,
            description=session_data.description,
            difficulty_level=session_data.difficulty_level,
            question_count=session_data.question_count,
            time_limit=session_data.time_limit,
            status="in_progress",
        )

        # 设置自适应调整数据
        if session_data.auto_adaptive:
            session.adaptation_data = {
                "auto_adaptive": True,
                "target_accuracy": 0.75,
                "adjustment_sensitivity": 0.5,
                "knowledge_points": session_data.knowledge_points,
                "initial_assessment": True,
            }

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return await self._build_session_response(session)

    async def get_training_session(
        self, session_id: int, student_id: int
    ) -> TrainingSessionResponse | None:
        """获取训练会话详情."""
        stmt = (
            select(TrainingSession)
            .where(
                and_(
                    TrainingSession.id == session_id,
                    TrainingSession.student_id == student_id,
                )
            )
            .options(selectinload(TrainingSession.records))
        )

        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        return await self._build_session_response(session)

    async def get_student_sessions(
        self,
        student_id: int,
        training_type: TrainingType | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[TrainingSessionResponse]:
        """获取学生训练会话列表."""
        stmt = select(TrainingSession).where(TrainingSession.student_id == student_id)

        if training_type:
            stmt = stmt.where(TrainingSession.session_type == training_type)

        if status:
            stmt = stmt.where(TrainingSession.status == status)

        stmt = stmt.order_by(desc(TrainingSession.created_at)).offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        return [await self._build_session_response(session) for session in sessions]

    async def complete_training_session(
        self, session_id: int, student_id: int
    ) -> TrainingSessionResponse | None:
        """完成训练会话."""
        stmt = (
            select(TrainingSession)
            .where(
                and_(
                    TrainingSession.id == session_id,
                    TrainingSession.student_id == student_id,
                )
            )
            .options(selectinload(TrainingSession.records))
        )

        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        # 计算会话统计数据
        total_questions = len(session.records)
        correct_answers = sum(1 for record in session.records if record.is_correct)
        total_score = sum(record.score for record in session.records)
        time_spent = sum(record.time_spent for record in session.records)

        # 更新会话状态
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.total_questions = total_questions
        session.correct_answers = correct_answers
        session.total_score = total_score
        session.time_spent = time_spent

        await self.db.commit()
        await self.db.refresh(session)

        return await self._build_session_response(session)

    # ==================== 题目生成和获取 ====================

    async def generate_questions(
        self,
        training_type: TrainingType,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None = None,
        student_id: int | None = None,
    ) -> list[QuestionResponse]:
        """生成训练题目."""
        # 根据训练类型调用相应的生成方法
        if training_type == TrainingType.VOCABULARY:
            return await self._generate_vocabulary_questions(
                difficulty_level, question_count, knowledge_points, student_id
            )
        elif training_type == TrainingType.LISTENING:
            return await self._generate_listening_questions(
                difficulty_level, question_count, knowledge_points, student_id
            )
        elif training_type == TrainingType.READING:
            return await self._generate_reading_questions(
                difficulty_level, question_count, knowledge_points, student_id
            )
        elif training_type == TrainingType.WRITING:
            return await self._generate_writing_questions(
                difficulty_level, question_count, knowledge_points, student_id
            )
        elif training_type == TrainingType.TRANSLATION:
            return await self._generate_translation_questions(
                difficulty_level, question_count, knowledge_points, student_id
            )
        else:
            return await self._generate_comprehensive_questions(
                difficulty_level, question_count, knowledge_points, student_id
            )

    async def get_question_by_id(self, question_id: int) -> Question | None:
        """根据ID获取题目."""
        stmt = select(Question).where(Question.id == question_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_questions_by_filter(
        self, filter_data: QuestionFilter, limit: int = 20, offset: int = 0
    ) -> list[Question]:
        """根据筛选条件获取题目."""
        stmt = select(Question)

        if filter_data.question_type:
            stmt = stmt.where(Question.question_type == filter_data.question_type)

        if filter_data.training_type:
            stmt = stmt.where(Question.training_type == filter_data.training_type)

        if filter_data.difficulty_level:
            stmt = stmt.where(Question.difficulty_level == filter_data.difficulty_level)

        if filter_data.knowledge_points:
            # JSON数组交集查询
            for point in filter_data.knowledge_points:
                stmt = stmt.where(Question.knowledge_points.op("@>")([point]))

        if filter_data.tags:
            # JSON数组交集查询
            for tag in filter_data.tags:
                stmt = stmt.where(Question.tags.op("@>")([tag]))

        if filter_data.is_active is not None:
            stmt = stmt.where(Question.is_active == filter_data.is_active)

        if filter_data.created_after:
            stmt = stmt.where(Question.created_at >= filter_data.created_after)

        if filter_data.created_before:
            stmt = stmt.where(Question.created_at <= filter_data.created_before)

        stmt = stmt.order_by(desc(Question.created_at)).offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ==================== 答题和批改 ====================

    async def submit_answer(
        self, student_id: int, answer_data: SubmitAnswerRequest
    ) -> tuple[TrainingRecord, GradingResult]:
        """提交答案并进行批改."""
        # 获取题目信息
        question = await self.get_question_by_id(answer_data.question_id)
        if not question:
            raise ValueError(f"题目ID {answer_data.question_id} 不存在")

        # 创建训练记录
        record = TrainingRecord(
            session_id=answer_data.session_id,
            student_id=student_id,
            question_id=answer_data.question_id,
            user_answer=answer_data.user_answer,
            start_time=answer_data.start_time,
            end_time=answer_data.end_time,
            time_spent=answer_data.time_spent,
            grading_status=GradingStatus.PENDING,
        )

        # 进行批改
        grading_result = await self._grade_answer(question, answer_data.user_answer)

        # 更新记录
        record.is_correct = grading_result.is_correct
        record.score = grading_result.score
        record.grading_status = grading_result.grading_status
        record.ai_feedback = grading_result.ai_feedback
        record.ai_confidence = grading_result.ai_confidence
        record.knowledge_points_mastered = grading_result.knowledge_points_mastered
        record.knowledge_points_weak = grading_result.knowledge_points_weak

        self.db.add(record)

        # 更新题目统计
        question.usage_count += 1
        await self._update_question_statistics(question)

        await self.db.commit()

        return record, grading_result

    # ==================== 私有方法：题目生成 ====================

    async def _generate_vocabulary_questions(
        self,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None,
        student_id: int | None,
    ) -> list[QuestionResponse]:
        """生成词汇训练题目."""
        questions: list[QuestionResponse] = []

        # 题型分布：60%选择题，30%填空题，10%翻译题
        question_types = (
            [QuestionType.MULTIPLE_CHOICE] * 6
            + [QuestionType.FILL_BLANK] * 3
            + [QuestionType.TRANSLATION_EN_TO_CN] * 1
        )

        for _ in range(question_count):
            question_type = random.choice(question_types)

            # 使用AI生成题目内容
            prompt = await self._build_vocabulary_prompt(
                question_type, difficulty_level, knowledge_points
            )

            try:
                ai_response = await self._safe_ai_completion(prompt)

                if ai_response:
                    question_data = self._parse_ai_question_response(
                        ai_response,
                        question_type,
                        TrainingType.VOCABULARY,
                        difficulty_level,
                    )

                    # 创建并保存题目
                    question = Question(
                        question_type=question_type,
                        training_type=TrainingType.VOCABULARY,
                        title=question_data["title"],
                        content=question_data["content"],
                        difficulty_level=difficulty_level,
                        max_score=10.0,
                        time_limit=(120 if question_type == QuestionType.MULTIPLE_CHOICE else 180),
                        knowledge_points=knowledge_points or ["vocabulary", "基础词汇"],
                        tags=["ai_generated", "vocabulary"],
                        correct_answer=question_data["correct_answer"],
                        answer_analysis=question_data.get("analysis", ""),
                        grading_criteria=question_data.get("grading_criteria", {}),
                    )

                    self.db.add(question)
                    await self.db.flush()

                    questions.append(await self._build_question_response(question))

            except Exception:
                # AI生成失败时使用备用题目
                backup_question = await self._get_backup_question(
                    TrainingType.VOCABULARY, difficulty_level, question_type
                )
                if backup_question:
                    questions.append(await self._build_question_response(backup_question))

        await self.db.commit()
        return questions[:question_count]

    async def _generate_listening_questions(
        self,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None,
        student_id: int | None,
    ) -> list[QuestionResponse]:
        """生成听力训练题目."""
        questions: list[QuestionResponse] = []
        question_type = QuestionType.LISTENING_COMPREHENSION

        for _ in range(question_count):
            # 生成听力材料和题目
            prompt = await self._build_listening_prompt(difficulty_level, knowledge_points)

            try:
                ai_response = await self._safe_ai_completion(prompt, max_tokens=1000)

                if ai_response:
                    question_data = self._parse_ai_question_response(
                        ai_response,
                        question_type,
                        TrainingType.LISTENING,
                        difficulty_level,
                    )

                    question = Question(
                        question_type=question_type,
                        training_type=TrainingType.LISTENING,
                        title=question_data["title"],
                        content=question_data["content"],
                        difficulty_level=difficulty_level,
                        max_score=15.0,
                        time_limit=300,  # 5分钟
                        knowledge_points=knowledge_points or ["listening", "英语听力"],
                        tags=["ai_generated", "listening"],
                        correct_answer=question_data["correct_answer"],
                        answer_analysis=question_data.get("analysis", ""),
                        grading_criteria={"accuracy": 0.7, "comprehension": 0.3},
                    )

                    self.db.add(question)
                    await self.db.flush()

                    questions.append(await self._build_question_response(question))

            except Exception:
                backup_question = await self._get_backup_question(
                    TrainingType.LISTENING, difficulty_level, question_type
                )
                if backup_question:
                    questions.append(await self._build_question_response(backup_question))

        await self.db.commit()
        return questions[:question_count]

    async def _generate_reading_questions(
        self,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None,
        student_id: int | None,
    ) -> list[QuestionResponse]:
        """生成阅读训练题目."""
        questions: list[QuestionResponse] = []
        question_type = QuestionType.READING_COMPREHENSION

        # 一般每篇阅读材料对应3-5个题目
        passage_count = max(1, question_count // 4)

        for _ in range(passage_count):
            # 生成阅读材料
            prompt = await self._build_reading_prompt(difficulty_level, knowledge_points)

            try:
                ai_response = await self._safe_ai_completion(prompt, max_tokens=1500)

                if ai_response:
                    passage_data = self._parse_ai_reading_response(ai_response, difficulty_level)

                    # 为每篇文章生成多个题目
                    questions_per_passage = min(4, question_count - len(questions))

                    for q_idx in range(questions_per_passage):
                        if q_idx < len(passage_data["questions"]):
                            question = Question(
                                question_type=question_type,
                                training_type=TrainingType.READING,
                                title=passage_data["questions"][q_idx]["title"],
                                content={
                                    "passage": passage_data["passage"],
                                    "question": passage_data["questions"][q_idx]["question"],
                                    "options": passage_data["questions"][q_idx]["options"],
                                },
                                difficulty_level=difficulty_level,
                                max_score=12.0,
                                time_limit=400,  # 6分40秒
                                knowledge_points=knowledge_points or ["reading", "英语阅读"],
                                tags=["ai_generated", "reading"],
                                correct_answer=passage_data["questions"][q_idx]["correct_answer"],
                                answer_analysis=passage_data["questions"][q_idx].get(
                                    "analysis", ""
                                ),
                                grading_criteria={"comprehension": 1.0},
                            )

                            self.db.add(question)
                            await self.db.flush()

                            questions.append(await self._build_question_response(question))

            except Exception:
                # 使用备用题目
                for _ in range(min(4, question_count - len(questions))):
                    backup_question = await self._get_backup_question(
                        TrainingType.READING, difficulty_level, question_type
                    )
                    if backup_question:
                        questions.append(await self._build_question_response(backup_question))

        await self.db.commit()
        return questions[:question_count]

    async def _generate_writing_questions(
        self,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None,
        student_id: int | None,
    ) -> list[QuestionResponse]:
        """生成写作训练题目."""
        questions: list[QuestionResponse] = []
        question_type = QuestionType.ESSAY

        for _ in range(question_count):
            prompt = await self._build_writing_prompt(difficulty_level, knowledge_points)

            try:
                ai_response = await self._safe_ai_completion(
                    prompt, temperature=0.8, max_tokens=600
                )

                if ai_response:
                    question_data = self._parse_ai_question_response(
                        ai_response,
                        question_type,
                        TrainingType.WRITING,
                        difficulty_level,
                    )

                    question = Question(
                        question_type=question_type,
                        training_type=TrainingType.WRITING,
                        title=question_data["title"],
                        content=question_data["content"],
                        difficulty_level=difficulty_level,
                        max_score=25.0,  # 按四级写作评分标准
                        time_limit=1800,  # 30分钟
                        knowledge_points=knowledge_points or ["writing", "英语写作"],
                        tags=["ai_generated", "writing"],
                        correct_answer=question_data["correct_answer"],
                        answer_analysis=question_data.get("analysis", ""),
                        grading_criteria={
                            "content": 0.35,
                            "language": 0.35,
                            "structure": 0.3,
                        },
                    )

                    self.db.add(question)
                    await self.db.flush()

                    questions.append(await self._build_question_response(question))

            except Exception:
                backup_question = await self._get_backup_question(
                    TrainingType.WRITING, difficulty_level, question_type
                )
                if backup_question:
                    questions.append(await self._build_question_response(backup_question))

        await self.db.commit()
        return questions[:question_count]

    async def _generate_translation_questions(
        self,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None,
        student_id: int | None,
    ) -> list[QuestionResponse]:
        """生成翻译训练题目."""
        questions: list[QuestionResponse] = []

        # 翻译题型：50%英译中，50%中译英
        question_types = [
            QuestionType.TRANSLATION_EN_TO_CN,
            QuestionType.TRANSLATION_CN_TO_EN,
        ]

        for i in range(question_count):
            question_type = question_types[i % 2]

            prompt = await self._build_translation_prompt(
                question_type, difficulty_level, knowledge_points
            )

            try:
                ai_response = await self._safe_ai_completion(prompt)

                if ai_response:
                    question_data = self._parse_ai_question_response(
                        ai_response,
                        question_type,
                        TrainingType.TRANSLATION,
                        difficulty_level,
                    )

                    question = Question(
                        question_type=question_type,
                        training_type=TrainingType.TRANSLATION,
                        title=question_data["title"],
                        content=question_data["content"],
                        difficulty_level=difficulty_level,
                        max_score=20.0,
                        time_limit=600,  # 10分钟
                        knowledge_points=knowledge_points or ["translation", "英汉翻译"],
                        tags=["ai_generated", "translation"],
                        correct_answer=question_data["correct_answer"],
                        answer_analysis=question_data.get("analysis", ""),
                        grading_criteria={
                            "accuracy": 0.5,
                            "fluency": 0.3,
                            "completeness": 0.2,
                        },
                    )

                    self.db.add(question)
                    await self.db.flush()

                    questions.append(await self._build_question_response(question))

            except Exception:
                backup_question = await self._get_backup_question(
                    TrainingType.TRANSLATION, difficulty_level, question_type
                )
                if backup_question:
                    questions.append(await self._build_question_response(backup_question))

        await self.db.commit()
        return questions[:question_count]

    async def _generate_comprehensive_questions(
        self,
        difficulty_level: DifficultyLevel,
        question_count: int,
        knowledge_points: list[str] | None,
        student_id: int | None,
    ) -> list[QuestionResponse]:
        """生成综合训练题目."""
        questions: list[QuestionResponse] = []

        # 综合训练包含各种题型 - 按比例分配题目数量
        allocation = {
            TrainingType.VOCABULARY: max(1, question_count // 5),
            TrainingType.LISTENING: max(1, question_count // 5),
            TrainingType.READING: max(1, question_count // 5),
            TrainingType.WRITING: max(1, question_count // 10),
            TrainingType.TRANSLATION: max(1, question_count // 10),
        }

        for training_type, count in allocation.items():
            if len(questions) >= question_count:
                break

            type_questions = await self.generate_questions(
                training_type,
                difficulty_level,
                min(count, question_count - len(questions)),
                knowledge_points,
                student_id,
            )
            questions.extend(type_questions)

        return questions[:question_count]

    # ==================== 私有方法：Prompt构建 ====================

    async def _build_vocabulary_prompt(
        self,
        question_type: QuestionType,
        difficulty_level: DifficultyLevel,
        knowledge_points: list[str] | None,
    ) -> str:
        """构建词汇题目生成prompt."""
        difficulty_map = {
            DifficultyLevel.BEGINNER: "基础词汇（高中水平）",
            DifficultyLevel.ELEMENTARY: "四级基础词汇",
            DifficultyLevel.INTERMEDIATE: "四级核心词汇",
            DifficultyLevel.UPPER_INTERMEDIATE: "四级高频词汇",
            DifficultyLevel.ADVANCED: "四级难点词汇",
        }

        knowledge_context = f"重点关注：{', '.join(knowledge_points)}" if knowledge_points else ""

        if question_type == QuestionType.MULTIPLE_CHOICE:
            return f"""
请生成一道英语四级词汇选择题，难度：{difficulty_map[difficulty_level]}。{knowledge_context}

要求：
1. 题干要有明确的语境
2. 提供4个选项，只有1个正确答案
3. 干扰项要有一定迷惑性
4. 包含详细解析

请按以下JSON格式返回：
{{
    "title": "题目标题",
    "content": {{
        "text": "题干内容（空格处用___表示）",
        "options": ["A选项", "B选项", "C选项", "D选项"]
    }},
    "correct_answer": {{
        "option": "A",
        "explanation": "正确答案解释"
    }},
    "analysis": "详细解析，包括词汇用法说明",
    "grading_criteria": {{"accuracy": 1.0}}
}}
"""
        elif question_type == QuestionType.FILL_BLANK:
            return f"""
请生成一道英语四级词汇填空题，难度：{difficulty_map[difficulty_level]}。{knowledge_context}

要求：
1. 提供有意义的语境
2. 挖空的词汇要符合难度要求
3. 可以提供首字母提示
4. 包含详细解析

请按以下JSON格式返回：
{{
    "title": "词汇填空题",
    "content": {{
        "text": "题干内容（空格处用___表示）",
        "hint": "首字母提示（可选）"
    }},
    "correct_answer": {{
        "word": "正确单词",
        "explanation": "词汇解释"
    }},
    "analysis": "详细解析，包括词汇用法和语法说明"
}}
"""
        else:
            return f"""
请生成一道英语四级{question_type.value}题目，难度：{difficulty_map[difficulty_level]}。{knowledge_context}

请按以下JSON格式返回：
{{
    "title": "题目标题",
    "content": {{"text": "题目内容"}},
    "correct_answer": {{"answer": "正确答案"}},
    "analysis": "详细解析"
}}
"""

    async def _build_listening_prompt(
        self, difficulty_level: DifficultyLevel, knowledge_points: list[str] | None
    ) -> str:
        """构建听力题目生成prompt."""
        return f"""
请生成一段英语四级听力材料和相关题目，难度：{difficulty_level.name.lower()}。

要求：
1. 听力材料长度150-200词
2. 内容贴近大学生生活
3. 语言自然，语速适中
4. 生成3-4个理解题目
5. 包含细节理解和推理判断

请按以下JSON格式返回：
{{
    "title": "听力理解",
    "content": {{
        "audio_script": "听力文本",
        "questions": [
            {{
                "question": "问题1",
                "options": ["A", "B", "C", "D"],
                "correct": "A"
            }}
        ]
    }},
    "correct_answer": {{"answers": ["A", "B", "C"]}},
    "analysis": "听力解析和答题技巧"
}}
"""

    async def _build_reading_prompt(
        self, difficulty_level: DifficultyLevel, knowledge_points: list[str] | None
    ) -> str:
        """构建阅读题目生成prompt."""
        return f"""
请生成一篇英语四级阅读理解文章和4个相关题目，难度：{difficulty_level.name.lower()}。

要求：
1. 文章长度250-300词
2. 题材丰富（科技、文化、社会等）
3. 题目类型包括：主旨大意、细节理解、推理判断、词汇理解
4. 选项设计要合理

请按以下JSON格式返回：
{{
    "passage": "阅读文章内容",
    "questions": [
        {{
            "title": "问题1",
            "question": "具体问题",
            "options": ["A选项", "B选项", "C选项", "D选项"],
            "correct_answer": {{"option": "A"}},
            "analysis": "答案解析"
        }}
    ]
}}
"""

    async def _build_writing_prompt(
        self, difficulty_level: DifficultyLevel, knowledge_points: list[str] | None
    ) -> str:
        """构建写作题目生成prompt."""
        return f"""
请生成一道英语四级写作题目，难度：{difficulty_level.name.lower()}。

要求：
1. 题目类型：议论文、说明文或应用文
2. 贴近大学生生活和社会热点
3. 字数要求：120-180词
4. 提供写作提纲和范文

请按以下JSON格式返回：
{{
    "title": "写作题目",
    "content": {{
        "instruction": "写作指令",
        "requirements": "具体要求",
        "outline": "写作提纲"
    }},
    "correct_answer": {{
        "sample_essay": "范文",
        "key_points": ["要点1", "要点2", "要点3"]
    }},
    "analysis": "写作指导和评分标准说明"
}}
"""

    async def _build_translation_prompt(
        self,
        question_type: QuestionType,
        difficulty_level: DifficultyLevel,
        knowledge_points: list[str] | None,
    ) -> str:
        """构建翻译题目生成prompt."""
        direction = "中译英" if question_type == QuestionType.TRANSLATION_CN_TO_EN else "英译中"

        return f"""
请生成一道英语四级{direction}翻译题目，难度：{difficulty_level.name.lower()}。

要求：
1. 内容体现中国文化特色（如果是中译英）
2. 句子结构适中，词汇难度适当
3. 涉及重要语法点和固定搭配
4. 提供标准译文和评分要点

请按以下JSON格式返回：
{{
    "title": "{direction}翻译",
    "content": {{
        "source_text": "原文",
        "instruction": "翻译指令"
    }},
    "correct_answer": {{
        "target_text": "标准译文",
        "key_phrases": ["重点短语1", "重点短语2"]
    }},
    "analysis": "翻译要点和常见错误分析"
}}
"""

    # ==================== 私有方法：AI调用辅助 ====================

    async def _safe_ai_completion(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 800
    ) -> dict[str, Any] | None:
        """安全的AI调用包装器."""
        try:
            success, ai_response, error_msg = await self.deepseek_service.generate_completion(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if success and ai_response:
                return ai_response
            else:
                # 记录错误但不抛出，让调用方处理
                return None
        except Exception:
            # 记录错误但不抛出，让调用方处理
            return None

    # ==================== 私有方法：AI响应解析 ====================

    def _parse_ai_question_response(
        self,
        ai_response: dict[str, Any],
        question_type: QuestionType,
        training_type: TrainingType,
        difficulty_level: DifficultyLevel,
    ) -> dict[str, Any]:
        """解析AI生成的题目响应."""
        try:
            # 从AI响应中提取内容
            content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 尝试解析JSON格式
            if content.strip().startswith("{"):
                return json.loads(content)  # type: ignore[no-any-return]
            else:
                # 如果不是JSON格式，进行简单解析
                return self._parse_plain_text_response(content, question_type)

        except (json.JSONDecodeError, KeyError, IndexError):
            # AI响应解析失败，返回默认结构
            return self._get_default_question_structure(question_type, training_type)

    def _parse_ai_reading_response(
        self, ai_response: dict[str, Any], difficulty_level: DifficultyLevel
    ) -> dict[str, Any]:
        """解析AI生成的阅读理解响应."""
        try:
            content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return cast(dict[str, Any], json.loads(content))
        except Exception:
            # 返回默认阅读材料
            return {
                "passage": "默认阅读材料...",
                "questions": [
                    {
                        "title": "阅读理解",
                        "question": "根据文章内容，以下说法正确的是：",
                        "options": ["选项A", "选项B", "选项C", "选项D"],
                        "correct_answer": {"option": "A"},
                        "analysis": "答案解析",
                    }
                ],
            }

    def _parse_plain_text_response(
        self, content: str, question_type: QuestionType
    ) -> dict[str, Any]:
        """解析纯文本格式的AI响应."""
        # 简单的文本解析逻辑
        return {
            "title": f"{question_type.value} 题目",
            "content": {"text": content[:200] + "..."},
            "correct_answer": {"answer": "默认答案"},
            "analysis": "AI生成的解析",
        }

    def _get_default_question_structure(
        self, question_type: QuestionType, training_type: TrainingType
    ) -> dict[str, Any]:
        """获取默认题目结构."""
        return {
            "title": f"{training_type.value} - {question_type.value}",
            "content": {"text": "默认题目内容"},
            "correct_answer": {"answer": "默认答案"},
            "analysis": "默认解析",
            "grading_criteria": {"accuracy": 1.0},
        }

    # ==================== 私有方法：批改和评分 ====================

    async def _grade_answer(self, question: Question, user_answer: dict[str, Any]) -> GradingResult:
        """批改答案."""
        # 根据题目类型进行不同的批改逻辑
        if question.question_type in [
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        ]:
            return await self._grade_choice_question(question, user_answer)
        elif question.question_type == QuestionType.FILL_BLANK:
            return await self._grade_fill_blank_question(question, user_answer)
        elif question.question_type == QuestionType.ESSAY:
            return await self._grade_essay_question(question, user_answer)
        elif question.question_type in [
            QuestionType.TRANSLATION_EN_TO_CN,
            QuestionType.TRANSLATION_CN_TO_EN,
        ]:
            return await self._grade_translation_question(question, user_answer)
        else:
            # 默认批改逻辑
            return GradingResult(
                is_correct=False,
                score=0.0,
                max_score=question.max_score,
                grading_status=GradingStatus.COMPLETED,
                ai_feedback={"message": "批改类型暂不支持"},
                ai_confidence=0.0,
                knowledge_points_mastered=[],
                knowledge_points_weak=question.knowledge_points,
                detailed_feedback="批改类型暂不支持",
                improvement_suggestions=[],
            )

    async def _grade_choice_question(
        self, question: Question, user_answer: dict[str, Any]
    ) -> GradingResult:
        """批改选择题."""
        user_choice = user_answer.get("option", "").upper()
        correct_choice = question.correct_answer.get("option", "").upper()

        is_correct = user_choice == correct_choice
        score = question.max_score if is_correct else 0.0

        return GradingResult(
            is_correct=is_correct,
            score=score,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={
                "user_choice": user_choice,
                "correct_choice": correct_choice,
                "explanation": question.correct_answer.get("explanation", ""),
            },
            ai_confidence=1.0,  # 选择题批改置信度高
            knowledge_points_mastered=question.knowledge_points if is_correct else [],
            knowledge_points_weak=[] if is_correct else question.knowledge_points,
            detailed_feedback=question.correct_answer.get("explanation", ""),
            improvement_suggestions=([] if is_correct else ["请仔细阅读题目，注意关键词"]),
        )

    async def _grade_fill_blank_question(
        self, question: Question, user_answer: dict[str, Any]
    ) -> GradingResult:
        """批改填空题."""
        user_words = user_answer.get("words", [])
        if isinstance(user_words, str):
            user_words = [user_words]

        correct_words = question.correct_answer.get("words", [])
        if isinstance(correct_words, str):
            correct_words = [correct_words]

        # 计算正确率
        correct_count = 0
        total_count = len(correct_words)

        for i, correct_word in enumerate(correct_words):
            if i < len(user_words):
                user_word = user_words[i].strip().lower()
                if user_word == correct_word.lower():
                    correct_count += 1

        accuracy = correct_count / total_count if total_count > 0 else 0.0
        score = question.max_score * accuracy

        return GradingResult(
            is_correct=accuracy >= 0.8,
            score=score,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={
                "accuracy": accuracy,
                "correct_words": correct_words,
                "user_words": user_words,
            },
            ai_confidence=0.9,
            knowledge_points_mastered=(question.knowledge_points if accuracy >= 0.8 else []),
            knowledge_points_weak=[] if accuracy >= 0.8 else question.knowledge_points,
            detailed_feedback=f"填空准确率: {accuracy:.1%}",
            improvement_suggestions=([] if accuracy >= 0.8 else ["注意单词拼写和形式变化"]),
        )

    async def _grade_essay_question(
        self, question: Question, user_answer: dict[str, Any]
    ) -> GradingResult:
        """批改作文题目（使用AI）."""
        essay_text = user_answer.get("text", "")

        if not essay_text.strip():
            return GradingResult(
                is_correct=False,
                score=0.0,
                max_score=question.max_score,
                grading_status=GradingStatus.COMPLETED,
                ai_feedback={"error": "作文内容为空"},
                ai_confidence=1.0,
                knowledge_points_mastered=[],
                knowledge_points_weak=question.knowledge_points,
                detailed_feedback="作文内容为空",
                improvement_suggestions=["请撰写完整的作文内容"],
            )

        # 构建AI批改prompt
        grading_prompt = f"""
请按照英语四级写作评分标准批改以下作文：

题目：{question.title}
要求：{question.content.get("instruction", "")}

学生作文：
{essay_text}

请从以下几个方面评分（满分{question.max_score}分）：
1. 内容相关性和完整性（{question.max_score * 0.35:.1f}分）
2. 语言准确性和丰富性（{question.max_score * 0.35:.1f}分）
3. 篇章结构和逻辑性（{question.max_score * 0.3:.1f}分）

请返回JSON格式：
{{
    "total_score": 总分,
    "content_score": 内容得分,
    "language_score": 语言得分,
    "structure_score": 结构得分,
    "feedback": "具体反馈意见",
    "strengths": ["优点1", "优点2"],
    "improvements": ["改进建议1", "改进建议2"],
    "confidence": 批改置信度(0-1)
}}
"""

        try:
            ai_response = await self._safe_ai_completion(
                grading_prompt, temperature=0.3, max_tokens=800
            )

            if ai_response:
                content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                grading_result_data = json.loads(content)

                total_score = min(grading_result_data.get("total_score", 0), question.max_score)
                is_correct = total_score >= question.max_score * 0.6  # 60%为及格线

                return GradingResult(
                    is_correct=is_correct,
                    score=total_score,
                    max_score=question.max_score,
                    grading_status=GradingStatus.COMPLETED,
                    ai_feedback=grading_result_data,
                    ai_confidence=grading_result_data.get("confidence", 0.8),
                    knowledge_points_mastered=(question.knowledge_points if is_correct else []),
                    knowledge_points_weak=([] if is_correct else question.knowledge_points),
                    detailed_feedback=grading_result_data.get("feedback", ""),
                    improvement_suggestions=grading_result_data.get("improvements", []),
                )
            else:
                raise ValueError("AI响应为空")

        except Exception:
            # AI批改失败，使用基础评分
            word_count = len(essay_text.split())
            basic_score = min(question.max_score * 0.6, question.max_score * word_count / 150)

            return GradingResult(
                is_correct=basic_score >= question.max_score * 0.6,
                score=basic_score,
                max_score=question.max_score,
                grading_status=GradingStatus.REVIEWING,
                ai_feedback={
                    "error": "AI批改失败，需要人工批改",
                    "word_count": word_count,
                },
                ai_confidence=0.3,
                knowledge_points_mastered=[],
                knowledge_points_weak=question.knowledge_points,
                detailed_feedback="AI批改失败，请等待人工批改",
                improvement_suggestions=["请等待详细批改结果"],
            )

    async def _grade_translation_question(
        self, question: Question, user_answer: dict[str, Any]
    ) -> GradingResult:
        """批改翻译题目（使用AI）."""
        user_translation = user_answer.get("text", "")

        if not user_translation.strip():
            return GradingResult(
                is_correct=False,
                score=0.0,
                max_score=question.max_score,
                grading_status=GradingStatus.COMPLETED,
                ai_feedback={"error": "翻译内容为空"},
                ai_confidence=1.0,
                knowledge_points_mastered=[],
                knowledge_points_weak=question.knowledge_points,
                detailed_feedback="翻译内容为空",
                improvement_suggestions=["请提供翻译内容"],
            )

        # 构建AI翻译批改prompt
        source_text = question.content.get("source_text", "")
        reference_translation = question.correct_answer.get("target_text", "")

        grading_prompt = f"""
请批改以下翻译（满分{question.max_score}分）：

原文：{source_text}
参考译文：{reference_translation}
学生译文：{user_translation}

评分维度：
1. 准确性（{question.max_score * 0.5:.1f}分）：译文准确传达原文意思
2. 流畅性（{question.max_score * 0.3:.1f}分）：译文符合目标语言表达习惯
3. 完整性（{question.max_score * 0.2:.1f}分）：无重要信息遗漏

请返回JSON格式：
{{
    "total_score": 总分,
    "accuracy_score": 准确性得分,
    "fluency_score": 流畅性得分,
    "completeness_score": 完整性得分,
    "feedback": "具体批改意见",
    "errors": ["错误1", "错误2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "confidence": 批改置信度(0-1)
}}
"""

        try:
            ai_response = await self._safe_ai_completion(
                grading_prompt, temperature=0.3, max_tokens=600
            )

            if ai_response:
                content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                grading_result_data = json.loads(content)

                total_score = min(grading_result_data.get("total_score", 0), question.max_score)
                is_correct = total_score >= question.max_score * 0.6

                return GradingResult(
                    is_correct=is_correct,
                    score=total_score,
                    max_score=question.max_score,
                    grading_status=GradingStatus.COMPLETED,
                    ai_feedback=grading_result_data,
                    ai_confidence=grading_result_data.get("confidence", 0.8),
                    knowledge_points_mastered=(question.knowledge_points if is_correct else []),
                    knowledge_points_weak=([] if is_correct else question.knowledge_points),
                    detailed_feedback=grading_result_data.get("feedback", ""),
                    improvement_suggestions=grading_result_data.get("suggestions", []),
                )
            else:
                raise ValueError("AI响应为空")

        except Exception:
            # AI批改失败，使用基础评分
            similarity_score = self._calculate_text_similarity(
                user_translation, reference_translation
            )
            basic_score = question.max_score * similarity_score

            return GradingResult(
                is_correct=basic_score >= question.max_score * 0.6,
                score=basic_score,
                max_score=question.max_score,
                grading_status=GradingStatus.REVIEWING,
                ai_feedback={"error": "AI批改失败", "similarity": similarity_score},
                ai_confidence=0.4,
                knowledge_points_mastered=[],
                knowledge_points_weak=question.knowledge_points,
                detailed_feedback="AI批改失败，请等待人工批改",
                improvement_suggestions=["请等待详细批改结果"],
            )

    # ==================== 私有方法：辅助功能 ====================

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    async def _get_backup_question(
        self,
        training_type: TrainingType,
        difficulty_level: DifficultyLevel,
        question_type: QuestionType,
    ) -> Question | None:
        """获取备用题目."""
        stmt = (
            select(Question)
            .where(
                and_(
                    Question.training_type == training_type,
                    Question.difficulty_level == difficulty_level,
                    Question.question_type == question_type,
                    Question.is_active == True,  # noqa: E712
                )
            )
            .order_by(func.random())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def _update_question_statistics(self, question: Question) -> None:
        """更新题目统计数据."""
        # 计算平均分数和正确率
        stmt = select(
            func.avg(TrainingRecord.score).label("avg_score"),
            func.avg(func.cast(TrainingRecord.is_correct, Float)).label("correct_rate"),
        ).where(TrainingRecord.question_id == question.id)

        result = await self.db.execute(stmt)
        stats = result.first()

        if stats:
            question.average_score = float(stats.avg_score or 0)
            question.correct_rate = float(stats.correct_rate or 0)

    async def _build_session_response(self, session: TrainingSession) -> TrainingSessionResponse:
        """构建训练会话响应数据."""
        # 计算正确率
        accuracy_rate = 0.0
        if session.total_questions > 0:
            accuracy_rate = round(session.correct_answers / session.total_questions * 100, 2)

        return TrainingSessionResponse(
            id=session.id,
            student_id=session.student_id,
            session_name=session.session_name,
            session_type=session.session_type,
            training_type=session.session_type,  # 别名字段
            description=session.description,
            difficulty_level=session.difficulty_level,
            question_count=session.question_count,
            time_limit=session.time_limit,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            completion_time=session.time_spent,  # 使用time_spent作为completion_time
            total_questions=session.total_questions,
            correct_answers=session.correct_answers,
            total_score=session.total_score,
            time_spent=session.time_spent,
            accuracy_rate=accuracy_rate,
            initial_level=session.initial_level,
            final_level=session.final_level,
            adaptation_data=session.adaptation_data,
            created_at=session.created_at,
            updated_at=session.updated_at or session.created_at,
        )

    async def _build_question_response(self, question: Question) -> QuestionResponse:
        """构建题目响应数据（不包含答案）."""
        return QuestionResponse(
            id=question.id,
            question_type=question.question_type,
            training_type=question.training_type,
            title=question.title,
            content=question.content,
            difficulty_level=question.difficulty_level,
            max_score=question.max_score,
            time_limit=question.time_limit,
            knowledge_points=question.knowledge_points,
            tags=question.tags,
            is_active=question.is_active,
            usage_count=question.usage_count,
            average_score=question.average_score,
            correct_rate=question.correct_rate,
            created_at=question.created_at,
            updated_at=question.updated_at or question.created_at,
        )
