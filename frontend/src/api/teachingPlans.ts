/**
 * 教学计划构建API客户端 - 需求13实现
 */
import { apiClient } from './client'

// 教学计划相关类型定义
export interface LessonPlan {
  id: number
  title: string
  syllabusId: number
  syllabusTitle: string
  chapterNumber: number
  chapterTitle: string
  objectives: string[]
  content: {
    introduction: string
    mainContent: string[]
    activities: string[]
    summary: string
  }
  duration: number
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  resources: string[]
  assessment: string
  homework: string
  status: 'draft' | 'reviewing' | 'approved' | 'published'
  templateId?: number
  templateName?: string
  createdBy: number
  createdAt: string
  updatedAt: string
  version: number
  collaborators: Array<{
    id: number
    name: string
    role: string
    lastActive: string
  }>
}

export interface LessonTemplate {
  id: number
  name: string
  description: string
  category: string
  structure: {
    sections: Array<{
      name: string
      duration: number
      type: string
    }>
  }
  isPublic: boolean
  usageCount: number
  rating: number
  createdBy: string
  createdAt: string
}

export interface ScheduleItem {
  id: number
  lessonPlanId: number
  lessonPlanTitle: string
  classId: number
  className: string
  teacherId: number
  teacherName: string
  roomId: number
  roomName: string
  dayOfWeek: number
  startTime: string
  endTime: string
  duration: number
  date: string
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled'
  conflicts: Array<{
    type: 'teacher' | 'room' | 'class'
    message: string
  }>
  attendanceCount?: number
  totalStudents?: number
}

export interface LessonPlanCreateRequest {
  title: string
  syllabusId: number
  chapterNumber: number
  chapterTitle: string
  objectives: string[]
  content: {
    introduction: string
    mainContent: string[]
    activities: string[]
    summary: string
  }
  duration: number
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  resources: string[]
  assessment: string
  homework: string
  templateId?: number
}

export interface LessonTemplateCreateRequest {
  name: string
  description: string
  category: string
  structure: {
    sections: Array<{
      name: string
      duration: number
      type: string
    }>
  }
  isPublic: boolean
}

export interface ScheduleCreateRequest {
  lessonPlanId: number
  classId: number
  teacherId: number
  roomId: number
  dayOfWeek: number
  startTime: string
  endTime: string
  date: string
}

export interface AIGenerateRequest {
  syllabusId: number
  mode: 'all' | 'missing' | 'selected'
  templateId?: number
  includeHotTopics?: boolean
  personalizeForClass?: boolean
  selectedChapters?: number[]
}

export interface ScheduleGenerateRequest {
  range: 'week' | 'month' | 'semester'
  priority: 'teacher' | 'room' | 'student'
  maxDailyHours: number
  autoResolveConflicts: boolean
  sendNotifications: boolean
  classIds?: number[]
}

export interface LessonPlanListResponse {
  lessonPlans: LessonPlan[]
  total: number
  page: number
  pageSize: number
}

export interface LessonTemplateListResponse {
  templates: LessonTemplate[]
  total: number
}

export interface ScheduleListResponse {
  scheduleItems: ScheduleItem[]
  conflicts: Array<{
    id: number
    type: string
    message: string
    severity: 'warning' | 'error'
    suggestions: string[]
  }>
}

export interface AIGenerateResponse {
  success: boolean
  generatedCount: number
  lessonPlans: LessonPlan[]
  message: string
  warnings?: string[]
}

export interface ScheduleGenerateResponse {
  success: boolean
  generatedCount: number
  scheduleItems: ScheduleItem[]
  conflicts: Array<{
    type: string
    message: string
    suggestions: string[]
  }>
  message: string
}

// 教案管理API
export const lessonPlanApi = {
  // 获取教案列表
  getLessonPlans: async (
    params: {
      page?: number
      limit?: number
      search?: string
      status?: string
      syllabusId?: number
    } = {}
  ): Promise<LessonPlanListResponse> => {
    const response = await apiClient.get('/ai/lesson-plans', { params })
    return response.data
  },

  // 获取教案详情
  getLessonPlan: async (id: number): Promise<LessonPlan> => {
    const response = await apiClient.get(`/ai/lesson-plans/${id}`)
    return response.data
  },

  // 创建教案
  createLessonPlan: async (data: LessonPlanCreateRequest): Promise<LessonPlan> => {
    const response = await apiClient.post('/ai/lesson-plans', data)
    return response.data
  },

  // 更新教案
  updateLessonPlan: async (
    id: number,
    data: Partial<LessonPlanCreateRequest>
  ): Promise<LessonPlan> => {
    const response = await apiClient.put(`/ai/lesson-plans/${id}`, data)
    return response.data
  },

  // 删除教案
  deleteLessonPlan: async (id: number): Promise<void> => {
    await apiClient.delete(`/ai/lesson-plans/${id}`)
  },

  // AI生成教案
  generateLessonPlans: async (params: AIGenerateRequest): Promise<AIGenerateResponse> => {
    const response = await apiClient.post('/ai/lesson-plans/generate', params)
    return response.data
  },

  // 复制教案
  copyLessonPlan: async (id: number, title?: string): Promise<LessonPlan> => {
    const response = await apiClient.post(`/ai/lesson-plans/${id}/copy`, { title })
    return response.data
  },

  // 分享到资源库
  shareToLibrary: async (id: number, shareLevel: 'private' | 'class' | 'public'): Promise<void> => {
    await apiClient.post(`/ai/lesson-plans/${id}/share`, { shareLevel })
  },

  // 导出教案
  exportLessonPlan: async (id: number, format: 'pdf' | 'word' | 'html'): Promise<Blob> => {
    const response = await apiClient.get(`/ai/lesson-plans/${id}/export`, {
      params: { format },
      responseType: 'blob',
    })
    return response.data
  },

  // 获取教案版本历史
  getVersionHistory: async (
    id: number
  ): Promise<
    Array<{
      version: number
      createdAt: string
      createdBy: string
      changes: string[]
    }>
  > => {
    const response = await apiClient.get(`/ai/lesson-plans/${id}/versions`)
    return response.data
  },

  // 回滚到指定版本
  rollbackToVersion: async (id: number, version: number): Promise<LessonPlan> => {
    const response = await apiClient.post(`/ai/lesson-plans/${id}/rollback`, { version })
    return response.data
  },
}

