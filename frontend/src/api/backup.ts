/**
 * 数据备份与恢复API客户端 - 需求9：数据备份与恢复
 */

import { apiClient } from './client'

// ===== 类型定义 =====

export interface BackupInfo {
  backup_id: string
  backup_type: string
  file_path: string
  file_size: number
  status: string
  created_at: string
  expires_at?: string
  description?: string
  tables: string[]
  compression: boolean
  encryption: boolean
  checksum: string
}

export interface BackupRequest {
  backup_type: string
  tables?: string[]
  storage_location?: string
  compression?: boolean
  encryption?: boolean
  description?: string
}

export interface RestoreInfo {
  restore_id: string
  backup_id: string
  restore_type: string
  status: string
  progress_percentage: number
  current_step: string
  estimated_remaining_time: string
  started_at: string
  completed_at?: string
  error_message?: string
  tables_restored?: string[]
  records_restored?: number
}

export interface RestoreRequest {
  backup_id: string
  restore_type: string
  tables?: string[]
  confirm_overwrite: boolean
  validate_before_restore?: boolean
  target_time?: string
}

export interface BackupStatistics {
  total_backups: number
  successful_backups: number
  failed_backups: number
  total_size: number
  average_size: number
  backup_types: Record<string, { count: number; size: number }>
  period_start: string
  period_end: string
}

export interface BackupConfig {
  name: string
  backup_type: string
  schedule: string
  retention_days: number
  enabled: boolean
  tables?: string[]
  compression?: boolean
  encryption?: boolean
}

export interface BackupAuditLog {
  id: number
  user_id: number
  username: string
  action_type: string
  resource_type: string
  resource_id: string
  details: Record<string, any>
  ip_address: string
  user_agent: string
  timestamp: string
  success: boolean
  error_message?: string
}

export interface BackupPermission {
  user_id: number
  username: string
  permissions: string[]
  granted_by: number
  granted_at: string
  expires_at?: string
}

// ===== API客户端 =====

