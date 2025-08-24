/**
 * 审计日志管理页面 - 需求5：审计日志
 * 实现日志查看、筛选、分析功能
 */

import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Pagination,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
  Alert,
  Grid,
  RingProgress,
  SimpleGrid,
} from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconEye,
  IconDownload,
  IconRefresh,
  IconChartBar,
  IconShield,
  IconUser,
  IconAlertTriangle,
  IconCheck,
  IconX,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/api/client'

// 审计日志接口
interface AuditLog {
  id: number
  user_id: number
  username: string
  action_type: string
  resource_type: string
  resource_id?: string
  details?: Record<string, any>
  ip_address: string
  user_agent?: string
  timestamp: string
  success: boolean
  error_message?: string
}

// 审计统计接口
interface AuditStatistics {
  total_logs: number
  success_rate: number
  failed_operations: number
  unique_users: number
  top_actions: Array<{ action: string; count: number }>
  hourly_distribution: Array<{ hour: number; count: number }>
}

// 筛选参数接口
interface FilterParams {
  start_date?: Date
  end_date?: Date
  user_id?: number
  action_type?: string
  resource_type?: string
  success?: boolean
  page: number
  limit: number
}

export function AuditLogPage(): JSX.Element {
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)
  const [detailOpened, { open: openDetail, close: closeDetail }] = useDisclosure(false)
  const [statsOpened, { open: openStats, close: closeStats }] = useDisclosure(false)

  // 筛选表单
  const filterForm = useForm<FilterParams>({
    initialValues: {
      page: 1,
      limit: 50,
    },
  })

  // 获取审计日志列表
  const {
    data: logsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['audit-logs', filterForm.values],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: filterForm.values.limit.toString(),
        offset: ((filterForm.values.page - 1) * filterForm.values.limit).toString(),
      })

      if (filterForm.values.start_date) {
        params.append('start_date', filterForm.values.start_date.toISOString().split('T')[0]!)
      }
      if (filterForm.values.end_date) {
        params.append('end_date', filterForm.values.end_date.toISOString().split('T')[0]!)
      }
      if (filterForm.values.user_id) {
        params.append('user_id', filterForm.values.user_id.toString())
      }
      if (filterForm.values.action_type) {
        params.append('action_type', filterForm.values.action_type)
      }
      if (filterForm.values.resource_type) {
        params.append('resource_type', filterForm.values.resource_type)
      }

      const response = await apiClient.get(`/users/audit/logs?${params}`)
      return response.data as AuditLog[]
    },
  })

  // 获取审计统计
  const { data: statsData } = useQuery({
    queryKey: ['audit-statistics'],
    queryFn: async () => {
      const response = await apiClient.get('/users/audit/statistics')
      return response.data as AuditStatistics
    },
  })

  // 导出日志
  const handleExportLogs = async () => {
    try {
      const params = new URLSearchParams()
      if (filterForm.values.start_date) {
        params.append('start_date', filterForm.values.start_date.toISOString().split('T')[0]!)
      }
      if (filterForm.values.end_date) {
        params.append('end_date', filterForm.values.end_date.toISOString().split('T')[0]!)
      }

      const response = await apiClient.get(`/users/audit/export?${params}`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url) // 清理内存

      notifications.show({
        title: '导出成功',
        message: '审计日志已导出',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '导出失败',
        message: error instanceof Error ? error.message : '导出审计日志时发生错误',
        color: 'red',
      })
    }
  }

  const getActionBadgeColor = (actionType: string) => {
    const colorMap: Record<string, string> = {
      login: 'blue',
      logout: 'gray',
      create: 'green',
      update: 'yellow',
      delete: 'red',
      permission_grant: 'purple',
      permission_revoke: 'orange',
    }
    return colorMap[actionType] || 'gray'
  }

  const getSuccessBadge = (success: boolean) => {
    return success ? (
      <Badge color="green" leftSection={<IconCheck size={12} />}>
        成功
      </Badge>
    ) : (
      <Badge color="red" leftSection={<IconX size={12} />}>
        失败
      </Badge>
    )
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>审计日志管理</Title>
          <Text c="dimmed" size="sm">
            查看和分析系统操作日志，确保安全合规
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconChartBar size={16} />} variant="light" onClick={openStats}>
            统计分析
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
            onClick={handleExportLogs}
          >
            导出日志
          </Button>
          <Button leftSection={<IconRefresh size={16} />} onClick={() => refetch()}>
            刷新
          </Button>
        </Group>
      </Group>

      {/* 统计卡片 */}
      {statsData && (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="lg">
          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  总日志数
                </Text>
                <Text fw={700} size="xl">
                  {statsData.total_logs.toLocaleString()}
                </Text>
              </div>
              <IconShield size={32} color="blue" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  成功率
                </Text>
                <Text fw={700} size="xl">
                  {(statsData.success_rate * 100).toFixed(1)}%
                </Text>
              </div>
              <RingProgress
                size={40}
                thickness={4}
                sections={[{ value: statsData.success_rate * 100, color: 'green' }]}
              />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  失败操作
                </Text>
                <Text fw={700} size="xl" c="red">
                  {statsData.failed_operations}
                </Text>
              </div>
              <IconAlertTriangle size={32} color="red" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  活跃用户
                </Text>
                <Text fw={700} size="xl">
                  {statsData.unique_users}
                </Text>
              </div>
              <IconUser size={32} color="purple" />
            </Group>
          </Card>
        </SimpleGrid>
      )}

      {/* 筛选器 */}
      <Paper withBorder p="md" mb="lg">
        <form onSubmit={filterForm.onSubmit(() => {})}>
          <Grid>
            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <DatePickerInput
                label="开始日期"
                placeholder="选择开始日期"
                {...filterForm.getInputProps('start_date')}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <DatePickerInput
                label="结束日期"
                placeholder="选择结束日期"
                {...filterForm.getInputProps('end_date')}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <Select
                label="操作类型"
                placeholder="选择操作类型"
                data={[
                  { value: 'login', label: '登录' },
                  { value: 'logout', label: '登出' },
                  { value: 'create', label: '创建' },
                  { value: 'update', label: '更新' },
                  { value: 'delete', label: '删除' },
                  { value: 'permission_grant', label: '授权' },
                  { value: 'permission_revoke', label: '撤权' },
                ]}
                {...filterForm.getInputProps('action_type')}
                clearable
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <Select
                label="资源类型"
                placeholder="选择资源类型"
                data={[
                  { value: 'user', label: '用户' },
                  { value: 'course', label: '课程' },
                  { value: 'class', label: '班级' },
                  { value: 'permission', label: '权限' },
                  { value: 'backup', label: '备份' },
                ]}
                {...filterForm.getInputProps('resource_type')}
                clearable
              />
            </Grid.Col>
          </Grid>
        </form>
      </Paper>

      {/* 日志列表 */}
      <Paper withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>时间</Table.Th>
              <Table.Th>用户</Table.Th>
              <Table.Th>操作</Table.Th>
              <Table.Th>资源</Table.Th>
              <Table.Th>状态</Table.Th>
              <Table.Th>IP地址</Table.Th>
              <Table.Th>操作</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {logsData?.map(log => (
              <Table.Tr key={log.id}>
                <Table.Td>
                  <Stack gap="xs">
                    <Text size="sm">{new Date(log.timestamp).toLocaleDateString('zh-CN')}</Text>
                    <Text size="xs" c="dimmed">
                      {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                    </Text>
                  </Stack>
                </Table.Td>
                <Table.Td>
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>
                      {log.username}
                    </Text>
                    <Text size="xs" c="dimmed">
                      ID: {log.user_id}
                    </Text>
                  </Stack>
                </Table.Td>
                <Table.Td>
                  <Badge color={getActionBadgeColor(log.action_type)}>{log.action_type}</Badge>
                </Table.Td>
                <Table.Td>
                  <Stack gap="xs">
                    <Text size="sm">{log.resource_type}</Text>
                    {log.resource_id && (
                      <Text size="xs" c="dimmed">
                        ID: {log.resource_id}
                      </Text>
                    )}
                  </Stack>
                </Table.Td>
                <Table.Td>{getSuccessBadge(log.success)}</Table.Td>
                <Table.Td>
                  <Text size="sm" ff="monospace">
                    {log.ip_address}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Tooltip label="查看详情">
                    <ActionIcon
                      variant="light"
                      onClick={() => {
                        setSelectedLog(log)
                        openDetail()
                      }}
                    >
                      <IconEye size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {/* 分页 */}
        {logsData && logsData.length > 0 && (
          <Group justify="center" p="md">
            <Pagination
              value={filterForm.values.page}
              onChange={page => filterForm.setFieldValue('page', page)}
              total={Math.ceil((logsData.length || 0) / filterForm.values.limit)}
            />
          </Group>
        )}
      </Paper>

      {/* 加载和错误状态 */}
      {isLoading && (
        <Paper withBorder p="xl" ta="center">
          <Text>正在加载审计日志...</Text>
        </Paper>
      )}

      {error && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red">
          {error.message}
        </Alert>
      )}

      {/* 日志详情模态框 */}
      <Modal opened={detailOpened} onClose={closeDetail} title="日志详情" size="lg">
        {selectedLog && (
          <Stack>
            <Grid>
              <Grid.Col span={6}>
                <Text fw={500}>操作时间</Text>
                <Text size="sm">{new Date(selectedLog.timestamp).toLocaleString('zh-CN')}</Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>操作用户</Text>
                <Text size="sm">
                  {selectedLog.username} (ID: {selectedLog.user_id})
                </Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>操作类型</Text>
                <Badge color={getActionBadgeColor(selectedLog.action_type)}>
                  {selectedLog.action_type}
                </Badge>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>操作状态</Text>
                {getSuccessBadge(selectedLog.success)}
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>资源类型</Text>
                <Text size="sm">{selectedLog.resource_type}</Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>资源ID</Text>
                <Text size="sm">{selectedLog.resource_id || '无'}</Text>
              </Grid.Col>
              <Grid.Col span={12}>
                <Text fw={500}>IP地址</Text>
                <Text size="sm" ff="monospace">
                  {selectedLog.ip_address}
                </Text>
              </Grid.Col>
              {selectedLog.user_agent && (
                <Grid.Col span={12}>
                  <Text fw={500}>用户代理</Text>
                  <Text size="sm" style={{ wordBreak: 'break-all' }}>
                    {selectedLog.user_agent}
                  </Text>
                </Grid.Col>
              )}
              {selectedLog.error_message && (
                <Grid.Col span={12}>
                  <Text fw={500} c="red">
                    错误信息
                  </Text>
                  <Paper withBorder p="sm" bg="red.0">
                    <Text size="sm" c="red">
                      {selectedLog.error_message}
                    </Text>
                  </Paper>
                </Grid.Col>
              )}
              {selectedLog.details && (
                <Grid.Col span={12}>
                  <Text fw={500}>操作详情</Text>
                  <Paper withBorder p="sm" bg="gray.0">
                    <Text size="sm" ff="monospace">
                      {JSON.stringify(selectedLog.details, null, 2)}
                    </Text>
                  </Paper>
                </Grid.Col>
              )}
            </Grid>
          </Stack>
        )}
      </Modal>

      {/* 统计分析模态框 */}
      <Modal opened={statsOpened} onClose={closeStats} title="审计统计分析" size="xl">
        {statsData && (
          <Stack>
            <SimpleGrid cols={2}>
              <Card withBorder>
                <Text fw={500} mb="md">
                  热门操作
                </Text>
                <Stack gap="xs">
                  {statsData.top_actions.map((action, index) => (
                    <Group key={index} justify="space-between">
                      <Badge color={getActionBadgeColor(action.action)}>{action.action}</Badge>
                      <Text size="sm">{action.count} 次</Text>
                    </Group>
                  ))}
                </Stack>
              </Card>

              <Card withBorder>
                <Text fw={500} mb="md">
                  24小时分布
                </Text>
                <Stack gap="xs">
                  {statsData.hourly_distribution.slice(0, 8).map((hour, index) => (
                    <Group key={index} justify="space-between">
                      <Text size="sm">{hour.hour}:00</Text>
                      <Text size="sm">{hour.count} 次</Text>
                    </Group>
                  ))}
                </Stack>
              </Card>
            </SimpleGrid>
          </Stack>
        )}
      </Modal>
    </Container>
  )
}
