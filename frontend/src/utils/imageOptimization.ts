/**
 * 图片优化工具
 * 
 * 提供图片优化功能：
 * - 图片压缩
 * - 格式转换
 * - 懒加载
 * - CDN优化
 */

// 图片优化配置
export interface ImageOptimizationConfig {
  quality?: number // 压缩质量 0-1
  maxWidth?: number // 最大宽度
  maxHeight?: number // 最大高度
  format?: 'webp' | 'jpeg' | 'png' // 目标格式
  enableLazyLoad?: boolean // 启用懒加载
  cdnBaseUrl?: string // CDN基础URL
}

// 图片信息
export interface ImageInfo {
  src: string
  width?: number
  height?: number
  size?: number
  format?: string
}

// 默认配置
const DEFAULT_CONFIG: Required<ImageOptimizationConfig> = {
  quality: 0.8,
  maxWidth: 1920,
  maxHeight: 1080,
  format: 'webp',
  enableLazyLoad: true,
  cdnBaseUrl: '',
}

// 图片优化管理器
class ImageOptimizationManager {
  private config: Required<ImageOptimizationConfig>
  private cache = new Map<string, string>()
  private observer: IntersectionObserver | null = null

  constructor(config: ImageOptimizationConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.initLazyLoadObserver()
  }

