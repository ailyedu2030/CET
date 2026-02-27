/**
 * 需求16：系统协同功能类型定义
 *
 * 定义双驱动机制、动态适配、标准化对接、权限隔离、数据贯通相关的类型
 */

// ==================== 基础类型 ====================

export interface SystemCoordinationConfig {
  dual_drive_enabled: boolean
  adaptive_learning_enabled: boolean
  standardization_enabled: boolean
  permission_isolation_enabled: boolean
  data_flow_enabled: boolean
}

export interface CoordinationMetrics {
  sync_frequency: number
  data_freshness: number
  system_performance: number
  user_satisfaction: number
  error_rate: number
}

// ==================== 双驱动机制类型 ====================

export interface StudentDriveData {
  student_id: number
  real_time_feedback: FeedbackItem[]
  learning_suggestions: LearningSuggestion[]
  difficulty_adjustments: DifficultyAdjustment[]
  adaptive_content: AdaptiveContent[]
  last_updated: string
}

export interface TeacherDriveData {
  teacher_id: number
  class_id: number
  data_dashboard: DashboardData
  teaching_optimization: any[]
  content_adjustments: any[]
  strategy_recommendations: any[]
  last_updated: string
}

export interface FeedbackItem {
  id: string
  type: 'performance' | 'suggestion' | 'warning' | 'achievement'
  content: string
  priority: 'high' | 'medium' | 'low'
  timestamp: string
  action_required: boolean
}

export interface LearningSuggestion {
  id: string
  category: 'study_method' | 'time_management' | 'content_focus' | 'skill_improvement'
  title: string
  description: string
  estimated_impact: number
  difficulty: 'easy' | 'medium' | 'hard'
  estimated_time_minutes: number
}

export interface DifficultyAdjustment {
  subject: string
  current_level: number
  target_level: number
  adjustment_reason: string
  adjustment_date: string
  effectiveness_score?: number
}

export interface AdaptiveContent {
  content_id: string
  content_type: 'exercise' | 'reading' | 'video' | 'quiz'
  title: string
  difficulty_level: number
  estimated_duration: number
  personalization_score: number
  recommended_order: number
}

// ==================== 动态适配类型 ====================

export interface AdaptationStrategy {
  strategy_id: string
  strategy_name: string
  target_skills: string[]
  adaptation_rules: AdaptationRule[]
  effectiveness_metrics: EffectivenessMetric[]
  last_updated: string
}

export interface AdaptationRule {
  rule_id: string
  condition: string
  action: string
  priority: number
  success_rate: number
}

export interface EffectivenessMetric {
  metric_name: string
  current_value: number
  target_value: number
  trend: 'improving' | 'stable' | 'declining'
  measurement_date: string
}

export interface LearningPath {
  path_id: string
  student_id: number
  current_stage: number
  total_stages: number
  milestones: Milestone[]
  estimated_completion_date: string
  personalization_factors: PersonalizationFactor[]
}

export interface Milestone {
  milestone_id: string
  title: string
  description: string
  target_skills: string[]
  completion_criteria: string[]
  estimated_duration_days: number
  is_completed: boolean
  completion_date?: string
}

export interface PersonalizationFactor {
  factor_name: string
  factor_value: number
  weight: number
  impact_description: string
}

// ==================== 标准化对接类型 ====================

export interface StandardCompliance {
  standard_name: string
  compliance_level: number
  compliance_details: ComplianceDetail[]
  last_assessment_date: string
  next_assessment_date: string
}

export interface ComplianceDetail {
  requirement_id: string
  requirement_description: string
  compliance_status: 'compliant' | 'partial' | 'non_compliant'
  gap_analysis: string
  remediation_plan?: string
}

export interface DataStandard {
  standard_id: string
  standard_name: string
  version: string
  format_specifications: FormatSpecification[]
  validation_rules: ValidationRule[]
  migration_support: boolean
}

export interface FormatSpecification {
  field_name: string
  data_type: string
  required: boolean
  format_pattern?: string
  validation_rules: string[]
}

export interface ValidationRule {
  rule_id: string
  rule_description: string
  validation_logic: string
  error_message: string
}

// ==================== 权限隔离类型 ====================

export interface PermissionMatrix {
  user_type: 'student' | 'teacher' | 'admin'
  permissions: Permission[]
  restrictions: Restriction[]
  audit_requirements: AuditRequirement[]
}

export interface Permission {
  permission_id: string
  permission_name: string
  resource_type: string
  allowed_operations: string[]
  conditions: PermissionCondition[]
  expiry_date?: string
}

export interface Restriction {
  restriction_id: string
  restriction_type: 'access' | 'operation' | 'data' | 'time'
  description: string
  enforcement_level: 'strict' | 'moderate' | 'advisory'
  bypass_conditions?: string[]
}

export interface PermissionCondition {
  condition_type: 'time' | 'location' | 'context' | 'approval'
  condition_value: string
  is_required: boolean
}

