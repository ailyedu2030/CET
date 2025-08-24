"""应用核心配置模块."""

import os
from typing import ClassVar


class Settings:
    """应用配置类."""

    # 应用基本信息
    PROJECT_NAME: str = "英语四级学习系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # JWT认证配置
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

    # 多因素认证配置
    MFA_REQUIRED: bool = os.getenv("MFA_REQUIRED", "false").lower() == "true"
    MFA_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("MFA_TOKEN_EXPIRE_MINUTES", "5"))

    # 安全配置
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "6"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

    # 服务器配置
    SERVER_NAME: str = os.getenv("SERVER_NAME", "localhost")
    SERVER_HOST: str = "http://localhost"

    # AI服务配置 - DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BACKUP_KEYS: str = os.getenv("DEEPSEEK_BACKUP_KEYS", "")
    DEEPSEEK_API_BASE_URL: str = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_DEFAULT_MODEL: str = os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat")
    DEEPSEEK_TIMEOUT: int = int(os.getenv("DEEPSEEK_TIMEOUT", "60"))
    DEEPSEEK_MAX_TOKENS: int = int(os.getenv("DEEPSEEK_MAX_TOKENS", "4096"))

    # CORS配置
    BACKEND_CORS_ORIGINS: ClassVar[list[str]] = [
        "http://localhost:3000",  # React开发服务器
        "http://localhost:8000",  # FastAPI服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "cet4_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "cet4_pass")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "cet4_learning")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def database_url(self) -> str:
        """数据库连接字符串."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # 添加DATABASE_URL属性以兼容现有代码
    @property
    def DATABASE_URL(self) -> str:
        """数据库连接字符串（兼容性属性）."""
        return self.database_url

    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    @property
    def redis_url(self) -> str:
        """Redis连接字符串."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # 添加REDIS_URL属性以兼容Celery
    @property
    def REDIS_URL(self) -> str:
        """Redis连接字符串（Celery兼容性属性）."""
        return self.redis_url

    # AI服务配置
    DEEPSEEK_API_KEYS: ClassVar[list[str]] = []
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    AI_REQUEST_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 3

    # AI成本控制配置
    AI_DAILY_COST_LIMIT: float = float(os.getenv("AI_DAILY_COST_LIMIT", "100.0"))
    AI_HOURLY_COST_LIMIT: float = float(os.getenv("AI_HOURLY_COST_LIMIT", "10.0"))

    # Celery配置
    CELERY_EAGER_MODE: bool = os.getenv("CELERY_EAGER_MODE", "false").lower() == "true"

    # 邮件配置
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@cet4learning.com")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

    # 数据库详细配置（从DATABASE_URL解析获取）
    @property
    def DATABASE_HOST(self) -> str:
        """从DATABASE_URL获取数据库主机."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.hostname or "localhost"

    @property
    def DATABASE_PORT(self) -> int:
        """从DATABASE_URL获取数据库端口."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.port or 5432

    @property
    def DATABASE_USER(self) -> str:
        """从DATABASE_URL获取数据库用户名."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.username or ""

    @property
    def DATABASE_PASSWORD(self) -> str:
        """从DATABASE_URL获取数据库密码."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.password or ""

    @property
    def DATABASE_NAME(self) -> str:
        """从DATABASE_URL获取数据库名."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.path.lstrip("/") if parsed.path else ""

    # 备份存储配置
    BACKUP_STORAGE_PATH: str = os.getenv("BACKUP_STORAGE_PATH", "/var/backups/cet")
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    BACKUP_MAX_FILES: int = int(os.getenv("BACKUP_MAX_FILES", "50"))
    BACKUP_COMPRESSION: bool = os.getenv("BACKUP_COMPRESSION", "true").lower() == "true"
    BACKUP_ENCRYPTION: bool = os.getenv("BACKUP_ENCRYPTION", "true").lower() == "true"

    # 环境配置
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"


# 全局配置实例
settings = Settings()
