/**
 * 通知系统API客户端 - 需求16通知中枢前端接口
 */

import { apiClient } from './client'
import type {
  NotificationCreate,
  NotificationResponse,
  NotificationListRequest,
  NotificationListResponse,
  NotificationBatchCreate,
  NotificationUpdate,
  NotificationPreferenceResponse,
  NotificationPreferenceUpdate,
  NotificationStats,
  TeachingPlanChangeNotification,
  TrainingAnomalyAlert,
  ResourceAuditNotification,
} from '../types/notification'

export const notificationApi = {
  // =================== 基础通知管理 ===================

  /**
   * 发送通知
   */
  async sendNotification(
    notificationData: NotificationCreate,
    userIds: number[],
    channels: string[] = ['in_app']
  ): Promise<NotificationResponse[]> {
    const response = await apiClient.post('/notifications/send', notificationData, {
      params: {
        user_ids: userIds.join(','),
        channels: channels.join(','),
      },
    })
    return response.data
  },

  /**
   * 批量发送通知
   */
  async sendBatchNotification(
    batchData: NotificationBatchCreate
  ): Promise<{ success: boolean; message: string; sent_count: number }> {
    const response = await apiClient.post('/notifications/batch', batchData)
    return response.data
  },

  /**
   * 获取通知列表
   */
  async getNotificationList(
    params: Partial<NotificationListRequest> = {}
  ): Promise<NotificationListResponse> {
    const response = await apiClient.get('/notifications/list', { params })
    return response.data
  },

  /**
   * 更新通知状态
   */
  async updateNotification(
    notificationId: number,
    updateData: NotificationUpdate
  ): Promise<NotificationResponse> {
    const response = await apiClient.put(`/notifications/${notificationId}`, updateData)
    return response.data
  },

  /**
   * 批量删除通知
   */
  async batchDeleteNotifications(
    notificationIds: number[]
  ): Promise<{ success: boolean; message: string; deleted_count: number }> {
    const response = await apiClient.delete('/notifications/batch', {
      data: { notification_ids: notificationIds },
    })
    return response.data
  },

  // =================== 特定通知类型 - 需求16验收标准1 ===================

  /**
   * 发送教学计划变更通知
   */
  async sendTeachingPlanChangeNotification(
    notificationData: TeachingPlanChangeNotification
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(
      '/notifications/teaching-plan-change',
      notificationData
    )
    return response.data
  },

  /**
   * 发送学生训练异常预警
   */
  async sendTrainingAnomalyAlert(
    alertData: TrainingAnomalyAlert
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/notifications/training-anomaly-alert', alertData)
    return response.data
  },

  /**
   * 发送资源审核状态提醒
   */
  async sendResourceAuditNotification(
    auditData: ResourceAuditNotification
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/notifications/resource-audit', auditData)
    return response.data
  },

  // =================== 通知偏好管理 ===================

  /**
   * 获取通知偏好设置
   */
  async getNotificationPreferences(): Promise<NotificationPreferenceResponse> {
    const response = await apiClient.get('/notifications/preferences')
    return response.data
  },

  /**
   * 更新通知偏好设置
   */
  async updateNotificationPreferences(
    preferenceData: NotificationPreferenceUpdate
  ): Promise<NotificationPreferenceResponse> {
    const response = await apiClient.put('/notifications/preferences', preferenceData)
    return response.data
  },

  // =================== 通知统计 ===================

  /**
   * 获取通知统计
   */
  async getNotificationStats(): Promise<NotificationStats> {
    const response = await apiClient.get('/notifications/stats')
    return response.data
  },

  /**
   * 获取WebSocket连接统计
   */
  async getWebSocketStats(): Promise<{
    success: boolean
    stats: {
      total_connections: number
      active_users: number
      user_connections: Record<string, number>
    }
  }> {
    const response = await apiClient.get('/notifications/websocket/stats')
    return response.data
  },

  // =================== 便捷方法 ===================

  /**
   * 标记通知为已读
   */
  async markAsRead(notificationId: number): Promise<NotificationResponse> {
    return this.updateNotification(notificationId, {
      is_read: true,
      read_at: new Date().toISOString(),
    })
  },

  /**
   * 批量标记为已读
   */
  async markAllAsRead(notificationIds: number[]): Promise<NotificationResponse[]> {
    const promises = notificationIds.map((id) => this.markAsRead(id))
    return Promise.all(promises)
  },

  /**
   * 获取未读通知数量
   */
  async getUnreadCount(): Promise<number> {
    const stats = await this.getNotificationStats()
    return stats.unread_count
  },

  /**
   * 获取最新通知
   */
  async getLatestNotifications(limit: number = 10): Promise<NotificationResponse[]> {
    const response = await this.getNotificationList({
      page: 1,
      page_size: limit,
    })
    return response.notifications
  },

  /**
   * 获取未读通知
   */
  async getUnreadNotifications(limit: number = 20): Promise<NotificationResponse[]> {
    const response = await this.getNotificationList({
      is_read: false,
      page: 1,
      page_size: limit,
    })
    return response.notifications
  },

  /**
   * 按类型获取通知
   */
  async getNotificationsByType(
    notificationType: string,
    limit: number = 20
  ): Promise<NotificationResponse[]> {
    const response = await this.getNotificationList({
      notification_type: notificationType,
      page: 1,
      page_size: limit,
    })
    return response.notifications
  },

  /**
   * 按优先级获取通知
   */
  async getNotificationsByPriority(
    priority: string,
    limit: number = 20
  ): Promise<NotificationResponse[]> {
    const response = await this.getNotificationList({
      priority,
      page: 1,
      page_size: limit,
    })
    return response.notifications
  },

  // =================== 教学相关便捷方法 ===================

  /**
   * 发送班级通知
   */
  async sendClassNotification(
    classIds: number[],
    title: string,
    content: string,
    priority: 'urgent' | 'high' | 'normal' | 'low' = 'normal',
    channels: string[] = ['in_app', 'email']
  ): Promise<{ success: boolean; message: string; sent_count: number }> {
    const batchData: NotificationBatchCreate = {
      notification_data: {
        title,
        content,
        notification_type: 'class_announcement',
        priority,
      },
      target_type: 'class',
      target_ids: classIds,
      channels,
    }

    return this.sendBatchNotification(batchData)
  },

  /**
   * 发送教师通知
   */
  async sendTeacherNotification(
    teacherIds: number[],
    title: string,
    content: string,
    priority: 'urgent' | 'high' | 'normal' | 'low' = 'normal',
    channels: string[] = ['in_app', 'email']
  ): Promise<NotificationResponse[]> {
    const notificationData: NotificationCreate = {
      title,
      content,
      notification_type: 'teacher_notification',
      priority,
    }

    return this.sendNotification(notificationData, teacherIds, channels)
  },

  /**
   * 发送系统维护通知
   */
  async sendMaintenanceNotification(
    title: string,
    content: string,
    scheduledTime: string
  ): Promise<{ success: boolean; message: string; sent_count: number }> {
    const batchData: NotificationBatchCreate = {
      notification_data: {
        title,
        content,
        notification_type: 'system_maintenance',
        priority: 'high',
        metadata: {
          scheduled_time: scheduledTime,
        },
      },
      target_type: 'role',
      target_ids: [1, 2, 3], // 所有角色
      channels: ['in_app', 'email'],
    }

    return this.sendBatchNotification(batchData)
  },

  /**
   * 发送成绩发布通知
   */
  async sendGradePublishedNotification(
    studentIds: number[],
    examName: string,
    courseId: number
  ): Promise<NotificationResponse[]> {
    const notificationData: NotificationCreate = {
      title: '成绩发布通知',
      content: `您的${examName}成绩已发布，请及时查看。`,
      notification_type: 'grade_published',
      priority: 'normal',
      metadata: {
        exam_name: examName,
        course_id: courseId,
      },
    }

    return this.sendNotification(notificationData, studentIds, ['in_app', 'email'])
  },

  /**
   * 发送作业提醒
   */
  async sendAssignmentReminder(
    studentIds: number[],
    assignmentName: string,
    dueDate: string
  ): Promise<NotificationResponse[]> {
    const notificationData: NotificationCreate = {
      title: '作业提醒',
      content: `您有作业"${assignmentName}"即将到期，截止时间：${dueDate}`,
      notification_type: 'assignment_reminder',
      priority: 'normal',
      metadata: {
        assignment_name: assignmentName,
        due_date: dueDate,
      },
    }

    return this.sendNotification(notificationData, studentIds, ['in_app', 'email'])
  },
}
