import { apiClient } from './client'

// 教师推送通知接口
export interface TeacherNotification {
  id: string
  type: 'weakness_analysis' | 'student_progress' | 'class_summary' | 'urgent_attention'
  title: string
  content: string
  priority: 'high' | 'medium' | 'low'
  created_at: string
  read_at?: string
  teacher_id: number
  student_id?: number
  class_id?: number
  data: Record<string, unknown>
  action_required: boolean
  action_url?: string
  expires_at?: string
}

// 薄弱环节推送数据接口
export interface WeaknessPushData {
  student_id: number
  student_name: string
  class_id: number
  class_name: string
  analysis_date: string
  weak_points: Array<{
    knowledge_point_name: string
    weakness_score: number
    priority_level: 'high' | 'medium' | 'low'
    recommended_actions: string[]
    estimated_improvement_time: string
  }>
  overall_mastery: number
  improvement_suggestions: string[]
  requires_immediate_attention: boolean
}

// 班级汇总推送数据接口
export interface ClassSummaryPushData {
  class_id: number
  class_name: string
  analysis_period: string
  total_students: number
  students_needing_attention: number
  common_weak_points: Array<{
    knowledge_point: string
    affected_students: number
    average_weakness_score: number
  }>
  class_average_mastery: number
  improvement_trends: Array<{
    knowledge_point: string
    trend: 'improving' | 'stable' | 'declining'
    change_percentage: number
  }>
  recommended_class_actions: string[]
}

// 推送设置接口
export interface NotificationSettings {
  teacher_id: number
  weakness_threshold: number // 薄弱分数阈值
  push_frequency: 'immediate' | 'daily' | 'weekly'
  push_channels: Array<'in_app' | 'email' | 'sms'>
  class_summary_enabled: boolean
  individual_student_enabled: boolean
  urgent_only: boolean
  quiet_hours: {
    enabled: boolean
    start_time: string
    end_time: string
  }
}

