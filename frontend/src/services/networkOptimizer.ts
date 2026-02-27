/**
 * 简化网络优化服务
 *
 * 满足🔥需求31简化验收标准2：
 * - 基础网络状态检测和优化
 * - 简单的请求重试和缓存
 */

// 网络状态检测结果
interface NetworkStatus {
  isOnline: boolean
  quality: 'excellent' | 'good' | 'fair' | 'poor'
  lastCheck: number
}

// 简化的网络配置
interface NetworkConfig {
  requestTimeout: number
  retryAttempts: number
  enableRetry: boolean
}

class SimpleNetworkOptimizer {
  private config: NetworkConfig
  private networkStatus: NetworkStatus
  private listeners: Array<(status: NetworkStatus) => void> = []

  constructor() {
    this.config = {
      requestTimeout: 10000,
      retryAttempts: 3,
      enableRetry: true,
    }

    this.networkStatus = {
      isOnline: navigator.onLine,
      quality: 'good',
      lastCheck: Date.now(),
    }

    this.initializeNetworkMonitoring()
  }

  /**
   * 初始化网络监控
   */
  private initializeNetworkMonitoring(): void {
    // 监听网络状态变化
    window.addEventListener('online', () => {
      this.updateNetworkStatus(true)
    })

    window.addEventListener('offline', () => {
      this.updateNetworkStatus(false)
    })

    // 定期检测网络质量
    setInterval(() => {
      this.detectNetworkQuality()
    }, 30000) // 每30秒检测一次
  }

  /**
   * 更新网络状态
   */
  private updateNetworkStatus(isOnline: boolean): void {
    this.networkStatus = {
      ...this.networkStatus,
      isOnline,
      lastCheck: Date.now(),
    }

    // 通知所有监听器
    this.listeners.forEach(listener => listener(this.networkStatus))
  }

  /**
   * 简化的网络质量检测
   */
  async detectNetworkQuality(): Promise<void> {
    if (!this.networkStatus.isOnline) return

    try {
      const startTime = performance.now()

      // 使用资源健康检查API测试网络
      const response = await fetch('/api/v1/resources/health', {
        method: 'GET',
        cache: 'no-cache',
      })

      const endTime = performance.now()
      const latency = endTime - startTime

      // 简化的质量判断
      let quality: 'excellent' | 'good' | 'fair' | 'poor'

      if (latency < 100 && response.ok) {
        quality = 'excellent'
      } else if (latency < 300 && response.ok) {
        quality = 'good'
      } else if (latency < 1000 && response.ok) {
        quality = 'fair'
      } else {
        quality = 'poor'
      }

      this.networkStatus = {
        ...this.networkStatus,
        quality,
        lastCheck: Date.now(),
      }

      // 通知监听器
      this.listeners.forEach(listener => listener(this.networkStatus))
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn('Network quality detection failed:', error)
      this.networkStatus = {
        ...this.networkStatus,
        quality: 'poor',
        lastCheck: Date.now(),
      }
    }
  }

  /**
   * 优化的fetch请求（带重试）
   */
  async optimizedFetch(url: string, options: Record<string, any> = {}): Promise<Response> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.config.requestTimeout)

    const fetchOptions: Record<string, any> = {
      ...options,
      signal: controller.signal,
    }

    let lastError: Error | null = null

    for (let attempt = 0; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, fetchOptions)
        clearTimeout(timeoutId)
        return response
      } catch (error) {
        lastError = error as Error

        if (attempt < this.config.retryAttempts && this.config.enableRetry) {
          // 简单的指数退避
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000))
        }
      }
    }

    clearTimeout(timeoutId)
    throw lastError || new Error('Request failed after retries')
  }

  /**
   * 添加网络状态监听器
   */
  addStatusListener(listener: (status: NetworkStatus) => void): void {
    this.listeners.push(listener)
  }

  /**
   * 移除网络状态监听器
   */
  removeStatusListener(listener: (status: NetworkStatus) => void): void {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  /**
   * 获取当前网络状态
   */
  getNetworkStatus(): NetworkStatus {
    return { ...this.networkStatus }
  }

  /**
   * 获取配置
   */
  getConfig(): NetworkConfig {
    return { ...this.config }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<NetworkConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }
}

// 创建全局网络优化器实例
export const networkOptimizer = new SimpleNetworkOptimizer()

// 导出优化的fetch函数
export const optimizedFetch = (url: string, options?: Record<string, any>) =>
  networkOptimizer.optimizedFetch(url, options)

export default networkOptimizer
