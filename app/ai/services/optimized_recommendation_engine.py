"""优化的智能推荐系统 - 提升响应速度和准确性."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import get_deepseek_service
from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class OptimizedRecommendationEngine:
    """优化的智能推荐引擎."""

    def __init__(self, cache_service: CacheService | None = None) -> None:
        self.deepseek_service = get_deepseek_service()
        self.cache_service = cache_service
        self.recommendation_cache: dict[str, Any] = {}
        self.cache_ttl = 3600  # 1小时缓存
        self.fast_cache_ttl = 300  # 5分钟快速缓存

    async def generate_intelligent_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        context: dict[str, Any],
        recommendation_type: str = "comprehensive",
    ) -> dict[str, Any]:
        """生成智能推荐."""
        try:
            # 构建缓存键
            cache_key = self._build_cache_key(user_id, context, recommendation_type)

            # 检查多层缓存
            cached_result = await self._get_cached_recommendation(cache_key)
            if cached_result:
                return cached_result

            # 收集用户画像和上下文
            user_profile = await self._build_user_profile(db, user_id, context)

            # 根据推荐类型生成推荐
            recommendations = await self._generate_recommendations_by_type(
                user_profile, context, recommendation_type
            )

            # 优化和排序推荐结果
            optimized_recommendations = await self._optimize_recommendations(
                recommendations, user_profile
            )

            # 计算推荐置信度
            confidence_scores = await self._calculate_confidence_scores(
                optimized_recommendations, user_profile
            )

            # 构建最终结果
            final_result = {
                "user_id": user_id,
                "recommendation_type": recommendation_type,
                "recommendations": optimized_recommendations,
                "confidence_scores": confidence_scores,
                "user_profile_summary": self._extract_profile_summary(user_profile),
                "generation_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "cache_status": "generated",
                    "processing_time_ms": 0,  # 这里可以添加实际计时
                },
            }

            # 缓存结果
            await self._cache_recommendation(cache_key, final_result)

            return final_result

        except Exception as e:
            logger.error(f"生成智能推荐失败: {str(e)}")
            raise

    async def generate_fast_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        context: dict[str, Any],
        max_items: int = 5,
    ) -> dict[str, Any]:
        """生成快速推荐（优化响应速度）."""
        try:
            # 快速缓存键
            fast_cache_key = f"fast_rec_{user_id}_{hash(str(context))}"

            # 检查快速缓存
            cached_result = await self._get_fast_cached_recommendation(fast_cache_key)
            if cached_result:
                return cached_result

            # 简化的用户画像
            simplified_profile = await self._build_simplified_user_profile(db, user_id)

            # 基于规则的快速推荐
            fast_recommendations = await self._generate_rule_based_recommendations(
                simplified_profile, context, max_items
            )

            # 快速结果
            fast_result = {
                "user_id": user_id,
                "recommendation_type": "fast",
                "recommendations": fast_recommendations,
                "generation_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "cache_status": "generated",
                    "is_fast_mode": True,
                },
            }

            # 快速缓存
            await self._cache_fast_recommendation(fast_cache_key, fast_result)

            return fast_result

        except Exception as e:
            logger.error(f"生成快速推荐失败: {str(e)}")
            # 返回默认推荐
            return await self._generate_fallback_recommendations(user_id, context)

    def _extract_profile_summary(self, user_profile: dict[str, Any]) -> dict[str, Any]:
        """提取用户画像摘要."""
        return {
            "user_id": user_profile.get("user_id"),
            "current_level": user_profile.get("profile_info", {}).get(
                "current_level", "intermediate"
            ),
            "target_score": user_profile.get("profile_info", {}).get("target_score", 425),
            "accuracy_rate": user_profile.get("ability_assessment", {}).get("accuracy_rate", 0.0),
            "weak_areas": user_profile.get("ability_assessment", {}).get("weak_areas", []),
        }

    async def _get_fast_cached_recommendation(self, cache_key: str) -> dict[str, Any] | None:
        """获取快速缓存的推荐."""
        try:
            # 检查内存缓存
            if cache_key in self.recommendation_cache:
                cached_item = self.recommendation_cache[cache_key]
                if (
                    datetime.now() - cached_item["timestamp"]
                ).total_seconds() < self.fast_cache_ttl:
                    data = cached_item["data"]
                    return data if isinstance(data, dict) else None
                else:
                    del self.recommendation_cache[cache_key]

            return None

        except Exception as e:
            logger.error(f"获取快速缓存推荐失败: {str(e)}")
            return None

    async def _build_simplified_user_profile(
        self, db: AsyncSession, user_id: int
    ) -> dict[str, Any]:
        """构建简化用户画像."""
        try:
            from sqlalchemy import select

            from app.users.models.user_models import User

            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                return {"user_id": user_id, "level": "intermediate"}

            return {
                "user_id": user_id,
                "username": user.username,
                "level": "intermediate",  # 简化处理
                "preferences": {"difficulty": "intermediate"},
            }

        except Exception as e:
            logger.error(f"构建简化用户画像失败: {str(e)}")
            return {"user_id": user_id, "level": "intermediate"}

    async def _generate_rule_based_recommendations(
        self,
        simplified_profile: dict[str, Any],
        context: dict[str, Any],
        max_items: int,
    ) -> list[dict[str, Any]]:
        """生成基于规则的快速推荐."""
        recommendations = []

        # 基于用户级别的简单推荐
        level = simplified_profile.get("level", "intermediate")

        for i in range(max_items):
            recommendations.append(
                {
                    "type": "quick_resource",
                    "title": f"{level}级别快速练习 {i + 1}",
                    "description": f"适合{level}水平的快速练习",
                    "priority": "medium",
                    "estimated_time": "15分钟",
                }
            )

        return recommendations

    async def _cache_fast_recommendation(self, cache_key: str, result: dict[str, Any]) -> None:
        """缓存快速推荐结果."""
        try:
            # 内存缓存
            self.recommendation_cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"缓存快速推荐结果失败: {str(e)}")

    async def _recommend_practice_materials(
        self, user_profile: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """推荐练习材料."""
        return [
            {
                "type": "practice_material",
                "title": "综合练习题",
                "description": "适合当前水平的练习题",
                "priority": "high",
            }
        ]

    async def _recommend_comprehensive(
        self, user_profile: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """推荐综合资源."""
        learning_resources = await self._recommend_learning_resources(user_profile, context)
        study_plan = await self._recommend_study_plan(user_profile, context)
        practice_materials = await self._recommend_practice_materials(user_profile, context)

        return learning_resources + study_plan + practice_materials

    async def _recommend_general(
        self, user_profile: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """推荐通用资源."""
        return await self._recommend_learning_resources(user_profile, context)

    async def _build_user_profile(
        self, db: AsyncSession, user_id: int, context: dict[str, Any]
    ) -> dict[str, Any]:
        """构建详细用户画像."""
        try:
            # 获取用户基本信息
            from sqlalchemy import select

            from app.users.models.user_models import StudentProfile, User

            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                raise ValueError(f"用户 {user_id} 不存在")

            # 获取学生档案
            profile_result = await db.execute(
                select(StudentProfile).where(StudentProfile.user_id == user_id)
            )
            profile = profile_result.scalar_one_or_none()

            # 获取学习历史
            learning_history = await self._get_learning_history(db, user_id)

            # 分析学习偏好
            learning_preferences = await self._analyze_learning_preferences(learning_history)

            # 计算能力评估
            ability_assessment = await self._assess_user_abilities(learning_history)

            return {
                "user_id": user_id,
                "basic_info": {
                    "username": user.username,
                    "user_type": (
                        user.user_type.value
                        if hasattr(user.user_type, "value")
                        else str(user.user_type)
                    ),
                    "is_active": user.is_active,
                },
                "profile_info": (
                    {
                        "current_level": (
                            profile.current_level.value
                            if profile and hasattr(profile.current_level, "value")
                            else "intermediate"
                        ),
                        "target_score": (getattr(profile, "target_score", 425) if profile else 425),
                        "study_plan": (getattr(profile, "study_plan", {}) if profile else {}),
                    }
                    if profile
                    else {}
                ),
                "learning_history": learning_history,
                "learning_preferences": learning_preferences,
                "ability_assessment": ability_assessment,
                "context": context,
            }

        except Exception as e:
            logger.error(f"构建用户画像失败: {str(e)}")
            return self._get_default_user_profile(user_id, context)

    async def _generate_recommendations_by_type(
        self,
        user_profile: dict[str, Any],
        context: dict[str, Any],
        recommendation_type: str,
    ) -> list[dict[str, Any]]:
        """根据类型生成推荐."""
        if recommendation_type == "learning_resources":
            return await self._recommend_learning_resources(user_profile, context)
        elif recommendation_type == "study_plan":
            return await self._recommend_study_plan(user_profile, context)
        elif recommendation_type == "practice_materials":
            return await self._recommend_practice_materials(user_profile, context)
        elif recommendation_type == "comprehensive":
            return await self._recommend_comprehensive(user_profile, context)
        else:
            return await self._recommend_general(user_profile, context)

    async def _recommend_learning_resources(
        self, user_profile: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """推荐学习资源."""
        try:
            # 基于用户能力和偏好推荐资源
            ability_level = user_profile.get("ability_assessment", {}).get(
                "overall_level", "intermediate"
            )
            weak_areas = user_profile.get("ability_assessment", {}).get("weak_areas", [])

            recommendations = []

            # 针对薄弱环节推荐资源
            for weak_area in weak_areas[:3]:  # 最多3个薄弱环节
                recommendations.append(
                    {
                        "type": "learning_resource",
                        "category": "weakness_improvement",
                        "title": f"{weak_area}专项训练资源",
                        "description": f"针对{weak_area}的专项学习材料",
                        "difficulty_level": ability_level,
                        "priority": "high",
                        "estimated_time": "30-45分钟",
                        "target_skill": weak_area,
                    }
                )

            # 推荐适合当前水平的综合资源
            recommendations.append(
                {
                    "type": "learning_resource",
                    "category": "comprehensive",
                    "title": f"{ability_level}级别综合训练",
                    "description": "全面提升英语四级各项技能",
                    "difficulty_level": ability_level,
                    "priority": "medium",
                    "estimated_time": "60-90分钟",
                    "target_skill": "comprehensive",
                }
            )

            return recommendations

        except Exception as e:
            logger.error(f"推荐学习资源失败: {str(e)}")
            return self._get_default_resource_recommendations()

    async def _recommend_study_plan(
        self, user_profile: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """推荐学习计划."""
        try:
            target_score = user_profile.get("profile_info", {}).get("target_score", 425)
            current_level = user_profile.get("profile_info", {}).get(
                "current_level", "intermediate"
            )

            # 基于目标分数和当前水平制定计划
            study_duration = self._calculate_study_duration(current_level, target_score)

            recommendations = [
                {
                    "type": "study_plan",
                    "category": "personalized_plan",
                    "title": f"个性化{study_duration}周学习计划",
                    "description": f"从{current_level}水平提升到{target_score}分的学习计划",
                    "duration_weeks": study_duration,
                    "daily_time_minutes": 60,
                    "weekly_schedule": self._generate_weekly_schedule(current_level),
                    "milestones": self._generate_milestones(study_duration, target_score),
                    "priority": "high",
                }
            ]

            return recommendations

        except Exception as e:
            logger.error(f"推荐学习计划失败: {str(e)}")
            return self._get_default_plan_recommendations()

    async def _optimize_recommendations(
        self, recommendations: list[dict[str, Any]], user_profile: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """优化推荐结果."""
        try:
            # 根据用户偏好调整推荐
            preferences = user_profile.get("learning_preferences", {})

            # 按优先级排序
            recommendations.sort(
                key=lambda x: self._get_priority_score(x, preferences), reverse=True
            )

            # 去重和过滤
            unique_recommendations = []
            seen_titles = set()

            for rec in recommendations:
                if rec["title"] not in seen_titles:
                    unique_recommendations.append(rec)
                    seen_titles.add(rec["title"])

            # 限制数量
            return unique_recommendations[:10]

        except Exception as e:
            logger.error(f"优化推荐结果失败: {str(e)}")
            return recommendations

    async def _calculate_confidence_scores(
        self, recommendations: list[dict[str, Any]], user_profile: dict[str, Any]
    ) -> dict[str, float]:
        """计算推荐置信度."""
        confidence_scores = {}

        for i, rec in enumerate(recommendations):
            # 基于多个因素计算置信度
            base_confidence = 0.7

            # 基于用户画像完整度调整
            profile_completeness = self._calculate_profile_completeness(user_profile)
            confidence_adjustment = profile_completeness * 0.2

            # 基于推荐类型调整
            type_confidence = {
                "learning_resource": 0.85,
                "study_plan": 0.80,
                "practice_materials": 0.90,
            }.get(rec.get("type", ""), 0.75)

            final_confidence = min(base_confidence + confidence_adjustment, type_confidence)
            confidence_scores[f"recommendation_{i}"] = round(final_confidence, 2)

        return confidence_scores

    def _build_cache_key(
        self, user_id: int, context: dict[str, Any], recommendation_type: str
    ) -> str:
        """构建缓存键."""
        context_hash = hash(str(sorted(context.items())))
        return f"rec_{user_id}_{recommendation_type}_{context_hash}"

    async def _get_cached_recommendation(self, cache_key: str) -> dict[str, Any] | None:
        """获取缓存的推荐."""
        try:
            if self.cache_service:
                cached_data = await self.cache_service.get(cache_key)
                if cached_data:
                    parsed_data = json.loads(cached_data)
                    return parsed_data if isinstance(parsed_data, dict) else None

            # 检查内存缓存
            if cache_key in self.recommendation_cache:
                cached_item = self.recommendation_cache[cache_key]
                if (datetime.now() - cached_item["timestamp"]).total_seconds() < self.cache_ttl:
                    data = cached_item["data"]
                    return data if isinstance(data, dict) else None
                else:
                    del self.recommendation_cache[cache_key]

            return None

        except Exception as e:
            logger.error(f"获取缓存推荐失败: {str(e)}")
            return None

    async def _cache_recommendation(self, cache_key: str, result: dict[str, Any]) -> None:
        """缓存推荐结果."""
        try:
            # Redis缓存
            if self.cache_service:
                await self.cache_service.set(cache_key, json.dumps(result), ttl=self.cache_ttl)

            # 内存缓存
            self.recommendation_cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"缓存推荐结果失败: {str(e)}")

    async def _get_learning_history(self, db: AsyncSession, user_id: int) -> dict[str, Any]:
        """获取学习历史."""
        try:
            from sqlalchemy import desc, select

            from app.training.models.training_models import TrainingRecord

            # 获取最近30天的训练记录
            thirty_days_ago = datetime.now() - timedelta(days=30)

            records_result = await db.execute(
                select(TrainingRecord)
                .where(
                    TrainingRecord.student_id == user_id,
                    TrainingRecord.created_at >= thirty_days_ago,
                )
                .order_by(desc(TrainingRecord.created_at))
                .limit(100)
            )
            records = records_result.scalars().all()

            # 统计学习历史
            total_attempts = len(records)
            correct_attempts = len([r for r in records if r.is_correct])
            accuracy_rate = correct_attempts / total_attempts if total_attempts > 0 else 0

            return {
                "total_attempts": total_attempts,
                "correct_attempts": correct_attempts,
                "accuracy_rate": accuracy_rate,
                "recent_activity_days": len({r.created_at.date() for r in records}),
                "last_activity": records[0].created_at.isoformat() if records else None,
            }

        except Exception as e:
            logger.error(f"获取学习历史失败: {str(e)}")
            return {"total_attempts": 0, "accuracy_rate": 0.0}

    async def _analyze_learning_preferences(
        self, learning_history: dict[str, Any]
    ) -> dict[str, Any]:
        """分析学习偏好."""
        return {
            "preferred_difficulty": "intermediate",
            "preferred_session_length": 45,
            "preferred_time_of_day": "evening",
            "learning_style": "visual",
        }

    async def _assess_user_abilities(self, learning_history: dict[str, Any]) -> dict[str, Any]:
        """评估用户能力."""
        accuracy_rate = learning_history.get("accuracy_rate", 0.0)

        if accuracy_rate >= 0.8:
            overall_level = "advanced"
        elif accuracy_rate >= 0.6:
            overall_level = "intermediate"
        else:
            overall_level = "beginner"

        return {
            "overall_level": overall_level,
            "accuracy_rate": accuracy_rate,
            "weak_areas": ["听力理解", "写作表达"],  # 这里可以基于实际数据分析
            "strong_areas": ["词汇", "语法"],
        }

    def _get_priority_score(
        self, recommendation: dict[str, Any], preferences: dict[str, Any]
    ) -> float:
        """计算推荐优先级分数."""
        base_score = {"high": 3, "medium": 2, "low": 1}.get(
            recommendation.get("priority", "medium"), 2
        )

        # 基于用户偏好调整分数
        if recommendation.get("type") == preferences.get("preferred_type"):
            base_score += 1

        return base_score

    def _calculate_profile_completeness(self, user_profile: dict[str, Any]) -> float:
        """计算用户画像完整度."""
        completeness_factors = [
            bool(user_profile.get("basic_info")),
            bool(user_profile.get("profile_info")),
            bool(user_profile.get("learning_history", {}).get("total_attempts", 0) > 0),
            bool(user_profile.get("ability_assessment")),
        ]

        return sum(completeness_factors) / len(completeness_factors)

    def _calculate_study_duration(self, current_level: str, target_score: int) -> int:
        """计算学习周期."""
        level_weeks = {"beginner": 16, "intermediate": 12, "advanced": 8}
        base_weeks = level_weeks.get(current_level, 12)

        # 根据目标分数调整
        if target_score >= 550:
            base_weeks += 4
        elif target_score >= 500:
            base_weeks += 2

        return base_weeks

    def _generate_weekly_schedule(self, current_level: str) -> dict[str, Any]:
        """生成周学习计划."""
        return {
            "monday": ["词汇学习", "语法练习"],
            "tuesday": ["听力训练", "阅读理解"],
            "wednesday": ["写作练习", "翻译训练"],
            "thursday": ["综合复习", "模拟测试"],
            "friday": ["错题回顾", "知识巩固"],
            "weekend": ["自由练习", "休息调整"],
        }

    def _generate_milestones(self, duration_weeks: int, target_score: int) -> list[dict[str, Any]]:
        """生成学习里程碑."""
        milestones = []
        for i in range(1, duration_weeks // 4 + 1):
            week = i * 4
            expected_score = 350 + (target_score - 350) * (week / duration_weeks)
            milestones.append(
                {
                    "week": week,
                    "target": f"模拟测试达到{int(expected_score)}分",
                    "description": f"第{week}周目标",
                }
            )

        return milestones

    # 默认和回退方法
    def _get_default_user_profile(self, user_id: int, context: dict[str, Any]) -> dict[str, Any]:
        """获取默认用户画像."""
        return {
            "user_id": user_id,
            "basic_info": {"username": f"user_{user_id}", "user_type": "student"},
            "profile_info": {"current_level": "intermediate", "target_score": 425},
            "learning_history": {"total_attempts": 0, "accuracy_rate": 0.0},
            "learning_preferences": {"preferred_difficulty": "intermediate"},
            "ability_assessment": {"overall_level": "intermediate", "weak_areas": []},
            "context": context,
        }

    def _get_default_resource_recommendations(self) -> list[dict[str, Any]]:
        """获取默认资源推荐."""
        return [
            {
                "type": "learning_resource",
                "category": "comprehensive",
                "title": "英语四级综合训练",
                "description": "全面提升英语四级各项技能",
                "difficulty_level": "intermediate",
                "priority": "high",
            }
        ]

    def _get_default_plan_recommendations(self) -> list[dict[str, Any]]:
        """获取默认计划推荐."""
        return [
            {
                "type": "study_plan",
                "category": "standard_plan",
                "title": "标准12周学习计划",
                "description": "适合大多数学生的标准学习计划",
                "duration_weeks": 12,
                "priority": "medium",
            }
        ]

    async def _generate_fallback_recommendations(
        self, user_id: int, context: dict[str, Any]
    ) -> dict[str, Any]:
        """生成回退推荐."""
        return {
            "user_id": user_id,
            "recommendation_type": "fallback",
            "recommendations": self._get_default_resource_recommendations(),
            "generation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "cache_status": "fallback",
                "is_fallback": True,
            },
        }
