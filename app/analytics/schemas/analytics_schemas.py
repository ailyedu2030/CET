"""系统监控与数据分析的Pydantic模式定义."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MonitorType(str, Enum):
    """监控类型枚举."""

    SYSTEM = "system"
    TEACHING = "teaching"
    USER = "user"
    PERFORMANCE = "performance"


class AlertLevel(str, Enum):
    """告警级别枚举."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """指标类型枚举."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"


# ===== 系统监控模式 =====


class SystemMetric(BaseModel):
    """系统指标模式."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: str = Field(..., description="单位")
    timestamp: datetime = Field(..., description="时间戳")
    labels: dict[str, str] = Field(default_factory=dict, description="标签")


class SystemHealthStatus(BaseModel):
    """系统健康状态模式."""

    model_config = ConfigDict(from_attributes=True)

    service_name: str = Field(..., description="服务名称")
    status: str = Field(..., description="状态：healthy/degraded/unhealthy")
    uptime: float = Field(..., description="运行时间（秒）")
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    network_io: dict[str, float] = Field(default_factory=dict, description="网络IO")
    last_check: datetime = Field(..., description="最后检查时间")


class DatabaseMetrics(BaseModel):
    """数据库指标模式."""

    model_config = ConfigDict(from_attributes=True)

    active_connections: int = Field(..., description="活跃连接数")
    slow_queries: int = Field(..., description="慢查询数")
    database_size: float = Field(..., description="数据库大小(GB)")
    query_per_second: float = Field(..., description="每秒查询数")
    response_time: float = Field(..., description="平均响应时间(ms)")
    buffer_hit_ratio: float = Field(..., description="缓冲区命中率")


# ===== 教学监控模式 =====


class TeachingQualityMetric(BaseModel):
    """教学质量指标模式."""

    model_config = ConfigDict(from_attributes=True)

    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    student_count: int = Field(..., description="学生数量")
    completion_rate: float = Field(..., description="完成率")
    average_score: float = Field(..., description="平均分数")
    satisfaction_score: float = Field(..., description="满意度评分")
    interaction_count: int = Field(..., description="互动次数")
    resource_usage: float = Field(..., description="资源使用率")
    period_start: datetime = Field(..., description="统计开始时间")
    period_end: datetime = Field(..., description="统计结束时间")


class LearningProgress(BaseModel):
    """学习进度统计模式."""

    model_config = ConfigDict(from_attributes=True)

    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")
    total_lessons: int = Field(..., description="总课程数")
    completed_lessons: int = Field(..., description="已完成课程数")
    total_exercises: int = Field(..., description="总练习数")
    completed_exercises: int = Field(..., description="已完成练习数")
    total_study_time: int = Field(..., description="总学习时间（分钟）")
    average_score: float = Field(..., description="平均分数")
    last_activity: datetime = Field(..., description="最后活动时间")


# ===== 报表模式 =====


class ReportRequest(BaseModel):
    """报表请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    report_type: str = Field(..., description="报表类型")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    filters: dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    export_format: str = Field(default="json", description="输出格式：json/excel/pdf")


class ReportResponse(BaseModel):
    """报表响应模式."""

    model_config = ConfigDict(from_attributes=True)

    report_id: str = Field(..., description="报表ID")
    report_type: str = Field(..., description="报表类型")
    title: str | None = Field(None, description="报表标题")
    generated_at: datetime = Field(..., description="生成时间")
    status: str = Field(..., description="状态：completed/failed/processing")
    data: dict[str, Any] = Field(..., description="报表数据")
    summary: dict[str, Any] | None = Field(None, description="数据摘要")
    charts: list[dict[str, Any]] = Field(default_factory=list, description="图表配置")
    export_format: str | None = Field(None, description="导出格式")
    exported_content: str | None = Field(None, description="导出内容")
    error_message: str | None = Field(None, description="错误信息")


class DashboardData(BaseModel):
    """监控大屏数据模式."""

    model_config = ConfigDict(from_attributes=True)

    system_status: SystemHealthStatus = Field(..., description="系统状态")
    user_statistics: dict[str, int] = Field(..., description="用户统计")
    teaching_metrics: list[TeachingQualityMetric] = Field(..., description="教学指标")
    recent_alerts: list["AlertRecord"] = Field(..., description="最近告警")
    performance_trends: dict[str, list[float]] = Field(..., description="性能趋势")
    refresh_time: datetime = Field(..., description="刷新时间")


# ===== 监控与报告模式 =====


