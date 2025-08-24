"""英语四级评分标准工具类 - 严格执行官方评分标准."""

from enum import Enum
from typing import Any


class CET4WritingLevel(str, Enum):
    """四级写作评分等级."""

    EXCELLENT = "excellent"  # 优秀 (13-15分)
    GOOD = "good"  # 良好 (10-12分)
    FAIR = "fair"  # 及格 (7-9分)
    POOR = "poor"  # 不及格 (4-6分)
    VERY_POOR = "very_poor"  # 很差 (1-3分)


class CET4TranslationLevel(str, Enum):
    """四级翻译评分等级."""

    EXCELLENT = "excellent"  # 优秀 (13-15分)
    GOOD = "good"  # 良好 (10-12分)
    FAIR = "fair"  # 及格 (7-9分)
    POOR = "poor"  # 不及格 (4-6分)
    VERY_POOR = "very_poor"  # 很差 (1-3分)


class CET4Standards:
    """英语四级评分标准工具类 - 官方标准实现."""

    # 四级写作评分标准
    WRITING_STANDARDS = {
        CET4WritingLevel.EXCELLENT: {
            "score_range": (13, 15),
            "description": "切题。表达思想清楚，文字通顺、连贯，基本上无语言错误，仅有个别小错。",
            "criteria": {
                "content": "内容切题，思想表达清楚",
                "organization": "文字通顺，连贯性强",
                "language": "基本无语言错误",
                "vocabulary": "词汇使用准确、丰富",
                "grammar": "语法正确，句式多样",
            },
            "requirements": {
                "word_count": "≥120词",
                "structure": "三段式结构完整",
                "coherence": "逻辑清晰，过渡自然",
                "accuracy": "错误率<5%",
            },
        },
        CET4WritingLevel.GOOD: {
            "score_range": (10, 12),
            "description": "切题。表达思想清楚，文字连贯，但有少量语言错误。",
            "criteria": {
                "content": "内容基本切题，思想较清楚",
                "organization": "文字较连贯",
                "language": "有少量语言错误",
                "vocabulary": "词汇使用基本准确",
                "grammar": "语法基本正确",
            },
            "requirements": {
                "word_count": "≥100词",
                "structure": "结构基本完整",
                "coherence": "逻辑基本清晰",
                "accuracy": "错误率5-10%",
            },
        },
        CET4WritingLevel.FAIR: {
            "score_range": (7, 9),
            "description": "基本切题。有些地方表达思想不够清楚，文字勉强连贯；语言错误相当多，其中有一些是严重错误。",
            "criteria": {
                "content": "基本切题，思想表达不够清楚",
                "organization": "文字勉强连贯",
                "language": "语言错误相当多",
                "vocabulary": "词汇使用有误",
                "grammar": "语法错误较多",
            },
            "requirements": {
                "word_count": "≥80词",
                "structure": "结构不够完整",
                "coherence": "逻辑不够清晰",
                "accuracy": "错误率10-20%",
            },
        },
        CET4WritingLevel.POOR: {
            "score_range": (4, 6),
            "description": "基本切题。表达思想不清楚，连贯性差。有较多的严重语言错误。",
            "criteria": {
                "content": "基本切题，思想表达不清楚",
                "organization": "连贯性差",
                "language": "严重语言错误较多",
                "vocabulary": "词汇使用错误多",
                "grammar": "语法错误严重",
            },
            "requirements": {
                "word_count": "≥60词",
                "structure": "结构混乱",
                "coherence": "逻辑混乱",
                "accuracy": "错误率20-40%",
            },
        },
        CET4WritingLevel.VERY_POOR: {
            "score_range": (1, 3),
            "description": "条理不清，思路紊乱，语言支离破碎或大部分句子均有错误，且多数为严重错误。",
            "criteria": {
                "content": "条理不清，思路紊乱",
                "organization": "语言支离破碎",
                "language": "大部分句子有严重错误",
                "vocabulary": "词汇使用严重错误",
                "grammar": "语法错误严重且普遍",
            },
            "requirements": {
                "word_count": "<60词",
                "structure": "无明确结构",
                "coherence": "无逻辑可言",
                "accuracy": "错误率>40%",
            },
        },
    }

    # 四级翻译评分标准
    TRANSLATION_STANDARDS = {
        CET4TranslationLevel.EXCELLENT: {
            "score_range": (13, 15),
            "description": "译文准确表达了原文的意思。用词贴切，行文流畅，基本上无语言错误。",
            "criteria": {
                "accuracy": "准确表达原文意思",
                "fluency": "行文流畅自然",
                "vocabulary": "用词贴切准确",
                "grammar": "基本无语言错误",
                "completeness": "翻译完整",
            },
        },
        CET4TranslationLevel.GOOD: {
            "score_range": (10, 12),
            "description": "译文基本上表达了原文的意思。文字通顺、连贯，无重大语言错误。",
            "criteria": {
                "accuracy": "基本表达原文意思",
                "fluency": "文字通顺连贯",
                "vocabulary": "用词基本准确",
                "grammar": "无重大语言错误",
                "completeness": "翻译基本完整",
            },
        },
        CET4TranslationLevel.FAIR: {
            "score_range": (7, 9),
            "description": "译文勉强表达了原文的意思。用词欠准确，语言错误相当多，其中有些是严重语言错误。",
            "criteria": {
                "accuracy": "勉强表达原文意思",
                "fluency": "文字不够流畅",
                "vocabulary": "用词欠准确",
                "grammar": "语言错误相当多",
                "completeness": "翻译不够完整",
            },
        },
        CET4TranslationLevel.POOR: {
            "score_range": (4, 6),
            "description": "译文仅表达了一小部分原文的意思。用词不准确，有相当多的严重语言错误。",
            "criteria": {
                "accuracy": "仅表达部分原文意思",
                "fluency": "文字不流畅",
                "vocabulary": "用词不准确",
                "grammar": "严重语言错误多",
                "completeness": "翻译不完整",
            },
        },
        CET4TranslationLevel.VERY_POOR: {
            "score_range": (1, 3),
            "description": "译文支离破碎。大部分句子均有错误，且多数为严重语言错误。",
            "criteria": {
                "accuracy": "译文支离破碎",
                "fluency": "无流畅性可言",
                "vocabulary": "用词严重错误",
                "grammar": "大部分句子有严重错误",
                "completeness": "翻译严重不完整",
            },
        },
    }

    # 四级听力评分标准
    LISTENING_STANDARDS = {
        "short_conversation": {
            "total_questions": 8,
            "points_per_question": 1,
            "time_limit": 25,  # 分钟
            "accuracy_threshold": 0.6,
        },
        "long_conversation": {
            "total_questions": 7,
            "points_per_question": 1,
            "time_limit": 25,
            "accuracy_threshold": 0.6,
        },
        "passage": {
            "total_questions": 10,
            "points_per_question": 2,
            "time_limit": 25,
            "accuracy_threshold": 0.6,
        },
    }

    # 四级阅读评分标准
    READING_STANDARDS = {
        "word_matching": {
            "total_questions": 10,
            "points_per_question": 0.5,
            "time_limit": 15,  # 分钟
            "accuracy_threshold": 0.7,
        },
        "long_reading": {
            "total_questions": 10,
            "points_per_question": 1,
            "time_limit": 15,
            "accuracy_threshold": 0.6,
        },
        "careful_reading": {
            "total_questions": 10,
            "points_per_question": 2,
            "time_limit": 25,
            "accuracy_threshold": 0.6,
        },
    }

    @classmethod
    def evaluate_writing(cls, content: str, word_count: int, error_count: int) -> dict[str, Any]:
        """评估写作水平."""
        # 计算错误率
        error_rate = error_count / max(word_count, 1) if word_count > 0 else 1.0

        # 根据字数和错误率确定等级
        if word_count >= 120 and error_rate < 0.05:
            level = CET4WritingLevel.EXCELLENT
        elif word_count >= 100 and error_rate < 0.10:
            level = CET4WritingLevel.GOOD
        elif word_count >= 80 and error_rate < 0.20:
            level = CET4WritingLevel.FAIR
        elif word_count >= 60 and error_rate < 0.40:
            level = CET4WritingLevel.POOR
        else:
            level = CET4WritingLevel.VERY_POOR

        standard = cls.WRITING_STANDARDS[level]
        score_range = standard["score_range"]

        # 在等级范围内根据具体表现调整分数
        base_score = float(score_range[0])  # type: ignore
        range_size = float(score_range[1]) - float(score_range[0])  # type: ignore

        # 根据字数和错误率在范围内调整
        word_factor = min(1.0, word_count / 120) if level != CET4WritingLevel.VERY_POOR else 0.5
        error_factor = max(0.0, 1.0 - error_rate * 2)

        adjustment = range_size * (word_factor * 0.5 + error_factor * 0.5)
        final_score = base_score + adjustment

        return {
            "level": level.value,
            "score": round(final_score, 1),
            "score_range": score_range,
            "standard": standard,
            "metrics": {
                "word_count": word_count,
                "error_count": error_count,
                "error_rate": round(error_rate * 100, 1),
                "word_factor": round(word_factor, 2),
                "error_factor": round(error_factor, 2),
            },
        }

    @classmethod
    def evaluate_translation(
        cls, accuracy_score: float, fluency_score: float, completeness_score: float
    ) -> dict[str, Any]:
        """评估翻译水平."""
        # 综合评分 (准确性50% + 流畅性30% + 完整性20%)
        composite_score = accuracy_score * 0.5 + fluency_score * 0.3 + completeness_score * 0.2

        # 确定等级
        if composite_score >= 0.9:
            level = CET4TranslationLevel.EXCELLENT
        elif composite_score >= 0.75:
            level = CET4TranslationLevel.GOOD
        elif composite_score >= 0.6:
            level = CET4TranslationLevel.FAIR
        elif composite_score >= 0.4:
            level = CET4TranslationLevel.POOR
        else:
            level = CET4TranslationLevel.VERY_POOR

        standard = cls.TRANSLATION_STANDARDS[level]
        score_range = standard["score_range"]

        # 在等级范围内调整分数
        base_score = float(score_range[0])  # type: ignore
        range_size = float(score_range[1]) - float(score_range[0])  # type: ignore
        adjustment = range_size * composite_score
        final_score = base_score + adjustment

        return {
            "level": level.value,
            "score": round(final_score, 1),
            "score_range": score_range,
            "standard": standard,
            "metrics": {
                "accuracy_score": round(accuracy_score, 2),
                "fluency_score": round(fluency_score, 2),
                "completeness_score": round(completeness_score, 2),
                "composite_score": round(composite_score, 2),
            },
        }

    @classmethod
    def get_vocabulary_requirements(cls) -> dict[str, Any]:
        """获取四级词汇要求."""
        return {
            "total_words": 4500,
            "core_words": 2000,
            "recognition_words": 2500,
            "frequency_levels": {
                "high": 1000,  # 高频词汇
                "medium": 1500,  # 中频词汇
                "low": 2000,  # 低频词汇
            },
            "word_types": {
                "nouns": 0.35,  # 名词35%
                "verbs": 0.25,  # 动词25%
                "adjectives": 0.20,  # 形容词20%
                "adverbs": 0.10,  # 副词10%
                "others": 0.10,  # 其他10%
            },
        }

    @classmethod
    def get_grammar_requirements(cls) -> list[str]:
        """获取四级语法要求."""
        return [
            "时态：一般现在时、一般过去时、一般将来时、现在完成时、过去完成时",
            "语态：主动语态、被动语态",
            "句型：简单句、并列句、复合句",
            "从句：定语从句、状语从句、名词性从句",
            "非谓语动词：不定式、动名词、分词",
            "虚拟语气：基本虚拟语气结构",
            "倒装句：部分倒装、完全倒装",
            "强调句：it强调句型",
            "比较结构：比较级、最高级、同级比较",
            "介词短语：常用介词搭配",
        ]
