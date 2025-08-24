"""智能训练工坊服务 - 需求15实现."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import DeepSeekService
from app.training.models.training_models import (
    TrainingParameterTemplate,
    TrainingTask,
    TrainingTaskSubmission,
)
from app.training.schemas.training_workshop_schemas import (
    TrainingParameterTemplateRequest,
    TrainingParameterTemplateResponse,
    TrainingTaskRequest,
    TrainingTaskResponse,
    WeeklyTrainingRequest,
)


class TrainingWorkshopService:
    """智能训练工坊核心服务 - 需求15验收标准实现."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化服务."""
        self.db = db
        self.deepseek_service = DeepSeekService()

    # ==================== 训练参数模板管理 (验收标准2) ====================

    async def create_parameter_template(
        self, teacher_id: int, template_data: TrainingParameterTemplateRequest
    ) -> TrainingParameterTemplateResponse:
        """创建训练参数模板."""
        # 如果设置为默认模板，先取消其他默认模板
        if template_data.is_default:
            await self._unset_default_templates(teacher_id)

        template = TrainingParameterTemplate(
            name=template_data.name,
            description=template_data.description,
            config=template_data.config.model_dump(),
            is_default=template_data.is_default,
            created_by=teacher_id,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return TrainingParameterTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            config=template_data.config,
            is_default=template.is_default,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at or template.created_at,
        )

    async def get_parameter_templates(
        self, teacher_id: int, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """获取教师的训练参数模板列表."""
        offset = (page - 1) * page_size

        # 查询模板
        stmt = (
            select(TrainingParameterTemplate)
            .where(TrainingParameterTemplate.created_by == teacher_id)
            .where(TrainingParameterTemplate.is_active.is_(True))
            .order_by(
                desc(TrainingParameterTemplate.is_default),
                desc(TrainingParameterTemplate.created_at),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        templates = result.scalars().all()

        # 查询总数
        count_stmt = (
            select(func.count(TrainingParameterTemplate.id))
            .where(TrainingParameterTemplate.created_by == teacher_id)
            .where(TrainingParameterTemplate.is_active.is_(True))
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 转换为响应格式
        template_responses = []
        for template in templates:
            template_responses.append(
                TrainingParameterTemplateResponse(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    config=template.config,  # type: ignore
                    is_default=template.is_default,
                    created_by=template.created_by,
                    created_at=template.created_at,
                    updated_at=template.updated_at or template.created_at,
                )
            )

        return {
            "templates": template_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def update_parameter_template(
        self,
        template_id: int,
        teacher_id: int,
        template_data: TrainingParameterTemplateRequest,
    ) -> TrainingParameterTemplateResponse:
        """更新训练参数模板."""
        # 查询模板
        stmt = select(TrainingParameterTemplate).where(
            and_(
                TrainingParameterTemplate.id == template_id,
                TrainingParameterTemplate.created_by == teacher_id,
            )
        )
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(f"模板ID {template_id} 不存在或无权限访问")

        # 如果设置为默认模板，先取消其他默认模板
        if template_data.is_default and not template.is_default:
            await self._unset_default_templates(teacher_id)

        # 更新模板
        template.name = template_data.name
        template.description = template_data.description
        template.config = template_data.config.model_dump()
        template.is_default = template_data.is_default

        await self.db.commit()
        await self.db.refresh(template)

        return TrainingParameterTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            config=template_data.config,
            is_default=template.is_default,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at or template.created_at,
        )

    async def delete_parameter_template(self, template_id: int, teacher_id: int) -> bool:
        """删除训练参数模板."""
        stmt = select(TrainingParameterTemplate).where(
            and_(
                TrainingParameterTemplate.id == template_id,
                TrainingParameterTemplate.created_by == teacher_id,
            )
        )
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            return False

        # 软删除
        template.is_active = False
        await self.db.commit()

        return True

    # ==================== 训练任务管理 (验收标准4) ====================

    async def create_training_task(
        self, teacher_id: int, task_data: TrainingTaskRequest
    ) -> TrainingTaskResponse:
        """创建训练任务."""
        task = TrainingTask(
            class_id=task_data.class_id,
            teacher_id=teacher_id,
            task_name=task_data.task_name,
            task_type=task_data.task_type,
            config=task_data.config,
            deadline=task_data.deadline,
        )

        # 处理发布设置
        if task_data.publish_type == "immediate":
            task.status = "published"
            task.publish_time = datetime.utcnow()
            # 立即生成题目并投放
            await self._generate_and_deploy_questions(task)
        elif task_data.publish_type == "scheduled" and task_data.scheduled_time:
            task.status = "scheduled"
            task.publish_time = task_data.scheduled_time

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return await self._build_task_response(task)

    async def get_training_tasks(
        self,
        teacher_id: int,
        class_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取训练任务列表."""
        offset = (page - 1) * page_size

        # 构建查询条件
        conditions = [TrainingTask.teacher_id == teacher_id]
        if class_id:
            conditions.append(TrainingTask.class_id == class_id)

        # 查询任务
        stmt = (
            select(TrainingTask)
            .where(and_(*conditions))
            .order_by(desc(TrainingTask.created_at))
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        # 查询总数
        count_stmt = select(func.count(TrainingTask.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 构建响应
        task_responses = []
        for task in tasks:
            task_responses.append(await self._build_task_response(task))

        return {
            "tasks": task_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ==================== 周训练配置 (验收标准3) ====================

    async def create_weekly_training(
        self, teacher_id: int, weekly_data: WeeklyTrainingRequest
    ) -> TrainingTaskResponse:
        """创建周训练配置."""
        # 构建任务配置
        task_config: dict[str, Any] = {
            "week_number": weekly_data.week_config.week_number,
            "training_types": [],
        }

        # 处理阅读理解配置
        if weekly_data.week_config.reading_config:
            reading_config = weekly_data.week_config.reading_config
            task_config["reading"] = {
                "topic_count": reading_config.topic_count,
                "questions_per_topic": reading_config.questions_per_topic,
                "syllabus_relevance_rate": reading_config.syllabus_relevance_rate,
                "topics": reading_config.topics or [],
            }
            task_config["training_types"].append("reading")

        # 处理写作配置
        if weekly_data.week_config.writing_config:
            writing_config = weekly_data.week_config.writing_config
            task_config["writing"] = {
                "writing_types": writing_config.writing_types,
                "cet4_standard_embedded": writing_config.cet4_standard_embedded,
                "topic_sources": writing_config.topic_sources,
            }
            task_config["training_types"].append("writing")

        # 创建训练任务
        task_request = TrainingTaskRequest(
            class_id=weekly_data.class_id,
            task_name=f"第{weekly_data.week_config.week_number}周训练",
            task_type="weekly",
            config=task_config,
            publish_type=weekly_data.publish_type,
            scheduled_time=weekly_data.scheduled_time,
            deadline=None,
        )

        return await self.create_training_task(teacher_id, task_request)

    # ==================== 私有辅助方法 ====================

    async def _unset_default_templates(self, teacher_id: int) -> None:
        """取消教师的其他默认模板."""
        stmt = (
            select(TrainingParameterTemplate)
            .where(TrainingParameterTemplate.created_by == teacher_id)
            .where(TrainingParameterTemplate.is_default.is_(True))
        )
        result = await self.db.execute(stmt)
        templates = result.scalars().all()

        for template in templates:
            template.is_default = False

        await self.db.commit()

    async def _build_task_response(self, task: TrainingTask) -> TrainingTaskResponse:
        """构建训练任务响应."""
        # 查询统计信息
        total_students = await self._get_class_student_count(task.class_id)
        completed_students = await self._get_task_completion_count(task.id)
        completion_rate = completed_students / total_students if total_students > 0 else 0.0

        return TrainingTaskResponse(
            id=task.id,
            class_id=task.class_id,
            teacher_id=task.teacher_id,
            task_name=task.task_name,
            task_type=task.task_type,
            config=task.config,
            status=task.status,
            publish_time=task.publish_time,
            deadline=task.deadline,
            created_at=task.created_at,
            updated_at=task.updated_at or task.created_at,
            total_students=total_students,
            completed_students=completed_students,
            completion_rate=completion_rate,
        )

    async def _get_class_student_count(self, class_id: int) -> int:
        """获取班级学生数量."""
        # 这里需要根据实际的班级模型来实现
        # 暂时返回模拟数据
        return 30

    async def _get_task_completion_count(self, task_id: int) -> int:
        """获取任务完成人数."""
        stmt = (
            select(func.count(TrainingTaskSubmission.id))
            .where(TrainingTaskSubmission.task_id == task_id)
            .where(TrainingTaskSubmission.completed_at.isnot(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _generate_and_deploy_questions(self, task: TrainingTask) -> None:
        """生成题目并投放到学生端 (验收标准5)."""
        try:
            logging.info(f"开始为任务 {task.id} 生成题目")

            # 解析任务配置
            config = task.config or {}
            training_types = config.get("training_types", [])

            # 创建题目批次标识
            batch_name = f"{task.task_name}_batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            logging.info(f"创建题目批次: {batch_name}")

            generated_questions = []

            # 处理阅读理解题目生成
            if "reading" in training_types:
                reading_questions = await self._generate_reading_questions(
                    task, config.get("reading", {})
                )
                generated_questions.extend(reading_questions)

            # 处理写作题目生成
            if "writing" in training_types:
                writing_questions = await self._generate_writing_questions(
                    task, config.get("writing", {})
                )
                generated_questions.extend(writing_questions)

            # 处理其他训练类型
            for training_type in training_types:
                if training_type not in ["reading", "writing"]:
                    other_questions = await self._generate_other_questions(
                        task, training_type, config
                    )
                    generated_questions.extend(other_questions)

            # 更新任务状态
            if generated_questions:
                task.status = "published"
                task.publish_time = datetime.utcnow()
                await self.db.commit()

                logging.info(f"任务 {task.id} 成功生成 {len(generated_questions)} 道题目并投放")
            else:
                task.status = "failed"
                await self.db.commit()
                logging.error(f"任务 {task.id} 题目生成失败")

        except Exception as e:
            logging.error(f"任务 {task.id} 题目生成过程中出错: {str(e)}")
            task.status = "failed"
            await self.db.commit()
            raise

    async def _generate_reading_questions(
        self, task: TrainingTask, reading_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """生成阅读理解题目."""
        questions = []

        topic_count = reading_config.get("topic_count", 3)
        questions_per_topic = reading_config.get("questions_per_topic", 5)
        syllabus_relevance_rate = reading_config.get("syllabus_relevance_rate", 80)
        topics = reading_config.get("topics", [])

        for i in range(topic_count):
            try:
                # 构建阅读理解生成提示词
                prompt = self._build_reading_prompt(
                    topics[i] if i < len(topics) else None,
                    questions_per_topic,
                    syllabus_relevance_rate,
                )

                # 调用DeepSeek生成阅读理解
                success, content, error = await self.deepseek_service.generate_completion(
                    prompt=prompt,
                    user_id=task.teacher_id,
                    task_type="reading_generation",
                    temperature=0.7,
                    max_tokens=3000,
                )

                if success and content:
                    # 提取AI生成的文本内容
                    content_text = (
                        content.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if isinstance(content, dict)
                        else str(content)
                    )
                    # 解析AI生成的内容
                    passage_data = self._parse_reading_content(content_text)
                    if passage_data:
                        questions.append(
                            {
                                "type": "reading",
                                "task_id": task.id,
                                "content": passage_data,
                                "difficulty": "intermediate",
                                "topic": (topics[i] if i < len(topics) else f"阅读主题{i + 1}"),
                            }
                        )

            except Exception as e:
                logging.error(f"生成阅读理解题目失败: {str(e)}")
                continue

        return questions

    async def _generate_writing_questions(
        self, task: TrainingTask, writing_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """生成写作题目."""
        questions = []

        writing_types = writing_config.get("writing_types", ["议论文"])
        cet4_standard_embedded = writing_config.get("cet4_standard_embedded", True)
        topic_sources = writing_config.get("topic_sources", ["时事热点"])

        for writing_type in writing_types:
            try:
                # 构建写作题目生成提示词
                prompt = self._build_writing_prompt(
                    writing_type, topic_sources, cet4_standard_embedded
                )

                # 调用DeepSeek生成写作题目
                success, content, error = await self.deepseek_service.generate_completion(
                    prompt=prompt,
                    user_id=task.teacher_id,
                    task_type="writing_generation",
                    temperature=0.8,
                    max_tokens=2000,
                )

                if success and content:
                    # 提取AI生成的文本内容
                    content_text = (
                        content.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if isinstance(content, dict)
                        else str(content)
                    )
                    # 解析AI生成的写作题目
                    writing_data = self._parse_writing_content(content_text)
                    if writing_data:
                        questions.append(
                            {
                                "type": "writing",
                                "task_id": task.id,
                                "content": writing_data,
                                "difficulty": "intermediate",
                                "writing_type": writing_type,
                            }
                        )

            except Exception as e:
                logging.error(f"生成写作题目失败: {str(e)}")
                continue

        return questions

    async def _generate_other_questions(
        self, task: TrainingTask, training_type: str, config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """生成其他类型题目."""
        questions = []

        try:
            # 根据训练类型生成相应题目
            prompt = self._build_general_prompt(training_type, config)

            success, content, error = await self.deepseek_service.generate_completion(
                prompt=prompt,
                user_id=task.teacher_id,
                task_type=f"{training_type}_generation",
                temperature=0.7,
                max_tokens=2000,
            )

            if success and content:
                # 提取AI生成的文本内容
                content_text = (
                    content.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if isinstance(content, dict)
                    else str(content)
                )
                question_data = self._parse_general_content(content_text, training_type)
                if question_data:
                    questions.append(
                        {
                            "type": training_type,
                            "task_id": task.id,
                            "content": question_data,
                            "difficulty": "intermediate",
                        }
                    )

        except Exception as e:
            logging.error(f"生成{training_type}题目失败: {str(e)}")

        return questions

    def _build_reading_prompt(
        self, topic: str | None, questions_per_topic: int, syllabus_relevance_rate: int
    ) -> str:
        """构建阅读理解生成提示词."""
        topic_text = f"主题：{topic}" if topic else "请自选合适的主题"

        return f"""请生成一篇适合大学英语四级考试的阅读理解材料和题目。

要求：
1. {topic_text}
2. 文章长度：300-400词
3. 难度：四级水平
4. 考纲关联度：≥{syllabus_relevance_rate}%
5. 生成{questions_per_topic}道选择题

请按以下JSON格式返回：
{{
    "passage": "阅读文章内容",
    "questions": [
        {{
            "title": "题目1",
            "question": "问题内容",
            "options": ["A选项", "B选项", "C选项", "D选项"],
            "correct_answer": "A",
            "analysis": "答案解析"
        }}
    ]
}}

确保内容符合四级考试标准，题目设计科学合理。"""

    def _build_writing_prompt(
        self, writing_type: str, topic_sources: list[str], cet4_standard: bool
    ) -> str:
        """构建写作题目生成提示词."""
        sources_text = "、".join(topic_sources)
        standard_text = (
            "严格按照大学英语四级考试写作评分标准" if cet4_standard else "按照一般英语写作标准"
        )

        return f"""请生成一道大学英语四级{writing_type}写作题目。

要求：
1. 题目来源：{sources_text}
2. 评分标准：{standard_text}
3. 字数要求：120-180词
4. 难度：四级水平

请按以下JSON格式返回：
{{
    "title": "写作题目标题",
    "prompt": "写作要求和提示",
    "requirements": ["要求1", "要求2", "要求3"],
    "scoring_criteria": {{
        "content": "内容评分标准",
        "language": "语言评分标准",
        "structure": "结构评分标准"
    }},
    "sample_outline": "参考提纲"
}}

确保题目具有时代性和实用性。"""

    def _build_general_prompt(self, training_type: str, config: dict[str, Any]) -> str:
        """构建通用题目生成提示词."""
        return f"""请生成{training_type}类型的英语训练题目。

要求：
1. 难度：大学英语四级水平
2. 题目数量：1-3道
3. 符合{training_type}训练的特点

请按JSON格式返回题目内容。"""

    def _parse_reading_content(self, content: str) -> dict[str, Any] | None:
        """解析阅读理解AI生成内容."""
        try:
            # 尝试从AI响应中提取JSON
            import json

            # 查找JSON内容
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)

                # 验证必要字段
                if isinstance(data, dict) and "passage" in data and "questions" in data:
                    return data

        except Exception as e:
            logging.error(f"解析阅读理解内容失败: {str(e)}")

        return None

    def _parse_writing_content(self, content: str) -> dict[str, Any] | None:
        """解析写作题目AI生成内容."""
        try:
            import json

            # 查找JSON内容
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)

                # 验证必要字段
                if isinstance(data, dict) and "title" in data and "prompt" in data:
                    return data

        except Exception as e:
            logging.error(f"解析写作题目内容失败: {str(e)}")

        return None

    def _parse_general_content(self, content: str, training_type: str) -> dict[str, Any] | None:
        """解析通用题目AI生成内容."""
        try:
            # 简单的内容解析
            return {
                "content": content,
                "type": training_type,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logging.error(f"解析{training_type}内容失败: {str(e)}")

        return None

    # ==================== 数据分析功能 (任务3.2) ====================

    async def get_class_task_statistics(
        self, class_id: int, start_date: str | None = None, end_date: str | None = None
    ) -> dict[str, Any]:
        """获取班级训练任务统计."""
        try:
            # 构建查询条件
            query = select(TrainingTask).where(TrainingTask.class_id == class_id)

            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                query = query.where(TrainingTask.created_at >= start_dt)

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                query = query.where(TrainingTask.created_at <= end_dt)

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            # 统计任务状态
            status_counts: dict[str, int] = {}
            task_types: dict[str, int] = {}
            total_tasks = len(tasks)

            for task in tasks:
                status = task.status or "draft"
                status_counts[status] = status_counts.get(status, 0) + 1

                task_type = task.task_type or "general"
                task_types[task_type] = task_types.get(task_type, 0) + 1

            # 计算完成率
            published_tasks = status_counts.get("published", 0)
            completion_rate = published_tasks / total_tasks if total_tasks > 0 else 0

            return {
                "total_tasks": total_tasks,
                "published_tasks": published_tasks,
                "draft_tasks": status_counts.get("draft", 0),
                "failed_tasks": status_counts.get("failed", 0),
                "completion_rate": completion_rate,
                "task_types": task_types,
                "status_distribution": status_counts,
            }

        except Exception as e:
            logging.error(f"获取班级任务统计失败: {str(e)}")
            return {
                "total_tasks": 0,
                "published_tasks": 0,
                "draft_tasks": 0,
                "failed_tasks": 0,
                "completion_rate": 0.0,
                "task_types": {},
                "status_distribution": {},
            }

    async def get_class_student_performance(
        self, class_id: int, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict[str, Any]]:
        """获取班级学生表现分析."""
        try:
            # 获取班级的训练任务
            task_query = select(TrainingTask).where(TrainingTask.class_id == class_id)
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                task_query = task_query.where(TrainingTask.created_at >= start_dt)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                task_query = task_query.where(TrainingTask.created_at <= end_dt)

            task_result = await self.db.execute(task_query)
            tasks = task_result.scalars().all()
            task_ids = [task.id for task in tasks]

            if not task_ids:
                return []

            # 获取学生提交记录
            submission_query = select(TrainingTaskSubmission).where(
                TrainingTaskSubmission.task_id.in_(task_ids)
            )

            submission_result = await self.db.execute(submission_query)
            submissions = submission_result.scalars().all()

            # 按学生分组统计
            student_stats: dict[int, dict[str, Any]] = {}
            for submission in submissions:
                student_id = submission.student_id
                if student_id not in student_stats:
                    student_stats[student_id] = {
                        "student_id": student_id,
                        "total_submissions": 0,
                        "completed_submissions": 0,
                        "total_score": 0.0,
                        "scores": [],
                        "completion_rates": [],
                    }

                stats = student_stats[student_id]
                stats["total_submissions"] += 1

                if submission.completed_at:
                    stats["completed_submissions"] += 1

                if submission.score is not None:
                    stats["total_score"] += submission.score
                    stats["scores"].append(submission.score)

                stats["completion_rates"].append(submission.completion_rate)

            # 计算统计指标
            performance_list = []
            for student_id, stats in student_stats.items():
                avg_score = stats["total_score"] / len(stats["scores"]) if stats["scores"] else 0.0
                avg_completion_rate = (
                    sum(stats["completion_rates"]) / len(stats["completion_rates"])
                    if stats["completion_rates"]
                    else 0.0
                )
                completion_ratio = (
                    stats["completed_submissions"] / stats["total_submissions"]
                    if stats["total_submissions"] > 0
                    else 0.0
                )

                performance_list.append(
                    {
                        "student_id": student_id,
                        "total_tasks": stats["total_submissions"],
                        "completed_tasks": stats["completed_submissions"],
                        "completion_ratio": completion_ratio,
                        "average_score": avg_score,
                        "average_completion_rate": avg_completion_rate,
                        "performance_level": self._calculate_performance_level(
                            avg_score, completion_ratio
                        ),
                    }
                )

            return performance_list

        except Exception as e:
            logging.error(f"获取学生表现分析失败: {str(e)}")
            return []

    async def identify_risk_students(self, class_id: int) -> list[dict[str, Any]]:
        """识别风险学生."""
        try:
            # 获取学生表现数据
            student_performance = await self.get_class_student_performance(class_id)

            risk_students = []
            for student in student_performance:
                risk_score = 0
                risk_factors = []

                # 完成率低于50%
                if student["completion_ratio"] < 0.5:
                    risk_score += 3
                    risk_factors.append("完成率过低")

                # 平均分低于60分
                if student["average_score"] < 60:
                    risk_score += 2
                    risk_factors.append("平均分过低")

                # 平均完成度低于70%
                if student["average_completion_rate"] < 0.7:
                    risk_score += 2
                    risk_factors.append("完成度不足")

                # 参与任务数量少
                if student["total_tasks"] < 3:
                    risk_score += 1
                    risk_factors.append("参与度不足")

                # 风险等级判定
                if risk_score >= 5:
                    risk_level = "高风险"
                elif risk_score >= 3:
                    risk_level = "中风险"
                elif risk_score >= 1:
                    risk_level = "低风险"
                else:
                    continue  # 无风险，跳过

                risk_students.append(
                    {
                        "student_id": student["student_id"],
                        "risk_level": risk_level,
                        "risk_score": risk_score,
                        "risk_factors": risk_factors,
                        "completion_ratio": student["completion_ratio"],
                        "average_score": student["average_score"],
                        "suggestions": self._generate_improvement_suggestions(risk_factors),
                    }
                )

            # 按风险分数排序
            risk_students.sort(key=lambda x: x["risk_score"], reverse=True)
            return risk_students

        except Exception as e:
            logging.error(f"识别风险学生失败: {str(e)}")
            return []

    async def get_training_effectiveness(
        self, class_id: int, start_date: str | None = None, end_date: str | None = None
    ) -> dict[str, Any]:
        """获取训练效果分析."""
        try:
            # 获取学生表现数据
            student_performance = await self.get_class_student_performance(
                class_id, start_date, end_date
            )

            if not student_performance:
                return {
                    "overall_effectiveness": 0.0,
                    "average_completion_rate": 0.0,
                    "average_score": 0.0,
                    "student_count": 0,
                    "performance_distribution": {},
                    "improvement_trends": {},
                }

            # 计算整体指标
            total_students = len(student_performance)
            avg_completion_rate = (
                sum(s["completion_ratio"] for s in student_performance) / total_students
            )
            avg_score = sum(s["average_score"] for s in student_performance) / total_students

            # 计算表现分布
            performance_distribution = {"优秀": 0, "良好": 0, "一般": 0, "较差": 0}
            for student in student_performance:
                level = student["performance_level"]
                if level in performance_distribution:
                    performance_distribution[level] += 1

            # 计算整体效果分数
            effectiveness_score = (avg_completion_rate * 0.4 + avg_score / 100 * 0.6) * 100

            return {
                "overall_effectiveness": effectiveness_score,
                "average_completion_rate": avg_completion_rate,
                "average_score": avg_score,
                "student_count": total_students,
                "performance_distribution": performance_distribution,
                "improvement_trends": {
                    "trend": "stable",  # 简化实现
                    "recommendation": "继续保持当前训练强度",
                },
            }

        except Exception as e:
            logging.error(f"获取训练效果分析失败: {str(e)}")
            return {
                "overall_effectiveness": 0.0,
                "average_completion_rate": 0.0,
                "average_score": 0.0,
                "student_count": 0,
                "performance_distribution": {},
                "improvement_trends": {},
            }

    def _calculate_performance_level(self, avg_score: float, completion_ratio: float) -> str:
        """计算学生表现等级."""
        # 综合分数计算
        composite_score = avg_score * 0.6 + completion_ratio * 100 * 0.4

        if composite_score >= 85:
            return "优秀"
        elif composite_score >= 75:
            return "良好"
        elif composite_score >= 60:
            return "一般"
        else:
            return "较差"

    def _generate_improvement_suggestions(self, risk_factors: list[str]) -> list[str]:
        """生成改进建议."""
        suggestions = []

        if "完成率过低" in risk_factors:
            suggestions.append("建议增加学习时间，确保按时完成训练任务")

        if "平均分过低" in risk_factors:
            suggestions.append("建议复习基础知识，加强薄弱环节练习")

        if "完成度不足" in risk_factors:
            suggestions.append("建议提高专注度，认真完成每道题目")

        if "参与度不足" in risk_factors:
            suggestions.append("建议积极参与训练，保持学习连续性")

        if not suggestions:
            suggestions.append("继续保持良好的学习状态")

        return suggestions
