import React, { useState } from 'react'
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
  Progress,
  Modal,
  NumberInput,
  Textarea,
  Timeline,
  ThemeIcon,
  Paper,
} from '@mantine/core'
import { Calendar } from '@mantine/dates'
import {
  IconCalendar,
  IconTarget,
  IconTrendingUp,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCheck,
  IconChartBar,
  IconSettings,
  IconSparkles,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { DatePickerInput } from '@mantine/dates'
import { learningPlanApi } from '../../../api/learningPlan'
import { TrainingType, DifficultyLevel } from '../../../types/training'

interface LearningPlan {
  id: number
  title: string
  description: string
  targetScore: number
  targetDate: string
  status: 'active' | 'completed' | 'paused'
  progress: number
  createdAt: string
  tasks: LearningTask[]
}

interface LearningTask {
  id: number
  title: string
  type: TrainingType
  difficulty: DifficultyLevel
  targetCount: number
  completedCount: number
  deadline: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  priority: 'low' | 'medium' | 'high'
}

// AI智能计划生成算法
interface AIAnalysisData {
  currentLevel: number
  targetScore: number
  availableTime: number // 每日可用学习时间（分钟）
  weakAreas: string[]
  strongAreas: string[]
  learningStyle: 'visual' | 'auditory' | 'kinesthetic' | 'reading'
  studyHistory: {
    totalHours: number
    averageScore: number
    improvementRate: number
  }
}

// 学习路径优化算法
interface LearningPath {
  phase: string
  duration: number // 天数
  focus: string[]
  dailyTasks: {
    type: string
    duration: number
    priority: 'high' | 'medium' | 'low'
  }[]
  milestones: {
    day: number
    target: string
    metric: string
  }[]
}

// 数据可视化配置
interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string[]
    borderColor?: string
    fill?: boolean
  }[]
}

