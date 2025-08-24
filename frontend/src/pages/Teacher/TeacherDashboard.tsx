/**
 * 教师仪表板 - 集成AI功能的主界面
 */
import { useEffect, useState } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Badge,
  Button,
  Group,
  Stack,
  Progress,
  Alert,
  ActionIcon,
  Menu,
  LoadingOverlay,
} from '@mantine/core'
import {
  IconBrain,
  IconChartLine,
  IconBook,
  IconUsers,
  IconAlertCircle,
  IconRefresh,
  IconSettings,
  IconEye,
  IconTrendingUp,
  IconTarget,
  IconBulb,
  IconBell,
} from '@tabler/icons-react'
import { aiService } from '../../services/aiService'
import { LearningAnalysis, TeachingAdjustment } from '../../types/ai'
import { useLoadingState } from '../../hooks/useLoadingState'

export function TeacherDashboard(): JSX.Element {
  // 状态管理
  const [analyses, setAnalyses] = useState<LearningAnalysis[]>([])
  const [adjustments, setAdjustments] = useState<TeachingAdjustment[]>([])
  const [refreshing, setRefreshing] = useState(false)
  const { loading, error, executeAsync } = useLoadingState({ loading: true, error: null })

  // 统计数据状态
  const [stats, setStats] = useState({
    totalClasses: 0,
    totalStudents: 0,
    activeAnalyses: 0,
    pendingAdjustments: 0,
  })

  // 加载仪表板数据
  const loadDashboardData = async () => {
    await executeAsync(async () => {
      // 并行获取最新分析和调整建议
      const [analysesResponse, adjustmentsResponse] = await Promise.all([
        aiService.getLearningAnalyses({ page: 1, size: 5 }),
        aiService.getTeachingAdjustments({ page: 1, size: 5 }),
      ])

      setAnalyses(analysesResponse.analyses)
      setAdjustments(adjustmentsResponse.adjustments)

      // 计算统计数据
      const uniqueClasses = new Set(analysesResponse.analyses.map(a => a.class_id))
      const totalStudents = analysesResponse.analyses.reduce((sum, a) => sum + a.student_count, 0)
      const pendingAdjustments = adjustmentsResponse.adjustments.filter(
        a => a.implementation_status === 'pending'
      ).length

      setStats({
        totalClasses: uniqueClasses.size,
        totalStudents,
        activeAnalyses: analysesResponse.total,
        pendingAdjustments,
      })

      return true
    })
  }

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true)
    await loadDashboardData()
    setRefreshing(false)
  }

  // 初始加载
  useEffect(() => {
    loadDashboardData()
  }, [])

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

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green'
      case 'in_progress':
        return 'blue'
      case 'pending':
        return 'orange'
      default:
        return 'gray'
    }
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={loading} />

      {/* 头部标题和操作 */}
      <Group justify="space-between" mb="xl">
        <Title order={1}>教师工作台</Title>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="light"
            loading={refreshing}
            onClick={handleRefresh}
          >
            刷新数据
          </Button>
          <Menu>
            <Menu.Target>
              <ActionIcon variant="light" size="lg">
                <IconSettings size={18} />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item leftSection={<IconChartLine size={14} />}>分析设置</Menu.Item>
              <Menu.Item leftSection={<IconBell size={14} />}>通知设置</Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>

      {/* 错误提示 */}
      {error && (
        <Alert icon={<IconAlertCircle size={16} />} title="数据加载失败" color="red" mb="lg">
          {error}
        </Alert>
      )}

      {/* 统计卡片 */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  管理班级
                </Text>
                <Text fw={700} size="xl">
                  {stats.totalClasses}
                </Text>
              </div>
              <IconUsers size={24} color="blue" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  学生总数
                </Text>
                <Text fw={700} size="xl">
                  {stats.totalStudents}
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
                  活跃分析
                </Text>
                <Text fw={700} size="xl">
                  {stats.activeAnalyses}
                </Text>
              </div>
              <IconBrain size={24} color="purple" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  待处理建议
                </Text>
                <Text fw={700} size="xl">
                  {stats.pendingAdjustments}
                </Text>
              </div>
              <IconBulb size={24} color="orange" />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 主要内容区域 */}
      <Grid>
        {/* 最新学情分析 */}
        <Grid.Col span={{ base: 12, lg: 6 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                最新学情分析
              </Text>
              <Button variant="light" size="xs" leftSection={<IconEye size={14} />}>
                查看全部
              </Button>
            </Group>

            <Stack gap="sm">
              {analyses.length > 0 ? (
                analyses.slice(0, 3).map(analysis => (
                  <Card key={analysis.id} withBorder radius="sm" p="sm">
                    <Group justify="space-between" mb="xs">
                      <Badge color="blue" variant="light" size="sm">
                        {analysis.analysis_type === 'progress'
                          ? '学习进度'
                          : analysis.analysis_type === 'difficulty'
                            ? '难点分析'
                            : '参与度分析'}
                      </Badge>
                      <Text size="xs" c="dimmed">
                        {new Date(analysis.analysis_date).toLocaleDateString()}
                      </Text>
                    </Group>

                    <Text size="sm" mb="xs">
                      学生数量: {analysis.student_count}人
                    </Text>

                    {analysis.risk_students.length > 0 && (
                      <Group gap="xs">
                        <IconAlertCircle size={14} color="orange" />
                        <Text size="xs" c="orange">
                          {analysis.risk_students.length}名学生需要关注
                        </Text>
                      </Group>
                    )}

                    <Progress
                      value={analysis.confidence_score * 100}
                      size="xs"
                      mt="xs"
                      color={
                        analysis.confidence_score > 0.8
                          ? 'green'
                          : analysis.confidence_score > 0.6
                            ? 'yellow'
                            : 'orange'
                      }
                    />
                    <Text size="xs" c="dimmed" mt="xs">
                      AI置信度: {Math.round(analysis.confidence_score * 100)}%
                    </Text>
                  </Card>
                ))
              ) : (
                <Text c="dimmed" ta="center" py="xl">
                  暂无学情分析数据
                </Text>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* 教学调整建议 */}
        <Grid.Col span={{ base: 12, lg: 6 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                智能教学建议
              </Text>
              <Button variant="light" size="xs" leftSection={<IconTrendingUp size={14} />}>
                查看全部
              </Button>
            </Group>

            <Stack gap="sm">
              {adjustments.length > 0 ? (
                adjustments.slice(0, 3).map(adjustment => (
                  <Card key={adjustment.id} withBorder radius="sm" p="sm">
                    <Group justify="space-between" mb="xs">
                      <Badge
                        color={getPriorityColor(adjustment.priority_level)}
                        variant="light"
                        size="sm"
                      >
                        {adjustment.priority_level === 'high'
                          ? '高优先级'
                          : adjustment.priority_level === 'medium'
                            ? '中优先级'
                            : '低优先级'}
                      </Badge>
                      <Badge
                        color={getStatusColor(adjustment.implementation_status)}
                        variant="outline"
                        size="xs"
                      >
                        {adjustment.implementation_status === 'pending'
                          ? '待处理'
                          : adjustment.implementation_status === 'in_progress'
                            ? '进行中'
                            : adjustment.implementation_status === 'completed'
                              ? '已完成'
                              : '已忽略'}
                      </Badge>
                    </Group>

                    <Text fw={500} size="sm" mb="xs">
                      {adjustment.title}
                    </Text>

                    <Text size="xs" c="dimmed" lineClamp={2}>
                      {adjustment.description}
                    </Text>

                    {adjustment.target_students.length > 0 && (
                      <Text size="xs" c="blue" mt="xs">
                        针对 {adjustment.target_students.length} 名特定学生
                      </Text>
                    )}
                  </Card>
                ))
              ) : (
                <Text c="dimmed" ta="center" py="xl">
                  暂无教学调整建议
                </Text>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* 快速操作 */}
        <Grid.Col span={12}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text fw={500} size="lg" mb="md">
              AI智能助手
            </Text>

            <Grid>
              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Button fullWidth variant="light" leftSection={<IconBrain size={18} />} size="lg">
                  生成课程大纲
                </Button>
              </Grid.Col>

              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Button
                  fullWidth
                  variant="light"
                  leftSection={<IconChartLine size={18} />}
                  size="lg"
                >
                  学情分析
                </Button>
              </Grid.Col>

              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Button fullWidth variant="light" leftSection={<IconBulb size={18} />} size="lg">
                  智能建议
                </Button>
              </Grid.Col>

              <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Button fullWidth variant="light" leftSection={<IconBook size={18} />} size="lg">
                  资源管理
                </Button>
              </Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  )
}
