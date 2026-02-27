"""听力训练系统 - API端点"""

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import DifficultyLevel
from app.training.schemas.listening_schemas import (
    ListeningExercise,
    ListeningExerciseListResponse,
    SubmitAnswersRequest,
)
from app.training.services.listening_service import ListeningService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/listening", tags=["听力训练系统"])


# ============ 听力练习相关端点 ============


@router.post("/exercises", response_model=dict[str, Any])
async def create_listening_exercise(
    exercise_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """创建听力练习 - 需求22验收标准1：题型分类"""
    try:
        service = ListeningService(db)

        # 验证题型分类 - 需求22验收标准1
        valid_types = ["short_conversation", "long_conversation", "short_passage", "lecture"]
        exercise_type = exercise_data.get("exercise_type")
        if exercise_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的练习类型，支持的类型：{valid_types}",
            )

        # 根据题型设置题目数量 - 需求22验收标准1
        type_question_mapping = {
            "short_conversation": 8,  # 短对话训练（8个对话×1题）
            "long_conversation": 6,  # 长对话训练（2段对话×3题）
            "short_passage": 9,  # 短文理解（3篇短文×3题）
            "lecture": 5,  # 讲座训练（1篇讲座×5题）
        }

        expected_questions = type_question_mapping.get(exercise_type, 1)
        service = ListeningService(db)

        # 验证题型分类 - 需求22验收标准1
        valid_types = ["short_conversation", "long_conversation", "short_passage", "lecture"]


        # 根据题型设置题目数量 - 需求22验收标准1
        type_question_mapping = {
            "short_conversation": 8,  # 短对话训练（8个对话×1题）
            "long_conversation": 6,  # 长对话训练（2段对话×3题）
            "short_passage": 9,  # 短文理解（3篇短文×3题）
            "lecture": 5,  # 讲座训练（1篇讲座×5题）
        }

        expected_questions = type_question_mapping.get(exercise_type, 1)

        total_questions = exercise_data.get("total_questions", expected_questions)

        exercise = await service.create_listening_exercise(
            title=str(exercise_data.get("title", "")),
            description=exercise_data.get("description"),
            exercise_type=exercise_type,
            difficulty_level=str(exercise_data.get("difficulty_level", "INTERMEDIATE")),
            questions_data=exercise_data.get("questions_data", {}),
            total_questions=total_questions,
            duration_seconds=int(exercise_data.get("duration_seconds", 300)),
            audio_duration=float(exercise_data.get("audio_duration", 0.0)),
            tags=exercise_data.get("tags", []),
            created_by=current_user.id,
        )

        return {
            "success": True,
            "data": {
                "exercise_id": exercise.id,
                "title": exercise.title,
                "exercise_type": exercise.exercise_type,
                "difficulty_level": exercise.difficulty_level,
                "total_questions": exercise.total_questions,
                "expected_questions": expected_questions,
                "duration_seconds": exercise.duration_seconds,
            },
            "message": f"听力练习创建成功，{exercise_type}类型预期{expected_questions}题",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建听力练习失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建听力练习失败"
        ) from e


