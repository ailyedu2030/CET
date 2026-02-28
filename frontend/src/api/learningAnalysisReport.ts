/**
 * 需求24：AI智能分析与学情报告生成 API
 *
 * 包含以下功能：
 * 1. AI自动学情分析
 * 2. 个人学情分析报告
 * 3. 班级学情分析报告
 * 4. 智能批改系统
 * 5. 数据反馈机制
 * 6. 报告推送与交互
 * 7. 数据同步与存储
 */

import { apiClient } from './client'


// ==================== 核心类型定义 ====================

// 学生能力评估（五个维度）
export interface StudentAbilityAssessment {
  listening: number // 听力能力评分 (0-100)
  reading: number // 阅读能力评分 (0-100)
  writing: number // 写作能力评分 (0-100)
  translation: number // 翻译能力评分 (0-100)
  vocabulary: number // 词汇能力评分 (0-100)
  overall_score: number // 综合评分 (0-100)
  assessment_date: string // 评估日期
  confidence_level: number // 评估置信度 (0-1)
}

// 知识点掌握状态
export interface KnowledgePointMastery {
  knowledge_point_id: string
  knowledge_point_name: string
  category: string
  mastery_level: number // 掌握程度 (0-100)
  difficulty_level: 'basic' | 'intermediate' | 'advanced'
  last_practiced: string
  practice_count: number
  error_count: number
  improvement_trend: 'improving' | 'stable' | 'declining'
  estimated_time_to_master: number // 预计掌握时间（小时）
}

// 学习行为分析
export interface LearningBehaviorAnalysis {
  daily_study_time: number // 日均学习时长（分钟）
  study_frequency: number // 学习频率（次/周）
  best_study_time: string // 最佳学习时段
  attention_span: number // 注意力集中度（分钟）
  learning_consistency: number // 学习一致性评分 (0-100)
  preferred_difficulty: 'easy' | 'medium' | 'hard'
  learning_style: 'visual' | 'auditory' | 'kinesthetic' | 'mixed'
  engagement_level: number // 参与度评分 (0-100)
}

// 进步趋势预测
export interface ProgressTrendPrediction {
  prediction_period: number // 预测周期（天）
  predicted_scores: Array<{
    date: string
    listening: number
    reading: number
    writing: number
    translation: number
    vocabulary: number
    overall: number
    confidence: number
  }>
  trend_direction: 'improving' | 'stable' | 'declining'
  expected_improvement_rate: number // 预期提升率 (%/月)
  bottleneck_areas: string[] // 瓶颈领域
  breakthrough_probability: number // 突破概率 (0-1)
}

// 个性化建议
export interface PersonalizedRecommendations {
  priority_areas: Array<{
    area: string
    importance: 'high' | 'medium' | 'low'
    recommended_time: number // 建议投入时间（小时/周）
    specific_actions: string[]
  }>
  study_plan: Array<{
    week: number
    focus_areas: string[]
    daily_tasks: string[]
    expected_outcomes: string[]
  }>
  resource_recommendations: Array<{
    type: 'exercise' | 'reading' | 'video' | 'practice'
    title: string
    description: string
    difficulty: string
    estimated_time: number
  }>
  motivational_tips: string[]
}

// 风险预警
export interface RiskWarning {
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  risk_factors: Array<{
    factor: string
    severity: number // 严重程度 (0-100)
    description: string
    suggested_intervention: string
  }>
  early_warning_indicators: string[]
  intervention_recommendations: string[]
  follow_up_schedule: Array<{
    date: string
    action: string
    responsible_party: 'student' | 'teacher' | 'system'
  }>
}

// 个人学情分析报告
export interface PersonalLearningReport {
  student_id: number
  student_name: string
  report_date: string
  report_period: {
    start_date: string
    end_date: string
  }
  ability_assessment: StudentAbilityAssessment
  knowledge_mastery: KnowledgePointMastery[]
  behavior_analysis: LearningBehaviorAnalysis
  progress_prediction: ProgressTrendPrediction
  recommendations: PersonalizedRecommendations
  risk_warning: RiskWarning
  summary: {
    strengths: string[]
    weaknesses: string[]
    key_insights: string[]
    next_steps: string[]
  }
}

