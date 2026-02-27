"""自定义异常类."""


class BusinessLogicError(Exception):
    """业务逻辑错误."""

    def __init__(self: "BusinessLogicError", message: str, error_code: str = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(Exception):
    """数据验证错误."""

    def __init__(self: "ValidationError", message: str, field: str = None) -> None:
        self.message = message
        self.field = field
        super().__init__(self.message)


class AuthenticationError(Exception):
    """认证错误."""

    def __init__(self: "AuthenticationError", message: str = "Authentication failed") -> None:
        self.message = message
        super().__init__(self.message)


class AuthorizationError(Exception):
    """授权错误."""

    def __init__(self: "AuthorizationError", message: str = "Access denied") -> None:
        self.message = message
        super().__init__(self.message)


class PermissionDeniedError(Exception):
    """权限拒绝错误."""

    def __init__(self: "PermissionDeniedError", message: str = "Permission denied") -> None:
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(Exception):
    """资源未找到错误."""

    def __init__(self: "ResourceNotFoundError", message: str, resource_type: str = None) -> None:
        self.message = message
        self.resource_type = resource_type
        super().__init__(self.message)


class ExternalServiceError(Exception):
    """外部服务错误."""

    def __init__(self: "ExternalServiceError", message: str, service_name: str = None) -> None:
        self.message = message
        self.service_name = service_name
        super().__init__(self.message)


class DatabaseError(Exception):
    """数据库错误."""

    def __init__(self: "DatabaseError", message: str, operation: str = None) -> None:
        self.message = message
        self.operation = operation
        super().__init__(self.message)


class ConfigurationError(Exception):
    """配置错误."""

    def __init__(self: "ConfigurationError", message: str, config_key: str = None) -> None:
        self.message = message
        self.config_key = config_key
        super().__init__(self.message)
