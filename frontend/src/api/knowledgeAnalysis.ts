import { apiClient } from './client'

// 知识点掌握数据接口
export interface KnowledgePoint {
  id: string
  name: string
  category: string
  level: number
  parent_id?: string
  description: string
  mastery_score: number // 0-100
  practice_count: number
  correct_count: number
  last_practiced: string
  difficulty_level: 'easy' | 'medium' | 'hard'
  related_points: string[]
}

// 知识点薄弱环节分析接口
export interface WeaknessAnalysis {
  student_id: number
  analysis_date: string
  overall_mastery: number
  weak_points: Array<{
    knowledge_point: KnowledgePoint
    weakness_score: number // 0-100，越高越薄弱
    error_patterns: string[]
    recommended_actions: string[]
    priority_level: 'high' | 'medium' | 'low'
    estimated_improvement_time: string
  }>
  improvement_suggestions: string[]
  focus_areas: string[]
  next_review_date: string
}

// 热力图数据接口
export interface HeatmapData {
  knowledge_points: Array<{
    id: string
    name: string
    category: string
    x: number
    y: number
    value: number // 掌握程度 0-100
    color: string
    size: number
    metadata: {
      practice_count: number
      accuracy_rate: number
      last_practiced: string
      difficulty: string
    }
  }>
  categories: Array<{
    name: string
    color: string
    point_count: number
    average_mastery: number
  }>
  dimensions: {
    width: number
    height: number
    min_value: number
    max_value: number
  }
  filters: {
    time_range: string
    difficulty_levels: string[]
    categories: string[]
  }
}

// 知识点统计接口
export interface KnowledgeStats {
  total_points: number
  mastered_points: number
  weak_points: number
  improving_points: number
  mastery_distribution: Record<string, number>
  category_performance: Array<{
    category: string
    mastery_rate: number
    point_count: number
    trend: 'improving' | 'stable' | 'declining'
  }>
  recent_progress: Array<{
    date: string
    mastery_score: number
    points_practiced: number
  }>
}

export const knowledgeAnalysisApi = {
  // 获取学生知识点薄弱环节分析
  getWeaknessAnalysis: async (studentId: number, params?: {
    include_categories?: string[]
    min_weakness_score?: number
    limit?: number
  }): Promise<WeaknessAnalysis> => {
    const response = await apiClient.get(`/api/v1/ai/analysis/knowledge-points/${studentId}/weakness`, { params })
    return response.data
  },

  // 获取知识点掌握热力图数据
  getHeatmapData: async (studentId: number, params?: {
    time_range?: 'week' | 'month' | 'semester'
    categories?: string[]
    difficulty_levels?: string[]
    layout?: 'grid' | 'tree' | 'force'
  }): Promise<HeatmapData> => {
    const response = await apiClient.get(`/api/v1/ai/analysis/knowledge-points/${studentId}/heatmap`, { params })
    return response.data
  },

  // 获取知识点统计
  getKnowledgeStats: async (studentId: number, params?: {
    period?: 'week' | 'month' | 'semester'
  }): Promise<KnowledgeStats> => {
    const response = await apiClient.get(`/api/v1/ai/analysis/knowledge-points/${studentId}/stats`, { params })
    return response.data
  },

  // 获取所有知识点列表
  getAllKnowledgePoints: async (params?: {
    category?: string
    level?: number
    search?: string
    include_mastery?: boolean
    student_id?: number
  }): Promise<KnowledgePoint[]> => {
    const response = await apiClient.get('/api/v1/ai/analysis/knowledge-points', { params })
    return response.data
  },

  // 更新知识点掌握度
  updateKnowledgeMastery: async (data: {
    student_id: number
    knowledge_point_id: string
    mastery_score: number
    practice_result: {
      is_correct: boolean
      time_spent: number
      difficulty: string
    }
  }): Promise<{
    updated_mastery: number
    mastery_change: number
    next_review_date: string
  }> => {
    const response = await apiClient.post('/api/v1/ai/analysis/knowledge-points/update-mastery', data)
    return response.data
  },

  // 生成个性化学习路径
  generateLearningPath: async (studentId: number, data: {
    target_knowledge_points?: string[]
    time_constraint?: number // 天数
    difficulty_preference?: 'gradual' | 'challenging'
    focus_weak_points?: boolean
  }): Promise<{
    path_id: string
    learning_sequence: Array<{
      knowledge_point: KnowledgePoint
      order: number
      estimated_time: number
      prerequisites: string[]
      practice_recommendations: string[]
    }>
    total_estimated_time: number
    completion_date: string
  }> => {
    const response = await apiClient.post(`/api/v1/ai/analysis/knowledge-points/${studentId}/learning-path`, data)
    return response.data
  },

  // 比较学生知识点掌握情况
  compareStudents: async (studentIds: number[], params?: {
    knowledge_point_ids?: string[]
    categories?: string[]
  }): Promise<{
    comparison_data: Array<{
      student_id: number
      student_name: string
      knowledge_points: Array<{
        id: string
        name: string
        mastery_score: number
        rank: number
      }>
      overall_rank: number
      strengths: string[]
      weaknesses: string[]
    }>
    class_average: Record<string, number>
    insights: string[]
  }> => {
    const response = await apiClient.post('/api/v1/ai/analysis/knowledge-points/compare', {
      student_ids: studentIds,
      ...params,
    })
    return response.data
  },

  // 导出知识点分析报告
  exportAnalysisReport: async (studentId: number, params: {
    format: 'pdf' | 'excel' | 'json'
    include_heatmap?: boolean
    include_recommendations?: boolean
    time_range?: string
  }): Promise<Blob> => {
    const response = await apiClient.post(`/api/v1/ai/analysis/knowledge-points/${studentId}/export`, params, {
      responseType: 'blob',
    })
    return response.data
  },

  // 获取知识点关联关系
  getKnowledgeRelations: async (knowledgePointId: string): Promise<{
    prerequisites: KnowledgePoint[]
    dependents: KnowledgePoint[]
    related: KnowledgePoint[]
    difficulty_progression: KnowledgePoint[]
  }> => {
    const response = await apiClient.get(`/api/v1/ai/analysis/knowledge-points/${knowledgePointId}/relations`)
    return response.data
  },

  // 预测知识点掌握趋势
  predictMasteryTrend: async (studentId: number, knowledgePointIds: string[], params?: {
    prediction_days?: number
    include_interventions?: boolean
  }): Promise<{
    predictions: Array<{
      knowledge_point_id: string
      current_mastery: number
      predicted_mastery: Array<{
        date: string
        mastery_score: number
        confidence: number
      }>
      recommended_interventions: string[]
    }>
    overall_trend: 'improving' | 'stable' | 'declining'
    risk_points: string[]
  }> => {
    const response = await apiClient.post(`/api/v1/ai/analysis/knowledge-points/${studentId}/predict`, {
      knowledge_point_ids: knowledgePointIds,
      ...params,
    })
    return response.data
  },
}
