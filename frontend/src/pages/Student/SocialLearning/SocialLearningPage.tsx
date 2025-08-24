import React, { useState, useEffect, useRef } from 'react'
import {
  Container,
  Grid,
  Card,
  Text,
  Button,
  Badge,
  Group,
  Stack,
  Title,
  Tabs,
  ActionIcon,
  Alert,
  Loader,
  Center,
  Avatar,
  Modal,
  Textarea,
  Select,
  Paper,
  Divider,
  ThemeIcon,
  Progress,
  RingProgress,
  Menu,
} from '@mantine/core'
import {
  IconUsers,
  IconTrophy,
  IconMessage,
  IconShare,
  IconPlus,
  IconDots,
  IconFlag,
  IconThumbUp,
  IconChartBar,
  IconCrown,
  IconMedal,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { socialLearningApi } from '@/api/socialLearning'

// 社交功能接口（将在后续版本中使用）

interface StudyGroup {
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
}

interface Discussion {
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
}

interface Achievement {
  id: number
  name: string
  description: string
  icon: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  achievedAt: string
  points: number
}

interface LeaderboardEntry {
  rank: number
  user: {
    id: number
    name: string
    avatar?: string
    level: number
  }
  score: number
  change: number
}

export const SocialLearningPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('groups')
  const [createGroupModalOpened, setCreateGroupModalOpened] = useState(false)
  const [_createDiscussionModalOpened, _setCreateDiscussionModalOpened] = useState(false)
  const [_selectedGroup, _setSelectedGroup] = useState<number | null>(null)

  // 社交功能状态（将在后续版本中使用）

  // WebSocket连接状态
  const [isConnected, setIsConnected] = useState(false)
  const [onlineUsers, setOnlineUsers] = useState<number>(0)
  const [realtimeMessages, setRealtimeMessages] = useState<
    Array<{
      id: string
      type: 'discussion' | 'reply' | 'like' | 'user_join' | 'user_leave'
      content: string
      timestamp: Date
      user: string
    }>
  >([])

  // WebSocket引用（将在后续版本中使用）
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 模拟WebSocket连接
  useEffect(() => {
    // 模拟WebSocket连接
    const connectWebSocket = () => {
      try {
        // 在实际项目中，这里应该连接到真实的WebSocket服务器
        // wsRef.current = new WebSocket('ws://localhost:8080/ws/social')

        // 模拟连接成功
        setIsConnected(true)
        setOnlineUsers(Math.floor(Math.random() * 50) + 10)

        // 模拟接收实时消息
        const messageInterval = setInterval(() => {
          const messageTypes = ['discussion', 'reply', 'like', 'user_join', 'user_leave'] as const
          const randomIndex = Math.floor(Math.random() * messageTypes.length)
          const randomType = messageTypes[randomIndex]

          if (randomType) {
            const newMessage = {
              id: Date.now().toString(),
              type: randomType,
              content: getRandomMessage(randomType),
              timestamp: new Date(),
              user: `用户${Math.floor(Math.random() * 100)}`,
            }

            setRealtimeMessages(prev => [...prev.slice(-9), newMessage])

            // 更新在线用户数
            if (randomType === 'user_join') {
              setOnlineUsers(prev => prev + 1)
            } else if (randomType === 'user_leave') {
              setOnlineUsers(prev => Math.max(1, prev - 1))
            }
          }
        }, 3000)

        return () => {
          clearInterval(messageInterval)
          setIsConnected(false)
        }
      } catch (error) {
        setIsConnected(false)
        return () => {}
      }
    }

    const cleanup = connectWebSocket()

    return cleanup
  }, [])

  // 滚动到消息底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [realtimeMessages])

  const getRandomMessage = (
    type: 'discussion' | 'reply' | 'like' | 'user_join' | 'user_leave'
  ): string => {
    const messages = {
      discussion: [
        '发起了新的讨论：如何提高听力理解能力？',
        '分享了学习经验：词汇记忆技巧',
        '提问：翻译练习的重点是什么？',
      ],
      reply: ['回复了讨论：我觉得多听英语新闻很有帮助', '分享了解题思路', '提供了学习资源链接'],
      like: ['点赞了一个讨论', '收藏了学习资料', '关注了学习伙伴'],
      user_join: ['加入了学习讨论', '开始了在线学习'],
      user_leave: ['结束了学习会话', '离开了讨论区'],
    }
    const typeMessages = messages[type] || ['进行了学习活动']
    return typeMessages[Math.floor(Math.random() * typeMessages.length)] || '进行了学习活动'
  }

  // 表单状态
  const [groupForm, setGroupForm] = useState({
    name: '',
    description: '',
    subject: 'english',
    maxMembers: 10,
  })

  const [_discussionForm, _setDiscussionForm] = useState({
    title: '',
    content: '',
    groupId: null as number | null,
    tags: [] as string[],
  })

  const queryClient = useQueryClient()

  // 获取学习小组
  const { data: groups, isLoading: groupsLoading } = useQuery({
    queryKey: ['study-groups'],
    queryFn: () => socialLearningApi.getStudyGroups(),
  })

  // 获取讨论列表
  const { data: discussions, isLoading: discussionsLoading } = useQuery({
    queryKey: ['discussions'],
    queryFn: () => socialLearningApi.getDiscussions(),
  })

  // 获取成就列表
  const { data: achievements, isLoading: achievementsLoading } = useQuery({
    queryKey: ['achievements'],
    queryFn: () => socialLearningApi.getAchievements(),
  })

  // 获取排行榜
  const { data: leaderboard, isLoading: leaderboardLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => socialLearningApi.getLeaderboard(),
  })

  // 加入小组
  const joinGroupMutation = useMutation({
    mutationFn: (groupId: number) => socialLearningApi.joinGroup(groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['study-groups'] })
      notifications.show({
        title: '加入成功',
        message: '您已成功加入学习小组！',
        color: 'green',
      })
    },
  })

  // 创建小组
  const createGroupMutation = useMutation({
    mutationFn: (data: {
      name: string
      description: string
      subject: string
      maxMembers: number
    }) => socialLearningApi.createGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['study-groups'] })
      setCreateGroupModalOpened(false)
      setGroupForm({ name: '', description: '', subject: 'english', maxMembers: 10 })
      notifications.show({
        title: '创建成功',
        message: '学习小组创建成功！',
        color: 'green',
      })
    },
  })

  // 点赞讨论
  const likeDiscussionMutation = useMutation({
    mutationFn: (discussionId: number) => socialLearningApi.likeDiscussion(discussionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discussions'] })
    },
  })

  const handleJoinGroup = (groupId: number) => {
    joinGroupMutation.mutate(groupId)
  }

  const handleCreateGroup = () => {
    if (!groupForm.name.trim()) {
      notifications.show({
        title: '请填写小组名称',
        message: '小组名称不能为空',
        color: 'orange',
      })
      return
    }
    createGroupMutation.mutate(groupForm)
  }

  const handleLikeDiscussion = (discussionId: number) => {
    likeDiscussionMutation.mutate(discussionId)
  }

  const getRarityColor = (rarity: string) => {
    const colors = {
      common: 'gray',
      rare: 'blue',
      epic: 'purple',
      legendary: 'orange',
    }
    return colors[rarity as keyof typeof colors] || 'gray'
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))

    if (diffInHours < 1) return '刚刚'
    if (diffInHours < 24) return `${diffInHours}小时前`
    return `${Math.floor(diffInHours / 24)}天前`
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>学习社交</Title>
        <Group>
          {/* 在线状态指示器 */}
          <Group gap="xs">
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: isConnected ? '#51cf66' : '#fa5252',
              }}
            />
            <Text size="sm" c="dimmed">
              {isConnected ? `${onlineUsers}人在线` : '离线'}
            </Text>
          </Group>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setCreateGroupModalOpened(true)}
          >
            创建小组
          </Button>
        </Group>
      </Group>

      {/* 实时活动流 */}
      {realtimeMessages.length > 0 && (
        <Alert icon={<IconMessage size={16} />} title="实时学习动态" color="blue" mb="lg">
          <Stack gap="xs" mah={120} style={{ overflow: 'auto' }}>
            {realtimeMessages.slice(-3).map(message => (
              <Group key={message.id} gap="xs">
                <Text size="xs" fw={500} c="blue">
                  {message.user}
                </Text>
                <Text size="xs" c="dimmed">
                  {message.content}
                </Text>
                <Text size="xs" c="dimmed">
                  {message.timestamp.toLocaleTimeString()}
                </Text>
              </Group>
            ))}
            <div ref={messagesEndRef} />
          </Stack>
        </Alert>
      )}

      <Tabs value={activeTab} onChange={value => value && setActiveTab(value)}>
        <Tabs.List>
          <Tabs.Tab value="groups" leftSection={<IconUsers size={16} />}>
            学习小组
          </Tabs.Tab>
          <Tabs.Tab value="discussions" leftSection={<IconMessage size={16} />}>
            讨论交流
          </Tabs.Tab>
          <Tabs.Tab value="achievements" leftSection={<IconTrophy size={16} />}>
            成就系统
          </Tabs.Tab>
          <Tabs.Tab value="leaderboard" leftSection={<IconChartBar size={16} />}>
            排行榜
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="groups" pt="md">
          {groupsLoading ? (
            <Center h={200}>
              <Loader />
            </Center>
          ) : (
            <Grid>
              {groups?.groups?.map((group: StudyGroup) => (
                <Grid.Col key={group.id} span={{ base: 12, md: 6, lg: 4 }}>
                  <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                    <Stack justify="space-between" h="100%">
                      <div>
                        <Group justify="space-between" mb="md">
                          <Avatar src={group.avatar} size="lg" radius="md" color="blue">
                            {group.name.charAt(0)}
                          </Avatar>
                          <Badge color="blue" variant="light">
                            {group.subject}
                          </Badge>
                        </Group>

                        <Text fw={600} size="lg" mb="xs">
                          {group.name}
                        </Text>
                        <Text size="sm" c="dimmed" lineClamp={2} mb="md">
                          {group.description}
                        </Text>

                        <Group justify="space-between" mb="md">
                          <Text size="sm" c="dimmed">
                            {group.memberCount}/{group.maxMembers} 成员
                          </Text>
                          <Badge size="sm" variant="light">
                            {group.level}
                          </Badge>
                        </Group>

                        <Progress
                          value={(group.memberCount / group.maxMembers) * 100}
                          size="sm"
                          mb="md"
                        />

                        <Text size="xs" c="dimmed">
                          最近活动: {group.recentActivity}
                        </Text>
                      </div>

                      <Button
                        fullWidth
                        variant={group.isJoined ? 'light' : 'filled'}
                        onClick={() => !group.isJoined && handleJoinGroup(group.id)}
                        disabled={group.isJoined || group.memberCount >= group.maxMembers}
                        loading={joinGroupMutation.isPending}
                      >
                        {group.isJoined
                          ? '已加入'
                          : group.memberCount >= group.maxMembers
                            ? '已满员'
                            : '加入小组'}
                      </Button>
                    </Stack>
                  </Card>
                </Grid.Col>
              )) || (
                <Grid.Col span={12}>
                  <Alert icon={<IconUsers size={16} />} title="暂无学习小组" color="blue">
                    还没有学习小组，创建一个开始学习交流吧！
                  </Alert>
                </Grid.Col>
              )}
            </Grid>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="discussions" pt="md">
          <Group justify="space-between" mb="md">
            <Text size="lg" fw={600}>
              最新讨论
            </Text>
            <Button
              size="sm"
              leftSection={<IconPlus size={14} />}
              onClick={() => _setCreateDiscussionModalOpened(true)}
            >
              发起讨论
            </Button>
          </Group>

          {discussionsLoading ? (
            <Center h={200}>
              <Loader />
            </Center>
          ) : (
            <Stack gap="md">
              {discussions?.discussions?.map((discussion: Discussion) => (
                <Card key={discussion.id} shadow="sm" padding="lg" radius="md" withBorder>
                  <Group justify="space-between" mb="md">
                    <Group gap="sm">
                      <Avatar src={discussion.author.avatar} size="md" radius="xl">
                        {discussion.author.name.charAt(0)}
                      </Avatar>
                      <div>
                        <Group gap="xs">
                          <Text fw={500}>{discussion.author.name}</Text>
                          <Badge size="xs" color="blue">
                            Lv.{discussion.author.level}
                          </Badge>
                        </Group>
                        <Group gap="xs">
                          <Text size="xs" c="dimmed">
                            {discussion.groupName}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {formatTimeAgo(discussion.createdAt)}
                          </Text>
                        </Group>
                      </div>
                    </Group>
                    <Menu>
                      <Menu.Target>
                        <ActionIcon variant="subtle">
                          <IconDots size={16} />
                        </ActionIcon>
                      </Menu.Target>
                      <Menu.Dropdown>
                        <Menu.Item leftSection={<IconShare size={14} />}>分享</Menu.Item>
                        <Menu.Item leftSection={<IconFlag size={14} />} color="red">
                          举报
                        </Menu.Item>
                      </Menu.Dropdown>
                    </Menu>
                  </Group>

                  <Text fw={600} mb="xs">
                    {discussion.title}
                  </Text>
                  <Text size="sm" lineClamp={3} mb="md">
                    {discussion.content}
                  </Text>

                  {discussion.tags.length > 0 && (
                    <Group gap="xs" mb="md">
                      {discussion.tags.map((tag, index) => (
                        <Badge key={index} size="sm" variant="light">
                          {tag}
                        </Badge>
                      ))}
                    </Group>
                  )}

                  <Group justify="space-between">
                    <Group gap="lg">
                      <Button
                        variant="subtle"
                        size="sm"
                        leftSection={<IconThumbUp size={14} />}
                        color={discussion.isLiked ? 'blue' : 'gray'}
                        onClick={() => handleLikeDiscussion(discussion.id)}
                      >
                        {discussion.likeCount}
                      </Button>
                      <Button
                        variant="subtle"
                        size="sm"
                        leftSection={<IconMessage size={14} />}
                        color="gray"
                      >
                        {discussion.replyCount}
                      </Button>
                    </Group>
                  </Group>
                </Card>
              )) || (
                <Alert icon={<IconMessage size={16} />} title="暂无讨论" color="blue">
                  还没有讨论内容，发起第一个讨论吧！
                </Alert>
              )}
            </Stack>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="achievements" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  我的成就
                </Text>
                {achievementsLoading ? (
                  <Center h={200}>
                    <Loader />
                  </Center>
                ) : (
                  <Grid>
                    {achievements?.achievements?.map((achievement: Achievement) => (
                      <Grid.Col key={achievement.id} span={{ base: 12, sm: 6 }}>
                        <Paper p="md" withBorder radius="md">
                          <Group gap="md">
                            <ThemeIcon
                              size="xl"
                              color={getRarityColor(achievement.rarity)}
                              variant="light"
                            >
                              <Text size="lg">{achievement.icon}</Text>
                            </ThemeIcon>
                            <div style={{ flex: 1 }}>
                              <Group justify="space-between" mb="xs">
                                <Text fw={600}>{achievement.name}</Text>
                                <Badge size="sm" color={getRarityColor(achievement.rarity)}>
                                  {achievement.rarity}
                                </Badge>
                              </Group>
                              <Text size="sm" c="dimmed" mb="xs">
                                {achievement.description}
                              </Text>
                              <Group justify="space-between">
                                <Text size="xs" c="dimmed">
                                  {formatTimeAgo(achievement.achievedAt)}
                                </Text>
                                <Text size="xs" fw={500} c="blue">
                                  +{achievement.points} 积分
                                </Text>
                              </Group>
                            </div>
                          </Group>
                        </Paper>
                      </Grid.Col>
                    )) || (
                      <Grid.Col span={12}>
                        <Alert icon={<IconTrophy size={16} />} title="暂无成就" color="blue">
                          完成学习任务来解锁您的第一个成就吧！
                        </Alert>
                      </Grid.Col>
                    )}
                  </Grid>
                )}
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                <Text size="lg" fw={600} mb="md">
                  成就统计
                </Text>
                <Stack gap="md">
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm" c="dimmed">
                        总积分
                      </Text>
                      <Text fw={700}>2,450</Text>
                    </Group>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm" c="dimmed">
                        成就数量
                      </Text>
                      <Text fw={700}>{achievements?.achievements?.length || 0}</Text>
                    </Group>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm" c="dimmed">
                        等级
                      </Text>
                      <Text fw={700}>15</Text>
                    </Group>
                  </div>

                  <Divider />

                  <div>
                    <Text size="sm" fw={500} mb="xs">
                      稀有度分布
                    </Text>
                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Badge size="sm" color="gray">
                          普通
                        </Badge>
                        <Text size="sm">12</Text>
                      </Group>
                      <Group justify="space-between">
                        <Badge size="sm" color="blue">
                          稀有
                        </Badge>
                        <Text size="sm">5</Text>
                      </Group>
                      <Group justify="space-between">
                        <Badge size="sm" color="purple">
                          史诗
                        </Badge>
                        <Text size="sm">2</Text>
                      </Group>
                      <Group justify="space-between">
                        <Badge size="sm" color="orange">
                          传说
                        </Badge>
                        <Text size="sm">1</Text>
                      </Group>
                    </Stack>
                  </div>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="leaderboard" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  学习排行榜
                </Text>
                {leaderboardLoading ? (
                  <Center h={200}>
                    <Loader />
                  </Center>
                ) : (
                  <Stack gap="md">
                    {leaderboard?.entries?.map((entry: LeaderboardEntry, _index: number) => (
                      <Paper key={entry.user.id} p="md" withBorder radius="md">
                        <Group justify="space-between">
                          <Group gap="md">
                            <div style={{ position: 'relative' }}>
                              <Avatar src={entry.user.avatar} size="lg" radius="xl">
                                {entry.user.name.charAt(0)}
                              </Avatar>
                              {entry.rank <= 3 && (
                                <ThemeIcon
                                  size="sm"
                                  color={
                                    entry.rank === 1
                                      ? 'yellow'
                                      : entry.rank === 2
                                        ? 'gray'
                                        : 'orange'
                                  }
                                  variant="filled"
                                  style={{
                                    position: 'absolute',
                                    top: -5,
                                    right: -5,
                                  }}
                                >
                                  {entry.rank === 1 ? (
                                    <IconCrown size={12} />
                                  ) : entry.rank === 2 ? (
                                    <IconMedal size={12} />
                                  ) : (
                                    <IconMedal size={12} />
                                  )}
                                </ThemeIcon>
                              )}
                            </div>
                            <div>
                              <Group gap="xs">
                                <Text fw={600}>{entry.user.name}</Text>
                                <Badge size="sm" color="blue">
                                  Lv.{entry.user.level}
                                </Badge>
                              </Group>
                              <Text size="sm" c="dimmed">
                                积分: {entry.score.toLocaleString()}
                              </Text>
                            </div>
                          </Group>
                          <Group gap="md">
                            <div style={{ textAlign: 'right' }}>
                              <Text size="xl" fw={700}>
                                #{entry.rank}
                              </Text>
                              <Group gap="xs" justify="flex-end">
                                {entry.change > 0 && (
                                  <Text size="xs" c="green">
                                    ↑{entry.change}
                                  </Text>
                                )}
                                {entry.change < 0 && (
                                  <Text size="xs" c="red">
                                    ↓{Math.abs(entry.change)}
                                  </Text>
                                )}
                                {entry.change === 0 && (
                                  <Text size="xs" c="gray">
                                    -
                                  </Text>
                                )}
                              </Group>
                            </div>
                          </Group>
                        </Group>
                      </Paper>
                    )) || (
                      <Alert icon={<IconChartBar size={16} />} title="暂无排行数据" color="blue">
                        开始学习来登上排行榜吧！
                      </Alert>
                    )}
                  </Stack>
                )}
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Stack gap="md">
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                  <Text size="lg" fw={600} mb="md">
                    我的排名
                  </Text>
                  <Center>
                    <RingProgress
                      size={120}
                      thickness={12}
                      sections={[{ value: 75, color: 'blue' }]}
                      label={
                        <div style={{ textAlign: 'center' }}>
                          <Text size="lg" fw={700}>
                            #15
                          </Text>
                          <Text size="xs" c="dimmed">
                            排名
                          </Text>
                        </div>
                      }
                    />
                  </Center>
                  <Text size="sm" ta="center" c="dimmed" mt="md">
                    超越了 85% 的学习者
                  </Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                  <Text size="lg" fw={600} mb="md">
                    本周目标
                  </Text>
                  <Stack gap="sm">
                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="sm">学习时间</Text>
                        <Text size="sm">12h / 15h</Text>
                      </Group>
                      <Progress value={80} size="sm" />
                    </div>
                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="sm">完成题目</Text>
                        <Text size="sm">85 / 100</Text>
                      </Group>
                      <Progress value={85} size="sm" />
                    </div>
                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="sm">社交互动</Text>
                        <Text size="sm">8 / 10</Text>
                      </Group>
                      <Progress value={80} size="sm" />
                    </div>
                  </Stack>
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>
      </Tabs>

      {/* 创建小组模态框 */}
      <Modal
        opened={createGroupModalOpened}
        onClose={() => setCreateGroupModalOpened(false)}
        title="创建学习小组"
        size="md"
      >
        <Stack gap="md">
          <Textarea
            label="小组名称"
            placeholder="输入小组名称"
            value={groupForm.name}
            onChange={event => setGroupForm({ ...groupForm, name: event.currentTarget.value })}
            required
          />
          <Textarea
            label="小组描述"
            placeholder="描述小组的学习目标和特色"
            value={groupForm.description}
            onChange={event =>
              setGroupForm({ ...groupForm, description: event.currentTarget.value })
            }
            rows={3}
          />
          <Select
            label="学习科目"
            value={groupForm.subject}
            onChange={value => setGroupForm({ ...groupForm, subject: value || 'english' })}
            data={[
              { value: 'english', label: '英语四级' },
              { value: 'listening', label: '听力专项' },
              { value: 'reading', label: '阅读专项' },
              { value: 'writing', label: '写作专项' },
            ]}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setCreateGroupModalOpened(false)}>
              取消
            </Button>
            <Button onClick={handleCreateGroup} loading={createGroupMutation.isPending}>
              创建小组
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
