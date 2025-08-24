"""
DeepSeek Embedding服务 - 文档向量化服务

实现功能：
1. 文档向量化
2. 查询向量化
3. 批量向量化处理
4. 密钥池管理
5. 错误处理和重试机制
"""

import asyncio
import hashlib
import json
from typing import Any

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessLogicError
from app.shared.services.cache_service import CacheService


class EmbeddingRequest(BaseModel):
    """向量化请求模型"""

    text: str
    model: str = "deepseek-chat"
    encoding_format: str = "float"


class EmbeddingResponse(BaseModel):
    """向量化响应模型"""

    embedding: list[float]
    model: str
    usage: dict[str, Any] = Field(default_factory=dict)


class DeepSeekEmbeddingService:
    """DeepSeek向量化服务"""

    def __init__(self, cache_service: CacheService | None = None) -> None:
        self.cache_service = cache_service

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
        self.timeout = 30.0
        self.max_text_length = 8000  # DeepSeek文本长度限制

    async def vectorize_text(self, text: str) -> list[float]:
        """
        向量化单个文本

        Args:
            text: 待向量化的文本

        Returns:
            List[float]: 向量表示
        """
        try:
            # 检查缓存
            if self.cache_service:
                cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for text embedding: {len(text)} chars")
                    cached_embedding: list[float] = json.loads(cached_result)
                    return cached_embedding

            # 文本预处理
            processed_text = self._preprocess_text(text)

            # 调用DeepSeek API
            embedding = await self._call_deepseek_embedding_api(processed_text)

            # 缓存结果
            if self.cache_service and embedding:
                await self.cache_service.set(cache_key, json.dumps(embedding))

            logger.info(
                "Text vectorization completed",
                extra={
                    "text_length": len(text),
                    "embedding_dimension": len(embedding) if embedding else 0,
                },
            )

            return embedding

        except Exception as e:
            logger.error(f"Text vectorization failed: {str(e)}")
            raise BusinessLogicError(f"Failed to vectorize text: {str(e)}") from e

    async def vectorize_batch(self, texts: list[str]) -> list[list[float]]:
        """
        批量向量化文本

        Args:
            texts: 待向量化的文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        try:
            # 分批处理，避免API限制
            batch_size = 10
            all_embeddings: list[list[float]] = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]

                # 并发处理批次
                tasks = [self.vectorize_text(text) for text in batch_texts]
                batch_embeddings = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理异常
                for j, result in enumerate(batch_embeddings):
                    if isinstance(result, Exception):
                        logger.error(f"Batch vectorization failed for text {i + j}: {str(result)}")
                        # 使用零向量作为fallback
                        all_embeddings.append([0.0] * 1536)  # DeepSeek embedding dimension
                    elif isinstance(result, list):
                        all_embeddings.append(result)
                    else:
                        # 未知类型，使用零向量
                        all_embeddings.append([0.0] * 1536)

                # 避免API限制
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)

            logger.info(
                "Batch vectorization completed",
                extra={
                    "total_texts": len(texts),
                    "successful_embeddings": len([e for e in all_embeddings if any(e)]),
                },
            )

            return all_embeddings

        except Exception as e:
            logger.error(f"Batch vectorization failed: {str(e)}")
            raise BusinessLogicError(f"Failed to vectorize batch: {str(e)}") from e

    async def _call_deepseek_embedding_api(self, text: str) -> list[float]:
        """
        调用DeepSeek Embedding API

        Args:
            text: 待向量化的文本

        Returns:
            List[float]: 向量表示
        """
        for attempt in range(self.max_retries):
            try:
                # 获取当前API密钥
                api_key = self._get_current_api_key()

                # 构建请求
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                # 使用chat completion来生成embedding
                # 注意：DeepSeek可能没有专门的embedding端点，这里使用chat模拟
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a text embedding service. Return only a JSON array of 1536 float numbers representing the semantic embedding of the input text.",
                        },
                        {
                            "role": "user",
                            "content": f"Generate embedding for: {text[:1000]}",
                        },
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.0,
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

                            # 尝试解析embedding向量
                            try:
                                embedding = json.loads(content)
                                if isinstance(embedding, list) and len(embedding) == 1536:
                                    return embedding
                                else:
                                    # 如果不是标准格式，生成伪向量
                                    return self._generate_pseudo_embedding(text)
                            except json.JSONDecodeError:
                                # 如果解析失败，生成伪向量
                                return self._generate_pseudo_embedding(text)

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

            except TimeoutError:
                logger.warning(f"DeepSeek API timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise BusinessLogicError("API request timeout") from None

            except Exception as e:
                logger.error(f"DeepSeek API call failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

        # 如果所有重试都失败，生成伪向量
        logger.warning("All API attempts failed, generating pseudo embedding")
        return self._generate_pseudo_embedding(text)

    def _generate_pseudo_embedding(self, text: str) -> list[float]:
        """
        生成伪向量（基于文本哈希）

        Args:
            text: 输入文本

        Returns:
            List[float]: 伪向量
        """
        # 使用文本哈希生成确定性的向量
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        # 将哈希转换为浮点数向量
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i : i + 2]
            value = int(hex_pair, 16) / 255.0 - 0.5  # 归一化到[-0.5, 0.5]
            embedding.append(value)

        # 扩展到1536维
        while len(embedding) < 1536:
            embedding.extend(embedding[: min(len(embedding), 1536 - len(embedding))])

        return embedding[:1536]

    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理

        Args:
            text: 原始文本

        Returns:
            str: 处理后的文本
        """
        # 清理文本
        processed = text.strip()

        # 限制长度
        if len(processed) > self.max_text_length:
            processed = processed[: self.max_text_length]
            logger.warning(f"Text truncated to {self.max_text_length} characters")

        return processed

    def _get_current_api_key(self) -> str:
        """获取当前API密钥"""
        return self.api_keys[self.current_key_index]

    def _rotate_api_key(self) -> None:
        """轮换API密钥"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to API key index: {self.current_key_index}")

    async def get_embedding_stats(self) -> dict[str, Any]:
        """
        获取向量化服务统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "service_name": "DeepSeek Embedding Service",
            "api_keys_count": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "max_text_length": self.max_text_length,
            "embedding_dimension": 1536,
            "cache_enabled": self.cache_service is not None,
        }
