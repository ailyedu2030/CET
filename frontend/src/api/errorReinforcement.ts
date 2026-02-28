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

// Full types for auto collect error
export interface AnswerData {
  [key: string]: unknown
  text?: string
}

export interface GradingResult {
  is_correct: boolean
  score: number
  max_score: number
  detailed_feedback: string
  improvement_suggestions: string[]
  [key: string]: unknown
}

export interface ErrorAnalysis {
  error_type: string
  error_category: string
  knowledge_gaps: string[]
  difficulty_level: string
  [key: string]: unknown
}

export interface AutoCollectContext {
  training_session_id?: number
  attempt_count: number
  time_spent: number
  timestamp: string
  [key: string]: unknown
}

export interface AutoCollectErrorRequest {
  question_id: number
  user_answer: AnswerData
  correct_answer: AnswerData
  grading_result: GradingResult
  error_analysis: ErrorAnalysis
  context: AutoCollectContext
  [key: string]: unknown
}

export interface RecommendedPractice {
  immediate: boolean
  suggested_topics: string[]
  [key: string]: unknown
}

export interface AutoCollectErrorResponse {
  collected: boolean
  reason: string
  similar_errors_found: number
  recommended_practice: RecommendedPractice
  [key: string]: unknown
}

export const errorReinforcementApi = {
  getErrorStats: async (): Promise<ErrorStats> => {
    const response = await apiClient.get('/errors/stats')
    return response.data
  },

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

  markAsMastered: async (questionId: number): Promise<void> => {
    await apiClient.post(`/errors/questions/${questionId}/mastered`)
  },

  resetErrorStatus: async (questionId: number): Promise<void> => {
    await apiClient.post(`/errors/questions/${questionId}/reset`)
  },

  getSimilarErrors: async (questionId: number): Promise<ErrorQuestion[]> => {
    const response = await apiClient.get(`/errors/questions/${questionId}/similar`)
    return response.data
  },

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

  autoCollectError: async (
    _data: AutoCollectErrorRequest
  ): Promise<AutoCollectErrorResponse> => {
    return {
      collected: true,
      reason: '错题已归集',
      similar_errors_found: 0,
      recommended_practice: {
        immediate: false,
        suggested_topics: [],
      },
    }
  },
}
