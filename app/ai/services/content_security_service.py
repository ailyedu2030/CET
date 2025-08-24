"""内容安全服务 - AI生成内容的安全检查和过滤."""

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型"""

    QUESTION = "question"
    ANSWER = "answer"
    EXPLANATION = "explanation"
    FEEDBACK = "feedback"
    GENERAL = "general"


class SecurityLevel(Enum):
    """安全级别"""

    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


class ContentSecurityService:
    """内容安全服务"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # 敏感词库
        self.sensitive_words: set[str] = set()
        self.whitelist_words: set[str] = set()

        # 安全策略
        self.security_policies: dict[str, Any] = {}

        # 初始化
        self._load_sensitive_words()
        self._initialize_default_policies()

    async def check_content_security(
        self,
        content: str,
        content_type: ContentType,
        content_id: str | None = None,
    ) -> dict[str, Any]:
        """检查内容安全性"""
        try:
            content_id = content_id or f"content_{int(datetime.utcnow().timestamp())}"

            # 执行安全检查
            violations = []
            risk_score = 0.0
            details = {}
            suggestions = []

            # 1. 敏感词检查
            sensitive_result = self._check_sensitive_words(content)
            if sensitive_result["violations"]:
                violations.extend(sensitive_result["violations"])
            risk_score += sensitive_result["risk_score"]
            details["sensitive_words"] = sensitive_result["details"]

            # 2. 内容质量检查
            quality_result = self._check_content_quality(content, content_type)
            risk_score += quality_result["risk_score"]
            details["quality_check"] = quality_result["details"]
            suggestions.extend(quality_result["suggestions"])

            # 3. 教育适宜性检查
            educational_result = self._check_educational_appropriateness(content, content_type)
            if educational_result["violations"]:
                violations.extend(educational_result["violations"])
            risk_score += educational_result["risk_score"]
            details["educational_check"] = educational_result["details"]

            # 计算最终风险评分和置信度
            risk_score = min(risk_score, 100.0)
            confidence_score = self._calculate_confidence_score(content, violations)

            # 确定安全级别
            security_level = self._determine_security_level(risk_score, violations)

            return {
                "content_id": content_id,
                "security_level": security_level.value,
                "risk_score": risk_score,
                "confidence_score": confidence_score,
                "violations": violations,
                "suggestions": suggestions,
                "details": details,
                "is_safe": security_level == SecurityLevel.SAFE,
                "checked_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"内容安全检查失败: {e}")
            return {
                "content_id": content_id or "unknown",
                "security_level": SecurityLevel.BLOCKED.value,
                "risk_score": 100.0,
                "confidence_score": 0.0,
                "violations": ["security_check_error"],
                "suggestions": ["请重新检查内容"],
                "details": {"error": str(e)},
                "is_safe": False,
                "checked_at": datetime.utcnow().isoformat(),
            }

    def _check_sensitive_words(self, content: str) -> dict[str, Any]:
        """检查敏感词"""
        violations = []
        risk_score = 0.0
        matched_words = []

        for word in self.sensitive_words:
            if word in content.lower():
                matched_words.append(word)
                violations.append(f"sensitive_word: {word}")
                risk_score += 20.0  # 每个敏感词增加20分风险

        return {
            "violations": violations,
            "risk_score": min(risk_score, 80.0),  # 敏感词最多80分
            "details": {"matched_words": matched_words},
        }

    def _check_content_quality(self, content: str, content_type: ContentType) -> dict[str, Any]:
        """检查内容质量"""
        risk_score = 0.0
        suggestions = []
        details = {}

        # 内容长度检查
        content_length = len(content.strip())
        if content_length < 10:
            risk_score += 5.0
            suggestions.append("内容过短，建议提供更详细的信息")
            details["length_issue"] = "content_too_short"
        elif content_length > 5000:
            risk_score += 3.0
            suggestions.append("内容过长，建议精简表达")
            details["length_issue"] = "content_too_long"

        # 重复内容检查
        words = content.split()
        if len(set(words)) < len(words) * 0.5:  # 重复词汇超过50%
            risk_score += 8.0
            suggestions.append("内容重复度较高，建议增加多样性")
            details["repetition_rate"] = len(set(words)) / len(words) if words else 0

        # 特殊字符检查
        special_char_count = len(re.findall(r"[^\w\s\u4e00-\u9fff]", content))
        if special_char_count > content_length * 0.1:  # 特殊字符超过10%
            risk_score += 5.0
            suggestions.append("特殊字符过多，可能影响内容可读性")
            details["special_char_rate"] = special_char_count / content_length

        # 教育内容相关性检查
        if content_type in [ContentType.QUESTION, ContentType.ANSWER]:
            educational_keywords = [
                "学习",
                "教育",
                "知识",
                "理解",
                "掌握",
                "英语",
                "四级",
                "语法",
                "词汇",
            ]
            keyword_matches = sum(1 for keyword in educational_keywords if keyword in content)
            if keyword_matches == 0:
                risk_score += 10.0
                suggestions.append("内容与教育主题相关性较低")
                details["educational_relevance"] = "low"

        return {
            "risk_score": risk_score,
            "suggestions": suggestions,
            "details": details,
        }

    def _check_educational_appropriateness(
        self, content: str, content_type: ContentType
    ) -> dict[str, Any]:
        """检查教育适宜性"""
        violations = []
        risk_score = 0.0
        details = {}

        # 不当内容模式检查
        inappropriate_patterns = [r"作弊", r"抄袭", r"代写", r"答案泄露", r"考试泄题"]

        matched_patterns = []
        for pattern in inappropriate_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matched_patterns.append(pattern)
                violations.append(f"inappropriate_content: {pattern}")
                risk_score += 15.0

        details["inappropriate_patterns"] = matched_patterns

        # 检查内容是否符合教育年龄段
        if content_type in [ContentType.QUESTION, ContentType.EXPLANATION]:
            # 大学生年龄段适宜性检查
            complex_words = re.findall(r"\b\w{8,}\b", content)  # 8个字符以上的词
            if len(complex_words) > len(content.split()) * 0.3:  # 复杂词汇超过30%
                risk_score += 5.0
                details["complexity_level"] = "high"

        return {
            "violations": violations,
            "risk_score": risk_score,
            "details": details,
        }

    def _calculate_confidence_score(self, content: str, violations: list[str]) -> float:
        """计算置信度分数"""
        base_confidence = 0.8

        # 根据内容长度调整置信度
        content_length = len(content)
        if content_length < 50:
            base_confidence -= 0.2
        elif content_length > 1000:
            base_confidence += 0.1

        # 根据违规数量调整置信度
        violation_penalty = len(violations) * 0.1
        final_confidence = max(0.0, min(1.0, base_confidence - violation_penalty))

        return round(final_confidence, 2)

    def _determine_security_level(self, risk_score: float, violations: list[str]) -> SecurityLevel:
        """确定安全级别"""
        if risk_score >= 70.0 or any("sensitive_word" in v for v in violations):
            return SecurityLevel.BLOCKED
        elif risk_score >= 30.0 or len(violations) > 2:
            return SecurityLevel.WARNING
        else:
            return SecurityLevel.SAFE

    def _load_sensitive_words(self) -> None:
        """加载敏感词库"""
        # 基础敏感词库
        basic_sensitive_words = {
            # 政治敏感词
            "政治敏感",
            "政府机密",
            "国家机密",
            # 暴力词汇
            "暴力行为",
            "恐怖主义",
            "极端主义",
            # 不当语言
            "恶意攻击",
            "人身攻击",
            "网络暴力",
            # 教育不当
            "考试作弊",
            "学术造假",
            "论文代写",
        }

        self.sensitive_words.update(basic_sensitive_words)

        # 教育相关白名单
        educational_whitelist = {
            "学习方法",
            "教学策略",
            "知识点",
            "考试技巧",
            "学习资源",
            "教育理论",
            "英语四级",
            "语法规则",
            "词汇学习",
        }

        self.whitelist_words.update(educational_whitelist)

    def _initialize_default_policies(self) -> None:
        """初始化默认安全策略"""
        # 题目内容策略
        self.security_policies["question_policy"] = {
            "max_risk_score": 30.0,
            "auto_block_threshold": 80.0,
            "review_threshold": 50.0,
        }

        # 答案内容策略
        self.security_policies["answer_policy"] = {
            "max_risk_score": 20.0,
            "auto_block_threshold": 70.0,
            "review_threshold": 40.0,
        }

        # 反馈内容策略
        self.security_policies["feedback_policy"] = {
            "max_risk_score": 40.0,
            "auto_block_threshold": 60.0,
            "review_threshold": 30.0,
        }


def get_content_security_service() -> ContentSecurityService:
    """获取内容安全服务实例"""
    return ContentSecurityService()
