/**
 * 听力训练系统 API - 需求22实现
 *
 * 验收标准：
 * 1. 题型分类：短对话训练、长对话训练、短文理解、讲座训练
 * 2. 训练特性：口语跟读练习、语速调节/重复播放、字幕辅助、单词/短语听写训练
 * 3. 智能辅助：音标识别练习、场景化听力应试技巧、自动标注个人听力难点、听力题目错误原因分析
 */

import { apiClient } from './client'
import { DifficultyLevel } from '../types/training'
import type { ListeningQuestion, AudioSegment, ListeningSessionSettings } from '../types/listening'

// ==================== 导出类型定义 ====================

export interface ListeningExercise {
  id: number
  title: string
  description?: string
  exercise_type: 'short_conversation' | 'long_conversation' | 'passage' | 'lecture'
  difficulty_level: DifficultyLevel
  audio_file_id?: number
  transcript?: string
  questions_data: {
    questions: ListeningQuestion[]
    audio_segments?: AudioSegment[]
  }
  total_questions: number
  duration_seconds?: number
  audio_duration?: number
  is_active: boolean
  tags: string[]
  created_at: string
  updated_at: string
}

// ListeningQuestion 类型定义已移至 ../types/listening.ts 以避免重复定义

// AudioSegment 类型定义已移至 ../types/listening.ts 以避免重复定义

export interface ListeningSession {
  id: number
  exercise_id: number
  session_name?: string
  start_time: string
  end_time?: string
  current_question: number
  total_questions: number
  is_completed: boolean
  answers: Record<string, any>
  audio_progress: Record<string, any>
  total_time_seconds: number
  listening_time_seconds: number
  answering_time_seconds: number
  settings: ListeningSessionSettings
}

// ListeningSessionSettings 类型定义已移至 ../types/listening.ts 以避免重复定义

export interface ListeningResult {
  id: number
  session_id: number
  score: number
  correct_count: number
  total_questions: number
  completion_time: string
  total_time_seconds: number
  average_time_per_question: number
  detailed_results: Record<string, any>
  answer_analysis: Record<string, any>
  listening_ability_score?: number
  comprehension_score?: number
  vocabulary_score?: number
  weak_points: string[]
  improvement_suggestions: string[]
}

// ==================== 请求/响应类型 ====================

export interface CreateListeningExerciseRequest {
  title: string
  description?: string
  exercise_type: 'short_conversation' | 'long_conversation' | 'passage' | 'lecture'
  difficulty_level: DifficultyLevel
  questions_data: {
    questions: Omit<ListeningQuestion, 'id'>[]
    audio_segments?: Omit<AudioSegment, 'id'>[]
  }
  total_questions: number
  duration_seconds?: number
  audio_duration?: number
  tags?: string[]
}

export interface StartListeningSessionRequest {
  exercise_id: number
  session_name?: string
  settings?: Partial<ListeningSessionSettings>
}

export interface SubmitListeningAnswersRequest {
  session_id: number
  answers: Record<string, any>
  audio_progress: Record<string, any>
  total_time_seconds: number
  listening_time_seconds: number
  answering_time_seconds: number
}

export interface ListeningExerciseListResponse {
  exercises: ListeningExercise[]
  total: number
  page: number
  limit: number
}

export interface ListeningStatsResponse {
  total_exercises: number
  completed_exercises: number
  average_score: number
  total_listening_time: number
  improvement_rate: number
  weak_exercise_types: string[]
  strong_exercise_types: string[]
  recent_performance: {
    date: string
    score: number
    exercise_type: string
  }[]
}

// ==================== API 函数 ====================

