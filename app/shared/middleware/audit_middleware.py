"""审计中间件

记录所有API请求、响应、安全事件等信息，用于安全审计和合规性检查。
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.utils.audit_logger import audit_logger

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """审计中间件"""

    def __init__(
        self,
        app: Any,
        enable_request_logging: bool = True,
        enable_response_logging: bool = True,
        enable_error_logging: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        excluded_paths: list[str] | None = None,
        sensitive_headers: list[str] | None = None,
        max_body_size: int = 10240,  # 10KB
    ) -> None:
        """初始化审计中间件

        Args:
            app: FastAPI应用实例
            enable_request_logging: 启用请求日志
            enable_response_logging: 启用响应日志
            enable_error_logging: 启用错误日志
            log_request_body: 记录请求体
            log_response_body: 记录响应体
            excluded_paths: 排除的路径列表
            sensitive_headers: 敏感头部列表
            max_body_size: 最大记录的请求/响应体大小
        """
        super().__init__(app)
        self.enable_request_logging = enable_request_logging
        self.enable_response_logging = enable_response_logging
        self.enable_error_logging = enable_error_logging
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.excluded_paths = excluded_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
        ]
        self.sensitive_headers = sensitive_headers or [
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
        ]
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """处理请求"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        try:
            # 检查是否为排除路径
            if self._is_excluded_path(request.url.path):
                return await call_next(request)  # type: ignore[no-any-return]

            # 记录请求信息
            if self.enable_request_logging:
                await self._log_request(request, request_id, start_time)

            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            if self.enable_response_logging:
                await self._log_response(request, response, request_id, process_time)

            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response  # type: ignore[no-any-return]

        except Exception as e:
            # 记录错误信息
            if self.enable_error_logging:
                process_time = time.time() - start_time
                await self._log_error(request, e, request_id, process_time)

            raise

    def _is_excluded_path(self, path: str) -> bool:
        """检查是否为排除路径"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    async def _log_request(self, request: Request, request_id: str, start_time: float) -> None:
        """记录请求信息"""
        try:
            # 获取客户端信息
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "")

            # 获取用户信息
            user_id = getattr(request.state, "user_id", None)
            user_type = getattr(request.state, "user_type", None)

            # 过滤敏感头部
            headers = self._filter_sensitive_headers(dict(request.headers))

            # 获取请求体
            request_body = None
            if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body and len(body) <= self.max_body_size:
                        request_body = body.decode("utf-8")
                except Exception:
                    request_body = "<failed_to_decode>"

            # 构建审计日志
            audit_data = {
                "event_type": "api_request",
                "request_id": request_id,
                "timestamp": start_time,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id,
                "user_type": user_type,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": headers,
                "request_body": request_body,
                "content_type": request.headers.get("Content-Type"),
                "content_length": request.headers.get("Content-Length"),
            }

            await audit_logger.log_api_request(audit_data)

        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")

    async def _log_response(
        self, request: Request, response: Response, request_id: str, process_time: float
    ) -> None:
        """记录响应信息"""
        try:
            # 获取响应体
            response_body = None
            if self.log_response_body and hasattr(response, "body"):
                try:
                    if response.body and len(response.body) <= self.max_body_size:
                        # 处理bytes和memoryview类型
                        if isinstance(response.body, memoryview):
                            response_body = bytes(response.body).decode("utf-8")
                        else:
                            response_body = response.body.decode("utf-8")
                except Exception:
                    response_body = "<failed_to_decode>"

            # 过滤敏感头部
            headers = self._filter_sensitive_headers(dict(response.headers))

            # 构建审计日志
            audit_data = {
                "event_type": "api_response",
                "request_id": request_id,
                "timestamp": time.time(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "headers": headers,
                "response_body": response_body,
                "process_time": process_time,
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
            }

            await audit_logger.log_api_response(audit_data)

        except Exception as e:
            logger.error(f"Failed to log response: {str(e)}")

    async def _log_error(
        self, request: Request, error: Exception, request_id: str, process_time: float
    ) -> None:
        """记录错误信息"""
        try:
            # 获取客户端信息
            client_ip = self._get_client_ip(request)
            user_id = getattr(request.state, "user_id", None)

            # 构建审计日志
            audit_data = {
                "event_type": "api_error",
                "request_id": request_id,
                "timestamp": time.time(),
                "client_ip": client_ip,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "process_time": process_time,
            }

            await audit_logger.log_api_error(audit_data)

        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")

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

    def _filter_sensitive_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """过滤敏感头部信息"""
        filtered_headers = {}

        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                filtered_headers[key] = "<redacted>"
            else:
                filtered_headers[key] = value

        return filtered_headers


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """安全审计中间件"""

    def __init__(
        self,
        app: Any,
        enable_authentication_logging: bool = True,
        enable_authorization_logging: bool = True,
        enable_data_access_logging: bool = True,
        enable_admin_action_logging: bool = True,
    ) -> None:
        """初始化安全审计中间件

        Args:
            app: FastAPI应用实例
            enable_authentication_logging: 启用认证日志
            enable_authorization_logging: 启用授权日志
            enable_data_access_logging: 启用数据访问日志
            enable_admin_action_logging: 启用管理员操作日志
        """
        super().__init__(app)
        self.enable_authentication_logging = enable_authentication_logging
        self.enable_authorization_logging = enable_authorization_logging
        self.enable_data_access_logging = enable_data_access_logging
        self.enable_admin_action_logging = enable_admin_action_logging

        # 需要记录的管理员操作路径
        self.admin_paths = [
            "/api/v1/admin",
            "/api/v1/users/approve",
            "/api/v1/users/reject",
            "/api/v1/system",
        ]

        # 需要记录的数据访问路径
        self.data_access_paths = [
            "/api/v1/users",
            "/api/v1/courses",
            "/api/v1/training",
            "/api/v1/analytics",
        ]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """处理请求"""
        try:
            # 记录认证事件
            if self.enable_authentication_logging and self._is_auth_request(request):
                await self._log_authentication_event(request)

            # 记录授权事件
            if self.enable_authorization_logging and self._requires_authorization(request):
                await self._log_authorization_event(request)

            # 记录管理员操作
            if self.enable_admin_action_logging and self._is_admin_action(request):
                await self._log_admin_action(request)

            # 记录数据访问
            if self.enable_data_access_logging and self._is_data_access(request):
                await self._log_data_access(request)

            response = await call_next(request)

            return response  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Security audit middleware error: {str(e)}")
            raise

    def _is_auth_request(self, request: Request) -> bool:
        """检查是否为认证请求"""
        auth_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/refresh",
        ]
        return any(request.url.path.startswith(path) for path in auth_paths)

    def _requires_authorization(self, request: Request) -> bool:
        """检查是否需要授权"""
        return request.url.path.startswith("/api/v1/") and not request.url.path.startswith(
            "/api/v1/auth/"
        )

    def _is_admin_action(self, request: Request) -> bool:
        """检查是否为管理员操作"""
        return any(request.url.path.startswith(path) for path in self.admin_paths)

    def _is_data_access(self, request: Request) -> bool:
        """检查是否为数据访问"""
        return any(request.url.path.startswith(path) for path in self.data_access_paths)

    async def _log_authentication_event(self, request: Request) -> None:
        """记录认证事件"""
        try:
            client_ip = self._get_client_ip(request)

            audit_data = {
                "event_type": "authentication",
                "timestamp": time.time(),
                "client_ip": client_ip,
                "path": request.url.path,
                "method": request.method,
                "user_agent": request.headers.get("User-Agent", ""),
            }

            await audit_logger.log_authentication_event(audit_data)

        except Exception as e:
            logger.error(f"Failed to log authentication event: {str(e)}")

    async def _log_authorization_event(self, request: Request) -> None:
        """记录授权事件"""
        try:
            user_id = getattr(request.state, "user_id", None)
            user_type = getattr(request.state, "user_type", None)

            if user_id:  # 只记录已认证用户的授权事件
                audit_data = {
                    "event_type": "authorization",
                    "timestamp": time.time(),
                    "user_id": user_id,
                    "user_type": user_type,
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": self._get_client_ip(request),
                }

                await audit_logger.log_authorization_event(audit_data)

        except Exception as e:
            logger.error(f"Failed to log authorization event: {str(e)}")

    async def _log_admin_action(self, request: Request) -> None:
        """记录管理员操作"""
        try:
            user_id = getattr(request.state, "user_id", None)
            user_type = getattr(request.state, "user_type", None)

            audit_data = {
                "event_type": "admin_action",
                "timestamp": time.time(),
                "user_id": user_id,
                "user_type": user_type,
                "path": request.url.path,
                "method": request.method,
                "client_ip": self._get_client_ip(request),
                "query_params": dict(request.query_params),
            }

            await audit_logger.log_admin_action(audit_data)

        except Exception as e:
            logger.error(f"Failed to log admin action: {str(e)}")

    async def _log_data_access(self, request: Request) -> None:
        """记录数据访问"""
        try:
            user_id = getattr(request.state, "user_id", None)
            user_type = getattr(request.state, "user_type", None)

            audit_data = {
                "event_type": "data_access",
                "timestamp": time.time(),
                "user_id": user_id,
                "user_type": user_type,
                "path": request.url.path,
                "method": request.method,
                "client_ip": self._get_client_ip(request),
                "access_type": "read" if request.method == "GET" else "write",
            }

            await audit_logger.log_data_access(audit_data)

        except Exception as e:
            logger.error(f"Failed to log data access: {str(e)}")

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"
