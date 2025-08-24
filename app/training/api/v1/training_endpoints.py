"""训练系统API端点 - 学生训练相关接口."""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import DifficultyLevel, TrainingType
from app.training.schemas.training_schemas import (
    LearningProgressResponse,
    PerformanceMetrics,
    PerformanceReportResponse,
    QuestionBatchListResponse,
    QuestionBatchRequest,
    QuestionBatchResponse,
    QuestionFilter,
    QuestionListResponse,
    QuestionResponse,
    SubmitAnswerRequest,
    TrainingRecordResponse,
    TrainingSessionRequest,
    TrainingSessionResponse,
)
from app.training.services.adaptive_service import AdaptiveLearningService
from app.training.services.analytics_service import AnalyticsService
from app.training.services.intelligent_training_loop_service import (
    IntelligentTrainingLoopService,
)
from app.training.services.precise_adaptive_service import PreciseAdaptiveService
from app.training.services.training_center_service import TrainingCenterService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

router = APIRouter(tags=["训练系统"])
logger = logging.getLogger(__name__)


# ==================== 训练会话管理 ====================


@router.post(
    "/sessions",
    response_model=TrainingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建训练会话",
    description="为学生创建新的训练会话，支持多种训练类型和难度配置",
)
async def create_training_session(
    request: TrainingSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingSessionResponse:
    """创建训练会话."""
    service = TrainingCenterService(db)

    try:
        session = await service.create_training_session(
            student_id=current_user.id,
            session_data=request,
        )
        return session  # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建训练会话失败: {str(e)}",
        ) from e


@router.get(
    "/sessions/{session_id}",
    response_model=TrainingSessionResponse,
    summary="获取训练会话详情",
    description="获取指定训练会话的详细信息和当前状态",
)
async def get_training_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingSessionResponse:
    """获取训练会话详情."""
    service = TrainingCenterService(db)

    try:
        session = await service.get_training_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="训练会话不存在或无权访问",
            )
        return session  # type: ignore[no-any-return]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练会话失败: {str(e)}",
        ) from e


@router.put(
    "/sessions/{session_id}/complete",
    response_model=TrainingSessionResponse,
    summary="完成训练会话",
    description="标记训练会话为完成状态，触发自适应学习调整",
)
async def complete_training_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingSessionResponse:
    """完成训练会话."""
    service = TrainingCenterService(db)
    adaptive_service = AdaptiveLearningService(db)

    try:
        # 完成会话
        session = await service.complete_training_session(session_id, current_user.id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="训练会话不存在或无权访问",
            )

        # 触发自适应调整
        session_results = {
            "session_id": session_id,
            "accuracy_rate": session.accuracy_rate or 0.0,
            "completion_time": session.completion_time or 0,
        }

        await adaptive_service.update_adaptive_config(
            student_id=current_user.id,
            training_type=session.training_type,
            session_results=session_results,
        )

        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"完成训练会话失败: {str(e)}",
        ) from e


# ==================== 题目管理 ====================


