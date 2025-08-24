/**
 * 权限管理页面 - 需求3：权限与角色管理
 * 实现角色分配、权限配置、RBAC管理功能
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
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
  Alert,
  Checkbox,
  Tabs,
  SimpleGrid,
  Textarea,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconEdit,
  IconEye,
  IconPlus,
  IconRefresh,
  IconShield,
  IconUsers,
  IconKey,
  IconSettings,
  IconAlertTriangle,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/api/client'

// 权限接口
interface Permission {
  id: number
  name: string
  code: string
  description?: string
  module: string
  action: string
  resource?: string
  is_active: boolean
  created_at: string
}

// 角色接口
interface Role {
  id: number
  name: string
  code: string
  description?: string
  is_active: boolean
  permissions: Permission[]
  user_count: number
  created_at: string
}

// 用户角色接口
interface UserRole {
  id: number
  user_id: number
  username: string
  email: string
  user_type: string
  roles: Role[]
  is_active: boolean
}

// 权限分配请求
interface PermissionAssignRequest {
  user_id: number
  role_ids: number[]
  permissions: number[]
}

export function PermissionManagementPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('roles')
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [selectedUser, setSelectedUser] = useState<UserRole | null>(null)
  const [page, setPage] = useState(1)

  const [roleModalOpened, { open: openRoleModal, close: closeRoleModal }] = useDisclosure(false)
  const [assignModalOpened, { open: openAssignModal, close: closeAssignModal }] =
    useDisclosure(false)

  // 角色表单
  const roleForm = useForm({
    initialValues: {
      name: '',
      code: '',
      description: '',
      permission_ids: [] as number[],
    },
  })

  // 权限分配表单
  const assignForm = useForm<PermissionAssignRequest>({
    initialValues: {
      user_id: 0,
      role_ids: [],
      permissions: [],
    },
  })

  // 获取角色列表
  const {
    data: rolesData,
    isLoading: rolesLoading,
    error: rolesError,
  } = useQuery({
    queryKey: ['roles', page],
    queryFn: async () => {
      const response = await apiClient.get(`/users/permissions/roles?page=${page}&limit=20`)
      return response.data as { items: Role[]; total: number; pages: number }
    },
  })

  // 获取权限列表
  const { data: permissionsData } = useQuery({
    queryKey: ['permissions'],
    queryFn: async () => {
      const response = await apiClient.get('/users/permissions/')
      return response.data as Permission[]
    },
  })

  // 获取用户角色列表
  const { data: userRolesData } = useQuery({
    queryKey: ['user-roles'],
    queryFn: async () => {
      const response = await apiClient.get('/users/permissions/user-roles')
      return response.data as UserRole[]
    },
  })

  // 创建/更新角色
  const roleMutation = useMutation({
    mutationFn: async (data: typeof roleForm.values) => {
      if (selectedRole) {
        return await apiClient.put(`/users/permissions/roles/${selectedRole.id}`, data)
      } else {
        return await apiClient.post('/users/permissions/roles', data)
      }
    },
    onSuccess: () => {
      notifications.show({
        title: '操作成功',
        message: selectedRole ? '角色更新成功' : '角色创建成功',
        color: 'green',
      })
      closeRoleModal()
      roleForm.reset()
      setSelectedRole(null)
      queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '操作失败',
        message: error.response?.data?.detail || '操作失败',
        color: 'red',
      })
    },
  })

  // 分配权限
  const assignMutation = useMutation({
    mutationFn: async (data: PermissionAssignRequest) => {
      return await apiClient.post('/users/permissions/assign', data)
    },
    onSuccess: () => {
      notifications.show({
        title: '分配成功',
        message: '权限分配成功',
        color: 'green',
      })
      closeAssignModal()
      assignForm.reset()
      setSelectedUser(null)
      queryClient.invalidateQueries({ queryKey: ['user-roles'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '分配失败',
        message: error.response?.data?.detail || '权限分配失败',
        color: 'red',
      })
    },
  })

  const handleCreateRole = () => {
    setSelectedRole(null)
    roleForm.reset()
    openRoleModal()
  }

  const handleEditRole = (role: Role) => {
    setSelectedRole(role)
    roleForm.setValues({
      name: role.name,
      code: role.code,
      description: role.description || '',
      permission_ids: role.permissions.map(p => p.id),
    })
    openRoleModal()
  }

  const handleAssignPermissions = (user: UserRole) => {
    setSelectedUser(user)
    assignForm.setValues({
      user_id: user.user_id,
      role_ids: user.roles.map(r => r.id),
      permissions: [],
    })
    openAssignModal()
  }

  const getPermissionsByModule = () => {
    if (!permissionsData) return {}

    return permissionsData.reduce(
      (acc, permission) => {
        if (!acc[permission.module]) {
          acc[permission.module] = []
        }
        acc[permission.module]!.push(permission)
        return acc
      },
      {} as Record<string, Permission[]>
    )
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>权限管理</Title>
          <Text c="dimmed" size="sm">
            管理系统角色和权限，确保访问控制安全
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreateRole}>
            创建角色
          </Button>
          <Button leftSection={<IconRefresh size={16} />} variant="light">
            刷新
          </Button>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'roles')}>
        <Tabs.List>
          <Tabs.Tab value="roles" leftSection={<IconShield size={16} />}>
            角色管理
          </Tabs.Tab>
          <Tabs.Tab value="permissions" leftSection={<IconKey size={16} />}>
            权限列表
          </Tabs.Tab>
          <Tabs.Tab value="assignments" leftSection={<IconUsers size={16} />}>
            用户权限
          </Tabs.Tab>
        </Tabs.List>

        {/* 角色管理标签页 */}
        <Tabs.Panel value="roles" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>角色信息</Table.Th>
                  <Table.Th>权限数量</Table.Th>
                  <Table.Th>用户数量</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>创建时间</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rolesData?.items.map(role => (
                  <Table.Tr key={role.id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text fw={500}>{role.name}</Text>
                        <Text size="sm" c="dimmed">
                          {role.code}
                        </Text>
                        {role.description && (
                          <Text size="xs" c="dimmed">
                            {role.description}
                          </Text>
                        )}
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Badge color="blue">{role.permissions.length} 个权限</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{role.user_count} 个用户</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={role.is_active ? 'green' : 'red'}>
                        {role.is_active ? '启用' : '禁用'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{new Date(role.created_at).toLocaleDateString('zh-CN')}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="编辑角色">
                          <ActionIcon variant="light" onClick={() => handleEditRole(role)}>
                            <IconEdit size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="查看权限">
                          <ActionIcon variant="light" color="blue">
                            <IconEye size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>

            {rolesData && rolesData.pages > 1 && (
              <Group justify="center" p="md">
                <Pagination value={page} onChange={setPage} total={rolesData.pages} />
              </Group>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 权限列表标签页 */}
        <Tabs.Panel value="permissions" pt="md">
          <Stack>
            {Object.entries(getPermissionsByModule()).map(([module, permissions]) => (
              <Card key={module} withBorder>
                <Title order={4} mb="md">
                  {module} 模块
                </Title>
                <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }}>
                  {permissions.map(permission => (
                    <Paper key={permission.id} withBorder p="sm">
                      <Stack gap="xs">
                        <Group justify="space-between">
                          <Text fw={500} size="sm">
                            {permission.name}
                          </Text>
                          <Badge size="xs" color={permission.is_active ? 'green' : 'red'}>
                            {permission.is_active ? '启用' : '禁用'}
                          </Badge>
                        </Group>
                        <Text size="xs" c="dimmed">
                          {permission.code}
                        </Text>
                        <Text size="xs">{permission.description}</Text>
                        <Group gap="xs">
                          <Badge size="xs" variant="light">
                            {permission.action}
                          </Badge>
                          {permission.resource && (
                            <Badge size="xs" variant="outline">
                              {permission.resource}
                            </Badge>
                          )}
                        </Group>
                      </Stack>
                    </Paper>
                  ))}
                </SimpleGrid>
              </Card>
            ))}
          </Stack>
        </Tabs.Panel>

        {/* 用户权限标签页 */}
        <Tabs.Panel value="assignments" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>用户信息</Table.Th>
                  <Table.Th>用户类型</Table.Th>
                  <Table.Th>分配角色</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {userRolesData?.map(userRole => (
                  <Table.Tr key={userRole.id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text fw={500}>{userRole.username}</Text>
                        <Text size="sm" c="dimmed">
                          {userRole.email}
                        </Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Badge color="blue">{userRole.user_type}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {userRole.roles.map(role => (
                          <Badge key={role.id} size="sm" variant="light">
                            {role.name}
                          </Badge>
                        ))}
                        {userRole.roles.length === 0 && (
                          <Text size="sm" c="dimmed">
                            未分配角色
                          </Text>
                        )}
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={userRole.is_active ? 'green' : 'red'}>
                        {userRole.is_active ? '启用' : '禁用'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Tooltip label="分配权限">
                        <ActionIcon
                          variant="light"
                          onClick={() => handleAssignPermissions(userRole)}
                        >
                          <IconSettings size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        </Tabs.Panel>
      </Tabs>

      {/* 角色创建/编辑模态框 */}
      <Modal
        opened={roleModalOpened}
        onClose={closeRoleModal}
        title={selectedRole ? '编辑角色' : '创建角色'}
        size="lg"
      >
        <form onSubmit={roleForm.onSubmit(values => roleMutation.mutate(values))}>
          <Stack>
            <TextInput
              label="角色名称"
              placeholder="输入角色名称"
              required
              {...roleForm.getInputProps('name')}
            />
            <TextInput
              label="角色代码"
              placeholder="输入角色代码"
              required
              {...roleForm.getInputProps('code')}
            />
            <Textarea
              label="角色描述"
              placeholder="输入角色描述"
              rows={3}
              {...roleForm.getInputProps('description')}
            />

            <div>
              <Text fw={500} mb="md">
                权限配置
              </Text>
              <Stack>
                {Object.entries(getPermissionsByModule()).map(([module, permissions]) => (
                  <Card key={module} withBorder>
                    <Text fw={500} mb="sm">
                      {module} 模块
                    </Text>
                    <Checkbox.Group {...roleForm.getInputProps('permission_ids')}>
                      <SimpleGrid cols={{ base: 1, md: 2 }}>
                        {permissions.map(permission => (
                          <Checkbox
                            key={permission.id}
                            value={permission.id.toString()}
                            label={
                              <div>
                                <Text size="sm">{permission.name}</Text>
                                <Text size="xs" c="dimmed">
                                  {permission.description}
                                </Text>
                              </div>
                            }
                          />
                        ))}
                      </SimpleGrid>
                    </Checkbox.Group>
                  </Card>
                ))}
              </Stack>
            </div>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeRoleModal}>
                取消
              </Button>
              <Button type="submit" loading={roleMutation.isPending}>
                {selectedRole ? '更新' : '创建'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 权限分配模态框 */}
      <Modal opened={assignModalOpened} onClose={closeAssignModal} title="分配权限" size="lg">
        {selectedUser && (
          <form onSubmit={assignForm.onSubmit(values => assignMutation.mutate(values))}>
            <Stack>
              <Paper withBorder p="md" bg="gray.0">
                <Text fw={500}>用户信息</Text>
                <Text size="sm">
                  {selectedUser.username} ({selectedUser.email})
                </Text>
              </Paper>

              <div>
                <Text fw={500} mb="md">
                  角色分配
                </Text>
                <Checkbox.Group {...assignForm.getInputProps('role_ids')}>
                  <Stack>
                    {rolesData?.items.map(role => (
                      <Checkbox
                        key={role.id}
                        value={role.id.toString()}
                        label={
                          <div>
                            <Text size="sm">{role.name}</Text>
                            <Text size="xs" c="dimmed">
                              {role.description}
                            </Text>
                          </div>
                        }
                      />
                    ))}
                  </Stack>
                </Checkbox.Group>
              </div>

              <Group justify="flex-end">
                <Button variant="light" onClick={closeAssignModal}>
                  取消
                </Button>
                <Button type="submit" loading={assignMutation.isPending}>
                  分配权限
                </Button>
              </Group>
            </Stack>
          </form>
        )}
      </Modal>

      {/* 加载和错误状态 */}
      {rolesLoading && (
        <Paper withBorder p="xl" ta="center">
          <Text>正在加载角色信息...</Text>
        </Paper>
      )}

      {rolesError && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red">
          {rolesError.message}
        </Alert>
      )}
    </Container>
  )
}
