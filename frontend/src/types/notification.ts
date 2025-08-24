/**
 * 通知系统类型定义 - 需求16通知中枢类型声明
 */

// =================== 基础通知类型 ===================

export interface NotificationBase {
  title: string
  content: string
  notification_type: string
  priority: 'urgent' | 'high' | 'normal' | 'low'
  metadata?: Record<string, any>
}

export interface NotificationCreate extends NotificationBase {
  channels?: string[]
}

export interface NotificationResponse extends NotificationBase {
  id: number
  user_id: number
  channels: string[]
  is_read: boolean
  read_at?: string
  created_at: string
  send_results?: Record<string, any>
}

export interface NotificationUpdate {
  is_read?: boolean
  read_at?: string
}

// =================== 批量通知类型 ===================

export interface NotificationBatchCreate {
  notification_data: NotificationCreate
  target_type: 'user' | 'class' | 'role'
  target_ids: number[]
  channels?: string[]
}

// =================== 通知列表类型 ===================

export interface NotificationListRequest {
  user_id?: number
  notification_type?: string
  is_read?: boolean
  priority?: string
  start_date?: string
  end_date?: string
  page: number
  page_size: number
}

export interface NotificationListResponse {
  notifications: NotificationResponse[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// =================== 通知偏好类型 ===================

export interface NotificationPreferenceBase {
  enable_in_app: boolean
  enable_email: boolean
  enable_sms: boolean
  enable_push: boolean
  quiet_hours_start?: string
  quiet_hours_end?: string
  notification_types: Record<string, boolean>
  max_daily_notifications: number
  batch_similar_notifications: boolean
}

export interface NotificationPreferenceCreate extends NotificationPreferenceBase {
  user_id: number
}

export interface NotificationPreferenceUpdate extends NotificationPreferenceBase {}

export interface NotificationPreferenceResponse extends NotificationPreferenceBase {
  id: number
  user_id: number
  created_at: string
  updated_at?: string
}

// =================== 通知统计类型 ===================

export interface NotificationStats {
  total_notifications: number
  unread_count: number
  read_count: number
  by_type: Record<string, number>
  by_priority: Record<string, number>
  by_channel: Record<string, number>
  recent_activity: Array<{
    id: number
    title: string
    type: string
    created_at: string
    is_read: boolean
  }>
}

export interface NotificationAnalytics {
  delivery_rate: number
  read_rate: number
  response_time: number
  channel_effectiveness: Record<string, number>
  peak_hours: number[]
  user_engagement: Record<string, any>
}

// =================== 特定通知类型 - 需求16验收标准1 ===================

export interface TeachingPlanChangeNotification {
  plan_id: number
  change_type: string
  affected_classes: number[]
  change_details: Record<string, any>
  notify_channels: string[]
}

export interface TrainingAnomalyAlert {
  student_id: number
  anomaly_type: string
  anomaly_details: Record<string, any>
  teacher_ids: number[]
  urgency_level: 'urgent' | 'high' | 'normal'
}

export interface ResourceAuditNotification {
  resource_id: number
  audit_status: string
  resource_type: string
  creator_id: number
  audit_comments?: string
}

// =================== WebSocket类型 ===================

export interface WebSocketNotificationMessage {
  type: string
  notification: NotificationResponse
  timestamp: string
}

export interface WebSocketConnectionInfo {
  user_id: number
  connection_id: string
  connected_at: string
  last_heartbeat: string
}

// =================== 通知模板类型 ===================

export interface NotificationTemplateBase {
  name: string
  code: string
  title_template: string
  content_template: string
  category: string
  notification_type: string
  supported_channels: string[]
  default_channels: string[]
  variables: Record<string, any>
}

export interface NotificationTemplateCreate extends NotificationTemplateBase {
  is_active: boolean
}

export interface NotificationTemplateResponse extends NotificationTemplateBase {
  id: number
  is_active: boolean
  created_at: string
  updated_at?: string
}

// =================== 通知历史类型 ===================

export interface NotificationHistoryResponse {
  id: number
  notification_id: number
  sent_at: string
  send_results: Record<string, any>
  total_channels: number
  success_channels: number
}

export interface NotificationBatchResponse {
  id: number
  batch_name: string
  batch_type: string
  target_type: string
  target_ids: number[]
  total_recipients: number
  sent_count: number
  failed_count: number
  status: string
  started_at?: string
  completed_at?: string
  channels: string[]
  created_at: string
}

// =================== 通知渠道类型 ===================

export type NotificationChannel = 'in_app' | 'email' | 'sms' | 'push'

export interface ChannelConfig {
  name: string
  label: string
  icon: string
  enabled: boolean
  description: string
}

export const NOTIFICATION_CHANNELS: Record<NotificationChannel, ChannelConfig> = {
  in_app: {
    name: 'in_app',
    label: '系统内消息',
    icon: 'bell',
    enabled: true,
    description: '在系统内显示通知消息',
  },
  email: {
    name: 'email',
    label: '邮件通知',
    icon: 'mail',
    enabled: true,
    description: '发送邮件到用户邮箱',
  },
  sms: {
    name: 'sms',
    label: '短信通知',
    icon: 'message',
    enabled: false,
    description: '发送短信到用户手机',
  },
  push: {
    name: 'push',
    label: '推送通知',
    icon: 'notification',
    enabled: true,
    description: '浏览器推送通知',
  },
}

// =================== 通知类型定义 ===================

export type NotificationType =
  | 'teaching_plan_change'
  | 'training_anomaly'
  | 'resource_audit'
  | 'class_announcement'
  | 'teacher_notification'
  | 'system_maintenance'
  | 'grade_published'
  | 'assignment_reminder'
  | 'course_update'
  | 'exam_schedule'
  | 'system_alert'

export interface NotificationTypeConfig {
  type: NotificationType
  label: string
  description: string
  default_priority: 'urgent' | 'high' | 'normal' | 'low'
  default_channels: NotificationChannel[]
  icon: string
  color: string
}

export const NOTIFICATION_TYPES: Record<NotificationType, NotificationTypeConfig> = {
  teaching_plan_change: {
    type: 'teaching_plan_change',
    label: '教学计划变更',
    description: '教学计划发生变更时的通知',
    default_priority: 'high',
    default_channels: ['in_app', 'email'],
    icon: 'calendar',
    color: 'orange',
  },
  training_anomaly: {
    type: 'training_anomaly',
    label: '训练异常预警',
    description: '学生训练出现异常时的预警',
    default_priority: 'urgent',
    default_channels: ['in_app', 'email', 'sms'],
    icon: 'alert-triangle',
    color: 'red',
  },
  resource_audit: {
    type: 'resource_audit',
    label: '资源审核状态',
    description: '资源审核状态变更通知',
    default_priority: 'normal',
    default_channels: ['in_app', 'email'],
    icon: 'file-check',
    color: 'blue',
  },
  class_announcement: {
    type: 'class_announcement',
    label: '班级公告',
    description: '班级重要公告通知',
    default_priority: 'normal',
    default_channels: ['in_app', 'email'],
    icon: 'megaphone',
    color: 'blue',
  },
  teacher_notification: {
    type: 'teacher_notification',
    label: '教师通知',
    description: '发送给教师的通知',
    default_priority: 'normal',
    default_channels: ['in_app', 'email'],
    icon: 'user-check',
    color: 'green',
  },
  system_maintenance: {
    type: 'system_maintenance',
    label: '系统维护',
    description: '系统维护相关通知',
    default_priority: 'high',
    default_channels: ['in_app', 'email'],
    icon: 'settings',
    color: 'yellow',
  },
  grade_published: {
    type: 'grade_published',
    label: '成绩发布',
    description: '考试成绩发布通知',
    default_priority: 'normal',
    default_channels: ['in_app', 'email'],
    icon: 'award',
    color: 'green',
  },
  assignment_reminder: {
    type: 'assignment_reminder',
    label: '作业提醒',
    description: '作业截止时间提醒',
    default_priority: 'normal',
    default_channels: ['in_app', 'email'],
    icon: 'clock',
    color: 'orange',
  },
  course_update: {
    type: 'course_update',
    label: '课程更新',
    description: '课程内容或安排更新',
    default_priority: 'normal',
    default_channels: ['in_app'],
    icon: 'book',
    color: 'blue',
  },
  exam_schedule: {
    type: 'exam_schedule',
    label: '考试安排',
    description: '考试时间安排通知',
    default_priority: 'high',
    default_channels: ['in_app', 'email'],
    icon: 'calendar-event',
    color: 'red',
  },
  system_alert: {
    type: 'system_alert',
    label: '系统警告',
    description: '系统异常或警告信息',
    default_priority: 'urgent',
    default_channels: ['in_app', 'email'],
    icon: 'alert-circle',
    color: 'red',
  },
}

// =================== 工具函数类型 ===================

export interface NotificationFilter {
  type?: NotificationType
  priority?: 'urgent' | 'high' | 'normal' | 'low'
  isRead?: boolean
  dateRange?: {
    start: string
    end: string
  }
  channels?: NotificationChannel[]
}

export interface NotificationSort {
  field: 'created_at' | 'priority' | 'type'
  order: 'asc' | 'desc'
}

export interface NotificationPagination {
  page: number
  pageSize: number
  total: number
  totalPages: number
}
