"""学习相关的混入类定义."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class LearningProgressMixin:
    """学习进度混入类."""

    @declared_attr
    def learning_start_time(cls) -> Mapped[datetime | None]:
        """学习开始时间."""
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="学习开始时间",
        )

    @declared_attr
    def learning_end_time(cls) -> Mapped[datetime | None]:
        """学习结束时间."""
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="学习结束时间",
        )

    @declared_attr
    def study_duration(cls) -> Mapped[int]:
        """学习时长（秒）."""
        return mapped_column(
            Integer,
            default=0,
            nullable=False,
            comment="学习时长（秒）",
        )

    @declared_attr
    def learning_progress(cls) -> Mapped[float]:
        """学习进度（0.0-1.0）."""
        return mapped_column(
            Float,
            default=0.0,
            nullable=False,
            comment="学习进度（0.0-1.0）",
        )

    @declared_attr
    def knowledge_points(cls) -> Mapped[list[str]]:
        """知识点列表."""
        return mapped_column(
            JSON,
            default=list,
            nullable=False,
            comment="知识点列表",
        )

    def start_learning_session(self) -> None:
        """开始学习会话."""
        self.learning_start_time = datetime.utcnow()
        self.learning_progress = 0.0

    def end_learning_session(self) -> None:
        """结束学习会话."""
        self.learning_end_time = datetime.utcnow()
        if self.learning_start_time:
            duration = self.learning_end_time - self.learning_start_time
            self.study_duration = int(duration.total_seconds())

    def update_progress(self, progress: float) -> None:
        """更新学习进度."""
        self.learning_progress = max(0.0, min(1.0, progress))

    def add_knowledge_point(self, point: str) -> None:
        """添加知识点."""
        if point not in self.knowledge_points:
            self.knowledge_points.append(point)

    def get_learning_summary(self) -> dict[str, Any]:
        """获取学习摘要."""
        return {
            "start_time": (
                self.learning_start_time.isoformat() if self.learning_start_time else None
            ),
            "end_time": (self.learning_end_time.isoformat() if self.learning_end_time else None),
            "duration_minutes": self.study_duration // 60,
            "progress": self.learning_progress,
            "knowledge_points": self.knowledge_points,
        }


class AIAnalysisMixin:
    """AI分析混入类."""

    @declared_attr
    def ai_analysis_result(cls) -> Mapped[dict[str, Any] | None]:
        """AI分析结果."""
        return mapped_column(
            JSON,
            nullable=True,
            comment="AI分析结果",
        )

    @declared_attr
    def ai_confidence_score(cls) -> Mapped[float]:
        """AI置信度分数."""
        return mapped_column(
            Float,
            default=0.0,
            nullable=False,
            comment="AI置信度分数",
        )

    @declared_attr
    def ai_model_version(cls) -> Mapped[str | None]:
        """AI模型版本."""
        return mapped_column(
            String(50),
            nullable=True,
            comment="AI模型版本",
        )

    @declared_attr
    def ai_analysis_time(cls) -> Mapped[datetime | None]:
        """AI分析时间."""
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="AI分析时间",
        )

    @declared_attr
    def human_review_required(cls) -> Mapped[bool]:
        """是否需要人工复审."""
        return mapped_column(
            Boolean,
            default=False,
            nullable=False,
            comment="是否需要人工复审",
        )

    def set_ai_analysis(
        self,
        result: dict[str, Any],
        confidence: float,
        model_version: str,
    ) -> None:
        """设置AI分析结果."""
        self.ai_analysis_result = result
        self.ai_confidence_score = confidence
        self.ai_model_version = model_version
        self.ai_analysis_time = datetime.utcnow()
        # 低置信度需要人工复审
        self.human_review_required = confidence < 0.8

    def get_ai_analysis_summary(self) -> dict[str, Any]:
        """获取AI分析摘要."""
        return {
            "confidence": self.ai_confidence_score,
            "model_version": self.ai_model_version,
            "analysis_time": (self.ai_analysis_time.isoformat() if self.ai_analysis_time else None),
            "needs_review": self.human_review_required,
            "result": self.ai_analysis_result,
        }


class AdaptiveLearningMixin:
    """自适应学习混入类."""

    @declared_attr
    def difficulty_preference(cls) -> Mapped[float]:
        """难度偏好（0.0-1.0）."""
        return mapped_column(
            Float,
            default=0.5,
            nullable=False,
            comment="难度偏好（0.0-1.0）",
        )

    @declared_attr
    def learning_style(cls) -> Mapped[str | None]:
        """学习风格."""
        return mapped_column(
            String(20),
            nullable=True,
            comment="学习风格",
        )

    @declared_attr
    def weak_knowledge_points(cls) -> Mapped[list[str]]:
        """薄弱知识点."""
        return mapped_column(
            JSON,
            default=list,
            nullable=False,
            comment="薄弱知识点",
        )

    @declared_attr
    def strong_knowledge_points(cls) -> Mapped[list[str]]:
        """强项知识点."""
        return mapped_column(
            JSON,
            default=list,
            nullable=False,
            comment="强项知识点",
        )

    @declared_attr
    def adaptive_parameters(cls) -> Mapped[dict[str, Any]]:
        """自适应参数."""
        return mapped_column(
            JSON,
            default=dict,
            nullable=False,
            comment="自适应参数",
        )

    def set_learning_style(self, style: str) -> None:
        """设置学习风格."""
        self.learning_style = style

    def update_difficulty_preference(self, preference: float) -> None:
        """更新难度偏好."""
        self.difficulty_preference = max(0.0, min(1.0, preference))

    def add_weak_point(self, point: str) -> None:
        """添加薄弱知识点."""
        if point not in self.weak_knowledge_points:
            self.weak_knowledge_points.append(point)

    def add_strong_point(self, point: str) -> None:
        """添加强项知识点."""
        if point not in self.strong_knowledge_points:
            self.strong_knowledge_points.append(point)

    def get_adaptive_profile(self) -> dict[str, Any]:
        """获取自适应档案."""
        return {
            "difficulty_preference": self.difficulty_preference,
            "learning_style": self.learning_style,
            "weak_points": self.weak_knowledge_points,
            "strong_points": self.strong_knowledge_points,
            "parameters": self.adaptive_parameters,
        }


class ComplianceMixin:
    """合规性混入类 - 教育系统特有的合规要求."""

    @declared_attr
    def daily_study_time(cls) -> Mapped[int]:
        """每日学习时长（秒）."""
        return mapped_column(
            Integer,
            default=0,
            nullable=False,
            comment="每日学习时长（秒）",
        )

    @declared_attr
    def last_study_date(cls) -> Mapped[datetime | None]:
        """最后学习日期."""
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="最后学习日期",
        )

    @declared_attr
    def parental_consent(cls) -> Mapped[bool]:
        """家长同意（未成年人）."""
        return mapped_column(
            Boolean,
            default=True,
            nullable=False,
            comment="家长同意（未成年人）",
        )

    @declared_attr
    def content_filter_level(cls) -> Mapped[str]:
        """内容过滤级别."""
        return mapped_column(
            String(20),
            default="standard",
            nullable=False,
            comment="内容过滤级别",
        )

    @declared_attr
    def privacy_settings(cls) -> Mapped[dict[str, Any]]:
        """隐私设置."""
        return mapped_column(
            JSON,
            default=dict,
            nullable=False,
            comment="隐私设置",
        )

    def check_daily_limit(self, max_minutes: int) -> bool:
        """检查每日学习时长限制."""
        today = datetime.utcnow().date()
        if self.last_study_date and self.last_study_date.date() == today:
            daily_minutes: int = self.daily_study_time // 60
            return daily_minutes < max_minutes
        return True

    def add_study_time(self, minutes: int) -> None:
        """添加学习时长."""
        today = datetime.utcnow().date()
        if not self.last_study_date or self.last_study_date.date() != today:
            # 新的一天，重置计时
            self.daily_study_time = 0

        self.daily_study_time += minutes * 60
        self.last_study_date = datetime.utcnow()

    def set_content_filter(self, level: str) -> None:
        """设置内容过滤级别."""
        self.content_filter_level = level

    def get_compliance_status(self) -> dict[str, Any]:
        """获取合规状态."""
        return {
            "daily_study_minutes": self.daily_study_time // 60,
            "last_study_date": (self.last_study_date.isoformat() if self.last_study_date else None),
            "parental_consent": self.parental_consent,
            "content_filter": self.content_filter_level,
            "privacy_settings": self.privacy_settings,
        }
