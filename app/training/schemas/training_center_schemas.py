"""学生综合训练中心 - 数据模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.training.models.training_center_models import (
    DifficultyLevel,
    TrainingMode,
    TrainingType,
)


# 基础模式
class TrainingCenterBase(BaseModel):
    """训练中心基础模式"""

    name: str = Field(..., description="训练中心名称", max_length=255)
    description: str | None = Field(None, description="描述")
    preferred_difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE, description="偏好难度"
    )
    daily_target_minutes: int = Field(default=60, description="每日目标训练时长(分钟)", ge=10, le=300)
    weekly_target_sessions: int = Field(default=5, description="每周目标训练次数", ge=1, le=14)


class TrainingCenterCreate(TrainingCenterBase):
    """创建训练中心的请求模式"""


class TrainingCenterUpdate(BaseModel):
    """更新训练中心的请求模式"""

    name: str | None = Field(None, description="训练中心名称", max_length=255)
    description: str | None = Field(None, description="描述")
    preferred_difficulty: DifficultyLevel | None = Field(None, description="偏好难度")
    daily_target_minutes: int | None = Field(None, description="每日目标训练时长(分钟)", ge=10, le=300)
    weekly_target_sessions: int | None = Field(None, description="每周目标训练次数", ge=1, le=14)
    is_active: bool | None = Field(None, description="是否激活")


class TrainingCenterResponse(TrainingCenterBase):
    """训练中心响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="学生ID")
    is_active: bool = Field(..., description="是否激活")

    # 统计数据
    total_sessions: int = Field(..., description="总训练次数")
    total_minutes: int = Field(..., description="总训练时长")
    current_streak: int = Field(..., description="当前连续训练天数")
    best_streak: int = Field(..., description="最佳连续训练天数")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_training_at: datetime | None = Field(None, description="最后训练时间")

    class Config:
        from_attributes = True


# 训练会话模式
class TrainingSessionBase(BaseModel):
    """训练会话基础模式"""

    training_type: TrainingType = Field(..., description="训练类型")
    training_mode: TrainingMode = Field(..., description="训练模式")
    difficulty_level: DifficultyLevel = Field(..., description="难度等级")


class TrainingSessionCreate(TrainingSessionBase):
    """创建训练会话的请求模式"""

    training_center_id: int = Field(..., description="训练中心ID")


class TrainingSessionUpdate(BaseModel):
    """更新训练会话的请求模式"""

    answers_data: dict[str, Any] | None = Field(None, description="答案数据")
    is_completed: bool | None = Field(None, description="是否完成")


class TrainingSessionResponse(TrainingSessionBase):
    """训练会话响应模式"""

    id: int = Field(..., description="ID")
    training_center_id: int = Field(..., description="训练中心ID")
    user_id: int = Field(..., description="学生ID")

    # 训练内容
    questions_data: dict[str, Any] | None = Field(None, description="题目数据")
    answers_data: dict[str, Any] | None = Field(None, description="答案数据")

    # 训练结果
    total_questions: int = Field(..., description="总题数")
    correct_answers: int = Field(..., description="正确答案数")
    accuracy_rate: float = Field(..., description="正确率")
    completion_rate: float = Field(..., description="完成率")

    # 时间统计
    duration_minutes: int = Field(..., description="训练时长(分钟)")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")

    # 状态
    is_completed: bool = Field(..., description="是否完成")
    is_graded: bool = Field(..., description="是否已批改")

    # AI分析结果
    ai_analysis: dict[str, Any] | None = Field(None, description="AI分析结果")
    weak_points: list[str] | None = Field(None, description="薄弱知识点")
    recommendations: list[str] | None = Field(None, description="学习建议")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 训练进度模式
class TrainingProgressResponse(BaseModel):
    """训练进度响应模式"""

    id: int = Field(..., description="ID")
    training_center_id: int = Field(..., description="训练中心ID")
    user_id: int = Field(..., description="学生ID")

    # 进度信息
    training_type: TrainingType = Field(..., description="训练类型")
    knowledge_point: str = Field(..., description="知识点")

    # 能力评估
    mastery_level: float = Field(..., description="掌握程度(0-1)")
    confidence_score: float = Field(..., description="置信度(0-1)")
    improvement_rate: float = Field(..., description="提升速度")

    # 统计数据
    practice_count: int = Field(..., description="练习次数")
    correct_count: int = Field(..., description="正确次数")
    recent_accuracy: float = Field(..., description="近期正确率")

    # 时间信息
    first_encounter_at: datetime = Field(..., description="首次接触时间")
    last_practice_at: datetime = Field(..., description="最后练习时间")
    mastery_achieved_at: datetime | None = Field(None, description="掌握达成时间")

    class Config:
        from_attributes = True


