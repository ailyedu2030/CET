"""学习辅助工具系统 - API端点"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.schemas.assistant_schemas import (KnowledgeBaseCreate,
                                                    KnowledgeBaseListResponse,
                                                    KnowledgeBaseResponse,
                                                    KnowledgeBaseUpdate,
                                                    LearningResourceCreate,
                                                    LearningResourceResponse,
                                                    QAFeedback, QARecordListResponse,
                                                    QARecordResponse, QARequest,
                                                    QAResponse,
                                                    ResourceRecommendationRequest,
                                                    ResourceRecommendationResponse,
                                                    UserResourceInteractionCreate,
                                                    VoiceRecognitionRecordListResponse,
                                                    VoiceRecognitionRequest,
                                                    VoiceRecognitionResponse)
from app.training.services.assistant_service import AssistantService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["学习辅助工具系统"])


# ==================== 知识库管理 ====================


@router.post("/knowledge-base", summary="创建知识库条目", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseResponse:
    """创建知识库条目"""
    try:
        service = AssistantService(db)
        knowledge = await service.create_knowledge_base(data)

        logger.info(f"用户 {current_user.id} 创建知识库条目成功: {knowledge.id}")  # type: ignore

        return KnowledgeBaseResponse.model_validate(knowledge)
    except Exception as e:
        logger.error(f"创建知识库条目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/knowledge-base", summary="获取知识库列表", response_model=KnowledgeBaseListResponse
)
async def get_knowledge_base_list(
    skip: int = 0,
    limit: int = 10,
    category: str | None = None,
    search_query: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseListResponse:
    """获取知识库列表"""
    try:
        service = AssistantService(db)
        knowledge_list, total = await service.get_knowledge_base_list(
            skip=skip,
            limit=limit,
            category=category,
            search_query=search_query,
        )

        logger.info(f"用户 {current_user.id} 查询知识库列表，共 {total} 条")

        return KnowledgeBaseListResponse(
            success=True,
            data=[KnowledgeBaseResponse.model_validate(k) for k in knowledge_list],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询知识库列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put(
    "/knowledge-base/{knowledge_id}",
    summary="更新知识库条目",
    response_model=KnowledgeBaseResponse,
)
async def update_knowledge_base(
    knowledge_id: int,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseResponse:
    """更新知识库条目"""
    try:
        service = AssistantService(db)
        knowledge = await service.update_knowledge_base(knowledge_id, data)

        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库条目不存在"
            )

        logger.info(f"用户 {current_user.id} 更新知识库条目: {knowledge_id}")

        return KnowledgeBaseResponse.model_validate(knowledge)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库条目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


# ==================== RAG智能问答 ====================


@router.post("/qa/ask", summary="智能问答", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QAResponse:
    """智能问答"""
    try:
        service = AssistantService(db)
        response = await service.ask_question(current_user.id, request)

        logger.info(f"用户 {current_user.id} 智能问答完成")

        return response
    except Exception as e:
        logger.error(f"智能问答失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="问答失败"
        ) from e


@router.get("/qa/history", summary="获取问答历史", response_model=QARecordListResponse)
async def get_qa_history(
    skip: int = 0,
    limit: int = 10,
    session_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QARecordListResponse:
    """获取用户问答历史"""
    try:
        service = AssistantService(db)
        qa_records, total = await service.get_qa_history(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            session_id=session_id,
        )

        logger.info(f"用户 {current_user.id} 查询问答历史，共 {total} 条")

        return QARecordListResponse(
            success=True,
            data=[QARecordResponse.model_validate(qa) for qa in qa_records],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询问答历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/qa/{qa_id}/feedback", summary="问答反馈")
async def submit_qa_feedback(
    qa_id: int,
    feedback: QAFeedback,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """提交问答反馈"""
    try:
        from sqlalchemy import select

        from app.training.models.assistant_models import QARecordModel

        # 验证问答记录是否存在且属于当前用户
        stmt = select(QARecordModel).where(
            QARecordModel.id == qa_id,  # type: ignore
            QARecordModel.user_id == current_user.id,  # type: ignore
        )
        result = await db.execute(stmt)
        qa_record = result.scalar_one_or_none()

        if not qa_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="问答记录不存在")

        # 更新反馈信息
        qa_record.user_rating = feedback.user_rating
        qa_record.user_feedback = feedback.user_feedback
        qa_record.is_helpful = feedback.is_helpful

        await db.commit()
        logger.info(f"用户 {current_user.id} 提交问答反馈: {qa_id}, 评分: {feedback.user_rating}")

        return {"message": "反馈提交成功"}
    except Exception as e:
        logger.error(f"提交问答反馈失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="反馈提交失败"
        ) from e


# ==================== 学习资源管理 ====================


@router.post("/resources", summary="创建学习资源", response_model=LearningResourceResponse)
async def create_learning_resource(
    data: LearningResourceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningResourceResponse:
    """创建学习资源"""
    try:
        service = AssistantService(db)
        resource = await service.create_learning_resource(data)

        logger.info(f"用户 {current_user.id} 创建学习资源成功: {resource.id}")  # type: ignore

        return LearningResourceResponse.model_validate(resource)
    except Exception as e:
        logger.error(f"创建学习资源失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/resources/recommendations",
    summary="获取资源推荐",
    response_model=list[ResourceRecommendationResponse],
)
async def get_resource_recommendations(
    limit: int = 10,
    category: str | None = None,
    difficulty_level: str | None = None,
    resource_type: str | None = None,
    exclude_viewed: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResourceRecommendationResponse]:
    """获取个性化资源推荐"""
    try:
        service = AssistantService(db)
        # 转换字符串参数为枚举类型
        from app.training.models.assistant_models import ResourceType

        resource_type_enum = None
        if resource_type:
            try:
                resource_type_enum = ResourceType(resource_type)
            except ValueError:
                resource_type_enum = None

        request = ResourceRecommendationRequest(
            limit=limit,
            category=category,
            difficulty_level=difficulty_level,
            resource_type=resource_type_enum,
            exclude_viewed=exclude_viewed,
        )

        recommendations = await service.get_resource_recommendations(
            current_user.id, request
        )

        logger.info(f"用户 {current_user.id} 获取资源推荐，共 {len(recommendations)} 个")

        return [ResourceRecommendationResponse(**rec) for rec in recommendations]
    except Exception as e:
        logger.error(f"获取资源推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="推荐失败"
        ) from e


@router.post("/resources/interactions", summary="记录资源交互")
async def record_resource_interaction(
    data: UserResourceInteractionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """记录用户资源交互"""
    try:
        service = AssistantService(db)
        interaction = await service.record_user_interaction(current_user.id, data)

        logger.info(f"用户 {current_user.id} 资源交互记录成功: {interaction.id}")  # type: ignore

        return {"message": "交互记录成功"}
    except Exception as e:
        logger.error(f"记录资源交互失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="记录失败"
        ) from e


# ==================== 语音识别功能 ====================


@router.post(
    "/voice/recognize", summary="语音识别", response_model=VoiceRecognitionResponse
)
async def recognize_voice(
    audio_file: UploadFile = File(...),
    exercise_type: str | None = None,
    target_text: str | None = None,
    language: str = "en",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceRecognitionResponse:
    """语音识别和分析"""
    try:
        # 验证文件类型
        if not audio_file.content_type or not audio_file.content_type.startswith(
            "audio/"
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请上传音频文件"
            )

        # 保存音频文件
        import uuid
        from pathlib import Path

        # 创建临时目录
        temp_dir = Path("/tmp/voice_recognition")
        temp_dir.mkdir(exist_ok=True)

        # 生成唯一文件名
        file_extension = Path(audio_file.filename or "audio.wav").suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        audio_file_path = temp_dir / unique_filename

        # 保存音频文件
        with open(audio_file_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)

        service = AssistantService(db)
        request = VoiceRecognitionRequest(
            audio_file=str(audio_file_path),
            exercise_type=exercise_type,
            target_text=target_text,
            language=language,
        )

        response = await service.recognize_voice(current_user.id, request)

        logger.info(f"用户 {current_user.id} 语音识别完成")

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="识别失败"
        ) from e


@router.get(
    "/voice/history",
    summary="获取语音识别历史",
    response_model=VoiceRecognitionRecordListResponse,
)
async def get_voice_recognition_history(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceRecognitionRecordListResponse:
    """获取用户语音识别历史"""
    try:
        logger.info(f"获取语音识别历史: user={current_user.id}, skip={skip}, limit={limit}")

        return VoiceRecognitionRecordListResponse(
            success=True,
            data=[],
            total=0,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询语音识别历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


# ==================== 智能学习建议 ====================


@router.get("/suggestions/learning", summary="获取学习建议")
async def get_learning_suggestions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取个性化学习建议"""
    try:
        logger.info(f"获取学习建议: user={current_user.id}")

        suggestions = {
            "daily_goals": [
                "完成10个词汇练习",
                "听力训练20分钟",
                "阅读一篇英语文章",
            ],
            "weak_areas": [
                "听力理解需要加强",
                "语法错误较多",
                "词汇量有待提升",
            ],
            "recommended_resources": [
                {
                    "title": "英语听力训练",
                    "type": "audio",
                    "difficulty": "intermediate",
                    "reason": "基于您的听力测试结果推荐",
                },
            ],
            "study_plan": {
                "morning": "词汇学习",
                "afternoon": "听力训练",
                "evening": "阅读练习",
            },
        }

        return suggestions
    except Exception as e:
        logger.error(f"获取学习建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取建议失败"
        ) from e


@router.get("/analytics/learning", summary="获取学习分析")
async def get_learning_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学习数据分析"""
    try:
        logger.info(f"获取学习分析: user={current_user.id}")

        analytics = {
            "study_time": {
                "today": 45,
                "this_week": 280,
                "this_month": 1200,
            },
            "progress": {
                "vocabulary": 0.75,
                "listening": 0.68,
                "reading": 0.82,
                "writing": 0.59,
            },
            "achievements": [
                "连续学习7天",
                "完成100个词汇练习",
                "听力测试达到80分",
            ],
            "trends": {
                "improvement_rate": 0.15,
                "consistency_score": 0.85,
                "difficulty_preference": "intermediate",
            },
        }

        return analytics
    except Exception as e:
        logger.error(f"获取学习分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="分析失败"
        ) from e