export const backupApi = {
  // ===== 备份管理 - 需求9验收标准1 =====

  /**
   * 创建数据备份
   */
  async createBackup(request: BackupRequest): Promise<BackupInfo> {
    const response = await apiClient.post<BackupInfo>('/api/v1/users/backup/', request)
    return response.data
  },

  /**
   * 获取备份列表
   */
  async getBackups(
    params: {
      backup_type?: string
      limit?: number
      offset?: number
    } = {}
  ): Promise<BackupInfo[]> {
    const response = await apiClient.get<BackupInfo[]>('/api/v1/users/backup/', { params })
    return response.data
  },

  /**
   * 获取备份详情
   */
  async getBackupInfo(backupId: string): Promise<BackupInfo> {
    const response = await apiClient.get<BackupInfo>(`/api/v1/users/backup/${backupId}`)
    return response.data
  },

  /**
   * 删除备份
   */
  async deleteBackup(backupId: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/api/v1/users/backup/${backupId}`)
    return response.data
  },

  /**
   * 创建增量备份
   */
  async createIncrementalBackup(baseBackupId: string): Promise<BackupInfo> {
    const response = await apiClient.post<BackupInfo>(
      `/api/v1/users/backup/incremental?base_backup_id=${baseBackupId}`
    )
    return response.data
  },

  /**
   * 获取备份统计
   */
  async getBackupStatistics(days: number = 30): Promise<BackupStatistics> {
    const response = await apiClient.get<BackupStatistics>(
      `/api/v1/users/backup/statistics?days=${days}`
    )
    return response.data
  },

  /**
   * 执行计划备份
   */
  async executeScheduledBackups(): Promise<{
    success: boolean
    message: string
    results: any[]
    total_backups: number
    successful_backups: number
    failed_backups: number
  }> {
    const response = await apiClient.post('/api/v1/users/backup/schedule/execute')
    return response.data
  },

  // ===== 备份调度管理 =====

  /**
   * 配置备份调度
   */
  async configureBackupSchedule(config: BackupConfig): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      '/api/v1/users/backup/schedule',
      config
    )
    return response.data
  },

  /**
   * 获取备份调度配置
   */
  async getBackupSchedules(): Promise<BackupConfig[]> {
    const response = await apiClient.get<BackupConfig[]>('/api/v1/users/backup/schedule')
    return response.data
  },

  /**
   * 更新备份调度配置
   */
  async updateBackupSchedule(name: string, config: Partial<BackupConfig>): Promise<BackupConfig> {
    const response = await apiClient.put<BackupConfig>(
      `/api/v1/users/backup/schedule/${name}`,
      config
    )
    return response.data
  },

  /**
   * 删除备份调度
   */
  async deleteBackupSchedule(name: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/users/backup/schedule/${name}`
    )
    return response.data
  },

  // ===== 数据恢复管理 - 需求9验收标准2 =====

  /**
   * 从备份恢复数据
   */
  async restoreFromBackup(request: RestoreRequest): Promise<RestoreInfo> {
    const response = await apiClient.post<RestoreInfo>('/api/v1/users/restore/', request)
    return response.data
  },

  /**
   * 获取恢复操作列表
   */
  async getRestoreOperations(
    params: {
      status?: string
      limit?: number
      offset?: number
    } = {}
  ): Promise<RestoreInfo[]> {
    const response = await apiClient.get<RestoreInfo[]>('/api/v1/users/restore/', { params })
    return response.data
  },

  /**
   * 获取恢复操作详情
   */
  async getRestoreInfo(restoreId: string): Promise<RestoreInfo> {
    const response = await apiClient.get<RestoreInfo>(`/api/v1/users/restore/${restoreId}`)
    return response.data
  },

  /**
   * 取消恢复操作
   */
  async cancelRestore(restoreId: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/users/restore/${restoreId}/cancel`
    )
    return response.data
  },

  /**
   * 时间点恢复
   */
  async restoreToPointInTime(params: {
    backup_id: string
    target_time: string
    confirm_overwrite: boolean
  }): Promise<RestoreInfo> {
    const response = await apiClient.post<RestoreInfo>(
      '/api/v1/users/restore/point-in-time',
      params
    )
    return response.data
  },

  /**
   * 验证恢复前提条件
   */
  async validateRestorePrerequisites(params: {
    backup_id: string
    restore_type: string
    tables?: string[]
  }): Promise<{
    can_restore: boolean
    validation_errors: string[]
    warnings: string[]
    estimated_duration: string
    disk_space_required: number
    backup_compatibility: boolean
  }> {
    const response = await apiClient.post(`/api/v1/users/restore/validate/${params.backup_id}`, {
      restore_type: params.restore_type,
      tables: params.tables || [],
    })
    return response.data
  },

  // ===== 备份验证 =====

  /**
   * 验证备份完整性
   */
  async validateBackupIntegrity(backupId: string): Promise<{
    is_valid: boolean
    checksum_match: boolean
    file_exists: boolean
    corruption_detected: boolean
    validation_details: Record<string, any>
  }> {
    const response = await apiClient.post(`/api/v1/users/backup/${backupId}/validate`)
    return response.data
  },

  // ===== 恢复操作管理 =====

  /**
   * 部分恢复
   */
  async restorePartialData(params: {
    backup_id: string
    tables: string[]
    confirm_overwrite: boolean
  }): Promise<RestoreInfo> {
    const response = await apiClient.post<RestoreInfo>('/api/v1/users/restore/partial', null, {
      params,
    })
    return response.data
  },

  /**
   * 获取恢复进度
   */
  async getRestoreProgress(restoreId: string): Promise<{
    restore_id: string
    progress_percentage: number
    current_step: string
    estimated_remaining_time: string
    status: string
    error_message?: string
  }> {
    const response = await apiClient.get(`/api/v1/users/restore/${restoreId}/progress`)
    return response.data
  },

  /**
   * 获取恢复历史摘要
   */
  async getRestoreHistorySummary(days: number = 30): Promise<{
    total_restores: number
    successful_restores: number
    failed_restores: number
    average_duration: string
    restore_types: Record<string, number>
    period_start: string
    period_end: string
  }> {
    const response = await apiClient.get(`/api/v1/users/restore/history/summary?days=${days}`)
    return response.data
  },

  // ===== 权限控制与安全性 - 需求9验收标准3 =====

  /**
   * 获取备份操作审计日志
   */
  async getBackupAuditLogs(
    params: {
      start_date?: string
      end_date?: string
      user_id?: number
      action_type?: string
      limit?: number
      offset?: number
    } = {}
  ): Promise<BackupAuditLog[]> {
    const response = await apiClient.get<BackupAuditLog[]>('/api/v1/users/audit/logs', { params })
    return response.data
  },

  /**
   * 获取备份权限列表
   */
  async getBackupPermissions(): Promise<BackupPermission[]> {
    const response = await apiClient.get<BackupPermission[]>('/api/v1/users/permissions/')
    return response.data
  },

  /**
   * 授予备份权限
   */
  async grantBackupPermission(params: {
    user_id: number
    permissions: string[]
    expires_at?: string
  }): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/v1/users/permissions/', params)
    return response.data
  },

  /**
   * 撤销备份权限
   */
  async revokeBackupPermission(userId: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `/api/v1/users/permissions/${userId}`
    )
    return response.data
  },

  /**
   * 检查当前用户备份权限
   */
  async checkBackupPermissions(): Promise<{
    can_create_backup: boolean
    can_restore_data: boolean
    can_delete_backup: boolean
    can_manage_schedule: boolean
    can_view_audit_logs: boolean
  }> {
    const response = await apiClient.get('/api/v1/users/permissions/users/me/permissions')
    return response.data
  },

  /**
   * 获取备份安全设置
   */
  async getBackupSecuritySettings(): Promise<{
    encryption_enabled: boolean
    compression_enabled: boolean
    retention_policy: number
    access_control_enabled: boolean
    audit_logging_enabled: boolean
  }> {
    const response = await apiClient.get('/api/v1/users/admin/system/security/settings')
    return response.data
  },

  /**
   * 更新备份安全设置
   */
  async updateBackupSecuritySettings(settings: {
    encryption_enabled?: boolean
    compression_enabled?: boolean
    retention_policy?: number
    access_control_enabled?: boolean
    audit_logging_enabled?: boolean
  }): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      '/api/v1/users/admin/system/security/settings',
      settings
    )
    return response.data
  },
}
