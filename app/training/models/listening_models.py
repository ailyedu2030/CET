"""听力训练系统 - 数据模型"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base_model import BaseModel
from app.shared.models.enums import DifficultyLevel


class ListeningExercise(BaseModel):
    """听力练习模型"""

    __tablename__ = "listening_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="练习标题")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="练习描述")

    # 练习分类
    exercise_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="练习类型：short_conversation, long_conversation, passage, lecture",
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        nullable=False, comment="难度等级"
    )

    # 练习内容
    audio_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("listening_audio_files.id"),
        nullable=True,
        comment="音频文件ID（需求22可选）",
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True, comment="听力原文")

    # 题目信息
    questions_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="题目数据"
    )
    total_questions: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="题目总数"
    )

    # 时间设置
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="练习时长（秒）"
    )
    audio_duration: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="音频时长（秒）"
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="标签"
    )

    # 关联关系
    audio_file: Mapped["ListeningAudioFile | None"] = relationship(
        "ListeningAudioFile", back_populates="exercises"
    )
    sessions: Mapped[list["ListeningSession"]] = relationship(
        "ListeningSession", back_populates="exercise"
    )
    results: Mapped[list["ListeningResult"]] = relationship(
        "ListeningResult", back_populates="exercise"
    )

    def __repr__(self) -> str:
        return f"<ListeningExercise(id={self.id}, title='{self.title}', type='{self.exercise_type}')>"


class ListeningAudioFile(BaseModel):
    """听力音频文件模型"""

    __tablename__ = "listening_audio_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名")
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="原始文件名"
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件路径")
    file_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="文件URL"
    )

    # 文件信息
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小（字节）")
    duration: Mapped[float] = mapped_column(Float, nullable=False, comment="音频时长（秒）")
    format: Mapped[str] = mapped_column(String(20), nullable=False, comment="音频格式")
    sample_rate: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="采样率"
    )
    bitrate: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="比特率")

    # 元数据
    audio_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="音频元数据"
    )

    # 状态信息
    is_processed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否已处理"
    )
    upload_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="上传用户ID"
    )

    # 关联关系
    exercises: Mapped[list["ListeningExercise"]] = relationship(
        "ListeningExercise", back_populates="audio_file"
    )

    def __repr__(self) -> str:
        return f"<ListeningAudioFile(id={self.id}, filename='{self.filename}', duration={self.duration}s)>"


class ListeningSession(BaseModel):
    """听力训练会话模型"""

    __tablename__ = "listening_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="学生ID"
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("listening_exercises.id"), nullable=False, comment="练习ID"
    )

    # 会话信息
    session_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="会话名称"
    )
    start_time: Mapped[datetime] = mapped_column(nullable=False, comment="开始时间")
    end_time: Mapped[datetime | None] = mapped_column(nullable=True, comment="结束时间")

    # 进度信息
    current_question: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="当前题目"
    )
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="总题目数"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否完成"
    )

    # 答题数据
    answers: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="答题数据"
    )
    audio_progress: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="音频播放进度"
    )

    # 时间统计
    total_time_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="总用时（秒）"
    )
    listening_time_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="听音频时间（秒）"
    )
    answering_time_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="答题时间（秒）"
    )

    # 关联关系
    exercise: Mapped["ListeningExercise"] = relationship(
        "ListeningExercise", back_populates="sessions"
    )
    result: Mapped["ListeningResult | None"] = relationship(
        "ListeningResult", back_populates="session", uselist=False
    )

    def __repr__(self) -> str:
        return f"<ListeningSession(id={self.id}, student_id={self.student_id}, exercise_id={self.exercise_id})>"


class ListeningResult(BaseModel):
    """听力训练结果模型"""

    __tablename__ = "listening_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("listening_sessions.id"), nullable=False, comment="会话ID"
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="学生ID"
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("listening_exercises.id"), nullable=False, comment="练习ID"
    )

    # 成绩信息
    total_score: Mapped[float] = mapped_column(Float, nullable=False, comment="总分")
    max_score: Mapped[float] = mapped_column(Float, nullable=False, comment="满分")
    percentage: Mapped[float] = mapped_column(Float, nullable=False, comment="得分率")

    # 答题统计
    correct_answers: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="正确答案数"
    )
    wrong_answers: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="错误答案数"
    )
    unanswered: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="未答题数"
    )
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="总题目数"
    )

    # 详细结果
    question_results: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="题目详细结果"
    )
    answer_analysis: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="答案分析"
    )

    # 时间统计
    completion_time: Mapped[datetime] = mapped_column(nullable=False, comment="完成时间")
    total_time_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="总用时（秒）"
    )
    average_time_per_question: Mapped[float] = mapped_column(
        Float, nullable=False, comment="平均每题用时（秒）"
    )

    # 能力评估
    listening_ability_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="听力能力评分"
    )
    comprehension_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="理解能力评分"
    )
    vocabulary_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="词汇掌握评分"
    )

    # 改进建议
    improvement_suggestions: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="改进建议"
    )
    weak_areas: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False, comment="薄弱环节"
    )

    # 关联关系
    session: Mapped["ListeningSession"] = relationship(
        "ListeningSession", back_populates="result"
    )
    exercise: Mapped["ListeningExercise"] = relationship(
        "ListeningExercise", back_populates="results"
    )


class ListeningSettings(BaseModel):
    """用户听力播放设置模型"""

    __tablename__ = "listening_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID"
    )
    exercise_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("listening_exercises.id"),
        nullable=True,
        index=True,
        comment="练习ID（可选）",
    )

    # 播放设置
    playback_speed: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0, comment="播放速度"
    )
    repeat_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="重复播放次数"
    )
    show_subtitles: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否显示字幕"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    session: Mapped["ListeningSession"] = relationship(
        "ListeningSession", back_populates="result"
    )
    exercise: Mapped["ListeningExercise"] = relationship(
        "ListeningExercise", back_populates="results"
    )

    def __repr__(self) -> str:
        return f"<ListeningResult(id={self.id}, score={self.total_score}/{self.max_score}, percentage={self.percentage:.1f}%)>"


# H5: Dictation Exercise Model
class DictationExercise(BaseModel):
    """听写练习模型"""

    __tablename__ = "dictation_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listening_exercises.id"), nullable=False
    )
    user_answers: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_blanks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )


# H6: Speaking Practice Model
class SpeakingPractice(BaseModel):
    """口语练习模型"""

    __tablename__ = "speaking_practices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listening_exercises.id"), nullable=False
    )
    audio_file_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("listening_audio_files.id"), nullable=True
    )
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pronunciation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fluency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )


# H7: Pronunciation Practice Model
class PronunciationPractice(BaseModel):
    """发音练习模型"""

    __tablename__ = "pronunciation_practices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listening_exercises.id"), nullable=False
    )
    target_text: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_file_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("listening_audio_files.id"), nullable=True
    )
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    phoneme_scores: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )
