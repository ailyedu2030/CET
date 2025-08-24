/**
 * 规则管理页面 - 需求8：班级与课程规则管理
 * 实现规则配置、监控、效果分析功能
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
  Tabs,
  SimpleGrid,
  Textarea,
  Switch,
  JsonInput,
  RingProgress,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconEdit,
  IconPlus,
  IconRefresh,
  IconSettings,
  IconChartBar,
  IconShield,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconTrash,
  IconBulb,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/api/client'

// 规则配置接口
interface RuleConfiguration {
  id: number
  rule_name: string
  rule_type: string
  rule_category: string
  rule_config: Record<string, any>
  scope_type: string
  scope_value?: string
  is_enabled: boolean
  priority: number
  description?: string
  created_by: number
  created_at: string
  updated_at: string
}

// 规则统计接口
interface RuleStatistics {
  rule_id: number
  rule_name: string
  total_executions: number
  successful_executions: number
  violation_count: number
  exception_count: number
  compliance_rate: number
  effectiveness_score: number
  last_execution: string
  trend: string
}

// 规则模板接口
interface RuleTemplate {
  template_name: string
  template_type: string
  description: string
  default_config: Record<string, any>
  required_fields: string[]
  optional_fields: string[]
  examples: Array<{
    name: string
    config: Record<string, any>
  }>
}

export function RuleManagementPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('rules')
  const [selectedRule, setSelectedRule] = useState<RuleConfiguration | null>(null)
  const [page, setPage] = useState(1)

  const [ruleModalOpened, { open: openRuleModal, close: closeRuleModal }] = useDisclosure(false)

  // 规则表单
  const ruleForm = useForm({
    initialValues: {
      rule_name: '',
      rule_type: '',
      rule_category: '',
      rule_config: '{}',
      scope_type: 'global',
      scope_value: '',
      is_enabled: true,
      priority: 1,
      description: '',
    },
  })

  // 获取规则列表
  const {
    data: rulesData,
    isLoading: rulesLoading,
    error: rulesError,
  } = useQuery({
    queryKey: ['rules', page],
    queryFn: async () => {
      const response = await apiClient.get(`/courses/rules/?skip=${(page - 1) * 20}&limit=20`)
      return response.data as RuleConfiguration[]
    },
  })

  // 获取规则模板
  const { data: templatesData } = useQuery({
    queryKey: ['rule-templates'],
    queryFn: async () => {
      const response = await apiClient.get('/courses/rules/templates')
      return response.data as RuleTemplate[]
    },
  })

  // 获取规则统计
  const { data: statisticsData } = useQuery({
    queryKey: ['rule-statistics'],
    queryFn: async () => {
      const response = await apiClient.get('/courses/rules/statistics')
      return response.data as RuleStatistics[]
    },
  })

  // 创建/更新规则
  const ruleMutation = useMutation({
    mutationFn: async (data: typeof ruleForm.values) => {
      const payload = {
        ...data,
        rule_config: JSON.parse(data.rule_config),
      }

      if (selectedRule) {
        return await apiClient.put(`/courses/rules/${selectedRule.id}`, payload)
      } else {
        return await apiClient.post('/courses/rules/', payload)
      }
    },
    onSuccess: () => {
      notifications.show({
        title: '操作成功',
        message: selectedRule ? '规则更新成功' : '规则创建成功',
        color: 'green',
      })
      closeRuleModal()
      ruleForm.reset()
      setSelectedRule(null)
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '操作失败',
        message: error.response?.data?.detail || '操作失败',
        color: 'red',
      })
    },
  })

  // 删除规则
  const deleteRuleMutation = useMutation({
    mutationFn: async (ruleId: number) => {
      return await apiClient.delete(`/courses/rules/${ruleId}`)
    },
    onSuccess: () => {
      notifications.show({
        title: '删除成功',
        message: '规则删除成功',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '删除失败',
        message: error.response?.data?.detail || '规则删除失败',
        color: 'red',
      })
    },
  })

  // 切换规则状态
  const toggleRuleMutation = useMutation({
    mutationFn: async ({ ruleId, enabled }: { ruleId: number; enabled: boolean }) => {
      return await apiClient.put(`/courses/rules/${ruleId}`, { is_enabled: enabled })
    },
    onSuccess: () => {
      notifications.show({
        title: '状态更新成功',
        message: '规则状态已更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '状态更新失败',
        message: error.response?.data?.detail || '状态更新失败',
        color: 'red',
      })
    },
  })

  const handleCreateRule = () => {
    setSelectedRule(null)
    ruleForm.reset()
    openRuleModal()
  }

  const handleEditRule = (rule: RuleConfiguration) => {
    setSelectedRule(rule)
    ruleForm.setValues({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      rule_category: rule.rule_category,
      rule_config: JSON.stringify(rule.rule_config, null, 2),
      scope_type: rule.scope_type,
      scope_value: rule.scope_value || '',
      is_enabled: rule.is_enabled,
      priority: rule.priority,
      description: rule.description || '',
    })
    openRuleModal()
  }

  const handleUseTemplate = (template: RuleTemplate) => {
    ruleForm.setValues({
      rule_name: template.template_name,
      rule_type: template.template_type,
      rule_category: template.template_type,
      rule_config: JSON.stringify(template.default_config, null, 2),
      scope_type: 'global',
      scope_value: '',
      is_enabled: true,
      priority: 1,
      description: template.description,
    })
    openRuleModal()
  }

  const getRuleCategoryBadge = (category: string) => {
    const categoryMap: Record<string, { color: string; label: string }> = {
      class_binding: { color: 'blue', label: '班级绑定' },
      classroom_scheduling: { color: 'green', label: '教室排课' },
      teacher_workload: { color: 'orange', label: '教师工作量' },
      permission_control: { color: 'purple', label: '权限控制' },
    }
    const categoryInfo = categoryMap[category] || { color: 'gray', label: category }
    return <Badge color={categoryInfo.color}>{categoryInfo.label}</Badge>
  }

  const getPriorityBadge = (priority: number) => {
    if (priority >= 8) return <Badge color="red">高</Badge>
    if (priority >= 5) return <Badge color="yellow">中</Badge>
    return <Badge color="green">低</Badge>
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <IconCheck size={16} color="green" />
      case 'declining':
        return <IconX size={16} color="red" />
      default:
        return <IconAlertTriangle size={16} color="orange" />
    }
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>规则管理</Title>
          <Text c="dimmed" size="sm">
            配置和监控班级与课程规则，确保业务规范执行
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreateRule}>
            创建规则
          </Button>
          <Button leftSection={<IconRefresh size={16} />} variant="light">
            刷新
          </Button>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'rules')}>
        <Tabs.List>
          <Tabs.Tab value="rules" leftSection={<IconShield size={16} />}>
            规则配置
          </Tabs.Tab>
          <Tabs.Tab value="monitoring" leftSection={<IconChartBar size={16} />}>
            监控统计
          </Tabs.Tab>
          <Tabs.Tab value="templates" leftSection={<IconSettings size={16} />}>
            规则模板
          </Tabs.Tab>
          <Tabs.Tab value="optimization" leftSection={<IconBulb size={16} />}>
            优化建议
          </Tabs.Tab>
        </Tabs.List>

        {/* 规则配置标签页 */}
        <Tabs.Panel value="rules" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>规则信息</Table.Th>
                  <Table.Th>类别</Table.Th>
                  <Table.Th>优先级</Table.Th>
                  <Table.Th>适用范围</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>创建时间</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rulesData?.map(rule => (
                  <Table.Tr key={rule.id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text fw={500}>{rule.rule_name}</Text>
                        <Text size="sm" c="dimmed">
                          {rule.rule_type}
                        </Text>
                        {rule.description && (
                          <Text size="xs" c="dimmed">
                            {rule.description}
                          </Text>
                        )}
                      </Stack>
                    </Table.Td>
                    <Table.Td>{getRuleCategoryBadge(rule.rule_category)}</Table.Td>
                    <Table.Td>{getPriorityBadge(rule.priority)}</Table.Td>
                    <Table.Td>
                      <Stack gap="xs">
                        <Badge size="sm" variant="light">
                          {rule.scope_type}
                        </Badge>
                        {rule.scope_value && (
                          <Text size="xs" c="dimmed">
                            {rule.scope_value}
                          </Text>
                        )}
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Switch
                        checked={rule.is_enabled}
                        onChange={event =>
                          toggleRuleMutation.mutate({
                            ruleId: rule.id,
                            enabled: event.currentTarget.checked,
                          })
                        }
                        size="sm"
                      />
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{new Date(rule.created_at).toLocaleDateString('zh-CN')}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="编辑规则">
                          <ActionIcon variant="light" onClick={() => handleEditRule(rule)}>
                            <IconEdit size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="查看统计">
                          <ActionIcon variant="light" color="blue" onClick={() => {}}>
                            <IconChartBar size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="删除规则">
                          <ActionIcon
                            variant="light"
                            color="red"
                            onClick={() => deleteRuleMutation.mutate(rule.id)}
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

            {rulesData && rulesData.length > 20 && (
              <Group justify="center" p="md">
                <Pagination
                  value={page}
                  onChange={setPage}
                  total={Math.ceil(rulesData.length / 20)}
                />
              </Group>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 监控统计标签页 */}
        <Tabs.Panel value="monitoring" pt="md">
          <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} mb="lg">
            {statisticsData?.map(stat => (
              <Card key={stat.rule_id} withBorder>
                <Group justify="space-between" mb="md">
                  <div>
                    <Text fw={500} size="sm">
                      {stat.rule_name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      规则ID: {stat.rule_id}
                    </Text>
                  </div>
                  {getTrendIcon(stat.trend)}
                </Group>

                <Stack gap="sm">
                  <Group justify="space-between">
                    <Text size="sm">执行次数</Text>
                    <Text size="sm" fw={500}>
                      {stat.total_executions}
                    </Text>
                  </Group>

                  <Group justify="space-between">
                    <Text size="sm">合规率</Text>
                    <Group gap="xs">
                      <RingProgress
                        size={24}
                        thickness={3}
                        sections={[{ value: stat.compliance_rate * 100, color: 'green' }]}
                      />
                      <Text size="sm" fw={500}>
                        {(stat.compliance_rate * 100).toFixed(1)}%
                      </Text>
                    </Group>
                  </Group>

                  <Group justify="space-between">
                    <Text size="sm">违规次数</Text>
                    <Text size="sm" fw={500} c="red">
                      {stat.violation_count}
                    </Text>
                  </Group>

                  <Group justify="space-between">
                    <Text size="sm">效果评分</Text>
                    <Text size="sm" fw={500}>
                      {stat.effectiveness_score.toFixed(2)}
                    </Text>
                  </Group>

                  <Text size="xs" c="dimmed">
                    最后执行: {new Date(stat.last_execution).toLocaleString('zh-CN')}
                  </Text>
                </Stack>
              </Card>
            ))}
          </SimpleGrid>
        </Tabs.Panel>

        {/* 规则模板标签页 */}
        <Tabs.Panel value="templates" pt="md">
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            {templatesData?.map((template, index) => (
              <Card key={index} withBorder>
                <Stack>
                  <Group justify="space-between">
                    <div>
                      <Text fw={500}>{template.template_name}</Text>
                      <Badge size="sm" variant="light">
                        {template.template_type}
                      </Badge>
                    </div>
                    <Button size="xs" onClick={() => handleUseTemplate(template)}>
                      使用模板
                    </Button>
                  </Group>

                  <Text size="sm" c="dimmed">
                    {template.description}
                  </Text>

                  <div>
                    <Text size="sm" fw={500} mb="xs">
                      必需字段
                    </Text>
                    <Group gap="xs">
                      {template.required_fields.map(field => (
                        <Badge key={field} size="xs" color="red">
                          {field}
                        </Badge>
                      ))}
                    </Group>
                  </div>

                  <div>
                    <Text size="sm" fw={500} mb="xs">
                      可选字段
                    </Text>
                    <Group gap="xs">
                      {template.optional_fields.map(field => (
                        <Badge key={field} size="xs" color="blue">
                          {field}
                        </Badge>
                      ))}
                    </Group>
                  </div>

                  {template.examples.length > 0 && (
                    <div>
                      <Text size="sm" fw={500} mb="xs">
                        示例配置
                      </Text>
                      <Stack gap="xs">
                        {template.examples.map((example, exampleIndex) => (
                          <Paper key={exampleIndex} withBorder p="xs" bg="gray.0">
                            <Text size="xs" fw={500}>
                              {example.name}
                            </Text>
                            <Text size="xs" ff="monospace" c="dimmed">
                              {JSON.stringify(example.config)}
                            </Text>
                          </Paper>
                        ))}
                      </Stack>
                    </div>
                  )}
                </Stack>
              </Card>
            ))}
          </SimpleGrid>
        </Tabs.Panel>

        {/* 优化建议标签页 */}
        <Tabs.Panel value="optimization" pt="md">
          <Stack>
            <Alert icon={<IconBulb size={16} />} title="优化建议" color="blue">
              基于规则执行统计和效果分析，系统为您提供以下优化建议
            </Alert>

            <SimpleGrid cols={{ base: 1, lg: 2 }}>
              {statisticsData?.map(stat => (
                <Card key={stat.rule_id} withBorder>
                  <Stack>
                    <Group justify="space-between">
                      <Text fw={500}>{stat.rule_name}</Text>
                      <Badge color={stat.effectiveness_score > 0.8 ? 'green' : 'orange'}>
                        评分: {stat.effectiveness_score.toFixed(2)}
                      </Badge>
                    </Group>

                    <Stack gap="xs">
                      {stat.compliance_rate < 0.9 && (
                        <Alert color="orange">
                          <Text size="sm">
                            合规率偏低 ({(stat.compliance_rate * 100).toFixed(1)}
                            %)，建议检查规则配置
                          </Text>
                        </Alert>
                      )}

                      {stat.violation_count > 10 && (
                        <Alert color="red">
                          <Text size="sm">
                            违规次数较多 ({stat.violation_count} 次)，建议加强规则执行
                          </Text>
                        </Alert>
                      )}

                      {stat.total_executions < 5 && (
                        <Alert color="blue">
                          <Text size="sm">执行次数较少，建议增加规则触发场景</Text>
                        </Alert>
                      )}
                    </Stack>

                    <Button
                      size="xs"
                      variant="light"
                      onClick={() => {
                        setSelectedRule(rulesData?.find(rule => rule.id === stat.rule_id) || null)
                      }}
                    >
                      查看详细建议
                    </Button>
                  </Stack>
                </Card>
              ))}
            </SimpleGrid>
          </Stack>
        </Tabs.Panel>
      </Tabs>

      {/* 规则创建/编辑模态框 */}
      <Modal
        opened={ruleModalOpened}
        onClose={closeRuleModal}
        title={selectedRule ? '编辑规则' : '创建规则'}
        size="xl"
      >
        <form onSubmit={ruleForm.onSubmit(values => ruleMutation.mutate(values))}>
          <Stack>
            <Grid>
              <Grid.Col span={6}>
                <TextInput
                  label="规则名称"
                  placeholder="输入规则名称"
                  required
                  {...ruleForm.getInputProps('rule_name')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <Select
                  label="规则类型"
                  placeholder="选择规则类型"
                  required
                  data={[
                    { value: 'validation', label: '验证规则' },
                    { value: 'constraint', label: '约束规则' },
                    { value: 'business', label: '业务规则' },
                  ]}
                  {...ruleForm.getInputProps('rule_type')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <Select
                  label="规则分类"
                  placeholder="选择规则分类"
                  required
                  data={[
                    { value: 'class_binding', label: '班级绑定' },
                    { value: 'classroom_scheduling', label: '教室排课' },
                    { value: 'teacher_workload', label: '教师工作量' },
                    { value: 'permission_control', label: '权限控制' },
                  ]}
                  {...ruleForm.getInputProps('rule_category')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <Select
                  label="适用范围"
                  placeholder="选择适用范围"
                  required
                  data={[
                    { value: 'global', label: '全局' },
                    { value: 'class', label: '班级' },
                    { value: 'course', label: '课程' },
                    { value: 'user', label: '用户' },
                  ]}
                  {...ruleForm.getInputProps('scope_type')}
                />
              </Grid.Col>
            </Grid>

            <TextInput
              label="范围值"
              placeholder="输入具体的范围值（可选）"
              {...ruleForm.getInputProps('scope_value')}
            />

            <JsonInput
              label="规则配置"
              placeholder="输入JSON格式的规则配置"
              required
              rows={8}
              {...ruleForm.getInputProps('rule_config')}
            />

            <Textarea
              label="规则描述"
              placeholder="输入规则描述"
              rows={3}
              {...ruleForm.getInputProps('description')}
            />

            <Grid>
              <Grid.Col span={6}>
                <Select
                  label="优先级"
                  data={[
                    { value: '1', label: '1 - 最低' },
                    { value: '3', label: '3 - 低' },
                    { value: '5', label: '5 - 中等' },
                    { value: '7', label: '7 - 高' },
                    { value: '9', label: '9 - 最高' },
                  ]}
                  {...ruleForm.getInputProps('priority')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <Switch
                  label="启用规则"
                  {...ruleForm.getInputProps('is_enabled', { type: 'checkbox' })}
                />
              </Grid.Col>
            </Grid>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeRuleModal}>
                取消
              </Button>
              <Button type="submit" loading={ruleMutation.isPending}>
                {selectedRule ? '更新' : '创建'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 加载和错误状态 */}
      {rulesLoading && (
        <Paper withBorder p="xl" ta="center">
          <Text>正在加载规则信息...</Text>
        </Paper>
      )}

      {rulesError && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red">
          {rulesError.message}
        </Alert>
      )}
    </Container>
  )
}
