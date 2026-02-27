/**
 * 听力训练系统页面 - 需求22实现
 * 
 * 验收标准：
 * 1. 题型分类：短对话训练（8个对话×1题）、长对话训练（2段对话×3题）、短文理解（3篇短文×3题）、讲座训练（1篇讲座×5题）
 * 2. 训练特性：口语跟读练习、语速调节/重复播放、训练模式下可显示字幕辅助、单词/短语听写训练
 * 3. 智能辅助：针对性音标识别练习、场景化听力应试技巧、自动标注个人听力难点、听力题目错误原因分析
 */

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import type { FC } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Button,
  Group,
  Stack,
  Badge,
  Tabs,
  ActionIcon,
  Modal,
  Select,
  Switch,
  Tooltip,
  Loader,
  Center,
  RingProgress,
  ThemeIcon,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconHeadphones,
  IconPlayerPlay,
  IconSettings,
  IconBrain,
  IconTarget,
  IconTrendingUp,
  IconRefresh,
  IconCheck,
  IconBulb,
  IconEar,
  IconBook,
  IconChartLine,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { listeningApi, type ListeningSession } from '../../../api/listening'
import { DifficultyLevel } from '../../../types/training'
import type {
  ListeningSessionSettings,
  AudioPlaybackSpeed,
  ListeningExerciseType,
  ListeningTrainingState,
} from '../../../types/listening'
import { ListeningTrainingSession } from './ListeningTrainingSession'

// 常量定义
const EXERCISE_TYPE_CONFIG = {
  short_conversation: {
    name: '短对话训练',
    description: '8个对话，每个对话1题',
    icon: IconHeadphones,
    color: 'blue',
    count: 8,
    questionsPerItem: 1,
  },
  long_conversation: {
    name: '长对话训练',
    description: '2段对话，每段对话3题',
    icon: IconEar,
    color: 'green',
    count: 2,
    questionsPerItem: 3,
  },
  passage: {
    name: '短文理解',
    description: '3篇短文，每篇短文3题',
    icon: IconBook,
    color: 'orange',
    count: 3,
    questionsPerItem: 3,
  },
  lecture: {
    name: '讲座训练',
    description: '1篇讲座，每篇讲座5题',
    icon: IconBrain,
    color: 'violet',
    count: 1,
    questionsPerItem: 5,
  },
} as const

const AUDIO_SPEEDS: AudioPlaybackSpeed[] = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

const DEFAULT_SETTINGS: ListeningSessionSettings = {
  audio_speed: 1.0,
  subtitles_enabled: false,
  repeat_enabled: true,
  pronunciation_practice: false,
  dictation_mode: false,
  auto_pause: false,
  highlight_keywords: false,
}

