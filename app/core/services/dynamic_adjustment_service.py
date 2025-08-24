"""
动态调整机制服务 - 需求18验收标准2实现
教案自动演进、智能题目生成、反馈周期、历史追踪
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import DeepSeekService
from app.shared.models.enums import CacheType
from app.shared.services.cache_service import CacheService
from app.shared.utils.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)


class DynamicAdjustmentService:
    """动态调整机制服务 - 需求18验收标准2实现."""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
        ai_service: DeepSeekService,
    ) -> None:
        """初始化动态调整服务."""
        self.db = db
        self.cache_service = cache_service
        self.ai_service = ai_service
        self.logger = logger

    # ==================== 教案自动演进 ====================

    async def evolve_lesson_plan_automatically(
        self,
        lesson_plan_id: int,
        student_mastery_data: dict[str, Any],
        user_id: int,
    ) -> dict[str, Any]:
        """根据学生掌握度自动演进教案内容."""
        try:
            # 获取当前教案
            current_plan = await self._get_lesson_plan(lesson_plan_id)
            if not current_plan:
                raise BusinessLogicError(f"教案 {lesson_plan_id} 不存在")

            # 分析学生掌握度
            mastery_analysis = await self._analyze_student_mastery(student_mastery_data, user_id)

            # 生成教案演进建议
            evolution_suggestions = await self._generate_evolution_suggestions(
                current_plan, mastery_analysis, user_id
            )

            # 应用演进建议
            evolved_plan = await self._apply_evolution_suggestions(
                current_plan, evolution_suggestions
            )

            # 记录演进历史
            evolution_record = await self._record_plan_evolution(
                lesson_plan_id, current_plan, evolved_plan, mastery_analysis
            )

            # 缓存演进结果
            cache_key = f"evolved_plan:{lesson_plan_id}:{datetime.utcnow().date()}"
            await self.cache_service.set(cache_key, evolved_plan, CacheType.AI_RESULT, ttl=7200)

            return {
                "evolved_plan": evolved_plan,
                "evolution_record": evolution_record,
                "mastery_analysis": mastery_analysis,
                "evolution_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"教案自动演进失败: {str(e)}")
            raise BusinessLogicError(f"教案自动演进失败: {str(e)}") from e

    async def _analyze_student_mastery(
        self,
        mastery_data: dict[str, Any],
        user_id: int,
    ) -> dict[str, Any]:
        """分析学生掌握度."""
        prompt = f"""
分析以下学生掌握度数据，提供详细的掌握情况分析：

学生掌握度数据：
{json.dumps(mastery_data, ensure_ascii=False, indent=2)}

请分析：
1. 整体掌握水平
2. 薄弱知识点
3. 优势领域
4. 学习进度评估
5. 个性化建议

要求：
- 提供具体的数据支撑
- 识别关键问题
- 给出改进方向
"""

        success, ai_response, error = await self.ai_service.generate_completion(
            prompt=prompt,
            model="deepseek-chat",
            temperature=0.3,
            max_tokens=2048,
            user_id=user_id,
            task_type="mastery_analysis",
        )

        if not success:
            self.logger.warning(f"AI掌握度分析失败: {error}")
            return self._generate_fallback_mastery_analysis(mastery_data)

        return {
            "analysis": ai_response,
            "data_source": mastery_data,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    # ==================== 智能题目生成 ====================

    async def generate_intelligent_questions(
        self,
        teaching_progress: dict[str, Any],
        difficulty_level: str,
        question_count: int,
        user_id: int,
    ) -> dict[str, Any]:
        """根据教学进度智能匹配生成训练题目."""
        try:
            # 构建题目生成提示
            prompt = self._build_question_generation_prompt(
                teaching_progress, difficulty_level, question_count
            )

            # 调用AI生成题目
            success, ai_response, error = await self.ai_service.generate_completion(
                prompt=prompt,
                model="deepseek-chat",
                temperature=0.8,
                max_tokens=4096,
                user_id=user_id,
                task_type="question_generation",
            )

            if not success or not ai_response:
                raise BusinessLogicError(f"AI生成题目失败: {error}")

            # 解析生成的题目
            generated_questions = self._parse_generated_questions(str(ai_response))

            # 质量检查
            quality_checked_questions = await self._quality_check_questions(
                generated_questions, user_id
            )

            # 缓存生成结果
            cache_key = f"generated_questions:{user_id}:{hash(str(teaching_progress))}"
            await self.cache_service.set(
                cache_key, quality_checked_questions, CacheType.AI_RESULT, ttl=1800
            )

            return {
                "questions": quality_checked_questions,
                "generation_metadata": {
                    "teaching_progress": teaching_progress,
                    "difficulty_level": difficulty_level,
                    "requested_count": question_count,
                    "generated_count": len(quality_checked_questions),
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"智能题目生成失败: {str(e)}")
            raise BusinessLogicError(f"智能题目生成失败: {str(e)}") from e

    def _build_question_generation_prompt(
        self,
        teaching_progress: dict[str, Any],
        difficulty_level: str,
        question_count: int,
    ) -> str:
        """构建题目生成提示."""
        return f"""
