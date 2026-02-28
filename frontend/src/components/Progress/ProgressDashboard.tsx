/**
 * 学习进度仪表盘组件
 */

import React, { useState, useEffect } from 'react'
import {
  Container,
  Title,
  Text,
  Card,
  Grid,
  Group,
  Stack,
  Badge,
  Alert,
  Tabs,
  Button,
  ActionIcon,
  Tooltip,
  Modal,
  Switch,
  Divider,
  Timeline,
  ThemeIcon,
  Center,
  Loader,
} from '@mantine/core'
import {
  IconDashboard,
  IconTarget,
  IconTrendingUp,
  IconClock,
  IconSettings,
  IconBell,
  IconDownload,
  IconRefresh,
  IconTrophy,
  IconAlertTriangle,
  IconCheck,
  IconBrain,
  IconCertificate,
} from '@tabler/icons-react'
import {
  useProgressMonitoring,
  useRealTimeProgress,
  useAchievements,
  useSetLearningReminder,
  useExportProgressReport,
  useRefreshProgressData,
} from '@/hooks/useProgressData'
import { ProgressCharts } from './ProgressCharts'
import { DualDriveMonitor } from './DualDriveMonitor'
import { AdaptiveAlgorithmDisplay } from './AdaptiveAlgorithmDisplay'
import { StandardizationInterface } from './StandardizationInterface'
import { KnowledgeHeatmap } from './KnowledgeHeatmap'

interface ProgressDashboardProps {
  studentId?: number
  showHeader?: boolean
  compactMode?: boolean
}

