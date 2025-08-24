"""AI功能API端点."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas.ai_schemas import (
    AITaskRequest,
    AITaskResponse,
    CollaborationJoinRequest,
    CollaborationSessionResponse,
    CollaborationUpdateRequest,
    LearningAnalysisListResponse,
    LearningAnalysisRequest,
    LearningAnalysisResponse,
    LessonPlanGenerationRequest,
    LessonPlanListResponse,
    LessonPlanResponse,
    LessonPlanUpdate,
    SmartSuggestionRequest,
    SmartSuggestionResponse,
    SyllabusGenerationRequest,
    SyllabusListResponse,
    SyllabusResponse,
    SyllabusUpdate,
    TeachingAdjustmentListResponse,
    TeachingAdjustmentRequest,
    TeachingAdjustmentResponse,
    TeachingAdjustmentUpdate,
)
from app.ai.services.deepseek_service import get_deepseek_service
from app.ai.services.learning_adjustment_service import get_learning_adjustment_service
from app.ai.services.lesson_plan_service import get_lesson_plan_service
from app.ai.services.syllabus_service import get_syllabus_service
from app.ai.utils.content_generator import SmartSuggestionEngine
from app.core.database import get_db
from app.users.models.user_models import User
from app.users.utils.auth_decorators import (
    AuthRequired,
    create_permission_dependency,
    get_current_user,
)

router = APIRouter(prefix="/ai", tags=["AI功能"])
logger = logging.getLogger(__name__)


# =================== 大纲相关端点 ===================


@router.post(
    "/syllabi/generate",
    response_model=SyllabusResponse,
    summary="AI生成教学大纲",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_CREATE", "AI_GENERATE"]),
    ],
)
async def generate_syllabus(
    request: SyllabusGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyllabusResponse:
    """AI生成教学大纲."""
    try:
        syllabus_service = get_syllabus_service()
        result = await syllabus_service.generate_syllabus(
            db=db,
            request=request,
            teacher_id=current_user.id,
        )
        return result  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"生成大纲失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="大纲生成失败"
        ) from e


@router.get(
    "/syllabi/{syllabus_id}",
    response_model=SyllabusResponse,
    summary="获取大纲详情",
    dependencies=[AuthRequired()],
)
async def get_syllabus(
    syllabus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyllabusResponse:
    """获取大纲详情."""
    try:
        syllabus_service = get_syllabus_service()
        result = await syllabus_service.get_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            teacher_id=current_user.id,
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="大纲不存在")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"获取大纲失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取大纲失败"
        ) from e


@router.put(
    "/syllabi/{syllabus_id}",
    response_model=SyllabusResponse,
    summary="更新大纲",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_UPDATE"]),
    ],
)
async def update_syllabus(
    syllabus_id: int,
    update_data: SyllabusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyllabusResponse:
    """更新大纲."""
    try:
        syllabus_service = get_syllabus_service()
        result = await syllabus_service.update_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            update_data=update_data,
            teacher_id=current_user.id,
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="大纲不存在或无权限")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"更新大纲失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新大纲失败"
        ) from e


@router.get(
    "/syllabi",
    response_model=SyllabusListResponse,
    summary="获取大纲列表",
    dependencies=[AuthRequired()],
)
async def list_syllabi(
    course_id: int | None = Query(None, description="课程ID"),
    status: str | None = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyllabusListResponse:
    """获取大纲列表."""
    try:
        syllabus_service = get_syllabus_service()
        syllabi, total = await syllabus_service.list_syllabi(
            db=db,
            course_id=course_id,
            teacher_id=current_user.id,
            status=status,
            page=page,
            size=size,
        )

        return SyllabusListResponse(
            syllabi=syllabi,
            total=total,
            page=page,
            size=size,
        )
    except Exception as e:
        logger.error(f"获取大纲列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # type: ignore[union-attr]
            detail="获取大纲列表失败",
        ) from e


@router.delete(
    "/syllabi/{syllabus_id}",
    summary="删除大纲",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_DELETE"]),
    ],
)
async def delete_syllabus(
    syllabus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """删除大纲."""
    try:
        syllabus_service = get_syllabus_service()
        success = await syllabus_service.delete_syllabus(
            db=db,
            syllabus_id=syllabus_id,
            teacher_id=current_user.id,
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="大纲不存在或无权限")

        return {"message": "大纲删除成功"}
    except Exception as e:
        logger.error(f"删除大纲失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除大纲失败"
        ) from e


# =================== 教案相关端点 ===================


@router.post(
    "/lesson-plans/generate",
    response_model=LessonPlanResponse,
    summary="AI生成教案",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_CREATE", "AI_GENERATE"]),
    ],
)
async def generate_lesson_plan(
    request: LessonPlanGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanResponse:
    """AI生成教案."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        result = await lesson_plan_service.generate_lesson_plan(
            db=db,
            request=request,
            teacher_id=current_user.id,
        )
        return result  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"生成教案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="教案生成失败"
        ) from e


