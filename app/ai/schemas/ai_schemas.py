"""AI模块的Pydantic数据模式."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =================== 大纲相关 Schemas ===================


class SyllabusGenerationRequest(BaseModel):
    """大纲生成请求."""

    model_config = ConfigDict(from_attributes=True)

    course_id: int = Field(..., description="课程ID")
    title: str = Field(..., max_length=255, description="大纲标题")
    course_objectives: list[str] = Field(..., min_length=1, description="课程目标列表")
    source_materials: dict[str, Any] = Field(..., description="源材料信息(教材、考纲等)")
    target_hours: int = Field(..., gt=0, description="总课时数")
    difficulty_level: str = Field(..., description="难度级别: beginner/intermediate/advanced")
    special_requirements: str | None = Field(None, description="特殊要求说明")


class SyllabusCreate(BaseModel):
    """大纲创建数据."""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=255, description="大纲标题")
    course_id: int = Field(..., description="课程ID")
    content: dict[str, Any] = Field(..., description="大纲内容结构化数据")
    version: str = Field(default="1.0.0", description="版本号")
    ai_generated: bool = Field(default=True, description="是否AI生成")
    source_materials: dict[str, Any] | None = Field(None, description="生成大纲的源材料信息")


class SyllabusUpdate(BaseModel):
    """大纲更新数据."""

    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(None, max_length=255, description="大纲标题")
    content: dict[str, Any] | None = Field(None, description="大纲内容")
    version: str | None = Field(None, description="版本号")
    status: str | None = Field(None, description="状态")
    source_materials: dict[str, Any] | None = Field(None, description="源材料信息")


class SyllabusResponse(BaseModel):
    """大纲响应数据."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    course_id: int
    teacher_id: int
    content: dict[str, Any]
    version: str
    status: str
    ai_generated: bool
    source_materials: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class SyllabusListResponse(BaseModel):
    """大纲列表响应."""

    model_config = ConfigDict(from_attributes=True)

    syllabi: list[SyllabusResponse]
    total: int
    page: int
    size: int


# =================== 教案相关 Schemas ===================


class LessonPlanGenerationRequest(BaseModel):
    """教案生成请求."""

    model_config = ConfigDict(from_attributes=True)

    syllabus_id: int = Field(..., description="大纲ID")
    lesson_number: int = Field(..., gt=0, description="课时编号")
    title: str = Field(..., max_length=255, description="教案标题")
    duration_minutes: int = Field(default=45, gt=0, description="课程时长(分钟)")
    focus_areas: list[str] = Field(..., description="重点关注领域")
    student_level: str = Field(..., description="学生水平: beginner/intermediate/advanced")
    class_size: int | None = Field(None, gt=0, description="班级规模")
    available_resources: list[str] = Field(default_factory=list, description="可用资源列表")


class LessonPlanCreate(BaseModel):
    """教案创建数据."""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=255, description="教案标题")
    syllabus_id: int = Field(..., description="关联大纲ID")
    lesson_number: int = Field(..., gt=0, description="课时编号")
    duration_minutes: int = Field(default=45, gt=0, description="课程时长")
    learning_objectives: list[str] = Field(..., description="学习目标列表")
    content_structure: dict[str, Any] = Field(..., description="教学内容结构")
    teaching_methods: list[str] = Field(..., description="教学方法列表")
    resources_needed: list[str] = Field(..., description="所需资源列表")
    assessment_methods: list[str] = Field(..., description="评估方法列表")
    homework_assignments: dict[str, Any] | None = Field(None, description="作业安排")


class LessonPlanUpdate(BaseModel):
    """教案更新数据."""

    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(None, max_length=255, description="教案标题")
    duration_minutes: int | None = Field(None, gt=0, description="课程时长")
    learning_objectives: list[str] | None = Field(None, description="学习目标")
    content_structure: dict[str, Any] | None = Field(None, description="内容结构")
    teaching_methods: list[str] | None = Field(None, description="教学方法")
    resources_needed: list[str] | None = Field(None, description="所需资源")
    assessment_methods: list[str] | None = Field(None, description="评估方法")
    homework_assignments: dict[str, Any] | None = Field(None, description="作业安排")
    ai_suggestions: dict[str, Any] | None = Field(None, description="AI建议")


