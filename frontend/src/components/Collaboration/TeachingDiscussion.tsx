/**
 * 教学难点讨论界面 - 需求16教研协作功能
 */

import { useState } from 'react'
import {
  Card,
  Group,
  Stack,
  Text,
  Title,
  Button,
  Badge,
  Avatar,
  Textarea,
  ActionIcon,
  Modal,
  Select,
  TextInput,
  Divider,
  ScrollArea,
  Paper,
  Tabs,
  Chip,
  Alert,
} from '@mantine/core'
import {
  IconPlus,
  IconMessage,
  IconThumbUp,
  IconBookmark,
  IconBookmarkFilled,
  IconSearch,
  IconQuestionMark,
  IconAlertCircle,
  IconCircleCheck,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'

// import { collaborationApi } from '@/api/collaboration'
import { useAuth } from '@/stores/authStore'

// 临时类型定义
interface User {
  id: number
  name: string
  avatar?: string
}

interface DiscussionTopic {
  id: number
  title: string
  content: string
  subject: string
  difficulty: string
  status: string
  author: User
  createdAt: string
  replyCount: number
  likeCount: number
  bookmarkCount: number
  isBookmarked: boolean
  tags: string[]
  lastReplyAt?: string
}

interface DiscussionReply {
  id: number
  author: User
  content: string
  createdAt: string
  likeCount: number
  isLiked: boolean
  isSolution: boolean
}

// 临时API对象
const collaborationApi = {
  getDiscussionTopics: async (_params?: any) => ({
    topics: [] as DiscussionTopic[],
    total: 0
  }),
  getDiscussionReplies: async (_topicId?: number) => [] as DiscussionReply[],
  createDiscussionTopic: async (_topicData?: any) => ({} as DiscussionTopic),
  addDiscussionReply: async (_replyData?: any) => ({} as DiscussionReply),
  likeDiscussionReply: async (_replyId?: number) => ({}),
  bookmarkDiscussionTopic: async (_topicId?: number) => ({}),
}

interface TeachingDiscussionProps {
  /** 是否显示为教师视图 */
  teacherView?: boolean
  /** 初始筛选条件 */
  initialFilter?: {
    subject?: string
    difficulty?: string
    status?: string
  }
}

export function TeachingDiscussion({
  teacherView: _teacherView = false,
  initialFilter = {},
}: TeachingDiscussionProps): JSX.Element {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [selectedTopic, setSelectedTopic] = useState<DiscussionTopic | null>(null)
  const [createModalOpened, setCreateModalOpened] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [filter, setFilter] = useState(initialFilter)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState('all')

  // 获取讨论话题列表
  const {
    data: topics,
    isLoading: topicsLoading,
    refetch: refetchTopics,
  } = useQuery({
    queryKey: ['discussions', 'topics', filter, searchQuery, activeTab],
    queryFn: () =>
      collaborationApi.getDiscussionTopics({
        ...filter,
        search: searchQuery,
        status: activeTab === 'all' ? undefined : activeTab,
        page: 1,
        pageSize: 20,
      }),
    enabled: !!user,
  })

  // 获取话题回复
  const {
    data: replies,
  } = useQuery({
    queryKey: ['discussion', selectedTopic?.id, 'replies'],
    queryFn: () => collaborationApi.getDiscussionReplies(selectedTopic!.id),
    enabled: !!selectedTopic,
  })

  // 创建讨论话题
  const createTopicMutation = useMutation({
    mutationFn: (topicData: {
      title: string
      content: string
      subject: string
      difficulty: string
      tags: string[]
    }) => collaborationApi.createDiscussionTopic(topicData),
    onSuccess: () => {
      notifications.show({
        title: '创建成功',
        message: '讨论话题已创建',
        color: 'green',
      })
      setCreateModalOpened(false)
      refetchTopics()
    },
  })

  // 添加回复
  const addReplyMutation = useMutation({
    mutationFn: (replyData: {
      topicId: number
      content: string
      replyToId?: number
    }) => collaborationApi.addDiscussionReply(replyData),
    onSuccess: () => {
      notifications.show({
        title: '回复成功',
        message: '您的回复已添加',
        color: 'green',
      })
      setReplyText('')
      queryClient.invalidateQueries({
        queryKey: ['discussion', selectedTopic?.id, 'replies'],
      })
    },
  })

  // 点赞回复
  const likeReplyMutation = useMutation({
    mutationFn: (replyId: number) => collaborationApi.likeDiscussionReply(replyId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['discussion', selectedTopic?.id, 'replies'],
      })
    },
  })

  // 收藏话题
  const bookmarkTopicMutation = useMutation({
    mutationFn: (topicId: number) => collaborationApi.bookmarkDiscussionTopic(topicId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discussions'] })
    },
  })

  const handleAddReply = () => {
    if (!selectedTopic || !replyText.trim()) return
    
    addReplyMutation.mutate({
      topicId: selectedTopic.id,
      content: replyText.trim(),
    })
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return '刚刚'
    if (diffInMinutes < 60) return `${diffInMinutes}分钟前`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}小时前`
    return `${Math.floor(diffInMinutes / 1440)}天前`
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'solved':
        return <IconCircleCheck size={16} color="green" />
      case 'discussing':
        return <IconMessage size={16} color="blue" />
      case 'urgent':
        return <IconAlertCircle size={16} color="red" />
      default:
        return <IconQuestionMark size={16} color="gray" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'solved':
        return 'green'
      case 'discussing':
        return 'blue'
      case 'urgent':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'high':
        return 'red'
      case 'medium':
        return 'orange'
      case 'low':
        return 'green'
      default:
        return 'gray'
    }
  }

  const TopicCard = ({ topic }: { topic: DiscussionTopic }) => (
    <Card key={topic.id} p="md" withBorder style={{ cursor: 'pointer' }}>
      <Stack gap="sm" onClick={() => setSelectedTopic(topic)}>
        {/* 头部信息 */}
        <Group justify="space-between">
          <Group>
            <Avatar src={topic.author.avatar} size="sm">
              {topic.author.name.charAt(0)}
            </Avatar>
            <div>
              <Text size="sm" fw={500}>
                {topic.author.name}
              </Text>
              <Text size="xs" c="dimmed">
                {formatTimeAgo(topic.createdAt)}
              </Text>
            </div>
          </Group>
          
          <Group gap="xs">
            {getStatusIcon(topic.status)}
            <ActionIcon
              variant="subtle"
              color={topic.isBookmarked ? 'yellow' : 'gray'}
              onClick={(e) => {
                e.stopPropagation()
                bookmarkTopicMutation.mutate(topic.id)
              }}
            >
              {topic.isBookmarked ? (
                <IconBookmarkFilled size={16} />
              ) : (
                <IconBookmark size={16} />
              )}
            </ActionIcon>
          </Group>
        </Group>

        {/* 话题标题和内容 */}
        <div>
          <Group mb="xs">
            <Title order={4} style={{ flex: 1 }}>
              {topic.title}
            </Title>
            <Badge
              size="sm"
              color={getStatusColor(topic.status)}
              variant="light"
            >
              {topic.status === 'solved' && '已解决'}
              {topic.status === 'discussing' && '讨论中'}
              {topic.status === 'urgent' && '紧急'}
            </Badge>
          </Group>
          
          <Text size="sm" c="dimmed" lineClamp={2}>
            {topic.content}
          </Text>
        </div>

        {/* 标签 */}
        <Group gap="xs">
          <Badge size="sm" variant="light" color="blue">
            {topic.subject}
          </Badge>
          <Badge
            size="sm"
            variant="light"
            color={getDifficultyColor(topic.difficulty)}
          >
            难度: {topic.difficulty}
          </Badge>
          {topic.tags.map((tag) => (
            <Chip key={tag} size="xs" variant="light">
              {tag}
            </Chip>
          ))}
        </Group>

        {/* 统计信息 */}
        <Group justify="space-between">
          <Group gap="md">
            <Group gap="xs">
              <IconMessage size={16} />
              <Text size="sm">{topic.replyCount} 回复</Text>
            </Group>
            
            <Group gap="xs">
              <IconThumbUp size={16} />
              <Text size="sm">{topic.likeCount} 赞</Text>
            </Group>
            
            <Group gap="xs">
              <IconBookmark size={16} />
              <Text size="sm">{topic.bookmarkCount} 收藏</Text>
            </Group>
          </Group>
          
          {topic.lastReplyAt && (
            <Text size="xs" c="dimmed">
              最后回复: {formatTimeAgo(topic.lastReplyAt)}
            </Text>
          )}
        </Group>
      </Stack>
    </Card>
  )

  const ReplyItem = ({ reply }: { reply: DiscussionReply }) => (
    <Paper p="sm" withBorder>
      <Group justify="space-between" mb="xs">
        <Group>
          <Avatar src={reply.author.avatar} size="sm">
            {reply.author.name.charAt(0)}
          </Avatar>
          <div>
            <Text size="sm" fw={500}>
              {reply.author.name}
            </Text>
            <Text size="xs" c="dimmed">
              {formatTimeAgo(reply.createdAt)}
            </Text>
          </div>
        </Group>
        
        <Group gap="xs">
          <ActionIcon
            variant="subtle"
            color={reply.isLiked ? 'blue' : 'gray'}
            onClick={() => likeReplyMutation.mutate(reply.id)}
          >
            <IconThumbUp size={14} />
          </ActionIcon>
          <Text size="xs">{reply.likeCount}</Text>
        </Group>
      </Group>
      
      <Text size="sm">{reply.content}</Text>
      
      {reply.isSolution && (
        <Alert
          icon={<IconCircleCheck size={16} />}
          color="green"
          variant="light"
          mt="xs"
        >
          此回复被标记为解决方案
        </Alert>
      )}
    </Paper>
  )

  return (
    <div>
      {/* 头部工具栏 */}
      <Group justify="space-between" mb="md">
        <Title order={2}>教学难点讨论</Title>
        
        <Group>
          <TextInput
            placeholder="搜索讨论..."
            leftSection={<IconSearch size={16} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          
          <Select
            placeholder="学科筛选"
            data={[
              { value: 'english', label: '英语' },
              { value: 'math', label: '数学' },
              { value: 'chinese', label: '语文' },
            ]}
            value={filter.subject}
            onChange={(value) => setFilter({ ...filter, subject: value || undefined })}
          />
          
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setCreateModalOpened(true)}
          >
            发起讨论
          </Button>
        </Group>
      </Group>

      {/* 状态标签页 */}
      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'all')} mb="md">
        <Tabs.List>
          <Tabs.Tab value="all">全部</Tabs.Tab>
          <Tabs.Tab value="discussing">讨论中</Tabs.Tab>
          <Tabs.Tab value="urgent">紧急</Tabs.Tab>
          <Tabs.Tab value="solved">已解决</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value={activeTab} pt="md">
          {topicsLoading ? (
            <Text ta="center" c="dimmed">
              加载中...
            </Text>
          ) : (
            <Stack gap="md">
              {topics?.topics.map((topic) => (
                <TopicCard key={topic.id} topic={topic} />
              ))}
            </Stack>
          )}
        </Tabs.Panel>
      </Tabs>

      {/* 讨论详情模态框 */}
      <Modal
        opened={!!selectedTopic}
        onClose={() => setSelectedTopic(null)}
        title={selectedTopic?.title}
        size="lg"
      >
        {selectedTopic && (
          <Stack gap="md">
            {/* 话题内容 */}
            <div>
              <Group mb="xs">
                <Avatar src={selectedTopic.author.avatar} size="sm">
                  {selectedTopic.author.name.charAt(0)}
                </Avatar>
                <div>
                  <Text size="sm" fw={500}>
                    {selectedTopic.author.name}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {formatTimeAgo(selectedTopic.createdAt)}
                  </Text>
                </div>
              </Group>
              
              <Text>{selectedTopic.content}</Text>
              
              <Group gap="xs" mt="sm">
                {selectedTopic.tags.map((tag) => (
                  <Chip key={tag} size="xs" variant="light">
                    {tag}
                  </Chip>
                ))}
              </Group>
            </div>

            <Divider />

            {/* 回复区 */}
            <div>
              <Title order={4} mb="md">
                回复 ({replies?.length || 0})
              </Title>
              
              {/* 添加回复 */}
              <Stack gap="sm" mb="md">
                <Textarea
                  placeholder="分享您的见解..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  minRows={3}
                />
                <Group justify="flex-end">
                  <Button
                    size="sm"
                    onClick={handleAddReply}
                    disabled={!replyText.trim()}
                    loading={addReplyMutation.isPending}
                  >
                    发表回复
                  </Button>
                </Group>
              </Stack>

              {/* 回复列表 */}
              <ScrollArea h={400}>
                <Stack gap="sm">
                  {replies?.map((reply) => (
                    <ReplyItem key={reply.id} reply={reply} />
                  ))}
                </Stack>
              </ScrollArea>
            </div>
          </Stack>
        )}
      </Modal>

      {/* 创建讨论模态框 */}
      <Modal
        opened={createModalOpened}
        onClose={() => setCreateModalOpened(false)}
        title="发起新讨论"
        size="md"
      >
        <Stack gap="md">
          <TextInput
            label="讨论标题"
            placeholder="简洁描述您遇到的教学难点..."
            required
          />
          
          <Textarea
            label="详细描述"
            placeholder="详细描述遇到的问题、已尝试的方法等..."
            minRows={4}
            required
          />
          
          <Group grow>
            <Select
              label="学科"
              placeholder="选择学科"
              data={[
                { value: 'english', label: '英语' },
                { value: 'math', label: '数学' },
                { value: 'chinese', label: '语文' },
              ]}
              required
            />
            
            <Select
              label="难度等级"
              placeholder="选择难度"
              data={[
                { value: 'low', label: '简单' },
                { value: 'medium', label: '中等' },
                { value: 'high', label: '困难' },
              ]}
              required
            />
          </Group>
          
          <TextInput
            label="标签"
            placeholder="用逗号分隔多个标签，如：语法,时态,练习"
          />
          
          <Group justify="flex-end">
            <Button
              variant="subtle"
              onClick={() => setCreateModalOpened(false)}
            >
              取消
            </Button>
            <Button
              onClick={() => {
                createTopicMutation.mutate({
                  title: '新讨论话题',
                  content: '讨论内容',
                  subject: 'english',
                  difficulty: 'medium',
                  tags: ['教学', '讨论'],
                })
              }}
            >
              发起讨论
            </Button>
          </Group>
        </Stack>
      </Modal>
    </div>
  )
}
