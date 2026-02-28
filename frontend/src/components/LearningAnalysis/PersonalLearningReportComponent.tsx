/**
 * 个人学情分析报告组件
 *
 * 功能：
 * 1. 能力评估雷达图
 * 2. 知识点掌握热力图
 * 3. 学习行为分析图表
 * 4. 进步趋势预测曲线
 * 5. 个性化建议列表
 * 6. 风险预警提示
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Grid,
  Title,
  Text,
  Badge,
  Progress,
  Alert,
  Button,
  Select,
  LoadingOverlay,
  Stack,
  Group,
  ActionIcon,
  Tooltip,
  Tabs,
  ScrollArea,
  Paper,
  ThemeIcon,
  List,
  Timeline,
  RingProgress,
  Center,
} from '@mantine/core'
import {
  IconUser,
  IconTrendingUp,
  IconAlertTriangle,
  IconTarget,
  IconRefresh,
  IconEye,
  IconChartLine,
  IconBulb,
  IconShield,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { personalReportApi, type PersonalLearningReport } from '../../api/learningAnalysisReport'

// 常量定义
const ABILITY_DIMENSIONS = {
  listening: '听力',
  reading: '阅读',
  writing: '写作',
  translation: '翻译',
  vocabulary: '词汇',
} as const

// UI常量
const UI_CONSTANTS = {
  CHART_HEIGHT: 400,
  SCROLL_AREA_HEIGHT: 300,
  LOADING_MIN_HEIGHT: 400,
  LOADING_CENTER_HEIGHT: 300,
  RING_PROGRESS_SIZE: 200,
  RING_PROGRESS_THICKNESS: 20,
  ICON_SIZE_LARGE: 48,
  ICON_SIZE_MEDIUM: 20,
  ICON_SIZE_SMALL: 16,
  ICON_SIZE_TINY: 14,
  ICON_SIZE_MINI: 12,
  SELECT_WIDTH: 120,
  TIMELINE_BULLET_SIZE: 24,
  TIMELINE_LINE_WIDTH: 2,
} as const

const MASTERY_LEVELS = {
  0: { label: '未掌握', color: 'red' },
  25: { label: '初步掌握', color: 'orange' },
  50: { label: '基本掌握', color: 'yellow' },
  75: { label: '熟练掌握', color: 'blue' },
  90: { label: '精通', color: 'green' },
} as const

const RISK_LEVELS = {
  low: { label: '低风险', color: 'green', icon: IconShield },
  medium: { label: '中等风险', color: 'yellow', icon: IconAlertTriangle },
  high: { label: '高风险', color: 'orange', icon: IconAlertTriangle },
  critical: { label: '严重风险', color: 'red', icon: IconAlertTriangle },
} as const

interface PersonalLearningReportComponentProps {
  studentId: number
  reportId?: string
  onReportUpdate?: (report: PersonalLearningReport) => void
  showControls?: boolean
  compactMode?: boolean
}

const PersonalLearningReportComponent: React.FC<PersonalLearningReportComponentProps> = ({
  studentId,
  reportId,
  onReportUpdate,
  showControls = true,
  compactMode: _compactMode = false,
}) => {
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('30')
  const [refreshing, setRefreshing] = useState(false)

  // 获取个人学情报告
  const {
    data: report,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['personalLearningReport', studentId, reportId],
    queryFn: () => personalReportApi.getPersonalReport(studentId, reportId),
    staleTime: 5 * 60 * 1000, // 5分钟
    refetchOnWindowFocus: false,
  })

  // 生成新报告
  const generateReportMutation = useMutation({
    mutationFn: (params: {
      time_period: { start_date: string; end_date: string }
      include_predictions: boolean
      include_recommendations: boolean
    }) => personalReportApi.generatePersonalReport(studentId, params),
    onSuccess: () => {
      notifications.show({
        title: '报告生成成功',
        message: '新的学情分析报告已生成',
        color: 'green',
      })
      refetch()
    },
    onError: error => {
      notifications.show({
        title: '报告生成失败',
        message: error instanceof Error ? error.message : '生成报告时发生错误',
        color: 'red',
      })
    },
  })

  // 刷新报告数据
  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      await refetch()
      notifications.show({
        title: '数据已更新',
        message: '学情分析报告数据已刷新',
        color: 'blue',
      })
    } catch (error) {
      notifications.show({
        title: '刷新失败',
        message: '刷新数据时发生错误',
        color: 'red',
      })
    } finally {
      setRefreshing(false)
    }
  }, [refetch])

  // 生成新报告
  const handleGenerateReport = useCallback(() => {
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - parseInt(selectedTimeRange))

    generateReportMutation.mutate({
      time_period: {
        start_date: startDate.toISOString().split('T')[0]!,
        end_date: endDate.toISOString().split('T')[0]!,
      },
      include_predictions: true,
      include_recommendations: true,
    })
  }, [selectedTimeRange, generateReportMutation])

  // 图表数据处理函数将在后续版本中实现

  // 获取掌握程度标签
  const getMasteryLabel = useCallback((level: number) => {
    const thresholds = Object.keys(MASTERY_LEVELS)
      .map(Number)
      .sort((a, b) => b - a)
    const threshold = thresholds.find(t => level >= t) || 0
    return MASTERY_LEVELS[threshold as keyof typeof MASTERY_LEVELS]
  }, [])

  // 获取风险等级信息
  const getRiskInfo = useCallback((level: string) => {
    return RISK_LEVELS[level as keyof typeof RISK_LEVELS] || RISK_LEVELS.low
  }, [])

  useEffect(() => {
    if (report && onReportUpdate) {
      onReportUpdate(report)
    }
  }, [report, onReportUpdate])

  if (isLoading) {
    return (
      <Card
        withBorder
        padding="xl"
        style={{ position: 'relative', minHeight: UI_CONSTANTS.LOADING_MIN_HEIGHT }}
      >
        <LoadingOverlay visible={true} overlayProps={{ radius: 'sm', blur: 2 }} />
        <Center style={{ height: UI_CONSTANTS.LOADING_CENTER_HEIGHT }}>
          <Text>正在加载学情分析报告...</Text>
        </Center>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert color="red" title="加载失败" icon={<IconAlertTriangle size={16} />}>
        <Text>无法加载学情分析报告，请稍后重试。</Text>
        <Button variant="light" size="sm" mt="sm" onClick={() => refetch()}>
          重新加载
        </Button>
      </Alert>
    )
  }

  if (!report) {
    return (
      <Card withBorder padding="xl">
        <Stack align="center" gap="md">
          <IconUser size={UI_CONSTANTS.ICON_SIZE_LARGE} color="gray" />
          <Text size="lg" c="dimmed">
            暂无学情分析报告
          </Text>
          <Button onClick={handleGenerateReport} loading={generateReportMutation.isPending}>
            生成报告
          </Button>
        </Stack>
      </Card>
    )
  }

  return (
    <Stack gap="md">
      {/* 报告头部 */}
      <Card withBorder padding="md">
        <Group justify="space-between" align="center">
          <Group>
            <ThemeIcon size="lg" variant="light" color="blue">
              <IconUser size={UI_CONSTANTS.ICON_SIZE_MEDIUM} />
            </ThemeIcon>
            <div>
              <Title order={3}>{report.student_name} 的学情分析报告</Title>
              <Text size="sm" c="dimmed">
                报告时间：{new Date(report.report_date).toLocaleDateString()} | 分析周期：
                {new Date(report.report_period.start_date).toLocaleDateString()} -{' '}
                {new Date(report.report_period.end_date).toLocaleDateString()}
              </Text>
            </div>
          </Group>

          {showControls && (
            <Group>
              <Select
                value={selectedTimeRange}
                onChange={value => setSelectedTimeRange(value || '30')}
                data={[
                  { value: '7', label: '最近7天' },
                  { value: '30', label: '最近30天' },
                  { value: '90', label: '最近90天' },
                ]}
                size="sm"
                w={120}
              />
              <Tooltip label="刷新数据">
                <ActionIcon
                  variant="light"
                  onClick={handleRefresh}
                  loading={refreshing}
                  aria-label="刷新学情数据"
                >
                  <IconRefresh size={UI_CONSTANTS.ICON_SIZE_SMALL} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="生成新报告">
                <ActionIcon
                  variant="light"
                  onClick={handleGenerateReport}
                  loading={generateReportMutation.isPending}
                  aria-label="生成新的个人学情报告"
                >
                  <IconRefresh size={UI_CONSTANTS.ICON_SIZE_SMALL} />
                </ActionIcon>
              </Tooltip>
            </Group>
          )}
        </Group>
      </Card>

      {/* 报告内容 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconEye size={16} />}>
            总览
          </Tabs.Tab>
          <Tabs.Tab value="ability" leftSection={<IconTarget size={16} />}>
            能力评估
          </Tabs.Tab>
          <Tabs.Tab value="knowledge" leftSection={<IconTarget size={16} />}>
            知识掌握
          </Tabs.Tab>
          <Tabs.Tab value="progress" leftSection={<IconChartLine size={16} />}>
            进步趋势
          </Tabs.Tab>
          <Tabs.Tab value="recommendations" leftSection={<IconBulb size={16} />}>
            学习建议
          </Tabs.Tab>
          <Tabs.Tab value="risks" leftSection={<IconShield size={16} />}>
            风险预警
          </Tabs.Tab>
        </Tabs.List>

        {/* 总览标签页 */}
        <Tabs.Panel value="overview" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder padding="md" h="100%">
                <Title order={4} mb="md">
                  综合评分
                </Title>
                <Center>
                  <RingProgress
                    size={200}
                    thickness={20}
                    sections={[{ value: report.ability_assessment.overall_score, color: 'blue' }]}
                    label={
                      <Center>
                        <div style={{ textAlign: 'center' }}>
                          <Text size="xl" fw={700}>
                            {report.ability_assessment.overall_score}
                          </Text>
                          <Text size="sm" c="dimmed">
                            综合评分
                          </Text>
                        </div>
                      </Center>
                    }
                  />
                </Center>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder padding="md" h="100%">
                <Title order={4} mb="md">
                  关键指标
                </Title>
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Text>学习一致性</Text>
                    <Badge color="blue">{report.behavior_analysis.learning_consistency}%</Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text>参与度</Text>
                    <Badge color="green">{report.behavior_analysis.engagement_level}%</Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text>日均学习时长</Text>
                    <Badge color="orange">{report.behavior_analysis.daily_study_time}分钟</Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text>评估置信度</Text>
                    <Badge color="purple">
                      {Math.round(report.ability_assessment.confidence_level * 100)}%
                    </Badge>
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 能力评估标签页 */}
        <Tabs.Panel value="ability" pt="md">
          <Card withBorder padding="md">
            <Title order={4} mb="md">
              五维能力评估
            </Title>
            <div
              style={{
                height: 400,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text c="dimmed">雷达图组件将在后续版本中实现</Text>
            </div>
            <Grid mt="md">
              {Object.entries(ABILITY_DIMENSIONS).map(([key, label]) => (
                <Grid.Col span={6} key={key}>
                  <Group justify="space-between">
                    <Text size="sm">{label}</Text>
                    <Badge color="blue">
                      {report.ability_assessment[key as keyof typeof ABILITY_DIMENSIONS]}分
                    </Badge>
                  </Group>
                  <Progress
                    value={report.ability_assessment[key as keyof typeof ABILITY_DIMENSIONS]}
                    size="sm"
                    mt={4}
                  />
                </Grid.Col>
              ))}
            </Grid>
          </Card>
        </Tabs.Panel>

        {/* 知识掌握标签页 */}
        <Tabs.Panel value="knowledge" pt="md">
          <Grid>
            <Grid.Col span={12}>
              <Card withBorder padding="md">
                <Title order={4} mb="md">
                  知识点掌握热力图
                </Title>
                <div
                  style={{
                    height: 300,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Text c="dimmed">知识点热力图组件将在后续版本中实现</Text>
                </div>
              </Card>
            </Grid.Col>
            <Grid.Col span={12}>
              <Card withBorder padding="md">
                <Title order={4} mb="md">
                  知识点详细分析
                </Title>
                <ScrollArea h={UI_CONSTANTS.SCROLL_AREA_HEIGHT}>
                  <Stack gap="xs">
                    {report.knowledge_mastery.slice(0, 20).map(point => {
                      const mastery = getMasteryLabel(point.mastery_level)
                      return (
                        <Paper key={point.knowledge_point_id} p="sm" withBorder>
                          <Group justify="space-between">
                            <div>
                              <Text fw={500}>{point.knowledge_point_name}</Text>
                              <Text size="sm" c="dimmed">
                                {point.category}
                              </Text>
                            </div>
                            <Group>
                              <Badge color={mastery.color} variant="light">
                                {mastery.label}
                              </Badge>
                              <Text size="sm">{point.mastery_level}%</Text>
                            </Group>
                          </Group>
                          <Progress
                            value={point.mastery_level}
                            size="xs"
                            mt="xs"
                            color={mastery.color}
                          />
                          <Group mt="xs" gap="xs">
                            <Text size="xs" c="dimmed">
                              练习次数: {point.practice_count}
                            </Text>
                            <Text size="xs" c="dimmed">
                              错误次数: {point.error_count}
                            </Text>
                            <Text size="xs" c="dimmed">
                              预计掌握: {point.estimated_time_to_master}小时
                            </Text>
                          </Group>
                        </Paper>
                      )
                    })}
                  </Stack>
                </ScrollArea>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 进步趋势标签页 */}
        <Tabs.Panel value="progress" pt="md">
          <Card withBorder padding="md">
            <Title order={4} mb="md">
              学习进步趋势预测
            </Title>
            <div
              style={{
                height: 400,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text c="dimmed">进步趋势图表组件将在后续版本中实现</Text>
            </div>
            <Grid mt="md">
              <Grid.Col span={6}>
                <Paper p="md" withBorder>
                  <Text size="sm" c="dimmed" mb="xs">
                    趋势方向
                  </Text>
                  <Group>
                    <ThemeIcon
                      color={
                        report.progress_prediction.trend_direction === 'improving'
                          ? 'green'
                          : report.progress_prediction.trend_direction === 'declining'
                            ? 'red'
                            : 'yellow'
                      }
                      variant="light"
                    >
                      <IconTrendingUp size={16} />
                    </ThemeIcon>
                    <Text fw={500}>
                      {report.progress_prediction.trend_direction === 'improving'
                        ? '上升'
                        : report.progress_prediction.trend_direction === 'declining'
                          ? '下降'
                          : '稳定'}
                    </Text>
                  </Group>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper p="md" withBorder>
                  <Text size="sm" c="dimmed" mb="xs">
                    预期提升率
                  </Text>
                  <Text size="lg" fw={700} c="blue">
                    {report.progress_prediction.expected_improvement_rate}%/月
                  </Text>
                </Paper>
              </Grid.Col>
            </Grid>
          </Card>
        </Tabs.Panel>

        {/* 学习建议标签页 */}
        <Tabs.Panel value="recommendations" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder padding="md" h="100%">
                <Title order={4} mb="md">
                  优先改进领域
                </Title>
                <Stack gap="sm">
                  {report.recommendations.priority_areas.map((area, index) => (
                    <Paper key={index} p="sm" withBorder>
                      <Group justify="space-between" mb="xs">
                        <Text fw={500}>{area.area}</Text>
                        <Badge
                          color={
                            area.importance === 'high'
                              ? 'red'
                              : area.importance === 'medium'
                                ? 'orange'
                                : 'blue'
                          }
                          variant="light"
                        >
                          {area.importance === 'high'
                            ? '高优先级'
                            : area.importance === 'medium'
                              ? '中优先级'
                              : '低优先级'}
                        </Badge>
                      </Group>
                      <Text size="sm" c="dimmed" mb="xs">
                        建议投入时间: {area.recommended_time}小时/周
                      </Text>
                      <List size="sm">
                        {area.specific_actions.slice(0, 3).map((action, actionIndex) => (
                          <List.Item key={actionIndex}>{action}</List.Item>
                        ))}
                      </List>
                    </Paper>
                  ))}
                </Stack>
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder padding="md" h="100%">
                <Title order={4} mb="md">
                  学习计划
                </Title>
                <Timeline
                  active={0}
                  bulletSize={UI_CONSTANTS.TIMELINE_BULLET_SIZE}
                  lineWidth={UI_CONSTANTS.TIMELINE_LINE_WIDTH}
                >
                  {report.recommendations.study_plan.slice(0, 4).map(week => (
                    <Timeline.Item
                      key={week.week}
                      bullet={<IconTarget size={UI_CONSTANTS.ICON_SIZE_MINI} />}
                      title={`第${week.week}周`}
                    >
                      <Text size="sm" c="dimmed" mb="xs">
                        重点领域: {week.focus_areas.join(', ')}
                      </Text>
                      <List size="sm">
                        {week.daily_tasks.slice(0, 2).map((task, index) => (
                          <List.Item key={index}>{task}</List.Item>
                        ))}
                      </List>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 风险预警标签页 */}
        <Tabs.Panel value="risks" pt="md">
          <Stack gap="md">
            {(() => {
              const riskInfo = getRiskInfo(report.risk_warning.risk_level)
              const RiskIcon = riskInfo.icon
              return (
                <Alert
                  color={riskInfo.color}
                  title={`风险等级: ${riskInfo.label}`}
                  icon={<RiskIcon size={16} />}
                >
                  当前学习状态存在{riskInfo.label}，需要关注以下风险因素。
                </Alert>
              )
            })()}

            <Grid>
              <Grid.Col span={{ base: 12, md: 8 }}>
                <Card withBorder padding="md">
                  <Title order={4} mb="md">
                    风险因素分析
                  </Title>
                  <Stack gap="sm">
                    {report.risk_warning.risk_factors.map((factor, index) => (
                      <Paper key={index} p="sm" withBorder>
                        <Group justify="space-between" mb="xs">
                          <Text fw={500}>{factor.factor}</Text>
                          <Badge
                            color={
                              factor.severity >= 80
                                ? 'red'
                                : factor.severity >= 60
                                  ? 'orange'
                                  : factor.severity >= 40
                                    ? 'yellow'
                                    : 'blue'
                            }
                            variant="light"
                          >
                            严重程度: {factor.severity}%
                          </Badge>
                        </Group>
                        <Text size="sm" mb="xs">
                          {factor.description}
                        </Text>
                        <Text size="sm" c="blue">
                          <strong>建议措施:</strong> {factor.suggested_intervention}
                        </Text>
                        <Progress value={factor.severity} size="xs" mt="xs" />
                      </Paper>
                    ))}
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={{ base: 12, md: 4 }}>
                <Card withBorder padding="md">
                  <Title order={4} mb="md">
                    干预建议
                  </Title>
                  <List size="sm" spacing="xs">
                    {report.risk_warning.intervention_recommendations.map(
                      (recommendation, index) => (
                        <List.Item key={index} icon={<IconBulb size={14} />}>
                          {recommendation}
                        </List.Item>
                      )
                    )}
                  </List>
                </Card>
              </Grid.Col>
            </Grid>
          </Stack>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}

export default PersonalLearningReportComponent
