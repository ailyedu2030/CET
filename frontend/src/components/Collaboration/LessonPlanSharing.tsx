/**
 * 教案共享与评论界面 - 需求16教研协作功能
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
  Menu,
  Modal,
  Select,
  TextInput,
  Divider,
  ScrollArea,
  Paper,
  Rating,
  Tabs,
} from '@mantine/core'
import {
  IconShare,
  IconHeart,
  IconHeartFilled,
  IconMessage,
  IconDots,
  IconEdit,
  IconDownload,
  IconEye,
  IconStar,
  IconStarFilled,
  IconPlus,
  IconSearch,
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

interface LessonPlan {
  id: number
  title: string
  description: string
  subject: string
  grade: string
  difficulty: string
  author: User
  createdAt: string
  likeCount: number
  commentCount: number
  favoriteCount: number
  isLiked: boolean
  isFavorited: boolean
  averageRating: number
}

interface LessonPlanComment {
  id: number
  author: User
  content: string
  rating?: number
  createdAt: string
}

// 临时API对象
const collaborationApi = {
  getSharedLessonPlans: async (_params?: any) => ({
    plans: [] as LessonPlan[],
    total: 0
  }),
  getMyLessonPlans: async () => ({
    plans: [] as LessonPlan[],
    total: 0
  }),
  getLessonPlanComments: async (_planId?: number) => [] as LessonPlanComment[],
  shareLessonPlan: async (_planData?: any) => ({}),
  addLessonPlanComment: async (_commentData?: any) => ({}),
  likeLessonPlan: async (_planId?: number) => ({}),
  favoriteLessonPlan: async (_planId?: number) => ({}),
  downloadLessonPlan: async (_planId?: number) => {},
}

interface LessonPlanSharingProps {
  /** 是否显示为教师视图 */
  teacherView?: boolean
  /** 初始筛选条件 */
  initialFilter?: {
    subject?: string
    grade?: string
    difficulty?: string
  }
}

