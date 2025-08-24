/**
 * 热点资源池管理页面 - 需求12实现
 */
import {
  ActionIcon,
  Badge,
  Button,
  Container,
  Group,
  Modal,
  Paper,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  TextInput,
  Title,
  Tooltip,
  Progress,
  Alert,
  Menu,
  Textarea,
  Switch,
  NumberInput,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconPlus,
  IconEdit,
  IconTrash,
  IconDownload,
  IconShare,
  IconRefresh,
  IconRss,
  IconNews,
  IconFilter,
  IconSearch,
  IconDots,
  IconEye,
  IconCopy,
  IconCalendar,
  IconTrendingUp,
  IconSettings,
  IconBolt,
} from '@tabler/icons-react'
import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

// 热点资源类型定义
interface HotspotResource {
  id: number
  title: string
  content: string
  summary: string
  sourceType: 'RSS' | 'API' | 'MANUAL'
  sourceUrl?: string
  sourceName: string
  category: string
  tags: string[]
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced'
  ageGroup: string
  publishedAt: string
  createdAt: string
  isRecommended: boolean
  relevanceScore: number
  viewCount: number
}

interface RSSSource {
  id: number
  name: string
  url: string
  category: string
  isActive: boolean
  lastSync: string
  itemCount: number
}

export function HotTopicsPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('hotspots')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [filterDifficulty, setFilterDifficulty] = useState<string>('')
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotResource | null>(null)
  const [selectedSource, setSelectedSource] = useState<RSSSource | null>(null)

  // 模态框状态
  const [hotspotModalOpened, { open: openHotspotModal, close: closeHotspotModal }] =
    useDisclosure(false)
  const [sourceModalOpened, { open: openSourceModal, close: closeSourceModal }] =
    useDisclosure(false)
  const [collectModalOpened, { open: openCollectModal, close: closeCollectModal }] =
    useDisclosure(false)

  // 模拟数据查询 - 热点资源
  const {
    data: hotspotsData,
    isLoading: hotspotsLoading,
    refetch: refetchHotspots,
  } = useQuery({
    queryKey: ['hotspots', searchQuery, filterCategory, filterDifficulty],
    queryFn: async () => {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockData: HotspotResource[] = [
        {
          id: 1,
          title: 'AI Technology Revolutionizes Education',
          content: 'Artificial Intelligence is transforming the way we learn and teach...',
          summary: 'AI在教育领域的革命性应用',
          sourceType: 'RSS',
          sourceUrl: 'https://example.com/news/ai-education',
          sourceName: 'Education Today',
          category: 'Technology',
          tags: ['AI', 'Education', 'Innovation'],
          difficultyLevel: 'intermediate',
          ageGroup: 'college',
          publishedAt: '2024-01-20T10:30:00Z',
          createdAt: '2024-01-20T11:00:00Z',
          isRecommended: true,
          relevanceScore: 0.92,
          viewCount: 156,
        },
        {
          id: 2,
          title: 'Climate Change and Global Response',
          content: 'World leaders gather to discuss climate action...',
          summary: '全球气候变化应对措施',
          sourceType: 'MANUAL',
          sourceName: 'Teacher Input',
          category: 'Environment',
          tags: ['Climate', 'Environment', 'Global'],
          difficultyLevel: 'advanced',
          ageGroup: 'college',
          publishedAt: '2024-01-19T14:20:00Z',
          createdAt: '2024-01-19T15:00:00Z',
          isRecommended: false,
          relevanceScore: 0.78,
          viewCount: 89,
        },
        {
          id: 3,
          title: 'New Study Methods for Language Learning',
          content: 'Research shows innovative approaches to language acquisition...',
          summary: '语言学习新方法研究',
          sourceType: 'API',
          sourceUrl: 'https://api.example.com/language-research',
          sourceName: 'Language Research API',
          category: 'Education',
          tags: ['Language', 'Learning', 'Research'],
          difficultyLevel: 'beginner',
          ageGroup: 'college',
          publishedAt: '2024-01-18T09:15:00Z',
          createdAt: '2024-01-18T10:00:00Z',
          isRecommended: true,
          relevanceScore: 0.95,
          viewCount: 234,
        },
      ]

      return mockData.filter(
        item =>
          (searchQuery === '' || item.title.toLowerCase().includes(searchQuery.toLowerCase())) &&
          (filterCategory === '' || item.category === filterCategory) &&
          (filterDifficulty === '' || item.difficultyLevel === filterDifficulty)
      )
    },
  })

  // 模拟数据查询 - RSS订阅源
  const { data: sourcesData, isLoading: sourcesLoading } = useQuery({
    queryKey: ['rss-sources'],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 300))

      const mockSources: RSSSource[] = [
        {
          id: 1,
          name: 'BBC Learning English',
          url: 'https://www.bbc.co.uk/learningenglish/rss',
          category: 'Education',
          isActive: true,
          lastSync: '2024-01-20T08:00:00Z',
          itemCount: 25,
        },
        {
          id: 2,
          name: 'CNN Education',
          url: 'https://rss.cnn.com/rss/edition.rss',
          category: 'News',
          isActive: true,
          lastSync: '2024-01-20T07:30:00Z',
          itemCount: 18,
        },
        {
          id: 3,
          name: 'TED Talks Education',
          url: 'https://feeds.feedburner.com/tedtalks_video',
          category: 'Technology',
          isActive: false,
          lastSync: '2024-01-19T12:00:00Z',
          itemCount: 12,
        },
      ]

      return mockSources
    },
  })

  const getDifficultyBadge = (level: string) => {
    const config = {
      beginner: { label: '初级', color: 'green' },
      intermediate: { label: '中级', color: 'blue' },
      advanced: { label: '高级', color: 'red' },
    }
    const { label, color } = config[level as keyof typeof config]
    return (
      <Badge color={color} size="sm">
        {label}
      </Badge>
    )
  }

  const getSourceTypeBadge = (type: string) => {
    const config = {
      RSS: { label: 'RSS', color: 'orange', icon: IconRss },
      API: { label: 'API', color: 'blue', icon: IconBolt },
      MANUAL: { label: '手动', color: 'gray', icon: IconEdit },
    }
    const { label, color, icon: Icon } = config[type as keyof typeof config]
    return (
      <Badge color={color} size="sm" leftSection={<Icon size={12} />}>
        {label}
      </Badge>
    )
  }

  const handleCreateHotspot = useCallback(() => {
    setSelectedHotspot(null)
    openHotspotModal()
  }, [openHotspotModal])

  const handleEditHotspot = useCallback(
    (hotspot: HotspotResource) => {
      setSelectedHotspot(hotspot)
      openHotspotModal()
    },
    [openHotspotModal]
  )

  const handleCreateSource = useCallback(() => {
    setSelectedSource(null)
    openSourceModal()
  }, [openSourceModal])

  const handleEditSource = useCallback(
    (source: RSSSource) => {
      setSelectedSource(source)
      openSourceModal()
    },
    [openSourceModal]
  )

  const handleCollectRSS = useCallback(async () => {
    try {
      // 模拟RSS收集
      await new Promise(resolve => setTimeout(resolve, 2000))

      notifications.show({
        title: 'RSS收集完成',
        message: '成功收集到 15 个新的热点资源',
        color: 'green',
      })

      refetchHotspots()
      closeCollectModal()
    } catch (error) {
      notifications.show({
        title: 'RSS收集失败',
        message: '请稍后重试',
        color: 'red',
      })
    }
  }, [refetchHotspots, closeCollectModal])

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>热点资源池管理</Title>
          <Text c="dimmed" mt="xs">
            管理时事热点资源，将最新资讯融入教学中
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="light"
            onClick={openCollectModal}
          >
            收集RSS
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreateHotspot}>
            新建热点
          </Button>
        </Group>
      </Group>

      {/* 标签页 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'hotspots')} mb="xl">
        <Tabs.List>
          <Tabs.Tab value="hotspots" leftSection={<IconNews size={16} />}>
            热点资源
          </Tabs.Tab>
          <Tabs.Tab value="sources" leftSection={<IconRss size={16} />}>
            订阅源管理
          </Tabs.Tab>
          <Tabs.Tab value="recommendations" leftSection={<IconTrendingUp size={16} />}>
            每日推荐
          </Tabs.Tab>
          <Tabs.Tab value="analytics" leftSection={<IconCalendar size={16} />}>
            数据统计
          </Tabs.Tab>
        </Tabs.List>

        {/* 热点资源标签页 */}
        <Tabs.Panel value="hotspots">
          <Alert color="blue" mb="md">
            <Text size="sm">管理热点资源，支持RSS自动收集、手动录入和智能分类</Text>
          </Alert>

          {/* 搜索和筛选 */}
          <Paper withBorder p="md" mb="xl">
            <Group>
              <TextInput
                placeholder="搜索热点资源..."
                leftSection={<IconSearch size={16} />}
                value={searchQuery}
                onChange={event => setSearchQuery(event.currentTarget.value)}
                style={{ flex: 1 }}
              />
              <Select
                placeholder="分类筛选"
                leftSection={<IconFilter size={16} />}
                value={filterCategory}
                onChange={value => setFilterCategory(value || '')}
                data={[
                  { value: '', label: '全部分类' },
                  { value: 'Technology', label: '科技' },
                  { value: 'Education', label: '教育' },
                  { value: 'Environment', label: '环境' },
                  { value: 'Health', label: '健康' },
                ]}
                clearable
                style={{ minWidth: 150 }}
              />
              <Select
                placeholder="难度筛选"
                value={filterDifficulty}
                onChange={value => setFilterDifficulty(value || '')}
                data={[
                  { value: '', label: '全部难度' },
                  { value: 'beginner', label: '初级' },
                  { value: 'intermediate', label: '中级' },
                  { value: 'advanced', label: '高级' },
                ]}
                clearable
                style={{ minWidth: 120 }}
              />
            </Group>
          </Paper>

          {/* 热点资源列表 */}
          <Paper withBorder>
            {hotspotsLoading ? (
              <Stack align="center" p="xl">
                <Progress value={50} size="sm" style={{ width: '100%' }} />
                <Text c="dimmed">加载热点资源中...</Text>
              </Stack>
            ) : hotspotsData && hotspotsData.length > 0 ? (
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>标题</Table.Th>
                    <Table.Th>来源</Table.Th>
                    <Table.Th>分类</Table.Th>
                    <Table.Th>难度</Table.Th>
                    <Table.Th>相关性</Table.Th>
                    <Table.Th>发布时间</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {hotspotsData.map(hotspot => (
                    <Table.Tr key={hotspot.id}>
                      <Table.Td>
                        <div>
                          <Group gap="xs" mb="xs">
                            <Text fw={500} size="sm">
                              {hotspot.title}
                            </Text>
                            {hotspot.isRecommended && (
                              <Badge color="yellow" size="xs">
                                推荐
                              </Badge>
                            )}
                          </Group>
                          <Text size="xs" c="dimmed" truncate style={{ maxWidth: 300 }}>
                            {hotspot.summary}
                          </Text>
                          <Group gap="xs" mt="xs">
                            {hotspot.tags.slice(0, 3).map((tag, index) => (
                              <Badge key={index} variant="light" size="xs">
                                {tag}
                              </Badge>
                            ))}
                          </Group>
                        </div>
                      </Table.Td>
                      <Table.Td>
                        <Stack gap="xs">
                          {getSourceTypeBadge(hotspot.sourceType)}
                          <Text size="xs" c="dimmed">
                            {hotspot.sourceName}
                          </Text>
                        </Stack>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="light" color="blue">
                          {hotspot.category}
                        </Badge>
                      </Table.Td>
                      <Table.Td>{getDifficultyBadge(hotspot.difficultyLevel)}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Progress
                            value={hotspot.relevanceScore * 100}
                            size="sm"
                            style={{ width: 60 }}
                            color={
                              hotspot.relevanceScore > 0.8
                                ? 'green'
                                : hotspot.relevanceScore > 0.6
                                  ? 'blue'
                                  : 'orange'
                            }
                          />
                          <Text size="xs">{(hotspot.relevanceScore * 100).toFixed(0)}%</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {new Date(hotspot.publishedAt).toLocaleDateString('zh-CN')}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {hotspot.viewCount} 次查看
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="查看详情">
                            <ActionIcon variant="light" size="sm">
                              <IconEye size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="编辑">
                            <ActionIcon
                              variant="light"
                              size="sm"
                              color="blue"
                              onClick={() => handleEditHotspot(hotspot)}
                            >
                              <IconEdit size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Menu shadow="md" width={200}>
                            <Menu.Target>
                              <ActionIcon variant="light" size="sm">
                                <IconDots size={14} />
                              </ActionIcon>
                            </Menu.Target>
                            <Menu.Dropdown>
                              <Menu.Item leftSection={<IconShare size={14} />}>
                                分享到课程
                              </Menu.Item>
                              <Menu.Item leftSection={<IconCopy size={14} />}>复制链接</Menu.Item>
                              <Menu.Item leftSection={<IconDownload size={14} />}>
                                导出内容
                              </Menu.Item>
                              <Menu.Divider />
                              <Menu.Item leftSection={<IconTrash size={14} />} color="red">
                                删除
                              </Menu.Item>
                            </Menu.Dropdown>
                          </Menu>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            ) : (
              <Stack align="center" p="xl">
                <Text c="dimmed">暂无热点资源数据</Text>
                <Button
                  variant="light"
                  leftSection={<IconPlus size={16} />}
                  onClick={handleCreateHotspot}
                >
                  创建第一个热点资源
                </Button>
              </Stack>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 订阅源管理标签页 */}
        <Tabs.Panel value="sources">
          <Alert color="orange" mb="md">
            <Text size="sm">管理RSS订阅源和API接口，自动收集最新热点资源</Text>
          </Alert>

          <Group justify="space-between" mb="md">
            <Text fw={500}>RSS订阅源列表</Text>
            <Button leftSection={<IconPlus size={16} />} onClick={handleCreateSource} size="sm">
              添加订阅源
            </Button>
          </Group>

          <Paper withBorder>
            {sourcesLoading ? (
              <Stack align="center" p="xl">
                <Progress value={50} size="sm" style={{ width: '100%' }} />
                <Text c="dimmed">加载订阅源中...</Text>
              </Stack>
            ) : sourcesData && sourcesData.length > 0 ? (
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>订阅源名称</Table.Th>
                    <Table.Th>分类</Table.Th>
                    <Table.Th>状态</Table.Th>
                    <Table.Th>最后同步</Table.Th>
                    <Table.Th>资源数量</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {sourcesData.map(source => (
                    <Table.Tr key={source.id}>
                      <Table.Td>
                        <div>
                          <Text fw={500} size="sm">
                            {source.name}
                          </Text>
                          <Text size="xs" c="dimmed" truncate style={{ maxWidth: 300 }}>
                            {source.url}
                          </Text>
                        </div>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="light" color="blue">
                          {source.category}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge color={source.isActive ? 'green' : 'gray'}>
                          {source.isActive ? '活跃' : '暂停'}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {new Date(source.lastSync).toLocaleDateString('zh-CN')}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {new Date(source.lastSync).toLocaleTimeString('zh-CN')}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{source.itemCount} 条</Text>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="立即同步">
                            <ActionIcon variant="light" size="sm" color="blue">
                              <IconRefresh size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="编辑">
                            <ActionIcon
                              variant="light"
                              size="sm"
                              color="orange"
                              onClick={() => handleEditSource(source)}
                            >
                              <IconEdit size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="设置">
                            <ActionIcon variant="light" size="sm">
                              <IconSettings size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="删除">
                            <ActionIcon variant="light" size="sm" color="red">
                              <IconTrash size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            ) : (
              <Stack align="center" p="xl">
                <Text c="dimmed">暂无订阅源</Text>
                <Button
                  variant="light"
                  leftSection={<IconPlus size={16} />}
                  onClick={handleCreateSource}
                >
                  添加第一个订阅源
                </Button>
              </Stack>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 每日推荐标签页 */}
        <Tabs.Panel value="recommendations">
          <Alert color="green" mb="md">
            <Text size="sm">基于教学内容和学生水平，智能推荐适合的热点资源</Text>
          </Alert>

          <Paper withBorder p="md">
            <Stack align="center" p="xl">
              <IconTrendingUp size={48} color="var(--mantine-color-green-6)" />
              <Text size="lg" fw={500}>
                每日推荐功能
              </Text>
              <Text c="dimmed" ta="center">
                系统将根据您的课程内容和学生水平，每日智能推荐适合的热点资源
              </Text>
              <Button leftSection={<IconRefresh size={16} />}>获取今日推荐</Button>
            </Stack>
          </Paper>
        </Tabs.Panel>

        {/* 数据统计标签页 */}
        <Tabs.Panel value="analytics">
          <Alert color="purple" mb="md">
            <Text size="sm">查看热点资源的使用统计和趋势分析</Text>
          </Alert>

          <Paper withBorder p="md">
            <Stack align="center" p="xl">
              <IconCalendar size={48} color="var(--mantine-color-purple-6)" />
              <Text size="lg" fw={500}>
                数据统计分析
              </Text>
              <Text c="dimmed" ta="center">
                热点资源的访问量、使用频率和教学效果统计分析
              </Text>
              <Button leftSection={<IconCalendar size={16} />}>查看详细统计</Button>
            </Stack>
          </Paper>
        </Tabs.Panel>
      </Tabs>

      {/* RSS收集模态框 */}
      <Modal
        opened={collectModalOpened}
        onClose={closeCollectModal}
        title="RSS资源收集"
        size="md"
        centered
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text size="sm">将从所有活跃的RSS订阅源收集最新的热点资源，预计需要1-2分钟</Text>
          </Alert>

          <Group justify="space-between">
            <Text size="sm">收集数量限制：</Text>
            <NumberInput value={10} min={1} max={50} style={{ width: 100 }} />
          </Group>

          <Group justify="space-between">
            <Text size="sm">目标语言：</Text>
            <Select
              value="en"
              data={[
                { value: 'en', label: '英语' },
                { value: 'zh', label: '中文' },
                { value: 'all', label: '全部' },
              ]}
              style={{ width: 120 }}
            />
          </Group>

          <Group justify="flex-end">
            <Button variant="light" onClick={closeCollectModal}>
              取消
            </Button>
            <Button onClick={handleCollectRSS}>开始收集</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 热点资源编辑模态框 */}
      <Modal
        opened={hotspotModalOpened}
        onClose={closeHotspotModal}
        title={selectedHotspot ? '编辑热点资源' : '新建热点资源'}
        size="lg"
      >
        <Stack gap="md">
          <TextInput label="标题" placeholder="输入热点资源标题" required />

          <Group grow>
            <Select
              label="分类"
              placeholder="选择分类"
              data={[
                { value: 'Technology', label: '科技' },
                { value: 'Education', label: '教育' },
                { value: 'Environment', label: '环境' },
                { value: 'Health', label: '健康' },
              ]}
              required
            />
            <Select
              label="难度级别"
              placeholder="选择难度"
              data={[
                { value: 'beginner', label: '初级' },
                { value: 'intermediate', label: '中级' },
                { value: 'advanced', label: '高级' },
              ]}
              required
            />
          </Group>

          <Textarea label="内容摘要" placeholder="输入内容摘要" minRows={3} required />

          <Textarea label="详细内容" placeholder="输入详细内容" minRows={5} required />

          <TextInput label="来源链接" placeholder="输入原文链接（可选）" />

          <TextInput label="标签" placeholder="输入标签，用逗号分隔" />

          <Group>
            <Switch label="推荐资源" description="标记为推荐资源" />
          </Group>

          <Group justify="flex-end">
            <Button variant="light" onClick={closeHotspotModal}>
              取消
            </Button>
            <Button onClick={closeHotspotModal}>{selectedHotspot ? '更新' : '创建'}</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 订阅源编辑模态框 */}
      <Modal
        opened={sourceModalOpened}
        onClose={closeSourceModal}
        title={selectedSource ? '编辑订阅源' : '添加订阅源'}
        size="md"
      >
        <Stack gap="md">
          <TextInput label="订阅源名称" placeholder="输入订阅源名称" required />

          <TextInput label="RSS URL" placeholder="输入RSS订阅地址" required />

          <Select
            label="分类"
            placeholder="选择分类"
            data={[
              { value: 'Education', label: '教育' },
              { value: 'News', label: '新闻' },
              { value: 'Technology', label: '科技' },
              { value: 'Science', label: '科学' },
            ]}
            required
          />

          <Group>
            <Switch label="启用订阅源" description="是否自动同步此订阅源" defaultChecked />
          </Group>

          <Group justify="flex-end">
            <Button variant="light" onClick={closeSourceModal}>
              取消
            </Button>
            <Button onClick={closeSourceModal}>{selectedSource ? '更新' : '添加'}</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
