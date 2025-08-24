/**
 * 多因素认证管理页面 - 需求4：多因素认证
 * 实现MFA配置、二次验证管理、TOTP设置功能
 */

import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
  Alert,
  Grid,
  Tabs,
  SimpleGrid,
  Switch,
  PinInput,
  Progress,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconShield,
  IconKey,
  IconPhone,
  IconMail,
  IconQrcode,
  IconRefresh,
  IconSettings,
  IconCheck,
  IconX,
  IconCopy,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/api/client'

// TOTP设置接口
interface TOTPSetup {
  secret_key: string
  qr_code_url: string
  backup_codes: string[]
  app_name: string
  account_name: string
}

// MFA统计接口
interface MFAStatistics {
  total_users: number
  mfa_enabled_users: number
  mfa_adoption_rate: number
  method_distribution: Record<string, number>
  recent_verifications: number
  failed_verifications: number
  success_rate: number
}

// 用户MFA状态接口
interface UserMFAStatus {
  user_id: number
  username: string
  email: string
  user_type: string
  mfa_enabled: boolean
  configured_methods: string[]
  last_verification: string
  verification_count: number
  is_locked: boolean
}

export function MFAManagementPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [selectedUser, setSelectedUser] = useState<UserMFAStatus | null>(null)
  const [totpSetup, setTotpSetup] = useState<TOTPSetup | null>(null)

  const [configModalOpened, { open: openConfigModal, close: closeConfigModal }] =
    useDisclosure(false)
  const [totpModalOpened, { open: openTotpModal, close: closeTotpModal }] = useDisclosure(false)
  const [verifyModalOpened, { open: openVerifyModal, close: closeVerifyModal }] =
    useDisclosure(false)

  // MFA配置表单
  const configForm = useForm({
    initialValues: {
      user_id: 0,
      mfa_enabled: false,
      primary_method: 'sms',
      backup_methods: [] as string[],
      require_for_admin: true,
    },
  })

  // TOTP验证表单
  const verifyForm = useForm({
    initialValues: {
      verification_code: '',
    },
  })

  // 获取MFA统计
  const { data: statsData } = useQuery({
    queryKey: ['mfa-statistics'],
    queryFn: async () => {
      const response = await apiClient.get('/users/mfa/statistics')
      return response.data as MFAStatistics
    },
  })

  // 获取用户MFA状态列表
  const { data: userStatusData, isLoading: usersLoading } = useQuery({
    queryKey: ['user-mfa-status'],
    queryFn: async () => {
      const response = await apiClient.get('/users/mfa/user-status')
      return response.data as UserMFAStatus[]
    },
  })

  // 配置用户MFA
  const configMutation = useMutation({
    mutationFn: async (data: typeof configForm.values) => {
      return await apiClient.post('/users/mfa/config', data)
    },
    onSuccess: () => {
      notifications.show({
        title: '配置成功',
        message: 'MFA配置已更新',
        color: 'green',
      })
      closeConfigModal()
      configForm.reset()
      setSelectedUser(null)
      queryClient.invalidateQueries({ queryKey: ['user-mfa-status'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '配置失败',
        message: error.response?.data?.detail || 'MFA配置失败',
        color: 'red',
      })
    },
  })

  // 设置TOTP
  const setupTotpMutation = useMutation({
    mutationFn: async (userId: number) => {
      const response = await apiClient.post('/users/mfa/totp/setup', { user_id: userId })
      return response.data as TOTPSetup
    },
    onSuccess: data => {
      setTotpSetup(data)
      openTotpModal()
    },
    onError: (error: any) => {
      notifications.show({
        title: 'TOTP设置失败',
        message: error.response?.data?.detail || 'TOTP设置失败',
        color: 'red',
      })
    },
  })

  // 验证TOTP
  const verifyTotpMutation = useMutation({
    mutationFn: async (data: { user_id: number; verification_code: string }) => {
      return await apiClient.post('/users/mfa/totp/verify', data)
    },
    onSuccess: () => {
      notifications.show({
        title: '验证成功',
        message: 'TOTP验证成功，已启用',
        color: 'green',
      })
      closeVerifyModal()
      closeTotpModal()
      verifyForm.reset()
      setTotpSetup(null)
      queryClient.invalidateQueries({ queryKey: ['user-mfa-status'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '验证失败',
        message: error.response?.data?.detail || 'TOTP验证失败',
        color: 'red',
      })
    },
  })

  // 重置用户MFA
  const resetMfaMutation = useMutation({
    mutationFn: async (userId: number) => {
      return await apiClient.post(`/users/mfa/reset/${userId}`)
    },
    onSuccess: () => {
      notifications.show({
        title: '重置成功',
        message: '用户MFA已重置',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['user-mfa-status'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '重置失败',
        message: error.response?.data?.detail || 'MFA重置失败',
        color: 'red',
      })
    },
  })

  const handleConfigureMFA = (user: UserMFAStatus) => {
    setSelectedUser(user)
    configForm.setValues({
      user_id: user.user_id,
      mfa_enabled: user.mfa_enabled,
      primary_method: user.configured_methods[0] || 'sms',
      backup_methods: user.configured_methods.slice(1),
      require_for_admin: user.user_type === 'admin',
    })
    openConfigModal()
  }

  const handleSetupTOTP = (user: UserMFAStatus) => {
    setSelectedUser(user)
    setupTotpMutation.mutate(user.user_id)
  }

  const handleCopyBackupCode = (code: string) => {
    navigator.clipboard.writeText(code)
    notifications.show({
      title: '已复制',
      message: '备用代码已复制到剪贴板',
      color: 'green',
    })
  }

  const getMethodBadge = (method: string) => {
    const methodMap: Record<string, { color: string; icon: any; label: string }> = {
      sms: { color: 'blue', icon: IconPhone, label: '短信' },
      email: { color: 'green', icon: IconMail, label: '邮箱' },
      totp: { color: 'purple', icon: IconQrcode, label: 'TOTP' },
    }
    const methodInfo = methodMap[method] || { color: 'gray', icon: IconKey, label: method }
    const IconComponent = methodInfo.icon
    return (
      <Badge color={methodInfo.color} leftSection={<IconComponent size={12} />}>
        {methodInfo.label}
      </Badge>
    )
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>多因素认证管理</Title>
          <Text c="dimmed" size="sm">
            管理用户多因素认证设置，提升系统安全性
          </Text>
        </div>
        <Group>
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
                  总用户数
                </Text>
                <Text fw={700} size="xl">
                  {statsData.total_users}
                </Text>
              </div>
              <IconShield size={32} color="blue" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  MFA启用率
                </Text>
                <Text fw={700} size="xl">
                  {(statsData.mfa_adoption_rate * 100).toFixed(1)}%
                </Text>
              </div>
              <Progress
                value={statsData.mfa_adoption_rate * 100}
                size="sm"
                color="green"
                style={{ width: 60 }}
              />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  验证成功率
                </Text>
                <Text fw={700} size="xl">
                  {(statsData.success_rate * 100).toFixed(1)}%
                </Text>
              </div>
              <IconCheck size={32} color="green" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  失败验证
                </Text>
                <Text fw={700} size="xl" c="red">
                  {statsData.failed_verifications}
                </Text>
              </div>
              <IconX size={32} color="red" />
            </Group>
          </Card>
        </SimpleGrid>
      )}

      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconShield size={16} />}>
            概览统计
          </Tabs.Tab>
          <Tabs.Tab value="users" leftSection={<IconSettings size={16} />}>
            用户管理
          </Tabs.Tab>
          <Tabs.Tab value="methods" leftSection={<IconKey size={16} />}>
            认证方式
          </Tabs.Tab>
        </Tabs.List>

        {/* 概览统计标签页 */}
        <Tabs.Panel value="overview" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder>
                <Title order={4} mb="md">
                  认证方式分布
                </Title>
                <Stack>
                  {Object.entries(statsData?.method_distribution || {}).map(([method, count]) => (
                    <Group key={method} justify="space-between">
                      {getMethodBadge(method)}
                      <Text fw={500}>{count} 用户</Text>
                    </Group>
                  ))}
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder>
                <Title order={4} mb="md">
                  安全建议
                </Title>
                <Stack>
                  <Alert color="blue">
                    <Text size="sm">建议所有管理员启用MFA</Text>
                  </Alert>
                  <Alert color="green">
                    <Text size="sm">TOTP是最安全的认证方式</Text>
                  </Alert>
                  <Alert color="orange">
                    <Text size="sm">定期检查用户MFA状态</Text>
                  </Alert>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 用户管理标签页 */}
        <Tabs.Panel value="users" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>用户信息</Table.Th>
                  <Table.Th>用户类型</Table.Th>
                  <Table.Th>MFA状态</Table.Th>
                  <Table.Th>认证方式</Table.Th>
                  <Table.Th>最后验证</Table.Th>
                  <Table.Th>验证次数</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {userStatusData?.map(user => (
                  <Table.Tr key={user.user_id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text fw={500}>{user.username}</Text>
                        <Text size="sm" c="dimmed">
                          {user.email}
                        </Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Badge color="blue">{user.user_type}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Badge color={user.mfa_enabled ? 'green' : 'red'}>
                          {user.mfa_enabled ? '已启用' : '未启用'}
                        </Badge>
                        {user.is_locked && (
                          <Badge color="red" size="sm">
                            锁定
                          </Badge>
                        )}
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {user.configured_methods.map(method => getMethodBadge(method))}
                        {user.configured_methods.length === 0 && (
                          <Text size="sm" c="dimmed">
                            未配置
                          </Text>
                        )}
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {user.last_verification
                          ? new Date(user.last_verification).toLocaleString('zh-CN')
                          : '从未验证'}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{user.verification_count}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="配置MFA">
                          <ActionIcon variant="light" onClick={() => handleConfigureMFA(user)}>
                            <IconSettings size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="设置TOTP">
                          <ActionIcon
                            variant="light"
                            color="purple"
                            onClick={() => handleSetupTOTP(user)}
                          >
                            <IconQrcode size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="重置MFA">
                          <ActionIcon
                            variant="light"
                            color="red"
                            onClick={() => resetMfaMutation.mutate(user.user_id)}
                          >
                            <IconRefresh size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        </Tabs.Panel>

        {/* 认证方式标签页 */}
        <Tabs.Panel value="methods" pt="md">
          <SimpleGrid cols={{ base: 1, md: 3 }}>
            <Card withBorder>
              <Stack ta="center">
                <IconPhone size={48} color="blue" />
                <Title order={4}>短信验证</Title>
                <Text size="sm" c="dimmed">
                  通过手机短信接收验证码
                </Text>
                <Badge color="blue">简单易用</Badge>
              </Stack>
            </Card>

            <Card withBorder>
              <Stack ta="center">
                <IconMail size={48} color="green" />
                <Title order={4}>邮箱验证</Title>
                <Text size="sm" c="dimmed">
                  通过邮箱接收验证码
                </Text>
                <Badge color="green">广泛支持</Badge>
              </Stack>
            </Card>

            <Card withBorder>
              <Stack ta="center">
                <IconQrcode size={48} color="purple" />
                <Title order={4}>TOTP认证</Title>
                <Text size="sm" c="dimmed">
                  使用认证器应用生成动态密码
                </Text>
                <Badge color="purple">最高安全</Badge>
              </Stack>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>

      {/* MFA配置模态框 */}
      <Modal opened={configModalOpened} onClose={closeConfigModal} title="配置MFA" size="lg">
        {selectedUser && (
          <form onSubmit={configForm.onSubmit(values => configMutation.mutate(values))}>
            <Stack>
              <Paper withBorder p="md" bg="gray.0">
                <Text fw={500}>用户信息</Text>
                <Text size="sm">
                  {selectedUser.username} ({selectedUser.email})
                </Text>
              </Paper>

              <Switch
                label="启用多因素认证"
                {...configForm.getInputProps('mfa_enabled', { type: 'checkbox' })}
              />

              <Select
                label="主要认证方式"
                data={[
                  { value: 'sms', label: '短信验证' },
                  { value: 'email', label: '邮箱验证' },
                  { value: 'totp', label: 'TOTP认证' },
                ]}
                {...configForm.getInputProps('primary_method')}
              />

              <Switch
                label="管理员操作需要MFA"
                {...configForm.getInputProps('require_for_admin', { type: 'checkbox' })}
              />

              <Group justify="flex-end">
                <Button variant="light" onClick={closeConfigModal}>
                  取消
                </Button>
                <Button type="submit" loading={configMutation.isPending}>
                  保存配置
                </Button>
              </Group>
            </Stack>
          </form>
        )}
      </Modal>

      {/* TOTP设置模态框 */}
      <Modal opened={totpModalOpened} onClose={closeTotpModal} title="设置TOTP认证" size="lg">
        {totpSetup && selectedUser && (
          <Stack>
            <Alert icon={<IconQrcode size={16} />} title="设置步骤" color="blue">
              <Text size="sm">
                1. 在手机上安装认证器应用（如Google Authenticator、Microsoft Authenticator）
                <br />
                2. 扫描下方二维码或手动输入密钥
                <br />
                3. 输入认证器显示的6位数字验证码
              </Text>
            </Alert>

            <Paper withBorder p="md" ta="center">
              <Title order={4} mb="md">
                扫描二维码
              </Title>
              <div
                style={{
                  width: 200,
                  height: 200,
                  backgroundColor: '#f0f0f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Text size="sm">二维码占位符</Text>
              </div>
            </Paper>

            <Paper withBorder p="md">
              <Group justify="space-between">
                <div>
                  <Text fw={500}>手动输入密钥</Text>
                  <Text size="sm" ff="monospace">
                    {totpSetup.secret_key}
                  </Text>
                </div>
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconCopy size={14} />}
                  onClick={() => {
                    navigator.clipboard.writeText(totpSetup.secret_key)
                    notifications.show({
                      title: '已复制',
                      message: '密钥已复制到剪贴板',
                      color: 'green',
                    })
                  }}
                >
                  复制
                </Button>
              </Group>
            </Paper>

            <div>
              <Text fw={500} mb="md">
                备用恢复代码
              </Text>
              <Alert color="orange" mb="md">
                <Text size="sm">请妥善保存这些备用代码，当您无法使用认证器时可以使用它们登录</Text>
              </Alert>
              <SimpleGrid cols={2}>
                {totpSetup.backup_codes.map((code, index) => (
                  <Paper key={index} withBorder p="sm">
                    <Group justify="space-between">
                      <Text size="sm" ff="monospace">
                        {code}
                      </Text>
                      <ActionIcon
                        size="sm"
                        variant="light"
                        onClick={() => handleCopyBackupCode(code)}
                      >
                        <IconCopy size={12} />
                      </ActionIcon>
                    </Group>
                  </Paper>
                ))}
              </SimpleGrid>
            </div>

            <Button onClick={openVerifyModal}>验证并启用TOTP</Button>
          </Stack>
        )}
      </Modal>

      {/* TOTP验证模态框 */}
      <Modal opened={verifyModalOpened} onClose={closeVerifyModal} title="验证TOTP" size="md">
        <form
          onSubmit={verifyForm.onSubmit(values =>
            verifyTotpMutation.mutate({
              user_id: selectedUser?.user_id || 0,
              verification_code: values.verification_code,
            })
          )}
        >
          <Stack>
            <Text ta="center">请输入认证器应用显示的6位验证码</Text>

            <Group justify="center">
              <PinInput
                length={6}
                type="number"
                {...verifyForm.getInputProps('verification_code')}
              />
            </Group>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeVerifyModal}>
                取消
              </Button>
              <Button type="submit" loading={verifyTotpMutation.isPending}>
                验证
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 加载状态 */}
      {usersLoading && (
        <Paper withBorder p="xl" ta="center">
          <Text>正在加载用户MFA状态...</Text>
        </Paper>
      )}
    </Container>
  )
}
