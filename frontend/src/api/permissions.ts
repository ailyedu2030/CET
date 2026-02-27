/**
 * 权限与角色管理API服务 - 需求3
 * 与后端 /api/v1/users/permissions 端点集成
 */

import { apiClient } from './client'

// ===== 权限管理接口 =====

export interface Permission {
  id: number
  name: string
  code: string
  description: string
  module: string
  action: string
  resource: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PermissionCreateRequest {
  name: string
  code: string
  module: string
  action: string
  description: string
  resource: string
}

export interface PermissionUpdateRequest {
  name?: string
  description?: string
  is_active?: boolean
}

// ===== 角色管理接口 =====

export interface Role {
  id: number
  name: string
  code: string
  description: string
  level: number
  is_active: boolean
  is_system: boolean
  permissions: Permission[]
  user_count: number
  created_at: string
  updated_at: string
}

export interface RoleCreateRequest {
  name: string
  code: string
  description: string
  permission_ids: number[]
}

export interface RoleUpdateRequest {
  name?: string
  description?: string
  is_active?: boolean
}

// ===== 用户权限分配接口 =====

export interface UserRole {
  user_id: number
  username: string
  email: string
  real_name: string
  user_type: string
  roles: Role[]
  permissions: Permission[]
  last_login: string | null
}

export interface PermissionAssignRequest {
  permission_ids: number[]
}

export interface UserRoleAssignRequest {
  role_ids: number[]
}

export interface UserPermissionAssignRequest {
  user_id: number
  role_ids: number[]
  permissions: string[]
}

// ===== 权限审计接口 =====

export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  resource_type: string
  resource_id: number | null
  details: Record<string, any>
  ip_address: string
  user_agent: string
  created_at: string
}

export interface PermissionAuditRequest {
  user_id?: number
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
}

export interface SecurityEvent {
  id: number
  event_type: string
  severity: string
  user_id: number | null
  username: string | null
  description: string
  ip_address: string
  user_agent: string
  created_at: string
}

// ===== API客户端实现 =====

/**
 * 权限管理API
 */
export const permissionApi = {
  /**
   * 获取权限列表
   */
  async getPermissions(params: {
    skip?: number
    limit?: number
    module?: string
    is_active?: boolean
  }): Promise<Permission[]> {
    const response = await apiClient.get<Permission[]>('/api/v1/users/permissions/', {
      params,
    })
    return response.data
  },

  /**
   * 获取权限详情
   */
  async getPermission(id: number): Promise<Permission> {
    const response = await apiClient.get<Permission>(`/api/v1/users/permissions/${id}`)
    return response.data
  },

  /**
   * 创建权限
   */
  async createPermission(data: PermissionCreateRequest): Promise<Permission> {
    const response = await apiClient.post<Permission>('/api/v1/users/permissions/', data)
    return response.data
  },

  /**
   * 更新权限
   */
  async updatePermission(id: number, data: PermissionUpdateRequest): Promise<Permission> {
    const response = await apiClient.put<Permission>(`/api/v1/users/permissions/${id}`, data)
    return response.data
  },

  /**
   * 删除权限
   */
  async deletePermission(id: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/api/v1/users/permissions/${id}`)
    return response.data
  },
}

/**
 * 角色管理API
 */
export const roleApi = {
  /**
   * 获取角色列表
   */
  async getRoles(params: { skip?: number; limit?: number; is_active?: boolean }): Promise<Role[]> {
    const response = await apiClient.get<Role[]>('/api/v1/users/permissions/roles/', {
      params,
    })
    return response.data
  },

  /**
   * 获取角色详情
   */
  async getRole(id: number): Promise<Role> {
    const response = await apiClient.get<Role>(`/api/v1/users/permissions/roles/${id}`)
    return response.data
  },

  /**
   * 创建角色
   */
  async createRole(data: RoleCreateRequest): Promise<Role> {
    const response = await apiClient.post<Role>('/api/v1/users/permissions/roles/', data)
    return response.data
  },

  /**
   * 更新角色
   */
  async updateRole(id: number, data: RoleUpdateRequest): Promise<Role> {
    const response = await apiClient.put<Role>(`/api/v1/users/permissions/roles/${id}`, data)
    return response.data
  },

  /**
   * 删除角色
   */
  async deleteRole(id: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/users/permissions/roles/${id}`
    )
    return response.data
  },

  /**
   * 给角色分配权限
   */
  async assignPermissionsToRole(
    roleId: number,
    data: PermissionAssignRequest
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/users/permissions/roles/${roleId}/permissions`,
      data
    )
    return response.data
  },
}

/**
 * 用户权限管理API
 */
export const userPermissionApi = {
  /**
   * 获取用户权限详情
   */
  async getUserPermission(userId: number): Promise<any> {
    const response = await apiClient.get<any>(
      `/api/v1/users/permissions/users/${userId}/permissions`
    )
    return response.data
  },

  /**
   * 给用户分配角色
   */
  async assignRolesToUser(
    userId: number,
    data: { role_ids: number[] }
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/users/permissions/users/${userId}/roles`,
      data
    )
    return response.data
  },

  /**
   * 获取所有用户的权限概览
   */
  async getUserPermissions(
    params: {
      skip?: number
      limit?: number
    } = {}
  ): Promise<UserRole[]> {
    const response = await apiClient.get<UserRole[]>(
      '/api/v1/users/permissions/user-roles-overview',
      {
        params,
      }
    )
    return response.data
  },
}

