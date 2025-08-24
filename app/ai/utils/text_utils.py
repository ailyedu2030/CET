"""AI文本处理工具模块

提供AI服务中常用的文本处理功能，避免代码重复。
"""

import re
from typing import Any


def calculate_text_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度

    使用Jaccard相似度算法，基于词汇重叠计算相似度。

    Args:
        text1: 第一个文本
        text2: 第二个文本

    Returns:
        float: 相似度值，范围0-1，1表示完全相同
    """
    try:
        # 转换为小写并分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # 处理空文本情况
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        # 计算Jaccard相似度
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    except Exception:
        return 0.0


def check_content_length(
    content: str, min_length: int = 10, max_length: int = 5000
) -> dict[str, Any]:
    """检查内容长度

    Args:
        content: 要检查的内容
        min_length: 最小长度
        max_length: 最大长度

    Returns:
        dict: 包含检查结果的字典
    """
    content_length = len(content.strip())

    issues: list[str] = []
    suggestions: list[str] = []

    if content_length < min_length:
        issues.append("content_too_short")
        suggestions.append("建议增加更多详细说明")
    elif content_length > max_length:
        issues.append("content_too_long")
        suggestions.append("建议精简内容，突出重点")

    result: dict[str, Any] = {
        "length": content_length,
        "is_valid": min_length <= content_length <= max_length,
        "issues": issues,
        "suggestions": suggestions,
    }

    return result


def check_content_repetition(content: str, max_repetition_rate: float = 0.5) -> dict[str, Any]:
    """检查内容重复度

    Args:
        content: 要检查的内容
        max_repetition_rate: 最大重复率阈值

    Returns:
        dict: 包含检查结果的字典
    """
    words = content.split()

    if not words:
        return {
            "repetition_rate": 0.0,
            "is_valid": True,
            "issues": [],
            "suggestions": [],
        }

    unique_words = set(words)
    repetition_rate = 1 - (len(unique_words) / len(words))

    issues: list[str] = []
    suggestions: list[str] = []

    if repetition_rate > max_repetition_rate:
        issues.append("high_repetition")
        suggestions.append("内容重复度较高，建议增加多样性")

    result: dict[str, Any] = {
        "repetition_rate": repetition_rate,
        "unique_words": len(unique_words),
        "total_words": len(words),
        "is_valid": repetition_rate <= max_repetition_rate,
        "issues": issues,
        "suggestions": suggestions,
    }

    return result


def check_special_characters(content: str, max_special_char_rate: float = 0.1) -> dict[str, Any]:
    """检查特殊字符比例

    Args:
        content: 要检查的内容
        max_special_char_rate: 最大特殊字符比例

    Returns:
        dict: 包含检查结果的字典
    """
    if not content:
        return {
            "special_char_rate": 0.0,
            "is_valid": True,
            "issues": [],
            "suggestions": [],
        }

    special_char_count = len(re.findall(r"[^\w\s\u4e00-\u9fff]", content))
    special_char_rate = special_char_count / len(content)

    issues: list[str] = []
    suggestions: list[str] = []

    if special_char_rate > max_special_char_rate:
        issues.append("too_many_special_chars")
        suggestions.append("特殊字符过多，可能影响内容可读性")

    result: dict[str, Any] = {
        "special_char_rate": special_char_rate,
        "special_char_count": special_char_count,
        "is_valid": special_char_rate <= max_special_char_rate,
        "issues": issues,
        "suggestions": suggestions,
    }

    return result


def check_educational_relevance(content: str, content_type: str = "general") -> dict[str, Any]:
    """检查教育内容相关性

    Args:
        content: 要检查的内容
        content_type: 内容类型

    Returns:
        dict: 包含检查结果的字典
    """
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
        "阅读",
        "听力",
        "写作",
        "翻译",
        "练习",
        "考试",
    ]

    keyword_matches = sum(1 for keyword in educational_keywords if keyword in content)
    relevance_score = min(1.0, keyword_matches / 5.0)  # 最多5个关键词满分

    issues: list[str] = []
    suggestions: list[str] = []

    if relevance_score <= 0.2:
        issues.append("low_educational_relevance")
        suggestions.append("内容与教育主题相关性较低")

    result: dict[str, Any] = {
        "relevance_score": relevance_score,
        "keyword_matches": keyword_matches,
        "matched_keywords": [kw for kw in educational_keywords if kw in content],
        "is_relevant": relevance_score > 0.2,  # 至少20%相关性
        "issues": issues,
        "suggestions": suggestions,
    }

    return result


def extract_sentences(content: str) -> list[str]:
    """提取句子

    Args:
        content: 要处理的内容

    Returns:
        list[str]: 句子列表
    """
    # 使用中文标点符号分割句子
    sentences = re.split(r"[。！？]", content)
    # 过滤空句子
    return [s.strip() for s in sentences if s.strip()]


def calculate_chinese_ratio(content: str) -> float:
    """计算中文字符比例

    Args:
        content: 要检查的内容

    Returns:
        float: 中文字符比例，范围0-1
    """
    if not content:
        return 0.0

    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", content))
    return chinese_chars / len(content)


def generate_cache_key(prefix: str, *args: Any) -> str:
    """生成统一的缓存键

    Args:
        prefix: 缓存键前缀
        *args: 用于生成键的参数

    Returns:
        str: 生成的缓存键
    """
    import hashlib

    # 将所有参数转换为字符串并连接
    key_parts = [prefix] + [str(arg) for arg in args]
    key_string = ":".join(key_parts)

    # 如果键太长，使用哈希
    if len(key_string) > 200:
        hash_obj = hashlib.md5(key_string.encode("utf-8"))
        return f"{prefix}:hash:{hash_obj.hexdigest()}"

    return key_string


def format_ai_error_message(error: Exception, context: str = "") -> str:
    """格式化AI服务错误消息

    Args:
        error: 异常对象
        context: 错误上下文

    Returns:
        str: 格式化的错误消息
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if context:
        return f"[{context}] {error_type}: {error_msg}"
    else:
        return f"{error_type}: {error_msg}"
