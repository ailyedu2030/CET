/**
 * 异步加载工具
 * 
 * 提供异步资源加载功能：
 * - 动态模块加载
 * - 资源预加载
 * - 加载状态管理
 * - 错误处理和重试
 */

// 加载状态
export type LoadingState = 'idle' | 'loading' | 'loaded' | 'error'

// 加载结果
export interface LoadResult<T> {
  data: T | null
  state: LoadingState
  error: Error | null
}

// 加载配置
export interface LoadConfig {
  timeout?: number // 超时时间（毫秒）
  retryCount?: number // 重试次数
  retryDelay?: number // 重试延迟（毫秒）
  cache?: boolean // 是否缓存结果
}

// 默认配置
const DEFAULT_CONFIG: Required<LoadConfig> = {
  timeout: 30000, // 30秒
  retryCount: 3,
  retryDelay: 1000, // 1秒
  cache: true,
}

// 缓存管理
class LoadCache {
  private cache = new Map<string, any>()
  private timestamps = new Map<string, number>()
  private readonly TTL = 5 * 60 * 1000 // 5分钟

  set(key: string, value: any): void {
    this.cache.set(key, value)
    this.timestamps.set(key, Date.now())
  }

  get(key: string): any | null {
    const timestamp = this.timestamps.get(key)
    if (!timestamp || Date.now() - timestamp > this.TTL) {
      this.delete(key)
      return null
    }
    return this.cache.get(key) || null
  }

  has(key: string): boolean {
    return this.get(key) !== null
  }

  delete(key: string): void {
    this.cache.delete(key)
    this.timestamps.delete(key)
  }

  clear(): void {
    this.cache.clear()
    this.timestamps.clear()
  }
}

// 异步加载管理器
class AsyncLoaderManager {
  private cache = new LoadCache()
  private loadingPromises = new Map<string, Promise<any>>()

  /**
   * 动态导入模块
   */
  async loadModule<T = any>(
    moduleFactory: () => Promise<T>,
    key: string,
    config: LoadConfig = {}
  ): Promise<LoadResult<T>> {
    const finalConfig = { ...DEFAULT_CONFIG, ...config }

    // 检查缓存
    if (finalConfig.cache && this.cache.has(key)) {
      return {
        data: this.cache.get(key),
        state: 'loaded',
        error: null,
      }
    }

    // 检查是否正在加载
    if (this.loadingPromises.has(key)) {
      try {
        const data = await this.loadingPromises.get(key)!
        return {
          data,
          state: 'loaded',
          error: null,
        }
      } catch (error) {
        return {
          data: null,
          state: 'error',
          error: error as Error,
        }
      }
    }

    // 开始加载
    const loadPromise = this.executeLoad(moduleFactory, finalConfig)
    this.loadingPromises.set(key, loadPromise)

    try {
      const data = await loadPromise
      
      // 缓存结果
      if (finalConfig.cache) {
        this.cache.set(key, data)
      }
      
      this.loadingPromises.delete(key)
      
      return {
        data,
        state: 'loaded',
        error: null,
      }
    } catch (error) {
      this.loadingPromises.delete(key)
      
      return {
        data: null,
        state: 'error',
        error: error as Error,
      }
    }
  }

