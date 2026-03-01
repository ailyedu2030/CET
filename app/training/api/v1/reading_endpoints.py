"""阅读理解训练 - API端点"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.schemas.reading_schemas import (
    ReadingAnswerRecordCreate,
    ReadingPassageCreate,
    ReadingPassageListResponse,
    ReadingPassageResponse,
    ReadingPassageUpdate,
    ReadingQuestionCreate,
    ReadingQuestionResponse,
    ReadingQuestionUpdate,
    ReadingRecommendation,
    ReadingStatistics,
    ReadingTrainingPlanCreate,
    ReadingTrainingPlanListResponse,
    ReadingTrainingPlanResponse,
    ReadingTrainingRecordCreate,
    ReadingTrainingRecordResponse,
    ReadingTrainingSession,
)
from app.training.services.reading_service import ReadingService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["阅读理解训练"])


# ==================== 阅读文章管理 ====================


@router.get("/passages", summary="获取阅读文章列表", response_model=ReadingPassageListResponse)
async def get_reading_passages(
    skip: int = 0,
    limit: int = 10,
    theme: str | None = None,
    difficulty: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingPassageListResponse:
    """获取阅读文章列表"""
    try:
        service = ReadingService(db)
        # 转换字符串参数为枚举类型
        from app.training.models.reading_models import ReadingDifficulty, ReadingTheme

        theme_enum = None
        if theme:
            try:
                theme_enum = ReadingTheme(theme)
            except ValueError:
                theme_enum = None

        difficulty_enum = None
        if difficulty:
            try:
                difficulty_enum = ReadingDifficulty(difficulty)
            except ValueError:
                difficulty_enum = None

        passages, total = await service.get_passages(
            skip=skip,
            limit=limit,
            theme=theme_enum,
            difficulty=difficulty_enum,
        )

        logger.info(f"用户 {current_user.id} 查询阅读文章列表，共 {total} 篇")

        return ReadingPassageListResponse(
            success=True,
            data=[ReadingPassageResponse.model_validate(p) for p in passages],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询阅读文章列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/passages", summary="创建阅读文章", response_model=ReadingPassageResponse)
async def create_reading_passage(
    data: ReadingPassageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingPassageResponse:
    """创建阅读文章"""
    try:
        service = ReadingService(db)
        passage = await service.create_passage(data)

        logger.info(f"用户 {current_user.id} 创建阅读文章成功: {passage.id}")  # type: ignore

        return ReadingPassageResponse.model_validate(passage)
    except Exception as e:
        logger.error(f"创建阅读文章失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/passages/{passage_id}",
    summary="获取阅读文章详情",
    response_model=ReadingPassageResponse,
)
async def get_reading_passage_detail(
    passage_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingPassageResponse:
    """获取阅读文章详情"""
    try:
        service = ReadingService(db)
        passage = await service.get_passage(passage_id)

        if not passage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        logger.info(f"用户 {current_user.id} 查询阅读文章详情: {passage_id}")

        return ReadingPassageResponse.model_validate(passage)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询阅读文章详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put(
    "/passages/{passage_id}",
    summary="更新阅读文章",
    response_model=ReadingPassageResponse,
)
async def update_reading_passage(
    passage_id: int,
    data: ReadingPassageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingPassageResponse:
    """更新阅读文章"""
    try:
        service = ReadingService(db)
        passage = await service.update_passage(passage_id, data)

        if not passage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        logger.info(f"用户 {current_user.id} 更新阅读文章: {passage_id}")

        return ReadingPassageResponse.model_validate(passage)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新阅读文章失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


# ==================== 阅读题目管理 ====================


@router.post(
    "/passages/{passage_id}/questions",
    summary="创建阅读题目",
    response_model=ReadingQuestionResponse,
)
async def create_reading_question(
    passage_id: int,
    data: ReadingQuestionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingQuestionResponse:
    """创建阅读题目"""
    try:
        # 确保passage_id一致
        data.passage_id = passage_id

        service = ReadingService(db)
        question = await service.create_question(data)

        logger.info(f"用户 {current_user.id} 为文章 {passage_id} 创建题目成功: {question.id}")  # type: ignore

        return ReadingQuestionResponse.model_validate(question)
    except Exception as e:
        logger.error(f"创建阅读题目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get("/passages/{passage_id}/questions", summary="获取文章题目列表")
async def get_passage_questions(
    passage_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[ReadingQuestionResponse]]:
    """获取文章的所有题目"""
    try:
        service = ReadingService(db)
        questions = await service.get_questions_by_passage(passage_id)

        logger.info(f"用户 {current_user.id} 查询文章 {passage_id} 的题目，共 {len(questions)} 道")

        return {
            "questions": [ReadingQuestionResponse.model_validate(q) for q in questions]
        }
    except Exception as e:
        logger.error(f"查询文章题目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put(
    "/questions/{question_id}",
    summary="更新阅读题目",
    response_model=ReadingQuestionResponse,
)
async def update_reading_question(
    question_id: int,
    data: ReadingQuestionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingQuestionResponse:
    """更新阅读题目"""
    try:
        service = ReadingService(db)
        question = await service.update_question(question_id, data)

        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

        logger.info(f"用户 {current_user.id} 更新阅读题目: {question_id}")

        return ReadingQuestionResponse.model_validate(question)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新阅读题目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


# ==================== 训练计划管理 ====================


@router.get(
    "/plans", summary="获取训练计划列表", response_model=ReadingTrainingPlanListResponse
)
async def get_training_plans(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingTrainingPlanListResponse:
    """获取用户的阅读训练计划列表"""
    try:
        service = ReadingService(db)
        plans, total = await service.get_user_training_plans(
            current_user.id, skip, limit
        )

        logger.info(f"用户 {current_user.id} 查询训练计划列表，共 {total} 个")

        return ReadingTrainingPlanListResponse(
            success=True,
            data=[ReadingTrainingPlanResponse.model_validate(p) for p in plans],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询训练计划列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/plans", summary="创建训练计划", response_model=ReadingTrainingPlanResponse)
async def create_training_plan(
    data: ReadingTrainingPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingTrainingPlanResponse:
    """创建阅读训练计划"""
    try:
        service = ReadingService(db)
        plan = await service.create_training_plan(current_user.id, data)

        logger.info(f"用户 {current_user.id} 创建训练计划成功: {plan.id}")  # type: ignore

        return ReadingTrainingPlanResponse.model_validate(plan)
    except Exception as e:
        logger.error(f"创建训练计划失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


# ==================== 训练会话管理 ====================


@router.post("/training/start", summary="开始阅读训练", response_model=ReadingTrainingSession)
async def start_reading_training(
    data: ReadingTrainingRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingTrainingSession:
    """开始阅读训练会话"""
    try:
        service = ReadingService(db)
        session = await service.start_training_session(current_user.id, data)

        logger.info(f"用户 {current_user.id} 开始阅读训练: passage={data.passage_id}")

        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"开始阅读训练失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="开始训练失败"
        ) from e


@router.put("/training/{training_record_id}/submit", summary="提交阅读答案")
async def submit_reading_answers(
    training_record_id: int,
    answers: list[ReadingAnswerRecordCreate],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """提交阅读训练答案"""
    try:
        service = ReadingService(db)
        training_record = await service.submit_answers(
            current_user.id, training_record_id, answers
        )

        if not training_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练记录不存在")

        logger.info(f"用户 {current_user.id} 提交阅读答案: {training_record_id}")

        return {
            "success": True,
            "data": ReadingTrainingRecordResponse.model_validate(training_record),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交阅读答案失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交失败"
        ) from e


# ==================== 统计和推荐 ====================


@router.get("/statistics", summary="获取阅读统计数据", response_model=ReadingStatistics)
async def get_reading_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingStatistics:
    """获取用户阅读统计数据"""
    try:
        service = ReadingService(db)
        statistics = await service.get_user_statistics(current_user.id)

        logger.info(f"用户 {current_user.id} 查询阅读统计")

        return statistics
    except Exception as e:
        logger.error(f"查询阅读统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.get("/recommendations", summary="获取阅读推荐", response_model=ReadingRecommendation)
async def get_reading_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingRecommendation:
    """获取个性化阅读推荐"""
    try:
        service = ReadingService(db)
        recommendations = await service.get_user_recommendations(current_user.id)

        logger.info(f"用户 {current_user.id} 获取阅读推荐")

        return recommendations
    except Exception as e:
        logger.error(f"获取阅读推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取推荐失败"
        ) from e
