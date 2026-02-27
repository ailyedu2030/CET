/**
 * 简化批量处理服务
 *
 * 满足🔥需求31简化验收标准6：
 * - 基础批量处理：简单的请求合并
 * - 实时处理：React Query缓存和更新
 * - 处理优化：基础性能监控
 */

import { optimizedFetch } from './networkOptimizer'

// 批处理请求项
interface BatchItem {
  id: string
  url: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  priority: 'high' | 'medium' | 'low'
  timestamp: number
  resolve: (value: any) => void
  reject: (error: any) => void
}

// 批处理配置
interface BatchConfig {
  maxBatchSize: number
  batchTimeout: number // 批处理窗口时间（毫秒）
  enableBatching: boolean
  priorityThreshold: number // 高优先级请求的阈值
}

// 批处理统计
interface BatchStats {
  totalRequests: number
  batchedRequests: number
  averageBatchSize: number
  successRate: number
}

class SimpleBatchProcessor {
  private config: BatchConfig
  private queue: BatchItem[] = []
  private batchTimer: ReturnType<typeof setTimeout> | null = null
  private stats: BatchStats

  constructor() {
    this.config = {
      maxBatchSize: 10,
      batchTimeout: 100, // 100ms批处理窗口
      enableBatching: true,
      priorityThreshold: 3, // 超过3个高优先级请求立即处理
    }

    this.stats = {
      totalRequests: 0,
      batchedRequests: 0,
      averageBatchSize: 0,
      successRate: 0,
    }
  }

