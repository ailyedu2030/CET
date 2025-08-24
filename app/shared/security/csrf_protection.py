"""CSRF防护模块

提供全面的跨站请求伪造(CSRF)攻击防护，包括令牌生成、验证、
同源检查等功能。
"""

import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CSRFValidationResult(Enum):
    """CSRF验证结果"""

    VALID = "valid"
    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    MISSING_TOKEN = "missing_token"
    ORIGIN_MISMATCH = "origin_mismatch"
    REFERER_MISMATCH = "referer_mismatch"


@dataclass
class CSRFToken:
    """CSRF令牌"""

    token: str
    timestamp: float
    user_id: str | None
    session_id: str | None
    expires_at: float


@dataclass
class CSRFValidation:
    """CSRF验证结果"""

    is_valid: bool
    result: CSRFValidationResult
    token_info: CSRFToken | None
    details: dict[str, Any]


class CSRFProtection:
    """CSRF攻击防护器"""

    def __init__(self, secret_key: str, token_lifetime: int = 3600) -> None:
        """初始化CSRF防护器

        Args:
            secret_key: 用于签名的密钥
            token_lifetime: 令牌有效期（秒）
        """
        self.secret_key = secret_key.encode("utf-8")
        self.token_lifetime = token_lifetime
        self.token_cache: dict[str, CSRFToken] = {}

    def generate_token(
        self, user_id: str | None = None, session_id: str | None = None
    ) -> CSRFToken:
        """生成CSRF令牌"""
        timestamp = time.time()
        expires_at = timestamp + self.token_lifetime

        # 生成随机令牌
        random_bytes = secrets.token_bytes(32)

        # 创建签名数据
        sign_data = f"{timestamp}:{user_id or ''}:{session_id or ''}".encode()
        signature = hmac.new(self.secret_key, random_bytes + sign_data, hashlib.sha256).hexdigest()

        # 组合令牌
        token = f"{random_bytes.hex()}:{timestamp}:{signature}"

        csrf_token = CSRFToken(
            token=token,
            timestamp=timestamp,
            user_id=user_id,
            session_id=session_id,
            expires_at=expires_at,
        )

        # 缓存令牌
        self.token_cache[token] = csrf_token

        # 清理过期令牌
        self._cleanup_expired_tokens()

        logger.debug(f"Generated CSRF token for user {user_id}, session {session_id}")
        return csrf_token

    def validate_token(
        self,
        token: str,
        user_id: str | None = None,
        session_id: str | None = None,
        origin: str | None = None,
        referer: str | None = None,
        allowed_origins: list[str] | None = None,
    ) -> CSRFValidation:
        """验证CSRF令牌"""
        if not token:
            return CSRFValidation(
                is_valid=False,
                result=CSRFValidationResult.MISSING_TOKEN,
                token_info=None,
                details={"reason": "token_not_provided"},
            )

        # 检查令牌格式
        try:
            parts = token.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid token format")

            random_hex, timestamp_str, signature = parts
            timestamp = float(timestamp_str)

        except (ValueError, IndexError) as e:
            return CSRFValidation(
                is_valid=False,
                result=CSRFValidationResult.INVALID_TOKEN,
                token_info=None,
                details={"reason": "malformed_token", "error": str(e)},
            )

        # 检查令牌是否过期
        current_time = time.time()
        if current_time > timestamp + self.token_lifetime:
            return CSRFValidation(
                is_valid=False,
                result=CSRFValidationResult.EXPIRED_TOKEN,
                token_info=None,
                details={
                    "reason": "token_expired",
                    "expired_at": timestamp + self.token_lifetime,
                },
            )

        # 验证签名
        try:
            random_bytes = bytes.fromhex(random_hex)
            sign_data = f"{timestamp}:{user_id or ''}:{session_id or ''}".encode()
            expected_signature = hmac.new(
                self.secret_key, random_bytes + sign_data, hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return CSRFValidation(
                    is_valid=False,
                    result=CSRFValidationResult.INVALID_TOKEN,
                    token_info=None,
                    details={"reason": "signature_mismatch"},
                )

        except Exception as e:
            return CSRFValidation(
                is_valid=False,
                result=CSRFValidationResult.INVALID_TOKEN,
                token_info=None,
                details={"reason": "signature_validation_error", "error": str(e)},
            )

        # 检查Origin头
        if origin and allowed_origins:
            if not self._validate_origin(origin, allowed_origins):
                return CSRFValidation(
                    is_valid=False,
                    result=CSRFValidationResult.ORIGIN_MISMATCH,
                    token_info=None,
                    details={"reason": "origin_not_allowed", "origin": origin},
                )

        # 检查Referer头
        if referer and allowed_origins:
            if not self._validate_referer(referer, allowed_origins):
                return CSRFValidation(
                    is_valid=False,
                    result=CSRFValidationResult.REFERER_MISMATCH,
                    token_info=None,
                    details={"reason": "referer_not_allowed", "referer": referer},
                )

        # 获取令牌信息
        token_info = self.token_cache.get(token)
        if not token_info:
            token_info = CSRFToken(
                token=token,
                timestamp=timestamp,
                user_id=user_id,
                session_id=session_id,
                expires_at=timestamp + self.token_lifetime,
            )

        return CSRFValidation(
            is_valid=True,
            result=CSRFValidationResult.VALID,
            token_info=token_info,
            details={"validation_time": current_time},
        )

    def _validate_origin(self, origin: str, allowed_origins: list[str]) -> bool:
        """验证Origin头"""
        try:
            parsed_origin = urlparse(origin)
            origin_host = parsed_origin.netloc.lower()

            for allowed in allowed_origins:
                parsed_allowed = urlparse(allowed)
                allowed_host = parsed_allowed.netloc.lower()

                if origin_host == allowed_host:
                    return True

                # 支持子域名匹配
                if allowed_host.startswith(".") and origin_host.endswith(allowed_host):
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error validating origin: {str(e)}")
            return False

    def _validate_referer(self, referer: str, allowed_origins: list[str]) -> bool:
        """验证Referer头"""
        try:
            parsed_referer = urlparse(referer)
            referer_origin = f"{parsed_referer.scheme}://{parsed_referer.netloc}"

            return self._validate_origin(referer_origin, allowed_origins)

        except Exception as e:
            logger.warning(f"Error validating referer: {str(e)}")
            return False

    def _cleanup_expired_tokens(self) -> None:
        """清理过期令牌"""
        current_time = time.time()
        expired_tokens = [
            token
            for token, token_info in self.token_cache.items()
            if current_time > token_info.expires_at
        ]

        for token in expired_tokens:
            del self.token_cache[token]

        if expired_tokens:
            logger.debug(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")

    def invalidate_token(self, token: str) -> bool:
        """使令牌失效"""
        if token in self.token_cache:
            del self.token_cache[token]
            logger.debug(f"Invalidated CSRF token: {token[:16]}...")
            return True
        return False

    def invalidate_user_tokens(self, user_id: str) -> int:
        """使用户的所有令牌失效"""
        invalidated_count = 0
        tokens_to_remove = []

        for token, token_info in self.token_cache.items():
            if token_info.user_id == user_id:
                tokens_to_remove.append(token)

        for token in tokens_to_remove:
            del self.token_cache[token]
            invalidated_count += 1

        logger.debug(f"Invalidated {invalidated_count} CSRF tokens for user {user_id}")
        return invalidated_count

    def get_token_stats(self) -> dict[str, Any]:
        """获取令牌统计信息"""
        current_time = time.time()
        active_tokens = 0
        expired_tokens = 0

        for token_info in self.token_cache.values():
            if current_time <= token_info.expires_at:
                active_tokens += 1
            else:
                expired_tokens += 1

        return {
            "total_tokens": len(self.token_cache),
            "active_tokens": active_tokens,
            "expired_tokens": expired_tokens,
            "token_lifetime": self.token_lifetime,
        }

    def generate_double_submit_cookie(self, token: str) -> tuple[str, str]:
        """生成双重提交Cookie"""
        # 生成Cookie值（令牌的哈希）
        cookie_value = hashlib.sha256(
            (token + self.secret_key.decode("utf-8")).encode("utf-8")
        ).hexdigest()

        # Cookie属性
        cookie_attributes = "HttpOnly; Secure; SameSite=Strict"

        return cookie_value, cookie_attributes

    def validate_double_submit(self, token: str, cookie_value: str) -> bool:
        """验证双重提交"""
        expected_cookie = hashlib.sha256(
            (token + self.secret_key.decode("utf-8")).encode("utf-8")
        ).hexdigest()

        return hmac.compare_digest(cookie_value, expected_cookie)

    def get_security_recommendations(self, validation: CSRFValidation) -> list[str]:
        """获取安全建议"""
        recommendations = []

        if not validation.is_valid:
            recommendations.extend(
                [
                    "在所有状态改变操作中使用CSRF令牌",
                    "验证Origin和Referer头",
                    "使用SameSite Cookie属性",
                    "实施双重提交Cookie模式",
                ]
            )

            if validation.result == CSRFValidationResult.INVALID_TOKEN:
                recommendations.extend(
                    [
                        "检查令牌生成和传输过程",
                        "确保令牌格式正确",
                        "记录可疑的CSRF攻击尝试",
                    ]
                )
            elif validation.result == CSRFValidationResult.EXPIRED_TOKEN:
                recommendations.extend(["适当调整令牌有效期", "实施令牌自动刷新机制"])

        return recommendations


# 全局CSRF防护器实例（需要在应用启动时用实际密钥初始化）
csrf_protection: CSRFProtection | None = None


def initialize_csrf_protection(secret_key: str, token_lifetime: int = 3600) -> None:
    """初始化CSRF防护器"""
    global csrf_protection
    csrf_protection = CSRFProtection(secret_key, token_lifetime)
    logger.info("CSRF protection initialized")


def get_csrf_protection() -> CSRFProtection:
    """获取CSRF防护器实例"""
    if csrf_protection is None:
        raise RuntimeError(
            "CSRF protection not initialized. Call initialize_csrf_protection() first."
        )
    return csrf_protection
