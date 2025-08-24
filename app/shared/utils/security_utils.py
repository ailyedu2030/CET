"""安全工具类

提供密码哈希、加密解密、安全随机数生成、输入验证等安全相关的工具函数。
"""

import base64
import hashlib
import hmac
import logging
import re
import secrets
import string

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class PasswordValidator:
    """密码验证器"""

    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?",
    ) -> None:
        """初始化密码验证器

        Args:
            min_length: 最小长度
            max_length: 最大长度
            require_uppercase: 需要大写字母
            require_lowercase: 需要小写字母
            require_digits: 需要数字
            require_special: 需要特殊字符
            special_chars: 允许的特殊字符
        """
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.special_chars = special_chars

    def validate(self, password: str) -> tuple[bool, list[str]]:
        """验证密码强度

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        if not password:
            errors.append("密码不能为空")
            return False, errors

        # 长度检查
        if len(password) < self.min_length:
            errors.append(f"密码长度不能少于{self.min_length}位")

        if len(password) > self.max_length:
            errors.append(f"密码长度不能超过{self.max_length}位")

        # 字符类型检查
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")

        if self.require_digits and not re.search(r"\d", password):
            errors.append("密码必须包含数字")

        if self.require_special and not re.search(f"[{re.escape(self.special_chars)}]", password):
            errors.append(f"密码必须包含特殊字符: {self.special_chars}")

        # 常见弱密码检查
        weak_patterns = [
            r"(.)\1{2,}",  # 连续相同字符
            r"(012|123|234|345|456|567|678|789|890)",  # 连续数字
            r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",  # 连续字母
        ]

        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append("密码不能包含连续的字符序列")
                break

        return len(errors) == 0, errors

    def generate_strong_password(self, length: int = 12) -> str:
        """生成强密码"""
        if length < self.min_length:
            length = self.min_length

        # 确保包含所有必需的字符类型
        chars = ""
        password_chars = []

        if self.require_uppercase:
            chars += string.ascii_uppercase
            password_chars.append(secrets.choice(string.ascii_uppercase))

        if self.require_lowercase:
            chars += string.ascii_lowercase
            password_chars.append(secrets.choice(string.ascii_lowercase))

        if self.require_digits:
            chars += string.digits
            password_chars.append(secrets.choice(string.digits))

        if self.require_special:
            chars += self.special_chars
            password_chars.append(secrets.choice(self.special_chars))

        # 填充剩余长度
        for _ in range(length - len(password_chars)):
            password_chars.append(secrets.choice(chars))

        # 随机打乱
        secrets.SystemRandom().shuffle(password_chars)

        return "".join(password_chars)


class PasswordHasher:
    """密码哈希器"""

    def __init__(self, rounds: int = 12) -> None:
        """初始化密码哈希器

        Args:
            rounds: bcrypt轮数
        """
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")  # type: ignore[no-any-return]

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False


class DataEncryption:
    """数据加密器"""

    def __init__(self, key: bytes | None = None) -> None:
        """初始化数据加密器

        Args:
            key: 加密密钥，如果为None则生成新密钥
        """
        if key is None:
            key = Fernet.generate_key()
        self.fernet = Fernet(key)
        self.key = key

    @classmethod
    def from_password(cls, password: str, salt: bytes | None = None) -> "DataEncryption":
        """从密码生成加密器"""
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(key)

    def encrypt(self, data: str | bytes) -> bytes:
        """加密数据"""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return self.fernet.encrypt(data)  # type: ignore[no-any-return]

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """解密数据"""
        return self.fernet.decrypt(encrypted_data)  # type: ignore[no-any-return]

    def encrypt_string(self, text: str) -> str:
        """加密字符串并返回base64编码"""
        encrypted = self.encrypt(text)
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt_string(self, encrypted_text: str) -> str:
        """解密base64编码的字符串"""
        encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode("utf-8"))
        decrypted = self.decrypt(encrypted_data)
        return decrypted.decode("utf-8")


class TokenGenerator:
    """令牌生成器"""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_numeric_token(length: int = 6) -> str:
        """生成数字令牌"""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    @staticmethod
    def generate_api_key(prefix: str = "cet4", length: int = 32) -> str:
        """生成API密钥"""
        token = secrets.token_urlsafe(length)
        return f"{prefix}_{token}"

    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID"""
        return secrets.token_urlsafe(32)


class InputValidator:
    """输入验证器"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        pattern = r"^1[3-9]\d{9}$"
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """验证用户名格式"""
        if not username:
            return False, "用户名不能为空"

        if len(username) < 3:
            return False, "用户名长度不能少于3位"

        if len(username) > 20:
            return False, "用户名长度不能超过20位"

        if not re.match(r"^[a-zA-Z0-9_\u4e00-\u9fa5]+$", username):
            return False, "用户名只能包含字母、数字、下划线和中文"

        return True, ""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名"""
        # 移除危险字符
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)

        # 移除控制字符
        filename = "".join(char for char in filename if ord(char) >= 32)

        # 限制长度
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            max_name_length = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_length] + ("." + ext if ext else "")

        return filename.strip()

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
        """验证文件扩展名"""
        if not filename or "." not in filename:
            return False

        ext = filename.rsplit(".", 1)[1].lower()
        return ext in [e.lower() for e in allowed_extensions]


class SecurityHeaders:
    """安全响应头生成器"""

    @staticmethod
    def get_default_headers() -> dict[str, str]:
        """获取默认安全头"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    @staticmethod
    def get_csp_header(strict: bool = True) -> str:
        """获取内容安全策略头"""
        if strict:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "media-src 'self'; "
                "object-src 'none'; "
                "child-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "object-src 'none'; "
                "frame-ancestors 'none'"
            )


class SecurityUtils:
    """安全工具类"""

    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """常量时间字符串比较"""
        return hmac.compare_digest(a, b)

    @staticmethod
    def generate_salt(length: int = 16) -> bytes:
        """生成盐值"""
        return secrets.token_bytes(length)

    @staticmethod
    def hash_with_salt(data: str, salt: bytes) -> str:
        """使用盐值哈希数据"""
        return hashlib.pbkdf2_hmac("sha256", data.encode(), salt, 100000).hex()

    @staticmethod
    def generate_hmac(data: str, key: str) -> str:
        """生成HMAC"""
        return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def verify_hmac(data: str, key: str, signature: str) -> bool:
        """验证HMAC"""
        expected = SecurityUtils.generate_hmac(data, key)
        return hmac.compare_digest(expected, signature)


# 全局实例
password_validator = PasswordValidator()
password_hasher = PasswordHasher()
token_generator = TokenGenerator()
input_validator = InputValidator()
security_headers = SecurityHeaders()
security_utils = SecurityUtils()