/**
 * 权限审计API
 */
export const auditApi = {
  /**
   * 获取审计日志
   */
  async getAuditLogs(params: {
    skip?: number
    limit?: number
    user_id?: number
    action?: string
    resource_type?: string
    start_date?: string
    end_date?: string
  }): Promise<{ items: AuditLog[]; total: number }> {
    const response = await apiClient.get<{ items: AuditLog[]; total: number }>(
      '/api/v1/users/audit/logs',
      {
        params,
      }
    )
    return response.data
  },

  /**
   * 获取权限审计记录
   */
  async getPermissionAudit(params: PermissionAuditRequest): Promise<AuditLog[]> {
    const response = await apiClient.get<AuditLog[]>('/api/v1/users/audit/permissions', {
      params,
    })
    return response.data
  },

  /**
   * 获取安全事件
   */
  async getSecurityEvents(params: {
    skip?: number
    limit?: number
    event_type?: string
    severity?: string
  }): Promise<SecurityEvent[]> {
    const response = await apiClient.get<SecurityEvent[]>('/api/v1/users/audit/security-events', {
      params,
    })
    return response.data
  },

  /**
   * 获取权限统计
   */
  async getPermissionStatistics(timeRange: string = '7d'): Promise<Record<string, any>> {
    const response = await apiClient.get<Record<string, any>>('/api/v1/users/audit/statistics', {
      params: { time_range: timeRange },
    })
    return response.data
  },

  /**
   * 生成审计报告
   */
  async generateAuditReport(params: {
    start_date: string
    end_date: string
    format: 'pdf' | 'excel'
  }): Promise<Blob> {
    // 根据后端API，需要使用查询参数
    const queryParams = new URLSearchParams({
      report_type: 'comprehensive',
      start_date: params.start_date,
      end_date: params.end_date,
      format: params.format === 'excel' ? 'csv' : params.format,
    })

    const response = await apiClient.post(
      `/api/v1/users/audit/reports/generate?${queryParams}`,
      {},
      {
        responseType: 'json', // 后端返回的是JSON格式的报告信息，不是直接的文件
      }
    )

    // 模拟文件下载，实际应该根据返回的download_url下载文件
    const reportData = response.data
    const content = JSON.stringify(reportData, null, 2)
    const blob = new Blob([content], {
      type: params.format === 'pdf' ? 'application/pdf' : 'text/csv',
    })

    return blob
  },
}
