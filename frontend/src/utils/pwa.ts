/**
 * PWA工具函数
 * 
 * 提供PWA相关功能：
 * - Service Worker注册和管理
 * - 离线状态检测
 * - 安装提示管理
 * - 更新通知
 */

import { notifications } from '@mantine/notifications'

// PWA安装事件接口
interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[]
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed'
    platform: string
  }>
  prompt(): Promise<void>
}

// PWA状态接口
export interface PWAStatus {
  isInstallable: boolean
  isInstalled: boolean
  isOffline: boolean
  hasUpdate: boolean
}

// PWA管理器类
class PWAManager {
  private installPrompt: BeforeInstallPromptEvent | null = null
  private registration: ServiceWorkerRegistration | null = null
  private updateAvailable = false

  constructor() {
    this.initializePWA()
  }

  /**
   * 初始化PWA功能
   */
  private initializePWA(): void {
    // 监听安装提示事件
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      this.installPrompt = e as BeforeInstallPromptEvent
      this.notifyInstallAvailable()
    })

    // 监听应用安装事件
    window.addEventListener('appinstalled', () => {
      this.installPrompt = null
      notifications.show({
        title: 'PWA安装成功',
        message: '应用已成功安装到您的设备',
        color: 'green',
      })
    })

    // 监听在线/离线状态
    window.addEventListener('online', () => {
      notifications.show({
        title: '网络已连接',
        message: '您现在可以同步离线期间的数据',
        color: 'green',
      })
    })

    window.addEventListener('offline', () => {
      notifications.show({
        title: '网络已断开',
        message: '应用将在离线模式下继续工作',
        color: 'orange',
      })
    })
  }

  /**
   * 注册Service Worker
   */
  async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        this.registration = await navigator.serviceWorker.register('/sw.js')
        
        // 监听更新
        this.registration.addEventListener('updatefound', () => {
          const newWorker = this.registration?.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.updateAvailable = true
                this.notifyUpdateAvailable()
              }
            })
          }
        })

        // Service Worker注册成功
      } catch (error) {
        // Service Worker注册失败
      }
    }
  }

  /**
   * 检查是否可以安装PWA
   */
  canInstall(): boolean {
    return this.installPrompt !== null
  }

  /**
   * 触发PWA安装
   */
  async install(): Promise<boolean> {
    if (!this.installPrompt) {
      return false
    }

    try {
      await this.installPrompt.prompt()
      const choiceResult = await this.installPrompt.userChoice
      
      if (choiceResult.outcome === 'accepted') {
        this.installPrompt = null
        return true
      }
      return false
    } catch (error) {
      // PWA安装失败
      return false
    }
  }

  /**
   * 检查是否有更新
   */
  hasUpdate(): boolean {
    return this.updateAvailable
  }

  /**
   * 应用更新
   */
  async applyUpdate(): Promise<void> {
    if (this.registration?.waiting) {
      this.registration.waiting.postMessage({ type: 'SKIP_WAITING' })
      window.location.reload()
    }
  }

  /**
   * 获取PWA状态
   */
  getStatus(): PWAStatus {
    return {
      isInstallable: this.canInstall(),
      isInstalled: window.matchMedia('(display-mode: standalone)').matches,
      isOffline: !navigator.onLine,
      hasUpdate: this.hasUpdate(),
    }
  }

  /**
   * 通知安装可用
   */
  private notifyInstallAvailable(): void {
    notifications.show({
      id: 'pwa-install',
      title: '安装应用',
      message: '点击安装到桌面，获得更好的使用体验',
      color: 'blue',
      autoClose: false,
      withCloseButton: true,
    })
  }

  /**
   * 通知更新可用
   */
  private notifyUpdateAvailable(): void {
    notifications.show({
      id: 'pwa-update',
      title: '应用更新',
      message: '发现新版本，点击更新以获得最新功能',
      color: 'blue',
      autoClose: false,
      withCloseButton: true,
    })
  }
}

// 导出PWA管理器实例
export const pwaManager = new PWAManager()

// 导出工具函数
export const pwaUtils = {
  /**
   * 检查是否支持PWA
   */
  isSupported(): boolean {
    return 'serviceWorker' in navigator && 'PushManager' in window
  },

  /**
   * 检查是否在PWA模式下运行
   */
  isRunningAsPWA(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches ||
           (window.navigator as any).standalone === true
  },

  /**
   * 检查是否在移动设备上
   */
  isMobile(): boolean {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    )
  },

  /**
   * 获取网络状态
   */
  getNetworkStatus(): 'online' | 'offline' {
    return navigator.onLine ? 'online' : 'offline'
  },

  /**
   * 检查是否支持通知
   */
  supportsNotifications(): boolean {
    return 'Notification' in window
  },

  /**
   * 请求通知权限
   */
  async requestNotificationPermission(): Promise<'granted' | 'denied' | 'default'> {
    if (!this.supportsNotifications()) {
      return 'denied'
    }

    if (Notification.permission === 'default') {
      return await Notification.requestPermission()
    }

    return Notification.permission
  },
}
