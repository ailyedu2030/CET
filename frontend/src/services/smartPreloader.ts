/**
 * 智能预加载服务
 * 
 * 基于用户行为预测和预加载资源：
 * - 用户行为分析
 * - 智能预测算法
 * - 资源优先级管理
 * - 网络状态适配
 */

import { asyncLoader } from '@/utils/asyncLoader'
import { imageOptimizer } from '@/utils/imageOptimization'

// 用户行为类型
export type UserAction = 'click' | 'hover' | 'scroll' | 'focus' | 'route_change'

// 行为记录
export interface ActionRecord {
  action: UserAction
  target: string
  timestamp: number
  metadata?: Record<string, any>
}

// 预加载项目
export interface PreloadItem {
  id: string
  type: 'route' | 'image' | 'data' | 'component'
  url: string
  priority: number
  estimatedSize?: number
  dependencies?: string[]
}

// 预测结果
export interface PredictionResult {
  item: PreloadItem
  probability: number
  reason: string
}

// 网络状态
export interface NetworkStatus {
  effectiveType: '2g' | '3g' | '4g' | 'slow-2g' | 'unknown'
  downlink: number
  rtt: number
  saveData: boolean
}

// 智能预加载管理器
class SmartPreloaderManager {
  private actionHistory: ActionRecord[] = []
  private preloadQueue: PreloadItem[] = []
  private loadedItems = new Set<string>()
  private patterns = new Map<string, number>()
  private isEnabled = true
  private maxHistorySize = 1000
  private maxQueueSize = 50

  constructor() {
    this.initializeEventListeners()
    this.startPeriodicAnalysis()
  }

  /**
   * 初始化事件监听器
   */
  private initializeEventListeners(): void {
    // 监听点击事件
    document.addEventListener('click', (event) => {
      this.recordAction('click', this.getElementSelector(event.target as Element))
    })

    // 监听悬停事件
    document.addEventListener('mouseover', (event) => {
      this.recordAction('hover', this.getElementSelector(event.target as Element))
    })

    // 监听滚动事件
    let scrollTimeout: number | null = null
    document.addEventListener('scroll', () => {
      if (scrollTimeout) {
        clearTimeout(scrollTimeout)
      }
      scrollTimeout = window.setTimeout(() => {
        this.recordAction('scroll', `${window.scrollY}`)
      }, 100)
    })

    // 监听路由变化
    window.addEventListener('popstate', () => {
      this.recordAction('route_change', window.location.pathname)
    })
  }

  /**
   * 获取元素选择器
   */
  private getElementSelector(element: Element): string {
    if (!element) return 'unknown'
    
    // 优先使用ID
    if (element.id) {
      return `#${element.id}`
    }
    
    // 使用类名
    if (element.className) {
      const classes = element.className.split(' ').filter(Boolean)
      if (classes.length > 0) {
        return `.${classes[0]}`
      }
    }
    
    // 使用标签名
    return element.tagName.toLowerCase()
  }

  /**
   * 记录用户行为
   */
  recordAction(action: UserAction, target: string, metadata?: Record<string, any>): void {
    if (!this.isEnabled) return

    const record: ActionRecord = {
      action,
      target,
      timestamp: Date.now(),
      metadata,
    }

    this.actionHistory.push(record)

    // 限制历史记录大小
    if (this.actionHistory.length > this.maxHistorySize) {
      this.actionHistory = this.actionHistory.slice(-this.maxHistorySize)
    }

    // 更新模式
    this.updatePatterns(record)

    // 触发预测
    this.triggerPrediction()
  }

  /**
   * 更新行为模式
   */
  private updatePatterns(record: ActionRecord): void {
    const key = `${record.action}:${record.target}`
    const count = this.patterns.get(key) || 0
    this.patterns.set(key, count + 1)
  }

  private predictionTimeout: number | null = null

  /**
   * 触发预测分析
   */
  private triggerPrediction(): void {
    // 防抖处理
    if (this.predictionTimeout) {
      clearTimeout(this.predictionTimeout)
    }
    this.predictionTimeout = window.setTimeout(() => {
      this.performPrediction()
    }, 500)
  }

  /**
   * 执行预测分析
   */
  private performPrediction(): void {
    const predictions = this.generatePredictions()
    
    // 根据预测结果添加预加载项目
    predictions.forEach(prediction => {
      if (prediction.probability > 0.6) { // 概率阈值
        this.addToPreloadQueue(prediction.item)
      }
    })

    // 执行预加载
    this.executePreloading()
  }

  /**
   * 生成预测结果
   */
  private generatePredictions(): PredictionResult[] {
    const predictions: PredictionResult[] = []
    const recentActions = this.actionHistory.slice(-10) // 最近10个行为

    // 基于序列模式预测
    predictions.push(...this.predictBySequence(recentActions))
    
    // 基于频率模式预测
    predictions.push(...this.predictByFrequency())
    
    // 基于时间模式预测
    predictions.push(...this.predictByTime())

    // 去重并排序
    const uniquePredictions = this.deduplicatePredictions(predictions)
    return uniquePredictions.sort((a, b) => b.probability - a.probability)
  }

