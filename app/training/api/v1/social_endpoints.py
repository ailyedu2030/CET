"""学习社交与互动API端点."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.training.schemas.social_schemas import (
    AchievementResponse,
    ClassLearningCircleResponse,
    CompetitionAnswerRequest,
    CompetitionCreateRequest,
    CompetitionLeaderboardResponse,
    CompetitionResponse,
    ContentQualityResponse,
    CustomAchievementCreateRequest,
    DiscussionPostCreateRequest,
    DiscussionPostResponse,
    HelpRequestCreateRequest,
    HelpResponseCreateRequest,
    HelpResponseResponse,
    InteractionInsightsResponse,
    JoinGroupRequest,
    StudyGroupCreateRequest,
    StudyGroupResponse,
    UserAchievementsResponse,
)
from app.training.services.achievement_service import AchievementService
from app.training.services.competition_service import CompetitionService
from app.training.services.social_learning_service import SocialLearningService
from app.training.utils.interaction_analyzer import InteractionAnalyzer
from app.users.models.user_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["学习社交与互动"])


# ==================== 学习小组管理 ====================


@router.post("/groups", response_model=StudyGroupResponse)
async def create_study_group(
    group_data: StudyGroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudyGroupResponse:
    """创建学习小组."""
    try:
        service = SocialLearningService(db)

        group_result = await service.create_study_group(
            creator_id=current_user.id, group_data=group_data.model_dump()
        )

        return StudyGroupResponse(**group_result)

    except Exception as e:
        logger.error(f"创建学习小组失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建学习小组失败: {str(e)}",
        ) from e


@router.post("/groups/{group_id}/join", response_model=StudyGroupResponse)
async def join_study_group(
    group_id: str,
    join_request: JoinGroupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudyGroupResponse:
    """加入学习小组."""
    try:
        service = SocialLearningService(db)

        group_result = await service.join_study_group(
            user_id=current_user.id,
            group_id=group_id,
            join_reason=join_request.join_reason,
        )

        return StudyGroupResponse(**group_result)

    except Exception as e:
        logger.error(f"加入学习小组失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"加入学习小组失败: {str(e)}",
        ) from e


@router.post("/groups/{group_id}/posts", response_model=DiscussionPostResponse)
async def create_discussion_post(
    group_id: str,
    post_data: DiscussionPostCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiscussionPostResponse:
    """创建讨论帖子."""
    try:
        service = SocialLearningService(db)

        post_result = await service.create_discussion_post(
            user_id=current_user.id, group_id=group_id, post_data=post_data.model_dump()
        )

        return DiscussionPostResponse(**post_result)

    except Exception as e:
        logger.error(f"创建讨论帖子失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建讨论帖子失败: {str(e)}",
        ) from e


# ==================== 同伴互助 ====================


@router.post("/help-requests", response_model=dict[str, Any])
async def create_help_request(
    help_data: HelpRequestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """发起同伴互助请求."""
    try:
        service = SocialLearningService(db)

        help_result = await service.request_peer_help(
            requester_id=current_user.id, help_data=help_data.model_dump()
        )

        return help_result

    except Exception as e:
        logger.error(f"发起求助请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发起求助请求失败: {str(e)}",
        ) from e


@router.post("/help-requests/{help_id}/responses", response_model=HelpResponseResponse)
async def provide_help_response(
    help_id: str,
    response_data: HelpResponseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelpResponseResponse:
    """提供同伴互助."""
    try:
        service = SocialLearningService(db)

        response_result = await service.provide_peer_help(
            helper_id=current_user.id,
            help_id=help_id,
            help_response=response_data.model_dump(),
        )

        return HelpResponseResponse(**response_result)

    except Exception as e:
        logger.error(f"提供同伴互助失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提供同伴互助失败: {str(e)}",
        ) from e


# ==================== 班级学习圈 ====================


@router.get("/classes/{class_id}/learning-circle", response_model=ClassLearningCircleResponse)
async def get_class_learning_circle(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClassLearningCircleResponse:
    """获取班级学习圈信息."""
    try:
        service = SocialLearningService(db)

        circle_result = await service.get_class_learning_circle(
            class_id=class_id, user_id=current_user.id
        )

        return ClassLearningCircleResponse(**circle_result)

    except Exception as e:
        logger.error(f"获取班级学习圈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取班级学习圈失败: {str(e)}",
        ) from e


# ==================== 成就系统 ====================


@router.get("/achievements", response_model=UserAchievementsResponse)
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserAchievementsResponse:
    """获取用户成就信息."""
    try:
        service = AchievementService(db)

        achievements_result = await service.get_user_achievements(user_id=current_user.id)

        return UserAchievementsResponse(**achievements_result)

    except Exception as e:
        logger.error(f"获取用户成就失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户成就失败: {str(e)}",
        ) from e


@router.post("/achievements/check", response_model=list[AchievementResponse])
async def check_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AchievementResponse]:
    """检查并颁发成就."""
    try:
        service = AchievementService(db)

        new_achievements = await service.check_and_award_achievements(user_id=current_user.id)

        return [AchievementResponse(**achievement) for achievement in new_achievements]

    except Exception as e:
        logger.error(f"检查成就失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查成就失败: {str(e)}",
        ) from e


@router.get("/achievements/leaderboard", response_model=list[dict[str, Any]])
async def get_achievement_leaderboard(
    limit: int = 50,
    achievement_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """获取成就排行榜."""
    try:
        service = AchievementService(db)

        leaderboard = await service.get_achievement_leaderboard(
            limit=limit, achievement_type=achievement_type
        )

        return leaderboard

    except Exception as e:
        logger.error(f"获取成就排行榜失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取成就排行榜失败: {str(e)}",
        ) from e


@router.post("/achievements/custom", response_model=dict[str, Any])
async def create_custom_achievement(
    achievement_data: CustomAchievementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """创建自定义成就（管理员功能）."""
    try:
        service = AchievementService(db)

        custom_achievement = await service.create_custom_achievement(
            creator_id=current_user.id, achievement_data=achievement_data.model_dump()
        )

        return custom_achievement

    except Exception as e:
        logger.error(f"创建自定义成就失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建自定义成就失败: {str(e)}",
        ) from e


# ==================== 学习竞赛 ====================


@router.post("/competitions", response_model=CompetitionResponse)
async def create_competition(
    competition_data: CompetitionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompetitionResponse:
    """创建学习竞赛."""
    try:
        service = CompetitionService(db)

        competition_result = await service.create_competition(
            organizer_id=current_user.id, competition_data=competition_data.model_dump()
        )

        return CompetitionResponse(**competition_result)

    except Exception as e:
        logger.error(f"创建竞赛失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建竞赛失败: {str(e)}",
        ) from e


@router.post("/competitions/{competition_id}/register", response_model=dict[str, Any])
async def register_for_competition(
    competition_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """报名参加竞赛."""
    try:
        service = CompetitionService(db)

        registration_result = await service.register_for_competition(
            user_id=current_user.id, competition_id=competition_id
        )

        return registration_result

    except Exception as e:
        logger.error(f"竞赛报名失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"竞赛报名失败: {str(e)}",
        ) from e


@router.post("/competitions/{competition_id}/start", response_model=dict[str, Any])
async def start_competition_session(
    competition_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """开始竞赛答题会话."""
    try:
        service = CompetitionService(db)

        session_result = await service.start_competition_session(
            user_id=current_user.id, competition_id=competition_id
        )

        return session_result

    except Exception as e:
        logger.error(f"开始竞赛会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始竞赛会话失败: {str(e)}",
        ) from e


@router.post("/competitions/sessions/{session_id}/answer", response_model=dict[str, Any])
async def submit_competition_answer(
    session_id: str,
    answer_data: CompetitionAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """提交竞赛答案."""
    try:
        service = CompetitionService(db)

        answer_result = await service.submit_competition_answer(
            user_id=current_user.id,
            session_id=session_id,
            answer_data=answer_data.model_dump(),
        )

        return answer_result

    except Exception as e:
        logger.error(f"提交竞赛答案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交竞赛答案失败: {str(e)}",
        ) from e


@router.get(
    "/competitions/{competition_id}/leaderboard",
    response_model=CompetitionLeaderboardResponse,
)
async def get_competition_leaderboard(
    competition_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> CompetitionLeaderboardResponse:
    """获取竞赛排行榜."""
    try:
        service = CompetitionService(db)

        leaderboard_result = await service.get_competition_leaderboard(
            competition_id=competition_id, limit=limit
        )

        return CompetitionLeaderboardResponse(**leaderboard_result)

    except Exception as e:
        logger.error(f"获取竞赛排行榜失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取竞赛排行榜失败: {str(e)}",
        ) from e


@router.get("/competitions/history", response_model=dict[str, Any])
async def get_user_competition_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取用户竞赛历史."""
    try:
        service = CompetitionService(db)

        history_result = await service.get_user_competition_history(user_id=current_user.id)

        return history_result

    except Exception as e:
        logger.error(f"获取竞赛历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取竞赛历史失败: {str(e)}",
        ) from e


# ==================== 互动分析 ====================


@router.post("/content/analyze", response_model=ContentQualityResponse)
async def analyze_content_quality(
    content: str,
    content_type: str = "general",
    db: AsyncSession = Depends(get_db),
) -> ContentQualityResponse:
    """分析内容质量."""
    try:
        analyzer = InteractionAnalyzer()

        quality_result = analyzer.analyze_content_quality(
            content=content, content_type=content_type
        )

        return ContentQualityResponse(**quality_result)

    except Exception as e:
        logger.error(f"内容质量分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内容质量分析失败: {str(e)}",
        ) from e


@router.get("/insights", response_model=InteractionInsightsResponse)
async def get_interaction_insights(
    period_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InteractionInsightsResponse:
    """获取用户互动洞察报告."""
    try:
        analyzer = InteractionAnalyzer()

        insights_result = analyzer.generate_interaction_insights(
            user_id=current_user.id, period_days=period_days
        )

        return InteractionInsightsResponse(**insights_result)

    except Exception as e:
        logger.error(f"获取互动洞察失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取互动洞察失败: {str(e)}",
        ) from e
