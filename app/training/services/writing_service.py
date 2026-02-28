"""英语四级写作标准库 - 服务层"""

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.services.cache_service import CacheType, get_cache_service
from app.training.models.writing_models import (
    WritingDifficulty,
    WritingGrammarRuleModel,
    WritingScoreLevel,
    WritingSubmissionModel,
    WritingTaskModel,
    WritingTemplateModel,
    WritingType,
    WritingVocabularyModel,
)
from app.training.schemas.writing_schemas import (
    GrammarCheckResult,
    WritingRecommendation,
    WritingStatistics,
    WritingSubmissionCreate,
    WritingTaskCreate,
    WritingTemplateCreate,
    WritingTemplateUpdate,
    WritingVocabularyCreate,
)

logger = logging.getLogger(__name__)


class WritingService:
    """
    英语四级写作标准库服务类

    实现写作评分引擎、模板库管理、智能写作辅助等功能
    """

    def __init__(self: "WritingService", db: AsyncSession) -> None:
        self.db = db
        self.deepseek_service = DeepSeekService()
        self.cache_service = None

    # ==================== 写作模板管理 ====================

    async def create_template(
        self: "WritingService", data: WritingTemplateCreate
    ) -> WritingTemplateModel:
        """创建写作模板"""
        logger.info(f"创建写作模板: {data.template_name}")

        template = WritingTemplateModel(
            template_name=data.template_name,
            writing_type=data.writing_type,
            difficulty=data.difficulty,
            template_structure=data.template_structure,
            opening_sentences=data.opening_sentences,
            transition_phrases=data.transition_phrases,
            conclusion_sentences=data.conclusion_sentences,
            example_essay=data.example_essay,
            usage_instructions=data.usage_instructions,
            key_phrases=data.key_phrases,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(f"写作模板创建成功: ID={template.id}")  # type: ignore[has-type]
        return template

    async def get_templates(
        self: "WritingService",
        skip: int = 0,
        limit: int = 10,
        writing_type: WritingType | None = None,
        difficulty: WritingDifficulty | None = None,
        is_recommended: bool | None = None,
    ) -> tuple[list[WritingTemplateModel], int]:
        """获取写作模板列表"""
        logger.info(f"查询写作模板列表: type={writing_type}, difficulty={difficulty}")

        # 构建查询条件
        conditions: list[Any] = [WritingTemplateModel.is_active.is_(True)]
        if writing_type:
            conditions.append(WritingTemplateModel.writing_type == writing_type)
        if difficulty:
            conditions.append(WritingTemplateModel.difficulty == difficulty)
        if is_recommended is not None:
            conditions.append(WritingTemplateModel.is_recommended.is_(is_recommended))

        # 查询总数
        count_query = select(func.count(WritingTemplateModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(WritingTemplateModel)
            .where(and_(*conditions))
            .order_by(
                desc(WritingTemplateModel.is_recommended),
                desc(WritingTemplateModel.average_score),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        templates = result.scalars().all()

        return list(templates), total

    async def get_template(
        self: "WritingService", template_id: int
    ) -> WritingTemplateModel | None:
        """获取写作模板详情"""
        logger.info(f"查询写作模板详情: {template_id}")

        query = select(WritingTemplateModel).where(WritingTemplateModel.id == template_id)  # type: ignore[has-type]
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_template(
        self: "WritingService", template_id: int, data: WritingTemplateUpdate
    ) -> WritingTemplateModel | None:
        """更新写作模板"""
        logger.info(f"更新写作模板: {template_id}")

        template = await self.get_template(template_id)
        if not template:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()  # type: ignore[has-type]
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(f"写作模板更新成功: ID={template.id}")  # type: ignore[has-type]
        return template

    # ==================== 写作任务管理 ====================

    async def create_task(
        self: "WritingService", data: WritingTaskCreate
    ) -> WritingTaskModel:
        """创建写作任务"""
        logger.info(f"创建写作任务: {data.task_title}")

        task = WritingTaskModel(
            task_title=data.task_title,
            task_prompt=data.task_prompt,
            writing_type=data.writing_type,
            difficulty=data.difficulty,
            word_count_min=data.word_count_min,
            word_count_max=data.word_count_max,
            time_limit_minutes=data.time_limit_minutes,
            scoring_criteria=data.scoring_criteria,
            sample_answers=data.sample_answers,
            keywords=data.keywords,
            outline_suggestions=data.outline_suggestions,
            template_id=data.template_id,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        logger.info(f"写作任务创建成功: ID={task.id}")  # type: ignore[has-type]
        return task

    async def get_tasks(
        self: "WritingService",
        skip: int = 0,
        limit: int = 10,
        writing_type: WritingType | None = None,
        difficulty: WritingDifficulty | None = None,
    ) -> tuple[list[WritingTaskModel], int]:
        """获取写作任务列表"""
        logger.info(f"查询写作任务列表: type={writing_type}, difficulty={difficulty}")

        # 构建查询条件
        conditions: list[Any] = [WritingTaskModel.is_active.is_(True)]
        if writing_type:
            conditions.append(WritingTaskModel.writing_type == writing_type)
        if difficulty:
            conditions.append(WritingTaskModel.difficulty == difficulty)

        # 查询总数
        count_query = select(func.count(WritingTaskModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(WritingTaskModel)
            .where(and_(*conditions))
            .options(selectinload(WritingTaskModel.template))
            .order_by(desc(WritingTaskModel.created_at))  # type: ignore[has-type]
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def get_task(self: "WritingService", task_id: int) -> WritingTaskModel | None:
        """获取写作任务详情"""
        logger.info(f"查询写作任务详情: {task_id}")

        query = (
            select(WritingTaskModel)
            .where(WritingTaskModel.id == task_id)  # type: ignore[has-type]
            .options(selectinload(WritingTaskModel.template))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== 写作提交和评分 ====================

    async def submit_essay(
        self: "WritingService", user_id: int, data: WritingSubmissionCreate
    ) -> WritingSubmissionModel:
        """提交作文"""
        logger.info(f"用户 {user_id} 提交作文: task={data.task_id}")

        # 计算字数
        word_count = len(data.essay_content.split())

        submission = WritingSubmissionModel(
            user_id=user_id,
            task_id=data.task_id,
            essay_content=data.essay_content,
            word_count=word_count,
            started_at=datetime.utcnow() - timedelta(minutes=data.writing_time_minutes),
            submitted_at=datetime.utcnow(),
            writing_time_minutes=data.writing_time_minutes,
        )

        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)

        # 自动评分
        await self._grade_essay(submission)
        await self.db.refresh(submission)  # 刷新以获取AI评分后的数据

        logger.info(f"作文提交成功: ID={submission.id}")  # type: ignore[has-type]
        return submission

    async def _grade_essay(
        self: "WritingService", submission: WritingSubmissionModel
    ) -> None:
        """AI评分作文"""
        logger.info(f"开始评分作文: {submission.id}")  # type: ignore[has-type]

        try:
            # 获取任务信息
            task = await self.get_task(int(submission.task_id))
            if not task:
                return

            # 首先检查缓存
            cached_result = await self._get_cached_grade(
                str(submission.essay_content), int(submission.task_id)
            )

            if cached_result:
                logger.info("使用缓存的评分结果")
                # 使用缓存结果
                submission.total_score = cached_result["total_score"]
                score_level_raw = cached_result.get("score_level", "fair").lower()
                score_level_map = {
                    "excellent": WritingScoreLevel.EXCELLENT,
                    "good": WritingScoreLevel.GOOD,
                    "fair": WritingScoreLevel.FAIR,
                    "poor": WritingScoreLevel.POOR,
                }
                submission.score_level = score_level_map.get(
                    score_level_raw, WritingScoreLevel.FAIR
                )
                submission.content_score = cached_result["content_score"]
                submission.structure_score = cached_result["structure_score"]
                submission.language_score = cached_result["language_score"]
                submission.grammar_score = cached_result["grammar_score"]
                submission.ai_feedback = cached_result["feedback"]
                submission.strengths = cached_result["strengths"]
                submission.weaknesses = cached_result["weaknesses"]
                submission.improvement_suggestions = cached_result["suggestions"]
                submission.grammar_errors = cached_result.get("grammar_errors", [])
                submission.vocabulary_suggestions = cached_result.get(
                    "vocabulary_suggestions", []
                )
                submission.structure_analysis = cached_result.get(
                    "structure_analysis", ""
                )
                submission.is_graded = True
                await self.db.commit()
                return

            # 构建评分prompt
            grading_prompt = self._build_grading_prompt(
                str(submission.essay_content), task
            )

            # 调用AI评分
            (
                success,
                ai_response,
                error_msg,
            ) = await self.deepseek_service.generate_completion(
                prompt=grading_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            if (
                success
                and ai_response
                and isinstance(ai_response, dict)
                and "choices" in ai_response
            ):
                content = str(ai_response["choices"][0]["message"]["content"])
                grading_result = self._parse_grading_result(content)

                # 更新评分结果
                submission.total_score = grading_result["total_score"]
                # 标准化score_level
                score_level_raw = grading_result.get("score_level", "fair").lower()
                score_level_map = {
                    "excellent": WritingScoreLevel.EXCELLENT,
                    "good": WritingScoreLevel.GOOD,
                    "fair": WritingScoreLevel.FAIR,
                    "poor": WritingScoreLevel.POOR,
                }
                submission.score_level = score_level_map.get(
                    score_level_raw, WritingScoreLevel.FAIR
                )
                submission.content_score = grading_result["content_score"]
                submission.structure_score = grading_result["structure_score"]
                submission.language_score = grading_result["language_score"]
                submission.grammar_score = grading_result["grammar_score"]
                submission.ai_feedback = grading_result["feedback"]
                submission.strengths = grading_result["strengths"]
                submission.weaknesses = grading_result["weaknesses"]
                submission.improvement_suggestions = grading_result["suggestions"]
                # AI反馈字段
                submission.grammar_errors = grading_result.get("grammar_errors", [])
                submission.vocabulary_suggestions = grading_result.get(
                    "vocabulary_suggestions", []
                )
                submission.structure_analysis = grading_result.get(
                    "structure_analysis", ""
                )
                submission.is_graded = True

                await self.db.commit()

                # 缓存评分结果
                await self._set_cached_grade(
                    str(submission.essay_content),
                    int(submission.task_id),
                    grading_result,
                )

                logger.info(f"作文评分完成: {submission.id}, 得分: {submission.total_score}")

        except Exception as e:
            logger.error(f"作文评分失败: {e}")
            # 设置默认评分
            submission.total_score = 8.0
            submission.score_level = WritingScoreLevel.FAIR
            submission.is_graded = True
            await self.db.commit()

    async def _get_cached_grade(self, text: str, task_id: int) -> dict[str, Any] | None:
        """获取缓存的评分结果"""
        try:
            if self.cache_service is None:
                self.cache_service = await get_cache_service()

            cache_key = hashlib.sha256(f"{text}:{task_id}".encode()).hexdigest()

            logger.info(f"Checking grading cache for key: {cache_key[:8]}...")

            cached_result = await self.cache_service.get(
                cache_key, cache_type=CacheType.AI_RESULT
            )

            if cached_result:
                logger.info(f"Cache hit for grading result: {cache_key[:8]}")

            return cached_result

        except Exception as e:
            logger.warning(f"Failed to get cached grade: {e}")
            return None

    async def _set_cached_grade(
        self, text: str, task_id: int, grade_result: dict[str, Any]
    ) -> None:
        """缓存评分结果"""
        try:
            if self.cache_service is None:
                self.cache_service = await get_cache_service()

            cache_key = hashlib.sha256(f"{text}:{task_id}".encode()).hexdigest()

            logger.info(f"Caching grading result for key: {cache_key[:8]}...")

            # 缓存24小时
            await self.cache_service.set(
                cache_key,
                grade_result,
                cache_type=CacheType.AI_RESULT,
                ttl=60 * 60 * 24,
            )

        except Exception as e:
            logger.warning(f"Failed to set cached grade: {e}")

    def _build_grading_prompt(
        self: "WritingService", essay: str, task: WritingTaskModel
    ) -> str:
        """构建评分prompt"""
        return f"""
请对以下英语四级作文进行评分，满分15分，按照以下标准：

题目要求：{task.task_prompt}
字数要求：{task.word_count_min}-{task.word_count_max}字
写作类型：{task.writing_type}

作文内容：
{essay}

评分标准：
- 内容分(4分)：切题、内容充实、观点明确
- 结构分(4分)：结构清晰、逻辑性强、过渡自然
- 语言分(4分)：用词准确、句式多样、表达流畅
- 语法分(3分)：语法正确、拼写无误

请按以下JSON格式返回评分结果：
{{
    "total_score": 总分(0-15),
    "score_level": "评分等级(excellent/good/fair/poor)",
    "content_score": 内容分(0-4),
    "structure_score": 结构分(0-4),
    "language_score": 语言分(0-4),
    "grammar_score": 语法分(0-3),
    "feedback": {{"overall": "总体评价", "details": "详细分析"}},
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": ["建议1", "建议2"]
}}
"""

    def _parse_grading_result(self: "WritingService", content: str) -> dict[str, Any]:
        """解析评分结果"""
        try:
            import json

            # 提取JSON部分
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return dict(result)
        except Exception as e:
            logger.error(f"解析评分结果失败: {e}")

        # 返回默认结果
        return {
            "total_score": 8.0,
            "score_level": "fair",
            "content_score": 2.0,
            "structure_score": 2.0,
            "language_score": 2.0,
            "grammar_score": 2.0,
            "feedback": {"overall": "评分解析失败", "details": "请联系管理员"},
            "strengths": ["基本完成任务"],
            "weaknesses": ["需要改进"],
            "suggestions": ["多练习写作"],
            "grammar_errors": [],
            "vocabulary_suggestions": [],
            "structure_analysis": "",
        }

    # ==================== 语法检查 ====================

    async def check_grammar(self: "WritingService", text: str) -> GrammarCheckResult:
        """检查语法错误"""
        logger.info("执行语法检查")

        try:
            # 获取语法规则
            grammar_rules = await self._get_grammar_rules()

            errors = []
            suggestions = []
            corrected_text = text

            # 应用语法规则检查
            for rule in grammar_rules:
                if rule.pattern_regex:
                    matches = re.finditer(str(rule.pattern_regex), text, re.IGNORECASE)
                    for match in matches:
                        errors.append(
                            {
                                "rule_name": rule.rule_name,
                                "position": match.span(),
                                "text": match.group(),
                                "description": rule.rule_description,
                                "severity": rule.severity_level,
                            }
                        )

                        suggestions.append(
                            {
                                "original": match.group(),
                                "suggestion": rule.correction_template,
                                "explanation": rule.explanation,
                            }
                        )

            # 计算语法得分
            grammar_score = max(0.0, 3.0 - len(errors) * 0.2)

            return GrammarCheckResult(
                error_count=len(errors),
                errors=errors,
                suggestions=suggestions,
                corrected_text=corrected_text,
                grammar_score=grammar_score,
            )

        except Exception as e:
            logger.error(f"语法检查失败: {e}")
            return GrammarCheckResult(
                error_count=0,
                errors=[],
                suggestions=[],
                corrected_text=text,
                grammar_score=3.0,
            )

    async def _get_grammar_rules(
        self: "WritingService",
    ) -> list[WritingGrammarRuleModel]:
        """获取语法规则"""
        query = select(WritingGrammarRuleModel).where(
            WritingGrammarRuleModel.is_active.is_(True)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== 词汇管理 ====================

    async def create_vocabulary(
        self: "WritingService", data: WritingVocabularyCreate
    ) -> WritingVocabularyModel:
        """创建写作词汇"""
        logger.info(f"创建写作词汇: {data.word_or_phrase}")

        vocabulary = WritingVocabularyModel(
            word_or_phrase=data.word_or_phrase,
            part_of_speech=data.part_of_speech,
            meaning=data.meaning,
            category=data.category,
            writing_type=data.writing_type,
            difficulty_level=data.difficulty_level,
            usage_examples=data.usage_examples,
            synonyms=data.synonyms,
            antonyms=data.antonyms,
            collocations=data.collocations,
        )

        self.db.add(vocabulary)
        await self.db.commit()
        await self.db.refresh(vocabulary)

        logger.info(f"写作词汇创建成功: ID={vocabulary.id}")  # type: ignore[has-type]
        return vocabulary

    async def get_vocabulary_list(
        self: "WritingService",
        skip: int = 0,
        limit: int = 10,
        category: str | None = None,
        writing_type: WritingType | None = None,
        difficulty_level: WritingDifficulty | None = None,
    ) -> tuple[list[WritingVocabularyModel], int]:
        """获取写作词汇列表"""
        logger.info(f"查询写作词汇列表: category={category}, type={writing_type}")

        # 构建查询条件
        conditions: list[Any] = [WritingVocabularyModel.is_active.is_(True)]
        if category:
            conditions.append(WritingVocabularyModel.category == category)
        if writing_type:
            conditions.append(WritingVocabularyModel.writing_type == writing_type)
        if difficulty_level:
            conditions.append(
                WritingVocabularyModel.difficulty_level == difficulty_level
            )

        # 查询总数
        count_query = select(func.count(WritingVocabularyModel.id)).where(and_(*conditions))  # type: ignore[has-type]
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(WritingVocabularyModel)
            .where(and_(*conditions))
            .order_by(
                desc(WritingVocabularyModel.is_recommended),
                desc(WritingVocabularyModel.effectiveness_score),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        vocabulary_list = result.scalars().all()

        return list(vocabulary_list), total

    # ==================== 用户提交管理 ====================

    async def get_user_submissions(
        self: "WritingService", user_id: int, skip: int = 0, limit: int = 10
    ) -> tuple[list[WritingSubmissionModel], int]:
        """获取用户的写作提交列表"""
        logger.info(f"查询用户 {user_id} 的写作提交")

        # 查询总数
        count_query = select(func.count(WritingSubmissionModel.id)).where(  # type: ignore[has-type]
            WritingSubmissionModel.user_id == user_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(WritingSubmissionModel)
            .where(WritingSubmissionModel.user_id == user_id)
            .options(selectinload(WritingSubmissionModel.task))
            .order_by(desc(WritingSubmissionModel.created_at))  # type: ignore[has-type]
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        submissions = result.scalars().all()

        return list(submissions), total

    async def get_submission(
        self: "WritingService", submission_id: int, user_id: int | None = None
    ) -> WritingSubmissionModel | None:
        """获取写作提交详情"""
        logger.info(f"查询写作提交详情: {submission_id}")

        conditions: list[Any] = [WritingSubmissionModel.id == submission_id]  # type: ignore[has-type]
        if user_id:
            conditions.append(WritingSubmissionModel.user_id == user_id)

        query = (
            select(WritingSubmissionModel)
            .where(and_(*conditions))
            .options(selectinload(WritingSubmissionModel.task))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def regrade_submission(
        self: "WritingService", submission_id: int, user_id: int
    ) -> WritingSubmissionModel | None:
        """重新评分作文"""
        submission = await self.get_submission(submission_id, user_id)
        if not submission:
            return None

        # 重新调用AI评分
        await self._grade_essay(submission)
        await self.db.refresh(submission)

        logger.info(f"作文重新评分完成: {submission_id}")
        return submission

    # ==================== 统计和推荐 ====================

    async def get_user_statistics(
        self: "WritingService", user_id: int
    ) -> WritingStatistics:
        """获取用户写作统计数据"""
        logger.info(f"查询用户 {user_id} 的写作统计")

        # 查询用户的所有提交
        query = select(WritingSubmissionModel).where(
            and_(
                WritingSubmissionModel.user_id == user_id,
                WritingSubmissionModel.is_graded.is_(True),
            )
        )
        result = await self.db.execute(query)
        submissions = result.scalars().all()

        if not submissions:
            return WritingStatistics(
                total_submissions=0,
                average_score=0.0,
                score_distribution={},
                writing_type_performance={},
                improvement_trend=[],
                common_errors=[],
                vocabulary_usage={},
            )

        # 计算基础统计
        total_submissions = len(submissions)
        total_score = sum(s.total_score for s in submissions)
        average_score = total_score / total_submissions if total_submissions > 0 else 0

        # 分数分布
        score_distribution = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for submission in submissions:
            if submission.score_level:
                score_distribution[str(submission.score_level)] += 1

        # 按写作类型分析表现
        writing_type_performance = {}
        for submission in submissions:
            if hasattr(submission, "writing_type") and submission.writing_type:
                wtype = submission.writing_type
                if wtype not in writing_type_performance:
                    writing_type_performance[wtype] = {"count": 0, "total_score": 0}
                writing_type_performance[wtype]["count"] += 1
                writing_type_performance[wtype]["total_score"] += submission.total_score
        # 计算平均分
        for wtype in writing_type_performance:
            count = writing_type_performance[wtype]["count"]
            total = writing_type_performance[wtype]["total_score"]
            writing_type_performance[wtype]["avg_score"] = (
                round(total / count, 1) if count > 0 else 0
            )

        # 提升趋势分析
        improvement_trend = []
        sorted_submissions = sorted(submissions, key=lambda s: s.created_at)
        for i in range(
            0, len(sorted_submissions), max(1, len(sorted_submissions) // 5)
        ):
            batch = sorted_submissions[i : i + 5]
            if batch:
                improvement_trend.append(
                    {
                        "period": i // 5 + 1,
                        "avg_score": round(
                            sum(s.total_score for s in batch) / len(batch), 1
                        ),
                    }
                )

        # 常见错误分析
        common_errors = []
        error_counts = {}
        for submission in submissions:
            if submission.weaknesses:
                for error in submission.weaknesses:
                    error_counts[error] = error_counts.get(error, 0) + 1
        common_errors = sorted(
            [{"error": k, "count": v} for k, v in error_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        # 词汇使用统计
        vocabulary_usage = {"unique_words": 0, "avg_length": 0}
        all_words = []
        for submission in submissions:
            if submission.essay_content:
                words = submission.essay_content.split()
                all_words.extend(words)
        if all_words:
            vocabulary_usage = {
                "unique_words": len(set(all_words)),
                "total_words": len(all_words),
                "avg_length": round(sum(len(w) for w in all_words) / len(all_words), 1),
            }

        return WritingStatistics(
            total_submissions=total_submissions,
            average_score=float(average_score),
            score_distribution=score_distribution,
            writing_type_performance=writing_type_performance,
            improvement_trend=improvement_trend,
            common_errors=common_errors,
            vocabulary_usage=vocabulary_usage,
        )

    async def get_user_recommendations(
        self: "WritingService", user_id: int
    ) -> WritingRecommendation:
        """获取用户个性化推荐"""
        logger.info(f"生成用户 {user_id} 的写作推荐")

        # 分析用户历史表现
        statistics = await self.get_user_statistics(user_id)

        # 推荐难度
        if statistics.average_score < 8.0:
            recommended_difficulty = WritingDifficulty.BASIC
        elif statistics.average_score < 11.0:
            recommended_difficulty = WritingDifficulty.INTERMEDIATE
        else:
            recommended_difficulty = WritingDifficulty.ADVANCED

        # 推荐模板
        templates, _ = await self.get_templates(
            limit=3,
            difficulty=recommended_difficulty,
            is_recommended=True,
        )

        # 推荐任务
        tasks, _ = await self.get_tasks(
            limit=3,
            difficulty=recommended_difficulty,
        )

        # 推荐词汇
        vocabulary, _ = await self.get_vocabulary_list(
            limit=10,
            difficulty_level=recommended_difficulty,
        )

        from app.training.schemas.writing_schemas import (
            WritingTaskResponse,
            WritingTemplateResponse,
            WritingVocabularyResponse,
        )

        return WritingRecommendation(
            recommended_templates=[
                WritingTemplateResponse.model_validate(t) for t in templates
            ],
            recommended_tasks=[WritingTaskResponse.model_validate(t) for t in tasks],
            focus_areas=["提高语法准确性", "丰富词汇表达"],
            vocabulary_suggestions=[
                WritingVocabularyResponse.model_validate(v) for v in vocabulary
            ],
            practice_plan={"daily_target": 1, "weekly_focus": "议论文写作"},
        )
