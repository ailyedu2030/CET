/**
 * 热点资源池API客户端 - 需求12实现
 */
import { apiClient } from './client'

// 热点资源类型定义
export interface HotspotResource {
  id: number
  title: string
  content: string
  summary: string
  sourceType: 'RSS' | 'API' | 'MANUAL'
  sourceUrl?: string
  sourceName: string
  category: string
  tags: string[]
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced'
  ageGroup: string
  publishedAt: string
  createdAt: string
  isRecommended: boolean
  relevanceScore: number
  viewCount: number
}

export interface RSSSource {
  id: number
  name: string
  url: string
  category: string
  isActive: boolean
  lastSync: string
  itemCount: number
}

export interface HotspotCreateRequest {
  title: string
  content: string
  summary: string
  sourceType: 'RSS' | 'API' | 'MANUAL'
  sourceUrl?: string
  sourceName: string
  category: string
  tags: string[]
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced'
  ageGroup: string
  isRecommended?: boolean
}

export interface RSSSourceCreateRequest {
  name: string
  url: string
  category: string
  isActive?: boolean
}

export interface CollectRSSRequest {
  maxItemsPerFeed?: number
  targetLanguage?: string
}

export interface DailyRecommendationsRequest {
  libraryId: number
  limit?: number
  difficultyLevel?: string
  topics?: string[]
}

export interface HotspotSearchParams {
  page?: number
  limit?: number
  search?: string
  category?: string
  difficultyLevel?: string
  sourceType?: string
  isRecommended?: boolean
}

export interface HotspotListResponse {
  hotspots: HotspotResource[]
  total: number
  page: number
  pageSize: number
}

export interface CollectRSSResponse {
  success: boolean
  collectedCount: number
  resources: HotspotResource[]
  message: string
}

export interface DailyRecommendationsResponse {
  success: boolean
  recommendations: HotspotResource[]
  totalCount: number
  generatedAt: string
}

// 热点资源API
export const hotTopicsApi = {
  // 获取热点资源列表
  getHotspots: async (params: HotspotSearchParams = {}): Promise<HotspotListResponse> => {
    const response = await apiClient.get('/hotspots', { params })
    return response.data
  },

  // 获取热点资源详情
  getHotspot: async (id: number): Promise<HotspotResource> => {
    const response = await apiClient.get(`/hotspots/${id}`)
    return response.data
  },

  // 创建热点资源
  createHotspot: async (data: HotspotCreateRequest): Promise<HotspotResource> => {
    const response = await apiClient.post('/hotspots', data)
    return response.data
  },

  // 更新热点资源
  updateHotspot: async (
    id: number,
    data: Partial<HotspotCreateRequest>
  ): Promise<HotspotResource> => {
    const response = await apiClient.put(`/hotspots/${id}`, data)
    return response.data
  },

  // 删除热点资源
  deleteHotspot: async (id: number): Promise<void> => {
    await apiClient.delete(`/hotspots/${id}`)
  },

  // 收集RSS资源
  collectRSSResources: async (params: CollectRSSRequest = {}): Promise<CollectRSSResponse> => {
    const response = await apiClient.post('/hotspots/rss-feeds/collect', null, { params })
    return response.data
  },

  // 获取每日推荐
  getDailyRecommendations: async (
    params: DailyRecommendationsRequest
  ): Promise<DailyRecommendationsResponse> => {
    const response = await apiClient.get('/hotspots/daily-recommendations', { params })
    return response.data
  },

  // 标记为推荐
  toggleRecommendation: async (id: number, isRecommended: boolean): Promise<HotspotResource> => {
    const response = await apiClient.patch(`/hotspots/${id}/recommendation`, { isRecommended })
    return response.data
  },

  // 增加查看次数
  incrementViewCount: async (id: number): Promise<void> => {
    await apiClient.post(`/hotspots/${id}/view`)
  },

  // RSS订阅源管理
  // 获取RSS订阅源列表
  getRSSSources: async (): Promise<RSSSource[]> => {
    const response = await apiClient.get('/hotspots/rss-sources')
    return response.data
  },

  // 创建RSS订阅源
  createRSSSource: async (data: RSSSourceCreateRequest): Promise<RSSSource> => {
    const response = await apiClient.post('/hotspots/rss-sources', data)
    return response.data
  },

  // 更新RSS订阅源
  updateRSSSource: async (
    id: number,
    data: Partial<RSSSourceCreateRequest>
  ): Promise<RSSSource> => {
    const response = await apiClient.put(`/hotspots/rss-sources/${id}`, data)
    return response.data
  },

  // 删除RSS订阅源
  deleteRSSSource: async (id: number): Promise<void> => {
    await apiClient.delete(`/hotspots/rss-sources/${id}`)
  },

  // 同步RSS订阅源
  syncRSSSource: async (
    id: number
  ): Promise<{ success: boolean; itemCount: number; message: string }> => {
    const response = await apiClient.post(`/hotspots/rss-sources/${id}/sync`)
    return response.data
  },

  // 切换RSS订阅源状态
  toggleRSSSourceStatus: async (id: number, isActive: boolean): Promise<RSSSource> => {
    const response = await apiClient.patch(`/hotspots/rss-sources/${id}/status`, { isActive })
    return response.data
  },

  // 获取热点统计
  getHotspotStats: async (): Promise<{
    totalHotspots: number
    totalSources: number
    todayCollected: number
    weeklyViews: number
    topCategories: Array<{ category: string; count: number }>
    recentActivity: Array<{
      type: string
      title: string
      timestamp: string
    }>
  }> => {
    const response = await apiClient.get('/hotspots/stats')
    return response.data
  },

  // 搜索热点资源
  searchHotspots: async (
    query: string,
    filters?: {
      category?: string
      difficultyLevel?: string
      dateRange?: { start: string; end: string }
    }
  ): Promise<HotspotResource[]> => {
    const response = await apiClient.post('/hotspots/search', { query, filters })
    return response.data
  },

  // 获取相关热点推荐
  getRelatedHotspots: async (id: number, limit: number = 5): Promise<HotspotResource[]> => {
    const response = await apiClient.get(`/hotspots/${id}/related`, { params: { limit } })
    return response.data
  },

  // 导出热点资源
  exportHotspots: async (params: {
    format: 'csv' | 'excel' | 'pdf'
    filters?: HotspotSearchParams
  }): Promise<Blob> => {
    const response = await apiClient.get('/hotspots/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  // 批量操作
  batchUpdateHotspots: async (
    ids: number[],
    updates: {
      category?: string
      difficultyLevel?: string
      isRecommended?: boolean
      tags?: string[]
    }
  ): Promise<{ success: boolean; updatedCount: number }> => {
    const response = await apiClient.patch('/hotspots/batch', { ids, updates })
    return response.data
  },

  // 批量删除
  batchDeleteHotspots: async (
    ids: number[]
  ): Promise<{ success: boolean; deletedCount: number }> => {
    const response = await apiClient.delete('/hotspots/batch', { data: { ids } })
    return response.data
  },
}
