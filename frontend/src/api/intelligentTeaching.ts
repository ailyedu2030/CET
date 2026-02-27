/**
 * 需求14：教师智能教学调整系统 API
 *
 * 包含以下功能：
 * 1. AI自动学情分析
 * 2. 教案同步调整建议
 * 3. 自动化教案调整
 * 4. 教学效果跟踪
 * 5. 教师工作台集成
 * 6. 个性化教学支持
 * 7. 教学质量保障
 * 8. 数据驱动决策
 */

import { apiClient } from './client'

// ==================== 类型定义 ====================

// 学情分析相关类型
export interface LearningAnalysisRequest {
  class_id: number
  course_id: number
  analysis_period_days?: number
  analysis_type?: 'progress' | 'difficulty' | 'engagement' | 'comprehensive'
  analysis_period?: 'monthly' | 'weekly' | 'semester'
}

// 后端实际返回的数据结构
export interface LearningAnalysisResult {
  analysis_metadata: {
    class_id: number
    course_id: number
    analysis_period_days: number
    analysis_timestamp: string
    data_quality_score: number
  }
  multi_dimensional_data: Record<string, any>
  ai_analysis: Record<string, any>
  prediction_results: Record<string, any>
  risk_assessment: {
    risk_students: Array<{
      student_id: number
      risk_level: 'low' | 'medium' | 'high'
      risk_factors: string[]
      recommendations: string[]
    }>
    warning_indicators: string[]
  }
  personalized_recommendations: Record<string, any>
  overall_insights: Record<string, any>
}

// 为了向后兼容，保留旧的接口定义
export interface LegacyLearningAnalysisResult {
  class_analysis: {
    overall_progress: number
    knowledge_mastery_distribution: Record<string, number>
    common_issues: string[]
    learning_effectiveness: number
  }
  individual_analysis: Array<{
    student_id: number
    student_name: string
    ability_assessment: number
    learning_trajectory: string[]
    progress_trend: 'improving' | 'stable' | 'declining'
    personalized_needs: string[]
  }>
  comparative_analysis: {
    class_ranking: number
    performance_comparison: Record<string, number>
    optimization_opportunities: string[]
  }
  alerts: Array<{
    type: 'attendance' | 'performance' | 'engagement'
    severity: 'low' | 'medium' | 'high'
    student_ids: number[]
    description: string
    recommendations: string[]
  }>
}

// 教学调整相关类型
export interface TeachingAdjustmentRequest {
  class_id: number
  course_id: number
  lesson_plan_id?: number
  adjustment_focus: 'vocabulary' | 'grammar' | 'reading' | 'listening' | 'comprehensive'
  adjustment_type?: 'content' | 'difficulty' | 'method' | 'resource' | 'time'
  priority?: 'high' | 'medium' | 'low'
}

// 后端实际返回的教学调整数据结构
export interface TeachingAdjustmentResult {
  adjustment_metadata: {
    class_id: number
    course_id: number
    lesson_plan_id?: number
    teacher_id?: number
    generation_timestamp: string
    analysis_confidence: number
  }
  learning_analysis_summary: Record<string, any>
  adjustment_suggestions: {
    content_adjustments: {
      focus_areas: string[]
      reduce_emphasis: string[]
      add_content: string[]
      content_sequence_changes: string[]
    }
    difficulty_adjustments: {
      overall_difficulty: string
      specific_adjustments: Array<{
        topic: string
        current_level: string
        recommended_level: string
        reason: string
      }>
    }
    method_adjustments: {
      recommended_methods: string[]
      discouraged_methods: string[]
      interactive_activities: string[]
      assessment_methods: string[]
    }
    pacing_adjustments: {
      overall_pace: string
      time_allocation_changes: Array<{
        topic: string
        current_time: string
        recommended_time: string
        reason: string
      }>
    }
    differentiated_instruction: {
      high_achievers: {
        strategies: string[]
        additional_challenges: string[]
      }
      average_students: {
        strategies: string[]
        support_methods: string[]
      }
      struggling_students: {
        strategies: string[]
        remediation_plans: string[]
      }
    }
    implementation_priority: Array<{
      adjustment_type: string
      priority: string
      urgency: string
      expected_impact: string
    }>
  }
  resource_recommendations: Record<string, any>
  implementation_plan: Record<string, any>
  effectiveness_prediction: Record<string, any>
  priority_actions: Array<{
    action: string
    priority: number
    urgency: string
    expected_impact: string
  }>
}

// 为了向后兼容，保留旧的接口定义
export interface LegacyTeachingAdjustmentResult {
  content_adjustments: Array<{
    section: string
    current_content: string
    suggested_content: string
    reasoning: string
    implementation_difficulty: 'easy' | 'medium' | 'hard'
  }>
  difficulty_adjustments: Array<{
    topic: string
    current_difficulty: number
    suggested_difficulty: number
    adjustment_strategy: string
  }>
  method_adjustments: Array<{
    activity_type: string
    current_method: string
    suggested_method: string
    expected_improvement: string
  }>
  resource_recommendations: Array<{
    resource_type: 'textbook' | 'exercise' | 'multimedia' | 'tool'
    resource_name: string
    usage_scenario: string
    effectiveness_score: number
  }>
  time_allocations: Array<{
    topic: string
    current_time: number
    suggested_time: number
    justification: string
  }>
  personalized_suggestions: Array<{
    student_group: string
    specific_adjustments: string[]
    implementation_notes: string
  }>
}