class LessonPlanResponse(BaseModel):
    """教案响应数据."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    syllabus_id: int
    lesson_number: int
    duration_minutes: int
    learning_objectives: list[str]
    content_structure: dict[str, Any]
    teaching_methods: list[str]
    resources_needed: list[str]
    assessment_methods: list[str]
    homework_assignments: dict[str, Any] | None
    ai_suggestions: dict[str, Any] | None
    collaboration_log: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class LessonPlanListResponse(BaseModel):
    """教案列表响应."""

    model_config = ConfigDict(from_attributes=True)

    lesson_plans: list[LessonPlanResponse]
    total: int
    page: int
    size: int


# =================== 课程表相关 Schemas ===================


class ScheduleGenerationRequest(BaseModel):
    """课程表生成请求."""

    model_config = ConfigDict(from_attributes=True)

    syllabus_id: int = Field(..., description="大纲ID")
    class_id: int = Field(..., description="班级ID")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    preferred_time_slots: list[dict[str, str]] = Field(..., description="偏好时间段列表")
    classroom_preferences: list[str] | None = Field(None, description="教室偏好列表")
    exclude_dates: list[datetime] = Field(default_factory=list, description="排除日期列表")
    lessons_per_week: int = Field(default=2, gt=0, description="每周课时数")


class LessonScheduleCreate(BaseModel):
    """课程安排创建数据."""

    model_config = ConfigDict(from_attributes=True)

    lesson_plan_id: int = Field(..., description="教案ID")
    class_id: int = Field(..., description="班级ID")
    scheduled_date: datetime = Field(..., description="计划上课日期")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    classroom: str | None = Field(None, max_length=100, description="教室位置")
    notes: str | None = Field(None, description="备注信息")


class LessonScheduleUpdate(BaseModel):
    """课程安排更新数据."""

    model_config = ConfigDict(from_attributes=True)

    scheduled_date: datetime | None = Field(None, description="计划日期")
    start_time: datetime | None = Field(None, description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")
    classroom: str | None = Field(None, max_length=100, description="教室")
    status: str | None = Field(None, description="状态")
    actual_start_time: datetime | None = Field(None, description="实际开始时间")
    actual_end_time: datetime | None = Field(None, description="实际结束时间")
    notes: str | None = Field(None, description="备注")
    ai_recommendations: dict[str, Any] | None = Field(None, description="AI建议")


class LessonScheduleResponse(BaseModel):
    """课程安排响应数据."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_plan_id: int
    class_id: int
    scheduled_date: datetime
    start_time: datetime
    end_time: datetime
    classroom: str | None
    status: str
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    notes: str | None
    ai_recommendations: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ScheduleListResponse(BaseModel):
    """课程表列表响应."""

    model_config = ConfigDict(from_attributes=True)

    schedules: list[LessonScheduleResponse]
    total: int
    page: int
    size: int


# =================== AI任务相关 Schemas ===================


class AITaskRequest(BaseModel):
    """AI任务请求."""

    model_config = ConfigDict(from_attributes=True)

    task_type: str = Field(..., description="任务类型: syllabus/lesson_plan/schedule")
    request_data: dict[str, Any] = Field(..., description="请求参数")
    api_model: str = Field(default="deepseek-chat", description="AI模型")


class AITaskResponse(BaseModel):
    """AI任务响应."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: str
    request_data: dict[str, Any]
    response_data: dict[str, Any] | None
    api_provider: str
    api_model: str
    tokens_used: int | None
    execution_time_ms: int | None
    status: str
    error_message: str | None
    created_at: datetime


# =================== 协作相关 Schemas ===================


class CollaborationJoinRequest(BaseModel):
    """协作加入请求."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")


