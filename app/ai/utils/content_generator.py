"""AI内容生成器工具."""

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ContentTemplate:
    """内容模板管理."""

    # 大纲生成提示模板
    SYLLABUS_PROMPT = """
你是一位经验丰富的英语四级教学专家。请基于以下信息生成详细的教学大纲：

课程信息：
- 课程标题：{title}
- 课程目标：{objectives}
- 总课时数：{total_hours}
- 难度级别：{difficulty_level}
- 特殊要求：{special_requirements}

源材料：
{source_materials}

请生成一个结构化的教学大纲，包含：
1. 课程概述
2. 学习目标
3. 教学内容安排（按周次/课时）
4. 重点难点分析
5. 评估方案
6. 参考资料

要求：
- 内容要符合英语四级考试要求
- 合理安排教学进度
- 突出重点难点
- 提供具体可行的教学建议

请以JSON格式返回，结构如下：
{
  "overview": "课程概述",
  "objectives": ["目标1", "目标2"],
  "weekly_plan": [
    {
      "week": 1,
      "lessons": [
        {
          "lesson_number": 1,
          "title": "课时标题",
          "content": "教学内容",
          "objectives": ["目标"],
          "key_points": ["重点"],
          "difficulties": ["难点"]
        }
      ]
    }
  ],
  "assessment": {
    "methods": ["评估方法"],
    "weight": {"平时": 30, "期中": 30, "期末": 40}
  },
  "resources": ["参考资料"]
}
"""

    # 教案生成提示模板
    LESSON_PLAN_PROMPT = """
你是一位专业的英语四级教师。请为以下课时生成详细的教案：

课时信息：
- 课时编号：{lesson_number}
- 课时标题：{title}
- 时长：{duration_minutes}分钟
- 学生水平：{student_level}
- 班级规模：{class_size}人
- 重点关注：{focus_areas}

大纲背景：
{syllabus_context}

可用资源：
{available_resources}

请生成包含以下要素的详细教案：
1. 学习目标（知识、技能、态度）
2. 教学内容结构（导入、新授、练习、总结）
3. 教学方法和策略
4. 互动活动设计
5. 所需教学资源
6. 评估方式
7. 作业安排
8. 教学反思要点

要求：
- 符合英语四级教学要求
- 注重学生参与和互动
- 合理分配时间
- 提供具体操作指导

请以JSON格式返回：
{
  "learning_objectives": {
    "knowledge": ["知识目标"],
    "skills": ["技能目标"],
    "attitudes": ["态度目标"]
  },
  "content_structure": {
    "warm_up": {
      "duration": 5,
      "activities": ["活动"]
    },
    "presentation": {
      "duration": 15,
      "content": "新知识呈现",
      "methods": ["教学方法"]
    },
    "practice": {
      "duration": 20,
      "activities": ["练习活动"]
    },
    "summary": {
      "duration": 5,
      "content": "总结要点"
    }
  },
  "teaching_methods": ["教学方法"],
  "resources_needed": ["所需资源"],
  "assessment": {
    "formative": ["形成性评估"],
    "summative": ["总结性评估"]
  },
  "homework": {
    "tasks": ["作业任务"],
    "time_estimate": "预计时间"
  },
  "reflection_points": ["反思要点"]
}
"""

    # 课程表优化提示模板
    SCHEDULE_OPTIMIZATION_PROMPT = """
你是一位教学管理专家。请为以下课程安排提供优化建议：

当前安排：
{current_schedule}

约束条件：
- 总课时：{total_lessons}
- 每周课时：{lessons_per_week}
- 时间范围：{start_date} 到 {end_date}
- 排除日期：{exclude_dates}
- 偏好时间：{preferred_times}
- 教室限制：{classroom_constraints}

请分析并提供：
1. 时间冲突检测
2. 负荷均衡分析
3. 优化建议
4. 替代方案

返回JSON格式：
{
  "conflicts": [
    {
      "type": "时间冲突",
      "description": "冲突描述",
      "affected_lessons": [1, 2]
    }
  ],
  "workload_analysis": {
    "weekly_distribution": {"周1": 2, "周2": 3},
    "peak_times": ["周三下午"],
    "suggestions": ["建议"]
  },
  "optimizations": [
    {
      "type": "时间调整",
      "original_time": "原时间",
      "suggested_time": "建议时间",
      "reason": "调整原因"
    }
  ],
  "alternatives": [
    {
      "scenario": "方案描述",
      "schedule": {"课时1": "时间安排"},
      "pros": ["优势"],
      "cons": ["劣势"]
    }
  ]
}
"""


