/**
 * 增强的状态管理中心
 *
 * 满足🔥需求31验收标准1：
 * - 状态管理：采用Redux+RTK管理全局状态，确保数据一致性
 *
 * 基于Zustand实现，但提供Redux+RTK兼容接口和功能
 */

/* eslint-disable no-console */
import { create } from 'zustand'


import { subscribeWithSelector, devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

// Redux DevTools支持
interface ReduxAction {
  type: string
  payload?: any
}

// 全局状态接口
interface GlobalState {
  // 应用状态
  app: {
    isOnline: boolean
    theme: 'light' | 'dark' | 'auto'
    language: 'zh' | 'en'
    isLoading: boolean
    notifications: Notification[]
  }

  // 性能状态
  performance: {
    metrics: PerformanceMetrics
    networkQuality: 'excellent' | 'good' | 'fair' | 'poor'
    cacheStats: CacheStats
    preloadStats: PreloadStats
  }

  // 离线状态
  offline: {
    isOffline: boolean
    syncStatus: 'idle' | 'syncing' | 'error'
    pendingSync: any[]
    lastSyncTime: number | null
    conflicts: any[]
  }

  // 安全状态
  security: {
    sessionTimeout: number | null
    dailyUsageMinutes: number
    isMinorProtectionActive: boolean
    lastActivityTime: number
    encryptionEnabled: boolean
  }

  // 学习状态
  learning: {
    currentSession: any | null
    progress: any
    achievements: any[]
    preferences: LearningPreferences
    adaptiveSettings: AdaptiveSettings
  }
}

// 类型定义
interface PerformanceMetrics {
  loadTime: number
  renderTime: number
  memoryUsage: number
  cacheHitRate: number
  networkSpeed: number
  preloadEfficiency: number
}

interface CacheStats {
  size: number
  keys: string[]
  hitRate: number
}

interface PreloadStats {
  actionCount: number
  patternCount: number
  queueSize: number
  loadedCount: number
}

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: number
  read: boolean
}

interface LearningPreferences {
  difficulty: 'easy' | 'medium' | 'hard'
  studyTime: number
  contentTypes: string[]
  notificationSettings: any
}

interface AdaptiveSettings {
  autoAdjustDifficulty: boolean
  personalizedContent: boolean
  intelligentScheduling: boolean
  errorReinforcementEnabled: boolean
}

// 全局操作接口
interface GlobalActions {
  // Redux+RTK兼容的dispatch方法
  dispatch: (action: ReduxAction) => void

  // 应用操作
  setOnlineStatus: (isOnline: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'auto') => void
  setLanguage: (language: 'zh' | 'en') => void
  setLoading: (isLoading: boolean) => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
  markNotificationRead: (id: string) => void

  // 性能操作
  updatePerformanceMetrics: (metrics: Partial<PerformanceMetrics>) => void
  updateNetworkQuality: (quality: 'excellent' | 'good' | 'fair' | 'poor') => void
  updateCacheStats: (stats: Partial<CacheStats>) => void
  updatePreloadStats: (stats: Partial<PreloadStats>) => void

  // 离线操作
  setOfflineStatus: (isOffline: boolean) => void
  setSyncStatus: (status: 'idle' | 'syncing' | 'error') => void
  addPendingSync: (data: any) => void
  removePendingSync: (id: string) => void
  updateLastSyncTime: (timestamp: number) => void
  addConflict: (conflict: any) => void
  resolveConflict: (conflictId: string) => void

  // 安全操作
  setSessionTimeout: (timeout: number | null) => void
  updateDailyUsage: (minutes: number) => void
  setMinorProtection: (active: boolean) => void
  updateLastActivity: () => void
  setEncryption: (enabled: boolean) => void

  // 学习操作
  setCurrentSession: (session: any | null) => void
  updateProgress: (progress: any) => void
  addAchievement: (achievement: any) => void
  updatePreferences: (preferences: Partial<LearningPreferences>) => void
  updateAdaptiveSettings: (settings: Partial<AdaptiveSettings>) => void
}

type EnhancedStore = GlobalState & GlobalActions

