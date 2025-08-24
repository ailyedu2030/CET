/**
 * 教研协作类型定义 - 需求16教研协作功能
 */

// =================== 基础用户类型 ===================

export interface User {
  id: number
  name: string
  email: string
  avatar?: string
  role: 'teacher' | 'admin' | 'student'
  department?: string
  title?: string
}

// =================== 教案共享类型 ===================

export interface LessonPlan {
  id: number
  title: string
  description: string
  content: string
  subject: string
  grade: string
  difficulty: 'low' | 'medium' | 'high'
  author: User
  createdAt: string
  updatedAt: string
  
  // 互动数据
  likeCount: number
  commentCount: number
  favoriteCount: number
  downloadCount: number
  viewCount: number
  
  // 用户状态
  isLiked: boolean
  isFavorited: boolean
  isBookmarked: boolean
  
  // 评分
  averageRating: number
  ratingCount: number
  
  // 分享信息
  shareLevel: 'private' | 'department' | 'school' | 'public'
  isShared: boolean
  sharedAt?: string
  
  // 附件
  attachments: LessonPlanAttachment[]
  
  // 标签
  tags: string[]
  
  // 版本信息
  version: string
  parentPlanId?: number
}

export interface LessonPlanAttachment {
  id: number
  name: string
  url: string
  type: string
  size: number
  uploadedAt: string
}

export interface LessonPlanComment {
  id: number
  planId: number
  author: User
  content: string
  rating?: number
  createdAt: string
  updatedAt: string
  
  // 互动数据
  likeCount: number
  isLiked: boolean
  
  // 回复
  replyToId?: number
  replies: LessonPlanComment[]
}

export interface LessonPlanShare {
  id: number
  planId: number
  sharedBy: User
  shareLevel: 'department' | 'school' | 'public'
  description?: string
  sharedAt: string
  
  // 统计
  viewCount: number
  downloadCount: number
}

// =================== 教学难点讨论类型 ===================

export interface DiscussionTopic {
  id: number
  title: string
  content: string
  subject: string
  difficulty: 'low' | 'medium' | 'high'
  status: 'open' | 'discussing' | 'solved' | 'urgent'
  author: User
  createdAt: string
  updatedAt: string
  
  // 互动数据
  replyCount: number
  likeCount: number
  bookmarkCount: number
  viewCount: number
  
  // 用户状态
  isLiked: boolean
  isBookmarked: boolean
  
  // 标签
  tags: string[]
  
  // 解决方案
  solutionReplyId?: number
  solvedAt?: string
  solvedBy?: User
  
  // 最后活动
  lastReplyAt?: string
  lastReplyBy?: User
  
  // 紧急程度
  urgencyLevel: 'low' | 'medium' | 'high' | 'urgent'
}

export interface DiscussionReply {
  id: number
  topicId: number
  author: User
  content: string
  createdAt: string
  updatedAt: string
  
  // 互动数据
  likeCount: number
  isLiked: boolean
  
  // 回复关系
  replyToId?: number
  replyTo?: DiscussionReply
  replies: DiscussionReply[]
  
  // 解决方案标记
  isSolution: boolean
  markedAsSolutionAt?: string
  markedBy?: User
  
  // 附件
  attachments: DiscussionAttachment[]
}

export interface DiscussionAttachment {
  id: number
  name: string
  url: string
  type: string
  size: number
  uploadedAt: string
}

export interface TeachingDifficulty {
  id: number
  title: string
  description: string
  subject: string
  grade: string
  difficulty: 'low' | 'medium' | 'high'
  category: string
  
  // 解决方案
  solutions: TeachingSolution[]
  
  // 统计
  encounterCount: number
  solvedCount: number
  
  // 标签
  tags: string[]
  
  // 创建信息
  createdBy: User
  createdAt: string
  updatedAt: string
}

export interface TeachingSolution {
  id: number
  difficultyId: number
  title: string
  description: string
  steps: string[]
  resources: string[]
  effectiveness: number
  
  // 作者
  author: User
  createdAt: string
  
  // 验证
  verifiedBy?: User
  verifiedAt?: string
  isVerified: boolean
  
  // 反馈
  feedbacks: SolutionFeedback[]
  averageRating: number
}

export interface SolutionFeedback {
  id: number
  solutionId: number
  author: User
  rating: number
  comment: string
  createdAt: string
}

// =================== 优秀案例分享类型 ===================

export interface ExcellentCase {
  id: number
  title: string
  description: string
  content: string
  category: 'teaching_method' | 'student_engagement' | 'assessment' | 'technology_integration'
  subject: string
  grade: string
  author: User
  createdAt: string
  updatedAt: string
  
  // 互动数据
  likeCount: number
  favoriteCount: number
  viewCount: number
  downloadCount: number
  
  // 用户状态
  isLiked: boolean
  isFavorited: boolean
  
  // 评分
  averageRating: number
  ratingCount: number
  
  // 附件
  attachments: CaseAttachment[]
  
  // 标签
  tags: string[]
  
  // 审核状态
  status: 'pending' | 'approved' | 'rejected'
  reviewedBy?: User
  reviewedAt?: string
  reviewComments?: string
  
