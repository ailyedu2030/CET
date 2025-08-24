"""
DeepSeek内容生成服务 - 真实AI服务集成

实现功能：
1. 教学大纲生成
2. 教案生成
3. 内容摘要生成
4. 多阶段AI处理
5. 密钥池管理和错误处理
"""

import asyncio
import json
import time
from typing import Any

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessLogicError


class ContentGenerationRequest(BaseModel):
    """内容生成请求模型"""

    prompt: str
    max_tokens: int = 2000
    temperature: float = 0.7
    model: str = "deepseek-chat"


class ContentGenerationResponse(BaseModel):
    """内容生成响应模型"""

    content: str
    model: str
    usage: dict[str, Any] = Field(default_factory=dict)
    generation_time: float = 0.0


class DeepSeekContentService:
    """DeepSeek内容生成服务"""

    def __init__(self) -> None:
        # DeepSeek密钥池
        self.api_keys = [
            "sk-873a542b4f5c4aa2b4fe9dc66bc8f5cc",
            "sk-334079d630b8447cacc7a4e56538f98a",
            "sk-0924ab64b3f143c9a3380d754875a631",
            "sk-0f8fdcc9d526486e80d43d2b1082d9d6",
            "sk-721503f5d7fc470ba8dbb96ec769c40c",
        ]
        self.current_key_index = 0
        self.api_base_url = "https://api.deepseek.com/v1"

        # 配置参数
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 60.0
        self.max_prompt_length = 32000  # DeepSeek上下文限制

    async def generate_syllabus(
        self, resource_content: str, course_info: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        生成教学大纲

        Args:
            resource_content: 资源内容
            course_info: 课程信息

        Returns:
            Dict[str, Any]: 生成的教学大纲
        """
        try:
            prompt = self._build_syllabus_prompt(resource_content, course_info)
            response = await self._generate_content(prompt, max_tokens=3000, temperature=0.3)

            if response:
                try:
                    syllabus = json.loads(response.content)
                    if isinstance(syllabus, dict):
                        logger.info(
                            "Syllabus generation completed",
                            extra={
                                "course_name": course_info.get("name", "Unknown"),
                                "content_length": len(resource_content),
                                "generation_time": response.generation_time,
                            },
                        )
                        return syllabus
                    else:
                        logger.error("Syllabus response is not a dict")
                        return None
                except json.JSONDecodeError:
                    logger.error("Failed to parse syllabus JSON response")
                    return None

            return None

        except Exception as e:
            logger.error(f"Syllabus generation failed: {str(e)}")
            return None

    async def generate_lesson_plan(
        self, syllabus: dict[str, Any], lesson_info: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        生成教案

        Args:
            syllabus: 教学大纲
            lesson_info: 课时信息

        Returns:
            Dict[str, Any]: 生成的教案
        """
        try:
            prompt = self._build_lesson_plan_prompt(syllabus, lesson_info)
            response = await self._generate_content(prompt, max_tokens=4000, temperature=0.5)

            if response:
                try:
                    lesson_plan = json.loads(response.content)
                    if isinstance(lesson_plan, dict):
                        logger.info(
                            "Lesson plan generation completed",
                            extra={
                                "lesson_title": lesson_info.get("title", "Unknown"),
                                "generation_time": response.generation_time,
                            },
                        )
                        return lesson_plan
                    else:
                        logger.error("Lesson plan response is not a dict")
                        return None
                except json.JSONDecodeError:
                    logger.error("Failed to parse lesson plan JSON response")
                    return None

            return None

        except Exception as e:
            logger.error(f"Lesson plan generation failed: {str(e)}")
            return None

    async def generate_summary(self, content: str, summary_type: str = "general") -> str:
        """
        生成内容摘要

        Args:
            content: 待摘要的内容
            summary_type: 摘要类型 (general, key_points, hierarchical)

        Returns:
            str: 生成的摘要
        """
        try:
            prompt = self._build_summary_prompt(content, summary_type)
            response = await self._generate_content(prompt, max_tokens=500, temperature=0.2)

            if response:
                logger.info(
                    "Summary generation completed",
                    extra={
                        "content_length": len(content),
                        "summary_type": summary_type,
                        "generation_time": response.generation_time,
                    },
                )
                return response.content

            return content[:200]  # Fallback to truncated content

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return content[:200]

    async def _generate_content(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7
    ) -> ContentGenerationResponse | None:
        """
        调用DeepSeek API生成内容

        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            ContentGenerationResponse: 生成响应
        """
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                # 获取当前API密钥
                api_key = self._get_current_api_key()

                # 构建请求
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False,
                }

                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.post(
                        f"{self.api_base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            content = result["choices"][0]["message"]["content"]
                            usage = result.get("usage", {})

                            generation_time = time.time() - start_time

                            return ContentGenerationResponse(
                                content=content,
                                model="deepseek-chat",
                                usage=usage,
                                generation_time=generation_time,
                            )

                        elif response.status == 429:
                            # API限制，切换密钥
                            self._rotate_api_key()
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue

                        elif response.status == 401:
                            # 密钥无效，切换密钥
                            self._rotate_api_key()
                            continue

                        else:
                            error_text = await response.text()
                            logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                            raise BusinessLogicError(f"API request failed: {response.status}")

            except TimeoutError as e:
                logger.warning(f"DeepSeek API timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise BusinessLogicError("API request timeout") from e

            except Exception as e:
                logger.error(f"DeepSeek API call failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

        return None

    def _build_syllabus_prompt(self, resource_content: str, course_info: dict[str, Any]) -> str:
        """构建教学大纲生成提示词"""
        course_name = course_info.get("name", "英语四级课程")
        course_duration = course_info.get("duration", "16周")
        target_level = course_info.get("target_level", "CET-4")

        prompt = f"""
请基于以下教材内容，为"{course_name}"生成详细的教学大纲。

课程信息：
- 课程名称：{course_name}
- 课程时长：{course_duration}
- 目标水平：{target_level}

教材内容摘要：
{resource_content[:2000]}

请生成包含以下结构的JSON格式教学大纲：
{{
    "course_title": "课程标题",
    "course_description": "课程描述",
    "learning_objectives": ["学习目标1", "学习目标2", "..."],
    "course_outline": [
        {{
            "week": 1,
            "topic": "主题",
            "objectives": ["目标1", "目标2"],
            "activities": ["活动1", "活动2"],
            "assessment": "评估方式"
        }}
    ],
    "assessment_methods": ["评估方法1", "评估方法2"],
    "required_materials": ["教材1", "教材2"]
}}

要求：
1. 大纲应符合CET-4考试要求
2. 每周安排应循序渐进
3. 包含听说读写译五个技能
4. 注重实用性和应试技巧
5. 输出纯JSON格式，不要其他文字
"""
        return prompt

    def _build_lesson_plan_prompt(
        self, syllabus: dict[str, Any], lesson_info: dict[str, Any]
    ) -> str:
        """构建教案生成提示词"""
        lesson_title = lesson_info.get("title", "英语四级课程")
        lesson_duration = lesson_info.get("duration", "90分钟")
        lesson_objectives = lesson_info.get("objectives", [])

        prompt = f"""
请基于以下教学大纲，为"{lesson_title}"生成详细的教案。

教学大纲：
{json.dumps(syllabus, ensure_ascii=False, indent=2)[:1500]}

课时信息：
- 课时标题：{lesson_title}
- 课时时长：{lesson_duration}
- 学习目标：{", ".join(lesson_objectives)}

请生成包含以下结构的JSON格式教案：
{{
    "lesson_title": "课时标题",
    "duration": "课时时长",
    "objectives": ["学习目标1", "学习目标2"],
    "materials": ["教学材料1", "教学材料2"],
    "lesson_structure": [
        {{
            "phase": "导入阶段",
            "duration": "10分钟",
            "activities": ["活动1", "活动2"],
            "teacher_actions": ["教师行为1", "教师行为2"],
            "student_actions": ["学生行为1", "学生行为2"]
        }}
    ],
    "assessment": {{
        "formative": ["形成性评估1", "形成性评估2"],
        "summative": ["总结性评估1", "总结性评估2"]
    }},
    "homework": ["作业1", "作业2"],
    "reflection": "教学反思要点"
}}

要求：
1. 教案应详细具体，可操作性强
2. 时间安排合理，活动丰富多样
3. 符合CET-4教学目标
4. 注重师生互动和学生参与
5. 输出纯JSON格式，不要其他文字
"""
        return prompt

    def _build_summary_prompt(self, content: str, summary_type: str) -> str:
        """构建摘要生成提示词"""
        content_preview = content[:1500]

        if summary_type == "key_points":
            prompt = f"""
请从以下内容中提取5个关键要点：

{content_preview}

要求：
1. 每个要点简洁明了
2. 突出核心概念
3. 按重要性排序
4. 用简体中文表达
"""
        elif summary_type == "hierarchical":
            prompt = f"""
请为以下内容生成分层摘要：

{content_preview}

要求：
1. 整体摘要（100字以内）
2. 章节摘要（每章50字以内）
3. 关键概念列表
4. 用简体中文表达
"""
        else:  # general
            prompt = f"""
请为以下内容生成简要摘要：

{content_preview}

要求：
1. 摘要长度150字以内
2. 突出主要内容和观点
3. 语言简洁流畅
4. 用简体中文表达
"""

        return prompt

    def _get_current_api_key(self) -> str:
        """获取当前API密钥"""
        return self.api_keys[self.current_key_index]

    def _rotate_api_key(self) -> None:
        """轮换API密钥"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to API key index: {self.current_key_index}")

    async def get_service_stats(self) -> dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "service_name": "DeepSeek Content Generation Service",
            "api_keys_count": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "max_prompt_length": self.max_prompt_length,
            "supported_models": ["deepseek-chat"],
            "max_retries": self.max_retries,
        }