export const LearningPlanPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [createModalOpened, setCreateModalOpened] = useState(false)
  const [_calendarDate, _setCalendarDate] = useState<Date>(new Date())

  // AI智能分析状态
  const [aiAnalysisData, setAiAnalysisData] = useState<AIAnalysisData | null>(null)
  const [generatedPath, setGeneratedPath] = useState<LearningPath | null>(null)
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false)
  const [_chartData, setChartData] = useState<ChartData | null>(null)

  // AI智能计划生成算法
  const generateAILearningPlan = async (analysisData: AIAnalysisData): Promise<LearningPath> => {
    // 计算学习阶段
    const phases = calculateLearningPhases(analysisData)

    // 生成每日任务
    const dailyTasks = generateDailyTasks(analysisData)

    // 设置里程碑
    const milestones = generateMilestones(analysisData)

    return {
      phase: phases[0] || '基础强化阶段',
      duration: calculateTotalDuration(analysisData),
      focus: analysisData.weakAreas,
      dailyTasks,
      milestones,
    }
  }

  // 计算学习阶段
  const calculateLearningPhases = (data: AIAnalysisData): string[] => {
    const phases: string[] = []
    const timeDiff = new Date(data.targetScore).getTime() - new Date().getTime()
    const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24))

    if (daysLeft > 90) {
      phases.push('基础强化阶段', '技能提升阶段', '冲刺复习阶段')
    } else if (daysLeft > 30) {
      phases.push('重点突破阶段', '冲刺复习阶段')
    } else {
      phases.push('冲刺复习阶段')
    }

    return phases
  }

  // 生成每日任务
  const generateDailyTasks = (data: AIAnalysisData) => {
    const tasks = []
    const timePerTask = Math.floor(data.availableTime / 4) // 分配给4个主要任务

    // 根据薄弱环节生成任务
    for (const area of data.weakAreas.slice(0, 3)) {
      tasks.push({
        type: area,
        duration: timePerTask,
        priority: 'high' as const,
      })
    }

    // 添加复习任务
    tasks.push({
      type: '综合复习',
      duration: timePerTask,
      priority: 'medium' as const,
    })

    return tasks
  }

  // 生成学习里程碑
  const generateMilestones = (data: AIAnalysisData) => {
    const milestones = []
    const totalDays = calculateTotalDuration(data)

    // 每周设置一个里程碑
    for (let week = 1; week <= Math.ceil(totalDays / 7); week++) {
      milestones.push({
        day: week * 7,
        target: `第${week}周目标完成`,
        metric: `预期提升${Math.round((data.targetScore - data.currentLevel) / Math.ceil(totalDays / 7))}分`,
      })
    }

    return milestones
  }

  // 计算总学习时长
  const calculateTotalDuration = (data: AIAnalysisData): number => {
    const scoreDiff = data.targetScore - data.currentLevel
    const baseTime = scoreDiff * 2 // 每分提升需要2天
    const adjustedTime = baseTime * (data.studyHistory.improvementRate || 1)
    return Math.max(Math.ceil(adjustedTime), 7) // 最少7天
  }

  // 开始AI分析和计划生成
  const startAIAnalysis = async () => {
    setIsGeneratingPlan(true)

    try {
      // 模拟获取用户数据
      const mockAnalysisData: AIAnalysisData = {
        currentLevel: 450, // 当前分数
        targetScore: 550, // 目标分数
        availableTime: 120, // 每日2小时
        weakAreas: ['听力理解', '阅读速度', '词汇量'],
        strongAreas: ['语法基础', '写作结构'],
        learningStyle: 'visual',
        studyHistory: {
          totalHours: 50,
          averageScore: 450,
          improvementRate: 1.2,
        },
      }

      setAiAnalysisData(mockAnalysisData)

      // 生成学习路径
      const path = await generateAILearningPlan(mockAnalysisData)
      setGeneratedPath(path)

      // 生成图表数据
      generateChartData(mockAnalysisData, path)

      notifications.show({
        title: 'AI分析完成',
        message: '已为您生成个性化学习计划',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '分析失败',
        message: '生成学习计划时出现错误，请稍后重试',
        color: 'red',
      })
    } finally {
      setIsGeneratingPlan(false)
    }
  }

  // 生成图表数据
  const generateChartData = (analysisData: AIAnalysisData, _path: LearningPath) => {
    const progressData: ChartData = {
      labels: ['第1周', '第2周', '第3周', '第4周', '第5周', '第6周'],
      datasets: [
        {
          label: '预期分数',
          data: [
            analysisData.currentLevel,
            analysisData.currentLevel + 20,
            analysisData.currentLevel + 40,
            analysisData.currentLevel + 60,
            analysisData.currentLevel + 80,
            analysisData.targetScore,
          ],
          borderColor: '#228be6',
          backgroundColor: ['rgba(34, 139, 230, 0.1)'],
          fill: true,
        },
        {
          label: '实际分数',
          data: [
            analysisData.currentLevel,
            analysisData.currentLevel + 15,
            analysisData.currentLevel + 35,
            analysisData.currentLevel + 50,
            analysisData.currentLevel + 70,
            analysisData.currentLevel + 85,
          ],
          borderColor: '#51cf66',
          backgroundColor: ['rgba(81, 207, 102, 0.1)'],
          fill: true,
        },
      ],
    }

    setChartData(progressData)
  }

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    targetScore: 425,
    targetDate: new Date(),
    tasks: [] as any[],
  })

  // 智能计划生成状态（将在后续版本中使用）
  const [smartRecommendations, _setSmartRecommendations] = useState<{
    dailyStudyTime: number
    weeklyGoals: string[]
    priorityAreas: string[]
    studySchedule: Array<{
      day: string
      tasks: string[]
      duration: number
    }>
  } | null>(null)

  const queryClient = useQueryClient()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['learning-plan-stats'],
    queryFn: learningPlanApi.getPlanStats,
  })

  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ['learning-plans'],
    queryFn: () => learningPlanApi.getLearningPlans(),
  })

  const { data: todayTasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['today-tasks'],
    queryFn: learningPlanApi.getTodayTasks,
  })

  const createPlanMutation = useMutation({
    mutationFn: learningPlanApi.createPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learning-plans'] })
      queryClient.invalidateQueries({ queryKey: ['learning-plan-stats'] })
      setCreateModalOpened(false)
      setFormData({
        title: '',
        description: '',
        targetScore: 425,
        targetDate: new Date(),
        tasks: [],
      })
      notifications.show({
        title: '计划创建成功',
        message: '您的学习计划已创建，开始执行吧！',
        color: 'green',
      })
    },
    onError: (error: any) => {
      notifications.show({
        title: '创建失败',
        message: error.message || '无法创建学习计划，请稍后重试',
        color: 'red',
      })
    },
  })

  const updateTaskMutation = useMutation({
    mutationFn: learningPlanApi.updateTaskStatus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learning-plans'] })
      queryClient.invalidateQueries({ queryKey: ['today-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['learning-plan-stats'] })
    },
  })

  // 智能计划生成功能已在新的AI系统中实现

  const handleCreatePlan = () => {
    if (!formData.title.trim()) {
      notifications.show({
        title: '请填写计划标题',
        message: '计划标题不能为空',
        color: 'orange',
      })
      return
    }
    createPlanMutation.mutate(formData)
  }

  const handleTaskComplete = (taskId: number) => {
    updateTaskMutation.mutate({ taskId, status: 'completed' })
  }

  const getStatusColor = (status: string) => {
    const colors = {
      active: 'blue',
      completed: 'green',
      paused: 'yellow',
      pending: 'gray',
      in_progress: 'blue',
      overdue: 'red',
    }
    return colors[status as keyof typeof colors] || 'gray'
  }

  const getStatusLabel = (status: string) => {
    const labels = {
      active: '进行中',
      completed: '已完成',
      paused: '已暂停',
      pending: '待开始',
      in_progress: '进行中',
      overdue: '已逾期',
    }
    return labels[status as keyof typeof labels] || status
  }

  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'green',
      medium: 'yellow',
      high: 'red',
    }
    return colors[priority as keyof typeof colors] || 'gray'
  }

  const getTypeLabel = (type: TrainingType) => {
    const labels = {
      listening: '听力',
      reading: '阅读',
      writing: '写作',
      translation: '翻译',
      vocabulary: '词汇',
      grammar: '语法',
      speaking: '口语',
    }
    return labels[type as keyof typeof labels] || type
  }

  const handleTabChange = (value: string | null) => {
    if (value) {
      setActiveTab(value)
    }
  }

  if (statsLoading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    )
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>学习计划管理</Title>
        <Group>
          <Button leftSection={<IconPlus size={16} />} onClick={() => setCreateModalOpened(true)}>
            创建计划
          </Button>
          <ActionIcon variant="light" size="lg">
            <IconSettings size={20} />
          </ActionIcon>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={handleTabChange}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartBar size={16} />}>
            计划概览
          </Tabs.Tab>
          <Tabs.Tab value="plans" leftSection={<IconTarget size={16} />}>
            我的计划
          </Tabs.Tab>
          <Tabs.Tab value="calendar" leftSection={<IconCalendar size={16} />}>
            学习日历
          </Tabs.Tab>
          <Tabs.Tab value="progress" leftSection={<IconTrendingUp size={16} />}>
            进度跟踪
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Grid>
                <Grid.Col span={6}>
                  <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Group justify="space-between">
                      <div>
                        <Text size="sm" c="dimmed">
                          活跃计划
                        </Text>
                        <Text size="xl" fw={700}>
                          {stats?.activePlans || 0}
                        </Text>
                      </div>
                      <ThemeIcon color="blue" variant="light" size="xl">
                        <IconTarget size={24} />
                      </ThemeIcon>
                    </Group>
                  </Card>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Group justify="space-between">
                      <div>
                        <Text size="sm" c="dimmed">
                          完成任务
                        </Text>
                        <Text size="xl" fw={700}>
                          {stats?.completedTasks || 0}
                        </Text>
                      </div>
                      <ThemeIcon color="green" variant="light" size="xl">
                        <IconCheck size={24} />
                      </ThemeIcon>
                    </Group>
                  </Card>
                </Grid.Col>
              </Grid>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                <Text size="lg" fw={600} mb="md">
                  今日任务
                </Text>
                {tasksLoading ? (
                  <Center h={200}>
                    <Loader />
                  </Center>
                ) : (
                  <Stack gap="sm">
                    {todayTasks?.tasks?.slice(0, 5).map((task: LearningTask) => (
                      <Paper key={task.id} p="sm" withBorder radius="md">
                        <Group justify="space-between">
                          <div>
                            <Text size="sm" fw={500} lineClamp={1}>
                              {task.title}
                            </Text>
                            <Group gap="xs">
                              <Badge size="xs" color={getPriorityColor(task.priority)}>
                                {task.priority}
                              </Badge>
                              <Badge size="xs" variant="light">
                                {getTypeLabel(task.type)}
                              </Badge>
                            </Group>
                          </div>
                          <ActionIcon
                            size="sm"
                            color="green"
                            variant="light"
                            onClick={() => handleTaskComplete(task.id)}
                            disabled={task.status === 'completed'}
                          >
                            <IconCheck size={12} />
                          </ActionIcon>
                        </Group>
                        <Progress
                          value={(task.completedCount / task.targetCount) * 100}
                          size="xs"
                          mt="xs"
                        />
                      </Paper>
                    )) || (
                      <Alert icon={<IconCheck size={16} />} title="今日无任务" color="green">
                        您今天没有安排学习任务，可以休息一下！
                      </Alert>
                    )}
                  </Stack>
                )}
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="plans" pt="md">
          {plansLoading ? (
            <Center h={200}>
              <Loader />
            </Center>
          ) : (
            <Stack gap="md">
              {plans?.plans?.map((plan: LearningPlan) => (
                <Card key={plan.id} shadow="sm" padding="lg" radius="md" withBorder>
                  <Group justify="space-between" mb="md">
                    <div>
                      <Group gap="xs" mb="xs">
                        <Text size="lg" fw={600}>
                          {plan.title}
                        </Text>
                        <Badge color={getStatusColor(plan.status)}>
                          {getStatusLabel(plan.status)}
                        </Badge>
                      </Group>
                      <Text size="sm" c="dimmed" lineClamp={2}>
                        {plan.description}
                      </Text>
                    </div>
                    <Group gap="xs">
                      <ActionIcon variant="light">
                        <IconEdit size={16} />
                      </ActionIcon>
                      <ActionIcon variant="light" color="red">
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Group>
                  </Group>
                  <Progress value={plan.progress} size="lg" radius="xl" mb="md" />
                </Card>
              )) || (
                <Alert icon={<IconTarget size={16} />} title="暂无学习计划" color="blue">
                  您还没有创建任何学习计划。点击"创建计划"开始制定您的学习目标吧！
                </Alert>
              )}
            </Stack>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="calendar" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Calendar />
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                <Text size="lg" fw={600} mb="md">
                  {_calendarDate.toLocaleDateString()} 的任务
                </Text>
                <Stack gap="sm">
                  <Paper p="sm" withBorder radius="md">
                    <Text size="sm" fw={500}>
                      听力练习
                    </Text>
                    <Text size="xs" c="dimmed">
                      10:00 - 10:30
                    </Text>
                    <Badge size="xs" color="blue" mt="xs">
                      进行中
                    </Badge>
                  </Paper>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="progress" pt="md">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text size="lg" fw={600} mb="md">
              学习进度时间线
            </Text>
            <Timeline active={2} bulletSize={24} lineWidth={2}>
              <Timeline.Item
                bullet={
                  <ThemeIcon color="green" variant="light" size={24}>
                    <IconCheck size={12} />
                  </ThemeIcon>
                }
                title="基础词汇掌握"
              >
                <Text size="sm" c="dimmed">
                  已完成 500 个核心词汇的学习和记忆
                </Text>
              </Timeline.Item>
            </Timeline>
          </Card>
        </Tabs.Panel>
      </Tabs>

      <Modal
        opened={createModalOpened}
        onClose={() => setCreateModalOpened(false)}
        title="创建学习计划"
        size="lg"
      >
        <Stack gap="md">
          {/* 智能生成按钮 */}
          <Alert color="blue" title="AI智能推荐" mb="md">
            <Text size="sm" mb="md">
              基于您的学习数据和目标，AI可以为您生成个性化学习计划
            </Text>
            <Button
              variant="light"
              size="sm"
              leftSection={<IconSparkles size={16} />}
              onClick={startAIAnalysis}
              loading={isGeneratingPlan}
            >
              {isGeneratingPlan ? '正在分析...' : 'AI智能生成计划'}
            </Button>
          </Alert>

          {/* AI智能分析结果展示 */}
          {aiAnalysisData && generatedPath && (
            <Alert color="green" title="AI智能分析结果">
              <Stack gap="md">
                {/* 基础分析 */}
                <Grid>
                  <Grid.Col span={6}>
                    <Text size="sm">
                      <strong>当前水平：</strong>
                      {aiAnalysisData.currentLevel}分
                    </Text>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text size="sm">
                      <strong>目标分数：</strong>
                      {aiAnalysisData.targetScore}分
                    </Text>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text size="sm">
                      <strong>每日可用时间：</strong>
                      {aiAnalysisData.availableTime}分钟
                    </Text>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text size="sm">
                      <strong>预计学习周期：</strong>
                      {generatedPath.duration}天
                    </Text>
                  </Grid.Col>
                </Grid>

                {/* 薄弱环节分析 */}
                <div>
                  <Text size="sm" fw={500} mb="xs">
                    重点提升领域：
                  </Text>
                  <Group gap="xs">
                    {aiAnalysisData.weakAreas.map((area, index) => (
                      <Badge key={index} color="red" variant="light">
                        {area}
                      </Badge>
                    ))}
                  </Group>
                </div>

                {/* 优势领域 */}
                <div>
                  <Text size="sm" fw={500} mb="xs">
                    优势领域：
                  </Text>
                  <Group gap="xs">
                    {aiAnalysisData.strongAreas.map((area, index) => (
                      <Badge key={index} color="green" variant="light">
                        {area}
                      </Badge>
                    ))}
                  </Group>
                </div>

                {/* 学习路径 */}
                <div>
                  <Text size="sm" fw={500} mb="xs">
                    学习路径：
                  </Text>
                  <Text size="sm" c="dimmed">
                    {generatedPath.phase} - 专注于{generatedPath.focus.join('、')}的提升
                  </Text>
                </div>

                {/* 里程碑 */}
                <div>
                  <Text size="sm" fw={500} mb="xs">
                    学习里程碑：
                  </Text>
                  <Stack gap="xs">
                    {generatedPath.milestones.slice(0, 3).map((milestone, index) => (
                      <Group key={index} gap="xs">
                        <Badge size="sm" color="blue" variant="light">
                          第{milestone.day}天
                        </Badge>
                        <Text size="xs" c="dimmed">
                          {milestone.target} - {milestone.metric}
                        </Text>
                      </Group>
                    ))}
                  </Stack>
                </div>
              </Stack>
            </Alert>
          )}

          {/* 原有智能推荐展示 */}
          {smartRecommendations && !aiAnalysisData && (
            <Alert color="green" title="智能推荐结果">
              <Stack gap="xs">
                <Text size="sm">
                  <strong>建议每日学习时间：</strong>
                  {smartRecommendations.dailyStudyTime}分钟
                </Text>
                <Text size="sm">
                  <strong>重点提升领域：</strong>
                  {smartRecommendations.priorityAreas.join('、')}
                </Text>
                <Text size="sm">
                  <strong>本周学习目标：</strong>
                </Text>
                <Stack gap="xs" ml="md">
                  {smartRecommendations.weeklyGoals.slice(0, 3).map((goal, index) => (
                    <Text key={index} size="xs" c="dimmed">
                      • {goal}
                    </Text>
                  ))}
                </Stack>
              </Stack>
            </Alert>
          )}

          <Textarea
            label="计划标题"
            placeholder="输入您的学习计划标题"
            value={formData.title}
            onChange={event => setFormData({ ...formData, title: event.currentTarget.value })}
            required
          />

          <Textarea
            label="计划描述"
            placeholder="描述您的学习计划"
            value={formData.description}
            onChange={event => setFormData({ ...formData, description: event.currentTarget.value })}
            rows={3}
          />

          <NumberInput
            label="目标分数"
            value={formData.targetScore}
            onChange={value => setFormData({ ...formData, targetScore: Number(value) })}
            min={300}
            max={710}
            step={5}
          />
          <DatePickerInput
            label="目标日期"
            value={formData.targetDate}
            onChange={date => setFormData({ ...formData, targetDate: date || new Date() })}
            minDate={new Date()}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setCreateModalOpened(false)}>
              取消
            </Button>
            <Button onClick={handleCreatePlan} loading={createPlanMutation.isPending}>
              创建计划
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
