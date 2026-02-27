"""英语四级写作标准库 - API端点"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.training.models.writing_models import WritingDifficulty, WritingType
from app.training.schemas.writing_schemas import (
    GrammarCheckResult,
    WritingRecommendation,
    WritingStatistics,
    WritingSubmissionCreate,
    WritingSubmissionListResponse,
    WritingSubmissionResponse,
    WritingTaskCreate,
    WritingTaskListResponse,
    WritingTaskResponse,
    WritingTemplateCreate,
    WritingTemplateListResponse,
    WritingTemplateResponse,
    WritingTemplateUpdate,
    WritingVocabularyCreate,
    WritingVocabularyListResponse,
    WritingVocabularyResponse,
)
from app.training.services.writing_service import WritingService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["英语四级写作标准库"])


# ==================== 写作模板管理 ====================


@router.get("/templates", summary="获取写作模板列表", response_model=WritingTemplateListResponse)
async def get_writing_templates(
    skip: int = 0,
    limit: int = 10,
    writing_type: str | None = None,
    difficulty: str | None = None,
    is_recommended: bool | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTemplateListResponse:
    """获取写作模板列表"""
    try:
        service = WritingService(db)
        templates, total = await service.get_templates(
            skip=skip,
            limit=limit,
            writing_type=WritingType(writing_type) if writing_type else None,
            difficulty=WritingDifficulty(difficulty) if difficulty else None,
            is_recommended=is_recommended,
        )

        logger.info(f"用户 {current_user.id} 查询写作模板列表，共 {total} 个")

        return WritingTemplateListResponse(
            success=True,
            data=[WritingTemplateResponse.model_validate(t) for t in templates],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询写作模板列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/templates", summary="创建写作模板", response_model=WritingTemplateResponse)
async def create_writing_template(
    data: WritingTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTemplateResponse:
    """创建写作模板"""
    try:
        service = WritingService(db)
        template = await service.create_template(data)

        logger.info(f"用户 {current_user.id} 创建写作模板成功: {template.id}")  # type: ignore[has-type]

        return WritingTemplateResponse.model_validate(template)
    except Exception as e:
        logger.error(f"创建写作模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get(
    "/templates/{template_id}", summary="获取写作模板详情", response_model=WritingTemplateResponse
)
async def get_writing_template_detail(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTemplateResponse:
    """获取写作模板详情"""
    try:
        service = WritingService(db)
        template = await service.get_template(template_id)

        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

        logger.info(f"用户 {current_user.id} 查询写作模板详情: {template_id}")

        return WritingTemplateResponse.model_validate(template)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询写作模板详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.put(
    "/templates/{template_id}", summary="更新写作模板", response_model=WritingTemplateResponse
)
async def update_writing_template(
    template_id: int,
    data: WritingTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTemplateResponse:
    """更新写作模板"""
    try:
        service = WritingService(db)
        template = await service.update_template(template_id, data)

        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

        logger.info(f"用户 {current_user.id} 更新写作模板: {template_id}")

        return WritingTemplateResponse.model_validate(template)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新写作模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新失败"
        ) from e


# ==================== 写作任务管理 ====================


@router.get("/tasks", summary="获取写作任务列表", response_model=WritingTaskListResponse)
async def get_writing_tasks(
    skip: int = 0,
    limit: int = 10,
    writing_type: str | None = None,
    difficulty: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTaskListResponse:
    """获取写作任务列表"""
    try:
        service = WritingService(db)
        tasks, total = await service.get_tasks(
            skip=skip,
            limit=limit,
            writing_type=WritingType(writing_type) if writing_type else None,
            difficulty=WritingDifficulty(difficulty) if difficulty else None,
        )

        logger.info(f"用户 {current_user.id} 查询写作任务列表，共 {total} 个")

        return WritingTaskListResponse(
            success=True,
            data=[WritingTaskResponse.model_validate(t) for t in tasks],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询写作任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/tasks", summary="创建写作任务", response_model=WritingTaskResponse)
async def create_writing_task(
    data: WritingTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTaskResponse:
    """创建写作任务"""
    try:
        service = WritingService(db)
        task = await service.create_task(data)

        logger.info(f"用户 {current_user.id} 创建写作任务成功: {task.id}")  # type: ignore[has-type]

        return WritingTaskResponse.model_validate(task)
    except Exception as e:
        logger.error(f"创建写作任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


@router.get("/tasks/{task_id}", summary="获取写作任务详情", response_model=WritingTaskResponse)
async def get_writing_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingTaskResponse:
    """获取写作任务详情"""
    try:
        service = WritingService(db)
        task = await service.get_task(task_id)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        logger.info(f"用户 {current_user.id} 查询写作任务详情: {task_id}")

        return WritingTaskResponse.model_validate(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询写作任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


# ==================== 写作提交管理 ====================


@router.post("/submissions", summary="提交作文", response_model=WritingSubmissionResponse)
async def submit_essay(
    data: WritingSubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingSubmissionResponse:
    """提交作文"""
    try:
        service = WritingService(db)
        submission = await service.submit_essay(current_user.id, data)

        logger.info(f"用户 {current_user.id} 提交作文成功: {submission.id}")  # type: ignore[has-type]

        return WritingSubmissionResponse.model_validate(submission)
    except Exception as e:
        logger.error(f"提交作文失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交失败"
        ) from e


@router.get(
    "/submissions", summary="获取我的写作提交列表", response_model=WritingSubmissionListResponse
)
async def get_my_submissions(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingSubmissionListResponse:
    """获取用户的写作提交列表"""
    try:
        service = WritingService(db)
        submissions, total = await service.get_user_submissions(current_user.id, skip, limit)

        logger.info(f"用户 {current_user.id} 查询写作提交列表，共 {total} 个")

        return WritingSubmissionListResponse(
            success=True,
            data=[WritingSubmissionResponse.model_validate(s) for s in submissions],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询写作提交列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.get(
    "/submissions/{submission_id}",
    summary="获取写作提交详情",
    response_model=WritingSubmissionResponse,
)
async def get_submission_detail(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingSubmissionResponse:
    """获取写作提交详情"""
    try:
        service = WritingService(db)
        submission = await service.get_submission(submission_id, current_user.id)

        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交记录不存在")

        logger.info(f"用户 {current_user.id} 查询写作提交详情: {submission_id}")

        return WritingSubmissionResponse.model_validate(submission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询写作提交详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post(
    "/submissions/{submission_id}/regrade",
    summary="重新评分作文",
    response_model=WritingSubmissionResponse,
)
async def regrade_submission(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingSubmissionResponse:
    """重新评分已提交的作文"""
    try:
        service = WritingService(db)
        submission = await service.regrade_submission(submission_id, current_user.id)

        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交记录不存在")

        logger.info(f"用户 {current_user.id} 重新评分作文: {submission_id}")

        return WritingSubmissionResponse.model_validate(submission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新评分失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="重新评分失败"
        ) from e


# ==================== 语法检查 ====================


# ==================== 语法检查 ====================


@router.post("/grammar-check", summary="语法检查", response_model=GrammarCheckResult)
async def check_grammar(
    text: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GrammarCheckResult:
    """检查文本语法错误"""
    try:
        service = WritingService(db)
        result = await service.check_grammar(text)

        logger.info(f"用户 {current_user.id} 执行语法检查，发现 {result.error_count} 个错误")

        return result
    except Exception as e:
        logger.error(f"语法检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="语法检查失败"
        ) from e


# ==================== 词汇管理 ====================


@router.get("/vocabulary", summary="获取写作词汇列表", response_model=WritingVocabularyListResponse)
async def get_writing_vocabulary(
    skip: int = 0,
    limit: int = 10,
    category: str | None = None,
    writing_type: str | None = None,
    difficulty_level: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingVocabularyListResponse:
    """获取写作词汇列表"""
    try:
        service = WritingService(db)
        vocabulary, total = await service.get_vocabulary_list(
            skip=skip,
            limit=limit,
            category=category,
            writing_type=WritingType(writing_type) if writing_type else None,
            difficulty_level=WritingDifficulty(difficulty_level) if difficulty_level else None,
        )

        logger.info(f"用户 {current_user.id} 查询写作词汇列表，共 {total} 个")

        return WritingVocabularyListResponse(
            success=True,
            data=[WritingVocabularyResponse.model_validate(v) for v in vocabulary],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查询写作词汇列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.post("/vocabulary", summary="创建写作词汇", response_model=WritingVocabularyResponse)
async def create_writing_vocabulary(
    data: WritingVocabularyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingVocabularyResponse:
    """创建写作词汇"""
    try:
        service = WritingService(db)
        vocabulary = await service.create_vocabulary(data)

        logger.info(f"用户 {current_user.id} 创建写作词汇成功: {vocabulary.id}")  # type: ignore[has-type]

        return WritingVocabularyResponse.model_validate(vocabulary)
    except Exception as e:
        logger.error(f"创建写作词汇失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建失败"
        ) from e


# ==================== 统计和推荐 ====================


@router.get("/statistics", summary="获取写作统计数据", response_model=WritingStatistics)
async def get_writing_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingStatistics:
    """获取用户写作统计数据"""
    try:
        service = WritingService(db)
        statistics = await service.get_user_statistics(current_user.id)

        logger.info(f"用户 {current_user.id} 查询写作统计")

        return statistics
    except Exception as e:
        logger.error(f"查询写作统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询失败"
        ) from e


@router.get("/recommendations", summary="获取写作推荐", response_model=WritingRecommendation)
async def get_writing_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WritingRecommendation:
    """获取个性化写作推荐"""
    try:
        service = WritingService(db)
        recommendations = await service.get_user_recommendations(current_user.id)

        logger.info(f"用户 {current_user.id} 获取写作推荐")

        return recommendations
    except Exception as e:
        logger.error(f"获取写作推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取推荐失败"
        ) from e


# ==================== 智能写作辅助 ====================


@router.post("/hints", summary="获取写作提示")
async def get_writing_hints(
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取智能写作提示"""
    try:
        task_id = request.get("task_id")
        current_content = request.get("current_content", "")

        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="task_id 参数是必需的"
            )

        service = WritingService(db)
        hints = await service.get_writing_hints(task_id, current_content)

        logger.info(f"用户 {current_user.id} 获取写作提示成功: task_id={task_id}")

        return hints
    except ValueError as e:
        logger.error(f"获取写作提示失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"获取写作提示失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取提示失败"
        ) from e