// 班级整体水平评估
export interface ClassOverallAssessment {
  class_id: number
  class_name: string
  total_students: number
  assessment_date: string
  average_scores: StudentAbilityAssessment
  score_distribution: Array<{
    score_range: string
    student_count: number
    percentage: number
  }>
  class_ranking: {
    position: number
    total_classes: number
    percentile: number
  }
  improvement_rate: number // 班级整体提升率 (%/月)
}

// 知识点掌握分析（班级维度）
export interface ClassKnowledgeMasteryAnalysis {
  knowledge_points: Array<{
    knowledge_point_id: string
    knowledge_point_name: string
    category: string
    class_mastery_rate: number // 班级掌握率 (0-100)
    difficulty_level: string
    students_mastered: number
    students_struggling: number
    common_errors: string[]
    teaching_suggestions: string[]
  }>
  weak_areas: string[] // 共性薄弱环节
  strong_areas: string[] // 共性优势环节
  mastery_distribution: Record<string, number> // 掌握程度分布
}

// 学习进度监控（班级维度）
export interface ClassProgressMonitoring {
  overall_progress: number // 整体进度 (0-100)
  on_track_students: number
  behind_students: number
  ahead_students: number
  progress_trends: Array<{
    week: number
    average_progress: number
    completion_rate: number
  }>
  lagging_students: Array<{
    student_id: number
    student_name: string
    current_progress: number
    expected_progress: number
    gap: number
    risk_level: string
  }>
}

// 教学效果评估
export interface TeachingEffectivenessEvaluation {
  teaching_methods: Array<{
    method: string
    effectiveness_score: number // 有效性评分 (0-100)
    student_feedback: number
    learning_outcomes: number
    engagement_level: number
  }>
  content_effectiveness: Array<{
    topic: string
    comprehension_rate: number
    retention_rate: number
    application_success: number
  }>
  correlation_analysis: {
    teaching_time_vs_performance: number
    difficulty_vs_engagement: number
    method_vs_outcomes: number
  }
  improvement_suggestions: string[]
}

// 差异化分析
export interface DifferentiatedAnalysis {
  ability_tiers: Array<{
    tier: 'high' | 'medium' | 'low'
    student_count: number
    characteristics: string[]
    learning_needs: string[]
    recommended_strategies: string[]
  }>
  learning_style_distribution: Record<string, number>
  pace_preferences: Record<string, number>
  support_needs: Array<{
    need_type: string
    student_count: number
    intervention_strategies: string[]
  }>
}

// 班级学情分析报告
export interface ClassLearningReport {
  class_id: number
  class_name: string
  teacher_id: number
  teacher_name: string
  report_date: string
  report_period: {
    start_date: string
    end_date: string
  }
  overall_assessment: ClassOverallAssessment
  knowledge_mastery: ClassKnowledgeMasteryAnalysis
  progress_monitoring: ClassProgressMonitoring
  teaching_effectiveness: TeachingEffectivenessEvaluation
  differentiated_analysis: DifferentiatedAnalysis
  improvement_recommendations: Array<{
    area: string
    priority: 'high' | 'medium' | 'low'
    specific_actions: string[]
    expected_outcomes: string[]
    timeline: string
  }>
  summary: {
    key_achievements: string[]
    main_challenges: string[]
    strategic_recommendations: string[]
  }
}

// 智能批改结果
export interface IntelligentGradingResult {
  submission_id: string
  student_id: number
  question_id: string
  question_type: 'objective' | 'subjective'
  grading_model: 'lightweight' | 'advanced'
  response_time: number // 响应时间（毫秒）
  scores: {
    content_accuracy: number // 内容准确性 (0-100)
    language_expression: number // 语言表达 (0-100)
    logical_structure: number // 逻辑结构 (0-100)
    creativity: number // 创新性 (0-100)
    overall_score: number // 总分 (0-100)
  }
  detailed_feedback: {
    error_annotations: Array<{
      position: number
      error_type: string
      description: string
      suggestion: string
    }>
    improvement_suggestions: string[]
    reference_answer: string
    knowledge_point_links: string[]
  }
  consistency_score: number // 批改一致性评分 (0-100)
  learning_trajectory: {
    answer_strategy: string
    thinking_process: string[]
    skill_demonstration: string[]
    areas_for_improvement: string[]
  }
}