基于以下教学进度，生成 {question_count} 道 {difficulty_level} 难度的训练题目：

教学进度：
{json.dumps(teaching_progress, ensure_ascii=False, indent=2)}

要求：
1. 题目类型多样化（选择题、填空题、阅读理解、写作题）
2. 难度符合 {difficulty_level} 级别
3. 紧密结合当前教学进度
4. 包含详细的答案和解析
5. 提供评分标准

输出格式：
{{
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice",
      "question": "题目内容",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "答案解析",
      "difficulty": "{difficulty_level}",
      "knowledge_points": ["知识点1", "知识点2"],
      "scoring_criteria": "评分标准"
    }}
  ]
}}
"""

    # ==================== 反馈周期：每周自动分析 ====================

    async def weekly_automatic_analysis(
        self,
        teacher_id: int,
        analysis_date: datetime | None = None,
    ) -> dict[str, Any]:
        """系统每周自动分析数据，提供调整建议."""
        try:
            if analysis_date is None:
                analysis_date = datetime.utcnow()

            # 获取一周内的数据
            week_start = analysis_date - timedelta(days=7)
            week_data = await self._collect_weekly_data(teacher_id, week_start, analysis_date)

            # AI分析周数据
            analysis_result = await self._analyze_weekly_data(week_data, teacher_id)

            # 生成调整建议
            adjustment_suggestions = await self._generate_weekly_suggestions(
                analysis_result, teacher_id
            )

            # 保存分析报告
            report = await self._save_weekly_report(
                teacher_id, analysis_date, analysis_result, adjustment_suggestions
            )

            return {
                "analysis_result": analysis_result,
                "adjustment_suggestions": adjustment_suggestions,
                "report_id": report["id"],
                "analysis_period": {
                    "start": week_start.isoformat(),
                    "end": analysis_date.isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"每周自动分析失败: {str(e)}")
            raise BusinessLogicError(f"每周自动分析失败: {str(e)}") from e

    async def _collect_weekly_data(
        self,
        teacher_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """收集一周内的教学数据."""
        # 这里应该查询实际的教学数据
        # 包括学生表现、教案使用情况、题目完成情况等
        return {
            "teacher_id": teacher_id,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "student_performance": {},
            "lesson_plan_usage": {},
            "question_completion": {},
            "collected_at": datetime.utcnow().isoformat(),
        }

    # ==================== 历史追踪：记录所有调整历史 ====================

    async def track_adjustment_history(
        self,
        adjustment_type: str,
        target_id: int,
        old_data: dict[str, Any],
        new_data: dict[str, Any],
        reason: str,
        user_id: int,
    ) -> dict[str, Any]:
        """记录调整历史，支持效果对比."""
        try:
            history_record = {
                "id": f"adj_{datetime.utcnow().timestamp()}",
                "adjustment_type": adjustment_type,
                "target_id": target_id,
                "old_data": old_data,
                "new_data": new_data,
                "reason": reason,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "changes": self._calculate_changes(old_data, new_data),
            }

            # 保存到数据库（这里需要创建相应的模型）
            # await self._save_adjustment_history(history_record)

            # 缓存历史记录
            cache_key = f"adjustment_history:{target_id}:{adjustment_type}"
            await self.cache_service.set(
                cache_key, history_record, CacheType.SYSTEM_DATA, ttl=86400
            )

            return history_record

        except Exception as e:
            self.logger.error(f"记录调整历史失败: {str(e)}")
            raise BusinessLogicError(f"记录调整历史失败: {str(e)}") from e

    async def compare_adjustment_effects(
        self,
        target_id: int,
        adjustment_type: str,
        comparison_period_days: int = 30,
    ) -> dict[str, Any]:
        """对比调整效果."""
        try:
            # 获取调整历史
            history_records = await self._get_adjustment_history(
                target_id, adjustment_type, comparison_period_days
            )

            if len(history_records) < 2:
                return {"message": "调整历史记录不足，无法进行效果对比"}

            # 分析效果对比
            effect_analysis = self._analyze_adjustment_effects(history_records)

            return {
                "comparison_result": effect_analysis,
                "history_count": len(history_records),
                "comparison_period": f"{comparison_period_days} 天",
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"对比调整效果失败: {str(e)}")
            raise BusinessLogicError(f"对比调整效果失败: {str(e)}") from e

    # ==================== 私有辅助方法 ====================

    async def _get_lesson_plan(self, lesson_plan_id: int) -> dict[str, Any] | None:
        """获取教案数据."""
        # 这里应该查询实际的教案数据
        return {
            "id": lesson_plan_id,
            "title": "示例教案",
            "content": "教案内容",
            "version": "1.0",
        }

    def _generate_fallback_mastery_analysis(self, mastery_data: dict[str, Any]) -> dict[str, Any]:
        """生成备用掌握度分析."""
        return {
            "analysis": "基于数据的基础分析",
            "fallback": True,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _parse_generated_questions(self, ai_response: str) -> list[dict[str, Any]]:
        """解析AI生成的题目."""
        try:
            # 尝试解析JSON格式的响应
            parsed = json.loads(ai_response)
            questions = parsed.get("questions", [])
            return list(questions) if isinstance(questions, list) else []
        except json.JSONDecodeError:
            # 如果不是JSON格式，返回基础格式
            return [
                {
                    "id": "fallback_q1",
                    "type": "text",
                    "question": ai_response[:200],
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ]

    async def _quality_check_questions(
        self, questions: list[dict[str, Any]], user_id: int
    ) -> list[dict[str, Any]]:
        """质量检查生成的题目."""
        # 这里应该实现题目质量检查逻辑
        return questions

    def _calculate_changes(
        self, old_data: dict[str, Any], new_data: dict[str, Any]
    ) -> dict[str, Any]:
        """计算数据变化."""
        changes = {}
        all_keys = set(old_data.keys()) | set(new_data.keys())

        for key in all_keys:
            old_value = old_data.get(key)
            new_value = new_data.get(key)

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value,
                    "changed": True,
                }

        return changes

    def _analyze_adjustment_effects(self, history_records: list[dict[str, Any]]) -> dict[str, Any]:
        """分析调整效果."""
        return {
            "total_adjustments": len(history_records),
            "improvement_trend": "positive",  # 这里应该基于实际数据计算
            "key_insights": ["调整效果分析结果"],
        }

    async def _get_adjustment_history(
        self, target_id: int, adjustment_type: str, days: int
    ) -> list[dict[str, Any]]:
        """获取调整历史记录."""
        # 这里应该查询实际的历史记录
        return [{"example": "data"}]  # 返回示例数据

    async def _generate_evolution_suggestions(
        self,
        current_plan: dict[str, Any],
        mastery_analysis: dict[str, Any],
        user_id: int,
    ) -> list[dict[str, Any]]:
        """生成教案演进建议."""
        return [
            {
                "type": "content_update",
                "description": "根据掌握度调整教学内容",
                "priority": "high",
            }
        ]

    async def _apply_evolution_suggestions(
        self,
        current_plan: dict[str, Any],
        suggestions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """应用演进建议."""
        evolved_plan = current_plan.copy()
        evolved_plan["evolved_at"] = datetime.utcnow().isoformat()
        evolved_plan["evolution_suggestions"] = suggestions
        return evolved_plan

    async def _record_plan_evolution(
        self,
        lesson_plan_id: int,
        old_plan: dict[str, Any],
        new_plan: dict[str, Any],
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """记录教案演进历史."""
        return {
            "lesson_plan_id": lesson_plan_id,
            "evolution_time": datetime.utcnow().isoformat(),
            "changes": self._calculate_changes(old_plan, new_plan),
            "analysis_basis": analysis,
        }

    async def _analyze_weekly_data(
        self, week_data: dict[str, Any], teacher_id: int
    ) -> dict[str, Any]:
        """分析周数据."""
        return {
            "summary": "周数据分析结果",
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    async def _generate_weekly_suggestions(
        self, analysis_result: dict[str, Any], teacher_id: int
    ) -> list[dict[str, Any]]:
        """生成周调整建议."""
        return [
            {
                "type": "weekly_adjustment",
                "description": "基于周数据的调整建议",
                "priority": "medium",
            }
        ]

    async def _save_weekly_report(
        self,
        teacher_id: int,
        analysis_date: datetime,
        analysis_result: dict[str, Any],
        suggestions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """保存周报告."""
        return {
            "id": f"report_{teacher_id}_{analysis_date.date()}",
            "saved_at": datetime.utcnow().isoformat(),
        }