# 列表响应模式
class TrainingCenterListResponse(BaseModel):
    """训练中心列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[TrainingCenterResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class TrainingSessionListResponse(BaseModel):
    """训练会话列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[TrainingSessionResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


# 训练模式选择模式
class TrainingModeSelection(BaseModel):
    """训练模式选择模式"""

    training_type: TrainingType = Field(..., description="训练类型")
    training_mode: TrainingMode = Field(..., description="训练模式")
    difficulty_level: DifficultyLevel = Field(..., description="难度等级")
    question_count: int = Field(default=10, description="题目数量", ge=1, le=50)


# 训练统计模式
class TrainingStatistics(BaseModel):
    """训练统计模式"""

    total_sessions: int = Field(..., description="总训练次数")
    total_minutes: int = Field(..., description="总训练时长")
    average_accuracy: float = Field(..., description="平均正确率")
    current_streak: int = Field(..., description="当前连续训练天数")
    best_streak: int = Field(..., description="最佳连续训练天数")

    # 按类型统计
    vocabulary_sessions: int = Field(..., description="词汇训练次数")
    listening_sessions: int = Field(..., description="听力训练次数")
    reading_sessions: int = Field(..., description="阅读训练次数")
    writing_sessions: int = Field(..., description="写作训练次数")
    translation_sessions: int = Field(..., description="翻译训练次数")

    # 进度分析
    weak_knowledge_points: list[str] = Field(..., description="薄弱知识点")
    strong_knowledge_points: list[str] = Field(..., description="强项知识点")
    improvement_suggestions: list[str] = Field(..., description="改进建议")


# 训练目标模式
class TrainingGoalBase(BaseModel):
    """训练目标基础模式"""

    goal_type: str = Field(..., description="目标类型", max_length=20)
    goal_title: str = Field(..., description="目标标题", max_length=200)
    goal_description: str | None = Field(None, description="目标描述")
    target_value: float = Field(..., description="目标值", ge=0)
    unit: str = Field(..., description="单位", max_length=20)
    start_date: datetime = Field(..., description="开始日期")
    target_date: datetime = Field(..., description="目标日期")


class TrainingGoalCreate(TrainingGoalBase):
    """创建训练目标的请求模式"""

    training_center_id: int = Field(..., description="训练中心ID")


class TrainingGoalUpdate(BaseModel):
    """更新训练目标的请求模式"""

    goal_title: str | None = Field(None, description="目标标题", max_length=200)
    goal_description: str | None = Field(None, description="目标描述")
    target_value: float | None = Field(None, description="目标值", ge=0)
    target_date: datetime | None = Field(None, description="目标日期")
    is_active: bool | None = Field(None, description="是否激活")


class TrainingGoalResponse(TrainingGoalBase):
    """训练目标响应模式"""

    id: int = Field(..., description="ID")
    training_center_id: int = Field(..., description="训练中心ID")
    user_id: int = Field(..., description="学生ID")
    current_value: float = Field(..., description="当前值")
    is_active: bool = Field(..., description="是否激活")
    is_completed: bool = Field(..., description="是否完成")
    completion_rate: float = Field(..., description="完成率")
    completed_date: datetime | None = Field(None, description="完成日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 训练成就模式
class TrainingAchievementResponse(BaseModel):
    """训练成就响应模式"""

    id: int = Field(..., description="ID")
    training_center_id: int = Field(..., description="训练中心ID")
    user_id: int = Field(..., description="学生ID")
    achievement_type: str = Field(..., description="成就类型")
    achievement_name: str = Field(..., description="成就名称")
    achievement_description: str | None = Field(None, description="成就描述")
    achievement_icon: str | None = Field(None, description="成就图标URL")
    condition_type: str = Field(..., description="条件类型")
    condition_value: float = Field(..., description="条件值")
    current_progress: float = Field(..., description="当前进度")
    reward_points: int = Field(..., description="奖励积分")
    reward_items: dict[str, Any] | None = Field(None, description="奖励物品")
    is_unlocked: bool = Field(..., description="是否解锁")
    is_claimed: bool = Field(..., description="是否领取")
    unlocked_at: datetime | None = Field(None, description="解锁时间")
    claimed_at: datetime | None = Field(None, description="领取时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# 训练反馈模式
class TrainingFeedbackCreate(BaseModel):
    """创建训练反馈的请求模式"""

    training_session_id: int = Field(..., description="训练会话ID")
    feedback_type: str = Field(..., description="反馈类型", max_length=20)
    rating: int = Field(..., description="评分(1-5)", ge=1, le=5)
    content: str | None = Field(None, description="反馈内容")
    difficulty_rating: int | None = Field(None, description="难度评分(1-5)", ge=1, le=5)
    usefulness_rating: int | None = Field(None, description="有用性评分(1-5)", ge=1, le=5)
    engagement_rating: int | None = Field(None, description="参与度评分(1-5)", ge=1, le=5)
    suggestions: str | None = Field(None, description="改进建议")
    tags: list[str] | None = Field(None, description="标签")
    is_anonymous: bool = Field(default=False, description="是否匿名")


class TrainingFeedbackResponse(BaseModel):
    """训练反馈响应模式"""

    id: int = Field(..., description="ID")
    training_session_id: int = Field(..., description="训练会话ID")
    user_id: int = Field(..., description="学生ID")
    feedback_type: str = Field(..., description="反馈类型")
    rating: int = Field(..., description="评分(1-5)")
    content: str | None = Field(None, description="反馈内容")
    difficulty_rating: int | None = Field(None, description="难度评分(1-5)")
    usefulness_rating: int | None = Field(None, description="有用性评分(1-5)")
    engagement_rating: int | None = Field(None, description="参与度评分(1-5)")
    suggestions: str | None = Field(None, description="改进建议")
    tags: list[str] | None = Field(None, description="标签")
    is_anonymous: bool = Field(..., description="是否匿名")
    is_processed: bool = Field(..., description="是否已处理")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# 综合训练中心仪表板模式
class TrainingCenterDashboard(BaseModel):
    """训练中心仪表板模式"""

    training_center: TrainingCenterResponse = Field(..., description="训练中心信息")
    recent_sessions: list[TrainingSessionResponse] = Field(..., description="最近训练会话")
    active_goals: list[TrainingGoalResponse] = Field(..., description="活跃目标")
    recent_achievements: list[TrainingAchievementResponse] = Field(..., description="最近成就")
    statistics: TrainingStatistics = Field(..., description="统计数据")
    recommendations: dict[str, Any] = Field(..., description="个性化推荐")


# 训练计划模式
class TrainingPlan(BaseModel):
    """训练计划模式"""

    plan_id: str = Field(..., description="计划ID")
    plan_name: str = Field(..., description="计划名称")
    plan_description: str = Field(..., description="计划描述")
    duration_weeks: int = Field(..., description="计划周数")
    difficulty_level: DifficultyLevel = Field(..., description="难度等级")
    training_types: list[TrainingType] = Field(..., description="训练类型")
    daily_sessions: int = Field(..., description="每日训练次数")
    session_duration: int = Field(..., description="单次训练时长(分钟)")
    target_accuracy: float = Field(..., description="目标正确率")
    milestones: list[dict[str, Any]] = Field(..., description="里程碑")


# 学习路径模式
class LearningPath(BaseModel):
    """学习路径模式"""

    path_id: str = Field(..., description="路径ID")
    path_name: str = Field(..., description="路径名称")
    current_level: DifficultyLevel = Field(..., description="当前等级")
    target_level: DifficultyLevel = Field(..., description="目标等级")
    progress_percentage: float = Field(..., description="进度百分比")
    estimated_completion_days: int = Field(..., description="预计完成天数")
    next_milestones: list[dict[str, Any]] = Field(..., description="下一个里程碑")
    knowledge_gaps: list[str] = Field(..., description="知识缺口")
    recommended_actions: list[str] = Field(..., description="推荐行动")
