/**
 * 数据备份管理页面 - 需求9：数据备份与恢复
 * 实现备份管理、恢复操作、备份监控功能
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
  TextInput,
  Title,
  Tooltip,
  Alert,
  Grid,
  Progress,
  SimpleGrid,
  Tabs,
  NumberInput,
  Checkbox,
} from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconDownload,
  IconUpload,
  IconRefresh,
  IconTrash,
  IconEye,
  IconPlayerPlay,
  IconDatabase,
  IconShield,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconSettings,
  IconChartBar,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/api/client'

// 备份信息接口
interface BackupInfo {
  backup_id: string
  backup_type: string
  file_path: string
  file_size: number
  status: string
  created_at: string
  expires_at?: string
  description?: string
  tables: string[]
  compression: boolean
  encryption: boolean
  checksum: string
}

// 恢复信息接口
interface RestoreInfo {
  restore_id: string
  backup_id: string
  restore_type: string
  status: string
  progress_percentage: number
  current_step: string
  estimated_remaining_time: string
  started_at: string
  completed_at?: string
  error_message?: string
}

// 备份统计接口
interface BackupStatistics {
  total_backups: number
  successful_backups: number
  failed_backups: number
  total_size: number
  average_size: number
  backup_types: Record<string, { count: number; size: number }>
  period_start: string
  period_end: string
}

// 备份请求接口
interface BackupRequest {
  backup_type: string
  tables: string[]
  storage_location: string
  compression: boolean
  encryption: boolean
  description?: string
}

export function BackupManagementPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('backups')
  const [selectedBackup, setSelectedBackup] = useState<BackupInfo | null>(null)

  const [page, setPage] = useState(1)

  const [backupModalOpened, { open: openBackupModal, close: closeBackupModal }] =
    useDisclosure(false)
  const [restoreModalOpened, { open: openRestoreModal, close: closeRestoreModal }] =
    useDisclosure(false)
  const [scheduleModalOpened, { open: openScheduleModal, close: closeScheduleModal }] =
    useDisclosure(false)
  const [detailModalOpened, { open: openDetailModal, close: closeDetailModal }] =
    useDisclosure(false)

  // 备份表单
  const backupForm = useForm<BackupRequest>({
    initialValues: {
      backup_type: 'full',
      tables: [],
      storage_location: 'local',
      compression: true,
      encryption: true,
      description: '',
    },
  })

  // 恢复表单
  const restoreForm = useForm({
    initialValues: {
      backup_id: '',
      restore_type: 'full',
      tables: [] as string[],
      confirm_overwrite: false,
      validate_before_restore: true,
      target_time: null as Date | null,
    },
  })

  // 调度表单
  const scheduleForm = useForm({
    initialValues: {
      name: '',
      backup_type: 'incremental',
      schedule: '0 2 * * *', // 每天凌晨2点
      retention_days: 30,
      enabled: true,
    },
  })

  // 获取备份列表
  const {
    data: backupsData,
    isLoading: backupsLoading,
    error: backupsError,
  } = useQuery({
    queryKey: ['backups', page],
    queryFn: async () => {
      const response = await apiClient.get(`/users/backup/?limit=20&offset=${(page - 1) * 20}`)
      return response.data as BackupInfo[]
    },
  })

  // 获取恢复操作列表
  const { data: restoresData } = useQuery({
    queryKey: ['restores'],
    queryFn: async () => {
      const response = await apiClient.get('/users/restore/')
      return response.data as RestoreInfo[]
    },
  })

  // 获取备份统计
  const { data: statsData } = useQuery({
    queryKey: ['backup-statistics'],
    queryFn: async () => {
      const response = await apiClient.get('/users/backup/statistics?days=30')
      return response.data as BackupStatistics
    },
  })

  // 创建备份
  const createBackupMutation = useMutation({
    mutationFn: async (data: BackupRequest) => {
      return await apiClient.post('/users/backup/', data)
    },
    onSuccess: () => {
      notifications.show({
        title: '备份创建成功',
        message: '数据备份已开始创建',
        color: 'green',
      })
      closeBackupModal()
      backupForm.reset()
      queryClient.invalidateQueries({ queryKey: ['backups'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '备份创建失败',
        message: error.response?.data?.detail || '创建备份时发生错误',
        color: 'red',
      })
    },
  })

  // 删除备份
  const deleteBackupMutation = useMutation({
    mutationFn: async (backupId: string) => {
      return await apiClient.delete(`/users/backup/${backupId}`)
    },
    onSuccess: () => {
      notifications.show({
        title: '删除成功',
        message: '备份已删除',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['backups'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '删除失败',
        message: error.response?.data?.detail || '删除备份时发生错误',
        color: 'red',
      })
    },
  })

  // 开始恢复
  const startRestoreMutation = useMutation({
    mutationFn: async (data: typeof restoreForm.values) => {
      return await apiClient.post('/users/restore/', {
        backup_id: data.backup_id,
        restore_type: data.restore_type,
        tables: data.tables,
        confirm_overwrite: data.confirm_overwrite,
        validate_before_restore: data.validate_before_restore,
        target_time: data.target_time?.toISOString(),
      })
    },
    onSuccess: () => {
      notifications.show({
        title: '恢复开始',
        message: '数据恢复操作已开始',
        color: 'green',
      })
      closeRestoreModal()
      restoreForm.reset()
      queryClient.invalidateQueries({ queryKey: ['restores'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '恢复失败',
        message: error.response?.data?.detail || '开始恢复时发生错误',
        color: 'red',
      })
    },
  })

  // 配置备份调度
  const scheduleBackupMutation = useMutation({
    mutationFn: async (data: typeof scheduleForm.values) => {
      return await apiClient.post('/users/backup/schedule', data)
    },
    onSuccess: () => {
      notifications.show({
        title: '调度配置成功',
        message: '备份调度已配置',
        color: 'green',
      })
      closeScheduleModal()
      scheduleForm.reset()
    },
    onError: (error: any) => {
      notifications.show({
        title: '配置失败',
        message: error.response?.data?.detail || '配置备份调度时发生错误',
        color: 'red',
      })
    },
  })

  const handleCreateBackup = () => {
    backupForm.reset()
    openBackupModal()
  }

  const handleRestore = (backup: BackupInfo) => {
    restoreForm.setFieldValue('backup_id', backup.backup_id)
    openRestoreModal()
  }

  const handleViewDetails = (backup: BackupInfo) => {
    setSelectedBackup(backup)
    openDetailModal()
  }

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    if (bytes === 0) return '0 B'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; label: string }> = {
      completed: { color: 'green', label: '完成' },
      in_progress: { color: 'blue', label: '进行中' },
      failed: { color: 'red', label: '失败' },
      pending: { color: 'yellow', label: '等待中' },
    }
    const statusInfo = statusMap[status] || { color: 'gray', label: status }
    return <Badge color={statusInfo.color}>{statusInfo.label}</Badge>
  }

  const getBackupTypeBadge = (type: string) => {
    const typeMap: Record<string, { color: string; label: string }> = {
      full: { color: 'blue', label: '全量备份' },
      incremental: { color: 'green', label: '增量备份' },
      differential: { color: 'orange', label: '差异备份' },
    }
    const typeInfo = typeMap[type] || { color: 'gray', label: type }
    return <Badge color={typeInfo.color}>{typeInfo.label}</Badge>
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>数据备份管理</Title>
          <Text c="dimmed" size="sm">
            管理系统数据备份和恢复操作，确保数据安全
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconSettings size={16} />}
            variant="light"
            onClick={openScheduleModal}
          >
            备份调度
          </Button>
          <Button leftSection={<IconUpload size={16} />} onClick={handleCreateBackup}>
            创建备份
          </Button>
          <Button leftSection={<IconRefresh size={16} />} variant="light">
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
                  总备份数
                </Text>
                <Text fw={700} size="xl">
                  {statsData.total_backups}
                </Text>
              </div>
              <IconDatabase size={32} color="blue" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  成功率
                </Text>
                <Text fw={700} size="xl">
                  {((statsData.successful_backups / statsData.total_backups) * 100).toFixed(1)}%
                </Text>
              </div>
              <IconCheck size={32} color="green" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  失败备份
                </Text>
                <Text fw={700} size="xl" c="red">
                  {statsData.failed_backups}
                </Text>
              </div>
              <IconX size={32} color="red" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  总大小
                </Text>
                <Text fw={700} size="xl">
                  {formatFileSize(statsData.total_size)}
                </Text>
              </div>
              <IconShield size={32} color="purple" />
            </Group>
          </Card>
        </SimpleGrid>
      )}

      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'backups')}>
        <Tabs.List>
          <Tabs.Tab value="backups" leftSection={<IconDatabase size={16} />}>
            备份列表
          </Tabs.Tab>
          <Tabs.Tab value="restores" leftSection={<IconDownload size={16} />}>
            恢复操作
          </Tabs.Tab>
          <Tabs.Tab value="statistics" leftSection={<IconChartBar size={16} />}>
            统计分析
          </Tabs.Tab>
        </Tabs.List>

        {/* 备份列表标签页 */}
        <Tabs.Panel value="backups" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>备份信息</Table.Th>
                  <Table.Th>类型</Table.Th>
                  <Table.Th>大小</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>创建时间</Table.Th>
                  <Table.Th>过期时间</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {backupsData?.map(backup => (
                  <Table.Tr key={backup.backup_id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text fw={500} size="sm">
                          {backup.backup_id}
                        </Text>
                        {backup.description && (
                          <Text size="xs" c="dimmed">
                            {backup.description}
                          </Text>
                        )}
                        <Group gap="xs">
                          {backup.compression && (
                            <Badge size="xs" color="blue">
                              压缩
                            </Badge>
                          )}
                          {backup.encryption && (
                            <Badge size="xs" color="green">
                              加密
                            </Badge>
                          )}
                        </Group>
                      </Stack>
                    </Table.Td>
                    <Table.Td>{getBackupTypeBadge(backup.backup_type)}</Table.Td>
                    <Table.Td>
                      <Text size="sm">{formatFileSize(backup.file_size)}</Text>
                    </Table.Td>
                    <Table.Td>{getStatusBadge(backup.status)}</Table.Td>
                    <Table.Td>
                      <Text size="sm">{new Date(backup.created_at).toLocaleString('zh-CN')}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {backup.expires_at
                          ? new Date(backup.expires_at).toLocaleDateString('zh-CN')
                          : '永久'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="查看详情">
                          <ActionIcon variant="light" onClick={() => handleViewDetails(backup)}>
                            <IconEye size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="恢复数据">
                          <ActionIcon
                            variant="light"
                            color="green"
                            onClick={() => handleRestore(backup)}
                            disabled={backup.status !== 'completed'}
                          >
                            <IconPlayerPlay size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="删除备份">
                          <ActionIcon
                            variant="light"
                            color="red"
                            onClick={() => deleteBackupMutation.mutate(backup.backup_id)}
                          >
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>

            {backupsData && backupsData.length > 20 && (
              <Group justify="center" p="md">
                <Pagination
                  value={page}
                  onChange={setPage}
                  total={Math.ceil(backupsData.length / 20)}
                />
              </Group>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 恢复操作标签页 */}
        <Tabs.Panel value="restores" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>恢复ID</Table.Th>
                  <Table.Th>备份ID</Table.Th>
                  <Table.Th>类型</Table.Th>
                  <Table.Th>进度</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>开始时间</Table.Th>
                  <Table.Th>预计剩余</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {restoresData?.map(restore => (
                  <Table.Tr key={restore.restore_id}>
                    <Table.Td>
                      <Text size="sm" ff="monospace">
                        {restore.restore_id}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" ff="monospace">
                        {restore.backup_id}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge>{restore.restore_type}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Stack gap="xs">
                        <Progress value={restore.progress_percentage} size="sm" />
                        <Text size="xs">{restore.progress_percentage.toFixed(1)}%</Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>{getStatusBadge(restore.status)}</Table.Td>
                    <Table.Td>
                      <Text size="sm">{new Date(restore.started_at).toLocaleString('zh-CN')}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{restore.estimated_remaining_time}</Text>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        </Tabs.Panel>

        {/* 统计分析标签页 */}
        <Tabs.Panel value="statistics" pt="md">
          {statsData && (
            <Grid>
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card withBorder>
                  <Title order={4} mb="md">
                    备份类型分布
                  </Title>
                  <Stack>
                    {Object.entries(statsData.backup_types).map(([type, data]) => (
                      <Group key={type} justify="space-between">
                        <div>
                          {getBackupTypeBadge(type)}
                          <Text size="sm" c="dimmed">
                            {data.count} 个备份
                          </Text>
                        </div>
                        <Text size="sm">{formatFileSize(data.size)}</Text>
                      </Group>
                    ))}
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card withBorder>
                  <Title order={4} mb="md">
                    备份趋势
                  </Title>
                  <Stack>
                    <Group justify="space-between">
                      <Text size="sm">统计周期</Text>
                      <Text size="sm">
                        {new Date(statsData.period_start).toLocaleDateString('zh-CN')} -{' '}
                        {new Date(statsData.period_end).toLocaleDateString('zh-CN')}
                      </Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">平均大小</Text>
                      <Text size="sm">{formatFileSize(statsData.average_size)}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">成功率</Text>
                      <Text size="sm">
                        {((statsData.successful_backups / statsData.total_backups) * 100).toFixed(
                          1
                        )}
                        %
                      </Text>
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          )}
        </Tabs.Panel>
      </Tabs>

      {/* 创建备份模态框 */}
      <Modal opened={backupModalOpened} onClose={closeBackupModal} title="创建数据备份" size="lg">
        <form onSubmit={backupForm.onSubmit(values => createBackupMutation.mutate(values))}>
          <Stack>
            <Select
              label="备份类型"
              required
              data={[
                { value: 'full', label: '全量备份' },
                { value: 'incremental', label: '增量备份' },
                { value: 'differential', label: '差异备份' },
              ]}
              {...backupForm.getInputProps('backup_type')}
            />

            <Select
              label="存储位置"
              required
              data={[
                { value: 'local', label: '本地存储' },
                { value: 'cloud', label: '云存储' },
              ]}
              {...backupForm.getInputProps('storage_location')}
            />

            <TextInput
              label="备份描述"
              placeholder="输入备份描述（可选）"
              {...backupForm.getInputProps('description')}
            />

            <Group>
              <Checkbox
                label="启用压缩"
                {...backupForm.getInputProps('compression', { type: 'checkbox' })}
              />
              <Checkbox
                label="启用加密"
                {...backupForm.getInputProps('encryption', { type: 'checkbox' })}
              />
            </Group>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeBackupModal}>
                取消
              </Button>
              <Button type="submit" loading={createBackupMutation.isPending}>
                创建备份
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 恢复数据模态框 */}
      <Modal opened={restoreModalOpened} onClose={closeRestoreModal} title="恢复数据" size="lg">
        <form onSubmit={restoreForm.onSubmit(values => startRestoreMutation.mutate(values))}>
          <Stack>
            <Alert icon={<IconAlertTriangle size={16} />} title="警告" color="orange">
              数据恢复操作将覆盖现有数据，请确认您了解此操作的风险。
            </Alert>

            <TextInput
              label="备份ID"
              required
              readOnly
              {...restoreForm.getInputProps('backup_id')}
            />

            <Select
              label="恢复类型"
              required
              data={[
                { value: 'full', label: '完整恢复' },
                { value: 'partial', label: '部分恢复' },
                { value: 'point_in_time', label: '时间点恢复' },
              ]}
              {...restoreForm.getInputProps('restore_type')}
            />

            {restoreForm.values.restore_type === 'point_in_time' && (
              <DatePickerInput
                label="目标时间点"
                placeholder="选择恢复的目标时间"
                {...restoreForm.getInputProps('target_time')}
              />
            )}

            <Group>
              <Checkbox
                label="确认覆盖现有数据"
                {...restoreForm.getInputProps('confirm_overwrite', { type: 'checkbox' })}
              />
              <Checkbox
                label="恢复前验证"
                {...restoreForm.getInputProps('validate_before_restore', { type: 'checkbox' })}
              />
            </Group>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeRestoreModal}>
                取消
              </Button>
              <Button
                type="submit"
                loading={startRestoreMutation.isPending}
                disabled={!restoreForm.values.confirm_overwrite}
                color="orange"
              >
                开始恢复
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 备份调度模态框 */}
      <Modal
        opened={scheduleModalOpened}
        onClose={closeScheduleModal}
        title="配置备份调度"
        size="lg"
      >
        <form onSubmit={scheduleForm.onSubmit(values => scheduleBackupMutation.mutate(values))}>
          <Stack>
            <TextInput
              label="调度名称"
              required
              placeholder="输入调度任务名称"
              {...scheduleForm.getInputProps('name')}
            />

            <Select
              label="备份类型"
              required
              data={[
                { value: 'full', label: '全量备份' },
                { value: 'incremental', label: '增量备份' },
              ]}
              {...scheduleForm.getInputProps('backup_type')}
            />

            <TextInput
              label="Cron表达式"
              required
              placeholder="0 2 * * * (每天凌晨2点)"
              {...scheduleForm.getInputProps('schedule')}
            />

            <NumberInput
              label="保留天数"
              required
              min={1}
              max={365}
              {...scheduleForm.getInputProps('retention_days')}
            />

            <Checkbox
              label="启用调度"
              {...scheduleForm.getInputProps('enabled', { type: 'checkbox' })}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeScheduleModal}>
                取消
              </Button>
              <Button type="submit" loading={scheduleBackupMutation.isPending}>
                保存配置
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 备份详情模态框 */}
      <Modal opened={detailModalOpened} onClose={closeDetailModal} title="备份详情" size="lg">
        {selectedBackup && (
          <Stack>
            <Grid>
              <Grid.Col span={6}>
                <Text fw={500}>备份ID</Text>
                <Text size="sm" ff="monospace">
                  {selectedBackup.backup_id}
                </Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>备份类型</Text>
                {getBackupTypeBadge(selectedBackup.backup_type)}
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>文件大小</Text>
                <Text size="sm">{formatFileSize(selectedBackup.file_size)}</Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>状态</Text>
                {getStatusBadge(selectedBackup.status)}
              </Grid.Col>
              <Grid.Col span={12}>
                <Text fw={500}>文件路径</Text>
                <Text size="sm" ff="monospace">
                  {selectedBackup.file_path}
                </Text>
              </Grid.Col>
              <Grid.Col span={12}>
                <Text fw={500}>校验和</Text>
                <Text size="sm" ff="monospace">
                  {selectedBackup.checksum}
                </Text>
              </Grid.Col>
              {selectedBackup.description && (
                <Grid.Col span={12}>
                  <Text fw={500}>描述</Text>
                  <Text size="sm">{selectedBackup.description}</Text>
                </Grid.Col>
              )}
              <Grid.Col span={12}>
                <Text fw={500}>包含表</Text>
                <Group gap="xs">
                  {selectedBackup.tables.map(table => (
                    <Badge key={table} size="sm" variant="light">
                      {table}
                    </Badge>
                  ))}
                </Group>
              </Grid.Col>
            </Grid>
          </Stack>
        )}
      </Modal>

      {/* 加载和错误状态 */}
      {backupsLoading && (
        <Paper withBorder p="xl" ta="center">
          <Text>正在加载备份信息...</Text>
        </Paper>
      )}

      {backupsError && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red">
          {backupsError.message}
        </Alert>
      )}
    </Container>
  )
}
