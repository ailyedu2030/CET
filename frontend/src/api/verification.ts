/**
 * 验证码API客户端
 * 
 * 实现🔥需求20验收标准3：
 * - 手机号验证码验证
 * - 验证码有效期5分钟
 * - 60秒内重发限制
 */

import { apiClient } from './client'

// 发送短信验证码请求
export interface SendSMSRequest {
  phone_number: string
  purpose: string
}

// 验证短信验证码请求
export interface VerifySMSRequest {
  target: string
  verification_code: string
  purpose: string
}

// 验证码响应
export interface VerificationResponse {
  success: boolean
  message: string
  expires_in?: number
  masked_target?: string
  verified_user_id?: number
  remaining_attempts?: number
}

/**
 * 发送短信验证码（注册专用，无需认证）
 */
export async function sendRegistrationSMS(data: SendSMSRequest): Promise<VerificationResponse> {
  const response = await apiClient.post<VerificationResponse>('/api/v1/registration/sms/send', data)
  return response.data
}

/**
 * 验证短信验证码（注册专用，无需认证）
 */
export async function verifyRegistrationSMS(data: VerifySMSRequest): Promise<VerificationResponse> {
  const response = await apiClient.post<VerificationResponse>('/api/v1/registration/sms/verify', data)
  return response.data
}

/**
 * 发送短信验证码（需要认证）
 */
export async function sendSMS(data: SendSMSRequest): Promise<VerificationResponse> {
  const response = await apiClient.post<VerificationResponse>('/api/v1/mfa/sms/send', data)
  return response.data
}

/**
 * 验证短信验证码（需要认证）
 */
export async function verifySMS(data: VerifySMSRequest): Promise<VerificationResponse> {
  const response = await apiClient.post<VerificationResponse>('/api/v1/mfa/sms/verify', data)
  return response.data
}
