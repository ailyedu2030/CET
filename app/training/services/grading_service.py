"""智能批改与反馈系统 - AI驱动的专业评分服务."""

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.models.enums import GradingStatus, QuestionType
from app.training.models.training_models import Question
from app.training.schemas.training_schemas import GradingResult


class IntelligentGradingService:
    """智能批改与反馈系统 - 专业的AI评分引擎."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化智能批改服务."""
        self.db = db
        self.deepseek_service = DeepSeekService()

        # 批改质量控制参数
        self.quality_thresholds = {
            "min_confidence": 0.7,  # 最低置信度阈值
            "complex_question_score": 15.0,  # 复杂题目分数阈值
            "detailed_feedback_length": 50,  # 详细反馈最短长度
        }

    # ==================== 主要批改接口 ====================

    async def grade_answer(
        self,
        question: Question,
        user_answer: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> GradingResult:
        """智能批改答案 - 统一入口."""
        # 预处理和验证
        validation_result = await self._validate_answer_format(question, user_answer)
        if not validation_result["valid"]:
            return self._create_error_result(question, validation_result["error"])

        # 根据题目类型选择批改策略
        grading_strategy = self._select_grading_strategy(question)

        try:
            # 执行批改
            result: GradingResult = await grading_strategy(question, user_answer, context or {})

            # 质量控制检查
            result = await self._apply_quality_control(result, question)

            # 生成改进建议
            result = await self._enhance_feedback(result, question, user_answer)

            return result  # type: ignore[no-any-return]

        except Exception as e:
            return self._create_fallback_result(question, str(e))

    # ==================== 题型专门批改方法 ====================

    async def _grade_choice_question(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改选择题 - 高精度对比."""
        user_choice = str(user_answer.get("option", "")).upper().strip()
        correct_choice = str(question.correct_answer.get("option", "")).upper().strip()

        # 支持多种答案格式
        normalized_user = self._normalize_choice_answer(user_choice)
        normalized_correct = self._normalize_choice_answer(correct_choice)

        is_correct = normalized_user == normalized_correct
        score = question.max_score if is_correct else 0.0

        # 生成详细的选择题反馈
        detailed_feedback = await self._generate_choice_feedback(
            question, user_choice, correct_choice, is_correct
        )

        return GradingResult(
            is_correct=is_correct,
            score=score,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={
                "user_choice": user_choice,
                "correct_choice": correct_choice,
                "explanation": question.correct_answer.get("explanation", ""),
                "analysis": detailed_feedback.get("analysis", ""),
            },
            ai_confidence=0.98,  # 选择题批改置信度很高
            knowledge_points_mastered=question.knowledge_points if is_correct else [],
            knowledge_points_weak=[] if is_correct else question.knowledge_points,
            detailed_feedback=detailed_feedback.get("detailed", ""),
            improvement_suggestions=detailed_feedback.get("suggestions", []),
        )

    async def _grade_fill_blank_question(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改填空题 - 灵活匹配."""
        user_words = user_answer.get("words", [])
        if isinstance(user_words, str):
            user_words = [user_words]

        correct_words = question.correct_answer.get("words", [])
        if isinstance(correct_words, str):
            correct_words = [correct_words]

        # 使用AI辅助批改，处理语法变形等情况
        ai_grading_result = await self._ai_assisted_fill_blank_grading(
            question, user_words, correct_words
        )

        if ai_grading_result:
            return ai_grading_result

        # 备用规则批改
        return await self._rule_based_fill_blank_grading(question, user_words, correct_words)

    async def _grade_essay_question(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改作文题 - 多维度AI评估."""
        essay_text = user_answer.get("text", "").strip()

        if not essay_text:
            return self._create_empty_essay_result(question)

        # 构建专业的作文批改prompt
        grading_prompt = await self._build_essay_grading_prompt(question, essay_text)

        try:
            success, ai_response, error_msg = await self.deepseek_service.generate_completion(
                prompt=grading_prompt,
                temperature=0.2,  # 较低温度确保批改一致性
                max_tokens=1500,
            )

            if success and ai_response:
                return await self._parse_essay_grading_result(ai_response, question, essay_text)
            else:
                raise ValueError(f"AI批改失败: {error_msg}")

        except Exception as e:
            return await self._fallback_essay_grading(question, essay_text, str(e))

    async def _grade_translation_question(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改翻译题 - 专业翻译评估."""
        user_translation = user_answer.get("text", "").strip()

        if not user_translation:
            return self._create_empty_translation_result(question)

        # 构建翻译专业批改prompt
        grading_prompt = await self._build_translation_grading_prompt(question, user_translation)

        try:
            success, ai_response, error_msg = await self.deepseek_service.generate_completion(
                prompt=grading_prompt,
                temperature=0.1,  # 更低温度确保翻译评估准确性
                max_tokens=1200,
            )

            if success and ai_response:
                return await self._parse_translation_grading_result(
                    ai_response, question, user_translation
                )
            else:
                raise ValueError(f"AI翻译批改失败: {error_msg}")

        except Exception as e:
            return await self._fallback_translation_grading(question, user_translation, str(e))

    async def _grade_reading_comprehension(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改阅读理解题 - 理解能力评估."""
        # 阅读理解通常是选择题形式，但需要更深层次的分析
        return await self._grade_choice_question(question, user_answer, context)

    async def _grade_listening_comprehension(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改听力理解题 - 听力能力评估."""
        # 听力理解也通常是选择题，但可能包含多个小题
        if isinstance(user_answer.get("answers"), list):
            return await self._grade_multiple_choice_set(question, user_answer, context)
        else:
            return await self._grade_choice_question(question, user_answer, context)

    # ==================== AI辅助批改方法 ====================

    async def _ai_assisted_fill_blank_grading(
        self, question: Question, user_words: list[str], correct_words: list[str]
    ) -> GradingResult | None:
        """AI辅助填空题批改 - 处理语法变形."""
        if not user_words or not correct_words:
            return None

        prompt = f"""
请批改以下英语填空题：

题目：{question.title}
题目内容：{question.content.get("text", "")}
学生答案：{", ".join(user_words)}
标准答案：{", ".join(correct_words)}

评分要求：
1. 考虑语法变形（时态、单复数、词性变化）
2. 考虑同义词替换的合理性
3. 满分{question.max_score}分
4. 给出每个空的具体得分

请返回JSON格式：
{{
    "total_score": 总分,
    "blank_scores": [空1得分, 空2得分, ...],
    "correct_items": ["正确的填空1", "正确的填空2", ...],
    "feedback": "详细反馈",
    "suggestions": ["改进建议1", "改进建议2"],
    "grammar_analysis": "语法分析",
    "confidence": 置信度(0-1)
}}
"""

        try:
            success, ai_response, _ = await self.deepseek_service.generate_completion(
                prompt=prompt, temperature=0.3, max_tokens=800
            )

            if success and ai_response:
                content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                result_data = json.loads(content)

                total_score = float(result_data.get("total_score", 0))
                confidence = float(result_data.get("confidence", 0.8))

                # 置信度过低时返回None，使用规则批改
                if confidence < self.quality_thresholds["min_confidence"]:
                    return None

                is_correct = total_score >= question.max_score * 0.8

                return GradingResult(
                    is_correct=is_correct,
                    score=total_score,
                    max_score=question.max_score,
                    grading_status=GradingStatus.COMPLETED,
                    ai_feedback=result_data,
                    ai_confidence=confidence,
                    knowledge_points_mastered=(question.knowledge_points if is_correct else []),
                    knowledge_points_weak=([] if is_correct else question.knowledge_points),
                    detailed_feedback=result_data.get("feedback", ""),
                    improvement_suggestions=result_data.get("suggestions", []),
                )

        except Exception:
            return None

        return None

    async def _build_essay_grading_prompt(self, question: Question, essay_text: str) -> str:
        """构建专业的作文批改prompt."""
        word_count = len(essay_text.split())

        return f"""
请按照英语四级写作评分标准严格批改以下作文：

【题目】：{question.title}
【写作要求】：{question.content.get("instruction", "")}
【字数要求】：120-180词（实际字数：{word_count}词）

【学生作文】：
{essay_text}

【评分标准】（满分{question.max_score}分）：
1. 内容相关性与完整性（{question.max_score * 0.35:.1f}分）
   - 是否完整回应题目要求
   - 内容是否相关且有说服力
   - 观点是否明确且合理

2. 语言运用与准确性（{question.max_score * 0.35:.1f}分）
   - 词汇运用的准确性和丰富性
   - 语法结构的正确性和多样性
   - 拼写和标点的准确性

3. 篇章结构与逻辑（{question.max_score * 0.3:.1f}分）
   - 段落结构是否清晰
   - 逻辑关系是否合理
   - 衔接手段是否恰当

【特别关注】：
- 字数不足或严重超标将扣分
- 抄袭模板过多将影响原创性评分
- 严重语法错误将显著影响得分

请返回JSON格式：
{{
    "total_score": 总分,
    "content_score": 内容得分,
    "language_score": 语言得分,
    "structure_score": 结构得分,
    "word_count_penalty": 字数扣分,
    "strengths": ["优点1", "优点2", "优点3"],
    "weaknesses": ["问题1", "问题2", "问题3"],
    "detailed_feedback": "逐段详细批改意见",
    "improvement_suggestions": ["具体改进建议1", "具体改进建议2"],
    "sample_corrections": ["语法纠错示例1", "语法纠错示例2"],
    "grade_level": "评分等级(优秀/良好/及格/不及格)",
    "confidence": 批改置信度(0-1)
}}
"""

    async def _build_translation_grading_prompt(
        self, question: Question, user_translation: str
    ) -> str:
        """构建专业的翻译批改prompt."""
        source_text = question.content.get("source_text", "")
        reference_translation = question.correct_answer.get("target_text", "")

        # 判断翻译方向
        direction = "中译英" if question.question_type.value == "translation_cn_to_en" else "英译中"

        return f"""
请按照专业翻译评分标准批改以下{direction}翻译：

【原文】：
{source_text}

【参考译文】：
{reference_translation}

【学生译文】：
{user_translation}

【评分标准】（满分{question.max_score}分）：
1. 准确性（{question.max_score * 0.5:.1f}分）
   - 原文意思是否准确传达
   - 关键信息是否遗漏或错误
   - 专业术语是否翻译正确

2. 流畅性（{question.max_score * 0.3:.1f}分）
   - 译文是否符合目标语言表达习惯
   - 语言是否自然流畅
   - 是否有明显的翻译腔

3. 完整性（{question.max_score * 0.2:.1f}分）
   - 是否翻译了全部内容
   - 重要信息是否遗漏
   - 语言风格是否一致

【评分要点】：
- 重大意思错误：扣2-3分
- 语法错误：每个扣0.5-1分
- 用词不当：每个扣0.5分
- 信息遗漏：根据重要程度扣1-2分

请返回JSON格式：
{{
    "total_score": 总分,
    "accuracy_score": 准确性得分,
    "fluency_score": 流畅性得分,
    "completeness_score": 完整性得分,
    "major_errors": ["重大错误1", "重大错误2"],
    "minor_errors": ["小错误1", "小错误2"],
    "good_points": ["翻译亮点1", "翻译亮点2"],
    "detailed_feedback": "逐句详细批改",
    "improvement_suggestions": ["改进建议1", "改进建议2"],
    "alternative_translations": ["可替代译法1", "可替代译法2"],
    "confidence": 批改置信度(0-1)
}}
"""

    # ==================== 结果解析方法 ====================

    async def _parse_essay_grading_result(
        self, ai_response: dict[str, Any], question: Question, essay_text: str
    ) -> GradingResult:
        """解析作文批改结果."""
        try:
            content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            result_data = json.loads(content)

            total_score = min(float(result_data.get("total_score", 0)), question.max_score)
            confidence = float(result_data.get("confidence", 0.8))
            is_correct = total_score >= question.max_score * 0.6

            return GradingResult(
                is_correct=is_correct,
                score=total_score,
                max_score=question.max_score,
                grading_status=GradingStatus.COMPLETED,
                ai_feedback=result_data,
                ai_confidence=confidence,
                knowledge_points_mastered=(question.knowledge_points if is_correct else []),
                knowledge_points_weak=[] if is_correct else question.knowledge_points,
                detailed_feedback=result_data.get("detailed_feedback", ""),
                improvement_suggestions=result_data.get("improvement_suggestions", []),
            )

        except Exception as e:
            return await self._fallback_essay_grading(question, essay_text, str(e))

    async def _parse_translation_grading_result(
        self, ai_response: dict[str, Any], question: Question, user_translation: str
    ) -> GradingResult:
        """解析翻译批改结果."""
        try:
            content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            result_data = json.loads(content)

            total_score = min(float(result_data.get("total_score", 0)), question.max_score)
            confidence = float(result_data.get("confidence", 0.8))
            is_correct = total_score >= question.max_score * 0.6

            return GradingResult(
                is_correct=is_correct,
                score=total_score,
                max_score=question.max_score,
                grading_status=GradingStatus.COMPLETED,
                ai_feedback=result_data,
                ai_confidence=confidence,
                knowledge_points_mastered=(question.knowledge_points if is_correct else []),
                knowledge_points_weak=[] if is_correct else question.knowledge_points,
                detailed_feedback=result_data.get("detailed_feedback", ""),
                improvement_suggestions=result_data.get("improvement_suggestions", []),
            )

        except Exception as e:
            return await self._fallback_translation_grading(question, user_translation, str(e))

    # ==================== 备用批改方法 ====================

    async def _rule_based_fill_blank_grading(
        self, question: Question, user_words: list[str], correct_words: list[str]
    ) -> GradingResult:
        """基于规则的填空题批改."""
        if not user_words or not correct_words:
            return self._create_empty_answer_result(question)

        # 确保长度一致
        user_words = user_words[: len(correct_words)]
        while len(user_words) < len(correct_words):
            user_words.append("")

        correct_count = 0
        detailed_analysis: list[str] = []

        for i, (user_word, correct_word) in enumerate(zip(user_words, correct_words, strict=False)):
            user_clean = user_word.strip().lower()
            correct_clean = correct_word.strip().lower()

            if user_clean == correct_clean:
                correct_count += 1
                detailed_analysis.append(f"第{i + 1}空: '{user_word}' ✓ 正确")
            else:
                # 检查是否是常见变形
                if self._is_acceptable_variation(user_clean, correct_clean):
                    correct_count += 1
                    detailed_analysis.append(f"第{i + 1}空: '{user_word}' ✓ 可接受的变形")
                else:
                    detailed_analysis.append(f"第{i + 1}空: '{user_word}' ✗ 应为'{correct_word}'")

        accuracy = correct_count / len(correct_words) if correct_words else 0
        score = question.max_score * accuracy
        is_correct = accuracy >= 0.8

        return GradingResult(
            is_correct=is_correct,
            score=score,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={
                "accuracy": accuracy,
                "correct_count": correct_count,
                "total_count": len(correct_words),
                "detailed_analysis": detailed_analysis,
            },
            ai_confidence=0.85,
            knowledge_points_mastered=question.knowledge_points if is_correct else [],
            knowledge_points_weak=[] if is_correct else question.knowledge_points,
            detailed_feedback=f"填空准确率: {accuracy:.1%}\n" + "\n".join(detailed_analysis),
            improvement_suggestions=(
                [
                    "注意单词拼写的准确性",
                    "考虑语法变形的正确性",
                    "关注上下文语境",
                ]
                if not is_correct
                else ["继续保持良好状态"]
            ),
        )

    async def _fallback_essay_grading(
        self, question: Question, essay_text: str, error: str
    ) -> GradingResult:
        """作文批改失败时的备用方法."""
        word_count = len(essay_text.split())

        # 基础评分：主要基于字数和基本结构
        base_score = min(question.max_score * 0.6, question.max_score * word_count / 150)

        # 简单的结构分析
        paragraphs = [p.strip() for p in essay_text.split("\n") if p.strip()]
        structure_bonus = 2 if len(paragraphs) >= 3 else 0

        total_score = min(base_score + structure_bonus, question.max_score)
        is_correct = total_score >= question.max_score * 0.6

        return GradingResult(
            is_correct=is_correct,
            score=total_score,
            max_score=question.max_score,
            grading_status=GradingStatus.REVIEWING,
            ai_feedback={
                "error": error,
                "word_count": word_count,
                "paragraph_count": len(paragraphs),
                "base_score": base_score,
            },
            ai_confidence=0.4,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback="AI批改暂时不可用，已进行基础评分，请等待人工复审",
            improvement_suggestions=["等待详细批改结果"],
        )

    async def _fallback_translation_grading(
        self, question: Question, user_translation: str, error: str
    ) -> GradingResult:
        """翻译批改失败时的备用方法."""
        reference = question.correct_answer.get("target_text", "")

        # 简单的文本相似度计算
        similarity = self._calculate_text_similarity(user_translation, reference)
        score = question.max_score * similarity
        is_correct = score >= question.max_score * 0.6

        return GradingResult(
            is_correct=is_correct,
            score=score,
            max_score=question.max_score,
            grading_status=GradingStatus.REVIEWING,
            ai_feedback={
                "error": error,
                "similarity_score": similarity,
                "fallback_method": "text_similarity",
            },
            ai_confidence=0.3,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback="AI批改暂时不可用，已进行基础相似度评分，请等待人工复审",
            improvement_suggestions=["等待详细批改结果"],
        )

    # ==================== 辅助方法 ====================

    def _select_grading_strategy(
        self, question: Question
    ) -> Callable[[Question, dict[str, Any], dict[str, Any]], Awaitable[GradingResult]]:
        """根据题目类型选择批改策略."""
        strategy_map = {
            QuestionType.MULTIPLE_CHOICE: self._grade_choice_question,
            QuestionType.TRUE_FALSE: self._grade_choice_question,
            QuestionType.FILL_BLANK: self._grade_fill_blank_question,
            QuestionType.SHORT_ANSWER: self._grade_fill_blank_question,
            QuestionType.ESSAY: self._grade_essay_question,
            QuestionType.LISTENING_COMPREHENSION: self._grade_listening_comprehension,
            QuestionType.READING_COMPREHENSION: self._grade_reading_comprehension,
            QuestionType.TRANSLATION_EN_TO_CN: self._grade_translation_question,
            QuestionType.TRANSLATION_CN_TO_EN: self._grade_translation_question,
        }

        return strategy_map.get(question.question_type, self._grade_choice_question)

    async def _validate_answer_format(
        self, question: Question, user_answer: dict[str, Any]
    ) -> dict[str, Any]:
        """验证答案格式."""
        if not user_answer:
            return {"valid": False, "error": "答案为空"}

        # 根据题目类型验证必需字段
        required_fields = {
            QuestionType.MULTIPLE_CHOICE: ["option"],
            QuestionType.TRUE_FALSE: ["option"],
            QuestionType.FILL_BLANK: ["words"],
            QuestionType.SHORT_ANSWER: ["text"],
            QuestionType.ESSAY: ["text"],
            QuestionType.TRANSLATION_EN_TO_CN: ["text"],
            QuestionType.TRANSLATION_CN_TO_EN: ["text"],
        }

        required = required_fields.get(question.question_type, [])
        for field in required:
            if field not in user_answer or not user_answer[field]:
                return {"valid": False, "error": f"缺少必需字段: {field}"}

        return {"valid": True}

    def _normalize_choice_answer(self, choice: str) -> str:
        """标准化选择题答案."""
        # 移除空格和特殊字符，只保留字母
        normalized = re.sub(r"[^A-Z]", "", choice.upper())
        return normalized if normalized else choice.upper()

    def _is_acceptable_variation(self, user_word: str, correct_word: str) -> bool:
        """检查是否是可接受的单词变形."""
        if not user_word or not correct_word:
            return False

        # 基本的变形检查
        variations = [
            correct_word + "s",  # 复数
            correct_word + "es",  # 复数
            correct_word + "ed",  # 过去式
            correct_word + "ing",  # 现在分词
            correct_word[:-1] + "ies" if correct_word.endswith("y") else None,  # y变ies
        ]

        return user_word in [v for v in variations if v is not None]

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    async def _generate_choice_feedback(
        self,
        question: Question,
        user_choice: str,
        correct_choice: str,
        is_correct: bool,
    ) -> dict[str, Any]:
        """生成选择题详细反馈."""
        if is_correct:
            return {
                "detailed": f"正确选择了{correct_choice}选项，说明对知识点掌握良好。",
                "analysis": question.correct_answer.get("explanation", ""),
                "suggestions": ["继续保持良好的理解能力"],
            }
        else:
            return {
                "detailed": f"选择了{user_choice}选项，正确答案是{correct_choice}选项。请重新审题并分析各选项的差异。",
                "analysis": question.correct_answer.get("explanation", ""),
                "suggestions": [
                    "仔细阅读题目，理解题意",
                    "分析各选项的关键差异",
                    "复习相关知识点",
                ],
            }

    async def _grade_multiple_choice_set(
        self, question: Question, user_answer: dict[str, Any], context: dict[str, Any]
    ) -> GradingResult:
        """批改多选题组."""
        user_answers = user_answer.get("answers", [])
        correct_answers = question.correct_answer.get("answers", [])

        if not user_answers or not correct_answers:
            return self._create_empty_answer_result(question)

        # 确保长度一致
        user_answers = user_answers[: len(correct_answers)]
        while len(user_answers) < len(correct_answers):
            user_answers.append("")

        correct_count = 0
        total_count = len(correct_answers)

        for user_ans, correct_ans in zip(user_answers, correct_answers, strict=False):
            if str(user_ans).upper().strip() == str(correct_ans).upper().strip():
                correct_count += 1

        accuracy = correct_count / total_count if total_count > 0 else 0
        score = question.max_score * accuracy
        is_correct = accuracy >= 0.8

        return GradingResult(
            is_correct=is_correct,
            score=score,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={
                "correct_count": correct_count,
                "total_count": total_count,
                "accuracy": accuracy,
                "user_answers": user_answers,
                "correct_answers": correct_answers,
            },
            ai_confidence=0.95,
            knowledge_points_mastered=question.knowledge_points if is_correct else [],
            knowledge_points_weak=[] if is_correct else question.knowledge_points,
            detailed_feedback=f"多选题组正确率: {accuracy:.1%}（{correct_count}/{total_count}）",
            improvement_suggestions=([] if is_correct else ["加强听力理解能力", "注意题目细节"]),
        )

    # ==================== 质量控制和增强 ====================

    async def _apply_quality_control(
        self, result: GradingResult, question: Question
    ) -> GradingResult:
        """应用质量控制检查."""
        # 置信度检查
        if result.ai_confidence < self.quality_thresholds["min_confidence"]:
            result.grading_status = GradingStatus.REVIEWING

        # 复杂题目检查
        if question.max_score >= self.quality_thresholds["complex_question_score"]:
            if (
                len(result.detailed_feedback or "")
                < self.quality_thresholds["detailed_feedback_length"]
            ):
                result.grading_status = GradingStatus.REVIEWING

        return result

    async def _enhance_feedback(
        self, result: GradingResult, question: Question, user_answer: dict[str, Any]
    ) -> GradingResult:
        """增强反馈质量."""
        # 如果反馈过于简单，尝试生成更详细的反馈
        if len(result.detailed_feedback or "") < 30 and result.ai_confidence > 0.8:
            enhanced_feedback = await self._generate_enhanced_feedback(
                result, question, user_answer
            )
            if enhanced_feedback:
                result.detailed_feedback = enhanced_feedback

        return result

    async def _generate_enhanced_feedback(
        self, result: GradingResult, question: Question, user_answer: dict[str, Any]
    ) -> str | None:
        """生成增强的反馈."""
        # 简化的增强反馈生成
        if result.is_correct:
            return f"回答正确！展现了对{question.training_type.value}知识点的良好掌握。"
        else:
            weak_points = ", ".join(result.knowledge_points_weak[:3])
            return f"需要加强{weak_points}等知识点的学习。建议多做相关练习。"

    # ==================== 错误结果创建 ====================

    def _create_error_result(self, question: Question, error: str) -> GradingResult:
        """创建错误结果."""
        return GradingResult(
            is_correct=False,
            score=0.0,
            max_score=question.max_score,
            grading_status=GradingStatus.FAILED,
            ai_feedback={"error": error},
            ai_confidence=0.0,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback=f"批改失败: {error}",
            improvement_suggestions=["请检查答案格式"],
        )

    def _create_fallback_result(self, question: Question, error: str) -> GradingResult:
        """创建备用结果."""
        return GradingResult(
            is_correct=False,
            score=0.0,
            max_score=question.max_score,
            grading_status=GradingStatus.REVIEWING,
            ai_feedback={"fallback_error": error},
            ai_confidence=0.1,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback="系统批改遇到问题，已转人工批改",
            improvement_suggestions=["等待人工批改结果"],
        )

    def _create_empty_essay_result(self, question: Question) -> GradingResult:
        """创建空作文结果."""
        return GradingResult(
            is_correct=False,
            score=0.0,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={"error": "作文内容为空"},
            ai_confidence=1.0,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback="作文内容为空，无法进行评分",
            improvement_suggestions=["请撰写完整的作文内容"],
        )

    def _create_empty_translation_result(self, question: Question) -> GradingResult:
        """创建空翻译结果."""
        return GradingResult(
            is_correct=False,
            score=0.0,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={"error": "翻译内容为空"},
            ai_confidence=1.0,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback="翻译内容为空，无法进行评分",
            improvement_suggestions=["请提供翻译内容"],
        )

    def _create_empty_answer_result(self, question: Question) -> GradingResult:
        """创建空答案结果."""
        return GradingResult(
            is_correct=False,
            score=0.0,
            max_score=question.max_score,
            grading_status=GradingStatus.COMPLETED,
            ai_feedback={"error": "答案内容为空"},
            ai_confidence=1.0,
            knowledge_points_mastered=[],
            knowledge_points_weak=question.knowledge_points,
            detailed_feedback="答案内容为空，无法进行评分",
            improvement_suggestions=["请提供答案内容"],
        )