  // 特色标记
  isFeatured: boolean
  featuredAt?: string
}

export interface CaseAttachment {
  id: number
  name: string
  url: string
  type: string
  size: number
  description?: string
  uploadedAt: string
}

export interface CaseComment {
  id: number
  caseId: number
  author: User
  content: string
  rating?: number
  createdAt: string
  
  // 互动
  likeCount: number
  isLiked: boolean
  
  // 回复
  replyToId?: number
  replies: CaseComment[]
}

// =================== 协同编辑类型 ===================

export interface CollaborationSession {
  id: number
  title: string
  description: string
  type: 'lesson_plan' | 'syllabus' | 'document' | 'discussion'
  status: 'active' | 'paused' | 'completed' | 'cancelled'
  
  // 参与者
  creator: User
  participants: CollaborationParticipant[]
  maxParticipants: number
  
  // 时间
  createdAt: string
  startedAt?: string
  endedAt?: string
  lastActivityAt: string
  
  // 内容
  content: any
  version: number
  
  // 权限
  permissions: CollaborationPermissions
  
  // 活动记录
  activities: CollaborationActivity[]
}

export interface CollaborationParticipant {
  user: User
  role: 'owner' | 'editor' | 'viewer' | 'commenter'
  joinedAt: string
  lastActiveAt: string
  isOnline: boolean
  
  // 权限
  canEdit: boolean
  canComment: boolean
  canInvite: boolean
  canManage: boolean
}

export interface CollaborationPermissions {
  canEdit: boolean
  canComment: boolean
  canInvite: boolean
  canManage: boolean
  canDelete: boolean
  canExport: boolean
}

export interface CollaborationActivity {
  id: number
  sessionId: number
  user: User
  action: 'join' | 'leave' | 'edit' | 'comment' | 'save' | 'invite'
  description: string
  timestamp: string
  
  // 详细信息
  details?: {
    changes?: any
    comment?: string
    invitedUser?: User
  }
}

// =================== 权限控制类型 ===================

export interface CollaborationRole {
  id: number
  name: string
  description: string
  permissions: string[]
  isDefault: boolean
}

export interface PermissionRequest {
  id: number
  requester: User
  resourceType: string
  resourceId: number
  permission: string
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  
  // 审核信息
  reviewedBy?: User
  reviewedAt?: string
  reviewComments?: string
  
  // 时间
  requestedAt: string
  expiresAt?: string
}

// =================== 统计和分析类型 ===================

export interface CollaborationStats {
  totalSharedPlans: number
  totalDiscussions: number
  totalCases: number
  totalSessions: number
  
  // 用户贡献
  myContributions: {
    plansShared: number
    discussionsStarted: number
    repliesPosted: number
    casesSubmitted: number
    sessionsCreated: number
  }
  
  // 最近活动
  recentActivity: CollaborationActivity[]
  
  // 热门内容
  popularPlans: LessonPlan[]
  hotDiscussions: DiscussionTopic[]
  featuredCases: ExcellentCase[]
}

export interface UserCollaborationProfile {
  user: User
  stats: {
    plansShared: number
    discussionsStarted: number
    repliesPosted: number
    casesSubmitted: number
    totalLikes: number
    totalViews: number
  }
  
  // 徽章和成就
  badges: CollaborationBadge[]
  achievements: CollaborationAchievement[]
  
  // 专长领域
  expertise: string[]
  interests: string[]
  
  // 活动历史
  recentActivities: CollaborationActivity[]
}

export interface CollaborationBadge {
  id: number
  name: string
  description: string
  icon: string
  color: string
  earnedAt: string
  level?: number
}

export interface CollaborationAchievement {
  id: number
  name: string
  description: string
  icon: string
  progress: number
  target: number
  isCompleted: boolean
  completedAt?: string
}

// =================== 搜索和筛选类型 ===================

export interface CollaborationSearchParams {
  query?: string
  type?: 'lesson_plan' | 'discussion' | 'case' | 'session'
  subject?: string
  grade?: string
  difficulty?: string
  status?: string
  author?: string
  dateRange?: {
    start: string
    end: string
  }
  tags?: string[]
  sortBy?: 'relevance' | 'date' | 'popularity' | 'rating'
  sortOrder?: 'asc' | 'desc'
  page: number
  pageSize: number
}

export interface CollaborationSearchResult {
  lessonPlans: LessonPlan[]
  discussions: DiscussionTopic[]
  cases: ExcellentCase[]
  sessions: CollaborationSession[]
  total: number
  facets: {
    subjects: { name: string; count: number }[]
    grades: { name: string; count: number }[]
    difficulties: { name: string; count: number }[]
    authors: { name: string; count: number }[]
  }
}

// =================== 通知类型 ===================

export interface CollaborationNotification {
  id: number
  type: 'new_comment' | 'new_reply' | 'plan_shared' | 'session_invite' | 'solution_found'
  title: string
  message: string
  data: any
  isRead: boolean
  createdAt: string
  
  // 相关资源
  resourceType?: string
  resourceId?: number
  
  // 发送者
  sender?: User
}
