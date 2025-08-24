"""SQL注入防护模块

提供全面的SQL注入攻击防护，包括输入验证、参数化查询检查、
危险SQL模式检测等功能。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from typing import Any

logger = logging.getLogger(__name__)


class SQLInjectionRiskLevel(Enum):
    """SQL注入风险级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SQLInjectionDetection:
    """SQL注入检测结果"""

    is_malicious: bool
    risk_level: SQLInjectionRiskLevel
    detected_patterns: list[str]
    sanitized_input: str
    confidence: float
    details: dict[str, Any]


class SQLInjectionGuard:
    """SQL注入防护器"""

    def __init__(self) -> None:
        """初始化SQL注入防护器"""
        self._setup_detection_patterns()
        self._setup_whitelist_patterns()

    def _setup_detection_patterns(self) -> None:
        """设置SQL注入检测模式"""
        # 高风险SQL关键词模式
        self.critical_patterns: list[Pattern[str]] = [
            re.compile(r"\b(union\s+select|union\s+all\s+select)\b", re.IGNORECASE),
            re.compile(r"\b(drop\s+table|drop\s+database|truncate\s+table)\b", re.IGNORECASE),
            re.compile(r"\b(delete\s+from|update\s+.*\s+set)\b", re.IGNORECASE),
            re.compile(r"\b(exec\s*\(|execute\s*\(|sp_executesql)\b", re.IGNORECASE),
            re.compile(r"\b(xp_cmdshell|sp_oacreate|sp_oamethod)\b", re.IGNORECASE),
        ]

        # 中等风险SQL模式
        self.high_patterns: list[Pattern[str]] = [
            re.compile(r"(\'\s*or\s*\'|\"\s*or\s*\")", re.IGNORECASE),
            re.compile(r"(\'\s*and\s*\'|\"\s*and\s*\")", re.IGNORECASE),
            re.compile(r"\b(select\s+.*\s+from|insert\s+into|create\s+table)\b", re.IGNORECASE),
            re.compile(r"(\-\-|\#|\/\*|\*\/)", re.IGNORECASE),
            re.compile(r"\b(information_schema|sys\.tables|sys\.columns)\b", re.IGNORECASE),
        ]

        # 低风险可疑模式
        self.medium_patterns: list[Pattern[str]] = [
            re.compile(r"(\'\s*=\s*\'|\"\s*=\s*\")", re.IGNORECASE),
            re.compile(r"\b(where\s+1\s*=\s*1|where\s+true)\b", re.IGNORECASE),
            re.compile(r"(\%27|\%22|\%2D\%2D|\%23)", re.IGNORECASE),  # URL编码
            re.compile(r"(\+|\%20)(union|select|from|where)", re.IGNORECASE),
        ]

        # 低风险模式
        self.low_patterns: list[Pattern[str]] = [
            re.compile(r"[\'\"]\s*[;,]\s*[\'\"]*", re.IGNORECASE),
            re.compile(r"\b(null|is\s+null|is\s+not\s+null)\b", re.IGNORECASE),
            re.compile(r"(\<|\>|\=|\!\=)", re.IGNORECASE),
        ]

    def _setup_whitelist_patterns(self) -> None:
        """设置白名单模式"""
        # 安全的输入模式
        self.safe_patterns: list[Pattern[str]] = [
            re.compile(r"^[a-zA-Z0-9_\-\s\.@]+$"),  # 基本字符
            re.compile(r"^[\u4e00-\u9fa5a-zA-Z0-9_\-\s\.@]+$"),  # 包含中文
            re.compile(r"^\d{4}-\d{2}-\d{2}$"),  # 日期格式
            re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),  # 邮箱
        ]

    def detect_sql_injection(self, input_value: str) -> SQLInjectionDetection:
        """检测SQL注入攻击"""
        if not input_value or not isinstance(input_value, str):
            return SQLInjectionDetection(
                is_malicious=False,
                risk_level=SQLInjectionRiskLevel.LOW,
                detected_patterns=[],
                sanitized_input=str(input_value) if input_value else "",
                confidence=0.0,
                details={"reason": "empty_or_invalid_input"},
            )

        # 检查是否为安全输入
        if self._is_safe_input(input_value):
            return SQLInjectionDetection(
                is_malicious=False,
                risk_level=SQLInjectionRiskLevel.LOW,
                detected_patterns=[],
                sanitized_input=input_value,
                confidence=0.0,
                details={"reason": "safe_pattern_match"},
            )

        detected_patterns = []
        risk_level = SQLInjectionRiskLevel.LOW
        confidence = 0.0

        # 检测关键风险模式
        for pattern in self.critical_patterns:
            if pattern.search(input_value):
                detected_patterns.append(f"critical:{pattern.pattern}")
                risk_level = SQLInjectionRiskLevel.CRITICAL
                confidence = max(confidence, 0.95)

        # 检测高风险模式
        for pattern in self.high_patterns:
            if pattern.search(input_value):
                detected_patterns.append(f"high:{pattern.pattern}")
                if risk_level != SQLInjectionRiskLevel.CRITICAL:
                    risk_level = SQLInjectionRiskLevel.HIGH
                confidence = max(confidence, 0.85)

        # 检测中等风险模式
        for pattern in self.medium_patterns:
            if pattern.search(input_value):
                detected_patterns.append(f"medium:{pattern.pattern}")
                if risk_level not in [
                    SQLInjectionRiskLevel.CRITICAL,
                    SQLInjectionRiskLevel.HIGH,
                ]:
                    risk_level = SQLInjectionRiskLevel.MEDIUM
                confidence = max(confidence, 0.65)

        # 检测低风险模式
        for pattern in self.low_patterns:
            if pattern.search(input_value):
                detected_patterns.append(f"low:{pattern.pattern}")
                if risk_level == SQLInjectionRiskLevel.LOW:
                    confidence = max(confidence, 0.35)

        is_malicious = len(detected_patterns) > 0 and confidence > 0.5
        sanitized_input = self._sanitize_input(input_value) if is_malicious else input_value

        return SQLInjectionDetection(
            is_malicious=is_malicious,
            risk_level=risk_level,
            detected_patterns=detected_patterns,
            sanitized_input=sanitized_input,
            confidence=confidence,
            details={
                "input_length": len(input_value),
                "pattern_count": len(detected_patterns),
                "analysis_method": "pattern_matching",
            },
        )

    def _is_safe_input(self, input_value: str) -> bool:
        """检查是否为安全输入"""
        for pattern in self.safe_patterns:
            if pattern.match(input_value):
                return True
        return False

    def _sanitize_input(self, input_value: str) -> str:
        """清理输入内容"""
        # 移除危险字符
        sanitized = input_value

        # 移除SQL注释
        sanitized = re.sub(r"(\-\-|\#|\/\*.*?\*\/)", "", sanitized, flags=re.DOTALL)

        # 转义单引号和双引号
        sanitized = sanitized.replace("'", "''").replace('"', '""')

        # 移除危险的SQL关键词
        dangerous_keywords = [
            "union",
            "select",
            "drop",
            "delete",
            "update",
            "insert",
            "exec",
            "execute",
            "xp_cmdshell",
            "sp_executesql",
        ]

        for keyword in dangerous_keywords:
            sanitized = re.sub(rf"\b{keyword}\b", "", sanitized, flags=re.IGNORECASE)

        # 移除多余空格
        sanitized = " ".join(sanitized.split())

        return sanitized.strip()

    def validate_query_parameters(self, query: str, parameters: dict[str, Any]) -> bool:
        """验证查询参数是否安全"""
        try:
            # 检查查询是否使用参数化
            if not self._is_parameterized_query(query):
                logger.warning("Non-parameterized query detected")
                return False

            # 检查每个参数
            for key, value in parameters.items():
                if isinstance(value, str):
                    detection = self.detect_sql_injection(value)
                    if detection.is_malicious:
                        logger.warning(f"Malicious parameter detected: {key}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating query parameters: {str(e)}")
            return False

    def _is_parameterized_query(self, query: str) -> bool:
        """检查查询是否为参数化查询"""
        # 检查是否包含参数占位符
        parameter_patterns = [
            r"\$\d+",  # PostgreSQL: $1, $2
            r"\?",  # MySQL/SQLite: ?
            r":\w+",  # Named parameters: :name
            r"%\(\w+\)s",  # Python format: %(name)s
        ]

        for pattern in parameter_patterns:
            if re.search(pattern, query):
                return True

        # 检查是否包含直接的字符串拼接（危险）
        dangerous_patterns = [
            r"[\'\"]\s*\+\s*\w+",  # 字符串拼接
            r"\w+\s*\+\s*[\'\"]*",  # 变量拼接
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query):
                return False

        return True

    def get_security_recommendations(self, detection: SQLInjectionDetection) -> list[str]:
        """获取安全建议"""
        recommendations = []

        if detection.is_malicious:
            recommendations.extend(
                [
                    "使用参数化查询或预编译语句",
                    "对所有用户输入进行严格验证",
                    "实施最小权限原则",
                    "启用数据库查询日志监控",
                ]
            )

            if detection.risk_level == SQLInjectionRiskLevel.CRITICAL:
                recommendations.extend(
                    [
                        "立即阻止该请求",
                        "记录安全事件并告警",
                        "考虑临时封禁来源IP",
                        "进行安全审计",
                    ]
                )

        return recommendations


# 全局SQL注入防护器实例
sql_injection_guard = SQLInjectionGuard()
