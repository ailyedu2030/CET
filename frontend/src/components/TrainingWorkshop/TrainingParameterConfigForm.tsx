/**
 * 训练参数配置表单组件 - 需求15实现
 * 复用现有Mantine组件，遵循现有表单模式
 */
import { useState, useEffect } from 'react'
import {
  Stack,
  Group,
  Text,
  NumberInput,
  Slider,
  MultiSelect,
  Card,
  Button,
  Alert,
  Progress,
  Grid,
  Divider,
  Badge,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import {
  IconBrain,
  IconTarget,
  IconBooks,
  IconAdjustments,
  IconCheck,
  IconAlertTriangle,
  IconRefresh,
} from '@tabler/icons-react'

import { trainingWorkshopApi, TrainingParameterConfig } from '@/api/trainingWorkshop'
import { DifficultyLevel, TrainingType } from '../../types/training'

interface TrainingParameterConfigFormProps {
  initialConfig?: TrainingParameterConfig
  onSubmit: (config: TrainingParameterConfig) => void
  onCancel?: () => void
  loading?: boolean
}

export function TrainingParameterConfigForm({
  initialConfig,
  onSubmit,
  onCancel,
  loading = false,
}: TrainingParameterConfigFormProps): JSX.Element {
  const [knowledgePointOptions] = useState([
    { value: '基础语法', label: '基础语法' },
    { value: '高级语法', label: '高级语法' },
    { value: '常用词汇', label: '常用词汇' },
    { value: '学术词汇', label: '学术词汇' },
    { value: '听力技巧', label: '听力技巧' },
    { value: '阅读理解', label: '阅读理解' },
    { value: '写作技巧', label: '写作技巧' },
    { value: '翻译技巧', label: '翻译技巧' },
  ])

  const [vocabularyLibraryOptions] = useState([
    { value: '1', label: '四级核心词汇库' },
    { value: '2', label: '四级扩展词汇库' },
    { value: '3', label: '学术英语词汇库' },
    { value: '4', label: '商务英语词汇库' },
  ])

  const form = useForm<TrainingParameterConfig>({
    initialValues: initialConfig || trainingWorkshopApi.getDefaultParameterConfig(),
    validate: {
      knowledge_points: value => (value.length === 0 ? '请至少选择一个知识点' : null),
      vocabulary_library_ids: value => (value.length === 0 ? '请至少选择一个词汇库' : null),
      hot_topics_fusion_rate: value =>
        value < 0 || value > 100 ? '热点融合度必须在0-100%之间' : null,
      lesson_plan_connection_rate: value =>
        value < 0 || value > 100 ? '教案衔接度必须在0-100%之间' : null,
    },
  })

  // 计算难度分布总和
  const difficultyTotal = Object.values(form.values.difficulty_distribution).reduce(
    (sum, val) => sum + val,
    0
  )

  // 计算题目总数
  const questionTotal = Object.values(form.values.question_count_per_type).reduce(
    (sum, val) => sum + val,
    0
  )

  // 验证难度分布
  useEffect(() => {
    if (difficultyTotal !== 100) {
      form.setFieldError('difficulty_distribution', '难度分布总和必须为100%')
    } else {
      form.clearFieldError('difficulty_distribution')
    }
  }, [difficultyTotal, form])

  const handleSubmit = (values: TrainingParameterConfig) => {
    // 验证配置
    const errors = trainingWorkshopApi.validateParameterConfig(values)
    if (errors.length > 0) {
      notifications.show({
        title: '配置验证失败',
        message: errors.join(', '),
        color: 'red',
      })
      return
    }

    onSubmit(values)
  }

  const handleReset = () => {
    form.setValues(trainingWorkshopApi.getDefaultParameterConfig())
    notifications.show({
      title: '已重置',
      message: '参数配置已重置为默认值',
      color: 'blue',
    })
  }

  const getDifficultyColor = (level: DifficultyLevel) => {
    switch (level) {
      case DifficultyLevel.BEGINNER:
        return 'green'
      case DifficultyLevel.ELEMENTARY:
        return 'blue'
      case DifficultyLevel.INTERMEDIATE:
        return 'yellow'
      case DifficultyLevel.ADVANCED:
        return 'orange'
      case DifficultyLevel.EXPERT:
        return 'red'
      default:
        return 'gray'
    }
  }

  const getDifficultyLabel = (level: DifficultyLevel) => {
    switch (level) {
      case DifficultyLevel.BEGINNER:
        return '入门'
      case DifficultyLevel.ELEMENTARY:
        return '初级'
      case DifficultyLevel.INTERMEDIATE:
        return '中级'
      case DifficultyLevel.ADVANCED:
        return '高级'
      case DifficultyLevel.EXPERT:
        return '专家'
      default:
        return level
    }
  }

  const getTrainingTypeLabel = (type: TrainingType) => {
    switch (type) {
      case TrainingType.VOCABULARY:
        return '词汇'
      case TrainingType.LISTENING:
        return '听力'
      case TrainingType.READING:
        return '阅读'
      case TrainingType.WRITING:
        return '写作'
      case TrainingType.TRANSLATION:
        return '翻译'
      case TrainingType.GRAMMAR:
        return '语法'
      case TrainingType.SPEAKING:
        return '口语'
      default:
        return type
    }
  }

  return (
    <form onSubmit={form.onSubmit(handleSubmit)}>
      <Stack gap="lg">
        {/* 基础配置 */}
        <Card withBorder p="md">
          <Group mb="md">
            <IconBooks size={20} />
            <Text fw={500}>基础配置</Text>
          </Group>

          <Stack gap="md">
            <MultiSelect
              label="关联知识点"
              placeholder="选择要训练的知识点"
              data={knowledgePointOptions}
              searchable
              clearable
              required
              {...form.getInputProps('knowledge_points')}
            />

            <MultiSelect
              label="词汇库选择"
              placeholder="选择词汇库"
              data={vocabularyLibraryOptions}
              searchable
              clearable
              required
              {...form.getInputProps('vocabulary_library_ids')}
            />
          </Stack>
        </Card>

        {/* 融合度配置 */}
        <Card withBorder p="md">
          <Group mb="md">
            <IconAdjustments size={20} />
            <Text fw={500}>融合度配置</Text>
          </Group>

          <Stack gap="lg">
            <div>
              <Group justify="space-between" mb="xs">
                <Text size="sm" fw={500}>
                  热点融合度
                </Text>
                <Badge color="blue">{form.values.hot_topics_fusion_rate}%</Badge>
              </Group>
              <Slider
                min={0}
                max={100}
                step={5}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 25, label: '25%' },
                  { value: 50, label: '50%' },
                  { value: 75, label: '75%' },
                  { value: 100, label: '100%' },
                ]}
                {...form.getInputProps('hot_topics_fusion_rate')}
              />
              <Text size="xs" c="dimmed" mt="xs">
                控制题目中融入时事热点的程度
              </Text>
            </div>

            <div>
              <Group justify="space-between" mb="xs">
                <Text size="sm" fw={500}>
                  教案衔接度
                </Text>
                <Badge color="green">{form.values.lesson_plan_connection_rate}%</Badge>
              </Group>
              <Slider
                min={0}
                max={100}
                step={5}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 25, label: '25%' },
                  { value: 50, label: '50%' },
                  { value: 75, label: '75%' },
                  { value: 100, label: '100%' },
                ]}
                {...form.getInputProps('lesson_plan_connection_rate')}
              />
              <Text size="xs" c="dimmed" mt="xs">
                控制题目与教学计划的关联程度
              </Text>
            </div>
          </Stack>
        </Card>

        {/* 难度分布配置 */}
        <Card withBorder p="md">
          <Group justify="space-between" mb="md">
            <Group>
              <IconTarget size={20} />
              <Text fw={500}>难度分布配置</Text>
            </Group>
            <Group>
              <Text size="sm" c={difficultyTotal === 100 ? 'green' : 'red'}>
                总计: {difficultyTotal}%
              </Text>
              {difficultyTotal === 100 ? (
                <IconCheck size={16} color="green" />
              ) : (
                <IconAlertTriangle size={16} color="red" />
              )}
            </Group>
          </Group>

          <Stack gap="md">
            {Object.entries(form.values.difficulty_distribution).map(([level, percentage]) => (
              <div key={level}>
                <Group justify="space-between" mb="xs">
                  <Badge color={getDifficultyColor(level as DifficultyLevel)} variant="light">
                    {getDifficultyLabel(level as DifficultyLevel)}
                  </Badge>
                  <NumberInput
                    w={80}
                    min={0}
                    max={100}
                    suffix="%"
                    value={percentage}
                    onChange={value => {
                      form.setFieldValue(`difficulty_distribution.${level}`, Number(value) || 0)
                    }}
                  />
                </Group>
                <Progress
                  value={percentage}
                  color={getDifficultyColor(level as DifficultyLevel)}
                  size="sm"
                />
              </div>
            ))}
          </Stack>

          {difficultyTotal !== 100 && (
            <Alert icon={<IconAlertTriangle size={16} />} color="red" mt="md">
              难度分布总和必须为100%，当前为{difficultyTotal}%
            </Alert>
          )}
        </Card>

        {/* 题型数量配置 */}
        <Card withBorder p="md">
          <Group justify="space-between" mb="md">
            <Group>
              <IconBrain size={20} />
              <Text fw={500}>题型数量配置</Text>
            </Group>
            <Text size="sm" c="blue">
              总题数: {questionTotal}
            </Text>
          </Group>

          <Grid>
            {Object.entries(form.values.question_count_per_type).map(([type, count]) => (
              <Grid.Col span={6} key={type}>
                <NumberInput
                  label={getTrainingTypeLabel(type as TrainingType)}
                  min={0}
                  max={50}
                  value={count}
                  onChange={value => {
                    form.setFieldValue(`question_count_per_type.${type}`, Number(value) || 0)
                  }}
                />
              </Grid.Col>
            ))}
          </Grid>
        </Card>

        <Divider />

        {/* 操作按钮 */}
        <Group justify="space-between">
          <Group>
            <Tooltip label="重置为默认配置">
              <ActionIcon variant="light" onClick={handleReset}>
                <IconRefresh size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>

          <Group>
            {onCancel && (
              <Button variant="light" onClick={onCancel}>
                取消
              </Button>
            )}
            <Button
              type="submit"
              loading={loading}
              disabled={difficultyTotal !== 100}
              leftSection={<IconCheck size={16} />}
            >
              确认配置
            </Button>
          </Group>
        </Group>
      </Stack>
    </form>
  )
}
