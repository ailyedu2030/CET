"""降级服务 - AI服务故障时的降级处理."""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.ai_models import FallbackLog

logger = logging.getLogger(__name__)


class FallbackLevel(Enum):
    """降级级别"""

    LEVEL_0 = 0  # 正常服务
    LEVEL_1 = 1  # 轻度降级 - 使用缓存
    LEVEL_2 = 2  # 中度降级 - 简化响应
    LEVEL_3 = 3  # 重度降级 - 预设响应
    LEVEL_4 = 4  # 完全降级 - 错误响应


class FallbackReason(Enum):
    """降级原因"""

    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_UNAVAILABLE = "service_unavailable"
    COST_LIMIT = "cost_limit"


class FallbackService:
    """降级服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.current_level = FallbackLevel.LEVEL_0
        self.fallback_cache: dict[str, Any] = {}

        # 预设响应模板
        self.preset_responses = {
            "question_generation": {
                "questions": [
                    {
                        "question": "请根据以下内容回答问题：",
                        "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                        "answer": "A",
                        "explanation": "这是一个预设的示例题目。",
                    }
                ],
                "total": 1,
            },
            "content_analysis": {
                "analysis": "由于服务暂时不可用，无法提供详细分析。请稍后重试。",
                "confidence": 0.0,
            },
            "grading": {
                "score": 0,
                "feedback": "系统暂时无法评分，请稍后重试。",
                "suggestions": [],
            },
        }

    async def handle_fallback(
        self,
        db: AsyncSession,
        original_request: dict[str, Any],
        error: Exception,
        reason: FallbackReason,
    ) -> dict[str, Any]:
        """处理降级请求"""
        try:
            # 确定降级级别
            fallback_level = self._determine_fallback_level(error, reason)

            # 记录降级日志
            await self._log_fallback(db, fallback_level, reason, str(error))

            # 执行降级处理
            fallback_response = await self._execute_fallback(
                original_request, fallback_level, reason
            )

            return {
                "success": True,
                "fallback_level": fallback_level.value,
                "reason": reason.value,
                "response": fallback_response,
                "is_fallback": True,
            }

        except Exception as e:
            self.logger.error(f"降级处理失败: {e}")
            return {
                "success": False,
                "fallback_level": FallbackLevel.LEVEL_4.value,
                "reason": "fallback_error",
                "response": {"error": "服务暂时不可用"},
                "is_fallback": True,
            }

    def _determine_fallback_level(self, error: Exception, reason: FallbackReason) -> FallbackLevel:
        """确定降级级别"""
        if reason == FallbackReason.RATE_LIMIT:
            return FallbackLevel.LEVEL_1  # 使用缓存
        elif reason == FallbackReason.TIMEOUT:
            return FallbackLevel.LEVEL_2  # 简化响应
        elif reason == FallbackReason.QUOTA_EXCEEDED:
            return FallbackLevel.LEVEL_3  # 预设响应
        elif reason == FallbackReason.SERVICE_UNAVAILABLE:
            return FallbackLevel.LEVEL_4  # 完全降级
        else:
            return FallbackLevel.LEVEL_2  # 默认中度降级

    async def _execute_fallback(
        self,
        original_request: dict[str, Any],
        level: FallbackLevel,
        reason: FallbackReason,
    ) -> dict[str, Any]:
        """执行降级处理"""
        task_type = original_request.get("task_type", "unknown")

        if level == FallbackLevel.LEVEL_1:
            # 尝试从缓存获取
            return await self._get_cached_response(original_request)
        elif level == FallbackLevel.LEVEL_2:
            # 返回简化响应
            return self._get_simplified_response(task_type)
        elif level == FallbackLevel.LEVEL_3:
            # 返回预设响应
            return self._get_preset_response(task_type)
        else:
            # 完全降级
            return {"error": "服务暂时不可用，请稍后重试"}

    async def _get_cached_response(self, request: dict[str, Any]) -> dict[str, Any]:
        """从缓存获取响应"""
        cache_key = self._generate_cache_key(request)

        if cache_key in self.fallback_cache:
            cached_response = self.fallback_cache[cache_key]
            if isinstance(cached_response, dict):
                cached_response["from_cache"] = True
                return cached_response
            else:
                # 缓存数据格式错误，返回简化响应
                return self._get_simplified_response(request.get("task_type", "unknown"))
        else:
            # 缓存未命中，返回简化响应
            return self._get_simplified_response(request.get("task_type", "unknown"))

    def _get_simplified_response(self, task_type: str) -> dict[str, Any]:
        """获取简化响应"""
        if task_type == "question_generation":
            return {
                "questions": [],
                "total": 0,
                "message": "由于服务负载过高，暂时无法生成题目",
            }
        elif task_type == "content_analysis":
            return {"analysis": "服务暂时不可用，无法提供分析", "confidence": 0.0}
        elif task_type == "grading":
            return {"score": None, "feedback": "评分服务暂时不可用", "suggestions": []}
        else:
            return {"message": "服务暂时不可用"}

    def _get_preset_response(self, task_type: str) -> dict[str, Any]:
        """获取预设响应"""
        return self.preset_responses.get(task_type, {"message": "服务暂时不可用，请稍后重试"})

    def _generate_cache_key(self, request: dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib

        # 使用请求的关键参数生成缓存键
        key_parts = [
            request.get("task_type", ""),
            str(request.get("prompt", ""))[:100],  # 只取前100个字符
            request.get("model_type", ""),
        ]

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _log_fallback(
        self,
        db: AsyncSession,
        level: FallbackLevel,
        reason: FallbackReason,
        error_message: str,
    ) -> None:
        """记录降级日志"""
        try:
            log_entry = FallbackLog(
                fallback_level=level.value,
                trigger_reason=reason.value,
                error_message=error_message,
                recovery_time=None,  # 恢复时间稍后更新
            )

            db.add(log_entry)
            await db.commit()

        except Exception as e:
            self.logger.error(f"记录降级日志失败: {e}")
            await db.rollback()

    def update_cache(self, request: dict[str, Any], response: dict[str, Any]) -> None:
        """更新降级缓存"""
        try:
            cache_key = self._generate_cache_key(request)
            self.fallback_cache[cache_key] = {
                **response,
                "cached_at": datetime.now().isoformat(),
            }

            # 限制缓存大小
            if len(self.fallback_cache) > 1000:
                # 删除最旧的缓存项
                oldest_key = min(
                    self.fallback_cache.keys(),
                    key=lambda k: self.fallback_cache[k].get("cached_at", ""),
                )
                del self.fallback_cache[oldest_key]

        except Exception as e:
            self.logger.error(f"更新降级缓存失败: {e}")

    def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        return {
            "current_level": self.current_level.value,
            "cache_size": len(self.fallback_cache),
            "status": ("degraded" if self.current_level != FallbackLevel.LEVEL_0 else "normal"),
        }


def get_fallback_service() -> FallbackService:
    """获取降级服务实例"""
    return FallbackService()
