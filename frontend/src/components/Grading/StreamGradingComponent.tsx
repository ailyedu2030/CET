import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  Card,
  Text,
  Button,
  Stack,
  Group,
  Alert,
  Progress,
  Badge,
  Textarea,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconCheck, IconX, IconRefresh, IconCopy } from '@tabler/icons-react'
import { gradingApi, type StreamGradingRequest, type UserAnswer, type GradingContext } from '../../api/grading'

// 常量定义
const STREAM_CONFIG = {
  CHUNK_SIZE: 1024,
  RESPONSE_INTERVAL_MS: 100, // 100ms 响应间隔，满足 <200ms 要求
} as const

const PROGRESS = {
  COMPLETE: 100,
  INITIAL: 0,
} as const

const RESPONSE_TIME = {
  THRESHOLD_MS: 200, // 响应时间阈值
} as const

const UI_CONFIG = {
  MAX_STREAM_HEIGHT: 200, // 流式输出最大高度
} as const

// 批改结果类型
interface GradingResult {
  score: number
  max_score: number
  feedback: string
  suggestions: string[]
  [key: string]: unknown
}

interface StreamGradingComponentProps {
  questionId: number
  userAnswer: UserAnswer
  context?: GradingContext
  onGradingComplete?: (result: GradingResult) => void
  onError?: (error: Error) => void
}

interface StreamChunk {
  type: 'progress' | 'result' | 'error' | 'complete'
  data: {
    progress?: number
    message?: string
    result?: GradingResult
    [key: string]: unknown
  }
  timestamp: number
}

