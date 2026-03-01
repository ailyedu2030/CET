"""学习社交相关Schema定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ==================== 学习小组相关Schema ====================


class StudyGroupCreateRequest(BaseModel):
    """学习小组创建请求."""

    name: str = Field(..., min_length=1, max_length=50, description="小组名称")
    description: str = Field("", max_length=200, description="小组描述")
    subject: str = Field("英语四级", description="学习科目")
    target_level: str = Field("intermediate", description="目标水平")
    max_members: int = Field(4, ge=2, le=8, description="最大成员数")
    study_schedule: dict[str, Any] = Field(default_factory=dict, description="学习计划")
    group_rules: list[str] = Field(default_factory=list, description="小组规则")


class StudyGroupResponse(BaseModel):
    """学习小组响应."""

    group_id: str = Field(..., description="小组ID")
    creator_id: int = Field(..., description="创建者ID")
    name: str = Field(..., description="小组名称")
    description: str = Field(..., description="小组描述")
    subject: str = Field(..., description="学习科目")
    target_level: str = Field(..., description="目标水平")
    max_members: int = Field(..., description="最大成员数")
    current_members: int = Field(..., description="当前成员数")
    member_ids: list[int] = Field(..., description="成员ID列表")
    status: str = Field(..., description="小组状态")
    created_at: datetime = Field(..., description="创建时间")
    study_schedule: dict[str, Any] = Field(..., description="学习计划")
    group_rules: list[str] = Field(..., description="小组规则")


class JoinGroupRequest(BaseModel):
    """加入小组请求."""

    join_reason: str = Field("", max_length=100, description="加入理由")


# ==================== 讨论相关Schema ====================


class DiscussionPostCreateRequest(BaseModel):
    """讨论帖子创建请求."""

    title: str = Field("", max_length=100, description="帖子标题")
    content: str = Field(..., min_length=1, max_length=2000, description="帖子内容")
    post_type: str = Field("discussion", description="帖子类型")
    tags: list[str] = Field(default_factory=list, description="标签")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="附件")


class DiscussionPostResponse(BaseModel):
    """讨论帖子响应."""

    post_id: str = Field(..., description="帖子ID")
    group_id: str = Field(..., description="小组ID")
    author_id: int = Field(..., description="作者ID")
    title: str = Field(..., description="帖子标题")
    content: str = Field(..., description="帖子内容")
    post_type: str = Field(..., description="帖子类型")
    tags: list[str] = Field(..., description="标签")
    attachments: list[dict[str, Any]] = Field(..., description="附件")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    like_count: int = Field(..., description="点赞数")
    reply_count: int = Field(..., description="回复数")
    view_count: int = Field(..., description="浏览数")
    is_pinned: bool = Field(..., description="是否置顶")
    is_resolved: bool = Field(..., description="是否已解决")
    quality_score: float = Field(..., description="质量分数")


# ==================== 同伴互助相关Schema ====================


class HelpRequestCreateRequest(BaseModel):
    """求助请求创建请求."""

    title: str = Field(..., min_length=1, max_length=100, description="求助标题")
    description: str = Field(
        ..., min_length=10, max_length=1000, description="求助描述"
    )
    subject: str = Field("英语四级", description="学习科目")
    difficulty_level: str = Field("intermediate", description="难度级别")
    urgency: str = Field("normal", description="紧急程度")
    help_type: str = Field("explanation", description="求助类型")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="附件")


class HelpRequestResponse(BaseModel):
    """求助请求响应."""

    help_id: str = Field(..., description="求助ID")
    requester_id: int = Field(..., description="求助者ID")
    title: str = Field(..., description="求助标题")
    description: str = Field(..., description="求助描述")
    subject: str = Field(..., description="学习科目")
    difficulty_level: str = Field(..., description="难度级别")
    urgency: str = Field(..., description="紧急程度")
    preferred_help_type: str = Field(..., description="偏好的帮助类型")
    attachments: list[dict[str, Any]] = Field(..., description="附件")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="状态")
    helper_id: int | None = Field(None, description="帮助者ID")
    response_count: int = Field(..., description="回复数量")
    is_resolved: bool = Field(..., description="是否已解决")
    resolution_rating: float | None = Field(None, description="解决评分")


class HelpResponseCreateRequest(BaseModel):
    """帮助回复创建请求."""

    content: str = Field(..., min_length=10, max_length=1000, description="回复内容")
    response_type: str = Field("explanation", description="回复类型")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="附件")


class HelpResponseResponse(BaseModel):
    """帮助回复响应."""

    response_id: str = Field(..., description="回复ID")
    help_id: str = Field(..., description="求助ID")
    helper_id: int = Field(..., description="帮助者ID")
    content: str = Field(..., description="回复内容")
    response_type: str = Field(..., description="回复类型")
    attachments: list[dict[str, Any]] = Field(..., description="附件")
    created_at: datetime = Field(..., description="创建时间")
    like_count: int = Field(..., description="点赞数")
    is_accepted: bool = Field(..., description="是否被采纳")
    quality_score: float = Field(..., description="质量分数")


# ==================== 成就系统相关Schema ====================


class AchievementResponse(BaseModel):
    """成就响应."""

    achievement_id: str = Field(..., description="成就ID")
    type: str = Field(..., description="成就类型")
    name: str = Field(..., description="成就名称")
    description: str = Field(..., description="成就描述")
    level: int = Field(..., description="成就等级")
    icon: str = Field(..., description="成就图标")
    points: int = Field(..., description="奖励积分")
    threshold: Any = Field(..., description="达成阈值")
    achieved_at: datetime = Field(..., description="获得时间")
    rarity: str = Field(..., description="稀有度")


class BadgeResponse(BaseModel):
    """徽章响应."""

    badge_id: str = Field(..., description="徽章ID")
    name: str = Field(..., description="徽章名称")
    description: str = Field(..., description="徽章描述")
    rarity: str = Field(..., description="稀有度")
    points: int = Field(..., description="奖励积分")
    achieved_at: datetime = Field(..., description="获得时间")


class UserAchievementsResponse(BaseModel):
    """用户成就响应."""

    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    achievements: list[AchievementResponse] = Field(..., description="成就列表")
    badges: list[BadgeResponse] = Field(..., description="徽章列表")
    stats: dict[str, Any] = Field(..., description="成就统计")
    progress: dict[str, Any] = Field(..., description="进度信息")
    leaderboard_position: dict[str, Any] = Field(..., description="排行榜位置")
    total_points: int = Field(..., description="总积分")
    achievement_level: str = Field(..., description="成就等级")
    next_level_points: int = Field(..., description="下一等级所需积分")


class CustomAchievementCreateRequest(BaseModel):
    """自定义成就创建请求."""

    name: str = Field(..., min_length=1, max_length=50, description="成就名称")
    description: str = Field(..., min_length=1, max_length=200, description="成就描述")
    icon: str = Field("🏆", description="成就图标")
    rarity: str = Field("custom", description="稀有度")
    points: int = Field(100, ge=1, le=1000, description="奖励积分")
    condition: str = Field(..., description="达成条件")


# ==================== 竞赛相关Schema ====================


class CompetitionCreateRequest(BaseModel):
    """竞赛创建请求."""

    title: str = Field(..., min_length=1, max_length=100, description="竞赛标题")
    description: str = Field("", max_length=500, description="竞赛描述")
    competition_type: str = Field(..., description="竞赛类型")
    difficulty_level: str = Field("intermediate", description="难度级别")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    registration_deadline: str = Field(..., description="报名截止时间")
    max_participants: int = Field(100, ge=1, le=1000, description="最大参与人数")
    entry_requirements: dict[str, Any] = Field(
        default_factory=dict, description="参赛要求"
    )
    question_pool: list[int] = Field(default_factory=list, description="题库")
    rules: list[str] = Field(default_factory=list, description="竞赛规则")
    prizes: dict[str, Any] = Field(default_factory=dict, description="奖品设置")


class CompetitionResponse(BaseModel):
    """竞赛响应."""

    competition_id: str = Field(..., description="竞赛ID")
    organizer_id: int = Field(..., description="组织者ID")
    title: str = Field(..., description="竞赛标题")
    description: str = Field(..., description="竞赛描述")
    competition_type: str = Field(..., description="竞赛类型")
    difficulty_level: str = Field(..., description="难度级别")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    registration_deadline: datetime = Field(..., description="报名截止时间")
    max_participants: int = Field(..., description="最大参与人数")
    participant_count: int = Field(..., description="当前参与人数")
    entry_requirements: dict[str, Any] = Field(..., description="参赛要求")
    rules: list[str] = Field(..., description="竞赛规则")
    prizes: dict[str, Any] = Field(..., description="奖品设置")
    status: str = Field(..., description="竞赛状态")
    created_at: datetime = Field(..., description="创建时间")


class CompetitionRegistrationResponse(BaseModel):
    """竞赛报名响应."""

    registration_id: str = Field(..., description="报名ID")
    competition_id: str = Field(..., description="竞赛ID")
    user_id: int = Field(..., description="用户ID")
    registered_at: datetime = Field(..., description="报名时间")
    status: str = Field(..., description="报名状态")
    team_id: str | None = Field(None, description="团队ID")


class CompetitionSessionResponse(BaseModel):
    """竞赛会话响应."""

    session_id: str = Field(..., description="会话ID")
    competition_id: str = Field(..., description="竞赛ID")
    user_id: int = Field(..., description="用户ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    current_question_index: int = Field(..., description="当前题目索引")
    score: float = Field(..., description="当前分数")
    status: str = Field(..., description="会话状态")


class CompetitionAnswerRequest(BaseModel):
    """竞赛答案提交请求."""

    answer: str = Field(..., description="答案")
    time_spent: int = Field(0, description="用时（秒）")


class CompetitionLeaderboardResponse(BaseModel):
    """竞赛排行榜响应."""

    competition: CompetitionResponse = Field(..., description="竞赛信息")
    leaderboard: list[dict[str, Any]] = Field(..., description="排行榜数据")
    statistics: dict[str, Any] = Field(..., description="竞赛统计")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 班级学习圈相关Schema ====================


class ClassLearningCircleResponse(BaseModel):
    """班级学习圈响应."""

    class_info: dict[str, Any] = Field(..., description="班级信息")
    learning_stats: dict[str, Any] = Field(..., description="学习统计")
    active_discussions: list[dict[str, Any]] = Field(..., description="活跃讨论")
    leaderboard: list[dict[str, Any]] = Field(..., description="排行榜")
    recent_activities: list[dict[str, Any]] = Field(..., description="最近活动")
    study_groups: list[dict[str, Any]] = Field(..., description="学习小组")
    user_participation: dict[str, Any] = Field(..., description="用户参与统计")
    generated_at: datetime = Field(..., description="生成时间")


# ==================== 互动分析相关Schema ====================


class ContentQualityResponse(BaseModel):
    """内容质量分析响应."""

    overall_score: float = Field(..., description="综合质量分数")
    basic_quality: dict[str, Any] = Field(..., description="基础质量")
    learning_relevance: dict[str, Any] = Field(..., description="学习相关性")
    structure_score: float = Field(..., description="结构化程度")
    engagement_score: float = Field(..., description="互动性分数")
    sentiment: dict[str, Any] = Field(..., description="情感分析")
    recommendations: list[str] = Field(..., description="改进建议")
    analyzed_at: datetime = Field(..., description="分析时间")


class InteractionInsightsResponse(BaseModel):
    """互动洞察响应."""

    user_id: int = Field(..., description="用户ID")
    analysis_period: dict[str, Any] = Field(..., description="分析周期")
    activity_analysis: dict[str, Any] = Field(..., description="活跃度分析")
    quality_analysis: dict[str, Any] = Field(..., description="质量分析")
    network_position: dict[str, Any] = Field(..., description="网络位置")
    learning_influence: dict[str, Any] = Field(..., description="学习影响")
    improvement_suggestions: list[str] = Field(..., description="改进建议")
    overall_rating: str = Field(..., description="综合评级")
    generated_at: datetime = Field(..., description="生成时间")


# ==================== 游戏化相关Schema ====================


class LevelInfoResponse(BaseModel):
    """等级信息响应."""

    level: int = Field(..., description="当前等级")
    current_exp: int = Field(..., description="当前经验值")
    exp_to_next: int = Field(..., description="升级所需经验")
    progress_percentage: float = Field(..., description="进度百分比")
    total_exp: int = Field(..., description="总经验值")


class ExpRewardResponse(BaseModel):
    """经验奖励响应."""

    base_exp: int = Field(..., description="基础经验")
    bonus_exp: int = Field(..., description="奖励经验")
    total_exp: int = Field(..., description="总经验")
    multipliers: list[dict[str, Any]] = Field(..., description="倍数详情")


class MotivationalMessageResponse(BaseModel):
    """激励消息响应."""

    message: str = Field(..., description="激励消息")
    type: str = Field(..., description="消息类型")
    personalization: str = Field(..., description="个性化内容")
    generated_at: datetime = Field(..., description="生成时间")
