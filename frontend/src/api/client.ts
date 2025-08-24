import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { authUtils } from '@/utils/auth'

// API客户端配置
const API_BASE_URL = import.meta.env['VITE_API_BASE_URL'] || '/api'

// 创建axios实例
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加认证token
    const token = authUtils.getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  error => {
    // 处理401未授权错误
    if (error.response?.status === 401) {
      authUtils.logout()
    }
    return Promise.reject(error)
  }
)

// API响应类型
export interface ApiResponse<T = unknown> {
  success: boolean
  data: T
  message?: string
  errors?: string[]
}

// API错误类型
export class ApiError extends Error {
  public status?: number
  public errors?: string[]

  constructor(message: string, status?: number, errors?: string[]) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.errors = errors
  }
}