  /**
   * 基于序列模式预测
   */
  private predictBySequence(recentActions: ActionRecord[]): PredictionResult[] {
    const predictions: PredictionResult[] = []

    // 简单的序列匹配
    if (recentActions.length >= 2) {
      const lastAction = recentActions[recentActions.length - 1]
      const secondLastAction = recentActions[recentActions.length - 2]

      if (!lastAction || !secondLastAction) {
        return predictions
      }

      // 查找历史中相似的序列
      for (let i = 1; i < this.actionHistory.length; i++) {
        const current = this.actionHistory[i]
        const previous = this.actionHistory[i - 1]

        if (!current || !previous) {
          continue
        }

        if (
          previous.action === secondLastAction.action &&
          previous.target === secondLastAction.target &&
          current.action === lastAction.action &&
          current.target === lastAction.target
        ) {
          // 找到匹配序列，预测下一个可能的行为
          if (i + 1 < this.actionHistory.length) {
            const next = this.actionHistory[i + 1]
            if (next) {
              predictions.push({
                item: this.createPreloadItem(next),
                probability: 0.7,
                reason: 'sequence_pattern',
              })
            }
          }
        }
      }
    }

    return predictions
  }

  /**
   * 基于频率模式预测
   */
  private predictByFrequency(): PredictionResult[] {
    const predictions: PredictionResult[] = []
    const sortedPatterns = Array.from(this.patterns.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5) // 取前5个最频繁的模式

    sortedPatterns.forEach(([pattern, count]) => {
      const parts = pattern.split(':')
      if (parts.length >= 2) {
        const action = parts[0]
        const target = parts[1]
        const probability = Math.min(count / this.actionHistory.length, 0.8)

        if (probability > 0.3 && action && target) {
          predictions.push({
            item: this.createPreloadItemFromPattern(action as UserAction, target),
            probability,
            reason: 'frequency_pattern',
          })
        }
      }
    })

    return predictions
  }

  /**
   * 基于时间模式预测
   */
  private predictByTime(): PredictionResult[] {
    const predictions: PredictionResult[] = []
    const now = new Date()
    const currentHour = now.getHours()
    
    // 分析相同时间段的行为模式
    const sameHourActions = this.actionHistory.filter(record => {
      const recordTime = new Date(record.timestamp)
      return recordTime.getHours() === currentHour
    })

    if (sameHourActions.length > 0) {
      const mostCommon = this.getMostCommonAction(sameHourActions)
      if (mostCommon) {
        predictions.push({
          item: this.createPreloadItem(mostCommon),
          probability: 0.5,
          reason: 'time_pattern',
        })
      }
    }

    return predictions
  }

  /**
   * 获取最常见的行为
   */
  private getMostCommonAction(actions: ActionRecord[]): ActionRecord | null {
    const counts = new Map<string, { record: ActionRecord; count: number }>()
    
    actions.forEach(action => {
      const key = `${action.action}:${action.target}`
      const existing = counts.get(key)
      if (existing) {
        existing.count++
      } else {
        counts.set(key, { record: action, count: 1 })
      }
    })

    let maxCount = 0
    let mostCommon: ActionRecord | null = null
    
    counts.forEach(({ record, count }) => {
      if (count > maxCount) {
        maxCount = count
        mostCommon = record
      }
    })

    return mostCommon
  }

  /**
   * 创建预加载项目
   */
  private createPreloadItem(action: ActionRecord): PreloadItem {
    return {
      id: `${action.action}_${action.target}_${Date.now()}`,
      type: this.inferItemType(action),
      url: this.inferUrl(action),
      priority: this.calculatePriority(action),
    }
  }

  /**
   * 从模式创建预加载项目
   */
  private createPreloadItemFromPattern(action: UserAction, target: string): PreloadItem {
    return {
      id: `${action}_${target}_pattern`,
      type: this.inferItemTypeFromTarget(target),
      url: this.inferUrlFromTarget(target),
      priority: this.calculatePriorityFromPattern(action, target),
    }
  }

  /**
   * 推断项目类型
   */
  private inferItemType(action: ActionRecord): PreloadItem['type'] {
    if (action.target.includes('img') || action.target.includes('image')) {
      return 'image'
    }
    if (action.target.includes('route') || action.action === 'route_change') {
      return 'route'
    }
    if (action.target.includes('data') || action.target.includes('api')) {
      return 'data'
    }
    return 'component'
  }

  /**
   * 从目标推断项目类型
   */
  private inferItemTypeFromTarget(target: string): PreloadItem['type'] {
    if (target.includes('img') || target.includes('image')) {
      return 'image'
    }
    if (target.includes('route') || target.startsWith('/')) {
      return 'route'
    }
    return 'component'
  }

  /**
   * 推断URL
   */
  private inferUrl(action: ActionRecord): string {
    // 简化的URL推断逻辑
    if (action.action === 'route_change') {
      return action.target
    }
    return `/api/preload/${action.target}`
  }

