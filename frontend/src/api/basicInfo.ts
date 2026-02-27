/**
 * 基础信息管理API服务 - 需求2
 * 与后端 /api/v1/users/basic-info 端点集成
 */

import { apiClient } from './client'

// ===== 学生信息管理接口 =====

export interface Student {
  id: number
  username: string
  email: string
  real_name: string
  is_active: boolean
  is_verified: boolean
  last_login: string | null
  created_at: string
  profile: {
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
    learning_status: string
    total_study_hours: number
    completed_courses: number
    current_level: string
    target_score: number
    last_test_score?: number
    last_test_date?: string
    notes?: string
  }
}

export interface StudentListResponse {
  items: Student[]
  total: number
  page: number
  size: number
  pages: number
}

export interface StudentUpdateRequest {
  real_name?: string
  age?: number
  gender?: string
  phone?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  school?: string
  department?: string
  major?: string
  grade?: string
  class_name?: string
  target_score?: number
  notes?: string
}

export interface StatusUpdateRequest {
  learning_status: string
  notes?: string
}

export interface BatchImportRequest {
  file: File
  overwrite_existing?: boolean
}

export interface BatchExportRequest {
  format: 'excel' | 'csv'
  filters?: {
    learning_status?: string
    school?: string
    grade?: string
  }
}

// ===== 教师信息管理接口 =====

export interface Teacher {
  id: number
  username: string
  email: string
  real_name: string
  is_active: boolean
  is_verified: boolean
  last_login: string | null
  created_at: string
  profile: {
    age?: number
    gender?: string
    title?: string
    subject?: string
    phone?: string
    introduction?: string
    teaching_status: string
    qualification_status: string
    qualification_notes?: string
    last_review_date?: string
    next_review_date?: string
    hourly_rate: number
    monthly_salary: number
    total_salary_paid: number
    total_teaching_hours: number
    student_count: number
    average_rating: number
    notes?: string
  }
}

export interface TeacherListResponse {
  items: Teacher[]
  total: number
  page: number
  size: number
  pages: number
}

export interface TeacherUpdateRequest {
  real_name?: string
  age?: number
  gender?: string
  title?: string
  subject?: string
  phone?: string
  introduction?: string
  notes?: string
}

export interface SalaryUpdateRequest {
  hourly_rate: number
  monthly_salary: number
}

export interface QualificationReviewRequest {
  qualification_status: string
  notes?: string
}

// ===== 教室信息管理接口 =====

export interface Building {
  id: number
  campus_id: number
  name: string
  building_number?: string
  floors: number
}

export interface Classroom {
  id: number
  building_id: number
  name: string
  room_number: string
  floor: number
  capacity: number
  area?: number
  equipment_list: Record<string, any>
  has_projector: boolean
  has_computer: boolean
  has_audio: boolean
  has_whiteboard: boolean
  is_available: boolean
  available_start_time?: string
  available_end_time?: string
  available_days: Record<string, any>
  maintenance_status: string
  last_maintenance_date?: string
  notes?: string
  building: Building
}

export interface ClassroomListResponse {
  items: Classroom[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ConflictCheckRequest {
  classroom_id: number
  start_time: Date
  end_time: Date
  exclude_schedule_id?: number
  repeat_type?: 'none' | 'daily' | 'weekly' | 'monthly'
  repeat_end_date?: Date
  repeat_days?: number[]
}

export interface ConflictCheckResult {
  has_conflict: boolean
  message: string
  classroom_id: number
  start_time: Date
  end_time: Date
  conflicts?: Array<{
    id: number
    title: string
    start_time: string
    end_time: string
    teacher_name?: string
  }>
}

// ===== API客户端实现 =====

/**
 * 学生信息管理API
 */
export const studentApi = {
  /**
   * 获取学生列表
   */
  async getStudents(params: {
    page?: number
    size?: number
    search?: string
    learning_status?: string
  }): Promise<StudentListResponse> {
    const response = await apiClient.get<StudentListResponse>('/api/v1/users/basic-info/students', {
      params,
    })
    return response.data
  },

  /**
   * 获取学生详情
   */
  async getStudent(id: number): Promise<Student> {
    const response = await apiClient.get<Student>(`/api/v1/users/basic-info/students/${id}`)
    return response.data
  },

  /**
   * 更新学生信息
   */
  async updateStudent(id: number, data: StudentUpdateRequest): Promise<Student> {
    const response = await apiClient.put<Student>(`/api/v1/users/basic-info/students/${id}`, data)
    return response.data
  },

  /**
   * 更新学生状态
   */
  async updateStudentStatus(id: number, data: StatusUpdateRequest): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      `/api/v1/users/basic-info/students/${id}/status`,
      data
    )
    return response.data
  },

