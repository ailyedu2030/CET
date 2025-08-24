/**
 * AI相关类型定义
 */

// 学情分析相关类型
export interface LearningAnalysisRequest {
  class_id: number
  course_id: number
  analysis_type: 'progress' | 'difficulty' | 'engagement'
  analysis_period: 'weekly' | 'monthly' | 'semester'
  include_students?: number[]
  additional_params?: Record<string, unknown>
}

export interface LearningAnalysis {
  id: number
  class_id: number
  course_id: number
  teacher_id: number
  analysis_type: string
  analysis_period: string
  student_count: number
  analysis_data: Record<string, unknown>
  insights: string[]
  risk_students: number[]
  ai_generated: boolean
  confidence_score: number
  status: string
  analysis_date: string
  created_at: string
  updated_at: string
}

export interface LearningAnalysisListResponse {
  analyses: LearningAnalysis[]
  total: number
  page: number
  size: number
}

// 教学调整建议相关类型
export interface TeachingAdjustmentRequest {
  learning_analysis_id?: number
  class_id: number
  course_id: number
  adjustment_focus: 'content' | 'pace' | 'method' | 'assessment'
  target_students?: number[]
  current_issues?: string[]
  priority_level?: 'high' | 'medium' | 'low'
}

export interface TeachingAdjustment {
  id: number
  learning_analysis_id?: number
  class_id: number
  course_id: number
  teacher_id: number
  adjustment_type: string
  priority_level: string
  title: string
  description: string
  adjustments: Record<string, unknown>
  target_students: number[]
  expected_outcome?: string
  implementation_timeline?: string
  ai_generated: boolean
  confidence_score: number
  reasoning?: string
  implementation_status: 'pending' | 'in_progress' | 'completed' | 'dismissed'
  implementation_date?: string
  feedback?: string
  effectiveness_rating?: number
  created_at: string
  updated_at: string
}

export interface TeachingAdjustmentUpdate {
  implementation_status?: 'pending' | 'in_progress' | 'completed' | 'dismissed'
  implementation_date?: string
  feedback?: string
  effectiveness_rating?: number
}

export interface TeachingAdjustmentListResponse {
  adjustments: TeachingAdjustment[]
  total: number
  page: number
  size: number
}

// 课程大纲相关类型
export interface SyllabusGenerateRequest {
  course_id: number
  course_name: string
  duration_weeks: number
  target_level: string
  learning_objectives: string[]
  source_materials?: Record<string, unknown>
  focus_areas?: string[]
  available_resources?: string[]
}

export interface Syllabus {
  id: number
  course_id: number
  teacher_id: number
  title: string
  content: Record<string, unknown>
  version: string
  status: 'draft' | 'review' | 'approved'
  ai_generated: boolean
  confidence_score: number
  source_materials?: Record<string, unknown>
  created_at: string
  updated_at: string
}

// 课程和班级基础类型
export interface Course {
  id: number
  name: string
  description?: string
  level: string
  duration_weeks: number
  created_at: string
  updated_at: string
}

export interface Class {
  id: number
  name: string
  course_id: number
  teacher_id: number
  student_count: number
  created_at: string
  updated_at: string
}

// API响应状态
export interface ApiError {
  message: string
  details?: string
  code?: string
}

export interface LoadingState {
  loading: boolean
  error?: string | null
}
