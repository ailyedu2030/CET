/**
 * 离线同步服务
 * 
 * 提供离线数据同步功能：
 * - 自动同步机制
 * - 冲突检测和解决
 * - 同步状态管理
 * - 重试机制
 */

import { notifications } from '@mantine/notifications'

import { apiClient } from '@/api/client'
import {
  offlineStorage,
  STORES,
  type SyncQueueItem,
  type ConflictItem,
  type OfflineData,
  type StoreType
} from './offlineStorage'

// 同步状态
export interface SyncStatus {
  isSync: boolean
  lastSyncTime: number | null
  pendingItems: number
  conflicts: ConflictItem[]
  errors: string[]
}

// 同步配置
const SYNC_CONFIG = {
  MAX_RETRY_COUNT: 3,
  RETRY_DELAY: 1000, // 1秒
  BATCH_SIZE: 10,
  SYNC_INTERVAL: 30000, // 30秒
}

// 离线同步管理器
class OfflineSyncManager {
  private syncStatus: SyncStatus = {
    isSync: false,
    lastSyncTime: null,
    pendingItems: 0,
    conflicts: [],
    errors: [],
  }
  
  private syncInterval: number | null = null
  private listeners: Array<(status: SyncStatus) => void> = []

  /**
   * 初始化同步服务
   */
  async initialize(): Promise<void> {
    await offlineStorage.initialize()
    
    // 监听网络状态变化
    window.addEventListener('online', () => {
      this.handleNetworkOnline()
    })
    
    window.addEventListener('offline', () => {
      this.handleNetworkOffline()
    })
    
    // 如果当前在线，启动同步
    if (navigator.onLine) {
      this.startAutoSync()
    }
    
    // 更新初始状态
    await this.updateSyncStatus()
  }

  /**
   * 添加状态监听器
   */
  addStatusListener(listener: (status: SyncStatus) => void): void {
    this.listeners.push(listener)
  }

