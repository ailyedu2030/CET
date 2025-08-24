"""DeepSeek API集成服务."""

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from app.ai.models.ai_models import AITaskLog
from app.ai.utils.api_key_pool import APICallManager, get_api_stats, get_deepseek_pool
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


class DeepSeekAPIError(Exception):
    """DeepSeek API错误."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class DeepSeekService:
    """DeepSeek API服务."""

    def __init__(self) -> None:
        self.base_url = getattr(settings, "DEEPSEEK_API_BASE_URL", "https://api.deepseek.com")
        self.default_model = getattr(settings, "DEEPSEEK_DEFAULT_MODEL", "deepseek-chat")
        self.timeout = getattr(settings, "DEEPSEEK_TIMEOUT", 60)
        self.max_tokens = getattr(settings, "DEEPSEEK_MAX_TOKENS", 4096)

        # 请求配置
        self.default_parameters = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

    async def generate_completion(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        user_id: int | None = None,
        task_type: str = "completion",
        **kwargs: Any,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """生成AI补全."""
        start_time = time.time()

        try:
            # 获取密钥池和调用管理器
            key_pool = await get_deepseek_pool()
            call_manager = APICallManager(key_pool)

            # 准备请求参数
            request_params = self._prepare_request_params(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # 执行API调用
            success, result, error_msg = await call_manager.execute_with_retry(
                self._make_api_call,
                request_params=request_params,
                max_retries=3,
            )

            # 计算执行时间
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 记录统计
            tokens_used = 0
            if success and result:
                tokens_used = result.get("usage", {}).get("total_tokens", 0)

            stats = get_api_stats()
            await stats.record_call(success, tokens_used, execution_time_ms)

            # 记录任务日志
            if user_id:
                await self._log_ai_task(
                    task_type=task_type,
                    request_data={
                        "prompt": prompt[:500],
                        "model": model or self.default_model,
                    },
                    response_data=result if success else None,
                    status="success" if success else "failed",
                    error_message=error_msg,
                    tokens_used=tokens_used,
                    execution_time_ms=execution_time_ms,
                    user_id=user_id,
                )

            return success, result, error_msg

        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            return False, None, str(e)

    async def stream_completion(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        user_id: int | None = None,
        task_type: str = "streaming",
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """流式生成AI补全."""
        try:
            # 获取密钥池
            key_pool = await get_deepseek_pool()
            api_key = await key_pool.get_available_key()

            if not api_key:
                yield "[错误: 无可用API密钥]"
                return

            # 准备请求参数
            request_params = self._prepare_request_params(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,  # 启用流式输出
                **kwargs,
            )

            # 构建请求头
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 流式API调用
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_params,
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            line_text = line.decode("utf-8").strip()
                            if line_text.startswith("data: "):
                                data_text = line_text[6:]  # 移除 'data: ' 前缀
                                if data_text == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_text)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.text()
                        yield f"[API错误: {response.status} - {error_text}]"

        except TimeoutError:
            yield "[错误: 请求超时]"
        except Exception as e:
            logger.error(f"流式API调用失败: {str(e)}")
            yield f"[错误: {str(e)}]"

    def _prepare_request_params(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """准备API请求参数."""
        params = self.default_parameters.copy()

        # 更新参数
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        # 添加额外参数
        params.update(kwargs)

        # 构建消息格式
        params.update(
            {
                "model": model or self.default_model,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        return params

    async def _make_api_call(self, api_key: str, request_params: dict[str, Any]) -> dict[str, Any]:
        """执行单次API调用."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CET4-Learning-System/1.0",
        }

        url = f"{self.base_url}/v1/chat/completions"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            try:
                async with session.post(url, headers=headers, json=request_params) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        return response_data  # type: ignore[no-any-return]
                    else:
                        error_msg = response_data.get("error", {}).get("message", "未知错误")
                        raise DeepSeekAPIError(
                            message=error_msg,
                            error_code=response_data.get("error", {}).get("code"),
                            status_code=response.status,
                        )

            except TimeoutError as e:
                raise DeepSeekAPIError("API请求超时") from e
            except aiohttp.ClientError as e:
                raise DeepSeekAPIError(f"网络请求错误: {str(e)}") from e
            except json.JSONDecodeError as e:
                raise DeepSeekAPIError("API响应格式错误") from e

    async def generate_syllabus_content(
        self, prompt: str, user_id: int, **kwargs: Any
    ) -> tuple[bool, str | None, str | None]:
        """生成大纲内容."""
        success, result, error_msg = await self.generate_completion(
            prompt=prompt,
            user_id=user_id,
            task_type="syllabus",
            temperature=0.6,  # 大纲生成需要较低随机性
            **kwargs,
        )

        if success and result:
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, content, None

        return False, None, error_msg

    async def generate_lesson_plan_content(
        self, prompt: str, user_id: int, **kwargs: Any
    ) -> tuple[bool, str | None, str | None]:
        """生成教案内容."""
        success, result, error_msg = await self.generate_completion(
            prompt=prompt,
            user_id=user_id,
            task_type="lesson_plan",
            temperature=0.7,  # 教案生成允许中等创造性
            **kwargs,
        )

        if success and result:
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, content, None

        return False, None, error_msg

    async def generate_smart_suggestions(
        self, prompt: str, user_id: int, **kwargs: Any
    ) -> tuple[bool, str | None, str | None]:
        """生成智能建议."""
        success, result, error_msg = await self.generate_completion(
            prompt=prompt,
            user_id=user_id,
            task_type="suggestion",
            temperature=0.8,  # 建议生成允许较高创造性
            max_tokens=2048,  # 建议通常较短
            **kwargs,
        )

        if success and result:
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, content, None

        return False, None, error_msg

    async def _log_ai_task(
        self,
        task_type: str,
        request_data: dict[str, Any],
        response_data: dict[str, Any] | None,
        status: str,
        error_message: str | None,
        tokens_used: int,
        execution_time_ms: int,
        user_id: int,
    ) -> None:
        """记录AI任务日志."""
        try:
            async for db in get_db():
                log_entry = AITaskLog(
                    task_type=task_type,
                    request_data=request_data,
                    response_data=response_data,
                    api_provider="deepseek",
                    api_model=request_data.get("model", self.default_model),
                    tokens_used=tokens_used,
                    execution_time_ms=execution_time_ms,
                    status=status,
                    error_message=error_message,
                    user_id=user_id,
                )

                db.add(log_entry)
                await db.commit()
                break  # 只需要一个数据库连接

        except Exception as e:
            logger.error(f"记录AI任务日志失败: {str(e)}")

    async def get_api_status(self) -> dict[str, Any]:
        """获取API服务状态."""
        try:
            # 获取密钥池状态
            key_pool = await get_deepseek_pool()
            pool_status = key_pool.get_pool_status()

            # 获取使用统计
            stats = get_api_stats()
            usage_stats = stats.get_stats()

            # 测试API连通性
            test_success, _, test_error = await self.generate_completion(
                prompt="Hello, this is a connectivity test.",
                max_tokens=10,
                temperature=0.1,
            )

            return {
                "service_status": "healthy" if test_success else "unhealthy",
                "test_error": test_error,
                "key_pool_status": pool_status,
                "usage_statistics": usage_stats,
                "configuration": {
                    "base_url": self.base_url,
                    "default_model": self.default_model,
                    "timeout": self.timeout,
                    "max_tokens": self.max_tokens,
                },
            }

        except Exception as e:
            logger.error(f"获取API状态失败: {str(e)}")
            return {
                "service_status": "error",
                "error": str(e),
            }

    async def validate_api_key(self, api_key: str) -> tuple[bool, str | None]:
        """验证API密钥有效性."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 简单的验证请求
        test_params = {
            "model": self.default_model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 5,
            "temperature": 0.1,
        }

        url = f"{self.base_url}/v1/chat/completions"

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(url, headers=headers, json=test_params) as response:
                    if response.status == 200:
                        return True, None
                    else:
                        response_data = await response.json()
                        error_msg = response_data.get("error", {}).get("message", "验证失败")
                        return False, error_msg

        except Exception as e:
            return False, f"验证请求失败: {str(e)}"


# 全局服务实例
_deepseek_service: DeepSeekService | None = None


def get_deepseek_service() -> DeepSeekService:
    """获取DeepSeek服务实例."""
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekService()
    return _deepseek_service