// 数据反馈机制
export interface DataFeedbackMechanism {
  real_time_data_flow: {
    last_update: string
    processing_time: number // 处理时间（毫秒）
    data_freshness: number // 数据新鲜度（秒）
    sync_status: 'synced' | 'syncing' | 'error'
  }
  multi_dimensional_stats: {
    by_time: Record<string, number>
    by_knowledge_point: Record<string, number>
    by_question_type: Record<string, number>
    by_difficulty: Record<string, number>
  }
  visualization_data: {
    heatmap_data: Array<Array<number>>
    progress_curves: Array<{
      date: string
      value: number
    }>
    ability_radar: Record<string, number>
    comparison_charts: Array<{
      category: string
      current_class: number
      other_classes: number
    }>
  }
  trend_analysis: {
    learning_trends: Array<{
      trend_type: string
      direction: 'up' | 'down' | 'stable'
      magnitude: number
      confidence: number
    }>
    bottleneck_prediction: string[]
    breakthrough_opportunities: string[]
  }
  anomaly_detection: {
    detected_anomalies: Array<{
      type: string
      severity: 'low' | 'medium' | 'high'
      description: string
      affected_students: number[]
      recommended_actions: string[]
    }>
    monitoring_alerts: string[]
  }
}

// 报告推送配置
export interface ReportPushConfiguration {
  push_schedule: {
    daily_brief: boolean
    weekly_detailed: boolean
    monthly_comprehensive: boolean
    custom_schedule: string[]
  }
  recipients: Array<{
    user_id: number
    user_type: 'teacher' | 'admin' | 'parent'
    notification_preferences: {
      email: boolean
      sms: boolean
      in_app: boolean
      push_notification: boolean
    }
  }>
  content_filters: {
    include_personal_reports: boolean
    include_class_reports: boolean
    include_comparisons: boolean
    include_recommendations: boolean
    minimum_priority: 'low' | 'medium' | 'high'
  }
}

// 交互式报告
export interface InteractiveReport {
  report_id: string
  report_type: 'personal' | 'class' | 'comparative'
  interactive_elements: {
    drill_down_enabled: boolean
    filter_options: string[]
    comparison_tools: boolean
    export_options: string[]
  }
  mobile_optimization: {
    responsive_design: boolean
    touch_friendly: boolean
    offline_access: boolean
  }
  real_time_updates: boolean
  collaboration_features: {
    comments_enabled: boolean
    sharing_options: string[]
    annotation_tools: boolean
  }
}

// API请求和响应类型
export interface LearningReportAnalysisRequest {
  student_id?: number
  class_id?: number
  analysis_type: 'personal' | 'class' | 'comparative'
  time_period: {
    start_date: string
    end_date: string
  }
  include_predictions?: boolean
  include_recommendations?: boolean
  detail_level: 'summary' | 'detailed' | 'comprehensive'
}

export interface BatchAnalysisRequest {
  student_ids: number[]
  class_ids: number[]
  analysis_types: string[]
  time_period: {
    start_date: string
    end_date: string
  }
  parallel_processing: boolean
}

export interface ReportExportRequest {
  report_id: string
  format: 'pdf' | 'excel' | 'json' | 'csv'
  include_charts: boolean
  include_raw_data: boolean
  language: 'zh' | 'en'
}

export interface DataSyncStatus {
  last_sync: string
  sync_frequency: number // 同步频率（秒）
  pending_updates: number
  sync_health: 'healthy' | 'warning' | 'error'
  data_integrity_score: number // 数据完整性评分 (0-100)
  retention_policy: {
    active_data_months: number
    archived_data_years: number
    deletion_schedule: string
  }
}

// ==================== API 实现 ====================

