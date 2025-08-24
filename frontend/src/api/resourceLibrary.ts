/**
 * 教学资源库API客户端 - 需求17扩展实现
 * 支持教学素材收集与分类、优质教案模板共享、多媒体资源管理、基于教师历史使用推荐资源
 */

import { apiClient } from './client'

// =================== 类型定义 ===================

export interface TeachingMaterial {
  id: number
  title: string
  description: string
  category: string
  tags: string[]
  fileType: string
  fileSize: number
  downloadUrl: string
  previewUrl?: string
  uploadedBy: {
    id: number
    name: string
    avatar: string
  }
  downloadCount: number
  rating: number
  ratingCount: number
  createdAt: string
  updatedAt: string
  isBookmarked: boolean
}

export interface LessonTemplate {
  id: number
  title: string
  description: string
  subject: string
  grade: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  duration: number // 课时时长（分钟）
  objectives: string[]
  content: {
    introduction: string
    mainContent: string
    activities: string[]
    assessment: string
    homework: string
  }
  resources: string[]
  author: {
    id: number
    name: string
    avatar: string
    title: string
  }
  isShared: boolean
  shareLevel: 'private' | 'department' | 'school' | 'public'
  usageCount: number
  rating: number
  ratingCount: number
  tags: string[]
  createdAt: string
  updatedAt: string
  isBookmarked: boolean
  isFavorited: boolean
}

export interface MultimediaResource {
  id: number
  title: string
  description: string
  type: 'video' | 'audio' | 'image' | 'document'
  category: string
  tags: string[]
  fileUrl: string
  thumbnailUrl?: string
  duration?: number // 视频/音频时长（秒）
  fileSize: number
  resolution?: string // 视频分辨率
  format: string
  uploadedBy: {
    id: number
    name: string
    avatar: string
  }
  viewCount: number
  downloadCount: number
  rating: number
  ratingCount: number
  transcription?: string // 音频/视频转录文本
  subtitles?: string[] // 字幕文件URL
  createdAt: string
  updatedAt: string
  isBookmarked: boolean
}

export interface ResourceRecommendation {
  id: number
  resourceType: 'material' | 'template' | 'multimedia'
  resourceId: number
  resource: TeachingMaterial | LessonTemplate | MultimediaResource
  reason: string
  score: number
  category: string
  recommendedAt: string
}

export interface UsageHistory {
  id: number
  resourceType: 'material' | 'template' | 'multimedia'
  resourceId: number
  action: 'view' | 'download' | 'bookmark' | 'rate' | 'share'
  timestamp: string
  duration?: number // 查看时长（秒）
}

// =================== API接口 ===================