class SyllabusGenerator:
    """大纲生成器."""

    def __init__(self) -> None:
        self.template = ContentTemplate.SYLLABUS_PROMPT

    def prepare_prompt(
        self,
        title: str,
        objectives: list[str],
        total_hours: int,
        difficulty_level: str,
        source_materials: dict[str, Any],
        special_requirements: str | None = None,
    ) -> str:
        """准备大纲生成提示."""
        # 格式化源材料信息
        materials_text = self._format_source_materials(source_materials)

        return self.template.format(
            title=title,
            objectives="\n".join(f"- {obj}" for obj in objectives),
            total_hours=total_hours,
            difficulty_level=self._format_difficulty_level(difficulty_level),
            special_requirements=special_requirements or "无特殊要求",
            source_materials=materials_text,
        )

    def _format_source_materials(self, materials: dict[str, Any]) -> str:
        """格式化源材料信息."""
        formatted = []

        if "textbooks" in materials:
            formatted.append("教材：")
            for book in materials["textbooks"]:
                formatted.append(f"  - {book.get('name', '未知')} ({book.get('chapters', '全册')})")

        if "exam_syllabus" in materials:
            formatted.append("考纲要求：")
            syllabus = materials["exam_syllabus"]
            for topic in syllabus.get("topics", []):
                formatted.append(f"  - {topic}")

        if "reference_materials" in materials:
            formatted.append("参考资料：")
            for ref in materials["reference_materials"]:
                formatted.append(f"  - {ref}")

        return "\n".join(formatted)

    def _format_difficulty_level(self, level: str) -> str:
        """格式化难度级别."""
        level_map = {
            "beginner": "初级（基础词汇2000-3000，简单语法）",
            "intermediate": "中级（四级词汇4000-5000，中等语法）",
            "advanced": "高级（扩展词汇6000+，复杂语法）",
        }
        return level_map.get(level, level)

    def validate_generated_content(
        self, content: str
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """验证生成的大纲内容."""
        try:
            # 尝试解析JSON
            syllabus_data = json.loads(content)

            # 验证必需字段
            required_fields = [
                "overview",
                "objectives",
                "weekly_plan",
                "assessment",
                "resources",
            ]
            for field in required_fields:
                if field not in syllabus_data:
                    return False, None, f"缺少必需字段: {field}"

            # 验证weekly_plan结构
            if not isinstance(syllabus_data["weekly_plan"], list):
                return False, None, "weekly_plan必须是列表"

            for week in syllabus_data["weekly_plan"]:
                if not isinstance(week.get("lessons"), list):
                    return False, None, f"第{week.get('week')}周的lessons必须是列表"

            return True, syllabus_data, None

        except json.JSONDecodeError as e:
            return False, None, f"JSON解析错误: {str(e)}"
        except Exception as e:
            return False, None, f"内容验证错误: {str(e)}"


class LessonPlanGenerator:
    """教案生成器."""

    def __init__(self) -> None:
        self.template = ContentTemplate.LESSON_PLAN_PROMPT

    def prepare_prompt(
        self,
        lesson_number: int,
        title: str,
        duration_minutes: int,
        student_level: str,
        focus_areas: list[str],
        syllabus_context: str,
        class_size: int | None = None,
        available_resources: list[str] | None = None,
    ) -> str:
        """准备教案生成提示."""
        return self.template.format(
            lesson_number=lesson_number,
            title=title,
            duration_minutes=duration_minutes,
            student_level=self._format_student_level(student_level),
            class_size=class_size or 30,
            focus_areas=", ".join(focus_areas),
            syllabus_context=syllabus_context,
            available_resources=self._format_resources(available_resources or []),
        )

    def _format_student_level(self, level: str) -> str:
        """格式化学生水平."""
        level_map = {
            "beginner": "基础水平（词汇量2000-3000）",
            "intermediate": "中等水平（词汇量4000-5000）",
            "advanced": "较高水平（词汇量6000+）",
        }
        return level_map.get(level, level)

    def _format_resources(self, resources: list[str]) -> str:
        """格式化可用资源."""
        if not resources:
            return "标准教室设备（黑板、投影仪、音响）"
        return "\n".join(f"- {resource}" for resource in resources)

    def validate_generated_content(
        self, content: str
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """验证生成的教案内容."""
        try:
            lesson_data = json.loads(content)

            required_fields = [
                "learning_objectives",
                "content_structure",
                "teaching_methods",
                "resources_needed",
                "assessment",
                "homework",
            ]

            for field in required_fields:
                if field not in lesson_data:
                    return False, None, f"缺少必需字段: {field}"

            # 验证content_structure时间分配
            structure = lesson_data["content_structure"]
            total_time = sum(
                section.get("duration", 0)
                for section in structure.values()
                if isinstance(section, dict)
            )

            if total_time <= 0:
                return False, None, "教学时间分配不合理"

            return True, lesson_data, None

        except json.JSONDecodeError as e:
            return False, None, f"JSON解析错误: {str(e)}"
        except Exception as e:
            return False, None, f"内容验证错误: {str(e)}"


class ScheduleOptimizer:
    """课程表优化器."""

    def __init__(self) -> None:
        self.template = ContentTemplate.SCHEDULE_OPTIMIZATION_PROMPT

    def prepare_prompt(
        self,
        current_schedule: list[dict[str, Any]],
        total_lessons: int,
        lessons_per_week: int,
        start_date: datetime,
        end_date: datetime,
        exclude_dates: list[datetime],
        preferred_times: list[dict[str, Any]],
        classroom_constraints: list[str] | None = None,
    ) -> str:
        """准备课程表优化提示."""
        return self.template.format(
            current_schedule=self._format_schedule(current_schedule),
            total_lessons=total_lessons,
            lessons_per_week=lessons_per_week,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            exclude_dates=self._format_dates(exclude_dates),
            preferred_times=self._format_time_preferences(preferred_times),
            classroom_constraints=classroom_constraints or [],
        )

    def _format_schedule(self, schedule: list[dict[str, Any]]) -> str:
        """格式化当前课程安排."""
        formatted = []
        for item in schedule:
            formatted.append(
                f"课时{item.get('lesson_number')}: "
                f"{item.get('date')} {item.get('start_time')}-{item.get('end_time')} "
                f"({item.get('classroom', '未指定教室')})"
            )
        return "\n".join(formatted)

    def _format_dates(self, dates: list[datetime]) -> str:
        """格式化日期列表."""
        return ", ".join(date.strftime("%Y-%m-%d") for date in dates)

    def _format_time_preferences(self, preferences: list[dict[str, Any]]) -> str:
        """格式化时间偏好."""
        formatted = []
        for pref in preferences:
            formatted.append(
                f"{pref.get('day_of_week')}: {pref.get('start_time')}-{pref.get('end_time')}"
            )
        return ", ".join(formatted)

    def detect_conflicts(self, schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """检测课程安排冲突."""
        conflicts = []

        # 按时间排序
        sorted_schedule = sorted(schedule, key=lambda x: x.get("start_time", ""))

        for i in range(len(sorted_schedule) - 1):
            current = sorted_schedule[i]
            next_item = sorted_schedule[i + 1]

            # 检查时间重叠
            current_end_time = current.get("end_time")
            next_start_time = next_item.get("start_time")
            if (
                current.get("date") == next_item.get("date")
                and current_end_time is not None
                and next_start_time is not None
                and current_end_time > next_start_time
            ):
                conflicts.append(
                    {
                        "type": "时间冲突",
                        "description": f"课时{current.get('lesson_number')}与课时{next_item.get('lesson_number')}时间重叠",
                        "affected_lessons": [
                            current.get("lesson_number"),
                            next_item.get("lesson_number"),
                        ],
                    }
                )

            # 检查教室冲突
            if (
                current.get("date") == next_item.get("date")
                and current.get("classroom") == next_item.get("classroom")
                and current.get("classroom")
            ):
                conflicts.append(
                    {
                        "type": "教室冲突",
                        "description": f"教室{current.get('classroom')}在同一时间被多个课时占用",
                        "affected_lessons": [
                            current.get("lesson_number"),
                            next_item.get("lesson_number"),
                        ],
                    }
                )

        return conflicts


class SmartSuggestionEngine:
    """智能建议引擎."""

    def __init__(self) -> None:
        self.suggestion_templates = {
            "syllabus_optimization": self._get_syllabus_optimization_suggestions,
            "lesson_plan_enhancement": self._get_lesson_plan_enhancement_suggestions,
            "schedule_improvement": self._get_schedule_improvement_suggestions,
        }

    def generate_suggestions(
        self,
        context_type: str,
        context_data: dict[str, Any],
        suggestion_type: str,
        user_preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成智能建议."""
        key = f"{context_type}_{suggestion_type}"

        if key in self.suggestion_templates:
            return self.suggestion_templates[key](context_data, user_preferences or {})

        return {
            "suggestions": [],
            "confidence_scores": [],
            "reasoning": [],
            "implementation_difficulty": [],
        }

    def _get_syllabus_optimization_suggestions(
        self, syllabus_data: dict[str, Any], preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """获取大纲优化建议."""
        suggestions = []
        confidence_scores = []
        reasoning = []
        difficulty = []

        # 检查课时分配合理性
        weekly_plan = syllabus_data.get("weekly_plan", [])
        if len(weekly_plan) > 0:
            total_lessons = sum(len(week.get("lessons", [])) for week in weekly_plan)
            avg_lessons_per_week = total_lessons / len(weekly_plan)

            if avg_lessons_per_week > 3:
                suggestions.append(
                    {
                        "type": "课时分配",
                        "description": "建议减少每周课时数，避免学生负担过重",
                        "specific_action": f"当前平均每周{avg_lessons_per_week:.1f}课时，建议控制在2-3课时内",
                    }
                )
                confidence_scores.append(0.85)
                reasoning.append("研究表明，每周2-3课时的安排更有利于知识消化吸收")
                difficulty.append("medium")

        # 检查评估方案合理性
        assessment = syllabus_data.get("assessment", {})
        weights = assessment.get("weight", {})
        if weights:
            total_weight = sum(weights.values())
            if total_weight != 100:
                suggestions.append(
                    {
                        "type": "评估权重",
                        "description": "评估权重分配需要调整至总计100%",
                        "specific_action": f"当前总权重为{total_weight}%，需要重新分配",
                    }
                )
                confidence_scores.append(0.95)
                reasoning.append("评估权重总和必须为100%以确保评分准确性")
                difficulty.append("easy")

        return {
            "suggestions": suggestions,
            "confidence_scores": confidence_scores,
            "reasoning": reasoning,
            "implementation_difficulty": difficulty,
        }

    def _get_lesson_plan_enhancement_suggestions(
        self, lesson_data: dict[str, Any], preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """获取教案增强建议."""
        suggestions = []
        confidence_scores = []
        reasoning = []
        difficulty = []

        # 检查时间分配
        content_structure = lesson_data.get("content_structure", {})
        practice_time = content_structure.get("practice", {}).get("duration", 0)
        total_time = sum(
            section.get("duration", 0)
            for section in content_structure.values()
            if isinstance(section, dict)
        )

        if practice_time / total_time < 0.4:  # 练习时间少于40%
            suggestions.append(
                {
                    "type": "练习时间",
                    "description": "建议增加学生练习时间，提高课堂参与度",
                    "specific_action": f"当前练习时间占比{practice_time / total_time * 100:.1f}%，建议提升至40%以上",
                }
            )
            confidence_scores.append(0.8)
            reasoning.append("充足的练习时间有助于知识巩固和技能提升")
            difficulty.append("easy")

        # 检查教学方法多样性
        teaching_methods = lesson_data.get("teaching_methods", [])
        if len(teaching_methods) < 3:
            suggestions.append(
                {
                    "type": "教学方法",
                    "description": "建议采用更多元化的教学方法",
                    "specific_action": "可以增加小组讨论、角色扮演、案例分析等互动方法",
                }
            )
            confidence_scores.append(0.75)
            reasoning.append("多样化的教学方法能够满足不同学习风格的学生需求")
            difficulty.append("medium")

        return {
            "suggestions": suggestions,
            "confidence_scores": confidence_scores,
            "reasoning": reasoning,
            "implementation_difficulty": difficulty,
        }

    def _get_schedule_improvement_suggestions(
        self, schedule_data: dict[str, Any], preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """获取课程表改进建议."""
        suggestions: list[str] = []
        confidence_scores: list[float] = []
        reasoning: list[str] = []
        difficulty: list[int] = []

        # 这里可以添加基于规则的课程表优化建议
        # 例如：避免连续排课、合理分配不同类型课程等

        return {
            "suggestions": suggestions,
            "confidence_scores": confidence_scores,
            "reasoning": reasoning,
            "implementation_difficulty": difficulty,
        }
