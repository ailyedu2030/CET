"""安全中间件

集成SQL注入防护、XSS防护、CSRF防护、API限流等安全功能，
为FastAPI应用提供全面的安全防护。
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.security.csrf_protection import (
    CSRFValidationResult,
    get_csrf_protection,
)
from app.shared.security.rate_limiter import RateLimitResult, rate_limiter
from app.shared.security.sql_injection_guard import (
    SQLInjectionRiskLevel,
    sql_injection_guard,
)
from app.shared.security.xss_protection import XSSContext, XSSRiskLevel, xss_protection
from app.shared.utils.audit_logger import audit_logger

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全防护中间件"""

    def __init__(
        self,
        app: Any,
        enable_sql_injection_protection: bool = True,
        enable_xss_protection: bool = True,
        enable_csrf_protection: bool = True,
        enable_rate_limiting: bool = True,
        enable_security_headers: bool = True,
        allowed_origins: list[str] | None = None,
        excluded_paths: list[str] | None = None,
    ) -> None:
        """初始化安全中间件

        Args:
            app: FastAPI应用实例
            enable_sql_injection_protection: 启用SQL注入防护
            enable_xss_protection: 启用XSS防护
            enable_csrf_protection: 启用CSRF防护
            enable_rate_limiting: 启用API限流
            enable_security_headers: 启用安全响应头
            allowed_origins: 允许的来源列表
            excluded_paths: 排除的路径列表
        """
        super().__init__(app)
        self.enable_sql_injection_protection = enable_sql_injection_protection
        self.enable_xss_protection = enable_xss_protection
        self.enable_csrf_protection = enable_csrf_protection
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_security_headers = enable_security_headers
        self.allowed_origins = allowed_origins or ["http://localhost:3000"]
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        ]

        # 需要CSRF保护的HTTP方法
        self.csrf_protected_methods = {"POST", "PUT", "DELETE", "PATCH"}

        # 限流规则映射
        self.rate_limit_rules = {
            "/api/v1/auth": "api_auth",
            "/api/v1/upload": "api_upload",
            "/api/v1/ai": "api_ai",
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """处理请求"""
        start_time = time.time()

        try:
            # 检查是否为排除路径
            if self._is_excluded_path(request.url.path):
                response = await call_next(request)
                return self._add_security_headers(response)

            # 1. API限流检查
            if self.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limit(request)
                if rate_limit_result.result != RateLimitResult.ALLOWED:
                    return self._create_rate_limit_response(rate_limit_result)

            # 2. SQL注入防护
            if self.enable_sql_injection_protection:
                sql_injection_result = await self._check_sql_injection(request)
                if sql_injection_result and sql_injection_result.is_malicious:
                    await self._log_security_event(
                        request, "sql_injection", sql_injection_result.details
                    )
                    if sql_injection_result.risk_level in [
                        SQLInjectionRiskLevel.HIGH,
                        SQLInjectionRiskLevel.CRITICAL,
                    ]:
                        raise HTTPException(status_code=400, detail="Invalid request parameters")

            # 3. XSS防护
            if self.enable_xss_protection:
                xss_result = await self._check_xss(request)
                if xss_result and xss_result.is_malicious:
                    await self._log_security_event(request, "xss_attack", xss_result.details)
                    if xss_result.risk_level in [
                        XSSRiskLevel.HIGH,
                        XSSRiskLevel.CRITICAL,
                    ]:
                        raise HTTPException(status_code=400, detail="Invalid request content")

            # 4. CSRF防护
            if self.enable_csrf_protection and request.method in self.csrf_protected_methods:
                csrf_result = await self._check_csrf(request)
                if csrf_result and not csrf_result.is_valid:
                    await self._log_security_event(request, "csrf_attack", csrf_result.details)
                    if csrf_result.result in [
                        CSRFValidationResult.INVALID_TOKEN,
                        CSRFValidationResult.ORIGIN_MISMATCH,
                    ]:
                        raise HTTPException(status_code=403, detail="CSRF token validation failed")

            # 处理请求
            response = await call_next(request)

            # 添加安全响应头
            if self.enable_security_headers:
                response = self._add_security_headers(response)

            # 记录请求处理时间
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            return response  # type: ignore[no-any-return]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            await self._log_security_event(request, "middleware_error", {"error": str(e)})
            raise HTTPException(status_code=500, detail="Internal server error") from e

    def _is_excluded_path(self, path: str) -> bool:
        """检查是否为排除路径"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    async def _check_rate_limit(self, request: Request) -> Any:
        """检查API限流"""
        try:
            # 获取客户端ID
            client_ip = self._get_client_ip(request)
            user_id = getattr(request.state, "user_id", None)
            client_id = rate_limiter.get_client_id(client_ip, user_id)

            # 确定限流规则
            rule_name = self._get_rate_limit_rule(request.url.path)

            # 检查限流
            return await rate_limiter.check_rate_limit(client_id, rule_name, request.url.path)

        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return None

    def _get_rate_limit_rule(self, path: str) -> str:
        """获取限流规则"""
        for pattern, rule_name in self.rate_limit_rules.items():
            if path.startswith(pattern):
                return rule_name
        return "api_general"

    async def _check_sql_injection(self, request: Request) -> Any:
        """检查SQL注入"""
        try:
            # 检查查询参数
            for _key, value in request.query_params.items():
                if isinstance(value, str):
                    detection = sql_injection_guard.detect_sql_injection(value)
                    if detection.is_malicious:
                        return detection

            # 检查表单数据
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    if "application/json" in request.headers.get("content-type", ""):
                        body = await request.body()
                        if body:
                            body_str = body.decode("utf-8")
                            detection = sql_injection_guard.detect_sql_injection(body_str)
                            if detection.is_malicious:
                                return detection
                except Exception:
                    pass  # 忽略解析错误

            return None

        except Exception as e:
            logger.error(f"SQL injection check error: {str(e)}")
            return None

    async def _check_xss(self, request: Request) -> Any:
        """检查XSS攻击"""
        try:
            # 检查查询参数
            for _key, value in request.query_params.items():
                if isinstance(value, str):
                    detection = xss_protection.detect_xss(value, XSSContext.HTML_CONTENT)
                    if detection.is_malicious:
                        return detection

            # 检查请求体
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    if "application/json" in request.headers.get("content-type", ""):
                        body = await request.body()
                        if body:
                            body_str = body.decode("utf-8")
                            detection = xss_protection.detect_xss(body_str, XSSContext.JSON)
                            if detection.is_malicious:
                                return detection
                except Exception:
                    pass  # 忽略解析错误

            return None

        except Exception as e:
            logger.error(f"XSS check error: {str(e)}")
            return None

    async def _check_csrf(self, request: Request) -> Any:
        """检查CSRF攻击"""
        try:
            csrf_protection = get_csrf_protection()

            # 获取CSRF令牌
            csrf_token = request.headers.get("X-CSRF-Token") or request.cookies.get("csrf_token")

            # 获取用户信息
            user_id = getattr(request.state, "user_id", None)
            session_id = getattr(request.state, "session_id", None)

            # 获取Origin和Referer
            origin = request.headers.get("Origin")
            referer = request.headers.get("Referer")

            # 验证CSRF令牌
            return csrf_protection.validate_token(
                csrf_token or "",
                user_id=user_id,
                session_id=session_id,
                origin=origin,
                referer=referer,
                allowed_origins=self.allowed_origins,
            )

        except Exception as e:
            logger.error(f"CSRF check error: {str(e)}")
            return None

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _create_rate_limit_response(self, rate_limit_result: Any) -> JSONResponse:
        """创建限流响应"""
        headers = rate_limiter.get_rate_limit_headers(rate_limit_result)

        if rate_limit_result.result == RateLimitResult.BLOCKED:
            status_code = 429
            message = "Too many requests - client blocked"
        else:
            status_code = 429
            message = "Too many requests"

        return JSONResponse(
            status_code=status_code,
            content={"error": message, "retry_after": rate_limit_result.retry_after},
            headers=headers,
        )

    def _add_security_headers(self, response: Response) -> Response:
        """添加安全响应头"""
        if self.enable_security_headers:
            security_headers = xss_protection.get_security_headers()
            for header, value in security_headers.items():
                response.headers[header] = value

        return response

    async def _log_security_event(
        self, request: Request, event_type: str, details: dict[str, Any]
    ) -> None:
        """记录安全事件"""
        try:
            event_data = {
                "event_type": event_type,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", ""),
                "path": request.url.path,
                "method": request.method,
                "timestamp": time.time(),
                "details": details,
            }

            await audit_logger.log_security_event(event_data)

        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")


def create_security_middleware(
    enable_sql_injection_protection: bool = True,
    enable_xss_protection: bool = True,
    enable_csrf_protection: bool = True,
    enable_rate_limiting: bool = True,
    enable_security_headers: bool = True,
    allowed_origins: list[str] | None = None,
    excluded_paths: list[str] | None = None,
) -> type:
    """创建安全中间件类"""

    class ConfiguredSecurityMiddleware(SecurityMiddleware):
        def __init__(self, app: Any) -> None:
            super().__init__(
                app,
                enable_sql_injection_protection=enable_sql_injection_protection,
                enable_xss_protection=enable_xss_protection,
                enable_csrf_protection=enable_csrf_protection,
                enable_rate_limiting=enable_rate_limiting,
                enable_security_headers=enable_security_headers,
                allowed_origins=allowed_origins,
                excluded_paths=excluded_paths,
            )

    return ConfiguredSecurityMiddleware
