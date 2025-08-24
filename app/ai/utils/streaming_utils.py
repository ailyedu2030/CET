"""流式输出工具类 - 支持实时批改和反馈."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.models.enums import QuestionType

logger = logging.getLogger(__name__)


class StreamingGradingUtils:
    """流式批改工具类 - 实现<200ms间隔的实时输出."""

    def __init__(self) -> None:
        """初始化流式批改工具."""
        self.deepseek_service = DeepSeekService()

        # 流式输出配置
        self.streaming_config = {
            "chunk_interval": 0.15,  # 150ms间隔，满足<200ms要求
            "min_chunk_size": 10,  # 最小块大小
            "max_chunk_size": 50,  # 最大块大小
            "buffer_size": 100,  # 缓冲区大小
        }

    async def stream_grading_process(
        self,
        question_content: str,
        user_answer: str,
        question_type: QuestionType,
        max_score: float,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式批改过程 - 实时返回批改进度和结果."""
        start_time = time.time()

        try:
            # 1. 发送开始信号
            yield {
                "type": "start",
                "message": "开始智能批改...",
                "progress": 0,
                "timestamp": time.time(),
            }

            # 2. 构建批改提示词
            grading_prompt = await self._build_streaming_grading_prompt(
                question_content, user_answer, question_type, max_score
            )

            # 3. 发送分析阶段信号
            yield {
                "type": "analysis",
                "message": "正在分析答案内容...",
                "progress": 10,
                "timestamp": time.time(),
            }

            # 4. 流式AI批改
            accumulated_content = ""
            progress = 20
            chunk_count = 0

            async for chunk in self.deepseek_service.stream_completion(
                prompt=grading_prompt,
                temperature=0.2,  # 低温度确保批改一致性
                max_tokens=1500,
            ):
                chunk_count += 1
                accumulated_content += chunk
                progress = min(85, 20 + (chunk_count * 2))

                # 实时返回批改内容
                yield {
                    "type": "grading",
                    "content": chunk,
                    "accumulated": accumulated_content,
                    "progress": progress,
                    "timestamp": time.time(),
                }

                # 控制输出间隔
                await asyncio.sleep(self.streaming_config["chunk_interval"])

            # 5. 解析批改结果
            yield {
                "type": "parsing",
                "message": "正在生成详细反馈...",
                "progress": 90,
                "timestamp": time.time(),
            }

            grading_result = await self._parse_streaming_grading_result(
                accumulated_content, question_type, max_score
            )

            # 6. 返回最终结果
            total_time = time.time() - start_time
            yield {
                "type": "complete",
                "result": grading_result,
                "progress": 100,
                "total_time": total_time,
                "timestamp": time.time(),
                "performance_metrics": {
                    "response_time": total_time,
                    "chunk_count": chunk_count,
                    "avg_chunk_interval": total_time / max(chunk_count, 1),
                },
            }

        except Exception as e:
            logger.error(f"流式批改失败: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "message": "批改过程中出现错误，正在降级处理...",
                "progress": 0,
                "timestamp": time.time(),
            }

    async def stream_writing_assistance(
        self, text: str, assistance_type: str = "grammar"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式写作辅助 - 实时语法检查和建议."""
        try:
            # 1. 开始信号
            yield {
                "type": "start",
                "message": f"开始{assistance_type}检查...",
                "progress": 0,
                "timestamp": time.time(),
            }

            # 2. 构建辅助提示词
            assistance_prompt = await self._build_writing_assistance_prompt(text, assistance_type)

            # 3. 流式处理
            accumulated_suggestions = ""
            progress = 10

            async for chunk in self.deepseek_service.stream_completion(
                prompt=assistance_prompt,
                temperature=0.1,  # 极低温度确保建议准确性
                max_tokens=800,
            ):
                accumulated_suggestions += chunk
                progress = min(90, progress + 5)

                yield {
                    "type": "suggestion",
                    "content": chunk,
                    "accumulated": accumulated_suggestions,
                    "progress": progress,
                    "timestamp": time.time(),
                }

                await asyncio.sleep(self.streaming_config["chunk_interval"])

            # 4. 解析建议
            suggestions = await self._parse_writing_suggestions(accumulated_suggestions)

            yield {
                "type": "complete",
                "suggestions": suggestions,
                "progress": 100,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"流式写作辅助失败: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": time.time(),
            }

    # ==================== 私有方法 ====================

    async def _build_streaming_grading_prompt(
        self,
        question_content: str,
        user_answer: str,
        question_type: QuestionType,
        max_score: float,
    ) -> str:
        """构建流式批改提示词."""
        base_prompt = f"""
你是专业的英语四级批改专家。请对以下答案进行详细批改，并按照指定格式返回结果。

题目内容：{question_content}
学生答案：{user_answer}
题目类型：{question_type.value}
满分：{max_score}分

批改要求：
1. 严格按照英语四级评分标准
2. 提供详细的错误分析和改进建议
3. 给出具体的得分和理由
4. 标注关键的语法、词汇、逻辑问题

请返回JSON格式的批改结果：
{{
    "score": 具体得分,
    "max_score": {max_score},
    "accuracy_rate": 准确率(0-1),
    "detailed_feedback": "详细反馈内容",
    "error_analysis": ["错误1", "错误2", ...],
    "improvement_suggestions": ["建议1", "建议2", ...],
    "grammar_issues": ["语法问题1", "语法问题2", ...],
    "vocabulary_suggestions": ["词汇建议1", "词汇建议2", ...],
    "confidence": 批改置信度(0-1),
    "grading_criteria": {{
        "content": 内容分,
        "language": 语言分,
        "structure": 结构分,
        "mechanics": 技巧分
    }}
}}
"""

        # 根据题目类型调整提示词
        if question_type == QuestionType.ESSAY:
            base_prompt += """
特别关注：
- 文章结构的完整性（引言、主体、结论）
- 论点的清晰性和逻辑性
- 语言表达的准确性和流畅性
- 词汇使用的丰富性和准确性
"""
        elif question_type in [
            QuestionType.TRANSLATION_EN_TO_CN,
            QuestionType.TRANSLATION_CN_TO_EN,
        ]:
            base_prompt += """
特别关注：
- 翻译的准确性和完整性
- 语言表达的自然性
- 文化背景的适当处理
- 专业术语的正确使用
"""

        return base_prompt

    async def _build_writing_assistance_prompt(self, text: str, assistance_type: str) -> str:
        """构建写作辅助提示词."""
        prompts = {
            "grammar": f"""
请检查以下英文文本的语法错误，并提供修改建议：

文本：{text}

请返回JSON格式：
{{
    "grammar_errors": [
        {{
            "error": "错误内容",
            "position": "位置",
            "suggestion": "修改建议",
            "explanation": "错误解释"
        }}
    ],
    "overall_score": 语法质量评分(0-100),
    "improvement_tips": ["改进建议1", "改进建议2"]
}}
""",
            "vocabulary": f"""
请分析以下英文文本的词汇使用，并提供改进建议：

文本：{text}

请返回JSON格式：
{{
    "vocabulary_analysis": {{
        "level": "词汇水平评估",
        "diversity": "词汇多样性评分(0-100)",
        "accuracy": "词汇准确性评分(0-100)"
    }},
    "suggestions": [
        {{
            "original": "原词汇",
            "suggested": "建议词汇",
            "reason": "建议理由"
        }}
    ],
    "advanced_alternatives": ["高级词汇替换1", "高级词汇替换2"]
}}
""",
            "style": f"""
请分析以下英文文本的写作风格，并提供改进建议：

文本：{text}

请返回JSON格式：
{{
    "style_analysis": {{
        "clarity": "清晰度评分(0-100)",
        "coherence": "连贯性评分(0-100)",
        "formality": "正式程度评估"
    }},
    "improvements": [
        {{
            "aspect": "改进方面",
            "suggestion": "具体建议",
            "example": "示例"
        }}
    ]
}}
""",
        }

        return prompts.get(assistance_type, prompts["grammar"])

    async def _parse_streaming_grading_result(
        self, ai_response: str, question_type: QuestionType, max_score: float
    ) -> dict[str, Any]:
        """解析流式批改结果."""
        try:
            # 尝试解析JSON
            result = json.loads(ai_response.strip())

            # 验证必要字段
            required_fields = ["score", "detailed_feedback", "improvement_suggestions"]
            for field in required_fields:
                if field not in result:
                    result[field] = self._get_default_value(field, max_score)

            # 确保分数在合理范围内
            result["score"] = max(0, min(result.get("score", 0), max_score))
            result["max_score"] = max_score

            # 计算准确率
            if "accuracy_rate" not in result:
                result["accuracy_rate"] = result["score"] / max_score

            return dict(result)

        except json.JSONDecodeError:
            logger.warning("AI响应JSON解析失败，使用备用解析")
            fallback_result = await self._fallback_parse_grading_result(ai_response, max_score)
            return dict(fallback_result)

    async def _parse_writing_suggestions(self, ai_response: str) -> dict[str, Any]:
        """解析写作建议."""
        try:
            result = json.loads(ai_response.strip())
            return dict(result)
        except json.JSONDecodeError:
            return {
                "suggestions": ["AI解析失败，请稍后重试"],
                "error": "解析错误",
            }

    async def _fallback_parse_grading_result(
        self, ai_response: str, max_score: float
    ) -> dict[str, Any]:
        """备用批改结果解析."""
        return {
            "score": max_score * 0.7,  # 默认给70%分数
            "max_score": max_score,
            "accuracy_rate": 0.7,
            "detailed_feedback": "AI批改解析失败，已进行基础评分",
            "improvement_suggestions": ["请重新提交以获得详细批改"],
            "confidence": 0.3,
            "error": "解析失败",
        }

    def _get_default_value(self, field: str, max_score: float) -> Any:
        """获取字段默认值."""
        defaults = {
            "score": max_score * 0.6,
            "detailed_feedback": "批改完成，请查看具体建议",
            "improvement_suggestions": ["继续努力学习"],
            "confidence": 0.8,
        }
        return defaults.get(field, "")
