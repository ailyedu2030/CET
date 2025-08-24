/**
 * 智能教学调整建议页面
 */
import { useEffect, useState } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Button,
  Select,
  Group,
  Stack,
  Badge,
  Alert,
  Modal,
  LoadingOverlay,
  ActionIcon,
  Table,
  ScrollArea,
  Textarea,
  Rating,
  Tabs,
  Progress,
} from '@mantine/core'
import {
  IconBulb,
  IconCheck,
  IconX,
  IconClock,
  IconAlertTriangle,
  IconRefresh,
  IconPlus,
  IconEye,
  IconEdit,
  IconTarget,
  IconBookmark,
  IconHistory,
  IconGitCompare,
  IconRobot,
  IconUserCheck,
} from '@tabler/icons-react'
import { useDisclosure } from '@mantine/hooks'
import { DatePickerInput } from '@mantine/dates'
import { aiService } from '../../services/aiService'
import {
  TeachingAdjustmentRequest,
  TeachingAdjustment,
  TeachingAdjustmentUpdate,
  LoadingState,
  Course,
  Class,
} from '../../types/ai'

export function TeachingAdjustmentsPage(): JSX.Element {
  // 状态管理
  const [adjustments, setAdjustments] = useState<TeachingAdjustment[]>([])
  const [selectedAdjustment, setSelectedAdjustment] = useState<TeachingAdjustment | null>(null)
  const [loadingState, setLoadingState] = useState<LoadingState>({ loading: true })
  const [generating, setGenerating] = useState(false)
  const [updating, setUpdating] = useState(false)

  // Modal控制
  const [detailModalOpened, { open: openDetailModal, close: closeDetailModal }] =
    useDisclosure(false)
  const [versionModalOpened, { open: openVersionModal, close: closeVersionModal }] =
    useDisclosure(false)
  const [autoAdjustModalOpened, { open: openAutoAdjustModal, close: closeAutoAdjustModal }] =
    useDisclosure(false)
  const [
    newAdjustmentModalOpened,
    { open: openNewAdjustmentModal, close: closeNewAdjustmentModal },
  ] = useDisclosure(false)

  // 表单状态
  const [adjustmentForm, setAdjustmentForm] = useState<TeachingAdjustmentRequest>({
    class_id: 0,
    course_id: 0,
    adjustment_focus: 'content',
    priority_level: 'medium',
  })

  const [updateForm, setUpdateForm] = useState<TeachingAdjustmentUpdate>({
    implementation_status: 'pending',
  })

  // 筛选状态
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')

  // 模拟数据
  const [courses] = useState<Course[]>([
    {
      id: 1,
      name: '英语四级听力',
      description: '',
      level: '中级',
      duration_weeks: 12,
      created_at: '',
      updated_at: '',
    },
    {
      id: 2,
      name: '英语四级阅读',
      description: '',
      level: '中级',
      duration_weeks: 16,
      created_at: '',
      updated_at: '',
    },
  ])

  const [classes] = useState<Class[]>([
    {
      id: 1,
      name: '2024春季班A',
      course_id: 1,
      teacher_id: 1,
      student_count: 25,
      created_at: '',
      updated_at: '',
    },
    {
      id: 2,
      name: '2024春季班B',
      course_id: 1,
      teacher_id: 1,
      student_count: 30,
      created_at: '',
      updated_at: '',
    },
  ])

  // 加载调整建议
  const loadAdjustments = async () => {
    try {
      setLoadingState({ loading: true })
      const response = await aiService.getTeachingAdjustments({
        page: 1,
        size: 50,
        ...(statusFilter !== 'all' && { implementation_status: statusFilter }),
        ...(priorityFilter !== 'all' && { priority_level: priorityFilter }),
      })
      setAdjustments(response.adjustments)
      setLoadingState({ loading: false })
    } catch (error) {
      setLoadingState({
        loading: false,
        error: error instanceof Error ? error.message : '加载调整建议失败',
      })
    }
  }

  // 生成新建议
  const generateAdjustment = async () => {
    try {
      setGenerating(true)
      const newAdjustments = await aiService.generateTeachingAdjustments(adjustmentForm)
      setAdjustments(prev => [...newAdjustments, ...prev])
      closeNewAdjustmentModal()
      // 重置表单
      setAdjustmentForm({
        class_id: 0,
        course_id: 0,
        adjustment_focus: 'content',
        priority_level: 'medium',
      })
    } catch (error) {
      // Handle error silently or show notification
    } finally {
      setGenerating(false)
    }
  }

  // 更新建议状态
  const updateAdjustment = async () => {
    if (!selectedAdjustment) return

    try {
      setUpdating(true)
      const updated = await aiService.updateTeachingAdjustment(selectedAdjustment.id, updateForm)
      setAdjustments(prev => prev.map(adj => (adj.id === updated.id ? updated : adj)))
      closeDetailModal()
    } catch (error) {
      // Handle error silently or show notification
    } finally {
      setUpdating(false)
    }
  }

  // 查看详情
  const viewDetail = (adjustment: TeachingAdjustment) => {
    setSelectedAdjustment(adjustment)
    setUpdateForm({
      implementation_status: adjustment.implementation_status,
      implementation_date: adjustment.implementation_date || undefined,
      feedback: adjustment.feedback || '',
      effectiveness_rating: adjustment.effectiveness_rating || undefined,
    })
    openDetailModal()
  }

  // 初始加载
  useEffect(() => {
    loadAdjustments()
  }, [statusFilter, priorityFilter])

  // 获取状态颜色和图标
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
        return { color: 'orange', icon: IconClock, text: '待处理' }
      case 'in_progress':
        return { color: 'blue', icon: IconBookmark, text: '进行中' }
      case 'completed':
        return { color: 'green', icon: IconCheck, text: '已完成' }
      case 'dismissed':
        return { color: 'gray', icon: IconX, text: '已忽略' }
      default:
        return { color: 'gray', icon: IconClock, text: status }
    }
  }

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'red'
      case 'medium':
        return 'yellow'
      case 'low':
        return 'green'
      default:
        return 'gray'
    }
  }

  // 获取焦点类型文本
  const getFocusText = (focus: string) => {
    switch (focus) {
      case 'content':
        return '内容调整'
      case 'pace':
        return '进度调整'
      case 'method':
        return '方法调整'
      case 'assessment':
        return '评估调整'
      default:
        return focus
    }
  }

  // 筛选后的数据
  const filteredAdjustments = adjustments

  // 统计数据
  const stats = {
    total: adjustments.length,
    pending: adjustments.filter(a => a.implementation_status === 'pending').length,
    inProgress: adjustments.filter(a => a.implementation_status === 'in_progress').length,
    completed: adjustments.filter(a => a.implementation_status === 'completed').length,
    avgConfidence:
      adjustments.length > 0
        ? adjustments.reduce((sum, a) => sum + a.confidence_score, 0) / adjustments.length
        : 0,
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={loadingState.loading} />

      {/* 页面头部 */}
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>智能教学调整</Title>
          <Text c="dimmed" size="sm">
            基于AI分析的个性化教学调整建议，提升教学效果
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconHistory size={16} />}
            variant="light"
            onClick={openVersionModal}
          >
            版本历史
          </Button>
          <Button
            leftSection={<IconRobot size={16} />}
            variant="light"
            onClick={openAutoAdjustModal}
          >
            自动调整
          </Button>
          <Button leftSection={<IconRefresh size={16} />} variant="light" onClick={loadAdjustments}>
            刷新
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={openNewAdjustmentModal}>
            生成建议
          </Button>
        </Group>
      </Group>

      {/* 错误提示 */}
      {loadingState.error && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red" mb="lg">
          {loadingState.error}
        </Alert>
      )}

      {/* 统计卡片 */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  总建议数
                </Text>
                <Text fw={700} size="xl">
                  {stats.total}
                </Text>
              </div>
              <IconBulb size={24} color="blue" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  待处理
                </Text>
                <Text fw={700} size="xl" c="orange">
                  {stats.pending}
                </Text>
              </div>
              <IconClock size={24} color="orange" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  已完成
                </Text>
                <Text fw={700} size="xl" c="green">
                  {stats.completed}
                </Text>
              </div>
              <IconCheck size={24} color="green" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  平均置信度
                </Text>
                <Text fw={700} size="xl">
                  {Math.round(stats.avgConfidence * 100)}%
                </Text>
              </div>
              <IconTarget size={24} color="purple" />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 筛选器 */}
      <Card shadow="sm" padding="md" radius="md" withBorder mb="lg">
        <Group>
          <Select
            placeholder="状态筛选"
            data={[
              { value: 'all', label: '全部状态' },
              { value: 'pending', label: '待处理' },
              { value: 'in_progress', label: '进行中' },
              { value: 'completed', label: '已完成' },
              { value: 'dismissed', label: '已忽略' },
            ]}
            value={statusFilter}
            onChange={value => setStatusFilter(value || 'all')}
            w={150}
          />

          <Select
            placeholder="优先级筛选"
            data={[
              { value: 'all', label: '全部优先级' },
              { value: 'high', label: '高优先级' },
              { value: 'medium', label: '中优先级' },
              { value: 'low', label: '低优先级' },
            ]}
            value={priorityFilter}
            onChange={value => setPriorityFilter(value || 'all')}
            w={150}
          />
        </Group>
      </Card>

      {/* 建议列表 */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Group justify="space-between" mb="md">
          <Text fw={500} size="lg">
            调整建议
          </Text>
        </Group>

        {filteredAdjustments.length > 0 ? (
          <ScrollArea>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>标题</Table.Th>
                  <Table.Th>类型</Table.Th>
                  <Table.Th>优先级</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>目标学生</Table.Th>
                  <Table.Th>置信度</Table.Th>
                  <Table.Th>创建时间</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredAdjustments.map(adjustment => {
                  const statusInfo = getStatusInfo(adjustment.implementation_status)
                  return (
                    <Table.Tr key={adjustment.id}>
                      <Table.Td>
                        <div>
                          <Text fw={500} size="sm" lineClamp={1}>
                            {adjustment.title}
                          </Text>
                          <Text size="xs" c="dimmed" lineClamp={1}>
                            {adjustment.description}
                          </Text>
                        </div>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="light" color="blue" size="sm">
                          {getFocusText(adjustment.adjustment_type)}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          color={getPriorityColor(adjustment.priority_level)}
                          variant="light"
                          size="sm"
                        >
                          {adjustment.priority_level === 'high'
                            ? '高'
                            : adjustment.priority_level === 'medium'
                              ? '中'
                              : '低'}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <statusInfo.icon size={14} color={statusInfo.color} />
                          <Text size="sm" c={statusInfo.color}>
                            {statusInfo.text}
                          </Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {adjustment.target_students.length > 0
                            ? `${adjustment.target_students.length}人`
                            : '全班'}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Progress
                            value={adjustment.confidence_score * 100}
                            size="sm"
                            w={60}
                            color={
                              adjustment.confidence_score > 0.8
                                ? 'green'
                                : adjustment.confidence_score > 0.6
                                  ? 'yellow'
                                  : 'orange'
                            }
                          />
                          <Text size="xs">{Math.round(adjustment.confidence_score * 100)}%</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {new Date(adjustment.created_at).toLocaleDateString()}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <ActionIcon
                            variant="light"
                            size="sm"
                            onClick={() => viewDetail(adjustment)}
                          >
                            <IconEye size={14} />
                          </ActionIcon>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  )
                })}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        ) : (
          <Text c="dimmed" ta="center" py="xl">
            暂无调整建议，点击"生成建议"开始
          </Text>
        )}
      </Card>

      {/* 生成新建议Modal */}
      <Modal
        opened={newAdjustmentModalOpened}
        onClose={closeNewAdjustmentModal}
        title="生成智能调整建议"
        size="md"
      >
        <Stack>
          <Select
            label="选择课程"
            placeholder="请选择课程"
            data={courses.map(c => ({ value: c.id.toString(), label: c.name }))}
            value={adjustmentForm.course_id.toString()}
            onChange={value =>
              setAdjustmentForm(prev => ({
                ...prev,
                course_id: parseInt(value || '0'),
              }))
            }
          />

          <Select
            label="选择班级"
            placeholder="请选择班级"
            data={classes
              .filter(c => c.course_id === adjustmentForm.course_id)
              .map(c => ({ value: c.id.toString(), label: c.name }))}
            value={adjustmentForm.class_id.toString()}
            onChange={value =>
              setAdjustmentForm(prev => ({
                ...prev,
                class_id: parseInt(value || '0'),
              }))
            }
          />

          <Select
            label="调整重点"
            data={[
              { value: 'content', label: '内容调整' },
              { value: 'pace', label: '进度调整' },
              { value: 'method', label: '方法调整' },
              { value: 'assessment', label: '评估调整' },
            ]}
            value={adjustmentForm.adjustment_focus}
            onChange={value =>
              setAdjustmentForm(prev => ({
                ...prev,
                adjustment_focus: value as 'content' | 'pace' | 'method' | 'assessment',
              }))
            }
          />

          <Select
            label="优先级"
            data={[
              { value: 'high', label: '高优先级' },
              { value: 'medium', label: '中优先级' },
              { value: 'low', label: '低优先级' },
            ]}
            value={adjustmentForm.priority_level}
            onChange={value =>
              setAdjustmentForm(prev => ({
                ...prev,
                priority_level: value as 'high' | 'medium' | 'low',
              }))
            }
          />

          <Textarea
            label="当前问题描述（可选）"
            placeholder="描述当前教学中遇到的具体问题..."
            minRows={3}
            onChange={event =>
              setAdjustmentForm(prev => ({
                ...prev,
                current_issues: event.target.value ? [event.target.value] : undefined,
              }))
            }
          />

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={closeNewAdjustmentModal}>
              取消
            </Button>
            <Button
              leftSection={<IconBulb size={16} />}
              loading={generating}
              onClick={generateAdjustment}
              disabled={adjustmentForm.class_id === 0 || adjustmentForm.course_id === 0}
            >
              生成建议
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 详情和更新Modal */}
      <Modal opened={detailModalOpened} onClose={closeDetailModal} title="调整建议详情" size="xl">
        {selectedAdjustment && (
          <Tabs defaultValue="details">
            <Tabs.List>
              <Tabs.Tab value="details" leftSection={<IconEye size={16} />}>
                详细信息
              </Tabs.Tab>
              <Tabs.Tab value="update" leftSection={<IconEdit size={16} />}>
                更新状态
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="details" pt="md">
              <Stack>
                {/* 基本信息 */}
                <Card withBorder p="md">
                  <Group justify="space-between" mb="md">
                    <Text fw={500} size="lg">
                      {selectedAdjustment.title}
                    </Text>
                    <Group gap="xs">
                      <Badge
                        color={getPriorityColor(selectedAdjustment.priority_level)}
                        variant="light"
                      >
                        {selectedAdjustment.priority_level === 'high'
                          ? '高优先级'
                          : selectedAdjustment.priority_level === 'medium'
                            ? '中优先级'
                            : '低优先级'}
                      </Badge>
                    </Group>
                  </Group>

                  <Text size="sm" mb="md">
                    {selectedAdjustment.description}
                  </Text>

                  <Grid>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">
                        调整类型
                      </Text>
                      <Text fw={500}>{getFocusText(selectedAdjustment.adjustment_type)}</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">
                        目标学生
                      </Text>
                      <Text fw={500}>
                        {selectedAdjustment.target_students.length > 0
                          ? `${selectedAdjustment.target_students.length}人`
                          : '全班学生'}
                      </Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">
                        AI置信度
                      </Text>
                      <Group gap="xs">
                        <Progress
                          value={selectedAdjustment.confidence_score * 100}
                          size="md"
                          w={100}
                          color="blue"
                        />
                        <Text fw={500}>
                          {Math.round(selectedAdjustment.confidence_score * 100)}%
                        </Text>
                      </Group>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">
                        创建时间
                      </Text>
                      <Text fw={500}>
                        {new Date(selectedAdjustment.created_at).toLocaleString()}
                      </Text>
                    </Grid.Col>
                  </Grid>
                </Card>

                {/* 预期效果 */}
                {selectedAdjustment.expected_outcome && (
                  <Card withBorder p="md">
                    <Text fw={500} size="md" mb="sm">
                      预期效果
                    </Text>
                    <Text size="sm">{selectedAdjustment.expected_outcome}</Text>
                  </Card>
                )}

                {/* AI推理依据 */}
                {selectedAdjustment.reasoning && (
                  <Card withBorder p="md">
                    <Text fw={500} size="md" mb="sm">
                      AI推理依据
                    </Text>
                    <Text size="sm">{selectedAdjustment.reasoning}</Text>
                  </Card>
                )}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="update" pt="md">
              <Stack>
                <Select
                  label="实施状态"
                  data={[
                    { value: 'pending', label: '待处理' },
                    { value: 'in_progress', label: '进行中' },
                    { value: 'completed', label: '已完成' },
                    { value: 'dismissed', label: '已忽略' },
                  ]}
                  value={updateForm.implementation_status}
                  onChange={value =>
                    setUpdateForm(prev => ({
                      ...prev,
                      implementation_status: value as any,
                    }))
                  }
                />

                {updateForm.implementation_status === 'in_progress' && (
                  <DatePickerInput
                    label="开始实施日期"
                    value={
                      updateForm.implementation_date
                        ? new Date(updateForm.implementation_date)
                        : null
                    }
                    onChange={date =>
                      setUpdateForm(prev => ({
                        ...prev,
                        implementation_date: date?.toISOString(),
                      }))
                    }
                  />
                )}

                <Textarea
                  label="实施反馈"
                  placeholder="记录实施过程中的反馈和心得..."
                  minRows={4}
                  value={updateForm.feedback || ''}
                  onChange={event =>
                    setUpdateForm(prev => ({
                      ...prev,
                      feedback: event.target.value,
                    }))
                  }
                />

                {updateForm.implementation_status === 'completed' && (
                  <div>
                    <Text size="sm" fw={500} mb="xs">
                      效果评分
                    </Text>
                    <Group gap="xs">
                      <Rating
                        value={updateForm.effectiveness_rating || 0}
                        onChange={value =>
                          setUpdateForm(prev => ({
                            ...prev,
                            effectiveness_rating: value,
                          }))
                        }
                      />
                      <Text size="sm" c="dimmed">
                        ({updateForm.effectiveness_rating || 0}/5)
                      </Text>
                    </Group>
                  </div>
                )}

                <Group justify="flex-end" mt="md">
                  <Button variant="light" onClick={closeDetailModal}>
                    取消
                  </Button>
                  <Button
                    leftSection={<IconCheck size={16} />}
                    loading={updating}
                    onClick={updateAdjustment}
                  >
                    更新状态
                  </Button>
                </Group>
              </Stack>
            </Tabs.Panel>
          </Tabs>
        )}
      </Modal>

      {/* 版本历史对比模态框 */}
      <Modal
        opened={versionModalOpened}
        onClose={closeVersionModal}
        title="教案调整版本历史"
        size="xl"
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text size="sm">查看教案调整的历史版本，支持版本对比和回滚操作</Text>
          </Alert>

          <Tabs defaultValue="history">
            <Tabs.List>
              <Tabs.Tab value="history" leftSection={<IconHistory size={16} />}>
                版本历史
              </Tabs.Tab>
              <Tabs.Tab value="compare" leftSection={<IconGitCompare size={16} />}>
                版本对比
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="history" pt="md">
              <Stack gap="md">
                {/* 模拟版本历史数据 */}
                {[
                  {
                    version: 'v3.0',
                    date: '2024-01-20 14:30',
                    author: '张老师',
                    changes: ['调整语法重点', '增加练习时间', '优化教学方法'],
                    type: 'auto',
                  },
                  {
                    version: 'v2.1',
                    date: '2024-01-19 16:20',
                    author: '系统自动',
                    changes: ['基于学情分析自动调整', '增加薄弱知识点'],
                    type: 'auto',
                  },
                  {
                    version: 'v2.0',
                    date: '2024-01-18 10:15',
                    author: '张老师',
                    changes: ['手动调整教学内容', '修改课时安排'],
                    type: 'manual',
                  },
                ].map((version, index) => (
                  <Card key={index} withBorder>
                    <Group justify="space-between" mb="xs">
                      <Group gap="xs">
                        <Badge color={version.type === 'auto' ? 'blue' : 'green'}>
                          {version.version}
                        </Badge>
                        <Text size="sm" fw={500}>
                          {version.author}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {version.date}
                        </Text>
                      </Group>
                      <Group gap="xs">
                        <Button size="xs" variant="light">
                          查看详情
                        </Button>
                        <Button size="xs" variant="light" color="orange">
                          回滚到此版本
                        </Button>
                      </Group>
                    </Group>
                    <Stack gap="xs">
                      {version.changes.map((change, idx) => (
                        <Text key={idx} size="sm" c="dimmed">
                          • {change}
                        </Text>
                      ))}
                    </Stack>
                  </Card>
                ))}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="compare" pt="md">
              <Stack gap="md">
                <Group grow>
                  <Select
                    label="版本A"
                    placeholder="选择版本"
                    data={[
                      { value: 'v3.0', label: 'v3.0 (当前版本)' },
                      { value: 'v2.1', label: 'v2.1 (自动调整)' },
                      { value: 'v2.0', label: 'v2.0 (手动调整)' },
                    ]}
                    defaultValue="v3.0"
                  />
                  <Select
                    label="版本B"
                    placeholder="选择版本"
                    data={[
                      { value: 'v3.0', label: 'v3.0 (当前版本)' },
                      { value: 'v2.1', label: 'v2.1 (自动调整)' },
                      { value: 'v2.0', label: 'v2.0 (手动调整)' },
                    ]}
                    defaultValue="v2.0"
                  />
                </Group>

                <Alert color="green">
                  <Text size="sm">对比结果：发现 3 处内容变更，2 处时间调整，1 处方法优化</Text>
                </Alert>

                <Card withBorder>
                  <Text fw={500} mb="md">
                    变更详情
                  </Text>
                  <Stack gap="xs">
                    <Group>
                      <Badge color="red" size="sm">
                        删除
                      </Badge>
                      <Text size="sm" td="line-through" c="dimmed">
                        原教学重点：基础语法规则
                      </Text>
                    </Group>
                    <Group>
                      <Badge color="green" size="sm">
                        新增
                      </Badge>
                      <Text size="sm" c="green">
                        新教学重点：时态应用和语法实践
                      </Text>
                    </Group>
                    <Group>
                      <Badge color="blue" size="sm">
                        修改
                      </Badge>
                      <Text size="sm">课时分配：30分钟 → 45分钟</Text>
                    </Group>
                  </Stack>
                </Card>
              </Stack>
            </Tabs.Panel>
          </Tabs>

          <Group justify="flex-end">
            <Button variant="light" onClick={closeVersionModal}>
              关闭
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 自动调整审核模态框 */}
      <Modal
        opened={autoAdjustModalOpened}
        onClose={closeAutoAdjustModal}
        title="自动教学调整审核"
        size="lg"
      >
        <Stack gap="md">
          <Alert color="orange" icon={<IconRobot size={16} />}>
            <Text size="sm">系统基于最新学情分析生成了以下自动调整建议，请审核确认后应用</Text>
          </Alert>

          <Card withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={500}>待审核的自动调整</Text>
              <Badge color="orange">3 项待确认</Badge>
            </Group>

            <Stack gap="md">
              {/* 模拟自动调整建议 */}
              {[
                {
                  type: '内容调整',
                  description: '基于学情分析，建议增加时态练习内容',
                  confidence: 0.92,
                  impact: '高',
                  details: '检测到65%学生在时态应用方面存在困难，建议增加15分钟专项练习',
                },
                {
                  type: '进度调整',
                  description: '建议放慢语法讲解进度',
                  confidence: 0.88,
                  impact: '中',
                  details: '班级整体掌握度为72%，建议延长讲解时间5分钟',
                },
                {
                  type: '方法调整',
                  description: '建议采用互动式教学方法',
                  confidence: 0.85,
                  impact: '中',
                  details: '数据显示互动式教学可提升15%的学习效果',
                },
              ].map((adjustment, index) => (
                <Card key={index} withBorder p="sm">
                  <Group justify="space-between" mb="xs">
                    <Group gap="xs">
                      <Badge variant="light">{adjustment.type}</Badge>
                      <Text size="sm" fw={500}>
                        {adjustment.description}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <Badge color={adjustment.impact === '高' ? 'red' : 'blue'} size="sm">
                        {adjustment.impact}影响
                      </Badge>
                      <Text size="xs" c="dimmed">
                        置信度: {(adjustment.confidence * 100).toFixed(0)}%
                      </Text>
                    </Group>
                  </Group>

                  <Text size="sm" c="dimmed" mb="md">
                    {adjustment.details}
                  </Text>

                  <Group justify="flex-end" gap="xs">
                    <Button size="xs" variant="light" color="red">
                      拒绝
                    </Button>
                    <Button size="xs" variant="light" color="blue">
                      修改
                    </Button>
                    <Button size="xs" leftSection={<IconUserCheck size={12} />}>
                      确认应用
                    </Button>
                  </Group>
                </Card>
              ))}
            </Stack>
          </Card>

          <Group justify="space-between">
            <Button variant="light" onClick={closeAutoAdjustModal}>
              稍后处理
            </Button>
            <Group gap="xs">
              <Button variant="light" color="red">
                全部拒绝
              </Button>
              <Button leftSection={<IconUserCheck size={16} />}>批量确认</Button>
            </Group>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
