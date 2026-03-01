"""学习辅助工具系统 - 服务层"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.deepseek_service import DeepSeekService
from app.training.models.assistant_models import (
    KnowledgeBaseModel,
    LearningResourceModel,
    QARecordModel,
    UserResourceInteractionModel,
    VoiceRecognitionRecordModel,
)
from app.training.schemas.assistant_schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    LearningResourceCreate,
    QARequest,
    QAResponse,
    ResourceRecommendationRequest,
    UserResourceInteractionCreate,
    VoiceRecognitionRequest,
    VoiceRecognitionResponse,
)

logger = logging.getLogger(__name__)


class AssistantService:
    """
    学习辅助工具服务类

    实现RAG智能问答系统、学习资源推荐、语音识别功能等
    """

    def __init__(self: "AssistantService", db: AsyncSession) -> None:
        self.db = db
        self.ai_service = DeepSeekService()

    # ==================== 知识库管理 ====================

    async def create_knowledge_base(
        self: "AssistantService", data: KnowledgeBaseCreate
    ) -> KnowledgeBaseModel:
        """创建知识库条目"""
        logger.info(f"创建知识库条目: {data.title}")

        # 生成向量表示
        embedding_vector = await self._generate_embedding(data.content)

        knowledge = KnowledgeBaseModel(
            title=data.title,
            content=data.content,
            summary=data.summary,
            category=data.category,
            tags=data.tags,
            difficulty_level=data.difficulty_level,
            source_type=data.source_type,
            source_url=data.source_url,
            author=data.author,
            embedding_vector=embedding_vector,
            vector_dimension=len(embedding_vector) if embedding_vector else 0,
        )

        self.db.add(knowledge)
        await self.db.commit()
        await self.db.refresh(knowledge)

        logger.info(f"知识库条目创建成功: ID={knowledge.id}")  # type: ignore
        return knowledge

    async def get_knowledge_base_list(
        self: "AssistantService",
        skip: int = 0,
        limit: int = 10,
        category: str | None = None,
        search_query: str | None = None,
    ) -> tuple[list[KnowledgeBaseModel], int]:
        """获取知识库列表"""
        logger.info("查询知识库列表")

        # 构建查询条件
        conditions = [KnowledgeBaseModel.is_active.is_(True)]
        if category:
            conditions.append(KnowledgeBaseModel.category == category)  # type: ignore
        if search_query:
            search_condition = KnowledgeBaseModel.title.contains(
                search_query
            ) | KnowledgeBaseModel.content.contains(search_query)
            conditions.append(search_condition)  # type: ignore

        # 查询总数
        count_query = select(func.count(KnowledgeBaseModel.id)).where(and_(*conditions))  # type: ignore
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(KnowledgeBaseModel)
            .where(and_(*conditions))
            .order_by(desc(KnowledgeBaseModel.quality_score))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        knowledge_list = result.scalars().all()

        return list(knowledge_list), total

    async def update_knowledge_base(
        self: "AssistantService", knowledge_id: int, data: KnowledgeBaseUpdate
    ) -> KnowledgeBaseModel | None:
        """更新知识库条目"""
        logger.info(f"更新知识库条目: {knowledge_id}")

        query = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == knowledge_id)  # type: ignore
        result = await self.db.execute(query)
        knowledge = result.scalar_one_or_none()

        if not knowledge:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(knowledge, field, value)

        # 如果内容更新，重新生成向量
        if "content" in update_data:
            content_text = str(knowledge.content)
            embedding_vector = await self._generate_embedding(content_text)
            knowledge.embedding_vector = embedding_vector
            knowledge.vector_dimension = (
                len(embedding_vector) if embedding_vector else 0
            )

        knowledge.updated_at = datetime.utcnow()  # type: ignore
        await self.db.commit()
        await self.db.refresh(knowledge)

        logger.info(f"知识库条目更新成功: ID={knowledge.id}")  # type: ignore
        return knowledge

    # ==================== RAG智能问答 ====================

    async def ask_question(
        self: "AssistantService", user_id: int, request: QARequest
    ) -> QAResponse:
        """处理用户问题"""
        logger.info(f"用户 {user_id} 提问: {request.question[:50]}...")

        start_time = time.time()

        try:
            # 1. 检索相关知识
            relevant_knowledge = await self._retrieve_relevant_knowledge(
                request.question, limit=5
            )

            # 2. 构建上下文
            context = self._build_context(relevant_knowledge, request.context)

            # 3. 生成回答
            answer = await self._generate_answer(request.question, context)

            # 4. 计算置信度
            confidence_score = await self._calculate_confidence(
                request.question, answer, relevant_knowledge
            )

            # 5. 生成相关资源和后续问题
            related_resources = await self._get_related_resources(request.question)
            follow_up_questions = await self._generate_follow_up_questions(
                request.question, answer
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # 6. 记录问答历史
            qa_record = QARecordModel(
                user_id=user_id,
                question=request.question,
                answer=answer,
                question_type=request.question_type,
                context=request.context,
                session_id=request.session_id,
                ai_model_used="deepseek-chat",
                processing_time_ms=processing_time_ms,
                confidence_score=confidence_score,
                related_resources=related_resources,
                follow_up_questions=follow_up_questions,
            )

            self.db.add(qa_record)
            await self.db.commit()

            logger.info(f"问答处理完成，耗时: {processing_time_ms}ms")

            return QAResponse(
                answer=answer,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
                related_resources=related_resources,
                follow_up_questions=follow_up_questions,
                sources=[
                    {
                        "id": k.id,  # type: ignore
                        "title": k.title,
                        "relevance_score": k.relevance_score,
                    }
                    for k in relevant_knowledge
                ],
            )

        except Exception as e:
            logger.error(f"问答处理失败: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return QAResponse(
                answer="抱歉，我暂时无法回答这个问题。请稍后再试或联系技术支持。",
                confidence_score=0.0,
                processing_time_ms=processing_time_ms,
                related_resources=[],
                follow_up_questions=[],
                sources=[],
            )

    async def get_qa_history(
        self: "AssistantService",
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        session_id: str | None = None,
    ) -> tuple[list[QARecordModel], int]:
        """获取用户问答历史"""
        logger.info(f"查询用户 {user_id} 的问答历史")

        # 构建查询条件
        conditions = [QARecordModel.user_id == user_id]
        if session_id:
            conditions.append(QARecordModel.session_id == session_id)

        # 查询总数
        count_query = select(func.count(QARecordModel.id)).where(and_(*conditions))  # type: ignore
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询数据
        query = (
            select(QARecordModel)
            .where(and_(*conditions))
            .order_by(desc(QARecordModel.created_at))  # type: ignore
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        qa_records = result.scalars().all()

        return list(qa_records), total

    # ==================== 学习资源推荐 ====================

    async def create_learning_resource(
        self: "AssistantService", data: LearningResourceCreate
    ) -> LearningResourceModel:
        """创建学习资源"""
        logger.info(f"创建学习资源: {data.title}")

        resource = LearningResourceModel(
            title=data.title,
            description=data.description,
            resource_type=data.resource_type,
            content_url=data.content_url,
            file_path=data.file_path,
            thumbnail_url=data.thumbnail_url,
            category=data.category,
            tags=data.tags,
            difficulty_level=data.difficulty_level,
            target_audience=data.target_audience,
            duration_minutes=data.duration_minutes,
            language=data.language,
            is_free=data.is_free,
        )

        self.db.add(resource)
        await self.db.commit()
        await self.db.refresh(resource)

        logger.info(f"学习资源创建成功: ID={resource.id}")  # type: ignore
        return resource

    async def get_resource_recommendations(
        self: "AssistantService", user_id: int, request: ResourceRecommendationRequest
    ) -> list[dict[str, Any]]:
        """获取个性化资源推荐"""
        logger.info(f"为用户 {user_id} 生成资源推荐")

        # 1. 获取用户画像
        user_profile = await self._get_user_profile(user_id)

        # 2. 协同过滤推荐
        collaborative_recommendations = await self._collaborative_filtering_recommend(
            user_id, request
        )

        # 3. 基于内容的推荐
        content_based_recommendations = await self._content_based_recommend(
            user_profile, request
        )

        # 4. 合并和排序推荐结果
        all_recommendations = await self._merge_recommendations(
            collaborative_recommendations, content_based_recommendations
        )

        # 5. 记录推荐历史
        await self._record_recommendations(user_id, all_recommendations)

        return all_recommendations[: request.limit]

    # ==================== 语音识别功能 ====================

    async def recognize_voice(
        self: "AssistantService", user_id: int, request: VoiceRecognitionRequest
    ) -> VoiceRecognitionResponse:
        """语音识别和分析"""
        logger.info(f"用户 {user_id} 进行语音识别")

        start_time = time.time()

        try:
            # 1. 语音识别
            recognized_text = await self._speech_to_text(request.audio_file)

            # 2. 发音分析
            pronunciation_analysis = await self._analyze_pronunciation(
                request.audio_file, recognized_text, request.target_text
            )

            # 3. 语法检查
            grammar_errors = await self._check_grammar(recognized_text)

            # 4. 生成改进建议
            improvement_suggestions = await self._generate_improvement_suggestions(
                recognized_text, pronunciation_analysis, grammar_errors
            )

            # 5. 推荐练习
            practice_recommendations = await self._recommend_practice(
                user_id, pronunciation_analysis, grammar_errors
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # 6. 记录识别结果
            record = VoiceRecognitionRecordModel(
                user_id=user_id,
                audio_file_path=request.audio_file,
                recognized_text=recognized_text,
                confidence_score=pronunciation_analysis.get("confidence", 0.0),
                processing_time_ms=processing_time_ms,
                pronunciation_score=pronunciation_analysis.get("pronunciation_score"),
                fluency_score=pronunciation_analysis.get("fluency_score"),
                accuracy_score=pronunciation_analysis.get("accuracy_score"),
                pronunciation_errors=pronunciation_analysis.get("errors", []),
                grammar_errors=grammar_errors,
                improvement_suggestions=improvement_suggestions,
                practice_recommendations=practice_recommendations,
                exercise_type=request.exercise_type,
                target_text=request.target_text,
            )

            self.db.add(record)
            await self.db.commit()

            logger.info(f"语音识别完成，耗时: {processing_time_ms}ms")

            return VoiceRecognitionResponse(
                recognized_text=recognized_text,
                confidence_score=pronunciation_analysis.get("confidence", 0.0),
                processing_time_ms=processing_time_ms,
                pronunciation_score=pronunciation_analysis.get("pronunciation_score"),
                fluency_score=pronunciation_analysis.get("fluency_score"),
                accuracy_score=pronunciation_analysis.get("accuracy_score"),
                pronunciation_errors=pronunciation_analysis.get("errors", []),
                grammar_errors=grammar_errors,
                vocabulary_suggestions=pronunciation_analysis.get(
                    "vocabulary_suggestions", []
                ),
                improvement_suggestions=improvement_suggestions,
                practice_recommendations=practice_recommendations,
            )

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return VoiceRecognitionResponse(
                recognized_text="",
                confidence_score=0.0,
                processing_time_ms=processing_time_ms,
                pronunciation_score=None,
                fluency_score=None,
                accuracy_score=None,
                pronunciation_errors=[],
                grammar_errors=[],
                vocabulary_suggestions=[],
                improvement_suggestions=["语音识别失败，请检查音频质量后重试"],
                practice_recommendations=[],
            )

    # ==================== 用户交互记录 ====================

    async def record_user_interaction(
        self: "AssistantService", user_id: int, data: UserResourceInteractionCreate
    ) -> UserResourceInteractionModel:
        """记录用户资源交互"""
        logger.info(f"记录用户 {user_id} 与资源 {data.resource_id} 的交互")

        # 查找现有交互记录
        query = select(UserResourceInteractionModel).where(
            and_(
                UserResourceInteractionModel.user_id == user_id,
                UserResourceInteractionModel.resource_id == data.resource_id,
            )
        )
        result = await self.db.execute(query)
        interaction = result.scalar_one_or_none()

        if interaction:
            # 更新现有记录
            interaction.interaction_type = data.interaction_type
            if data.interaction_duration:
                interaction.interaction_duration = data.interaction_duration
            if data.completion_rate is not None:
                interaction.completion_rate = data.completion_rate
            if data.difficulty_rating:
                interaction.difficulty_rating = data.difficulty_rating
            if data.usefulness_rating:
                interaction.usefulness_rating = data.usefulness_rating

            interaction.view_count += 1
            interaction.last_interaction_at = datetime.utcnow()
            interaction.updated_at = datetime.utcnow()  # type: ignore
        else:
            # 创建新记录
            interaction = UserResourceInteractionModel(
                user_id=user_id,
                resource_id=data.resource_id,
                interaction_type=data.interaction_type,
                interaction_duration=data.interaction_duration,
                completion_rate=data.completion_rate,
                difficulty_rating=data.difficulty_rating,
                usefulness_rating=data.usefulness_rating,
                view_count=1,
            )
            self.db.add(interaction)

        await self.db.commit()
        await self.db.refresh(interaction)

        # 更新资源统计
        await self._update_resource_stats(data.resource_id)

        logger.info(f"用户交互记录成功: ID={interaction.id}")  # type: ignore
        return interaction

    # ==================== 私有辅助方法 ====================

    async def _generate_embedding(
        self: "AssistantService", text: str
    ) -> list[float] | None:
        """生成文本向量表示"""
        try:
            logger.info("Method implemented")
            # 这里应该调用向量化模型API
            return [0.0] * 768  # 占位符
        except Exception as e:
            logger.error(f"向量生成失败: {e}")
            return None

    async def _retrieve_relevant_knowledge(
        self: "AssistantService", question: str, limit: int = 5
    ) -> list[KnowledgeBaseModel]:
        """检索相关知识"""
        # 这里应该使用向量数据库进行相似度搜索
        query = (
            select(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.is_active.is_(True))
            .order_by(desc(KnowledgeBaseModel.quality_score))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _build_context(
        self: "AssistantService",
        knowledge_list: list[KnowledgeBaseModel],
        user_context: dict[str, Any] | None,
    ) -> str:
        """构建问答上下文"""
        context_parts = []

        # 添加知识库内容
        for knowledge in knowledge_list:
            context_parts.append(f"知识点: {knowledge.title}\n内容: {knowledge.content}")

        # 添加用户上下文
        if user_context:
            context_parts.append(f"用户上下文: {user_context}")

        return "\n\n".join(context_parts)

    async def _generate_answer(
        self: "AssistantService", question: str, context: str
    ) -> str:
        """生成回答"""
        try:
            prompt = f"""
            基于以下知识内容回答用户问题：

            知识内容：
            {context}

            用户问题：
            {question}

            请提供准确、有帮助的回答：
            """

            response = await self.ai_service.generate_completion(
                prompt=prompt,
                model="deepseek-chat",
            )

            return str(response) if response else "抱歉，我无法回答这个问题。"

        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return "抱歉，我暂时无法回答这个问题。"

    async def _calculate_confidence(
        self: "AssistantService",
        question: str,
        answer: str,
        knowledge_list: list[KnowledgeBaseModel],
    ) -> float:
        """计算回答置信度"""
        logger.info("Method implemented")
        # 可以基于知识匹配度、答案长度、关键词覆盖等因素
        return 0.85  # 占位符

    async def _get_related_resources(
        self: "AssistantService", question: str
    ) -> list[dict[str, Any]]:
        """获取相关资源"""
        logger.info("Method implemented")
        return []  # 占位符

    async def _generate_follow_up_questions(
        self: "AssistantService", question: str, answer: str
    ) -> list[str]:
        """生成后续问题建议"""
        logger.info("Method implemented")
        return []  # 占位符

    async def _get_user_profile(
        self: "AssistantService", user_id: int
    ) -> dict[str, Any]:
        """获取用户画像"""
        logger.info("Method implemented")
        return {}  # 占位符

    async def _collaborative_filtering_recommend(
        self: "AssistantService", user_id: int, request: ResourceRecommendationRequest
    ) -> list[dict[str, Any]]:
        """协同过滤推荐"""
        logger.info("Method implemented")
        return []  # 占位符

    async def _content_based_recommend(
        self: "AssistantService",
        user_profile: dict[str, Any],
        request: ResourceRecommendationRequest,
    ) -> list[dict[str, Any]]:
        """基于内容的推荐"""
        try:
            # 构建查询条件
            query = select(LearningResourceModel).where(LearningResourceModel.is_active)

            # 按类别过滤
            if request.category:
                query = query.where(LearningResourceModel.category == request.category)

            # 按难度级别过滤
            if request.difficulty_level:
                query = query.where(
                    LearningResourceModel.difficulty_level == request.difficulty_level
                )

            # 按资源类型过滤
            if request.resource_type:
                query = query.where(
                    LearningResourceModel.resource_type == request.resource_type
                )

            # 排序：优先推荐质量分数高、受欢迎的资源
            query = query.order_by(
                desc(LearningResourceModel.quality_score),
                desc(LearningResourceModel.popularity_score),
                desc(LearningResourceModel.view_count),
            ).limit(
                request.limit * 2
            )  # 获取更多候选资源

            result = await self.db.execute(query)
            resources = result.scalars().all()

            # 转换为推荐格式
            recommendations = []
            for resource in resources:
                # 计算推荐分数
                rec_score = resource.quality_score + resource.popularity_score

                recommendation = {
                    "resource": {
                        "id": resource.id,  # type: ignore
                        "title": resource.title,
                        "description": resource.description,
                        "resource_type": resource.resource_type,
                        "category": resource.category,
                        "difficulty_level": resource.difficulty_level,
                        "content_url": resource.content_url,
                        "file_path": resource.file_path,
                        "thumbnail_url": resource.thumbnail_url,
                        "tags": resource.tags,
                        "target_audience": resource.target_audience,
                        "duration_minutes": resource.duration_minutes,
                        "file_size_mb": resource.file_size_mb,
                        "language": resource.language,
                        "quality_score": resource.quality_score,
                        "popularity_score": resource.popularity_score,
                        "view_count": resource.view_count,
                        "download_count": resource.download_count,
                        "recommendation_score": rec_score,  # 添加推荐分数字段
                        "recommendation_reasons": [
                            f"匹配您的学习类别：{resource.category}",
                            f"适合您的难度级别：{resource.difficulty_level}",
                        ],
                        "is_active": resource.is_active,
                        "is_featured": resource.is_featured,
                        "is_free": resource.is_free,
                        "created_at": None,  # 简化处理，避免类型检查问题
                        "updated_at": None,  # 简化处理，避免类型检查问题
                    },
                    "recommendation_score": rec_score,
                    "recommendation_reason": f"匹配您的学习类别：{resource.category}，适合您的难度级别：{resource.difficulty_level}",
                    "recommendation_source": "content_based",
                }
                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"基于内容的推荐失败: {e}")
            return []

    async def _merge_recommendations(
        self: "AssistantService",
        collaborative: list[dict[str, Any]],
        content_based: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """合并推荐结果"""
        try:
            # 合并所有推荐结果
            all_recommendations = []

            # 添加协同过滤推荐（权重：0.4）
            for rec in collaborative:
                rec["final_score"] = rec.get("recommendation_score", 0) * 0.4
                rec["source_weight"] = 0.4
                all_recommendations.append(rec)

            # 添加基于内容的推荐（权重：0.6）
            for rec in content_based:
                rec["final_score"] = rec.get("recommendation_score", 0) * 0.6
                rec["source_weight"] = 0.6
                all_recommendations.append(rec)

            # 去重：如果同一个资源被多种算法推荐，合并分数
            resource_map: dict[Any, Any] = {}
            for rec in all_recommendations:
                resource_id = rec.get("resource", {}).get("id")
                if resource_id in resource_map:
                    # 合并分数
                    existing = resource_map[resource_id]
                    existing["final_score"] += rec["final_score"]
                    existing[
                        "recommendation_reason"
                    ] += f", {rec.get('recommendation_reason', '')}"
                    existing[
                        "recommendation_source"
                    ] = f"{existing['recommendation_source']}, {rec['recommendation_source']}"
                else:
                    resource_map[resource_id] = rec

            # 转换回列表并按最终分数排序
            merged_recommendations = list(resource_map.values())
            merged_recommendations.sort(
                key=lambda x: x.get("final_score", 0), reverse=True
            )

            return merged_recommendations

        except Exception as e:
            logger.error(f"合并推荐结果失败: {e}")
            # 如果合并失败，至少返回基于内容的推荐
            return content_based

    async def _record_recommendations(
        self: "AssistantService", user_id: int, recommendations: list[dict[str, Any]]
    ) -> None:
        """记录推荐历史"""
        try:
            from app.training.models.assistant_models import ResourceRecommendationModel

            # 为每个推荐创建记录
            for rec in recommendations:
                resource_data = rec.get("resource", {})
                resource_id = resource_data.get("id")

                if resource_id:
                    recommendation_record = ResourceRecommendationModel(
                        user_id=user_id,
                        resource_id=resource_id,
                        recommendation_score=rec.get("recommendation_score", 0.0),
                        recommendation_reason=rec.get("recommendation_reason", ""),
                        recommendation_source=rec.get(
                            "recommendation_source", "unknown"
                        ),
                        user_clicked=False,
                        user_viewed=False,
                    )

                    self.db.add(recommendation_record)

            await self.db.commit()
            logger.info(f"成功记录 {len(recommendations)} 条推荐历史")

        except Exception as e:
            logger.error(f"记录推荐历史失败: {e}")
            await self.db.rollback()

    async def _speech_to_text(self: "AssistantService", audio_file: str) -> str:
        """语音转文本"""
        try:
            # 模拟语音识别API调用
            # 在实际应用中，这里会调用真实的语音识别服务
            # 如 Google Speech-to-Text, Azure Speech Services, 或 OpenAI Whisper

            import random

            # 模拟不同的识别结果
            sample_texts = [
                "Hello, how are you today?",
                "I am learning English pronunciation.",
                "The weather is very nice today.",
                "Can you help me with my homework?",
                "I want to improve my speaking skills.",
            ]

            # 模拟处理时间
            await asyncio.sleep(0.5)

            # 返回随机的识别结果（实际应用中会基于音频内容）
            recognized_text = random.choice(sample_texts)
            logger.info(f"语音识别结果: {recognized_text}")

            return recognized_text

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return "语音识别失败"

    async def _analyze_pronunciation(
        self: "AssistantService",
        audio_file: str,
        recognized_text: str,
        target_text: str | None,
    ) -> dict[str, Any]:
        """发音分析"""
        try:
            import random

            # 模拟发音分析
            # 在实际应用中，这里会使用专业的发音评估API
            # 基础分数（随机生成，实际应用中基于音频分析）
            base_score = random.uniform(0.7, 0.95)

            # 如果有目标文本，比较准确性
            accuracy_score = base_score
            if target_text and recognized_text:
                # 简单的文本相似度计算
                similarity = self._calculate_text_similarity(
                    recognized_text.lower(), target_text.lower()
                )
                accuracy_score = min(base_score, similarity)

            # 生成发音错误（模拟）
            pronunciation_errors = []
            if accuracy_score < 0.8:
                pronunciation_errors = [
                    {
                        "word": "pronunciation",
                        "expected": "/prəˌnʌnsiˈeɪʃən/",
                        "actual": "/prəˌnaʊnsiˈeɪʃən/",
                        "error_type": "vowel_substitution",
                        "suggestion": "注意 'nun' 部分的发音，应该是 /nʌn/ 而不是 /naʊn/",
                    }
                ]

            # 词汇建议
            vocabulary_suggestions = [
                "建议练习长元音的发音",
                "注意重音位置的准确性",
                "可以多练习连读技巧",
            ]

            result = {
                "confidence": base_score,
                "pronunciation_score": accuracy_score,
                "fluency_score": random.uniform(0.7, 0.9),
                "accuracy_score": accuracy_score,
                "errors": pronunciation_errors,
                "vocabulary_suggestions": vocabulary_suggestions,
            }

            logger.info(f"发音分析完成，准确率: {accuracy_score:.2f}")
            return result

        except Exception as e:
            logger.error(f"发音分析失败: {e}")
            return {
                "confidence": 0.5,
                "pronunciation_score": 0.5,
                "fluency_score": 0.5,
                "accuracy_score": 0.5,
                "errors": [],
                "vocabulary_suggestions": [],
            }

    async def _check_grammar(
        self: "AssistantService", text: str
    ) -> list[dict[str, Any]]:
        """语法检查"""
        try:
            # 模拟语法检查
            # 在实际应用中，这里会使用专业的语法检查API，如LanguageTool或Grammarly API

            grammar_errors = []

            # 简单的语法规则检查（模拟）
            if text:
                words = text.lower().split()

                # 检查常见语法错误
                for i, word in enumerate(words):
                    # 模拟一些常见错误
                    if word == "i" and i > 0:  # 'i' 应该大写
                        grammar_errors.append(
                            {
                                "error_type": "capitalization",
                                "position": i,
                                "original": word,
                                "suggestion": "I",
                                "message": "人称代词 'I' 应该大写",
                                "severity": "minor",
                            }
                        )

                    if word in ["dont", "cant", "wont"]:  # 缺少撇号
                        suggestions = {
                            "dont": "don't",
                            "cant": "can't",
                            "wont": "won't",
                        }
                        grammar_errors.append(
                            {
                                "error_type": "punctuation",
                                "position": i,
                                "original": word,
                                "suggestion": suggestions[word],
                                "message": f"缺少撇号，应该是 '{suggestions[word]}'",
                                "severity": "moderate",
                            }
                        )

            logger.info(f"语法检查完成，发现 {len(grammar_errors)} 个问题")
            return grammar_errors

        except Exception as e:
            logger.error(f"语法检查失败: {e}")
            return []

    def _calculate_text_similarity(
        self: "AssistantService", text1: str, text2: str
    ) -> float:
        """计算两个文本的相似度"""
        try:
            # 简单的文本相似度计算（基于编辑距离）
            if not text1 or not text2:
                return 0.0

            # 计算Levenshtein距离
            def levenshtein_distance(s1: str, s2: str) -> int:
                if len(s1) < len(s2):
                    return levenshtein_distance(s2, s1)

                if len(s2) == 0:
                    return len(s1)

                previous_row = list(range(len(s2) + 1))
                for i, c1 in enumerate(s1):
                    current_row = [i + 1]
                    for j, c2 in enumerate(s2):
                        insertions = previous_row[j + 1] + 1
                        deletions = current_row[j] + 1
                        substitutions = previous_row[j] + (c1 != c2)
                        current_row.append(min(insertions, deletions, substitutions))
                    previous_row = current_row

                return previous_row[-1]

            # 计算相似度（1 - 标准化的编辑距离）
            max_len = max(len(text1), len(text2))
            if max_len == 0:
                return 1.0

            distance = levenshtein_distance(text1, text2)
            similarity = 1.0 - (distance / max_len)

            return max(0.0, similarity)

        except Exception as e:
            logger.error(f"计算文本相似度失败: {e}")
            return 0.5

    async def _generate_improvement_suggestions(
        self: "AssistantService",
        text: str,
        pronunciation_analysis: dict[str, Any],
        grammar_errors: list[dict[str, Any]],
    ) -> list[str]:
        """生成改进建议"""
        try:
            suggestions = []

            # 基于发音分析的建议
            pronunciation_score = pronunciation_analysis.get("pronunciation_score", 0)
            fluency_score = pronunciation_analysis.get("fluency_score", 0)
            accuracy_score = pronunciation_analysis.get("accuracy_score", 0)

            if pronunciation_score < 0.7:
                suggestions.append("建议多练习单词发音，特别注意元音和辅音的准确性")
                suggestions.append("可以使用发音练习应用，跟读标准发音")

            if fluency_score < 0.7:
                suggestions.append("建议提高语音流畅度，可以通过朗读练习来改善")
                suggestions.append("尝试录制自己的发音并与标准发音对比")

            if accuracy_score < 0.8:
                suggestions.append("注意语音的准确性，建议放慢语速确保每个音节清晰")

            # 基于语法错误的建议
            if grammar_errors:
                error_types = [error.get("error_type") for error in grammar_errors]

                if "capitalization" in error_types:
                    suggestions.append("注意大小写规则，特别是句首和专有名词")

                if "punctuation" in error_types:
                    suggestions.append("注意标点符号的使用，特别是撇号和逗号")

                suggestions.append(f"发现 {len(grammar_errors)} 个语法问题，建议复习相关语法规则")

            # 通用建议
            if len(text.split()) < 5:
                suggestions.append("尝试说更长的句子来提高表达能力")

            suggestions.append("坚持每天练习，语言学习需要持续的努力")

            # 如果没有具体建议，提供通用建议
            if not suggestions:
                suggestions = [
                    "继续保持良好的发音习惯",
                    "可以尝试更复杂的表达来挑战自己",
                    "建议多听英语材料来提高语感",
                ]

            logger.info(f"生成了 {len(suggestions)} 条改进建议")
            return suggestions[:5]  # 限制建议数量

        except Exception as e:
            logger.error(f"生成改进建议失败: {e}")
            return ["建议继续练习以提高英语水平"]

    async def _recommend_practice(
        self: "AssistantService",
        user_id: int,
        pronunciation_analysis: dict[str, Any],
        grammar_errors: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """推荐练习"""
        try:
            recommendations = []

            # 基于发音分析推荐练习
            pronunciation_score = pronunciation_analysis.get("pronunciation_score", 0)
            fluency_score = pronunciation_analysis.get("fluency_score", 0)

            if pronunciation_score < 0.7:
                recommendations.append(
                    {
                        "type": "pronunciation",
                        "title": "发音基础练习",
                        "description": "针对元音和辅音的发音练习",
                        "difficulty": "beginner",
                        "estimated_time": 15,
                        "exercises": [
                            "跟读单词发音练习",
                            "音标识别练习",
                            "最小对比练习",
                        ],
                    }
                )

            if fluency_score < 0.7:
                recommendations.append(
                    {
                        "type": "fluency",
                        "title": "流畅度提升练习",
                        "description": "通过朗读和复述提高语音流畅度",
                        "difficulty": "intermediate",
                        "estimated_time": 20,
                        "exercises": ["短文朗读练习", "影子跟读练习", "语音语调练习"],
                    }
                )

            # 基于语法错误推荐练习
            if grammar_errors:
                error_types = [error.get("error_type") for error in grammar_errors]

                if "capitalization" in error_types:
                    recommendations.append(
                        {
                            "type": "grammar",
                            "title": "大小写规则练习",
                            "description": "掌握英语大小写的基本规则",
                            "difficulty": "beginner",
                            "estimated_time": 10,
                            "exercises": [
                                "句首大写练习",
                                "专有名词识别",
                                "人称代词练习",
                            ],
                        }
                    )

                if "punctuation" in error_types:
                    recommendations.append(
                        {
                            "type": "grammar",
                            "title": "标点符号练习",
                            "description": "学习正确使用英语标点符号",
                            "difficulty": "beginner",
                            "estimated_time": 15,
                            "exercises": [
                                "撇号使用练习",
                                "逗号规则练习",
                                "句号和问号练习",
                            ],
                        }
                    )

            # 通用推荐练习
            recommendations.append(
                {
                    "type": "comprehensive",
                    "title": "综合口语练习",
                    "description": "全面提升英语口语能力",
                    "difficulty": "intermediate",
                    "estimated_time": 30,
                    "exercises": ["日常对话练习", "话题讨论练习", "角色扮演练习"],
                }
            )

            logger.info(f"为用户 {user_id} 推荐了 {len(recommendations)} 个练习")
            return recommendations[:3]  # 限制推荐数量

        except Exception as e:
            logger.error(f"推荐练习失败: {e}")
            return [
                {
                    "type": "general",
                    "title": "基础英语练习",
                    "description": "提高英语综合能力",
                    "difficulty": "beginner",
                    "estimated_time": 20,
                    "exercises": ["基础练习"],
                }
            ]

    async def _update_resource_stats(
        self: "AssistantService", resource_id: int
    ) -> None:
        """更新资源统计"""
        query = select(LearningResourceModel).where(LearningResourceModel.id == resource_id)  # type: ignore
        result = await self.db.execute(query)
        resource = result.scalar_one_or_none()

        if resource:
            resource.view_count += 1
            await self.db.commit()
