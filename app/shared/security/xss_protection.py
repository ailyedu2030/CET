"""XSS攻击防护模块

提供全面的跨站脚本攻击(XSS)防护，包括输入过滤、输出编码、
内容安全策略(CSP)等功能。
"""

import html
import logging
import re
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from typing import Any

logger = logging.getLogger(__name__)


class XSSRiskLevel(Enum):
    """XSS风险级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class XSSContext(Enum):
    """XSS上下文类型"""

    HTML_CONTENT = "html_content"
    HTML_ATTRIBUTE = "html_attribute"
    JAVASCRIPT = "javascript"
    CSS = "css"
    URL = "url"
    JSON = "json"


@dataclass
class XSSDetection:
    """XSS检测结果"""

    is_malicious: bool
    risk_level: XSSRiskLevel
    detected_patterns: list[str]
    sanitized_content: str
    confidence: float
    context: XSSContext
    details: dict[str, Any]


class XSSProtection:
    """XSS攻击防护器"""

    def __init__(self) -> None:
        """初始化XSS防护器"""
        self._setup_detection_patterns()
        self._setup_dangerous_tags()
        self._setup_safe_tags()

    def _setup_detection_patterns(self) -> None:
        """设置XSS检测模式"""
        # 关键风险模式
        self.critical_patterns: list[Pattern[str]] = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript\s*:", re.IGNORECASE),
            re.compile(r'on\w+\s*=\s*["\'].*?["\']', re.IGNORECASE),
            re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<object[^>]*>.*?</object>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<embed[^>]*>", re.IGNORECASE),
        ]

        # 高风险模式
        self.high_patterns: list[Pattern[str]] = [
            re.compile(r"<img[^>]*onerror[^>]*>", re.IGNORECASE),
            re.compile(r"<svg[^>]*onload[^>]*>", re.IGNORECASE),
            re.compile(r'<form[^>]*action\s*=\s*["\']javascript:', re.IGNORECASE),
            re.compile(r'<link[^>]*href\s*=\s*["\']javascript:', re.IGNORECASE),
            re.compile(r"<meta[^>]*http-equiv[^>]*refresh[^>]*>", re.IGNORECASE),
        ]

        # 中等风险模式
        self.medium_patterns: list[Pattern[str]] = [
            re.compile(r"<\s*\w+[^>]*\s+on\w+[^>]*>", re.IGNORECASE),
            re.compile(r"expression\s*\(", re.IGNORECASE),
            re.compile(r'url\s*\(\s*["\']?javascript:', re.IGNORECASE),
            re.compile(r"<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL),
        ]

        # 低风险模式
        self.low_patterns: list[Pattern[str]] = [
            re.compile(r"<\s*\/?\s*\w+[^>]*>", re.IGNORECASE),
            re.compile(r"&\w+;"),
            re.compile(r"%[0-9a-fA-F]{2}"),
        ]

    def _setup_dangerous_tags(self) -> None:
        """设置危险HTML标签"""
        self.dangerous_tags: set[str] = {
            "script",
            "iframe",
            "object",
            "embed",
            "applet",
            "form",
            "input",
            "textarea",
            "button",
            "select",
            "meta",
            "link",
            "base",
            "style",
        }

        self.dangerous_attributes: set[str] = {
            "onload",
            "onerror",
            "onclick",
            "onmouseover",
            "onmouseout",
            "onfocus",
            "onblur",
            "onchange",
            "onsubmit",
            "onreset",
            "onkeydown",
            "onkeyup",
            "onkeypress",
            "onabort",
            "href",
            "src",
            "action",
            "formaction",
            "background",
            "lowsrc",
            "dynsrc",
            "ping",
        }

    def _setup_safe_tags(self) -> None:
        """设置安全HTML标签"""
        self.safe_tags: set[str] = {
            "p",
            "br",
            "strong",
            "em",
            "u",
            "i",
            "b",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "dl",
            "dt",
            "dd",
            "table",
            "tr",
            "td",
            "th",
            "thead",
            "tbody",
            "div",
            "span",
            "blockquote",
            "pre",
            "code",
        }

        self.safe_attributes: set[str] = {
            "class",
            "id",
            "title",
            "alt",
            "width",
            "height",
            "align",
            "valign",
            "border",
            "cellpadding",
            "cellspacing",
        }

    def detect_xss(
        self, content: str, context: XSSContext = XSSContext.HTML_CONTENT
    ) -> XSSDetection:
        """检测XSS攻击"""
        if not content or not isinstance(content, str):
            return XSSDetection(
                is_malicious=False,
                risk_level=XSSRiskLevel.LOW,
                detected_patterns=[],
                sanitized_content=str(content) if content else "",
                confidence=0.0,
                context=context,
                details={"reason": "empty_or_invalid_content"},
            )

        detected_patterns = []
        risk_level = XSSRiskLevel.LOW
        confidence = 0.0

        # 检测关键风险模式
        for pattern in self.critical_patterns:
            if pattern.search(content):
                detected_patterns.append(f"critical:{pattern.pattern}")
                risk_level = XSSRiskLevel.CRITICAL
                confidence = max(confidence, 0.95)

        # 检测高风险模式
        for pattern in self.high_patterns:
            if pattern.search(content):
                detected_patterns.append(f"high:{pattern.pattern}")
                if risk_level != XSSRiskLevel.CRITICAL:
                    risk_level = XSSRiskLevel.HIGH
                confidence = max(confidence, 0.85)

        # 检测中等风险模式
        for pattern in self.medium_patterns:
            if pattern.search(content):
                detected_patterns.append(f"medium:{pattern.pattern}")
                if risk_level not in [XSSRiskLevel.CRITICAL, XSSRiskLevel.HIGH]:
                    risk_level = XSSRiskLevel.MEDIUM
                confidence = max(confidence, 0.65)

        # 检测低风险模式
        for pattern in self.low_patterns:
            if pattern.search(content):
                detected_patterns.append(f"low:{pattern.pattern}")
                if risk_level == XSSRiskLevel.LOW:
                    confidence = max(confidence, 0.35)

        is_malicious = len(detected_patterns) > 0 and confidence > 0.5
        sanitized_content = self._sanitize_content(content, context) if is_malicious else content

        return XSSDetection(
            is_malicious=is_malicious,
            risk_level=risk_level,
            detected_patterns=detected_patterns,
            sanitized_content=sanitized_content,
            confidence=confidence,
            context=context,
            details={
                "content_length": len(content),
                "pattern_count": len(detected_patterns),
                "analysis_method": "pattern_matching",
            },
        )

    def _sanitize_content(self, content: str, context: XSSContext) -> str:
        """根据上下文清理内容"""
        if context == XSSContext.HTML_CONTENT:
            return self._sanitize_html_content(content)
        elif context == XSSContext.HTML_ATTRIBUTE:
            return self._sanitize_html_attribute(content)
        elif context == XSSContext.JAVASCRIPT:
            return self._sanitize_javascript(content)
        elif context == XSSContext.CSS:
            return self._sanitize_css(content)
        elif context == XSSContext.URL:
            return self._sanitize_url(content)
        elif context == XSSContext.JSON:
            return self._sanitize_json(content)

        # 这里不应该到达，所有枚举值都已覆盖
        raise ValueError(f"Unknown XSS context: {context}")

    def _sanitize_html_content(self, content: str) -> str:
        """清理HTML内容"""
        # 移除危险标签
        for tag in self.dangerous_tags:
            pattern = rf"<\s*{tag}[^>]*>.*?<\s*/\s*{tag}\s*>"
            content = re.sub(pattern, "", content, flags=re.IGNORECASE | re.DOTALL)

            # 移除自闭合标签
            pattern = rf"<\s*{tag}[^>]*/?>"
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        # 移除危险属性
        for attr in self.dangerous_attributes:
            pattern = rf'\s+{attr}\s*=\s*["\'][^"\']*["\']'
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        # HTML实体编码
        content = html.escape(content, quote=False)

        return content

    def _sanitize_html_attribute(self, content: str) -> str:
        """清理HTML属性值"""
        # 移除javascript:协议
        content = re.sub(r"javascript\s*:", "", content, flags=re.IGNORECASE)

        # 移除data:协议
        content = re.sub(r"data\s*:", "", content, flags=re.IGNORECASE)

        # HTML属性编码
        content = html.escape(content, quote=True)

        return content

    def _sanitize_javascript(self, content: str) -> str:
        """清理JavaScript内容"""
        # 移除危险函数调用
        dangerous_functions = [
            "eval",
            "setTimeout",
            "setInterval",
            "Function",
            "document.write",
            "document.writeln",
            "innerHTML",
            "outerHTML",
            "insertAdjacentHTML",
        ]

        for func in dangerous_functions:
            pattern = rf"\b{func}\s*\("
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        # JavaScript字符串编码
        content = content.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")

        return content

    def _sanitize_css(self, content: str) -> str:
        """清理CSS内容"""
        # 移除expression
        content = re.sub(r"expression\s*\([^)]*\)", "", content, flags=re.IGNORECASE)

        # 移除javascript:协议
        content = re.sub(r"javascript\s*:", "", content, flags=re.IGNORECASE)

        # 移除@import
        content = re.sub(r"@import[^;]*;", "", content, flags=re.IGNORECASE)

        return content

    def _sanitize_url(self, content: str) -> str:
        """清理URL内容"""
        # URL编码
        content = urllib.parse.quote(content, safe=":/?#[]@!$&'()*+,;=")

        return content

    def _sanitize_json(self, content: str) -> str:
        """清理JSON内容"""
        # JSON字符串编码
        content = content.replace("\\", "\\\\").replace('"', '\\"')

        return content

    def generate_csp_header(self, strict: bool = True) -> str:
        """生成内容安全策略头"""
        if strict:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self'",
                "connect-src 'self'",
                "media-src 'self'",
                "object-src 'none'",
                "child-src 'none'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        else:
            csp_directives = [
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "img-src 'self' data: https:",
                "object-src 'none'",
                "frame-ancestors 'none'",
            ]

        return "; ".join(csp_directives)

    def get_security_headers(self) -> dict[str, str]:
        """获取安全响应头"""
        return {
            "Content-Security-Policy": self.generate_csp_header(strict=True),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    def get_security_recommendations(self, detection: XSSDetection) -> list[str]:
        """获取安全建议"""
        recommendations = []

        if detection.is_malicious:
            recommendations.extend(
                [
                    "对所有用户输入进行严格过滤和编码",
                    "实施内容安全策略(CSP)",
                    "使用安全的模板引擎",
                    "启用XSS防护响应头",
                ]
            )

            if detection.risk_level == XSSRiskLevel.CRITICAL:
                recommendations.extend(
                    [
                        "立即阻止该请求",
                        "记录安全事件并告警",
                        "检查是否存在存储型XSS",
                        "进行全面的安全审计",
                    ]
                )

        return recommendations


# 全局XSS防护器实例
xss_protection = XSSProtection()