export interface AuditRequirement {
  audit_type: 'access' | 'modification' | 'deletion' | 'export'
  retention_period_days: number
  audit_detail_level: 'basic' | 'detailed' | 'comprehensive'
  notification_required: boolean
}

// ==================== 数据贯通类型 ====================

export interface DataFlowMapping {
  flow_id: string
  source_system: string
  target_system: string
  data_entities: DataEntity[]
  transformation_rules: TransformationRule[]
  sync_schedule: SyncSchedule
  quality_metrics: DataQualityMetric[]
}

export interface DataEntity {
  entity_name: string
  entity_type: string
  source_schema: Record<string, any>
  target_schema: Record<string, any>
  mapping_rules: FieldMapping[]
}

export interface FieldMapping {
  source_field: string
  target_field: string
  transformation_function?: string
  validation_rules: string[]
  is_required: boolean
}

export interface TransformationRule {
  rule_id: string
  rule_name: string
  source_format: string
  target_format: string
  transformation_logic: string
  error_handling: string
}

export interface SyncSchedule {
  schedule_type: 'real_time' | 'batch' | 'event_driven'
  frequency?: string
  batch_size?: number
  retry_policy: RetryPolicy
  monitoring_enabled: boolean
}

export interface RetryPolicy {
  max_retries: number
  retry_interval_seconds: number
  exponential_backoff: boolean
  failure_notification: boolean
}

export interface DataQualityMetric {
  metric_name: string
  metric_type: 'completeness' | 'accuracy' | 'consistency' | 'timeliness'
  current_score: number
  target_score: number
  measurement_method: string
}

// ==================== 可视化监控类型 ====================

export interface DashboardData {
  dashboard_id: string
  dashboard_name: string
  widgets: DashboardWidget[]
  refresh_interval_seconds: number
  last_updated: string
  user_permissions: string[]
}

export interface DashboardWidget {
  widget_id: string
  widget_type: 'chart' | 'table' | 'metric' | 'heatmap' | 'progress'
  title: string
  data_source: string
  configuration: WidgetConfiguration
  position: WidgetPosition
  refresh_enabled: boolean
}

export interface WidgetConfiguration {
  chart_type?: 'line' | 'bar' | 'pie' | 'scatter' | 'heatmap'
  data_fields: string[]
  filters: Record<string, any>
  aggregation_method?: string
  time_range?: string
}

export interface WidgetPosition {
  x: number
  y: number
  width: number
  height: number
}

export interface HeatmapData {
  knowledge_points: KnowledgePointStatus[]
  mastery_levels: MasteryLevel[]
  time_periods: TimePeriod[]
  visualization_config: HeatmapConfig
}

export interface KnowledgePointStatus {
  knowledge_point_id: string
  knowledge_point_name: string
  mastery_score: number
  difficulty_level: number
  student_count: number
  last_updated: string
}

export interface MasteryLevel {
  level_id: string
  level_name: string
  score_range: [number, number]
  color_code: string
  description: string
}

export interface TimePeriod {
  period_id: string
  start_date: string
  end_date: string
  period_type: 'day' | 'week' | 'month' | 'semester'
}

export interface HeatmapConfig {
  color_scheme: string
  scale_type: 'linear' | 'logarithmic'
  show_labels: boolean
  interactive_enabled: boolean
  drill_down_enabled: boolean
}

// ==================== 系统架构类型 ====================

export interface SystemArchitecture {
  architecture_type: 'microservices' | 'monolithic' | 'hybrid'
  components: SystemComponent[]
  communication_patterns: CommunicationPattern[]
  scalability_config: ScalabilityConfig
  reliability_metrics: ReliabilityMetric[]
}

export interface SystemComponent {
  component_id: string
  component_name: string
  component_type: 'service' | 'database' | 'cache' | 'queue' | 'gateway'
  dependencies: string[]
  health_status: 'healthy' | 'degraded' | 'unhealthy'
  performance_metrics: ComponentMetric[]
}

export interface CommunicationPattern {
  pattern_type: 'synchronous' | 'asynchronous' | 'event_driven'
  protocol: 'http' | 'websocket' | 'message_queue' | 'grpc'
  reliability_level: 'at_least_once' | 'at_most_once' | 'exactly_once'
  error_handling: string
}

export interface ScalabilityConfig {
  horizontal_scaling: boolean
  vertical_scaling: boolean
  auto_scaling_enabled: boolean
  scaling_triggers: ScalingTrigger[]
  resource_limits: ResourceLimit[]
}

export interface ScalingTrigger {
  metric_name: string
  threshold_value: number
  scaling_action: 'scale_up' | 'scale_down'
  cooldown_period_seconds: number
}

export interface ResourceLimit {
  resource_type: 'cpu' | 'memory' | 'storage' | 'network'
  min_allocation: number
  max_allocation: number
  unit: string
}

export interface ReliabilityMetric {
  metric_name: string
  current_value: number
  target_value: number
  measurement_unit: string
  trend: 'improving' | 'stable' | 'declining'
}

export interface ComponentMetric {
  metric_name: string
  metric_value: number
  metric_unit: string
  timestamp: string
  alert_threshold?: number
}
