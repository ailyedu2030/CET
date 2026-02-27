/**
 * 权限审计页面 - 需求3：权限与角色管理
 * 实现权限变更日志、操作记录、合规检查功能
 */

import {
  Container,
  Title,
  Paper,
  TextInput,
  Button,
  Group,
  Stack,
  Table,
  Badge,
  Text,
  Pagination,
  Select,
  Card,
  SimpleGrid,
  Alert,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import {
  IconSearch,
  IconDownload,
  IconRefresh,
  IconEye,
  IconAlertTriangle,
  IconShield,
  IconClock,
  IconUser,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { auditApi } from '@/api/permissions'

export function PermissionAuditPage(): JSX.Element {
  const [page, setPage] = useState(1)
  const [timeRange] = useState('7d')

  // 搜索表单
  const searchForm = useForm({
    initialValues: {
      user_id: '',
      action: '',
      resource_type: '',
      start_date: null as Date | null,
      end_date: null as Date | null,
    },
  })

  // 获取审计日志
  const {
    data: auditData,
  } = useQuery({
    queryKey: ['audit-logs', page, searchForm.values],
    queryFn: async () => {
      return await auditApi.getAuditLogs({
        skip: (page - 1) * 20,
        limit: 20,
        user_id: searchForm.values.user_id ? parseInt(searchForm.values.user_id) : undefined,
        action: searchForm.values.action || undefined,
        resource_type: searchForm.values.resource_type || undefined,
        start_date: searchForm.values.start_date?.toISOString(),
        end_date: searchForm.values.end_date?.toISOString(),
      })
    },
  })

  // 获取安全事件
  const { data: securityEvents } = useQuery({
    queryKey: ['security-events'],
    queryFn: async () => {
      return await auditApi.getSecurityEvents({
        skip: 0,
        limit: 10,
      })
    },
  })

  // 获取权限统计
  const { data: statistics } = useQuery({
    queryKey: ['permission-statistics', timeRange],
    queryFn: async () => {
      return await auditApi.getPermissionStatistics(timeRange)
    },
  })

  // 导出审计报告
  const handleExportReport = async (format: 'pdf' | 'excel') => {
    try {
      const blob = await auditApi.generateAuditReport({
        start_date: searchForm.values.start_date?.toISOString() || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end_date: searchForm.values.end_date?.toISOString() || new Date().toISOString(),
        format,
      })

      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `权限审计报告_${new Date().toISOString().split('T')[0]}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      notifications.show({
        title: '导出成功',
        message: `审计报告已导出为${format.toUpperCase()}文件`,
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '导出失败',
        message: error instanceof Error ? error.message : '导出过程中发生错误',
        color: 'red',
      })
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'create':
        return 'green'
      case 'update':
        return 'blue'
      case 'delete':
        return 'red'
      case 'assign':
        return 'orange'
      case 'revoke':
        return 'gray'
      default:
        return 'blue'
    }
  }



  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>权限审计</Title>
          <Text c="dimmed" size="sm">
            监控权限变更、操作记录和安全事件
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
            onClick={() => handleExportReport('excel')}
          >
            导出Excel
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            onClick={() => handleExportReport('pdf')}
          >
            导出PDF
          </Button>
          <Button leftSection={<IconRefresh size={16} />} variant="light">
            刷新
          </Button>
        </Group>
      </Group>

      {/* 统计卡片 */}
      <SimpleGrid cols={{ base: 1, md: 4 }} mb="lg">
        <Card withBorder>
          <Group justify="space-between">
            <div>
              <Text size="sm" c="dimmed">
                总操作数
              </Text>
              <Text size="xl" fw={700}>
                {statistics?.['total_operations'] || 0}
              </Text>
            </div>
            <IconShield size={32} color="blue" />
          </Group>
        </Card>

        <Card withBorder>
          <Group justify="space-between">
            <div>
              <Text size="sm" c="dimmed">
                权限变更
              </Text>
              <Text size="xl" fw={700}>
                {statistics?.['permission_changes'] || 0}
              </Text>
            </div>
            <IconUser size={32} color="green" />
          </Group>
        </Card>

        <Card withBorder>
          <Group justify="space-between">
            <div>
              <Text size="sm" c="dimmed">
                安全事件
              </Text>
              <Text size="xl" fw={700}>
                {statistics?.['security_events'] || 0}
              </Text>
            </div>
            <IconAlertTriangle size={32} color="red" />
          </Group>
        </Card>

        <Card withBorder>
          <Group justify="space-between">
            <div>
              <Text size="sm" c="dimmed">
                活跃用户
              </Text>
              <Text size="xl" fw={700}>
                {statistics?.['active_users'] || 0}
              </Text>
            </div>
            <IconClock size={32} color="orange" />
          </Group>
        </Card>
      </SimpleGrid>

      {/* 搜索过滤器 */}
      <Paper withBorder p="md" mb="lg">
        <form onSubmit={searchForm.onSubmit(() => setPage(1))}>
          <SimpleGrid cols={{ base: 1, md: 3 }} mb="md">
            <TextInput
              label="用户ID"
              placeholder="输入用户ID"
              {...searchForm.getInputProps('user_id')}
            />
            <Select
              label="操作类型"
              placeholder="选择操作类型"
              data={[
                { value: '', label: '全部' },
                { value: 'create', label: '创建' },
                { value: 'update', label: '更新' },
                { value: 'delete', label: '删除' },
                { value: 'assign', label: '分配' },
                { value: 'revoke', label: '回收' },
              ]}
              {...searchForm.getInputProps('action')}
            />
            <Select
              label="资源类型"
              placeholder="选择资源类型"
              data={[
                { value: '', label: '全部' },
                { value: 'role', label: '角色' },
                { value: 'permission', label: '权限' },
                { value: 'user', label: '用户' },
              ]}
              {...searchForm.getInputProps('resource_type')}
            />
          </SimpleGrid>
          <Group justify="space-between">
            <Group>
              <DatePickerInput
                label="开始日期"
                placeholder="选择开始日期"
                {...searchForm.getInputProps('start_date')}
              />
              <DatePickerInput
                label="结束日期"
                placeholder="选择结束日期"
                {...searchForm.getInputProps('end_date')}
              />
            </Group>
            <Button type="submit" leftSection={<IconSearch size={16} />}>
              搜索
            </Button>
          </Group>
        </form>
      </Paper>

      {/* 安全事件警告 */}
      {securityEvents && securityEvents.length > 0 && (
        <Alert color="red" icon={<IconAlertTriangle size={16} />} mb="lg">
          <Text fw={500}>检测到 {securityEvents.length} 个安全事件</Text>
          <Text size="sm">
            最新事件：{securityEvents[0]?.description} ({securityEvents[0]?.created_at ? new Date(securityEvents[0].created_at).toLocaleString() : '未知时间'})
          </Text>
        </Alert>
      )}

      {/* 审计日志表格 */}
      <Paper withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>时间</Table.Th>
              <Table.Th>用户</Table.Th>
              <Table.Th>操作</Table.Th>
              <Table.Th>资源</Table.Th>
              <Table.Th>详情</Table.Th>
              <Table.Th>IP地址</Table.Th>
              <Table.Th>操作</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {auditData?.items.map(log => (
              <Table.Tr key={log.id}>
                <Table.Td>
                  <Text size="sm">{new Date(log.created_at).toLocaleString()}</Text>
                </Table.Td>
                <Table.Td>
                  <Stack gap="xs">
                    <Text fw={500} size="sm">
                      {log.username}
                    </Text>
                    <Text size="xs" c="dimmed">
                      ID: {log.user_id}
                    </Text>
                  </Stack>
                </Table.Td>
                <Table.Td>
                  <Badge color={getActionColor(log.action)}>{log.action}</Badge>
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
                <Table.Td>
                  <Text size="sm" lineClamp={2}>
                    {JSON.stringify(log.details)}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{log.ip_address}</Text>
                </Table.Td>
                <Table.Td>
                  <Tooltip label="查看详情">
                    <ActionIcon variant="light">
                      <IconEye size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {auditData && auditData.total > 20 && (
          <Group justify="center" p="md">
            <Pagination
              value={page}
              onChange={setPage}
              total={Math.ceil(auditData.total / 20)}
            />
          </Group>
        )}
      </Paper>
    </Container>
  )
}
