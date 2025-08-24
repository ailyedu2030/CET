"""核心异常类定义."""


class BusinessLogicError(Exception):
    """业务逻辑错误异常."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """初始化业务逻辑错误.

        Args:
            message: 错误消息
            error_code: 错误代码
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """返回错误消息."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ValidationError(BusinessLogicError):
    """数据验证错误异常."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """初始化验证错误.

        Args:
            message: 错误消息
            field: 验证失败的字段名
        """
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field


class AuthenticationError(BusinessLogicError):
    """认证错误异常."""

    def __init__(self, message: str = "认证失败") -> None:
        """初始化认证错误."""
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(BusinessLogicError):
    """授权错误异常."""

    def __init__(self, message: str = "权限不足") -> None:
        """初始化授权错误."""
        super().__init__(message, "PERMISSION_ERROR")


class ResourceNotFoundError(BusinessLogicError):
    """资源未找到错误异常."""

    def __init__(self, message: str = "资源未找到", resource_type: str | None = None) -> None:
        """初始化资源未找到错误.

        Args:
            message: 错误消息
            resource_type: 资源类型
        """
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.resource_type = resource_type


class ConfigurationError(BusinessLogicError):
    """配置错误异常."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        """初始化配置错误.

        Args:
            message: 错误消息
            config_key: 配置键名
        """
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key


class ExternalServiceError(BusinessLogicError):
    """外部服务错误异常."""

    def __init__(self, message: str, service_name: str | None = None) -> None:
        """初始化外部服务错误.

        Args:
            message: 错误消息
            service_name: 服务名称
        """
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service_name = service_name
