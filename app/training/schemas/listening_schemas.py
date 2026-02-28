"""听力训练系统 - 数据验证模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

from app.shared.models.enums import DifficultyLevel

# ============ 听力练习相关Schema ============


class ListeningExerciseBase(BaseModel):
    """听力练习基础Schema"""

    title: str = Field(..., max_length=255, description="练习标题")
    description: str | None = Field(None, description="练习描述")
    exercise_type: str = Field(
        ..., description="练习类型：short_conversation, long_conversation, passage, lecture"
    )
    difficulty_level: DifficultyLevel = Field(..., description="难度等级")
    transcript: str | None = Field(None, description="听力原文")
    questions_data: dict[str, Any] = Field(..., description="题目数据")
    total_questions: int = Field(default=0, ge=0, description="题目总数")
    duration_seconds: int | None = Field(None, ge=0, description="练习时长（秒）")
    audio_duration: float | None = Field(None, ge=0, description="音频时长（秒）")
    is_active: bool = Field(default=True, description="是否启用")
    tags: list[str] = Field(default_factory=list, description="标签")

    @validator("exercise_type")
    def validate_exercise_type(cls, v: str) -> str:
        allowed_types = [
            "short_conversation",
            "long_conversation",
            "passage",
            "lecture",
        ]
        if v not in allowed_types:
            raise ValueError(f"练习类型必须是以下之一: {', '.join(allowed_types)}")
        return v

    @validator("questions_data")
    def validate_questions_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("题目数据必须是字典格式")
        if "questions" not in v:
            raise ValueError("题目数据必须包含questions字段")
        return v


class ListeningExerciseCreate(ListeningExerciseBase):
    """创建听力练习Schema"""

    audio_file_id: int = Field(..., description="音频文件ID")


class ListeningExerciseUpdate(BaseModel):
    """更新听力练习Schema"""

    title: str | None = Field(None, max_length=255, description="练习标题")
    description: str | None = Field(None, description="练习描述")
    exercise_type: str | None = Field(None, description="练习类型")
    difficulty_level: DifficultyLevel | None = Field(None, description="难度等级")
    transcript: str | None = Field(None, description="听力原文")
    questions_data: dict[str, Any] | None = Field(None, description="题目数据")
    total_questions: int | None = Field(None, ge=0, description="题目总数")
    duration_seconds: int | None = Field(None, ge=0, description="练习时长（秒）")
    audio_duration: float | None = Field(None, ge=0, description="音频时长（秒）")
    is_active: bool | None = Field(None, description="是否启用")
    tags: list[str] | None = Field(None, description="标签")


class ListeningExercise(ListeningExerciseBase):
    """听力练习Schema"""

    id: int = Field(..., description="练习ID")
    audio_file_id: int = Field(..., description="音频文件ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============ 音频文件相关Schema ============


class ListeningAudioFileBase(BaseModel):
    """音频文件基础Schema"""

    filename: str = Field(..., max_length=255, description="文件名")
    original_filename: str = Field(..., max_length=255, description="原始文件名")
    file_path: str = Field(..., max_length=500, description="文件路径")
    file_url: str | None = Field(None, max_length=500, description="文件URL")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    duration: float = Field(..., ge=0, description="音频时长（秒）")
    format: str = Field(..., max_length=20, description="音频格式")
    sample_rate: int | None = Field(None, ge=0, description="采样率")
    bitrate: int | None = Field(None, ge=0, description="比特率")
    audio_metadata: dict[str, Any] = Field(default_factory=dict, description="音频元数据")
    is_processed: bool = Field(default=False, description="是否已处理")
    upload_user_id: int | None = Field(None, description="上传用户ID")


class ListeningAudioFileCreate(ListeningAudioFileBase):
    """创建音频文件Schema"""


class ListeningAudioFileUpdate(BaseModel):
    """更新音频文件Schema"""

    filename: str | None = Field(None, max_length=255, description="文件名")
    file_url: str | None = Field(None, max_length=500, description="文件URL")
    audio_metadata: dict[str, Any] | None = Field(None, description="音频元数据")
    is_processed: bool | None = Field(None, description="是否已处理")


class ListeningAudioFile(ListeningAudioFileBase):
    """音频文件Schema"""

    id: int = Field(..., description="文件ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============ 听力会话相关Schema ============


class ListeningSessionBase(BaseModel):
    """听力会话基础Schema"""

    session_name: str | None = Field(None, max_length=255, description="会话名称")
    current_question: int = Field(default=1, ge=1, description="当前题目")
    total_questions: int = Field(..., ge=1, description="总题目数")
    is_completed: bool = Field(default=False, description="是否完成")
    answers: dict[str, Any] = Field(default_factory=dict, description="答题数据")
    audio_progress: dict[str, Any] = Field(default_factory=dict, description="音频播放进度")


class ListeningSessionCreate(ListeningSessionBase):
    """创建听力会话Schema"""

    exercise_id: int = Field(..., description="练习ID")


class ListeningSessionUpdate(BaseModel):
    """更新听力会话Schema"""

    current_question: int | None = Field(None, ge=1, description="当前题目")
    is_completed: bool | None = Field(None, description="是否完成")
    answers: dict[str, Any] | None = Field(None, description="答题数据")
    audio_progress: dict[str, Any] | None = Field(None, description="音频播放进度")


class ListeningSession(ListeningSessionBase):
    """听力会话Schema"""

    id: int = Field(..., description="会话ID")
    student_id: int = Field(..., description="学生ID")
    exercise_id: int = Field(..., description="练习ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")
    total_time_seconds: int = Field(default=0, ge=0, description="总用时（秒）")
    listening_time_seconds: int = Field(default=0, ge=0, description="听音频时间（秒）")
    answering_time_seconds: int = Field(default=0, ge=0, description="答题时间（秒）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============ 听力结果相关Schema ============


class ListeningResultBase(BaseModel):
    """听力结果基础Schema"""

    total_score: float = Field(..., ge=0, description="总分")
    max_score: float = Field(..., ge=0, description="满分")
    percentage: float = Field(..., ge=0, le=100, description="得分率")
    correct_answers: int = Field(default=0, ge=0, description="正确答案数")
    wrong_answers: int = Field(default=0, ge=0, description="错误答案数")
    unanswered: int = Field(default=0, ge=0, description="未答题数")
    total_questions: int = Field(..., ge=1, description="总题目数")
    question_results: dict[str, Any] = Field(..., description="题目详细结果")
    answer_analysis: dict[str, Any] = Field(default_factory=dict, description="答案分析")
    total_time_seconds: int = Field(..., ge=0, description="总用时（秒）")
    average_time_per_question: float = Field(..., ge=0, description="平均每题用时（秒）")
    listening_ability_score: float | None = Field(
        None, ge=0, le=100, description="听力能力评分"
    )
    comprehension_score: float | None = Field(None, ge=0, le=100, description="理解能力评分")
    vocabulary_score: float | None = Field(None, ge=0, le=100, description="词汇掌握评分")
    improvement_suggestions: list[str] = Field(default_factory=list, description="改进建议")
    weak_areas: list[str] = Field(default_factory=list, description="薄弱环节")


class ListeningResultCreate(ListeningResultBase):
    """创建听力结果Schema"""

    session_id: int = Field(..., description="会话ID")
    exercise_id: int = Field(..., description="练习ID")


class ListeningResult(ListeningResultBase):
    """听力结果Schema"""

    id: int = Field(..., description="结果ID")
    session_id: int = Field(..., description="会话ID")
    student_id: int = Field(..., description="学生ID")
    exercise_id: int = Field(..., description="练习ID")
    completion_time: datetime = Field(..., description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============ 答题相关Schema ============


class SubmitAnswerRequest(BaseModel):
    """提交答案请求Schema"""

    question_id: str = Field(..., description="题目ID")
    answer: str | list[str] = Field(..., description="答案")
    time_spent: int = Field(..., ge=0, description="答题用时（秒）")
    is_final: bool = Field(default=False, description="是否最终提交")


class SubmitAnswersRequest(BaseModel):
    """批量提交答案请求Schema"""

    answers: list[SubmitAnswerRequest] = Field(..., description="答案列表")
    total_time: int = Field(..., ge=0, description="总用时（秒）")
    listening_time: int = Field(default=0, ge=0, description="听音频时间（秒）")
    answering_time: int = Field(default=0, ge=0, description="答题时间（秒）")


# ============ 统计相关Schema ============


class ListeningStatistics(BaseModel):
    """听力统计Schema"""

    total_exercises: int = Field(..., ge=0, description="总练习数")
    completed_exercises: int = Field(..., ge=0, description="已完成练习数")
    total_time_spent: int = Field(..., ge=0, description="总用时（秒）")
    average_score: float = Field(..., ge=0, le=100, description="平均分")
    best_score: float = Field(..., ge=0, le=100, description="最高分")
    improvement_rate: float = Field(..., description="进步率")
    weak_areas: list[str] = Field(default_factory=list, description="薄弱环节")
    strong_areas: list[str] = Field(default_factory=list, description="优势领域")
    recent_performance: list[dict[str, Any]] = Field(
        default_factory=list, description="近期表现"
    )


# ============ 响应Schema ============


class ListeningExerciseListResponse(BaseModel):
    """听力练习列表响应Schema"""

    success: bool = Field(..., description="是否成功")
    data: list[ListeningExercise] = Field(..., description="练习列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ListeningSessionResponse(BaseModel):
    """听力会话响应Schema"""

    success: bool = Field(..., description="是否成功")
    data: ListeningSession = Field(..., description="会话数据")
    exercise: ListeningExercise | None = Field(None, description="练习信息")


class ListeningResultResponse(BaseModel):
    """听力结果响应Schema"""

    success: bool = Field(..., description="是否成功")
    data: ListeningResult = Field(..., description="结果数据")
    session: ListeningSession | None = Field(None, description="会话信息")
    exercise: ListeningExercise | None = Field(None, description="练习信息")
