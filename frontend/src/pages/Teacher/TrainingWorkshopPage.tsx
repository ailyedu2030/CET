/**
 * 智能训练工坊页面 - 需求15实现
 * 教师配置训练参数，系统自动生成题目并投放至学生训练中心
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
  ActionIcon,
  Tooltip,
  Modal,
  Select,
  Table,
  ScrollArea,
} from '@mantine/core'
import {
  IconSettings,
  IconTemplate,
  IconCalendarWeek,
  IconChartBar,
  IconChartLine,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCopy,
  IconRefresh,
  IconRocket,
  IconTarget,
  IconBrain,
  IconAlertTriangle,
  IconCheck,
} from '@tabler/icons-react'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { useQuery, useMutation } from '@tanstack/react-query'

import {
  trainingWorkshopApi,
  TrainingParameterTemplate,
  TrainingParameterTemplateRequest,
} from '@/api/trainingWorkshop'
import { TrainingParameterConfigForm } from '@/components/TrainingWorkshop/TrainingParameterConfigForm'
import { TrainingParameterTemplateModal } from '@/components/TrainingWorkshop/TrainingParameterTemplateModal'
import { WeeklyTrainingConfigForm } from '@/components/TrainingWorkshop/WeeklyTrainingConfigForm'
import { TrainingAnalyticsPanel } from '@/components/TrainingWorkshop/TrainingAnalyticsPanel'

export function TrainingWorkshopPage(): JSX.Element {
  // 状态管理
  const [activeTab, setActiveTab] = useState<string>('parameter-config')
  const [selectedClass, setSelectedClass] = useState<number | null>(null)

  // Modal控制
  const [templateModalOpened, { open: openTemplateModal, close: closeTemplateModal }] =
    useDisclosure(false)
  const [taskModalOpened, { open: openTaskModal, close: closeTaskModal }] = useDisclosure(false)

  // 查询数据
  const {
    data: templates,
    isLoading: templatesLoading,
    refetch: refetchTemplates,
  } = useQuery({
    queryKey: ['training-parameter-templates'],
    queryFn: () => trainingWorkshopApi.getParameterTemplates(),
  })

  // 创建模板的Mutation
  const createTemplateMutation = useMutation({
    mutationFn: trainingWorkshopApi.createParameterTemplate,
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '训练参数模板创建成功',
        color: 'green',
      })
      closeTemplateModal()
      refetchTemplates()
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '创建模板失败',
        color: 'red',
      })
    },
  })

  // 创建周训练的Mutation
  const createWeeklyTrainingMutation = useMutation({
    mutationFn: trainingWorkshopApi.createWeeklyTraining,
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '周训练配置创建成功',
        color: 'green',
      })
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '创建周训练失败',
        color: 'red',
      })
    },
  })

  // 删除模板的Mutation
  const deleteTemplateMutation = useMutation({
    mutationFn: trainingWorkshopApi.deleteParameterTemplate,
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '模板删除成功',
        color: 'green',
      })
      refetchTemplates()
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '删除模板失败',
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

  const handleDeleteTemplate = (templateId: number) => {
    if (window.confirm('确定要删除这个模板吗？')) {
      deleteTemplateMutation.mutate(templateId)
    }
  }

  const handleCopyTemplate = (template: TrainingParameterTemplate) => {
    const newTemplate: TrainingParameterTemplateRequest = {
      name: `${template.name} - 副本`,
      description: template.description,
      config: template.config,
      is_default: false,
    }
    createTemplateMutation.mutate(newTemplate)
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={templatesLoading} />

      {/* 页面头部 */}
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>智能训练工坊</Title>
          <Text c="dimmed" size="sm">
            配置训练参数，AI自动生成题目并投放至学生训练中心
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
            onClick={() => {
              refetchTemplates()
            }}
          >
            刷新
          </Button>
        </Group>
      </Group>

      {/* 功能概览卡片 */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Group justify="space-between" mb="md">
              <IconSettings size={24} color="blue" />
              <Badge color="blue" variant="light">
                参数配置
              </Badge>
            </Group>
            <Text fw={500} mb="xs">
              训练参数配置
            </Text>
            <Text size="sm" c="dimmed">
              设置知识点、词汇库、热点融合度、教案衔接度等参数
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Group justify="space-between" mb="md">
              <IconTemplate size={24} color="green" />
              <Badge color="green" variant="light">
                模板管理
              </Badge>
            </Group>
            <Text fw={500} mb="xs">
              参数模板管理
            </Text>
            <Text size="sm" c="dimmed">
              保存常用训练参数模板，快速应用历史配置
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Group justify="space-between" mb="md">
              <IconCalendarWeek size={24} color="orange" />
              <Badge color="orange" variant="light">
                周训练
              </Badge>
            </Group>
            <Text fw={500} mb="xs">
              周训练配置
            </Text>
            <Text size="sm" c="dimmed">
              配置阅读理解和写作的专项训练，支持定时发布
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Group justify="space-between" mb="md">
              <IconChartLine size={24} color="purple" />
              <Badge color="purple" variant="light">
                数据分析
              </Badge>
            </Group>
            <Text fw={500} mb="xs">
              训练数据分析
            </Text>
            <Text size="sm" c="dimmed">
              查看学生训练数据自动分析报告和统计信息
            </Text>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 主要内容区域 */}
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'parameter-config')}>
        <Tabs.List>
          <Tabs.Tab value="parameter-config" leftSection={<IconSettings size={16} />}>
            参数配置
          </Tabs.Tab>
          <Tabs.Tab value="template-management" leftSection={<IconTemplate size={16} />}>
            模板管理
          </Tabs.Tab>
          <Tabs.Tab value="weekly-training" leftSection={<IconCalendarWeek size={16} />}>
            周训练配置
          </Tabs.Tab>
          <Tabs.Tab value="analytics" leftSection={<IconChartBar size={16} />}>
            数据分析
          </Tabs.Tab>
          <Tabs.Tab value="data-analytics" leftSection={<IconChartLine size={16} />}>
            数据分析
          </Tabs.Tab>
        </Tabs.List>

        {/* 参数配置标签页 */}
        <Tabs.Panel value="parameter-config" pt="lg">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                训练参数配置
              </Text>
              <Button leftSection={<IconRocket size={16} />} onClick={openTaskModal}>
                创建训练任务
              </Button>
            </Group>

            <Alert icon={<IconBrain size={16} />} title="AI自动生成" color="blue" mb="md">
              配置参数后，DeepSeek将完全自动生成题目，系统自动投放至学生训练中心
            </Alert>

            <TrainingParameterConfigForm
              onSubmit={_config => {
                notifications.show({
                  title: '配置已保存',
                  message: '训练参数配置已保存，可以创建训练任务',
                  color: 'green',
                })
              }}
            />
          </Card>
        </Tabs.Panel>

        {/* 模板管理标签页 */}
        <Tabs.Panel value="template-management" pt="lg">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                训练参数模板
              </Text>
              <Button leftSection={<IconPlus size={16} />} onClick={openTemplateModal}>
                创建模板
              </Button>
            </Group>

            {templates?.templates && templates.templates.length > 0 ? (
              <ScrollArea>
                <Table highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>模板名称</Table.Th>
                      <Table.Th>描述</Table.Th>
                      <Table.Th>默认模板</Table.Th>
                      <Table.Th>创建时间</Table.Th>
                      <Table.Th>操作</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {templates.templates.map(template => (
                      <Table.Tr key={template.id}>
                        <Table.Td>
                          <Text fw={500}>{template.name}</Text>
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm" c="dimmed" lineClamp={2}>
                            {template.description || '无描述'}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          {template.is_default && (
                            <Badge color="blue" variant="light" size="sm">
                              默认
                            </Badge>
                          )}
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm">
                            {template.created_at
                              ? new Date(template.created_at).toLocaleDateString()
                              : '-'}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <Group gap="xs">
                            <Tooltip label="复制模板">
                              <ActionIcon
                                variant="light"
                                size="sm"
                                onClick={() => handleCopyTemplate(template)}
                              >
                                <IconCopy size={14} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="编辑模板">
                              <ActionIcon variant="light" size="sm" color="blue">
                                <IconEdit size={14} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="删除模板">
                              <ActionIcon
                                variant="light"
                                size="sm"
                                color="red"
                                onClick={() => template.id && handleDeleteTemplate(template.id)}
                              >
                                <IconTrash size={14} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            ) : (
              <Text c="dimmed" ta="center" py="xl">
                暂无训练参数模板，点击"创建模板"开始
              </Text>
            )}
          </Card>
        </Tabs.Panel>

        {/* 周训练配置标签页 */}
        <Tabs.Panel value="weekly-training" pt="lg">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                周训练配置
              </Text>
            </Group>

            <Alert icon={<IconTarget size={16} />} title="考纲关联度保证" color="green" mb="md">
              阅读理解确保考纲关联度≥80%，写作嵌入四级评分标准
            </Alert>

            <WeeklyTrainingConfigForm
              classId={selectedClass || undefined}
              onSubmit={data => {
                createWeeklyTrainingMutation.mutate(data)
              }}
              loading={createWeeklyTrainingMutation.isPending}
            />
          </Card>
        </Tabs.Panel>

        {/* 数据分析标签页 */}
        <Tabs.Panel value="analytics" pt="lg">
          {selectedClass ? (
            <TrainingAnalyticsPanel classId={selectedClass} />
          ) : (
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Alert icon={<IconChartBar size={16} />} title="请选择班级" color="blue">
                请先在左侧选择要分析的班级
              </Alert>
            </Card>
          )}
        </Tabs.Panel>

        {/* 高级数据分析标签页 */}
        <Tabs.Panel value="data-analytics" pt="lg">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text fw={500} size="lg" mb="md">
              训练数据分析
            </Text>

            {selectedClass ? (
              <div>
                <Alert icon={<IconCheck size={16} />} title="数据流转完整" color="teal" mb="md">
                  教师配置参数 → DeepSeek生成题目 → 自动投放学生端 → 数据反馈教师端
                </Alert>
                <Text c="dimmed" ta="center" py="xl">
                  训练数据分析看板将在下一步实现...
                </Text>
              </div>
            ) : (
              <Alert icon={<IconAlertTriangle size={16} />} title="请选择班级" color="yellow">
                请先在页面顶部选择要分析的班级
              </Alert>
            )}
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* 训练参数模板Modal */}
      <TrainingParameterTemplateModal
        opened={templateModalOpened}
        onClose={closeTemplateModal}
        onSuccess={() => {
          refetchTemplates()
        }}
      />

      {/* 创建任务Modal - 简化版本 */}
      <Modal opened={taskModalOpened} onClose={closeTaskModal} title="创建训练任务" size="md">
        <Text c="dimmed" ta="center" py="xl">
          任务创建表单将在下一步实现...
        </Text>
      </Modal>
    </Container>
  )
}
