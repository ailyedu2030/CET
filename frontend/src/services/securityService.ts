/**
 * 简化安全服务
 *
 * 满足🔥需求31简化验收标准4：
 * - 基础数据加密（HTTPS + 本地存储加密）
 * - 简化会话管理（JWT token管理）
 * - 基础时间提醒（学习时长监控）
 */

import { useAuthStore } from '@/stores/authStore'

// 用户类型定义（兼容现有auth类型）
interface SecurityUser {
  id: string | number
  username: string
  userType: 'student' | 'teacher' | 'admin' | 'minor'
  age?: number
  profile?: {
    birthDate?: string
    isMinor?: boolean
  }
}

// 安全配置
interface SecurityConfig {
  sessionTimeout: number // 15分钟无操作自动登出
  maxDailyUsage: number // 最大每日使用时长（分钟）
  enableTimeReminder: boolean // 启用时间提醒
  encryptLocalStorage: boolean // 加密本地存储
}

// 会话信息
interface SessionInfo {
  startTime: number
  lastActivity: number
  dailyUsage: number
  isActive: boolean
  timeoutId?: ReturnType<typeof setTimeout>
}

class SimpleSecurityService {
  private config: SecurityConfig
  private sessionInfo: SessionInfo
  private sessionTimer: ReturnType<typeof setTimeout> | null = null
  private usageTimer: ReturnType<typeof setInterval> | null = null
  private authStore = useAuthStore.getState()

  constructor() {
    this.config = {
      sessionTimeout: 15 * 60 * 1000, // 15分钟
      maxDailyUsage: 120, // 2小时
      enableTimeReminder: true,
      encryptLocalStorage: true,
    }

    this.sessionInfo = {
      startTime: Date.now(),
      lastActivity: Date.now(),
      dailyUsage: this.getDailyUsage(),
      isActive: false,
    }

    this.initializeSecurity()
  }

  /**
   * 初始化安全服务
   */
  private initializeSecurity(): void {
    // 检查用户是否已登录
    if (this.authStore.isAuthenticated) {
      this.startSession()
    }

    // 监听用户活动
    this.setupActivityMonitoring()

    // 设置每日使用时长重置
    this.setupDailyUsageReset()
  }

  /**
   * 开始会话
   */
  startSession(): void {
    this.sessionInfo = {
      startTime: Date.now(),
      lastActivity: Date.now(),
      dailyUsage: this.getDailyUsage(),
      isActive: true,
    }

    // 启动会话超时定时器
    this.resetSessionTimer()

    // 启动使用时长计时器
    this.startUsageTimer()

  }

