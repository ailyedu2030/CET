/**
 * 系统监控与数据决策支持API客户端 - 需求6：系统监控与数据决策支持
 */

import { apiClient } from './client'

// ===== 类型定义 =====

export interface TeachingMonitoringData {
  teacher_quality_stats: {
    total_teachers: number
    average_rating: number
    completion_rate: number
    student_satisfaction: number
  }
  student_progress_stats: {
    total_students: number
    average_progress: number
    completion_rate: number
    knowledge_mastery_rate: number
  }
  completion_stats: {
    course_completion_rate: number
    lesson_completion_rate: number
    exercise_completion_rate: number
  }
  knowledge_mastery_stats: {
    total_knowledge_points: number
    mastered_points: number
    weak_points: number
    mastery_distribution: Array<{
      level: string
      count: number
      percentage: number
    }>
  }
  teaching_alerts: Array<{
    id: string
    type: 'low_completion' | 'poor_rating' | 'slow_progress'
    severity: 'low' | 'medium' | 'high'
    message: string
    affected_count: number
    created_at: string
  }>
}

export interface SystemOperationsMonitoring {
  system_health: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_status: 'healthy' | 'warning' | 'critical'
    uptime: number
  }
  api_statistics: {
    total_calls: number
    success_rate: number
    average_response_time: number
    error_rate: number
    deepseek_api_usage: {
      total_calls: number
      success_rate: number
      cost: number
      budget_usage_percentage: number
    }
  }
  alerts: Array<{
    id: string
    type: 'resource_usage' | 'api_failure' | 'budget_exceeded'
    severity: 'low' | 'medium' | 'high' | 'critical'
    message: string
    created_at: string
    resolved: boolean
  }>
  operation_logs: Array<{
    id: string
    timestamp: string
    user_id: number
    action: string
    resource: string
    status: 'success' | 'failure'
    ip_address: string
  }>
}

export interface ReportGenerationRequest {
  report_type: 'teaching_efficiency' | 'resource_usage' | 'security_audit'
  time_range: {
    start_date: string
    end_date: string
  }
  format: 'pdf' | 'excel' | 'html'
  recipients?: string[]
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly'
    enabled: boolean
  }
}

export interface ReportGenerationResponse {
  report_id: string
  status: 'generating' | 'completed' | 'failed'
  download_url?: string
  created_at: string
  estimated_completion?: string
}

export interface PredictiveMaintenanceData {
  hardware_predictions: Array<{
    component: string
    failure_probability: number
    predicted_failure_date: string
    confidence_level: number
    recommendations: string[]
  }>
  resource_predictions: Array<{
    resource_type: string
    predicted_shortage_date: string
    severity: 'low' | 'medium' | 'high'
    recommendations: string[]
  }>
  security_scan_results: Array<{
    vulnerability_type: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    description: string
    affected_components: string[]
    remediation_steps: string[]
  }>
  trend_analysis: {
    resource_trends: Array<{
      resource: string
      trend: 'increasing' | 'decreasing' | 'stable'
      growth_rate: number
      projection_3_months: number
    }>
    usage_patterns: Array<{
      pattern_name: string
      description: string
      impact: string
    }>
  }
}

export interface DataVisualizationConfig {
  chart_type: 'line' | 'bar' | 'pie' | 'heatmap' | 'gauge'
  metric_type: 'system' | 'teaching' | 'api' | 'user_activity'
  time_range: '1h' | '24h' | '7d' | '30d' | '90d'
  filters?: Record<string, any>
}

export interface ChartData {
  chart_type: string
  metric_type: string
  time_range: string
  data: any
  config: {
    responsive: boolean
    interactive: boolean
    drill_down_enabled: boolean
    export_enabled: boolean
  }
  last_updated: string
}

export interface RealTimeMonitoringDashboard {
  system_overview: {
    total_users_online: number
    active_sessions: number
    system_load: number
    response_time: number
  }
  teaching_metrics: {
    active_classes: number
    students_learning: number
    completion_rate_today: number
    average_score_today: number
  }
  system_metrics: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_throughput: number
  }
  alerts_summary: {
    critical_alerts: number
    warning_alerts: number
    info_alerts: number
    resolved_today: number
  }
  charts: Array<{
    id: string
    title: string
    type: string
    data: any
    position: { x: number; y: number; width: number; height: number }
  }>
}

export interface AlertManagementData {
  alerts: Array<{
    id: string
    title: string
    description: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    category: 'system' | 'teaching' | 'security' | 'performance'
    status: 'active' | 'acknowledged' | 'resolved'
    created_at: string
    updated_at: string
    assigned_to?: number
    resolution_notes?: string
  }>
  alert_rules: Array<{
    id: string
    name: string
    condition: string
    threshold: number
    enabled: boolean
    notification_channels: string[]
  }>
  notification_settings: {
    email_enabled: boolean
    sms_enabled: boolean
    webhook_enabled: boolean
    notification_frequency: 'immediate' | 'hourly' | 'daily'
  }
}

// ===== API客户端 =====

