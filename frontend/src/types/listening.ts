/**
 * 听力训练系统类型定义 - 需求22
 */

import { DifficultyLevel } from './training'

// ==================== 基础类型 ====================

export type ListeningExerciseType =
  | 'short_conversation'
  | 'long_conversation'
  | 'passage'
  | 'lecture'

export type ListeningQuestionType = 'single_choice' | 'multiple_choice' | 'fill_blank' | 'dictation'

export type AudioPlaybackSpeed = 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 2.0

// ==================== 听力练习相关 ====================

export interface ListeningExerciseConfig {
  // 验收标准1：题型分类配置
  short_conversation: {
    count: number // 8个对话
    questions_per_dialogue: number // 每个对话1题
  }
  long_conversation: {
    count: number // 2段对话
    questions_per_dialogue: number // 每段对话3题
  }
  passage: {
    count: number // 3篇短文
    questions_per_passage: number // 每篇短文3题
  }
  lecture: {
    count: number // 1篇讲座
    questions_per_lecture: number // 每篇讲座5题
  }
}

export interface AudioSegment {
  id: string
  start_time: number
  end_time: number
  transcript: string
  speaker?: string
  speed_level: AudioPlaybackSpeed
  difficulty_markers?: string[] // 难点标记
}

export interface ListeningQuestion {
  id: number
  question_text: string
  options: string[]
  correct_answer: string | string[]
  explanation: string
  audio_start_time?: number
  audio_end_time?: number
  question_type: ListeningQuestionType
  difficulty_score?: number
  skill_focus: string[] // 考查技能点
}

// ==================== 训练会话相关 ====================

export interface ListeningSessionSettings {
  // 验收标准2：训练特性
  audio_speed: AudioPlaybackSpeed // 语速调节
  subtitles_enabled: boolean // 字幕辅助
  repeat_enabled: boolean // 重复播放
  pronunciation_practice: boolean // 口语跟读练习
  dictation_mode: boolean // 单词/短语听写训练
  auto_pause: boolean // 自动暂停
  highlight_keywords: boolean // 关键词高亮
}

export interface AudioProgress {
  current_time: number
  total_time: number
  play_count: number
  segments_played: string[]
  pause_points: number[]
  replay_segments: Array<{
    start: number
    end: number
    count: number
  }>
}

// 类型约束定义
export type ConfidenceLevel = 1 | 2 | 3 | 4 | 5
export type ScoreRange = number // 0-100
export type AccuracyRate = number // 0-1

export interface ListeningAnswer {
  question_id: number
  answer: string | string[]
  confidence_level: ConfidenceLevel // 1-5
  time_spent: number // 非负数，单位：毫秒
  attempt_count: number // 正整数
  audio_replays: number // 非负整数
}

// ==================== 智能辅助相关 ====================

export interface PhoneticDifficulty {
  // 验收标准3：音标识别练习
  phoneme: string
  accuracy_rate: AccuracyRate // 0-1之间的准确率
  confusion_pairs: string[] // 易混淆音标
  practice_words: string[]
  practice_suggestions: string[]
}

export interface ListeningWeakPoint {
  // 验收标准3：个人听力难点
  category: 'vocabulary' | 'grammar' | 'pronunciation' | 'speed' | 'accent' | 'context'
  description: string
  frequency: number // 非负整数，出现频次
  severity: 'low' | 'medium' | 'high'
  affected_question_types: ListeningQuestionType[]
  improvement_suggestions: string[]
  practice_exercises: string[]
}

export interface ErrorAnalysis {
  // 验收标准3：错误原因分析
  error_type:
    | 'mishearing'
    | 'vocabulary_gap'
    | 'grammar_confusion'
    | 'speed_issue'
    | 'context_misunderstanding'
  frequency: number // 非负整数，错误出现频次
  examples: Array<{
    question_text: string
    student_answer: string
    correct_answer: string
    audio_segment: string
  }>
  root_causes: string[]
  targeted_practice: string[]
}

export interface ListeningTip {
  // 验收标准3：场景化听力技巧
  category: 'pre_listening' | 'while_listening' | 'post_listening'
  exercise_type: ListeningExerciseType
  title: string
  description: string
  examples: string[]
  practice_methods: string[]
  difficulty_level: DifficultyLevel
}

// ==================== 评估和反馈 ====================

export interface PronunciationEvaluation {
  // 验收标准2：口语跟读练习评估
  overall_score: ScoreRange // 0-100
  pronunciation_score: ScoreRange // 0-100
  fluency_score: ScoreRange // 0-100
  accuracy_score: ScoreRange // 0-100
  rhythm_score: ScoreRange // 0-100
  intonation_score: ScoreRange // 0-100
  detailed_feedback: Array<{
    word: string
    phonetic: string
    score: ScoreRange // 0-100
    issues: string[]
    suggestions: string[]
    audio_comparison?: string
  }>
}

export interface ListeningAbilityAssessment {
  // 综合听力能力评估
  overall_level: DifficultyLevel
  sub_skills: {
    vocabulary_recognition: ScoreRange // 0-100
    grammar_comprehension: ScoreRange // 0-100
    pronunciation_understanding: ScoreRange // 0-100
    speed_adaptation: ScoreRange // 0-100
    context_inference: ScoreRange // 0-100
    detail_catching: ScoreRange // 0-100
    main_idea_grasping: ScoreRange // 0-100
  }
  progress_trend: Array<{
    date: string
    score: ScoreRange // 0-100
    skill_breakdown: Record<string, ScoreRange> // 0-100
  }>
  next_level_requirements: string[]
}

// ==================== UI状态相关 ====================

export interface ListeningTrainingState {
  // 当前训练状态
  current_exercise?: number
  current_question: number
  is_playing: boolean
  is_paused: boolean
  audio_loaded: boolean
  subtitles_visible: boolean
  answer_submitted: boolean
  session_active: boolean
  time_remaining?: number
}

export interface AudioPlayerState {
  // 音频播放器状态
  current_time: number
  duration: number
  is_playing: boolean
  is_loading: boolean
  playback_speed: AudioPlaybackSpeed
  volume: number
  is_muted: boolean
  current_segment?: string
  loop_enabled: boolean
}

// ==================== 练习生成配置 ====================

export interface ListeningExerciseGenerationConfig {
  // 智能练习生成配置
  target_skills: string[]
  difficulty_progression: boolean
  adaptive_difficulty: boolean
  focus_weak_points: boolean
  include_pronunciation: boolean
  include_dictation: boolean
  time_limit?: number
  question_count: number
  exercise_types: ListeningExerciseType[]
}

// ==================== 统计和报告 ====================

export interface ListeningPerformanceMetrics {
  // 听力表现指标
  accuracy_by_type: Record<ListeningExerciseType, number>
  speed_adaptation: Record<AudioPlaybackSpeed, number>
  improvement_rate: number
  consistency_score: number
  weak_areas: ListeningWeakPoint[]
  strong_areas: string[]
  recommended_practice: string[]
}

export interface ListeningProgressReport {
  // 听力进度报告
  period: string
  total_exercises: number
  completed_exercises: number
  average_score: number
  time_spent: number
  skill_improvements: Record<string, number>
  achievements: string[]
  next_goals: string[]
  detailed_analysis: ErrorAnalysis[]
}
