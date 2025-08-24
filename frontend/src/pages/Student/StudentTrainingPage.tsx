/**
 * 学生训练中心页面
 */
import { useState } from 'react'
import {
  Container,
  Title,
  Text,
  Card,
  Grid,
  Group,
  Badge,
  Button,
  Stack,
  Progress,
  Modal,
  Select,
  NumberInput,
  Switch,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import {
  IconBook,
  IconHeadphones,
  IconPencil,
  IconLanguage,
  IconFileText,
  IconPlayerPlay,
  IconRefresh,
} from '@tabler/icons-react'
import { useDisclosure } from '@mantine/hooks'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { trainingApi } from '@/api/training'
import { TrainingType, DifficultyLevel } from '../../types/training'

export function StudentTrainingPage(): JSX.Element {
  const [settingsOpened, { open: openSettings, close: closeSettings }] = useDisclosure(false)
  const [selectedModule, setSelectedModule] = useState<string | null>(null)
  const [difficulty, setDifficulty] = useState<DifficultyLevel>(DifficultyLevel.INTERMEDIATE)
  const [questionCount, setQuestionCount] = useState(20)
  const [timeLimit, setTimeLimit] = useState(30)
  const [adaptiveMode, setAdaptiveMode] = useState(true)

  const queryClient = useQueryClient()

  // 获取训练统计
  const { data: stats, refetch } = useQuery({
    queryKey: ['training-stats'],
    queryFn: () => trainingApi.getTrainingStats(),
  })

  // 获取当前训练会话
  const { data: currentSession } = useQuery({
    queryKey: ['current-session'],
    queryFn: () => trainingApi.getCurrentSession(),
  })

  // 开始训练
  const startTrainingMutation = useMutation({
    mutationFn: (data: {
      type: TrainingType
      difficulty: DifficultyLevel
      questionCount: number
      timeLimit: number
      adaptiveMode: boolean
    }) => trainingApi.startTraining(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-session'] })
      queryClient.invalidateQueries({ queryKey: ['training-stats'] })
      notifications.show({
        title: '训练开始',
        message: '训练会话已创建，开始你的学习之旅！',
        color: 'green',
      })
      closeSettings()
    },
  })

  const trainingModules = [
    {
      id: 'vocabulary',
      name: '词汇训练',
      icon: IconBook,
      color: 'blue',
      description: '基础词汇和高频词汇训练',
      progress: 75,
      available: true,
    },
    {
      id: 'listening',
      name: '听力训练',
      icon: IconHeadphones,
      color: 'green',
      description: '听力理解和听力技巧训练',
      progress: 60,
      available: true,
    },
    {
      id: 'reading',
      name: '阅读训练',
      icon: IconFileText,
      color: 'orange',
      description: '阅读理解和阅读技巧训练',
      progress: 85,
      available: true,
    },
    {
      id: 'writing',
      name: '写作训练',
      icon: IconPencil,
      color: 'violet',
      description: '写作技巧和表达能力训练',
      progress: 45,
      available: true,
    },
    {
      id: 'translation',
      name: '翻译训练',
      icon: IconLanguage,
      color: 'red',
      description: '中英互译和翻译技巧训练',
      progress: 30,
      available: false,
    },
  ]

  const handleStartTraining = (moduleId: string) => {
    setSelectedModule(moduleId)
    openSettings()
  }

  const handleConfirmStart = () => {
    if (!selectedModule) return

    startTrainingMutation.mutate({
      type: selectedModule as TrainingType,
      difficulty,
      questionCount,
      timeLimit: timeLimit * 60, // 转换为秒
      adaptiveMode,
    })
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>训练中心</Title>
          <Text size="lg" c="dimmed">
            选择一个训练模块开始你的英语学习之旅
          </Text>
        </div>
        <Tooltip label="刷新数据">
          <ActionIcon variant="light" size="lg" onClick={() => refetch()}>
            <IconRefresh size={20} />
          </ActionIcon>
        </Tooltip>
      </Group>

      {/* 当前训练会话 */}
      {currentSession && (
        <Card shadow="sm" padding="lg" radius="md" withBorder mb="xl" bg="blue.0">
          <Group justify="space-between" mb="md">
            <Text size="lg" fw={600} c="blue">
              当前训练会话
            </Text>
            <Badge color="blue" variant="filled">
              进行中
            </Badge>
          </Group>
          <Group justify="space-between">
            <div>
              <Text size="sm" c="dimmed">
                训练类型
              </Text>
              <Text fw={500}>{currentSession.type}</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">
                进度
              </Text>
              <Text fw={500}>{currentSession.progress.toFixed(1)}%</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">
                当前分数
              </Text>
              <Text fw={500}>{currentSession.score.toFixed(1)}</Text>
            </div>
            <Button leftSection={<IconPlayerPlay size={16} />} size="sm">
              继续训练
            </Button>
          </Group>
        </Card>
      )}

      <Grid>
        {trainingModules.map(module => {
          const IconComponent = module.icon
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
                    {module.available ? '可用' : '即将开放'}
                  </Badge>
                </Group>

                <Text size="sm" c="dimmed" mb="md">
                  {module.description}
                </Text>

                {module.available && (
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">学习进度</Text>
                      <Text size="sm" fw={500}>
                        {module.progress}%
                      </Text>
                    </Group>
                    <Progress value={module.progress} color={module.color} size="sm" mb="md" />
                  </div>
                )}

                <Button
                  variant="light"
                  color={module.color}
                  fullWidth
                  disabled={!module.available}
                  leftSection={<IconPlayerPlay size={16} />}
                  onClick={() => handleStartTraining(module.id)}
                >
                  {module.available ? '开始训练' : '即将开放'}
                </Button>
              </Card>
            </Grid.Col>
          )
        })}
      </Grid>

      {/* 训练统计 */}
      {stats && (
        <Card shadow="sm" padding="lg" radius="md" withBorder mt="xl">
          <Text size="lg" fw={600} mb="md">
            训练统计
          </Text>
          <Grid>
            <Grid.Col span={{ base: 6, md: 3 }}>
              <Stack gap="xs" align="center">
                <Text size="xl" fw={700} c="blue">
                  {stats.totalSessions}
                </Text>
                <Text size="sm" c="dimmed">
                  总训练次数
                </Text>
              </Stack>
            </Grid.Col>
            <Grid.Col span={{ base: 6, md: 3 }}>
              <Stack gap="xs" align="center">
                <Text size="xl" fw={700} c="green">
                  {stats.averageScore.toFixed(1)}
                </Text>
                <Text size="sm" c="dimmed">
                  平均分数
                </Text>
              </Stack>
            </Grid.Col>
            <Grid.Col span={{ base: 6, md: 3 }}>
              <Stack gap="xs" align="center">
                <Text size="xl" fw={700} c="orange">
                  {stats.streak}
                </Text>
                <Text size="sm" c="dimmed">
                  连续学习天数
                </Text>
              </Stack>
            </Grid.Col>
            <Grid.Col span={{ base: 6, md: 3 }}>
              <Stack gap="xs" align="center">
                <Text size="xl" fw={700} c="violet">
                  {stats.level}
                </Text>
                <Text size="sm" c="dimmed">
                  当前等级
                </Text>
              </Stack>
            </Grid.Col>
          </Grid>
        </Card>
      )}

      {/* 训练设置模态框 */}
      <Modal opened={settingsOpened} onClose={closeSettings} title="训练设置" size="md">
        <Stack gap="md">
          <Select
            label="难度等级"
            value={difficulty}
            onChange={value => setDifficulty(value as DifficultyLevel)}
            data={[
              { value: 'beginner', label: '初级' },
              { value: 'intermediate', label: '中级' },
              { value: 'advanced', label: '高级' },
              { value: 'expert', label: '专家' },
            ]}
          />

          <NumberInput
            label="题目数量"
            value={questionCount}
            onChange={value => setQuestionCount(Number(value))}
            min={10}
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
            <Button
              leftSection={<IconPlayerPlay size={16} />}
              onClick={handleConfirmStart}
              loading={startTrainingMutation.isPending}
            >
              开始训练
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
