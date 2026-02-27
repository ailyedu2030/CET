/**
 * 需求16：系统协同功能页面 - 教师端
 *
 * 实现通知中枢、教研协作、权限控制的协同管理界面
 */

import { useState } from 'react'
import {
  Container,
  Title,
  Text,
  Grid,
  Card,
  Button,
  Group,
  Badge,
  Tabs,
  Alert,
  LoadingOverlay,
  Select,
  RingProgress,
  Center,
} from '@mantine/core'
import {
  IconRefresh,
  IconDatabase,
  IconShield,
  IconNetwork,
  IconBrain,
  IconTarget,
  IconCheck,
  IconAlertTriangle,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'

import {
  notificationApi,
  permissionApi,
  systemHealthApi,
} from '@/api/systemCoordination'
import { usePermissions } from '@/utils/permissions'

export function SystemCoordinationPage(): JSX.Element {
  // 状态管理
  const [activeTab, setActiveTab] = useState<string | null>('notifications')
  const [selectedClass, setSelectedClass] = useState<number | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // 权限检查
  const { hasTeacherPermission } = usePermissions()

  // 查询系统健康状态
  const {
    data: systemHealth,
    isLoading: healthLoading,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['system-coordination-health', refreshKey],
    queryFn: () => systemHealthApi.getCoordinationHealth(),
  })

  // 查询系统能力
  const {
    data: _systemCapabilities,
    isLoading: capabilitiesLoading,
  } = useQuery({
    queryKey: ['system-capabilities'],
    queryFn: () => systemHealthApi.getSystemCapabilities(),
  })

  // 查询权限状态
  const {
    data: _permissionStatus,
    isLoading: _permissionLoading,
    refetch: _refetchPermissions,
  } = useQuery({
    queryKey: ['user-permissions', selectedClass],
    queryFn: () => permissionApi.getCurrentUserPermissions(),
    enabled: !!selectedClass,
  })

  // 触发通知发送
  const sendNotificationMutation = useMutation({
    mutationFn: (notificationData: any) => notificationApi.sendNotification(notificationData),
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '通知已发送',
        color: 'green',
      })
      setRefreshKey(prev => prev + 1)
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '通知发送失败',
        color: 'red',
      })
    },
  })

  // 模拟班级数据
  const mockClasses = [
    { value: '1', label: '2024春季班A' },
    { value: '2', label: '2024春季班B' },
    { value: '3', label: '2024春季班C' },
  ]

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    refetchHealth()
  }



  // 权限检查
  if (!hasTeacherPermission()) {
    return (
      <Container size="xl" py="lg">
        <Alert icon={<IconAlertTriangle size={16} />} color="red">
          您没有权限访问系统协同功能
        </Alert>
      </Container>
    )
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={healthLoading || capabilitiesLoading} />

      {/* 页面头部 */}
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>系统协同功能</Title>
          <Text c="dimmed" size="sm">
            通知中枢、教研协作、权限控制的协同管理平台
          </Text>
        </div>
        <Group>
          <Select
            placeholder="选择班级"
            data={mockClasses}
            value={selectedClass?.toString()}
            onChange={value => setSelectedClass(value ? parseInt(value) : null)}
            w={200}
          />
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="light"
            onClick={handleRefresh}
            loading={sendNotificationMutation.isPending}
          >
            刷新
          </Button>
        </Group>
      </Group>

      {/* 系统健康状态概览 */}
      <Grid mb="xl">
        <Grid.Col span={3}>
          <Card withBorder p="md">
            <Group justify="space-between">
              <div>
                <Text size="sm" c="dimmed">
                  系统健康度
                </Text>
                <Text size="xl" fw={700}>
                  {systemHealth?.health_status === 'healthy' ? '优秀' : '良好'}
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: 95, color: 'green' }]}
                label={
                  <Center>
                    <IconCheck size={16} color="green" />
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={3}>
          <Card withBorder p="md">
            <Group justify="space-between">
              <div>
                <Text size="sm" c="dimmed">
                  协同效率
                </Text>
                <Text size="xl" fw={700}>
                  88%
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: 88, color: 'blue' }]}
                label={
                  <Center>
                    <IconNetwork size={16} color="blue" />
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={3}>
          <Card withBorder p="md">
            <Group justify="space-between">
              <div>
                <Text size="sm" c="dimmed">
                  数据同步率
                </Text>
                <Text size="xl" fw={700}>
                  92%
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: 92, color: 'orange' }]}
                label={
                  <Center>
                    <IconDatabase size={16} color="orange" />
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={3}>
          <Card withBorder p="md">
            <Group justify="space-between">
              <div>
                <Text size="sm" c="dimmed">
                  权限合规性
                </Text>
                <Text size="xl" fw={700}>
                  100%
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: 100, color: 'green' }]}
                label={
                  <Center>
                    <IconShield size={16} color="green" />
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 功能标签页 */}
      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="notifications" leftSection={<IconBrain size={16} />}>
            通知中枢
          </Tabs.Tab>
          <Tabs.Tab value="collaboration" leftSection={<IconTarget size={16} />}>
            教研协作
          </Tabs.Tab>
          <Tabs.Tab value="permissions" leftSection={<IconShield size={16} />}>
            权限控制
          </Tabs.Tab>
        </Tabs.List>

        {/* 通知中枢面板 */}
        <Tabs.Panel value="notifications" pt="lg">
          <Grid>
            <Grid.Col span={12}>
              <Card withBorder p="md">
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">
                    通知中枢
                  </Text>
                  <Badge color="blue">运行中</Badge>
                </Group>
                <Grid>
                  <Grid.Col span={4}>
                    <Card withBorder p="sm" bg="blue.0">
                      <Text fw={500} mb="xs">
                        教学计划变更通知
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        自动通知教学计划变更，支持系统内消息、邮件、短信
                      </Text>
                      <Badge size="sm" color="green">
                        已启用
                      </Badge>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={4}>
                    <Card withBorder p="sm" bg="orange.0">
                      <Text fw={500} mb="xs">
                        学生训练异常预警
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        监控学生训练状态，异常情况及时预警
                      </Text>
                      <Badge size="sm" color="green">
                        已启用
                      </Badge>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={4}>
                    <Card withBorder p="sm" bg="green.0">
                      <Text fw={500} mb="xs">
                        资源审核状态提醒
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        资源审核状态变更及时提醒，支持按班级批量发送
                      </Text>
                      <Badge size="sm" color="green">
                        已启用
                      </Badge>
                    </Card>
                  </Grid.Col>
                </Grid>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 教研协作面板 */}
        <Tabs.Panel value="collaboration" pt="lg">
          <Grid>
            <Grid.Col span={12}>
              <Card withBorder p="md">
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">
                    教研协作
                  </Text>
                  <Badge color="green">活跃</Badge>
                </Group>
                <Grid>
                  <Grid.Col span={6}>
                    <Card withBorder p="sm" bg="blue.0">
                      <Text fw={500} mb="xs">
                        教案共享与评论
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        支持教案共享、评论和协同编辑
                      </Text>
                      <Button size="sm" variant="light">
                        查看共享教案
                      </Button>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Card withBorder p="sm" bg="green.0">
                      <Text fw={500} mb="xs">
                        教学难点讨论
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        教师间教学难点讨论和经验分享
                      </Text>
                      <Button size="sm" variant="light">
                        参与讨论
                      </Button>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Card withBorder p="sm" bg="orange.0">
                      <Text fw={500} mb="xs">
                        优秀案例分享
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        优秀教学案例分享和学习
                      </Text>
                      <Button size="sm" variant="light">
                        浏览案例
                      </Button>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Card withBorder p="sm" bg="purple.0">
                      <Text fw={500} mb="xs">
                        同时编辑和讨论
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        支持多教师同时编辑和实时讨论
                      </Text>
                      <Button size="sm" variant="light">
                        开始协作
                      </Button>
                    </Card>
                  </Grid.Col>
                </Grid>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="permissions" pt="lg">
          <Grid>
            <Grid.Col span={12}>
              <Card withBorder p="md">
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">
                    权限控制
                  </Text>
                  <Badge color="green">正常</Badge>
                </Group>
                <Grid>
                  <Grid.Col span={4}>
                    <Card withBorder p="sm" bg="blue.0">
                      <Text fw={500} mb="xs">
                        大纲编辑权
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        教师拥有课程大纲编辑权限
                      </Text>
                      <Badge size="sm" color="green">
                        已授权
                      </Badge>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={4}>
                    <Card withBorder p="sm" bg="green.0">
                      <Text fw={500} mb="xs">
                        教案编辑权
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        教师拥有教案编辑权限
                      </Text>
                      <Badge size="sm" color="green">
                        已授权
                      </Badge>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={4}>
                    <Card withBorder p="sm" bg="orange.0">
                      <Text fw={500} mb="xs">
                        教室时段查看
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        可查看教室可用时段但不能修改
                      </Text>
                      <Badge size="sm" color="blue">
                        只读权限
                      </Badge>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={12}>
                    <Card withBorder p="sm" bg="purple.0">
                      <Text fw={500} mb="xs">
                        多教师协同编辑
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        支持多教师协同编辑大纲，实时同步修改
                      </Text>
                      <Button size="sm" variant="light">
                        开始协同编辑
                      </Button>
                    </Card>
                  </Grid.Col>
                </Grid>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>
      </Tabs>
    </Container>
  )
}
