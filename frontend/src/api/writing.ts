/**
 * 需求26：英语四级写作标准库 - API接口
 *
 * 实现与后端写作API的完整对接
 */

import { apiClient } from './client'

// ==================== 基础类型定义 ====================

export enum WritingType {
  ARGUMENTATIVE = 'argumentative', // 议论文
  NARRATIVE = 'narrative', // 记叙文
  DESCRIPTIVE = 'descriptive', // 描述文
  EXPOSITORY = 'expository', // 说明文
  PRACTICAL = 'practical', // 应用文
}

export enum WritingDifficulty {
  BASIC = 'basic', // 基础级
  INTERMEDIATE = 'intermediate', // 中级
  ADVANCED = 'advanced', // 高级
  EXPERT = 'expert', // 专家级
}

export enum WritingScoreLevel {
  EXCELLENT = 'excellent', // 优秀 (13-15分)
  GOOD = 'good', // 良好 (10-12分)
  FAIR = 'fair', // 及格 (7-9分)
  POOR = 'poor', // 不及格 (0-6分)
}

// ==================== 写作模板相关 ====================

export interface WritingTemplate {
  id: number
  template_name: string
  writing_type: WritingType
  difficulty: WritingDifficulty
  template_structure: Record<string, any>
  opening_sentences: string[]
  transition_phrases: string[]
  conclusion_sentences: string[]
  example_essay?: string
  usage_instructions?: string
  key_phrases: string[]
  is_recommended: boolean
  usage_count: number
  average_score: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WritingTemplateCreate {
  template_name: string
  writing_type: WritingType
  difficulty: WritingDifficulty
  template_structure: Record<string, any>
  opening_sentences?: string[]
  transition_phrases?: string[]
  conclusion_sentences?: string[]
  example_essay?: string
  usage_instructions?: string
  key_phrases?: string[]
  is_recommended?: boolean
}

export interface WritingTemplateUpdate {
  template_name?: string
  writing_type?: WritingType
  difficulty?: WritingDifficulty
  template_structure?: Record<string, any>
  opening_sentences?: string[]
  transition_phrases?: string[]
  conclusion_sentences?: string[]
  example_essay?: string
  usage_instructions?: string
  key_phrases?: string[]
  is_recommended?: boolean
  is_active?: boolean
}

export interface WritingTemplateListResponse {
  success: boolean
  data: WritingTemplate[]
  total: number
  skip: number
  limit: number
}

// ==================== 写作任务相关 ====================

export interface WritingTask {
  id: number
  task_title: string
  task_prompt: string
  writing_type: WritingType
  difficulty: WritingDifficulty
  word_count_min: number
  word_count_max: number
  time_limit_minutes: number
  scoring_criteria?: Record<string, any>
  sample_answers?: string[]
  keywords?: string[]
  outline_suggestions?: string[]
  template_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WritingTaskCreate {
  task_title: string
  task_prompt: string
  writing_type: WritingType
  difficulty: WritingDifficulty
  word_count_min?: number
  word_count_max?: number
  time_limit_minutes?: number
  scoring_criteria?: Record<string, any>
  sample_answers?: string[]
  keywords?: string[]
  outline_suggestions?: string[]
  template_id?: number
}

export interface WritingTaskListResponse {
  success: boolean
  data: WritingTask[]
  total: number
  skip: number
  limit: number
}

// ==================== 写作提交相关 ====================

export interface WritingSubmission {
  id: number
  user_id: number
  task_id: number
  essay_content: string
  word_count: number
  started_at: string
  submitted_at: string
  writing_time_minutes: number
  total_score: number
  score_level?: WritingScoreLevel
  content_score: number
  structure_score: number
  language_score: number
  grammar_score: number
  feedback?: string
  improvement_suggestions?: string[]
  grammar_errors?: GrammarError[]
  vocabulary_suggestions?: string[]
  is_graded: boolean
  graded_at?: string
  created_at: string
}

export interface WritingSubmissionCreate {
  task_id: number
  essay_content: string
  writing_time_minutes: number
}

export interface WritingSubmissionListResponse {
  success: boolean
  data: WritingSubmission[]
  total: number
  skip: number
  limit: number
}

// ==================== 语法检测相关 ====================

export interface GrammarError {
  position: { start: number; end: number }
  error_type: string
  message: string
  suggestion: string
  severity: 'low' | 'medium' | 'high'
}

export interface GrammarCheckResult {
  text: string
  errors: GrammarError[]
  total_errors: number
  error_density: number
  suggestions: string[]
  corrected_text?: string
}

// ==================== 写作词汇相关 ====================

export interface WritingVocabulary {
  id: number
  word_or_phrase: string
  part_of_speech?: string
  meaning?: string
  category?: string
  writing_type?: WritingType
  difficulty_level?: WritingDifficulty
  usage_examples?: string[]
  synonyms?: string[]
  antonyms?: string[]
  collocations?: string[]
  frequency_score: number
  is_active: boolean
  created_at: string
}

export interface WritingVocabularyCreate {
  word_or_phrase: string
  part_of_speech?: string
  meaning?: string
  category?: string
  writing_type?: WritingType
  difficulty_level?: WritingDifficulty
  usage_examples?: string[]
  synonyms?: string[]
  antonyms?: string[]
  collocations?: string[]
}

export interface WritingVocabularyListResponse {
  success: boolean
  data: WritingVocabulary[]
  total: number
  skip: number
  limit: number
}

// ==================== 写作统计相关 ====================

export interface WritingStatistics {
  total_submissions: number
  average_score: number
  score_distribution: Record<WritingScoreLevel, number>
  writing_type_performance: Record<
    WritingType,
    {
      count: number
      average_score: number
      improvement_rate: number
    }
  >
  difficulty_performance: Record<
    WritingDifficulty,
    {
      count: number
      average_score: number
      success_rate: number
    }
  >
  recent_performance: Array<{
    date: string
    submissions: number
    average_score: number
  }>
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
}

// ==================== 写作推荐相关 ====================

export interface WritingRecommendation {
  recommended_templates: WritingTemplate[]
  suggested_tasks: WritingTask[]
  vocabulary_to_learn: WritingVocabulary[]
  practice_focus_areas: string[]
  next_difficulty_level?: WritingDifficulty
  estimated_improvement_time: number
  personalized_tips: string[]
}

// ==================== API接口实现 ====================

export const writingApi = {
  // ==================== 模板管理 ====================

  // 获取写作模板列表
  getTemplates: async (
    params: {
      skip?: number
      limit?: number
      writing_type?: WritingType
      difficulty?: WritingDifficulty
      is_recommended?: boolean
    } = {}
  ): Promise<WritingTemplateListResponse> => {
    const response = await apiClient.get('/api/v1/writing/templates', { params })
    return response.data
  },

  // 获取模板详情
  getTemplate: async (id: number): Promise<WritingTemplate> => {
    const response = await apiClient.get(`/api/v1/writing/templates/${id}`)
    return response.data
  },

  // 创建写作模板
  createTemplate: async (data: WritingTemplateCreate): Promise<WritingTemplate> => {
    const response = await apiClient.post('/api/v1/writing/templates', data)
    return response.data
  },

  // 更新写作模板
  updateTemplate: async (id: number, data: WritingTemplateUpdate): Promise<WritingTemplate> => {
    const response = await apiClient.put(`/api/v1/writing/templates/${id}`, data)
    return response.data
  },

  // 删除写作模板
  deleteTemplate: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/writing/templates/${id}`)
  },

  // ==================== 写作任务管理 ====================

  // 获取写作任务列表
  getTasks: async (
    params: {
      skip?: number
      limit?: number
      writing_type?: WritingType
      difficulty?: WritingDifficulty
    } = {}
  ): Promise<WritingTaskListResponse> => {
    const response = await apiClient.get('/api/v1/writing/tasks', { params })
    return response.data
  },

  // 获取任务详情
  getTask: async (id: number): Promise<WritingTask> => {
    const response = await apiClient.get(`/api/v1/writing/tasks/${id}`)
    return response.data
  },

  // 创建写作任务
  createTask: async (data: WritingTaskCreate): Promise<WritingTask> => {
    const response = await apiClient.post('/api/v1/writing/tasks', data)
    return response.data
  },

  // ==================== 写作提交管理 ====================

  // 提交作文
  submitEssay: async (data: WritingSubmissionCreate): Promise<WritingSubmission> => {
    const response = await apiClient.post('/api/v1/writing/submissions', data)
    return response.data
  },

  // 获取我的写作提交列表
  getMySubmissions: async (
    params: {
      skip?: number
      limit?: number
    } = {}
  ): Promise<WritingSubmissionListResponse> => {
    const response = await apiClient.get('/api/v1/writing/submissions', { params })
    return response.data
  },

  // 获取提交详情
  getSubmission: async (id: number): Promise<WritingSubmission> => {
    const response = await apiClient.get(`/api/v1/writing/submissions/${id}`)
    return response.data
  },

  // ==================== 语法检测 ====================

  // 语法检测
  checkGrammar: async (text: string): Promise<GrammarCheckResult> => {
    // 后端期望的是查询参数，而不是请求体
    const response = await apiClient.post(
      `/api/v1/writing/grammar-check?text=${encodeURIComponent(text)}`
    )
    return response.data
  },

  // ==================== 词汇管理 ====================

  // 获取写作词汇列表
  getVocabulary: async (
    params: {
      skip?: number
      limit?: number
      category?: string
      writing_type?: WritingType
      difficulty_level?: WritingDifficulty
    } = {}
  ): Promise<WritingVocabularyListResponse> => {
    const response = await apiClient.get('/api/v1/writing/vocabulary', { params })
    return response.data
  },

  // 创建词汇
  createVocabulary: async (data: WritingVocabularyCreate): Promise<WritingVocabulary> => {
    const response = await apiClient.post('/api/v1/writing/vocabulary', data)
    return response.data
  },

  // ==================== 写作统计和推荐 ====================

  // 获取写作统计
  getStatistics: async (): Promise<WritingStatistics> => {
    const response = await apiClient.get('/api/v1/writing/statistics')
    return response.data
  },

  // 获取写作推荐
  getRecommendations: async (): Promise<WritingRecommendation> => {
    const response = await apiClient.get('/api/v1/writing/recommendations')
    return response.data
  },

  // ==================== 智能写作辅助 ====================

  // 获取写作提示
  getWritingHints: async (
    taskId: number,
    currentContent: string
  ): Promise<{
    hints: string[]
    suggestions: string[]
    next_steps: string[]
  }> => {
    const response = await apiClient.post('/api/v1/writing/hints', {
      task_id: taskId,
      current_content: currentContent,
    })
    return response.data
  },

  // 获取同义词建议
  getSynonymSuggestions: async (
    word: string
  ): Promise<{
    synonyms: string[]
    context_suggestions: string[]
    usage_examples: string[]
  }> => {
    const response = await apiClient.post('/api/v1/writing/synonyms', {
      word: word,
    })
    return response.data
  },

  // 保存草稿
  saveDraft: async (taskId: number, content: string, title?: string): Promise<void> => {
    await apiClient.post('/api/v1/writing/drafts', {
      task_id: taskId,
      content: content,
      title: title,
    })
  },

  // 获取草稿
  getDraft: async (taskId: number): Promise<{ content: string; saved_at: string } | null> => {
    try {
      const response = await apiClient.get(`/api/v1/writing/drafts/${taskId}`)
      return {
        content: response.data.content,
        saved_at: response.data.saved_at,
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  // 删除草稿
  deleteDraft: async (taskId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/writing/drafts/${taskId}`)
  },

  // 获取用户草稿列表
  getUserDrafts: async (
    params: { skip?: number; limit?: number } = {}
  ): Promise<{
    success: boolean
    data: Array<{
      draft_id: number
      task_id: number
      content: string
      word_count: number
      title: string
      saved_at: string
      auto_saved: boolean
    }>
    total: number
    skip: number
    limit: number
  }> => {
    const response = await apiClient.get('/api/v1/writing/drafts', { params })
    return response.data
  },
}
