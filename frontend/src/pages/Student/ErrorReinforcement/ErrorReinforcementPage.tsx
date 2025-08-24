import React, { useState, useEffect } from 'react'
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
  Tooltip,
  Alert,
  Loader,
  Center,
  Select,
  Checkbox,
  Progress,
  Paper,
  Modal,
  Timeline,
  ThemeIcon,
  Accordion,
  Highlight,
} from '@mantine/core'
import {
  IconTarget,
  IconRefresh,
  IconTrendingUp,
  IconBrain,
  IconCheck,
  IconAlertCircle,
  IconBulb,
  IconPlayerPlay,
  IconBook,
  IconChartBar,
  IconStar,
  IconClock,
  IconSparkles,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { errorReinforcementApi, ErrorQuestion } from '@/api/errorReinforcement'
import { TrainingType, DifficultyLevel } from '../../../types/training'

// 艾宾浩斯遗忘曲线算法实现（将在后续版本中使用）

// 艾宾浩斯遗忘曲线标准间隔（将在后续版本中使用）

// 智能诊断分析接口
interface DiagnosisAnalysis {
  errorPatterns: {
    type: string
    frequency: number
    examples: string[]
    severity: 'low' | 'medium' | 'high'
  }[]
  knowledgeGaps: {
    topic: string
    mastery: number
    priority: number
    relatedErrors: string[]
  }[]
  learningStyle: {
    preferredType: 'visual' | 'auditory' | 'kinesthetic' | 'reading'
    confidence: number
    recommendations: string[]
  }
  difficultyProgression: {
    currentLevel: number
    suggestedNext: number
    readinessScore: number
  }
}

// 通知系统接口（将在后续版本中使用）

export const ErrorReinforcementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [selectedType, setSelectedType] = useState<string>('all')

  // 艾宾浩斯算法状态
  const [diagnosisAnalysis, setDiagnosisAnalysis] = useState<DiagnosisAnalysis | null>(null)

  // 艾宾浩斯算法实现（将在后续版本中使用）

  // 智能诊断分析
  const performDiagnosisAnalysis = (errorQuestions: ErrorQuestion[]): DiagnosisAnalysis => {
    // 错误模式分析
    const errorPatterns = analyzeErrorPatterns(errorQuestions)

    // 知识盲点分析
    const knowledgeGaps = analyzeKnowledgeGaps(errorQuestions)

    // 学习风格分析
    const learningStyle = analyzeLearningStyle(errorQuestions)

    // 难度进阶分析
    const difficultyProgression = analyzeDifficultyProgression(errorQuestions)

    return {
      errorPatterns,
      knowledgeGaps,
      learningStyle,
      difficultyProgression,
    }
  }

  // 错误模式分析
  const analyzeErrorPatterns = (questions: ErrorQuestion[]) => {
    const patterns: Record<string, { count: number; examples: string[] }> = {}

    questions.forEach(q => {
      const errorType = q.errorType || '其他错误'
      if (!patterns[errorType]) {
        patterns[errorType] = { count: 0, examples: [] }
      }
      patterns[errorType].count++
      if (patterns[errorType].examples.length < 3) {
        patterns[errorType].examples.push(q.questionText)
      }
    })

    return Object.entries(patterns).map(([type, data]) => {
      const severity: 'low' | 'medium' | 'high' =
        data.count > 5 ? 'high' : data.count > 2 ? 'medium' : 'low'
      return {
        type,
        frequency: data.count,
        examples: data.examples,
        severity,
      }
    })
  }

  // 知识盲点分析
  const analyzeKnowledgeGaps = (questions: ErrorQuestion[]) => {
    const topics: Record<string, { total: number; correct: number; errors: string[] }> = {}

    questions.forEach(q => {
      const topic = q.topic || '未分类'
      if (!topics[topic]) {
        topics[topic] = { total: 0, correct: 0, errors: [] }
      }
      topics[topic].total++
      // 根据掌握度判断是否正确（掌握度>80%认为已掌握）
      if (q.masteryLevel > 80) {
        topics[topic].correct++
      } else {
        topics[topic].errors.push(q.questionText)
      }
    })

    return Object.entries(topics)
      .map(([topic, data]) => ({
        topic,
        mastery: data.total > 0 ? (data.correct / data.total) * 100 : 0,
        priority: data.total - data.correct, // 错误数量作为优先级
        relatedErrors: data.errors.slice(0, 3),
      }))
      .sort((a, b) => b.priority - a.priority)
  }

  // 学习风格分析
  const analyzeLearningStyle = (_questions: ErrorQuestion[]) => {
    // 简化的学习风格分析，实际项目中可以基于用户行为数据
    return {
      preferredType: 'visual' as const,
      confidence: 0.75,
      recommendations: [
        '建议使用图表和思维导图学习',
        '可以尝试视频教程和动画演示',
        '使用颜色标记重点内容',
      ],
    }
  }

  // 难度进阶分析
  const analyzeDifficultyProgression = (questions: ErrorQuestion[]) => {
    const recentQuestions = questions.slice(-20) // 最近20题
    const accuracy =
      recentQuestions.length > 0
        ? recentQuestions.filter(q => q.masteryLevel > 80).length / recentQuestions.length
        : 0

    const currentLevel = 1
    let suggestedNext = 1
    let readinessScore = accuracy * 100

    if (accuracy >= 0.8) {
      suggestedNext = Math.min(currentLevel + 1, 5)
      readinessScore = Math.min(readinessScore + 20, 100)
    } else if (accuracy < 0.6) {
      suggestedNext = Math.max(currentLevel - 1, 1)
      readinessScore = Math.max(readinessScore - 20, 0)
    } else {
      suggestedNext = currentLevel
    }

    return {
      currentLevel,
      suggestedNext,
      readinessScore,
    }
  }

  // 通知功能将在后续版本中实现
  const [selectedTopic, _setSelectedTopic] = useState<string>('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [showMastered, setShowMastered] = useState(false)
  const [practiceModalOpened, setPracticeModalOpened] = useState(false)
  const [selectedQuestions, setSelectedQuestions] = useState<number[]>([])

  // 复习提醒状态
  const [reviewReminders, setReviewReminders] = useState<{
    urgent: ErrorQuestion[]
    today: ErrorQuestion[]
    upcoming: ErrorQuestion[]
  }>({ urgent: [], today: [], upcoming: [] })

  const queryClient = useQueryClient()

  // 获取错题统计
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['error-stats'],
    queryFn: () => errorReinforcementApi.getErrorStats(),
  })

  // 获取错题列表
  const { data: errors, isLoading: errorsLoading } = useQuery({
    queryKey: ['error-questions', selectedType, selectedTopic, selectedDifficulty, showMastered],
    queryFn: () =>
      errorReinforcementApi.getErrorQuestions({
        type: selectedType === 'all' ? undefined : (selectedType as TrainingType),
        topic: selectedTopic === 'all' ? undefined : selectedTopic,
        difficulty:
          selectedDifficulty === 'all' ? undefined : (selectedDifficulty as DifficultyLevel),
        includeMastered: showMastered,
      }),
  })

  // 模拟复习提醒数据
  useEffect(() => {
    if (errors?.questions) {
      const now = new Date()
      const urgent = errors.questions.filter((q: ErrorQuestion) => {
        const daysSinceLastReview = Math.floor(
          (now.getTime() - new Date(q.lastAttemptAt).getTime()) / (24 * 60 * 60 * 1000)
        )
        return daysSinceLastReview >= 7 && q.masteryLevel < 0.7
      })

      const today = errors.questions.filter((q: ErrorQuestion) => {
        const daysSinceLastReview = Math.floor(
          (now.getTime() - new Date(q.lastAttemptAt).getTime()) / (24 * 60 * 60 * 1000)
        )
        return daysSinceLastReview >= 3 && daysSinceLastReview < 7 && q.masteryLevel < 0.8
      })

      const upcoming = errors.questions.filter((q: ErrorQuestion) => {
        const daysSinceLastReview = Math.floor(
          (now.getTime() - new Date(q.lastAttemptAt).getTime()) / (24 * 60 * 60 * 1000)
        )
        return daysSinceLastReview >= 1 && daysSinceLastReview < 3 && q.masteryLevel < 0.9
      })

      setReviewReminders({ urgent, today, upcoming })
    }
  }, [errors, setReviewReminders])

  // 开始错题练习
  const startPracticeMutation = useMutation({
    mutationFn: (data: {
      questionIds: number[]
      mode: 'reinforcement' | 'review' | 'test'
      timeLimit?: number
    }) => errorReinforcementApi.startErrorPractice(data),
    onSuccess: _data => {
      notifications.show({
        title: '错题练习开始',
        message: '已为您准备好错题练习，开始强化训练吧！',
        color: 'green',
      })
      setPracticeModalOpened(false)
      // 可以导航到练习页面
    },
    onError: error => {
      notifications.show({
        title: '启动失败',
        message: error.message || '无法启动错题练习，请稍后重试',
        color: 'red',
      })
    },
  })

  // 标记为已掌握
  const markMasteredMutation = useMutation({
    mutationFn: (questionId: number) => errorReinforcementApi.markAsMastered(questionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['error-questions'] })
      queryClient.invalidateQueries({ queryKey: ['error-stats'] })
      notifications.show({
        title: '标记成功',
        message: '已标记为已掌握',
        color: 'green',
      })
    },
  })

  const handleStartPractice = () => {
    if (selectedQuestions.length === 0) {
      notifications.show({
        title: '请选择题目',
        message: '请至少选择一道错题进行练习',
        color: 'orange',
      })
      return
    }

    startPracticeMutation.mutate({
      questionIds: selectedQuestions,
      mode: 'reinforcement',
    })
  }

  const handleMarkMastered = (questionId: number) => {
    markMasteredMutation.mutate(questionId)
  }

  const getTypeLabel = (type: TrainingType) => {
    const labels: Record<TrainingType, string> = {
      listening: '听力',
      reading: '阅读',
      writing: '写作',
      translation: '翻译',
      vocabulary: '词汇',
      grammar: '语法',
      speaking: '口语',
    }
    return labels[type] || type
  }

  const getMasteryColor = (level: number) => {
    if (level >= 80) return 'green'
    if (level >= 60) return 'blue'
    if (level >= 40) return 'yellow'
    return 'red'
  }

  const getMasteryLabel = (level: number) => {
    if (level >= 80) return '已掌握'
    if (level >= 60) return '良好'
    if (level >= 40) return '一般'
    return '需加强'
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
        <Title order={2}>错题强化训练</Title>
        <Group>
          <Button
            leftSection={<IconPlayerPlay size={16} />}
            onClick={() => setPracticeModalOpened(true)}
            disabled={!errors?.questions?.length}
          >
            开始练习
          </Button>
          <Tooltip label="刷新数据">
            <ActionIcon variant="light" size="lg" onClick={() => queryClient.invalidateQueries()}>
              <IconRefresh size={20} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={value => value && setActiveTab(value)}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartBar size={16} />}>
            错题概览
          </Tabs.Tab>
          <Tabs.Tab value="questions" leftSection={<IconTarget size={16} />}>
            错题列表
          </Tabs.Tab>
          <Tabs.Tab value="analysis" leftSection={<IconTrendingUp size={16} />}>
            错误分析
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          {/* 复习提醒卡片 */}
          {(reviewReminders.urgent.length > 0 || reviewReminders.today.length > 0) && (
            <Alert icon={<IconClock size={16} />} title="复习提醒" color="orange" mb="lg">
              <Stack gap="xs">
                {reviewReminders.urgent.length > 0 && (
                  <Group>
                    <IconAlertCircle size={16} color="red" />
                    <Text size="sm">
                      <Text span fw={600} c="red">
                        {reviewReminders.urgent.length}
                      </Text>{' '}
                      道错题需要紧急复习（超过7天未复习）
                    </Text>
                  </Group>
                )}
                {reviewReminders.today.length > 0 && (
                  <Group>
                    <IconClock size={16} color="orange" />
                    <Text size="sm">
                      <Text span fw={600} c="orange">
                        {reviewReminders.today.length}
                      </Text>{' '}
                      道错题建议今日复习
                    </Text>
                  </Group>
                )}
                <Button
                  size="xs"
                  variant="light"
                  color="orange"
                  leftSection={<IconPlayerPlay size={14} />}
                  onClick={() => {
                    const urgentIds = reviewReminders.urgent.map(q => q.id)
                    const todayIds = reviewReminders.today.map(q => q.id)
                    setSelectedQuestions([...urgentIds, ...todayIds])
                    setPracticeModalOpened(true)
                  }}
                >
                  立即复习
                </Button>
              </Stack>
            </Alert>
          )}

          <Grid>
            {/* 错题统计卡片 */}
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  错题统计
                </Text>
                <Grid>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        总错题数
                      </Text>
                      <Text size="xl" fw={700}>
                        {stats?.totalErrors || 0}
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        已掌握
                      </Text>
                      <Text size="xl" fw={700} c="green">
                        {stats?.masteredErrors || 0}
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        改进中
                      </Text>
                      <Text size="xl" fw={700} c="blue">
                        {stats?.improvingErrors || 0}
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        顽固错题
                      </Text>
                      <Text size="xl" fw={700} c="red">
                        {stats?.persistentErrors || 0}
                      </Text>
                    </Stack>
                  </Grid.Col>
                </Grid>

                <Stack gap="xs" mt="md">
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      掌握进度
                    </Text>
                    <Text size="sm" c="dimmed">
                      {stats?.masteryProgress?.toFixed(1) || 0}%
                    </Text>
                  </Group>
                  <Progress
                    value={stats?.masteryProgress || 0}
                    size="lg"
                    radius="xl"
                    color="green"
                  />
                </Stack>
              </Card>
            </Grid.Col>

            {/* 快速练习卡片 */}
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                <Stack justify="space-between" h="100%">
                  <div>
                    <Text size="lg" fw={600} mb="md">
                      智能推荐
                    </Text>
                    <Stack gap="sm">
                      <Paper p="sm" withBorder radius="md">
                        <Group gap="xs">
                          <ThemeIcon color="red" variant="light" size="sm">
                            <IconAlertCircle size={12} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" fw={500}>
                              顽固错题
                            </Text>
                            <Text size="xs" c="dimmed">
                              {stats?.persistentErrors || 0} 道题需要重点练习
                            </Text>
                          </div>
                        </Group>
                      </Paper>
                      <Paper p="sm" withBorder radius="md">
                        <Group gap="xs">
                          <ThemeIcon color="blue" variant="light" size="sm">
                            <IconBrain size={12} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" fw={500}>
                              薄弱知识点
                            </Text>
                            <Text size="xs" c="dimmed">
                              语法和词汇需要加强
                            </Text>
                          </div>
                        </Group>
                      </Paper>
                    </Stack>
                  </div>
                  <Button
                    fullWidth
                    leftSection={<IconTarget size={16} />}
                    onClick={() => setPracticeModalOpened(true)}
                  >
                    智能练习
                  </Button>
                </Stack>
              </Card>
            </Grid.Col>

            {/* 错误类型分布 */}
            <Grid.Col span={12}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  错误类型分布
                </Text>
                <Grid>
                  {Object.entries(stats?.errorsByType || {}).map(([type, count]) => (
                    <Grid.Col key={type} span={{ base: 12, sm: 6, md: 3 }}>
                      <Paper p="md" withBorder radius="md" ta="center">
                        <Text size="xl" fw={700} c="red">
                          {String(count)}
                        </Text>
                        <Text size="sm" c="dimmed">
                          {getTypeLabel(type as TrainingType)}
                        </Text>
                      </Paper>
                    </Grid.Col>
                  ))}
                </Grid>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="questions" pt="md">
          {/* 筛选器 */}
          <Card shadow="sm" padding="md" radius="md" withBorder mb="md">
            <Group>
              <Select
                placeholder="训练类型"
                value={selectedType}
                onChange={value => setSelectedType(value || 'all')}
                data={[
                  { value: 'all', label: '全部类型' },
                  { value: 'listening', label: '听力' },
                  { value: 'reading', label: '阅读' },
                  { value: 'vocabulary', label: '词汇' },
                  { value: 'grammar', label: '语法' },
                ]}
                w={150}
              />
              <Select
                placeholder="难度级别"
                value={selectedDifficulty}
                onChange={value => setSelectedDifficulty(value || 'all')}
                data={[
                  { value: 'all', label: '全部难度' },
                  { value: 'beginner', label: '初级' },
                  { value: 'intermediate', label: '中级' },
                  { value: 'advanced', label: '高级' },
                ]}
                w={150}
              />
              <Checkbox
                label="显示已掌握"
                checked={showMastered}
                onChange={event => setShowMastered(event.currentTarget.checked)}
              />
            </Group>
          </Card>

          {errorsLoading ? (
            <Center h={200}>
              <Loader />
            </Center>
          ) : (
            <Stack gap="md">
              {errors?.questions?.map((error: ErrorQuestion) => (
                <Card key={error.id} shadow="sm" padding="md" radius="md" withBorder>
                  <Group justify="space-between" mb="md">
                    <Group gap="xs">
                      <Checkbox
                        checked={selectedQuestions.includes(error.id)}
                        onChange={event => {
                          if (event.currentTarget.checked) {
                            setSelectedQuestions([...selectedQuestions, error.id])
                          } else {
                            setSelectedQuestions(selectedQuestions.filter(id => id !== error.id))
                          }
                        }}
                      />
                      <Badge color={getMasteryColor(error.masteryLevel)}>
                        {getMasteryLabel(error.masteryLevel)}
                      </Badge>
                      <Badge variant="light">{getTypeLabel(error.type)}</Badge>
                      <Badge variant="light">{error.topic}</Badge>
                      <Badge color="red" variant="light">
                        错误 {error.errorCount} 次
                      </Badge>
                    </Group>
                    <Group gap="xs">
                      {error.masteryLevel < 80 && (
                        <Button
                          size="xs"
                          variant="light"
                          onClick={() => handleMarkMastered(error.id)}
                          loading={markMasteredMutation.isPending}
                        >
                          标记已掌握
                        </Button>
                      )}
                    </Group>
                  </Group>

                  <Accordion variant="contained">
                    <Accordion.Item value="details">
                      <Accordion.Control>
                        <Text lineClamp={2}>{error.questionText}</Text>
                      </Accordion.Control>
                      <Accordion.Panel>
                        <Stack gap="md">
                          <div>
                            <Text fw={500} mb="xs">
                              题目
                            </Text>
                            <Text>{error.questionText}</Text>
                          </div>

                          <Grid>
                            <Grid.Col span={6}>
                              <Text fw={500} mb="xs">
                                您的答案
                              </Text>
                              <Highlight highlight={[error.userAnswer]} color="red">
                                {error.userAnswer}
                              </Highlight>
                            </Grid.Col>
                            <Grid.Col span={6}>
                              <Text fw={500} mb="xs">
                                正确答案
                              </Text>
                              <Highlight highlight={[error.correctAnswer]} color="green">
                                {error.correctAnswer}
                              </Highlight>
                            </Grid.Col>
                          </Grid>

                          <div>
                            <Text fw={500} mb="xs">
                              解析
                            </Text>
                            <Text>{error.explanation}</Text>
                          </div>

                          {error.relatedConcepts.length > 0 && (
                            <div>
                              <Text fw={500} mb="xs">
                                相关概念
                              </Text>
                              <Group gap="xs">
                                {error.relatedConcepts.map((concept: string, idx: number) => (
                                  <Badge key={idx} size="sm" variant="light">
                                    {concept}
                                  </Badge>
                                ))}
                              </Group>
                            </div>
                          )}

                          <div>
                            <Text size="sm" fw={500} mb="xs">
                              掌握程度
                            </Text>
                            <Progress
                              value={error.masteryLevel}
                              color={getMasteryColor(error.masteryLevel)}
                              size="lg"
                            />
                          </div>
                        </Stack>
                      </Accordion.Panel>
                    </Accordion.Item>
                  </Accordion>
                </Card>
              )) || (
                <Alert icon={<IconCheck size={16} />} title="太棒了！" color="green">
                  您当前没有错题需要强化练习。继续保持良好的学习状态！
                </Alert>
              )}
            </Stack>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="analysis" pt="md">
          {/* 智能诊断分析 */}
          <Card shadow="sm" padding="lg" radius="md" withBorder mb="lg">
            <Group justify="space-between" mb="md">
              <Group>
                <IconBrain size={24} color="purple" />
                <Text size="lg" fw={600}>
                  AI智能诊断分析
                </Text>
              </Group>
              <Button
                leftSection={<IconSparkles size={16} />}
                onClick={() => {
                  if (errors?.questions?.length) {
                    const analysis = performDiagnosisAnalysis(errors.questions)
                    setDiagnosisAnalysis(analysis)
                    notifications.show({
                      title: '诊断完成',
                      message: '已生成个性化学习分析报告',
                      color: 'green',
                    })
                  } else {
                    notifications.show({
                      title: '暂无数据',
                      message: '请先完成一些练习后再进行诊断',
                      color: 'orange',
                    })
                  }
                }}
                loading={false}
              >
                开始诊断
              </Button>
            </Group>

            {diagnosisAnalysis && (
              <Grid>
                {/* 错误模式分析 */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      错误模式分析
                    </Text>
                    <Stack gap="sm">
                      {diagnosisAnalysis.errorPatterns.map((pattern, index) => (
                        <Group key={index} justify="space-between">
                          <div>
                            <Text size="sm" fw={500}>
                              {pattern.type}
                            </Text>
                            <Text size="xs" c="dimmed">
                              出现{pattern.frequency}次 ·{' '}
                              {pattern.severity === 'high'
                                ? '高频'
                                : pattern.severity === 'medium'
                                  ? '中频'
                                  : '低频'}
                            </Text>
                          </div>
                          <Badge
                            color={
                              pattern.severity === 'high'
                                ? 'red'
                                : pattern.severity === 'medium'
                                  ? 'orange'
                                  : 'blue'
                            }
                            variant="light"
                          >
                            {pattern.severity === 'high'
                              ? '需重点关注'
                              : pattern.severity === 'medium'
                                ? '需要注意'
                                : '继续保持'}
                          </Badge>
                        </Group>
                      ))}
                    </Stack>
                  </Paper>
                </Grid.Col>

                {/* 知识盲点分析 */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      知识盲点分析
                    </Text>
                    <Stack gap="sm">
                      {diagnosisAnalysis.knowledgeGaps.slice(0, 5).map((gap, index) => (
                        <Group key={index} justify="space-between">
                          <div>
                            <Text size="sm" fw={500}>
                              {gap.topic}
                            </Text>
                            <Text size="xs" c="dimmed">
                              掌握度: {gap.mastery.toFixed(1)}%
                            </Text>
                          </div>
                          <Progress
                            value={gap.mastery}
                            color={
                              gap.mastery >= 80 ? 'green' : gap.mastery >= 60 ? 'yellow' : 'red'
                            }
                            size="sm"
                            w={80}
                          />
                        </Group>
                      ))}
                    </Stack>
                  </Paper>
                </Grid.Col>

                {/* 学习风格推荐 */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      学习风格推荐
                    </Text>
                    <Stack gap="sm">
                      <Group>
                        <Text size="sm">推荐学习方式:</Text>
                        <Badge color="blue" variant="light">
                          {diagnosisAnalysis.learningStyle.preferredType === 'visual'
                            ? '视觉型'
                            : diagnosisAnalysis.learningStyle.preferredType === 'auditory'
                              ? '听觉型'
                              : diagnosisAnalysis.learningStyle.preferredType === 'kinesthetic'
                                ? '动觉型'
                                : '阅读型'}
                        </Badge>
                      </Group>
                      <Text size="xs" c="dimmed">
                        置信度: {(diagnosisAnalysis.learningStyle.confidence * 100).toFixed(1)}%
                      </Text>
                      <Stack gap="xs">
                        {diagnosisAnalysis.learningStyle.recommendations.map((rec, index) => (
                          <Text key={index} size="xs" c="dimmed">
                            • {rec}
                          </Text>
                        ))}
                      </Stack>
                    </Stack>
                  </Paper>
                </Grid.Col>

                {/* 难度进阶建议 */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      难度进阶建议
                    </Text>
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Text size="sm">当前水平:</Text>
                        <Badge color="blue">
                          Level {diagnosisAnalysis.difficultyProgression.currentLevel}
                        </Badge>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm">建议难度:</Text>
                        <Badge color="green">
                          Level {diagnosisAnalysis.difficultyProgression.suggestedNext}
                        </Badge>
                      </Group>
                      <div>
                        <Text size="sm" mb="xs">
                          准备度评估:
                        </Text>
                        <Progress
                          value={diagnosisAnalysis.difficultyProgression.readinessScore}
                          color={
                            diagnosisAnalysis.difficultyProgression.readinessScore >= 80
                              ? 'green'
                              : diagnosisAnalysis.difficultyProgression.readinessScore >= 60
                                ? 'yellow'
                                : 'red'
                          }
                          size="lg"
                        />
                        <Text size="xs" c="dimmed" mt="xs">
                          {diagnosisAnalysis.difficultyProgression.readinessScore.toFixed(1)}%
                          准备就绪
                        </Text>
                      </div>
                    </Stack>
                  </Paper>
                </Grid.Col>
              </Grid>
            )}
          </Card>

          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  错误趋势分析
                </Text>
                <Timeline active={-1} bulletSize={24} lineWidth={2}>
                  <Timeline.Item
                    bullet={
                      <ThemeIcon color="red" variant="light" size={24}>
                        <IconAlertCircle size={12} />
                      </ThemeIcon>
                    }
                    title="语法错误"
                  >
                    <Text size="sm" c="dimmed">
                      最常见的错误类型，建议加强语法基础练习
                    </Text>
                  </Timeline.Item>
                  <Timeline.Item
                    bullet={
                      <ThemeIcon color="orange" variant="light" size={24}>
                        <IconBook size={12} />
                      </ThemeIcon>
                    }
                    title="词汇理解"
                  >
                    <Text size="sm" c="dimmed">
                      词汇量需要提升，建议增加词汇记忆练习
                    </Text>
                  </Timeline.Item>
                  <Timeline.Item
                    bullet={
                      <ThemeIcon color="blue" variant="light" size={24}>
                        <IconBrain size={12} />
                      </ThemeIcon>
                    }
                    title="阅读理解"
                  >
                    <Text size="sm" c="dimmed">
                      理解能力有所改善，继续保持练习频率
                    </Text>
                  </Timeline.Item>
                </Timeline>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  学习建议
                </Text>
                <Stack gap="md">
                  <Paper p="md" withBorder radius="md">
                    <Group gap="xs" mb="xs">
                      <IconBulb size={16} color="blue" />
                      <Text fw={500}>重点练习</Text>
                    </Group>
                    <Text size="sm">建议每天花15-20分钟专门练习错题，重点关注语法和词汇部分。</Text>
                  </Paper>
                  <Paper p="md" withBorder radius="md">
                    <Group gap="xs" mb="xs">
                      <IconTarget size={16} color="green" />
                      <Text fw={500}>学习策略</Text>
                    </Group>
                    <Text size="sm">采用间隔重复的方法，对于掌握程度较低的题目增加练习频率。</Text>
                  </Paper>
                  <Paper p="md" withBorder radius="md">
                    <Group gap="xs" mb="xs">
                      <IconStar size={16} color="orange" />
                      <Text fw={500}>进步跟踪</Text>
                    </Group>
                    <Text size="sm">定期回顾已掌握的错题，确保知识点得到巩固。</Text>
                  </Paper>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>
      </Tabs>

      {/* 练习设置模态框 */}
      <Modal
        opened={practiceModalOpened}
        onClose={() => setPracticeModalOpened(false)}
        title="开始错题练习"
        size="md"
      >
        <Stack gap="md">
          <Alert icon={<IconBulb size={16} />} title="智能推荐" color="blue">
            系统已为您智能选择了 {selectedQuestions.length} 道最需要练习的错题。
          </Alert>

          <Group justify="space-between">
            <Text>选中题目数量:</Text>
            <Badge size="lg">{selectedQuestions.length}</Badge>
          </Group>

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setPracticeModalOpened(false)}>
              取消
            </Button>
            <Button
              onClick={handleStartPractice}
              loading={startPracticeMutation.isPending}
              disabled={selectedQuestions.length === 0}
            >
              开始练习
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
