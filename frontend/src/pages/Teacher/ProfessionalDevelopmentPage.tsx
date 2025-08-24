/**
 * 专业发展支持页面 - 需求17实现
 * 提供教学能力培训资源、专业认证辅导材料、教师社区交流平台和教育教学研究最新动态推送
 */
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Paper,
  Progress,
  Select,
  Stack,
  Tabs,
  Text,
  TextInput,
  Title,
  Timeline,
  Avatar,
  Alert,
  Grid,
  Anchor,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconBook,
  IconCertificate,
  IconUsers,
  IconNews,
  IconSearch,
  IconFilter,
  IconPlus,
  IconHeart,
  IconMessage,
  IconShare,
  IconDownload,
  IconStar,
  IconTrendingUp,
  IconCalendar,
  IconUser,
  IconBell,
} from '@tabler/icons-react'
import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

// 模拟数据类型
interface TrainingResource {
  id: number
  title: string
  category: string
  description: string
  duration: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  rating: number
  enrolledCount: number
  isEnrolled: boolean
  progress?: number
}

interface CommunityPost {
  id: number
  author: string
  avatar: string
  title: string
  content: string
  category: string
  likes: number
  replies: number
  createdAt: string
  isLiked: boolean
}

interface ResearchUpdate {
  id: number
  title: string
  source: string
  summary: string
  publishedAt: string
  category: string
  importance: 'high' | 'medium' | 'low'
}

export function ProfessionalDevelopmentPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('training')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('')

  // 模态框状态
  const [postModalOpened, { open: openPostModal, close: closePostModal }] = useDisclosure(false)
  const [settingsOpened, { open: openSettings, close: closeSettings }] = useDisclosure(false)

  // 模拟数据查询
  const { data: trainingData } = useQuery({
    queryKey: ['training-resources', searchQuery, filterCategory],
    queryFn: async () => {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      return [
        {
          id: 1,
          title: '在线教学技能提升',
          category: '教学技能',
          description: '掌握现代在线教学工具和方法',
          duration: '8小时',
          difficulty: 'intermediate' as const,
          rating: 4.8,
          enrolledCount: 1250,
          isEnrolled: true,
          progress: 65,
        },
        {
          id: 2,
          title: 'CET-4教学方法研究',
          category: '专业认证',
          description: '深入了解CET-4考试特点和教学策略',
          duration: '12小时',
          difficulty: 'advanced' as const,
          rating: 4.9,
          enrolledCount: 890,
          isEnrolled: false,
        },
      ] as TrainingResource[]
    },
  })

  const { data: communityData } = useQuery({
    queryKey: ['community-posts', searchQuery],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 800))
      return [
        {
          id: 1,
          author: '张老师',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=zhang',
          title: '如何提高学生的听力理解能力？',
          content: '最近在教学中发现学生的听力理解能力有待提高，想请教各位老师有什么好的方法...',
          category: '教学方法',
          likes: 23,
          replies: 8,
          createdAt: '2024-01-15',
          isLiked: false,
        },
        {
          id: 2,
          author: '李老师',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=li',
          title: '分享一个写作教学的小技巧',
          content: '在写作教学中，我发现使用思维导图可以有效帮助学生组织思路...',
          category: '经验分享',
          likes: 45,
          replies: 12,
          createdAt: '2024-01-14',
          isLiked: true,
        },
      ] as CommunityPost[]
    },
  })

  const { data: researchData } = useQuery({
    queryKey: ['research-updates'],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 600))
      return [
        {
          id: 1,
          title: '人工智能在英语教学中的应用研究',
          source: '教育技术学报',
          summary: '研究表明AI技术可以显著提高英语学习效率，特别是在个性化学习方面...',
          publishedAt: '2024-01-16',
          category: 'AI教育',
          importance: 'high' as const,
        },
        {
          id: 2,
          title: '混合式教学模式的效果评估',
          source: '现代教育技术',
          summary: '对比传统教学和混合式教学的效果，发现混合式教学在学生参与度方面有显著优势...',
          publishedAt: '2024-01-15',
          category: '教学模式',
          importance: 'medium' as const,
        },
      ] as ResearchUpdate[]
    },
  })

  const handleEnrollCourse = useCallback((_courseId: number) => {
    notifications.show({
      title: '报名成功',
      message: '您已成功报名该培训课程',
      color: 'green',
    })
  }, [])

  const handleLikePost = useCallback((_postId: number) => {
    notifications.show({
      title: '操作成功',
      message: '已点赞该帖子',
      color: 'blue',
    })
  }, [])

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'green'
      case 'intermediate':
        return 'yellow'
      case 'advanced':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high':
        return 'red'
      case 'medium':
        return 'yellow'
      case 'low':
        return 'gray'
      default:
        return 'gray'
    }
  }

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>专业发展支持</Title>
          <Text c="dimmed" mt="xs">
            培训资源、认证辅导、社区交流和研究动态 - 需求17实现
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconBell size={16} />} variant="light" onClick={openSettings}>
            通知设置
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={openPostModal}>
            发布话题
          </Button>
        </Group>
      </Group>

      {/* 功能标签页 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'training')} mb="xl">
        <Tabs.List>
          <Tabs.Tab value="training" leftSection={<IconBook size={16} />}>
            培训资源
          </Tabs.Tab>
          <Tabs.Tab value="certification" leftSection={<IconCertificate size={16} />}>
            认证辅导
          </Tabs.Tab>
          <Tabs.Tab value="community" leftSection={<IconUsers size={16} />}>
            社区交流
          </Tabs.Tab>
          <Tabs.Tab value="research" leftSection={<IconNews size={16} />}>
            研究动态
          </Tabs.Tab>
        </Tabs.List>

        {/* 培训资源标签页 */}
        <Tabs.Panel value="training">
          <Alert color="blue" mb="md">
            <Text size="sm">提供教学能力培训资源，支持在线学习和进度跟踪</Text>
          </Alert>

          {/* 搜索和筛选 */}
          <Paper withBorder p="md" mb="md">
            <Group>
              <TextInput
                placeholder="搜索培训课程..."
                leftSection={<IconSearch size={16} />}
                value={searchQuery}
                onChange={event => setSearchQuery(event.currentTarget.value)}
                style={{ flex: 1 }}
              />
              <Select
                placeholder="分类筛选"
                leftSection={<IconFilter size={16} />}
                value={filterCategory}
                onChange={value => setFilterCategory(value || '')}
                data={[
                  { value: '', label: '全部分类' },
                  { value: '教学技能', label: '教学技能' },
                  { value: '专业认证', label: '专业认证' },
                  { value: '技术应用', label: '技术应用' },
                ]}
                clearable
                style={{ minWidth: 150 }}
              />
            </Group>
          </Paper>

          {/* 培训课程列表 */}
          <Grid>
            {trainingData?.map(course => (
              <Grid.Col key={course.id} span={{ base: 12, md: 6 }}>
                <Card withBorder>
                  <Group justify="space-between" mb="sm">
                    <Badge variant="light" color={getDifficultyColor(course.difficulty)}>
                      {course.difficulty === 'beginner' && '初级'}
                      {course.difficulty === 'intermediate' && '中级'}
                      {course.difficulty === 'advanced' && '高级'}
                    </Badge>
                    <Group gap="xs">
                      <IconStar size={14} />
                      <Text size="sm">{course.rating}</Text>
                    </Group>
                  </Group>

                  <Text fw={500} mb="xs">
                    {course.title}
                  </Text>
                  <Text size="sm" c="dimmed" mb="md">
                    {course.description}
                  </Text>

                  <Group justify="space-between" mb="md">
                    <Text size="sm">
                      <IconCalendar size={14} style={{ marginRight: 4 }} />
                      {course.duration}
                    </Text>
                    <Text size="sm">
                      <IconUser size={14} style={{ marginRight: 4 }} />
                      {course.enrolledCount} 人已报名
                    </Text>
                  </Group>

                  {course.isEnrolled && course.progress && (
                    <div>
                      <Group justify="space-between" mb="xs">
                        <Text size="sm">学习进度</Text>
                        <Text size="sm">{course.progress}%</Text>
                      </Group>
                      <Progress value={course.progress} mb="md" />
                    </div>
                  )}

                  <Group justify="space-between">
                    <Badge variant="outline">{course.category}</Badge>
                    {course.isEnrolled ? (
                      <Button size="sm" variant="light">
                        继续学习
                      </Button>
                    ) : (
                      <Button size="sm" onClick={() => handleEnrollCourse(course.id)}>
                        立即报名
                      </Button>
                    )}
                  </Group>
                </Card>
              </Grid.Col>
            ))}
          </Grid>
        </Tabs.Panel>

        {/* 认证辅导标签页 */}
        <Tabs.Panel value="certification">
          <Alert color="indigo" mb="md">
            <Text size="sm">提供专业认证辅导材料，助力教师职业发展</Text>
          </Alert>

          <Grid>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder>
                <Text fw={500} mb="sm">教师资格证</Text>
                <Text size="sm" c="dimmed" mb="md">
                  教师资格证考试辅导材料和模拟试题
                </Text>
                <Group justify="space-between">
                  <Badge variant="light" color="blue">热门</Badge>
                  <Button size="sm" variant="light">查看资料</Button>
                </Group>
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder>
                <Text fw={500} mb="sm">英语专业八级</Text>
                <Text size="sm" c="dimmed" mb="md">
                  专业八级考试备考指南和练习题库
                </Text>
                <Group justify="space-between">
                  <Badge variant="light" color="green">推荐</Badge>
                  <Button size="sm" variant="light">查看资料</Button>
                </Group>
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder>
                <Text fw={500} mb="sm">TESOL认证</Text>
                <Text size="sm" c="dimmed" mb="md">
                  国际英语教师资格认证培训材料
                </Text>
                <Group justify="space-between">
                  <Badge variant="light" color="orange">新增</Badge>
                  <Button size="sm" variant="light">查看资料</Button>
                </Group>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 社区交流标签页 */}
        <Tabs.Panel value="community">
          <Alert color="teal" mb="md">
            <Text size="sm">教师社区交流平台，分享经验、讨论问题、共同成长</Text>
          </Alert>

          <Stack gap="md">
            {communityData?.map(post => (
              <Card key={post.id} withBorder>
                <Group justify="space-between" mb="sm">
                  <Group>
                    <Avatar src={post.avatar} size="sm" />
                    <div>
                      <Text size="sm" fw={500}>{post.author}</Text>
                      <Text size="xs" c="dimmed">{post.createdAt}</Text>
                    </div>
                  </Group>
                  <Badge variant="light">{post.category}</Badge>
                </Group>

                <Text fw={500} mb="xs">{post.title}</Text>
                <Text size="sm" c="dimmed" mb="md">{post.content}</Text>

                <Group justify="space-between">
                  <Group>
                    <ActionIcon
                      variant={post.isLiked ? 'filled' : 'light'}
                      color="red"
                      onClick={() => handleLikePost(post.id)}
                    >
                      <IconHeart size={16} />
                    </ActionIcon>
                    <Text size="sm">{post.likes}</Text>
                    <ActionIcon variant="light">
                      <IconMessage size={16} />
                    </ActionIcon>
                    <Text size="sm">{post.replies}</Text>
                  </Group>
                  <ActionIcon variant="light">
                    <IconShare size={16} />
                  </ActionIcon>
                </Group>
              </Card>
            ))}
          </Stack>
        </Tabs.Panel>

        {/* 研究动态标签页 */}
        <Tabs.Panel value="research">
          <Alert color="yellow" mb="md">
            <Text size="sm">教育教学研究最新动态推送，把握行业发展趋势</Text>
          </Alert>

          <Timeline active={-1} bulletSize={24} lineWidth={2}>
            {researchData?.map(update => (
              <Timeline.Item
                key={update.id}
                bullet={<IconTrendingUp size={12} />}
                title={
                  <Group justify="space-between">
                    <Text fw={500}>{update.title}</Text>
                    <Badge variant="light" color={getImportanceColor(update.importance)}>
                      {update.importance === 'high' && '重要'}
                      {update.importance === 'medium' && '一般'}
                      {update.importance === 'low' && '参考'}
                    </Badge>
                  </Group>
                }
              >
                <Text size="sm" c="dimmed" mb="xs">
                  来源：{update.source} | {update.publishedAt}
                </Text>
                <Text size="sm" mb="md">
                  {update.summary}
                </Text>
                <Group>
                  <Badge variant="outline" size="sm">{update.category}</Badge>
                  <Anchor size="sm">阅读全文</Anchor>
                  <ActionIcon variant="light" size="sm">
                    <IconDownload size={14} />
                  </ActionIcon>
                </Group>
              </Timeline.Item>
            ))}
          </Timeline>
        </Tabs.Panel>
      </Tabs>

      {/* 发布话题模态框 */}
      <Modal opened={postModalOpened} onClose={closePostModal} title="发布新话题" size="lg">
        <Stack gap="md">
          <TextInput label="话题标题" placeholder="输入话题标题" required />
          <Select
            label="分类"
            placeholder="选择分类"
            data={[
              { value: 'teaching', label: '教学方法' },
              { value: 'experience', label: '经验分享' },
              { value: 'question', label: '问题求助' },
              { value: 'discussion', label: '学术讨论' },
            ]}
            required
          />
          <TextInput label="内容" placeholder="详细描述您的话题内容..." required />
          <Group justify="flex-end">
            <Button variant="light" onClick={closePostModal}>
              取消
            </Button>
            <Button onClick={closePostModal}>发布</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 通知设置模态框 */}
      <Modal opened={settingsOpened} onClose={closeSettings} title="通知设置" size="md">
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            配置您希望接收的通知类型
          </Text>
          {/* 通知设置内容 */}
          <Group justify="flex-end">
            <Button variant="light" onClick={closeSettings}>
              取消
            </Button>
            <Button onClick={closeSettings}>保存设置</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
