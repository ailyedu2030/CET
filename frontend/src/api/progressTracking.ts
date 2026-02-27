/**
 * 学习进度跟踪与分析 API
 *
 * 功能包括：
 * 1. 学习进度监控
 * 2. 实时进度数据
 * 3. 进度分析报告
 * 4. 目标跟踪
 * 5. 学习模式分析
 * 6. 可视化数据
 */

import { apiClient } from './client'

// ==================== 类型定义 ====================

export interface ProgressMetrics {
  completion_rate: number
  accuracy_rate: number
  consistency_score: number
  improvement_rate: number
  engagement_score: number
  overall_score: number
}

export interface ProgressTrend {
  metric: string
  trend: 'improving' | 'stable' | 'declining'
  change_rate: number
  confidence: number
}

export interface LearningAnomaly {
  type: 'performance_drop' | 'inactivity' | 'unusual_pattern'
  severity: 'low' | 'medium' | 'high'
  description: string
  detected_at: string
  suggestions: string[]
}

export interface ProgressReport {
  student_id: number
  monitoring_timestamp: string
  progress_metrics: Record<string, any>
  progress_trends: Record<string, any>
  anomalies: Array<Record<string, any>>
  progress_report: Record<string, any>
  reminders: Array<Record<string, any>>
  overall_status: string
}

export interface Achievement {
  achievement_id: string
  type: string
  name: string
  description: string
  level: number
  icon: string
  points: number
  threshold: any
  achieved_at: string
  rarity: string
}

export interface GoalProgress {
  goal_id: number
  title: string
  target_value: number
  current_value: number
  progress_percentage: number
  deadline: string
  status: 'on_track' | 'behind' | 'ahead' | 'completed' | 'overdue'
  achievement_probability: number
  milestones: Milestone[]
}

export interface Milestone {
  id: number
  title: string
  target_value: number
  current_value: number
  completed: boolean
  completed_at?: string
}

export interface LearningPattern {
  pattern_type: 'time_preference' | 'difficulty_progression' | 'type_preference'
  description: string
  strength: number
  insights: string[]
  recommendations: string[]
}

export interface RealTimeProgress {
  student_id: number
  timestamp: string
  today_progress: Record<string, any>
  week_progress: Record<string, any>
  current_session: Record<string, any> | null
  real_time_metrics: Record<string, any>
  suggestions: string[]
}

export interface VisualizationData {
  progress_chart: {
    labels: string[]
    datasets: Array<{
      label: string
      data: number[]
      color: string
    }>
  }
  knowledge_heatmap: Array<{
    knowledge_point: string
    mastery_level: number
    practice_count: number
    last_practiced: string
  }>
  performance_radar: {
    categories: string[]
    current_scores: number[]
    target_scores: number[]
    previous_scores?: number[]
  }
  time_distribution: Array<{
    time_slot: string
    study_minutes: number
    efficiency_score: number
  }>
}

// ==================== API 实现 ====================

export const progressTrackingApi = {
  // 获取学习进度监控数据
  getProgressMonitoring: async (): Promise<ProgressReport> => {
    const response = await apiClient.get('/api/v1/training/learning-plan/progress/monitor')
    return response.data
  },

  // 获取实时进度数据
  getRealTimeProgress: async (): Promise<RealTimeProgress> => {
    const response = await apiClient.get('/api/v1/training/learning-plan/progress/realtime')
    return response.data
  },

  // 获取进度总结
  getProgressSummary: async (periodDays: number = 30): Promise<ProgressReport> => {
    const response = await apiClient.get('/api/v1/training/learning-plan/progress/summary', {
      params: { period_days: periodDays },
    })
    return response.data
  },

  // 跟踪目标进度
  trackGoalProgress: async (goalId: number): Promise<GoalProgress> => {
    const response = await apiClient.get(`/api/v1/training/learning-plan/progress/goals/${goalId}`)
    return response.data
  },

  // 获取学习模式分析
  getLearningPatterns: async (periodDays: number = 30): Promise<LearningPattern[]> => {
    const response = await apiClient.get('/api/v1/training/analytics/patterns', {
      params: { days: periodDays },
    })
    return response.data
  },

  // 获取可视化数据（使用学习进度API生成）
  getVisualizationData: async (
    _type: 'progress' | 'knowledge' | 'performance' | 'time',
    periodDays: number = 30
  ): Promise<VisualizationData> => {
    // 使用学习进度API获取数据，然后转换为可视化格式
    const response = await apiClient.get('/api/v1/training/analytics/progress', {
      params: { days: periodDays, training_type: 'all' },
    })

    // 将学习进度数据转换为可视化格式
    const progressData = response.data
    return {
      progress_chart: {
        labels: progressData.timeline?.map((item: any) => item.date) || [],
        datasets: [
          {
            label: '学习进度',
            data: progressData.timeline?.map((item: any) => item.progress_percentage) || [],
            color: '#228be6',
          },
        ],
      },
      knowledge_heatmap: progressData.knowledge_point_progress || [],
      performance_radar: {
        categories: ['词汇', '听力', '阅读', '写作', '语法'],
        current_scores: [
          progressData.overall_metrics?.vocabulary_score || 0,
          progressData.overall_metrics?.listening_score || 0,
          progressData.overall_metrics?.reading_score || 0,
          progressData.overall_metrics?.writing_score || 0,
          progressData.overall_metrics?.grammar_score || 0,
        ],
        target_scores: [100, 100, 100, 100, 100],
      },
      time_distribution: progressData.time_distribution || [],
    }
  },

  // 获取学习进度（训练相关）
  getLearningProgress: async (trainingType?: string, days: number = 30): Promise<any> => {
    const response = await apiClient.get('/api/v1/training/analytics/progress', {
      params: { training_type: trainingType, days },
    })
    return response.data
  },

  // 获取成就列表
  getAchievements: async (): Promise<Achievement[]> => {
    const response = await apiClient.get('/api/v1/training/social/achievements')
    return response.data
  },

  // 设置学习提醒
  setLearningReminder: async (data: {
    type: 'daily' | 'goal_deadline' | 'performance_drop'
    enabled: boolean
    settings: Record<string, any>
  }): Promise<void> => {
    await apiClient.post('/api/v1/training/learning-management/reminders', data)
  },

  // 导出进度报告
  exportProgressReport: async (
    format: 'pdf' | 'excel' | 'csv',
    periodDays: number = 30
  ): Promise<{
    download_url: string
    file_name: string
    file_size: number
    generated_at: string
  }> => {
    const dateRange =
      periodDays <= 7 ? '7d' : periodDays <= 30 ? '30d' : periodDays <= 90 ? '90d' : 'all'
    const response = await apiClient.get('/api/v1/training/learning-management/export/data', {
      params: {
        format: format === 'excel' ? 'excel' : format,
        date_range: dateRange,
        include_details: true,
      },
    })
    return response.data
  },
}
