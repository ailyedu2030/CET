import { User } from '../types/auth'

// 认证工具函数
export const authUtils = {
  // 获取存储的token
  getToken(): string | null {
    return localStorage.getItem('token')
  },

  // 设置token
  setToken(token: string): void {
    localStorage.setItem('token', token)
  },

  // 移除token
  removeToken(): void {
    localStorage.removeItem('token')
  },

  // 获取当前用户信息
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user')
    if (!userStr) return null

    try {
      return JSON.parse(userStr) as User
    } catch {
      return null
    }
  },

  // 设置用户信息
  setCurrentUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user))
  },

  // 移除用户信息
  removeCurrentUser(): void {
    localStorage.removeItem('user')
  },

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!this.getToken()
  },

  // 检查用户权限
  hasPermission(requiredRole: User['userType']): boolean {
    const user = this.getCurrentUser()
    if (!user) return false

    // 管理员拥有所有权限
    if (user.userType === 'admin') return true

    // 检查具体权限
    return user.userType === requiredRole
  },

  // 登出
  logout(): void {
    this.removeToken()
    this.removeCurrentUser()
    window.location.href = '/login'
  },
}
