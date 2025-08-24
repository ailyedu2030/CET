import React, { useState, useRef } from 'react'
import {
  Container,
  Grid,
  Card,
  Text,
  Button,
  Badge,
  Group,
  Stack,
  Progress,
  Title,
  Tabs,
  ActionIcon,
  Tooltip,
  Modal,
  Select,
  NumberInput,
  Switch,
  Alert,
  Loader,
  Center,
  Textarea,
} from '@mantine/core'
import {
  IconBrain,
  IconClock,
  IconTrophy,
  IconPlayerPlay,
  IconPlayerPause,
  IconSettings,
  IconChartBar,
  IconBook,
  IconHeadphones,
  IconLanguage,
  IconFileText,
  IconPencil,
  IconCheck,
  IconChevronRight,
} from '@tabler/icons-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { useDisclosure } from '@mantine/hooks'
import { trainingApi, TrainingStats } from '@/api/training'
import { TrainingType, DifficultyLevel } from '../../../types/training'

// 扩展训练统计类型
interface ExtendedTrainingStats extends TrainingStats {
  moduleStats?: Record<
    string,
    {
      completed: number
      progress: number
      streak: number
      averageScore: number
    }
  >
}

// 训练模块接口定义
interface TrainingModule {
  id: TrainingType
  name: string
  icon: React.ComponentType<{ size?: number; color?: string }>
  color: string
  description: string
  features: string[]
  dailyTarget: number
  estimatedTime: string
  difficulty: DifficultyLevel[]
  available: boolean
}

// 训练题目接口定义
interface Question {
  id: string
  type: TrainingType
  subType: string
  content: string
  options?: string[]
  correctAnswer: string | string[]
  explanation: string
  difficulty: DifficultyLevel
  timeLimit: number
  audioUrl?: string
  imageUrl?: string
  context?: string
  hints?: string[]
}

// 训练会话接口
interface TrainingSessionData {
  id: string
  type: TrainingType
  questions: Question[]
  startTime: Date
  endTime?: Date
  score?: number
  progress: number
  currentQuestionIndex: number
  answers: Record<string, string | string[]>
  timeSpent: number
  correctCount: number
  totalQuestions: number
}

// 训练题型接口（将在后续版本中使用）