// 1. AI自动学情分析 API
export const aiLearningAnalysisApi = {
  // 个人维度分析（使用现有的综合分析端点）
  analyzePersonalLearning: async (
    studentId: number,
    params?: {
      analysis_period_days?: number
      include_predictions?: boolean
      detail_level?: 'summary' | 'detailed' | 'comprehensive'
    }
  ): Promise<PersonalLearningReport> => {
    try {
      // 构造请求数据以匹配后端期望的格式
      const requestData = {
        student_id: studentId,
        analysis_type: 'personal',
        analysis_period: params?.analysis_period_days
          ? `${params.analysis_period_days}days`
          : '30days',
        include_predictions: params?.include_predictions ?? true,
        detail_level: params?.detail_level ?? 'comprehensive',
      }

      const response = await apiClient.post(
        '/api/v1/ai/enhanced-teaching/learning-analysis/comprehensive',
        requestData
      )
      return response.data.analysis_result
    } catch (error) {
      throw new Error(`个人学情分析失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  },

  // 班级维度分析（使用现有的综合分析端点）
  analyzeClassLearning: async (
    classId: number,
    params?: {
      analysis_period_days?: number
      include_comparisons?: boolean
      detail_level?: 'summary' | 'detailed' | 'comprehensive'
    }
  ): Promise<ClassLearningReport> => {
    try {
      const requestData = {
        class_id: classId,
        analysis_type: 'class',
        analysis_period: params?.analysis_period_days
          ? `${params.analysis_period_days}days`
          : '30days',
        include_comparisons: params?.include_comparisons ?? true,
        detail_level: params?.detail_level ?? 'comprehensive',
      }

      const response = await apiClient.post(
        '/api/v1/ai/enhanced-teaching/learning-analysis/comprehensive',
        requestData
      )
      return response.data.analysis_result
    } catch (error) {
      throw new Error(`班级学情分析失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  },

  // 多维度数据融合分析
  comprehensiveAnalysis: async (
    request: LearningReportAnalysisRequest
  ): Promise<{
    personal_reports: PersonalLearningReport[]
    class_reports: ClassLearningReport[]
    comparative_analysis: {
      cross_class_comparison: Record<string, unknown>
      temporal_trends: Record<string, unknown>
      performance_correlations: Record<string, unknown>
    }
    analysis_metadata: {
      processing_time: number
      accuracy_score: number
      confidence_level: number
    }
  }> => {
    try {
      const response = await apiClient.post(
        '/api/v1/ai/enhanced-teaching/learning-analysis/comprehensive',
        request
      )
      return response.data
    } catch (error) {
      throw new Error(`综合学情分析失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  },

  // 批量分析
  batchAnalysis: async (
    request: BatchAnalysisRequest
  ): Promise<{
    analysis_results: Array<PersonalLearningReport | ClassLearningReport>
    processing_summary: {
      total_processed: number
      successful: number
      failed: number
      processing_time: number
    }
  }> => {
    const response = await apiClient.post('/api/v1/ai/learning-analysis/batch', request)
    return response.data
  },

  // 实时更新分析数据
  updateAnalysisData: async (
    studentId: number
  ): Promise<{
    update_status: 'success' | 'partial' | 'failed'
    updated_components: string[]
    next_update: string
  }> => {
    const response = await apiClient.post(`/api/v1/ai/learning-analysis/update/${studentId}`)
    return response.data
  },
}

// 2. 个人学情分析报告 API
// 注意：以下大部分API端点为占位符，等待后端实现
// 实际使用时需要根据后端API调整路径和错误处理
export const personalReportApi = {
  // 获取个人学情报告
  getPersonalReport: async (
    studentId: number,
    reportId?: string
  ): Promise<PersonalLearningReport> => {
    const url = reportId
      ? `/api/v1/ai/reports/personal/${studentId}/${reportId}`
      : `/api/v1/ai/reports/personal/${studentId}/latest`
    const response = await apiClient.get(url)
    return response.data
  },

  // 生成个人学情报告
  generatePersonalReport: async (
    studentId: number,
    params: {
      time_period: { start_date: string; end_date: string }
      include_predictions: boolean
      include_recommendations: boolean
    }
  ): Promise<{
    report_id: string
    generation_status: 'processing' | 'completed' | 'failed'
    estimated_completion: string
  }> => {
    const response = await apiClient.post(
      `/api/v1/ai/reports/personal/${studentId}/generate`,
      params
    )
    return response.data
  },

  // 获取能力评估历史
  getAbilityAssessmentHistory: async (
    studentId: number,
    params?: {
      months?: number
      include_predictions?: boolean
    }
  ): Promise<{
    assessments: StudentAbilityAssessment[]
    trends: {
      listening_trend: number
      reading_trend: number
      writing_trend: number
      translation_trend: number
      vocabulary_trend: number
    }
    milestones: Array<{
      date: string
      achievement: string
      score_improvement: number
    }>
  }> => {
    const response = await apiClient.get(
      `/api/v1/ai/reports/personal/${studentId}/ability-history`,
      { params }
    )
    return response.data
  },

  // 获取学习行为分析
  getLearningBehaviorAnalysis: async (studentId: number): Promise<LearningBehaviorAnalysis> => {
    const response = await apiClient.get(
      `/api/v1/ai/reports/personal/${studentId}/behavior-analysis`
    )
    return response.data
  },

  // 获取个性化建议
  getPersonalizedRecommendations: async (
    studentId: number,
    params?: {
      focus_areas?: string[]
      time_constraint?: number
      difficulty_preference?: 'gradual' | 'challenging'
    }
  ): Promise<PersonalizedRecommendations> => {
    const response = await apiClient.get(
      `/api/v1/ai/reports/personal/${studentId}/recommendations`,
      { params }
    )
    return response.data
  },

  // 获取风险预警
  getRiskWarning: async (studentId: number): Promise<RiskWarning> => {
    const response = await apiClient.get(`/api/v1/ai/reports/personal/${studentId}/risk-warning`)
    return response.data
  },
}

// 3. 班级学情分析报告 API
export const classReportApi = {
  // 获取班级学情报告
  getClassReport: async (classId: number, reportId?: string): Promise<ClassLearningReport> => {
    const url = reportId
      ? `/api/v1/ai/reports/class/${classId}/${reportId}`
      : `/api/v1/ai/reports/class/${classId}/latest`
    const response = await apiClient.get(url)
    return response.data
  },

  // 生成班级学情报告
  generateClassReport: async (
    classId: number,
    params: {
      time_period: { start_date: string; end_date: string }
      include_individual_analysis: boolean
      include_teaching_effectiveness: boolean
    }
  ): Promise<{
    report_id: string
    generation_status: 'processing' | 'completed' | 'failed'
    estimated_completion: string
  }> => {
    const response = await apiClient.post(`/api/v1/ai/reports/class/${classId}/generate`, params)
    return response.data
  },

  // 获取班级整体评估
  getClassOverallAssessment: async (classId: number): Promise<ClassOverallAssessment> => {
    const response = await apiClient.get(`/api/v1/ai/reports/class/${classId}/overall-assessment`)
    return response.data
  },

  // 获取知识点掌握分析
  getKnowledgeMasteryAnalysis: async (
    classId: number,
    params?: {
      knowledge_point_categories?: string[]
      difficulty_levels?: string[]
    }
  ): Promise<ClassKnowledgeMasteryAnalysis> => {
    const response = await apiClient.get(`/api/v1/ai/reports/class/${classId}/knowledge-mastery`, {
      params,
    })
    return response.data
  },

  // 获取学习进度监控
  getProgressMonitoring: async (classId: number): Promise<ClassProgressMonitoring> => {
    const response = await apiClient.get(`/api/v1/ai/reports/class/${classId}/progress-monitoring`)
    return response.data
  },

  // 获取教学效果评估
  getTeachingEffectiveness: async (
    classId: number,
    teacherId: number
  ): Promise<TeachingEffectivenessEvaluation> => {
    const response = await apiClient.get(
      `/api/v1/ai/reports/class/${classId}/teaching-effectiveness/${teacherId}`
    )
    return response.data
  },

  // 获取差异化分析
  getDifferentiatedAnalysis: async (classId: number): Promise<DifferentiatedAnalysis> => {
    const response = await apiClient.get(
      `/api/v1/ai/reports/class/${classId}/differentiated-analysis`
    )
    return response.data
  },

  // 比较多个班级
  compareClasses: async (
    classIds: number[],
    params?: {
      comparison_metrics?: string[]
      time_period?: { start_date: string; end_date: string }
    }
  ): Promise<{
    comparison_results: Array<{
      class_id: number
      class_name: string
      metrics: Record<string, number>
      ranking: number
    }>
    insights: string[]
    recommendations: string[]
  }> => {
    const response = await apiClient.post('/api/v1/ai/reports/class/compare', {
      class_ids: classIds,
      ...params,
    })
    return response.data
  },
}

// 4. 智能批改系统 API（使用现有的grading API）
export const intelligentGradingApi = {
  // 提交作业进行智能批改（使用现有的grading API）
  submitForGrading: async (data: {
    student_id: number
    question_id: string
    answer_content: string
    question_type: 'objective' | 'subjective'
    submission_metadata?: Record<string, unknown>
  }): Promise<{
    submission_id: string
    estimated_grading_time: number
    grading_status: 'queued' | 'processing' | 'completed'
  }> => {
    try {
      // 使用现有的grading API接口
      const gradingRequest: GradingRequest = {
        question_id: parseInt(data.question_id),
        user_answer: {
          text: data.answer_content,
        },
        context: data.submission_metadata,
      }

      await apiClient.post('/api/v1/ai/grading/grade', gradingRequest)

      // 转换响应格式以匹配期望的接口
      return {
        submission_id: `${data.student_id}_${data.question_id}_${Date.now()}`,
        estimated_grading_time: 2000, // 2秒估计时间
        grading_status: 'completed' as const,
      }
    } catch (error) {
      throw new Error(`智能批改提交失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  },

  // 获取批改结果
  getGradingResult: async (submissionId: string): Promise<IntelligentGradingResult> => {
    const response = await apiClient.get(`/api/v1/ai/grading/result/${submissionId}`)
    return response.data
  },

  // 批量批改
  batchGrading: async (
    submissions: Array<{
      student_id: number
      question_id: string
      answer_content: string
      question_type: 'objective' | 'subjective'
    }>
  ): Promise<{
    batch_id: string
    total_submissions: number
    estimated_completion_time: number
  }> => {
    const response = await apiClient.post('/api/v1/ai/grading/batch', { submissions })
    return response.data
  },

  // 获取批改历史
  getGradingHistory: async (
    studentId: number,
    params?: {
      limit?: number
      offset?: number
      question_type?: 'objective' | 'subjective'
      date_range?: { start: string; end: string }
    }
  ): Promise<{
    grading_results: IntelligentGradingResult[]
    total_count: number
    statistics: {
      average_score: number
      improvement_trend: number
      common_error_types: string[]
    }
  }> => {
    const response = await apiClient.get(`/api/v1/ai/grading/history/${studentId}`, { params })
    return response.data
  },

  // 获取批改质量统计
  getGradingQualityStats: async (params?: {
    time_period?: { start: string; end: string }
    question_types?: string[]
  }): Promise<{
    consistency_scores: Array<{
      question_type: string
      consistency_score: number
      sample_size: number
    }>
    response_times: Array<{
      model_type: 'lightweight' | 'advanced'
      average_response_time: number
      percentile_95: number
    }>
    accuracy_metrics: {
      objective_accuracy: number
      subjective_correlation: number
      human_agreement_rate: number
    }
  }> => {
    const response = await apiClient.get('/api/v1/ai/grading/quality-stats', { params })
    return response.data
  },
}

// 5. 数据反馈机制 API
export const dataFeedbackApi = {
  // 获取实时数据流状态
  getRealTimeDataFlow: async (
    studentId?: number,
    classId?: number
  ): Promise<DataFeedbackMechanism> => {
    const params = { student_id: studentId, class_id: classId }
    const response = await apiClient.get('/api/v1/ai/data-feedback/real-time', { params })
    return response.data
  },

  // 获取多维度统计数据
  getMultiDimensionalStats: async (params: {
    entity_type: 'student' | 'class'
    entity_id: number
    dimensions: string[]
    time_range: { start: string; end: string }
  }): Promise<{
    statistics: Record<string, Record<string, number>>
    aggregations: Record<string, number>
    trends: Array<{
      dimension: string
      trend_direction: 'up' | 'down' | 'stable'
      change_rate: number
    }>
  }> => {
    const response = await apiClient.post(
      '/api/v1/ai/data-feedback/multi-dimensional-stats',
      params
    )
    return response.data
  },

  // 获取可视化数据
  getVisualizationData: async (params: {
    chart_type: 'heatmap' | 'progress_curve' | 'radar' | 'comparison'
    entity_type: 'student' | 'class'
    entity_id: number
    time_range?: { start: string; end: string }
  }): Promise<{
    chart_data: Record<string, unknown>
    chart_config: {
      title: string
      axes_labels: string[]
      color_scheme: string[]
      interactive_features: string[]
    }
    data_freshness: number
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-feedback/visualization', params)
    return response.data
  },

  // 获取趋势分析
  getTrendAnalysis: async (params: {
    entity_type: 'student' | 'class'
    entity_id: number
    analysis_period: number // 天数
    trend_types: string[]
  }): Promise<{
    trends: Array<{
      trend_type: string
      direction: 'up' | 'down' | 'stable'
      magnitude: number
      confidence: number
      key_factors: string[]
    }>
    predictions: Array<{
      metric: string
      predicted_values: Array<{ date: string; value: number; confidence: number }>
    }>
    insights: string[]
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-feedback/trend-analysis', params)
    return response.data
  },

  // 获取异常检测结果
  getAnomalyDetection: async (params: {
    entity_type: 'student' | 'class'
    entity_id: number
    detection_sensitivity: 'low' | 'medium' | 'high'
  }): Promise<{
    anomalies: Array<{
      type: string
      severity: 'low' | 'medium' | 'high'
      description: string
      detected_at: string
      affected_metrics: string[]
      recommended_actions: string[]
    }>
    monitoring_status: {
      active_monitors: number
      last_check: string
      next_check: string
    }
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-feedback/anomaly-detection', params)
    return response.data
  },
}

// 6. 报告推送与交互 API
export const reportPushApi = {
  // 配置报告推送
  configurePush: async (
    config: ReportPushConfiguration
  ): Promise<{
    configuration_id: string
    status: 'active' | 'inactive'
    next_push_time: string
  }> => {
    const response = await apiClient.post('/api/v1/ai/reports/push/configure', config)
    return response.data
  },

  // 获取推送配置
  getPushConfiguration: async (userId: number): Promise<ReportPushConfiguration> => {
    const response = await apiClient.get(`/api/v1/ai/reports/push/configuration/${userId}`)
    return response.data
  },

  // 手动触发报告推送
  triggerPush: async (params: {
    report_type: 'personal' | 'class' | 'comparative'
    entity_ids: number[]
    recipients: number[]
    push_channels: string[]
  }): Promise<{
    push_id: string
    status: 'sent' | 'pending' | 'failed'
    delivery_summary: Record<string, number>
  }> => {
    const response = await apiClient.post('/api/v1/ai/reports/push/trigger', params)
    return response.data
  },

  // 获取交互式报告
  getInteractiveReport: async (
    reportId: string,
    params?: {
      interaction_level: 'basic' | 'advanced'
      mobile_optimized: boolean
    }
  ): Promise<InteractiveReport> => {
    const response = await apiClient.get(`/api/v1/ai/reports/interactive/${reportId}`, { params })
    return response.data
  },

  // 导出报告
  exportReport: async (request: ReportExportRequest): Promise<Blob> => {
    const response = await apiClient.post('/api/v1/ai/reports/export', request, {
      responseType: 'blob',
    })
    return response.data
  },

  // 获取推送历史
  getPushHistory: async (
    userId: number,
    params?: {
      limit?: number
      offset?: number
      date_range?: { start: string; end: string }
    }
  ): Promise<{
    push_records: Array<{
      push_id: string
      report_type: string
      sent_at: string
      delivery_status: Record<string, string>
      recipient_count: number
    }>
    total_count: number
    delivery_statistics: {
      success_rate: number
      average_delivery_time: number
      common_failures: string[]
    }
  }> => {
    const response = await apiClient.get(`/api/v1/ai/reports/push/history/${userId}`, { params })
    return response.data
  },
}

// 7. 数据同步与存储 API
export const dataSyncApi = {
  // 获取数据同步状态
  getSyncStatus: async (params?: {
    entity_type?: 'student' | 'class' | 'system'
    entity_id?: number
  }): Promise<DataSyncStatus> => {
    const response = await apiClient.get('/api/v1/ai/data-sync/status', { params })
    return response.data
  },

  // 触发实时同步
  triggerRealTimeSync: async (params: {
    entity_type: 'student' | 'class'
    entity_id: number
    sync_components: string[]
    priority: 'low' | 'medium' | 'high'
  }): Promise<{
    sync_id: string
    status: 'initiated' | 'in_progress' | 'completed' | 'failed'
    estimated_completion: string
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-sync/real-time', params)
    return response.data
  },

  // 配置批量同步
  configureBatchSync: async (config: {
    sync_frequency: number // 分钟
    batch_size: number
    sync_components: string[]
    retry_policy: {
      max_retries: number
      retry_interval: number
    }
  }): Promise<{
    configuration_id: string
    next_sync_time: string
    status: 'active' | 'inactive'
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-sync/batch/configure', config)
    return response.data
  },

  // 检查数据完整性
  checkDataIntegrity: async (params: {
    entity_type: 'student' | 'class' | 'system'
    entity_id?: number
    check_components: string[]
  }): Promise<{
    integrity_score: number // 0-100
    issues_found: Array<{
      component: string
      issue_type: string
      severity: 'low' | 'medium' | 'high'
      description: string
      suggested_fix: string
    }>
    last_check: string
    next_check: string
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-sync/integrity-check', params)
    return response.data
  },

  // 数据恢复
  recoverData: async (params: {
    entity_type: 'student' | 'class'
    entity_id: number
    recovery_point: string // ISO date string
    components_to_recover: string[]
  }): Promise<{
    recovery_id: string
    status: 'initiated' | 'in_progress' | 'completed' | 'failed'
    recovered_components: string[]
    estimated_completion: string
  }> => {
    const response = await apiClient.post('/api/v1/ai/data-sync/recover', params)
    return response.data
  },

  // 获取数据保留策略
  getRetentionPolicy: async (): Promise<{
    active_data_retention: number // 月数
    archived_data_retention: number // 年数
    deletion_schedule: Array<{
      data_type: string
      retention_period: number
      next_deletion: string
    }>
    compliance_status: 'compliant' | 'warning' | 'violation'
  }> => {
    const response = await apiClient.get('/api/v1/ai/data-sync/retention-policy')
    return response.data
  },

  // 更新数据保留策略
  updateRetentionPolicy: async (policy: {
    active_data_months: number
    archived_data_years: number
    auto_deletion_enabled: boolean
    compliance_requirements: string[]
  }): Promise<{
    policy_id: string
    status: 'updated' | 'pending_approval' | 'rejected'
    effective_date: string
  }> => {
    const response = await apiClient.put('/api/v1/ai/data-sync/retention-policy', policy)
    return response.data
  },

  // 获取同步历史
  getSyncHistory: async (params?: {
    limit?: number
    offset?: number
    sync_type?: 'real_time' | 'batch'
    status?: 'completed' | 'failed' | 'in_progress'
    date_range?: { start: string; end: string }
  }): Promise<{
    sync_records: Array<{
      sync_id: string
      sync_type: 'real_time' | 'batch'
      entity_type: string
      entity_id: number
      started_at: string
      completed_at?: string
      status: string
      components_synced: string[]
      data_volume: number // bytes
      error_message?: string
    }>
    total_count: number
    performance_metrics: {
      average_sync_time: number
      success_rate: number
      data_throughput: number // bytes/second
    }
  }> => {
    const response = await apiClient.get('/api/v1/ai/data-sync/history', { params })
    return response.data
  },
}

// 统一导出所有API
export const learningAnalysisReportApi = {
  aiLearningAnalysis: aiLearningAnalysisApi,
  personalReport: personalReportApi,
  classReport: classReportApi,
  intelligentGrading: intelligentGradingApi,
  dataFeedback: dataFeedbackApi,
  reportPush: reportPushApi,
  dataSync: dataSyncApi,
}
