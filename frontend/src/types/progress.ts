/**
 * 学习进度跟踪相关类型定义
 */

export interface StudentProgressOverview {
  student_id: number
  student_name: string
  overall_progress: number
  current_level: number
  total_study_time: number
  completed_sessions: number
  average_score: number
  streak_days: number
  last_activity: string
  status: 'active' | 'inactive' | 'at_risk'
}

export interface ClassProgressSummary {
  class_id: number
  class_name: string
  total_students: number
  active_students: number
  average_progress: number
  completion_rate: number
  performance_distribution: {
    excellent: number
    good: number
    average: number
    needs_improvement: number
  }
  top_performers: StudentProgressOverview[]
  at_risk_students: StudentProgressOverview[]
}

export interface ProgressTimelineData {
  date: string
  progress_percentage: number
  study_minutes: number
  completed_tasks: number
  accuracy_rate: number
  knowledge_points_mastered: number
}

export interface KnowledgePointProgress {
  knowledge_point_id: number
  name: string
  category: string
  mastery_level: number
  practice_count: number
  correct_rate: number
  last_practiced: string
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  estimated_time_to_master: number
}

export interface LearningEfficiencyMetrics {
  time_efficiency: number
  accuracy_efficiency: number
  retention_rate: number
  improvement_velocity: number
  consistency_score: number
  optimal_study_duration: number
  peak_performance_hours: string[]
}

export interface ProgressPrediction {
  target_completion_date: string
  success_probability: number
  estimated_final_score: number
  bottleneck_areas: string[]
  recommended_adjustments: Array<{
    type: 'study_time' | 'difficulty' | 'focus_areas'
    description: string
    expected_impact: number
  }>
}

export interface ComparisonData {
  current_student: StudentProgressOverview
  class_average: {
    progress: number
    study_time: number
    accuracy: number
    completion_rate: number
  }
  percentile_ranking: number
  similar_students: StudentProgressOverview[]
  improvement_opportunities: string[]
}

export interface ProgressAlert {
  id: number
  type: 'performance_drop' | 'inactivity' | 'goal_deadline' | 'achievement'
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  created_at: string
  action_required: boolean
  suggested_actions: string[]
}

export interface StudySession {
  session_id: number
  start_time: string
  end_time: string
  duration_minutes: number
  training_type: string
  difficulty_level: string
  questions_attempted: number
  questions_correct: number
  accuracy_rate: number
  average_response_time: number
  knowledge_points_covered: string[]
  performance_score: number
}

export interface ProgressFilter {
  time_range: {
    start_date: string
    end_date: string
  }
  training_types?: string[]
  difficulty_levels?: string[]
  knowledge_categories?: string[]
  performance_threshold?: {
    min_score: number
    max_score: number
  }
  student_ids?: number[]
  class_ids?: number[]
}

export interface ProgressExportOptions {
  format: 'pdf' | 'excel' | 'csv' | 'json'
  include_charts: boolean
  include_detailed_data: boolean
  include_recommendations: boolean
  date_range: {
    start_date: string
    end_date: string
  }
  sections: Array<
    'overview' | 'timeline' | 'knowledge_points' | 'comparisons' | 'predictions'
  >
}

export interface ProgressDashboardConfig {
  refresh_interval: number
  default_time_range: number
  visible_metrics: string[]
  chart_preferences: {
    theme: 'light' | 'dark'
    animation_enabled: boolean
    show_grid: boolean
    color_scheme: string[]
  }
  notification_settings: {
    email_enabled: boolean
    push_enabled: boolean
    alert_types: string[]
  }
}

export interface LearningGoal {
  goal_id: number
  title: string
  description: string
  target_value: number
  current_value: number
  unit: string
  deadline: string
  priority: 'low' | 'medium' | 'high'
  category: 'skill' | 'knowledge' | 'performance' | 'time'
  created_at: string
  status: 'active' | 'completed' | 'paused' | 'cancelled'
  milestones: Array<{
    milestone_id: number
    title: string
    target_value: number
    completed: boolean
    completed_at?: string
  }>
}

export interface ProgressInsight {
  insight_id: number
  type: 'strength' | 'weakness' | 'opportunity' | 'trend'
  title: string
  description: string
  confidence_score: number
  supporting_data: Record<string, any>
  recommendations: string[]
  priority: number
  created_at: string
}

export interface LearningPath {
  path_id: number
  name: string
  description: string
  total_steps: number
  completed_steps: number
  estimated_duration: number
  difficulty_level: string
  prerequisites: string[]
  learning_objectives: string[]
  progress_percentage: number
  next_recommended_step: {
    step_id: number
    title: string
    estimated_time: number
  }
}