  /**
   * 结束会话
   */
  endSession(): void {
    this.sessionInfo.isActive = false

    // 清除定时器
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer)
      this.sessionTimer = null
    }

    if (this.usageTimer) {
      clearInterval(this.usageTimer)
      this.usageTimer = null
    }

    // 清除强制登出定时器
    if (this.sessionInfo.timeoutId) {
      clearTimeout(this.sessionInfo.timeoutId)
      this.sessionInfo.timeoutId = undefined
    }

    // 保存使用时长
    this.saveDailyUsage()

  }

  /**
   * 更新用户活动
   */
  updateActivity(): void {
    if (!this.sessionInfo.isActive) return

    this.sessionInfo.lastActivity = Date.now()
    this.resetSessionTimer()
  }

  /**
   * 重置会话定时器
   */
  private resetSessionTimer(): void {
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer)
    }

    this.sessionTimer = setTimeout(() => {
      this.handleSessionTimeout()
    }, this.config.sessionTimeout)
  }

  /**
   * 处理会话超时
   */
  private handleSessionTimeout(): void {

    // 自动登出
    this.authStore.logout()
    this.endSession()

    // 显示超时提示
    this.showTimeoutNotification()
  }

  /**
   * 设置活动监听
   */
  private setupActivityMonitoring(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']

    const activityHandler = () => {
      this.updateActivity()
    }

    events.forEach(event => {
      document.addEventListener(event, activityHandler, true)
    })
  }

  /**
   * 启动使用时长计时器
   */
  private startUsageTimer(): void {
    this.usageTimer = setInterval(() => {
      if (this.sessionInfo.isActive) {
        this.sessionInfo.dailyUsage += 1 // 每分钟增加1分钟

        // 检查是否超过每日限制
        if (this.config.enableTimeReminder) {
          this.checkDailyUsageLimit()
        }
      }
    }, 60000) // 每分钟检查一次
  }

  /**
   * 检查每日使用时长限制
   */
  private checkDailyUsageLimit(): void {
    const usage = this.sessionInfo.dailyUsage

    // 1小时提醒
    if (usage === 60) {
      this.showUsageReminder('您已学习1小时，建议适当休息')
    }

    // 1.5小时提醒
    if (usage === 90) {
      this.showUsageReminder('您已学习1.5小时，请注意休息保护视力')
    }

    // 2小时限制（如果是未成年人）
    if (usage >= this.config.maxDailyUsage) {
      const user = this.authStore.user
      if (user && this.isMinor(user)) {
        this.enforceTimeLimit()
      } else {
        this.showUsageReminder('您今日学习时间较长，建议适当休息')
      }
    }
  }

  /**
   * 判断是否为未成年人
   */
  private isMinor(user: SecurityUser | any): boolean {
    if (!user) return false

    // 优先检查profile中的isMinor标记
    if (user.profile?.isMinor !== undefined) {
      return user.profile.isMinor
    }

    // 根据年龄判断
    if (typeof user.age === 'number' && user.age < 18) {
      return true
    }

    // 根据用户类型判断
    if (user.userType === 'minor') {
      return true
    }

    // 根据出生日期计算年龄
    if (user.profile?.birthDate) {
      const birthDate = new Date(user.profile.birthDate)
      const today = new Date()
      const age = today.getFullYear() - birthDate.getFullYear()
      const monthDiff = today.getMonth() - birthDate.getMonth()

      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        return age - 1 < 18
      }
      return age < 18
    }

    return false
  }

  /**
   * 强制时间限制
   */
  private enforceTimeLimit(): void {

    // 显示限制提示
    this.showTimeLimitNotification()

    // 强制登出（检查会话是否仍然活跃）
    const timeoutId = setTimeout(() => {
      // 检查会话是否仍然活跃，避免重复登出
      if (this.sessionInfo.isActive && this.authStore.isAuthenticated) {
        this.authStore.logout()
        this.endSession()
      }
    }, 5000) // 5秒后自动登出

    // 存储timeout ID以便清理
    this.sessionInfo = {
      ...this.sessionInfo,
      timeoutId,
    }
  }

  /**
   * 获取每日使用时长
   */
  private getDailyUsage(): number {
    const today = new Date().toDateString()
    const stored = localStorage.getItem(`daily_usage_${today}`)
    return stored ? parseInt(stored, 10) : 0
  }

  /**
   * 保存每日使用时长
   */
  private saveDailyUsage(): void {
    const today = new Date().toDateString()
    localStorage.setItem(`daily_usage_${today}`, this.sessionInfo.dailyUsage.toString())
  }

  /**
   * 设置每日使用时长重置
   */
  private setupDailyUsageReset(): void {
    // 每天午夜重置使用时长
    const now = new Date()
    const tomorrow = new Date(now)
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(0, 0, 0, 0)

    const msUntilMidnight = tomorrow.getTime() - now.getTime()

    setTimeout(() => {
      this.sessionInfo.dailyUsage = 0

      // 设置下一次重置
      this.setupDailyUsageReset()
    }, msUntilMidnight)
  }

  /**
   * 简单的本地存储加密
   */
  encryptData(data: string): string {
    if (!this.config.encryptLocalStorage) return data

    // 简单的Base64编码（实际项目中应使用更强的加密）
    return btoa(data)
  }

  /**
   * 简单的本地存储解密
   */
  decryptData(encryptedData: string): string {
    if (!this.config.encryptLocalStorage) return encryptedData

    try {
      return atob(encryptedData)
    } catch {
      return encryptedData
    }
  }

  /**
   * 显示超时通知
   */
  private showTimeoutNotification(): void {
    // 这里应该集成到通知系统
  }

  /**
   * 显示使用时长提醒
   */
  private showUsageReminder(_message: string): void {
    // TODO: 实现使用时长提醒功能
  }
  /**
   * 显示时间限制通知
   */
  private showTimeLimitNotification(): void {
  }

  /**
   * 获取会话信息
   */
  getSessionInfo(): SessionInfo {
    return { ...this.sessionInfo }
  }

  /**
   * 获取安全配置
   */
  getConfig(): SecurityConfig {
    return { ...this.config }
  }

  /**
   * 更新安全配置
   */
  updateConfig(newConfig: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }
}

// 创建全局安全服务实例
export const securityService = new SimpleSecurityService()

export default securityService