export const ProgressDashboard: React.FC<ProgressDashboardProps> = ({
  studentId,
  showHeader = true,
  compactMode = false,
}) => {
  const [settingsOpened, setSettingsOpened] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [isComponentMounted, setIsComponentMounted] = useState(true)

  // 组件卸载清理
  useEffect(() => {
    return () => {
      setIsComponentMounted(false)
    }
  }, [])

  // 数据获取
  const {
    data: monitoring,
    isLoading: monitoringLoading,
    error: monitoringError,
  } = useProgressMonitoring()
  const {
    data: realtime,
    isLoading: realtimeLoading,
    error: realtimeError,
  } = useRealTimeProgress(isComponentMounted)
  const { data: achievements, error: achievementsError } = useAchievements()

  // 操作
  const setReminderMutation = useSetLearningReminder()
  const exportReportMutation = useExportProgressReport()
  const refreshData = useRefreshProgressData()

  const handleExportReport = (format: 'pdf' | 'excel' | 'csv') => {
    exportReportMutation.mutate({ format, periodDays: 30 })
  }

  const handleSetReminder = (
    type: 'daily' | 'goal_deadline' | 'performance_drop',
    enabled: boolean
  ) => {
    setReminderMutation.mutate({
      type,
      enabled,
      settings: {
        time: '09:00',
        frequency: 'daily',
      },
    })
  }

  // 检查是否有关键错误
  const hasError = monitoringError || realtimeError

  if (monitoringLoading || realtimeLoading) {
    return (
      <Container size="xl" py="md">
        <Center h={400}>
          <Loader size="lg" />
        </Center>
      </Container>
    )
  }

  if (hasError) {
    return (
      <Container size="xl" py="md">
        <Alert icon={<IconAlertTriangle size={16} />} title="数据加载失败" color="red">
          <Text size="sm">无法加载进度数据，请检查网络连接或稍后重试。</Text>
          <Group mt="md">
            <Button variant="light" onClick={refreshData}>
              重新加载
            </Button>
          </Group>
        </Alert>
        {achievementsError && (
          <Alert
            icon={<IconAlertTriangle size={16} />}
            title="成就数据加载失败"
            color="orange"
            mt="md"
          >
            <Text size="sm">成就数据暂时无法加载，其他功能正常使用。</Text>
          </Alert>
        )}
      </Container>
    )
  }

  return (
    <Container size="xl" py="md">
      {/* 页面标题和控制 */}
      {showHeader && (
        <Group justify="space-between" mb="lg">
          <div>
            <Title order={2}>学习进度仪表盘</Title>
            <Text c="dimmed" size="sm">
              实时监控学习进度，分析学习效果
            </Text>
          </div>
          <Group>
            <Tooltip label="刷新数据">
              <ActionIcon variant="light" size="lg" onClick={refreshData}>
                <IconRefresh size={20} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="导出报告">
              <Button
                leftSection={<IconDownload size={16} />}
                variant="light"
                onClick={() => handleExportReport('pdf')}
                loading={exportReportMutation.isPending}
              >
                导出
              </Button>
            </Tooltip>
            <Tooltip label="设置">
              <ActionIcon variant="light" size="lg" onClick={() => setSettingsOpened(true)}>
                <IconSettings size={20} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      )}

      {/* 实时状态卡片 */}
      {!compactMode && (
        <Grid mb="lg">
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder padding="md" h="100%">
              <Group justify="space-between" mb="xs">
                <Text size="sm" c="dimmed">
                  今日学习时间
                </Text>
                <IconClock size={16} color="blue" />
              </Group>
              <Text size="xl" fw={700} c="blue">
                {Math.floor((realtime?.today_progress?.['study_time'] || 0) / 60)}h{' '}
                {(realtime?.today_progress?.['study_time'] || 0) % 60}m
              </Text>
              <Text size="xs" c="dimmed">
                已完成 {realtime?.today_progress?.['completed_tasks'] || 0} 个任务
              </Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder padding="md" h="100%">
              <Group justify="space-between" mb="xs">
                <Text size="sm" c="dimmed">
                  今日准确率
                </Text>
                <IconTarget size={16} color="green" />
              </Group>
              <Text size="xl" fw={700} c="green">
                {Math.round((realtime?.today_progress?.['accuracy_rate'] || 0) * 100)}%
              </Text>
              <Text size="xs" c="dimmed">
                连续学习 {realtime?.today_progress?.['streak_days'] || 0} 天
              </Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder padding="md" h="100%">
              <Group justify="space-between" mb="xs">
                <Text size="sm" c="dimmed">
                  整体进度
                </Text>
                <IconTrendingUp size={16} color="orange" />
              </Group>
              <Text size="xl" fw={700} c="orange">
                {Math.round(monitoring?.progress_metrics?.['overall_score'] || 0)}%
              </Text>
              <Text size="xs" c="dimmed">
                {monitoring?.overall_status === 'excellent'
                  ? '表现优秀'
                  : monitoring?.overall_status === 'good'
                    ? '表现良好'
                    : monitoring?.overall_status === 'needs_attention'
                      ? '需要关注'
                      : '需要改进'}
              </Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Card withBorder padding="md" h="100%">
              <Group justify="space-between" mb="xs">
                <Text size="sm" c="dimmed">
                  获得成就
                </Text>
                <IconTrophy size={16} color="yellow" />
              </Group>
              <Text size="xl" fw={700} c="yellow">
                {achievements?.length || 0}
              </Text>
              <Text size="xs" c="dimmed">
                本月新增{' '}
                {achievements?.filter(
                  a => new Date(a.achieved_at) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
                ).length || 0}{' '}
                个
              </Text>
            </Card>
          </Grid.Col>
        </Grid>
      )}

      {/* 主要内容区域 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconDashboard size={16} />}>
            总览
          </Tabs.Tab>
          <Tabs.Tab value="dual-drive" leftSection={<IconRefresh size={16} />}>
            双驱动机制
          </Tabs.Tab>
          <Tabs.Tab value="adaptive" leftSection={<IconBrain size={16} />}>
            自适应算法
          </Tabs.Tab>
          <Tabs.Tab value="heatmap" leftSection={<IconTarget size={16} />}>
            知识热力图
          </Tabs.Tab>
          <Tabs.Tab value="standards" leftSection={<IconCertificate size={16} />}>
            标准对接
          </Tabs.Tab>
          <Tabs.Tab value="charts" leftSection={<IconTrendingUp size={16} />}>
            图表分析
          </Tabs.Tab>
          <Tabs.Tab value="achievements" leftSection={<IconTrophy size={16} />}>
            成就记录
          </Tabs.Tab>
          <Tabs.Tab value="alerts" leftSection={<IconBell size={16} />}>
            提醒通知
          </Tabs.Tab>
        </Tabs.List>

        {/* 双驱动机制面板 */}
        <Tabs.Panel value="dual-drive" pt="md">
          <DualDriveMonitor studentId={studentId} />
        </Tabs.Panel>

        {/* 自适应算法面板 */}
        <Tabs.Panel value="adaptive" pt="md">
          <AdaptiveAlgorithmDisplay studentId={studentId} />
        </Tabs.Panel>

        {/* 知识热力图面板 */}
        <Tabs.Panel value="heatmap" pt="md">
          <KnowledgeHeatmap studentId={studentId} />
        </Tabs.Panel>

        {/* 标准对接面板 */}
        <Tabs.Panel value="standards" pt="md">
          <StandardizationInterface />
        </Tabs.Panel>

        {/* 总览面板 */}
        <Tabs.Panel value="overview" pt="md">
          <Grid>
            {/* 最近活动 */}
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder padding="md" h="100%">
                <Title order={4} mb="md">
                  最近活动
                </Title>
                <Timeline active={-1}>
                  {realtime?.suggestions && Array.isArray(realtime.suggestions) ? (
                    realtime.suggestions.slice(0, 5).map((suggestion: string, index: number) => (
                      <Timeline.Item
                        key={index}
                        title={suggestion}
                        bullet={
                          <ThemeIcon size={20} color="blue" radius="xl">
                            <IconCheck size={12} />
                          </ThemeIcon>
                        }
                      >
                        <Text size="xs" c="dimmed">
                          {new Date().toLocaleString()}
                        </Text>
                      </Timeline.Item>
                    ))
                  ) : (
                    <Text c="dimmed" size="sm">
                      暂无最近活动
                    </Text>
                  )}
                </Timeline>
              </Card>
            </Grid.Col>

            {/* 异常提醒 */}
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder padding="md" h="100%">
                <Title order={4} mb="md">
                  异常提醒
                </Title>
                <Stack gap="xs">
                  {monitoring?.anomalies && Array.isArray(monitoring.anomalies) ? (
                    monitoring.anomalies.map((anomaly: any, index: number) => (
                      <Alert
                        key={index}
                        icon={<IconAlertTriangle size={16} />}
                        color={
                          anomaly?.['severity'] === 'high'
                            ? 'red'
                            : anomaly?.['severity'] === 'medium'
                              ? 'orange'
                              : 'yellow'
                        }
                        title={anomaly?.['type'] || '异常'}
                      >
                        <Text size="sm">{anomaly?.['description'] || '未知异常'}</Text>
                        {anomaly?.['suggestions'] &&
                          Array.isArray(anomaly['suggestions']) &&
                          anomaly['suggestions'].length > 0 && (
                            <Text size="xs" c="dimmed" mt="xs">
                              建议: {anomaly['suggestions'][0]}
                            </Text>
                          )}
                      </Alert>
                    ))
                  ) : (
                    <Text c="dimmed" size="sm">
                      暂无异常提醒
                    </Text>
                  )}
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 图表分析面板 */}
        <Tabs.Panel value="charts" pt="md">
          <ProgressCharts studentId={studentId} />
        </Tabs.Panel>

        {/* 成就记录面板 */}
        <Tabs.Panel value="achievements" pt="md">
          <Grid>
            {achievements?.map(achievement => (
              <Grid.Col key={achievement.achievement_id} span={{ base: 12, sm: 6, md: 4 }}>
                <Card withBorder padding="md" h="100%">
                  <Group justify="space-between" mb="xs">
                    <Badge color="yellow" variant="light">
                      {achievement.type}
                    </Badge>
                    <Text size="xs" c="dimmed">
                      {new Date(achievement.achieved_at).toLocaleDateString()}
                    </Text>
                  </Group>
                  <Title order={5} mb="xs">
                    {achievement.name}
                  </Title>
                  <Text size="sm" c="dimmed">
                    {achievement.description}
                  </Text>
                </Card>
              </Grid.Col>
            )) || (
              <Grid.Col span={12}>
                <Text c="dimmed" size="sm" ta="center">
                  暂无成就记录
                </Text>
              </Grid.Col>
            )}
          </Grid>
        </Tabs.Panel>

        {/* 提醒通知面板 */}
        <Tabs.Panel value="alerts" pt="md">
          <Stack gap="md">
            {realtime?.suggestions && Array.isArray(realtime.suggestions) ? (
              realtime.suggestions.map((suggestion: string, index: number) => (
                <Alert key={index} icon={<IconBell size={16} />} color="blue" title="学习建议">
                  <Group justify="space-between">
                    <Text size="sm">{suggestion}</Text>
                    <Text size="xs" c="dimmed">
                      {new Date().toLocaleString()}
                    </Text>
                  </Group>
                </Alert>
              ))
            ) : (
              <Text c="dimmed" size="sm" ta="center">
                暂无通知
              </Text>
            )}
          </Stack>
        </Tabs.Panel>
      </Tabs>

      {/* 设置模态框 */}
      <Modal
        opened={settingsOpened}
        onClose={() => setSettingsOpened(false)}
        title="仪表盘设置"
        size="md"
      >
        <Stack gap="md">
          <div>
            <Text size="sm" fw={500} mb="xs">
              学习提醒
            </Text>
            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm">每日学习提醒</Text>
                <Switch
                  onChange={event => handleSetReminder('daily', event.currentTarget.checked)}
                />
              </Group>
              <Group justify="space-between">
                <Text size="sm">目标截止提醒</Text>
                <Switch
                  onChange={event =>
                    handleSetReminder('goal_deadline', event.currentTarget.checked)
                  }
                />
              </Group>
              <Group justify="space-between">
                <Text size="sm">表现下降提醒</Text>
                <Switch
                  onChange={event =>
                    handleSetReminder('performance_drop', event.currentTarget.checked)
                  }
                />
              </Group>
            </Stack>
          </div>

          <Divider />

          <div>
            <Text size="sm" fw={500} mb="xs">
              导出选项
            </Text>
            <Group>
              <Button
                size="sm"
                variant="light"
                onClick={() => handleExportReport('pdf')}
                loading={exportReportMutation.isPending}
              >
                导出PDF
              </Button>
              <Button
                size="sm"
                variant="light"
                onClick={() => handleExportReport('excel')}
                loading={exportReportMutation.isPending}
              >
                导出Excel
              </Button>
              <Button
                size="sm"
                variant="light"
                onClick={() => handleExportReport('csv')}
                loading={exportReportMutation.isPending}
              >
                导出CSV
              </Button>
            </Group>
          </div>
        </Stack>
      </Modal>
    </Container>
  )
}