// 教案模板API
export const lessonTemplateApi = {
  // 获取模板列表
  getTemplates: async (): Promise<LessonTemplateListResponse> => {
    const response = await apiClient.get('/ai/lesson-templates')
    return response.data
  },

  // 创建模板
  createTemplate: async (data: LessonTemplateCreateRequest): Promise<LessonTemplate> => {
    const response = await apiClient.post('/ai/lesson-templates', data)
    return response.data
  },

  // 更新模板
  updateTemplate: async (
    id: number,
    data: Partial<LessonTemplateCreateRequest>
  ): Promise<LessonTemplate> => {
    const response = await apiClient.put(`/ai/lesson-templates/${id}`, data)
    return response.data
  },

  // 删除模板
  deleteTemplate: async (id: number): Promise<void> => {
    await apiClient.delete(`/ai/lesson-templates/${id}`)
  },

  // 使用模板创建教案
  createFromTemplate: async (
    templateId: number,
    data: {
      title: string
      syllabusId: number
      chapterNumber: number
      chapterTitle: string
    }
  ): Promise<LessonPlan> => {
    const response = await apiClient.post(`/ai/lesson-templates/${templateId}/create-lesson`, data)
    return response.data
  },
}

// 课程表管理API
export const scheduleApi = {
  // 获取课程表
  getSchedule: async (
    params: {
      week?: string
      classId?: number
      teacherId?: number
    } = {}
  ): Promise<ScheduleListResponse> => {
    const response = await apiClient.get('/schedules', { params })
    return response.data
  },

  // 创建课程安排
  createScheduleItem: async (data: ScheduleCreateRequest): Promise<ScheduleItem> => {
    const response = await apiClient.post('/schedules', data)
    return response.data
  },

  // 更新课程安排
  updateScheduleItem: async (
    id: number,
    data: Partial<ScheduleCreateRequest>
  ): Promise<ScheduleItem> => {
    const response = await apiClient.put(`/schedules/${id}`, data)
    return response.data
  },

  // 删除课程安排
  deleteScheduleItem: async (id: number): Promise<void> => {
    await apiClient.delete(`/schedules/${id}`)
  },

  // 智能生成课程表
  generateSchedule: async (params: ScheduleGenerateRequest): Promise<ScheduleGenerateResponse> => {
    const response = await apiClient.post('/schedules/generate', params)
    return response.data
  },

  // 检测冲突
  detectConflicts: async (
    scheduleItems: ScheduleCreateRequest[]
  ): Promise<
    Array<{
      type: string
      message: string
      severity: 'warning' | 'error'
      suggestions: string[]
    }>
  > => {
    const response = await apiClient.post('/schedules/detect-conflicts', { scheduleItems })
    return response.data
  },

  // 自动解决冲突
  resolveConflicts: async (
    conflictIds: number[]
  ): Promise<{
    resolved: number
    remaining: number
    suggestions: string[]
  }> => {
    const response = await apiClient.post('/schedules/resolve-conflicts', { conflictIds })
    return response.data
  },
}

// 协作管理API
export const collaborationApi = {
  // 创建协作会话
  createSession: async (
    lessonPlanId: number
  ): Promise<{
    sessionId: string
    joinUrl: string
    expiresAt: string
  }> => {
    const response = await apiClient.post(`/ai/lesson-plans/${lessonPlanId}/collaboration`)
    return response.data
  },

  // 加入协作会话
  joinSession: async (
    sessionId: string
  ): Promise<{
    success: boolean
    participants: Array<{
      id: number
      name: string
      role: string
      joinedAt: string
    }>
  }> => {
    const response = await apiClient.post(`/ai/collaboration/${sessionId}/join`)
    return response.data
  },

  // 邀请协作者
  inviteCollaborator: async (
    lessonPlanId: number,
    data: {
      email: string
      role: 'edit' | 'comment' | 'view'
    }
  ): Promise<void> => {
    await apiClient.post(`/ai/lesson-plans/${lessonPlanId}/invite`, data)
  },

  // 获取协作历史
  getCollaborationHistory: async (
    lessonPlanId: number
  ): Promise<
    Array<{
      id: number
      action: string
      user: string
      timestamp: string
      changes: string[]
    }>
  > => {
    const response = await apiClient.get(`/ai/lesson-plans/${lessonPlanId}/collaboration/history`)
    return response.data
  },
}
