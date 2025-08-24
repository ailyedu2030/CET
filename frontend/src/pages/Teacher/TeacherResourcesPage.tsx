/**
 * 教师资源管理页面 - 需求11实现
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
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconPlus,
  IconEdit,
  IconTrash,
  IconDownload,
  IconShare,
  IconUpload,
  IconBook,
  IconVocabulary,
  IconBrain,
  IconFileText,
  IconFilter,
  IconSearch,
  IconDots,
  IconEye,
  IconCopy,
  IconLock,
  IconUsers,
  IconWorld,
  IconFolder,
  IconTemplate,
  IconPhoto,
  IconStar,
  IconVideo,
  IconMusic,
} from '@tabler/icons-react'
import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

import { BatchImportModal } from '@/components/Resources/BatchImportModal'
import { PermissionSettingsModal } from '@/components/Resources/PermissionSettingsModal'

// 资源类型定义
interface ResourceItem {
  id: number
  name: string
  type: 'vocabulary' | 'knowledge' | 'material' | 'syllabus'
  category: string
  itemCount: number
  permission: 'private' | 'class' | 'public'
  lastUpdated: string
  createdAt: string
  fileSize?: number
  version?: string
  description?: string
}

export function TeacherResourcesPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('vocabulary')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [selectedResource, setSelectedResource] = useState<ResourceItem | null>(null)

  // 模态框状态
  const [batchImportOpened, { open: openBatchImport, close: closeBatchImport }] =
    useDisclosure(false)
  const [permissionOpened, { open: openPermission, close: closePermission }] = useDisclosure(false)
  const [resourceModalOpened, { open: openResourceModal, close: closeResourceModal }] =
    useDisclosure(false)

  // 模拟数据查询
  const {
    data: resourcesData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['teacher-resources', activeTab, searchQuery, filterCategory],
    queryFn: async () => {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockData: ResourceItem[] = [
        {
          id: 1,
          name: 'CET4核心词汇库',
          type: 'vocabulary',
          category: '核心词汇',
          itemCount: 2500,
          permission: 'class',
          lastUpdated: '2024-01-20T10:30:00Z',
          createdAt: '2024-01-15T08:00:00Z',
          description: 'CET4考试核心词汇，包含音标、释义、例句',
        },
        {
          id: 2,
          name: '语法知识点库',
          type: 'knowledge',
          category: '语法',
          itemCount: 150,
          permission: 'public',
          lastUpdated: '2024-01-19T14:20:00Z',
          createdAt: '2024-01-10T09:00:00Z',
          description: '英语语法知识点详解',
        },
        {
          id: 3,
          name: '新视野大学英语1',
          type: 'material',
          category: '主教材',
          itemCount: 8,
          permission: 'private',
          lastUpdated: '2024-01-18T16:45:00Z',
          createdAt: '2024-01-12T11:00:00Z',
          fileSize: 25600000,
          version: '第三版',
          description: '新视野大学英语第三版教材',
        },
        {
          id: 4,
          name: 'CET4考试大纲2024',
          type: 'syllabus',
          category: '考试大纲',
          itemCount: 1,
          permission: 'public',
          lastUpdated: '2024-01-17T09:15:00Z',
          createdAt: '2024-01-05T10:00:00Z',
          version: '2024版',
          description: '2024年CET4考试大纲',
        },
      ]

      return mockData.filter(
        item =>
          item.type === activeTab &&
          (searchQuery === '' || item.name.toLowerCase().includes(searchQuery.toLowerCase())) &&
          (filterCategory === '' || item.category === filterCategory)
      )
    },
  })

  const resourceTypeConfig = {
    vocabulary: {
      label: '词汇库',
      icon: IconVocabulary,
      color: 'blue',
      description: '管理课程词汇，支持批量导入和模板复用',
    },
    knowledge: {
      label: '知识点库',
      icon: IconBrain,
      color: 'green',
      description: '管理知识点，支持跨课程共享',
    },
    material: {
      label: '教材库',
      icon: IconBook,
      color: 'orange',
      description: '管理教材文件，支持多版本管理',
    },
    syllabus: {
      label: '考纲管理',
      icon: IconFileText,
      color: 'purple',
      description: '管理考试大纲，支持版本化管理',
    },
    // 需求17：教学资源库功能扩展
    teaching_materials: {
      label: '教学素材',
      icon: IconFolder,
      color: 'teal',
      description: '收集和分类各类教学素材，支持标签管理和快速检索',
    },
    lesson_templates: {
      label: '教案模板',
      icon: IconTemplate,
      color: 'indigo',
      description: '共享优质教案模板，支持模板复用和协作编辑',
    },
    multimedia: {
      label: '多媒体资源',
      icon: IconPhoto,
      color: 'pink',
      description: '管理视频、音频、图片等多媒体教学资源',
    },
    recommendations: {
      label: '智能推荐',
      icon: IconStar,
      color: 'yellow',
      description: '基于教师历史使用情况的个性化资源推荐',
    },
  }

  const getPermissionBadge = (permission: string) => {
    const config = {
      private: { label: '私有', color: 'gray', icon: IconLock },
      class: { label: '班级', color: 'blue', icon: IconUsers },
      public: { label: '公开', color: 'green', icon: IconWorld },
    }
    const { label, color, icon: Icon } = config[permission as keyof typeof config]
    return (
      <Badge color={color} size="sm" leftSection={<Icon size={12} />}>
        {label}
      </Badge>
    )
  }

  const handleBatchImport = useCallback(
    (resourceType: 'vocabulary' | 'knowledge') => {
      setActiveTab(resourceType)
      openBatchImport()
    },
    [openBatchImport]
  )

  const handlePermissionSettings = useCallback(
    (resource: ResourceItem) => {
      setSelectedResource(resource)
      openPermission()
    },
    [openPermission]
  )

  const handleCreateResource = useCallback(() => {
    setSelectedResource(null)
    openResourceModal()
  }, [openResourceModal])

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>教学资源库与专业发展</Title>
          <Text c="dimmed" mt="xs">
            管理教学素材、教案模板、多媒体资源，支持智能推荐和协作共享 - 需求17实现
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconUpload size={16} />}
            variant="light"
            onClick={() => handleBatchImport(activeTab as 'vocabulary' | 'knowledge')}
            disabled={!['vocabulary', 'knowledge'].includes(activeTab)}
          >
            批量导入
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreateResource}>
            新建资源
          </Button>
        </Group>
      </Group>

      {/* 资源类型标签页 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'vocabulary')} mb="xl">
        <Tabs.List>
          {Object.entries(resourceTypeConfig).map(([key, config]) => {
            const Icon = config.icon
            return (
              <Tabs.Tab key={key} value={key} leftSection={<Icon size={16} />}>
                {config.label}
              </Tabs.Tab>
            )
          })}
        </Tabs.List>

        {Object.entries(resourceTypeConfig).map(([key, config]) => (
          <Tabs.Panel key={key} value={key}>
            <Alert color={config.color} mb="md">
              <Text size="sm">{config.description}</Text>
            </Alert>

            {/* 需求17：为新资源类型添加特殊功能 */}
            {key === 'lesson_templates' && (
              <Paper withBorder p="md" mb="md">
                <Group justify="space-between" mb="sm">
                  <Text fw={500}>教案模板功能</Text>
                  <Group>
                    <Button size="xs" variant="light" leftSection={<IconShare size={14} />}>
                      共享模板
                    </Button>
                    <Button size="xs" variant="light" leftSection={<IconDownload size={14} />}>
                      导入模板
                    </Button>
                  </Group>
                </Group>
                <Text size="sm" c="dimmed">
                  支持模板共享、协作编辑和版本管理
                </Text>
              </Paper>
            )}

            {key === 'multimedia' && (
              <Paper withBorder p="md" mb="md">
                <Group justify="space-between" mb="sm">
                  <Text fw={500}>多媒体管理</Text>
                  <Group>
                    <Button size="xs" variant="light" leftSection={<IconVideo size={14} />}>
                      上传视频
                    </Button>
                    <Button size="xs" variant="light" leftSection={<IconMusic size={14} />}>
                      上传音频
                    </Button>
                    <Button size="xs" variant="light" leftSection={<IconPhoto size={14} />}>
                      上传图片
                    </Button>
                  </Group>
                </Group>
                <Text size="sm" c="dimmed">
                  支持视频、音频、图片等多媒体资源的上传和管理
                </Text>
              </Paper>
            )}

            {key === 'recommendations' && (
              <Paper withBorder p="md" mb="md">
                <Group justify="space-between" mb="sm">
                  <Text fw={500}>智能推荐系统</Text>
                  <Button size="xs" variant="light" leftSection={<IconStar size={14} />}>
                    刷新推荐
                  </Button>
                </Group>
                <Text size="sm" c="dimmed">
                  基于您的使用历史和教学偏好，为您推荐相关资源
                </Text>
              </Paper>
            )}

            {key === 'teaching_materials' && (
              <Paper withBorder p="md" mb="md">
                <Group justify="space-between" mb="sm">
                  <Text fw={500}>素材收集工具</Text>
                  <Group>
                    <Button size="xs" variant="light" leftSection={<IconFolder size={14} />}>
                      批量分类
                    </Button>
                    <Button size="xs" variant="light" leftSection={<IconUpload size={14} />}>
                      批量上传
                    </Button>
                  </Group>
                </Group>
                <Text size="sm" c="dimmed">
                  支持教学素材的自动分类和标签管理
                </Text>
              </Paper>
            )}
          </Tabs.Panel>
        ))}
      </Tabs>

      {/* 搜索和筛选 */}
      <Paper withBorder p="md" mb="xl">
        <Group>
          <TextInput
            placeholder="搜索资源..."
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
              { value: '核心词汇', label: '核心词汇' },
              { value: '语法', label: '语法' },
              { value: '主教材', label: '主教材' },
              { value: '考试大纲', label: '考试大纲' },
              // 需求17：新增分类选项
              { value: '课件素材', label: '课件素材' },
              { value: '练习题库', label: '练习题库' },
              { value: '教案模板', label: '教案模板' },
              { value: '视频资源', label: '视频资源' },
              { value: '音频资源', label: '音频资源' },
              { value: '图片素材', label: '图片素材' },
              { value: '推荐资源', label: '推荐资源' },
            ]}
            clearable
            style={{ minWidth: 150 }}
          />
        </Group>
      </Paper>

      {/* 资源列表 */}
      <Paper withBorder>
        {isLoading ? (
          <Stack align="center" p="xl">
            <Progress value={50} size="sm" style={{ width: '100%' }} />
            <Text c="dimmed">加载资源中...</Text>
          </Stack>
        ) : resourcesData && resourcesData.length > 0 ? (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>资源名称</Table.Th>
                <Table.Th>分类</Table.Th>
                <Table.Th>内容数量</Table.Th>
                <Table.Th>权限</Table.Th>
                <Table.Th>最后更新</Table.Th>
                <Table.Th>操作</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {resourcesData.map(resource => (
                <Table.Tr key={resource.id}>
                  <Table.Td>
                    <div>
                      <Text fw={500}>{resource.name}</Text>
                      {resource.description && (
                        <Text size="sm" c="dimmed" truncate style={{ maxWidth: 200 }}>
                          {resource.description}
                        </Text>
                      )}
                      {resource.version && (
                        <Badge size="xs" variant="light" mt="xs">
                          {resource.version}
                        </Badge>
                      )}
                    </div>
                  </Table.Td>
                  <Table.Td>
                    <Badge variant="light" color={resourceTypeConfig[resource.type].color}>
                      {resource.category}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Text size="sm">{resource.itemCount}</Text>
                      <Text size="xs" c="dimmed">
                        {resource.type === 'vocabulary' && '词汇'}
                        {resource.type === 'knowledge' && '知识点'}
                        {resource.type === 'material' && '章节'}
                        {resource.type === 'syllabus' && '版本'}
                      </Text>
                    </Group>
                    {resource.fileSize && (
                      <Text size="xs" c="dimmed">
                        {(resource.fileSize / 1024 / 1024).toFixed(1)} MB
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td>{getPermissionBadge(resource.permission)}</Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {new Date(resource.lastUpdated).toLocaleDateString('zh-CN')}
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
                        <ActionIcon variant="light" size="sm" color="blue">
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
                          <Menu.Item
                            leftSection={<IconShare size={14} />}
                            onClick={() => handlePermissionSettings(resource)}
                          >
                            权限设置
                          </Menu.Item>
                          <Menu.Item leftSection={<IconCopy size={14} />}>复制资源</Menu.Item>
                          <Menu.Item leftSection={<IconDownload size={14} />}>导出数据</Menu.Item>
                          <Menu.Divider />
                          <Menu.Item leftSection={<IconTrash size={14} />} color="red">
                            删除资源
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
            <Text c="dimmed">
              暂无{resourceTypeConfig[activeTab as keyof typeof resourceTypeConfig].label}数据
            </Text>
            <Button
              variant="light"
              leftSection={<IconPlus size={16} />}
              onClick={handleCreateResource}
            >
              创建第一个资源
            </Button>
          </Stack>
        )}
      </Paper>

      {/* 批量导入模态框 */}
      <BatchImportModal
        opened={batchImportOpened}
        onClose={closeBatchImport}
        resourceType={activeTab as 'vocabulary' | 'knowledge'}
        courseId={1} // 模拟课程ID
        onImportComplete={() => {
          refetch()
          notifications.show({
            title: '导入完成',
            message: '资源已成功导入',
            color: 'green',
          })
        }}
      />

      {/* 权限设置模态框 */}
      {selectedResource && (
        <PermissionSettingsModal
          opened={permissionOpened}
          onClose={closePermission}
          resourceId={selectedResource.id}
          resourceType={selectedResource.type}
          currentPermission={selectedResource.permission}
          onPermissionUpdate={newPermission => {
            // 更新本地状态
            refetch()
            notifications.show({
              title: '权限更新成功',
              message: `资源权限已更新为${newPermission}`,
              color: 'green',
            })
          }}
        />
      )}

      {/* 新建/编辑资源模态框 - 简化版本 */}
      <Modal
        opened={resourceModalOpened}
        onClose={closeResourceModal}
        title={selectedResource ? '编辑资源' : '新建资源'}
        size="md"
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text size="sm">资源创建和编辑功能将在后续版本中完善，目前支持批量导入功能。</Text>
          </Alert>
          <Group justify="flex-end">
            <Button variant="light" onClick={closeResourceModal}>
              关闭
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
