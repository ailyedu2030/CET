"""智能批改API端点 - 流式批改和反馈接口."""

import json
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas.grading_schemas import (
    GradingRequest,
    GradingResponse,
    StreamingGradingRequest,
    WritingAssistanceRequest,
)
from app.ai.utils.cet4_standards import CET4Standards
from app.ai.utils.streaming_utils import StreamingGradingUtils
from app.core.database import get_db
from app.shared.models.enums import QuestionType
from app.training.models.training_models import Question
from app.training.services.grading_service import IntelligentGradingService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/grading", tags=["智能批改"])


# ==================== 流式批改端点 ====================


@router.post(
    "/stream",
    summary="流式智能批改",
    description="实时流式批改，响应间隔<200ms，支持写作和翻译题型",
)
async def stream_grading(
    request: StreamingGradingRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """流式智能批改 - 实时返回批改进度和结果."""
    try:
        # 获取题目信息
        question = await db.get(Question, request.question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

        # 验证题目类型是否支持流式批改
        supported_types = [
            QuestionType.ESSAY,
            QuestionType.TRANSLATION_EN_TO_CN,
            QuestionType.TRANSLATION_CN_TO_EN,
            QuestionType.SHORT_ANSWER,
        ]

        if question.question_type not in supported_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"题目类型 {question.question_type} 不支持流式批改",
            )

        # 初始化流式批改工具
        streaming_utils = StreamingGradingUtils()

        # 创建流式响应生成器
        async def generate_streaming_response() -> AsyncGenerator[str, None]:
            """生成流式响应."""
            try:
                async for chunk in streaming_utils.stream_grading_process(
                    question_content=question.content.get("text", ""),
                    user_answer=request.user_answer,
                    question_type=question.question_type,
                    max_score=question.max_score,
                ):
                    # 返回JSON格式的流式数据
                    yield f"data: {chunk}\n\n"

            except Exception as e:
                logger.error(f"流式批改过程出错: {str(e)}")
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "message": "批改过程中出现错误",
                }
                yield f"data: {error_chunk}\n\n"

        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式批改端点错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="流式批改服务暂时不可用",
        ) from e


@router.post(
    "/writing-assistance/stream",
    summary="流式写作辅助",
    description="实时写作辅助，语法检查、词汇建议、句式优化",
)
async def stream_writing_assistance(
    request: WritingAssistanceRequest,
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """流式写作辅助 - 实时语法检查和建议."""
    try:
        streaming_utils = StreamingGradingUtils()

        async def generate_assistance_response() -> AsyncGenerator[str, None]:
            """生成写作辅助响应."""
            try:
                async for chunk in streaming_utils.stream_writing_assistance(
                    text=request.text,
                    assistance_type=request.assistance_type,
                ):
                    # 将chunk转换为JSON字符串格式
                    chunk_str = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {chunk_str}\n\n"

            except Exception as e:
                logger.error(f"写作辅助过程出错: {str(e)}")
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "message": "写作辅助过程中出现错误",
                    "timestamp": time.time(),
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
            finally:
                # 发送结束信号
                end_chunk = {
                    "type": "end",
                    "message": "写作辅助完成",
                    "timestamp": time.time(),
                }
                yield f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_assistance_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"写作辅助端点错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="写作辅助服务暂时不可用",
        ) from e


# ==================== 传统批改端点 ====================


