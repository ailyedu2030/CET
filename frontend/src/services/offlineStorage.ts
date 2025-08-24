/**
 * 离线存储服务
 * 
 * 提供离线数据存储和管理功能：
 * - IndexedDB数据库操作
 * - 离线数据缓存
 * - 数据版本控制
 * - 冲突检测
 */

// 数据库配置
const DB_NAME = 'CET4LearningOfflineDB'
const DB_VERSION = 1

// 存储表名
export const STORES = {
  LESSON_PLANS: 'lessonPlans',
  RESOURCES: 'resources',
  STUDENTS: 'students',
  SYNC_QUEUE: 'syncQueue',
  METADATA: 'metadata',
} as const

export type StoreType = typeof STORES[keyof typeof STORES]

// 数据类型定义
export interface OfflineData {
  id: string
  type: StoreType
  data: any
  lastModified: number
  version: number
  isDeleted?: boolean
  needsSync?: boolean
  conflictData?: any
}

export interface SyncQueueItem {
  id: string
  action: 'create' | 'update' | 'delete'
  type: StoreType
  data: any
  timestamp: number
  retryCount: number
  lastError?: string
}

export interface ConflictItem {
  id: string
  type: StoreType
  localData: any
  serverData: any
  localTimestamp: number
  serverTimestamp: number
  conflictFields: string[]
}

// 离线存储管理器
class OfflineStorageManager {
  private db: IDBDatabase | null = null
  private isInitialized = false

  /**
   * 初始化数据库
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onerror = () => {
        reject(new Error('Failed to open IndexedDB'))
      }

      request.onsuccess = () => {
        this.db = request.result
        this.isInitialized = true
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        // 创建教案存储
        if (!db.objectStoreNames.contains(STORES.LESSON_PLANS)) {
          const lessonStore = db.createObjectStore(STORES.LESSON_PLANS, { keyPath: 'id' })
          lessonStore.createIndex('lastModified', 'lastModified')
          lessonStore.createIndex('needsSync', 'needsSync')
        }

        // 创建资源存储
        if (!db.objectStoreNames.contains(STORES.RESOURCES)) {
          const resourceStore = db.createObjectStore(STORES.RESOURCES, { keyPath: 'id' })
          resourceStore.createIndex('type', 'type')
          resourceStore.createIndex('lastModified', 'lastModified')
        }

        // 创建学生存储
        if (!db.objectStoreNames.contains(STORES.STUDENTS)) {
          const studentStore = db.createObjectStore(STORES.STUDENTS, { keyPath: 'id' })
          studentStore.createIndex('lastModified', 'lastModified')
        }

        // 创建同步队列
        if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
          const syncStore = db.createObjectStore(STORES.SYNC_QUEUE, { keyPath: 'id' })
          syncStore.createIndex('timestamp', 'timestamp')
          syncStore.createIndex('retryCount', 'retryCount')
        }

        // 创建元数据存储
        if (!db.objectStoreNames.contains(STORES.METADATA)) {
          db.createObjectStore(STORES.METADATA, { keyPath: 'key' })
        }
      }
    })
  }

  /**
   * 存储数据
   */
  async store(storeName: StoreType, data: OfflineData): Promise<void> {
    await this.ensureInitialized()
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      
      const request = store.put(data)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(new Error(`Failed to store data in ${storeName}`))
    })
  }

  /**
   * 获取数据
   */
  async get(storeName: StoreType, id: string): Promise<OfflineData | null> {
    await this.ensureInitialized()
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      
      const request = store.get(id)
      
      request.onsuccess = () => {
        resolve(request.result || null)
      }
      request.onerror = () => reject(new Error(`Failed to get data from ${storeName}`))
    })
  }

  /**
   * 获取所有数据
   */
  async getAll(storeName: StoreType): Promise<OfflineData[]> {
    await this.ensureInitialized()
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      
      const request = store.getAll()
      
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(new Error(`Failed to get all data from ${storeName}`))
    })
  }

  /**
   * 删除数据
   */
  async delete(storeName: StoreType, id: string): Promise<void> {
    await this.ensureInitialized()
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      
      const request = store.delete(id)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(new Error(`Failed to delete data from ${storeName}`))
    })
  }

  /**
   * 添加到同步队列
   */
  async addToSyncQueue(item: SyncQueueItem): Promise<void> {
    await this.store(STORES.SYNC_QUEUE, {
      id: item.id,
      type: STORES.SYNC_QUEUE,
      data: item,
      lastModified: Date.now(),
      version: 1,
      needsSync: true,
    })
  }

  /**
   * 获取需要同步的数据
   */
  async getSyncQueue(): Promise<SyncQueueItem[]> {
    const items = await this.getAll(STORES.SYNC_QUEUE)
    return items.map(item => item.data)
  }

  /**
   * 清空同步队列
   */
  async clearSyncQueue(): Promise<void> {
    await this.ensureInitialized()
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORES.SYNC_QUEUE], 'readwrite')
      const store = transaction.objectStore(STORES.SYNC_QUEUE)
      
      const request = store.clear()
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(new Error('Failed to clear sync queue'))
    })
  }

  /**
   * 获取存储统计信息
   */
  async getStorageStats(): Promise<Record<string, number>> {
    const stats: Record<string, number> = {}
    
    const storeNames = Object.keys(STORES) as Array<keyof typeof STORES>
    for (const storeKey of storeNames) {
      const storeName = STORES[storeKey]
      const items = await this.getAll(storeName)
      stats[storeName] = items.length
    }
    
    return stats
  }

  /**
   * 确保数据库已初始化
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize()
    }
  }
}

// 导出单例实例
export const offlineStorage = new OfflineStorageManager()
