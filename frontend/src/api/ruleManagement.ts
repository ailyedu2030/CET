/**
 * 规则管理API客户端 - 需求8：班级与课程规则管理
 */

import { apiClient } from './client'

// ===== 类型定义 =====

export interface RuleConfiguration {
  id: number
  rule_name: string
  rule_type: string
  rule_category: string
  rule_config: Record<string, any>
  is_enabled: boolean
  is_strict: boolean
  allow_exceptions: boolean
  scope_type: string
  scope_config: Record<string, any>
  description?: string
  created_by: number
  created_at: string
  updated_at: string
}

export interface RuleConfigurationCreate {
  rule_name: string
  rule_type: string
  rule_category: string
  rule_config: Record<string, any>
  is_enabled?: boolean
  is_strict?: boolean
  allow_exceptions?: boolean
  scope_type?: string
  scope_config?: Record<string, any>
  description?: string
}

export interface RuleConfigurationUpdate {
  rule_name?: string
  rule_type?: string
  rule_category?: string
  rule_config?: Record<string, any>
  is_enabled?: boolean
  is_strict?: boolean
  allow_exceptions?: boolean
  scope_type?: string
  scope_config?: Record<string, any>
  description?: string
}

export interface RuleTemplate {
  template_name: string
  template_type: string
  description: string
  default_config: Record<string, any>
  required_fields: string[]
  optional_fields: string[]
  examples: Array<{
    name: string
    config: Record<string, any>
  }>
}

export interface RuleStatistics {
  rule_id: number
  rule_name: string
  execution_count: number
  success_count: number
  failure_count: number
  violation_count: number
  last_execution: string
  average_execution_time: number
  effectiveness_score: number
  trend: 'improving' | 'declining' | 'stable'
  recommendations: string[]
}

export interface RuleValidationRequest {
  target_type: string
  target_id: number
  context: Record<string, any>
}

export interface RuleValidationResponse {
  is_compliant: boolean
  message: string
  violations: Array<{
    rule: string
    message: string
    severity: 'low' | 'medium' | 'high'
    details: Record<string, any>
  }>
  warnings: string[]
  suggestions: string[]
}

export interface RuleExecutionRequest {
  execution_context: Record<string, any>
  dry_run?: boolean
  execution_notes?: string
}

export interface RuleExecutionResponse {
  execution_id: string
  execution_result: 'success' | 'failure' | 'partial' | 'skipped'
  message: string
  execution_time: number
  affected_entities: Array<{
    entity_type: string
    entity_id: number
    action: string
  }>
  violations: Array<{
    rule: string
    message: string
    severity: string
  }>
}

export interface RuleExemption {
  id: number
  rule_id: number
  target_type: string
  target_id: number
  exemption_reason: string
  exemption_period_start: string
  exemption_period_end: string
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  requested_by: number
  approved_by?: number
  approval_notes?: string
  created_at: string
  updated_at: string
}

export interface RuleExemptionCreate {
  rule_id: number
  target_type: string
  target_id: number
  exemption_reason: string
  exemption_period_start: string
  exemption_period_end: string
}

export interface RuleMonitoring {
  rule_id: number
  monitoring_period: string
  execution_count: number
  success_rate: number
  average_response_time: number
  violation_count: number
  effectiveness_metrics: Record<string, any>
  performance_trends: Array<{
    date: string
    execution_count: number
    success_rate: number
    response_time: number
  }>
  recommendations: string[]
}

export interface RuleExecutionLog {
  id: number
  rule_id: number
  execution_type: string
  execution_result: string
  execution_context: Record<string, any>
  violation_details: Record<string, any>
  resolution_action?: string
  target_type: string
  target_id: number
  executed_by?: number
  execution_time: string
}

// ===== API客户端 =====

