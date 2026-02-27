/**
 * 学习进度数据相关 Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { progressTrackingApi } from '@/api/progressTracking'
import { ProgressFilter } from '@/types/progress'

// 获取进度监控数据
export const useProgressMonitoring = () => {
  return useQuery({
    queryKey: ['progress-monitoring'],
    queryFn: () => progressTrackingApi.getProgressMonitoring(),
    refetchInterval: 5 * 60 * 1000, // 5分钟刷新一次
    staleTime: 2 * 60 * 1000, // 2分钟内认为数据是新鲜的
  })
}

// 获取实时进度数据
export const useRealTimeProgress = (enabled: boolean = true) => {
  return useQuery({
    queryKey: ['realtime-progress'],
    queryFn: () => progressTrackingApi.getRealTimeProgress(),
    refetchInterval: enabled ? 30 * 1000 : false, // 30秒刷新一次，可控制
    staleTime: 15 * 1000, // 15秒内认为数据是新鲜的
    enabled, // 允许外部控制是否启用
  })
}

// 获取进度总结
export const useProgressSummary = (periodDays: number = 30) => {
  return useQuery({
    queryKey: ['progress-summary', periodDays],
    queryFn: () => progressTrackingApi.getProgressSummary(periodDays),
    staleTime: 5 * 60 * 1000, // 5分钟内认为数据是新鲜的
  })
}

// 获取目标进度
export const useGoalProgress = (goalId: number) => {
  return useQuery({
    queryKey: ['goal-progress', goalId],
    queryFn: () => progressTrackingApi.trackGoalProgress(goalId),
    enabled: !!goalId,
    staleTime: 2 * 60 * 1000,
  })
}

// 获取学习模式分析
export const useLearningPatterns = (periodDays: number = 30) => {
  return useQuery({
    queryKey: ['learning-patterns', periodDays],
    queryFn: () => progressTrackingApi.getLearningPatterns(periodDays),
    staleTime: 10 * 60 * 1000, // 10分钟内认为数据是新鲜的
  })
}

// 获取可视化数据
export const useVisualizationData = (
  type: 'progress' | 'knowledge' | 'performance' | 'time',
  periodDays: number = 30
) => {
  return useQuery({
    queryKey: ['visualization-data', type, periodDays],
    queryFn: () => progressTrackingApi.getVisualizationData(type, periodDays),
    staleTime: 5 * 60 * 1000,
  })
}

// 获取学习进度
export const useLearningProgress = (trainingType?: string, days: number = 30) => {
  return useQuery({
    queryKey: ['learning-progress', trainingType, days],
    queryFn: () => progressTrackingApi.getLearningProgress(trainingType, days),
    staleTime: 5 * 60 * 1000,
  })
}

// 获取成就列表
export const useAchievements = () => {
  return useQuery({
    queryKey: ['achievements'],
    queryFn: () => progressTrackingApi.getAchievements(),
    staleTime: 10 * 60 * 1000,
  })
}

// 设置学习提醒
export const useSetLearningReminder = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      type: 'daily' | 'goal_deadline' | 'performance_drop'
      enabled: boolean
      settings: Record<string, any>
    }) => progressTrackingApi.setLearningReminder(data),
    onSuccess: () => {
      notifications.show({
        title: '设置成功',
        message: '学习提醒设置已更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['progress-monitoring'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '设置失败',
        message: error.message || '设置学习提醒失败',
        color: 'red',
      })
    },
  })
}

// 导出进度报告
export const useExportProgressReport = () => {
  return useMutation({
    mutationFn: (data: { format: 'pdf' | 'excel' | 'csv'; periodDays: number }) =>
      progressTrackingApi.exportProgressReport(data.format, data.periodDays),
    onSuccess: (result, variables) => {
      // 使用返回的下载链接
      if (result.download_url) {
        const link = document.createElement('a')
        link.href = result.download_url
        link.download = result.file_name || `progress-report.${variables.format}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }

      notifications.show({
        title: '导出成功',
        message: `进度报告已生成 (${(result.file_size / 1024).toFixed(1)}KB)`,
        color: 'green',
      })
    },
    onError: (error: any) => {
      notifications.show({
        title: '导出失败',
        message: error.message || '导出进度报告失败',
        color: 'red',
      })
    },
  })
}

// 刷新所有进度数据
export const useRefreshProgressData = () => {
  const queryClient = useQueryClient()

  return () => {
    queryClient.invalidateQueries({ queryKey: ['progress-monitoring'] })
    queryClient.invalidateQueries({ queryKey: ['realtime-progress'] })
    queryClient.invalidateQueries({ queryKey: ['progress-summary'] })
    queryClient.invalidateQueries({ queryKey: ['learning-patterns'] })
    queryClient.invalidateQueries({ queryKey: ['visualization-data'] })
    queryClient.invalidateQueries({ queryKey: ['learning-progress'] })
    queryClient.invalidateQueries({ queryKey: ['achievements'] })
  }
}

// 进度数据过滤
export const useProgressFilter = () => {
  const queryClient = useQueryClient()

  const applyFilter = (_filter: ProgressFilter) => {
    // 使用过滤条件重新获取数据
    queryClient.invalidateQueries({ queryKey: ['progress-monitoring'] })
    queryClient.invalidateQueries({ queryKey: ['progress-summary'] })
    queryClient.invalidateQueries({ queryKey: ['learning-progress'] })
  }

  const clearFilter = () => {
    // 清除过滤条件，恢复默认数据
    queryClient.invalidateQueries({ queryKey: ['progress-monitoring'] })
    queryClient.invalidateQueries({ queryKey: ['progress-summary'] })
    queryClient.invalidateQueries({ queryKey: ['learning-progress'] })
  }

  return {
    applyFilter,
    clearFilter,
  }
}

// 进度数据聚合
export const useProgressAggregation = () => {
  const { data: monitoring } = useProgressMonitoring()
  const { data: realtime } = useRealTimeProgress()
  const { data: summary } = useProgressSummary()
  const { data: achievements } = useAchievements()

  // 聚合所有进度数据
  const aggregatedData = {
    overview: {
      overall_progress: monitoring?.progress_metrics?.['overall_score'] || 0,
      current_streak: realtime?.today_progress?.['streak_days'] || 0,
      total_achievements: achievements?.length || 0,
      study_time_today: realtime?.today_progress?.['study_time'] || 0,
    },
    trends: monitoring?.progress_trends || {},
    alerts: monitoring?.anomalies || [],
    recent_activities: realtime?.suggestions || [],
    performance_summary: summary?.progress_metrics || null,
  }

  return aggregatedData
}