export function LessonPlanSharing({
  teacherView = false,
  initialFilter = {},
}: LessonPlanSharingProps): JSX.Element {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [selectedPlan, setSelectedPlan] = useState<LessonPlan | null>(null)
  const [shareModalOpened, setShareModalOpened] = useState(false)
  const [commentText, setCommentText] = useState('')
  const [filter, setFilter] = useState(initialFilter)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState('shared')

  // 获取共享教案列表
  const {
    data: sharedPlans,
    isLoading: plansLoading,
    refetch: refetchPlans,
  } = useQuery({
    queryKey: ['lessonPlans', 'shared', filter, searchQuery],
    queryFn: () =>
      collaborationApi.getSharedLessonPlans({
        ...filter,
        search: searchQuery,
        page: 1,
        pageSize: 20,
      }),
    enabled: !!user,
  })

  // 获取我的教案列表
  const {
    data: myPlans,
    isLoading: myPlansLoading,
  } = useQuery({
    queryKey: ['lessonPlans', 'my'],
    queryFn: () => collaborationApi.getMyLessonPlans(),
    enabled: !!user && teacherView,
  })

  // 获取教案评论
  const {
    data: comments,
  } = useQuery({
    queryKey: ['lessonPlan', selectedPlan?.id, 'comments'],
    queryFn: () => collaborationApi.getLessonPlanComments(selectedPlan!.id),
    enabled: !!selectedPlan,
  })

  // 分享教案
  const sharePlanMutation = useMutation({
    mutationFn: (planData: {
      planId: number
      shareLevel: 'public' | 'school' | 'department'
      description?: string
    }) => collaborationApi.shareLessonPlan(planData),
    onSuccess: () => {
      notifications.show({
        title: '分享成功',
        message: '教案已成功分享',
        color: 'green',
      })
      setShareModalOpened(false)
      refetchPlans()
    },
  })

  // 添加评论
  const addCommentMutation = useMutation({
    mutationFn: (commentData: {
      planId: number
      content: string
      rating?: number
    }) => collaborationApi.addLessonPlanComment(commentData),
    onSuccess: () => {
      notifications.show({
        title: '评论成功',
        message: '您的评论已添加',
        color: 'green',
      })
      setCommentText('')
      queryClient.invalidateQueries({
        queryKey: ['lessonPlan', selectedPlan?.id, 'comments'],
      })
    },
  })

  // 点赞教案
  const likePlanMutation = useMutation({
    mutationFn: (planId: number) => collaborationApi.likeLessonPlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lessonPlans'] })
    },
  })

  // 收藏教案
  const favoritePlanMutation = useMutation({
    mutationFn: (planId: number) => collaborationApi.favoriteLessonPlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lessonPlans'] })
    },
  })



  const handleAddComment = () => {
    if (!selectedPlan || !commentText.trim()) return

    addCommentMutation.mutate({
      planId: selectedPlan.id,
      content: commentText.trim(),
    })
  }

  const handleSharePlan = (planId: number, shareLevel: string, description?: string) => {
    sharePlanMutation.mutate({
      planId,
      shareLevel: shareLevel as 'public' | 'school' | 'department',
      description,
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

  const LessonPlanCard = ({ plan }: { plan: LessonPlan }) => (
    <Card key={plan.id} p="md" withBorder>
      <Stack gap="sm">
        {/* 头部信息 */}
        <Group justify="space-between">
          <Group>
            <Avatar src={plan.author.avatar} size="sm">
              {plan.author.name.charAt(0)}
            </Avatar>
            <div>
              <Text size="sm" fw={500}>
                {plan.author.name}
              </Text>
              <Text size="xs" c="dimmed">
                {formatTimeAgo(plan.createdAt)}
              </Text>
            </div>
          </Group>
          
          <Menu position="bottom-end">
            <Menu.Target>
              <ActionIcon variant="subtle">
                <IconDots size={16} />
              </ActionIcon>
            </Menu.Target>
            
            <Menu.Dropdown>
              <Menu.Item
                leftSection={<IconEye size={14} />}
                onClick={() => setSelectedPlan(plan)}
              >
                查看详情
              </Menu.Item>
              
              <Menu.Item
                leftSection={<IconDownload size={14} />}
                onClick={() => collaborationApi.downloadLessonPlan(plan.id)}
              >
                下载教案
              </Menu.Item>
              
              {teacherView && plan.author.id === Number(user?.id) && (
                <>
                  <Menu.Item
                    leftSection={<IconShare size={14} />}
                    onClick={() => {
                      setSelectedPlan(plan)
                      setShareModalOpened(true)
                    }}
                  >
                    分享教案
                  </Menu.Item>
                  
                  <Menu.Item
                    leftSection={<IconEdit size={14} />}
                    onClick={() => {
                      // 跳转到编辑页面
                      window.location.href = `/teacher/lesson-plans/${plan.id}/edit`
                    }}
                  >
                    编辑教案
                  </Menu.Item>
                </>
              )}
            </Menu.Dropdown>
          </Menu>
        </Group>

        {/* 教案信息 */}
        <div>
          <Title order={4} mb="xs">
            {plan.title}
          </Title>
          <Text size="sm" c="dimmed" lineClamp={2}>
            {plan.description}
          </Text>
        </div>

        {/* 标签 */}
        <Group gap="xs">
          <Badge size="sm" variant="light" color="blue">
            {plan.subject}
          </Badge>
          <Badge size="sm" variant="light" color="green">
            {plan.grade}
          </Badge>
          <Badge size="sm" variant="light" color="orange">
            {plan.difficulty}
          </Badge>
        </Group>

        {/* 统计信息 */}
        <Group justify="space-between">
          <Group gap="md">
            <Group gap="xs">
              <ActionIcon
                variant="subtle"
                color={plan.isLiked ? 'red' : 'gray'}
                onClick={() => likePlanMutation.mutate(plan.id)}
              >
                {plan.isLiked ? (
                  <IconHeartFilled size={16} />
                ) : (
                  <IconHeart size={16} />
                )}
              </ActionIcon>
              <Text size="sm">{plan.likeCount}</Text>
            </Group>
            
            <Group gap="xs">
              <ActionIcon variant="subtle">
                <IconMessage size={16} />
              </ActionIcon>
              <Text size="sm">{plan.commentCount}</Text>
            </Group>
            
            <Group gap="xs">
              <ActionIcon
                variant="subtle"
                color={plan.isFavorited ? 'yellow' : 'gray'}
                onClick={() => favoritePlanMutation.mutate(plan.id)}
              >
                {plan.isFavorited ? (
                  <IconStarFilled size={16} />
                ) : (
                  <IconStar size={16} />
                )}
              </ActionIcon>
              <Text size="sm">{plan.favoriteCount}</Text>
            </Group>
          </Group>
          
          <Rating value={plan.averageRating} readOnly size="sm" />
        </Group>
      </Stack>
    </Card>
  )

  const CommentItem = ({ comment }: { comment: LessonPlanComment }) => (
    <Paper p="sm" withBorder>
      <Group justify="space-between" mb="xs">
        <Group>
          <Avatar src={comment.author.avatar} size="sm">
            {comment.author.name.charAt(0)}
          </Avatar>
          <div>
            <Text size="sm" fw={500}>
              {comment.author.name}
            </Text>
            <Text size="xs" c="dimmed">
              {formatTimeAgo(comment.createdAt)}
            </Text>
          </div>
        </Group>
        
        {comment.rating && (
          <Rating value={comment.rating} readOnly size="sm" />
        )}
      </Group>
      
      <Text size="sm">{comment.content}</Text>
    </Paper>
  )

  return (
    <div>
      {/* 头部工具栏 */}
      <Group justify="space-between" mb="md">
        <Title order={2}>教案共享中心</Title>
        
        <Group>
          <TextInput
            placeholder="搜索教案..."
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
          
          {teacherView && (
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => {
                window.location.href = '/teacher/lesson-plans/create'
              }}
            >
              创建教案
            </Button>
          )}
        </Group>
      </Group>

      {/* 标签页 */}
      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'shared')} mb="md">
        <Tabs.List>
          <Tabs.Tab value="shared">共享教案</Tabs.Tab>
          {teacherView && <Tabs.Tab value="my">我的教案</Tabs.Tab>}
          <Tabs.Tab value="favorites">我的收藏</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="shared" pt="md">
          {plansLoading ? (
            <Text ta="center" c="dimmed">
              加载中...
            </Text>
          ) : (
            <Stack gap="md">
              {sharedPlans?.plans.map((plan) => (
                <LessonPlanCard key={plan.id} plan={plan} />
              ))}
            </Stack>
          )}
        </Tabs.Panel>

        {teacherView && (
          <Tabs.Panel value="my" pt="md">
            {myPlansLoading ? (
              <Text ta="center" c="dimmed">
                加载中...
              </Text>
            ) : (
              <Stack gap="md">
                {myPlans?.plans.map((plan) => (
                  <LessonPlanCard key={plan.id} plan={plan} />
                ))}
              </Stack>
            )}
          </Tabs.Panel>
        )}

        <Tabs.Panel value="favorites" pt="md">
          <Text ta="center" c="dimmed">
            收藏功能开发中...
          </Text>
        </Tabs.Panel>
      </Tabs>

      {/* 教案详情模态框 */}
      <Modal
        opened={!!selectedPlan}
        onClose={() => setSelectedPlan(null)}
        title={selectedPlan?.title}
        size="lg"
      >
        {selectedPlan && (
          <Stack gap="md">
            {/* 教案内容 */}
            <div>
              <Text size="sm" c="dimmed" mb="xs">
                教案描述
              </Text>
              <Text>{selectedPlan.description}</Text>
            </div>

            <Divider />

            {/* 评论区 */}
            <div>
              <Title order={4} mb="md">
                评论 ({comments?.length || 0})
              </Title>
              
              {/* 添加评论 */}
              <Stack gap="sm" mb="md">
                <Textarea
                  placeholder="写下您的评论..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  minRows={3}
                />
                <Group justify="flex-end">
                  <Button
                    size="sm"
                    onClick={handleAddComment}
                    disabled={!commentText.trim()}
                    loading={addCommentMutation.isPending}
                  >
                    发表评论
                  </Button>
                </Group>
              </Stack>

              {/* 评论列表 */}
              <ScrollArea h={300}>
                <Stack gap="sm">
                  {comments?.map((comment) => (
                    <CommentItem key={comment.id} comment={comment} />
                  ))}
                </Stack>
              </ScrollArea>
            </div>
          </Stack>
        )}
      </Modal>

      {/* 分享教案模态框 */}
      <Modal
        opened={shareModalOpened}
        onClose={() => setShareModalOpened(false)}
        title="分享教案"
      >
        <Stack gap="md">
          <Select
            label="分享范围"
            placeholder="选择分享范围"
            data={[
              { value: 'department', label: '本部门' },
              { value: 'school', label: '全校' },
              { value: 'public', label: '公开' },
            ]}
          />
          
          <Textarea
            label="分享说明"
            placeholder="简单介绍一下这个教案..."
            minRows={3}
          />
          
          <Group justify="flex-end">
            <Button
              variant="subtle"
              onClick={() => setShareModalOpened(false)}
            >
              取消
            </Button>
            <Button
              onClick={() => {
                if (selectedPlan) {
                  handleSharePlan(selectedPlan.id, 'public', '分享教案')
                }
              }}
            >
              确认分享
            </Button>
          </Group>
        </Stack>
      </Modal>
    </div>
  )
}