// 协作相关类型
export interface CollaborationSessionRequest {
  resource_type: string
  resource_id: number
  collaboration_settings?: Record<string, any>
}

export interface CollaborationJoinRequest {
  session_id: string
  requested_permissions?: string[]
}

// 推荐系统类型
export interface IntelligentRecommendationRequest {
  recommendation_type: 'learning_path' | 'content_recommendation'
  context: Record<string, any>
}

// 效果跟踪类型
export interface EffectTrackingRequest {
  training_type?: string
  period_days?: number
  comparison_groups?: string[]
}

// ==================== API 实现 ====================

// 1. AI自动学情分析 API
export const learningAnalysisApi = {
  // 基础学情分析
  analyzeLearning: async (request: LearningAnalysisRequest): Promise<LearningAnalysisResult> => {
    const response = await apiClient.post('/api/v1/ai/ai/learning-analysis/analyze', request)
    return response.data
  },

  // 综合学情分析（增强版）
  comprehensiveAnalysis: async (
    request: LearningAnalysisRequest
  ): Promise<LearningAnalysisResult> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/learning-analysis/comprehensive',
      request
    )
    return response.data.analysis_result
  },
}

// 2. 教学调整建议 API
export const teachingAdjustmentApi = {
  // 生成教学调整建议
  generateAdjustments: async (
    request: TeachingAdjustmentRequest
  ): Promise<TeachingAdjustmentResult> => {
    const response = await apiClient.post('/api/v1/ai/ai/teaching-adjustments/generate', request)
    return response.data
  },

  // 综合教学调整（增强版）
  comprehensiveAdjustment: async (
    request: TeachingAdjustmentRequest
  ): Promise<TeachingAdjustmentResult> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/teaching-adjustment/comprehensive',
      request
    )
    return response.data.adjustment_result
  },
}

// 3. 协作管理 API
export const collaborationApi = {
  // 创建协作会话
  createSession: async (request: CollaborationSessionRequest): Promise<any> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/collaboration/create-session',
      request
    )
    return response.data
  },

  // 加入协作会话
  joinSession: async (sessionId: string, request: CollaborationJoinRequest): Promise<any> => {
    const response = await apiClient.post(
      `/api/v1/ai/enhanced-teaching/collaboration/join-session?session_id=${sessionId}`,
      request
    )
    return response.data
  },

  // 处理协作编辑
  handleEdit: async (sessionId: string, editOperation: any): Promise<any> => {
    const response = await apiClient.post(
      `/api/v1/ai/enhanced-teaching/collaboration/edit?session_id=${sessionId}`,
      {
        edit_operation: editOperation,
      }
    )
    return response.data
  },
}

// 4. 智能推荐 API
export const recommendationApi = {
  // 获取智能推荐
  getIntelligentRecommendations: async (
    request: IntelligentRecommendationRequest
  ): Promise<any> => {
    const response = await apiClient.post(
      '/api/v1/ai/enhanced-teaching/recommendations/intelligent',
      request
    )
    return response.data
  },
}

// 5. 系统状态和健康检查 API
export const systemApi = {
  // 系统健康检查
  healthCheck: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/ai/enhanced-teaching/system/health')
    return response.data
  },

  // 获取系统能力
  getCapabilities: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/ai/enhanced-teaching/system/capabilities')
    return response.data
  },

  // AI服务状态
  getAIStatus: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/ai/ai/status')
    return response.data
  },
}

// 6. 效果跟踪 API
export const effectTrackingApi = {
  // 学习进度分析
  getProgressAnalysis: async (request: EffectTrackingRequest): Promise<any> => {
    const response = await apiClient.get('/api/v1/training/analytics/progress', { params: request })
    return response.data
  },

  // 性能分析
  getPerformanceAnalysis: async (
    trainingType: string,
    request: EffectTrackingRequest
  ): Promise<any> => {
    const response = await apiClient.get(`/api/v1/training/analytics/performance/${trainingType}`, {
      params: request,
    })
    return response.data
  },

  // 对比分析
  getComparisonAnalysis: async (request: EffectTrackingRequest): Promise<any> => {
    const response = await apiClient.get('/api/v1/training/analytics/comparison', {
      params: request,
    })
    return response.data
  },

  // 模式分析
  getPatternAnalysis: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/training/analytics/patterns')
    return response.data
  },

  // 分析报告
  getAnalysisReport: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/training/analytics/report')
    return response.data
  },

  // 预测性分析
  getPredictiveAnalysis: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/analytics/monitoring/predictive/maintenance')
    return response.data
  },
}

// 7. 自适应学习 API
export const adaptiveLearningApi = {
  // 获取学习策略
  getLearningStrategy: async (studentId: number): Promise<any> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/learning-strategy/${studentId}`
    )
    return response.data
  },

  // 获取强化计划
  getReinforcementPlan: async (studentId: number): Promise<any> => {
    const response = await apiClient.get(
      `/api/v1/training/adaptive-learning/reinforcement-plan/${studentId}`
    )
    return response.data
  },
}