  /**
   * 移除状态监听器
   */
  removeStatusListener(listener: (status: SyncStatus) => void): void {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  /**
   * 获取当前同步状态
   */
  getSyncStatus(): SyncStatus {
    return { ...this.syncStatus }
  }

  /**
   * 手动触发同步
   */
  async manualSync(): Promise<void> {
    if (!navigator.onLine) {
      throw new Error('网络未连接，无法同步')
    }
    
    await this.performSync()
  }

  /**
   * 添加离线操作到队列
   */
  async addOfflineOperation(
    action: 'create' | 'update' | 'delete',
    type: StoreType,
    data: any
  ): Promise<void> {
    const queueItem: SyncQueueItem = {
      id: `${type}_${data.id || Date.now()}_${action}`,
      action,
      type,
      data,
      timestamp: Date.now(),
      retryCount: 0,
    }
    
    await offlineStorage.addToSyncQueue(queueItem)
    await this.updateSyncStatus()
    
    // 如果在线，立即尝试同步
    if (navigator.onLine) {
      this.performSync().catch(() => {
        // 同步失败，静默处理
      })
    }
  }

  /**
   * 处理网络连接
   */
  private async handleNetworkOnline(): Promise<void> {
    notifications.show({
      title: '网络已连接',
      message: '正在同步离线期间的数据...',
      color: 'green',
    })
    
    this.startAutoSync()
    await this.performSync()
  }

  /**
   * 处理网络断开
   */
  private handleNetworkOffline(): void {
    notifications.show({
      title: '网络已断开',
      message: '应用将在离线模式下继续工作',
      color: 'orange',
    })
    
    this.stopAutoSync()
  }

  /**
   * 启动自动同步
   */
  private startAutoSync(): void {
    if (this.syncInterval) return
    
    this.syncInterval = window.setInterval(() => {
      if (navigator.onLine) {
        this.performSync().catch(() => {
          // 同步失败，静默处理
        })
      }
    }, SYNC_CONFIG.SYNC_INTERVAL)
  }

  /**
   * 停止自动同步
   */
  private stopAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
      this.syncInterval = null
    }
  }

  /**
   * 执行同步
   */
  private async performSync(): Promise<void> {
    if (this.syncStatus.isSync) return
    
    this.syncStatus.isSync = true
    this.notifyListeners()
    
    try {
      const syncQueue = await offlineStorage.getSyncQueue()
      
      if (syncQueue.length === 0) {
        this.syncStatus.lastSyncTime = Date.now()
        return
      }
      
      // 分批处理同步项目
      const batches = this.createBatches(syncQueue, SYNC_CONFIG.BATCH_SIZE)
      
      for (const batch of batches) {
        await this.processBatch(batch)
      }
      
      this.syncStatus.lastSyncTime = Date.now()
      this.syncStatus.errors = []
      
      notifications.show({
        title: '同步完成',
        message: `成功同步 ${syncQueue.length} 项数据`,
        color: 'green',
      })
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '同步失败'
      this.syncStatus.errors.push(errorMessage)
      
      notifications.show({
        title: '同步失败',
        message: errorMessage,
        color: 'red',
      })
    } finally {
      this.syncStatus.isSync = false
      await this.updateSyncStatus()
    }
  }

  /**
   * 处理同步批次
   */
  private async processBatch(batch: SyncQueueItem[]): Promise<void> {
    const promises = batch.map(item => this.processSyncItem(item))
    await Promise.allSettled(promises)
  }

  /**
   * 处理单个同步项目
   */
  private async processSyncItem(item: SyncQueueItem): Promise<void> {
    try {
      let response: any
      
      switch (item.action) {
        case 'create':
          response = await this.createOnServer(item)
          break
        case 'update':
          response = await this.updateOnServer(item)
          break
        case 'delete':
          response = await this.deleteOnServer(item)
          break
      }
      
      // 同步成功，从队列中移除
      await offlineStorage.delete(STORES.SYNC_QUEUE, item.id)
      
      // 更新本地数据
      if (response && item.action !== 'delete') {
        await this.updateLocalData(item.type, response)
      }
      
    } catch (error) {
      // 增加重试次数
      item.retryCount++
      item.lastError = error instanceof Error ? error.message : 'Unknown error'
      
      if (item.retryCount >= SYNC_CONFIG.MAX_RETRY_COUNT) {
        // 达到最大重试次数，检查是否为冲突
        if (this.isConflictError(error)) {
          await this.handleConflict(item, error)
        } else {
          // 移除失败的项目
          await offlineStorage.delete(STORES.SYNC_QUEUE, item.id)
        }
      } else {
        // 更新重试信息
        await offlineStorage.store(STORES.SYNC_QUEUE, {
          id: item.id,
          type: STORES.SYNC_QUEUE,
          data: item,
          lastModified: Date.now(),
          version: 1,
          needsSync: true,
        })
      }
    }
  }

  /**
   * 在服务器上创建数据
   */
  private async createOnServer(item: SyncQueueItem): Promise<any> {
    const endpoint = this.getApiEndpoint(item.type, 'create')
    return await apiClient.post(endpoint, item.data)
  }

  /**
   * 在服务器上更新数据
   */
  private async updateOnServer(item: SyncQueueItem): Promise<any> {
    const endpoint = this.getApiEndpoint(item.type, 'update', item.data.id)
    return await apiClient.put(endpoint, item.data)
  }

  /**
   * 在服务器上删除数据
   */
  private async deleteOnServer(item: SyncQueueItem): Promise<any> {
    const endpoint = this.getApiEndpoint(item.type, 'delete', item.data.id)
    return await apiClient.delete(endpoint)
  }

  /**
   * 获取API端点
   */
  private getApiEndpoint(type: StoreType, _action: string, id?: string): string {
    const baseEndpoints: Record<string, string> = {
      [STORES.LESSON_PLANS]: '/api/v1/courses/lesson-plans',
      [STORES.RESOURCES]: '/api/v1/resources',
      [STORES.STUDENTS]: '/api/v1/users/students',
    }

    const base = baseEndpoints[type]
    if (!base) {
      throw new Error(`Unknown store type: ${type}`)
    }

    return id ? `${base}/${id}` : base
  }

  /**
   * 更新本地数据
   */
  private async updateLocalData(type: StoreType, serverData: any): Promise<void> {
    const offlineData: OfflineData = {
      id: serverData.id,
      type,
      data: serverData,
      lastModified: Date.now(),
      version: serverData.version || 1,
      needsSync: false,
    }
    
    await offlineStorage.store(type, offlineData)
  }

  /**
   * 检查是否为冲突错误
   */
  private isConflictError(error: any): boolean {
    return error?.status === 409 || error?.message?.includes('conflict')
  }

  /**
   * 处理冲突
   */
  private async handleConflict(item: SyncQueueItem, error: any): Promise<void> {
    const conflict: ConflictItem = {
      id: item.data.id,
      type: item.type,
      localData: item.data,
      serverData: error.serverData || {},
      localTimestamp: item.timestamp,
      serverTimestamp: error.serverTimestamp || Date.now(),
      conflictFields: error.conflictFields || [],
    }
    
    this.syncStatus.conflicts.push(conflict)
    
    // 从同步队列中移除冲突项目
    await offlineStorage.delete(STORES.SYNC_QUEUE, item.id)
  }

  /**
   * 创建批次
   */
  private createBatches<T>(items: T[], batchSize: number): T[][] {
    const batches: T[][] = []
    for (let i = 0; i < items.length; i += batchSize) {
      batches.push(items.slice(i, i + batchSize))
    }
    return batches
  }

  /**
   * 更新同步状态
   */
  private async updateSyncStatus(): Promise<void> {
    const syncQueue = await offlineStorage.getSyncQueue()
    this.syncStatus.pendingItems = syncQueue.length
    this.notifyListeners()
  }

  /**
   * 通知监听器
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      listener(this.getSyncStatus())
    })
  }
}

// 导出单例实例
export const offlineSync = new OfflineSyncManager()

// 导出冲突解决函数
export const conflictResolver = {
  /**
   * 解决冲突 - 使用本地数据
   */
  async resolveWithLocal(conflict: ConflictItem): Promise<void> {
    await offlineSync.addOfflineOperation('update', conflict.type, conflict.localData)
  },

  /**
   * 解决冲突 - 使用服务器数据
   */
  async resolveWithServer(conflict: ConflictItem): Promise<void> {
    await offlineStorage.store(conflict.type, {
      id: conflict.id,
      type: conflict.type,
      data: conflict.serverData,
      lastModified: Date.now(),
      version: conflict.serverData.version || 1,
      needsSync: false,
    })
  },

  /**
   * 解决冲突 - 手动合并
   */
  async resolveWithMerge(conflict: ConflictItem, mergedData: any): Promise<void> {
    await offlineSync.addOfflineOperation('update', conflict.type, mergedData)
  },
}