@router.get(
    "/lesson-plans/{lesson_plan_id}",
    response_model=LessonPlanResponse,
    summary="获取教案详情",
    dependencies=[AuthRequired()],
)
async def get_lesson_plan(
    lesson_plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> LessonPlanResponse:
    """获取教案详情."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        result = await lesson_plan_service.get_lesson_plan(
            db=db,
            lesson_plan_id=lesson_plan_id,
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教案不存在")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"获取教案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取教案失败"
        ) from e


@router.put(
    "/lesson-plans/{lesson_plan_id}",
    response_model=LessonPlanResponse,
    summary="更新教案",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_UPDATE"]),
    ],
)
async def update_lesson_plan(
    lesson_plan_id: int,
    update_data: LessonPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanResponse:
    """更新教案."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        result = await lesson_plan_service.update_lesson_plan(
            db=db,
            lesson_plan_id=lesson_plan_id,
            update_data=update_data,
            user_id=current_user.id,
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教案不存在")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"更新教案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新教案失败"
        ) from e


@router.get(
    "/lesson-plans",
    response_model=LessonPlanListResponse,
    summary="获取教案列表",
    dependencies=[AuthRequired()],
)
async def list_lesson_plans(
    syllabus_id: int | None = Query(None, description="大纲ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanListResponse:
    """获取教案列表."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        lesson_plans, total = await lesson_plan_service.list_lesson_plans(
            db=db,
            syllabus_id=syllabus_id,
            page=page,
            size=size,
        )

        return LessonPlanListResponse(
            lesson_plans=lesson_plans,
            total=total,
            page=page,
            size=size,
        )
    except Exception as e:
        logger.error(f"获取教案列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取教案列表失败"
        ) from e


@router.delete(
    "/lesson-plans/{lesson_plan_id}",
    summary="删除教案",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_DELETE"]),
    ],
)
async def delete_lesson_plan(
    lesson_plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """删除教案."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        success = await lesson_plan_service.delete_lesson_plan(
            db=db,
            lesson_plan_id=lesson_plan_id,
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教案不存在")

        return {"message": "教案删除成功"}
    except Exception as e:
        logger.error(f"删除教案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除教案失败"
        ) from e


# =================== 协作相关端点 ===================


@router.post(
    "/lesson-plans/{lesson_plan_id}/collaborate",
    response_model=CollaborationSessionResponse,
    summary="创建教案协作会话",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_UPDATE"]),
    ],
)
async def create_collaboration_session(
    lesson_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollaborationSessionResponse:
    """创建教案协作会话."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        result = await lesson_plan_service.create_collaboration_session(
            db=db,
            lesson_plan_id=lesson_plan_id,
            initiator_id=current_user.id,
        )
        return result  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"创建协作会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建协作会话失败"
        ) from e


@router.post(
    "/collaboration/join",
    response_model=CollaborationSessionResponse,
    summary="加入协作会话",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_UPDATE"]),
    ],
)
async def join_collaboration_session(
    request: CollaborationJoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollaborationSessionResponse:
    """加入协作会话."""
    try:
        # 确保用户只能以自己的身份加入
        request.user_id = current_user.id

        lesson_plan_service = get_lesson_plan_service()
        result = await lesson_plan_service.join_collaboration_session(
            db=db,
            request=request,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="协作会话不存在或已关闭"
            )

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"加入协作会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="加入协作会话失败"
        ) from e


@router.post(
    "/collaboration/update",
    response_model=CollaborationSessionResponse,
    summary="更新协作内容",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["COURSE_UPDATE"]),
    ],
)
async def update_collaboration_session(
    request: CollaborationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollaborationSessionResponse:
    """更新协作内容."""
    try:
        lesson_plan_service = get_lesson_plan_service()
        result = await lesson_plan_service.update_collaboration_session(
            db=db,
            request=request,
            user_id=current_user.id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="协作会话不存在或无权限"
            )

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"更新协作内容失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新协作内容失败"
        ) from e


# =================== 智能建议相关端点 ===================


@router.post(
    "/suggestions",
    response_model=SmartSuggestionResponse,
    summary="获取智能建议",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["AI_GENERATE"]),
    ],
)
async def get_smart_suggestions(
    request: SmartSuggestionRequest,
    current_user: User = Depends(get_current_user),
) -> SmartSuggestionResponse:
    """获取智能建议."""
    try:
        suggestion_engine = SmartSuggestionEngine()
        result = suggestion_engine.generate_suggestions(
            context_type=request.context_type,
            context_data=request.context_data,
            suggestion_type=request.suggestion_type,
            user_preferences=request.user_preferences,
        )

        return SmartSuggestionResponse(**result)
    except Exception as e:
        logger.error(f"生成智能建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="生成智能建议失败"
        ) from e


# =================== 系统状态相关端点 ===================


@router.get(
    "/status",
    summary="获取AI服务状态",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["SYSTEM_MONITOR"]),
    ],
)
async def get_ai_service_status() -> dict[str, Any]:
    """获取AI服务状态."""
    try:
        deepseek_service = get_deepseek_service()
        status_info = await deepseek_service.get_api_status()
        return status_info
    except Exception as e:
        logger.error(f"获取AI服务状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取服务状态失败"
        ) from e


@router.post(
    "/tasks",
    response_model=AITaskResponse,
    summary="执行AI任务",
    dependencies=[
        AuthRequired(),
        create_permission_dependency(["AI_GENERATE"]),
    ],
)
async def execute_ai_task(
    request: AITaskRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """执行自定义AI任务."""
    try:
        deepseek_service = get_deepseek_service()

        # 构建提示
        prompt = request.request_data.get("prompt", "")
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请求中缺少prompt参数"
            )

        success, result, error_msg = await deepseek_service.generate_completion(
            prompt=prompt,
            model=request.api_model,
            user_id=current_user.id,
            task_type=request.task_type,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI任务执行失败: {error_msg}",
            )

        return {
            "success": True,
            "result": result,
            "task_type": request.task_type,
        }
    except Exception as e:
        logger.error(f"执行AI任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI任务执行失败"
        ) from e


# =================== 学情分析相关端点 ===================


@router.post(
    "/learning-analysis/analyze",
    response_model=LearningAnalysisResponse,
    summary="执行学情分析",
    dependencies=[AuthRequired()],
)
async def analyze_learning_progress(
    request: LearningAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningAnalysisResponse:
    """执行学情分析."""
    try:
        service = get_learning_adjustment_service()
        result = await service.analyze_learning_progress(
            db=db, request=request, teacher_id=current_user.id
        )
        return result  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"学情分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="学情分析失败"
        ) from e


@router.get(
    "/learning-analysis/{analysis_id}",
    response_model=LearningAnalysisResponse,
    summary="获取学情分析详情",
    dependencies=[AuthRequired()],
)
async def get_learning_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningAnalysisResponse:
    """获取学情分析详情."""
    try:
        service = get_learning_adjustment_service()
        result = await service.get_analysis_by_id(
            db=db, analysis_id=analysis_id, teacher_id=current_user.id
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"获取学情分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取学情分析失败"
        ) from e


@router.get(
    "/learning-analysis",
    response_model=LearningAnalysisListResponse,
    summary="获取学情分析列表",
    dependencies=[AuthRequired()],
)
async def get_learning_analyses(
    class_id: int | None = Query(None, description="班级ID"),
    course_id: int | None = Query(None, description="课程ID"),
    analysis_type: str | None = Query(None, description="分析类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningAnalysisListResponse:
    """获取学情分析列表."""
    try:
        service = get_learning_adjustment_service()
        result = await service.get_analyses_list(
            db=db,
            class_id=class_id,
            course_id=course_id,
            teacher_id=current_user.id,
            analysis_type=analysis_type,
            page=page,
            size=size,
        )
        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"获取学情分析列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取学情分析列表失败",
        ) from e


# =================== 教学调整相关端点 ===================


@router.post(
    "/teaching-adjustments/generate",
    response_model=list[TeachingAdjustmentResponse],
    summary="生成教学调整建议",
    dependencies=[AuthRequired()],
)
async def generate_teaching_adjustments(
    request: TeachingAdjustmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeachingAdjustmentResponse]:
    """生成教学调整建议."""
    try:
        service = get_learning_adjustment_service()
        result = await service.generate_teaching_adjustments(
            db=db, request=request, teacher_id=current_user.id
        )
        return result  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"生成教学调整建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成教学调整建议失败",
        ) from e


@router.get(
    "/teaching-adjustments/{adjustment_id}",
    response_model=TeachingAdjustmentResponse,
    summary="获取教学调整建议详情",
    dependencies=[AuthRequired()],
)
async def get_teaching_adjustment(
    adjustment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingAdjustmentResponse:
    """获取教学调整建议详情."""
    try:
        service = get_learning_adjustment_service()
        result = await service.get_adjustment_by_id(
            db=db, adjustment_id=adjustment_id, teacher_id=current_user.id
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="调整建议不存在")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"获取教学调整建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取教学调整建议失败",
        ) from e


@router.put(
    "/teaching-adjustments/{adjustment_id}",
    response_model=TeachingAdjustmentResponse,
    summary="更新教学调整建议",
    dependencies=[AuthRequired()],
)
async def update_teaching_adjustment(
    adjustment_id: int,
    request: TeachingAdjustmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingAdjustmentResponse:
    """更新教学调整建议."""
    try:
        service = get_learning_adjustment_service()
        result = await service.update_adjustment(
            db=db,
            adjustment_id=adjustment_id,
            update_data=request,
            teacher_id=current_user.id,
        )

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="调整建议不存在")

        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"更新教学调整建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新教学调整建议失败",
        ) from e


@router.get(
    "/teaching-adjustments",
    response_model=TeachingAdjustmentListResponse,
    summary="获取教学调整建议列表",
    dependencies=[AuthRequired()],
)
async def get_teaching_adjustments(
    class_id: int | None = Query(None, description="班级ID"),
    course_id: int | None = Query(None, description="课程ID"),
    adjustment_type: str | None = Query(None, description="调整类型"),
    implementation_status: str | None = Query(None, description="实施状态"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingAdjustmentListResponse:
    """获取教学调整建议列表."""
    try:
        service = get_learning_adjustment_service()
        result = await service.get_adjustments_list(
            db=db,
            class_id=class_id,
            course_id=course_id,
            teacher_id=current_user.id,
            adjustment_type=adjustment_type,
            implementation_status=implementation_status,
            page=page,
            size=size,
        )
        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"获取教学调整建议列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取教学调整建议列表失败",
        ) from e
