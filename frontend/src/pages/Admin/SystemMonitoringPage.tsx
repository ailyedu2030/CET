/**
 * 系统监控与数据决策支持页面 - 需求6：系统监控与数据决策支持
 * 实现教学监控、系统运维监控、智能报表生成、预测性维护、数据可视化等功能
 */

import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Container,
  Grid,
  Group,
  Modal,
  Paper,
  Progress,
  RingProgress,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  TextInput,
  Title,
  Tooltip,
  Switch,
  Divider,
  NumberInput,
  Textarea,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { DatePickerInput } from '@mantine/dates'
import {
  IconActivity,
  IconAlertTriangle,
  IconCpu,
  IconEye,
  IconFileReport,
  IconNetwork,
  IconRefresh,
  IconSettings,
  IconShield,
  IconUsers,
  IconCheck,
  IconBell,
  IconChartLine,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  systemMonitoringApi,
  type ReportGenerationRequest,
} from '../../api/systemMonitoring'

export function SystemMonitoringPage(): JSX.Element {
  const queryClient = useQueryClient()
  
  // 状态管理
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d')
  const [_selectedAlert, setSelectedAlert] = useState<string | null>(null)

  // 模态框状态
  const [reportModalOpened, { open: openReportModal, close: closeReportModal }] = useDisclosure(false)
  const [alertModalOpened, { open: openAlertModal, close: closeAlertModal }] = useDisclosure(false)
  const [settingsModalOpened, { open: openSettingsModal, close: closeSettingsModal }] = useDisclosure(false)

  // 表单管理
  const reportForm = useForm({
    initialValues: {
      report_type: 'teaching_efficiency',
      time_range: {
        start_date: '',
        end_date: '',
      },
      format: 'pdf',
      recipients: [],
      schedule: {
        frequency: 'weekly',
        enabled: false,
      },
    },
  })

  // ===== 数据查询 =====

  // 获取教学监控数据
  const {
    data: teachingData,
    refetch: refetchTeaching,
  } = useQuery({
    queryKey: ['teaching-monitoring', selectedTimeRange],
    queryFn: () => systemMonitoringApi.getTeachingMonitoringDashboard(
      selectedTimeRange === '7d' ? 7 : selectedTimeRange === '30d' ? 30 : 90
    ),
  })

  // 获取系统运维监控数据
  const {
    data: systemData,
    refetch: refetchSystem,
  } = useQuery({
    queryKey: ['system-monitoring'],
    queryFn: () => systemMonitoringApi.getSystemOperationsMonitoring(),
    refetchInterval: 30000, // 30秒刷新一次
  })

  // 获取实时监控大屏数据
  const {
    data: dashboardData,
  } = useQuery({
    queryKey: ['real-time-dashboard'],
    queryFn: () => systemMonitoringApi.getRealTimeMonitoringDashboard(),
    refetchInterval: 10000, // 10秒刷新一次
  })

  // 获取预测性维护数据
  const { data: predictiveData } = useQuery({
    queryKey: ['predictive-maintenance'],
    queryFn: () => systemMonitoringApi.getPredictiveMaintenanceData(),
  })

  // 获取告警管理数据
  const { data: alertData } = useQuery({
    queryKey: ['alert-management'],
    queryFn: () => systemMonitoringApi.getAlertManagementData(),
  })

  // ===== 数据操作 =====

  // 生成报表
  const generateReportMutation = useMutation({
    mutationFn: (data: ReportGenerationRequest) => systemMonitoringApi.generateReport(data),
    onSuccess: () => {
      notifications.show({
        title: '报表生成成功',
        message: '报表正在生成中，完成后将通知您',
        color: 'green',
      })
      closeReportModal()
      reportForm.reset()
    },
    onError: (error: Error) => {
      notifications.show({
        title: '报表生成失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 确认告警
  const acknowledgeAlertMutation = useMutation({
    mutationFn: ({ alertId, notes }: { alertId: string; notes?: string }) =>
      systemMonitoringApi.acknowledgeAlert(alertId, notes),
    onSuccess: () => {
      notifications.show({
        title: '告警确认成功',
        message: '告警已确认',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['alert-management'] })
    },
  })

  // ===== 事件处理 =====

  const handleGenerateReport = (values: typeof reportForm.values) => {
    generateReportMutation.mutate(values as ReportGenerationRequest)
  }

  const handleRefreshData = () => {
    refetchTeaching()
    refetchSystem()
    queryClient.invalidateQueries({ queryKey: ['real-time-dashboard'] })
  }

  const handleAcknowledgeAlert = (alertId: string) => {
    acknowledgeAlertMutation.mutate({ alertId })
  }

  // 获取系统健康状态颜色
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green'
      case 'warning': return 'yellow'
      case 'critical': return 'red'
      default: return 'gray'
    }
  }

  // 获取告警严重性颜色
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red'
      case 'high': return 'orange'
      case 'medium': return 'yellow'
      case 'low': return 'blue'
      default: return 'gray'
    }
  }

  return (
    <Container size="xl" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>系统监控与数据决策支持</Title>
          <Group>
            <Select
              value={selectedTimeRange}
              onChange={(value) => setSelectedTimeRange(value || '7d')}
              data={[
                { value: '7d', label: '最近7天' },
                { value: '30d', label: '最近30天' },
                { value: '90d', label: '最近90天' },
              ]}
              leftSection={<IconChartLine size={16} />}
            />
            <Button
              leftSection={<IconFileReport size={16} />}
              variant="light"
              onClick={openReportModal}
            >
              生成报表
            </Button>
            <Button
              leftSection={<IconSettings size={16} />}
              variant="light"
              onClick={openSettingsModal}
            >
              设置
            </Button>
            <Button
              leftSection={<IconRefresh size={16} />}
              onClick={handleRefreshData}
            >
              刷新数据
            </Button>
          </Group>
        </Group>

        <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
          <Tabs.List>
            <Tabs.Tab value="overview" leftSection={<IconActivity size={16} />}>
              总览
            </Tabs.Tab>
            <Tabs.Tab value="teaching" leftSection={<IconUsers size={16} />}>
              教学监控
            </Tabs.Tab>
            <Tabs.Tab value="system" leftSection={<IconCpu size={16} />}>
              系统监控
            </Tabs.Tab>
            <Tabs.Tab value="reports" leftSection={<IconFileReport size={16} />}>
              报表管理
            </Tabs.Tab>
            <Tabs.Tab value="predictive" leftSection={<IconShield size={16} />}>
              预测维护
            </Tabs.Tab>
            <Tabs.Tab value="alerts" leftSection={<IconAlertTriangle size={16} />}>
              告警管理
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="md">
            {/* 实时监控总览 */}
            <Grid>
              <Grid.Col span={3}>
                <Card withBorder>
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">在线用户</Text>
                      <IconUsers size={16} />
                    </Group>
                    <Text size="xl" fw={700}>
                      {dashboardData?.system_overview.total_users_online || 0}
                    </Text>
                    <Text size="xs" c="dimmed">
                      活跃会话: {dashboardData?.system_overview.active_sessions || 0}
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={3}>
                <Card withBorder>
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">系统负载</Text>
                      <IconCpu size={16} />
                    </Group>
                    <RingProgress
                      size={80}
                      thickness={8}
                      sections={[
                        {
                          value: dashboardData?.system_overview.system_load || 0,
                          color: (dashboardData?.system_overview.system_load || 0) > 80 ? 'red' : 'blue',
                        },
                      ]}
                      label={
                        <Text ta="center" size="xs">
                          {dashboardData?.system_overview.system_load || 0}%
                        </Text>
                      }
                    />
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={3}>
                <Card withBorder>
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">响应时间</Text>
                      <IconNetwork size={16} />
                    </Group>
                    <Text size="xl" fw={700}>
                      {dashboardData?.system_overview.response_time || 0}ms
                    </Text>
                    <Text size="xs" c="dimmed">
                      平均响应时间
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={3}>
                <Card withBorder>
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">告警状态</Text>
                      <IconAlertTriangle size={16} />
                    </Group>
                    <Group>
                      <Badge color="red" size="sm">
                        {dashboardData?.alerts_summary.critical_alerts || 0}
                      </Badge>
                      <Badge color="yellow" size="sm">
                        {dashboardData?.alerts_summary.warning_alerts || 0}
                      </Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      今日已解决: {dashboardData?.alerts_summary.resolved_today || 0}
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>

            {/* 系统健康状态 */}
            <Paper withBorder p="md" mt="md">
              <Title order={4} mb="md">系统健康状态</Title>
              <Grid>
                <Grid.Col span={3}>
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>CPU使用率</Text>
                    <Progress
                      value={dashboardData?.system_metrics.cpu_usage || 0}
                      color={(dashboardData?.system_metrics.cpu_usage || 0) > 80 ? 'red' : 'blue'}
                      size="lg"
                    />
                    <Text size="xs" c="dimmed">
                      {dashboardData?.system_metrics.cpu_usage || 0}%
                    </Text>
                  </Stack>
                </Grid.Col>

                <Grid.Col span={3}>
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>内存使用率</Text>
                    <Progress
                      value={dashboardData?.system_metrics.memory_usage || 0}
                      color={(dashboardData?.system_metrics.memory_usage || 0) > 80 ? 'red' : 'green'}
                      size="lg"
                    />
                    <Text size="xs" c="dimmed">
                      {dashboardData?.system_metrics.memory_usage || 0}%
                    </Text>
                  </Stack>
                </Grid.Col>

                <Grid.Col span={3}>
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>磁盘使用率</Text>
                    <Progress
                      value={dashboardData?.system_metrics.disk_usage || 0}
                      color={(dashboardData?.system_metrics.disk_usage || 0) > 90 ? 'red' : 'blue'}
                      size="lg"
                    />
                    <Text size="xs" c="dimmed">
                      {dashboardData?.system_metrics.disk_usage || 0}%
                    </Text>
                  </Stack>
                </Grid.Col>

                <Grid.Col span={3}>
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>网络吞吐量</Text>
                    <Text size="lg" fw={700}>
                      {dashboardData?.system_metrics.network_throughput || 0} MB/s
                    </Text>
                    <Text size="xs" c="dimmed">
                      实时网络流量
                    </Text>
                  </Stack>
                </Grid.Col>
              </Grid>
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="teaching" pt="md">
            {/* 教学监控 - 需求6验收标准1 */}
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder>
                  <Title order={5} mb="md">教师质量统计</Title>
                  <Stack>
                    <Group justify="space-between">
                      <Text size="sm">教师总数</Text>
                      <Text fw={500}>{teachingData?.teacher_quality_stats.total_teachers || 0}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">平均评分</Text>
                      <Badge color="blue">
                        {teachingData?.teacher_quality_stats.average_rating?.toFixed(1) || '0.0'}
                      </Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">完成率</Text>
                      <Progress
                        value={teachingData?.teacher_quality_stats.completion_rate || 0}
                        size="sm"
                        style={{ width: 100 }}
                      />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">学生满意度</Text>
                      <Text fw={500} c="green">
                        {teachingData?.teacher_quality_stats.student_satisfaction?.toFixed(1) || '0.0'}%
                      </Text>
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card withBorder>
                  <Title order={5} mb="md">学生进度统计</Title>
                  <Stack>
                    <Group justify="space-between">
                      <Text size="sm">学生总数</Text>
                      <Text fw={500}>{teachingData?.student_progress_stats.total_students || 0}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">平均进度</Text>
                      <Progress
                        value={teachingData?.student_progress_stats.average_progress || 0}
                        size="sm"
                        style={{ width: 100 }}
                      />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">完成率</Text>
                      <Text fw={500} c="blue">
                        {teachingData?.student_progress_stats.completion_rate?.toFixed(1) || '0.0'}%
                      </Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">知识掌握率</Text>
                      <Text fw={500} c="green">
                        {teachingData?.student_progress_stats.knowledge_mastery_rate?.toFixed(1) || '0.0'}%
                      </Text>
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={12}>
                <Card withBorder>
                  <Title order={5} mb="md">教学告警</Title>
                  <Table striped>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>类型</Table.Th>
                        <Table.Th>严重性</Table.Th>
                        <Table.Th>消息</Table.Th>
                        <Table.Th>影响数量</Table.Th>
                        <Table.Th>创建时间</Table.Th>
                        <Table.Th>操作</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {teachingData?.teaching_alerts.map(alert => (
                        <Table.Tr key={alert.id}>
                          <Table.Td>
                            <Badge variant="light">
                              {alert.type === 'low_completion' && '完成率低'}
                              {alert.type === 'poor_rating' && '评分差'}
                              {alert.type === 'slow_progress' && '进度慢'}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            <Badge color={getSeverityColor(alert.severity)}>
                              {alert.severity}
                            </Badge>
                          </Table.Td>
                          <Table.Td>{alert.message}</Table.Td>
                          <Table.Td>{alert.affected_count}</Table.Td>
                          <Table.Td>
                            {new Date(alert.created_at).toLocaleDateString('zh-CN')}
                          </Table.Td>
                          <Table.Td>
                            <Button
                              size="xs"
                              variant="light"
                              onClick={() => handleAcknowledgeAlert(alert.id)}
                            >
                              确认
                            </Button>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="system" pt="md">
            {/* 系统运维监控 - 需求6验收标准2 */}
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder>
                  <Title order={5} mb="md">系统健康状态</Title>
                  <Stack>
                    <Group justify="space-between">
                      <Text size="sm">CPU使用率</Text>
                      <Text fw={500}>{systemData?.system_health.cpu_usage || 0}%</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">内存使用率</Text>
                      <Text fw={500}>{systemData?.system_health.memory_usage || 0}%</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">磁盘使用率</Text>
                      <Text fw={500}>{systemData?.system_health.disk_usage || 0}%</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">网络状态</Text>
                      <Badge color={getHealthColor(systemData?.system_health.network_status || 'healthy')}>
                        {systemData?.system_health.network_status || 'healthy'}
                      </Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">运行时间</Text>
                      <Text fw={500}>{Math.floor((systemData?.system_health.uptime || 0) / 3600)}小时</Text>
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card withBorder>
                  <Title order={5} mb="md">API统计</Title>
                  <Stack>
                    <Group justify="space-between">
                      <Text size="sm">总调用次数</Text>
                      <Text fw={500}>{systemData?.api_statistics.total_calls || 0}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">成功率</Text>
                      <Text fw={500} c="green">
                        {systemData?.api_statistics.success_rate?.toFixed(1) || '0.0'}%
                      </Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">平均响应时间</Text>
                      <Text fw={500}>{systemData?.api_statistics.average_response_time || 0}ms</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">错误率</Text>
                      <Text fw={500} c="red">
                        {systemData?.api_statistics.error_rate?.toFixed(1) || '0.0'}%
                      </Text>
                    </Group>
                    <Divider />
                    <Group justify="space-between">
                      <Text size="sm">DeepSeek API调用</Text>
                      <Text fw={500}>{systemData?.api_statistics.deepseek_api_usage.total_calls || 0}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">预算使用率</Text>
                      <Progress
                        value={systemData?.api_statistics.deepseek_api_usage.budget_usage_percentage || 0}
                        color={
                          (systemData?.api_statistics.deepseek_api_usage.budget_usage_percentage || 0) > 80
                            ? 'red'
                            : 'blue'
                        }
                        size="sm"
                        style={{ width: 100 }}
                      />
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={12}>
                <Card withBorder>
                  <Title order={5} mb="md">系统告警</Title>
                  <Table striped>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>类型</Table.Th>
                        <Table.Th>严重性</Table.Th>
                        <Table.Th>消息</Table.Th>
                        <Table.Th>状态</Table.Th>
                        <Table.Th>创建时间</Table.Th>
                        <Table.Th>操作</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {systemData?.alerts.map(alert => (
                        <Table.Tr key={alert.id}>
                          <Table.Td>
                            <Badge variant="light">
                              {alert.type === 'resource_usage' && '资源使用'}
                              {alert.type === 'api_failure' && 'API失败'}
                              {alert.type === 'budget_exceeded' && '预算超支'}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            <Badge color={getSeverityColor(alert.severity)}>
                              {alert.severity}
                            </Badge>
                          </Table.Td>
                          <Table.Td>{alert.message}</Table.Td>
                          <Table.Td>
                            <Badge color={alert.resolved ? 'green' : 'red'}>
                              {alert.resolved ? '已解决' : '未解决'}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            {new Date(alert.created_at).toLocaleDateString('zh-CN')}
                          </Table.Td>
                          <Table.Td>
                            {!alert.resolved && (
                              <Button
                                size="xs"
                                variant="light"
                                onClick={() => handleAcknowledgeAlert(alert.id)}
                              >
                                确认
                              </Button>
                            )}
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="reports" pt="md">
            {/* 报表管理 - 需求6验收标准3 */}
            <Alert color="blue" mb="md">
              <Text size="sm">
                智能报表生成功能可以自动生成教学效率、资源使用、安全审计等报表。
              </Text>
            </Alert>
          </Tabs.Panel>

          <Tabs.Panel value="predictive" pt="md">
            {/* 预测性维护 - 需求6验收标准4 */}
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder>
                  <Title order={5} mb="md">硬件预测</Title>
                  <Stack>
                    {predictiveData?.hardware_predictions.map((prediction, index) => (
                      <Paper key={index} withBorder p="sm">
                        <Group justify="space-between">
                          <Text size="sm" fw={500}>{prediction.component}</Text>
                          <Badge color={prediction.failure_probability > 0.7 ? 'red' : 'yellow'}>
                            {(prediction.failure_probability * 100).toFixed(1)}%
                          </Badge>
                        </Group>
                        <Text size="xs" c="dimmed">
                          预计故障时间: {new Date(prediction.predicted_failure_date).toLocaleDateString('zh-CN')}
                        </Text>
                        <Text size="xs" c="dimmed">
                          置信度: {(prediction.confidence_level * 100).toFixed(1)}%
                        </Text>
                      </Paper>
                    ))}
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card withBorder>
                  <Title order={5} mb="md">安全扫描结果</Title>
                  <Stack>
                    {predictiveData?.security_scan_results.map((result, index) => (
                      <Paper key={index} withBorder p="sm">
                        <Group justify="space-between">
                          <Text size="sm" fw={500}>{result.vulnerability_type}</Text>
                          <Badge color={getSeverityColor(result.severity)}>
                            {result.severity}
                          </Badge>
                        </Group>
                        <Text size="xs" c="dimmed">{result.description}</Text>
                        <Text size="xs" c="dimmed">
                          影响组件: {result.affected_components.join(', ')}
                        </Text>
                      </Paper>
                    ))}
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="alerts" pt="md">
            {/* 告警管理 */}
            <Grid>
              <Grid.Col span={12}>
                <Card withBorder>
                  <Group justify="space-between" mb="md">
                    <Title order={5}>告警列表</Title>
                    <Button
                      leftSection={<IconBell size={16} />}
                      variant="light"
                      onClick={openAlertModal}
                    >
                      创建告警规则
                    </Button>
                  </Group>
                  <Table striped>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>标题</Table.Th>
                        <Table.Th>类别</Table.Th>
                        <Table.Th>严重性</Table.Th>
                        <Table.Th>状态</Table.Th>
                        <Table.Th>创建时间</Table.Th>
                        <Table.Th>操作</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {alertData?.alerts.map(alert => (
                        <Table.Tr key={alert.id}>
                          <Table.Td>
                            <Stack gap="xs">
                              <Text size="sm" fw={500}>{alert.title}</Text>
                              <Text size="xs" c="dimmed">{alert.description}</Text>
                            </Stack>
                          </Table.Td>
                          <Table.Td>
                            <Badge variant="light">
                              {alert.category === 'system' && '系统'}
                              {alert.category === 'teaching' && '教学'}
                              {alert.category === 'security' && '安全'}
                              {alert.category === 'performance' && '性能'}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            <Badge color={getSeverityColor(alert.severity)}>
                              {alert.severity}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            <Badge color={
                              alert.status === 'resolved' ? 'green' :
                              alert.status === 'acknowledged' ? 'yellow' : 'red'
                            }>
                              {alert.status === 'active' && '活跃'}
                              {alert.status === 'acknowledged' && '已确认'}
                              {alert.status === 'resolved' && '已解决'}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            {new Date(alert.created_at).toLocaleDateString('zh-CN')}
                          </Table.Td>
                          <Table.Td>
                            <Group gap="xs">
                              <Tooltip label="查看详情">
                                <ActionIcon
                                  variant="light"
                                  onClick={() => setSelectedAlert(alert.id)}
                                >
                                  <IconEye size={16} />
                                </ActionIcon>
                              </Tooltip>
                              {alert.status === 'active' && (
                                <Tooltip label="确认告警">
                                  <ActionIcon
                                    variant="light"
                                    color="blue"
                                    onClick={() => handleAcknowledgeAlert(alert.id)}
                                  >
                                    <IconCheck size={16} />
                                  </ActionIcon>
                                </Tooltip>
                              )}
                            </Group>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>
        </Tabs>

        {/* 生成报表模态框 - 需求6验收标准3 */}
        <Modal
          opened={reportModalOpened}
          onClose={closeReportModal}
          title="生成智能报表"
          size="lg"
        >
          <form onSubmit={reportForm.onSubmit(handleGenerateReport)}>
            <Stack>
              <Select
                label="报表类型"
                placeholder="请选择报表类型"
                required
                data={[
                  { value: 'teaching_efficiency', label: '教学效率报表' },
                  { value: 'resource_usage', label: '资源使用报表' },
                  { value: 'security_audit', label: '安全审计报表' },
                ]}
                {...reportForm.getInputProps('report_type')}
              />

              <Group grow>
                <DatePickerInput
                  label="开始日期"
                  placeholder="请选择开始日期"
                  required
                  {...reportForm.getInputProps('time_range.start_date')}
                />

                <DatePickerInput
                  label="结束日期"
                  placeholder="请选择结束日期"
                  required
                  {...reportForm.getInputProps('time_range.end_date')}
                />
              </Group>

              <Select
                label="导出格式"
                placeholder="请选择导出格式"
                required
                data={[
                  { value: 'pdf', label: 'PDF格式' },
                  { value: 'excel', label: 'Excel格式' },
                  { value: 'html', label: 'HTML格式' },
                ]}
                {...reportForm.getInputProps('format')}
              />

              <Switch
                label="启用定时生成"
                description="定期自动生成报表"
                {...reportForm.getInputProps('schedule.enabled', { type: 'checkbox' })}
              />

              {reportForm.values.schedule?.enabled && (
                <Select
                  label="生成频率"
                  data={[
                    { value: 'daily', label: '每日' },
                    { value: 'weekly', label: '每周' },
                    { value: 'monthly', label: '每月' },
                  ]}
                  {...reportForm.getInputProps('schedule.frequency')}
                />
              )}

              <Group justify="flex-end">
                <Button variant="light" onClick={closeReportModal}>
                  取消
                </Button>
                <Button type="submit" loading={generateReportMutation.isPending}>
                  生成报表
                </Button>
              </Group>
            </Stack>
          </form>
        </Modal>

        {/* 告警规则模态框 */}
        <Modal
          opened={alertModalOpened}
          onClose={closeAlertModal}
          title="创建告警规则"
          size="md"
        >
          <Stack>
            <TextInput
              label="规则名称"
              placeholder="请输入规则名称"
              required
            />

            <Textarea
              label="触发条件"
              placeholder="请输入触发条件"
              rows={3}
              required
            />

            <NumberInput
              label="阈值"
              placeholder="请输入阈值"
              required
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeAlertModal}>
                取消
              </Button>
              <Button>
                创建规则
              </Button>
            </Group>
          </Stack>
        </Modal>

        {/* 设置模态框 */}
        <Modal
          opened={settingsModalOpened}
          onClose={closeSettingsModal}
          title="监控设置"
          size="md"
        >
          <Stack>
            <Alert color="blue">
              <Text size="sm">
                监控设置功能正在开发中，将提供告警阈值、通知设置等配置选项。
              </Text>
            </Alert>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeSettingsModal}>
                关闭
              </Button>
              <Button>
                保存设置
              </Button>
            </Group>
          </Stack>
        </Modal>
      </Stack>
    </Container>
  )
}