export const teacherNotificationApi = {
  // 推送学生薄弱环节分析给教师
  pushWeaknessAnalysis: async (
    data: WeaknessPushData
  ): Promise<{
    notification_id: string
    pushed_to_teachers: number[]
    push_channels_used: string[]
    estimated_delivery_time: string
  }> => {
    const response = await apiClient.post('/api/v1/ai/notifications/teachers/weakness-push', data)
    return response.data
  },

  // 推送班级汇总分析给教师
  pushClassSummary: async (
    data: ClassSummaryPushData
  ): Promise<{
    notification_id: string
    pushed_to_teachers: number[]
    summary_type: 'daily' | 'weekly' | 'monthly'
  }> => {
    const response = await apiClient.post('/api/v1/ai/notifications/teachers/class-summary', data)
    return response.data
  },

  // 获取教师通知列表
  getTeacherNotifications: async (
    teacherId: number,
    params?: {
      type?: string
      priority?: string
      unread_only?: boolean
      page?: number
      limit?: number
      start_date?: string
      end_date?: string
    }
  ): Promise<{
    notifications: TeacherNotification[]
    total: number
    unread_count: number
    page: number
    limit: number
  }> => {
    const response = await apiClient.get(`/api/v1/ai/notifications/teachers/${teacherId}`, {
      params,
    })
    return response.data
  },

  // 标记通知为已读
  markAsRead: async (notificationId: string): Promise<void> => {
    await apiClient.patch(`/api/v1/ai/notifications/${notificationId}/read`)
  },

  // 批量标记通知为已读
  markMultipleAsRead: async (
    notificationIds: string[]
  ): Promise<{
    marked_count: number
    failed_ids: string[]
  }> => {
    const response = await apiClient.patch('/api/v1/ai/notifications/batch-read', {
      notification_ids: notificationIds,
    })
    return response.data
  },

  // 删除通知
  deleteNotification: async (notificationId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/ai/notifications/${notificationId}`)
  },

  // 获取教师推送设置
  getNotificationSettings: async (teacherId: number): Promise<NotificationSettings> => {
    const response = await apiClient.get(`/api/v1/ai/notifications/teachers/${teacherId}/settings`)
    return response.data
  },

  // 更新教师推送设置
  updateNotificationSettings: async (
    teacherId: number,
    settings: Partial<NotificationSettings>
  ): Promise<NotificationSettings> => {
    const response = await apiClient.patch(
      `/api/v1/ai/notifications/teachers/${teacherId}/settings`,
      settings
    )
    return response.data
  },

  // 测试推送功能
  testPush: async (
    teacherId: number,
    channel: 'in_app' | 'email' | 'sms'
  ): Promise<{
    success: boolean
    message: string
    delivery_time: string
  }> => {
    const response = await apiClient.post(`/api/v1/ai/notifications/teachers/${teacherId}/test`, {
      channel,
    })
    return response.data
  },

  // 获取推送统计
  getPushStats: async (
    teacherId: number,
    params?: {
      period?: 'week' | 'month' | 'semester'
    }
  ): Promise<{
    total_notifications: number
    read_rate: number
    response_rate: number
    channel_effectiveness: Record<string, number>
    notification_types: Record<string, number>
    peak_hours: Array<{
      hour: number
      count: number
    }>
  }> => {
    const response = await apiClient.get(`/api/v1/ai/notifications/teachers/${teacherId}/stats`, {
      params,
    })
    return response.data
  },

  // 创建自定义推送规则
  createPushRule: async (
    teacherId: number,
    rule: {
      name: string
      conditions: {
        weakness_score_threshold?: number
        knowledge_points?: string[]
        student_groups?: string[]
        time_conditions?: string[]
      }
      actions: {
        push_immediately: boolean
        push_channels: string[]
        custom_message?: string
        escalate_after?: number // 小时
      }
      enabled: boolean
    }
  ): Promise<{
    rule_id: string
    created_at: string
  }> => {
    const response = await apiClient.post(
      `/api/v1/ai/notifications/teachers/${teacherId}/rules`,
      rule
    )
    return response.data
  },

  // 获取推送规则列表
  getPushRules: async (
    teacherId: number
  ): Promise<
    Array<{
      id: string
      name: string
      conditions: Record<string, unknown>
      actions: Record<string, unknown>
      enabled: boolean
      created_at: string
      last_triggered?: string
      trigger_count: number
    }>
  > => {
    const response = await apiClient.get(`/api/v1/ai/notifications/teachers/${teacherId}/rules`)
    return response.data
  },

  // 更新推送规则
  updatePushRule: async (ruleId: string, updates: Record<string, unknown>): Promise<void> => {
    await apiClient.patch(`/api/v1/ai/notifications/rules/${ruleId}`, updates)
  },

  // 删除推送规则
  deletePushRule: async (ruleId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/ai/notifications/rules/${ruleId}`)
  },

  // 获取班级学生薄弱点汇总
  getClassWeaknessSummary: async (
    classId: number,
    params?: {
      time_range?: 'week' | 'month' | 'semester'
      min_weakness_score?: number
    }
  ): Promise<{
    class_info: {
      id: number
      name: string
      student_count: number
    }
    summary_date: string
    overall_stats: {
      average_mastery: number
      students_needing_attention: number
      total_weak_points: number
    }
    common_weak_points: Array<{
      knowledge_point: string
      affected_students: number
      average_weakness_score: number
      priority: 'high' | 'medium' | 'low'
    }>
    student_details: Array<{
      student_id: number
      student_name: string
      weak_points_count: number
      most_critical_point: string
      overall_mastery: number
    }>
    recommendations: string[]
  }> => {
    const response = await apiClient.get(
      `/api/v1/ai/notifications/classes/${classId}/weakness-summary`,
      { params }
    )
    return response.data
  },

  // 手动触发班级推送
  triggerClassPush: async (
    classId: number,
    pushType: 'weakness_summary' | 'progress_report' | 'urgent_attention'
  ): Promise<{
    notification_id: string
    teachers_notified: number
    push_time: string
  }> => {
    const response = await apiClient.post(
      `/api/v1/ai/notifications/classes/${classId}/trigger-push`,
      {
        push_type: pushType,
      }
    )
    return response.data
  },
}