export const listeningApi = {
  // ============ 听力练习管理 ============

  /**
   * 获取听力练习列表
   * 验收标准1：题型分类支持
   */
  getExercises: async (
    params: {
      page?: number
      limit?: number
      exercise_type?: string
      difficulty_level?: DifficultyLevel
      search?: string
    } = {}
  ): Promise<ListeningExerciseListResponse> => {
    const response = await apiClient.get('/api/v1/training/listening/exercises', { params })
    return response.data
  },

  /**
   * 获取听力练习详情
   */
  getExercise: async (exerciseId: number): Promise<ListeningExercise> => {
    const response = await apiClient.get(`/api/v1/training/listening/exercises/${exerciseId}`)
    return response.data
  },

  /**
   * 创建听力练习
   * 验收标准1：支持所有题型分类
   */
  createExercise: async (data: CreateListeningExerciseRequest): Promise<ListeningExercise> => {
    const response = await apiClient.post('/api/v1/training/listening/exercises', data)
    return response.data
  },

  // ============ 听力训练会话 ============

  /**
   * 开始听力训练会话
   * 验收标准2：支持训练特性配置
   */
  startSession: async (data: StartListeningSessionRequest): Promise<ListeningSession> => {
    const response = await apiClient.post(
      `/api/v1/training/listening/exercises/${data.exercise_id}/start`,
      {
        session_name: data.session_name,
        settings: data.settings,
      }
    )
    return response.data
  },

  /**
   * 获取当前会话状态
   */
  getSession: async (sessionId: number): Promise<ListeningSession> => {
    const response = await apiClient.get(`/api/v1/training/listening/sessions/${sessionId}`)
    return response.data
  },

  /**
   * 更新会话进度
   * 验收标准2：支持音频进度跟踪
   */
  updateSessionProgress: async (
    sessionId: number,
    progress: {
      current_question?: number
      audio_progress?: Record<string, any>
      answers?: Record<string, any>
    }
  ): Promise<void> => {
    await apiClient.patch(`/api/v1/training/listening/sessions/${sessionId}/progress`, progress)
  },

  /**
   * 提交听力答案
   * 验收标准3：支持智能分析
   */
  submitAnswers: async (data: SubmitListeningAnswersRequest): Promise<ListeningResult> => {
    const response = await apiClient.post(
      `/api/v1/training/listening/sessions/${data.session_id}/submit`,
      data
    )
    return response.data
  },

  // ============ 听力统计和分析 ============

  /**
   * 获取听力训练统计
   * 验收标准3：智能辅助分析
   */
  getStats: async (): Promise<ListeningStatsResponse> => {
    const response = await apiClient.get('/api/v1/training/listening/statistics')
    return response.data
  },

  /**
   * 获取个人听力难点分析
   * 验收标准3：自动标注个人听力难点
   */
  getWeakPoints: async (
    exerciseId: number
  ): Promise<{
    weak_points: Array<{
      category: string
      description: string
      frequency: number
      improvement_suggestions: string[]
    }>
    phonetic_difficulties: Array<{
      phoneme: string
      accuracy_rate: number
      practice_suggestions: string[]
    }>
  }> => {
    const response = await apiClient.post(
      `/api/v1/training/listening/exercises/${exerciseId}/difficulty-analysis`,
      {
        analysis_type: 'weak_points',
        user_answers: [],
        correct_answers: [],
      }
    )
    return response.data
  },

  /**
   * 获取听力错误原因分析
   * 验收标准3：听力题目错误原因分析
   */
  getErrorAnalysis: async (
    exerciseId: number,
    userAnswers: any[],
    correctAnswers: any[]
  ): Promise<{
    error_categories: Array<{
      category: string
      count: number
      percentage: number
      examples: string[]
    }>
    improvement_plan: Array<{
      focus_area: string
      practice_methods: string[]
      estimated_improvement_time: string
    }>
  }> => {
    const response = await apiClient.post(
      `/api/v1/training/listening/exercises/${exerciseId}/difficulty-analysis`,
      {
        analysis_type: 'error_analysis',
        user_answers: userAnswers,
        correct_answers: correctAnswers,
      }
    )
    return response.data
  },

  // ============ 智能辅助功能 ============

  /**
   * 获取音标识别练习
   * 验收标准3：针对性音标识别练习
   */
  getPhoneticPractice: async (
    exerciseId: number,
    targetPhonetics: string[]
  ): Promise<{
    exercises: Array<{
      id: string
      phoneme: string
      word_examples: string[]
      audio_url: string
      practice_type: 'recognition' | 'pronunciation'
    }>
  }> => {
    const response = await apiClient.post(
      `/api/v1/training/listening/exercises/${exerciseId}/phonetic-practice`,
      {
        target_phonetics: targetPhonetics,
        practice_type: 'recognition',
      }
    )
    return response.data
  },

  /**
   * 获取场景化听力技巧
   * 验收标准3：场景化听力应试技巧
   */
  getListeningTips: async (
    exerciseId: number
  ): Promise<{
    tips: Array<{
      category: string
      title: string
      description: string
      examples: string[]
      practice_methods: string[]
    }>
  }> => {
    const response = await apiClient.get(
      `/api/v1/training/listening/exercises/${exerciseId}/techniques`
    )
    return response.data
  },

  /**
   * 语音识别和发音评估
   * 验收标准2：口语跟读练习
   */
  evaluatePronunciation: async (
    audioBlob: Blob,
    targetText: string
  ): Promise<{
    overall_score: number
    pronunciation_score: number
    fluency_score: number
    accuracy_score: number
    detailed_feedback: Array<{
      word: string
      score: number
      issues: string[]
      suggestions: string[]
    }>
  }> => {
    const formData = new FormData()
    formData.append('audio', audioBlob)
    formData.append('target_text', targetText)

    const response = await apiClient.post(
      '/api/v1/training/listening/pronunciation-evaluation',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },
}