export const ListeningTrainingPage: FC = () => {
  const queryClient = useQueryClient()

  // 状态管理
  const [selectedExerciseType, setSelectedExerciseType] = useState<ListeningExerciseType>('short_conversation')
  const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel>(DifficultyLevel.INTERMEDIATE)
  const [sessionSettings, setSessionSettings] = useState<ListeningSessionSettings>(DEFAULT_SETTINGS)
  const [currentSession, setCurrentSession] = useState<ListeningSession | null>(null)
  const [trainingState, setTrainingState] = useState<ListeningTrainingState>({
    current_question: 1,
    is_playing: false,
    is_paused: false,
    audio_loaded: false,
    subtitles_visible: false,
    answer_submitted: false,
    session_active: false,
  })
  const [trainingResult, setTrainingResult] = useState<any>(null)
  // 模态框状态
  const [settingsOpened, { open: openSettings, close: closeSettings }] = useDisclosure(false)
  const [tipsOpened, { open: openTips, close: closeTips }] = useDisclosure(false)
  const [weakPointsOpened, { open: openWeakPoints, close: closeWeakPoints }] = useDisclosure(false)
  const [resultOpened, { open: openResult, close: closeResult }] = useDisclosure(false)

  // 音频引用
  const audioRef = useRef<HTMLAudioElement>(null)

  // ==================== 数据查询 ====================

  // 获取听力练习列表
  const { data: exercises, isLoading: exercisesLoading, error: exercisesError } = useQuery({
    queryKey: ['listening-exercises', selectedExerciseType, selectedDifficulty],
    queryFn: () => listeningApi.getExercises({
      exercise_type: selectedExerciseType,
      difficulty_level: selectedDifficulty,
      limit: 10,
    }),
  })

  // 处理练习加载错误
  useEffect(() => {
    if (exercisesError) {
      notifications.show({
        title: '加载练习失败',
        message: (exercisesError as any).response?.data?.message || (exercisesError as any).message || '请检查网络连接后重试',
        color: 'red',
      })
    }
  }, [exercisesError])

  // 组件卸载时清理资源
  useEffect(() => {
    return () => {
      // 清理音频引用
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ''
        audioRef.current.load()
      }
    }
  }, [])

  // 获取听力统计
  const { data: stats } = useQuery({
    queryKey: ['listening-stats'],
    queryFn: () => listeningApi.getStats(),
  })

  // 获取个人听力难点 - 需要在选择练习后调用
  const { data: weakPoints } = useQuery({
    queryKey: ['listening-weak-points', currentSession?.exercise_id],
    queryFn: () => currentSession?.exercise_id ? listeningApi.getWeakPoints(currentSession.exercise_id) : Promise.resolve(null),
    enabled: !!currentSession?.exercise_id,
  })

  // 获取听力技巧 - 需要在选择练习后调用
  const { data: tips } = useQuery({
    queryKey: ['listening-tips', currentSession?.exercise_id],
    queryFn: () => currentSession?.exercise_id ? listeningApi.getListeningTips(currentSession.exercise_id) : Promise.resolve(null),
    enabled: !!currentSession?.exercise_id,
  })

  // ==================== 变更操作 ====================

  // 开始训练会话
  const startSessionMutation = useMutation({
    mutationFn: (exerciseId: number) => listeningApi.startSession({
      exercise_id: exerciseId,
      session_name: `${EXERCISE_TYPE_CONFIG[selectedExerciseType].name}训练`,
      settings: sessionSettings,
    }),
    onSuccess: (session) => {
      setCurrentSession(session)
      setTrainingState(prev => ({
        ...prev,
        session_active: true,
        current_exercise: session.exercise_id,
      }))
      notifications.show({
        title: '训练开始',
        message: '听力训练会话已创建，开始你的听力练习！',
        color: 'green',
      })
    },
    onError: (error: any) => {
      notifications.show({
        title: '开始训练失败',
        message: error.message || '请稍后重试',
        color: 'red',
      })
    },
  })

  // 提交答案
  const submitAnswersMutation = useMutation({
    mutationFn: (data: {
      session_id: number
      answers: Record<string, any>
      audio_progress: Record<string, any>
      total_time_seconds: number
      listening_time_seconds: number
      answering_time_seconds: number
    }) => listeningApi.submitAnswers(data),
    onSuccess: (result) => {
      setTrainingState(prev => ({
        ...prev,
        session_active: false,
        answer_submitted: true,
      }))
      setTrainingResult(result)
      queryClient.invalidateQueries({ queryKey: ['listening-stats'] })
      queryClient.invalidateQueries({ queryKey: ['listening-weak-points'] })

      // 显示结果模态框
      openResult()

      notifications.show({
        title: '训练完成',
        message: `得分：${result.score}分，正确率：${Math.round((result.correct_count / result.total_questions) * 100)}%`,
        color: result.score >= 80 ? 'green' : result.score >= 60 ? 'yellow' : 'red',
      })
    },
    onError: (error: any) => {
      setTrainingState(prev => ({
        ...prev,
        session_active: false,
        answer_submitted: false,
      }))
      notifications.show({
        title: '提交答案失败',
        message: error.response?.data?.message || error.message || '请检查网络连接后重试',
        color: 'red',
      })
    },
  })

  // ==================== 事件处理 ====================

  const handleStartTraining = useCallback((exerciseId: number) => {
    // 验证练习ID
    if (!exerciseId || exerciseId <= 0) {
      notifications.show({
        title: '开始训练失败',
        message: '无效的练习ID',
        color: 'red',
      })
      return
    }
    startSessionMutation.mutate(exerciseId)
  }, [startSessionMutation])

  const handleSpeedChange = useCallback((speed: AudioPlaybackSpeed) => {
    setSessionSettings(prev => ({ ...prev, audio_speed: speed }))
  }, [])

  // ==================== 渲染函数 ====================

  const renderExerciseTypeCard = useCallback((type: ListeningExerciseType) => {
    const config = EXERCISE_TYPE_CONFIG[type]
    const IconComponent = config.icon
    const isSelected = selectedExerciseType === type

    return (
      <Card
        key={type}
        shadow={isSelected ? 'md' : 'sm'}
        padding="lg"
        radius="md"
        withBorder
        style={{
          cursor: 'pointer',
          borderColor: isSelected ? `var(--mantine-color-${config.color}-6)` : undefined,
          backgroundColor: isSelected ? `var(--mantine-color-${config.color}-0)` : undefined,
        }}
        onClick={() => setSelectedExerciseType(type)}
      >
        <Group justify="space-between" mb="md">
          <ThemeIcon size="lg" color={config.color} variant="light">
            <IconComponent size={24} />
          </ThemeIcon>
          {isSelected && (
            <Badge color={config.color} variant="filled">
              已选择
            </Badge>
          )}
        </Group>

        <Text fw={500} size="lg" mb="xs">
          {config.name}
        </Text>
        <Text size="sm" c="dimmed" mb="md">
          {config.description}
        </Text>

        <Group justify="space-between">
          <Text size="xs" c="dimmed">
            {config.count} × {config.questionsPerItem}题
          </Text>
          <Text size="xs" fw={500} c={config.color}>
            总计 {config.count * config.questionsPerItem} 题
          </Text>
        </Group>
      </Card>
    )
  }, [selectedExerciseType])

  return (
    <Container size="xl" py="md">
      {/* 页面标题 */}
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>听力训练系统</Title>
          <Text size="lg" c="dimmed">
            专业的英语四级听力训练，提升你的听力理解能力
          </Text>
        </div>
        <Group>
          <Tooltip label="查看听力技巧">
            <ActionIcon variant="light" size="lg" onClick={openTips}>
              <IconBulb size={20} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="个人听力难点">
            <ActionIcon variant="light" size="lg" onClick={openWeakPoints}>
              <IconTarget size={20} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="训练设置">
            <ActionIcon variant="light" size="lg" onClick={openSettings}>
              <IconSettings size={20} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      {/* 统计概览 */}
      {stats && (
        <Grid mb="xl">
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                    完成练习
                  </Text>
                  <Text fw={700} size="xl">
                    {stats.completed_exercises}
                  </Text>
                </div>
                <ThemeIcon color="blue" size="lg" variant="light">
                  <IconCheck size={18} />
                </ThemeIcon>
              </Group>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                    平均得分
                  </Text>
                  <Text fw={700} size="xl">
                    {Math.round(stats.average_score)}分
                  </Text>
                </div>
                <ThemeIcon color="green" size="lg" variant="light">
                  <IconTrendingUp size={18} />
                </ThemeIcon>
              </Group>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                    听力时长
                  </Text>
                  <Text fw={700} size="xl">
                    {Math.round(stats.total_listening_time / 60)}分钟
                  </Text>
                </div>
                <ThemeIcon color="orange" size="lg" variant="light">
                  <IconHeadphones size={18} />
                </ThemeIcon>
              </Group>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                    进步率
                  </Text>
                  <Text fw={700} size="xl">
                    +{Math.round(stats.improvement_rate * 100)}%
                  </Text>
                </div>
                <ThemeIcon color="violet" size="lg" variant="light">
                  <IconChartLine size={18} />
                </ThemeIcon>
              </Group>
            </Card>
          </Grid.Col>
        </Grid>
      )}

      <Tabs defaultValue="practice">
        <Tabs.List>
          <Tabs.Tab value="practice" leftSection={<IconHeadphones size={16} />}>
            听力练习
          </Tabs.Tab>
          <Tabs.Tab value="analysis" leftSection={<IconBrain size={16} />}>
            能力分析
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="practice" pt="md">
          {/* 题型选择 */}
          <Card withBorder mb="lg">
            <Title order={3} mb="md">选择练习类型</Title>
            <Text size="sm" c="dimmed" mb="lg">
              根据英语四级听力考试标准，选择不同类型的听力练习
            </Text>
            
            <Grid>
              {useMemo(() =>
              (Object.keys(EXERCISE_TYPE_CONFIG) as ListeningExerciseType[]).map(renderExerciseTypeCard),
              [renderExerciseTypeCard]
            )}
            </Grid>
          </Card>

          {/* 难度和设置 */}
          <Grid mb="lg">
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder>
                <Title order={4} mb="md">难度设置</Title>
                <Select
                  label="选择难度级别"
                  value={selectedDifficulty}
                  onChange={(value) => setSelectedDifficulty(value as DifficultyLevel)}
                  data={[
                    { value: DifficultyLevel.BEGINNER, label: '初级' },
                    { value: DifficultyLevel.ELEMENTARY, label: '基础' },
                    { value: DifficultyLevel.INTERMEDIATE, label: '中级' },
                    { value: DifficultyLevel.ADVANCED, label: '高级' },
                    { value: DifficultyLevel.EXPERT, label: '专家' },
                  ]}
                />
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder>
                <Title order={4} mb="md">快速设置</Title>
                <Stack gap="xs">
                  <Group justify="space-between">
                    <Text size="sm">字幕辅助</Text>
                    <Switch
                      checked={sessionSettings.subtitles_enabled}
                      onChange={(event) => setSessionSettings(prev => ({
                        ...prev,
                        subtitles_enabled: event.currentTarget.checked
                      }))}
                    />
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">跟读练习</Text>
                    <Switch
                      checked={sessionSettings.pronunciation_practice}
                      onChange={(event) => setSessionSettings(prev => ({
                        ...prev,
                        pronunciation_practice: event.currentTarget.checked
                      }))}
                    />
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>

          {/* 练习列表 */}
          <Card withBorder>
            <Group justify="space-between" mb="md">
              <Title order={3}>可用练习</Title>
              <Badge color="blue">
                {EXERCISE_TYPE_CONFIG[selectedExerciseType].name}
              </Badge>
            </Group>

            {exercisesLoading ? (
              <Center h={200}>
                <Loader size="lg" />
              </Center>
            ) : exercises?.exercises.length ? (
              <Stack gap="md">
                {exercises.exercises.map((exercise) => (
                  <Card key={exercise.id} withBorder padding="md">
                    <Group justify="space-between">
                      <div style={{ flex: 1 }}>
                        <Text fw={500} mb="xs">{exercise.title}</Text>
                        <Text size="sm" c="dimmed" mb="sm">
                          {exercise.description}
                        </Text>
                        <Group gap="xs">
                          <Badge size="sm" color="blue">
                            {exercise.total_questions}题
                          </Badge>
                          <Badge size="sm" color="green">
                            {exercise.difficulty_level}
                          </Badge>
                          {exercise.audio_duration && (
                            <Badge size="sm" color="orange">
                              {Math.round(exercise.audio_duration / 60)}分钟
                            </Badge>
                          )}
                        </Group>
                      </div>
                      <Button
                        leftSection={<IconPlayerPlay size={16} />}
                        onClick={() => handleStartTraining(exercise.id)}
                        loading={startSessionMutation.isPending}
                      >
                        开始训练
                      </Button>
                    </Group>
                  </Card>
                ))}
              </Stack>
            ) : (
              <Center h={200}>
                <Stack align="center">
                  <IconHeadphones size={48} color="gray" />
                  <Text c="dimmed">暂无可用的听力练习</Text>
                  <Button variant="light" leftSection={<IconRefresh size={16} />}>
                    刷新列表
                  </Button>
                </Stack>
              </Center>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="analysis" pt="md">
          {/* 能力分析面板 */}
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card withBorder>
                <Title order={3} mb="md">听力能力分析</Title>
                {/* 这里将在后续添加详细的能力分析图表 */}
                <Center h={300}>
                  <Stack align="center">
                    <IconBrain size={48} color="gray" />
                    <Text c="dimmed">能力分析功能开发中...</Text>
                  </Stack>
                </Center>
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Stack>
                <Card withBorder>
                  <Title order={4} mb="md">薄弱环节</Title>
                  {weakPoints?.weak_points.length ? (
                    <Stack gap="xs">
                      {weakPoints.weak_points.slice(0, 3).map((point, index) => (
                        <Group key={index} justify="space-between">
                          <Text size="sm">{point.description}</Text>
                          <Badge size="xs" color="red">
                            {point.frequency}次
                          </Badge>
                        </Group>
                      ))}
                    </Stack>
                  ) : (
                    <Text size="sm" c="dimmed">暂无数据</Text>
                  )}
                </Card>
                <Card withBorder>
                  <Title order={4} mb="md">优势领域</Title>
                  {stats?.strong_exercise_types.length ? (
                    <Stack gap="xs">
                      {stats.strong_exercise_types.map((type, index) => (
                        <Badge key={index} color="green" variant="light">
                          {EXERCISE_TYPE_CONFIG[type as ListeningExerciseType]?.name || type}
                        </Badge>
                      ))}
                    </Stack>
                  ) : (
                    <Text size="sm" c="dimmed">继续练习以发现优势</Text>
                  )}
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>
      </Tabs>

      {/* 当前训练会话界面 */}
      {currentSession && trainingState.session_active && (
        <Modal
          opened={trainingState.session_active}
          onClose={() => {}}
          title={`${EXERCISE_TYPE_CONFIG[selectedExerciseType].name} - 训练中`}
          size="xl"
          closeOnClickOutside={false}
          closeOnEscape={false}
        >
          <ListeningTrainingSession
            session={currentSession}
            settings={sessionSettings}
            onComplete={(result) => {
              submitAnswersMutation.mutate({
                session_id: currentSession.id,
                answers: result.answers,
                audio_progress: result.audio_progress,
                total_time_seconds: result.total_time_seconds,
                listening_time_seconds: result.listening_time_seconds,
                answering_time_seconds: result.answering_time_seconds,
              })
            }}
            onExit={() => {
              setCurrentSession(null)
              setTrainingState(prev => ({ ...prev, session_active: false }))
            }}
          />
        </Modal>
      )}

      {/* 隐藏的音频元素 */}
      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* 训练设置模态框 */}
      <Modal opened={settingsOpened} onClose={closeSettings} title="训练设置" size="md">
        <Stack gap="md">
          <div>
            <Text size="sm" fw={500} mb="xs">音频播放速度</Text>
            <Select
              value={sessionSettings.audio_speed.toString()}
              onChange={(value) => handleSpeedChange(parseFloat(value!) as AudioPlaybackSpeed)}
              data={AUDIO_SPEEDS.map(speed => ({
                value: speed.toString(),
                label: `${speed}x ${speed === 1.0 ? '(正常)' : speed < 1.0 ? '(慢速)' : '(快速)'}`
              }))}
            />
          </div>

          <Switch
            label="显示字幕辅助"
            description="在训练模式下显示听力原文"
            checked={sessionSettings.subtitles_enabled}
            onChange={(event) => setSessionSettings(prev => ({
              ...prev,
              subtitles_enabled: event.currentTarget.checked
            }))}
          />

          <Switch
            label="启用重复播放"
            description="允许重复播放音频片段"
            checked={sessionSettings.repeat_enabled}
            onChange={(event) => setSessionSettings(prev => ({
              ...prev,
              repeat_enabled: event.currentTarget.checked
            }))}
          />

          <Switch
            label="口语跟读练习"
            description="开启发音练习和评估功能"
            checked={sessionSettings.pronunciation_practice}
            onChange={(event) => setSessionSettings(prev => ({
              ...prev,
              pronunciation_practice: event.currentTarget.checked
            }))}
          />

          <Switch
            label="听写训练模式"
            description="启用单词和短语听写功能"
            checked={sessionSettings.dictation_mode}
            onChange={(event) => setSessionSettings(prev => ({
              ...prev,
              dictation_mode: event.currentTarget.checked
            }))}
          />

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={closeSettings}>
              取消
            </Button>
            <Button onClick={closeSettings}>
              保存设置
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 听力技巧模态框 */}
      <Modal opened={tipsOpened} onClose={closeTips} title="听力应试技巧" size="lg">
        {tips?.tips.length ? (
          <Stack gap="md">
            {tips.tips.map((tip, index) => (
              <Card key={index} withBorder padding="md">
                <Group justify="space-between" mb="xs">
                  <Text fw={500}>{tip.title}</Text>
                  <Badge size="sm" color="blue">{tip.category}</Badge>
                </Group>
                <Text size="sm" c="dimmed" mb="sm">{tip.description}</Text>
                {tip.examples.length > 0 && (
                  <div>
                    <Text size="xs" fw={500} mb="xs">示例：</Text>
                    <Stack gap="xs">
                      {tip.examples.map((example, idx) => (
                        <Text key={idx} size="xs" c="dimmed">• {example}</Text>
                      ))}
                    </Stack>
                  </div>
                )}
              </Card>
            ))}
          </Stack>
        ) : (
          <Center h={200}>
            <Stack align="center">
              <IconBulb size={48} color="gray" />
              <Text c="dimmed">暂无听力技巧数据</Text>
            </Stack>
          </Center>
        )}
      </Modal>

      {/* 个人听力难点模态框 */}
      <Modal opened={weakPointsOpened} onClose={closeWeakPoints} title="个人听力难点分析" size="lg">
        {weakPoints ? (
          <Tabs defaultValue="weak-points">
            <Tabs.List>
              <Tabs.Tab value="weak-points">薄弱环节</Tabs.Tab>
              <Tabs.Tab value="phonetic">音标难点</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="weak-points" pt="md">
              {weakPoints.weak_points.length ? (
                <Stack gap="md">
                  {weakPoints.weak_points.map((point, index) => (
                    <Card key={index} withBorder padding="md">
                      <Group justify="space-between" mb="xs">
                        <Text fw={500}>{point.description}</Text>
                        <Group gap="xs">
                          <Badge size="sm" color="red">
                            出现 {point.frequency} 次
                          </Badge>
                          <Badge size="sm" color="blue">
                            {point.category}
                          </Badge>
                        </Group>
                      </Group>
                      <Text size="sm" c="dimmed" mb="sm">
                        改进建议：
                      </Text>
                      <Stack gap="xs">
                        {point.improvement_suggestions.map((suggestion, idx) => (
                          <Text key={idx} size="sm">• {suggestion}</Text>
                        ))}
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              ) : (
                <Center h={200}>
                  <Stack align="center">
                    <IconTarget size={48} color="gray" />
                    <Text c="dimmed">暂无薄弱环节数据</Text>
                  </Stack>
                </Center>
              )}
            </Tabs.Panel>

            <Tabs.Panel value="phonetic" pt="md">
              {weakPoints.phonetic_difficulties.length ? (
                <Stack gap="md">
                  {weakPoints.phonetic_difficulties.map((phonetic, index) => (
                    <Card key={index} withBorder padding="md">
                      <Group justify="space-between" mb="xs">
                        <Text fw={500} size="lg">/{phonetic.phoneme}/</Text>
                        <RingProgress
                          size={60}
                          thickness={6}
                          sections={[
                            { value: phonetic.accuracy_rate * 100, color: phonetic.accuracy_rate > 0.8 ? 'green' : phonetic.accuracy_rate > 0.6 ? 'yellow' : 'red' }
                          ]}
                          label={
                            <Text size="xs" ta="center">
                              {Math.round(phonetic.accuracy_rate * 100)}%
                            </Text>
                          }
                        />
                      </Group>
                      <Text size="sm" c="dimmed" mb="sm">
                        练习建议：
                      </Text>
                      <Stack gap="xs">
                        {phonetic.practice_suggestions.map((suggestion, idx) => (
                          <Text key={idx} size="sm">• {suggestion}</Text>
                        ))}
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              ) : (
                <Center h={200}>
                  <Stack align="center">
                    <IconEar size={48} color="gray" />
                    <Text c="dimmed">暂无音标难点数据</Text>
                  </Stack>
                </Center>
              )}
            </Tabs.Panel>
          </Tabs>
        ) : (
          <Center h={200}>
            <Loader size="lg" />
          </Center>
        )}
      </Modal>

      {/* 训练结果模态框 */}
      <Modal opened={resultOpened} onClose={closeResult} title="训练结果分析" size="xl">
        {trainingResult && (
          <Stack gap="md">
            {/* 基础结果 */}
            <Card withBorder>
              <Group justify="space-between" mb="md">
                <Text fw={500}>训练成绩</Text>
                <Badge color={trainingResult.score >= 80 ? 'green' : trainingResult.score >= 60 ? 'yellow' : 'red'} size="lg">
                  {trainingResult.score}分
                </Badge>
              </Group>
              <Grid>
                <Grid.Col span={6}>
                  <Text size="sm" c="dimmed">正确题数</Text>
                  <Text fw={500}>{trainingResult.correct_count} / {trainingResult.total_questions}</Text>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="sm" c="dimmed">正确率</Text>
                  <Text fw={500}>{Math.round((trainingResult.correct_count / trainingResult.total_questions) * 100)}%</Text>
                </Grid.Col>
              </Grid>
            </Card>

            {/* 错误分析 */}
            <Card withBorder>
              <Text fw={500} mb="md">错误原因分析</Text>
              <Text size="sm" c="dimmed">
                基于您的答题情况，系统将为您生成详细的错误分析报告...
              </Text>
            </Card>

            {/* 改进建议 */}
            <Card withBorder>
              <Text fw={500} mb="md">改进建议</Text>
              {trainingResult.improvement_suggestions?.length > 0 ? (
                <Stack gap="xs">
                  {trainingResult.improvement_suggestions.map((suggestion: string, index: number) => (
                    <Text key={index} size="sm">• {suggestion}</Text>
                  ))}
                </Stack>
              ) : (
                <Text size="sm" c="dimmed">继续保持良好的学习状态！</Text>
              )}
            </Card>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeResult}>
                关闭
              </Button>
              <Button onClick={() => {
                closeResult()
                setCurrentSession(null)
                setTrainingResult(null)
                setTrainingState(prev => ({ ...prev, session_active: false, answer_submitted: false }))
              }}>
                继续训练
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Container>
  )
}