export const resourceLibraryApi = {
  // =================== 教学素材管理 ===================

  /**
   * 获取教学素材列表
   */
  async getTeachingMaterials(params: {
    page?: number
    pageSize?: number
    category?: string
    tags?: string[]
    fileType?: string
    search?: string
    sortBy?: 'latest' | 'popular' | 'rating'
  }): Promise<{
    materials: TeachingMaterial[]
    total: number
    page: number
    pageSize: number
    categories: string[]
    tags: string[]
  }> {
    const response = await apiClient.get('/api/v1/resource-library/teaching-materials', {
      params,
    })
    return response.data
  },

  /**
   * 上传教学素材
   */
  async uploadTeachingMaterial(formData: FormData): Promise<TeachingMaterial> {
    const response = await apiClient.post('/api/v1/resource-library/teaching-materials/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * 批量分类教学素材
   */
  async batchCategorizeTeachingMaterials(materialIds: number[], category: string, tags: string[]): Promise<{
    success: boolean
    updatedCount: number
  }> {
    const response = await apiClient.post('/api/v1/resource-library/teaching-materials/batch-categorize', {
      materialIds,
      category,
      tags,
    })
    return response.data
  },

  /**
   * 自动分类教学素材（AI辅助）
   */
  async autoCategorizeMaterial(materialId: number): Promise<{
    suggestedCategory: string
    suggestedTags: string[]
    confidence: number
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/teaching-materials/${materialId}/auto-categorize`)
    return response.data
  },

  // =================== 教案模板管理 ===================

  /**
   * 获取教案模板列表
   */
  async getLessonTemplates(params: {
    page?: number
    pageSize?: number
    subject?: string
    grade?: string
    difficulty?: string
    shareLevel?: string
    search?: string
    sortBy?: 'latest' | 'popular' | 'rating'
  }): Promise<{
    templates: LessonTemplate[]
    total: number
    page: number
    pageSize: number
    subjects: string[]
    grades: string[]
  }> {
    const response = await apiClient.get('/api/v1/resource-library/lesson-templates', {
      params,
    })
    return response.data
  },

  /**
   * 创建教案模板
   */
  async createLessonTemplate(templateData: Omit<LessonTemplate, 'id' | 'author' | 'usageCount' | 'rating' | 'ratingCount' | 'createdAt' | 'updatedAt' | 'isBookmarked' | 'isFavorited'>): Promise<LessonTemplate> {
    const response = await apiClient.post('/api/v1/resource-library/lesson-templates', templateData)
    return response.data
  },

  /**
   * 共享教案模板
   */
  async shareLessonTemplate(templateId: number, shareLevel: 'department' | 'school' | 'public', message?: string): Promise<{
    success: boolean
    shareUrl: string
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/lesson-templates/${templateId}/share`, {
      shareLevel,
      message,
    })
    return response.data
  },

  /**
   * 复制教案模板
   */
  async copyLessonTemplate(templateId: number, customizations?: Partial<LessonTemplate>): Promise<LessonTemplate> {
    const response = await apiClient.post(`/api/v1/resource-library/lesson-templates/${templateId}/copy`, customizations)
    return response.data
  },

  /**
   * 协作编辑教案模板
   */
  async startCollaborativeEditing(templateId: number): Promise<{
    sessionId: string
    editUrl: string
    collaborators: Array<{
      id: number
      name: string
      avatar: string
      isOnline: boolean
    }>
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/lesson-templates/${templateId}/collaborate`)
    return response.data
  },

  // =================== 多媒体资源管理 ===================

  /**
   * 获取多媒体资源列表
   */
  async getMultimediaResources(params: {
    page?: number
    pageSize?: number
    type?: 'video' | 'audio' | 'image' | 'document'
    category?: string
    tags?: string[]
    search?: string
    sortBy?: 'latest' | 'popular' | 'rating'
  }): Promise<{
    resources: MultimediaResource[]
    total: number
    page: number
    pageSize: number
    categories: string[]
    tags: string[]
  }> {
    const response = await apiClient.get('/api/v1/resource-library/multimedia-resources', {
      params,
    })
    return response.data
  },

  /**
   * 上传多媒体资源
   */
  async uploadMultimediaResource(formData: FormData, onProgress?: (progress: number) => void): Promise<MultimediaResource> {
    const response = await apiClient.post('/api/v1/resource-library/multimedia-resources/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  },

  /**
   * 生成视频缩略图
   */
  async generateVideoThumbnail(resourceId: number, timestamp: number): Promise<{
    thumbnailUrl: string
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/multimedia-resources/${resourceId}/thumbnail`, {
      timestamp,
    })
    return response.data
  },

  /**
   * 转录音频/视频
   */
  async transcribeMedia(resourceId: number): Promise<{
    transcription: string
    confidence: number
    language: string
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/multimedia-resources/${resourceId}/transcribe`)
    return response.data
  },

  // =================== 智能推荐系统 ===================

  /**
   * 获取个性化资源推荐
   */
  async getPersonalizedRecommendations(params: {
    resourceType?: 'material' | 'template' | 'multimedia'
    category?: string
    limit?: number
  }): Promise<{
    recommendations: ResourceRecommendation[]
    totalScore: number
    categories: Array<{
      category: string
      score: number
      count: number
    }>
  }> {
    const response = await apiClient.get('/api/v1/resource-library/recommendations', {
      params,
    })
    return response.data
  },

  /**
   * 记录资源使用行为
   */
  async recordUsage(resourceType: 'material' | 'template' | 'multimedia', resourceId: number, action: 'view' | 'download' | 'bookmark' | 'rate' | 'share', duration?: number): Promise<{
    success: boolean
  }> {
    const response = await apiClient.post('/api/v1/resource-library/usage', {
      resourceType,
      resourceId,
      action,
      duration,
    })
    return response.data
  },

  /**
   * 获取使用历史
   */
  async getUsageHistory(params: {
    page?: number
    pageSize?: number
    resourceType?: string
    action?: string
    dateRange?: {
      start: string
      end: string
    }
  }): Promise<{
    history: UsageHistory[]
    total: number
    page: number
    pageSize: number
    stats: {
      totalViews: number
      totalDownloads: number
      totalBookmarks: number
      averageViewDuration: number
    }
  }> {
    const response = await apiClient.get('/api/v1/resource-library/usage/history', {
      params,
    })
    return response.data
  },

  /**
   * 刷新推荐算法
   */
  async refreshRecommendations(): Promise<{
    success: boolean
    updatedAt: string
    newRecommendationsCount: number
  }> {
    const response = await apiClient.post('/api/v1/resource-library/recommendations/refresh')
    return response.data
  },

  // =================== 通用功能 ===================

  /**
   * 收藏资源
   */
  async bookmarkResource(resourceType: 'material' | 'template' | 'multimedia', resourceId: number): Promise<{
    success: boolean
    isBookmarked: boolean
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/${resourceType}s/${resourceId}/bookmark`)
    return response.data
  },

  /**
   * 评价资源
   */
  async rateResource(resourceType: 'material' | 'template' | 'multimedia', resourceId: number, rating: number, comment?: string): Promise<{
    success: boolean
    averageRating: number
    ratingCount: number
  }> {
    const response = await apiClient.post(`/api/v1/resource-library/${resourceType}s/${resourceId}/rate`, {
      rating,
      comment,
    })
    return response.data
  },

  /**
   * 获取资源统计
   */
  async getResourceStats(): Promise<{
    totalMaterials: number
    totalTemplates: number
    totalMultimedia: number
    totalDownloads: number
    totalViews: number
    popularCategories: Array<{
      category: string
      count: number
      percentage: number
    }>
    recentActivity: Array<{
      action: string
      resourceTitle: string
      timestamp: string
    }>
  }> {
    const response = await apiClient.get('/api/v1/resource-library/stats')
    return response.data
  },
}
