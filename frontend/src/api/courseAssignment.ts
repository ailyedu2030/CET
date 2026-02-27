/**
 * 课程分配管理API客户端 - 需求5：课程分配管理
 */

import { apiClient } from './client'

// ===== 类型定义 =====

export interface CourseAssignmentRequest {
  course_id: number
  teacher_ids: number[]
  class_ids: number[]
  assignment_type: 'single' | 'multiple_teachers' | 'multiple_classes'
  start_date: string
  end_date: string
  schedule?: Record<string, any>
  notes?: string
}

export interface CourseAssignmentResponse {
  id: number
  course_id: number
  teacher_ids: number[]
  class_ids: number[]
  assignment_type: string
  start_date: string
  end_date: string
  status: string
  created_at: string
  updated_at: string
  course?: {
    id: number
    name: string
    code?: string
  }
  teachers?: Array<{
    id: number
    real_name: string
    email: string
    qualification_status: string
  }>
  classes?: Array<{
    id: number
    name: string
    current_students: number
    max_students: number
  }>
}

export interface TeacherQualificationCheck {
  teacher_id: number
  course_id: number
}

export interface QualificationCheckResult {
  is_qualified: boolean
  teacher_id: number
  course_id: number
  qualification_score: number
  missing_qualifications: string[]
  recommendations: string[]
}

export interface TeacherWorkloadInfo {
  teacher_id: number
  current_classes: number
  current_students: number
  total_hours_per_week: number
  workload_percentage: number
  is_overloaded: boolean
  available_capacity: number
}

export interface WorkloadBalanceRequest {
  teacher_ids: number[]
  course_ids: number[]
  target_balance_threshold: number
}

export interface WorkloadBalanceResponse {
  balanced_assignments: Array<{
    teacher_id: number
    course_id: number
    recommended_classes: number
  }>
  balance_score: number
  recommendations: string[]
}

export interface TimeConflictCheck {
  teacher_id?: number
  class_id?: number
  classroom_id?: number
  start_time: string
  end_time: string
  day_of_week: number
}

export interface TimeConflictResult {
  has_conflict: boolean
  conflicts: Array<{
    type: 'teacher' | 'class' | 'classroom'
    conflicting_id: number
    conflicting_name: string
    conflict_time: string
    severity: 'low' | 'medium' | 'high'
  }>
  suggestions: string[]
}

export interface BulkAssignmentRequest {
  assignments: CourseAssignmentRequest[]
  check_conflicts: boolean
  auto_resolve_conflicts: boolean
}

export interface BulkAssignmentResponse {
  successful_assignments: CourseAssignmentResponse[]
  failed_assignments: Array<{
    request: CourseAssignmentRequest
    error: string
  }>
  conflicts_detected: TimeConflictResult[]
  summary: {
    total: number
    successful: number
    failed: number
    conflicts: number
  }
}

export interface TeacherCollaborationPermission {
  teacher_id: number
  course_id: number
  permissions: {
    can_edit_syllabus: boolean
    can_create_lesson_plans: boolean
    can_grade_assignments: boolean
    can_view_analytics: boolean
    assigned_chapters: string[]
    assigned_modules: string[]
  }
}

export interface ClassroomSchedulingRule {
  rule_id: string
  rule_name: string
  rule_type: 'basic' | 'advanced'
  enabled: boolean
  configuration: {
    max_classes_per_room_per_day?: number
    allow_room_sharing?: boolean
    minimum_break_minutes?: number
    priority_levels?: string[]
  }
}

export interface RuleExemptionRequest {
  rule_id: string
  exemption_type: 'temporary' | 'permanent'
  reason: string
  affected_entities: {
    teacher_ids?: number[]
    class_ids?: number[]
    classroom_ids?: number[]
  }
  start_date: string
  end_date?: string
}

// ===== API客户端 =====

