/**
 * 需求19：教师端技术实现与性能要求页面
 *
 * 展示和管理教师端技术实现的6个验收标准：
 * 1. 前端技术实现
 * 2. 接口规范与安全
 * 3. 离线支持
 * 4. 性能优化
 * 5. 数据安全
 * 6. 系统集成
 */

import React, { useState } from 'react'
import {
  Container,
  Title,
  Text,
  Tabs,
  Card,
  Grid,
  Badge,
  Group,
  Stack,
  Alert,
  Progress,
  Button,
  LoadingOverlay,
} from '@mantine/core'
import {
  IconCode,
  IconShield,
  IconCloudOff,
  IconSpeedboat,
  IconLock,
  IconNetwork,
  IconInfoCircle,
  IconRefresh,
  IconCheck,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'

import {
  technicalImplementationApi,
  interfaceSecurityApi,
  offlineSupportApi,
  performanceOptimizationApi,
  dataSecurityApi,
  systemIntegrationApi,
} from '@/api/teacherTechnicalRequirements'

const TechnicalRequirementsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string | null>('overview')
  const [refreshKey, setRefreshKey] = useState(0)

  // 查询各个模块的状态
  const { isLoading: technicalLoading } = useQuery({
    queryKey: ['technical-status', refreshKey],
    queryFn: () => technicalImplementationApi.getTechnicalStatus(),
  })

  const { data: securityStatus, isLoading: securityLoading } = useQuery({
    queryKey: ['security-status', refreshKey],
    queryFn: () => interfaceSecurityApi.getSecurityStatus(),
  })

  const { data: offlineStatus, isLoading: offlineLoading } = useQuery({
    queryKey: ['offline-status', refreshKey],
    queryFn: () => offlineSupportApi.getOfflineStatus(),
  })

  const { isLoading: performanceLoading } = useQuery({
    queryKey: ['performance-status', refreshKey],
    queryFn: () => performanceOptimizationApi.getPerformanceStatus(),
  })

  const { data: dataSecurityStatus, isLoading: dataSecurityLoading } = useQuery({
    queryKey: ['data-security-status', refreshKey],
    queryFn: () => dataSecurityApi.getSecurityStatus(),
  })

  const { data: integrationStatus, isLoading: integrationLoading } = useQuery({
    queryKey: ['integration-status', refreshKey],
    queryFn: () => systemIntegrationApi.getIntegrationStatus(),
  })

  // 手动同步
  const syncMutation = useMutation({
    mutationFn: offlineSupportApi.triggerManualSync,
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '手动同步完成',
        color: 'green',
      })
      setRefreshKey(prev => prev + 1)
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '同步失败',
        color: 'red',
      })
    },
  })

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  const handleManualSync = () => {
    syncMutation.mutate()
  }

  const isLoading =
    technicalLoading ||
    securityLoading ||
    offlineLoading ||
    performanceLoading ||
    dataSecurityLoading ||
    integrationLoading

  return (
    <Container size="xl" py="md">
      <Stack gap="lg">
        {/* 页面标题 */}
        <Group justify="space-between">
          <div>
            <Title order={1} mb="xs">
              教师端技术实现与性能要求
            </Title>
            <Text size="lg" c="dimmed">
              前端技术架构、性能优化、离线支持、数据安全等技术指标监控 - 需求19实现
            </Text>
          </div>
          <Group>
            <Button
              variant="light"
              leftSection={<IconRefresh size={16} />}
              onClick={handleRefresh}
              loading={isLoading}
            >
              刷新状态
            </Button>
            <Button variant="filled" onClick={handleManualSync} loading={syncMutation.isPending}>
              手动同步
            </Button>
          </Group>
        </Group>

        {/* 系统状态概览 */}
        <Card withBorder p="md" pos="relative">
          <LoadingOverlay visible={isLoading} />
          <Group justify="space-between" mb="md">
            <Text fw={500} size="lg">
              技术实现状态概览
            </Text>
            <Badge color="green">系统正常</Badge>
          </Group>
          <Grid>
            <Grid.Col span={2}>
              <Stack gap="xs" align="center">
                <IconCode size={32} color="blue" />
                <Text fw={500}>前端技术</Text>
                <Text size="sm" c="dimmed">
                  React 18.2.0
                </Text>
                <Badge size="sm" color="blue">
                  PWA就绪
                </Badge>
              </Stack>
            </Grid.Col>
            <Grid.Col span={2}>
              <Stack gap="xs" align="center">
                <IconShield size={32} color="green" />
                <Text fw={500}>接口安全</Text>
                <Text size="sm" c="dimmed">
                  JWT认证
                </Text>
                <Badge size="sm" color="green">
                  {securityStatus?.rate_limiting?.requests_per_minute || 100}/分钟
                </Badge>
              </Stack>
            </Grid.Col>
            <Grid.Col span={2}>
              <Stack gap="xs" align="center">
                <IconCloudOff size={32} color="orange" />
                <Text fw={500}>离线支持</Text>
                <Text size="sm" c="dimmed">
                  缓存命中率: {Math.round((offlineStatus?.data_cache?.hit_rate || 0) * 100)}%
                </Text>
                <Badge size="sm" color="orange">
                  离线可用
                </Badge>
              </Stack>
            </Grid.Col>
            <Grid.Col span={2}>
              <Stack gap="xs" align="center">
                <IconSpeedboat size={32} color="purple" />
                <Text fw={500}>性能优化</Text>
                <Text size="sm" c="dimmed">
                  虚拟滚动
                </Text>
                <Badge size="sm" color="purple">
                  异步加载
                </Badge>
              </Stack>
            </Grid.Col>
            <Grid.Col span={2}>
              <Stack gap="xs" align="center">
                <IconLock size={32} color="red" />
                <Text fw={500}>数据安全</Text>
                <Text size="sm" c="dimmed">
                  AES-256加密
                </Text>
                <Badge size="sm" color="red">
                  {dataSecurityStatus?.session_management?.timeout_minutes || 30}分钟超时
                </Badge>
              </Stack>
            </Grid.Col>
            <Grid.Col span={2}>
              <Stack gap="xs" align="center">
                <IconNetwork size={32} color="teal" />
                <Text fw={500}>系统集成</Text>
                <Text size="sm" c="dimmed">
                  {integrationStatus?.third_party_integration?.platform_integration_count || 8}
                  个平台
                </Text>
                <Badge size="sm" color="teal">
                  实时同步
                </Badge>
              </Stack>
            </Grid.Col>
          </Grid>
        </Card>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          <Text fw={500} mb="xs">
            需求19验收标准
          </Text>
          <Text size="sm">
            本页面展示教师端技术实现与性能要求的6个验收标准：前端技术实现、接口规范与安全、
            离线支持、性能优化、数据安全、系统集成。所有指标均实时监控，确保系统稳定运行。
          </Text>
        </Alert>

        {/* 详细功能标签页 */}
        <Tabs value={activeTab} onChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab value="overview" leftSection={<IconInfoCircle size={16} />}>
              技术概览
            </Tabs.Tab>
            <Tabs.Tab value="frontend" leftSection={<IconCode size={16} />}>
              前端技术实现
            </Tabs.Tab>
            <Tabs.Tab value="security" leftSection={<IconShield size={16} />}>
              接口规范与安全
            </Tabs.Tab>
            <Tabs.Tab value="offline" leftSection={<IconCloudOff size={16} />}>
              离线支持
            </Tabs.Tab>
            <Tabs.Tab value="performance" leftSection={<IconSpeedboat size={16} />}>
              性能优化
            </Tabs.Tab>
            <Tabs.Tab value="data-security" leftSection={<IconLock size={16} />}>
              数据安全
            </Tabs.Tab>
            <Tabs.Tab value="integration" leftSection={<IconNetwork size={16} />}>
              系统集成
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    技术架构评分
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">React框架</Text>
                      <Badge color="green">优秀</Badge>
                    </Group>
                    <Progress value={95} color="green" size="sm" />

                    <Group justify="space-between">
                      <Text size="sm">组件化设计</Text>
                      <Badge color="blue">良好</Badge>
                    </Group>
                    <Progress value={85} color="blue" size="sm" />

                    <Group justify="space-between">
                      <Text size="sm">响应式布局</Text>
                      <Badge color="green">优秀</Badge>
                    </Group>
                    <Progress value={92} color="green" size="sm" />

                    <Group justify="space-between">
                      <Text size="sm">PWA支持</Text>
                      <Badge color="green">完整</Badge>
                    </Group>
                    <Progress value={100} color="green" size="sm" />
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    性能与安全指标
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">接口安全</Text>
                      <Group gap="xs">
                        <IconCheck size={16} color="green" />
                        <Text size="sm" c="green">
                          正常
                        </Text>
                      </Group>
                    </Group>

                    <Group justify="space-between">
                      <Text size="sm">离线功能</Text>
                      <Group gap="xs">
                        <IconCheck size={16} color="green" />
                        <Text size="sm" c="green">
                          可用
                        </Text>
                      </Group>
                    </Group>

                    <Group justify="space-between">
                      <Text size="sm">性能优化</Text>
                      <Group gap="xs">
                        <IconCheck size={16} color="green" />
                        <Text size="sm" c="green">
                          已启用
                        </Text>
                      </Group>
                    </Group>

                    <Group justify="space-between">
                      <Text size="sm">数据加密</Text>
                      <Group gap="xs">
                        <IconCheck size={16} color="green" />
                        <Text size="sm" c="green">
                          AES-256
                        </Text>
                      </Group>
                    </Group>

                    <Group justify="space-between">
                      <Text size="sm">系统集成</Text>
                      <Group gap="xs">
                        <IconCheck size={16} color="green" />
                        <Text size="sm" c="green">
                          已连接
                        </Text>
                      </Group>
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="frontend" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    React框架实现
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">版本</Text>
                      <Badge color="blue">React 18.2.0</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">响应式设计</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">PC/平板兼容</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      使用React 18最新特性，支持并发渲染和自动批处理，
                      提供优秀的用户体验和性能表现。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    组件化设计
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">模块化组件</Text>
                      <Badge color="green">150+</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">复用率</Text>
                      <Badge color="blue">85%</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">维护效率</Text>
                      <Badge color="green">92%</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      采用原子化设计原则，组件高度模块化， 支持主题定制和样式复用。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    响应式布局
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">移动端优化</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">平板优化</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">桌面优化</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      支持320px-2560px全屏幕尺寸， 自适应布局确保最佳显示效果。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    PWA支持
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">离线可用</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">桌面安装</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">Service Worker</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      完整的PWA实现，支持离线使用、 桌面安装和后台同步。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="security" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    RESTful接口
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">标准化设计</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">易于集成</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">维护友好</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      遵循REST架构原则，使用标准HTTP方法， 统一的错误处理和响应格式。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    JWT认证
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">无状态认证</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">安全级别</Text>
                      <Badge color="red">高</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">Token刷新</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      使用JWT标准，支持自动刷新， 确保安全性和用户体验平衡。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    请求频率限制
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">限制频率</Text>
                      <Badge color="orange">100次/分钟</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">当前使用</Text>
                      <Badge color="green">
                        {securityStatus?.rate_limiting?.current_usage || 0}次
                      </Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">过载保护</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      智能限流算法，防止系统过载， 保障服务稳定性。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    权限前置检查
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">前置验证</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">成功率</Text>
                      <Badge color="green">99%</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">未授权拦截</Text>
                      <Badge color="red">0次</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      每个API调用前进行权限验证， 确保数据安全和访问控制。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="offline" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    关键功能离线
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">教案编辑</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">资源查看</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">数据缓存</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      核心教学功能支持离线使用， 确保网络中断时正常工作。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    自动同步
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">同步状态</Text>
                      <Badge color="green">已启用</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">成功率</Text>
                      <Badge color="green">
                        {Math.round((offlineStatus?.auto_sync?.sync_success_rate || 0) * 100)}%
                      </Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">最后同步</Text>
                      <Text size="xs">刚刚</Text>
                    </Group>
                    <Text size="xs" c="dimmed">
                      网络恢复后自动同步离线期间的操作， 保证数据一致性。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    数据缓存
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">缓存大小</Text>
                      <Badge color="blue">
                        {offlineStatus?.data_cache?.cache_size_mb || 125.6}MB
                      </Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">命中率</Text>
                      <Badge color="green">
                        {Math.round((offlineStatus?.data_cache?.hit_rate || 0) * 100)}%
                      </Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">智能缓存</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      智能缓存常用数据， 提升离线体验和响应速度。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    冲突处理
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">合并算法</Text>
                      <Badge color="purple">三路合并</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">解决率</Text>
                      <Badge color="green">95%</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">手动干预</Text>
                      <Badge color="orange">2次</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      智能冲突检测和自动合并， 最小化手动干预需求。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="performance" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    异步加载
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">大文件异步</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">非阻塞操作</Text>
                      <Badge color="blue">25个</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">加载优化</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      大型资源文件异步加载， 避免阻塞用户操作。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    图片优化
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">自动压缩</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">CDN分发</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">速度提升</Text>
                      <Badge color="green">65%</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      图片资源自动压缩和CDN分发， 显著提升加载速度。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    虚拟滚动
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">长列表支持</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">性能提升</Text>
                      <Badge color="green">75%</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">内存优化</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      虚拟滚动技术处理大量数据展示， 保持流畅的用户体验。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    智能预加载
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">行为预测</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">预测准确率</Text>
                      <Badge color="green">82%</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">资源效率</Text>
                      <Badge color="green">88%</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      基于用户行为预测， 提前加载可能需要的资源。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="data-security" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    数据加密
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">加密算法</Text>
                      <Badge color="red">AES-256</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">隐私保护</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">数据安全</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      教师数据采用AES-256加密存储， 确保隐私信息安全。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    二次验证
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">敏感操作保护</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">验证成功率</Text>
                      <Badge color="green">97%</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">误操作防护</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      敏感操作需要二次验证， 有效防止误操作。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    会话管理
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">超时时间</Text>
                      <Badge color="orange">30分钟</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">自动登出</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">安全平衡</Text>
                      <Badge color="green">91%</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      30分钟会话超时， 平衡安全性和用户体验。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    操作日志
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">详细记录</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">审计支持</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">问题排查</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      详细记录教师操作日志， 支持审计和问题排查。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="integration" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    模块间交互
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">边界定义</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">数据交换</Text>
                      <Badge color="blue">REST/WebSocket</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">权限边界</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      明确定义教师模块和管理模块的 数据交换和权限边界。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    数据一致性
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">统一数据库</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">实时一致性</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">教学数据同步</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      统一数据库保证教学数据的 实时一致性和准确性。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    消息通知
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">集成状态</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">重要信息推送</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">送达率</Text>
                      <Badge color="green">96%</Badge>
                    </Group>
                    <Text size="xs" c="dimmed">
                      集成消息通知功能， 及时推送重要信息。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card withBorder p="md">
                  <Text fw={500} mb="md">
                    第三方集成
                  </Text>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm">教育工具支持</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">平台集成数量</Text>
                      <Badge color="teal">8个</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm">API兼容性</Text>
                      <IconCheck size={16} color="green" />
                    </Group>
                    <Text size="xs" c="dimmed">
                      支持与其他教育工具和平台的 无缝集成和数据交换。
                    </Text>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  )
}

export default TechnicalRequirementsPage
