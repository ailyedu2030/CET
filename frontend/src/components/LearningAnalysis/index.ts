/**
 * 学情分析组件统一导出
 * 需求24：AI智能分析与学情报告生成
 */

export { default as PersonalLearningReportComponent } from './PersonalLearningReportComponent'
export { default as ClassLearningReportComponent } from './ClassLearningReportComponent'

// 导出类型定义
export type {
  // 核心类型定义
  StudentAbilityAssessment,
  KnowledgePointMastery,
  LearningBehaviorAnalysis,
  ProgressTrendPrediction,
  PersonalizedRecommendations,
  RiskWarning,
  PersonalLearningReport,
  ClassOverallAssessment,
  ClassKnowledgeMasteryAnalysis,
  ClassProgressMonitoring,
  TeachingEffectivenessEvaluation,
  DifferentiatedAnalysis,
  ClassLearningReport,
  IntelligentGradingResult,
  DataFeedbackMechanism,
  ReportPushConfiguration,
  InteractiveReport,
  // API请求和响应类型
  LearningReportAnalysisRequest,
  BatchAnalysisRequest,
  ReportExportRequest,
  DataSyncStatus,
} from '../../api/learningAnalysisReport'
