import { apiClient } from './client'
import { TrainingType, DifficultyLevel } from '../types/training'

export interface StartTrainingRequest {
  type: TrainingType
  difficulty: DifficultyLevel
  questionCount: number
  timeLimit: number
  adaptiveMode: boolean
}

export interface TrainingSession {
  id: number
  type: TrainingType
  difficulty: DifficultyLevel
  questionCount: number
  timeLimit: number
  status: 'active' | 'paused' | 'completed'
  progress: number
  score: number
  startedAt: string
}

export interface TrainingStats {
  totalSessions: number
  completedSessions: number
  averageScore: number
  totalTime: number
  streak: number
  level: number
  exp: number
  nextLevelExp: number
}

export interface TrainingHistoryResponse {
  sessions: TrainingSession[]
  total: number
  page: number
  pageSize: number
}

export const trainingApi = {
  // 获取训练统计
  getTrainingStats: async (): Promise<TrainingStats> => {
    const response = await apiClient.get('/training/stats')
    return response.data
  },

  // 获取当前训练会话
  getCurrentSession: async (): Promise<TrainingSession | null> => {
    try {
      const response = await apiClient.get('/training/current-session')
      return response.data
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  // 获取训练历史
  getTrainingHistory: async (
    params: {
      page?: number
      limit?: number
    } = {}
  ): Promise<TrainingHistoryResponse> => {
    const response = await apiClient.get('/training/history', { params })
    return response.data
  },

  // 开始训练
  startTraining: async (request: StartTrainingRequest): Promise<TrainingSession> => {
    const response = await apiClient.post('/training/start', request)
    return response.data
  },

  // 暂停训练
  pauseTraining: async (): Promise<void> => {
    await apiClient.post('/training/pause')
  },

  // 恢复训练
  resumeTraining: async (): Promise<void> => {
    await apiClient.post('/training/resume')
  },

  // 结束训练
  endTraining: async (): Promise<void> => {
    await apiClient.post('/training/end')
  },

  // 提交答案
  submitAnswer: async (data: {
    sessionId: number
    questionId: number
    answer: string
    timeSpent: number
  }): Promise<{
    isCorrect: boolean
    explanation?: string
    nextQuestion?: any
  }> => {
    const response = await apiClient.post('/training/submit-answer', data)
    return response.data
  },

  // 获取下一题
  getNextQuestion: async (sessionId: number): Promise<any> => {
    const response = await apiClient.get(`/training/sessions/${sessionId}/next-question`)
    return response.data
  },

  // 获取训练配置
  getTrainingConfig: async (): Promise<{
    types: { value: TrainingType; label: string }[]
    difficulties: { value: DifficultyLevel; label: string }[]
    defaultSettings: any
  }> => {
    const response = await apiClient.get('/training/config')
    return response.data
  },

  // 更新训练设置
  updateTrainingSettings: async (settings: {
    defaultQuestionCount?: number
    defaultTimeLimit?: number
    adaptiveMode?: boolean
    notifications?: boolean
  }): Promise<void> => {
    await apiClient.put('/training/settings', settings)
  },
}
