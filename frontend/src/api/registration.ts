/**
 * 注册相关API服务
 * 与后端 /api/v1/registration 端点集成
 */

import { apiClient } from './client'

// 学生注册请求接口
export interface StudentRegistrationRequest {
  // 账户信息
  username: string
  password: string
  email: string

  // 学生档案信息（需求1：11项基础信息）
  real_name: string
  age?: number
  gender?: string
  id_number?: string
  phone?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  school?: string
  department?: string
  major?: string
  grade?: string
  class_name?: string
}

// 教师注册请求接口
export interface TeacherRegistrationRequest {
  // 账户信息
  username: string
  password: string
  email: string

  // 教师档案信息（需求1：7项基础信息）
  real_name: string
  age?: number
  gender?: string
  title?: string
  subject?: string
  phone?: string
  introduction?: string
}

// 注册响应接口
export interface RegistrationResponse {
  application_id: number
  message: string
  estimated_review_time: string
}

// 申请状态查询响应
export interface ApplicationStatusResponse {
  application_id: number
  status: 'pending' | 'approved' | 'rejected'
  submitted_at: string
  reviewed_at?: string
  review_notes?: string
  estimated_review_time?: string
}

// 申请列表响应（管理员用）
export interface ApplicationListResponse {
  total: number
  page: number
  size: number
  items: RegistrationApplication[]
}

// 注册申请详情
export interface RegistrationApplication {
  id: number
  user_id: number
  username: string
  email: string
  application_type: 'student' | 'teacher'
  status: 'pending' | 'approved' | 'rejected'
  submitted_at: string
  reviewed_at?: string
  reviewer_id?: number
  review_notes?: string
  application_data: Record<string, any>
  submitted_documents: Record<string, any>
}

// 审核请求接口
export interface ReviewApplicationRequest {
  application_id: number
  action: 'approve' | 'reject'
  review_notes?: string
}

// 批量审核请求接口
export interface BatchReviewRequest {
  application_ids: number[]
  action: 'approve' | 'reject'
  review_notes?: string
}

// 批量导入结果接口
export interface ImportResult {
  success: boolean
  total_records: number
  successful_imports: number
  failed_imports: number
  created_applications?: Array<{
    row_number: number
    application_id: string
    user_id: number
    username: string
    real_name: string
  }>
  failed_records?: Array<{
    row_number: number
    username: string
    real_name: string
    error: string
  }>
  validation_errors?: string[]
  message: string
}

// Excel模板接口
export interface ExcelTemplate {
  success: boolean
  template: {
    headers: string[]
    sample_data: Record<string, any>[]
    required_fields: string[]
    field_descriptions: Record<string, string>
  }
  message: string
}

/**
 * 学生注册API
 */
export const studentRegistration = {
  /**
   * 提交学生注册申请
   */
  async register(data: StudentRegistrationRequest): Promise<RegistrationResponse> {
    const response = await apiClient.post<RegistrationResponse>(
      '/api/v1/registration/student',
      data
    )
    return response.data
  },

  /**
   * 查询申请状态（公开API，无需登录）
   */
  async getStatus(applicationId: number): Promise<ApplicationStatusResponse> {
    const response = await apiClient.get<ApplicationStatusResponse>(
      `/api/v1/registration/status/${applicationId}`
    )
    return response.data
  },
}

/**
 * 教师注册API
 */
