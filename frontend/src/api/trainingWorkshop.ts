/**
 * 智能训练工坊API客户端 - 需求15实现
 */
import { apiClient } from './client'
import { DifficultyLevel, TrainingType } from '../types/training'

// ==================== 类型定义 ====================

export interface TrainingParameterConfig {
  knowledge_points: string[]
  vocabulary_library_ids: number[]
  hot_topics_fusion_rate: number // 0-100%
  lesson_plan_connection_rate: number // 0-100%
  difficulty_distribution: Record<DifficultyLevel, number>
  question_count_per_type: Record<TrainingType, number>
}

export interface TrainingParameterTemplate {
  id?: number
  name: string
  description?: string
  config: TrainingParameterConfig
  is_default: boolean
  created_by?: number
  created_at?: string
  updated_at?: string
}

export interface TrainingParameterTemplateRequest {
  name: string
  description?: string
  config: TrainingParameterConfig
  is_default: boolean
}

export interface ReadingTrainingConfig {
  topic_count: number
  questions_per_topic: number
  syllabus_relevance_rate: number
  topics?: string[]
}

export interface WritingTrainingConfig {
  writing_types: string[]
  cet4_standard_embedded: boolean
  topic_sources: string[]
}

export interface WeeklyTrainingConfig {
  week_number: number
  reading_config?: ReadingTrainingConfig
  writing_config?: WritingTrainingConfig
  vocabulary_config?: Record<string, any>
  listening_config?: Record<string, any>
  translation_config?: Record<string, any>
}

export interface TrainingTask {
  id: number
  class_id: number
  teacher_id: number
  task_name: string
  task_type: string
  config: Record<string, any>
  status: string
  publish_time?: string
  deadline?: string
  created_at: string
  updated_at: string
  total_students?: number
  completed_students?: number
  completion_rate?: number
}

export interface TrainingTaskRequest {
  class_id: number
  task_name: string
  task_type: string
  config: Record<string, any>
  publish_type: 'immediate' | 'scheduled'
  scheduled_time?: string
  deadline?: string
}

export interface WeeklyTrainingRequest {
  class_id: number
  week_config: WeeklyTrainingConfig
  publish_type: 'immediate' | 'scheduled'
  scheduled_time?: string
}

export interface TrainingAnalyticsData {
  class_id: number
  analysis_period: string
  task_statistics: {
    total_tasks: number
    published_tasks: number
    draft_tasks: number
    failed_tasks: number
    completion_rate: number
    task_types: Record<string, number>
    status_distribution: Record<string, number>
  }
  student_performance: Array<{
    student_id: number
    total_tasks: number
    completed_tasks: number
    completion_ratio: number
    average_score: number
    average_completion_rate: number
    performance_level: string
  }>
  risk_students: Array<{
    student_id: number
    risk_level: string
    risk_score: number
    risk_factors: string[]
    completion_ratio: number
    average_score: number
    suggestions: string[]
  }>
  effectiveness_analysis: {
    overall_effectiveness: number
    average_completion_rate: number
    average_score: number
    student_count: number
    performance_distribution: Record<string, number>
    improvement_trends: {
      trend: string
      recommendation: string
    }
  }
  generated_at: string
}

// ==================== API响应类型 ====================

export interface TrainingParameterTemplateListResponse {
  templates: TrainingParameterTemplate[]
  total: number
  page: number
  page_size: number
}

export interface TrainingTaskListResponse {
  tasks: TrainingTask[]
  total: number
  page: number
  page_size: number
}

export interface TrainingWorkshopResponse {
  success: boolean
  message: string
  data?: any
}

// ==================== API客户端 ====================