export const StreamGradingComponent: React.FC<StreamGradingComponentProps> = ({
  questionId,
  userAnswer,
  context,
  onGradingComplete,
  onError,
}) => {
  const [isGrading, setIsGrading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [streamChunks, setStreamChunks] = useState<StreamChunk[]>([])
  const [finalResult, setFinalResult] = useState<GradingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [responseTime, setResponseTime] = useState<number>(0)
  
  const abortControllerRef = useRef<AbortController | null>(null)
  const startTimeRef = useRef<number>(0)

  const startStreamGrading = useCallback(async () => {
    if (isGrading) return

    setIsGrading(true)
    setProgress(0)
    setStreamChunks([])
    setFinalResult(null)
    setError(null)
    startTimeRef.current = Date.now()

    // 创建新的 AbortController
    abortControllerRef.current = new AbortController()

    try {
      const request: StreamGradingRequest = {
        question_id: questionId,
        user_answer: userAnswer,
        context,
        stream_config: {
          chunk_size: STREAM_CONFIG.CHUNK_SIZE,
          response_interval_ms: STREAM_CONFIG.RESPONSE_INTERVAL_MS,
        },
      }

      const stream = await gradingApi.gradeStream(request)
      const reader = stream.getReader()
      const decoder = new TextDecoder()

      let buffer = ''

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        // 检查是否被取消
        if (abortControllerRef.current?.signal.aborted) {
          break
        }

        buffer += decoder.decode(value, { stream: true })
        
        // 处理完整的 JSON 行
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留不完整的行

        for (const line of lines) {
          if (line.trim()) {
            try {
              const chunk: StreamChunk = JSON.parse(line)
              chunk.timestamp = Date.now() - startTimeRef.current
              
              setStreamChunks(prev => [...prev, chunk])

              // 更新进度
              if (chunk.type === 'progress') {
                setProgress(chunk.data.progress || 0)
              } else if (chunk.type === 'result') {
                if (chunk.data.result) {
                  setFinalResult(chunk.data.result)
                }
                setProgress(PROGRESS.COMPLETE)
              } else if (chunk.type === 'error') {
                throw new Error(chunk.data.message || '批改过程中发生错误')
              } else if (chunk.type === 'complete') {
                setProgress(PROGRESS.COMPLETE)
                setResponseTime(Date.now() - startTimeRef.current)
                break
              }
            } catch (parseError) {
              // 静默处理解析错误
            }
          }
        }
      }

      if (finalResult && onGradingComplete) {
        onGradingComplete(finalResult)
      }

      notifications.show({
        title: '批改完成',
        message: `批改完成，响应时间：${responseTime}ms`,
        color: 'green',
        icon: <IconCheck size={16} />,
      })

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '批改失败'
      setError(errorMessage)
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage))
      }

      notifications.show({
        title: '批改失败',
        message: errorMessage,
        color: 'red',
        icon: <IconX size={16} />,
      })
    } finally {
      setIsGrading(false)
      abortControllerRef.current = null
    }
  }, [questionId, userAnswer, context, onGradingComplete, onError, isGrading])

  const cancelGrading = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsGrading(false)
      notifications.show({
        title: '批改已取消',
        message: '流式批改已被用户取消',
        color: 'yellow',
      })
    }
  }, [])

  const copyResult = useCallback(async () => {
    if (finalResult) {
      try {
        await navigator.clipboard.writeText(JSON.stringify(finalResult, null, 2))
        notifications.show({
          title: '已复制',
          message: '批改结果已复制到剪贴板',
          color: 'blue',
          icon: <IconCopy size={16} />,
        })
      } catch (error) {
        notifications.show({
          title: '复制失败',
          message: '无法访问剪贴板，请手动复制',
          color: 'red',
        })
      }
    }
  }, [finalResult])

  // 组件卸载时清理资源
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return (
    <Card withBorder padding="lg">
      <Stack gap="md">
        <Group justify="space-between" align="center">
          <Text fw={500} size="lg">
            流式智能批改
          </Text>
          <Group gap="xs">
            {responseTime > 0 && (
              <Badge color={responseTime < RESPONSE_TIME.THRESHOLD_MS ? 'green' : 'yellow'} variant="light">
                {responseTime}ms
              </Badge>
            )}
            {finalResult && (
              <Tooltip label="复制结果">
                <ActionIcon variant="light" onClick={copyResult}>
                  <IconCopy size={16} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        </Group>

        {error && (
          <Alert color="red" title="批改错误" icon={<IconX size={16} />}>
            {error}
          </Alert>
        )}

        <Group justify="space-between" align="center">
          <Button
            onClick={startStreamGrading}
            loading={isGrading}
            disabled={isGrading}
            leftSection={<IconCheck size={16} />}
          >
            {isGrading ? '批改中...' : '开始流式批改'}
          </Button>

          {isGrading && (
            <Button
              variant="outline"
              color="red"
              onClick={cancelGrading}
              leftSection={<IconX size={16} />}
            >
              取消批改
            </Button>
          )}

          {!isGrading && finalResult && (
            <Button
              variant="outline"
              onClick={startStreamGrading}
              leftSection={<IconRefresh size={16} />}
            >
              重新批改
            </Button>
          )}
        </Group>

        {isGrading && (
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">
                批改进度
              </Text>
              <Text size="sm" fw={500}>
                {progress.toFixed(1)}%
              </Text>
            </Group>
            <Progress value={progress} animated />
          </Stack>
        )}

        {streamChunks.length > 0 && (
          <Stack gap="xs">
            <Text size="sm" fw={500}>
              实时流式输出 ({streamChunks.length} 个数据块)
            </Text>
            <Card withBorder padding="sm" style={{ maxHeight: UI_CONFIG.MAX_STREAM_HEIGHT, overflowY: 'auto' }}>
              <Stack gap="xs">
                {streamChunks.map((chunk, index) => (
                  <Group key={index} justify="space-between" align="flex-start">
                    <Badge
                      size="xs"
                      color={
                        chunk.type === 'progress' ? 'blue' :
                        chunk.type === 'result' ? 'green' :
                        chunk.type === 'error' ? 'red' : 'gray'
                      }
                    >
                      {chunk.type}
                    </Badge>
                    <Text size="xs" style={{ flex: 1, marginLeft: 8 }}>
                      {typeof chunk.data === 'string' ? chunk.data : JSON.stringify(chunk.data)}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {chunk.timestamp}ms
                    </Text>
                  </Group>
                ))}
              </Stack>
            </Card>
          </Stack>
        )}

        {finalResult && (
          <Stack gap="xs">
            <Text size="sm" fw={500}>
              最终批改结果
            </Text>
            <Textarea
              value={JSON.stringify(finalResult, null, 2)}
              readOnly
              autosize
              minRows={4}
              maxRows={10}
            />
          </Stack>
        )}
      </Stack>
    </Card>
  )
}
