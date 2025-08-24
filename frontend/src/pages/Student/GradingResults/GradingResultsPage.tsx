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
  Progress,
  Title,
  Tabs,
  ActionIcon,
  Tooltip,
  Alert,
  Loader,
  Center,
  Timeline,
  ThemeIcon,
  Accordion,
  Highlight,
  Paper,
  Divider,
  RingProgress,
} from '@mantine/core'
import {
  IconCheck,
  IconX,
  IconAlertCircle,
  IconBulb,
  IconTarget,
  IconTrendingUp,
  IconDownload,
  IconShare,
  IconEye,
  IconChevronRight,
  IconStar,
  IconThumbUp,
  IconThumbDown,
  IconRobot,
  IconSparkles,
  IconRefresh,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { gradingApi, GradingResult, QuestionResult } from '@/api/grading'
import { TrainingType } from '../../../types/training'

// 流式批改状态接口
interface StreamingGradingState {
  isStreaming: boolean
  currentText: string
  progress: number
  stage: 'analyzing' | 'grading' | 'generating_feedback' | 'complete'
  estimatedTime: number
  elapsedTime: number
}

// DeepSeek API配置
interface DeepSeekConfig {
  apiKey: string
  baseUrl: string
  model: string
  maxTokens: number
  temperature: number
}

// API密钥池管理
interface ApiKeyPool {
  keys: string[]
  currentIndex: number
  failedKeys: Set<string>
  lastRotation: Date
}

// 批改历史记录
interface GradingHistory {
  id: string
  submissionId: number
  timestamp: Date
  result: AIAnalysisResult
  apiKeyUsed: string
  processingTime: number
  retryCount: number
}

// AI分析结果接口
interface AIAnalysisResult {
  overallScore: number
  detailedScores: {
    grammar: number
    vocabulary: number
    structure: number
    content: number
    fluency: number
  }
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  knowledgeGaps: string[]
  improvementPlan: string[]
  nextSteps: string[]
}

export const GradingResultsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview')

  // 流式批改状态
  const [streamingState, setStreamingState] = useState<StreamingGradingState>({
    isStreaming: false,
    currentText: '',
    progress: 0,
    stage: 'analyzing',
    estimatedTime: 0,
    elapsedTime: 0,
  })

  // AI分析状态
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysisResult | null>(null)
  const [_gradingHistory, setGradingHistory] = useState<GradingHistory[]>([])
  const [apiKeyPool, setApiKeyPool] = useState<ApiKeyPool>({
    keys: [
      'sk-deepseek-key-1',
      'sk-deepseek-key-2',
      'sk-deepseek-key-3',
      // 在实际项目中，这些密钥应该从环境变量或安全存储中获取
    ],
    currentIndex: 0,
    failedKeys: new Set(),
    lastRotation: new Date(),
  })
  const [_retryCount, setRetryCount] = useState(0)
  const [maxRetries] = useState(3)

  // 获取最新的批改结果
  const { data: latestResult, isLoading: resultLoading } = useQuery({
    queryKey: ['latest-grading-result'],
    queryFn: () => gradingApi.getLatestResult(),
  })

  // 获取批改历史
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['grading-history'],
    queryFn: () => gradingApi.getGradingHistory({ limit: 20 }),
  })

  // 获取下一个可用的API密钥
  const getNextApiKey = (): string | null => {
    const availableKeys = apiKeyPool.keys.filter(key => !apiKeyPool.failedKeys.has(key))

    if (availableKeys.length === 0) {
      // 如果所有密钥都失败了，重置失败列表（可能是临时问题）
      if (Date.now() - apiKeyPool.lastRotation.getTime() > 5 * 60 * 1000) {
        // 5分钟后重试
        setApiKeyPool(prev => ({
          ...prev,
          failedKeys: new Set(),
          lastRotation: new Date(),
        }))
        return apiKeyPool.keys[0] || null
      }
      return null
    }

    const nextIndex = apiKeyPool.currentIndex % availableKeys.length
    setApiKeyPool(prev => ({
      ...prev,
      currentIndex: nextIndex + 1,
    }))

    return availableKeys[nextIndex] || null
  }

  // 标记API密钥为失败
  const markKeyAsFailed = (key: string) => {
    setApiKeyPool(prev => ({
      ...prev,
      failedKeys: new Set([...prev.failedKeys, key]),
    }))
  }

  // 调用DeepSeek API进行批改
  const callDeepSeekAPI = async (content: string, apiKey: string): Promise<AIAnalysisResult> => {
    const config: DeepSeekConfig = {
      apiKey,
      baseUrl: 'https://api.deepseek.com/v1',
      model: 'deepseek-chat',
      maxTokens: 2000,
      temperature: 0.7,
    }

    const prompt = `
请对以下英语作文进行详细批改和分析：

作文内容：
${content}

请按照以下格式返回JSON结果：
{
  "overallScore": 总分(0-100),
  "detailedScores": {
    "grammar": 语法分数(0-100),
    "vocabulary": 词汇分数(0-100),
    "structure": 结构分数(0-100),
    "content": 内容分数(0-100),
    "fluency": 流畅度分数(0-100)
  },
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["不足1", "不足2", "不足3"],
  "suggestions": ["建议1", "建议2", "建议3"],
  "knowledgeGaps": ["知识盲点1", "知识盲点2"],
  "improvementPlan": ["改进计划1", "改进计划2"],
  "nextSteps": ["下一步1", "下一步2"]
}
`

    const response = await fetch(`${config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${config.apiKey}`,
      },
      body: JSON.stringify({
        model: config.model,
        messages: [
          {
            role: 'system',
            content: '你是一个专业的英语作文批改老师，请提供详细、准确、有建设性的批改意见。',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        max_tokens: config.maxTokens,
        temperature: config.temperature,
        stream: false,
      }),
    })

    if (!response.ok) {
      throw new Error(`API调用失败: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    const content_text = data.choices[0]?.message?.content

    if (!content_text) {
      throw new Error('API返回内容为空')
    }

    return JSON.parse(content_text)
  }

  // 带重试机制的AI分析
  const performAIAnalysisWithRetry = async (
    content: string,
    submissionId: number
  ): Promise<AIAnalysisResult> => {
    let currentRetry = 0

    while (currentRetry < maxRetries) {
      const apiKey = getNextApiKey()

      if (!apiKey) {
        throw new Error('没有可用的API密钥')
      }

      try {
        setRetryCount(currentRetry)
        const result = await callDeepSeekAPI(content, apiKey)

        // 保存批改历史
        const historyRecord: GradingHistory = {
          id: Date.now().toString(),
          submissionId: submissionId || 0,
          timestamp: new Date(),
          result,
          apiKeyUsed: apiKey.substring(0, 10) + '...',
          processingTime: streamingState.elapsedTime,
          retryCount: currentRetry,
        }

        setGradingHistory(prev => [historyRecord, ...prev.slice(0, 9)]) // 保留最近10条记录
        return result
      } catch (error) {
        // API调用失败，进行重试
        markKeyAsFailed(apiKey)
        currentRetry++

        if (currentRetry < maxRetries) {
          // 等待一段时间后重试
          await new Promise(resolve => setTimeout(resolve, 1000 * currentRetry))
        }
      }
    }

    throw new Error('所有API调用都失败了')
  }

  // 流式批改功能（集成真实API）
  const startStreamingGrading = async (submissionId: number) => {
    setStreamingState({
      isStreaming: true,
      currentText: '',
      progress: 0,
      stage: 'analyzing',
      estimatedTime: 30, // 预估30秒
      elapsedTime: 0,
    })

    try {
      // 模拟流式批改过程
      const stages = [
        { stage: 'analyzing' as const, duration: 8000, text: '正在分析您的答案...' },
        { stage: 'grading' as const, duration: 12000, text: '正在进行智能批改...' },
        { stage: 'generating_feedback' as const, duration: 10000, text: '正在生成详细反馈...' },
        { stage: 'complete' as const, duration: 0, text: '批改完成！' },
      ]

      for (const stageInfo of stages) {
        setStreamingState(prev => ({
          ...prev,
          stage: stageInfo.stage,
          currentText: stageInfo.text,
        }))

        if (stageInfo.duration > 0) {
          await new Promise(resolve => {
            let elapsed = 0
            const interval = setInterval(() => {
              elapsed += 200
              const progress = Math.min((elapsed / stageInfo.duration) * 100, 100)

              setStreamingState(prev => ({
                ...prev,
                progress: progress,
                elapsedTime: prev.elapsedTime + 0.2,
              }))

              if (elapsed >= stageInfo.duration) {
                clearInterval(interval)
                resolve(void 0)
              }
            }, 200)
          })
        }
      }

      // 尝试调用真实API进行分析
      try {
        // 模拟获取提交内容
        const submissionContent = 'This is a sample essay content for grading...'
        const analysisResult = await performAIAnalysisWithRetry(submissionContent, submissionId)
        setAiAnalysis(analysisResult)

        notifications.show({
          title: '批改完成',
          message: 'AI智能批改已完成，请查看详细分析结果',
          color: 'green',
        })
      } catch (apiError) {
        // API调用失败，使用模拟数据

        // 如果API调用失败，使用模拟数据
        const fallbackResult: AIAnalysisResult = {
          overallScore: 85,
          detailedScores: {
            grammar: 88,
            vocabulary: 82,
            structure: 90,
            content: 85,
            fluency: 80,
          },
          strengths: ['语法结构基本正确', '词汇使用较为丰富', '逻辑结构清晰', '表达较为流畅'],
          weaknesses: ['部分词汇搭配不够准确', '句式变化可以更丰富', '个别语法细节需要注意'],
          suggestions: ['建议多练习高级词汇的使用', '可以尝试使用更多复合句', '注意时态的一致性'],
          knowledgeGaps: ['虚拟语气的使用', '高级词汇搭配', '复杂句式结构'],
          improvementPlan: [
            '每日练习10个高频词汇搭配',
            '阅读英文原版文章提升语感',
            '练习写作时注意句式多样化',
          ],
          nextSteps: ['完成词汇强化训练', '进行语法专项练习', '参与写作技巧提升课程'],
        }

        setAiAnalysis(fallbackResult)

        notifications.show({
          title: '批改完成（模拟模式）',
          message: 'API服务暂时不可用，已使用模拟数据完成批改',
          color: 'yellow',
        })
      }

      setStreamingState(prev => ({ ...prev, isStreaming: false }))
    } catch (error) {
      setStreamingState(prev => ({ ...prev, isStreaming: false }))
      notifications.show({
        title: '批改失败',
        message: '批改过程中出现错误，请重试',
        color: 'red',
      })
    }
  }

  // 提交反馈
  const feedbackMutation = useMutation({
    mutationFn: (data: { resultId: number; helpful: boolean }) => gradingApi.submitFeedback(data),
    onSuccess: () => {
      notifications.show({
        title: '反馈已提交',
        message: '感谢您的反馈，这将帮助我们改进批改质量',
        color: 'green',
      })
    },
  })

  // 重新批改功能
  const handleRegrade = () => {
    setAiAnalysis(null)
    setStreamingState({
      isStreaming: false,
      currentText: '',
      progress: 0,
      stage: 'analyzing',
      estimatedTime: 0,
      elapsedTime: 0,
    })

    notifications.show({
      title: '重新批改',
      message: '正在重新分析您的答案...',
      color: 'blue',
    })

    // 模拟重新批改
    setTimeout(() => {
      startStreamingGrading(1)
    }, 1000)
  }

  // 知识点热力图组件
  const KnowledgeHeatmap: React.FC<{ knowledgeGaps: string[] }> = ({ knowledgeGaps }) => {
    const knowledgeAreas = [
      { name: '语法基础', level: knowledgeGaps.includes('语法基础') ? 'weak' : 'strong' },
      { name: '词汇运用', level: knowledgeGaps.includes('词汇运用') ? 'weak' : 'medium' },
      { name: '句式结构', level: knowledgeGaps.includes('句式结构') ? 'weak' : 'strong' },
      { name: '逻辑连贯', level: knowledgeGaps.includes('逻辑连贯') ? 'weak' : 'strong' },
      { name: '时态运用', level: knowledgeGaps.includes('时态运用') ? 'weak' : 'medium' },
      { name: '语音语调', level: knowledgeGaps.includes('语音语调') ? 'weak' : 'medium' },
      { name: '写作技巧', level: knowledgeGaps.includes('写作技巧') ? 'weak' : 'strong' },
      { name: '阅读理解', level: knowledgeGaps.includes('阅读理解') ? 'weak' : 'strong' },
    ]

    const getHeatmapColor = (level: string) => {
      switch (level) {
        case 'strong':
          return '#51cf66' // 绿色 - 掌握良好
        case 'medium':
          return '#ffd43b' // 黄色 - 一般掌握
        case 'weak':
          return '#ff6b6b' // 红色 - 需要加强
        default:
          return '#e9ecef' // 灰色 - 未评估
      }
    }

    const getLevelText = (level: string) => {
      switch (level) {
        case 'strong':
          return '掌握良好'
        case 'medium':
          return '一般掌握'
        case 'weak':
          return '需要加强'
        default:
          return '未评估'
      }
    }

    return (
      <div>
        <Text size="md" fw={600} mb="md">
          知识点掌握热力图
        </Text>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px',
            marginBottom: '16px',
          }}
        >
          {knowledgeAreas.map((area, index) => (
            <div
              key={index}
              style={{
                backgroundColor: getHeatmapColor(area.level),
                padding: '12px',
                borderRadius: '8px',
                textAlign: 'center',
                color: area.level === 'medium' ? '#000' : '#fff',
                fontSize: '12px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'transform 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'scale(1.05)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'scale(1)'
              }}
              title={`${area.name}: ${getLevelText(area.level)}`}
            >
              {area.name}
            </div>
          ))}
        </div>

        {/* 图例 */}
        <Group gap="md" justify="center">
          <Group gap="xs">
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#51cf66',
                borderRadius: 4,
              }}
            />
            <Text size="xs">掌握良好</Text>
          </Group>
          <Group gap="xs">
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#ffd43b',
                borderRadius: 4,
              }}
            />
            <Text size="xs">一般掌握</Text>
          </Group>
          <Group gap="xs">
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#ff6b6b',
                borderRadius: 4,
              }}
            />
            <Text size="xs">需要加强</Text>
          </Group>
        </Group>
      </div>
    )
  }

  const handleFeedback = (resultId: number, helpful: boolean) => {
    feedbackMutation.mutate({ resultId, helpful })
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'green'
    if (score >= 80) return 'blue'
    if (score >= 70) return 'yellow'
    return 'red'
  }

  const getTypeLabel = (type: TrainingType) => {
    const labels: Record<TrainingType, string> = {
      listening: '听力训练',
      reading: '阅读理解',
      writing: '写作练习',
      translation: '翻译训练',
      vocabulary: '词汇练习',
      grammar: '语法训练',
      speaking: '口语练习',
    }
    return labels[type] || type
  }

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  if (resultLoading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    )
  }

  if (!latestResult) {
    return (
      <Container size="xl" py="md">
        <Alert icon={<IconAlertCircle size={16} />} title="暂无批改结果" color="blue">
          您还没有完成任何训练。完成训练后，AI将为您提供详细的批改结果和学习建议。
        </Alert>
      </Container>
    )
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>智能批改结果</Title>
        <Group>
          <Tooltip label="下载报告">
            <ActionIcon variant="light" size="lg">
              <IconDownload size={20} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="分享结果">
            <ActionIcon variant="light" size="lg">
              <IconShare size={20} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={value => value && setActiveTab(value)}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconTarget size={16} />}>
            结果概览
          </Tabs.Tab>
          <Tabs.Tab value="details" leftSection={<IconEye size={16} />}>
            详细分析
          </Tabs.Tab>
          <Tabs.Tab value="history" leftSection={<IconTrendingUp size={16} />}>
            历史记录
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          {/* 流式批改状态显示 */}
          {streamingState.isStreaming && (
            <Card shadow="sm" padding="lg" radius="md" withBorder mb="lg">
              <Group justify="space-between" mb="md">
                <Group>
                  <IconRobot size={24} color="blue" />
                  <Text size="lg" fw={600}>
                    AI智能批改进行中
                  </Text>
                </Group>
                <Badge color="blue" variant="light">
                  {streamingState.stage === 'analyzing' && '分析中'}
                  {streamingState.stage === 'grading' && '批改中'}
                  {streamingState.stage === 'generating_feedback' && '生成反馈'}
                  {streamingState.stage === 'complete' && '完成'}
                </Badge>
              </Group>

              <Text size="sm" c="dimmed" mb="md">
                {streamingState.currentText}
              </Text>

              <Progress
                value={streamingState.progress}
                color="blue"
                size="lg"
                radius="xl"
                mb="md"
                animated
              />

              <Group justify="space-between">
                <Text size="xs" c="dimmed">
                  已用时: {streamingState.elapsedTime.toFixed(1)}秒
                </Text>
                <Text size="xs" c="dimmed">
                  预计剩余:{' '}
                  {Math.max(0, streamingState.estimatedTime - streamingState.elapsedTime).toFixed(
                    1
                  )}
                  秒
                </Text>
              </Group>
            </Card>
          )}

          <Grid>
            {/* 总体成绩卡片 */}
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Stack align="center" gap="md">
                  <RingProgress
                    size={120}
                    thickness={12}
                    sections={[
                      {
                        value: (latestResult as GradingResult).accuracy * 100,
                        color: getScoreColor((latestResult as GradingResult).score),
                      },
                    ]}
                    label={
                      <Text size="xl" fw={700} ta="center">
                        {(latestResult as GradingResult).score}
                      </Text>
                    }
                  />
                  <div style={{ textAlign: 'center' }}>
                    <Text size="lg" fw={600}>
                      {getTypeLabel((latestResult as GradingResult).type)}
                    </Text>
                    <Text size="sm" c="dimmed">
                      {new Date((latestResult as GradingResult).completedAt).toLocaleString()}
                    </Text>
                  </div>

                  {/* 重新批改按钮 */}
                  <Button
                    variant="light"
                    size="sm"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => startStreamingGrading((latestResult as GradingResult).id)}
                    loading={streamingState.isStreaming}
                    disabled={streamingState.isStreaming}
                  >
                    重新批改
                  </Button>
                </Stack>
              </Card>
            </Grid.Col>

            {/* 详细统计 */}
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text size="lg" fw={600} mb="md">
                  详细统计
                </Text>
                <Grid>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        正确率
                      </Text>
                      <Group gap="xs">
                        <Text size="xl" fw={700}>
                          {((latestResult as GradingResult).accuracy * 100).toFixed(1)}%
                        </Text>
                        <Badge color={getScoreColor((latestResult as GradingResult).score)}>
                          {(latestResult as GradingResult).correctAnswers}/
                          {(latestResult as GradingResult).totalQuestions}
                        </Badge>
                      </Group>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Stack gap="xs">
                      <Text size="sm" c="dimmed">
                        用时
                      </Text>
                      <Text size="xl" fw={700}>
                        {formatTime((latestResult as GradingResult).timeSpent)}
                      </Text>
                    </Stack>
                  </Grid.Col>
                  <Grid.Col span={12}>
                    <Progress
                      value={(latestResult as GradingResult).accuracy * 100}
                      size="lg"
                      radius="xl"
                      color={getScoreColor((latestResult as GradingResult).score)}
                    />
                  </Grid.Col>
                </Grid>
              </Card>
            </Grid.Col>

            {/* AI 反馈 */}
            <Grid.Col span={12}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <Text size="lg" fw={600}>
                    AI 智能反馈
                  </Text>
                  <Group gap="xs">
                    <Tooltip label="这个反馈有帮助吗？">
                      <ActionIcon
                        variant="light"
                        color="green"
                        onClick={() => handleFeedback((latestResult as GradingResult).id, true)}
                      >
                        <IconThumbUp size={16} />
                      </ActionIcon>
                    </Tooltip>
                    <Tooltip label="这个反馈没有帮助">
                      <ActionIcon
                        variant="light"
                        color="red"
                        onClick={() => handleFeedback((latestResult as GradingResult).id, false)}
                      >
                        <IconThumbDown size={16} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                </Group>

                <Stack gap="md">
                  {/* 总体评价 */}
                  <Paper p="md" withBorder radius="md">
                    <Group gap="xs" mb="xs">
                      <IconStar size={16} color="orange" />
                      <Text fw={500}>总体评价</Text>
                    </Group>
                    <Text>{(latestResult as GradingResult).feedback.overall}</Text>
                  </Paper>

                  <Grid>
                    {/* 优势 */}
                    <Grid.Col span={{ base: 12, md: 4 }}>
                      <Paper p="md" withBorder radius="md" h="100%">
                        <Group gap="xs" mb="xs">
                          <ThemeIcon color="green" variant="light" size="sm">
                            <IconCheck size={12} />
                          </ThemeIcon>
                          <Text fw={500} c="green">
                            优势
                          </Text>
                        </Group>
                        <Stack gap="xs">
                          {(latestResult as GradingResult).feedback.strengths.map(
                            (strength: string, index: number) => (
                              <Text key={index} size="sm">
                                • {strength}
                              </Text>
                            )
                          )}
                        </Stack>
                      </Paper>
                    </Grid.Col>

                    {/* 待改进 */}
                    <Grid.Col span={{ base: 12, md: 4 }}>
                      <Paper p="md" withBorder radius="md" h="100%">
                        <Group gap="xs" mb="xs">
                          <ThemeIcon color="orange" variant="light" size="sm">
                            <IconAlertCircle size={12} />
                          </ThemeIcon>
                          <Text fw={500} c="orange">
                            待改进
                          </Text>
                        </Group>
                        <Stack gap="xs">
                          {(latestResult as GradingResult).feedback.weaknesses.map(
                            (weakness: string, index: number) => (
                              <Text key={index} size="sm">
                                • {weakness}
                              </Text>
                            )
                          )}
                        </Stack>
                      </Paper>
                    </Grid.Col>

                    {/* 学习建议 */}
                    <Grid.Col span={{ base: 12, md: 4 }}>
                      <Paper p="md" withBorder radius="md" h="100%">
                        <Group gap="xs" mb="xs">
                          <ThemeIcon color="blue" variant="light" size="sm">
                            <IconBulb size={12} />
                          </ThemeIcon>
                          <Text fw={500} c="blue">
                            学习建议
                          </Text>
                        </Group>
                        <Stack gap="xs">
                          {(latestResult as GradingResult).feedback.suggestions.map(
                            (suggestion: string, index: number) => (
                              <Text key={index} size="sm">
                                • {suggestion}
                              </Text>
                            )
                          )}
                        </Stack>
                      </Paper>
                    </Grid.Col>
                  </Grid>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="details" pt="md">
          {/* AI智能分析结果 */}
          {aiAnalysis && (
            <Card shadow="sm" padding="lg" radius="md" withBorder mb="lg">
              <Group justify="space-between" mb="md">
                <Group>
                  <IconSparkles size={24} color="purple" />
                  <Text size="lg" fw={600}>
                    AI智能分析报告
                  </Text>
                </Group>
                <Badge color="purple" variant="light">
                  深度分析
                </Badge>
              </Group>

              <Grid>
                {/* 详细评分 */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      详细评分
                    </Text>
                    <Stack gap="sm">
                      {Object.entries(aiAnalysis.detailedScores).map(([key, score]) => (
                        <Group key={key} justify="space-between">
                          <Text size="sm">
                            {key === 'grammar' && '语法'}
                            {key === 'vocabulary' && '词汇'}
                            {key === 'structure' && '结构'}
                            {key === 'content' && '内容'}
                            {key === 'fluency' && '流畅度'}
                          </Text>
                          <Group gap="xs">
                            <Progress value={score} color={getScoreColor(score)} size="sm" w={80} />
                            <Text size="sm" fw={500} w={30}>
                              {score}
                            </Text>
                          </Group>
                        </Group>
                      ))}
                    </Stack>
                  </Paper>
                </Grid.Col>

                {/* 优势与不足 */}
                <Grid.Col span={{ base: 12, md: 6 }}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      优势与不足
                    </Text>
                    <Stack gap="md">
                      <div>
                        <Group gap="xs" mb="xs">
                          <IconCheck size={16} color="green" />
                          <Text size="sm" fw={500} c="green">
                            优势
                          </Text>
                        </Group>
                        <Stack gap="xs">
                          {aiAnalysis.strengths.map((strength, index) => (
                            <Text key={index} size="xs" c="dimmed">
                              • {strength}
                            </Text>
                          ))}
                        </Stack>
                      </div>
                      <div>
                        <Group gap="xs" mb="xs">
                          <IconAlertCircle size={16} color="orange" />
                          <Text size="sm" fw={500} c="orange">
                            待改进
                          </Text>
                        </Group>
                        <Stack gap="xs">
                          {aiAnalysis.weaknesses.map((weakness, index) => (
                            <Text key={index} size="xs" c="dimmed">
                              • {weakness}
                            </Text>
                          ))}
                        </Stack>
                      </div>
                    </Stack>
                  </Paper>
                </Grid.Col>

                {/* 学习建议 */}
                <Grid.Col span={12}>
                  <Paper p="md" withBorder radius="md">
                    <Text fw={500} mb="md">
                      个性化学习建议
                    </Text>
                    <Grid>
                      <Grid.Col span={{ base: 12, md: 4 }}>
                        <Text size="sm" fw={500} mb="xs" c="blue">
                          即时建议
                        </Text>
                        <Stack gap="xs">
                          {aiAnalysis.suggestions.map((suggestion, index) => (
                            <Text key={index} size="xs" c="dimmed">
                              • {suggestion}
                            </Text>
                          ))}
                        </Stack>
                      </Grid.Col>
                      <Grid.Col span={{ base: 12, md: 4 }}>
                        <Text size="sm" fw={500} mb="xs" c="orange">
                          改进计划
                        </Text>
                        <Stack gap="xs">
                          {aiAnalysis.improvementPlan.map((plan, index) => (
                            <Text key={index} size="xs" c="dimmed">
                              • {plan}
                            </Text>
                          ))}
                        </Stack>
                      </Grid.Col>
                      <Grid.Col span={{ base: 12, md: 4 }}>
                        <Text size="sm" fw={500} mb="xs" c="green">
                          下一步行动
                        </Text>
                        <Stack gap="xs">
                          {aiAnalysis.nextSteps.map((step, index) => (
                            <Text key={index} size="xs" c="dimmed">
                              • {step}
                            </Text>
                          ))}
                        </Stack>
                      </Grid.Col>
                    </Grid>
                  </Paper>
                </Grid.Col>

                {/* 知识点热力图 */}
                <Grid.Col span={12}>
                  <Paper p="md" withBorder radius="md">
                    <KnowledgeHeatmap knowledgeGaps={aiAnalysis.knowledgeGaps} />
                  </Paper>
                </Grid.Col>
              </Grid>

              {/* 重新批改按钮 */}
              <Group justify="flex-end" mt="md">
                <Button
                  variant="light"
                  leftSection={<IconRefresh size={16} />}
                  onClick={handleRegrade}
                  disabled={streamingState.isStreaming}
                >
                  重新批改
                </Button>
              </Group>
            </Card>
          )}

          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text size="lg" fw={600} mb="md">
              题目详细分析
            </Text>

            <Accordion variant="separated">
              {(latestResult as GradingResult).questionResults.map(
                (question: QuestionResult, index: number) => (
                  <Accordion.Item key={question.id} value={question.id.toString()}>
                    <Accordion.Control>
                      <Group justify="space-between">
                        <Group gap="xs">
                          <ThemeIcon
                            color={question.isCorrect ? 'green' : 'red'}
                            variant="light"
                            size="sm"
                          >
                            {question.isCorrect ? <IconCheck size={12} /> : <IconX size={12} />}
                          </ThemeIcon>
                          <Text>第 {index + 1} 题</Text>
                          <Badge size="sm" variant="light">
                            {question.topic}
                          </Badge>
                        </Group>
                        <Text size="sm" c="dimmed">
                          {formatTime(question.timeSpent)}
                        </Text>
                      </Group>
                    </Accordion.Control>

                    <Accordion.Panel>
                      <Stack gap="md">
                        <div>
                          <Text fw={500} mb="xs">
                            题目
                          </Text>
                          <Text>{question.questionText}</Text>
                        </div>

                        <Grid>
                          <Grid.Col span={6}>
                            <Text fw={500} mb="xs">
                              您的答案
                            </Text>
                            <Highlight
                              highlight={question.isCorrect ? [] : [question.userAnswer]}
                              color={question.isCorrect ? 'green' : 'red'}
                            >
                              {question.userAnswer}
                            </Highlight>
                          </Grid.Col>
                          <Grid.Col span={6}>
                            <Text fw={500} mb="xs">
                              正确答案
                            </Text>
                            <Highlight highlight={[question.correctAnswer]} color="green">
                              {question.correctAnswer}
                            </Highlight>
                          </Grid.Col>
                        </Grid>

                        <Divider />

                        <div>
                          <Text fw={500} mb="xs">
                            解析
                          </Text>
                          <Text>{question.explanation}</Text>
                        </div>

                        {question.aiAnalysis && (
                          <Paper p="md" withBorder radius="md" bg="blue.0">
                            <Group gap="xs" mb="xs">
                              <IconBulb size={16} color="blue" />
                              <Text fw={500} c="blue">
                                AI 分析建议
                              </Text>
                            </Group>
                            <Text size="sm" mb="xs">
                              {question.aiAnalysis.suggestion}
                            </Text>
                            {question.aiAnalysis.relatedConcepts.length > 0 && (
                              <Group gap="xs">
                                <Text size="sm" fw={500}>
                                  相关概念:
                                </Text>
                                {question.aiAnalysis.relatedConcepts.map(
                                  (concept: string, idx: number) => (
                                    <Badge key={idx} size="sm" variant="light">
                                      {concept}
                                    </Badge>
                                  )
                                )}
                              </Group>
                            )}
                          </Paper>
                        )}
                      </Stack>
                    </Accordion.Panel>
                  </Accordion.Item>
                )
              )}
            </Accordion>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="history" pt="md">
          {historyLoading ? (
            <Center h={200}>
              <Loader />
            </Center>
          ) : (
            <Timeline active={-1} bulletSize={24} lineWidth={2}>
              {history?.results?.map((result: GradingResult) => (
                <Timeline.Item
                  key={result.id}
                  bullet={
                    <ThemeIcon color={getScoreColor(result.score)} variant="light" size={24}>
                      <IconStar size={12} />
                    </ThemeIcon>
                  }
                  title={getTypeLabel(result.type)}
                >
                  <Card shadow="sm" padding="md" radius="md" withBorder mt="xs">
                    <Group justify="space-between">
                      <div>
                        <Text fw={500}>分数: {result.score}</Text>
                        <Text size="sm" c="dimmed">
                          正确率: {(result.accuracy * 100).toFixed(1)}%
                        </Text>
                        <Text size="sm" c="dimmed">
                          {new Date(result.completedAt).toLocaleString()}
                        </Text>
                      </div>
                      <Button
                        variant="light"
                        size="sm"
                        rightSection={<IconChevronRight size={14} />}
                        onClick={() => {
                          notifications.show({
                            title: '功能开发中',
                            message: '详情查看功能正在开发中',
                            color: 'blue',
                          })
                        }}
                      >
                        查看详情
                      </Button>
                    </Group>
                  </Card>
                </Timeline.Item>
              )) || (
                <Alert icon={<IconAlertCircle size={16} />} title="暂无历史记录" color="gray">
                  您还没有完成任何训练。开始您的第一次训练吧！
                </Alert>
              )}
            </Timeline>
          )}
        </Tabs.Panel>
      </Tabs>
    </Container>
  )
}
