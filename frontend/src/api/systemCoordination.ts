/**
 * 需求16：系统协同功能 API
 *
 * 实现通知中枢、教研协作、权限控制等3个验收标准
 * 只使用后端真正存在的API端点
 */

import { apiClient } from './client'

// ==================== 类型定义 ====================

// 通知中枢相关类型
export interface NotificationRequest {
  type: 'teaching_plan_change' | 'training_anomaly' | 'resource_audit'
  title: string
  content: string
  target_users?: number[]
  target_classes?: number[]
  channels?: ('in_app' | 'email' | 'sms')[]
}

export interface NotificationResult {
  id: string
  type: string
  title: string
  content: string
  status: 'sent' | 'pending' | 'failed'
  sent_count: number
  created_at: string
}

// 教研协作相关类型
export interface CollaborationRequest {
  session_type: 'lesson_plan' | 'syllabus' | 'discussion'
  resource_id?: number
  participants?: number[]
  permissions?: string[]
}

export interface CollaborationResult {
  session_id: string
  session_type: string
  participants: Array<{
    id: number
    name: string
    role: string
    joined_at: string
  }>
  permissions: string[]
  status: 'active' | 'ended'
  created_at: string
}

// 权限控制相关类型
export interface PermissionRequest {
  user_id: number
  resource_type: string
  resource_id?: number
  action: string
}

export interface PermissionResult {
  has_permission: boolean
  permission_details: {
    can_edit_syllabus: boolean
    can_edit_lesson_plan: boolean
    can_view_classroom_schedule: boolean
    can_modify_classroom_schedule: boolean
  }
  reason?: string
}

// ==================== API 实现 ====================

// 1. 通知中枢 API
export const notificationApi = {
  // 发送通知
  sendNotification: async (request: NotificationRequest): Promise<NotificationResult> => {
    const response = await apiClient.post('/api/v1/notifications/send', {
      notification_data: {
        type: request.type,
        title: request.title,
        content: request.content,
      },
      user_ids: request.target_users || [],
      channels: request.channels || ['in_app'],
    })
    return response.data
  },

  // 批量发送通知
  sendBatchNotification: async (request: NotificationRequest): Promise<any> => {
    const response = await apiClient.post('/api/v1/notifications/batch', {
      notifications: [
        {
          type: request.type,
          title: request.title,
          content: request.content,
          target_users: request.target_users,
          target_classes: request.target_classes,
        },
      ],
      channels: request.channels || ['in_app'],
    })
    return response.data
  },

  // 发送教学计划变更通知
  sendTeachingPlanChangeNotification: async (planData: any): Promise<any> => {
    const response = await apiClient.post('/api/v1/notifications/teaching-plan-change', planData)
    return response.data
  },

  // 发送训练异常预警
  sendTrainingAnomalyAlert: async (alertData: any): Promise<any> => {
    const response = await apiClient.post('/api/v1/notifications/training-anomaly', alertData)
    return response.data
  },

  // 发送资源审核状态提醒
  sendResourceAuditNotification: async (auditData: any): Promise<any> => {
    const response = await apiClient.post('/api/v1/notifications/resource-audit', auditData)
    return response.data
  },
}

// 2. 教研协作 API
export const collaborationApi = {
  // 创建协作会话
  createSession: async (request: CollaborationRequest): Promise<CollaborationResult> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/collaboration/create-session',
      {
        session_type: request.session_type,
        resource_id: request.resource_id,
        participants: request.participants || [],
        requested_permissions: request.permissions || [],
      }
    )
    return response.data
  },

  // 加入协作会话
  joinSession: async (sessionId: string, permissions: string[]): Promise<any> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/collaboration/join-session',
      {
        session_id: sessionId,
        requested_permissions: permissions,
      }
    )
    return response.data
  },
}

// 3. 权限控制 API
export const permissionApi = {
  // 检查教师教案权限
  checkTeacherLessonPlanPermission: async (lessonPlanId: number, action: string): Promise<any> => {
    const response = await apiClient.get(
      '/api/v1/core/architecture/permission/check/teacher/lesson-plan',
      {
        params: {
          lesson_plan_id: lessonPlanId,
          action: action,
        },
      }
    )
    return response.data
  },

  // 获取当前用户权限
  getCurrentUserPermissions: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/users/permissions/users/me/permissions')
    return response.data
  },

  // 检查资源权限
  checkResourcePermission: async (resourceType: string, resourceId: number): Promise<any> => {
    const response = await apiClient.get(
      `/api/v1/resources/permissions/${resourceType}/${resourceId}`
    )
    return response.data
  },
}

// 4. 系统健康检查 API
export const systemHealthApi = {
  // 获取系统协同健康状态
  getCoordinationHealth: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/ai/enhanced-teaching/system/health')
    return response.data
  },

  // 获取系统能力
  getSystemCapabilities: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/ai/enhanced-teaching/system/capabilities')
    return response.data
  },

  // AI服务状态
  getAIStatus: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/ai/ai/status')
    return response.data
  },
}

// 5. 学习分析 API（用于教师端驱动）
export const learningAnalysisApi = {
  // 综合学情分析
  getComprehensiveAnalysis: async (classId: number, courseId: number): Promise<any> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/learning-analysis/comprehensive',
      {
        class_id: classId,
        course_id: courseId,
      }
    )
    return response.data
  },
}
