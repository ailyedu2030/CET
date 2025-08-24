/**
 * 管理员相关的类型定义
 * 对应后端API的数据结构
 */

// 审计日志相关类型
export interface AuditLog {
  id: number
  user_id: number
  username: string
  action_type: string
  resource_type: string
  resource_id?: string
  details?: Record<string, any>
  ip_address: string
  user_agent?: string
  timestamp: string
  success: boolean
  error_message?: string
}

export interface AuditStatistics {
  total_logs: number
  success_rate: number
  failed_operations: number
  unique_users: number
  top_actions: Array<{ action: string; count: number }>
  hourly_distribution: Array<{ hour: number; count: number }>
}

// 权限管理相关类型
export interface Permission {
  id: number
  name: string
  code: string
  description?: string
  module: string
  action: string
  resource?: string
  is_active: boolean
  created_at: string
}

export interface Role {
  id: number
  name: string
  code: string
  description?: string
  is_active: boolean
  permissions: Permission[]
  user_count: number
  created_at: string
}

export interface UserRole {
  id: number
  user_id: number
  username: string
  email: string
  user_type: string
  roles: Role[]
  is_active: boolean
}

// MFA相关类型
export interface MFAConfig {
  user_id: number
  mfa_enabled: boolean
  primary_method: string
  backup_methods: string[]
  configured_methods: string[]
  require_for_admin: boolean
  last_updated: string
}

export interface TOTPSetup {
  secret_key: string
  qr_code_url: string
  backup_codes: string[]
  app_name: string
  account_name: string
}

export interface MFAStatistics {
  total_users: number
  mfa_enabled_users: number
  mfa_adoption_rate: number
  method_distribution: Record<string, number>
  recent_verifications: number
  failed_verifications: number
  success_rate: number
}

export interface UserMFAStatus {
  user_id: number
  username: string
  email: string
  user_type: string
  mfa_enabled: boolean
  configured_methods: string[]
  last_verification: string
  verification_count: number
  is_locked: boolean
}

// 备份管理相关类型
export interface BackupInfo {
  backup_id: string
  backup_type: string
  file_path: string
  file_size: number
  status: string
  created_at: string
  expires_at?: string
  description?: string
  tables: string[]
  compression: boolean
  encryption: boolean
  checksum: string
}

export interface RestoreInfo {
  restore_id: string
  backup_id: string
  restore_type: string
  status: string
  progress_percentage: number
  current_step: string
  estimated_remaining_time: string
  started_at: string
  completed_at?: string
  error_message?: string
}

export interface BackupStatistics {
  total_backups: number
  successful_backups: number
  failed_backups: number
  total_size: number
  average_size: number
  backup_types: Record<string, { count: number; size: number }>
  period_start: string
  period_end: string
}

// 规则管理相关类型
export interface RuleConfiguration {
  id: number
  rule_name: string
  rule_type: string
  rule_category: string
  rule_config: Record<string, any>
  scope_type: string
  scope_value?: string
  is_enabled: boolean
  priority: number
  description?: string
  created_by: number
  created_at: string
  updated_at: string
}

export interface RuleStatistics {
  rule_id: number
  rule_name: string
  total_executions: number
  successful_executions: number
  violation_count: number
  exception_count: number
  compliance_rate: number
  effectiveness_score: number
  last_execution: string
  trend: string
}

export interface RuleTemplate {
  template_name: string
  template_type: string
  description: string
  default_config: Record<string, any>
  required_fields: string[]
  optional_fields: string[]
  examples: Array<{
    name: string
    config: Record<string, any>
  }>
}

// 课程管理相关类型
export interface Course {
  id: number
  course_name: string
  course_code: string
  description?: string
  category: string
  difficulty_level: number
  duration_weeks: number
  total_hours: number
  max_students: number
  prerequisites: string[]
  learning_objectives: string[]
  syllabus_content: Record<string, any>
  status: string
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
  enrolled_students: number
  assigned_teachers: number
  completion_rate: number
}

export interface CourseAssignment {
  id: number
  course_id: number
  course_name: string
  teacher_id: number
  teacher_name: string
  class_id: number
  class_name: string
  start_date: string
  end_date: string
  schedule: Record<string, any>
  status: string
  created_at: string
}

export interface CourseStatistics {
  total_courses: number
  active_courses: number
  draft_courses: number
  archived_courses: number
  total_enrollments: number
  average_completion_rate: number
  popular_categories: Array<{ category: string; count: number }>
  recent_activities: Array<{
    action: string
    course_name: string
    timestamp: string
    user: string
  }>
}

// 通用API响应类型
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  pages: number
  current_page: number
  per_page: number
}

// 请求参数类型
export interface BackupRequest {
  backup_type: string
  tables: string[]
  storage_location: string
  compression: boolean
  encryption: boolean
  description?: string
}

export interface RestoreRequest {
  backup_id: string
  restore_type: string
  tables: string[]
  confirm_overwrite: boolean
  validate_before_restore: boolean
  target_time?: string
}

export interface PermissionAssignRequest {
  user_id: number
  role_ids: number[]
  permissions: number[]
}

export interface RuleCreateRequest {
  rule_name: string
  rule_type: string
  rule_category: string
  rule_config: Record<string, any>
  scope_type: string
  scope_value?: string
  is_enabled: boolean
  priority: number
  description?: string
}

export interface MFAConfigRequest {
  user_id: number
  mfa_enabled: boolean
  primary_method: string
  backup_methods: string[]
  require_for_admin: boolean
}