  /**
   * 初始化懒加载观察器
   */
  private initLazyLoadObserver(): void {
    if (!this.config.enableLazyLoad || typeof IntersectionObserver === 'undefined') {
      return
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement
            const src = img.dataset['src']
            
            if (src) {
              this.loadImage(img, src)
              this.observer?.unobserve(img)
            }
          }
        })
      },
      {
        rootMargin: '50px',
        threshold: 0.1,
      }
    )
  }

  /**
   * 压缩图片
   */
  async compressImage(
    file: File,
    options: Partial<ImageOptimizationConfig> = {}
  ): Promise<Blob> {
    const config = { ...this.config, ...options }
    
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        // 计算新尺寸
        const { width, height } = this.calculateDimensions(
          img.width,
          img.height,
          config.maxWidth,
          config.maxHeight
        )

        canvas.width = width
        canvas.height = height

        // 绘制图片
        ctx?.drawImage(img, 0, 0, width, height)

        // 转换为Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Failed to compress image'))
            }
          },
          `image/${config.format}`,
          config.quality
        )
      }

      img.onerror = () => reject(new Error('Failed to load image'))
      img.src = URL.createObjectURL(file)
    })
  }

  /**
   * 计算优化后的尺寸
   */
  private calculateDimensions(
    originalWidth: number,
    originalHeight: number,
    maxWidth: number,
    maxHeight: number
  ): { width: number; height: number } {
    let { width, height } = { width: originalWidth, height: originalHeight }

    // 按比例缩放
    if (width > maxWidth) {
      height = (height * maxWidth) / width
      width = maxWidth
    }

    if (height > maxHeight) {
      width = (width * maxHeight) / height
      height = maxHeight
    }

    return { width: Math.round(width), height: Math.round(height) }
  }

  /**
   * 生成优化后的图片URL
   */
  getOptimizedUrl(
    originalUrl: string,
    options: Partial<ImageOptimizationConfig> = {}
  ): string {
    const config = { ...this.config, ...options }
    const cacheKey = `${originalUrl}_${JSON.stringify(options)}`

    // 检查缓存
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!
    }

    let optimizedUrl = originalUrl

    // 如果有CDN配置，使用CDN
    if (config.cdnBaseUrl) {
      optimizedUrl = this.buildCdnUrl(originalUrl, config)
    }

    // 缓存结果
    this.cache.set(cacheKey, optimizedUrl)
    return optimizedUrl
  }

  /**
   * 构建CDN URL
   */
  private buildCdnUrl(
    originalUrl: string,
    config: Required<ImageOptimizationConfig>
  ): string {
    const params = new URLSearchParams()
    
    if (config.maxWidth) {
      params.set('w', config.maxWidth.toString())
    }
    
    if (config.maxHeight) {
      params.set('h', config.maxHeight.toString())
    }
    
    if (config.quality < 1) {
      params.set('q', Math.round(config.quality * 100).toString())
    }
    
    if (config.format) {
      params.set('f', config.format)
    }

    const encodedUrl = encodeURIComponent(originalUrl)
    return `${config.cdnBaseUrl}/${encodedUrl}?${params.toString()}`
  }

  /**
   * 启用图片懒加载
   */
  enableLazyLoad(img: HTMLImageElement, src: string): void {
    if (!this.observer) {
      // 如果没有观察器，直接加载
      this.loadImage(img, src)
      return
    }

    // 设置占位符
    img.src = this.generatePlaceholder(100, 100)
    img.dataset['src'] = src
    img.classList.add('lazy-loading')

    // 开始观察
    this.observer.observe(img)
  }

  /**
   * 加载图片
   */
  private loadImage(img: HTMLImageElement, src: string): void {
    const optimizedSrc = this.getOptimizedUrl(src)
    
    img.classList.add('loading')
    
    const tempImg = new Image()
    tempImg.onload = () => {
      img.src = optimizedSrc
      img.classList.remove('lazy-loading', 'loading')
      img.classList.add('loaded')
    }
    
    tempImg.onerror = () => {
      img.classList.remove('lazy-loading', 'loading')
      img.classList.add('error')
    }
    
    tempImg.src = optimizedSrc
  }

  /**
   * 生成占位符图片
   */
  private generatePlaceholder(width: number, height: number): string {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    
    canvas.width = width
    canvas.height = height
    
    if (ctx) {
      // 绘制简单的占位符
      ctx.fillStyle = '#f0f0f0'
      ctx.fillRect(0, 0, width, height)
      
      ctx.fillStyle = '#ccc'
      ctx.font = '14px Arial'
      ctx.textAlign = 'center'
      ctx.fillText('Loading...', width / 2, height / 2)
    }
    
    return canvas.toDataURL()
  }

  /**
   * 预加载图片
   */
  async preloadImage(src: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = this.getOptimizedUrl(src)
    })
  }

  /**
   * 批量预加载图片
   */
  async preloadImages(urls: string[]): Promise<HTMLImageElement[]> {
    const promises = urls.map(url => this.preloadImage(url))
    return Promise.all(promises)
  }

  /**
   * 获取图片信息
   */
  async getImageInfo(src: string): Promise<ImageInfo> {
    const img = await this.preloadImage(src)
    
    return {
      src,
      width: img.naturalWidth,
      height: img.naturalHeight,
      format: this.getImageFormat(src),
    }
  }

  /**
   * 获取图片格式
   */
  private getImageFormat(src: string): string {
    const extension = src.split('.').pop()?.toLowerCase()
    return extension || 'unknown'
  }

  /**
   * 清理缓存
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * 销毁观察器
   */
  destroy(): void {
    if (this.observer) {
      this.observer.disconnect()
      this.observer = null
    }
    this.clearCache()
  }
}

// 导出单例实例
export const imageOptimizer = new ImageOptimizationManager()

// 导出工具函数
export const imageUtils = {
  /**
   * 检查浏览器是否支持WebP
   */
  supportsWebP(): Promise<boolean> {
    return new Promise((resolve) => {
      const webP = new Image()
      webP.onload = webP.onerror = () => {
        resolve(webP.height === 2)
      }
      webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA'
    })
  },

  /**
   * 获取最佳图片格式
   */
  async getBestFormat(): Promise<'webp' | 'jpeg'> {
    const supportsWebP = await this.supportsWebP()
    return supportsWebP ? 'webp' : 'jpeg'
  },

  /**
   * 计算图片文件大小
   */
  calculateFileSize(width: number, height: number, quality: number = 0.8): number {
    // 估算压缩后的文件大小（字节）
    const pixels = width * height
    const bytesPerPixel = quality * 3 // RGB
    return Math.round(pixels * bytesPerPixel * quality)
  },
}
