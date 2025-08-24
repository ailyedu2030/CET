/**
 * 离线功能测试页面
 * 
 * 用于测试和演示离线功能：
 * - 离线数据操作
 * - 同步状态监控
 * - 冲突处理演示
 * - 存储管理
 */

import {
  Container,
  Title,
  Text,
  Grid,
  Card,
  Stack,
  Button,
  Group,
  Alert,
  Tabs,
  Badge,
} from '@mantine/core'
import {
  IconDatabase,
  IconCloudUpload,
  IconAlertTriangle,
  IconInfoCircle,
  IconEdit,
  IconEye,
  IconSpeedboat,
} from '@tabler/icons-react'
import { useState } from 'react'

import { OfflineLessonPlanEditor } from '@/components/Offline/OfflineLessonPlanEditor'
import { OfflineStatusPanel } from '@/components/Offline/OfflineStatusPanel'
import { PerformanceMonitor } from '@/components/Performance/PerformanceMonitor'
import { VirtualList } from '@/components/Performance/VirtualList'
import { OptimizedImage, ImageGrid } from '@/components/Performance/OptimizedImage'
import { useOfflineData, useOfflineStatus, useSyncStatus } from '@/hooks/useOfflineData'
import { STORES } from '@/services/offlineStorage'

export function OfflineTest(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string | null>('overview')
  const [editingLessonPlan, setEditingLessonPlan] = useState<string | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [testData, setTestData] = useState<any[]>([])

  // 生成测试数据
  const generateTestData = () => {
    const data = Array.from({ length: 1000 }, (_, index) => ({
      id: `item-${index}`,
      title: `测试项目 ${index + 1}`,
      description: `这是第 ${index + 1} 个测试项目的描述`,
      timestamp: Date.now() - Math.random() * 86400000,
      type: ['lesson', 'resource', 'student'][index % 3],
    }))
    setTestData(data)
  }

  const { isOffline } = useOfflineStatus()
  const { pendingItems, isSync } = useSyncStatus()

  // 获取离线教案数据
  const {
    data: lessonPlans,
    isLoading: lessonPlansLoading,
    create: createLessonPlan,
    delete: deleteLessonPlan,
  } = useOfflineData<any>(
    ['lessonPlans'],
    {
      storeType: STORES.LESSON_PLANS,
      enableSync: true,
    }
  )

  // 创建测试教案
  const handleCreateTestLessonPlan = async () => {
    const testPlan = {
      id: `test_${Date.now()}`,
      title: `测试教案 ${new Date().toLocaleTimeString()}`,
      content: '这是一个测试教案内容，用于演示离线功能。',
      objectives: '测试离线数据存储和同步功能',
      materials: '无需特殊材料',
      duration: 45,
    }

    await createLessonPlan(testPlan)
  }

  // 删除教案
  const handleDeleteLessonPlan = async (id: string) => {
    await deleteLessonPlan(id)
  }

  return (
    <Container size="xl" py="xl">
      <Stack gap="lg">
        {/* 页面标题 */}
        <Group justify="space-between">
          <div>
            <Title order={2}>离线功能测试</Title>
            <Text c="dimmed">测试和演示离线数据存储、同步和冲突处理功能</Text>
          </div>
          
          <Group gap="xs">
            <Badge color={isOffline ? 'orange' : 'green'}>
              {isOffline ? '离线模式' : '在线模式'}
            </Badge>
            
            {pendingItems > 0 && (
              <Badge color="blue">{pendingItems} 待同步</Badge>
            )}
            
            {isSync && (
              <Badge color="blue" variant="light">同步中</Badge>
            )}
          </Group>
        </Group>

        {/* 功能说明 */}
        <Alert icon={<IconInfoCircle size={16} />} color="blue">
          <Text size="sm">
            此页面演示离线功能：断开网络连接后，您仍可以编辑教案、查看资源。
            网络恢复后，数据将自动同步到服务器。
          </Text>
        </Alert>

        <Grid>
          {/* 左侧：功能测试 */}
          <Grid.Col span={8}>
            <Tabs value={activeTab} onChange={setActiveTab}>
              <Tabs.List>
                <Tabs.Tab value="overview" leftSection={<IconEye size={16} />}>
                  功能概览
                </Tabs.Tab>
                <Tabs.Tab value="editor" leftSection={<IconEdit size={16} />}>
                  离线编辑
                </Tabs.Tab>
                <Tabs.Tab value="data" leftSection={<IconDatabase size={16} />}>
                  数据管理
                </Tabs.Tab>
                <Tabs.Tab value="performance" leftSection={<IconSpeedboat size={16} />}>
                  性能优化
                </Tabs.Tab>
              </Tabs.List>

              <Tabs.Panel value="overview" pt="md">
                <Stack gap="md">
                  <Card withBorder>
                    <Stack gap="md">
                      <Text fw={600}>离线功能特性</Text>
                      
                      <Grid>
                        <Grid.Col span={6}>
                          <Card withBorder>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <IconDatabase size={16} color="blue" />
                                <Text size="sm" fw={600}>本地存储</Text>
                              </Group>
                              <Text size="xs" c="dimmed">
                                使用IndexedDB存储离线数据，支持大容量数据缓存
                              </Text>
                            </Stack>
                          </Card>
                        </Grid.Col>
                        
                        <Grid.Col span={6}>
                          <Card withBorder>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <IconCloudUpload size={16} color="green" />
                                <Text size="sm" fw={600}>自动同步</Text>
                              </Group>
                              <Text size="xs" c="dimmed">
                                网络恢复后自动同步离线期间的所有操作
                              </Text>
                            </Stack>
                          </Card>
                        </Grid.Col>
                        
                        <Grid.Col span={6}>
                          <Card withBorder>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <IconAlertTriangle size={16} color="orange" />
                                <Text size="sm" fw={600}>冲突处理</Text>
                              </Group>
                              <Text size="xs" c="dimmed">
                                智能检测数据冲突，提供多种解决方案
                              </Text>
                            </Stack>
                          </Card>
                        </Grid.Col>
                        
                        <Grid.Col span={6}>
                          <Card withBorder>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <IconEdit size={16} color="purple" />
                                <Text size="sm" fw={600}>离线编辑</Text>
                              </Group>
                              <Text size="xs" c="dimmed">
                                支持教案编辑、资源查看等核心功能离线使用
                              </Text>
                            </Stack>
                          </Card>
                        </Grid.Col>
                      </Grid>
                    </Stack>
                  </Card>

                  <Card withBorder>
                    <Stack gap="md">
                      <Text fw={600}>测试步骤</Text>
                      
                      <Stack gap="xs">
                        <Text size="sm">1. 在在线状态下创建或编辑教案</Text>
                        <Text size="sm">2. 断开网络连接（关闭WiFi或拔掉网线）</Text>
                        <Text size="sm">3. 继续编辑教案，观察离线模式提示</Text>
                        <Text size="sm">4. 重新连接网络，观察自动同步过程</Text>
                        <Text size="sm">5. 如有冲突，使用冲突解决工具处理</Text>
                      </Stack>
                    </Stack>
                  </Card>
                </Stack>
              </Tabs.Panel>

              <Tabs.Panel value="editor" pt="md">
                <Stack gap="md">
                  {!showEditor ? (
                    <Card withBorder>
                      <Stack gap="md">
                        <Group justify="space-between">
                          <Text fw={600}>离线教案编辑器</Text>
                          <Button
                            onClick={() => setShowEditor(true)}
                            leftSection={<IconEdit size={16} />}
                          >
                            打开编辑器
                          </Button>
                        </Group>
                        
                        <Text size="sm" c="dimmed">
                          点击打开编辑器，体验离线编辑功能。编辑器支持自动保存、
                          离线存储和网络恢复后的自动同步。
                        </Text>
                      </Stack>
                    </Card>
                  ) : (
                    <OfflineLessonPlanEditor
                      lessonPlanId={editingLessonPlan || undefined}
                      onSave={() => {
                        setShowEditor(false)
                        setEditingLessonPlan(null)
                      }}
                      onCancel={() => {
                        setShowEditor(false)
                        setEditingLessonPlan(null)
                      }}
                    />
                  )}
                </Stack>
              </Tabs.Panel>

              <Tabs.Panel value="data" pt="md">
                <Stack gap="md">
                  <Card withBorder>
                    <Stack gap="md">
                      <Group justify="space-between">
                        <Text fw={600}>离线教案数据</Text>
                        <Button
                          size="sm"
                          onClick={handleCreateTestLessonPlan}
                          leftSection={<IconDatabase size={16} />}
                        >
                          创建测试数据
                        </Button>
                      </Group>

                      {lessonPlansLoading ? (
                        <Text size="sm" c="dimmed">加载中...</Text>
                      ) : (
                        <Stack gap="xs">
                          {(!lessonPlans || (Array.isArray(lessonPlans) && lessonPlans.length === 0)) ? (
                            <Text size="sm" c="dimmed">暂无离线教案数据</Text>
                          ) : (
                            (Array.isArray(lessonPlans) ? lessonPlans : [lessonPlans]).map((plan: any) => (
                              <Card key={plan.id} withBorder>
                                <Group justify="space-between">
                                  <div>
                                    <Text size="sm" fw={600}>{plan.title}</Text>
                                    <Text size="xs" c="dimmed">
                                      {new Date(plan.lastModified).toLocaleString()}
                                    </Text>
                                  </div>

                                  <Group gap="xs">
                                    <Button
                                      size="xs"
                                      variant="outline"
                                      onClick={() => {
                                        setEditingLessonPlan(plan.id)
                                        setShowEditor(true)
                                        setActiveTab('editor')
                                      }}
                                    >
                                      编辑
                                    </Button>
                                    <Button
                                      size="xs"
                                      variant="outline"
                                      color="red"
                                      onClick={() => handleDeleteLessonPlan(plan.id)}
                                    >
                                      删除
                                    </Button>
                                  </Group>
                                </Group>
                              </Card>
                            ))
                          )}
                        </Stack>
                      )}
                    </Stack>
                  </Card>
                </Stack>
              </Tabs.Panel>

              <Tabs.Panel value="performance" pt="md">
                <Stack gap="md">
                  {/* 性能监控 */}
                  <PerformanceMonitor />

                  {/* 虚拟滚动演示 */}
                  <Card withBorder>
                    <Stack gap="md">
                      <Group justify="space-between">
                        <Text fw={600}>虚拟滚动演示</Text>
                        <Button
                          size="sm"
                          onClick={generateTestData}
                          leftSection={<IconDatabase size={16} />}
                        >
                          生成测试数据
                        </Button>
                      </Group>

                      <Text size="sm" c="dimmed">
                        虚拟滚动可以高效渲染大量列表项目，只渲染可见区域的内容
                      </Text>

                      {testData.length > 0 && (
                        <VirtualList
                          items={testData}
                          itemHeight={60}
                          height={300}
                          renderItem={(item, _index) => (
                            <Card withBorder p="sm">
                              <Group justify="space-between">
                                <div>
                                  <Text size="sm" fw={600}>{item.title}</Text>
                                  <Text size="xs" c="dimmed">{item.description}</Text>
                                </div>
                                <Badge size="sm" variant="outline">
                                  {item.type}
                                </Badge>
                              </Group>
                            </Card>
                          )}
                        />
                      )}
                    </Stack>
                  </Card>

                  {/* 图片优化演示 */}
                  <Card withBorder>
                    <Stack gap="md">
                      <Text fw={600}>图片优化演示</Text>

                      <Text size="sm" c="dimmed">
                        自动选择最佳图片格式、懒加载和响应式尺寸
                      </Text>

                      <Grid>
                        <Grid.Col span={6}>
                          <Stack gap="xs">
                            <Text size="sm" fw={600}>普通图片</Text>
                            <img
                              src="https://picsum.photos/300/200?random=1"
                              alt="普通图片"
                              style={{ width: '100%', height: 'auto' }}
                            />
                          </Stack>
                        </Grid.Col>

                        <Grid.Col span={6}>
                          <Stack gap="xs">
                            <Text size="sm" fw={600}>优化图片</Text>
                            <OptimizedImage
                              src="https://picsum.photos/300/200?random=2"
                              alt="优化图片"
                              width="100%"
                              quality={0.8}
                              format="auto"
                              lazy={true}
                            />
                          </Stack>
                        </Grid.Col>
                      </Grid>

                      <Text size="sm" fw={600}>响应式图片网格</Text>
                      <ImageGrid
                        images={[
                          { id: '1', src: 'https://picsum.photos/300/300?random=3', alt: '图片1' },
                          { id: '2', src: 'https://picsum.photos/300/300?random=4', alt: '图片2' },
                          { id: '3', src: 'https://picsum.photos/300/300?random=5', alt: '图片3' },
                          { id: '4', src: 'https://picsum.photos/300/300?random=6', alt: '图片4' },
                          { id: '5', src: 'https://picsum.photos/300/300?random=7', alt: '图片5' },
                          { id: '6', src: 'https://picsum.photos/300/300?random=8', alt: '图片6' },
                        ]}
                        columns={3}
                        aspectRatio={1}
                      />
                    </Stack>
                  </Card>
                </Stack>
              </Tabs.Panel>
            </Tabs>
          </Grid.Col>

          {/* 右侧：状态面板 */}
          <Grid.Col span={4}>
            <OfflineStatusPanel />
          </Grid.Col>
        </Grid>
      </Stack>
    </Container>
  )
}