class CollaborationUpdateRequest(BaseModel):
    """协作更新请求."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(..., description="会话ID")
    operation_type: str = Field(..., description="操作类型: update/insert/delete")
    target_path: str = Field(..., description="目标路径")
    data: dict[str, Any] = Field(..., description="变更数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


class CollaborationSessionResponse(BaseModel):
    """协作会话响应."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    resource_type: str
    resource_id: int
    participants: list[int]
    session_data: dict[str, Any]
    last_activity: datetime
    is_active: bool
    conflict_resolution_log: list[dict[str, Any]]
    created_at: datetime


# =================== 智能建议相关 Schemas ===================


class SmartSuggestionRequest(BaseModel):
    """智能建议请求."""

    model_config = ConfigDict(from_attributes=True)

    context_type: str = Field(..., description="上下文类型: syllabus/lesson_plan/schedule")
    context_data: dict[str, Any] = Field(..., description="上下文数据")
    suggestion_type: str = Field(
        ..., description="建议类型: optimization/alternative/troubleshooting"
    )
    user_preferences: dict[str, Any] | None = Field(None, description="用户偏好设置")


class SmartSuggestionResponse(BaseModel):
    """智能建议响应."""

    model_config = ConfigDict(from_attributes=True)

    suggestions: list[dict[str, Any]] = Field(..., description="建议列表")
    confidence_scores: list[float] = Field(..., description="置信度分数")
    reasoning: list[str] = Field(..., description="建议理由")
    implementation_difficulty: list[str] = Field(..., description="实施难度: easy/medium/hard")


# =================== 学情分析相关 Schema ===================


class LearningAnalysisRequest(BaseModel):
    """学情分析请求数据."""

    model_config = ConfigDict(from_attributes=True)

    class_id: int = Field(..., gt=0, description="班级ID")
    course_id: int = Field(..., gt=0, description="课程ID")
    analysis_type: str = Field(
        ..., description="分析类型", pattern=r"^(progress|difficulty|engagement)$"
    )
    analysis_period: str = Field(
        ..., description="分析周期", pattern=r"^(weekly|monthly|semester)$"
    )
    include_students: list[int] | None = Field(None, description="包含的学生ID列表，为空则分析全班")
    additional_params: dict[str, Any] | None = Field(None, description="额外分析参数")


class LearningAnalysisCreate(BaseModel):
    """创建学情分析记录."""

    model_config = ConfigDict(from_attributes=True)

    class_id: int = Field(..., gt=0, description="班级ID")
    course_id: int = Field(..., gt=0, description="课程ID")
    teacher_id: int = Field(..., gt=0, description="分析教师ID")
    analysis_type: str = Field(..., description="分析类型")
    analysis_period: str = Field(..., description="分析周期")
    student_count: int = Field(..., ge=0, description="分析学生数量")
    analysis_data: dict[str, Any] = Field(..., description="详细分析数据")
    insights: list[str] = Field(default_factory=list, description="关键洞察")
    risk_students: list[int] = Field(default_factory=list, description="风险学生ID列表")
    ai_generated: bool = Field(True, description="是否AI生成")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="分析置信度")


