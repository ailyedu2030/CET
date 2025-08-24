/**
 * 专业发展支持API客户端 - 需求17实现
 * 提供教学能力培训资源、专业认证辅导材料、教师社区交流平台和教育教学研究最新动态推送
 */

import { apiClient } from './client'

// =================== 类型定义 ===================

export interface TrainingResource {
  id: number
  title: string
  category: string
  description: string
  duration: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  rating: number
  enrolledCount: number
  isEnrolled: boolean
  progress?: number
  instructor: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface CertificationMaterial {
  id: number
  title: string
  type: 'guide' | 'practice' | 'mock_exam' | 'video'
  category: string
  description: string
  downloadUrl?: string
  viewUrl?: string
  fileSize?: number
  downloadCount: number
  rating: number
  createdAt: string
}

export interface CommunityPost {
  id: number
  author: {
    id: number
    name: string
    avatar: string
    title: string
  }
  title: string
  content: string
  category: string
  tags: string[]
  likes: number
  replies: number
  views: number
  createdAt: string
  updatedAt: string
  isLiked: boolean
  isBookmarked: boolean
}

export interface CommunityReply {
  id: number
  postId: number
  author: {
    id: number
    name: string
    avatar: string
  }
  content: string
  likes: number
  createdAt: string
  isLiked: boolean
}

export interface ResearchUpdate {
  id: number
  title: string
  source: string
  summary: string
  fullContent?: string
  publishedAt: string
  category: string
  importance: 'high' | 'medium' | 'low'
  tags: string[]
  readCount: number
  isBookmarked: boolean
  downloadUrl?: string
}

export interface NotificationSettings {
  trainingUpdates: boolean
  communityReplies: boolean
  researchUpdates: boolean
  certificationReminders: boolean
  emailNotifications: boolean
  pushNotifications: boolean
}

// =================== API接口 ===================

export const professionalDevelopmentApi = {
  // =================== 培训资源管理 ===================

  /**
   * 获取培训资源列表
   */
  async getTrainingResources(params: {
    page?: number
    pageSize?: number
    category?: string
    difficulty?: string
    search?: string
  }): Promise<{
    resources: TrainingResource[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get('/api/v1/professional-development/training/resources', {
      params,
    })
    return response.data
  },

  /**
   * 报名培训课程
   */
  async enrollTraining(trainingId: number): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`/api/v1/professional-development/training/${trainingId}/enroll`)
    return response.data
  },

  /**
   * 获取学习进度
   */
  async getTrainingProgress(trainingId: number): Promise<{
    progress: number
    completedLessons: number
    totalLessons: number
    lastAccessedAt: string
  }> {
    const response = await apiClient.get(`/api/v1/professional-development/training/${trainingId}/progress`)
    return response.data
  },

  /**
   * 更新学习进度
   */
  async updateTrainingProgress(
    trainingId: number,
    lessonId: number,
    progress: number
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/api/v1/professional-development/training/${trainingId}/progress`, {
      lessonId,
      progress,
    })
    return response.data
  },

  // =================== 认证辅导材料 ===================

  /**
   * 获取认证辅导材料列表
   */
  async getCertificationMaterials(params: {
    page?: number
    pageSize?: number
    category?: string
    type?: string
    search?: string
  }): Promise<{
    materials: CertificationMaterial[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get('/api/v1/professional-development/certification/materials', {
      params,
    })
    return response.data
  },

  /**
   * 下载认证材料
   */
  async downloadCertificationMaterial(materialId: number): Promise<{ downloadUrl: string }> {
    const response = await apiClient.post(`/api/v1/professional-development/certification/materials/${materialId}/download`)
    return response.data
  },

  /**
   * 评价认证材料
   */
  async rateCertificationMaterial(
    materialId: number,
    rating: number,
    comment?: string
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/api/v1/professional-development/certification/materials/${materialId}/rate`, {
      rating,
      comment,
    })
    return response.data
  },

  // =================== 社区交流平台 ===================

  /**
   * 获取社区帖子列表
   */
  async getCommunityPosts(params: {
    page?: number
    pageSize?: number
    category?: string
    sortBy?: 'latest' | 'popular' | 'replies'
    search?: string
  }): Promise<{
    posts: CommunityPost[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get('/api/v1/professional-development/community/posts', {
      params,
    })
    return response.data
  },

  /**
   * 创建社区帖子
   */
  async createCommunityPost(postData: {
    title: string
    content: string
    category: string
    tags: string[]
  }): Promise<CommunityPost> {
    const response = await apiClient.post('/api/v1/professional-development/community/posts', postData)
    return response.data
  },

  /**
   * 点赞帖子
   */
  async likeCommunityPost(postId: number): Promise<{ success: boolean; isLiked: boolean }> {
    const response = await apiClient.post(`/api/v1/professional-development/community/posts/${postId}/like`)
    return response.data
  },

  /**
   * 获取帖子回复
   */
  async getCommunityReplies(postId: number, params: {
    page?: number
    pageSize?: number
  }): Promise<{
    replies: CommunityReply[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get(`/api/v1/professional-development/community/posts/${postId}/replies`, {
      params,
    })
    return response.data
  },

  /**
   * 回复帖子
   */
  async replyCommunityPost(postId: number, content: string): Promise<CommunityReply> {
    const response = await apiClient.post(`/api/v1/professional-development/community/posts/${postId}/replies`, {
      content,
    })
    return response.data
  },

  // =================== 研究动态推送 ===================

  /**
   * 获取研究动态列表
   */
  async getResearchUpdates(params: {
    page?: number
    pageSize?: number
    category?: string
    importance?: string
    dateRange?: {
      start: string
      end: string
    }
  }): Promise<{
    updates: ResearchUpdate[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get('/api/v1/professional-development/research/updates', {
      params,
    })
    return response.data
  },

  /**
   * 标记研究动态为已读
   */
  async markResearchUpdateAsRead(updateId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/api/v1/professional-development/research/updates/${updateId}/read`)
    return response.data
  },

  /**
   * 收藏研究动态
   */
  async bookmarkResearchUpdate(updateId: number): Promise<{ success: boolean; isBookmarked: boolean }> {
    const response = await apiClient.post(`/api/v1/professional-development/research/updates/${updateId}/bookmark`)
    return response.data
  },

  // =================== 通知设置 ===================

  /**
   * 获取通知设置
   */
  async getNotificationSettings(): Promise<NotificationSettings> {
    const response = await apiClient.get('/api/v1/professional-development/notifications/settings')
    return response.data
  },

  /**
   * 更新通知设置
   */
  async updateNotificationSettings(settings: Partial<NotificationSettings>): Promise<{ success: boolean }> {
    const response = await apiClient.put('/api/v1/professional-development/notifications/settings', settings)
    return response.data
  },

  // =================== 统计和推荐 ===================

  /**
   * 获取个人学习统计
   */
  async getLearningStats(): Promise<{
    totalTrainings: number
    completedTrainings: number
    totalStudyHours: number
    certificationsEarned: number
    communityContributions: number
    researchArticlesRead: number
  }> {
    const response = await apiClient.get('/api/v1/professional-development/stats/learning')
    return response.data
  },

  /**
   * 获取个性化推荐
   */
  async getPersonalizedRecommendations(): Promise<{
    recommendedTrainings: TrainingResource[]
    recommendedMaterials: CertificationMaterial[]
    recommendedPosts: CommunityPost[]
    recommendedResearch: ResearchUpdate[]
  }> {
    const response = await apiClient.get('/api/v1/professional-development/recommendations')
    return response.data
  },
}
