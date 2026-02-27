/**
 * 需求26：英语四级写作标准库 - 写作练习页面
 * 
 * 实现智能写作辅助和实时评分功能
 */

import { useState, useEffect } from 'react'
import {
  Container,
  Title,
  Text,
  Grid,
  Card,
  Button,
  Group,
  Badge,
  Stack,
  Textarea,
  Paper,
  Progress,
  Alert,
  LoadingOverlay,
  Modal,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import {
  IconPencil,
  IconClock,
  IconSend,
  IconBulb,
  IconBook,
  IconTarget,
  IconAlertCircle,
  IconCheck,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { useDisclosure } from '@mantine/hooks'

import { writingApi, WritingTask, GrammarError } from '@/api/writing'

export function WritingPracticePage(): JSX.Element {
  // 状态管理
  const [selectedTask, setSelectedTask] = useState<WritingTask | null>(null)
  const [essayContent, setEssayContent] = useState('')
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [isTimerActive, setIsTimerActive] = useState(false)
  const [startTime, setStartTime] = useState<Date | null>(null)
  const [grammarErrors, setGrammarErrors] = useState<GrammarError[]>([])
  const [writingHints, setWritingHints] = useState<string[]>([])
  const [wordCount, setWordCount] = useState(0)
  
  const [taskModalOpened, { open: openTaskModal, close: closeTaskModal }] = useDisclosure(false)
  const [submitModalOpened, { open: openSubmitModal, close: closeSubmitModal }] = useDisclosure(false)
  
  // const { user } = useAuthStore()
  const queryClient = useQueryClient()

  // 查询写作任务列表
  const {
    data: tasks,
    isLoading: tasksLoading,
  } = useQuery({
    queryKey: ['writing-tasks'],
    queryFn: () => writingApi.getTasks({ limit: 50 }),
  })

  // 语法检测
  const grammarCheckMutation = useMutation({
    mutationFn: (text: string) => writingApi.checkGrammar(text),
    onSuccess: (result) => {
      setGrammarErrors(result.errors)
      if (result.errors.length === 0) {
        notifications.show({
          title: '语法检测',
          message: '未发现语法错误，写得很好！',
          color: 'green',
          icon: <IconCheck size={16} />,
        })
      }
    },
  })

  // 获取写作提示
  const hintsQuery = useQuery({
    queryKey: ['writing-hints', selectedTask?.id, essayContent],
    queryFn: () => writingApi.getWritingHints(selectedTask!.id, essayContent),
    enabled: !!selectedTask && essayContent.length > 50,
    refetchInterval: 30000, // 每30秒更新一次提示
  })

  // 自动保存草稿
  const saveDraftMutation = useMutation({
    mutationFn: ({ taskId, content }: { taskId: number; content: string }) =>
      writingApi.saveDraft(taskId, content),
  })

  // 提交作文
  const submitEssayMutation = useMutation({
    mutationFn: (data: { task_id: number; essay_content: string; writing_time_minutes: number }) =>
      writingApi.submitEssay(data),
    onSuccess: () => {
      notifications.show({
        title: '提交成功',
        message: '作文已提交，正在进行智能评分...',
        color: 'green',
      })
      setSelectedTask(null)
      setEssayContent('')
      setTimeRemaining(0)
      setIsTimerActive(false)
      setStartTime(null)
      closeSubmitModal()
      queryClient.invalidateQueries({ queryKey: ['writing-submissions'] })
    },
  })

  // 计算字数
  useEffect(() => {
    const words = essayContent.trim().split(/\s+/).filter(word => word.length > 0)
    setWordCount(words.length)
  }, [essayContent])

  // 自动保存
  useEffect(() => {
    if (selectedTask && essayContent.length > 0) {
      const timer = setTimeout(() => {
        saveDraftMutation.mutate({ taskId: selectedTask.id, content: essayContent })
      }, 5000) // 5秒后自动保存

      return () => clearTimeout(timer)
    }
    return undefined
  }, [essayContent, selectedTask, saveDraftMutation])

  // 倒计时器
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null
    
    if (isTimerActive && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(time => {
          if (time <= 1) {
            setIsTimerActive(false)
            notifications.show({
              title: '时间到！',
              message: '写作时间已结束，请提交您的作文',
              color: 'orange',
              autoClose: false,
            })
            return 0
          }
          return time - 1
        })
      }, 1000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isTimerActive, timeRemaining])

  // 更新写作提示
  useEffect(() => {
    if (hintsQuery.data) {
      setWritingHints(hintsQuery.data.hints)
    }
  }, [hintsQuery.data])

  // 开始写作任务
  const startWritingTask = (task: WritingTask) => {
    setSelectedTask(task)
    setTimeRemaining(task.time_limit_minutes * 60)
    setIsTimerActive(true)
    setStartTime(new Date())
    setEssayContent('')
    setGrammarErrors([])
    setWritingHints([])
    closeTaskModal()
    
    // 加载草稿
    writingApi.getDraft(task.id).then(draft => {
      if (draft) {
        setEssayContent(draft.content)
        notifications.show({
          title: '草稿已加载',
          message: '已为您加载之前保存的草稿',
          color: 'blue',
        })
      }
    })
  }

  // 格式化时间
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 获取写作进度
  const getWritingProgress = () => {
    if (!selectedTask) return 0
    const targetWords = (selectedTask.word_count_min + selectedTask.word_count_max) / 2
    return Math.min((wordCount / targetWords) * 100, 100)
  }

  // 提交作文
  const handleSubmitEssay = () => {
    if (!selectedTask || !startTime) return
    
    const writingTimeMinutes = Math.round((Date.now() - startTime.getTime()) / (1000 * 60))
    
    submitEssayMutation.mutate({
      task_id: selectedTask.id,
      essay_content: essayContent,
      writing_time_minutes: writingTimeMinutes,
    })
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={tasksLoading} />

      {/* 页面标题 */}
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>写作练习</Title>
          <Text size="lg" c="dimmed">
            选择写作任务，开始您的英语写作训练
          </Text>
        </div>
        <Group>
          {!selectedTask && (
            <Button leftSection={<IconPencil size={16} />} onClick={openTaskModal}>
              开始写作
            </Button>
          )}
          {selectedTask && (
            <Group>
              <Badge color="blue" size="lg">
                {formatTime(timeRemaining)}
              </Badge>
              <Button
                leftSection={<IconSend size={16} />}
                onClick={openSubmitModal}
                disabled={wordCount < (selectedTask.word_count_min || 0)}
              >
                提交作文
              </Button>
            </Group>
          )}
        </Group>
      </Group>

      {selectedTask ? (
        // 写作界面
        <Grid>
          <Grid.Col span={8}>
            {/* 写作任务信息 */}
            <Card withBorder mb="md">
              <Group justify="space-between" mb="sm">
                <Text fw={600} size="lg">{selectedTask.task_title}</Text>
                <Group>
                  <Badge color="blue">{selectedTask.writing_type}</Badge>
                  <Badge color="orange">{selectedTask.difficulty}</Badge>
                </Group>
              </Group>
              <Text size="sm" c="dimmed" mb="sm">
                {selectedTask.task_prompt}
              </Text>
              <Group>
                <Text size="xs" c="dimmed">
                  字数要求: {selectedTask.word_count_min}-{selectedTask.word_count_max}
                </Text>
                <Text size="xs" c="dimmed">
                  时间限制: {selectedTask.time_limit_minutes}分钟
                </Text>
              </Group>
            </Card>

            {/* 写作区域 */}
            <Card withBorder>
              <Group justify="space-between" mb="sm">
                <Text fw={600}>写作区域</Text>
                <Group>
                  <Text size="sm" c="dimmed">
                    字数: {wordCount}/{selectedTask.word_count_min}-{selectedTask.word_count_max}
                  </Text>
                  <Tooltip label="语法检测">
                    <ActionIcon
                      variant="light"
                      onClick={() => grammarCheckMutation.mutate(essayContent)}
                      loading={grammarCheckMutation.isPending}
                    >
                      <IconCheck size={16} />
                    </ActionIcon>
                  </Tooltip>
                  <Tooltip label="保存草稿">
                    <ActionIcon
                      variant="light"
                      onClick={() => saveDraftMutation.mutate({ taskId: selectedTask.id, content: essayContent })}
                      loading={saveDraftMutation.isPending}
                    >
                      <IconBook size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Group>
              
              <Progress value={getWritingProgress()} mb="sm" />
              
              <Textarea
                value={essayContent}
                onChange={(event) => setEssayContent(event.currentTarget.value)}
                placeholder="在这里开始您的写作..."
                minRows={15}
                maxRows={20}
                autosize
              />
              
              {/* 语法错误提示 */}
              {grammarErrors.length > 0 && (
                <Alert icon={<IconAlertCircle size={16} />} color="red" mt="sm">
                  <Text size="sm" fw={600} mb="xs">发现 {grammarErrors.length} 个语法错误：</Text>
                  <Stack gap="xs">
                    {grammarErrors.slice(0, 3).map((error, index) => (
                      <Text key={index} size="xs">
                        • {error.message} - {error.suggestion}
                      </Text>
                    ))}
                  </Stack>
                </Alert>
              )}
            </Card>
          </Grid.Col>

          <Grid.Col span={4}>
            {/* 写作辅助 */}
            <Stack gap="md">
              {/* 时间管理 */}
              <Card withBorder>
                <Group justify="space-between" mb="sm">
                  <Text fw={600}>时间管理</Text>
                  <IconClock size={20} />
                </Group>
                <Text size="xl" fw={700} ta="center" mb="sm">
                  {formatTime(timeRemaining)}
                </Text>
                <Progress
                  value={(1 - timeRemaining / (selectedTask.time_limit_minutes * 60)) * 100}
                  color={timeRemaining < 300 ? 'red' : timeRemaining < 600 ? 'orange' : 'blue'}
                />
              </Card>

              {/* 写作提示 */}
              {writingHints.length > 0 && (
                <Card withBorder>
                  <Group justify="space-between" mb="sm">
                    <Text fw={600}>写作提示</Text>
                    <IconBulb size={20} />
                  </Group>
                  <Stack gap="xs">
                    {writingHints.slice(0, 3).map((hint, index) => (
                      <Paper key={index} p="xs" withBorder>
                        <Text size="sm">{hint}</Text>
                      </Paper>
                    ))}
                  </Stack>
                </Card>
              )}

              {/* 关键词提示 */}
              {selectedTask.keywords && selectedTask.keywords.length > 0 && (
                <Card withBorder>
                  <Group justify="space-between" mb="sm">
                    <Text fw={600}>关键词</Text>
                    <IconTarget size={20} />
                  </Group>
                  <Group gap="xs">
                    {selectedTask.keywords.map((keyword, index) => (
                      <Badge key={index} variant="light" size="sm">
                        {keyword}
                      </Badge>
                    ))}
                  </Group>
                </Card>
              )}

              {/* 大纲建议 */}
              {selectedTask.outline_suggestions && selectedTask.outline_suggestions.length > 0 && (
                <Card withBorder>
                  <Group justify="space-between" mb="sm">
                    <Text fw={600}>大纲建议</Text>
                    <IconBook size={20} />
                  </Group>
                  <Stack gap="xs">
                    {selectedTask.outline_suggestions.map((suggestion, index) => (
                      <Text key={index} size="sm">
                        {index + 1}. {suggestion}
                      </Text>
                    ))}
                  </Stack>
                </Card>
              )}
            </Stack>
          </Grid.Col>
        </Grid>
      ) : (
        // 任务选择界面
        <Card withBorder>
          <Text size="lg" fw={600} mb="md">选择写作任务</Text>
          <Text c="dimmed" mb="lg">
            请选择一个写作任务开始练习，系统将为您提供智能写作辅助
          </Text>
          <Button leftSection={<IconPencil size={16} />} onClick={openTaskModal}>
            浏览写作任务
          </Button>
        </Card>
      )}

      {/* 任务选择模态框 */}
      <Modal opened={taskModalOpened} onClose={closeTaskModal} title="选择写作任务" size="lg">
        <Stack gap="md">
          {tasks?.data?.map((task) => (
            <Card key={task.id} withBorder p="md" style={{ cursor: 'pointer' }} onClick={() => startWritingTask(task)}>
              <Group justify="space-between" mb="sm">
                <Text fw={600}>{task.task_title}</Text>
                <Group>
                  <Badge color="blue">{task.writing_type}</Badge>
                  <Badge color="orange">{task.difficulty}</Badge>
                </Group>
              </Group>
              <Text size="sm" c="dimmed" lineClamp={2} mb="sm">
                {task.task_prompt}
              </Text>
              <Group>
                <Text size="xs" c="dimmed">
                  字数: {task.word_count_min}-{task.word_count_max}
                </Text>
                <Text size="xs" c="dimmed">
                  时间: {task.time_limit_minutes}分钟
                </Text>
              </Group>
            </Card>
          ))}
        </Stack>
      </Modal>

      {/* 提交确认模态框 */}
      <Modal opened={submitModalOpened} onClose={closeSubmitModal} title="提交作文">
        <Stack gap="md">
          <Text>确定要提交这篇作文吗？提交后将无法修改。</Text>
          <Group>
            <Text size="sm" c="dimmed">字数: {wordCount}</Text>
            <Text size="sm" c="dimmed">
              用时: {startTime ? Math.round((Date.now() - startTime.getTime()) / (1000 * 60)) : 0}分钟
            </Text>
          </Group>
          <Group justify="flex-end">
            <Button variant="light" onClick={closeSubmitModal}>
              取消
            </Button>
            <Button onClick={handleSubmitEssay} loading={submitEssayMutation.isPending}>
              确认提交
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
