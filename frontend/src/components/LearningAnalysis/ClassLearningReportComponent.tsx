/**
 * 班级学情分析报告组件
 *
 * 功能：
 * 1. 整体水平评估仪表盘
 * 2. 知识点掌握分布图
 * 3. 学习进度监控面板
 * 4. 教学效果评估图表
 * 5. 差异化分析视图
 * 6. 改进建议面板
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Grid,
  Title,
  Text,
  Badge,
  Alert,
  Button,
  Select,
  LoadingOverlay,
  Stack,
  Group,
  ActionIcon,
  Tooltip,
  Tabs,
  ThemeIcon,
  List,
  RingProgress,
  Center,
  SimpleGrid,
} from '@mantine/core'
import {
  IconUsers,
  IconChartBar,
  IconTrendingUp,
  IconAlertTriangle,
  IconTarget,
  IconRefresh,
  IconEye,
  IconAward,
  IconSchool,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { classReportApi, type ClassLearningReport } from '../../api/learningAnalysisReport'

// 常量定义将在后续版本中使用

interface ClassLearningReportComponentProps {
  classId: number
  teacherId: number
  reportId?: string
  onReportUpdate?: (report: ClassLearningReport) => void
  showControls?: boolean
  compactMode?: boolean
}

const ClassLearningReportComponent: React.FC<ClassLearningReportComponentProps> = ({
  classId,
  teacherId: _teacherId,
  reportId,
  onReportUpdate,
  showControls = true,
  compactMode: _compactMode = false,
}) => {
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('30')
  const [refreshing, setRefreshing] = useState(false)

  // 获取班级学情报告
  const {
    data: report,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['classLearningReport', classId, reportId],
    queryFn: () => classReportApi.getClassReport(classId, reportId),
    staleTime: 5 * 60 * 1000, // 5分钟
    refetchOnWindowFocus: false,
  })

  // 生成新报告
  const generateReportMutation = useMutation({
    mutationFn: (params: {
      time_period: { start_date: string; end_date: string }
      include_individual_analysis: boolean
      include_teaching_effectiveness: boolean
    }) => classReportApi.generateClassReport(classId, params),
    onSuccess: () => {
      notifications.show({
        title: '报告生成成功',
        message: '新的班级学情分析报告已生成',
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
        message: '班级学情分析报告数据已刷新',
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
      include_individual_analysis: true,
      include_teaching_effectiveness: true,
    })
  }, [selectedTimeRange, generateReportMutation])

  // 这些数据处理函数将在后续版本中实现图表功能时使用

  useEffect(() => {
    if (report && onReportUpdate) {
      onReportUpdate(report)
    }
  }, [report, onReportUpdate])

  if (isLoading) {
    return (
      <Card withBorder padding="xl" style={{ position: 'relative', minHeight: 400 }}>
        <LoadingOverlay visible={true} overlayProps={{ radius: 'sm', blur: 2 }} />
        <Center style={{ height: 300 }}>
          <Text>正在加载班级学情分析报告...</Text>
        </Center>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert color="red" title="加载失败" icon={<IconAlertTriangle size={16} />}>
        <Text>无法加载班级学情分析报告，请稍后重试。</Text>
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
          <IconUsers size={48} color="gray" />
          <Text size="lg" c="dimmed">
            暂无班级学情分析报告
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
              <IconUsers size={20} />
            </ThemeIcon>
            <div>
              <Title order={3}>{report.class_name} 班级学情分析报告</Title>
              <Text size="sm" c="dimmed">
                任课教师：{report.teacher_name} | 学生人数：
                {report.overall_assessment.total_students}人 | 报告时间：
                {new Date(report.report_date).toLocaleDateString()}
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
                <ActionIcon variant="light" onClick={handleRefresh} loading={refreshing}>
                  <IconRefresh size={16} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="生成新报告">
                <ActionIcon
                  variant="light"
                  onClick={handleGenerateReport}
                  loading={generateReportMutation.isPending}
                >
                  <IconChartBar size={16} />
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
          <Tabs.Tab value="performance" leftSection={<IconChartBar size={16} />}>
            整体表现
          </Tabs.Tab>
          <Tabs.Tab value="knowledge" leftSection={<IconTarget size={16} />}>
            知识掌握
          </Tabs.Tab>
          <Tabs.Tab value="progress" leftSection={<IconTrendingUp size={16} />}>
            学习进度
          </Tabs.Tab>
          <Tabs.Tab value="teaching" leftSection={<IconSchool size={16} />}>
            教学效果
          </Tabs.Tab>
          <Tabs.Tab value="differentiation" leftSection={<IconUsers size={16} />}>
            差异化分析
          </Tabs.Tab>
        </Tabs.List>

        {/* 总览标签页 */}
        <Tabs.Panel value="overview" pt="md">
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
            <Card withBorder padding="md" style={{ textAlign: 'center' }}>
              <ThemeIcon size="xl" variant="light" color="blue" mx="auto" mb="sm">
                <IconUsers size={24} />
              </ThemeIcon>
              <Text size="xl" fw={700}>
                {report.overall_assessment.total_students}
              </Text>
              <Text size="sm" c="dimmed">
                学生总数
              </Text>
            </Card>

            <Card withBorder padding="md" style={{ textAlign: 'center' }}>
              <ThemeIcon size="xl" variant="light" color="green" mx="auto" mb="sm">
                <IconAward size={24} />
              </ThemeIcon>
              <Text size="xl" fw={700}>
                {report.overall_assessment.average_scores.overall_score}
              </Text>
              <Text size="sm" c="dimmed">
                班级平均分
              </Text>
            </Card>

            <Card withBorder padding="md" style={{ textAlign: 'center' }}>
              <ThemeIcon size="xl" variant="light" color="orange" mx="auto" mb="sm">
                <IconTrendingUp size={24} />
              </ThemeIcon>
              <Text size="xl" fw={700}>
                {report.overall_assessment.improvement_rate}%
              </Text>
              <Text size="sm" c="dimmed">
                月提升率
              </Text>
            </Card>

            <Card withBorder padding="md" style={{ textAlign: 'center' }}>
              <ThemeIcon size="xl" variant="light" color="purple" mx="auto" mb="sm">
                <IconChartBar size={24} />
              </ThemeIcon>
              <Text size="xl" fw={700}>
                {report.overall_assessment.class_ranking.percentile}%
              </Text>
              <Text size="sm" c="dimmed">
                年级排名百分位
              </Text>
            </Card>
          </SimpleGrid>

          <Grid mt="md">
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card withBorder padding="md">
                <Title order={4} mb="md">
                  关键成就与挑战
                </Title>
                <Grid>
                  <Grid.Col span={6}>
                    <Text fw={500} c="green" mb="xs">
                      主要成就
                    </Text>
                    <List size="sm" spacing="xs">
                      {report.summary.key_achievements.slice(0, 3).map((achievement, index) => (
                        <List.Item key={index}>{achievement}</List.Item>
                      ))}
                    </List>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text fw={500} c="orange" mb="xs">
                      主要挑战
                    </Text>
                    <List size="sm" spacing="xs">
                      {report.summary.main_challenges.slice(0, 3).map((challenge, index) => (
                        <List.Item key={index}>{challenge}</List.Item>
                      ))}
                    </List>
                  </Grid.Col>
                </Grid>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder padding="md">
                <Title order={4} mb="md">
                  学习进度概览
                </Title>
                <Center>
                  <RingProgress
                    size={150}
                    thickness={16}
                    sections={[
                      { value: report.progress_monitoring.overall_progress, color: 'blue' },
                    ]}
                    label={
                      <Center>
                        <div style={{ textAlign: 'center' }}>
                          <Text size="lg" fw={700}>
                            {report.progress_monitoring.overall_progress}%
                          </Text>
                          <Text size="xs" c="dimmed">
                            整体进度
                          </Text>
                        </div>
                      </Center>
                    }
                  />
                </Center>
                <Stack gap="xs" mt="md">
                  <Group justify="space-between">
                    <Text size="sm">按时完成</Text>
                    <Badge color="green">{report.progress_monitoring.on_track_students}人</Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">进度落后</Text>
                    <Badge color="orange">{report.progress_monitoring.behind_students}人</Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm">进度超前</Text>
                    <Badge color="blue">{report.progress_monitoring.ahead_students}人</Badge>
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 其他标签页内容将在下一部分实现 */}
      </Tabs>
    </Stack>
  )
}

export default ClassLearningReportComponent
