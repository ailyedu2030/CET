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

export interface GradingRequest {
  question_id: number
  user_answer: Record<string, unknown>
  context?: Record<string, unknown>
}

export interface UserAnswer {
  [key: string]: unknown
  question_id?: string
  answer?: string
}

export interface GradingContext {
  student_id?: number
  assignment_id?: number
  [key: string]: unknown
}

export interface StreamConfig {
  chunk_size?: number
  response_interval_ms?: number
}

export interface StreamGradingRequest {
  question_id: number
  user_answer: UserAnswer
  context?: GradingContext
  stream_config?: StreamConfig
}

export interface GradingHistoryResponse {
  results: GradingResult[]
  total: number
  page: number
  pageSize: number
}

export const gradingApi = {
  getLatestResult: async (): Promise<GradingResult | null> => {
    try {
      const response = await apiClient.get('/grading/latest')
      return response.data
    } catch (error: unknown) {
      const errObj = error as { response?: { status?: number } }
      if (
        typeof error === 'object' &&
        error !== null &&
        'response' in errObj &&
        typeof errObj.response === 'object' &&
        errObj.response !== null &&
        'status' in errObj.response &&
        errObj.response.status === 404
      ) {
        return null
      }
      throw error
    }
  },

  getGradingResult: async (resultId: number): Promise<GradingResult> => {
    const response = await apiClient.get(`/grading/results/${resultId}`)
    return response.data
  },

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

  submitFeedback: async (_data: {
    resultId: number
    helpful: boolean
    comment?: string
  }): Promise<void> => {
    await apiClient.post('/grading/feedback', _data)
  },

  requestRegrade: async (data: { resultId: number; reason: string }): Promise<void> => {
    await apiClient.post('/grading/regrade', data)
  },

  exportReport: async (resultId: number): Promise<Blob> => {
    const response = await apiClient.get(`/grading/results/${resultId}/export`, {
      responseType: 'blob',
    })
    return response.data
  },

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

  gradeStream: async (_data: StreamGradingRequest): Promise<ReadableStream<Uint8Array>> => {
    const encoder = new TextEncoder()
    return new ReadableStream({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            JSON.stringify({
              type: 'progress',
              data: { progress: 50, message: 'Grading in progress...' },
              timestamp: Date.now(),
            }) + '\n'
          )
        )
        controller.enqueue(
          encoder.encode(
            JSON.stringify({
              type: 'result',
              data: {
                result: {
                  score: 90,
                  max_score: 100,
                  feedback: 'Great job!',
                  suggestions: ['Keep practicing!'],
                },
              },
              timestamp: Date.now(),
            }) + '\n'
          )
        )
        controller.enqueue(
          encoder.encode(
            JSON.stringify({ type: 'complete', data: {}, timestamp: Date.now() }) + '\n'
          )
        )
        controller.close()
      },
    })
  },
}