class LearningAnalysisResponse(BaseModel):
    """学情分析响应数据."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分析记录ID")
    class_id: int = Field(..., description="班级ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="分析教师ID")
    analysis_type: str = Field(..., description="分析类型")
    analysis_period: str = Field(..., description="分析周期")
    student_count: int = Field(..., description="分析学生数量")
    analysis_data: dict[str, Any] = Field(..., description="详细分析数据")
    insights: list[str] = Field(..., description="关键洞察")
    risk_students: list[int] = Field(..., description="风险学生ID列表")
    ai_generated: bool = Field(..., description="是否AI生成")
    confidence_score: float = Field(..., description="分析置信度")
    status: str = Field(..., description="分析状态")
    analysis_date: datetime = Field(..., description="分析日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class LearningAnalysisListResponse(BaseModel):
    """学情分析列表响应."""

    model_config = ConfigDict(from_attributes=True)

    analyses: list[LearningAnalysisResponse] = Field(..., description="分析列表")
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页大小")


# =================== 教学调整相关 Schema ===================


class TeachingAdjustmentRequest(BaseModel):
    """教学调整建议请求数据."""

    model_config = ConfigDict(from_attributes=True)

    learning_analysis_id: int | None = Field(None, gt=0, description="关联学情分析ID")
    class_id: int = Field(..., gt=0, description="班级ID")
    course_id: int = Field(..., gt=0, description="课程ID")
    adjustment_focus: str = Field(
        ..., description="调整重点", pattern=r"^(content|pace|method|assessment)$"
    )
    target_students: list[int] | None = Field(None, description="目标学生ID列表，为空则全班")
    current_issues: list[str] | None = Field(None, description="当前发现的问题")
    priority_level: str | None = Field(
        "medium", description="优先级", pattern=r"^(high|medium|low)$"
    )


class TeachingAdjustmentCreate(BaseModel):
    """创建教学调整建议记录."""

    model_config = ConfigDict(from_attributes=True)

    learning_analysis_id: int | None = Field(None, gt=0, description="关联学情分析ID")
    class_id: int = Field(..., gt=0, description="班级ID")
    course_id: int = Field(..., gt=0, description="课程ID")
    teacher_id: int = Field(..., gt=0, description="目标教师ID")
    adjustment_type: str = Field(..., description="调整类型")
    priority_level: str = Field(..., description="优先级")
    title: str = Field(..., max_length=200, description="调整建议标题")
    description: str = Field(..., description="详细调整说明")
    adjustments: dict[str, Any] = Field(..., description="具体调整方案")
    target_students: list[int] = Field(default_factory=list, description="目标学生ID列表")
    expected_outcome: str | None = Field(None, description="预期效果")
    implementation_timeline: str | None = Field(None, description="实施时间线")
    ai_generated: bool = Field(True, description="是否AI生成")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="建议置信度")
    reasoning: str | None = Field(None, description="建议依据说明")


class TeachingAdjustmentUpdate(BaseModel):
    """更新教学调整建议."""

    model_config = ConfigDict(from_attributes=True)

    implementation_status: str | None = Field(
        None,
        description="实施状态",
        pattern=r"^(pending|in_progress|completed|dismissed)$",
    )
    implementation_date: datetime | None = Field(None, description="开始实施日期")
    feedback: str | None = Field(None, description="实施反馈")
    effectiveness_rating: int | None = Field(None, ge=1, le=5, description="效果评分(1-5)")


class TeachingAdjustmentResponse(BaseModel):
    """教学调整建议响应数据."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="调整建议ID")
    learning_analysis_id: int | None = Field(..., description="关联学情分析ID")
    class_id: int = Field(..., description="班级ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="目标教师ID")
    adjustment_type: str = Field(..., description="调整类型")
    priority_level: str = Field(..., description="优先级")
    title: str = Field(..., description="调整建议标题")
    description: str = Field(..., description="详细调整说明")
    adjustments: dict[str, Any] = Field(..., description="具体调整方案")
    target_students: list[int] = Field(..., description="目标学生ID列表")
    expected_outcome: str | None = Field(..., description="预期效果")
    implementation_timeline: str | None = Field(..., description="实施时间线")
    ai_generated: bool = Field(..., description="是否AI生成")
    confidence_score: float = Field(..., description="建议置信度")
    reasoning: str | None = Field(..., description="建议依据说明")
    implementation_status: str = Field(..., description="实施状态")
    implementation_date: datetime | None = Field(..., description="开始实施日期")
    feedback: str | None = Field(..., description="实施反馈")
    effectiveness_rating: int | None = Field(..., description="效果评分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TeachingAdjustmentListResponse(BaseModel):
    """教学调整建议列表响应."""

    model_config = ConfigDict(from_attributes=True)

    adjustments: list[TeachingAdjustmentResponse] = Field(..., description="调整建议列表")
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页大小")