class MonitoringAlert(BaseModel):
    """监控告警模式."""

    model_config = ConfigDict(from_attributes=True)

    level: str = Field(..., description="告警级别")
    type: str = Field(..., description="告警类型")
    message: str = Field(..., description="告警消息")
    timestamp: str = Field(..., description="告警时间戳")


class SystemHealthReport(BaseModel):
    """系统健康报告模式."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime = Field(..., description="报告时间")
    health_score: float = Field(..., description="健康评分")
    status: str = Field(..., description="系统状态")
    performance_metrics: dict[str, Any] = Field(..., description="性能指标")
    active_alerts: list[MonitoringAlert] = Field(..., description="活跃告警")
    uptime: float = Field(..., description="运行时间")
    resource_usage: dict[str, Any] = Field(..., description="资源使用情况")
    database_health: dict[str, Any] = Field(..., description="数据库健康状况")
    storage_health: dict[str, Any] = Field(..., description="存储健康状况")


class TeachingActivity(BaseModel):
    """教学活动模式."""

    model_config = ConfigDict(from_attributes=True)

    activity_type: str = Field(..., description="活动类型")
    participant_count: int = Field(..., description="参与人数")
    completion_rate: float = Field(..., description="完成率")
    timestamp: datetime = Field(..., description="活动时间")


class MonitoringRequest(BaseModel):
    """监控请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    report_types: list[str] = Field(default=["system", "teaching"], description="报告类型")


class UserBehaviorReport(BaseModel):
    """用户行为报告模式."""

    model_config = ConfigDict(from_attributes=True)

    report_period: dict[str, Any] = Field(..., description="报告周期")
    user_statistics: dict[str, Any] = Field(..., description="用户统计")
    login_behavior: dict[str, Any] = Field(..., description="登录行为")
    learning_progress: dict[str, Any] = Field(..., description="学习进度")
    retention_analysis: dict[str, Any] = Field(..., description="留存分析")
    visualizations: dict[str, Any] = Field(..., description="可视化图表")
    generated_at: datetime = Field(..., description="生成时间")


# ===== 数据备份与恢复模式 =====


class BackupRequest(BaseModel):
    """备份请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    backup_type: str = Field(..., description="备份类型：full/incremental/differential")
    tables: list[str] = Field(default=[], description="要备份的表名列表")
    storage_location: str = Field(default="local", description="存储位置：local/cloud/both")
    compression: bool = Field(default=True, description="是否压缩")
    encryption: bool = Field(default=True, description="是否加密")
    description: str | None = Field(None, description="备份描述")


class BackupInfo(BaseModel):
    """备份信息模式."""

    model_config = ConfigDict(from_attributes=True)

    backup_id: str = Field(..., description="备份ID")
    backup_type: str = Field(..., description="备份类型")
    file_path: str = Field(..., description="备份文件路径")
    file_size: int = Field(..., description="文件大小（字节）")
    checksum: str = Field(..., description="文件校验和")
    created_at: datetime = Field(..., description="创建时间")
    expires_at: datetime | None = Field(None, description="过期时间")
    status: str = Field(..., description="状态：pending/running/completed/failed")
    tables_included: list[str] = Field(..., description="包含的表")
    compression_ratio: float | None = Field(None, description="压缩比")
    encryption_enabled: bool = Field(..., description="是否加密")


class RestoreRequest(BaseModel):
    """恢复请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    backup_id: str = Field(..., description="要恢复的备份ID")
    restore_type: str = Field(..., description="恢复类型：full/partial/point_in_time")
    tables: list[str] = Field(default=[], description="要恢复的表名列表")
    target_time: datetime | None = Field(None, description="目标时间点")
    confirm_overwrite: bool = Field(default=False, description="确认覆盖现有数据")
    validate_before_restore: bool = Field(default=True, description="恢复前验证备份")


class RestoreInfo(BaseModel):
    """恢复信息模式."""

    model_config = ConfigDict(from_attributes=True)

    restore_id: str = Field(..., description="恢复ID")
    backup_id: str = Field(..., description="源备份ID")
    status: str = Field(..., description="状态：pending/running/completed/failed")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    tables_restored: list[str] = Field(..., description="已恢复的表")
    records_restored: int = Field(default=0, description="恢复记录数")
    error_message: str | None = Field(None, description="错误信息")