@router.post(
    "/grade",
    response_model=GradingResponse,
    summary="智能批改",
    description="传统批改接口，支持所有题型，响应时间<3秒",
)
async def grade_answer(
    request: GradingRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GradingResponse:
    """智能批改答案 - 传统同步接口."""
    try:
        # 获取题目信息
        question = await db.get(Question, request.question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

        # 初始化批改服务
        grading_service = IntelligentGradingService(db)

        # 执行批改
        grading_result = await grading_service.grade_answer(
            question=question,
            user_answer=request.user_answer,
            context=request.context or {},
        )

        return GradingResponse(
            question_id=request.question_id,
            user_id=current_user.id,
            grading_result=grading_result,
            grading_time=datetime.now(),
            cet4_standard_applied=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批改答案错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批改服务暂时不可用",
        ) from e


# ==================== 四级标准查询端点 ====================


@router.get(
    "/standards/writing",
    summary="获取四级写作评分标准",
    description="返回官方四级写作评分标准和要求",
)
async def get_writing_standards() -> dict[str, Any]:
    """获取四级写作评分标准."""
    return {
        "standards": CET4Standards.WRITING_STANDARDS,
        "vocabulary_requirements": CET4Standards.get_vocabulary_requirements(),
        "grammar_requirements": CET4Standards.get_grammar_requirements(),
    }


@router.get(
    "/standards/translation",
    summary="获取四级翻译评分标准",
    description="返回官方四级翻译评分标准和要求",
)
async def get_translation_standards() -> dict[str, Any]:
    """获取四级翻译评分标准."""
    return {
        "standards": CET4Standards.TRANSLATION_STANDARDS,
        "evaluation_criteria": {
            "accuracy": "翻译准确性 (50%权重)",
            "fluency": "语言流畅性 (30%权重)",
            "completeness": "翻译完整性 (20%权重)",
        },
    }


@router.post(
    "/evaluate/writing",
    summary="写作水平评估",
    description="根据四级标准评估写作水平",
)
async def evaluate_writing_level(
    content: str,
    word_count: int,
    error_count: int,
) -> dict[str, Any]:
    """评估写作水平."""
    try:
        evaluation = CET4Standards.evaluate_writing(
            content=content,
            word_count=word_count,
            error_count=error_count,
        )

        return {
            "evaluation": evaluation,
            "recommendations": _get_writing_recommendations(evaluation),
        }

    except Exception as e:
        logger.error(f"写作评估错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="写作评估服务暂时不可用",
        ) from e


@router.post(
    "/evaluate/translation",
    summary="翻译水平评估",
    description="根据四级标准评估翻译水平",
)
async def evaluate_translation_level(
    accuracy_score: float,
    fluency_score: float,
    completeness_score: float,
) -> dict[str, Any]:
    """评估翻译水平."""
    try:
        evaluation = CET4Standards.evaluate_translation(
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
        )

        return {
            "evaluation": evaluation,
            "recommendations": _get_translation_recommendations(evaluation),
        }

    except Exception as e:
        logger.error(f"翻译评估错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="翻译评估服务暂时不可用",
        ) from e


# ==================== 私有辅助方法 ====================


def _get_writing_recommendations(evaluation: dict[str, Any]) -> list[str]:
    """获取写作改进建议."""
    level = evaluation["level"]
    metrics = evaluation["metrics"]

    recommendations = []

    if metrics["word_count"] < 120:
        recommendations.append("增加文章长度，建议达到120词以上")

    if metrics["error_rate"] > 10:
        recommendations.append("加强语法和拼写练习，降低错误率")

    if level in ["poor", "very_poor"]:
        recommendations.extend(
            ["加强基础语法学习", "扩大词汇量", "多练习写作结构", "注意文章逻辑性"]
        )
    elif level == "fair":
        recommendations.extend(["提高词汇使用准确性", "加强句式多样性", "注意文章连贯性"])
    elif level == "good":
        recommendations.extend(["追求更高级的词汇表达", "完善文章结构", "提高语言流畅性"])

    return recommendations


def _get_translation_recommendations(evaluation: dict[str, Any]) -> list[str]:
    """获取翻译改进建议."""
    level = evaluation["level"]
    metrics = evaluation["metrics"]

    recommendations = []

    if metrics["accuracy_score"] < 0.7:
        recommendations.append("加强翻译准确性，注意原文理解")

    if metrics["fluency_score"] < 0.7:
        recommendations.append("提高译文流畅性，注意语言表达")

    if metrics["completeness_score"] < 0.7:
        recommendations.append("确保翻译完整性，避免遗漏信息")

    if level in ["poor", "very_poor"]:
        recommendations.extend(["加强双语基础能力", "多练习翻译技巧", "注意文化背景差异"])
    elif level == "fair":
        recommendations.extend(["提高专业术语翻译", "加强语言转换能力"])
    elif level == "good":
        recommendations.extend(["追求更自然的表达", "提高翻译效率"])

    return recommendations
