/**
 * 离线数据Hook
 * 
 * 提供离线数据操作的React Hook：
 * - 离线数据查询
 * - 离线数据修改
 * - 同步状态管理
 * - 冲突处理
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import {
  offlineStorage,
  type OfflineData,
  type ConflictItem,
  type StoreType
} from '@/services/offlineStorage'
import {
  offlineSync,
  conflictResolver,
  type SyncStatus
} from '@/services/offlineSync'

// Hook选项
interface UseOfflineDataOptions {
  storeType: StoreType
  enableSync?: boolean
  fallbackToOnline?: boolean
}

// 离线数据查询Hook
export function useOfflineData<T = any>(
  key: string | string[],
  options: UseOfflineDataOptions
) {
  const queryClient = useQueryClient()
  const queryKey = Array.isArray(key) ? key : [key]
  const cacheKey = ['offline', options.storeType, ...queryKey]

  // 查询离线数据
  const query = useQuery({
    queryKey: cacheKey,
    queryFn: async () => {
      await offlineStorage.initialize()
      
      if (queryKey.length === 2 && queryKey[1]) {
        // 查询单个项目
        const item = await offlineStorage.get(options.storeType, queryKey[1])
        return item?.data as T | null
      } else {
        // 查询所有项目
        const items = await offlineStorage.getAll(options.storeType)
        return items.map(item => item.data) as T[]
      }
    },
    staleTime: 1000 * 60 * 5, // 5分钟
    gcTime: 1000 * 60 * 30, // 30分钟
  })

  // 离线创建
  const createMutation = useMutation({
    mutationFn: async (data: T) => {
      const id = (data as any).id || `offline_${Date.now()}`
      const offlineData: OfflineData = {
        id,
        type: options.storeType,
        data: { ...data, id },
        lastModified: Date.now(),
        version: 1,
        needsSync: true,
      }
      
      await offlineStorage.store(options.storeType, offlineData)
      
      if (options.enableSync && navigator.onLine) {
        await offlineSync.addOfflineOperation('create', options.storeType, offlineData.data)
      }
      
      return offlineData.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKey })
    },
  })

  // 离线更新
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<T> }) => {
      const existing = await offlineStorage.get(options.storeType, id)
      if (!existing) {
        throw new Error('Item not found')
      }
      
      const updatedData = { ...existing.data, ...data }
      const offlineData: OfflineData = {
        ...existing,
        data: updatedData,
        lastModified: Date.now(),
        version: existing.version + 1,
        needsSync: true,
      }
      
      await offlineStorage.store(options.storeType, offlineData)
      
      if (options.enableSync && navigator.onLine) {
        await offlineSync.addOfflineOperation('update', options.storeType, updatedData)
      }
      
      return updatedData
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKey })
    },
  })

  // 离线删除
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const existing = await offlineStorage.get(options.storeType, id)
      if (!existing) {
        throw new Error('Item not found')
      }
      
      await offlineStorage.delete(options.storeType, id)
      
      if (options.enableSync && navigator.onLine) {
        await offlineSync.addOfflineOperation('delete', options.storeType, { id })
      }
      
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKey })
    },
  })

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    create: createMutation.mutate,
    update: updateMutation.mutate,
    delete: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}

// 同步状态Hook
export function useSyncStatus() {
  const [status, setStatus] = useState<SyncStatus>(offlineSync.getSyncStatus())

  useEffect(() => {
    const handleStatusChange = (newStatus: SyncStatus) => {
      setStatus(newStatus)
    }

    offlineSync.addStatusListener(handleStatusChange)
    
    return () => {
      offlineSync.removeStatusListener(handleStatusChange)
    }
  }, [])

  const manualSync = async () => {
    await offlineSync.manualSync()
  }

  return {
    ...status,
    manualSync,
  }
}

// 冲突管理Hook
export function useConflictResolver() {
  const [conflicts, setConflicts] = useState<ConflictItem[]>([])

  useEffect(() => {
    const handleStatusChange = (status: SyncStatus) => {
      setConflicts(status.conflicts)
    }

    offlineSync.addStatusListener(handleStatusChange)
    
    return () => {
      offlineSync.removeStatusListener(handleStatusChange)
    }
  }, [])

  const resolveConflict = {
    withLocal: async (conflict: ConflictItem) => {
      await conflictResolver.resolveWithLocal(conflict)
      setConflicts(prev => prev.filter(c => c.id !== conflict.id))
    },
    
    withServer: async (conflict: ConflictItem) => {
      await conflictResolver.resolveWithServer(conflict)
      setConflicts(prev => prev.filter(c => c.id !== conflict.id))
    },
    
    withMerge: async (conflict: ConflictItem, mergedData: any) => {
      await conflictResolver.resolveWithMerge(conflict, mergedData)
      setConflicts(prev => prev.filter(c => c.id !== conflict.id))
    },
  }

  return {
    conflicts,
    resolveConflict,
    hasConflicts: conflicts.length > 0,
  }
}

// 离线状态Hook
export function useOfflineStatus() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return {
    isOffline,
    isOnline: !isOffline,
  }
}

// 存储统计Hook
export function useStorageStats() {
  const [stats, setStats] = useState<Record<string, number>>({})

  const refreshStats = async () => {
    const newStats = await offlineStorage.getStorageStats()
    setStats(newStats)
  }

  useEffect(() => {
    refreshStats()
  }, [])

  return {
    stats,
    refreshStats,
  }
}