export const systemMonitoringApi = {
  // ===== 教学监控 - 需求6验收标准1 =====

  /**
   * 获取教学监控看板
   */
  async getTeachingMonitoringDashboard(periodDays: number = 7): Promise<TeachingMonitoringData> {
    const response = await apiClient.get<TeachingMonitoringData>(
      `/api/v1/analytics/monitoring/teaching/dashboard?period_days=${periodDays}`
    )
    return response.data
  },

  // ===== 系统运维监控 - 需求6验收标准2 =====

  /**
   * 获取系统运维监控数据
   */
  async getSystemOperationsMonitoring(): Promise<SystemOperationsMonitoring> {
    const response = await apiClient.get<SystemOperationsMonitoring>(
      '/api/v1/analytics/monitoring/system/operations'
    )
    return response.data
  },

  /**
   * 获取系统健康状态
   */
  async getSystemHealthStatus(): Promise<{
    status: 'healthy' | 'warning' | 'critical'
    metrics: Record<string, number>
    alerts: Array<{ type: string; message: string; severity: string }>
  }> {
    const response = await apiClient.get('/api/v1/analytics/monitoring/system/health')
    return response.data
  },

  // ===== 智能报表生成 - 需求6验收标准3 =====

  /**
   * 生成报表
   */
  async generateReport(request: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    const response = await apiClient.post<ReportGenerationResponse>(
      '/api/v1/analytics/reports/generate',
      request
    )
    return response.data
  },

  /**
   * 获取报表列表
   */
  async getReports(
    params: {
      page?: number
      size?: number
      report_type?: string
      status?: string
    } = {}
  ): Promise<{
    items: ReportGenerationResponse[]
    total: number
    page: number
    pages: number
  }> {
    const response = await apiClient.get('/api/v1/analytics/reports', { params })
    return response.data
  },

  /**
   * 下载报表
   */
  async downloadReport(reportId: string): Promise<Blob> {
    const response = await apiClient.get(`/api/v1/analytics/reports/${reportId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  // ===== 预测性维护 - 需求6验收标准4 =====

  /**
   * 获取预测性维护数据
   */
  async getPredictiveMaintenanceData(): Promise<PredictiveMaintenanceData> {
    const response = await apiClient.get<PredictiveMaintenanceData>(
      '/api/v1/analytics/monitoring/predictive/maintenance'
    )
    return response.data
  },

  /**
   * 触发安全漏洞扫描
   */
  async triggerSecurityScan(): Promise<{ message: string; scan_id: string }> {
    const response = await apiClient.post<{ message: string; scan_id: string }>(
      '/api/v1/analytics/monitoring/security/scan'
    )
    return response.data
  },

  // ===== 数据可视化 - 需求6验收标准5 =====

  /**
   * 获取实时监控大屏数据
   */
  async getRealTimeMonitoringDashboard(): Promise<RealTimeMonitoringDashboard> {
    const response = await apiClient.get<RealTimeMonitoringDashboard>(
      '/api/v1/analytics/visualization/dashboard/real-time'
    )
    return response.data
  },

  /**
   * 获取交互式图表数据
   */
  async getInteractiveChartData(config: DataVisualizationConfig): Promise<ChartData> {
    const response = await apiClient.post<ChartData>(
      '/api/v1/analytics/visualization/charts/interactive',
      config
    )
    return response.data
  },

  /**
   * 导出图表
   */
  async exportChart(chartId: string, format: 'png' | 'svg' | 'pdf'): Promise<Blob> {
    const response = await apiClient.get(
      `/api/v1/analytics/visualization/charts/${chartId}/export`,
      {
        params: { format },
        responseType: 'blob',
      }
    )
    return response.data
  },

  // ===== 告警管理 =====

  /**
   * 获取告警管理数据
   */
  async getAlertManagementData(
    params: {
      page?: number
      size?: number
      severity?: string
      status?: string
      category?: string
    } = {}
  ): Promise<AlertManagementData> {
    const response = await apiClient.get<AlertManagementData>(
      '/api/v1/analytics/alerts/management',
      { params }
    )
    return response.data
  },

  /**
   * 确认告警
   */
  async acknowledgeAlert(alertId: string, notes?: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/analytics/alerts/${alertId}/acknowledge`,
      { notes }
    )
    return response.data
  },

  /**
   * 解决告警
   */
  async resolveAlert(alertId: string, resolutionNotes: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/analytics/alerts/${alertId}/resolve`,
      { resolution_notes: resolutionNotes }
    )
    return response.data
  },

  /**
   * 创建告警规则
   */
  async createAlertRule(rule: {
    name: string
    condition: string
    threshold: number
    notification_channels: string[]
  }): Promise<{ message: string; rule_id: string }> {
    const response = await apiClient.post<{ message: string; rule_id: string }>(
      '/api/v1/analytics/alerts/rules',
      rule
    )
    return response.data
  },

  /**
   * 更新通知设置
   */
  async updateNotificationSettings(settings: {
    email_enabled: boolean
    sms_enabled: boolean
    webhook_enabled: boolean
    notification_frequency: string
  }): Promise<{ message: string }> {
    const response = await apiClient.put<{ message: string }>(
      '/api/v1/analytics/alerts/notification-settings',
      settings
    )
    return response.data
  },
}
