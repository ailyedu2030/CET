/**
 * 需求25：错题强化与自适应学习 - API接口
 *
 * 实现与后端自适应学习API的完整对接
 */

import { apiClient } from './client'

// ==================== 基础类型定义 ====================

export interface ErrorAnalysisResponse {
  student_id: number
  analysis_period_days: number
  total_errors: number
  error_frequency: Record<string, number>
  error_trend: Array<{
    date: string
    error_count: number
    improvement_rate: number
  }>
  weak_knowledge_points: Array<{
    knowledge_point_id: number
    knowledge_point_title: string
    error_count: number
    mastery_level: number
    improvement_priority: number
  }>
  improvement_suggestions: string[]
  analysis_time: string
}

export interface KnowledgeGapResponse {
  knowledge_point_id: number
  knowledge_point_title: string
  mastery_level: number
  error_count: number
  last_error_date: string
  improvement_priority: number
  related_concepts: string[]
  recommended_practice_time: number
}

export interface ForgettingCurveResponse {
  student_id: number
  question_id: number
  current_retention: number
  learning_sessions: number
  curve_data: Array<{
    day: number
    date: string
    retention_rate: number
  }>
  next_review_date: string
  mastery_status: 'learning' | 'reviewing' | 'mastered'
  analysis_time: string
}

export interface LearningStrategyResponse {
  student_id: number
  strategy_type: 'spaced_repetition' | 'difficulty_progression' | 'knowledge_graph'
  current_strategy: {
    name: string
    description: string
    parameters: Record<string, any>
  }
  effectiveness_score: number
  adaptation_history: Array<{
    date: string
    strategy_change: string
    reason: string
    performance_impact: number
  }>
  next_adaptation_date: string
}

export interface ReinforcementPlanResponse {
  student_id: number
  plan_id: number
  plan_name: string
  target_knowledge_points: Array<{
    knowledge_point_id: number
    knowledge_point_title: string
    current_mastery: number
    target_mastery: number
    estimated_completion_days: number
  }>
  daily_practice_schedule: Array<{
    day: number
    practice_sessions: Array<{
      session_type: string
      duration_minutes: number
      question_count: number
      focus_areas: string[]
    }>
  }>
  progress_milestones: Array<{
    milestone_name: string
    target_date: string
    completion_criteria: string
    reward_points: number
  }>
  estimated_completion_date: string
  created_at: string
}

export interface ReviewScheduleResponse {
  student_id: number
  total_items: number
  urgent_reviews: Array<{
    question_id: number
    question_title: string
    last_review_date: string
    next_review_date: string
    priority_level: 'high' | 'medium' | 'low'
    estimated_retention: number
  }>
  today_reviews: Array<{
    question_id: number
    question_title: string
    review_type: 'reinforcement' | 'maintenance' | 'assessment'
    estimated_duration: number
  }>
  upcoming_reviews: Array<{
    date: string
    review_count: number
    estimated_total_time: number
  }>
  schedule_optimization: {
    optimal_daily_time: number
    best_review_times: string[]
    workload_distribution: Record<string, number>
  }
}

// ==================== API请求类型 ====================

export interface ErrorAnalysisRequest {
  student_id: number
  analysis_days: number
  include_categories?: boolean
  include_trends?: boolean
}

export interface LearningStrategyRequest {
  student_id: number
  strategy_preferences?: string[]
  performance_goals?: Record<string, number>
}

export interface ReinforcementPlanRequest {
  student_id: number
  target_knowledge_points: number[]
  daily_time_budget: number
  completion_deadline?: string
  difficulty_preference?: 'adaptive' | 'progressive' | 'mixed'
}

export interface ReviewScheduleRequest {
  student_id: number
  schedule_days: number
  daily_time_limit?: number
  priority_focus?: 'weak_areas' | 'balanced' | 'maintenance'
}

// ==================== API接口实现 ====================

export const adaptiveLearningApi = {
  // 错题分析
  getErrorAnalysis: async (params: ErrorAnalysisRequest): Promise<ErrorAnalysisResponse> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/error-analysis/${params.student_id}`,
      {
        params: {
          analysis_days: params.analysis_days,
          include_categories: params.include_categories,
          include_trends: params.include_trends,
        },
      }
    )
    return response.data
  },

  // 知识缺口分析
  getKnowledgeGaps: async (studentId: number): Promise<KnowledgeGapResponse[]> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/knowledge-gaps/${studentId}`
    )
    return response.data
  },

  // 遗忘曲线分析
  getForgettingCurve: async (
    studentId: number,
    questionId: number
  ): Promise<ForgettingCurveResponse> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/forgetting-curve/${studentId}/${questionId}`
    )
    return response.data
  },

  // 学习策略
  getLearningStrategy: async (studentId: number): Promise<LearningStrategyResponse> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/learning-strategy/${studentId}`
    )
    return response.data
  },

  updateLearningStrategy: async (
    params: LearningStrategyRequest
  ): Promise<LearningStrategyResponse> => {
    const response = await apiClient.post(
      `/api/v1/training/adaptive-learning/learning-strategy/${params.student_id}`,
      params
    )
    return response.data
  },

  // 强化训练计划
  getReinforcementPlan: async (studentId: number): Promise<ReinforcementPlanResponse> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/reinforcement-plan/${studentId}`
    )
    return response.data
  },

  generateReinforcementPlan: async (
    params: ReinforcementPlanRequest
  ): Promise<ReinforcementPlanResponse> => {
    const response = await apiClient.post(
      `/api/v1/training/adaptive-learning/reinforcement-plan/${params.student_id}`,
      params
    )
    return response.data
  },

  // 复习计划
  getReviewSchedule: async (params: ReviewScheduleRequest): Promise<ReviewScheduleResponse> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/review-schedule/${params.student_id}`,
      {
        params: {
          schedule_days: params.schedule_days,
          daily_time_limit: params.daily_time_limit,
          priority_focus: params.priority_focus,
        },
      }
    )
    return response.data
  },

  // 触发自适应调整
  triggerAdaptation: async (studentId: number): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(
      `/api/v1/training/adaptive-learning/trigger-adaptation/${studentId}`
    )
    return response.data
  },

  // 获取学习效果评估
  getLearningEffectiveness: async (
    studentId: number,
    evaluationDays: number = 30
  ): Promise<any> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/learning-effectiveness/${studentId}`,
      {
        params: { evaluation_days: evaluationDays },
      }
    )
    return response.data
  },
}
