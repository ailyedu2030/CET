import React, { useState, useCallback } from 'react'
import {
  Card,
  Text,
  Button,
  Stack,
  Group,
  Select,
  MultiSelect,
  NumberInput,
  Textarea,
  Switch,
  Badge,
  Alert,
  Divider,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { useQuery, useMutation } from '@tanstack/react-query'
import { IconWand, IconEye, IconDownload, IconRefresh } from '@tabler/icons-react'
import {
  questionGenerationApi,
  type QuestionGenerationRequest,
  type GeneratedQuestion,
} from '../../api/questionGeneration'

interface QuestionGeneratorComponentProps {
  courseId?: number
  onQuestionsGenerated?: (questions: GeneratedQuestion[]) => void
  onError?: (error: Error) => void
}

export const QuestionGeneratorComponent: React.FC<QuestionGeneratorComponentProps> = ({
  courseId,
  onQuestionsGenerated,
  onError,
}) => {
  const [generatedQuestions, setGeneratedQuestions] = useState<GeneratedQuestion[]>([])
  const [previewData, setPreviewData] = useState<{
    estimated_count: number
    vocabulary_coverage: number
    hot_topics_available: string[]
    generation_time_estimate: string
  } | null>(null)

  // 表单管理
  const form = useForm<QuestionGenerationRequest>({
    initialValues: {
      course_id: courseId,
      vocabulary_level: 'intermediate',
      topic_keywords: [],
      question_types: ['reading'],
      difficulty_level: 'medium',
      count: 5,
      include_hot_topics: true,
      custom_requirements: '',
    },
    validate: {
      count: (value) => (value && value > 0 && value <= 50 ? null : '题目数量必须在1-50之间'),
    },
  })

  // 获取词汇库信息
  const { data: vocabularyInfo } = useQuery({
    queryKey: ['vocabulary-info', courseId],
    queryFn: () => courseId ? questionGenerationApi.getVocabularyInfo(courseId) : Promise.resolve(null),
    enabled: !!courseId,
  })

  // 获取热点话题
  const { data: hotTopics } = useQuery({
    queryKey: ['hot-topics'],
    queryFn: () => questionGenerationApi.getHotTopics({ limit: 20 }),
  })

  // 预览生成
  const previewMutation = useMutation({
    mutationFn: questionGenerationApi.previewGeneration,
    onSuccess: (data) => {
      setPreviewData(data)
      notifications.show({
        title: '预览生成',
        message: `预计生成 ${data.estimated_count} 道题目，词汇覆盖率 ${(data.vocabulary_coverage * 100).toFixed(1)}%`,
        color: 'blue',
      })
    },
    onError: (error) => {
      notifications.show({
        title: '预览失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 题目生成
  const generateMutation = useMutation({
    mutationFn: questionGenerationApi.generateQuestions,
    onSuccess: (data) => {
      setGeneratedQuestions(data.questions)
      if (onQuestionsGenerated) {
        onQuestionsGenerated(data.questions)
      }
      notifications.show({
        title: '生成成功',
        message: `成功生成 ${data.questions.length} 道题目`,
        color: 'green',
      })
    },
    onError: (error) => {
      if (onError) {
        onError(error instanceof Error ? error : new Error('题目生成失败'))
      }
      notifications.show({
        title: '生成失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 保存题目
  const saveMutation = useMutation({
    mutationFn: (questions: GeneratedQuestion[]) => 
      questionGenerationApi.saveGeneratedQuestions(questions),
    onSuccess: (data) => {
      notifications.show({
        title: '保存成功',
        message: `成功保存 ${data.saved_count} 道题目`,
        color: 'green',
      })
    },
    onError: (error) => {
      notifications.show({
        title: '保存失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handlePreview = useCallback(() => {
    const values = form.values
    if (form.validate().hasErrors) return
    previewMutation.mutate(values)
  }, [form, previewMutation])

  const handleGenerate = useCallback(() => {
    const values = form.values
    if (form.validate().hasErrors) return
    generateMutation.mutate(values)
  }, [form, generateMutation])

  const handleSave = useCallback(() => {
    if (generatedQuestions.length === 0) {
      notifications.show({
        title: '无题目可保存',
        message: '请先生成题目',
        color: 'yellow',
      })
      return
    }
    saveMutation.mutate(generatedQuestions)
  }, [generatedQuestions, saveMutation])

  const handleExport = useCallback(async () => {
    if (generatedQuestions.length === 0) return
    
    try {
      const questionIds = generatedQuestions.map(q => q.id)
      const blob = await questionGenerationApi.exportQuestions(questionIds, 'json')
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `generated-questions-${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      notifications.show({
        title: '导出成功',
        message: '题目已导出到本地',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '导出失败',
        message: '导出过程中发生错误',
        color: 'red',
      })
    }
  }, [generatedQuestions])

  // 题目类型选项
  const questionTypeOptions = [
    { value: 'reading', label: '阅读理解' },
    { value: 'listening', label: '听力理解' },
    { value: 'writing', label: '写作' },
    { value: 'translation', label: '翻译' },
  ]

  // 难度级别选项
  const difficultyOptions = [
    { value: 'easy', label: '简单' },
    { value: 'medium', label: '中等' },
    { value: 'hard', label: '困难' },
  ]

  // 词汇水平选项
  const vocabularyLevelOptions = [
    { value: 'basic', label: '基础' },
    { value: 'intermediate', label: '中级' },
    { value: 'advanced', label: '高级' },
  ]

  return (
    <Stack gap="lg">
      <Card withBorder padding="lg">
        <Stack gap="md">
          <Group justify="space-between" align="center">
            <Text fw={500} size="lg">
              智能题目生成器
            </Text>
            <Group gap="xs">
              {vocabularyInfo && (
                <Badge variant="light" color="blue">
                  词汇库: {vocabularyInfo.total_words} 词
                </Badge>
              )}
              {hotTopics && (
                <Badge variant="light" color="green">
                  热点: {hotTopics.length} 个
                </Badge>
              )}
            </Group>
          </Group>

          <form>
            <Stack gap="md">
              <Group grow>
                <Select
                  label="词汇水平"
                  placeholder="选择词汇水平"
                  data={vocabularyLevelOptions}
                  {...form.getInputProps('vocabulary_level')}
                />
                <Select
                  label="难度级别"
                  placeholder="选择难度级别"
                  data={difficultyOptions}
                  {...form.getInputProps('difficulty_level')}
                />
              </Group>

              <Group grow>
                <MultiSelect
                  label="题目类型"
                  placeholder="选择题目类型"
                  data={questionTypeOptions}
                  {...form.getInputProps('question_types')}
                />
                <NumberInput
                  label="生成数量"
                  placeholder="输入题目数量"
                  min={1}
                  max={50}
                  {...form.getInputProps('count')}
                />
              </Group>

              {hotTopics && (
                <MultiSelect
                  label="热点话题关键词"
                  placeholder="选择热点话题"
                  data={hotTopics.map(topic => ({
                    value: topic.title,
                    label: `${topic.title} (${topic.category})`,
                  }))}
                  {...form.getInputProps('topic_keywords')}
                />
              )}

              <Switch
                label="包含热点话题"
                description="自动融入当前热点话题到题目中"
                {...form.getInputProps('include_hot_topics', { type: 'checkbox' })}
              />

              <Textarea
                label="自定义要求"
                placeholder="输入特殊要求或偏好..."
                autosize
                minRows={2}
                maxRows={4}
                {...form.getInputProps('custom_requirements')}
              />
            </Stack>
          </form>

          <Divider />

          <Group justify="space-between">
            <Group gap="xs">
              <Button
                leftSection={<IconEye size={16} />}
                variant="outline"
                onClick={handlePreview}
                loading={previewMutation.isPending}
              >
                预览生成
              </Button>
              <Button
                leftSection={<IconWand size={16} />}
                onClick={handleGenerate}
                loading={generateMutation.isPending}
              >
                开始生成
              </Button>
            </Group>

            {generatedQuestions.length > 0 && (
              <Group gap="xs">
                <Button
                  variant="outline"
                  onClick={handleSave}
                  loading={saveMutation.isPending}
                >
                  保存题目
                </Button>
                <Tooltip label="导出题目">
                  <ActionIcon variant="outline" onClick={handleExport}>
                    <IconDownload size={16} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            )}
          </Group>

          {previewData && (
            <Alert color="blue" title="生成预览">
              <Stack gap="xs">
                <Text size="sm">
                  预计生成 <strong>{previewData.estimated_count}</strong> 道题目
                </Text>
                <Text size="sm">
                  词汇覆盖率: <strong>{(previewData.vocabulary_coverage * 100).toFixed(1)}%</strong>
                </Text>
                <Text size="sm">
                  预计用时: <strong>{previewData.generation_time_estimate}</strong>
                </Text>
                {previewData.hot_topics_available.length > 0 && (
                  <Text size="sm">
                    可用热点: {previewData.hot_topics_available.join(', ')}
                  </Text>
                )}
              </Stack>
            </Alert>
          )}
        </Stack>
      </Card>

      {generatedQuestions.length > 0 && (
        <Card withBorder padding="lg">
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Text fw={500} size="lg">
                生成结果 ({generatedQuestions.length} 道题目)
              </Text>
              <ActionIcon variant="outline" onClick={() => setGeneratedQuestions([])}>
                <IconRefresh size={16} />
              </ActionIcon>
            </Group>

            <Stack gap="sm">
              {generatedQuestions.map((question, index) => (
                <Card key={question.id} withBorder padding="sm">
                  <Stack gap="xs">
                    <Group justify="space-between" align="flex-start">
                      <Text fw={500} size="sm">
                        {index + 1}. {question.title}
                      </Text>
                      <Group gap="xs">
                        <Badge size="xs" color="blue">
                          {question.type}
                        </Badge>
                        <Badge size="xs" color="green">
                          难度: {question.difficulty_score}/10
                        </Badge>
                      </Group>
                    </Group>
                    <Text size="sm" c="dimmed" lineClamp={2}>
                      {question.content}
                    </Text>
                    {question.vocabulary_used.length > 0 && (
                      <Group gap="xs">
                        <Text size="xs" c="dimmed">词汇:</Text>
                        {question.vocabulary_used.slice(0, 5).map(word => (
                          <Badge key={word} size="xs" variant="outline">
                            {word}
                          </Badge>
                        ))}
                        {question.vocabulary_used.length > 5 && (
                          <Text size="xs" c="dimmed">
                            +{question.vocabulary_used.length - 5} 更多
                          </Text>
                        )}
                      </Group>
                    )}
                  </Stack>
                </Card>
              ))}
            </Stack>
          </Stack>
        </Card>
      )}
    </Stack>
  )
}