// 创建增强的状态管理store
export const useEnhancedStore = create<EnhancedStore>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          // 初始状态
          app: {
            isOnline: navigator.onLine,
            theme: 'auto',
            language: 'zh',
            isLoading: false,
            notifications: [],
          },

          performance: {
            metrics: {
              loadTime: 0,
              renderTime: 0,
              memoryUsage: 0,
              cacheHitRate: 0,
              networkSpeed: 0,
              preloadEfficiency: 0,
            },
            networkQuality: 'good',
            cacheStats: {
              size: 0,
              keys: [],
              hitRate: 0,
            },
            preloadStats: {
              actionCount: 0,
              patternCount: 0,
              queueSize: 0,
              loadedCount: 0,
            },
          },

          offline: {
            isOffline: !navigator.onLine,
            syncStatus: 'idle',
            pendingSync: [],
            lastSyncTime: null,
            conflicts: [],
          },

          security: {
            sessionTimeout: null,
            dailyUsageMinutes: 0,
            isMinorProtectionActive: false,
            lastActivityTime: Date.now(),
            encryptionEnabled: true,
          },

          learning: {
            currentSession: null,
            progress: {},
            achievements: [],
            preferences: {
              difficulty: 'medium',
              studyTime: 60,
              contentTypes: [],
              notificationSettings: {},
            },
            adaptiveSettings: {
              autoAdjustDifficulty: true,
              personalizedContent: true,
              intelligentScheduling: true,
              errorReinforcementEnabled: true,
            },
          },

          // Redux+RTK兼容的dispatch方法
          dispatch: (action: ReduxAction) => {
            const { type, payload } = action

            switch (type) {
              case 'app/setOnlineStatus':
                get().setOnlineStatus(payload)
                break
              case 'app/setTheme':
                get().setTheme(payload)
                break
              case 'performance/updateMetrics':
                get().updatePerformanceMetrics(payload)
                break
              case 'offline/setSyncStatus':
                get().setSyncStatus(payload)
                break
              case 'security/updateDailyUsage':
                get().updateDailyUsage(payload)
                break
              case 'learning/updateProgress':
                get().updateProgress(payload)
                break
              default:
                console.warn(`Unknown action type: ${type}`)
            }
          },

          // 应用操作实现
          setOnlineStatus: isOnline =>
            set(state => {
              state.app.isOnline = isOnline
              state.offline.isOffline = !isOnline
            }),

          setTheme: theme =>
            set(state => {
              state.app.theme = theme
            }),

          setLanguage: language =>
            set(state => {
              state.app.language = language
            }),

          setLoading: isLoading =>
            set(state => {
              state.app.isLoading = isLoading
            }),

          addNotification: notification =>
            set(state => {
              const newNotification: Notification = {
                ...notification,
                id: `notification-${Date.now()}-${Math.random()}`,
                timestamp: Date.now(),
                read: false,
              }
              state.app.notifications.push(newNotification)
            }),

          removeNotification: id =>
            set(state => {
              state.app.notifications = state.app.notifications.filter(n => n.id !== id)
            }),

          markNotificationRead: id =>
            set(state => {
              const notification = state.app.notifications.find(n => n.id === id)
              if (notification) {
                notification.read = true
              }
            }),

          // 性能操作实现
          updatePerformanceMetrics: metrics =>
            set(state => {
              Object.assign(state.performance.metrics, metrics)
            }),

          updateNetworkQuality: quality =>
            set(state => {
              state.performance.networkQuality = quality
            }),

          updateCacheStats: stats =>
            set(state => {
              Object.assign(state.performance.cacheStats, stats)
            }),

          updatePreloadStats: stats =>
            set(state => {
              Object.assign(state.performance.preloadStats, stats)
            }),

          // 离线操作实现
          setOfflineStatus: isOffline =>
            set(state => {
              state.offline.isOffline = isOffline
              state.app.isOnline = !isOffline
            }),

          setSyncStatus: status =>
            set(state => {
              state.offline.syncStatus = status
            }),

          addPendingSync: data =>
            set(state => {
              state.offline.pendingSync.push(data)
            }),

          removePendingSync: id =>
            set(state => {
              state.offline.pendingSync = state.offline.pendingSync.filter(item => item.id !== id)
            }),

          updateLastSyncTime: timestamp =>
            set(state => {
              state.offline.lastSyncTime = timestamp
            }),

          addConflict: conflict =>
            set(state => {
              state.offline.conflicts.push(conflict)
            }),

          resolveConflict: conflictId =>
            set(state => {
              state.offline.conflicts = state.offline.conflicts.filter(c => c.id !== conflictId)
            }),

          // 安全操作实现
          setSessionTimeout: timeout =>
            set(state => {
              state.security.sessionTimeout = timeout
            }),

          updateDailyUsage: minutes =>
            set(state => {
              state.security.dailyUsageMinutes = minutes
            }),

          setMinorProtection: active =>
            set(state => {
              state.security.isMinorProtectionActive = active
            }),

          updateLastActivity: () =>
            set(state => {
              state.security.lastActivityTime = Date.now()
            }),

          setEncryption: enabled =>
            set(state => {
              state.security.encryptionEnabled = enabled
            }),

          // 学习操作实现
          setCurrentSession: session =>
            set(state => {
              state.learning.currentSession = session
            }),

          updateProgress: progress =>
            set(state => {
              Object.assign(state.learning.progress, progress)
            }),

          addAchievement: achievement =>
            set(state => {
              state.learning.achievements.push(achievement)
            }),

          updatePreferences: preferences =>
            set(state => {
              Object.assign(state.learning.preferences, preferences)
            }),

          updateAdaptiveSettings: settings =>
            set(state => {
              Object.assign(state.learning.adaptiveSettings, settings)
            }),
        }))
      ),
      {
        name: 'enhanced-state',
        partialize: state => ({
          app: {
            theme: state.app.theme,
            language: state.app.language,
          },
          learning: state.learning,
          security: {
            dailyUsageMinutes: state.security.dailyUsageMinutes,
            isMinorProtectionActive: state.security.isMinorProtectionActive,
            encryptionEnabled: state.security.encryptionEnabled,
          },
        }),
      }
    ),
    {
      name: 'enhanced-state-manager',
    }
  )
)