export const teacherRegistration = {
  /**
   * 提交教师注册申请
   */
  async register(data: TeacherRegistrationRequest): Promise<RegistrationResponse> {
    const response = await apiClient.post<RegistrationResponse>(
      '/api/v1/registration/teacher',
      data
    )
    return response.data
  },

  /**
   * 上传教师资质证书
   */
  async uploadCertificate(
    applicationId: number,
    certificateType: 'teacher_certificate' | 'qualification_certificates' | 'honor_certificates',
    file: File
  ): Promise<{ file_url: string; message: string }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('certificate_type', certificateType)

    const response = await apiClient.post<{ file_url: string; message: string }>(
      `/api/v1/registration/teacher/${applicationId}/upload-certificate`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * 查询申请状态（公开API，无需登录）
   */
  async getStatus(applicationId: number): Promise<ApplicationStatusResponse> {
    const response = await apiClient.get<ApplicationStatusResponse>(
      `/api/v1/registration/status/${applicationId}`
    )
    return response.data
  },
}

/**
 * 管理员审核API
 */
export const adminReview = {
  /**
   * 获取申请列表
   */
  async getApplications(params: {
    application_type?: 'student' | 'teacher'
    status?: 'pending' | 'approved' | 'rejected'
    page?: number
    size?: number
    search?: string
  }): Promise<ApplicationListResponse> {
    const response = await apiClient.get<ApplicationListResponse>(
      '/api/v1/registration/applications',
      {
        params,
      }
    )
    return response.data
  },

  /**
   * 获取申请详情
   */
  async getApplicationDetail(applicationId: number): Promise<RegistrationApplication> {
    const response = await apiClient.get<RegistrationApplication>(
      `/api/v1/registration/applications/${applicationId}`
    )
    return response.data
  },

  /**
   * 审核单个申请
   */
  async reviewApplication(data: ReviewApplicationRequest): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/registration/applications/${data.application_id}/review`,
      {
        action: data.action,
        review_notes: data.review_notes,
      }
    )
    return response.data
  },

  /**
   * 批量审核申请（需求1：最多20条/批）
   */
  async batchReview(
    data: BatchReviewRequest
  ): Promise<{ message: string; processed_count: number }> {
    if (data.application_ids.length > 20) {
      throw new Error('批量审核最多支持20条申请')
    }

    const response = await apiClient.post<{ message: string; processed_count: number }>(
      '/api/v1/registration/applications/batch-review',
      data
    )
    return response.data
  },

  /**
   * 导出申请数据（Excel格式）
   */
  async exportApplications(params: {
    application_type?: 'student' | 'teacher'
    status?: 'pending' | 'approved' | 'rejected'
    start_date?: string
    end_date?: string
  }): Promise<Blob> {
    const response = await apiClient.get('/api/v1/registration/applications/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * 批量导入学生数据（Excel格式）
   */
  async importStudents(file: File): Promise<ImportResult> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ImportResult>(
      '/api/v1/registration/students/import-excel',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * 获取Excel导入模板
   */
  async getImportTemplate(): Promise<ExcelTemplate> {
    const response = await apiClient.get<ExcelTemplate>(
      '/api/v1/registration/students/import-template'
    )
    return response.data
  },
}

/**
 * 通用注册工具函数
 */
export const registrationUtils = {
  /**
   * 格式化申请状态显示
   */
  formatStatus(status: string): string {
    const statusMap = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已驳回',
    }
    return statusMap[status as keyof typeof statusMap] || '未知状态'
  },

  /**
   * 格式化申请类型显示
   */
  formatType(type: string): string {
    const typeMap = {
      student: '学生',
      teacher: '教师',
    }
    return typeMap[type as keyof typeof typeMap] || '未知类型'
  },

  /**
   * 获取状态颜色
   */
  getStatusColor(status: string): string {
    const colorMap = {
      pending: 'orange',
      approved: 'green',
      rejected: 'red',
    }
    return colorMap[status as keyof typeof colorMap] || 'gray'
  },

  /**
   * 验证文件类型（教师资质材料）
   */
  validateCertificateFile(file: File): { valid: boolean; error?: string } {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
    const maxSize = 5 * 1024 * 1024 // 5MB

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: '文件格式不支持，请上传PDF、JPG或PNG格式的文件',
      }
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: '文件大小不能超过5MB',
      }
    }

    return { valid: true }
  },

  /**
   * 生成下载文件名
   */
  generateExportFileName(type: 'student' | 'teacher' | 'all', status?: string): string {
    const timestamp = new Date().toISOString().slice(0, 10)
    const typeLabel = type === 'all' ? '全部' : type === 'student' ? '学生' : '教师'
    const statusLabel = status ? `_${status}` : ''
    return `${typeLabel}注册申请${statusLabel}_${timestamp}.xlsx`
  },
}
