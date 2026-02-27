/**
 * 班级管理API客户端 - 需求4：班级管理与资源配置
 */

import { apiClient } from './client'

// ===== 类型定义 =====

export interface ClassBase {
  name: string
  description?: string
  code?: string
  max_students: number
  resource_allocation?: Record<string, any>
  class_rules?: Record<string, any>
  start_date?: string
  end_date?: string
  schedule?: Record<string, any>
}

export interface ClassCreate extends ClassBase {
  course_id: number
  teacher_id?: number
  classroom_id?: number
}

export interface ClassUpdate extends Partial<ClassBase> {
  teacher_id?: number
  classroom_id?: number
  status?: string
}

export interface ClassResponse extends ClassBase {
  id: number
  course_id: number
  teacher_id?: number
  classroom_id?: number
  status: string
  current_students: number
  completion_rate: number
  is_active: boolean
  created_at: string
  updated_at: string
  course?: {
    id: number
    name: string
    code?: string
  }
  teacher?: {
    id: number
    real_name: string
    email: string
  }
  classroom?: {
    id: number
    name: string
    building_name: string
  }
}

export interface ClassListResponse {
  items: ClassResponse[]
  total: number
  page: number
  pages: number
  size: number
}

export interface ClassBatchCreate {
  course_id: number
  teacher_id?: number
  class_prefix: string
  class_count: number
  max_students_per_class: number
  start_date?: string
  end_date?: string
  schedule_template?: Record<string, any>
}

export interface BatchCreateResult {
  message: string
  created_count: number
  classes: Array<{
    id: number
    name: string
    code?: string
  }>
}

export interface ResourceAllocation {
  teacher_id?: number
  classroom_id?: number
  course_materials?: number[]
  equipment_list?: string[]
}

export interface ResourceChangeHistory {
  id: number
  class_id: number
  change_type: string
  old_allocation: Record<string, any>
  new_allocation: Record<string, any>
  changed_by: number
  changed_at: string
  reason: string
}

export interface BindingRuleValidation {
  is_valid: boolean
  message: string
  class_id: number
  current_teacher_id?: number
  current_course_id: number
}

// ===== API客户端 =====

export const classManagementApi = {
  // ===== 班级基础管理 - 需求4验收标准1 =====

  /**
   * 创建班级
   */
  async createClass(classData: ClassCreate): Promise<ClassResponse> {
    const response = await apiClient.post<ClassResponse>(
      '/api/v1/class-management/classes',
      classData
    )
    return response.data
  },

  /**
   * 获取班级列表
   */
  async getClasses(
    params: {
      page?: number
      size?: number
      course_id?: number
      teacher_id?: number
      status?: string
    } = {}
  ): Promise<ClassListResponse> {
    const response = await apiClient.get<ClassListResponse>('/api/v1/class-management/classes', {
      params,
    })
    return response.data
  },

  /**
   * 获取班级详情
   */
  async getClass(classId: number): Promise<ClassResponse> {
    const response = await apiClient.get<ClassResponse>(
      `/api/v1/class-management/classes/${classId}`
    )
    return response.data
  },

  /**
   * 更新班级信息
   */
  async updateClass(classId: number, classData: ClassUpdate): Promise<ClassResponse> {
    const response = await apiClient.put<ClassResponse>(
      `/api/v1/class-management/classes/${classId}`,
      classData
    )
    return response.data
  },

  /**
   * 删除班级
   */
  async deleteClass(classId: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/class-management/classes/${classId}`
    )
    return response.data
  },

  // ===== 基于课程模板创建班级 - 需求4验收标准2 =====

  /**
   * 基于课程模板创建班级
   */
  async createClassFromTemplate(params: {
    course_id: number
    class_name: string
    teacher_id?: number
    max_students?: number
  }): Promise<ClassResponse> {
    const response = await apiClient.post<ClassResponse>(
      '/api/v1/class-management/classes/from-template',
      null,
      { params }
    )
    return response.data
  },

  /**
   * 批量创建班级
   */
  async batchCreateClasses(batchData: ClassBatchCreate): Promise<BatchCreateResult> {
    const response = await apiClient.post<BatchCreateResult>(
      '/api/v1/class-management/classes/batch',
      batchData
    )
    return response.data
  },

  // ===== 班级资源配置 - 需求4验收标准3 =====

  /**
   * 配置班级资源
   */
  async configureClassResources(
    classId: number,
    resources: ResourceAllocation
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/class-management/classes/${classId}/resources`,
      resources
    )
    return response.data
  },

  /**
   * 获取班级资源配置
   */
  async getClassResources(classId: number): Promise<ResourceAllocation> {
    const response = await apiClient.get<ResourceAllocation>(
      `/api/v1/class-management/classes/${classId}/resources`
    )
    return response.data
  },

  // ===== 班级资源变更历史 - 需求4验收标准4 =====

  /**
   * 获取班级资源变更历史
   */
  async getResourceChangeHistory(
    classId: number,
    params: {
      page?: number
      size?: number
    } = {}
  ): Promise<{
    items: ResourceChangeHistory[]
    total: number
    page: number
    pages: number
  }> {
    const response = await apiClient.get(
      `/api/v1/class-management/classes/${classId}/resource-history`,
      { params }
    )
    return response.data
  },

  // ===== 班级绑定规则验证 - 需求4验收标准5 =====

  /**
   * 验证班级绑定规则
   */
  async validateBindingRules(
    classId: number,
    params: {
      teacher_id?: number
      course_id?: number
    } = {}
  ): Promise<BindingRuleValidation> {
    const response = await apiClient.get<BindingRuleValidation>(
      `/api/v1/class-management/classes/${classId}/binding-validation`,
      { params }
    )
    return response.data
  },

  /**
   * 获取可用课程列表（用于班级创建）
   */
  async getAvailableCourses(): Promise<
    Array<{
      id: number
      name: string
      code?: string
      status: string
    }>
  > {
    const response = await apiClient.get('/api/v1/class-management/available-courses')
    return response.data
  },

  /**
   * 获取可用教师列表（用于班级分配）
   */
  async getAvailableTeachers(): Promise<
    Array<{
      id: number
      real_name: string
      email: string
      subject?: string
      qualification_status: string
    }>
  > {
    const response = await apiClient.get('/api/v1/class-management/available-teachers')
    return response.data
  },

  /**
   * 获取可用教室列表（用于班级分配）
   */
  async getAvailableClassrooms(): Promise<
    Array<{
      id: number
      name: string
      building_name: string
      capacity: number
      is_available: boolean
    }>
  > {
    const response = await apiClient.get('/api/v1/class-management/available-classrooms')
    return response.data
  },
}