export const ruleManagementApi = {
  // ===== 规则配置管理 - 需求8验收标准1 =====

  /**
   * 创建规则配置
   */
  async createRule(ruleData: RuleConfigurationCreate): Promise<RuleConfiguration> {
    const response = await apiClient.post<RuleConfiguration>('/api/v1/courses/rules/', ruleData)
    return response.data
  },

  /**
   * 获取规则配置列表
   */
  async getRules(
    params: {
      rule_type?: string
      rule_category?: string
      is_enabled?: boolean
      scope_type?: string
      skip?: number
      limit?: number
    } = {}
  ): Promise<RuleConfiguration[]> {
    const response = await apiClient.get<RuleConfiguration[]>('/api/v1/courses/rules/', { params })
    return response.data
  },

  /**
   * 获取规则配置详情
   */
  async getRule(ruleId: number): Promise<RuleConfiguration> {
    const response = await apiClient.get<RuleConfiguration>(`/api/v1/courses/rules/${ruleId}`)
    return response.data
  },

  /**
   * 更新规则配置
   */
  async updateRule(ruleId: number, ruleData: RuleConfigurationUpdate): Promise<RuleConfiguration> {
    const response = await apiClient.put<RuleConfiguration>(
      `/api/v1/courses/rules/${ruleId}`,
      ruleData
    )
    return response.data
  },

  /**
   * 删除规则配置
   */
  async deleteRule(ruleId: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/api/v1/courses/rules/${ruleId}`)
    return response.data
  },

  // ===== 规则模板管理 =====

  /**
   * 获取规则模板列表
   */
  async getRuleTemplates(templateType?: string): Promise<RuleTemplate[]> {
    const response = await apiClient.get<RuleTemplate[]>('/api/v1/courses/rules/templates', {
      params: templateType ? { template_type: templateType } : {},
    })
    return response.data
  },

  // ===== 规则验证 - 需求8验收标准2 =====

  /**
   * 验证规则合规性
   */
  async validateRule(
    ruleId: number,
    request: RuleValidationRequest
  ): Promise<RuleValidationResponse> {
    const response = await apiClient.post<RuleValidationResponse>(
      `/api/v1/courses/rules/${ruleId}/validate`,
      request
    )
    return response.data
  },

  /**
   * 执行规则
   */
  async executeRule(ruleId: number, request: RuleExecutionRequest): Promise<RuleExecutionResponse> {
    const response = await apiClient.post<RuleExecutionResponse>(
      `/api/v1/courses/rules/${ruleId}/execute`,
      request
    )
    return response.data
  },

  // ===== 规则监控 - 需求8验收标准3 =====

  /**
   * 获取规则监控数据
   */
  async getRuleMonitoring(
    ruleId: number,
    params: {
      limit?: number
      offset?: number
    } = {}
  ): Promise<RuleMonitoring[]> {
    const response = await apiClient.get<RuleMonitoring[]>(
      `/api/v1/courses/rules/${ruleId}/monitoring`,
      { params }
    )
    return response.data
  },

  /**
   * 获取规则统计
   */
  async getRuleStatistics(): Promise<RuleStatistics[]> {
    const response = await apiClient.get<RuleStatistics[]>('/api/v1/courses/rules/statistics')
    return response.data
  },

  /**
   * 获取规则执行历史
   */
  async getRuleExecutionHistory(
    ruleId: number,
    params: {
      limit?: number
      offset?: number
    } = {}
  ): Promise<RuleExecutionLog[]> {
    const response = await apiClient.get<RuleExecutionLog[]>(
      `/api/v1/courses/rules/${ruleId}/executions`,
      { params }
    )
    return response.data
  },

  // ===== 规则豁免管理 =====

  /**
   * 创建规则豁免申请
   */
  async createRuleExemption(exemptionData: RuleExemptionCreate): Promise<RuleExemption> {
    const response = await apiClient.post<RuleExemption>(
      '/api/v1/courses/rules/exemptions/',
      exemptionData
    )
    return response.data
  },

  /**
   * 获取规则豁免列表
   */
  async getRuleExemptions(
    params: {
      rule_id?: number
      status?: string
      skip?: number
      limit?: number
    } = {}
  ): Promise<{
    items: RuleExemption[]
    total: number
    page: number
    pages: number
  }> {
    const response = await apiClient.get('/api/v1/courses/rules/exemptions/', { params })
    return response.data
  },

  /**
   * 审批规则豁免
   */
  async approveRuleExemption(
    exemptionId: number,
    decision: {
      action: 'approve' | 'reject'
      approval_notes?: string
    }
  ): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/courses/rules/exemptions/${exemptionId}/approve`,
      decision
    )
    return response.data
  },
}
