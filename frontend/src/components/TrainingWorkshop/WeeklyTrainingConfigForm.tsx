/**
 * 周训练配置表单组件 - 需求15实现
 * 复用现有表单组件和验证模式
 */
import { useState } from 'react'
import {
  Stack,
  Group,
  Text,
  NumberInput,
  Switch,
  MultiSelect,
  Card,
  Button,
  Alert,
  Tabs,
  TagsInput,
  Select,
  Divider,
  Badge,
  Grid,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { DateTimePicker } from '@mantine/dates'
import {
  IconBook,
  IconPencil,
  IconCalendarWeek,
  IconTarget,
  IconClock,
  IconCheck,
  IconAlertTriangle,
} from '@tabler/icons-react'

import { WeeklyTrainingRequest, WeeklyTrainingConfig } from '@/api/trainingWorkshop'

interface WeeklyTrainingConfigFormProps {
  onSubmit: (data: WeeklyTrainingRequest) => void
  onCancel?: () => void
  loading?: boolean
  classId?: number
}

export function WeeklyTrainingConfigForm({
  onSubmit,
  onCancel,
  loading = false,
  classId,
}: WeeklyTrainingConfigFormProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('basic')

  const form = useForm<WeeklyTrainingRequest>({
    initialValues: {
      class_id: classId || 0,
      week_config: {
        week_number: 1,
        reading_config: {
          topic_count: 3,
          questions_per_topic: 5,
          syllabus_relevance_rate: 80,
          topics: [],
        },
        writing_config: {
          writing_types: ['议论文'],
          cet4_standard_embedded: true,
          topic_sources: ['时事热点', '校园生活'],
        },
      },
      publish_type: 'immediate',
      scheduled_time: undefined,
    },
    validate: {
      class_id: value => (value <= 0 ? '请选择班级' : null),
      week_config: {
        week_number: value => {
          if (value < 1 || value > 52) return '周次必须在1-52之间'
          return null
        },
      },
      scheduled_time: (value, values) => {
        if (values.publish_type === 'scheduled' && !value) {
          return '定时发布必须选择发布时间'
        }
        if (values.publish_type === 'scheduled' && value) {
          const dateValue =
            (value as any) instanceof Date
              ? (value as unknown as Date)
              : new Date(value as unknown as string)
          if (dateValue <= new Date()) {
            return '发布时间必须晚于当前时间'
          }
        }
        return null
      },
    },
  })

  const [readingEnabled, setReadingEnabled] = useState(true)
  const [writingEnabled, setWritingEnabled] = useState(true)

  const topicOptions = [
    '科技发展',
    '环境保护',
    '教育改革',
    '文化交流',
    '健康生活',
    '经济发展',
    '社会问题',
    '国际关系',
  ]

  const writingTypeOptions = [
    { value: '议论文', label: '议论文' },
    { value: '说明文', label: '说明文' },
    { value: '记叙文', label: '记叙文' },
    { value: '应用文', label: '应用文' },
  ]

  const topicSourceOptions = [
    { value: '时事热点', label: '时事热点' },
    { value: '校园生活', label: '校园生活' },
    { value: '社会现象', label: '社会现象' },
    { value: '文化话题', label: '文化话题' },
    { value: '科技前沿', label: '科技前沿' },
  ]

  const handleSubmit = (values: WeeklyTrainingRequest) => {
    // 构建最终配置
    const weekConfig: WeeklyTrainingConfig = {
      week_number: values.week_config.week_number,
    }

    if (readingEnabled && values.week_config.reading_config) {
      weekConfig.reading_config = values.week_config.reading_config
    }

    if (writingEnabled && values.week_config.writing_config) {
      weekConfig.writing_config = values.week_config.writing_config
    }

    const finalData: WeeklyTrainingRequest = {
      ...values,
      week_config: weekConfig,
    }

    onSubmit(finalData)
  }

  const getEstimatedQuestions = () => {
    let total = 0
    if (readingEnabled && form.values.week_config.reading_config) {
      const { topic_count, questions_per_topic } = form.values.week_config.reading_config
      total += topic_count * questions_per_topic
    }
    if (writingEnabled && form.values.week_config.writing_config) {
      total += form.values.week_config.writing_config.writing_types.length
    }
    return total
  }

  return (
    <form onSubmit={form.onSubmit(handleSubmit)}>
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'basic')}>
        <Tabs.List>
          <Tabs.Tab value="basic" leftSection={<IconCalendarWeek size={16} />}>
            基本设置
          </Tabs.Tab>
          <Tabs.Tab value="reading" leftSection={<IconBook size={16} />}>
            阅读理解
          </Tabs.Tab>
          <Tabs.Tab value="writing" leftSection={<IconPencil size={16} />}>
            写作训练
          </Tabs.Tab>
          <Tabs.Tab value="publish" leftSection={<IconClock size={16} />}>
            发布设置
          </Tabs.Tab>
        </Tabs.List>

        {/* 基本设置 */}
        <Tabs.Panel value="basic" pt="lg">
          <Stack gap="md">
            <Alert icon={<IconTarget size={16} />} color="blue">
              周训练配置将自动生成符合四级考试要求的训练题目，确保考纲关联度≥80%
            </Alert>

            <NumberInput
              label="训练周次"
              placeholder="请输入周次"
              min={1}
              max={52}
              required
              {...form.getInputProps('week_config.week_number')}
            />

            <Card withBorder p="md">
              <Text fw={500} mb="md">
                训练模块选择
              </Text>
              <Stack gap="md">
                <Group justify="space-between">
                  <div>
                    <Text size="sm" fw={500}>
                      阅读理解训练
                    </Text>
                    <Text size="xs" c="dimmed">
                      包含多主题阅读理解题目
                    </Text>
                  </div>
                  <Switch
                    checked={readingEnabled}
                    onChange={event => setReadingEnabled(event.currentTarget.checked)}
                  />
                </Group>

                <Group justify="space-between">
                  <div>
                    <Text size="sm" fw={500}>
                      写作训练
                    </Text>
                    <Text size="xs" c="dimmed">
                      包含四级标准写作题目
                    </Text>
                  </div>
                  <Switch
                    checked={writingEnabled}
                    onChange={event => setWritingEnabled(event.currentTarget.checked)}
                  />
                </Group>
              </Stack>
            </Card>

            <Card withBorder p="md">
              <Group justify="space-between">
                <Text fw={500}>预估题目数量</Text>
                <Badge size="lg" color="blue">
                  {getEstimatedQuestions()} 题
                </Badge>
              </Group>
            </Card>
          </Stack>
        </Tabs.Panel>

        {/* 阅读理解配置 */}
        <Tabs.Panel value="reading" pt="lg">
          <Stack gap="md">
            {!readingEnabled ? (
              <Alert icon={<IconAlertTriangle size={16} />} color="yellow">
                阅读理解训练已禁用，请在基本设置中启用
              </Alert>
            ) : (
              <>
                <Alert icon={<IconTarget size={16} />} color="green">
                  阅读理解将确保考纲关联度≥80%，自动匹配四级考试难度
                </Alert>

                <Grid>
                  <Grid.Col span={6}>
                    <NumberInput
                      label="主题数量"
                      description="每个主题包含一篇文章"
                      min={1}
                      max={10}
                      {...form.getInputProps('week_config.reading_config.topic_count')}
                    />
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <NumberInput
                      label="每主题题目数"
                      description="每篇文章的题目数量"
                      min={1}
                      max={10}
                      {...form.getInputProps('week_config.reading_config.questions_per_topic')}
                    />
                  </Grid.Col>
                </Grid>

                <NumberInput
                  label="考纲关联度要求"
                  description="与四级考试大纲的关联程度"
                  min={60}
                  max={100}
                  suffix="%"
                  {...form.getInputProps('week_config.reading_config.syllabus_relevance_rate')}
                />

                <TagsInput
                  label="指定主题（可选）"
                  description="留空则自动选择主题"
                  placeholder="输入主题后按回车添加"
                  data={topicOptions}
                  {...form.getInputProps('week_config.reading_config.topics')}
                />

                <Card withBorder p="md" bg="blue.0">
                  <Text size="sm" fw={500} mb="xs">
                    预计生成内容
                  </Text>
                  <Text size="sm">
                    • {form.values.week_config.reading_config?.topic_count || 0} 篇阅读文章
                  </Text>
                  <Text size="sm">
                    •{' '}
                    {(form.values.week_config.reading_config?.topic_count || 0) *
                      (form.values.week_config.reading_config?.questions_per_topic || 0)}{' '}
                    道阅读题目
                  </Text>
                  <Text size="sm">
                    • 考纲关联度:{' '}
                    {form.values.week_config.reading_config?.syllabus_relevance_rate || 80}%
                  </Text>
                </Card>
              </>
            )}
          </Stack>
        </Tabs.Panel>

        {/* 写作训练配置 */}
        <Tabs.Panel value="writing" pt="lg">
          <Stack gap="md">
            {!writingEnabled ? (
              <Alert icon={<IconAlertTriangle size={16} />} color="yellow">
                写作训练已禁用，请在基本设置中启用
              </Alert>
            ) : (
              <>
                <Alert icon={<IconCheck size={16} />} color="green">
                  写作训练将自动嵌入四级评分标准，确保训练效果
                </Alert>

                <MultiSelect
                  label="写作类型组合"
                  description="选择本周要训练的写作类型"
                  data={writingTypeOptions}
                  required
                  {...form.getInputProps('week_config.writing_config.writing_types')}
                />

                <Switch
                  label="嵌入四级评分标准"
                  description="在写作题目中嵌入四级考试评分标准和要求"
                  {...form.getInputProps('week_config.writing_config.cet4_standard_embedded', {
                    type: 'checkbox',
                  })}
                />

                <MultiSelect
                  label="题目来源"
                  description="写作题目的来源类型"
                  data={topicSourceOptions}
                  {...form.getInputProps('week_config.writing_config.topic_sources')}
                />

                <Card withBorder p="md" bg="green.0">
                  <Text size="sm" fw={500} mb="xs">
                    预计生成内容
                  </Text>
                  <Text size="sm">
                    • {form.values.week_config.writing_config?.writing_types.length || 0} 道写作题目
                  </Text>
                  <Text size="sm">
                    • 四级标准:{' '}
                    {form.values.week_config.writing_config?.cet4_standard_embedded
                      ? '已嵌入'
                      : '未嵌入'}
                  </Text>
                  <Text size="sm">
                    • 题目来源:{' '}
                    {form.values.week_config.writing_config?.topic_sources.join(', ') || '无'}
                  </Text>
                </Card>
              </>
            )}
          </Stack>
        </Tabs.Panel>

        {/* 发布设置 */}
        <Tabs.Panel value="publish" pt="lg">
          <Stack gap="md">
            <Select
              label="发布方式"
              data={[
                { value: 'immediate', label: '立即发布' },
                { value: 'scheduled', label: '定时发布' },
              ]}
              {...form.getInputProps('publish_type')}
            />

            {form.values.publish_type === 'scheduled' && (
              <DateTimePicker
                label="发布时间"
                description="选择自动发布的时间"
                placeholder="选择日期和时间"
                minDate={new Date()}
                required
                {...form.getInputProps('scheduled_time')}
              />
            )}

            <Alert
              icon={
                form.values.publish_type === 'immediate' ? (
                  <IconCheck size={16} />
                ) : (
                  <IconClock size={16} />
                )
              }
              color={form.values.publish_type === 'immediate' ? 'green' : 'blue'}
            >
              {form.values.publish_type === 'immediate'
                ? '题目将在创建后立即投放到学生训练中心'
                : `题目将在 ${form.values.scheduled_time?.toLocaleString() || '选定时间'} 自动投放`}
            </Alert>
          </Stack>
        </Tabs.Panel>
      </Tabs>

      <Divider my="lg" />

      {/* 操作按钮 */}
      <Group justify="flex-end">
        {onCancel && (
          <Button variant="light" onClick={onCancel}>
            取消
          </Button>
        )}
        <Button
          type="submit"
          loading={loading}
          leftSection={<IconCheck size={16} />}
          disabled={!readingEnabled && !writingEnabled}
        >
          创建周训练
        </Button>
      </Group>
    </form>
  )
}