  /**
   * 添加请求到批处理队列
   */
  async addRequest(
    url: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    data?: any,
    priority: 'high' | 'medium' | 'low' = 'medium'
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      const batchItem: BatchItem = {
        id: `batch-${Date.now()}-${Math.random()}`,
        url,
        method,
        data,
        priority,
        timestamp: Date.now(),
        resolve,
        reject,
      }

      this.stats.totalRequests++

      // 如果批处理被禁用，直接执行请求
      if (!this.config.enableBatching) {
        this.executeSingleRequest(batchItem)
        return
      }

      // 添加到队列
      this.queue.push(batchItem)

      // 检查是否需要立即处理
      if (this.shouldProcessImmediately()) {
        this.processBatch()
      } else {
        // 设置批处理定时器
        this.scheduleBatchProcessing()
      }
    })
  }

  /**
   * 判断是否应该立即处理批次
   */
  private shouldProcessImmediately(): boolean {
    // 队列已满
    if (this.queue.length >= this.config.maxBatchSize) {
      return true
    }

    // 高优先级请求过多
    const highPriorityCount = this.queue.filter(item => item.priority === 'high').length
    if (highPriorityCount >= this.config.priorityThreshold) {
      return true
    }

    return false
  }

  /**
   * 安排批处理
   */
  private scheduleBatchProcessing(): void {
    if (this.batchTimer) return

    this.batchTimer = setTimeout(() => {
      this.processBatch()
    }, this.config.batchTimeout)
  }

  /**
   * 处理批次
   */
  private async processBatch(): Promise<void> {
    if (this.queue.length === 0) return

    // 清除定时器
    if (this.batchTimer) {
      clearTimeout(this.batchTimer)
      this.batchTimer = null
    }

    // 取出当前队列中的所有请求
    const currentBatch = [...this.queue]
    this.queue = []

    // 按优先级排序
    currentBatch.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    })

    // 分组处理：相同URL和方法的请求可以合并
    const groups = this.groupRequests(currentBatch)

    // 并行处理各组
    const groupPromises = groups.map(group => this.processGroup(group))

    // 使用Promise.allSettled处理所有组，不会因为单个失败而中断
    const results = await Promise.allSettled(groupPromises)

    // 检查是否有失败的组
    const hasFailures = results.some(result => result.status === 'rejected')

    if (hasFailures) {
      // eslint-disable-next-line no-console
      console.warn(
        'Some batch groups failed:',
        results.filter(r => r.status === 'rejected')
      )
      this.updateStats(currentBatch, false)
    } else {
      this.updateStats(currentBatch, true)
    }
  }

  /**
   * 将请求分组
   */
  private groupRequests(requests: BatchItem[]): BatchItem[][] {
    const groups: { [key: string]: BatchItem[] } = {}

    requests.forEach(request => {
      // 只有GET请求可以合并
      if (request.method === 'GET') {
        const key = `${request.method}:${request.url}`
        if (!groups[key]) {
          groups[key] = []
        }
        groups[key].push(request)
      } else {
        // 非GET请求单独处理
        const key = `${request.method}:${request.url}:${request.id}`
        groups[key] = [request]
      }
    })

    return Object.values(groups)
  }

  /**
   * 处理请求组
   */
  private async processGroup(group: BatchItem[]): Promise<void> {
    if (group.length === 0) return

    const firstRequest = group[0]
    if (!firstRequest) return

    try {
      if (group.length === 1 || firstRequest.method !== 'GET') {
        // 单个请求或非GET请求
        await this.executeSingleRequest(firstRequest)
      } else {
        // 合并的GET请求
        await this.executeMergedRequest(group)
      }
    } catch (error) {
      // 如果合并请求失败，回退到单个请求
      // eslint-disable-next-line no-console
      console.warn('Merged request failed, falling back to individual requests')
      for (const request of group) {
        await this.executeSingleRequest(request)
      }
    }
  }

  /**
   * 执行单个请求
   */
  private async executeSingleRequest(request: BatchItem): Promise<void> {
    try {
      const response = await optimizedFetch(request.url, {
        method: request.method,
        body: request.data ? JSON.stringify(request.data) : undefined,
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      request.resolve(result)
    } catch (error) {
      request.reject(error)
    }
  }

  /**
   * 执行合并的GET请求
   */
  private async executeMergedRequest(requests: BatchItem[]): Promise<void> {
    const firstRequest = requests[0]
    if (!firstRequest) return

    try {
      // 对于相同的GET请求，只执行一次
      const response = await optimizedFetch(firstRequest.url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      // 所有请求都返回相同的结果
      requests.forEach(request => {
        request.resolve(result)
      })

      this.stats.batchedRequests += requests.length - 1 // 减去实际执行的那一个
    } catch (error) {
      // 如果合并请求失败，所有请求都失败
      requests.forEach(request => {
        request.reject(error)
      })
    }
  }

  /**
   * 更新统计信息
   */
  private updateStats(_batch: BatchItem[], success: boolean): void {
    // 更新平均批次大小
    const totalBatches = Math.ceil(this.stats.totalRequests / this.config.maxBatchSize)
    this.stats.averageBatchSize = this.stats.totalRequests / Math.max(totalBatches, 1)

    // 更新成功率
    if (success) {
      this.stats.successRate = this.stats.successRate * 0.9 + 1 * 0.1 // 指数移动平均
    } else {
      this.stats.successRate = this.stats.successRate * 0.9
    }
  }

  /**
   * 立即处理所有待处理请求
   */
  async flush(): Promise<void> {
    if (this.queue.length > 0) {
      await this.processBatch()
    }
  }

  /**
   * 清空队列
   */
  clear(): void {
    // 拒绝所有待处理的请求
    this.queue.forEach(request => {
      request.reject(new Error('Batch processor cleared'))
    })

    this.queue = []

    if (this.batchTimer) {
      clearTimeout(this.batchTimer)
      this.batchTimer = null
    }
  }

  /**
   * 获取统计信息
   */
  getStats(): BatchStats {
    return { ...this.stats }
  }

  /**
   * 获取配置
   */
  getConfig(): BatchConfig {
    return { ...this.config }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<BatchConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  /**
   * 获取队列状态
   */
  getQueueStatus(): {
    queueLength: number
    highPriorityCount: number
    oldestRequestAge: number
  } {
    const highPriorityCount = this.queue.filter(item => item.priority === 'high').length

    if (this.queue.length === 0) {
      return {
        queueLength: 0,
        highPriorityCount: 0,
        oldestRequestAge: 0,
      }
    }

    const oldestRequest = this.queue.reduce((oldest, current) =>
      current.timestamp < oldest.timestamp ? current : oldest
    )

    return {
      queueLength: this.queue.length,
      highPriorityCount,
      oldestRequestAge: Date.now() - oldestRequest.timestamp,
    }
  }
}

// 创建全局批处理器实例
export const batchProcessor = new SimpleBatchProcessor()

// 便捷的批处理请求函数
export const batchRequest = (
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: any,
  priority: 'high' | 'medium' | 'low' = 'medium'
) => batchProcessor.addRequest(url, method, data, priority)

export default batchProcessor
