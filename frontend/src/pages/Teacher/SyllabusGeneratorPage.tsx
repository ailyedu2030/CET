/**
 * AI课程大纲生成页面
 */
import { useState } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Button,
  TextInput,
  Select,
  Group,
  Stack,
  Badge,
  Alert,
  LoadingOverlay,
  NumberInput,
  TagsInput,
  JsonInput,
  Tabs,
  Accordion,
  List,
  ActionIcon,
  CopyButton,
  Tooltip,
} from '@mantine/core'
import {
  IconBrain,
  IconFileText,
  IconDownload,
  IconCopy,
  IconCheck,
  IconRefresh,
  IconStar,
  IconClock,
  IconTarget,
  IconBook,
  IconChartLine,
} from '@tabler/icons-react'
import { aiService } from '../../services/aiService'
import { SyllabusGenerateRequest, Syllabus, LoadingState } from '../../types/ai'

export function SyllabusGeneratorPage(): JSX.Element {
  // 状态管理
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null)
  const [loadingState, setLoadingState] = useState<LoadingState>({ loading: false })
  const [generating, setGenerating] = useState(false)

  // 表单状态
  const [form, setForm] = useState<SyllabusGenerateRequest>({
    course_id: 1, // 默认值，实际应该从选择框获取
    course_name: '',
    duration_weeks: 16,
    target_level: '中级',
    learning_objectives: [],
    focus_areas: [],
    available_resources: [],
    source_materials: {},
  })

  // 生成大纲
  const generateSyllabus = async () => {
    if (!form.course_name || form.learning_objectives.length === 0) {
      setLoadingState({ loading: false, error: '请填写课程名称和学习目标' })
      return
    }

    try {
      setGenerating(true)
      setLoadingState({ loading: true })

      const newSyllabus = await aiService.generateSyllabus(form)
      setSyllabus(newSyllabus)
      setLoadingState({ loading: false })
    } catch (error) {
      setLoadingState({
        loading: false,
        error: error instanceof Error ? error.message : '生成大纲失败',
      })
    } finally {
      setGenerating(false)
    }
  }

  // 重新生成
  const regenerate = () => {
    setSyllabus(null)
    generateSyllabus()
  }

  // 下载大纲
  const downloadSyllabus = () => {
    if (!syllabus) return

    const content = JSON.stringify(syllabus.content, null, 2)
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${syllabus.title}-syllabus.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 解析大纲内容结构
  const parseContent = (content: Record<string, unknown>) => {
    return {
      overview: (content['overview'] as string) || '',
      weeks:
        (content['weeks'] as Array<{
          week: number
          title: string
          objectives: string[]
          topics: string[]
          activities: string[]
          assessments?: string[]
          materials?: string[]
        }>) || [],
      assessment_plan: content['assessment_plan'] as {
        methods: string[]
        weights: Record<string, number>
        schedule: Array<{ type: string; week: number; description: string }>
      },
      resources: content['resources'] as {
        textbooks: string[]
        online_resources: string[]
        tools: string[]
      },
      additional_notes: (content['additional_notes'] as string) || '',
    }
  }

  const parsedContent = syllabus ? parseContent(syllabus.content) : null

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={loadingState.loading} />

      {/* 页面头部 */}
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>AI课程大纲生成</Title>
          <Text c="dimmed" size="sm">
            基于AI智能生成个性化课程教学大纲，提升课程设计效率
          </Text>
        </div>
        {syllabus && (
          <Group>
            <Tooltip label="重新生成">
              <ActionIcon variant="light" size="lg" onClick={regenerate} loading={generating}>
                <IconRefresh size={18} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="下载大纲">
              <ActionIcon variant="light" size="lg" onClick={downloadSyllabus}>
                <IconDownload size={18} />
              </ActionIcon>
            </Tooltip>
          </Group>
        )}
      </Group>

      {/* 错误提示 */}
      {loadingState.error && (
        <Alert
          icon={<IconBrain size={16} />}
          title="生成失败"
          color="red"
          mb="lg"
          onClose={() => setLoadingState({ loading: false })}
          withCloseButton
        >
          {loadingState.error}
        </Alert>
      )}

      <Grid>
        {/* 左侧：输入表单 */}
        <Grid.Col span={{ base: 12, lg: 4 }}>
          <Card
            shadow="sm"
            padding="lg"
            radius="md"
            withBorder
            style={{ position: 'sticky', top: '20px' }}
          >
            <Text fw={500} size="lg" mb="md">
              生成参数
            </Text>

            <Stack>
              <TextInput
                label="课程名称"
                placeholder="例如：英语四级听力强化训练"
                value={form.course_name}
                onChange={event =>
                  setForm(prev => ({
                    ...prev,
                    course_name: event.target.value,
                  }))
                }
                required
              />

              <NumberInput
                label="课程周数"
                placeholder="16"
                min={1}
                max={52}
                value={form.duration_weeks}
                onChange={value =>
                  setForm(prev => ({
                    ...prev,
                    duration_weeks: typeof value === 'number' ? value : 16,
                  }))
                }
              />

              <Select
                label="目标水平"
                data={[
                  { value: '初级', label: '初级' },
                  { value: '中级', label: '中级' },
                  { value: '高级', label: '高级' },
                ]}
                value={form.target_level}
                onChange={value =>
                  setForm(prev => ({
                    ...prev,
                    target_level: value || '中级',
                  }))
                }
              />

              <TagsInput
                label="学习目标"
                placeholder="输入学习目标，按回车添加"
                value={form.learning_objectives}
                onChange={value =>
                  setForm(prev => ({
                    ...prev,
                    learning_objectives: value,
                  }))
                }
                required
              />

              <TagsInput
                label="重点领域"
                placeholder="例如：听力、口语、阅读"
                value={form.focus_areas || []}
                onChange={value =>
                  setForm(prev => ({
                    ...prev,
                    focus_areas: value,
                  }))
                }
              />

              <TagsInput
                label="可用资源"
                placeholder="例如：教材、在线平台、实验室"
                value={form.available_resources || []}
                onChange={value =>
                  setForm(prev => ({
                    ...prev,
                    available_resources: value,
                  }))
                }
              />

              <JsonInput
                label="补充材料 (JSON)"
                placeholder='{"textbook": "教材信息", "tools": ["工具1", "工具2"]}'
                minRows={4}
                value={JSON.stringify(form.source_materials || {}, null, 2)}
                onChange={value => {
                  try {
                    const parsed = JSON.parse(value || '{}')
                    setForm(prev => ({ ...prev, source_materials: parsed }))
                  } catch {
                    // 忽略JSON解析错误
                  }
                }}
              />

              <Button
                fullWidth
                leftSection={<IconBrain size={16} />}
                loading={generating}
                onClick={generateSyllabus}
                size="md"
              >
                生成AI课程大纲
              </Button>
            </Stack>
          </Card>
        </Grid.Col>

        {/* 右侧：生成结果 */}
        <Grid.Col span={{ base: 12, lg: 8 }}>
          {syllabus && parsedContent ? (
            <Stack>
              {/* 大纲基本信息 */}
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <div>
                    <Title order={2}>{syllabus.title}</Title>
                    <Group gap="xs" mt="xs">
                      <Badge color="blue" variant="light">
                        {syllabus.status === 'draft'
                          ? '草稿'
                          : syllabus.status === 'review'
                            ? '审核中'
                            : '已批准'}
                      </Badge>
                      <Badge color="green" variant="outline">
                        版本 {syllabus.version}
                      </Badge>
                      {syllabus.ai_generated && (
                        <Badge color="purple" variant="light">
                          AI生成
                        </Badge>
                      )}
                    </Group>
                  </div>
                  <Group gap="xs">
                    <IconStar size={16} />
                    <Text size="sm" fw={500}>
                      置信度: {Math.round(syllabus.confidence_score * 100)}%
                    </Text>
                  </Group>
                </Group>

                <Grid>
                  <Grid.Col span={6}>
                    <Group gap="xs">
                      <IconClock size={16} color="blue" />
                      <Text size="sm">课程时长: {form.duration_weeks}周</Text>
                    </Group>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Group gap="xs">
                      <IconTarget size={16} color="green" />
                      <Text size="sm">目标水平: {form.target_level}</Text>
                    </Group>
                  </Grid.Col>
                  <Grid.Col span={12}>
                    <Group gap="xs">
                      <IconBook size={16} color="purple" />
                      <Text size="sm">
                        生成时间: {new Date(syllabus.created_at).toLocaleString()}
                      </Text>
                    </Group>
                  </Grid.Col>
                </Grid>
              </Card>

              {/* 大纲详细内容 */}
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Tabs defaultValue="overview">
                  <Tabs.List>
                    <Tabs.Tab value="overview" leftSection={<IconFileText size={16} />}>
                      课程概述
                    </Tabs.Tab>
                    <Tabs.Tab value="schedule" leftSection={<IconClock size={16} />}>
                      教学安排
                    </Tabs.Tab>
                    <Tabs.Tab value="assessment" leftSection={<IconChartLine size={16} />}>
                      评估计划
                    </Tabs.Tab>
                    <Tabs.Tab value="resources" leftSection={<IconBook size={16} />}>
                      教学资源
                    </Tabs.Tab>
                  </Tabs.List>

                  <Tabs.Panel value="overview" pt="md">
                    <Stack>
                      <div>
                        <Text fw={500} mb="sm">
                          课程概述
                        </Text>
                        <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                          {parsedContent.overview}
                        </Text>
                      </div>

                      <div>
                        <Text fw={500} mb="sm">
                          学习目标
                        </Text>
                        <List size="sm">
                          {form.learning_objectives.map((objective, index) => (
                            <List.Item key={index}>{objective}</List.Item>
                          ))}
                        </List>
                      </div>

                      {form.focus_areas && form.focus_areas.length > 0 && (
                        <div>
                          <Text fw={500} mb="sm">
                            重点领域
                          </Text>
                          <Group gap="xs">
                            {form.focus_areas.map((area, index) => (
                              <Badge key={index} variant="light">
                                {area}
                              </Badge>
                            ))}
                          </Group>
                        </div>
                      )}

                      {parsedContent.additional_notes && (
                        <div>
                          <Text fw={500} mb="sm">
                            补充说明
                          </Text>
                          <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                            {parsedContent.additional_notes}
                          </Text>
                        </div>
                      )}
                    </Stack>
                  </Tabs.Panel>

                  <Tabs.Panel value="schedule" pt="md">
                    <Accordion variant="separated">
                      {parsedContent.weeks.map((week, index) => (
                        <Accordion.Item key={index} value={`week-${week.week}`}>
                          <Accordion.Control>
                            <Group justify="space-between" w="100%">
                              <Text fw={500}>
                                第{week.week}周: {week.title}
                              </Text>
                              <Badge variant="light" size="sm">
                                {week.topics.length}个主题
                              </Badge>
                            </Group>
                          </Accordion.Control>
                          <Accordion.Panel>
                            <Stack gap="sm">
                              {week.objectives && week.objectives.length > 0 && (
                                <div>
                                  <Text fw={500} size="sm" mb="xs">
                                    本周目标
                                  </Text>
                                  <List size="sm">
                                    {week.objectives.map((obj, idx) => (
                                      <List.Item key={idx}>{obj}</List.Item>
                                    ))}
                                  </List>
                                </div>
                              )}

                              <div>
                                <Text fw={500} size="sm" mb="xs">
                                  主题内容
                                </Text>
                                <List size="sm">
                                  {week.topics.map((topic, idx) => (
                                    <List.Item key={idx}>{topic}</List.Item>
                                  ))}
                                </List>
                              </div>

                              {week.activities && week.activities.length > 0 && (
                                <div>
                                  <Text fw={500} size="sm" mb="xs">
                                    教学活动
                                  </Text>
                                  <List size="sm">
                                    {week.activities.map((activity, idx) => (
                                      <List.Item key={idx}>{activity}</List.Item>
                                    ))}
                                  </List>
                                </div>
                              )}

                              {week.assessments && week.assessments.length > 0 && (
                                <div>
                                  <Text fw={500} size="sm" mb="xs">
                                    评估任务
                                  </Text>
                                  <List size="sm">
                                    {week.assessments.map((assessment, idx) => (
                                      <List.Item key={idx}>{assessment}</List.Item>
                                    ))}
                                  </List>
                                </div>
                              )}
                            </Stack>
                          </Accordion.Panel>
                        </Accordion.Item>
                      ))}
                    </Accordion>
                  </Tabs.Panel>

                  <Tabs.Panel value="assessment" pt="md">
                    <Stack>
                      {parsedContent.assessment_plan.methods && (
                        <div>
                          <Text fw={500} mb="sm">
                            评估方法
                          </Text>
                          <List size="sm">
                            {parsedContent.assessment_plan.methods.map((method, index) => (
                              <List.Item key={index}>{method}</List.Item>
                            ))}
                          </List>
                        </div>
                      )}

                      {parsedContent.assessment_plan.weights && (
                        <div>
                          <Text fw={500} mb="sm">
                            评分权重
                          </Text>
                          <Grid>
                            {Object.entries(parsedContent.assessment_plan.weights).map(
                              ([key, weight]) => (
                                <Grid.Col key={key} span={6}>
                                  <Group justify="space-between">
                                    <Text size="sm">{key}</Text>
                                    <Badge variant="light">{weight}%</Badge>
                                  </Group>
                                </Grid.Col>
                              )
                            )}
                          </Grid>
                        </div>
                      )}

                      {parsedContent.assessment_plan.schedule && (
                        <div>
                          <Text fw={500} mb="sm">
                            评估时间表
                          </Text>
                          <Stack gap="xs">
                            {parsedContent.assessment_plan.schedule.map((item, index) => (
                              <Group
                                key={index}
                                justify="space-between"
                                p="sm"
                                style={{ border: '1px solid #e9ecef', borderRadius: '8px' }}
                              >
                                <div>
                                  <Text fw={500} size="sm">
                                    {item.type}
                                  </Text>
                                  <Text size="xs" c="dimmed">
                                    {item.description}
                                  </Text>
                                </div>
                                <Badge variant="outline">第{item.week}周</Badge>
                              </Group>
                            ))}
                          </Stack>
                        </div>
                      )}
                    </Stack>
                  </Tabs.Panel>

                  <Tabs.Panel value="resources" pt="md">
                    <Stack>
                      {parsedContent.resources.textbooks &&
                        parsedContent.resources.textbooks.length > 0 && (
                          <div>
                            <Text fw={500} mb="sm">
                              教材资料
                            </Text>
                            <List size="sm">
                              {parsedContent.resources.textbooks.map((book, index) => (
                                <List.Item key={index}>{book}</List.Item>
                              ))}
                            </List>
                          </div>
                        )}

                      {parsedContent.resources.online_resources &&
                        parsedContent.resources.online_resources.length > 0 && (
                          <div>
                            <Text fw={500} mb="sm">
                              在线资源
                            </Text>
                            <List size="sm">
                              {parsedContent.resources.online_resources.map((resource, index) => (
                                <List.Item key={index}>{resource}</List.Item>
                              ))}
                            </List>
                          </div>
                        )}

                      {parsedContent.resources.tools &&
                        parsedContent.resources.tools.length > 0 && (
                          <div>
                            <Text fw={500} mb="sm">
                              教学工具
                            </Text>
                            <Group gap="xs">
                              {parsedContent.resources.tools.map((tool, index) => (
                                <Badge key={index} variant="light" color="blue">
                                  {tool}
                                </Badge>
                              ))}
                            </Group>
                          </div>
                        )}
                    </Stack>
                  </Tabs.Panel>
                </Tabs>
              </Card>

              {/* 操作按钮 */}
              <Card shadow="sm" padding="md" radius="md" withBorder>
                <Group>
                  <Button
                    leftSection={<IconRefresh size={16} />}
                    variant="light"
                    onClick={regenerate}
                  >
                    重新生成
                  </Button>
                  <Button
                    leftSection={<IconDownload size={16} />}
                    variant="light"
                    onClick={downloadSyllabus}
                  >
                    下载大纲
                  </Button>
                  <CopyButton value={JSON.stringify(syllabus.content, null, 2)}>
                    {({ copied, copy }) => (
                      <Button
                        leftSection={copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                        color={copied ? 'teal' : 'blue'}
                        variant="light"
                        onClick={copy}
                      >
                        {copied ? '已复制' : '复制内容'}
                      </Button>
                    )}
                  </CopyButton>
                </Group>
              </Card>
            </Stack>
          ) : (
            <Card shadow="sm" padding="xl" radius="md" withBorder>
              <Stack align="center" gap="lg">
                <IconFileText size={48} color="gray" />
                <div style={{ textAlign: 'center' }}>
                  <Text fw={500} size="lg" mb="xs">
                    AI课程大纲生成器
                  </Text>
                  <Text c="dimmed" size="sm">
                    填写左侧表单信息，点击生成按钮开始创建个性化的课程教学大纲
                  </Text>
                </div>
              </Stack>
            </Card>
          )}
        </Grid.Col>
      </Grid>
    </Container>
  )
}
