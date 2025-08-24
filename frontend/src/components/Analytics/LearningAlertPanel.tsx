/**
 * 学习预警面板组件 - 需求14实现
 */
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Modal,
  Stack,
  Text,
  Title,
  ActionIcon,
  Tooltip,
  Progress,
  Divider,
  List,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import {
  IconAlertTriangle,
  IconClock,
  IconTrendingDown,
  IconUser,
  IconUsers,
  IconEye,
  IconBell,
  IconTarget,
  IconChartLine,
} from '@tabler/icons-react'
import { useState, useEffect } from 'react'

// 预警类型定义
interface LearningAlert {
  id: number
  type: 'individual' | 'class' | 'system'
  severity: 'low' | 'medium' | 'high' | 'critical'
  category: 'attendance' | 'performance' | 'engagement' | 'progress'
  title: string
  description: string
  studentId?: number
  studentName?: string
  classId?: number
  className?: string
  metrics: {
    current: number
    threshold: number
    trend: 'up' | 'down' | 'stable'
  }
  suggestions: string[]
  createdAt: string
  isRead: boolean
  isResolved: boolean
}

interface LearningAlertPanelProps {
  classId?: number
  studentId?: number
  showHeader?: boolean
  maxAlerts?: number
}

export function LearningAlertPanel({
  classId,
  studentId,
  showHeader = true,
  maxAlerts = 10,
}: LearningAlertPanelProps): JSX.Element {
  const [alerts, setAlerts] = useState<LearningAlert[]>([])
  const [selectedAlert, setSelectedAlert] = useState<LearningAlert | null>(null)
  const [loading, setLoading] = useState(false)

  const [alertModalOpened, { open: openAlertModal, close: closeAlertModal }] = useDisclosure(false)

  // 模拟加载预警数据
  useEffect(() => {
    loadAlerts()
  }, [classId, studentId])

  const loadAlerts = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockAlerts: LearningAlert[] = [
        {
          id: 1,
          type: 'individual',
          severity: 'high',
          category: 'attendance',
          title: '连续缺勤预警',
          description: '学生张三已连续3天未完成训练',
          studentId: 1,
          studentName: '张三',
          classId: 1,
          className: '英语四级A班',
          metrics: {
            current: 3,
            threshold: 3,
            trend: 'up',
          },
          suggestions: ['联系学生了解情况', '提供补课安排', '调整学习计划'],
          createdAt: '2024-01-20T09:00:00Z',
          isRead: false,
          isResolved: false,
        },
        {
          id: 2,
          type: 'individual',
          severity: 'medium',
          category: 'performance',
          title: '正确率下降预警',
          description: '学生李四近期正确率降至55%，低于60%阈值',
          studentId: 2,
          studentName: '李四',
          classId: 1,
          className: '英语四级A班',
          metrics: {
            current: 55,
            threshold: 60,
            trend: 'down',
          },
          suggestions: ['安排个别辅导', '调整学习难度', '增加练习量'],
          createdAt: '2024-01-20T08:30:00Z',
          isRead: true,
          isResolved: false,
        },
        {
          id: 3,
          type: 'class',
          severity: 'medium',
          category: 'progress',
          title: '班级进度滞后',
          description: '英语四级A班整体学习进度落后预期15%',
          classId: 1,
          className: '英语四级A班',
          metrics: {
            current: 65,
            threshold: 80,
            trend: 'down',
          },
          suggestions: ['调整教学进度', '增加课时安排', '优化教学方法'],
          createdAt: '2024-01-19T16:00:00Z',
          isRead: true,
          isResolved: false,
        },
        {
          id: 4,
          type: 'individual',
          severity: 'critical',
          category: 'engagement',
          title: '学习时间异常',
          description: '学生王五每日学习时间不足10分钟',
          studentId: 3,
          studentName: '王五',
          classId: 1,
          className: '英语四级A班',
          metrics: {
            current: 8,
            threshold: 30,
            trend: 'down',
          },
          suggestions: ['紧急联系学生', '了解学习困难', '制定专项计划'],
          createdAt: '2024-01-19T14:20:00Z',
          isRead: false,
          isResolved: false,
        },
      ]

      // 根据筛选条件过滤
      let filteredAlerts = mockAlerts
      if (classId) {
        filteredAlerts = filteredAlerts.filter(alert => alert.classId === classId)
      }
      if (studentId) {
        filteredAlerts = filteredAlerts.filter(alert => alert.studentId === studentId)
      }

      setAlerts(filteredAlerts.slice(0, maxAlerts))
    } catch (error) {
      // 静默处理错误，实际应用中可以显示错误通知
    } finally {
      setLoading(false)
    }
  }

  const getSeverityConfig = (severity: string) => {
    const configs = {
      low: { color: 'blue', label: '低', icon: IconBell },
      medium: { color: 'yellow', label: '中', icon: IconAlertTriangle },
      high: { color: 'orange', label: '高', icon: IconAlertTriangle },
      critical: { color: 'red', label: '紧急', icon: IconAlertTriangle },
    }
    return configs[severity as keyof typeof configs] || configs.low
  }

  const getCategoryConfig = (category: string) => {
    const configs = {
      attendance: { label: '出勤', icon: IconClock },
      performance: { label: '成绩', icon: IconChartLine },
      engagement: { label: '参与度', icon: IconUser },
      progress: { label: '进度', icon: IconTrendingDown },
    }
    return configs[category as keyof typeof configs] || configs.attendance
  }

  const handleAlertClick = (alert: LearningAlert) => {
    setSelectedAlert(alert)
    openAlertModal()

    // 标记为已读
    if (!alert.isRead) {
      setAlerts(prev => prev.map(a => (a.id === alert.id ? { ...a, isRead: true } : a)))
    }
  }

  const handleResolveAlert = (alertId: number) => {
    setAlerts(prev => prev.map(a => (a.id === alertId ? { ...a, isResolved: true } : a)))
    closeAlertModal()
  }

  const unreadCount = alerts.filter(alert => !alert.isRead).length
  const criticalCount = alerts.filter(alert => alert.severity === 'critical').length

  return (
    <>
      {showHeader && (
        <Group justify="space-between" mb="md">
          <Group gap="xs">
            <Title order={3}>学习预警</Title>
            {unreadCount > 0 && (
              <Badge color="red" size="sm">
                {unreadCount} 条未读
              </Badge>
            )}
            {criticalCount > 0 && (
              <Badge color="red" variant="light" size="sm">
                {criticalCount} 条紧急
              </Badge>
            )}
          </Group>
          <Button size="sm" variant="light" onClick={loadAlerts} loading={loading}>
            刷新
          </Button>
        </Group>
      )}

      <Stack gap="xs">
        {alerts.length === 0 ? (
          <Alert color="green" icon={<IconTarget size={16} />}>
            <Text size="sm">暂无预警信息，学习状态良好！</Text>
          </Alert>
        ) : (
          alerts.map(alert => {
            const severityConfig = getSeverityConfig(alert.severity)
            const categoryConfig = getCategoryConfig(alert.category)

            return (
              <Card
                key={alert.id}
                withBorder
                p="sm"
                style={{
                  cursor: 'pointer',
                  opacity: alert.isResolved ? 0.6 : 1,
                  borderColor:
                    alert.severity === 'critical' ? 'var(--mantine-color-red-4)' : undefined,
                }}
                onClick={() => handleAlertClick(alert)}
              >
                <Group justify="space-between" align="flex-start">
                  <Group gap="xs" align="flex-start" style={{ flex: 1 }}>
                    <severityConfig.icon
                      size={16}
                      color={`var(--mantine-color-${severityConfig.color}-6)`}
                    />
                    <div style={{ flex: 1 }}>
                      <Group gap="xs" mb="xs">
                        <Text size="sm" fw={500}>
                          {alert.title}
                        </Text>
                        <Badge color={severityConfig.color} size="xs">
                          {severityConfig.label}
                        </Badge>
                        <Badge variant="light" size="xs">
                          {categoryConfig.label}
                        </Badge>
                        {!alert.isRead && (
                          <Badge color="blue" size="xs">
                            新
                          </Badge>
                        )}
                      </Group>

                      <Text size="xs" c="dimmed" mb="xs">
                        {alert.description}
                      </Text>

                      {alert.studentName && (
                        <Group gap="xs">
                          <IconUser size={12} />
                          <Text size="xs" c="dimmed">
                            {alert.studentName}
                          </Text>
                        </Group>
                      )}

                      {alert.className && alert.type === 'class' && (
                        <Group gap="xs">
                          <IconUsers size={12} />
                          <Text size="xs" c="dimmed">
                            {alert.className}
                          </Text>
                        </Group>
                      )}
                    </div>
                  </Group>

                  <Group gap="xs">
                    <Tooltip label="查看详情">
                      <ActionIcon variant="light" size="sm">
                        <IconEye size={14} />
                      </ActionIcon>
                    </Tooltip>
                    {alert.isResolved && (
                      <Badge color="green" size="xs">
                        已解决
                      </Badge>
                    )}
                  </Group>
                </Group>
              </Card>
            )
          })
        )}
      </Stack>

      {/* 预警详情模态框 */}
      <Modal opened={alertModalOpened} onClose={closeAlertModal} title="预警详情" size="md">
        {selectedAlert && (
          <Stack gap="md">
            <Group justify="space-between">
              <Group gap="xs">
                <Badge color={getSeverityConfig(selectedAlert.severity).color}>
                  {getSeverityConfig(selectedAlert.severity).label}级预警
                </Badge>
                <Badge variant="light">{getCategoryConfig(selectedAlert.category).label}</Badge>
              </Group>
              <Text size="xs" c="dimmed">
                {new Date(selectedAlert.createdAt).toLocaleString('zh-CN')}
              </Text>
            </Group>

            <div>
              <Text fw={500} mb="xs">
                {selectedAlert.title}
              </Text>
              <Text size="sm" c="dimmed">
                {selectedAlert.description}
              </Text>
            </div>

            <Card withBorder p="sm">
              <Text size="sm" fw={500} mb="xs">
                数据指标
              </Text>
              <Group justify="space-between" mb="xs">
                <Text size="sm">当前值</Text>
                <Text size="sm" fw={500}>
                  {selectedAlert.metrics.current}
                </Text>
              </Group>
              <Group justify="space-between" mb="xs">
                <Text size="sm">阈值</Text>
                <Text size="sm">{selectedAlert.metrics.threshold}</Text>
              </Group>
              <Progress
                value={(selectedAlert.metrics.current / selectedAlert.metrics.threshold) * 100}
                color={
                  selectedAlert.metrics.current < selectedAlert.metrics.threshold ? 'red' : 'green'
                }
                size="sm"
              />
            </Card>

            <div>
              <Text size="sm" fw={500} mb="xs">
                建议措施
              </Text>
              <List size="sm">
                {selectedAlert.suggestions.map((suggestion, index) => (
                  <List.Item key={index}>{suggestion}</List.Item>
                ))}
              </List>
            </div>

            <Divider />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeAlertModal}>
                关闭
              </Button>
              {!selectedAlert.isResolved && (
                <Button onClick={() => handleResolveAlert(selectedAlert.id)}>标记为已解决</Button>
              )}
            </Group>
          </Stack>
        )}
      </Modal>
    </>
  )
}
