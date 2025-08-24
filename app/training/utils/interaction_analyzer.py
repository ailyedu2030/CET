"""互动分析器 - 分析学习社交互动的质量和效果."""

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class InteractionAnalyzer:
    """互动分析器 - 分析和评估学习社交互动的质量."""

    def __init__(self) -> None:
        """初始化互动分析器."""
        # 内容质量评估配置
        self.quality_config = {
            "min_length": 10,  # 最小字符长度
            "max_length": 2000,  # 最大字符长度
            "keyword_bonus": 0.1,  # 关键词奖励
            "structure_bonus": 0.15,  # 结构化奖励
            "engagement_bonus": 0.2,  # 互动性奖励
        }

        # 学习相关关键词
        self.learning_keywords = {
            "positive": [
                "学习",
                "理解",
                "掌握",
                "练习",
                "复习",
                "总结",
                "思考",
                "分析",
                "方法",
                "技巧",
                "经验",
                "心得",
                "建议",
                "推荐",
                "有效",
                "提高",
                "progress",
                "improve",
                "understand",
                "practice",
                "review",
                "method",
            ],
            "question": [
                "问题",
                "疑问",
                "不懂",
                "困惑",
                "请教",
                "求助",
                "怎么",
                "为什么",
                "question",
                "doubt",
                "confused",
                "help",
                "how",
                "why",
                "what",
            ],
            "answer": [
                "答案",
                "解答",
                "解释",
                "说明",
                "因为",
                "所以",
                "首先",
                "其次",
                "answer",
                "explain",
                "because",
                "first",
                "second",
                "solution",
            ],
        }

        # 互动模式配置
        self.interaction_patterns = {
            "question_answer": {"weight": 1.0, "description": "问答互动"},
            "discussion": {"weight": 0.8, "description": "讨论交流"},
            "resource_sharing": {"weight": 1.2, "description": "资源分享"},
            "peer_review": {"weight": 1.1, "description": "同伴评议"},
            "encouragement": {"weight": 0.6, "description": "鼓励支持"},
        }

    def analyze_content_quality(
        self, content: str, content_type: str = "general"
    ) -> dict[str, Any]:
        """分析内容质量."""
        try:
            # 基础质量检查
            basic_quality = self._assess_basic_quality(content)

            # 学习相关性分析
            learning_relevance = self._analyze_learning_relevance(content)

            # 结构化程度分析
            structure_score = self._analyze_content_structure(content)

            # 互动性分析
            engagement_score = self._analyze_engagement_potential(content)

            # 情感倾向分析
            sentiment_analysis = self._analyze_sentiment(content)

            # 计算综合质量分数
            quality_score = self._calculate_overall_quality(
                basic_quality,
                learning_relevance,
                structure_score,
                engagement_score,
                sentiment_analysis,
            )

            return {
                "overall_score": quality_score,
                "basic_quality": basic_quality,
                "learning_relevance": learning_relevance,
                "structure_score": structure_score,
                "engagement_score": engagement_score,
                "sentiment": sentiment_analysis,
                "recommendations": self._generate_quality_recommendations(
                    basic_quality, learning_relevance, structure_score, engagement_score
                ),
                "analyzed_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"内容质量分析失败: {str(e)}")
            return {"overall_score": 0.5, "error": str(e)}

    def analyze_interaction_pattern(self, interaction_data: dict[str, Any]) -> dict[str, Any]:
        """分析互动模式."""
        try:
            # 识别互动类型
            interaction_type = self._identify_interaction_type(interaction_data)

            # 分析互动频率
            frequency_analysis = self._analyze_interaction_frequency(interaction_data)

            # 分析参与度
            participation_analysis = self._analyze_participation_level(interaction_data)

            # 分析互动效果
            effectiveness_analysis = self._analyze_interaction_effectiveness(interaction_data)

            # 网络分析
            network_analysis = self._analyze_interaction_network(interaction_data)

            return {
                "interaction_type": interaction_type,
                "frequency_analysis": frequency_analysis,
                "participation_analysis": participation_analysis,
                "effectiveness_analysis": effectiveness_analysis,
                "network_analysis": network_analysis,
                "pattern_insights": self._generate_pattern_insights(
                    interaction_type, frequency_analysis, participation_analysis
                ),
                "analyzed_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"互动模式分析失败: {str(e)}")
            return {"error": str(e)}

    def analyze_learning_impact(self, interaction_history: list[dict[str, Any]]) -> dict[str, Any]:
        """分析互动对学习效果的影响."""
        try:
            # 学习成果关联分析
            learning_correlation = self._analyze_learning_correlation(interaction_history)

            # 知识传播分析
            knowledge_diffusion = self._analyze_knowledge_diffusion(interaction_history)

            # 协作效果分析
            collaboration_effectiveness = self._analyze_collaboration_effectiveness(
                interaction_history
            )

            # 长期影响分析
            long_term_impact = self._analyze_long_term_impact(interaction_history)

            return {
                "learning_correlation": learning_correlation,
                "knowledge_diffusion": knowledge_diffusion,
                "collaboration_effectiveness": collaboration_effectiveness,
                "long_term_impact": long_term_impact,
                "overall_impact_score": self._calculate_impact_score(
                    learning_correlation,
                    knowledge_diffusion,
                    collaboration_effectiveness,
                ),
                "recommendations": self._generate_impact_recommendations(
                    learning_correlation, collaboration_effectiveness
                ),
                "analyzed_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"学习影响分析失败: {str(e)}")
            return {"error": str(e)}

    def generate_interaction_insights(self, user_id: int, period_days: int = 30) -> dict[str, Any]:
        """生成用户互动洞察报告."""
        try:
            # 获取用户互动数据
            user_interactions = self._get_user_interactions(user_id, period_days)

            # 互动活跃度分析
            activity_analysis = self._analyze_user_activity(user_interactions)

            # 互动质量分析
            quality_analysis = self._analyze_user_interaction_quality(user_interactions)

            # 社交网络位置分析
            network_position = self._analyze_user_network_position(user_id, user_interactions)

            # 学习影响分析
            learning_influence = self._analyze_user_learning_influence(user_interactions)

            # 改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                activity_analysis, quality_analysis, network_position
            )

            return {
                "user_id": user_id,
                "analysis_period": {"days": period_days, "end_date": datetime.now()},
                "activity_analysis": activity_analysis,
                "quality_analysis": quality_analysis,
                "network_position": network_position,
                "learning_influence": learning_influence,
                "improvement_suggestions": improvement_suggestions,
                "overall_rating": self._calculate_overall_interaction_rating(
                    activity_analysis, quality_analysis, learning_influence
                ),
                "generated_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"生成互动洞察失败: {str(e)}")
            return {"error": str(e)}

    # ==================== 私有方法 ====================

    def _assess_basic_quality(self, content: str) -> dict[str, Any]:
        """评估基础内容质量."""
        length = len(content.strip())

        # 长度评分
        if length < self.quality_config["min_length"]:
            length_score = 0.3
        elif length > self.quality_config["max_length"]:
            length_score = 0.7
        else:
            # 理想长度范围内的评分
            ideal_length = 200
            length_score = min(1.0, 0.5 + (length / ideal_length) * 0.5)

        # 语言质量评分
        language_score = self._assess_language_quality(content)

        # 信息密度评分
        information_density = self._assess_information_density(content)

        return {
            "length_score": length_score,
            "language_score": language_score,
            "information_density": information_density,
            "overall": (length_score + language_score + information_density) / 3,
        }

    def _analyze_learning_relevance(self, content: str) -> dict[str, Any]:
        """分析学习相关性."""
        content_lower = content.lower()

        # 计算各类关键词出现频率
        keyword_scores = {}
        for category, keywords in self.learning_keywords.items():
            count = sum(1 for keyword in keywords if keyword in content_lower)
            keyword_scores[category] = min(count / len(keywords), 1.0)

        # 计算整体学习相关性
        relevance_score = sum(keyword_scores.values()) / len(keyword_scores)

        return {
            "keyword_scores": keyword_scores,
            "relevance_score": relevance_score,
            "dominant_theme": max(keyword_scores.items(), key=lambda x: x[1])[0],
        }

    def _analyze_content_structure(self, content: str) -> float:
        """分析内容结构化程度."""
        structure_indicators = [
            r"\d+\.",  # 数字列表
            r"[一二三四五六七八九十]+[、.]",  # 中文数字列表
            r"[（(]\d+[）)]",  # 括号数字
            r"首先|其次|然后|最后|总之",  # 逻辑连接词
            r"因为|所以|但是|然而|因此",  # 因果关系词
            r"\n\s*[-*+]\s+",  # 项目符号
        ]

        structure_count = 0
        for pattern in structure_indicators:
            if re.search(pattern, content):
                structure_count += 1

        # 结构化程度评分
        max_indicators = len(structure_indicators)
        structure_score = min(structure_count / max_indicators * 2, 1.0)

        return structure_score

    def _analyze_engagement_potential(self, content: str) -> float:
        """分析内容的互动潜力."""
        engagement_indicators = [
            r"[？?]",  # 问号
            r"大家|同学们|朋友们",  # 称呼词
            r"请问|求助|帮忙|建议",  # 求助词
            r"分享|推荐|介绍",  # 分享词
            r"讨论|交流|聊聊",  # 讨论词
            r"@\w+",  # @提及
        ]

        engagement_count = 0
        for pattern in engagement_indicators:
            engagement_count += len(re.findall(pattern, content))

        # 互动潜力评分
        engagement_score = min(engagement_count / 5, 1.0)

        return engagement_score

    def _analyze_sentiment(self, content: str) -> dict[str, Any]:
        """分析情感倾向."""
        positive_words = [
            "好",
            "棒",
            "赞",
            "优秀",
            "完美",
            "成功",
            "进步",
            "提高",
            "有效",
            "good",
            "great",
            "excellent",
            "perfect",
            "success",
            "improve",
        ]

        negative_words = [
            "差",
            "糟",
            "失败",
            "困难",
            "问题",
            "错误",
            "不会",
            "不懂",
            "bad",
            "terrible",
            "fail",
            "difficult",
            "problem",
            "error",
        ]

        content_lower = content.lower()

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        if positive_count + negative_count == 0:
            sentiment = "neutral"
            polarity = 0.0
        else:
            polarity = (positive_count - negative_count) / (positive_count + negative_count)
            if polarity > 0.2:
                sentiment = "positive"
            elif polarity < -0.2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "polarity": polarity,
            "positive_count": positive_count,
            "negative_count": negative_count,
        }

    def _calculate_overall_quality(
        self,
        basic: dict[str, Any],
        relevance: dict[str, Any],
        structure: float,
        engagement: float,
        sentiment: dict[str, Any],
    ) -> float:
        """计算综合质量分数."""
        # 权重配置
        weights = {
            "basic": 0.3,
            "relevance": 0.25,
            "structure": 0.2,
            "engagement": 0.15,
            "sentiment": 0.1,
        }

        # 情感调整因子
        sentiment_factor = 1.0
        if sentiment["sentiment"] == "positive":
            sentiment_factor = 1.1
        elif sentiment["sentiment"] == "negative":
            sentiment_factor = 0.9

        quality_score = (
            basic["overall"] * weights["basic"]
            + relevance["relevance_score"] * weights["relevance"]
            + structure * weights["structure"]
            + engagement * weights["engagement"]
            + abs(sentiment["polarity"]) * weights["sentiment"]
        ) * sentiment_factor

        return float(min(quality_score, 1.0))

    def _generate_quality_recommendations(
        self,
        basic: dict[str, Any],
        relevance: dict[str, Any],
        structure: float,
        engagement: float,
    ) -> list[str]:
        """生成质量改进建议."""
        recommendations = []

        if basic["overall"] < 0.6:
            recommendations.append("建议增加内容的信息密度，提供更多有价值的信息")

        if relevance["relevance_score"] < 0.5:
            recommendations.append("建议增加更多学习相关的内容和关键词")

        if structure < 0.4:
            recommendations.append("建议使用列表、序号等方式提高内容的结构化程度")

        if engagement < 0.3:
            recommendations.append("建议增加问题、讨论等互动元素")

        return recommendations

    def _assess_language_quality(self, content: str) -> float:
        """评估语言质量."""
        # 简化的语言质量评估
        # 检查是否有明显的语法错误标志
        error_patterns = [
            r"(.)\1{3,}",  # 重复字符
            r"[！!]{2,}",  # 多个感叹号
            r"[？?]{2,}",  # 多个问号
        ]

        error_count = 0
        for pattern in error_patterns:
            error_count += len(re.findall(pattern, content))

        # 基础语言质量评分
        base_score = 0.8
        penalty = min(error_count * 0.1, 0.3)

        return max(base_score - penalty, 0.3)

    def _assess_information_density(self, content: str) -> float:
        """评估信息密度."""
        # 计算有效信息词汇比例
        words = content.split()
        if not words:
            return 0.0

        # 过滤停用词和无意义词汇
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "你",
            "他",
            "她",
            "它",
            "们",
            "这",
            "那",
            "有",
            "和",
            "与",
        }
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 1]

        density = len(meaningful_words) / len(words) if words else 0
        return min(density * 1.2, 1.0)  # 适当放大密度分数

    # 简化实现的其他方法
    def _identify_interaction_type(self, interaction_data: dict[str, Any]) -> str:
        return "discussion"

    def _analyze_interaction_frequency(self, interaction_data: dict[str, Any]) -> dict[str, Any]:
        return {"frequency": "moderate", "trend": "stable"}

    def _analyze_participation_level(self, interaction_data: dict[str, Any]) -> dict[str, Any]:
        return {"level": "active", "engagement_score": 0.75}

    def _analyze_interaction_effectiveness(
        self, interaction_data: dict[str, Any]
    ) -> dict[str, Any]:
        return {"effectiveness": "high", "impact_score": 0.8}

    def _analyze_interaction_network(self, interaction_data: dict[str, Any]) -> dict[str, Any]:
        return {"centrality": 0.6, "connections": 15}

    def _generate_pattern_insights(
        self,
        interaction_type: str,
        frequency: dict[str, Any],
        participation: dict[str, Any],
    ) -> list[str]:
        return ["用户互动积极", "参与度较高", "有良好的学习氛围"]

    def _analyze_learning_correlation(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return {"correlation": 0.7, "significance": "high"}

    def _analyze_knowledge_diffusion(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return {"diffusion_rate": 0.6, "reach": 25}

    def _analyze_collaboration_effectiveness(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return {"effectiveness": 0.75, "team_performance": "good"}

    def _analyze_long_term_impact(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return {"retention_improvement": 0.15, "skill_development": 0.2}

    def _calculate_impact_score(
        self,
        correlation: dict[str, Any],
        diffusion: dict[str, Any],
        collaboration: dict[str, Any],
    ) -> float:
        return 0.75

    def _generate_impact_recommendations(
        self, correlation: dict[str, Any], collaboration: dict[str, Any]
    ) -> list[str]:
        return ["继续保持积极互动", "可以尝试更多协作学习"]

    def _get_user_interactions(self, user_id: int, period_days: int) -> list[dict[str, Any]]:
        return []

    def _analyze_user_activity(self, interactions: list[dict[str, Any]]) -> dict[str, Any]:
        return {"activity_level": "high", "consistency": 0.8}

    def _analyze_user_interaction_quality(
        self, interactions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {"avg_quality": 0.75, "improvement_trend": "positive"}

    def _analyze_user_network_position(
        self, user_id: int, interactions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {"position": "connector", "influence": 0.7}

    def _analyze_user_learning_influence(
        self, interactions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {"influence_score": 0.65, "helped_users": 8}

    def _generate_improvement_suggestions(
        self,
        activity: dict[str, Any],
        quality: dict[str, Any],
        position: dict[str, Any],
    ) -> list[str]:
        return ["可以尝试帮助更多同学", "继续保持高质量的互动"]

    def _calculate_overall_interaction_rating(
        self,
        activity: dict[str, Any],
        quality: dict[str, Any],
        influence: dict[str, Any],
    ) -> str:
        return "优秀"
