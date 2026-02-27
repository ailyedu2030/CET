"""学习计划与管理系统 - 数据模式"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.training.models.learning_plan_models import (
    PlanStatus,
    PlanType,
    TaskStatus,
)


# 学习计划模式
class LearningPlanBase(BaseModel):
    """学习计划基础模式"""

    plan_name: str = Field(..., description="计划名称", max_length=100)
    plan_description: str | None = Field(None, description="计划描述")
    plan_type: PlanType = Field(..., description="计划类型")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    estimated_hours: int | None = Field(None, description="预估学习时长(小时)", ge=1, le=1000)
    learning_goals: list[str] | None = Field(None, description="学习目标")
    target_score: int | None = Field(None, description="目标分数", ge=0, le=710)
    priority_level: int = Field(default=3, description="优先级(1-5)", ge=1, le=5)
    daily_study_time: int | None = Field(None, description="每日学习时间(分钟)", ge=10, le=480)
    study_schedule: dict[str, Any] | None = Field(None, description="学习时间表")
    reminder_settings: dict[str, Any] | None = Field(None, description="提醒设置")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls: type["LearningPlanBase"], v: datetime, info: Any) -> datetime:
        """验证结束日期必须晚于开始日期"""
        if hasattr(info, "data") and "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("结束日期必须晚于开始日期")
        return v

    @field_validator("plan_name")
    @classmethod
    def validate_plan_name(cls: type["LearningPlanBase"], v: str) -> str:
        """验证计划名称不能为空"""
        if not v or not v.strip():
            raise ValueError("计划名称不能为空")
        return v.strip()

    @field_validator("learning_goals")
    @classmethod
    def validate_learning_goals(
        cls: type["LearningPlanBase"], v: list[str] | None
    ) -> list[str] | None:
        """验证学习目标"""
        if v is not None:
            # 过滤空字符串
            v = [goal.strip() for goal in v if goal and goal.strip()]
            if len(v) > 10:
                raise ValueError("学习目标不能超过10个")
        return v


class LearningPlanCreate(LearningPlanBase):
    """创建学习计划的请求模式"""


class LearningPlanUpdate(BaseModel):
    """更新学习计划的请求模式"""

    plan_name: str | None = Field(None, description="计划名称", max_length=100)
    plan_description: str | None = Field(None, description="计划描述")
    plan_type: PlanType | None = Field(None, description="计划类型")
    end_date: datetime | None = Field(None, description="结束日期")
    estimated_hours: int | None = Field(None, description="预估学习时长(小时)", ge=1, le=1000)
    learning_goals: list[str] | None = Field(None, description="学习目标")
    target_score: int | None = Field(None, description="目标分数", ge=0, le=710)
    priority_level: int | None = Field(None, description="优先级(1-5)", ge=1, le=5)
    daily_study_time: int | None = Field(None, description="每日学习时间(分钟)", ge=10, le=480)
    study_schedule: dict[str, Any] | None = Field(None, description="学习时间表")
    reminder_settings: dict[str, Any] | None = Field(None, description="提醒设置")
    status: PlanStatus | None = Field(None, description="计划状态")


class LearningPlanResponse(LearningPlanBase):
    """学习计划响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="用户ID")
    status: PlanStatus = Field(..., description="计划状态")
    completion_rate: float = Field(..., description="完成率")
    actual_hours: float = Field(..., description="实际学习时长")
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    overdue_tasks: int = Field(..., description="逾期任务数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 学习任务模式
class LearningTaskBase(BaseModel):
    """学习任务基础模式"""

    task_name: str = Field(..., description="任务名称", max_length=200)
    task_description: str | None = Field(None, description="任务描述")
    task_type: str | None = Field(None, description="任务类型", max_length=50)
    scheduled_date: datetime = Field(..., description="计划日期")
    due_date: datetime | None = Field(None, description="截止日期")
    estimated_minutes: int | None = Field(None, description="预估时长(分钟)", ge=1, le=480)
    task_content: dict[str, Any] | None = Field(None, description="任务内容配置")
    resources: list[str] | None = Field(None, description="学习资源")
    requirements: list[str] | None = Field(None, description="完成要求")
    difficulty_level: int = Field(default=3, description="难度等级(1-5)", ge=1, le=5)


class LearningTaskCreate(LearningTaskBase):
    """创建学习任务的请求模式"""

    plan_id: int = Field(..., description="计划ID")


class LearningTaskUpdate(BaseModel):
    """更新学习任务的请求模式"""

    task_name: str | None = Field(None, description="任务名称", max_length=200)
    task_description: str | None = Field(None, description="任务描述")
    task_type: str | None = Field(None, description="任务类型", max_length=50)
    scheduled_date: datetime | None = Field(None, description="计划日期")
    due_date: datetime | None = Field(None, description="截止日期")
    estimated_minutes: int | None = Field(None, description="预估时长(分钟)", ge=1, le=480)
    task_content: dict[str, Any] | None = Field(None, description="任务内容配置")
    resources: list[str] | None = Field(None, description="学习资源")
    requirements: list[str] | None = Field(None, description="完成要求")
    difficulty_level: int | None = Field(None, description="难度等级(1-5)", ge=1, le=5)
    status: TaskStatus | None = Field(None, description="任务状态")
    completion_rate: float | None = Field(None, description="完成率", ge=0.0, le=1.0)
    actual_minutes: int | None = Field(None, description="实际时长(分钟)", ge=0)
    result_score: float | None = Field(None, description="完成得分", ge=0.0)
    self_rating: int | None = Field(None, description="自我评分(1-5)", ge=1, le=5)
    notes: str | None = Field(None, description="学习笔记")


class LearningTaskResponse(LearningTaskBase):
    """学习任务响应模式"""

    id: int = Field(..., description="ID")
    plan_id: int = Field(..., description="计划ID")
    user_id: int = Field(..., description="用户ID")
    status: TaskStatus = Field(..., description="任务状态")
    completion_rate: float = Field(..., description="完成率")
    actual_minutes: int = Field(..., description="实际时长(分钟)")
    started_at: datetime | None = Field(None, description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    result_score: float | None = Field(None, description="完成得分")
    result_data: dict[str, Any] | None = Field(None, description="完成结果数据")
    self_rating: int | None = Field(None, description="自我评分(1-5)")
    notes: str | None = Field(None, description="学习笔记")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 学习进度模式
class LearningProgressCreate(BaseModel):
    """创建学习进度的请求模式"""

    plan_id: int | None = Field(None, description="计划ID")
    record_date: datetime = Field(..., description="记录日期")
    study_minutes: int = Field(default=0, description="学习时长(分钟)", ge=0)
    tasks_completed: int = Field(default=0, description="完成任务数", ge=0)
    listening_score: float | None = Field(None, description="听力得分", ge=0.0)
    reading_score: float | None = Field(None, description="阅读得分", ge=0.0)
    writing_score: float | None = Field(None, description="写作得分", ge=0.0)
    overall_score: float | None = Field(None, description="综合得分", ge=0.0)
    login_count: int = Field(default=0, description="登录次数", ge=0)
    practice_count: int = Field(default=0, description="练习次数", ge=0)
    mistake_count: int = Field(default=0, description="错误次数", ge=0)
    focus_level: int | None = Field(None, description="专注度(1-5)", ge=1, le=5)
    satisfaction_level: int | None = Field(None, description="满意度(1-5)", ge=1, le=5)
    difficulty_perception: int | None = Field(None, description="难度感知(1-5)", ge=1, le=5)
    notes: str | None = Field(None, description="学习笔记")
    achievements: list[str] | None = Field(None, description="当日成就")


class LearningProgressResponse(BaseModel):
    """学习进度响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="用户ID")
    plan_id: int | None = Field(None, description="计划ID")
    record_date: datetime = Field(..., description="记录日期")
    study_minutes: int = Field(..., description="学习时长(分钟)")
    tasks_completed: int = Field(..., description="完成任务数")
    listening_score: float | None = Field(None, description="听力得分")
    reading_score: float | None = Field(None, description="阅读得分")
    writing_score: float | None = Field(None, description="写作得分")
    overall_score: float | None = Field(None, description="综合得分")
    login_count: int = Field(..., description="登录次数")
    practice_count: int = Field(..., description="练习次数")
    mistake_count: int = Field(..., description="错误次数")
    focus_level: int | None = Field(None, description="专注度(1-5)")
    satisfaction_level: int | None = Field(None, description="满意度(1-5)")
    difficulty_perception: int | None = Field(None, description="难度感知(1-5)")
    notes: str | None = Field(None, description="学习笔记")
    achievements: list[str] | None = Field(None, description="当日成就")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 学习统计模式
class LearningStatistics(BaseModel):
    """学习统计模式"""

    total_study_time: int = Field(..., description="总学习时间(分钟)")
    total_plans: int = Field(..., description="总计划数")
    active_plans: int = Field(..., description="进行中计划数")
    completed_plans: int = Field(..., description="已完成计划数")
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    overdue_tasks: int = Field(..., description="逾期任务数")
    average_completion_rate: float = Field(..., description="平均完成率")
    study_streak: int = Field(..., description="连续学习天数")
    weekly_study_time: list[int] = Field(..., description="每周学习时间")
    monthly_progress: dict[str, float] = Field(..., description="月度进度")
    skill_progress: dict[str, float] = Field(..., description="技能进度")


# 学习仪表板模式
class LearningDashboard(BaseModel):
    """学习仪表板模式"""

    today_tasks: list[LearningTaskResponse] = Field(..., description="今日任务")
    upcoming_tasks: list[LearningTaskResponse] = Field(..., description="即将到来的任务")
    overdue_tasks: list[LearningTaskResponse] = Field(..., description="逾期任务")
    recent_progress: list[LearningProgressResponse] = Field(..., description="最近进度")
    active_plans: list[LearningPlanResponse] = Field(..., description="进行中的计划")
    statistics: LearningStatistics = Field(..., description="统计数据")
    achievements: list[str] = Field(..., description="最近成就")
    recommendations: list[str] = Field(..., description="学习建议")


# 学习报告模式
class LearningReportCreate(BaseModel):
    """创建学习报告的请求模式"""

    plan_id: int | None = Field(None, description="计划ID")
    report_name: str = Field(..., description="报告名称", max_length=100)
    report_type: str = Field(..., description="报告类型", max_length=50)
    report_period: str | None = Field(None, description="报告周期", max_length=50)
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")


class LearningReportResponse(BaseModel):
    """学习报告响应模式"""

    id: int = Field(..., description="ID")
    user_id: int = Field(..., description="用户ID")
    plan_id: int | None = Field(None, description="计划ID")
    report_name: str = Field(..., description="报告名称")
    report_type: str = Field(..., description="报告类型")
    report_period: str | None = Field(None, description="报告周期")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    summary_data: dict[str, Any] | None = Field(None, description="汇总数据")
    detailed_data: dict[str, Any] | None = Field(None, description="详细数据")
    charts_data: dict[str, Any] | None = Field(None, description="图表数据")
    insights: list[str] | None = Field(None, description="洞察分析")
    recommendations: list[str] | None = Field(None, description="改进建议")
    is_generated: bool = Field(..., description="是否已生成")
    generation_time: datetime | None = Field(None, description="生成时间")
    file_path: str | None = Field(None, description="文件路径")
    is_shared: bool = Field(..., description="是否分享")
    share_token: str | None = Field(None, description="分享令牌")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 列表响应模式
class LearningPlanListResponse(BaseModel):
    """学习计划列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[LearningPlanResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class LearningTaskListResponse(BaseModel):
    """学习任务列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[LearningTaskResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class LearningProgressListResponse(BaseModel):
    """学习进度列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[LearningProgressResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class LearningReportListResponse(BaseModel):
    """学习报告列表响应模式"""

    success: bool = Field(..., description="是否成功")
    data: list[LearningReportResponse] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
