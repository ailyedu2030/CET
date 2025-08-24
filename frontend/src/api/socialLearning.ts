import { apiClient } from './client'

export interface StudyGroup {
  id: number
  name: string
  description: string
  memberCount: number
  maxMembers: number
  subject: string
  level: string
  isJoined: boolean
  recentActivity: string
  avatar?: string
  createdAt: string
  creator: {
    id: number
    name: string
    avatar?: string
  }
}

export interface Discussion {
  id: number
  title: string
  content: string
  author: {
    id: number
    name: string
    avatar?: string
    level: number
  }
  groupId: number
  groupName: string
  createdAt: string
  likeCount: number
  replyCount: number
  isLiked: boolean
  tags: string[]
  replies?: DiscussionReply[]
}

export interface DiscussionReply {
  id: number
  content: string
  author: {
    id: number
    name: string
    avatar?: string
    level: number
  }
  createdAt: string
  likeCount: number
  isLiked: boolean
}

export interface Achievement {
  id: number
  name: string
  description: string
  icon: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  achievedAt: string
  points: number
  category: string
}

export interface LeaderboardEntry {
  rank: number
  user: {
    id: number
    name: string
    avatar?: string
    level: number
  }
  score: number
  change: number
  weeklyScore: number
  monthlyScore: number
}