  /**
   * 执行加载逻辑
   */
  private async executeLoad<T>(
    moduleFactory: () => Promise<T>,
    config: Required<LoadConfig>
  ): Promise<T> {
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= config.retryCount; attempt++) {
      try {
        // 设置超时
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('Load timeout')), config.timeout)
        })

        const loadPromise = moduleFactory()
        const result = await Promise.race([loadPromise, timeoutPromise])
        
        return result
      } catch (error) {
        lastError = error as Error
        
        // 如果不是最后一次尝试，等待后重试
        if (attempt < config.retryCount) {
          await this.delay(config.retryDelay * (attempt + 1)) // 指数退避
        }
      }
    }

    throw lastError || new Error('Load failed')
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 预加载资源
   */
  async preload<T>(
    moduleFactory: () => Promise<T>,
    key: string,
    config: LoadConfig = {}
  ): Promise<void> {
    // 在后台加载，不等待结果
    this.loadModule(moduleFactory, key, config).catch(() => {
      // 预加载失败，静默处理
    })
  }

  /**
   * 批量预加载
   */
  async preloadBatch(
    items: Array<{
      factory: () => Promise<any>
      key: string
      config?: LoadConfig
    }>
  ): Promise<void> {
    const promises = items.map(item => 
      this.preload(item.factory, item.key, item.config)
    )
    
    await Promise.allSettled(promises)
  }

  /**
   * 加载脚本文件
   */
  async loadScript(src: string, config: LoadConfig = {}): Promise<LoadResult<void>> {
    return this.loadModule(
      () => new Promise<void>((resolve, reject) => {
        const script = document.createElement('script')
        script.src = src
        script.onload = () => resolve()
        script.onerror = () => reject(new Error(`Failed to load script: ${src}`))
        document.head.appendChild(script)
      }),
      `script_${src}`,
      config
    )
  }

  /**
   * 加载CSS文件
   */
  async loadCSS(href: string, config: LoadConfig = {}): Promise<LoadResult<void>> {
    return this.loadModule(
      () => new Promise<void>((resolve, reject) => {
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = href
        link.onload = () => resolve()
        link.onerror = () => reject(new Error(`Failed to load CSS: ${href}`))
        document.head.appendChild(link)
      }),
      `css_${href}`,
      config
    )
  }

  /**
   * 加载JSON数据
   */
  async loadJSON<T = any>(url: string, config: LoadConfig = {}): Promise<LoadResult<T>> {
    return this.loadModule(
      async () => {
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        return response.json()
      },
      `json_${url}`,
      config
    )
  }

  /**
   * 加载文本文件
   */
  async loadText(url: string, config: LoadConfig = {}): Promise<LoadResult<string>> {
    return this.loadModule(
      async () => {
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        return response.text()
      },
      `text_${url}`,
      config
    )
  }

  /**
   * 获取缓存统计
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache['cache'].size,
      keys: Array.from(this.cache['cache'].keys()),
    }
  }

  /**
   * 清理缓存
   */
  clearCache(): void {
    this.cache.clear()
    this.loadingPromises.clear()
  }
}

// 导出单例实例
export const asyncLoader = new AsyncLoaderManager()

// 导出React Hook
export function useAsyncLoader<T>(
  moduleFactory: () => Promise<T>,
  key: string,
  config: LoadConfig = {}
): LoadResult<T> & { reload: () => void } {
  const [result, setResult] = useState<LoadResult<T>>({
    data: null,
    state: 'idle',
    error: null,
  })

  const load = useCallback(async () => {
    setResult(prev => ({ ...prev, state: 'loading', error: null }))
    
    const loadResult = await asyncLoader.loadModule(moduleFactory, key, config)
    setResult(loadResult)
  }, [moduleFactory, key, config])

  const reload = useCallback(() => {
    // 清除缓存并重新加载
    asyncLoader['cache'].delete(key)
    load()
  }, [key, load])

  useEffect(() => {
    load()
  }, [load])

  return {
    ...result,
    reload,
  }
}

// 导出工具函数
export const loadUtils = {
  /**
   * 检查资源是否可用
   */
  async checkResource(url: string): Promise<boolean> {
    try {
      const response = await fetch(url, { method: 'HEAD' })
      return response.ok
    } catch {
      return false
    }
  },

  /**
   * 获取资源大小
   */
  async getResourceSize(url: string): Promise<number> {
    try {
      const response = await fetch(url, { method: 'HEAD' })
      const contentLength = response.headers.get('content-length')
      return contentLength ? parseInt(contentLength, 10) : 0
    } catch {
      return 0
    }
  },

  /**
   * 估算加载时间
   */
  estimateLoadTime(size: number, bandwidth: number = 1000000): number {
    // 带宽单位：字节/秒，默认1MB/s
    return Math.ceil(size / bandwidth * 1000) // 返回毫秒
  },
}

// 导入React相关依赖
import { useCallback, useEffect, useState } from 'react'