export const TrainingCenterPage: React.FC = () => {
  // 基础状态管理
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [settingsOpened, { open: openSettings, close: closeSettings }] = useDisclosure(false)
  const [selectedType, setSelectedType] = useState<TrainingType>(TrainingType.VOCABULARY)
  const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel>(
    DifficultyLevel.INTERMEDIATE
  )
  const [questionCount, setQuestionCount] = useState(20)
  const [timeLimit, setTimeLimit] = useState(30)
  const [adaptiveMode, setAdaptiveMode] = useState(true)

  // 训练会话状态
  const [trainingSession, setTrainingSession] = useState<TrainingSessionData | null>(null)
  const [isTraining, setIsTraining] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [userAnswer, setUserAnswer] = useState<string | string[]>('')
  const [showExplanation, setShowExplanation] = useState(false)
  const [sessionTimer, setSessionTimer] = useState(0)
  const [questionTimer, setQuestionTimer] = useState(0)

  // Refs
  const sessionTimerRef = useRef<number | null>(null)
  const questionTimerRef = useRef<number | null>(null)

  const queryClient = useQueryClient()

  // 训练模块配置
  const trainingModules: TrainingModule[] = [
    {
      id: TrainingType.VOCABULARY,
      name: '词汇训练',
      icon: IconBook,
      color: 'blue',
      description: '词义选择、词形变换、语境填空、同义词辨析、词汇搭配',
      features: ['5种题型', '自适应难度', '记忆强化', '每日15-30题'],
      dailyTarget: 20,
      estimatedTime: '15-20分钟',
      difficulty: [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
        DifficultyLevel.EXPERT,
      ],
      available: true,
    },
    {
      id: TrainingType.LISTENING,
      name: '听力训练',
      icon: IconHeadphones,
      color: 'green',
      description: '短对话、长对话、短文理解、讲座训练',
      features: ['4种题型', '语速调节', '跟读练习', '字幕辅助'],
      dailyTarget: 15,
      estimatedTime: '20-25分钟',
      difficulty: [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
        DifficultyLevel.EXPERT,
      ],
      available: true,
    },
    {
      id: TrainingType.TRANSLATION,
      name: '翻译训练',
      icon: IconLanguage,
      color: 'orange',
      description: '中英互译、翻译技巧、表达优化',
      features: ['中英互译', 'AI评分', '参考答案', '技巧指导'],
      dailyTarget: 2,
      estimatedTime: '10-15分钟',
      difficulty: [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT],
      available: true,
    },
    {
      id: TrainingType.READING,
      name: '阅读理解',
      icon: IconFileText,
      color: 'violet',
      description: '多主题阅读、技能训练、长文本处理',
      features: ['多主题', '技能分类', '长文本', '深度理解'],
      dailyTarget: 5,
      estimatedTime: '25-30分钟',
      difficulty: [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
        DifficultyLevel.EXPERT,
      ],
      available: true,
    },
    {
      id: TrainingType.WRITING,
      name: '写作训练',
      icon: IconPencil,
      color: 'red',
      description: '应用文、议论文、图表作文、实时辅助',
      features: ['多题型', '实时辅助', '四级评分', '模板框架'],
      dailyTarget: 1,
      estimatedTime: '30-45分钟',
      difficulty: [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT],
      available: true,
    },
  ]

  // 获取训练统计
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['training-stats'],
    queryFn: trainingApi.getTrainingStats,
  })

  // 训练API调用已在新的训练系统中实现

  // 生成训练题目
  const generateQuestions = (
    type: TrainingType,
    count: number,
    difficulty: DifficultyLevel
  ): Question[] => {
    const questions: Question[] = []

    for (let i = 0; i < count; i++) {
      const baseQuestion = {
        id: `${type}_${i + 1}`,
        type,
        difficulty,
        timeLimit: 60, // 默认60秒
        explanation: '',
      }

      switch (type) {
        case 'vocabulary': {
          const vocabSubTypes = ['meaning', 'form', 'context', 'synonym', 'collocation'] as const
          questions.push({
            ...baseQuestion,
            subType: vocabSubTypes[i % 5] || 'meaning',
            content: `词汇题目 ${i + 1}：请选择单词 "example" 的正确含义`,
            options: ['例子', '练习', '考试', '问题'],
            correctAnswer: '例子',
            explanation: '"example" 的意思是例子、实例。',
          })
          break
        }
        case 'listening': {
          const listeningSubTypes = [
            'short_dialogue',
            'long_dialogue',
            'passage',
            'lecture',
          ] as const
          questions.push({
            ...baseQuestion,
            subType: listeningSubTypes[i % 4] || 'short_dialogue',
            content: `听力题目 ${i + 1}：请听音频并回答问题`,
            audioUrl: `/audio/listening_${i + 1}.mp3`,
            options: ['选项A', '选项B', '选项C', '选项D'],
            correctAnswer: '选项A',
            explanation: '根据对话内容，正确答案是选项A。',
          })
          break
        }
        case 'translation':
          questions.push({
            ...baseQuestion,
            subType: i % 2 === 0 ? 'en_to_cn' : 'cn_to_en',
            content: i % 2 === 0 ? 'Please translate: "Hello, world!"' : '请翻译：你好，世界！',
            correctAnswer: i % 2 === 0 ? '你好，世界！' : 'Hello, world!',
            explanation: '这是一个基础的翻译练习。',
          })
          break
        case 'reading': {
          const readingSubTypes = [
            'main_idea',
            'detail',
            'inference',
            'vocabulary_in_context',
          ] as const
          questions.push({
            ...baseQuestion,
            subType: readingSubTypes[i % 4] || 'main_idea',
            content: `阅读理解题目 ${i + 1}`,
            context: '这是一篇关于环境保护的文章...',
            options: ['选项A', '选项B', '选项C', '选项D'],
            correctAnswer: '选项A',
            explanation: '根据文章内容，正确答案是选项A。',
          })
          break
        }
        case 'writing': {
          const writingSubTypes = ['application', 'argumentative', 'chart_description'] as const
          questions.push({
            ...baseQuestion,
            subType: writingSubTypes[i % 3] || 'application',
            content: `写作题目 ${i + 1}：请根据以下提示写一篇短文`,
            correctAnswer: '', // 写作题没有标准答案
            explanation: '写作评分将基于内容、组织、语言和语法四个维度。',
            timeLimit: 30 * 60, // 写作题30分钟
          })
          break
        }
        default:
          break
      }
    }

    return questions
  }

  // 开始训练会话
  const startTrainingSession = (type: TrainingType) => {
    const questions = generateQuestions(type, questionCount, selectedDifficulty)
    const session: TrainingSessionData = {
      id: `session_${Date.now()}`,
      type,
      questions,
      startTime: new Date(),
      progress: 0,
      currentQuestionIndex: 0,
      answers: {},
      timeSpent: 0,
      correctCount: 0,
      totalQuestions: questions.length,
    }

    setTrainingSession(session)
    setCurrentQuestion(questions[0] || null)
    setIsTraining(true)
    setSessionTimer(0)
    setQuestionTimer(0)
    setUserAnswer('')
    setShowExplanation(false)

    // 开始计时
    sessionTimerRef.current = window.setInterval(() => {
      setSessionTimer(prev => prev + 1)
    }, 1000)

    questionTimerRef.current = window.setInterval(() => {
      setQuestionTimer(prev => prev + 1)
    }, 1000)

    notifications.show({
      title: '训练开始',
      message: `开始${getTrainingTypeName(type)}训练，共${questions.length}题`,
      color: 'blue',
    })
  }

  const getTrainingTypeName = (type: TrainingType): string => {
    const names: Partial<Record<TrainingType, string>> = {
      vocabulary: '词汇',
      listening: '听力',
      translation: '翻译',
      reading: '阅读',
      writing: '写作',
    }
    return names[type] || type
  }

  // 提交答案
  const submitAnswer = () => {
    if (!trainingSession || !currentQuestion) return

    const isCorrect = checkAnswer(currentQuestion, userAnswer)
    const updatedSession = {
      ...trainingSession,
      answers: {
        ...trainingSession.answers,
        [currentQuestion.id]: userAnswer,
      },
      correctCount: isCorrect ? trainingSession.correctCount + 1 : trainingSession.correctCount,
    }

    setTrainingSession(updatedSession)
    setShowExplanation(true)

    // 显示答题结果
    notifications.show({
      title: isCorrect ? '回答正确！' : '回答错误',
      message: currentQuestion.explanation,
      color: isCorrect ? 'green' : 'red',
    })
  }

  // 检查答案是否正确
  const checkAnswer = (question: Question, answer: string | string[]): boolean => {
    if (Array.isArray(question.correctAnswer)) {
      return (
        Array.isArray(answer) &&
        answer.length === question.correctAnswer.length &&
        answer.every(a => question.correctAnswer.includes(a))
      )
    }
    return question.correctAnswer === answer
  }

  // 下一题
  const nextQuestion = () => {
    if (!trainingSession) return

    const nextIndex = trainingSession.currentQuestionIndex + 1

    if (nextIndex >= trainingSession.questions.length) {
      // 训练完成
      finishTraining()
      return
    }

    const updatedSession = {
      ...trainingSession,
      currentQuestionIndex: nextIndex,
      progress: Math.round((nextIndex / trainingSession.questions.length) * 100),
    }

    setTrainingSession(updatedSession)
    setCurrentQuestion(trainingSession.questions[nextIndex] || null)
    setUserAnswer('')
    setShowExplanation(false)
    setQuestionTimer(0)

    // 重置题目计时器
    if (questionTimerRef.current) {
      clearInterval(questionTimerRef.current)
    }
    questionTimerRef.current = window.setInterval(() => {
      setQuestionTimer(prev => prev + 1)
    }, 1000)
  }

  // 完成训练
  const finishTraining = () => {
    if (!trainingSession) return

    const finalSession = {
      ...trainingSession,
      endTime: new Date(),
      timeSpent: sessionTimer,
      score: Math.round((trainingSession.correctCount / trainingSession.totalQuestions) * 100),
    }

    // 清理计时器
    if (sessionTimerRef.current) {
      clearInterval(sessionTimerRef.current)
    }
    if (questionTimerRef.current) {
      clearInterval(questionTimerRef.current)
    }

    setIsTraining(false)
    setTrainingSession(null)
    setCurrentQuestion(null)

    // 显示训练结果
    notifications.show({
      title: '训练完成！',
      message: `得分：${finalSession.score}分，用时：${Math.floor(finalSession.timeSpent / 60)}分${finalSession.timeSpent % 60}秒`,
      color: finalSession.score >= 80 ? 'green' : finalSession.score >= 60 ? 'yellow' : 'red',
    })

    // 刷新统计数据
    queryClient.invalidateQueries({ queryKey: ['training-stats'] })
  }

  // 暂停/恢复训练
  const toggleTrainingPause = () => {
    if (sessionTimerRef.current) {
      clearInterval(sessionTimerRef.current)
      clearInterval(questionTimerRef.current!)
      sessionTimerRef.current = null
      questionTimerRef.current = null
    } else {
      sessionTimerRef.current = window.setInterval(() => {
        setSessionTimer(prev => prev + 1)
      }, 1000)
      questionTimerRef.current = window.setInterval(() => {
        setQuestionTimer(prev => prev + 1)
      }, 1000)
    }
  }

  const handleStartTraining = (type?: TrainingType) => {
    const trainingType = type || selectedType
    startTrainingSession(trainingType)
  }

  // 训练控制功能已在新的训练系统中实现

  // 辅助函数已在新的训练系统中实现

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
        <Title order={2}>学生训练中心</Title>
        <Group>
          {isTraining && (
            <Group gap="xs">
              <Badge color="blue" variant="light">
                训练中
              </Badge>
              <Text size="sm" c="dimmed">
                {Math.floor(sessionTimer / 60)}:{(sessionTimer % 60).toString().padStart(2, '0')}
              </Text>
              <ActionIcon
                variant="light"
                size="sm"
                onClick={toggleTrainingPause}
                color={sessionTimerRef.current ? 'orange' : 'green'}
              >
                {sessionTimerRef.current ? (
                  <IconPlayerPause size={16} />
                ) : (
                  <IconPlayerPlay size={16} />
                )}
              </ActionIcon>
            </Group>
          )}
          <Tooltip label="训练设置">
            <ActionIcon variant="light" size="lg" onClick={openSettings}>
              <IconSettings size={20} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="查看统计">
            <ActionIcon variant="light" size="lg">
              <IconChartBar size={20} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={value => value && setActiveTab(value)}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconBrain size={16} />}>
            训练概览
          </Tabs.Tab>
          <Tabs.Tab value="session" leftSection={<IconPlayerPlay size={16} />}>
            当前训练
          </Tabs.Tab>
          <Tabs.Tab value="history" leftSection={<IconClock size={16} />}>
            训练历史
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          <Grid>
            {/* 学习统计卡片 */}
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <Text size="lg" fw={600}>
                    学习统计
                  </Text>
                  <Badge color="blue" variant="light">
                    等级 {(stats as TrainingStats)?.level || 1}
                  </Badge>
                </Group>

                <Grid>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        总训练次数
                      </Text>
                      <Text size="xl" fw={700}>
                        {(stats as TrainingStats)?.totalSessions || 0}
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        完成率
                      </Text>
                      <Text size="xl" fw={700}>
                        {(stats as TrainingStats)?.totalSessions
                          ? Math.round(
                              ((stats as TrainingStats).completedSessions /
                                (stats as TrainingStats).totalSessions) *
                                100
                            )
                          : 0}
                        %
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        平均分数
                      </Text>
                      <Text size="xl" fw={700}>
                        {(stats as TrainingStats)?.averageScore?.toFixed(1) || '0.0'}
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        连续天数
                      </Text>
                      <Group gap="xs">
                        <IconTrophy size={20} color="orange" />
                        <Text size="xl" fw={700}>
                          {(stats as TrainingStats)?.streak || 0}
                        </Text>
                      </Group>
                    </Stack>
                  </Grid.Col>
                </Grid>

                {/* 经验值进度条 */}
                <Stack gap="xs" mt="md">
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      经验值
                    </Text>
                    <Text size="sm" c="dimmed">
                      {(stats as TrainingStats)?.exp || 0} /{' '}
                      {(stats as TrainingStats)?.nextLevelExp || 100}
                    </Text>
                  </Group>
                  <Progress
                    value={
                      (stats as TrainingStats)?.nextLevelExp
                        ? ((stats as TrainingStats).exp / (stats as TrainingStats).nextLevelExp) *
                          100
                        : 0
                    }
                    size="lg"
                    radius="xl"
                  />
                </Stack>
              </Card>
            </Grid.Col>

            {/* 快速开始卡片 */}
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                <Stack justify="space-between" h="100%">
                  <div>
                    <Text size="lg" fw={600} mb="md">
                      快速开始
                    </Text>
                    <Stack gap="sm">
                      <Select
                        label="训练类型"
                        value={selectedType}
                        onChange={value => setSelectedType(value as TrainingType)}
                        data={[
                          { value: 'listening', label: '听力训练' },
                          { value: 'reading', label: '阅读理解' },
                          { value: 'writing', label: '写作练习' },
                          { value: 'vocabulary', label: '词汇练习' },
                        ]}
                      />
                      <Select
                        label="难度级别"
                        value={selectedDifficulty}
                        onChange={value => setSelectedDifficulty(value as DifficultyLevel)}
                        data={[
                          { value: 'beginner', label: '初级' },
                          { value: 'intermediate', label: '中级' },
                          { value: 'advanced', label: '高级' },
                        ]}
                      />
                    </Stack>
                  </div>
                  <Button
                    fullWidth
                    size="lg"
                    leftSection={<IconPlayerPlay size={20} />}
                    onClick={() => handleStartTraining()}
                    loading={false}
                  >
                    开始训练
                  </Button>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>

          {/* 训练模块网格 */}
          <Title order={3} mt="xl" mb="md">
            训练模块
          </Title>
          <Grid>
            {trainingModules.map(module => {
              const IconComponent = module.icon
              const moduleStats = (stats as ExtendedTrainingStats)?.moduleStats?.[module.id] || {
                completed: 0,
                progress: 0,
                streak: 0,
                averageScore: 0,
              }

              return (
                <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={module.id}>
                  <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                    <Group justify="space-between" mb="md">
                      <Group>
                        <IconComponent size={24} color={module.color} />
                        <Text size="lg" fw={500}>
                          {module.name}
                        </Text>
                      </Group>
                      <Badge color={module.color} variant="light">
                        {moduleStats.completed}/{module.dailyTarget}
                      </Badge>
                    </Group>

                    <Text size="sm" c="dimmed" mb="md">
                      {module.description}
                    </Text>

                    <Stack gap="xs" mb="md">
                      {module.features.map((feature, index) => (
                        <Group key={index} gap="xs">
                          <IconCheck size={14} color={module.color} />
                          <Text size="xs" c="dimmed">
                            {feature}
                          </Text>
                        </Group>
                      ))}
                    </Stack>

                    <Group justify="space-between" mb="xs">
                      <Text size="sm">今日进度</Text>
                      <Text size="sm" fw={500}>
                        {moduleStats.progress}%
                      </Text>
                    </Group>
                    <Progress value={moduleStats.progress} color={module.color} size="sm" mb="xs" />

                    <Group justify="space-between" mb="md">
                      <Text size="xs" c="dimmed">
                        预计时间: {module.estimatedTime}
                      </Text>
                      <Text size="xs" c="dimmed">
                        平均分: {moduleStats.averageScore.toFixed(1)}
                      </Text>
                    </Group>

                    <Button
                      variant="light"
                      color={module.color}
                      fullWidth
                      leftSection={<IconPlayerPlay size={16} />}
                      onClick={() => handleStartTraining(module.id)}
                      disabled={!module.available}
                    >
                      {module.available ? '开始训练' : '即将开放'}
                    </Button>
                  </Card>
                </Grid.Col>
              )
            })}
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="session" pt="md">
          {isTraining && currentQuestion ? (
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              {/* 训练进度 */}
              <Group justify="space-between" mb="md">
                <Text size="lg" fw={600}>
                  {getTrainingTypeName(trainingSession?.type || TrainingType.VOCABULARY)}训练
                </Text>
                <Badge color="blue" variant="light">
                  {(trainingSession?.currentQuestionIndex || 0) + 1} /{' '}
                  {trainingSession?.totalQuestions || 1}
                </Badge>
              </Group>

              <Progress
                value={trainingSession?.progress || 0}
                color="blue"
                size="lg"
                radius="xl"
                mb="lg"
              />

              {/* 题目内容 */}
              <Stack gap="md">
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    题型：{currentQuestion.subType}
                  </Text>
                  <Text size="sm" c="dimmed">
                    用时：{Math.floor(questionTimer / 60)}:
                    {(questionTimer % 60).toString().padStart(2, '0')}
                  </Text>
                </Group>

                <Text size="md" fw={500}>
                  {currentQuestion.content}
                </Text>

                {/* 选择题选项 */}
                {currentQuestion.options && (
                  <Stack gap="xs">
                    {currentQuestion.options.map((option, index) => (
                      <Button
                        key={index}
                        variant={userAnswer === option ? 'filled' : 'light'}
                        color={userAnswer === option ? 'blue' : 'gray'}
                        justify="flex-start"
                        onClick={() => setUserAnswer(option)}
                        disabled={showExplanation}
                      >
                        {String.fromCharCode(65 + index)}. {option}
                      </Button>
                    ))}
                  </Stack>
                )}

                {/* 文本输入（翻译题、写作题） */}
                {(currentQuestion.type === 'translation' || currentQuestion.type === 'writing') && (
                  <Textarea
                    placeholder={
                      currentQuestion.type === 'translation'
                        ? '请输入翻译结果...'
                        : '请输入作文内容...'
                    }
                    value={typeof userAnswer === 'string' ? userAnswer : ''}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                      setUserAnswer(e.target.value)
                    }
                    rows={currentQuestion.type === 'writing' ? 10 : 4}
                    disabled={showExplanation}
                  />
                )}

                {/* 答案解析 */}
                {showExplanation && (
                  <Alert color="blue" title="答案解析">
                    <Text size="sm" mb="xs">
                      <strong>正确答案：</strong>
                      {currentQuestion.correctAnswer}
                    </Text>
                    <Text size="sm">{currentQuestion.explanation}</Text>
                  </Alert>
                )}

                {/* 操作按钮 */}
                <Group justify="flex-end" mt="md">
                  {!showExplanation ? (
                    <Button
                      onClick={submitAnswer}
                      disabled={!userAnswer}
                      leftSection={<IconCheck size={16} />}
                    >
                      提交答案
                    </Button>
                  ) : (
                    <Button onClick={nextQuestion} leftSection={<IconChevronRight size={16} />}>
                      {trainingSession &&
                      trainingSession.currentQuestionIndex >= trainingSession.totalQuestions - 1
                        ? '完成训练'
                        : '下一题'}
                    </Button>
                  )}
                </Group>
              </Stack>
            </Card>
          ) : (
            <Center h={300}>
              <Stack align="center" gap="md">
                <Text c="dimmed">当前没有进行中的训练</Text>
                <Button
                  leftSection={<IconPlayerPlay size={16} />}
                  onClick={() => setActiveTab('overview')}
                >
                  开始训练
                </Button>
              </Stack>
            </Center>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="history" pt="md">
          <Center h={300}>
            <Stack align="center" gap="md">
              <Text c="dimmed">训练历史功能开发中...</Text>
              <Text size="sm" c="dimmed">
                完成训练后，您的历史记录将在这里显示
              </Text>
            </Stack>
          </Center>
        </Tabs.Panel>
      </Tabs>

      {/* 训练设置模态框 */}
      <Modal opened={settingsOpened} onClose={closeSettings} title="训练设置" size="md">
        <Stack gap="md">
          <NumberInput
            label="题目数量"
            value={questionCount}
            onChange={value => setQuestionCount(Number(value))}
            min={5}
            max={50}
            step={5}
          />
          <NumberInput
            label="时间限制（分钟）"
            value={timeLimit}
            onChange={value => setTimeLimit(Number(value))}
            min={10}
            max={120}
            step={5}
          />
          <Switch
            label="自适应模式"
            description="根据答题情况自动调整难度"
            checked={adaptiveMode}
            onChange={event => setAdaptiveMode(event.currentTarget.checked)}
          />
          <Group justify="flex-end" mt="md">
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
