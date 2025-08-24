/**
 * 用户激活API客户端
 * 
 * 实现🔥需求20验收标准5：
 * - 激活链接处理
 * - 24小时有效期
 * - 支持过期重发
 */

import { apiClient } from './client'

// 激活请求
export interface ActivationRequest {
  activation_token: string
}

// 重发激活邮件请求
export interface ResendActivationRequest {
  email: string
}

// 激活响应
export interface ActivationResponse {
  success: boolean
  message: string
  user_id?: number
  username?: string
}

// 激活状态响应
export interface ActivationStatusResponse {
  valid: boolean
  message: string
  user_id?: number
  email?: string
  created_at?: string
}

/**
 * 激活用户账号
 */
export async function activateUser(data: ActivationRequest): Promise<ActivationResponse> {
  const response = await apiClient.post<ActivationResponse>('/api/v1/activation/activate', data)
  return response.data
}

/**
 * 重发激活邮件
 */
export async function resendActivationEmail(data: ResendActivationRequest): Promise<ActivationResponse> {
  const response = await apiClient.post<ActivationResponse>('/api/v1/activation/resend', data)
  return response.data
}

/**
 * 检查激活链接状态
 */
export async function checkActivationStatus(token: string): Promise<ActivationStatusResponse> {
  const response = await apiClient.get<ActivationStatusResponse>(`/api/v1/activation/status/${token}`)
  return response.data
}
