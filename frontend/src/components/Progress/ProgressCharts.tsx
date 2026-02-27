/**
 * 学习进度可视化图表组件
 */

import React from 'react'
import {
  Card,
  Title,
  Text,
  Group,
  Stack,
  RingProgress,
  Progress,
  Badge,
  Grid,
  Center,
  Loader,
  Alert,
  Select,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import {
  IconTrendingUp,
  IconTrendingDown,
  IconMinus,
  IconRefresh,
  IconDownload,
} from '@tabler/icons-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { useVisualizationData, useProgressSummary } from '@/hooks/useProgressData'
import { useState } from 'react'

interface ProgressChartsProps {
  studentId?: number
  showControls?: boolean
  height?: number
}

export const ProgressCharts: React.FC<ProgressChartsProps> = ({
  showControls = true,
  height = 300,
}) => {
  const [timeRange, setTimeRange] = useState('30')
  const [chartType, setChartType] = useState<'progress' | 'knowledge' | 'performance' | 'time'>('progress')

  const { data: visualizationData, isLoading, error, refetch } = useVisualizationData(
    chartType,
    parseInt(timeRange)
  )
  const { data: summary } = useProgressSummary(parseInt(timeRange))

  if (isLoading) {
    return (
      <Card withBorder padding="md">
        <Center h={height}>
          <Loader />
        </Center>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert color="red" title="加载失败">
        无法加载图表数据，请稍后重试
      </Alert>
    )
  }

  const getTrendIcon = (trend: 'improving' | 'stable' | 'declining') => {
    switch (trend) {
      case 'improving':
        return <IconTrendingUp size={16} color="green" />
      case 'declining':
        return <IconTrendingDown size={16} color="red" />
      default:
        return <IconMinus size={16} color="gray" />
    }
  }

  const getTrendColor = (trend: 'improving' | 'stable' | 'declining') => {
    switch (trend) {
      case 'improving':
        return 'green'
      case 'declining':
        return 'red'
      default:
        return 'gray'
    }
  }

  return (
    <Stack gap="md">
      {/* 控制面板 */}
      {showControls && (
        <Card withBorder padding="md">
          <Group justify="space-between">
            <Group>
              <Select
                label="时间范围"
                value={timeRange}
                onChange={(value) => setTimeRange(value || '30')}
                data={[
                  { value: '7', label: '最近7天' },
                  { value: '30', label: '最近30天' },
                  { value: '90', label: '最近90天' },
                  { value: '180', label: '最近半年' },
                ]}
                size="sm"
                w={120}
              />
              <Select
                label="图表类型"
                value={chartType}
                onChange={(value) => setChartType(value as any || 'progress')}
                data={[
                  { value: 'progress', label: '学习进度' },
                  { value: 'knowledge', label: '知识点掌握' },
                  { value: 'performance', label: '能力雷达' },
                  { value: 'time', label: '时间分布' },
                ]}
                size="sm"
                w={120}
              />
            </Group>
            <Group>
              <Tooltip label="刷新数据">
                <ActionIcon variant="light" onClick={() => refetch()}>
                  <IconRefresh size={16} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="导出图表">
                <ActionIcon variant="light">
                  <IconDownload size={16} />
                </ActionIcon>
              </Tooltip>
            </Group>
          </Group>
        </Card>
      )}

      <Grid>
        {/* 总体进度环形图 */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder padding="md" h="100%">
            <Title order={4} mb="md">总体进度</Title>
            <Center>
              <RingProgress
                size={150}
                thickness={16}
                sections={[
                  {
                    value: summary?.progress_metrics?.['overall_score'] || 0,
                    color: 'blue'
                  },
                ]}
                label={
                  <Center>
                    <div style={{ textAlign: 'center' }}>
                      <Text size="lg" fw={700}>
                        {Math.round(summary?.progress_metrics?.['overall_score'] || 0)}%
                      </Text>
                      <Text size="xs" c="dimmed">
                        整体进度
                      </Text>
                    </div>
                  </Center>
                }
              />
            </Center>
            
            {/* 进度趋势指标 */}
            <Stack gap="xs" mt="md">
              {Array.isArray(summary?.progress_trends) ?
                summary.progress_trends.slice(0, 3).map((trend: any, index: number) => (
                  <Group key={index} justify="space-between">
                    <Group gap="xs">
                      {getTrendIcon(trend?.trend || 'stable')}
                      <Text size="sm">{trend?.metric || '未知指标'}</Text>
                    </Group>
                    <Badge
                      size="sm"
                      color={getTrendColor(trend?.trend || 'stable')}
                      variant="light"
                    >
                      {(trend?.change_rate || 0) > 0 ? '+' : ''}{((trend?.change_rate || 0) * 100).toFixed(1)}%
                    </Badge>
                  </Group>
                )) :
                <Text size="sm" c="dimmed">暂无趋势数据</Text>
              }
            </Stack>
          </Card>
        </Grid.Col>

        {/* 主要图表区域 */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder padding="md" h="100%">
            <Title order={4} mb="md">
              {chartType === 'progress' && '学习进度趋势'}
              {chartType === 'knowledge' && '知识点掌握热力图'}
              {chartType === 'performance' && '能力雷达图'}
              {chartType === 'time' && '学习时间分布'}
            </Title>
            
            <div style={{ height: height }}>
              {chartType === 'progress' && visualizationData?.progress_chart && (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={(() => {
                    const datasets = visualizationData.progress_chart.datasets
                    const labels = visualizationData.progress_chart.labels
                    if (!datasets || !Array.isArray(datasets) || datasets.length === 0 || !labels || !Array.isArray(labels)) {
                      return []
                    }
                    const firstDataset = datasets[0]
                    if (!firstDataset?.data || !Array.isArray(firstDataset.data)) {
                      return []
                    }
                    // 限制数据点数量以提高性能
                    const maxDataPoints = 100
                    const dataToShow = firstDataset.data.length > maxDataPoints
                      ? firstDataset.data.slice(-maxDataPoints)
                      : firstDataset.data
                    const labelsToShow = labels.length > maxDataPoints
                      ? labels.slice(-maxDataPoints)
                      : labels

                    return dataToShow.map((value, index) => ({
                      date: labelsToShow[index] || `Day ${index + 1}`,
                      progress: typeof value === 'number' ? value : 0,
                    }))
                  })()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line
                      type="monotone"
                      dataKey="progress"
                      stroke="#228be6"
                      strokeWidth={2}
                      dot={{ fill: '#228be6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}

              {chartType === 'knowledge' && visualizationData?.knowledge_heatmap && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={visualizationData.knowledge_heatmap}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="knowledge_point" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="mastery_level" fill="#40c057" />
                  </BarChart>
                </ResponsiveContainer>
              )}

              {chartType === 'performance' && visualizationData?.performance_radar && (
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={(() => {
                    const radar = visualizationData.performance_radar
                    if (!radar.categories || !Array.isArray(radar.categories) ||
                        !radar.current_scores || !Array.isArray(radar.current_scores) ||
                        !radar.target_scores || !Array.isArray(radar.target_scores)) {
                      return []
                    }
                    return radar.categories.map((category, index) => ({
                      category: category || `Category ${index + 1}`,
                      current: typeof radar.current_scores[index] === 'number' ? radar.current_scores[index] : 0,
                      target: typeof radar.target_scores[index] === 'number' ? radar.target_scores[index] : 0,
                    }))
                  })()}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="category" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="当前水平"
                      dataKey="current"
                      stroke="#228be6"
                      fill="#228be6"
                      fillOpacity={0.3}
                    />
                    <Radar
                      name="目标水平"
                      dataKey="target"
                      stroke="#fa5252"
                      fill="#fa5252"
                      fillOpacity={0.1}
                    />
                    <RechartsTooltip />
                  </RadarChart>
                </ResponsiveContainer>
              )}

              {chartType === 'time' && visualizationData?.time_distribution && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={visualizationData.time_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time_slot" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="study_minutes" fill="#fd7e14" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 详细指标卡片 */}
      <Grid>
        <Grid.Col span={{ base: 6, md: 3 }}>
          <Card withBorder padding="md" h="100%">
            <Stack gap="xs" align="center">
              <Text size="sm" c="dimmed">完成率</Text>
              <Text size="xl" fw={700} c="blue">
                {Math.round((summary?.progress_metrics?.['completion_rate'] || 0) * 100)}%
              </Text>
              <Progress
                value={(summary?.progress_metrics?.['completion_rate'] || 0) * 100}
                color="blue"
                size="sm"
                w="100%"
              />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 6, md: 3 }}>
          <Card withBorder padding="md" h="100%">
            <Stack gap="xs" align="center">
              <Text size="sm" c="dimmed">准确率</Text>
              <Text size="xl" fw={700} c="green">
                {Math.round((summary?.progress_metrics?.['accuracy_rate'] || 0) * 100)}%
              </Text>
              <Progress
                value={(summary?.progress_metrics?.['accuracy_rate'] || 0) * 100}
                color="green"
                size="sm"
                w="100%"
              />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 6, md: 3 }}>
          <Card withBorder padding="md" h="100%">
            <Stack gap="xs" align="center">
              <Text size="sm" c="dimmed">一致性</Text>
              <Text size="xl" fw={700} c="orange">
                {Math.round((summary?.progress_metrics?.['consistency_score'] || 0) * 100)}%
              </Text>
              <Progress
                value={(summary?.progress_metrics?.['consistency_score'] || 0) * 100}
                color="orange"
                size="sm"
                w="100%"
              />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 6, md: 3 }}>
          <Card withBorder padding="md" h="100%">
            <Stack gap="xs" align="center">
              <Text size="sm" c="dimmed">参与度</Text>
              <Text size="xl" fw={700} c="violet">
                {Math.round((summary?.progress_metrics?.['engagement_score'] || 0) * 100)}%
              </Text>
              <Progress
                value={(summary?.progress_metrics?.['engagement_score'] || 0) * 100}
                color="violet"
                size="sm"
                w="100%"
              />
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