class BackupConfig(BaseModel):
    """备份配置模式."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="配置名称")
    backup_type: str = Field(..., description="备份类型")
    schedule: str = Field(..., description="备份计划（cron表达式）")
    retention_days: int = Field(default=30, description="保留天数")
    max_backups: int = Field(default=10, description="最大备份数量")
    storage_locations: list[str] = Field(..., description="存储位置列表")
    tables_to_backup: list[str] = Field(default=[], description="备份表列表")
    compression_enabled: bool = Field(default=True, description="启用压缩")
    encryption_enabled: bool = Field(default=True, description="启用加密")
    enabled: bool = Field(default=True, description="是否启用")


class BackupStatistics(BaseModel):
    """备份统计模式."""

    model_config = ConfigDict(from_attributes=True)

    total_backups: int = Field(..., description="总备份数")
    successful_backups: int = Field(..., description="成功备份数")
    failed_backups: int = Field(..., description="失败备份数")
    total_size: int = Field(..., description="总占用空间")
    last_backup_time: datetime | None = Field(None, description="最后备份时间")
    next_scheduled_backup: datetime | None = Field(None, description="下次计划备份时间")
    backup_frequency: dict[str, int] = Field(..., description="备份频率统计")
    storage_distribution: dict[str, int] = Field(..., description="存储分布")


# ===== 预测与告警模式 =====


class PredictionRequest(BaseModel):
    """预测请求模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    metric_name: str = Field(..., description="指标名称")
    prediction_type: str = Field(..., description="预测类型：failure/capacity/performance")
    time_range: int = Field(default=7, description="预测时间范围（天）")
    confidence_level: float = Field(default=0.85, description="置信水平")


class PredictionResult(BaseModel):
    """预测结果模式."""

    model_config = ConfigDict(from_attributes=True)

    metric_name: str = Field(..., description="指标名称")
    prediction_type: str = Field(..., description="预测类型")
    confidence: float = Field(..., description="预测置信度")
    predicted_date: datetime | None = Field(None, description="预测发生日期")
    risk_level: str = Field(..., description="风险级别：low/medium/high/critical")
    recommendations: list[str] = Field(..., description="建议措施")
    historical_data: list[dict[str, Any]] = Field(..., description="历史数据")
    model_accuracy: float = Field(..., description="模型准确率")


class AlertRule(BaseModel):
    """告警规则模式."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="规则名称")
    metric_name: str = Field(..., description="指标名称")
    condition: str = Field(..., description="触发条件")
    threshold: float = Field(..., description="阈值")
    level: AlertLevel = Field(..., description="告警级别")
    enabled: bool = Field(default=True, description="是否启用")
    notification_channels: list[str] = Field(..., description="通知渠道")


class AlertRecord(BaseModel):
    """告警记录模式."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="告警ID")
    rule_name: str = Field(..., description="规则名称")
    level: AlertLevel = Field(..., description="告警级别")
    message: str = Field(..., description="告警消息")
    metric_value: float = Field(..., description="当前指标值")
    threshold: float = Field(..., description="阈值")
    triggered_at: datetime = Field(..., description="触发时间")
    resolved_at: datetime | None = Field(None, description="解决时间")
    status: str = Field(..., description="状态：active/resolved/suppressed")
    acknowledgment: dict[str, Any] | None = Field(None, description="确认信息")


# ===== 统计分析模式 =====


class StatisticsQuery(BaseModel):
    """统计查询模式."""

    model_config = ConfigDict(str_strip_whitespace=True)

    metrics: list[str] = Field(..., description="指标列表")
    dimensions: list[str] = Field(default_factory=list, description="维度列表")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    group_by: str | None = Field(None, description="分组字段")
    aggregation: str = Field(default="avg", description="聚合方式：sum/avg/max/min/count")


class StatisticsResult(BaseModel):
    """统计结果模式."""

    model_config = ConfigDict(from_attributes=True)

    query_id: str = Field(..., description="查询ID")
    data: list[dict[str, Any]] = Field(..., description="统计数据")
    summary: dict[str, float] = Field(..., description="汇总统计")
    total_records: int = Field(..., description="总记录数")
    execution_time: float = Field(..., description="执行时间（秒）")
    cached: bool = Field(default=False, description="是否使用缓存")


class PerformanceBenchmark(BaseModel):
    """性能基准模式."""

    model_config = ConfigDict(from_attributes=True)

    component: str = Field(..., description="组件名称")
    operation: str = Field(..., description="操作类型")
    avg_response_time: float = Field(..., description="平均响应时间(ms)")
    p95_response_time: float = Field(..., description="95%响应时间(ms)")
    p99_response_time: float = Field(..., description="99%响应时间(ms)")
    throughput: float = Field(..., description="吞吐量(ops/sec)")
    error_rate: float = Field(..., description="错误率")
    benchmark_date: datetime = Field(..., description="基准测试日期")
