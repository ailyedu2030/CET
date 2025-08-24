import { apiClient } from './client'
import { TrainingType, DifficultyLevel } from '../types/training'

export interface LearningPlan {
  id: number
  title: string
  description: string
  targetScore: number
  targetDate: string
  status: 'active' | 'completed' | 'paused'
  progress: number
  createdAt: string
  tasks: LearningTask[]
}

export interface LearningTask {
  id: number
  title: string
  type: TrainingType
  difficulty: DifficultyLevel
  targetCount: number
  completedCount: number
  deadline: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  priority: 'low' | 'medium' | 'high'
}

export interface PlanStats {
  totalPlans: number
  activePlans: number
  completedPlans: number
  totalTasks: number
  completedTasks: number
  overdueTasks: number
  weeklyProgress: number
  monthlyProgress: number
}

export interface CreatePlanRequest {
  title: string
  description: string
  targetScore: number
  targetDate: Date
  tasks: Array<{
    title: string
    type: TrainingType
    difficulty: DifficultyLevel
    targetCount: number
    deadline: Date
    priority: 'low' | 'medium' | 'high'
  }>
}

export const learningPlanApi = {
  // 获取学习计划统计
  getPlanStats: async (): Promise<PlanStats> => {
    const response = await apiClient.get('/learning-plan/stats')
    return response.data
  },

  // 获取学习计划列表
  getLearningPlans: async (
    params: {
      page?: number
      limit?: number
      status?: 'active' | 'completed' | 'paused'
    } = {}
  ): Promise<{
    plans: LearningPlan[]
    total: number
    page: number
    pageSize: number
  }> => {
    const response = await apiClient.get('/learning-plan/plans', { params })
    return response.data
  },

  // 获取今日任务
  getTodayTasks: async (): Promise<{
    tasks: LearningTask[]
    totalTasks: number
    completedTasks: number
    progress: number
  }> => {
    const response = await apiClient.get('/learning-plan/today-tasks')
    return response.data
  },

  // 创建学习计划
  createPlan: async (data: CreatePlanRequest): Promise<LearningPlan> => {
    const response = await apiClient.post('/learning-plan/plans', data)
    return response.data
  },

  // 更新学习计划
  updatePlan: async (planId: number, data: Partial<CreatePlanRequest>): Promise<LearningPlan> => {
    const response = await apiClient.put(`/learning-plan/plans/${planId}`, data)
    return response.data
  },

  // 删除学习计划
  deletePlan: async (planId: number): Promise<void> => {
    await apiClient.delete(`/learning-plan/plans/${planId}`)
  },

  // 更新任务状态
  updateTaskStatus: async (data: {
    taskId: number
    status: 'pending' | 'in_progress' | 'completed'
    progress?: number
  }): Promise<void> => {
    await apiClient.put('/learning-plan/tasks/status', data)
  },

  // 添加任务到计划
  addTaskToPlan: async (
    planId: number,
    task: {
      title: string
      type: TrainingType
      difficulty: DifficultyLevel
      targetCount: number
      deadline: Date
      priority: 'low' | 'medium' | 'high'
    }
  ): Promise<LearningTask> => {
    const response = await apiClient.post(`/learning-plan/plans/${planId}/tasks`, task)
    return response.data
  },

  // 删除任务
  deleteTask: async (taskId: number): Promise<void> => {
    await apiClient.delete(`/learning-plan/tasks/${taskId}`)
  },

  // 获取计划详情
  getPlanDetail: async (planId: number): Promise<LearningPlan> => {
    const response = await apiClient.get(`/learning-plan/plans/${planId}`)
    return response.data
  },

  // 生成智能学习计划
  generateSmartPlan: async (data: {
    targetScore: number
    targetDate: Date
    currentLevel: DifficultyLevel
    availableTimePerDay: number
    focusAreas: TrainingType[]
    weaknessAreas?: string[]
  }): Promise<{
    plan: CreatePlanRequest
    estimatedSuccess: number
    recommendations: string[]
  }> => {
    const response = await apiClient.post('/learning-plan/generate', data)
    return response.data
  },

  // 获取学习进度分析
  getProgressAnalysis: async (
    planId: number
  ): Promise<{
    overallProgress: number
    taskProgress: Array<{
      taskId: number
      title: string
      progress: number
      trend: 'improving' | 'stable' | 'declining'
    }>
    timeAnalysis: {
      plannedTime: number
      actualTime: number
      efficiency: number
    }
    predictions: {
      estimatedCompletion: string
      successProbability: number
      adjustmentSuggestions: string[]
    }
  }> => {
    const response = await apiClient.get(`/learning-plan/plans/${planId}/analysis`)
    return response.data
  },

  // 调整计划
  adjustPlan: async (
    planId: number,
    data: {
      newTargetDate?: Date
      newTargetScore?: number
      addTasks?: Array<{
        title: string
        type: TrainingType
        difficulty: DifficultyLevel
        targetCount: number
        deadline: Date
        priority: 'low' | 'medium' | 'high'
      }>
      removeTasks?: number[]
      adjustReason: string
    }
  ): Promise<LearningPlan> => {
    const response = await apiClient.post(`/learning-plan/plans/${planId}/adjust`, data)
    return response.data
  },

  // 获取计划模板
  getPlanTemplates: async (): Promise<
    Array<{
      id: number
      name: string
      description: string
      targetScore: number
      duration: number
      difficulty: DifficultyLevel
      tasks: Array<{
        title: string
        type: TrainingType
        difficulty: DifficultyLevel
        targetCount: number
        priority: 'low' | 'medium' | 'high'
      }>
    }>
  > => {
    const response = await apiClient.get('/learning-plan/templates')
    return response.data
  },

  // 从模板创建计划
  createFromTemplate: async (data: {
    templateId: number
    title: string
    targetDate: Date
    customizations?: {
      targetScore?: number
      additionalTasks?: Array<{
        title: string
        type: TrainingType
        difficulty: DifficultyLevel
        targetCount: number
        priority: 'low' | 'medium' | 'high'
      }>
    }
  }): Promise<LearningPlan> => {
    const response = await apiClient.post('/learning-plan/create-from-template', data)
    return response.data
  },
}