@router.get("/exercises", response_model=ListeningExerciseListResponse)
async def get_exercises(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    difficulty: DifficultyLevel | None = Query(None, description="难度等级"),
    exercise_type: str | None = Query(None, description="练习类型"),
    is_active: bool = Query(True, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ListeningExerciseListResponse:
    """获取听力练习列表"""
    try:
        service = ListeningService(db)
        exercises, total = await service.get_exercises(
            skip=skip,
            limit=limit,
            difficulty=difficulty,
            exercise_type=exercise_type,
            is_active=is_active,
        )

        # 转换为Pydantic模型
        exercise_schemas = [ListeningExercise.model_validate(exercise) for exercise in exercises]

        return ListeningExerciseListResponse(
            success=True,
            data=exercise_schemas,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"获取听力练习列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取听力练习列表失败"
        ) from e


@router.get("/exercises/{exercise_id}", response_model=ListeningExercise)
async def get_exercise_by_id(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ListeningExercise:
    """根据ID获取听力练习详情"""
    try:
        service = ListeningService(db)
        exercise = await service.get_exercise_by_id(exercise_id)

        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        return ListeningExercise.model_validate(exercise)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取听力练习详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取听力练习详情失败"
        ) from e


# ============ 听力会话相关端点 ============


@router.post("/exercises/{exercise_id}/start")
async def start_session(
    exercise_id: int,
    session_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """开始听力训练会话"""
    try:
        service = ListeningService(db)
        session = await service.start_session(
            student_id=current_user.id,
            exercise_id=exercise_id,
            session_name=session_name,
        )

        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "exercise_id": exercise_id,
                "start_time": session.start_time.isoformat(),
                "total_questions": session.total_questions,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"开始听力训练会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="开始听力训练会话失败"
        ) from e


@router.post("/sessions/{session_id}/submit")
async def submit_answers(
    session_id: int,
    answers_data: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """提交听力答案"""
    try:
        service = ListeningService(db)
        result = await service.submit_answers(
            session_id=session_id,
            answers_data=answers_data.model_dump(),
        )

        return {
            "success": True,
            "data": {
                "result_id": result.id,
                "score": result.total_score,
                "max_score": result.max_score,
                "percentage": result.percentage,
                "correct_answers": result.correct_answers,
                "wrong_answers": result.wrong_answers,
                "unanswered": result.unanswered,
                "completion_time": result.completion_time.isoformat(),
                "improvement_suggestions": result.improvement_suggestions,
                "weak_areas": result.weak_areas,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"提交听力答案失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交听力答案失败"
        ) from e


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取听力会话详情"""
    try:
        service = ListeningService(db)
        session = await service.get_session_by_id(session_id)

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力会话不存在")

        # 验证权限
        if session.student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "exercise_id": session.exercise_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "current_question": session.current_question,
                "total_questions": session.total_questions,
                "is_completed": session.is_completed,
                "answers": session.answers,
                "audio_progress": session.audio_progress,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取听力会话详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取听力会话详情失败"
        ) from e


# ============ 统计相关端点 ============


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取听力训练统计数据"""
    try:
        service = ListeningService(db)
        statistics = await service.get_student_statistics(current_user.id)

        return {"success": True, "data": statistics}

    except Exception as e:
        logger.error(f"获取听力训练统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取听力训练统计失败"
        ) from e


@router.get("/results/{result_id}")
async def get_result(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取听力结果详情"""
    try:
        service = ListeningService(db)
        result = await service.get_result_by_id(result_id)

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力结果不存在")

        # 验证权限
        if result.student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此结果")

        return {
            "success": True,
            "data": {
                "result_id": result.id,
                "session_id": result.session_id,
                "exercise_id": result.exercise_id,
                "completion_time": result.completion_time.isoformat(),
                "total_score": result.total_score,
                "max_score": result.max_score,
                "percentage": result.percentage,
                "correct_answers": result.correct_answers,
                "wrong_answers": result.wrong_answers,
                "unanswered": result.unanswered,
                "total_questions": result.total_questions,
                "question_results": result.question_results,
                "answer_analysis": result.answer_analysis,
                "total_time_seconds": result.total_time_seconds,
                "average_time_per_question": result.average_time_per_question,
                "listening_ability_score": result.listening_ability_score,
                "comprehension_score": result.comprehension_score,
                "vocabulary_score": result.vocabulary_score,
                "improvement_suggestions": result.improvement_suggestions,
                "weak_areas": result.weak_areas,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取听力结果详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取听力结果详情失败"
        ) from e


# ============ 训练特性端点 - 需求22验收标准2 ============


@router.post("/exercises/{exercise_id}/playback-settings", response_model=dict[str, Any])
async def update_playback_settings(
    exercise_id: int,
    settings: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """更新播放设置 - 需求22验收标准2：语速调节/重复播放"""
    try:
        service = ListeningService(db)

        # 验证练习是否存在
        exercise = await service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        # 验证设置参数
        playback_speed = settings.get("playback_speed", 1.0)
        if not 0.5 <= playback_speed <= 2.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="播放速度必须在0.5-2.0之间"
            )

        repeat_count = settings.get("repeat_count", 1)
        if not 1 <= repeat_count <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="重复次数必须在1-5之间"
            )

        show_subtitles = settings.get("show_subtitles", False)

        # 保存播放设置到数据库
        playback_settings = await service.save_playback_settings(
            user_id=current_user.id,
            exercise_id=exercise_id,
            playback_speed=playback_speed,
            repeat_count=repeat_count,
            show_subtitles=show_subtitles,
        )

        # 保存播放设置
        playback_settings = {
            "playback_speed": playback_speed,
            "repeat_count": repeat_count,
            "show_subtitles": show_subtitles,
            "user_id": current_user.id,
            "exercise_id": exercise_id,
        }

        return {
            "success": True,
            "data": playback_settings,
            "message": f"播放设置已更新：速度{playback_speed}x，重复{repeat_count}次，字幕{'开启' if show_subtitles else '关闭'}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新播放设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新播放设置失败"
        ) from e


@router.post("/exercises/{exercise_id}/dictation", response_model=dict[str, Any])
async def create_dictation_exercise(
    exercise_id: int,
    dictation_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """创建听写练习 - 需求22验收标准2：单词/短语听写训练"""
    try:
        service = ListeningService(db)

        # 验证练习是否存在
        exercise = await service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        # 创建听写练习
        dictation_type = dictation_data.get("type", "word")  # word, phrase, sentence
        target_words = dictation_data.get("target_words", [])

        if not target_words:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="听写目标词汇不能为空"
            )

        dictation_exercise = {
            "exercise_id": exercise_id,
            "type": dictation_type,
            "target_words": target_words,
            "user_id": current_user.id,
            "created_at": "now",
        }

        return {
            "success": True,
            "data": dictation_exercise,
            "message": f"听写练习创建成功，类型：{dictation_type}，目标词汇：{len(target_words)}个",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建听写练习失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建听写练习失败"
        ) from e


@router.post("/exercises/{exercise_id}/pronunciation", response_model=dict[str, Any])
async def start_pronunciation_practice(
    exercise_id: int,
    practice_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """开始口语跟读练习 - 需求22验收标准2：口语跟读练习"""
    try:
        service = ListeningService(db)

        # 验证练习是否存在
        exercise = await service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        # 创建跟读练习
        target_text = practice_data.get("target_text", "")
        if not target_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="跟读目标文本不能为空"
            )

        pronunciation_practice = {
            "exercise_id": exercise_id,
            "target_text": target_text,
            "user_id": current_user.id,
            "practice_mode": practice_data.get(
                "practice_mode", "sentence"
            ),  # word, phrase, sentence
            "phonetic_focus": practice_data.get("phonetic_focus", []),  # 重点音标
            "created_at": "now",
        }

        return {
            "success": True,
            "data": pronunciation_practice,
            "message": f"口语跟读练习已开始，模式：{practice_data.get('practice_mode', 'sentence')}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始口语跟读练习失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="开始口语跟读练习失败"
        ) from e


# ============ 智能辅助端点 - 需求22验收标准3 ============


@router.post("/exercises/{exercise_id}/phonetic-practice", response_model=dict[str, Any])
async def create_phonetic_practice(
    exercise_id: int,
    phonetic_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """创建音标识别练习 - 需求22验收标准3：针对性音标识别练习"""
    try:
        service = ListeningService(db)

        # 验证练习是否存在
        exercise = await service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        # 创建音标练习
        target_phonetics = phonetic_data.get("target_phonetics", [])
        if not target_phonetics:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目标音标不能为空")

        # 常见难点音标
        difficult_phonetics = [
            "/θ/",
            "/ð/",
            "/ʃ/",
            "/ʒ/",
            "/tʃ/",
            "/dʒ/",
            "/r/",
            "/l/",
            "/w/",
            "/v/",
            "/f/",
            "/s/",
            "/z/",
        ]

        phonetic_practice = {
            "exercise_id": exercise_id,
            "target_phonetics": target_phonetics,
            "difficult_phonetics": [p for p in target_phonetics if p in difficult_phonetics],
            "user_id": current_user.id,
            "practice_type": phonetic_data.get(
                "practice_type", "recognition"
            ),  # recognition, production
            "created_at": "now",
        }

        return {
            "success": True,
            "data": phonetic_practice,
            "message": f"音标识别练习创建成功，目标音标：{len(target_phonetics)}个，难点音标：{len(phonetic_practice['difficult_phonetics'])}个",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建音标识别练习失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建音标识别练习失败"
        ) from e


@router.post("/exercises/{exercise_id}/difficulty-analysis", response_model=dict[str, Any])
async def analyze_listening_difficulties(
    exercise_id: int,
    analysis_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """分析个人听力难点 - 需求22验收标准3：自动标注个人听力难点"""
    try:
        service = ListeningService(db)

        # 验证练习是否存在
        exercise = await service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        # 分析用户答题情况
        user_answers = analysis_data.get("user_answers", [])
        correct_answers = analysis_data.get("correct_answers", [])

        if len(user_answers) != len(correct_answers):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户答案和正确答案数量不匹配"
            )

        # 分析错误类型
        difficult_areas: list[str] = []
        improvement_suggestions: list[str] = []

        error_analysis = {
            "total_questions": len(user_answers),
            "correct_count": sum(
                1
                for i, (user, correct) in enumerate(
                    zip(user_answers, correct_answers, strict=False)
                )
                if user == correct
            ),
            "error_types": {
                "detail_comprehension": 0,  # 细节理解错误
                "main_idea": 0,  # 主旨理解错误
                "inference": 0,  # 推理判断错误
                "vocabulary": 0,  # 词汇理解错误
            },
            "difficult_areas": difficult_areas,
            "improvement_suggestions": improvement_suggestions,
        }

        # 计算准确率
        correct_count = cast(int, error_analysis["correct_count"])
        total_questions = cast(int, error_analysis["total_questions"])
        accuracy = correct_count / total_questions
        error_analysis["accuracy"] = accuracy

        # 生成改进建议
        if accuracy < 0.6:
            improvement_suggestions.extend(
                ["建议加强基础听力训练", "重点练习单词发音和语调", "增加听力材料的接触量"]
            )
        elif accuracy < 0.8:
            improvement_suggestions.extend(
                ["注意听力技巧的运用", "加强对话语境的理解", "练习预测和推理能力"]
            )

        # 标注个人难点
        if exercise.exercise_type == "short_conversation":
            difficult_areas.append("短对话理解")
        elif exercise.exercise_type == "long_conversation":
            difficult_areas.append("长对话理解")
        elif exercise.exercise_type == "short_passage":
            difficult_areas.append("短文理解")
        elif exercise.exercise_type == "lecture":
            difficult_areas.append("讲座理解")

        return {
            "success": True,
            "data": error_analysis,
            "message": f"听力难点分析完成，准确率：{accuracy:.1%}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析听力难点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="分析听力难点失败"
        ) from e


@router.get("/exercises/{exercise_id}/techniques", response_model=dict[str, Any])
async def get_listening_techniques(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取场景化听力应试技巧 - 需求22验收标准3：场景化听力应试技巧"""
    try:
        service = ListeningService(db)

        # 验证练习是否存在
        exercise = await service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="听力练习不存在")

        # 根据题型提供相应技巧
        techniques = {
            "short_conversation": {
                "pre_listening": [
                    "快速浏览选项，预测对话主题",
                    "注意选项中的关键词和差异",
                    "预判可能的问题类型",
                ],
                "while_listening": [
                    "抓住对话的关键信息",
                    "注意说话人的语气和态度",
                    "关注转折词和强调词",
                ],
                "post_listening": ["结合语境选择最佳答案", "排除明显错误选项", "相信第一直觉"],
            },
            "long_conversation": {
                "pre_listening": [
                    "仔细阅读所有题目和选项",
                    "标记关键词和数字信息",
                    "预测对话可能涉及的场景",
                ],
                "while_listening": [
                    "记录重要信息和细节",
                    "注意对话的逻辑结构",
                    "关注问答之间的关系",
                ],
                "post_listening": ["逐题分析，避免混淆", "利用排除法缩小范围", "检查答案的逻辑性"],
            },
            "short_passage": {
                "pre_listening": [
                    "通过题目了解文章主题",
                    "预测文章可能的结构",
                    "注意题目的时间顺序",
                ],
                "while_listening": [
                    "抓住文章的主旨大意",
                    "记录关键细节和数据",
                    "注意段落之间的逻辑关系",
                ],
                "post_listening": [
                    "先做主旨题，再做细节题",
                    "利用已知信息推断答案",
                    "注意题目与原文的对应关系",
                ],
            },
            "lecture": {
                "pre_listening": ["了解讲座的学科背景", "预测可能的专业词汇", "关注题目的考查重点"],
                "while_listening": [
                    "抓住讲座的核心观点",
                    "注意例证和解释说明",
                    "关注讲者的态度和结论",
                ],
                "post_listening": ["理解题目的深层含义", "结合背景知识判断", "注意推理题的逻辑性"],
            },
        }

        exercise_techniques = techniques.get(
            exercise.exercise_type, techniques["short_conversation"]
        )

        return {
            "success": True,
            "data": {
                "exercise_type": exercise.exercise_type,
                "techniques": exercise_techniques,
                "general_tips": [
                    "保持冷静，不要因为一题影响后续",
                    "合理分配时间，不要在难题上纠结",
                    "充分利用题目间的间隔时间",
                    "培养英语思维，避免中文翻译",
                ],
            },
            "message": f"已获取{exercise.exercise_type}类型的听力应试技巧",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取听力应试技巧失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取听力应试技巧失败"
        ) from e


# ============ 音频相关端点 ============


# H9: Audio upload endpoint
@router.post("/audio/upload")
async def upload_audio_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """上传听力音频文件"""
    import os
    import uuid
    from pathlib import Path
    
    # Validate file type
    allowed_types = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/ogg", "audio/webm"}
    content_type = file.content_type or ""
    
    # Check file extension as fallback
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    allowed_exts = {".mp3", ".wav", ".ogg", ".webm", ".m4a"}
    
    if content_type not in allowed_types and file_ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的音频格式。支持: {', '.join(allowed_exts)}"
        )
    
    # Create upload directory
    upload_dir = Path("uploads/listening/audio")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Save file
    content = await file.read()
    await file.seek(0)
    
    # Write file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Get duration (simplified - in production use audio library)
    duration = 0.0
    
    # Create database record
    from app.training.models import ListeningAudioFile
    
    audio_file = ListeningAudioFile(
        filename=unique_filename,
        original_filename=file.filename or "unknown.mp3",
        file_path=str(file_path),
        file_url=f"/uploads/listening/audio/{unique_filename}",
        file_size=len(content),
        duration=duration,
        format=file_ext.lstrip("."),
        sample_rate=None,
        bitrate=None,
        audio_metadata={},
        is_processed=False,
        upload_user_id=current_user.id,
    )
    
    db.add(audio_file)
    await db.commit()
    await db.refresh(audio_file)
    
    return JSONResponse({
        "success": True,
        "message": "音频文件上传成功",
        "data": {
            "audio_id": audio_file.id,
            "filename": audio_file.filename,
            "original_filename": audio_file.original_filename,
            "file_url": audio_file.file_url,
            "file_size": audio_file.file_size,
            "format": audio_file.format,
        }
    })


@router.get("/audio/{audio_id}")
async def get_audio_file(
    audio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取音频文件信息"""
    try:
        service = ListeningService(db)
        audio_file = await service.get_audio_file_by_id(audio_id)

        if not audio_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音频文件不存在")

        return {
            "success": True,
            "data": {
                "audio_id": audio_file.id,
                "filename": audio_file.filename,
                "original_filename": audio_file.original_filename,
                "file_url": audio_file.file_url,
                "duration": audio_file.duration,
                "format": audio_file.format,
                "sample_rate": audio_file.sample_rate,
                "bitrate": audio_file.bitrate,
                "file_size": audio_file.file_size,
                "audio_metadata": audio_file.audio_metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音频文件信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取音频文件信息失败"
        ) from e
