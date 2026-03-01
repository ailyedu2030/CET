"""AI深度学习分析服务 - 🔥需求21第三阶段AI分析核心实现.

AI深度分析功能：
- 学习模式识别和分析
- 知识掌握度深度评估
- 学习效率智能评估
- 基于DeepSeek AI的深度分析
- 生成时间<5秒的高效分析
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, TypedDict

import httpx
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.shared.models.enums import TrainingType
from app.training.models.training_models import TrainingRecord, TrainingSession

logger = logging.getLogger(__name__)


class PatternRecognitionConfig(TypedDict):
    """学习模式识别配置类型."""

    min_sessions_for_pattern: int
    pattern_confidence_threshold: float
    learning_style_categories: list[str]


class KnowledgeMasteryConfig(TypedDict):
    """知识掌握度配置类型."""

    mastery_threshold: float
    struggling_threshold: float
    knowledge_decay_days: int
    retention_analysis_window: int


class EfficiencyFactors(TypedDict):
    """效率因子配置类型."""

    accuracy_weight: float
    speed_weight: float
    consistency_weight: float
    progress_weight: float


class EfficiencyAssessmentConfig(TypedDict):
    """学习效率评估配置类型."""

    optimal_accuracy_range: tuple[float, float]
    optimal_speed_range: tuple[int, int]
    efficiency_factors: EfficiencyFactors


class AIAnalysisConfig(TypedDict):
    """AI分析配置类型."""

    ai_model: str
    analysis_timeout: int
    max_data_points: int
    analysis_window_days: int
    confidence_threshold: float
    pattern_recognition: PatternRecognitionConfig
    knowledge_mastery: KnowledgeMasteryConfig
    efficiency_assessment: EfficiencyAssessmentConfig


class AIAnalysisService:
    """AI深度学习分析服务 - 基于AI的学习模式识别和深度分析."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

        # AI分析配置
        self.analysis_config: AIAnalysisConfig = {
            "ai_model": "deepseek-chat",  # DeepSeek AI模型
            "analysis_timeout": 5,  # 5秒分析超时
            "max_data_points": 200,  # 最大数据点数
            "analysis_window_days": 30,  # 30天分析窗口
            "confidence_threshold": 0.8,  # 置信度阈值
            # 学习模式识别配置
            "pattern_recognition": {
                "min_sessions_for_pattern": 5,  # 最少5个会话才识别模式
                "pattern_confidence_threshold": 0.7,  # 模式识别置信度
                "learning_style_categories": [
                    "visual_learner",
                    "auditory_learner",
                    "kinesthetic_learner",
                    "sequential_learner",
                    "global_learner",
                    "analytical_learner",
                ],
            },
            # 知识掌握度分析配置
            "knowledge_mastery": {
                "mastery_threshold": 0.85,  # 掌握阈值85%
                "struggling_threshold": 0.6,  # 困难阈值60%
                "knowledge_decay_days": 7,  # 知识遗忘周期7天
                "retention_analysis_window": 14,  # 保持分析窗口14天
            },
            # 学习效率评估配置
            "efficiency_assessment": {
                "optimal_accuracy_range": (0.75, 0.85),  # 最佳正确率范围
                "optimal_speed_range": (45, 90),  # 最佳答题时间范围（秒）
                "efficiency_factors": {
                    "accuracy_weight": 0.4,
                    "speed_weight": 0.3,
                    "consistency_weight": 0.2,
                    "progress_weight": 0.1,
                },
            },
        }

    async def generate_comprehensive_analysis_report(
        self, student_id: int, training_type: TrainingType | None = None
    ) -> dict[str, Any]:
        """生成综合AI分析报告."""
        try:
            logger.info(f"开始生成AI深度分析报告: 学生{student_id}, 训练类型{training_type}")
            start_time = datetime.now()

            # 1. 收集学习数据
            learning_data = await self._collect_learning_data(student_id, training_type)

            if not learning_data["has_sufficient_data"]:
                return {
                    "analysis_available": False,
                    "reason": "数据不足，需要更多学习记录",
                    "minimum_requirements": {
                        "sessions": self.analysis_config["pattern_recognition"][
                            "min_sessions_for_pattern"
                        ],
                        "records": 20,
                    },
                }

            # 2. 学习模式识别
            learning_patterns = await self._analyze_learning_patterns(learning_data)

            # 3. 知识掌握度分析
            knowledge_mastery = await self._analyze_knowledge_mastery(learning_data)

            # 4. 学习效率评估
            efficiency_assessment = await self._assess_learning_efficiency(
                learning_data
            )

            # 5. AI深度分析（调用DeepSeek API）
            ai_insights = await self._generate_ai_insights(
                learning_data,
                learning_patterns,
                knowledge_mastery,
                efficiency_assessment,
            )

            # 6. 生成综合报告
            analysis_time = (datetime.now() - start_time).total_seconds()

            comprehensive_report = {
                "analysis_available": True,
                "student_id": student_id,
                "training_type": training_type.name if training_type else "ALL",
                "analysis_timestamp": datetime.now(),
                "analysis_duration": analysis_time,
                "meets_time_requirement": analysis_time
                < self.analysis_config["analysis_timeout"],
                # 核心分析结果
                "learning_patterns": learning_patterns,
                "knowledge_mastery": knowledge_mastery,
                "efficiency_assessment": efficiency_assessment,
                "ai_insights": ai_insights,
                # 数据统计
                "data_summary": {
                    "analysis_period_days": self.analysis_config[
                        "analysis_window_days"
                    ],
                    "total_sessions": learning_data["session_count"],
                    "total_records": learning_data["record_count"],
                    "data_quality_score": learning_data["data_quality_score"],
                },
                # 置信度评估
                "confidence_metrics": {
                    "overall_confidence": self._calculate_overall_confidence(
                        learning_patterns, knowledge_mastery, efficiency_assessment
                    ),
                    "pattern_confidence": learning_patterns.get("confidence", 0),
                    "mastery_confidence": knowledge_mastery.get("confidence", 0),
                    "efficiency_confidence": efficiency_assessment.get("confidence", 0),
                },
            }

            logger.info(f"AI深度分析报告生成完成: 学生{student_id}, 耗时{analysis_time:.2f}秒")
            return comprehensive_report

        except Exception as e:
            logger.error(f"生成AI深度分析报告失败: {str(e)}")
            return {
                "analysis_available": False,
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def _collect_learning_data(
        self, student_id: int, training_type: TrainingType | None = None
    ) -> dict[str, Any]:
        """收集学习数据."""
        try:
            cutoff_date = datetime.now() - timedelta(
                days=self.analysis_config["analysis_window_days"]
            )

            # 构建查询
            stmt = (
                select(TrainingRecord, TrainingSession)
                .join(TrainingSession, TrainingRecord.session_id == TrainingSession.id)
                .where(
                    and_(
                        TrainingSession.student_id == student_id,
                        TrainingRecord.created_at >= cutoff_date,
                    )
                )
            )

            if training_type:
                stmt = stmt.where(TrainingSession.session_type == training_type)

            stmt = stmt.order_by(desc(TrainingRecord.created_at)).limit(
                self.analysis_config["max_data_points"]
            )

            result = await self.db.execute(stmt)
            data = result.all()

            if not data:
                return {"has_sufficient_data": False, "reason": "无学习记录"}

            # 分离记录和会话
            records = [item[0] for item in data]
            sessions = [item[1] for item in data]
            unique_sessions = list(
                {session.id: session for session in sessions}.values()
            )

            # 检查数据充分性
            has_sufficient_data = (
                len(unique_sessions)
                >= self.analysis_config["pattern_recognition"][
                    "min_sessions_for_pattern"
                ]
                and len(records) >= 20
            )

            # 计算数据质量分数
            data_quality_score = self._calculate_data_quality_score(
                records, unique_sessions
            )

            return {
                "has_sufficient_data": has_sufficient_data,
                "records": records,
                "sessions": unique_sessions,
                "session_count": len(unique_sessions),
                "record_count": len(records),
                "data_quality_score": data_quality_score,
                "analysis_period": {
                    "start_date": cutoff_date,
                    "end_date": datetime.now(),
                    "days": self.analysis_config["analysis_window_days"],
                },
            }

        except Exception as e:
            logger.error(f"收集学习数据失败: {str(e)}")
            return {"has_sufficient_data": False, "error": str(e)}

    async def _analyze_learning_patterns(
        self, learning_data: dict[str, Any]
    ) -> dict[str, Any]:
        """分析学习模式."""
        try:
            records = learning_data["records"]
            sessions = learning_data["sessions"]

            # 1. 学习时间模式分析
            time_patterns = self._analyze_time_patterns(records, sessions)

            # 2. 答题行为模式分析
            behavior_patterns = self._analyze_behavior_patterns(records)

            # 3. 难度适应模式分析
            difficulty_patterns = self._analyze_difficulty_adaptation_patterns(
                sessions, records
            )

            # 4. 学习风格识别
            learning_style = self._identify_learning_style(records, sessions)

            # 5. 计算模式识别置信度
            pattern_confidence = self._calculate_pattern_confidence(
                time_patterns, behavior_patterns, difficulty_patterns, learning_style
            )

            return {
                "time_patterns": time_patterns,
                "behavior_patterns": behavior_patterns,
                "difficulty_patterns": difficulty_patterns,
                "learning_style": learning_style,
                "confidence": pattern_confidence,
                "pattern_summary": self._generate_pattern_summary(
                    time_patterns,
                    behavior_patterns,
                    difficulty_patterns,
                    learning_style,
                ),
            }

        except Exception as e:
            logger.error(f"学习模式分析失败: {str(e)}")
            return {"error": str(e), "confidence": 0}

    async def _analyze_knowledge_mastery(
        self, learning_data: dict[str, Any]
    ) -> dict[str, Any]:
        """分析知识掌握度."""
        try:
            records = learning_data["records"]

            # 1. 按知识点分组分析
            knowledge_point_analysis = self._analyze_by_knowledge_points(records)

            # 2. 掌握度等级分类
            mastery_levels = self._classify_mastery_levels(knowledge_point_analysis)

            # 3. 知识遗忘分析
            retention_analysis = self._analyze_knowledge_retention(records)

            # 4. 学习进度评估
            progress_assessment = self._assess_learning_progress(records)

            # 5. 薄弱环节识别
            weak_areas = self._identify_weak_areas(knowledge_point_analysis)

            # 6. 计算掌握度置信度
            mastery_confidence = self._calculate_mastery_confidence(
                knowledge_point_analysis, retention_analysis, progress_assessment
            )

            return {
                "knowledge_point_analysis": knowledge_point_analysis,
                "mastery_levels": mastery_levels,
                "retention_analysis": retention_analysis,
                "progress_assessment": progress_assessment,
                "weak_areas": weak_areas,
                "confidence": mastery_confidence,
                "overall_mastery_score": self._calculate_overall_mastery_score(
                    mastery_levels
                ),
            }

        except Exception as e:
            logger.error(f"知识掌握度分析失败: {str(e)}")
            return {"error": str(e), "confidence": 0}

    async def _assess_learning_efficiency(
        self, learning_data: dict[str, Any]
    ) -> dict[str, Any]:
        """评估学习效率."""
        try:
            records = learning_data["records"]
            sessions = learning_data["sessions"]

            # 1. 准确率效率分析
            accuracy_efficiency = self._analyze_accuracy_efficiency(records)

            # 2. 速度效率分析
            speed_efficiency = self._analyze_speed_efficiency(records)

            # 3. 一致性分析
            consistency_analysis = self._analyze_learning_consistency(records)

            # 4. 进步速度分析
            progress_rate = self._analyze_progress_rate(records, sessions)

            # 5. 综合效率评分
            efficiency_factors = self.analysis_config["efficiency_assessment"][
                "efficiency_factors"
            ]
            overall_efficiency = (
                accuracy_efficiency["score"] * efficiency_factors["accuracy_weight"]
                + speed_efficiency["score"] * efficiency_factors["speed_weight"]
                + consistency_analysis["score"]
                * efficiency_factors["consistency_weight"]
                + progress_rate["score"] * efficiency_factors["progress_weight"]
            )

            # 6. 效率等级评定
            efficiency_level = self._determine_efficiency_level(overall_efficiency)

            # 7. 改进建议
            improvement_suggestions = self._generate_efficiency_improvement_suggestions(
                accuracy_efficiency,
                speed_efficiency,
                consistency_analysis,
                progress_rate,
            )

            return {
                "accuracy_efficiency": accuracy_efficiency,
                "speed_efficiency": speed_efficiency,
                "consistency_analysis": consistency_analysis,
                "progress_rate": progress_rate,
                "overall_efficiency": overall_efficiency,
                "efficiency_level": efficiency_level,
                "improvement_suggestions": improvement_suggestions,
                "confidence": min(0.9, overall_efficiency),  # 效率分数作为置信度
            }

        except Exception as e:
            logger.error(f"学习效率评估失败: {str(e)}")
            return {"error": str(e), "confidence": 0}

    async def _generate_ai_insights(
        self,
        learning_data: dict[str, Any],
        patterns: dict[str, Any],
        mastery: dict[str, Any],
        efficiency: dict[str, Any],
    ) -> dict[str, Any]:
        """生成AI深度洞察."""
        try:
            # 准备AI分析的数据摘要
            data_summary = {
                "student_profile": {
                    "total_sessions": learning_data["session_count"],
                    "total_records": learning_data["record_count"],
                    "data_quality": learning_data["data_quality_score"],
                    "analysis_period": learning_data["analysis_period"]["days"],
                },
                "learning_patterns": {
                    "learning_style": patterns.get("learning_style", {}),
                    "time_patterns": patterns.get("time_patterns", {}),
                    "behavior_patterns": patterns.get("behavior_patterns", {}),
                },
                "knowledge_mastery": {
                    "overall_score": mastery.get("overall_mastery_score", 0),
                    "weak_areas": mastery.get("weak_areas", []),
                    "progress_rate": mastery.get("progress_assessment", {}),
                },
                "efficiency_metrics": {
                    "overall_efficiency": efficiency.get("overall_efficiency", 0),
                    "efficiency_level": efficiency.get("efficiency_level", "unknown"),
                    "main_bottlenecks": efficiency.get("improvement_suggestions", []),
                },
            }

            # 调用AI分析API
            ai_analysis = await self._call_deepseek_analysis_api(data_summary)

            return {
                "ai_generated_insights": ai_analysis.get("insights", []),
                "personalized_recommendations": ai_analysis.get("recommendations", []),
                "learning_trajectory_prediction": ai_analysis.get("predictions", {}),
                "confidence_score": ai_analysis.get("confidence", 0.8),
                "analysis_method": "deepseek_ai",
                "api_response_time": ai_analysis.get("response_time", 0),
            }

        except Exception as e:
            logger.error(f"生成AI洞察失败: {str(e)}")
            # 返回基于规则的备用分析
            return await self._generate_fallback_insights(
                learning_data, patterns, mastery, efficiency
            )

    async def _call_deepseek_analysis_api(
        self, data_summary: dict[str, Any]
    ) -> dict[str, Any]:
        """调用DeepSeek AI分析API."""
        try:
            start_time = datetime.now()

            # 构建AI分析提示
            analysis_prompt = self._build_analysis_prompt(data_summary)

            # 调用DeepSeek API
            async with httpx.AsyncClient(
                timeout=self.analysis_config["analysis_timeout"]
            ) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.analysis_config["ai_model"],
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的学习分析专家，擅长分析学生的学习数据并提供个性化建议。",
                            },
                            {"role": "user", "content": analysis_prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    },
                )

            response_time = (datetime.now() - start_time).total_seconds()

            if response.status_code == 200:
                ai_response = response.json()
                content = ai_response["choices"][0]["message"]["content"]

                # 解析AI响应
                parsed_analysis = self._parse_ai_response(content)
                parsed_analysis["response_time"] = response_time

                return parsed_analysis
            else:
                logger.error(f"DeepSeek API调用失败: {response.status_code}")
                return {"error": "API调用失败", "response_time": response_time}

        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {str(e)}")
            return {"error": str(e), "response_time": 0}

    def _build_analysis_prompt(self, data_summary: dict[str, Any]) -> str:
        """构建AI分析提示."""
        prompt = f"""
请基于以下学习数据进行深度分析：

学生概况：
- 学习会话数：{data_summary["student_profile"]["total_sessions"]}
- 答题记录数：{data_summary["student_profile"]["total_records"]}
- 数据质量分数：{data_summary["student_profile"]["data_quality"]:.2f}
- 分析周期：{data_summary["student_profile"]["analysis_period"]}天

学习模式：
- 学习风格：{data_summary["learning_patterns"]["learning_style"]}
- 时间模式：{data_summary["learning_patterns"]["time_patterns"]}
- 行为模式：{data_summary["learning_patterns"]["behavior_patterns"]}

知识掌握度：
- 整体掌握分数：{data_summary["knowledge_mastery"]["overall_score"]:.2f}
- 薄弱环节：{data_summary["knowledge_mastery"]["weak_areas"]}
- 进步情况：{data_summary["knowledge_mastery"]["progress_rate"]}

学习效率：
- 整体效率：{data_summary["efficiency_metrics"]["overall_efficiency"]:.2f}
- 效率等级：{data_summary["efficiency_metrics"]["efficiency_level"]}
- 主要瓶颈：{data_summary["efficiency_metrics"]["main_bottlenecks"]}

请提供：
1. 深度学习洞察（3-5个关键发现）
2. 个性化改进建议（具体可执行的建议）
3. 学习轨迹预测（未来发展趋势）

请以JSON格式返回，包含insights、recommendations、predictions三个字段。
"""
        return prompt

    def _parse_ai_response(self, content: str) -> dict[str, Any]:
        """解析AI响应内容."""
        try:
            # 尝试解析JSON
            if content.strip().startswith("{"):
                parsed_content: dict[str, Any] = json.loads(content)
                return parsed_content

            # 如果不是JSON，进行文本解析
            insights: list[str] = []
            recommendations: list[str] = []
            predictions: dict[str, Any] = {}

            lines = content.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if "洞察" in line or "insights" in line.lower():
                    current_section = "insights"
                elif "建议" in line or "recommendations" in line.lower():
                    current_section = "recommendations"
                elif "预测" in line or "predictions" in line.lower():
                    current_section = "predictions"
                elif line and line.startswith(("-", "•", "1.", "2.", "3.")):
                    if current_section == "insights":
                        insights.append(line.lstrip("-•123. "))
                    elif current_section == "recommendations":
                        recommendations.append(line.lstrip("-•123. "))

            return {
                "insights": insights,
                "recommendations": recommendations,
                "predictions": predictions,
                "confidence": 0.8,
            }

        except Exception as e:
            logger.error(f"解析AI响应失败: {str(e)}")
            return {
                "insights": ["AI分析响应解析失败"],
                "recommendations": ["建议重新进行分析"],
                "predictions": {},
                "confidence": 0.3,
            }

    async def _generate_fallback_insights(
        self,
        learning_data: dict[str, Any],
        patterns: dict[str, Any],
        mastery: dict[str, Any],
        efficiency: dict[str, Any],
    ) -> dict[str, Any]:
        """生成备用洞察（基于规则）."""
        insights = []
        recommendations = []

        # 基于效率生成洞察
        overall_efficiency = efficiency.get("overall_efficiency", 0)
        if overall_efficiency > 0.8:
            insights.append("学习效率优秀，保持当前学习节奏")
        elif overall_efficiency > 0.6:
            insights.append("学习效率良好，有进一步提升空间")
        else:
            insights.append("学习效率需要改进，建议调整学习策略")

        # 基于掌握度生成洞察
        mastery_score = mastery.get("overall_mastery_score", 0)
        if mastery_score > 0.85:
            insights.append("知识掌握度很高，可以尝试更高难度内容")
        elif mastery_score > 0.7:
            insights.append("知识掌握度良好，继续巩固薄弱环节")
        else:
            insights.append("知识掌握度有待提高，需要加强基础练习")

        # 生成基础建议
        weak_areas = mastery.get("weak_areas", [])
        if weak_areas:
            recommendations.append(f"重点关注薄弱知识点：{', '.join(weak_areas[:3])}")

        efficiency_level = efficiency.get("efficiency_level", "unknown")
        if efficiency_level == "low":
            recommendations.append("建议调整学习时间安排，提高专注度")

        return {
            "ai_generated_insights": insights,
            "personalized_recommendations": recommendations,
            "learning_trajectory_prediction": {"trend": "stable", "confidence": 0.6},
            "confidence_score": 0.6,
            "analysis_method": "rule_based_fallback",
            "api_response_time": 0,
        }

    def _calculate_data_quality_score(
        self, records: list[Any], sessions: list[Any]
    ) -> float:
        """计算数据质量分数."""
        try:
            quality_factors = []

            # 数据完整性
            complete_records = sum(
                1 for r in records if r.time_spent and r.time_spent > 0
            )
            completeness = complete_records / len(records) if records else 0
            quality_factors.append(completeness)

            # 数据时间分布
            if len(sessions) > 1:
                session_dates = [s.created_at.date() for s in sessions]
                unique_dates = len(set(session_dates))
                time_distribution = min(1.0, unique_dates / 7)  # 理想情况下7天内有分布
                quality_factors.append(time_distribution)

            # 数据量充分性
            volume_score = min(1.0, len(records) / 50)  # 50个记录为满分
            quality_factors.append(volume_score)

            return sum(quality_factors) / len(quality_factors) if quality_factors else 0

        except Exception as e:
            logger.error(f"计算数据质量分数失败: {str(e)}")
            return 0.5

    def _calculate_overall_confidence(
        self,
        patterns: dict[str, Any],
        mastery: dict[str, Any],
        efficiency: dict[str, Any],
    ) -> float:
        """计算整体置信度."""
        confidences: list[float] = [
            patterns.get("confidence", 0),
            mastery.get("confidence", 0),
            efficiency.get("confidence", 0),
        ]

        return sum(confidences) / len(confidences) if confidences else 0

    def _analyze_time_patterns(
        self, records: list[Any], sessions: list[Any]
    ) -> dict[str, Any]:
        """分析学习时间模式."""
        try:
            if not sessions:
                return {
                    "optimal_learning_time": "unknown",
                    "session_duration_pattern": "unknown",
                }

            # 分析学习时间偏好
            hour_counts: dict[int, int] = {}
            for session in sessions:
                hour = session.created_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

            # 找出最活跃的时间段
            if hour_counts:
                peak_hour = max(hour_counts.keys(), key=lambda x: hour_counts[x])
                if 6 <= peak_hour < 12:
                    optimal_time = "morning"
                elif 12 <= peak_hour < 18:
                    optimal_time = "afternoon"
                elif 18 <= peak_hour < 22:
                    optimal_time = "evening"
                else:
                    optimal_time = "night"
            else:
                optimal_time = "unknown"

            # 分析会话持续时间模式
            durations: list[float] = []
            for session in sessions:
                if session.end_time and session.start_time:
                    duration = (
                        session.end_time - session.start_time
                    ).total_seconds() / 60
                    durations.append(duration)

            if durations:
                avg_duration = sum(durations) / len(durations)
                if avg_duration < 15:
                    duration_pattern = "short_sessions"
                elif avg_duration < 45:
                    duration_pattern = "medium_sessions"
                else:
                    duration_pattern = "long_sessions"
            else:
                duration_pattern = "unknown"

            return {
                "optimal_learning_time": optimal_time,
                "session_duration_pattern": duration_pattern,
                "average_session_duration": (
                    sum(durations) / len(durations) if durations else 0
                ),
                "peak_hour": hour_counts,
            }

        except Exception as e:
            logger.error(f"分析时间模式失败: {str(e)}")
            return {
                "optimal_learning_time": "unknown",
                "session_duration_pattern": "unknown",
            }

    def _analyze_behavior_patterns(self, records: list[Any]) -> dict[str, Any]:
        """分析答题行为模式."""
        try:
            if not records:
                return {
                    "answer_speed_pattern": "unknown",
                    "accuracy_pattern": "unknown",
                }

            # 分析答题速度模式
            answer_times: list[float] = [
                r.time_spent for r in records if r.time_spent and r.time_spent > 0
            ]
            if answer_times:
                avg_time = sum(answer_times) / len(answer_times)
                if avg_time < 30:
                    speed_pattern = "fast_answerer"
                elif avg_time < 90:
                    speed_pattern = "moderate_answerer"
                else:
                    speed_pattern = "careful_answerer"
            else:
                speed_pattern = "unknown"

            # 分析正确率模式
            correct_count = sum(1 for r in records if r.is_correct)
            accuracy = correct_count / len(records) if records else 0

            if accuracy > 0.85:
                accuracy_pattern = "high_achiever"
            elif accuracy > 0.7:
                accuracy_pattern = "steady_learner"
            elif accuracy > 0.5:
                accuracy_pattern = "developing_learner"
            else:
                accuracy_pattern = "struggling_learner"

            # 分析答题一致性
            if len(answer_times) > 1:
                import statistics

                time_std = statistics.stdev(answer_times)
                consistency = 1 - min(1.0, time_std / avg_time) if avg_time > 0 else 0
            else:
                consistency = 0

            return {
                "answer_speed_pattern": speed_pattern,
                "accuracy_pattern": accuracy_pattern,
                "consistency_score": consistency,
                "average_answer_time": (
                    sum(answer_times) / len(answer_times) if answer_times else 0
                ),
                "accuracy_rate": accuracy,
            }

        except Exception as e:
            logger.error(f"分析行为模式失败: {str(e)}")
            return {"answer_speed_pattern": "unknown", "accuracy_pattern": "unknown"}

    def _analyze_difficulty_adaptation_patterns(
        self, sessions: list[Any], records: list[Any]
    ) -> dict[str, Any]:
        """分析难度适应模式."""
        try:
            if not sessions:
                return {
                    "adaptation_ability": "unknown",
                    "preferred_difficulty": "unknown",
                }

            # 按难度分组统计
            difficulty_stats = {}
            for session in sessions:
                difficulty = session.difficulty_level
                if difficulty not in difficulty_stats:
                    difficulty_stats[difficulty] = {
                        "sessions": 0,
                        "total_correct": 0,
                        "total_questions": 0,
                    }

                difficulty_stats[difficulty]["sessions"] += 1

                # 统计该会话的答题情况
                session_records = [r for r in records if r.session_id == session.id]
                difficulty_stats[difficulty]["total_questions"] += len(session_records)
                difficulty_stats[difficulty]["total_correct"] += sum(
                    1 for r in session_records if r.is_correct
                )

            # 计算各难度的正确率
            difficulty_accuracies = {}
            for difficulty, stats in difficulty_stats.items():
                if stats["total_questions"] > 0:
                    accuracy = stats["total_correct"] / stats["total_questions"]
                    difficulty_accuracies[difficulty] = accuracy

            # 确定适应能力
            if len(difficulty_accuracies) >= 2:
                accuracies: list[float] = list(difficulty_accuracies.values())
                if min(accuracies) > 0.7:
                    adaptation_ability = "excellent"
                elif min(accuracies) > 0.5:
                    adaptation_ability = "good"
                else:
                    adaptation_ability = "needs_improvement"
            else:
                adaptation_ability = "insufficient_data"

            # 确定偏好难度
            if difficulty_accuracies:
                preferred_difficulty = max(
                    difficulty_accuracies.keys(), key=lambda x: difficulty_accuracies[x]
                )
            else:
                preferred_difficulty = "elementary"

            return {
                "adaptation_ability": adaptation_ability,
                "preferred_difficulty": preferred_difficulty,
                "difficulty_accuracies": difficulty_accuracies,
                "difficulty_stats": difficulty_stats,
            }

        except Exception as e:
            logger.error(f"分析难度适应模式失败: {str(e)}")
            return {"adaptation_ability": "unknown", "preferred_difficulty": "unknown"}

    def _identify_learning_style(
        self, records: list[Any], sessions: list[Any]
    ) -> dict[str, Any]:
        """识别学习风格."""
        try:
            if not records or not sessions:
                return {"primary_style": "unknown", "confidence": 0}

            # 分析答题速度特征
            answer_times = [
                r.time_spent for r in records if r.time_spent and r.time_spent > 0
            ]
            avg_time = sum(answer_times) / len(answer_times) if answer_times else 60

            # 分析会话时长特征
            session_durations: list[float] = []
            for session in sessions:
                if session.end_time and session.start_time:
                    duration = (
                        session.end_time - session.start_time
                    ).total_seconds() / 60
                    session_durations.append(duration)

            avg_session_duration = (
                sum(session_durations) / len(session_durations)
                if session_durations
                else 30
            )

            # 分析正确率变化特征
            correct_count = sum(1 for r in records if r.is_correct)
            accuracy = correct_count / len(records) if records else 0

            # 基于特征判断学习风格
            style_scores = {
                "visual_learner": 0,
                "auditory_learner": 0,
                "kinesthetic_learner": 0,
                "sequential_learner": 0,
                "global_learner": 0,
                "analytical_learner": 0,
            }

            # 视觉学习者特征：快速答题，短会话
            if avg_time < 45 and avg_session_duration < 30:
                style_scores["visual_learner"] += 0.3

            # 听觉学习者特征：中等答题速度，中等会话时长
            if 45 <= avg_time <= 90 and 30 <= avg_session_duration <= 60:
                style_scores["auditory_learner"] += 0.3

            # 动觉学习者特征：较慢答题，长会话
            if avg_time > 90 and avg_session_duration > 60:
                style_scores["kinesthetic_learner"] += 0.3

            # 序列学习者特征：稳定的正确率
            if 0.7 <= accuracy <= 0.85:
                style_scores["sequential_learner"] += 0.2

            # 整体学习者特征：高正确率或低正确率（两极化）
            if accuracy > 0.85 or accuracy < 0.5:
                style_scores["global_learner"] += 0.2

            # 分析学习者特征：高正确率，快速答题
            if accuracy > 0.8 and avg_time < 60:
                style_scores["analytical_learner"] += 0.3

            # 确定主要学习风格
            primary_style = max(style_scores.keys(), key=lambda x: style_scores[x])
            confidence = style_scores[primary_style]

            return {
                "primary_style": primary_style,
                "confidence": confidence,
                "style_scores": style_scores,
                "characteristics": {
                    "average_answer_time": avg_time,
                    "average_session_duration": avg_session_duration,
                    "accuracy_rate": accuracy,
                },
            }

        except Exception as e:
            logger.error(f"识别学习风格失败: {str(e)}")
            return {"primary_style": "unknown", "confidence": 0}

    def _calculate_pattern_confidence(
        self,
        time_patterns: dict[str, Any],
        behavior_patterns: dict[str, Any],
        difficulty_patterns: dict[str, Any],
        learning_style: dict[str, Any],
    ) -> float:
        """计算模式识别置信度."""
        try:
            confidences = []

            # 时间模式置信度
            if time_patterns.get("optimal_learning_time") != "unknown":
                confidences.append(0.8)
            else:
                confidences.append(0.3)

            # 行为模式置信度
            if behavior_patterns.get("answer_speed_pattern") != "unknown":
                confidences.append(0.8)
            else:
                confidences.append(0.3)

            # 难度适应置信度
            if difficulty_patterns.get("adaptation_ability") != "unknown":
                confidences.append(0.8)
            else:
                confidences.append(0.3)

            # 学习风格置信度
            style_confidence = learning_style.get("confidence", 0)
            confidences.append(style_confidence)

            return sum(confidences) / len(confidences) if confidences else 0

        except Exception as e:
            logger.error(f"计算模式置信度失败: {str(e)}")
            return 0.5

    def _generate_pattern_summary(
        self,
        time_patterns: dict[str, Any],
        behavior_patterns: dict[str, Any],
        difficulty_patterns: dict[str, Any],
        learning_style: dict[str, Any],
    ) -> str:
        """生成模式总结."""
        try:
            summary_parts = []

            # 学习风格总结
            primary_style = learning_style.get("primary_style", "unknown")
            if primary_style != "unknown":
                style_names = {
                    "visual_learner": "视觉学习者",
                    "auditory_learner": "听觉学习者",
                    "kinesthetic_learner": "动觉学习者",
                    "sequential_learner": "序列学习者",
                    "global_learner": "整体学习者",
                    "analytical_learner": "分析学习者",
                }
                summary_parts.append(
                    f"主要学习风格：{style_names.get(primary_style, primary_style)}"
                )

            # 时间偏好总结
            optimal_time = time_patterns.get("optimal_learning_time", "unknown")
            if optimal_time != "unknown":
                time_names = {
                    "morning": "上午",
                    "afternoon": "下午",
                    "evening": "晚上",
                    "night": "深夜",
                }
                summary_parts.append(
                    f"最佳学习时间：{time_names.get(optimal_time, optimal_time)}"
                )

            # 答题特征总结
            speed_pattern = behavior_patterns.get("answer_speed_pattern", "unknown")
            if speed_pattern != "unknown":
                speed_names = {
                    "fast_answerer": "快速答题型",
                    "moderate_answerer": "稳健答题型",
                    "careful_answerer": "谨慎答题型",
                }
                summary_parts.append(
                    f"答题特征：{speed_names.get(speed_pattern, speed_pattern)}"
                )

            # 难度适应总结
            adaptation = difficulty_patterns.get("adaptation_ability", "unknown")
            if adaptation != "unknown":
                adaptation_names = {
                    "excellent": "优秀",
                    "good": "良好",
                    "needs_improvement": "需要改进",
                }
                summary_parts.append(
                    f"难度适应能力：{adaptation_names.get(adaptation, adaptation)}"
                )

            return "；".join(summary_parts) if summary_parts else "学习模式特征不明显"

        except Exception as e:
            logger.error(f"生成模式总结失败: {str(e)}")
            return "模式分析异常"

    def _analyze_by_knowledge_points(self, records: list[Any]) -> dict[str, Any]:
        """按知识点分组分析."""
        try:
            if not records:
                return {}

            # 按知识点分组（这里假设有knowledge_point字段，实际可能需要根据题目类型推断）
            knowledge_points: dict[str, dict[str, Any]] = {}

            for record in records:
                # 这里简化处理，实际应该根据题目内容或标签确定知识点
                point = getattr(record, "knowledge_point", "general")
                if point not in knowledge_points:
                    knowledge_points[point] = {
                        "total_attempts": 0,
                        "correct_attempts": 0,
                        "total_time": 0,
                        "attempts": [],
                    }

                point_data = knowledge_points[point]
                point_data["total_attempts"] += 1
                if record.is_correct:
                    point_data["correct_attempts"] += 1

                if record.time_spent:
                    point_data["total_time"] += record.time_spent

                point_data["attempts"].append(
                    {
                        "is_correct": record.is_correct,
                        "time_spent": record.time_spent,
                        "created_at": record.created_at,
                    }
                )

            # 计算每个知识点的统计信息
            for _point, data in knowledge_points.items():
                data["accuracy"] = (
                    data["correct_attempts"] / data["total_attempts"]
                    if data["total_attempts"] > 0
                    else 0
                )
                data["average_time"] = (
                    data["total_time"] / data["total_attempts"]
                    if data["total_attempts"] > 0
                    else 0
                )

                # 计算掌握度
                if data["accuracy"] >= 0.85:
                    data["mastery_level"] = "mastered"
                elif data["accuracy"] >= 0.7:
                    data["mastery_level"] = "proficient"
                elif data["accuracy"] >= 0.5:
                    data["mastery_level"] = "developing"
                else:
                    data["mastery_level"] = "struggling"

            return knowledge_points

        except Exception as e:
            logger.error(f"按知识点分析失败: {str(e)}")
            return {}

    def _classify_mastery_levels(
        self, knowledge_point_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """分类掌握度等级."""
        try:
            mastery_classification: dict[str, list[dict[str, Any]]] = {
                "mastered": [],
                "proficient": [],
                "developing": [],
                "struggling": [],
            }

            for point, data in knowledge_point_analysis.items():
                level = data.get("mastery_level", "struggling")
                mastery_classification[level].append(
                    {
                        "knowledge_point": point,
                        "accuracy": data.get("accuracy", 0),
                        "attempts": data.get("total_attempts", 0),
                        "average_time": data.get("average_time", 0),
                    }
                )

            # 计算各等级的统计信息
            total_points = len(knowledge_point_analysis)
            mastery_stats = {}
            for level, points in mastery_classification.items():
                count = len(points)
                percentage = count / total_points if total_points > 0 else 0
                mastery_stats[level] = {
                    "count": count,
                    "percentage": percentage,
                    "points": points,
                }

            return {
                "classification": mastery_classification,
                "statistics": mastery_stats,
                "total_knowledge_points": total_points,
            }

        except Exception as e:
            logger.error(f"分类掌握度等级失败: {str(e)}")
            return {}

    def _analyze_knowledge_retention(self, records: list[Any]) -> dict[str, Any]:
        """分析知识保持情况."""
        try:
            if not records:
                return {"retention_score": 0, "decay_analysis": {}}

            # 按时间排序
            sorted_records = sorted(records, key=lambda x: x.created_at)

            # 分析知识遗忘曲线
            retention_data: dict[str, list[dict[str, Any]]] = {}
            decay_days = self.analysis_config["knowledge_mastery"][
                "knowledge_decay_days"
            ]

            # 按知识点分析保持情况
            for record in sorted_records:
                point = getattr(record, "knowledge_point", "general")
                if point not in retention_data:
                    retention_data[point] = []

                retention_data[point].append(
                    {
                        "date": record.created_at.date(),
                        "is_correct": record.is_correct,
                        "time_spent": record.time_spent,
                    }
                )

            # 计算保持分数
            retention_scores = {}
            for point, data in retention_data.items():
                if len(data) < 2:
                    retention_scores[point] = 0.5  # 数据不足
                    continue

                # 计算最近表现与早期表现的对比
                recent_data = [
                    d
                    for d in data
                    if (datetime.now().date() - d["date"]).days <= decay_days
                ]
                early_data = [
                    d
                    for d in data
                    if (datetime.now().date() - d["date"]).days > decay_days
                ]

                if not recent_data or not early_data:
                    retention_scores[point] = 0.5
                    continue

                recent_accuracy = sum(1 for d in recent_data if d["is_correct"]) / len(
                    recent_data
                )
                early_accuracy = sum(1 for d in early_data if d["is_correct"]) / len(
                    early_data
                )

                # 保持分数 = 最近正确率 / 早期正确率
                retention_scores[point] = (
                    recent_accuracy / early_accuracy if early_accuracy > 0 else 0.5
                )

            # 计算整体保持分数
            overall_retention = (
                sum(retention_scores.values()) / len(retention_scores)
                if retention_scores
                else 0
            )

            return {
                "retention_score": overall_retention,
                "knowledge_point_retention": retention_scores,
                "decay_analysis": {
                    "decay_period_days": decay_days,
                    "points_with_decay": [
                        k for k, v in retention_scores.items() if v < 0.8
                    ],
                    "points_well_retained": [
                        k for k, v in retention_scores.items() if v >= 0.8
                    ],
                },
            }

        except Exception as e:
            logger.error(f"分析知识保持失败: {str(e)}")
            return {"retention_score": 0, "decay_analysis": {}}

    def _assess_learning_progress(self, records: list[Any]) -> dict[str, Any]:
        """评估学习进度."""
        try:
            if not records:
                return {"progress_rate": 0, "trend": "unknown"}

            # 按时间排序
            sorted_records = sorted(records, key=lambda x: x.created_at)

            # 分时间段分析进步情况
            total_days = (
                sorted_records[-1].created_at - sorted_records[0].created_at
            ).days
            if total_days < 1:
                return {"progress_rate": 0, "trend": "insufficient_data"}

            # 将记录分为前半段和后半段
            mid_point = len(sorted_records) // 2
            early_records: list[Any] = sorted_records[:mid_point]
            recent_records: list[Any] = sorted_records[mid_point:]

            # 计算各阶段的表现
            early_accuracy = (
                sum(1 for r in early_records if r.is_correct) / len(early_records)
                if early_records
                else 0
            )
            recent_accuracy = (
                sum(1 for r in recent_records if r.is_correct) / len(recent_records)
                if recent_records
                else 0
            )

            early_avg_time = (
                sum(r.time_spent for r in early_records if r.time_spent)
                / len([r for r in early_records if r.time_spent])
                if any(r.time_spent for r in early_records)
                else 0
            )
            recent_avg_time = (
                sum(r.time_spent for r in recent_records if r.time_spent)
                / len([r for r in recent_records if r.time_spent])
                if any(r.time_spent for r in recent_records)
                else 0
            )

            # 计算进步率
            accuracy_improvement = recent_accuracy - early_accuracy
            speed_improvement = (
                (early_avg_time - recent_avg_time) / early_avg_time
                if early_avg_time > 0
                else 0
            )

            # 综合进步评分
            progress_rate = (accuracy_improvement + speed_improvement * 0.5) / 1.5

            # 确定趋势
            if progress_rate > 0.1:
                trend = "improving"
            elif progress_rate < -0.1:
                trend = "declining"
            else:
                trend = "stable"

            return {
                "progress_rate": progress_rate,
                "trend": trend,
                "accuracy_improvement": accuracy_improvement,
                "speed_improvement": speed_improvement,
                "early_performance": {
                    "accuracy": early_accuracy,
                    "average_time": early_avg_time,
                },
                "recent_performance": {
                    "accuracy": recent_accuracy,
                    "average_time": recent_avg_time,
                },
            }

        except Exception as e:
            logger.error(f"评估学习进度失败: {str(e)}")
            return {"progress_rate": 0, "trend": "unknown"}

    def _identify_weak_areas(
        self, knowledge_point_analysis: dict[str, Any]
    ) -> list[str]:
        """识别薄弱环节."""
        try:
            weak_areas = []

            for point, data in knowledge_point_analysis.items():
                accuracy = data.get("accuracy", 0)
                attempts = data.get("total_attempts", 0)

                # 判断薄弱环节的条件：正确率低于60%且尝试次数足够
                if accuracy < 0.6 and attempts >= 3:
                    weak_areas.append(point)
                # 或者正确率低于40%（无论尝试次数）
                elif accuracy < 0.4:
                    weak_areas.append(point)

            return weak_areas

        except Exception as e:
            logger.error(f"识别薄弱环节失败: {str(e)}")
            return []

    def _calculate_mastery_confidence(
        self,
        knowledge_point_analysis: dict[str, Any],
        retention_analysis: dict[str, Any],
        progress_assessment: dict[str, Any],
    ) -> float:
        """计算掌握度置信度."""
        try:
            confidence_factors = []

            # 知识点分析置信度
            if knowledge_point_analysis:
                total_attempts = sum(
                    data.get("total_attempts", 0)
                    for data in knowledge_point_analysis.values()
                )
                if total_attempts >= 20:
                    confidence_factors.append(0.9)
                elif total_attempts >= 10:
                    confidence_factors.append(0.7)
                else:
                    confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.3)

            # 保持分析置信度
            retention_score = retention_analysis.get("retention_score", 0)
            if retention_score > 0:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.4)

            # 进度评估置信度
            trend = progress_assessment.get("trend", "unknown")
            if trend != "unknown":
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.4)

            return (
                sum(confidence_factors) / len(confidence_factors)
                if confidence_factors
                else 0
            )

        except Exception as e:
            logger.error(f"计算掌握度置信度失败: {str(e)}")
            return 0.5

    def _calculate_overall_mastery_score(self, mastery_levels: dict[str, Any]) -> float:
        """计算整体掌握度分数."""
        try:
            stats = mastery_levels.get("statistics", {})

            # 权重分配
            weights = {
                "mastered": 1.0,
                "proficient": 0.8,
                "developing": 0.6,
                "struggling": 0.3,
            }

            total_score = 0
            total_points = 0

            for level, weight in weights.items():
                level_stats = stats.get(level, {})
                count = level_stats.get("count", 0)
                total_score += count * weight
                total_points += count

            return total_score / total_points if total_points > 0 else 0

        except Exception as e:
            logger.error(f"计算整体掌握度分数失败: {str(e)}")
            return 0

    def _analyze_accuracy_efficiency(self, records: list[Any]) -> dict[str, Any]:
        """分析准确率效率."""
        try:
            if not records:
                return {"efficiency_score": 0, "accuracy_trend": "unknown"}

            # 计算整体准确率
            correct_count = sum(1 for r in records if r.is_correct)
            total_count = len(records)
            overall_accuracy = correct_count / total_count if total_count > 0 else 0

            # 分析准确率趋势
            if len(records) >= 10:
                recent_10 = records[:10]
                earlier_10 = records[10:20] if len(records) >= 20 else records[10:]

                recent_accuracy = sum(1 for r in recent_10 if r.is_correct) / len(
                    recent_10
                )
                earlier_accuracy = (
                    sum(1 for r in earlier_10 if r.is_correct) / len(earlier_10)
                    if earlier_10
                    else recent_accuracy
                )

                if recent_accuracy > earlier_accuracy + 0.1:
                    trend = "improving"
                elif recent_accuracy < earlier_accuracy - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            # 计算效率分数 (准确率 * 一致性因子)
            accuracy_variance = 0
            if len(records) >= 5:
                # 计算最近5次的准确率方差
                recent_results = [1 if r.is_correct else 0 for r in records[:5]]
                mean_recent = sum(recent_results) / len(recent_results)
                accuracy_variance = sum(
                    (x - mean_recent) ** 2 for x in recent_results
                ) / len(recent_results)

            consistency_factor = max(0.5, 1 - accuracy_variance)
            efficiency_score = overall_accuracy * consistency_factor

            return {
                "efficiency_score": efficiency_score,
                "overall_accuracy": overall_accuracy,
                "accuracy_trend": trend,
                "consistency_factor": consistency_factor,
                "recent_accuracy": (
                    sum(1 for r in records[:10] if r.is_correct) / min(10, len(records))
                    if records
                    else 0
                ),
                "confidence": min(1.0, len(records) / 20),
            }

        except Exception as e:
            logger.error(f"分析准确率效率失败: {str(e)}")
            return {"efficiency_score": 0, "accuracy_trend": "unknown"}

    def _analyze_speed_efficiency(self, records: list[Any]) -> dict[str, Any]:
        """分析速度效率."""
        try:
            if not records:
                return {"efficiency_score": 0, "speed_trend": "unknown"}

            # 获取有效的答题时间
            valid_times = [
                r.time_spent for r in records if r.time_spent and r.time_spent > 0
            ]
            if not valid_times:
                return {"efficiency_score": 0, "speed_trend": "unknown"}

            # 计算平均答题时间
            avg_time = sum(valid_times) / len(valid_times)

            # 分析速度趋势
            if len(valid_times) >= 10:
                recent_times = valid_times[:10]
                earlier_times = (
                    valid_times[10:20] if len(valid_times) >= 20 else valid_times[10:]
                )

                recent_avg = sum(recent_times) / len(recent_times)
                earlier_avg = (
                    sum(earlier_times) / len(earlier_times)
                    if earlier_times
                    else recent_avg
                )

                if recent_avg < earlier_avg * 0.9:
                    trend = "accelerating"
                elif recent_avg > earlier_avg * 1.1:
                    trend = "decelerating"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            # 计算速度效率分数 (基于理想时间范围)
            ideal_time_range = (30, 120)  # 30-120秒为理想范围
            if ideal_time_range[0] <= avg_time <= ideal_time_range[1]:
                speed_efficiency = 1.0
            elif avg_time < ideal_time_range[0]:
                # 太快可能影响准确率
                speed_efficiency = 0.8
            else:
                # 太慢效率低
                speed_efficiency = max(0.3, ideal_time_range[1] / avg_time)

            # 考虑一致性
            if len(valid_times) >= 5:
                import statistics

                time_std = statistics.stdev(valid_times[:5])
                consistency_factor = max(0.5, 1 - min(1.0, time_std / avg_time))
            else:
                consistency_factor = 0.8

            efficiency_score = speed_efficiency * consistency_factor

            return {
                "efficiency_score": efficiency_score,
                "average_time": avg_time,
                "speed_trend": trend,
                "consistency_factor": consistency_factor,
                "ideal_range": ideal_time_range,
                "confidence": min(1.0, len(valid_times) / 20),
            }

        except Exception as e:
            logger.error(f"分析速度效率失败: {str(e)}")
            return {"efficiency_score": 0, "speed_trend": "unknown"}

    def _analyze_learning_consistency(self, records: list[Any]) -> dict[str, Any]:
        """分析学习一致性."""
        try:
            if not records:
                return {"consistency_score": 0, "pattern": "unknown"}

            # 分析答题时间一致性
            valid_times = [
                r.time_spent for r in records if r.time_spent and r.time_spent > 0
            ]
            time_consistency = 0
            if len(valid_times) >= 3:
                import statistics

                avg_time = sum(valid_times) / len(valid_times)
                time_std = statistics.stdev(valid_times)
                time_consistency = (
                    max(0, 1 - min(1.0, time_std / avg_time)) if avg_time > 0 else 0
                )

            # 分析正确率一致性
            accuracy_consistency = 0
            if len(records) >= 10:
                # 将记录分为5个区间，计算每个区间的正确率
                chunk_size = len(records) // 5
                chunk_accuracies = []
                for i in range(5):
                    start_idx = i * chunk_size
                    end_idx = start_idx + chunk_size if i < 4 else len(records)
                    chunk = records[start_idx:end_idx]
                    chunk_accuracy = (
                        sum(1 for r in chunk if r.is_correct) / len(chunk)
                        if chunk
                        else 0
                    )
                    chunk_accuracies.append(chunk_accuracy)

                if chunk_accuracies:
                    import statistics

                    accuracy_std = statistics.stdev(chunk_accuracies)
                    accuracy_consistency = max(
                        0, 1 - min(1.0, accuracy_std / 0.5)
                    )  # 标准化到0.5

            # 综合一致性分数
            consistency_score = time_consistency * 0.4 + accuracy_consistency * 0.6

            # 确定一致性模式
            if consistency_score >= 0.8:
                pattern = "highly_consistent"
            elif consistency_score >= 0.6:
                pattern = "moderately_consistent"
            elif consistency_score >= 0.4:
                pattern = "somewhat_inconsistent"
            else:
                pattern = "highly_inconsistent"

            return {
                "consistency_score": consistency_score,
                "time_consistency": time_consistency,
                "accuracy_consistency": accuracy_consistency,
                "pattern": pattern,
                "confidence": min(1.0, len(records) / 30),
            }

        except Exception as e:
            logger.error(f"分析学习一致性失败: {str(e)}")
            return {"consistency_score": 0, "pattern": "unknown"}

    def _analyze_progress_rate(
        self, records: list[Any], sessions: list[Any]
    ) -> dict[str, Any]:
        """分析进步速度."""
        try:
            if not records or not sessions:
                return {"progress_rate": 0, "trend": "unknown"}

            # 按时间排序
            sorted_records = sorted(records, key=lambda x: x.created_at)
            # sorted_sessions = sorted(sessions, key=lambda x: x.created_at)  # 暂时不使用

            # 计算时间跨度
            if len(sorted_records) < 2:
                return {"progress_rate": 0, "trend": "insufficient_data"}

            time_span = (
                sorted_records[-1].created_at - sorted_records[0].created_at
            ).total_seconds() / 86400  # 天数

            # 分时间段分析进步
            if len(sorted_records) >= 20:
                # 分为前后两半
                mid_point = len(sorted_records) // 2
                early_records = sorted_records[:mid_point]
                recent_records = sorted_records[mid_point:]

                # 计算各阶段表现
                early_accuracy = sum(1 for r in early_records if r.is_correct) / len(
                    early_records
                )
                recent_accuracy = sum(1 for r in recent_records if r.is_correct) / len(
                    recent_records
                )

                # 计算平均答题时间变化
                early_times = [
                    r.time_spent
                    for r in early_records
                    if r.time_spent and r.time_spent > 0
                ]
                recent_times = [
                    r.time_spent
                    for r in recent_records
                    if r.time_spent and r.time_spent > 0
                ]

                early_avg_time = (
                    sum(early_times) / len(early_times) if early_times else 0
                )
                recent_avg_time = (
                    sum(recent_times) / len(recent_times) if recent_times else 0
                )

                # 计算进步率
                accuracy_improvement = recent_accuracy - early_accuracy
                speed_improvement = (
                    (early_avg_time - recent_avg_time) / early_avg_time
                    if early_avg_time > 0
                    else 0
                )

                # 综合进步率 (准确率权重0.7，速度权重0.3)
                progress_rate = accuracy_improvement * 0.7 + speed_improvement * 0.3

                # 确定趋势
                if progress_rate > 0.05:
                    trend = "rapid_improvement"
                elif progress_rate > 0.02:
                    trend = "steady_improvement"
                elif progress_rate > -0.02:
                    trend = "stable"
                elif progress_rate > -0.05:
                    trend = "slight_decline"
                else:
                    trend = "significant_decline"

                # 计算日均进步率
                daily_progress_rate = (
                    progress_rate / max(1, time_span) if time_span > 0 else 0
                )

                return {
                    "progress_rate": progress_rate,
                    "daily_progress_rate": daily_progress_rate,
                    "trend": trend,
                    "accuracy_improvement": accuracy_improvement,
                    "speed_improvement": speed_improvement,
                    "time_span_days": time_span,
                    "confidence": min(1.0, len(sorted_records) / 50),
                }
            else:
                return {"progress_rate": 0, "trend": "insufficient_data"}

        except Exception as e:
            logger.error(f"分析进步速度失败: {str(e)}")
            return {"progress_rate": 0, "trend": "unknown"}

    def _determine_efficiency_level(self, overall_efficiency: float) -> str:
        """确定效率等级."""
        try:
            if overall_efficiency >= 0.9:
                return "excellent"
            elif overall_efficiency >= 0.8:
                return "very_good"
            elif overall_efficiency >= 0.7:
                return "good"
            elif overall_efficiency >= 0.6:
                return "fair"
            elif overall_efficiency >= 0.5:
                return "poor"
            else:
                return "very_poor"

        except Exception as e:
            logger.error(f"确定效率等级失败: {str(e)}")
            return "unknown"

    def _generate_efficiency_improvement_suggestions(
        self,
        accuracy_efficiency: dict[str, Any],
        speed_efficiency: dict[str, Any],
        consistency_analysis: dict[str, Any],
        progress_rate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """生成效率改进建议."""
        try:
            suggestions = []

            # 基于准确率效率的建议
            accuracy_score = accuracy_efficiency.get("efficiency_score", 0)
            accuracy_trend = accuracy_efficiency.get("accuracy_trend", "unknown")

            if accuracy_score < 0.6:
                suggestions.append(
                    {
                        "type": "accuracy_improvement",
                        "priority": "high",
                        "suggestion": "建议加强基础知识练习，重点关注错误率较高的题型",
                        "reason": f"当前准确率效率较低 ({accuracy_score:.2f})",
                        "action_items": [
                            "复习基础语法和词汇",
                            "针对错误题型进行专项练习",
                            "降低答题速度，提高准确率",
                        ],
                    }
                )

            if accuracy_trend == "declining":
                suggestions.append(
                    {
                        "type": "accuracy_trend",
                        "priority": "high",
                        "suggestion": "注意到准确率呈下降趋势，建议暂停新内容学习，巩固已学知识",
                        "reason": "准确率趋势下降",
                        "action_items": [
                            "回顾最近的错误题目",
                            "加强薄弱知识点练习",
                            "适当休息，避免疲劳学习",
                        ],
                    }
                )

            # 基于速度效率的建议
            speed_score = speed_efficiency.get("efficiency_score", 0)
            avg_time = speed_efficiency.get("average_time", 0)
            ideal_range = speed_efficiency.get("ideal_range", (30, 120))

            if speed_score < 0.6:
                if avg_time > ideal_range[1]:
                    suggestions.append(
                        {
                            "type": "speed_improvement",
                            "priority": "medium",
                            "suggestion": "答题速度偏慢，建议进行限时练习提高答题效率",
                            "reason": f"平均答题时间 {avg_time:.1f}秒，超出理想范围",
                            "action_items": [
                                "进行限时练习",
                                "提高阅读速度",
                                "熟练掌握常见题型解题技巧",
                            ],
                        }
                    )
                elif avg_time < ideal_range[0]:
                    suggestions.append(
                        {
                            "type": "accuracy_focus",
                            "priority": "medium",
                            "suggestion": "答题速度过快，建议放慢速度，仔细审题",
                            "reason": f"平均答题时间 {avg_time:.1f}秒，过于匆忙",
                            "action_items": [
                                "仔细阅读题目要求",
                                "检查答案准确性",
                                "避免急躁情绪",
                            ],
                        }
                    )

            # 基于一致性的建议
            consistency_score = consistency_analysis.get("consistency_score", 0)
            pattern = consistency_analysis.get("pattern", "unknown")

            if consistency_score < 0.5:
                suggestions.append(
                    {
                        "type": "consistency_improvement",
                        "priority": "medium",
                        "suggestion": "学习表现不够稳定，建议建立规律的学习习惯",
                        "reason": f"一致性分数较低 ({consistency_score:.2f})，表现为{pattern}",
                        "action_items": [
                            "制定固定的学习时间表",
                            "保持良好的学习环境",
                            "避免在疲劳或分心时学习",
                        ],
                    }
                )

            # 基于进步率的建议
            progress_trend = progress_rate.get("trend", "unknown")
            progress_value = progress_rate.get("progress_rate", 0)

            if progress_trend in ["stable", "slight_decline", "significant_decline"]:
                suggestions.append(
                    {
                        "type": "progress_enhancement",
                        "priority": (
                            "high"
                            if progress_trend == "significant_decline"
                            else "medium"
                        ),
                        "suggestion": "学习进步缓慢，建议调整学习策略和方法",
                        "reason": f"进步趋势: {progress_trend}，进步率: {progress_value:.3f}",
                        "action_items": [
                            "尝试新的学习方法",
                            "增加练习难度或题量",
                            "寻求老师或同学的帮助",
                        ],
                    }
                )

            # 如果没有明显问题，给出积极建议
            if not suggestions:
                suggestions.append(
                    {
                        "type": "maintenance",
                        "priority": "low",
                        "suggestion": "当前学习效率良好，建议保持现有学习节奏",
                        "reason": "各项效率指标表现良好",
                        "action_items": [
                            "继续保持当前学习方法",
                            "适当增加挑战性内容",
                            "定期回顾和总结",
                        ],
                    }
                )

            return suggestions

        except Exception as e:
            logger.error(f"生成效率改进建议失败: {str(e)}")
            return []
