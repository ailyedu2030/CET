/**
 * 需求26：英语四级写作标准库 - 写作分析页面
 * 
 * 实现写作成绩分析和进步跟踪功能
 */

import { useState } from 'react'
import {
  Container,
  Title,
  Text,
  Grid,
  Card,
  Group,
  Badge,
  Stack,
  Progress,
  Paper,
  RingProgress,
  Center,
  Timeline,
  Select,
  Alert,
  LoadingOverlay,
  Tabs,
  List,
} from '@mantine/core'
import {
  IconTrendingUp,
  IconTarget,
  IconStar,
  IconAlertCircle,
  IconBulb,
  IconChartLine,
  IconCalendar,
  IconPencil,
  IconCheck,
  IconX,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

import { writingApi, WritingType, WritingScoreLevel } from '@/api/writing'
import { useAuthStore } from '@/stores/authStore'

export function WritingAnalysisPage(): JSX.Element {
  // 状态管理
  const [selectedPeriod, setSelectedPeriod] = useState('30')
  const { user } = useAuthStore()

  // 查询写作统计
  const {
    data: statistics,
    isLoading: statisticsLoading,
  } = useQuery({
    queryKey: ['writing-statistics', user?.id],
    queryFn: () => writingApi.getStatistics(),
    enabled: !!user?.id,
  })

  // 查询写作提交历史
  const {
    data: submissions,
    isLoading: submissionsLoading,
  } = useQuery({
    queryKey: ['writing-submissions', user?.id],
    queryFn: () => writingApi.getMySubmissions({ limit: 50 }),
    enabled: !!user?.id,
  })

  const isLoading = statisticsLoading || submissionsLoading

  // 获取分数等级标签
  const getScoreLevelLabel = (level: WritingScoreLevel) => {
    const labels = {
      [WritingScoreLevel.EXCELLENT]: '优秀',
      [WritingScoreLevel.GOOD]: '良好',
      [WritingScoreLevel.FAIR]: '及格',
      [WritingScoreLevel.POOR]: '不及格',
    }
    return labels[level] || level
  }

  // 获取分数等级颜色
  const getScoreLevelColor = (level: WritingScoreLevel) => {
    const colors = {
      [WritingScoreLevel.EXCELLENT]: 'green',
      [WritingScoreLevel.GOOD]: 'blue',
      [WritingScoreLevel.FAIR]: 'orange',
      [WritingScoreLevel.POOR]: 'red',
    }
    return colors[level] || 'gray'
  }

  // 获取写作类型标签
  const getWritingTypeLabel = (type: WritingType) => {
    const labels = {
      [WritingType.ARGUMENTATIVE]: '议论文',
      [WritingType.NARRATIVE]: '记叙文',
      [WritingType.DESCRIPTIVE]: '描述文',
      [WritingType.EXPOSITORY]: '说明文',
      [WritingType.PRACTICAL]: '应用文',
    }
    return labels[type] || type
  }

  // 准备图表数据
  const scoreDistributionData = statistics?.score_distribution ? 
    Object.entries(statistics.score_distribution).map(([level, count]) => ({
      name: getScoreLevelLabel(level as WritingScoreLevel),
      value: count,
      color: getScoreLevelColor(level as WritingScoreLevel),
    })) : []

  const typePerformanceData = statistics?.writing_type_performance ?
    Object.entries(statistics.writing_type_performance).map(([type, data]) => ({
      name: getWritingTypeLabel(type as WritingType),
      count: data.count,
      average_score: data.average_score,
      improvement_rate: data.improvement_rate,
    })) : []

  const recentPerformanceData = statistics?.recent_performance?.map(item => ({
    date: new Date(item.date).toLocaleDateString(),
    score: item.average_score,
    submissions: item.submissions,
  })) || []

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1']

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={isLoading} />

      {/* 页面标题 */}
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>写作分析</Title>
          <Text size="lg" c="dimmed">
            深入分析您的写作表现，发现进步空间
          </Text>
        </div>
        <Select
          value={selectedPeriod}
          onChange={(value) => setSelectedPeriod(value || '30')}
          data={[
            { value: '7', label: '最近7天' },
            { value: '30', label: '最近30天' },
            { value: '90', label: '最近90天' },
            { value: '365', label: '最近一年' },
          ]}
          w={150}
        />
      </Group>

      <Tabs defaultValue="overview">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartLine size={16} />}>
            总体概览
          </Tabs.Tab>
          <Tabs.Tab value="performance" leftSection={<IconTrendingUp size={16} />}>
            表现分析
          </Tabs.Tab>
          <Tabs.Tab value="improvement" leftSection={<IconTarget size={16} />}>
            改进建议
          </Tabs.Tab>
          <Tabs.Tab value="history" leftSection={<IconCalendar size={16} />}>
            历史记录
          </Tabs.Tab>
        </Tabs.List>

        {/* 总体概览 */}
        <Tabs.Panel value="overview" pt="lg">
          <Grid>
            {/* 基础统计 */}
            <Grid.Col span={3}>
              <Card withBorder p="md">
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">总提交数</Text>
                    <Text size="xl" fw={700}>{statistics?.total_submissions || 0}</Text>
                  </div>
                  <RingProgress
                    size={60}
                    thickness={6}
                    sections={[{ value: Math.min((statistics?.total_submissions || 0) * 2, 100), color: 'blue' }]}
                    label={<Center><IconPencil size={16} /></Center>}
                  />
                </Group>
              </Card>
            </Grid.Col>

            <Grid.Col span={3}>
              <Card withBorder p="md">
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">平均分数</Text>
                    <Text size="xl" fw={700}>{Math.round((statistics?.average_score || 0) * 10) / 10}</Text>
                  </div>
                  <RingProgress
                    size={60}
                    thickness={6}
                    sections={[{ value: (statistics?.average_score || 0) * 100 / 15, color: 'green' }]}
                    label={<Center><IconStar size={16} /></Center>}
                  />
                </Group>
              </Card>
            </Grid.Col>

            <Grid.Col span={3}>
              <Card withBorder p="md">
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">优势领域</Text>
                    <Text size="xl" fw={700}>{statistics?.strengths?.length || 0}</Text>
                  </div>
                  <RingProgress
                    size={60}
                    thickness={6}
                    sections={[{ value: (statistics?.strengths?.length || 0) * 20, color: 'orange' }]}
                    label={<Center><IconCheck size={16} /></Center>}
                  />
                </Group>
              </Card>
            </Grid.Col>

            <Grid.Col span={3}>
              <Card withBorder p="md">
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">改进空间</Text>
                    <Text size="xl" fw={700}>{statistics?.weaknesses?.length || 0}</Text>
                  </div>
                  <RingProgress
                    size={60}
                    thickness={6}
                    sections={[{ value: Math.max(100 - (statistics?.weaknesses?.length || 0) * 20, 20), color: 'red' }]}
                    label={<Center><IconAlertCircle size={16} /></Center>}
                  />
                </Group>
              </Card>
            </Grid.Col>

            {/* 分数分布 */}
            <Grid.Col span={6}>
              <Card withBorder p="md" h={300}>
                <Text fw={600} mb="md">分数分布</Text>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={scoreDistributionData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {scoreDistributionData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Grid.Col>

            {/* 近期表现趋势 */}
            <Grid.Col span={6}>
              <Card withBorder p="md" h={300}>
                <Text fw={600} mb="md">近期表现趋势</Text>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={recentPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 15]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#8884d8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 表现分析 */}
        <Tabs.Panel value="performance" pt="lg">
          <Grid>
            {/* 各类型表现 */}
            <Grid.Col span={12}>
              <Card withBorder p="md">
                <Text fw={600} mb="md">各写作类型表现</Text>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={typePerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="average_score" fill="#8884d8" name="平均分数" />
                    <Bar dataKey="count" fill="#82ca9d" name="练习次数" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Grid.Col>

            {/* 难度表现 */}
            <Grid.Col span={6}>
              <Card withBorder p="md">
                <Text fw={600} mb="md">各难度表现</Text>
                <Stack gap="md">
                  {statistics?.difficulty_performance && Object.entries(statistics.difficulty_performance).map(([difficulty, data]) => (
                    <Paper key={difficulty} p="sm" withBorder>
                      <Group justify="space-between" mb="xs">
                        <Text fw={500}>{difficulty}</Text>
                        <Badge color="blue">{data.count}次</Badge>
                      </Group>
                      <Group justify="space-between" mb="xs">
                        <Text size="sm" c="dimmed">平均分数</Text>
                        <Text size="sm">{Math.round(data.average_score * 10) / 10}/15</Text>
                      </Group>
                      <Progress value={(data.average_score / 15) * 100} />
                      <Group justify="space-between" mt="xs">
                        <Text size="sm" c="dimmed">成功率</Text>
                        <Text size="sm">{Math.round(data.success_rate * 100)}%</Text>
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </Card>
            </Grid.Col>

            {/* 优势和劣势 */}
            <Grid.Col span={6}>
              <Stack gap="md">
                <Card withBorder p="md">
                  <Group mb="md">
                    <IconCheck size={20} color="green" />
                    <Text fw={600}>优势领域</Text>
                  </Group>
                  <List>
                    {statistics?.strengths?.map((strength, index) => (
                      <List.Item key={index} icon={<IconCheck size={16} color="green" />}>
                        {strength}
                      </List.Item>
                    )) || <Text c="dimmed">暂无数据</Text>}
                  </List>
                </Card>

                <Card withBorder p="md">
                  <Group mb="md">
                    <IconAlertCircle size={20} color="red" />
                    <Text fw={600}>改进空间</Text>
                  </Group>
                  <List>
                    {statistics?.weaknesses?.map((weakness, index) => (
                      <List.Item key={index} icon={<IconX size={16} color="red" />}>
                        {weakness}
                      </List.Item>
                    )) || <Text c="dimmed">暂无数据</Text>}
                  </List>
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 改进建议 */}
        <Tabs.Panel value="improvement" pt="lg">
          <Grid>
            <Grid.Col span={12}>
              <Card withBorder p="md">
                <Group mb="md">
                  <IconBulb size={24} color="orange" />
                  <Text fw={600} size="lg">个性化改进建议</Text>
                </Group>
                <Stack gap="md">
                  {statistics?.recommendations?.map((recommendation, index) => (
                    <Alert key={index} icon={<IconBulb size={16} />} color="blue">
                      {recommendation}
                    </Alert>
                  )) || (
                    <Alert icon={<IconBulb size={16} />} color="gray">
                      完成更多写作练习后，系统将为您提供个性化建议
                    </Alert>
                  )}
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 历史记录 */}
        <Tabs.Panel value="history" pt="lg">
          <Card withBorder p="md">
            <Text fw={600} mb="md">写作历史记录</Text>
            <Timeline active={submissions?.data?.length || 0} bulletSize={24} lineWidth={2}>
              {submissions?.data?.map((submission) => (
                <Timeline.Item
                  key={submission.id}
                  bullet={<IconPencil size={12} />}
                  title={`写作练习 #${submission.id}`}
                >
                  <Group gap="md" mb="xs">
                    <Badge color="blue" size="sm">
                      {submission.score_level ? getScoreLevelLabel(submission.score_level) : '未评分'}
                    </Badge>
                    <Text size="sm">分数: {submission.total_score}/15</Text>
                    <Text size="sm">字数: {submission.word_count}</Text>
                    <Text size="sm">用时: {submission.writing_time_minutes}分钟</Text>
                  </Group>
                  <Text size="xs" c="dimmed">
                    {new Date(submission.submitted_at).toLocaleString()}
                  </Text>
                </Timeline.Item>
              )) || (
                <Timeline.Item bullet={<IconAlertCircle size={12} />} title="暂无写作记录">
                  <Text size="sm" c="dimmed">
                    开始您的第一次写作练习吧！
                  </Text>
                </Timeline.Item>
              )}
            </Timeline>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Container>
  )
}
