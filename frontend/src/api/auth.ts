/**
 * 认证相关API服务
 * 与后端 /api/v1/auth 端点集成
 */

import { apiClient } from './client'

// 登录请求接口
export interface LoginRequest {
  username: string
  password: string
  user_type: 'student' | 'teacher' | 'admin'
}

// 后端API响应接口（匹配后端LoginResponse）
export interface BackendLoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user_info: {
    id: number
    username: string
    email: string
    real_name: string
    user_type: string
    is_active: boolean
    is_verified: boolean
    last_login: string | null
  }
}

// 前端使用的登录响应接口
export interface LoginResponse {
  success: boolean
  user: {
    id: string
    username: string
    userType: 'student' | 'teacher' | 'admin'
    email: string
    real_name: string
    lastLogin: string
    is_active: boolean
  }
  token: string
  refresh_token: string
  expires_in: number
}

// 刷新token请求
export interface RefreshTokenRequest {
  refresh_token: string
}

// 刷新token响应
export interface RefreshTokenResponse {
  success: boolean
  token: string
  refresh_token: string
  expires_in: number
}

// 登出响应
export interface LogoutResponse {
  success: boolean
  message: string
}

// 密码修改请求接口 - 需求10验收标准5
export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

// 密码修改响应接口
export interface PasswordChangeResponse {
  success: boolean
  message: string
}

/**
 * 用户登录
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<BackendLoginResponse>('/api/v1/users/auth/login', data)

  // 转换后端响应格式为前端格式
  const backendData = response.data
  return {
    success: true,
    user: {
      id: backendData.user_info.id.toString(),
      username: backendData.user_info.username,
      userType: backendData.user_info.user_type as 'student' | 'teacher' | 'admin',
      email: backendData.user_info.email,
      real_name: backendData.user_info.real_name,
      lastLogin: backendData.user_info.last_login || new Date().toISOString(),
      is_active: backendData.user_info.is_active,
    },
    token: backendData.access_token,
    refresh_token: backendData.refresh_token,
    expires_in: backendData.expires_in,
  }
}

/**
 * 用户登出
 */
export async function logout(): Promise<LogoutResponse> {
  const response = await apiClient.post<{ message: string }>('/api/v1/users/auth/logout')
  return { success: true, message: response.data.message }
}

/**
 * 刷新访问token
 */
export async function refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<RefreshTokenResponse>('/api/v1/users/auth/refresh', data)
  return response.data
}

/**
 * 验证token有效性
 */
export async function verifyToken(): Promise<{ valid: boolean; user?: LoginResponse['user'] }> {
  try {
    const response = await apiClient.get<{
      valid: boolean
      user_id: number
      username: string
      user_type: string
      is_verified: boolean
      last_login: string | null
    }>('/api/v1/users/auth/verify-token')

    return {
      valid: response.data.valid,
      user: {
        id: response.data.user_id.toString(),
        username: response.data.username,
        userType: response.data.user_type as 'student' | 'teacher' | 'admin',
        email: '', // 需要从其他接口获取
        real_name: '', // 需要从其他接口获取
        lastLogin: response.data.last_login || new Date().toISOString(),
        is_active: true,
      },
    }
  } catch {
    return { valid: false }
  }
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<LoginResponse['user']> {
  const response = await apiClient.get<{ user: LoginResponse['user'] }>(
    '/api/v1/users/auth/profile'
  )
  return response.data.user
}

/**
 * 修改密码 - 需求10验收标准5：定期提醒密码更新
 */
export async function changePassword(data: PasswordChangeRequest): Promise<PasswordChangeResponse> {
  const response = await apiClient.post<{ message: string }>(
    '/api/v1/users/auth/change-password',
    data
  )
  return { success: true, message: response.data.message }
}

/**
 * 获取密码安全信息
 */
export async function getPasswordInfo(): Promise<{
  last_change: string
  days_since_change: number
  should_remind: boolean
}> {
  const response = await apiClient.get('/api/v1/users/auth/password-info')
  return response.data
}
