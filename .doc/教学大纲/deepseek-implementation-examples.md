# DeepSeek优化实现代码示例

## 📋 文档概述

本文档提供基于DeepSeek模型特性优化的具体代码实现示例，可直接应用于教学大纲生成系统的改进。

## 🔧 优化后的DeepSeek服务实现

### 1. 核心服务类优化

````python
# backend/ai_services/optimized_deepseek_service.py

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
import openai

from .services import DeepSeekAPIService


@dataclass
class ModelConfig:
    """模型配置"""
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    use_reasoning: bool = False


class OptimizedDeepSeekService(DeepSeekAPIService):
    """优化的DeepSeek服务"""

    # 优化的模型配置
    OPTIMIZED_MODEL_CONFIGS = {
        "reasoning_analysis": ModelConfig(
            model="deepseek-reasoner",
            temperature=0.6,
            max_tokens=4000,
            top_p=0.9,
            use_reasoning=True
        ),
        "structured_generation": ModelConfig(
            model="deepseek-chat",
            temperature=0.3,
            max_tokens=6000,
            top_p=0.8,
            use_reasoning=False
        ),
        "creative_generation": ModelConfig(
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=8000,
            top_p=0.95,
            use_reasoning=False
        ),
        "quality_assessment": ModelConfig(
            model="deepseek-reasoner",
            temperature=0.5,
            max_tokens=3000,
            top_p=0.85,
            use_reasoning=True
        )
    }

    def __init__(self):
        super().__init__()
        self.cache_manager = IntelligentCacheManager()
        self.prompt_optimizer = DeepSeekPromptOptimizer()

    async def analyze_with_reasoning(
        self,
        content: str,
        analysis_type: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """使用推理模型进行分析"""

        # 1. 选择最优配置
        config = self._select_optimal_config(analysis_type, len(content))

        # 2. 构建推理提示词
        prompt = self.prompt_optimizer.build_reasoning_prompt(
            problem_statement=f"请对以下{analysis_type}内容进行深度分析",
            analysis_context={"content": content, "context": context or {}},
            expected_output=self._get_expected_output_format(analysis_type)
        )

        # 3. 缓存检查
        cache_key = self._generate_cache_key(prompt, config)
        cached_result = await self.cache_manager.get_cached_result(cache_key)

        if cached_result:
            return {**cached_result, "from_cache": True}

        # 4. 执行分析
        result = await self._call_optimized_api(prompt, config)

        # 5. 缓存结果
        await self.cache_manager.cache_result(cache_key, result, ttl=3600)

        return result

    async def generate_with_context(
        self,
        task_description: str,
        context_data: Dict[str, Any],
        output_format: str,
        generation_type: str = "structured"
    ) -> Dict[str, Any]:
        """基于上下文生成内容"""

        # 1. 选择生成配置
        config_key = f"{generation_type}_generation"
        config = self.OPTIMIZED_MODEL_CONFIGS.get(
            config_key,
            self.OPTIMIZED_MODEL_CONFIGS["structured_generation"]
        )

        # 2. 构建结构化提示词
        prompt = self.prompt_optimizer.build_structured_prompt(
            task_description=task_description,
            context_data=context_data,
            output_format=output_format,
            reasoning_required=(generation_type == "reasoning")
        )

        # 3. 执行生成
        result = await self._call_optimized_api(prompt, config)

        # 4. 质量验证
        validated_result = self._validate_generation_quality(result, output_format)

        return validated_result

    def _select_optimal_config(self, task_type: str, content_length: int) -> ModelConfig:
        """选择最优模型配置"""

        # 基于任务类型选择
        if task_type in ["structure_analysis", "knowledge_extraction", "difficulty_assessment"]:
            base_config = self.OPTIMIZED_MODEL_CONFIGS["reasoning_analysis"]
        elif task_type in ["json_generation", "data_extraction"]:
            base_config = self.OPTIMIZED_MODEL_CONFIGS["structured_generation"]
        elif task_type in ["content_generation", "lesson_plan"]:
            base_config = self.OPTIMIZED_MODEL_CONFIGS["creative_generation"]
        else:
            base_config = self.OPTIMIZED_MODEL_CONFIGS["structured_generation"]

        # 基于内容长度调整
        if content_length > 50000:  # 长文档
            adjusted_config = ModelConfig(
                model=base_config.model,
                temperature=max(0.3, base_config.temperature - 0.1),  # 降低温度提高稳定性
                max_tokens=min(8000, base_config.max_tokens + 1000),  # 增加输出长度
                top_p=base_config.top_p,
                use_reasoning=base_config.use_reasoning
            )
            return adjusted_config

        return base_config

    async def _call_optimized_api(
        self,
        prompt: str,
        config: ModelConfig,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """优化的API调用"""

        messages = [
            {
                "role": "system",
                "content": self._get_optimized_system_prompt(config.use_reasoning)
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            start_time = time.time()

            response = self._call_api(
                messages=messages,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            processing_time = time.time() - start_time

            # 提取推理过程（如果使用推理模型）
            if config.use_reasoning and config.model == "deepseek-reasoner":
                reasoning_content = self._extract_reasoning_content(response["content"])
                final_answer = self._extract_final_answer(response["content"])

                return {
                    "reasoning_process": reasoning_content,
                    "final_answer": final_answer,
                    "raw_content": response["content"],
                    "model_used": config.model,
                    "processing_time": processing_time,
                    "tokens_used": response["usage"]["total_tokens"],
                    "cost": response.get("cost", 0)
                }
            else:
                return {
                    "content": response["content"],
                    "model_used": config.model,
                    "processing_time": processing_time,
                    "tokens_used": response["usage"]["total_tokens"],
                    "cost": response.get("cost", 0)
                }

        except Exception as e:
            if retry_count < 2:  # 最多重试2次
                # 调整参数重试
                adjusted_config = self._adjust_config_for_retry(config, retry_count)
                return await self._call_optimized_api(prompt, adjusted_config, retry_count + 1)
            else:
                raise e

    def _get_optimized_system_prompt(self, use_reasoning: bool) -> str:
        """获取优化的系统提示词"""

        base_prompt = """你是专业的教育内容分析和生成专家，具备深厚的教育学理论知识和丰富的实践经验。"""

        if use_reasoning:
            return base_prompt + """
请使用以下结构进行分析：
1. 在<think>标签中进行详细的思考和推理
2. 在<answer>标签中提供最终的分析结果
3. 确保推理过程逻辑清晰、结论准确可靠
"""
        else:
            return base_prompt + """
请提供准确、结构化的分析结果，确保输出格式符合要求。
"""

    def _extract_reasoning_content(self, content: str) -> str:
        """提取推理过程"""
        import re

        think_pattern = r'<think>(.*?)</think>'
        match = re.search(think_pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()
        return ""

    def _extract_final_answer(self, content: str) -> str:
        """提取最终答案"""
        import re

        answer_pattern = r'<answer>(.*?)</answer>'
        match = re.search(answer_pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        # 如果没有answer标签，返回整个内容
        return content

    def _adjust_config_for_retry(self, config: ModelConfig, retry_count: int) -> ModelConfig:
        """调整配置用于重试"""

        return ModelConfig(
            model=config.model,
            temperature=max(0.1, config.temperature - 0.1 * retry_count),
            max_tokens=min(8000, config.max_tokens + 500 * retry_count),
            top_p=max(0.7, config.top_p - 0.05 * retry_count),
            use_reasoning=config.use_reasoning
        )

    def _generate_cache_key(self, prompt: str, config: ModelConfig) -> str:
        """生成缓存键"""

        content_hash = hashlib.md5(prompt.encode()).hexdigest()[:16]
        config_hash = hashlib.md5(
            f"{config.model}:{config.temperature}:{config.max_tokens}".encode()
        ).hexdigest()[:8]

        return f"deepseek:optimized:{content_hash}:{config_hash}"


class IntelligentCacheManager:
    """智能缓存管理器"""

    def __init__(self):
        self.cache_prefix = "deepseek_optimized"

    async def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""

        full_key = f"{self.cache_prefix}:{cache_key}"
        cached_data = cache.get(full_key)

        if cached_data:
            # 更新缓存命中统计
            self._update_cache_stats("hit")
            return cached_data

        self._update_cache_stats("miss")
        return None

    async def cache_result(
        self,
        cache_key: str,
        result: Dict[str, Any],
        ttl: int = 3600
    ) -> None:
        """缓存结果"""

        full_key = f"{self.cache_prefix}:{cache_key}"

        # 只缓存成功的结果
        if result.get("success", True):
            cache.set(full_key, result, ttl)
            self._update_cache_stats("store")

    def _update_cache_stats(self, operation: str) -> None:
        """更新缓存统计"""

        stats_key = f"{self.cache_prefix}:stats"
        stats = cache.get(stats_key, {"hits": 0, "misses": 0, "stores": 0})

        if operation in stats:
            stats[operation] += 1
            cache.set(stats_key, stats, 86400)  # 24小时


class DeepSeekPromptOptimizer:
    """DeepSeek提示词优化器"""

    def build_reasoning_prompt(
        self,
        problem_statement: str,
        analysis_context: Dict[str, Any],
        expected_output: str
    ) -> str:
        """构建推理提示词"""

        context_str = self._format_context(analysis_context)

        return f"""# 深度分析任务

## 问题描述
{problem_statement}

## 分析材料
{context_str}

## 分析要求
请使用以下结构进行深度分析：

<think>
请在这里进行详细的思考和推理：
1. 问题理解和关键信息识别
2. 分析方法选择和应用
3. 逻辑推理过程
4. 结论验证和质量检查
</think>

<answer>
{expected_output}
</answer>

## 质量标准
- 推理过程要逻辑清晰、步骤完整
- 最终答案要准确、完整、符合格式要求
- 如有不确定性，请明确说明并提供最佳判断
"""

    def build_structured_prompt(
        self,
        task_description: str,
        context_data: Dict[str, Any],
        output_format: str,
        reasoning_required: bool = False
    ) -> str:
        """构建结构化提示词"""

        prompt_parts = [
            f"# 任务：{task_description}",
            "",
            "## 输入信息"
        ]

        # 添加上下文信息
        for key, value in context_data.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)

            prompt_parts.append(f"**{key}**:")
            prompt_parts.append(f"```\n{value_str}\n```")
            prompt_parts.append("")

        # 添加处理要求
        if reasoning_required:
            prompt_parts.extend([
                "## 处理要求",
                "请按以下步骤进行分析：",
                "1. 理解任务要求和输入信息",
                "2. 分析关键要素和关系",
                "3. 应用专业知识进行推理",
                "4. 生成符合要求的输出",
                ""
            ])

        # 添加输出格式
        prompt_parts.extend([
            "## 输出格式",
            output_format,
            "",
            "## 质量要求",
            "- 严格按照指定格式输出",
            "- 确保内容准确、完整",
            "- 逻辑清晰、表述规范",
            "- 避免重复和冗余信息"
        ])

        return "\n".join(prompt_parts)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""

        formatted_parts = []

        for key, value in context.items():
            if isinstance(value, str) and len(value) > 1000:
                # 长文本截取
                value = value[:1000] + "...[内容截取]"
            elif isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)

            formatted_parts.append(f"**{key}**: {value}")

        return "\n".join(formatted_parts)
````

## 🔗 相关文档

- [DeepSeek优化策略](./deepseek-optimization-strategy.md)
- [技术实现详细设计](./teaching-syllabus-technical-implementation.md)

---

**文档版本**: v1.0  
**创建日期**: 2025-01-22  
**最后更新**: 2025-01-22
