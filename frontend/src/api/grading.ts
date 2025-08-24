import { apiClient } from './client'
import { TrainingType } from '../types/training'

export interface GradingResult {
  id: number
  sessionId: number
  type: TrainingType
  totalQuestions: number
  correctAnswers: number
  score: number
  accuracy: number
  timeSpent: number
  completedAt: string
  feedback: {
    overall: string
    strengths: string[]
    weaknesses: string[]
    suggestions: string[]
  }
  questionResults: QuestionResult[]
}

export interface QuestionResult {
  id: number
  questionText: string
  userAnswer: string
  correctAnswer: string
  isCorrect: boolean
  explanation: string
  difficulty: string
  topic: string
  timeSpent: number
  aiAnalysis: {
    errorType?: string
    suggestion: string
    relatedConcepts: string[]
  }
}

export interface GradingHistoryResponse {
  results: GradingResult[]
  total: number
  page: number
  pageSize: number
}

export const gradingApi = {
  // 获取最新批改结果
  getLatestResult: async (): Promise<GradingResult | null> => {
    try {
      const response = await apiClient.get('/grading/latest')
      return response.data
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  // 获取批改结果详情
  getGradingResult: async (resultId: number): Promise<GradingResult> => {
    const response = await apiClient.get(`/grading/results/${resultId}`)
    return response.data
  },

  // 获取批改历史
  getGradingHistory: async (
    params: {
      page?: number
      limit?: number
      type?: TrainingType
    } = {}
  ): Promise<GradingHistoryResponse> => {
    const response = await apiClient.get('/grading/history', { params })
    return response.data
  },

  // 提交反馈
  submitFeedback: async (data: {
    resultId: number
    helpful: boolean
    comment?: string
  }): Promise<void> => {
    await apiClient.post('/grading/feedback', data)
  },

  // 请求重新批改
  requestRegrade: async (data: { resultId: number; reason: string }): Promise<void> => {
    await apiClient.post('/grading/regrade', data)
  },

  // 导出批改报告
  exportReport: async (resultId: number): Promise<Blob> => {
    const response = await apiClient.get(`/grading/results/${resultId}/export`, {
      responseType: 'blob',
    })
    return response.data
  },

  // 获取批改统计
  getGradingStats: async (
    params: {
      period?: 'week' | 'month' | 'year'
    } = {}
  ): Promise<{
    totalResults: number
    averageScore: number
    improvementTrend: number
    strengthAreas: string[]
    weaknessAreas: string[]
    recentProgress: Array<{
      date: string
      score: number
      type: TrainingType
    }>
  }> => {
    const response = await apiClient.get('/grading/stats', { params })
    return response.data
  },
}