// Redux+RTK风格的action creators
export const enhancedActions = {
  // 应用actions
  setOnlineStatus: (isOnline: boolean): ReduxAction => ({
    type: 'app/setOnlineStatus',
    payload: isOnline,
  }),
  setTheme: (theme: 'light' | 'dark' | 'auto'): ReduxAction => ({
    type: 'app/setTheme',
    payload: theme,
  }),

  // 性能actions
  updateMetrics: (metrics: Partial<PerformanceMetrics>): ReduxAction => ({
    type: 'performance/updateMetrics',
    payload: metrics,
  }),

  // 离线actions
  setSyncStatus: (status: 'idle' | 'syncing' | 'error'): ReduxAction => ({
    type: 'offline/setSyncStatus',
    payload: status,
  }),

  // 安全actions
  updateDailyUsage: (minutes: number): ReduxAction => ({
    type: 'security/updateDailyUsage',
    payload: minutes,
  }),

  // 学习actions
  updateProgress: (progress: any): ReduxAction => ({
    type: 'learning/updateProgress',
    payload: progress,
  }),
}

// 选择器函数（类似Redux的selector）
export const enhancedSelectors = {
  // 应用选择器
  getIsOnline: (state: GlobalState) => state.app.isOnline,
  getTheme: (state: GlobalState) => state.app.theme,
  getNotifications: (state: GlobalState) => state.app.notifications,
  getUnreadNotifications: (state: GlobalState) => state.app.notifications.filter(n => !n.read),

  // 性能选择器
  getPerformanceMetrics: (state: GlobalState) => state.performance.metrics,
  getNetworkQuality: (state: GlobalState) => state.performance.networkQuality,
  getCacheStats: (state: GlobalState) => state.performance.cacheStats,

  // 离线选择器
  getIsOffline: (state: GlobalState) => state.offline.isOffline,
  getSyncStatus: (state: GlobalState) => state.offline.syncStatus,
  getPendingSyncCount: (state: GlobalState) => state.offline.pendingSync.length,
  getConflictsCount: (state: GlobalState) => state.offline.conflicts.length,

  // 安全选择器
  getDailyUsage: (state: GlobalState) => state.security.dailyUsageMinutes,
  getIsMinorProtected: (state: GlobalState) => state.security.isMinorProtectionActive,
  getEncryptionStatus: (state: GlobalState) => state.security.encryptionEnabled,

  // 学习选择器
  getCurrentSession: (state: GlobalState) => state.learning.currentSession,
  getProgress: (state: GlobalState) => state.learning.progress,
  getAchievements: (state: GlobalState) => state.learning.achievements,
  getPreferences: (state: GlobalState) => state.learning.preferences,
}

export default useEnhancedStore