export const courseAssignmentApi = {
  // ===== 教师课程资质匹配 - 需求5验收标准1 =====

  /**
   * 分配课程给教师
   */
  async assignCourseToTeacher(request: CourseAssignmentRequest): Promise<CourseAssignmentResponse> {
    const response = await apiClient.post<CourseAssignmentResponse>(
      '/api/v1/courses/course-assignment/assignments',
      request
    )
    return response.data
  },

  /**
   * 检查教师课程资质匹配
   */
  async checkTeacherQualification(
    check: TeacherQualificationCheck
  ): Promise<QualificationCheckResult> {
    const response = await apiClient.post<QualificationCheckResult>(
      `/api/v1/courses/course-assignment/qualifications/check?teacher_id=${check.teacher_id}&course_id=${check.course_id}`
    )
    return response.data
  },

  /**
   * 获取教师工作量信息
   */
  async getTeacherWorkload(teacherId: number): Promise<TeacherWorkloadInfo> {
    const response = await apiClient.get<TeacherWorkloadInfo>(
      `/api/v1/courses/course-assignment/workload/teachers/${teacherId}`
    )
    return response.data
  },

  /**
   * 检查时间冲突
   */
  async checkTimeConflict(check: TimeConflictCheck): Promise<TimeConflictResult> {
    const params = new URLSearchParams()
    if (check.teacher_id) params.append('teacher_id', check.teacher_id.toString())
    if (check.class_id) params.append('class_id', check.class_id.toString())
    if (check.classroom_id) params.append('classroom_id', check.classroom_id.toString())
    params.append('start_time', check.start_time)
    params.append('end_time', check.end_time)
    params.append('day_of_week', check.day_of_week.toString())

    const response = await apiClient.post<TimeConflictResult>(
      `/api/v1/courses/course-assignment/conflicts/check?${params.toString()}`
    )
    return response.data
  },

  // ===== 工作量平衡分配 - 需求5验收标准1 =====

  /**
   * 工作量平衡分配
   */
  async balanceWorkload(request: WorkloadBalanceRequest): Promise<WorkloadBalanceResponse> {
    const params = new URLSearchParams()
    request.teacher_ids.forEach(id => params.append('teacher_ids', id.toString()))
    request.course_ids.forEach(id => params.append('course_ids', id.toString()))
    params.append('target_balance_threshold', request.target_balance_threshold.toString())

    const response = await apiClient.post<WorkloadBalanceResponse>(
      `/api/v1/courses/course-assignment/workload/balance?${params.toString()}`
    )
    return response.data
  },

  /**
   * 获取所有教师工作量统计
   */
  async getAllTeachersWorkload(): Promise<TeacherWorkloadInfo[]> {
    const response = await apiClient.get<TeacherWorkloadInfo[]>(
      '/api/v1/courses/course-assignment/workload/teachers'
    )
    return response.data
  },

  // ===== 一对多配置 - 需求5验收标准2 =====

  /**
   * 配置一对多分配
   */
  async configureOneToManyAssignment(
    courseId: number,
    configuration: {
      type: 'multiple_classes' | 'multiple_teachers'
      class_configurations?: Array<{
        class_id: number
        customizations: Record<string, any>
      }>
      teacher_assignments?: Array<{
        teacher_id: number
        chapters: string[]
        modules: string[]
      }>
    }
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/courses/course-assignment/one-to-many-configuration?course_id=${courseId}`,
      configuration
    )
    return response.data
  },

  // ===== 批量分配 - 需求5验收标准2 =====

  /**
   * 批量分配课程
   */
  async bulkAssignCourses(request: BulkAssignmentRequest): Promise<BulkAssignmentResponse> {
    const response = await apiClient.post<BulkAssignmentResponse>(
      '/api/v1/courses/course-assignment/assignments/bulk',
      request
    )
    return response.data
  },

  // ===== 权限划分 - 需求5验收标准3 =====

  /**
   * 设置教师协作权限
   */
  async setTeacherCollaborationPermissions(
    permissions: TeacherCollaborationPermission
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      '/api/v1/courses/course-assignment/teacher-collaboration-permissions',
      permissions
    )
    return response.data
  },

  /**
   * 获取教师协作权限
   */
  async getTeacherCollaborationPermissions(
    teacherId: number,
    courseId: number
  ): Promise<TeacherCollaborationPermission> {
    const response = await apiClient.get<TeacherCollaborationPermission>(
      `/api/v1/courses/course-assignment/teacher-collaboration-permissions?teacher_id=${teacherId}&course_id=${courseId}`
    )
    return response.data
  },

  // ===== 教室排课规则 - 需求5验收标准4 =====

  /**
   * 获取教室排课规则
   */
  async getClassroomSchedulingRules(): Promise<ClassroomSchedulingRule[]> {
    const response = await apiClient.get<ClassroomSchedulingRule[]>(
      '/api/v1/courses/course-assignment/classroom-rules'
    )
    return response.data
  },

  /**
   * 更新教室排课规则
   */
  async updateClassroomSchedulingRule(
    ruleId: string,
    rule: Partial<ClassroomSchedulingRule>
  ): Promise<ClassroomSchedulingRule> {
    const response = await apiClient.put<ClassroomSchedulingRule>(
      `/api/v1/courses/course-assignment/classroom-rules/${ruleId}`,
      rule
    )
    return response.data
  },

  // ===== 特殊情况豁免 - 需求5验收标准5 =====

  /**
   * 申请规则豁免
   */
  async requestRuleExemption(
    request: RuleExemptionRequest
  ): Promise<{ message: string; exemption_id: string }> {
    const response = await apiClient.post<{ message: string; exemption_id: string }>(
      '/api/v1/courses/course-assignment/rule-exemption-requests',
      request
    )
    return response.data
  },

  /**
   * 获取规则豁免列表
   */
  async getRuleExemptions(
    params: {
      status?: 'pending' | 'approved' | 'rejected'
      page?: number
      size?: number
    } = {}
  ): Promise<{
    items: Array<{
      id: string
      rule_id: string
      exemption_type: string
      reason: string
      status: string
      created_at: string
      approved_at?: string
      approved_by?: number
    }>
    total: number
    page: number
    pages: number
  }> {
    const response = await apiClient.get(
      '/api/v1/courses/course-assignment/rule-exemption-requests',
      { params }
    )
    return response.data
  },

  /**
   * 审批规则豁免
   */
  async approveRuleExemption(
    exemptionId: string,
    decision: {
      action: 'approve' | 'reject'
      notes?: string
    }
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/courses/course-assignment/rule-exemption-requests/${exemptionId}/approve`,
      decision
    )
    return response.data
  },

  // ===== 分配管理查询 =====

  /**
   * 获取课程分配列表
   */
  async getCourseAssignments(
    params: {
      page?: number
      size?: number
      course_id?: number
      teacher_id?: number
      status?: string
    } = {}
  ): Promise<{
    items: CourseAssignmentResponse[]
    total: number
    page: number
    pages: number
  }> {
    const response = await apiClient.get('/api/v1/courses/course-assignment/assignments', {
      params,
    })
    return response.data
  },

  /**
   * 获取分配详情
   */
  async getAssignmentDetail(assignmentId: number): Promise<CourseAssignmentResponse> {
    const response = await apiClient.get<CourseAssignmentResponse>(
      `/api/v1/courses/course-assignment/assignments/${assignmentId}`
    )
    return response.data
  },

  /**
   * 更新课程分配
   */
  async updateCourseAssignment(
    assignmentId: number,
    updates: Partial<CourseAssignmentRequest>
  ): Promise<CourseAssignmentResponse> {
    const response = await apiClient.put<CourseAssignmentResponse>(
      `/api/v1/courses/course-assignment/assignments/${assignmentId}`,
      updates
    )
    return response.data
  },

  /**
   * 删除课程分配
   */
  async deleteCourseAssignment(assignmentId: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/courses/course-assignment/assignments/${assignmentId}`
    )
    return response.data
  },
}