  /**
   * 删除学生
   */
  async deleteStudent(id: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/users/basic-info/students/${id}`
    )
    return response.data
  },

  /**
   * 批量导入学生
   */
  async batchImport(data: BatchImportRequest): Promise<{ message: string; imported: number }> {
    const formData = new FormData()
    formData.append('file', data.file)
    if (data.overwrite_existing) {
      formData.append('overwrite_existing', 'true')
    }

    const response = await apiClient.post<{ message: string; imported: number }>(
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
   * 批量导出学生
   */
  async batchExport(data: BatchExportRequest): Promise<Blob> {
    const response = await apiClient.post('/api/v1/users/basic-info/students/batch-export', data, {
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * 获取批量导入模板
   */
  async getImportTemplate(): Promise<{ template: any; message: string }> {
    const response = await apiClient.get<{ template: any; message: string }>(
      '/api/v1/registration/students/import-template'
    )
    return response.data
  },

  /**
   * 获取学生费用记录
   */
  async getStudentFees(
    studentId: number,
    params: {
      page?: number
      size?: number
      fee_type?: string
    } = {}
  ): Promise<{ fees: any[]; total: number }> {
    const response = await apiClient.get<{ fees: any[]; total: number }>(
      `/api/v1/users/basic-info/students/${studentId}/fees`,
      { params }
    )
    return response.data
  },

  /**
   * 创建费用记录
   */
  async createFeeRecord(
    studentId: number,
    feeData: any
  ): Promise<{ message: string; record: any }> {
    const response = await apiClient.post<{ message: string; record: any }>(
      `/api/v1/users/basic-info/students/${studentId}/fees`,
      feeData
    )
    return response.data
  },

  /**
   * 创建退费记录
   */
  async createRefundRecord(
    studentId: number,
    refundData: any
  ): Promise<{ message: string; record: any }> {
    const response = await apiClient.post<{ message: string; record: any }>(
      `/api/v1/users/basic-info/students/${studentId}/refunds`,
      refundData
    )
    return response.data
  },

  /**
   * 生成发票
   */
  async generateInvoice(feeId: number): Promise<{ message: string; invoice: any }> {
    const response = await apiClient.post<{ message: string; invoice: any }>(
      `/api/v1/users/basic-info/fees/${feeId}/invoice`
    )
    return response.data
  },
}

/**
 * 教师信息管理API
 */
export const teacherApi = {
  /**
   * 获取教师列表
   */
  async getTeachers(params: {
    page?: number
    size?: number
    search?: string
    teaching_status?: string
  }): Promise<TeacherListResponse> {
    const response = await apiClient.get<TeacherListResponse>('/api/v1/users/basic-info/teachers', {
      params,
    })
    return response.data
  },

  /**
   * 获取教师详情
   */
  async getTeacher(id: number): Promise<Teacher> {
    const response = await apiClient.get<Teacher>(`/api/v1/users/basic-info/teachers/${id}`)
    return response.data
  },

  /**
   * 更新教师信息
   */
  async updateTeacher(id: number, data: TeacherUpdateRequest): Promise<Teacher> {
    const response = await apiClient.put<Teacher>(`/api/v1/users/basic-info/teachers/${id}`, data)
    return response.data
  },

  /**
   * 更新教师薪酬
   */
  async updateTeacherSalary(id: number, data: SalaryUpdateRequest): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      `/api/v1/users/basic-info/teachers/${id}/salary`,
      data
    )
    return response.data
  },

  /**
   * 教师资质审核
   */
  async reviewQualification(
    id: number,
    data: QualificationReviewRequest
  ): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      `/api/v1/users/basic-info/teachers/${id}/qualification`,
      data
    )
    return response.data
  },

  /**
   * 删除教师
   */
  async deleteTeacher(id: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/users/basic-info/teachers/${id}`
    )
    return response.data
  },
}

/**
 * 教室信息管理API
 */
export const classroomApi = {
  /**
   * 获取楼栋列表
   */
  async getBuildings(): Promise<{ buildings: Building[] }> {
    const response = await apiClient.get<{ buildings: Building[] }>(
      '/api/v1/users/basic-info/buildings'
    )
    return response.data
  },

  /**
   * 获取教室列表
   */
  async getClassrooms(params: {
    page?: number
    size?: number
    building_id?: number
    is_available?: boolean
  }): Promise<ClassroomListResponse> {
    const response = await apiClient.get<ClassroomListResponse>(
      '/api/v1/users/basic-info/classrooms',
      {
        params,
      }
    )
    return response.data
  },

  /**
   * 获取教室详情
   */
  async getClassroom(id: number): Promise<Classroom> {
    const response = await apiClient.get<Classroom>(`/api/v1/users/basic-info/classrooms/${id}`)
    return response.data
  },

  /**
   * 教室排期冲突检查
   */
  async checkConflict(data: ConflictCheckRequest): Promise<ConflictCheckResult> {
    const response = await apiClient.post<ConflictCheckResult>(
      '/api/v1/users/basic-info/classrooms/check-conflict',
      data
    )
    return response.data
  },

  /**
   * 更新教室信息
   */
  async updateClassroom(id: number, data: Partial<Classroom>): Promise<Classroom> {
    const response = await apiClient.put<Classroom>(
      `/api/v1/users/basic-info/classrooms/${id}`,
      data
    )
    return response.data
  },

  /**
   * 更新教室可用状态
   */
  async updateClassroomAvailability(
    id: number,
    is_available: boolean
  ): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      `/api/v1/users/basic-info/classrooms/${id}/availability`,
      { is_available }
    )
    return response.data
  },

  /**
   * 更新教室维护状态
   */
  async updateMaintenanceStatus(
    id: number,
    status: string,
    notes?: string
  ): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      `/api/v1/users/basic-info/classrooms/${id}/maintenance`,
      { maintenance_status: status, notes }
    )
    return response.data
  },
}
