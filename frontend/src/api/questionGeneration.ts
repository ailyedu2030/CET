import { apiClient } from './client'

// 题目生成请求接口
export interface QuestionGenerationRequest {
  course_id?: number
  vocabulary_level?: 'basic' | 'intermediate' | 'advanced'
  topic_keywords?: string[]
  question_types?: string[]
  difficulty_level?: 'easy' | 'medium' | 'hard'
  count?: number
  include_hot_topics?: boolean
  custom_requirements?: string
}

// 题目生成响应接口
export interface QuestionGenerationResponse {
  questions: GeneratedQuestion[]
  generation_metadata: {
    vocabulary_source: string
    hot_topics_used: string[]
    generation_time: string
    total_count: number
  }
}

// 生成的题目接口
export interface GeneratedQuestion {
  id: string
  type: 'reading' | 'listening' | 'writing' | 'translation'
  title: string
  content: string
  options?: string[]
  correct_answer: string | string[]
  explanation: string
  difficulty_score: number
  vocabulary_used: string[]
  hot_topics: string[]
  estimated_time: number
  knowledge_points: string[]
}

// 词汇库信息接口
export interface VocabularyInfo {
  course_id: number
  course_name: string
  total_words: number
  levels: {
    basic: number
    intermediate: number
    advanced: number
  }
  recent_additions: string[]
  hot_topics: string[]
}

// 热点话题接口
export interface HotTopic {
  id: string
  title: string
  keywords: string[]
  relevance_score: number
  last_updated: string
  category: string
}

export const questionGenerationApi = {
  // 智能题目生成
  generateQuestions: async (
    request: QuestionGenerationRequest
  ): Promise<QuestionGenerationResponse> => {
    const response = await apiClient.post('/api/v1/core/questions/generate', request)
    return response.data
  },

  // 基于训练会话生成题目
  generateForSession: async (
    sessionId: number,
    request: Partial<QuestionGenerationRequest>
  ): Promise<QuestionGenerationResponse> => {
    const response = await apiClient.post(
      `/api/v1/training/sessions/${sessionId}/questions`,
      request
    )
    return response.data
  },

  // 获取课程词汇库信息
  getVocabularyInfo: async (courseId: number): Promise<VocabularyInfo> => {
    const response = await apiClient.get(`/api/v1/core/courses/${courseId}/vocabulary`)
    return response.data
  },

  // 获取热点话题
  getHotTopics: async (params?: {
    category?: string
    limit?: number
    min_relevance?: number
  }): Promise<HotTopic[]> => {
    const response = await apiClient.get('/api/v1/core/hot-topics', { params })
    return response.data
  },

  // 预览题目生成
  previewGeneration: async (
    request: QuestionGenerationRequest
  ): Promise<{
    estimated_count: number
    vocabulary_coverage: number
    hot_topics_available: string[]
    generation_time_estimate: string
  }> => {
    const response = await apiClient.post('/api/v1/core/questions/generate/preview', request)
    return response.data
  },

  // 保存生成的题目
  saveGeneratedQuestions: async (
    questions: GeneratedQuestion[],
    metadata?: Record<string, unknown>
  ): Promise<{
    saved_count: number
    question_ids: string[]
  }> => {
    const response = await apiClient.post('/api/v1/core/questions/save', {
      questions,
      metadata,
    })
    return response.data
  },

  // 获取生成历史
  getGenerationHistory: async (params?: {
    page?: number
    limit?: number
    course_id?: number
    start_date?: string
    end_date?: string
  }): Promise<{
    generations: Array<{
      id: string
      request: QuestionGenerationRequest
      response: QuestionGenerationResponse
      created_at: string
      status: 'success' | 'failed' | 'pending'
    }>
    total: number
    page: number
    limit: number
  }> => {
    const response = await apiClient.get('/api/v1/core/questions/generate/history', { params })
    return response.data
  },

  // 评估题目质量
  evaluateQuestions: async (
    questionIds: string[]
  ): Promise<{
    evaluations: Array<{
      question_id: string
      quality_score: number
      difficulty_accuracy: number
      vocabulary_appropriateness: number
      content_relevance: number
      suggestions: string[]
    }>
    overall_quality: number
  }> => {
    const response = await apiClient.post('/api/v1/core/questions/evaluate', {
      question_ids: questionIds,
    })
    return response.data
  },

  // 批量删除生成的题目
  deleteGeneratedQuestions: async (
    questionIds: string[]
  ): Promise<{
    deleted_count: number
    failed_deletions: string[]
  }> => {
    const response = await apiClient.delete('/api/v1/core/questions/generated', {
      data: { question_ids: questionIds },
    })
    return response.data
  },

  // 导出生成的题目
  exportQuestions: async (
    questionIds: string[],
    format: 'json' | 'excel' | 'word'
  ): Promise<Blob> => {
    const response = await apiClient.post(
      '/api/v1/core/questions/export',
      {
        question_ids: questionIds,
        format,
      },
      {
        responseType: 'blob',
      }
    )
    return response.data
  },

  // 获取题目生成统计
  getGenerationStats: async (params?: {
    period?: 'week' | 'month' | 'year'
    course_id?: number
  }): Promise<{
    total_generated: number
    success_rate: number
    average_quality_score: number
    popular_topics: string[]
    vocabulary_usage: Record<string, number>
    generation_trends: Array<{
      date: string
      count: number
      quality_score: number
    }>
  }> => {
    const response = await apiClient.get('/api/v1/core/questions/generate/stats', { params })
    return response.data
  },
}
