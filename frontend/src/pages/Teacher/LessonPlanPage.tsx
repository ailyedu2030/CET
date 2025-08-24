/**
 * 教案构建页面 - 需求13实现
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
  Accordion,
  Divider,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconPlus,
  IconEdit,
  IconTrash,
  IconDownload,
  IconShare,
  IconBook,
  IconFileText,
  IconBrain,
  IconUsers,
  IconTemplate,
  IconHistory,
  IconEye,
  IconCopy,
  IconSettings,
  IconStar,
  IconCheck,
} from '@tabler/icons-react'
import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

// 教案相关类型定义
interface LessonPlan {
  id: number
  title: string
  syllabusId: number
  syllabusTitle: string
  chapterNumber: number
  chapterTitle: string
  objectives: string[]
  content: {
    introduction: string
    mainContent: string[]
    activities: string[]
    summary: string
  }
  duration: number // 课时
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  resources: string[]
  assessment: string
  homework: string
  status: 'draft' | 'reviewing' | 'approved' | 'published'
  templateId?: number
  templateName?: string
  createdBy: number
  createdAt: string
  updatedAt: string
  version: number
  collaborators: Array<{
    id: number
    name: string
    role: string
    lastActive: string
  }>
}

interface LessonTemplate {
  id: number
  name: string
  description: string
  category: string
  structure: {
    sections: Array<{
      name: string
      duration: number
      type: string
    }>
  }
  isPublic: boolean
  usageCount: number
  rating: number
  createdBy: string
  createdAt: string
}

interface Syllabus {
  id: number
  title: string
  courseId: number
  courseName: string
  status: string
  chapters: Array<{
    id: number
    title: string
    order: number
    duration: number
    hasLessonPlan: boolean
  }>
}

export function LessonPlanPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('plans')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterSyllabus, setFilterSyllabus] = useState<string>('')
  const [selectedPlan, setSelectedPlan] = useState<LessonPlan | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<LessonTemplate | null>(null)
  const [_selectedSyllabus, setSelectedSyllabus] = useState<Syllabus | null>(null)

  // 模态框状态
  const [planModalOpened, { open: openPlanModal, close: closePlanModal }] = useDisclosure(false)
  const [templateModalOpened, { open: openTemplateModal, close: closeTemplateModal }] =
    useDisclosure(false)
  const [generateModalOpened, { open: openGenerateModal, close: closeGenerateModal }] =
    useDisclosure(false)
  const [collaborateModalOpened, { open: openCollaborateModal, close: closeCollaborateModal }] =
    useDisclosure(false)

  // 模拟数据查询 - 教案列表
  const {
    data: lessonPlansData,
    isLoading: plansLoading,
    refetch: refetchPlans,
  } = useQuery({
    queryKey: ['lesson-plans', searchQuery, filterStatus, filterSyllabus],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockData: LessonPlan[] = [
        {
          id: 1,
          title: '英语语法基础 - 时态概述',
          syllabusId: 1,
          syllabusTitle: '大学英语四级语法大纲',
          chapterNumber: 1,
          chapterTitle: '时态系统',
          objectives: [
            '掌握英语基本时态的概念',
            '理解时态在句子中的作用',
            '能够正确使用一般现在时和一般过去时',
          ],
          content: {
            introduction: '本节课将介绍英语时态系统的基本概念...',
            mainContent: [
              '时态的定义和分类',
              '一般现在时的用法和结构',
              '一般过去时的用法和结构',
              '时态选择的原则',
            ],
            activities: ['时态识别练习', '句子转换练习', '情景对话练习'],
            summary: '通过本节课的学习，学生应该能够...',
          },
          duration: 90,
          difficulty: 'beginner',
          resources: ['PPT课件', '练习册第1-5页', '在线语法测试'],
          assessment: '课堂练习 + 小测验',
          homework: '完成练习册第6-10页',
          status: 'approved',
          templateId: 1,
          templateName: '语法教学模板',
          createdBy: 1,
          createdAt: '2024-01-15T10:00:00Z',
          updatedAt: '2024-01-20T14:30:00Z',
          version: 3,
          collaborators: [
            { id: 1, name: '张老师', role: '主讲', lastActive: '2024-01-20T14:30:00Z' },
            { id: 2, name: '李老师', role: '协作', lastActive: '2024-01-19T16:20:00Z' },
          ],
        },
        {
          id: 2,
          title: '阅读理解技巧训练',
          syllabusId: 2,
          syllabusTitle: '大学英语四级阅读大纲',
          chapterNumber: 3,
          chapterTitle: '快速阅读技巧',
          objectives: ['掌握快速阅读的基本技巧', '提高阅读理解的准确率', '培养良好的阅读习惯'],
          content: {
            introduction: '快速阅读是英语学习的重要技能...',
            mainContent: ['扫读技巧(Scanning)', '略读技巧(Skimming)', '精读方法', '阅读策略选择'],
            activities: ['限时阅读练习', '关键词定位训练', '文章结构分析'],
            summary: '掌握不同的阅读技巧，提高阅读效率',
          },
          duration: 120,
          difficulty: 'intermediate',
          resources: ['阅读材料包', '计时器', '理解测试题'],
          assessment: '阅读理解测试',
          homework: '完成3篇阅读理解练习',
          status: 'draft',
          createdBy: 1,
          createdAt: '2024-01-18T09:00:00Z',
          updatedAt: '2024-01-18T09:00:00Z',
          version: 1,
          collaborators: [
            { id: 1, name: '张老师', role: '主讲', lastActive: '2024-01-18T09:00:00Z' },
          ],
        },
      ]

      return mockData.filter(
        item =>
          (searchQuery === '' || item.title.toLowerCase().includes(searchQuery.toLowerCase())) &&
          (filterStatus === '' || item.status === filterStatus) &&
          (filterSyllabus === '' || item.syllabusId.toString() === filterSyllabus)
      )
    },
  })

  // 模拟数据查询 - 教案模板
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['lesson-templates'],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 300))

      const mockTemplates: LessonTemplate[] = [
        {
          id: 1,
          name: '语法教学模板',
          description: '适用于语法知识点教学的标准模板',
          category: '语法教学',
          structure: {
            sections: [
              { name: '导入', duration: 10, type: 'introduction' },
              { name: '知识讲解', duration: 30, type: 'content' },
              { name: '练习巩固', duration: 25, type: 'practice' },
              { name: '总结回顾', duration: 15, type: 'summary' },
            ],
          },
          isPublic: true,
          usageCount: 45,
          rating: 4.8,
          createdBy: '系统模板',
          createdAt: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          name: '阅读理解模板',
          description: '专门用于阅读理解教学的模板',
          category: '阅读教学',
          structure: {
            sections: [
              { name: '预读准备', duration: 15, type: 'preparation' },
              { name: '文章阅读', duration: 40, type: 'reading' },
              { name: '理解检测', duration: 20, type: 'comprehension' },
              { name: '技巧总结', duration: 15, type: 'summary' },
            ],
          },
          isPublic: true,
          usageCount: 32,
          rating: 4.6,
          createdBy: '李老师',
          createdAt: '2024-01-10T00:00:00Z',
        },
      ]

      return mockTemplates
    },
  })

  // 模拟数据查询 - 教学大纲
  const { data: syllabiData, isLoading: syllabiLoading } = useQuery({
    queryKey: ['syllabi'],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 200))

      const mockSyllabi: Syllabus[] = [
        {
          id: 1,
          title: '大学英语四级语法大纲',
          courseId: 1,
          courseName: '大学英语四级',
          status: 'approved',
          chapters: [
            { id: 1, title: '时态系统', order: 1, duration: 180, hasLessonPlan: true },
            { id: 2, title: '语态变换', order: 2, duration: 120, hasLessonPlan: false },
            { id: 3, title: '从句结构', order: 3, duration: 240, hasLessonPlan: false },
          ],
        },
        {
          id: 2,
          title: '大学英语四级阅读大纲',
          courseId: 1,
          courseName: '大学英语四级',
          status: 'approved',
          chapters: [
            { id: 4, title: '阅读策略', order: 1, duration: 90, hasLessonPlan: false },
            { id: 5, title: '快速阅读技巧', order: 2, duration: 120, hasLessonPlan: true },
            { id: 6, title: '深度理解', order: 3, duration: 150, hasLessonPlan: false },
          ],
        },
      ]

      return mockSyllabi
    },
  })

  const getStatusBadge = (status: string) => {
    const config = {
      draft: { label: '草稿', color: 'gray' },
      reviewing: { label: '审核中', color: 'blue' },
      approved: { label: '已批准', color: 'green' },
      published: { label: '已发布', color: 'teal' },
    }
    const { label, color } = config[status as keyof typeof config]
    return (
      <Badge color={color} size="sm">
        {label}
      </Badge>
    )
  }

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

  const handleCreatePlan = useCallback(() => {
    setSelectedPlan(null)
    openPlanModal()
  }, [openPlanModal])

  const handleEditPlan = useCallback(
    (plan: LessonPlan) => {
      setSelectedPlan(plan)
      openPlanModal()
    },
    [openPlanModal]
  )

  const handleGenerateFromSyllabus = useCallback(
    (syllabus: Syllabus) => {
      setSelectedSyllabus(syllabus)
      openGenerateModal()
    },
    [openGenerateModal]
  )

  const handleCollaborate = useCallback(
    (plan: LessonPlan) => {
      setSelectedPlan(plan)
      openCollaborateModal()
    },
    [openCollaborateModal]
  )

  const handleGenerateLessonPlan = useCallback(async () => {
    try {
      // 模拟AI生成教案
      await new Promise(resolve => setTimeout(resolve, 3000))

      notifications.show({
        title: '教案生成完成',
        message: '已成功生成 3 个章节的教案',
        color: 'green',
      })

      refetchPlans()
      closeGenerateModal()
    } catch (error) {
      notifications.show({
        title: '教案生成失败',
        message: '请稍后重试',
        color: 'red',
      })
    }
  }, [refetchPlans, closeGenerateModal])

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>教案构建管理</Title>
          <Text c="dimmed" mt="xs">
            智能生成教案，支持协同编辑和模板管理
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconBrain size={16} />} variant="light" onClick={openGenerateModal}>
            AI生成教案
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreatePlan}>
            新建教案
          </Button>
        </Group>
      </Group>

      {/* 标签页 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'plans')} mb="xl">
        <Tabs.List>
          <Tabs.Tab value="plans" leftSection={<IconFileText size={16} />}>
            教案管理
          </Tabs.Tab>
          <Tabs.Tab value="templates" leftSection={<IconTemplate size={16} />}>
            模板库
          </Tabs.Tab>
          <Tabs.Tab value="syllabi" leftSection={<IconBook size={16} />}>
            大纲章节
          </Tabs.Tab>
          <Tabs.Tab value="collaboration" leftSection={<IconUsers size={16} />}>
            协作管理
          </Tabs.Tab>
        </Tabs.List>

        {/* 教案管理标签页 */}
        <Tabs.Panel value="plans">
          <Alert color="blue" mb="md">
            <Text size="sm">管理教案内容，支持AI智能生成、协同编辑和版本控制</Text>
          </Alert>

          {/* 搜索和筛选 */}
          <Paper withBorder p="md" mb="xl">
            <Group>
              <TextInput
                placeholder="搜索教案..."
                leftSection={<IconFileText size={16} />}
                value={searchQuery}
                onChange={event => setSearchQuery(event.currentTarget.value)}
                style={{ flex: 1 }}
              />
              <Select
                placeholder="状态筛选"
                value={filterStatus}
                onChange={value => setFilterStatus(value || '')}
                data={[
                  { value: '', label: '全部状态' },
                  { value: 'draft', label: '草稿' },
                  { value: 'reviewing', label: '审核中' },
                  { value: 'approved', label: '已批准' },
                  { value: 'published', label: '已发布' },
                ]}
                clearable
                style={{ minWidth: 120 }}
              />
              <Select
                placeholder="大纲筛选"
                value={filterSyllabus}
                onChange={value => setFilterSyllabus(value || '')}
                data={syllabiData?.map(s => ({ value: s.id.toString(), label: s.title })) || []}
                clearable
                style={{ minWidth: 200 }}
              />
            </Group>
          </Paper>

          {/* 教案列表 */}
          <Paper withBorder>
            {plansLoading ? (
              <Stack align="center" p="xl">
                <Progress value={50} size="sm" style={{ width: '100%' }} />
                <Text c="dimmed">加载教案中...</Text>
              </Stack>
            ) : lessonPlansData && lessonPlansData.length > 0 ? (
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>教案信息</Table.Th>
                    <Table.Th>所属大纲</Table.Th>
                    <Table.Th>状态</Table.Th>
                    <Table.Th>协作者</Table.Th>
                    <Table.Th>更新时间</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {lessonPlansData.map(plan => (
                    <Table.Tr key={plan.id}>
                      <Table.Td>
                        <div>
                          <Group gap="xs" mb="xs">
                            <Text fw={500} size="sm">
                              {plan.title}
                            </Text>
                            {plan.templateName && (
                              <Badge
                                variant="light"
                                size="xs"
                                leftSection={<IconTemplate size={10} />}
                              >
                                {plan.templateName}
                              </Badge>
                            )}
                          </Group>
                          <Text size="xs" c="dimmed">
                            第{plan.chapterNumber}章 · {plan.duration}分钟 ·{' '}
                            {getDifficultyBadge(plan.difficulty)}
                          </Text>
                          <Group gap="xs" mt="xs">
                            <Text size="xs" c="dimmed">
                              目标: {plan.objectives.length}个
                            </Text>
                            <Text size="xs" c="dimmed">
                              资源: {plan.resources.length}个
                            </Text>
                            <Text size="xs" c="dimmed">
                              v{plan.version}
                            </Text>
                          </Group>
                        </div>
                      </Table.Td>
                      <Table.Td>
                        <div>
                          <Text size="sm" fw={500}>
                            {plan.syllabusTitle}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {plan.chapterTitle}
                          </Text>
                        </div>
                      </Table.Td>
                      <Table.Td>{getStatusBadge(plan.status)}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          {plan.collaborators.slice(0, 2).map((collaborator, index) => (
                            <Tooltip
                              key={index}
                              label={`${collaborator.name} (${collaborator.role})`}
                            >
                              <Badge variant="light" size="xs">
                                {collaborator.name}
                              </Badge>
                            </Tooltip>
                          ))}
                          {plan.collaborators.length > 2 && (
                            <Badge variant="light" size="xs">
                              +{plan.collaborators.length - 2}
                            </Badge>
                          )}
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {new Date(plan.updatedAt).toLocaleDateString('zh-CN')}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {new Date(plan.updatedAt).toLocaleTimeString('zh-CN')}
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
                              onClick={() => handleEditPlan(plan)}
                            >
                              <IconEdit size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="协作">
                            <ActionIcon
                              variant="light"
                              size="sm"
                              color="green"
                              onClick={() => handleCollaborate(plan)}
                            >
                              <IconUsers size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Menu shadow="md" width={200}>
                            <Menu.Target>
                              <ActionIcon variant="light" size="sm">
                                <IconSettings size={14} />
                              </ActionIcon>
                            </Menu.Target>
                            <Menu.Dropdown>
                              <Menu.Item leftSection={<IconHistory size={14} />}>
                                版本历史
                              </Menu.Item>
                              <Menu.Item leftSection={<IconCopy size={14} />}>复制教案</Menu.Item>
                              <Menu.Item leftSection={<IconShare size={14} />}>
                                分享到资源库
                              </Menu.Item>
                              <Menu.Item leftSection={<IconDownload size={14} />}>
                                导出教案
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
                <Text c="dimmed">暂无教案数据</Text>
                <Button
                  variant="light"
                  leftSection={<IconPlus size={16} />}
                  onClick={handleCreatePlan}
                >
                  创建第一个教案
                </Button>
              </Stack>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 模板库标签页 */}
        <Tabs.Panel value="templates">
          <Alert color="orange" mb="md">
            <Text size="sm">管理教案模板，提高教案创建效率</Text>
          </Alert>

          <Group justify="space-between" mb="md">
            <Text fw={500}>教案模板库</Text>
            <Button
              leftSection={<IconPlus size={16} />}
              size="sm"
              onClick={() => {
                setSelectedTemplate(null)
                openTemplateModal()
              }}
            >
              创建模板
            </Button>
          </Group>

          <Paper withBorder>
            {templatesLoading ? (
              <Stack align="center" p="xl">
                <Progress value={50} size="sm" style={{ width: '100%' }} />
                <Text c="dimmed">加载模板中...</Text>
              </Stack>
            ) : templatesData && templatesData.length > 0 ? (
              <div style={{ padding: '1rem' }}>
                <Group>
                  {templatesData.map(template => (
                    <Card key={template.id} withBorder style={{ width: 300 }}>
                      <Group justify="space-between" mb="md">
                        <Badge color="blue" variant="light">
                          {template.category}
                        </Badge>
                        <Group gap="xs">
                          <IconStar size={14} color="gold" />
                          <Text size="xs">{template.rating}</Text>
                        </Group>
                      </Group>

                      <Text fw={500} mb="xs">
                        {template.name}
                      </Text>
                      <Text size="sm" c="dimmed" mb="md">
                        {template.description}
                      </Text>

                      <Stack gap="xs" mb="md">
                        <Text size="xs" fw={500}>
                          模板结构:
                        </Text>
                        {template.structure.sections.map((section, index) => (
                          <Group key={index} justify="space-between">
                            <Text size="xs">{section.name}</Text>
                            <Badge size="xs" variant="light">
                              {section.duration}分钟
                            </Badge>
                          </Group>
                        ))}
                      </Stack>

                      <Group justify="space-between" align="center">
                        <div>
                          <Text size="xs" c="dimmed">
                            使用次数: {template.usageCount}
                          </Text>
                          <Text size="xs" c="dimmed">
                            创建者: {template.createdBy}
                          </Text>
                        </div>
                        <Group gap="xs">
                          <Tooltip label="使用模板">
                            <ActionIcon variant="light" size="sm" color="blue">
                              <IconTemplate size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="编辑模板">
                            <ActionIcon
                              variant="light"
                              size="sm"
                              onClick={() => {
                                setSelectedTemplate(template)
                                openTemplateModal()
                              }}
                            >
                              <IconEdit size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Group>
                    </Card>
                  ))}
                </Group>
              </div>
            ) : (
              <Stack align="center" p="xl">
                <Text c="dimmed">暂无模板</Text>
                <Button
                  variant="light"
                  leftSection={<IconPlus size={16} />}
                  onClick={() => {
                    setSelectedTemplate(null)
                    openTemplateModal()
                  }}
                >
                  创建第一个模板
                </Button>
              </Stack>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 大纲章节标签页 */}
        <Tabs.Panel value="syllabi">
          <Alert color="green" mb="md">
            <Text size="sm">基于已审核的教学大纲生成教案</Text>
          </Alert>

          <Paper withBorder>
            {syllabiLoading ? (
              <Stack align="center" p="xl">
                <Progress value={50} size="sm" style={{ width: '100%' }} />
                <Text c="dimmed">加载大纲中...</Text>
              </Stack>
            ) : syllabiData && syllabiData.length > 0 ? (
              <Accordion>
                {syllabiData.map(syllabus => (
                  <Accordion.Item key={syllabus.id} value={syllabus.id.toString()}>
                    <Accordion.Control>
                      <Group justify="space-between">
                        <div>
                          <Text fw={500}>{syllabus.title}</Text>
                          <Text size="sm" c="dimmed">
                            {syllabus.courseName}
                          </Text>
                        </div>
                        <Group gap="xs">
                          <Badge color="green">{syllabus.status}</Badge>
                          <Badge variant="light">{syllabus.chapters.length} 章节</Badge>
                        </Group>
                      </Group>
                    </Accordion.Control>
                    <Accordion.Panel>
                      <Stack gap="md">
                        {syllabus.chapters.map(chapter => (
                          <Card key={chapter.id} withBorder>
                            <Group justify="space-between">
                              <div>
                                <Text fw={500}>
                                  第{chapter.order}章: {chapter.title}
                                </Text>
                                <Text size="sm" c="dimmed">
                                  预计课时: {chapter.duration}分钟
                                </Text>
                              </div>
                              <Group gap="xs">
                                {chapter.hasLessonPlan ? (
                                  <Badge color="green" leftSection={<IconCheck size={12} />}>
                                    已有教案
                                  </Badge>
                                ) : (
                                  <Badge color="gray">待生成</Badge>
                                )}
                                <Button
                                  size="xs"
                                  variant="light"
                                  leftSection={<IconBrain size={12} />}
                                  onClick={() => handleGenerateFromSyllabus(syllabus)}
                                  disabled={chapter.hasLessonPlan}
                                >
                                  {chapter.hasLessonPlan ? '已生成' : 'AI生成'}
                                </Button>
                              </Group>
                            </Group>
                          </Card>
                        ))}

                        <Divider />

                        <Group justify="center">
                          <Button
                            leftSection={<IconBrain size={16} />}
                            onClick={() => handleGenerateFromSyllabus(syllabus)}
                          >
                            批量生成所有章节教案
                          </Button>
                        </Group>
                      </Stack>
                    </Accordion.Panel>
                  </Accordion.Item>
                ))}
              </Accordion>
            ) : (
              <Stack align="center" p="xl">
                <Text c="dimmed">暂无已审核的教学大纲</Text>
                <Text size="sm" c="dimmed">
                  请先在大纲生成页面创建并审核教学大纲
                </Text>
              </Stack>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 协作管理标签页 */}
        <Tabs.Panel value="collaboration">
          <Alert color="purple" mb="md">
            <Text size="sm">管理教案协作，支持多教师实时编辑</Text>
          </Alert>

          <Paper withBorder p="md">
            <Stack align="center" p="xl">
              <IconUsers size={48} color="var(--mantine-color-purple-6)" />
              <Text size="lg" fw={500}>
                协作管理功能
              </Text>
              <Text c="dimmed" ta="center">
                支持多教师实时协作编辑教案，自动冲突解决和版本管理
              </Text>
              <Button leftSection={<IconUsers size={16} />}>查看协作会话</Button>
            </Stack>
          </Paper>
        </Tabs.Panel>
      </Tabs>

      {/* AI生成教案模态框 */}
      <Modal
        opened={generateModalOpened}
        onClose={closeGenerateModal}
        title="AI智能生成教案"
        size="lg"
        centered
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text size="sm">基于教学大纲、热点资源和知识点库，AI将为您智能生成高质量教案</Text>
          </Alert>

          <Select
            label="选择教学大纲"
            placeholder="选择要生成教案的大纲"
            data={syllabiData?.map(s => ({ value: s.id.toString(), label: s.title })) || []}
            required
          />

          <Group grow>
            <Select
              label="生成模式"
              placeholder="选择生成模式"
              data={[
                { value: 'all', label: '全部章节' },
                { value: 'missing', label: '仅缺失章节' },
                { value: 'selected', label: '指定章节' },
              ]}
              defaultValue="missing"
            />
            <Select
              label="教案模板"
              placeholder="选择模板（可选）"
              data={templatesData?.map(t => ({ value: t.id.toString(), label: t.name })) || []}
            />
          </Group>

          <Switch label="融入热点资源" description="自动融入相关的时事热点内容" defaultChecked />

          <Switch label="个性化调整" description="根据班级学情进行个性化调整" defaultChecked />

          <Group justify="flex-end">
            <Button variant="light" onClick={closeGenerateModal}>
              取消
            </Button>
            <Button onClick={handleGenerateLessonPlan}>开始生成</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 教案编辑模态框 */}
      <Modal
        opened={planModalOpened}
        onClose={closePlanModal}
        title={selectedPlan ? '编辑教案' : '新建教案'}
        size="xl"
      >
        <Stack gap="md">
          <Group grow>
            <TextInput label="教案标题" placeholder="输入教案标题" required />
            <Select
              label="所属大纲"
              placeholder="选择教学大纲"
              data={syllabiData?.map(s => ({ value: s.id.toString(), label: s.title })) || []}
              required
            />
          </Group>

          <Group grow>
            <NumberInput label="课时时长" placeholder="分钟" min={30} max={180} defaultValue={90} />
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

          <Textarea label="教学目标" placeholder="输入教学目标，每行一个" minRows={3} required />

          <Textarea label="教学内容" placeholder="输入主要教学内容" minRows={5} required />

          <Group grow>
            <Textarea label="教学活动" placeholder="设计的教学活动" minRows={3} />
            <Textarea label="教学资源" placeholder="所需教学资源" minRows={3} />
          </Group>

          <Group grow>
            <Textarea label="评估方式" placeholder="学习效果评估方式" minRows={2} />
            <Textarea label="课后作业" placeholder="布置的课后作业" minRows={2} />
          </Group>

          <Group justify="flex-end">
            <Button variant="light" onClick={closePlanModal}>
              取消
            </Button>
            <Button onClick={closePlanModal}>{selectedPlan ? '更新' : '创建'}</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 模板编辑模态框 */}
      <Modal
        opened={templateModalOpened}
        onClose={closeTemplateModal}
        title={selectedTemplate ? '编辑模板' : '创建模板'}
        size="lg"
      >
        <Stack gap="md">
          <Group grow>
            <TextInput label="模板名称" placeholder="输入模板名称" required />
            <Select
              label="模板分类"
              placeholder="选择分类"
              data={[
                { value: 'grammar', label: '语法教学' },
                { value: 'reading', label: '阅读教学' },
                { value: 'writing', label: '写作教学' },
                { value: 'listening', label: '听力教学' },
                { value: 'speaking', label: '口语教学' },
              ]}
              required
            />
          </Group>

          <Textarea label="模板描述" placeholder="描述模板的用途和特点" minRows={3} required />

          <Switch label="公开模板" description="允许其他教师使用此模板" />

          <Group justify="flex-end">
            <Button variant="light" onClick={closeTemplateModal}>
              取消
            </Button>
            <Button onClick={closeTemplateModal}>{selectedTemplate ? '更新' : '创建'}</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 协作管理模态框 */}
      <Modal
        opened={collaborateModalOpened}
        onClose={closeCollaborateModal}
        title="协作管理"
        size="md"
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text size="sm">邀请其他教师协作编辑此教案</Text>
          </Alert>

          <TextInput label="邀请教师" placeholder="输入教师邮箱或姓名" />

          <Select
            label="协作权限"
            placeholder="选择权限级别"
            data={[
              { value: 'edit', label: '编辑权限' },
              { value: 'comment', label: '评论权限' },
              { value: 'view', label: '查看权限' },
            ]}
            defaultValue="edit"
          />

          <Group justify="flex-end">
            <Button variant="light" onClick={closeCollaborateModal}>
              取消
            </Button>
            <Button onClick={closeCollaborateModal}>发送邀请</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
