/**
 * AI服务API客户端
 */
import { apiClient, ApiResponse } from '../api/client'
import {
  LearningAnalysisRequest,
  LearningAnalysis,
  LearningAnalysisListResponse,
  TeachingAdjustmentRequest,
  TeachingAdjustment,
  TeachingAdjustmentUpdate,
  TeachingAdjustmentListResponse,
  SyllabusGenerateRequest,
  Syllabus,
} from '../types/ai'

class AIService {
  private readonly baseURL = '/ai/api/v1'

  // 学情分析相关API
  async analyzeLearningProgress(request: LearningAnalysisRequest): Promise<LearningAnalysis> {
    const response = await apiClient.post<ApiResponse<LearningAnalysis>>(
      `${this.baseURL}/learning-analysis/analyze`,
      request
    )
    return response.data.data
  }

  async getLearningAnalysis(analysisId: number): Promise<LearningAnalysis> {
    const response = await apiClient.get<ApiResponse<LearningAnalysis>>(
      `${this.baseURL}/learning-analysis/${analysisId}`
    )
    return response.data.data
  }

  async getLearningAnalyses(
    params: {
      page?: number
      size?: number
      class_id?: number
      course_id?: number
      analysis_type?: string
      analysis_period?: string
    } = {}
  ): Promise<LearningAnalysisListResponse> {
    const response = await apiClient.get<ApiResponse<LearningAnalysisListResponse>>(
      `${this.baseURL}/learning-analysis`,
      { params }
    )
    return response.data.data
  }

  // 教学调整建议相关API
  async generateTeachingAdjustments(
    request: TeachingAdjustmentRequest
  ): Promise<TeachingAdjustment[]> {
    const response = await apiClient.post<ApiResponse<TeachingAdjustment[]>>(
      `${this.baseURL}/teaching-adjustments/generate`,
      request
    )
    return response.data.data
  }

  async getTeachingAdjustment(adjustmentId: number): Promise<TeachingAdjustment> {
    const response = await apiClient.get<ApiResponse<TeachingAdjustment>>(
      `${this.baseURL}/teaching-adjustments/${adjustmentId}`
    )
    return response.data.data
  }

  async updateTeachingAdjustment(
    adjustmentId: number,
    update: TeachingAdjustmentUpdate
  ): Promise<TeachingAdjustment> {
    const response = await apiClient.put<ApiResponse<TeachingAdjustment>>(
      `${this.baseURL}/teaching-adjustments/${adjustmentId}`,
      update
    )
    return response.data.data
  }

  async getTeachingAdjustments(
    params: {
      page?: number
      size?: number
      class_id?: number
      course_id?: number
      adjustment_type?: string
      implementation_status?: string
      priority_level?: string
    } = {}
  ): Promise<TeachingAdjustmentListResponse> {
    const response = await apiClient.get<ApiResponse<TeachingAdjustmentListResponse>>(
      `${this.baseURL}/teaching-adjustments`,
      { params }
    )
    return response.data.data
  }

  // 课程大纲生成相关API
  async generateSyllabus(request: SyllabusGenerateRequest): Promise<Syllabus> {
    const response = await apiClient.post<ApiResponse<Syllabus>>(
      `${this.baseURL}/syllabus/generate`,
      request
    )
    return response.data.data
  }

  async getSyllabus(syllabusId: number): Promise<Syllabus> {
    const response = await apiClient.get<ApiResponse<Syllabus>>(
      `${this.baseURL}/syllabus/${syllabusId}`
    )
    return response.data.data
  }

  async listSyllabi(
    params: {
      page?: number
      size?: number
      course_id?: number
      status?: string
    } = {}
  ): Promise<{ syllabi: Syllabus[]; total: number; page: number; size: number }> {
    const response = await apiClient.get<
      ApiResponse<{ syllabi: Syllabus[]; total: number; page: number; size: number }>
    >(`${this.baseURL}/syllabus`, { params })
    return response.data.data
  }

  async updateSyllabus(
    syllabusId: number,
    updates: {
      title?: string
      content?: Record<string, unknown>
      status?: 'draft' | 'review' | 'approved'
    }
  ): Promise<Syllabus> {
    const response = await apiClient.put<ApiResponse<Syllabus>>(
      `${this.baseURL}/syllabus/${syllabusId}`,
      updates
    )
    return response.data.data
  }
}

// 导出单例实例
export const aiService = new AIService()
