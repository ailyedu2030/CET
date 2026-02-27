import React, { useCallback, useEffect } from 'react'
import {
  Card,
  Text,
  Badge,
  Group,
  Stack,
  Alert,
  Progress,
  ActionIcon,
  Tooltip,
  Button,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { IconCheck, IconX, IconAlertTriangle, IconBookmark, IconRefresh } from '@tabler/icons-react'
import {
  errorReinforcementApi,
  type AutoCollectErrorRequest,
  type AutoCollectErrorResponse,
  type AnswerData,
} from '../../api/errorReinforcement'

interface AutoErrorCollectionComponentProps {
  questionId: number
  userAnswer: AnswerData
  correctAnswer: AnswerData
  gradingResult: {
    is_correct: boolean
    score: number
    max_score: number
    detailed_feedback: string
    improvement_suggestions: string[]
  }
  context?: {
    training_session_id?: number
    attempt_count: number
    time_spent: number
  }
  onCollectionComplete?: (result: AutoCollectErrorResponse) => void
  autoTrigger?: boolean // 是否自动触发归集
}

export const AutoErrorCollectionComponent: React.FC<AutoErrorCollectionComponentProps> = ({
  questionId,
  userAnswer,
  correctAnswer,
  gradingResult,
  context,
  onCollectionComplete,
  autoTrigger = true,
}) => {
  const queryClient = useQueryClient()

  // 自动归集错题
  const collectErrorMutation = useMutation({
    mutationFn: errorReinforcementApi.autoCollectError,
    onSuccess: (result) => {
      if (result.collected) {
        notifications.show({
          title: '错题已自动归集',
          message: `已添加到错题本，发现 ${result.similar_errors_found} 个相似错题`,
          color: 'blue',
          icon: <IconBookmark size={16} />,
        })
      } else {
        notifications.show({
          title: '未归集错题',
          message: result.reason,
          color: 'gray',
        })
      }

      if (onCollectionComplete) {
        onCollectionComplete(result)
      }

      // 刷新错题相关查询
      queryClient.invalidateQueries({ queryKey: ['error-questions'] })
      queryClient.invalidateQueries({ queryKey: ['error-stats'] })
    },
    onError: (error) => {
      notifications.show({
        title: '错题归集失败',
        message: error.message,
        color: 'red',
        icon: <IconX size={16} />,
      })
    },
  })

  // 手动触发错题归集
  const handleManualCollect = useCallback(() => {
    if (!gradingResult || gradingResult.is_correct) {
      notifications.show({
        title: '无需归集',
        message: '该题目回答正确，无需归集到错题本',
        color: 'yellow',
      })
      return
    }

    const request: AutoCollectErrorRequest = {
      question_id: questionId,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      grading_result: gradingResult,
      error_analysis: {
        error_type: analyzeErrorType(userAnswer, correctAnswer),
        error_category: categorizeError(gradingResult),
        knowledge_gaps: extractKnowledgeGaps(gradingResult.improvement_suggestions),
        difficulty_level: calculateDifficultyLevel(gradingResult.score, gradingResult.max_score),
      },
      context: {
        training_session_id: context?.training_session_id,
        attempt_count: context?.attempt_count || 1,
        time_spent: context?.time_spent || 0,
        timestamp: new Date().toISOString(),
      },
    }

    collectErrorMutation.mutate(request)
  }, [questionId, userAnswer, correctAnswer, gradingResult, context, collectErrorMutation])

  // 自动触发归集（当答题错误时）
  useEffect(() => {
    if (autoTrigger && gradingResult && !gradingResult.is_correct && !collectErrorMutation.isPending) {
      // 延迟一点时间，让用户看到批改结果
      const timer = setTimeout(() => {
        handleManualCollect()
      }, 1000)

      return () => clearTimeout(timer)
    }
    // 如果条件不满足，返回undefined（可选的清理函数）
    return undefined
  }, [autoTrigger, gradingResult, handleManualCollect, collectErrorMutation.isPending])

  // 分析错误类型
  const analyzeErrorType = (userAns: AnswerData, correctAns: AnswerData): string => {
    // 简单的错误类型分析逻辑
    if (typeof userAns['text'] === 'string' && typeof correctAns['text'] === 'string') {
      const userText = userAns['text'].toLowerCase()
      const correctText = correctAns['text'].toLowerCase()

      if (userText.length < correctText.length * 0.5) {
        return 'incomplete_answer'
      } else if (userText.includes(correctText.substring(0, correctText.length / 2))) {
        return 'partial_understanding'
      } else {
        return 'conceptual_error'
      }
    }
    return 'unknown_error'
  }

  // 错误分类
  const categorizeError = (result: { score: number; max_score: number }): string => {
    const score = result.score / result.max_score
    if (score < 0.3) return 'major_error'
    if (score < 0.7) return 'minor_error'
    return 'slight_error'
  }

  // 提取知识缺口
  const extractKnowledgeGaps = (suggestions: string[]): string[] => {
    return suggestions.map(suggestion => {
      // 简单的关键词提取
      if (suggestion.includes('语法')) return 'grammar'
      if (suggestion.includes('词汇')) return 'vocabulary'
      if (suggestion.includes('理解')) return 'comprehension'
      if (suggestion.includes('逻辑')) return 'logic'
      return 'general'
    })
  }

  // 计算难度级别
  const calculateDifficultyLevel = (score: number, maxScore: number): string => {
    const percentage = score / maxScore
    if (percentage < 0.3) return 'hard'
    if (percentage < 0.7) return 'medium'
    return 'easy'
  }

  // 如果答题正确，不显示组件
  if (gradingResult?.is_correct) {
    return null
  }

  return (
    <Card withBorder padding="md" style={{ borderColor: '#ffa8a8' }}>
      <Stack gap="sm">
        <Group justify="space-between" align="center">
          <Group gap="xs">
            <IconAlertTriangle size={20} color="#fa5252" />
            <Text fw={500} c="red">
              错题检测
            </Text>
          </Group>
          <Badge color="red" variant="light">
            答题错误
          </Badge>
        </Group>

        {collectErrorMutation.isPending && (
          <Alert color="blue" title="正在归集错题...">
            <Stack gap="xs">
              <Progress value={50} animated />
              <Text size="sm">
                正在分析错误类型并归集到错题本...
              </Text>
            </Stack>
          </Alert>
        )}

        {collectErrorMutation.data && (
          <Alert 
            color={collectErrorMutation.data.collected ? "green" : "gray"} 
            title={collectErrorMutation.data.collected ? "归集成功" : "未归集"}
            icon={collectErrorMutation.data.collected ? <IconCheck size={16} /> : <IconX size={16} />}
          >
            <Stack gap="xs">
              <Text size="sm">
                {collectErrorMutation.data.reason}
              </Text>
              {collectErrorMutation.data.collected && (
                <>
                  <Text size="sm">
                    发现 {collectErrorMutation.data.similar_errors_found} 个相似错题
                  </Text>
                  {collectErrorMutation.data.recommended_practice.immediate && (
                    <Text size="sm" fw={500} c="blue">
                      建议立即进行针对性练习
                    </Text>
                  )}
                </>
              )}
            </Stack>
          </Alert>
        )}

        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            错题将自动归集到错题本，用于后续强化练习
          </Text>
          <Group gap="xs">
            {!autoTrigger && (
              <Button
                size="xs"
                variant="outline"
                color="red"
                onClick={handleManualCollect}
                loading={collectErrorMutation.isPending}
                leftSection={<IconBookmark size={14} />}
              >
                手动归集
              </Button>
            )}
            {collectErrorMutation.data && (
              <Tooltip label="重新归集">
                <ActionIcon
                  variant="outline"
                  size="sm"
                  onClick={handleManualCollect}
                  loading={collectErrorMutation.isPending}
                >
                  <IconRefresh size={14} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        </Group>
      </Stack>
    </Card>
  )
}