@router.get(
    "/questions",
    response_model=QuestionListResponse,
    summary="获取题目列表",
    description="根据筛选条件获取题目列表，支持分页和多种筛选选项",
)
async def get_questions(
    training_type: TrainingType | None = Query(None, description="训练类型"),
    difficulty_level: DifficultyLevel | None = Query(None, description="难度等级"),
    knowledge_points: list[str] | None = Query(None, description="知识点"),
    tags: list[str] | None = Query(None, description="标签"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionListResponse:
    """获取题目列表."""
    service = TrainingCenterService(db)

    try:
        # 构建筛选条件
        filters = QuestionFilter(
            question_type=None,
            training_type=training_type,
            difficulty_level=difficulty_level,
            knowledge_points=knowledge_points or [],
            tags=tags or [],
            is_active=None,
            created_after=None,
            created_before=None,
        )

        questions = await service.get_questions_by_filter(
            filter_data=filters,
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        # 构建响应格式
        from app.training.schemas.training_schemas import PaginatedResponse

        return QuestionListResponse(
            questions=[await service._build_question_response(q) for q in questions],
            pagination=PaginatedResponse(
                total=len(questions),
                page=page,
                size=page_size,
                pages=(len(questions) + page_size - 1) // page_size,
                page_size=page_size,
                total_items=len(questions),
                total_pages=(len(questions) + page_size - 1) // page_size,
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取题目列表失败: {str(e)}",
        ) from e


@router.get(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="获取题目详情",
    description="获取指定题目的详细信息，包括题目内容和配置",
)
async def get_question_detail(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionResponse:
    """获取题目详情."""
    service = TrainingCenterService(db)

    try:
        question = await service.get_question_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在",
            )
        return await service._build_question_response(question)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取题目详情失败: {str(e)}",
        ) from e


@router.post(
    "/questions/{question_id}/submit",
    response_model=TrainingRecordResponse,
    summary="提交答案",
    description="提交学生答案并进行智能批改，返回批改结果和反馈",
)
async def submit_answer(
    question_id: int,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingRecordResponse:
    """提交答案."""
    service = TrainingCenterService(db)

    try:
        # 提交答案并批改
        record, grading_result = await service.submit_answer(
            student_id=current_user.id,
            answer_data=request,
        )

        # 构建训练记录响应
        from app.training.schemas.training_schemas import TrainingRecordResponse

        return TrainingRecordResponse(
            id=record.id,
            session_id=record.session_id,
            student_id=record.student_id,
            question_id=record.question_id,
            user_answer=record.user_answer,
            grading_result=grading_result,
            start_time=record.start_time,
            end_time=record.end_time,
            time_spent=record.time_spent,
            created_at=record.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提交答案失败: {str(e)}",
        ) from e


# ==================== 题目批次管理 ====================


@router.post(
    "/question-batches",
    response_model=QuestionBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建题目批次",
    description="创建题目批次，用于组织和管理相关题目",
)
async def create_question_batch(
    request: QuestionBatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionBatchResponse:
    """创建题目批次."""

    try:
        # 题目批次功能暂未实现
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="题目批次功能正在开发中",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建题目批次失败: {str(e)}",
        ) from e


@router.get(
    "/question-batches",
    response_model=QuestionBatchListResponse,
    summary="获取题目批次列表",
    description="获取题目批次列表，支持分页和筛选",
)
async def get_question_batches(
    training_type: TrainingType | None = Query(None, description="训练类型"),
    difficulty_level: DifficultyLevel | None = Query(None, description="难度等级"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionBatchListResponse:
    """获取题目批次列表."""

    try:
        # 题目批次功能暂未实现
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="题目批次功能正在开发中",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取题目批次列表失败: {str(e)}",
        ) from e


# ==================== 学习分析 ====================


@router.get(
    "/analytics/progress",
    response_model=LearningProgressResponse,
    summary="获取学习进度",
    description="获取学生的学习进度分析，包括准确率、学习趋势等",
)
async def get_learning_progress(
    training_type: TrainingType | None = Query(None, description="训练类型"),
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LearningProgressResponse:
    """获取学习进度."""
    service = AnalyticsService(db)

    try:
        progress = await service.get_learning_progress(
            student_id=current_user.id,
            training_type=training_type,
            days=days,
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习进度失败: {str(e)}",
        ) from e


@router.get(
    "/analytics/performance/{training_type}",
    response_model=PerformanceMetrics,
    summary="获取性能指标",
    description="获取特定训练类型的性能指标和统计数据",
)
async def get_performance_metrics(
    training_type: TrainingType,
    days: int = Query(7, ge=1, le=90, description="分析天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PerformanceMetrics:
    """获取性能指标."""
    service = AnalyticsService(db)

    try:
        metrics = await service.get_performance_metrics(
            student_id=current_user.id,
            training_type=training_type,
            days=days,
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}",
        ) from e


@router.get(
    "/analytics/report",
    response_model=PerformanceReportResponse,
    summary="生成性能报告",
    description="生成综合性能报告，包含详细分析和改进建议",
)
async def generate_performance_report(
    days: int = Query(30, ge=7, le=365, description="报告天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PerformanceReportResponse:
    """生成性能报告."""
    service = AnalyticsService(db)

    try:
        report = await service.generate_performance_report(
            student_id=current_user.id,
            days=days,
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成性能报告失败: {str(e)}",
        ) from e


@router.get(
    "/analytics/patterns",
    summary="获取学习模式分析",
    description="分析学生的学习模式和习惯，提供个性化洞察",
)
async def get_learning_patterns(
    days: int = Query(60, ge=30, le=365, description="分析天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学习模式分析."""
    service = AnalyticsService(db)

    try:
        patterns = await service.get_learning_patterns(
            student_id=current_user.id,
            days=days,
        )
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习模式失败: {str(e)}",
        ) from e


@router.get(
    "/analytics/comparison",
    summary="获取对比分析",
    description="获取与其他学生的对比分析数据",
)
async def get_comparative_analysis(
    comparison_group: str = Query("grade_level", description="对比组类型"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取对比分析."""
    service = AnalyticsService(db)

    try:
        analysis = await service.get_comparative_analysis(
            student_id=current_user.id,
            comparison_group=comparison_group,
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对比分析失败: {str(e)}",
        ) from e


# ==================== 自适应学习 ====================


@router.get(
    "/adaptive/recommendations",
    summary="获取学习推荐",
    description="基于学习表现获取个性化学习推荐",
)
async def get_learning_recommendations(
    training_type: TrainingType | None = Query(None, description="训练类型"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取学习推荐."""

    try:
        # 学习推荐功能暂未完全实现
        return {
            "recommendations": [
                {
                    "type": "difficulty_adjustment",
                    "message": f"建议继续练习{training_type.value if training_type else '各类'}题目",
                    "priority": "medium",
                }
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习推荐失败: {str(e)}",
        ) from e


@router.get(
    "/adaptive/next-questions",
    response_model=QuestionListResponse,
    summary="获取推荐题目",
    description="基于自适应算法推荐下一批练习题目",
)
async def get_recommended_questions(
    training_type: TrainingType,
    count: int = Query(10, ge=1, le=50, description="题目数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionListResponse:
    """获取推荐题目."""
    training_service = TrainingCenterService(db)

    try:
        # 默认推荐（简化实现）
        filters = QuestionFilter(
            question_type=None,
            training_type=training_type,
            difficulty_level=DifficultyLevel.ELEMENTARY,
            knowledge_points=[],
            tags=[],
            is_active=None,
            created_after=None,
            created_before=None,
        )

        questions = await training_service.get_questions_by_filter(
            filter_data=filters,
            limit=count,
            offset=0,
        )

        # 构建响应格式
        from app.training.schemas.training_schemas import PaginatedResponse

        return QuestionListResponse(
            questions=[await training_service._build_question_response(q) for q in questions],
            pagination=PaginatedResponse(
                total=len(questions),
                page=1,
                size=count,
                pages=1,
                page_size=count,
                total_items=len(questions),
                total_pages=1,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推荐题目失败: {str(e)}",
        ) from e


# ==================== 智能训练闭环API - 🔥需求21核心功能 ====================


@router.post(
    "/intelligent-loop/execute",
    summary="执行智能训练闭环",
    description="执行完整的智能训练闭环：数据采集→AI分析→策略调整→效果验证",
)
async def execute_intelligent_training_loop(
    training_type: TrainingType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """执行智能训练闭环 - 🔥需求21核心功能."""
    try:
        logger.info(f"开始执行智能训练闭环: 用户{current_user.id}, 训练类型{training_type}")

        # 创建智能训练闭环服务
        loop_service = IntelligentTrainingLoopService(db)

        # 执行完整的训练闭环
        loop_result = await loop_service.execute_training_loop(
            student_id=current_user.id, training_type=training_type
        )

        return {
            "message": "智能训练闭环执行成功",
            "data": loop_result,
            "success": loop_result["loop_success"],
            "ai_analysis_accuracy": loop_result["phases"]["ai_analysis"]["analysis_accuracy"],
            "next_execution_time": loop_result["next_execution_time"],
        }

    except Exception as e:
        logger.error(f"智能训练闭环执行失败: 用户{current_user.id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"智能训练闭环执行失败: {str(e)}") from None


@router.get(
    "/intelligent-loop/history",
    summary="获取智能训练闭环历史",
    description="获取智能训练闭环的执行历史记录",
)
async def get_intelligent_loop_history(
    training_type: TrainingType | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取智能训练闭环历史记录."""
    try:
        from app.training.models.training_models import IntelligentTrainingLoop

        # 构建查询
        stmt = select(IntelligentTrainingLoop).where(
            IntelligentTrainingLoop.student_id == current_user.id
        )

        if training_type:
            stmt = stmt.where(IntelligentTrainingLoop.training_type == training_type)

        stmt = stmt.order_by(desc(IntelligentTrainingLoop.execution_time)).limit(limit)

        result = await db.execute(stmt)
        loop_records = result.scalars().all()

        # 构建响应数据
        history_data = []
        for record in loop_records:
            history_data.append(
                {
                    "id": record.id,
                    "training_type": record.training_type.value,
                    "execution_time": record.execution_time,
                    "loop_success": record.loop_success,
                    "ai_analysis_accuracy": record.ai_analysis_accuracy,
                    "improvement_rate": record.improvement_rate,
                    "next_execution_time": record.next_execution_time,
                    "phases_summary": {
                        "data_collection_success": record.data_collection_result.get(
                            "collection_success", False
                        ),
                        "ai_analysis_success": record.ai_analysis_result.get(
                            "analysis_success", False
                        ),
                        "strategy_adjustment_success": record.strategy_adjustment_result.get(
                            "adjustment_success", False
                        ),
                        "effect_verification_success": record.effect_verification_result.get(
                            "verification_success", False
                        ),
                    },
                }
            )

        return {
            "message": "智能训练闭环历史获取成功",
            "data": history_data,
            "total": len(history_data),
        }

    except Exception as e:
        logger.error(f"获取智能训练闭环历史失败: 用户{current_user.id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取智能训练闭环历史失败: {str(e)}") from None


@router.get(
    "/intelligent-loop/status",
    summary="获取智能训练闭环状态",
    description="获取智能训练闭环的当前状态和性能指标",
)
async def get_intelligent_loop_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取智能训练闭环状态."""
    try:
        from app.training.models.training_models import IntelligentTrainingLoop

        # 获取最近的闭环记录
        stmt = (
            select(IntelligentTrainingLoop)
            .where(IntelligentTrainingLoop.student_id == current_user.id)
            .order_by(desc(IntelligentTrainingLoop.execution_time))
            .limit(5)
        )

        result = await db.execute(stmt)
        recent_loops = result.scalars().all()

        # 计算状态统计
        total_loops = len(recent_loops)
        successful_loops = sum(1 for loop in recent_loops if loop.loop_success)
        avg_accuracy = (
            sum(loop.ai_analysis_accuracy for loop in recent_loops) / total_loops
            if total_loops > 0
            else 0
        )
        avg_improvement = (
            sum(loop.improvement_rate for loop in recent_loops) / total_loops
            if total_loops > 0
            else 0
        )

        # 下次执行时间
        next_execution = None
        if recent_loops:
            next_execution = recent_loops[0].next_execution_time

        status_data = {
            "total_loops_executed": total_loops,
            "successful_loops": successful_loops,
            "success_rate": successful_loops / total_loops if total_loops > 0 else 0,
            "average_ai_accuracy": avg_accuracy,
            "average_improvement_rate": avg_improvement,
            "next_execution_time": next_execution,
            "loop_active": (
                next_execution and next_execution > datetime.now() if next_execution else False
            ),
            "performance_metrics": {
                "ai_analysis_accuracy_threshold": 0.9,
                "meets_accuracy_threshold": avg_accuracy >= 0.9,
                "improvement_trend": (
                    "positive"
                    if avg_improvement > 0.05
                    else "stable"
                    if avg_improvement > 0
                    else "negative"
                ),
            },
        }

        return {
            "message": "智能训练闭环状态获取成功",
            "data": status_data,
        }

    except Exception as e:
        logger.error(f"获取智能训练闭环状态失败: 用户{current_user.id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取智能训练闭环状态失败: {str(e)}") from None


# ==================== 精确自适应算法 ====================


@router.post(
    "/precise-adaptive/execute",
    summary="执行精确自适应算法",
    description="🔥需求21第二阶段：基于近10次正确率的精确调整算法",
    response_description="精确自适应调整结果",
)
async def execute_precise_adaptive_algorithm(
    training_type: TrainingType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """执行精确自适应算法 - 🔥需求21第二阶段核心功能."""
    try:
        logger.info(f"开始执行精确自适应算法: 用户{current_user.id}, 训练类型{training_type}")

        # 创建精确自适应服务
        precise_service = PreciseAdaptiveService(db)

        # 执行精确调整算法
        adjustment_result = await precise_service.execute_precise_adjustment(
            current_user.id, training_type
        )

        logger.info(
            f"精确自适应算法执行完成: 用户{current_user.id}, "
            f"算法精度{adjustment_result.get('algorithm_precision', 0):.2%}, "
            f"个性化程度{adjustment_result.get('personalization_score', 0):.2%}"
        )

        return {
            "success": True,
            "message": "精确自适应算法执行成功",
            "data": adjustment_result,
            "performance_metrics": {
                "algorithm_precision_achieved": adjustment_result.get(
                    "meets_precision_target", False
                ),
                "personalization_target_achieved": adjustment_result.get(
                    "meets_personalization_target", False
                ),
                "precision_score": adjustment_result.get("algorithm_precision", 0.0),
                "personalization_score": adjustment_result.get("personalization_score", 0.0),
            },
        }

    except Exception as e:
        logger.error(f"精确自适应算法执行失败: 用户{current_user.id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"精确自适应算法执行失败: {str(e)}") from None


@router.get(
    "/precise-adaptive/performance",
    summary="获取精确自适应算法性能指标",
    description="获取算法精度和个性化程度的详细性能指标",
    response_description="算法性能指标",
)
async def get_precise_adaptive_performance(
    training_type: TrainingType | None = Query(None, description="训练类型筛选"),
    days: int = Query(30, description="统计天数", ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取精确自适应算法性能指标."""
    try:
        from app.training.models.training_models import IntelligentTrainingLoop

        # 构建查询
        stmt = select(IntelligentTrainingLoop).where(
            IntelligentTrainingLoop.student_id == current_user.id
        )

        if training_type:
            stmt = stmt.where(IntelligentTrainingLoop.training_type == training_type)

        # 时间范围筛选
        cutoff_date = datetime.now() - timedelta(days=days)
        stmt = stmt.where(IntelligentTrainingLoop.execution_time >= cutoff_date)

        stmt = stmt.order_by(desc(IntelligentTrainingLoop.execution_time))

        result = await db.execute(stmt)
        loop_records = result.scalars().all()

        if not loop_records:
            return {
                "algorithm_precision": 0.0,
                "personalization_score": 0.0,
                "meets_precision_target": False,
                "meets_personalization_target": False,
                "total_adjustments": 0,
                "successful_adjustments": 0,
                "performance_trend": "insufficient_data",
            }

        # 计算性能指标
        total_adjustments = len(loop_records)
        successful_adjustments = sum(1 for record in loop_records if record.loop_success)

        avg_precision = (
            sum(record.ai_analysis_accuracy for record in loop_records) / total_adjustments
        )
        avg_improvement = (
            sum(record.improvement_rate for record in loop_records) / total_adjustments
        )

        # 计算个性化程度（基于改进率的变异系数）
        improvement_rates = [record.improvement_rate for record in loop_records]
        if len(improvement_rates) > 1:
            import statistics

            personalization_score = min(
                1.0, statistics.stdev(improvement_rates) * 2
            )  # 变异系数作为个性化指标
        else:
            personalization_score = 0.5

        return {
            "algorithm_precision": avg_precision,
            "personalization_score": personalization_score,
            "meets_precision_target": avg_precision >= 0.90,
            "meets_personalization_target": personalization_score >= 0.80,
            "total_adjustments": total_adjustments,
            "successful_adjustments": successful_adjustments,
            "success_rate": (
                successful_adjustments / total_adjustments if total_adjustments > 0 else 0.0
            ),
            "average_improvement_rate": avg_improvement,
            "performance_trend": (
                "improving"
                if avg_improvement > 0.05
                else "stable"
                if avg_improvement > 0
                else "declining"
            ),
            "recent_performance": [
                {
                    "execution_time": record.execution_time,
                    "ai_analysis_accuracy": record.ai_analysis_accuracy,
                    "improvement_rate": record.improvement_rate,
                    "loop_success": record.loop_success,
                }
                for record in loop_records[:10]  # 最近10次
            ],
        }

    except Exception as e:
        logger.error(f"获取精确自适应算法性能指标失败: 用户{current_user.id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取算法性能指标失败: {str(e)}") from None
