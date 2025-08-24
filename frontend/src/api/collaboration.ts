/**
 * 教研协作API客户端 - 需求16教研协作功能
 */

import { apiClient } from './client'
import type {
  LessonPlan,
  LessonPlanComment,
  LessonPlanShare,
  DiscussionTopic,
  DiscussionReply,
  CollaborationSession,
} from '../types/collaboration'

export const collaborationApi = {
  // =================== 教案共享功能 ===================

  /**
   * 获取共享教案列表
   */
  async getSharedLessonPlans(params: {
    subject?: string
    grade?: string
    difficulty?: string
    search?: string
    page: number
    pageSize: number
  }): Promise<{ plans: LessonPlan[]; total: number }> {
    const response = await apiClient.get('/collaboration/lesson-plans/shared', { params })
    return response.data
  },

  /**
   * 获取我的教案列表
   */
  async getMyLessonPlans(): Promise<{ plans: LessonPlan[]; total: number }> {
    const response = await apiClient.get('/collaboration/lesson-plans/my')
    return response.data
  },

  /**
   * 分享教案
   */
  async shareLessonPlan(shareData: {
    planId: number
    shareLevel: 'public' | 'school' | 'department'
    description?: string
  }): Promise<LessonPlanShare> {
    const response = await apiClient.post('/collaboration/lesson-plans/share', shareData)
    return response.data
  },

  /**
   * 获取教案评论
   */
  async getLessonPlanComments(planId: number): Promise<LessonPlanComment[]> {
    const response = await apiClient.get(`/collaboration/lesson-plans/${planId}/comments`)
    return response.data
  },

  /**
   * 添加教案评论
   */
  async addLessonPlanComment(commentData: {
    planId: number
    content: string
    rating?: number
  }): Promise<LessonPlanComment> {
    const response = await apiClient.post(
      `/collaboration/lesson-plans/${commentData.planId}/comments`,
      commentData
    )
    return response.data
  },

  /**
   * 点赞教案
   */
  async likeLessonPlan(planId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/lesson-plans/${planId}/like`)
    return response.data
  },

  /**
   * 收藏教案
   */
  async favoriteLessonPlan(planId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/lesson-plans/${planId}/favorite`)
    return response.data
  },

  /**
   * 下载教案
   */
  async downloadLessonPlan(planId: number): Promise<void> {
    const response = await apiClient.get(`/collaboration/lesson-plans/${planId}/download`, {
      responseType: 'blob',
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `lesson-plan-${planId}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  // =================== 教学难点讨论功能 ===================

  /**
   * 获取讨论话题列表
   */
  async getDiscussionTopics(params: {
    subject?: string
    difficulty?: string
    status?: string
    search?: string
    page: number
    pageSize: number
  }): Promise<{ topics: DiscussionTopic[]; total: number }> {
    const response = await apiClient.get('/collaboration/discussions/topics', { params })
    return response.data
  },

  /**
   * 创建讨论话题
   */
  async createDiscussionTopic(topicData: {
    title: string
    content: string
    subject: string
    difficulty: string
    tags: string[]
  }): Promise<DiscussionTopic> {
    const response = await apiClient.post('/collaboration/discussions/topics', topicData)
    return response.data
  },

  /**
   * 获取话题回复
   */
  async getDiscussionReplies(topicId: number): Promise<DiscussionReply[]> {
    const response = await apiClient.get(`/collaboration/discussions/topics/${topicId}/replies`)
    return response.data
  },

  /**
   * 添加讨论回复
   */
  async addDiscussionReply(replyData: {
    topicId: number
    content: string
    replyToId?: number
  }): Promise<DiscussionReply> {
    const response = await apiClient.post(
      `/collaboration/discussions/topics/${replyData.topicId}/replies`,
      replyData
    )
    return response.data
  },

  /**
   * 点赞回复
   */
  async likeDiscussionReply(replyId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/discussions/replies/${replyId}/like`)
    return response.data
  },

  /**
   * 收藏讨论话题
   */
  async bookmarkDiscussionTopic(topicId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/discussions/topics/${topicId}/bookmark`)
    return response.data
  },

  /**
   * 标记回复为解决方案
   */
  async markReplyAsSolution(replyId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/discussions/replies/${replyId}/solution`)
    return response.data
  },

  // =================== 优秀案例分享功能 ===================

  /**
   * 获取优秀案例列表
   */
  async getExcellentCases(params: {
    category?: string
    subject?: string
    search?: string
    page: number
    pageSize: number
  }): Promise<{ cases: any[]; total: number }> {
    const response = await apiClient.get('/collaboration/excellent-cases', { params })
    return response.data
  },

  /**
   * 提交优秀案例
   */
  async submitExcellentCase(caseData: {
    title: string
    description: string
    category: string
    subject: string
    content: string
    attachments?: File[]
  }): Promise<any> {
    const formData = new FormData()
    formData.append('title', caseData.title)
    formData.append('description', caseData.description)
    formData.append('category', caseData.category)
    formData.append('subject', caseData.subject)
    formData.append('content', caseData.content)
    
    if (caseData.attachments) {
      caseData.attachments.forEach((file, index) => {
        formData.append(`attachments[${index}]`, file)
      })
    }

    const response = await apiClient.post('/collaboration/excellent-cases', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * 点赞案例
   */
  async likeExcellentCase(caseId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/excellent-cases/${caseId}/like`)
    return response.data
  },

  /**
   * 收藏案例
   */
  async favoriteExcellentCase(caseId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/excellent-cases/${caseId}/favorite`)
    return response.data
  },

  // =================== 协同编辑功能 ===================

  /**
   * 创建协作会话
   */
  async createCollaborationSession(sessionData: {
    title: string
    description: string
    type: 'lesson_plan' | 'syllabus' | 'document'
    participants: number[]
  }): Promise<CollaborationSession> {
    const response = await apiClient.post('/collaboration/sessions', sessionData)
    return response.data
  },

  /**
   * 获取协作会话列表
   */
  async getCollaborationSessions(): Promise<CollaborationSession[]> {
    const response = await apiClient.get('/collaboration/sessions')
    return response.data
  },

  /**
   * 加入协作会话
   */
  async joinCollaborationSession(sessionId: number): Promise<{ success: boolean; token: string }> {
    const response = await apiClient.post(`/collaboration/sessions/${sessionId}/join`)
    return response.data
  },

  /**
   * 离开协作会话
   */
  async leaveCollaborationSession(sessionId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/sessions/${sessionId}/leave`)
    return response.data
  },

  /**
   * 获取协作会话详情
   */
  async getCollaborationSessionDetail(sessionId: number): Promise<CollaborationSession> {
    const response = await apiClient.get(`/collaboration/sessions/${sessionId}`)
    return response.data
  },

  /**
   * 保存协作内容
   */
  async saveCollaborationContent(sessionId: number, content: any): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/collaboration/sessions/${sessionId}/save`, { content })
    return response.data
  },

  // =================== 权限管理功能 ===================

  /**
   * 检查协作权限
   */
  async checkCollaborationPermission(
    resourceType: string,
    resourceId: number,
    action: string
  ): Promise<{ hasPermission: boolean; reason?: string }> {
    const response = await apiClient.get('/collaboration/permissions/check', {
      params: {
        resource_type: resourceType,
        resource_id: resourceId,
        action,
      },
    })
    return response.data
  },

  /**
   * 获取用户协作权限
   */
  async getUserCollaborationPermissions(): Promise<{
    canCreateLessonPlan: boolean
    canShareLessonPlan: boolean
    canEditSyllabus: boolean
    canViewClassSchedule: boolean
    canModifyClassSchedule: boolean
  }> {
    const response = await apiClient.get('/collaboration/permissions/user')
    return response.data
  },

  /**
   * 申请协作权限
   */
  async requestCollaborationPermission(requestData: {
    resourceType: string
    resourceId: number
    permission: string
    reason: string
  }): Promise<{ success: boolean; requestId: number }> {
    const response = await apiClient.post('/collaboration/permissions/request', requestData)
    return response.data
  },

  // =================== 统计和分析功能 ===================

  /**
   * 获取协作统计数据
   */
  async getCollaborationStats(): Promise<{
    totalSharedPlans: number
    totalDiscussions: number
    totalCases: number
    myContributions: number
    recentActivity: any[]
  }> {
    const response = await apiClient.get('/collaboration/stats')
    return response.data
  },

  /**
   * 获取用户协作活动
   */
  async getUserCollaborationActivity(userId?: number): Promise<{
    activities: any[]
    summary: {
      plansShared: number
      discussionsStarted: number
      repliesPosted: number
      casesSubmitted: number
    }
  }> {
    const response = await apiClient.get('/collaboration/activity', {
      params: userId ? { user_id: userId } : {},
    })
    return response.data
  },

  // =================== 便捷方法 ===================

  /**
   * 搜索协作内容
   */
  async searchCollaborationContent(query: string, type?: string): Promise<{
    lessonPlans: LessonPlan[]
    discussions: DiscussionTopic[]
    cases: any[]
  }> {
    const response = await apiClient.get('/collaboration/search', {
      params: { q: query, type },
    })
    return response.data
  },

  /**
   * 获取推荐内容
   */
  async getRecommendedContent(): Promise<{
    recommendedPlans: LessonPlan[]
    hotDiscussions: DiscussionTopic[]
    featuredCases: any[]
  }> {
    const response = await apiClient.get('/collaboration/recommendations')
    return response.data
  },

  /**
   * 获取协作通知
   */
  async getCollaborationNotifications(): Promise<{
    notifications: any[]
    unreadCount: number
  }> {
    const response = await apiClient.get('/collaboration/notifications')
    return response.data
  },
}