export const trainingWorkshopApi = {
  // ==================== 训练参数模板管理 ====================

  // 创建训练参数模板
  createParameterTemplate: async (
    templateData: TrainingParameterTemplateRequest
  ): Promise<TrainingParameterTemplate> => {
    const response = await apiClient.post(
      '/training/training-workshop/parameter-templates',
      templateData
    )
    return response.data
  },

  // 获取训练参数模板列表
  getParameterTemplates: async (
    params: {
      page?: number
      page_size?: number
    } = {}
  ): Promise<TrainingParameterTemplateListResponse> => {
    const response = await apiClient.get('/training/training-workshop/parameter-templates', {
      params,
    })
    return response.data
  },

  // 更新训练参数模板
  updateParameterTemplate: async (
    templateId: number,
    templateData: TrainingParameterTemplateRequest
  ): Promise<TrainingParameterTemplate> => {
    const response = await apiClient.put(
      `/training/training-workshop/parameter-templates/${templateId}`,
      templateData
    )
    return response.data
  },

  // 删除训练参数模板
  deleteParameterTemplate: async (templateId: number): Promise<TrainingWorkshopResponse> => {
    const response = await apiClient.delete(
      `/training/training-workshop/parameter-templates/${templateId}`
    )
    return response.data
  },

  // ==================== 训练任务管理 ====================

  // 创建训练任务
  createTrainingTask: async (taskData: TrainingTaskRequest): Promise<TrainingTask> => {
    const response = await apiClient.post('/training/training-workshop/training-tasks', taskData)
    return response.data
  },

  // 获取训练任务列表
  getTrainingTasks: async (
    params: {
      class_id?: number
      page?: number
      page_size?: number
    } = {}
  ): Promise<TrainingTaskListResponse> => {
    const response = await apiClient.get('/training/training-workshop/training-tasks', { params })
    return response.data
  },

  // ==================== 周训练配置 ====================

  // 创建周训练配置
  createWeeklyTraining: async (weeklyData: WeeklyTrainingRequest): Promise<TrainingTask> => {
    const response = await apiClient.post('/training/training-workshop/weekly-training', weeklyData)
    return response.data
  },

  // ==================== 训练数据分析 ====================

  // 获取班级训练数据分析
  getClassTrainingAnalytics: async (
    classId: number,
    params: {
      start_date?: string
      end_date?: string
    } = {}
  ): Promise<TrainingAnalyticsData> => {
    const response = await apiClient.get(`/training/training-workshop/analytics/class/${classId}`, {
      params,
    })
    return response.data
  },

  // ==================== 辅助方法 ====================

  // 获取默认训练参数配置
  getDefaultParameterConfig: (): TrainingParameterConfig => {
    return {
      knowledge_points: [],
      vocabulary_library_ids: [],
      hot_topics_fusion_rate: 30,
      lesson_plan_connection_rate: 80,
      difficulty_distribution: {
        [DifficultyLevel.BEGINNER]: 20,
        [DifficultyLevel.ELEMENTARY]: 30,
        [DifficultyLevel.INTERMEDIATE]: 30,
        [DifficultyLevel.ADVANCED]: 15,
        [DifficultyLevel.EXPERT]: 5,
      },
      question_count_per_type: {
        [TrainingType.VOCABULARY]: 15,
        [TrainingType.LISTENING]: 10,
        [TrainingType.READING]: 8,
        [TrainingType.WRITING]: 2,
        [TrainingType.TRANSLATION]: 3,
        [TrainingType.GRAMMAR]: 0,
        [TrainingType.SPEAKING]: 0,
      },
    }
  },

  // 验证训练参数配置
  validateParameterConfig: (config: TrainingParameterConfig): string[] => {
    const errors: string[] = []

    // 验证难度分布总和为100%
    const difficultyTotal = Object.values(config.difficulty_distribution).reduce(
      (sum, val) => sum + val,
      0
    )
    if (difficultyTotal !== 100) {
      errors.push('难度分布总和必须为100%')
    }

    // 验证融合程度范围
    if (config.hot_topics_fusion_rate < 0 || config.hot_topics_fusion_rate > 100) {
      errors.push('热点融合程度必须在0-100%之间')
    }

    if (config.lesson_plan_connection_rate < 0 || config.lesson_plan_connection_rate > 100) {
      errors.push('教案衔接度必须在0-100%之间')
    }

    // 验证题目数量
    const totalQuestions = Object.values(config.question_count_per_type).reduce(
      (sum, val) => sum + val,
      0
    )
    if (totalQuestions === 0) {
      errors.push('至少需要配置一种题型的题目数量')
    }

    return errors
  },

  // 获取预设模板
  getPresetTemplates: (): TrainingParameterTemplate[] => {
    return [
      {
        name: '基础训练模板',
        description: '适合初学者的基础训练配置',
        config: {
          knowledge_points: ['基础语法', '常用词汇'],
          vocabulary_library_ids: [1],
          hot_topics_fusion_rate: 20,
          lesson_plan_connection_rate: 90,
          difficulty_distribution: {
            [DifficultyLevel.BEGINNER]: 40,
            [DifficultyLevel.ELEMENTARY]: 35,
            [DifficultyLevel.INTERMEDIATE]: 20,
            [DifficultyLevel.ADVANCED]: 5,
            [DifficultyLevel.EXPERT]: 0,
          },
          question_count_per_type: {
            [TrainingType.VOCABULARY]: 20,
            [TrainingType.LISTENING]: 8,
            [TrainingType.READING]: 5,
            [TrainingType.WRITING]: 1,
            [TrainingType.TRANSLATION]: 2,
            [TrainingType.GRAMMAR]: 0,
            [TrainingType.SPEAKING]: 0,
          },
        },
        is_default: false,
      },
      {
        name: '强化训练模板',
        description: '适合有一定基础的学生进行强化训练',
        config: {
          knowledge_points: ['高级语法', '学术词汇', '写作技巧'],
          vocabulary_library_ids: [1, 2],
          hot_topics_fusion_rate: 50,
          lesson_plan_connection_rate: 70,
          difficulty_distribution: {
            [DifficultyLevel.BEGINNER]: 10,
            [DifficultyLevel.ELEMENTARY]: 20,
            [DifficultyLevel.INTERMEDIATE]: 40,
            [DifficultyLevel.ADVANCED]: 25,
            [DifficultyLevel.EXPERT]: 5,
          },
          question_count_per_type: {
            [TrainingType.VOCABULARY]: 12,
            [TrainingType.LISTENING]: 12,
            [TrainingType.READING]: 10,
            [TrainingType.WRITING]: 3,
            [TrainingType.TRANSLATION]: 5,
            [TrainingType.GRAMMAR]: 0,
            [TrainingType.SPEAKING]: 0,
          },
        },
        is_default: false,
      },
    ]
  },
}