export const socialLearningApi = {
  // 获取学习小组列表
  getStudyGroups: async (
    params: {
      page?: number
      limit?: number
      subject?: string
      level?: string
      search?: string
    } = {}
  ): Promise<{
    groups: StudyGroup[]
    total: number
    page: number
    pageSize: number
  }> => {
    const response = await apiClient.get('/social/groups', { params })
    return response.data
  },

  // 创建学习小组
  createGroup: async (data: {
    name: string
    description: string
    subject: string
    maxMembers: number
    level?: string
    isPrivate?: boolean
  }): Promise<StudyGroup> => {
    const response = await apiClient.post('/social/groups', data)
    return response.data
  },

  // 加入学习小组
  joinGroup: async (groupId: number): Promise<void> => {
    await apiClient.post(`/social/groups/${groupId}/join`)
  },

  // 退出学习小组
  leaveGroup: async (groupId: number): Promise<void> => {
    await apiClient.post(`/social/groups/${groupId}/leave`)
  },

  // 获取小组详情
  getGroupDetail: async (
    groupId: number
  ): Promise<
    StudyGroup & {
      members: Array<{
        id: number
        name: string
        avatar?: string
        level: number
        joinedAt: string
        role: 'creator' | 'admin' | 'member'
      }>
      recentDiscussions: Discussion[]
      stats: {
        totalDiscussions: number
        totalMessages: number
        activeMembers: number
      }
    }
  > => {
    const response = await apiClient.get(`/social/groups/${groupId}`)
    return response.data
  },

  // 获取讨论列表
  getDiscussions: async (
    params: {
      page?: number
      limit?: number
      groupId?: number
      search?: string
      sortBy?: 'latest' | 'popular' | 'trending'
    } = {}
  ): Promise<{
    discussions: Discussion[]
    total: number
    page: number
    pageSize: number
  }> => {
    const response = await apiClient.get('/social/discussions', { params })
    return response.data
  },

  // 创建讨论
  createDiscussion: async (data: {
    title: string
    content: string
    groupId: number
    tags?: string[]
    attachments?: File[]
  }): Promise<Discussion> => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('content', data.content)
    formData.append('groupId', data.groupId.toString())

    if (data.tags) {
      formData.append('tags', JSON.stringify(data.tags))
    }

    if (data.attachments) {
      data.attachments.forEach((file, index) => {
        formData.append(`attachments[${index}]`, file)
      })
    }

    const response = await apiClient.post('/social/discussions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 点赞讨论
  likeDiscussion: async (discussionId: number): Promise<void> => {
    await apiClient.post(`/social/discussions/${discussionId}/like`)
  },

  // 回复讨论
  replyToDiscussion: async (
    discussionId: number,
    data: {
      content: string
      replyToId?: number
    }
  ): Promise<DiscussionReply> => {
    const response = await apiClient.post(`/social/discussions/${discussionId}/replies`, data)
    return response.data
  },

  // 获取讨论详情
  getDiscussionDetail: async (
    discussionId: number
  ): Promise<
    Discussion & {
      replies: DiscussionReply[]
    }
  > => {
    const response = await apiClient.get(`/social/discussions/${discussionId}`)
    return response.data
  },

  // 获取用户成就
  getAchievements: async (
    userId?: number
  ): Promise<{
    achievements: Achievement[]
    totalPoints: number
    level: number
    nextLevelPoints: number
    stats: {
      totalAchievements: number
      rareAchievements: number
      recentAchievements: Achievement[]
    }
  }> => {
    const url = userId ? `/social/achievements/${userId}` : '/social/achievements'
    const response = await apiClient.get(url)
    return response.data
  },

  // 获取排行榜
  getLeaderboard: async (
    params: {
      type?: 'weekly' | 'monthly' | 'all-time'
      category?: 'points' | 'study-time' | 'accuracy'
      limit?: number
    } = {}
  ): Promise<{
    entries: LeaderboardEntry[]
    userRank?: {
      rank: number
      score: number
      change: number
    }
    period: string
    lastUpdated: string
  }> => {
    const response = await apiClient.get('/social/leaderboard', { params })
    return response.data
  },

  // 获取学习伙伴推荐
  getStudyPartnerRecommendations: async (): Promise<
    Array<{
      user: {
        id: number
        name: string
        avatar?: string
        level: number
      }
      compatibility: number
      commonInterests: string[]
      studyStats: {
        averageScore: number
        studyTime: number
        activeGroups: number
      }
      reason: string
    }>
  > => {
    const response = await apiClient.get('/social/partner-recommendations')
    return response.data
  },

  // 发送学习邀请
  sendStudyInvitation: async (data: {
    userId: number
    message: string
    studyType: string
    scheduledTime?: string
  }): Promise<void> => {
    await apiClient.post('/social/study-invitations', data)
  },

  // 获取学习邀请
  getStudyInvitations: async (): Promise<
    Array<{
      id: number
      from: {
        id: number
        name: string
        avatar?: string
        level: number
      }
      message: string
      studyType: string
      scheduledTime?: string
      status: 'pending' | 'accepted' | 'declined'
      createdAt: string
    }>
  > => {
    const response = await apiClient.get('/social/study-invitations')
    return response.data
  },

  // 响应学习邀请
  respondToInvitation: async (
    invitationId: number,
    data: {
      action: 'accept' | 'decline'
      message?: string
    }
  ): Promise<void> => {
    await apiClient.post(`/social/study-invitations/${invitationId}/respond`, data)
  },

  // 获取社交统计
  getSocialStats: async (): Promise<{
    joinedGroups: number
    createdDiscussions: number
    receivedLikes: number
    helpedUsers: number
    studyPartners: number
    socialLevel: number
    socialExp: number
    nextLevelExp: number
    recentActivities: Array<{
      type: string
      description: string
      timestamp: string
      points: number
    }>
  }> => {
    const response = await apiClient.get('/social/stats')
    return response.data
  },

  // 举报内容
  reportContent: async (data: {
    contentType: 'discussion' | 'reply' | 'user'
    contentId: number
    reason: string
    description?: string
  }): Promise<void> => {
    await apiClient.post('/social/reports', data)
  },

  // 获取学习圈动态
  getLearningCircleActivity: async (
    params: {
      limit?: number
      type?: 'all' | 'groups' | 'discussions' | 'achievements'
    } = {}
  ): Promise<
    Array<{
      id: number
      type: string
      user: {
        id: number
        name: string
        avatar?: string
      }
      content: string
      timestamp: string
      metadata?: any
    }>
  > => {
    const response = await apiClient.get('/social/activity', { params })
    return response.data
  },
}