@router.post("/synonyms", summary="获取同义词建议")
async def get_synonym_suggestions(
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取同义词建议"""
    try:
        word = request.get("word")

        if not word:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="word 参数是必需的")

        service = WritingService(db)
        suggestions = await service.get_synonym_suggestions(word)

        logger.info(f"用户 {current_user.id} 获取同义词建议成功: word={word}")

        return suggestions
    except Exception as e:
        logger.error(f"获取同义词建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取建议失败"
        ) from e


# ==================== 草稿管理 ====================


@router.post("/drafts", summary="保存写作草稿")
async def save_writing_draft(
    request: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """保存写作草稿"""
    try:
        task_id = request.get("task_id")
        content = request.get("content", "")
        title = request.get("title")

        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="task_id 参数是必需的"
            )

        service = WritingService(db)
        draft = await service.save_draft(current_user.id, task_id, content, title)

        logger.info(f"用户 {current_user.id} 保存草稿成功: task_id={task_id}")

        return draft
    except ValueError as e:
        logger.error(f"保存草稿失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"保存草稿失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="保存失败"
        ) from e


@router.get("/drafts/{task_id}", summary="获取写作草稿")
async def get_writing_draft(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取写作草稿"""
    try:
        service = WritingService(db)
        draft = await service.get_draft(current_user.id, task_id)

        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="草稿不存在")

        logger.info(f"用户 {current_user.id} 获取草稿成功: task_id={task_id}")

        return draft
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取草稿失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取失败"
        ) from e


@router.delete("/drafts/{task_id}", summary="删除写作草稿")
async def delete_writing_draft(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除写作草稿"""
    try:
        service = WritingService(db)
        success = await service.delete_draft(current_user.id, task_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="草稿不存在")

        logger.info(f"用户 {current_user.id} 删除草稿成功: task_id={task_id}")

        return {"message": "草稿删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除草稿失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除失败"
        ) from e


@router.get("/drafts", summary="获取用户草稿列表")
async def get_user_drafts(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取用户的所有草稿"""
    try:
        service = WritingService(db)
        drafts, total = await service.get_user_drafts(current_user.id, skip, limit)

        logger.info(f"用户 {current_user.id} 获取草稿列表成功，共 {total} 个")

        return {
            "success": True,
            "data": drafts,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"获取草稿列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取失败"
        ) from e
