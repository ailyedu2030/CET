export enum TrainingType {
  LISTENING = 'listening',
  READING = 'reading',
  WRITING = 'writing',
  TRANSLATION = 'translation',
  VOCABULARY = 'vocabulary',
  GRAMMAR = 'grammar',
  SPEAKING = 'speaking',
}

export enum DifficultyLevel {
  BEGINNER = 'beginner',
  ELEMENTARY = 'elementary',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert',
}

export interface TrainingSession {
  id: number
  type: TrainingType
  difficulty: DifficultyLevel
  questionCount: number
  timeLimit: number
  status: 'active' | 'paused' | 'completed'
  progress: number
  score: number
  startedAt: string
  completedAt?: string
  duration?: number
  finalScore?: number
}

export interface TrainingQuestion {
  id: number
  type: TrainingType
  difficulty: DifficultyLevel
  content: string
  options?: string[]
  correctAnswer: string
  explanation: string
  topic: string
  timeLimit: number
}

export interface TrainingResult {
  id: number
  sessionId: number
  questionId: number
  userAnswer: string
  isCorrect: boolean
  timeSpent: number
  submittedAt: string
}

export interface TrainingStats {
  totalSessions: number
  completedSessions: number
  averageScore: number
  totalTime: number
  streak: number
  level: number
  exp: number
  nextLevelExp: number
  bestScore: number
  improvementRate: number
}

export interface TrainingConfig {
  defaultQuestionCount: number
  defaultTimeLimit: number
  adaptiveMode: boolean
  notifications: boolean
  autoSave: boolean
}
