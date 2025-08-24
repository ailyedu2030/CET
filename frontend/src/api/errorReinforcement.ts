import { apiClient } from './client'
import { TrainingType, DifficultyLevel } from '../types/training'

export interface ErrorQuestion {
  id: number
  questionText: string
  userAnswer: string
  correctAnswer: string
  explanation: string
  type: TrainingType
  difficulty: DifficultyLevel
  topic: string
  errorType: string
  errorCount: number
  lastAttemptAt: string
  masteryLevel: number
  relatedConcepts: string[]
  similarQuestions: number[]
}

export interface ErrorStats {
  totalErrors: number
  masteredErrors: number
  improvingErrors: number
  persistentErrors: number
  errorsByType: Record<string, number>
  errorsByTopic: Record<string, number>
  masteryProgress: number
}

export interface ErrorQuestionsResponse {
  questions: ErrorQuestion[]
  total: number
  page: number
  pageSize: number
}

export const errorReinforcementApi = {
  // 获取错题统计
  getErrorStats: async (): Promise<ErrorStats> => {
    const response = await apiClient.get('/errors/stats')
    return response.data
  },

  // 获取错题列表
  getErrorQuestions: async (
    params: {
      page?: number
      limit?: number
      type?: TrainingType
      topic?: string
      difficulty?: DifficultyLevel
      masteryLevel?: 'low' | 'medium' | 'high'
      includeMastered?: boolean
    } = {}
  ): Promise<ErrorQuestionsResponse> => {
    const response = await apiClient.get('/errors/questions', { params })
    return response.data
  },

  // 开始错题练习
  startErrorPractice: async (data: {
    questionIds: number[]
    mode: 'reinforcement' | 'review' | 'test'
    timeLimit?: number
  }): Promise<{
    sessionId: number
    questionCount: number
    estimatedTime: number
  }> => {
    const response = await apiClient.post('/errors/practice/start', data)
    return response.data
  },

  // 标记为已掌握
  markAsMastered: async (questionId: number): Promise<void> => {
    await apiClient.post(`/errors/questions/${questionId}/mastered`)
  },

  // 重置错题状态
  resetErrorStatus: async (questionId: number): Promise<void> => {
    await apiClient.post(`/errors/questions/${questionId}/reset`)
  },

  // 获取相似错题
  getSimilarErrors: async (questionId: number): Promise<ErrorQuestion[]> => {
    const response = await apiClient.get(`/errors/questions/${questionId}/similar`)
    return response.data
  },

  // 获取错题分析报告
  getErrorAnalysis: async (
    params: {
      period?: 'week' | 'month' | 'quarter'
    } = {}
  ): Promise<{
    errorTrends: Array<{
      date: string
      errorCount: number
      masteredCount: number
    }>
    topicAnalysis: Array<{
      topic: string
      errorRate: number
      improvementRate: number
    }>
    difficultyDistribution: Record<DifficultyLevel, number>
    recommendations: string[]
  }> => {
    const response = await apiClient.get('/errors/analysis', { params })
    return response.data
  },

  // 生成个性化练习计划
  generatePracticePlan: async (data: {
    targetMasteryLevel: number
    dailyTimeLimit: number
    focusAreas?: string[]
  }): Promise<{
    planId: number
    dailyTasks: Array<{
      date: string
      questionIds: number[]
      estimatedTime: number
      priority: 'high' | 'medium' | 'low'
    }>
    expectedCompletion: string
  }> => {
    const response = await apiClient.post('/errors/practice-plan', data)
    return response.data
  },

  // 更新练习进度
  updatePracticeProgress: async (data: {
    questionId: number
    isCorrect: boolean
    timeSpent: number
    confidence: number
  }): Promise<{
    masteryLevelChange: number
    nextReviewDate: string
  }> => {
    const response = await apiClient.post('/errors/practice/progress', data)
    return response.data
  },
}
