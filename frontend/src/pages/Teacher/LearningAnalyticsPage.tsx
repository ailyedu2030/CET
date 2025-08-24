/**
 * 学情分析页面 - AI驱动的学习分析界面
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
  Progress,
  Alert,
  Modal,
  LoadingOverlay,
  ActionIcon,
  Menu,
  Table,
  ScrollArea,
  RingProgress,
} from '@mantine/core'
import {
  IconBrain,
  IconChartLine,
  IconAlertTriangle,
  IconTrendingUp,
  IconUsers,
  IconRefresh,
  IconDownload,
  IconFilter,
  IconEye,
  IconTarget,
} from '@tabler/icons-react'
import { useDisclosure } from '@mantine/hooks'
import { aiService } from '../../services/aiService'
import { LearningAlertPanel } from '@/components/Analytics/LearningAlertPanel'
import {
  LearningAnalysisRequest,
  LearningAnalysis,
  TeachingAdjustment,
  Course,
  Class,
} from '../../types/ai'

export function LearningAnalyticsPage(): JSX.Element {
  // 状态管理
  const [analyses, setAnalyses] = useState<LearningAnalysis[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<LearningAnalysis | null>(null)
  const [relatedAdjustments, setRelatedAdjustments] = useState<TeachingAdjustment[]>([])
  const [generating, setGenerating] = useState(false)
  const [loadingState, setLoadingState] = useState<{ loading: boolean; error: string | null }>({
    loading: true,
    error: null,
  })

  // Modal控制
  const [detailModalOpened, { open: openDetailModal, close: closeDetailModal }] =
    useDisclosure(false)
  const [newAnalysisModalOpened, { open: openNewAnalysisModal, close: closeNewAnalysisModal }] =
    useDisclosure(false)

  // 表单状态
  const [analysisForm, setAnalysisForm] = useState<LearningAnalysisRequest>({
    class_id: 0,
    course_id: 0,
    analysis_type: 'progress',
    analysis_period: 'weekly',
  })

  // 模拟数据 - 实际应用中应该从API获取
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

  // 加载分析数据
  const loadAnalyses = async () => {
    try {
      setLoadingState({ loading: true, error: null })
      const response = await aiService.getLearningAnalyses({ page: 1, size: 20 })
      setAnalyses(response.analyses)
      setLoadingState({ loading: false, error: null })
    } catch (error) {
      setLoadingState({
        loading: false,
        error: error instanceof Error ? error.message : '加载分析数据失败',
      })
    }
  }

  // 生成新分析
  const generateAnalysis = async () => {
    try {
      setGenerating(true)
      const newAnalysis = await aiService.analyzeLearningProgress(analysisForm)
      setAnalyses(prev => [newAnalysis, ...prev])
      closeNewAnalysisModal()
      // 重置表单
      setAnalysisForm({
        class_id: 0,
        course_id: 0,
        analysis_type: 'progress',
        analysis_period: 'weekly',
      })
    } catch (error) {
      // Handle error silently or show notification
    } finally {
      setGenerating(false)
    }
  }

  // 查看分析详情
  const viewAnalysisDetail = async (analysis: LearningAnalysis) => {
    setSelectedAnalysis(analysis)

    // 获取相关的调整建议
    try {
      const adjustments = await aiService.getTeachingAdjustments({
        class_id: analysis.class_id,
        course_id: analysis.course_id,
      })
      setRelatedAdjustments(adjustments.adjustments)
    } catch (error) {
      // Handle error silently or show notification
    }

    openDetailModal()
  }

  // 初始加载
  useEffect(() => {
    loadAnalyses()
  }, [])

  // 获取分析类型显示文本
  const getAnalysisTypeText = (type: string) => {
    switch (type) {
      case 'progress':
        return '学习进度'
      case 'difficulty':
        return '难点分析'
      case 'engagement':
        return '参与度分析'
      default:
        return type
    }
  }

  // 获取周期显示文本
  const getPeriodText = (period: string) => {
    switch (period) {
      case 'weekly':
        return '周度'
      case 'monthly':
        return '月度'
      case 'semester':
        return '学期'
      default:
        return period
    }
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={loadingState.loading} />

      {/* 页面头部 */}
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>学情分析</Title>
          <Text c="dimmed" size="sm">
            AI驱动的智能学习分析，帮助您更好地了解学生学习状况
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconRefresh size={16} />} variant="light" onClick={loadAnalyses}>
            刷新
          </Button>
          <Button leftSection={<IconBrain size={16} />} onClick={openNewAnalysisModal}>
            生成新分析
          </Button>
        </Group>
      </Group>

      {/* 错误提示 */}
      {loadingState.error && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red" mb="lg">
          {loadingState.error}
        </Alert>
      )}

      {/* 分析概览卡片 */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  总分析数
                </Text>
                <Text fw={700} size="xl">
                  {analyses.length}
                </Text>
              </div>
              <IconChartLine size={24} color="blue" />
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
                  {analyses.length > 0
                    ? Math.round(
                        (analyses.reduce((sum, a) => sum + a.confidence_score, 0) /
                          analyses.length) *
                          100
                      )
                    : 0}
                  %
                </Text>
              </div>
              <IconTarget size={24} color="green" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  风险学生
                </Text>
                <Text fw={700} size="xl">
                  {analyses.reduce((sum, a) => sum + a.risk_students.length, 0)}
                </Text>
              </div>
              <IconAlertTriangle size={24} color="orange" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  覆盖学生
                </Text>
                <Text fw={700} size="xl">
                  {analyses.reduce((sum, a) => sum + a.student_count, 0)}
                </Text>
              </div>
              <IconUsers size={24} color="purple" />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 学习预警面板 */}
      <Card shadow="sm" padding="lg" radius="md" withBorder mb="xl">
        <LearningAlertPanel maxAlerts={5} />
      </Card>

      {/* 分析列表 */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Group justify="space-between" mb="md">
          <Text fw={500} size="lg">
            分析记录
          </Text>
          <Group>
            <Menu>
              <Menu.Target>
                <ActionIcon variant="light">
                  <IconFilter size={16} />
                </ActionIcon>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item>按时间排序</Menu.Item>
                <Menu.Item>按置信度排序</Menu.Item>
                <Menu.Item>按类型筛选</Menu.Item>
              </Menu.Dropdown>
            </Menu>
            <ActionIcon variant="light">
              <IconDownload size={16} />
            </ActionIcon>
          </Group>
        </Group>

        {analyses.length > 0 ? (
          <ScrollArea>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>分析类型</Table.Th>
                  <Table.Th>周期</Table.Th>
                  <Table.Th>班级</Table.Th>
                  <Table.Th>学生数</Table.Th>
                  <Table.Th>风险学生</Table.Th>
                  <Table.Th>置信度</Table.Th>
                  <Table.Th>日期</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {analyses.map(analysis => (
                  <Table.Tr key={analysis.id}>
                    <Table.Td>
                      <Badge variant="light" color="blue">
                        {getAnalysisTypeText(analysis.analysis_type)}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{getPeriodText(analysis.analysis_period)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {classes.find(c => c.id === analysis.class_id)?.name ||
                          `班级${analysis.class_id}`}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{analysis.student_count}人</Text>
                    </Table.Td>
                    <Table.Td>
                      {analysis.risk_students.length > 0 ? (
                        <Badge color="orange" variant="light" size="sm">
                          {analysis.risk_students.length}人
                        </Badge>
                      ) : (
                        <Text size="sm" c="green">
                          无
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Progress
                          value={analysis.confidence_score * 100}
                          size="sm"
                          w={60}
                          color={
                            analysis.confidence_score > 0.8
                              ? 'green'
                              : analysis.confidence_score > 0.6
                                ? 'yellow'
                                : 'orange'
                          }
                        />
                        <Text size="xs">{Math.round(analysis.confidence_score * 100)}%</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{new Date(analysis.analysis_date).toLocaleDateString()}</Text>
                    </Table.Td>
                    <Table.Td>
                      <ActionIcon
                        variant="light"
                        size="sm"
                        onClick={() => viewAnalysisDetail(analysis)}
                      >
                        <IconEye size={14} />
                      </ActionIcon>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        ) : (
          <Text c="dimmed" ta="center" py="xl">
            暂无分析记录，点击"生成新分析"开始
          </Text>
        )}
      </Card>

      {/* 新分析Modal */}
      <Modal
        opened={newAnalysisModalOpened}
        onClose={closeNewAnalysisModal}
        title="生成新的学情分析"
        size="md"
      >
        <Stack>
          <Select
            label="选择课程"
            placeholder="请选择课程"
            data={courses.map(c => ({ value: c.id.toString(), label: c.name }))}
            value={analysisForm.course_id.toString()}
            onChange={value =>
              setAnalysisForm(prev => ({
                ...prev,
                course_id: parseInt(value || '0'),
              }))
            }
          />

          <Select
            label="选择班级"
            placeholder="请选择班级"
            data={classes
              .filter(c => c.course_id === analysisForm.course_id)
              .map(c => ({ value: c.id.toString(), label: c.name }))}
            value={analysisForm.class_id.toString()}
            onChange={value =>
              setAnalysisForm(prev => ({
                ...prev,
                class_id: parseInt(value || '0'),
              }))
            }
          />

          <Select
            label="分析类型"
            data={[
              { value: 'progress', label: '学习进度分析' },
              { value: 'difficulty', label: '学习难点分析' },
              { value: 'engagement', label: '学习参与度分析' },
            ]}
            value={analysisForm.analysis_type}
            onChange={value =>
              setAnalysisForm(prev => ({
                ...prev,
                analysis_type: value as 'progress' | 'difficulty' | 'engagement',
              }))
            }
          />

          <Select
            label="分析周期"
            data={[
              { value: 'weekly', label: '周度分析' },
              { value: 'monthly', label: '月度分析' },
              { value: 'semester', label: '学期分析' },
            ]}
            value={analysisForm.analysis_period}
            onChange={value =>
              setAnalysisForm(prev => ({
                ...prev,
                analysis_period: value as 'weekly' | 'monthly' | 'semester',
              }))
            }
          />

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={closeNewAnalysisModal}>
              取消
            </Button>
            <Button
              leftSection={<IconBrain size={16} />}
              loading={generating}
              onClick={generateAnalysis}
              disabled={analysisForm.class_id === 0 || analysisForm.course_id === 0}
            >
              开始分析
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 分析详情Modal */}
      <Modal opened={detailModalOpened} onClose={closeDetailModal} title="分析详情" size="xl">
        {selectedAnalysis && (
          <Stack>
            {/* 基本信息 */}
            <Card withBorder p="md">
              <Group justify="space-between" mb="md">
                <Text fw={500} size="lg">
                  基本信息
                </Text>
                <Group gap="xs">
                  <Badge variant="light" color="blue">
                    {getAnalysisTypeText(selectedAnalysis.analysis_type)}
                  </Badge>
                  <Badge variant="outline">{getPeriodText(selectedAnalysis.analysis_period)}</Badge>
                </Group>
              </Group>

              <Grid>
                <Grid.Col span={6}>
                  <Text size="sm" c="dimmed">
                    分析日期
                  </Text>
                  <Text fw={500}>
                    {new Date(selectedAnalysis.analysis_date).toLocaleDateString()}
                  </Text>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="sm" c="dimmed">
                    学生数量
                  </Text>
                  <Text fw={500}>{selectedAnalysis.student_count}人</Text>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="sm" c="dimmed">
                    AI置信度
                  </Text>
                  <Group gap="xs">
                    <RingProgress
                      size={40}
                      thickness={4}
                      sections={[{ value: selectedAnalysis.confidence_score * 100, color: 'blue' }]}
                    />
                    <Text fw={500}>{Math.round(selectedAnalysis.confidence_score * 100)}%</Text>
                  </Group>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="sm" c="dimmed">
                    风险学生
                  </Text>
                  <Text fw={500} c={selectedAnalysis.risk_students.length > 0 ? 'orange' : 'green'}>
                    {selectedAnalysis.risk_students.length}人
                  </Text>
                </Grid.Col>
              </Grid>
            </Card>

            {/* 关键洞察 */}
            {selectedAnalysis.insights.length > 0 && (
              <Card withBorder p="md">
                <Text fw={500} size="lg" mb="md">
                  关键洞察
                </Text>
                <Stack gap="xs">
                  {selectedAnalysis.insights.map((insight, index) => (
                    <Group key={index} align="flex-start" gap="xs">
                      <IconTrendingUp size={16} style={{ marginTop: 2 }} color="blue" />
                      <Text size="sm">{insight}</Text>
                    </Group>
                  ))}
                </Stack>
              </Card>
            )}

            {/* 相关调整建议 */}
            {relatedAdjustments.length > 0 && (
              <Card withBorder p="md">
                <Text fw={500} size="lg" mb="md">
                  相关调整建议
                </Text>
                <Stack gap="sm">
                  {relatedAdjustments.slice(0, 3).map(adjustment => (
                    <Card key={adjustment.id} withBorder radius="sm" p="sm">
                      <Group justify="space-between" mb="xs">
                        <Text fw={500} size="sm">
                          {adjustment.title}
                        </Text>
                        <Badge
                          color={
                            adjustment.priority_level === 'high'
                              ? 'red'
                              : adjustment.priority_level === 'medium'
                                ? 'yellow'
                                : 'green'
                          }
                          variant="light"
                          size="sm"
                        >
                          {adjustment.priority_level === 'high'
                            ? '高优先级'
                            : adjustment.priority_level === 'medium'
                              ? '中优先级'
                              : '低优先级'}
                        </Badge>
                      </Group>
                      <Text size="xs" c="dimmed" lineClamp={2}>
                        {adjustment.description}
                      </Text>
                    </Card>
                  ))}
                </Stack>
              </Card>
            )}
          </Stack>
        )}
      </Modal>
    </Container>
  )
}