  /**
   * 从目标推断URL
   */
  private inferUrlFromTarget(target: string): string {
    if (target.startsWith('/')) {
      return target
    }
    return `/api/preload/${target}`
  }

  /**
   * 计算优先级
   */
  private calculatePriority(action: ActionRecord): number {
    const baseScore = 50
    const actionWeights = {
      click: 30,
      hover: 20,
      focus: 25,
      scroll: 10,
      route_change: 40,
    }
    
    return baseScore + (actionWeights[action.action] || 0)
  }

  /**
   * 从模式计算优先级
   */
  private calculatePriorityFromPattern(action: UserAction, target: string): number {
    const frequency = this.patterns.get(`${action}:${target}`) || 0
    return Math.min(50 + frequency * 5, 100)
  }

  /**
   * 去重预测结果
   */
  private deduplicatePredictions(predictions: PredictionResult[]): PredictionResult[] {
    const seen = new Set<string>()
    return predictions.filter(prediction => {
      const key = prediction.item.id
      if (seen.has(key)) {
        return false
      }
      seen.add(key)
      return true
    })
  }

  /**
   * 添加到预加载队列
   */
  private addToPreloadQueue(item: PreloadItem): void {
    // 检查是否已经加载或在队列中
    if (this.loadedItems.has(item.id) || 
        this.preloadQueue.some(queueItem => queueItem.id === item.id)) {
      return
    }

    this.preloadQueue.push(item)
    
    // 按优先级排序
    this.preloadQueue.sort((a, b) => b.priority - a.priority)
    
    // 限制队列大小
    if (this.preloadQueue.length > this.maxQueueSize) {
      this.preloadQueue = this.preloadQueue.slice(0, this.maxQueueSize)
    }
  }

  /**
   * 执行预加载
   */
  private async executePreloading(): Promise<void> {
    if (!this.isEnabled || this.preloadQueue.length === 0) {
      return
    }

    // 检查网络状态
    const networkStatus = this.getNetworkStatus()
    if (networkStatus.saveData || networkStatus.effectiveType === 'slow-2g') {
      return // 在慢网络或省流量模式下不预加载
    }

    // 取出优先级最高的项目
    const item = this.preloadQueue.shift()
    if (!item) return

    try {
      await this.preloadItem(item)
      this.loadedItems.add(item.id)
    } catch (error) {
      // 预加载失败，静默处理
    }

    // 继续处理下一个项目（限制并发）
    setTimeout(() => this.executePreloading(), 100)
  }

  /**
   * 预加载单个项目
   */
  private async preloadItem(item: PreloadItem): Promise<void> {
    switch (item.type) {
      case 'image':
        await imageOptimizer.preloadImage(item.url)
        break
      case 'data':
        await asyncLoader.loadJSON(item.url)
        break
      case 'route':
      case 'component':
        await asyncLoader.preload(
          () => import(/* webpackChunkName: "preload" */ item.url),
          item.id
        )
        break
    }
  }

  /**
   * 获取网络状态
   */
  private getNetworkStatus(): NetworkStatus {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
    
    if (connection) {
      return {
        effectiveType: connection.effectiveType || 'unknown',
        downlink: connection.downlink || 0,
        rtt: connection.rtt || 0,
        saveData: connection.saveData || false,
      }
    }

    return {
      effectiveType: 'unknown',
      downlink: 0,
      rtt: 0,
      saveData: false,
    }
  }

  /**
   * 开始周期性分析
   */
  private startPeriodicAnalysis(): void {
    setInterval(() => {
      this.cleanupOldData()
      this.optimizePatterns()
    }, 60000) // 每分钟执行一次
  }

  /**
   * 清理旧数据
   */
  private cleanupOldData(): void {
    const oneHourAgo = Date.now() - 60 * 60 * 1000
    this.actionHistory = this.actionHistory.filter(record => record.timestamp > oneHourAgo)
  }

  /**
   * 优化模式数据
   */
  private optimizePatterns(): void {
    // 移除低频模式
    const minCount = Math.max(2, this.actionHistory.length * 0.01)
    for (const [pattern, count] of this.patterns.entries()) {
      if (count < minCount) {
        this.patterns.delete(pattern)
      }
    }
  }

  /**
   * 获取统计信息
   */
  getStats(): {
    actionCount: number
    patternCount: number
    queueSize: number
    loadedCount: number
  } {
    return {
      actionCount: this.actionHistory.length,
      patternCount: this.patterns.size,
      queueSize: this.preloadQueue.length,
      loadedCount: this.loadedItems.size,
    }
  }

  /**
   * 启用/禁用预加载
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled
  }

  /**
   * 清理所有数据
   */
  clear(): void {
    this.actionHistory = []
    this.preloadQueue = []
    this.loadedItems.clear()
    this.patterns.clear()
  }
}

// 导出单例实例
export const smartPreloader = new SmartPreloaderManager()
