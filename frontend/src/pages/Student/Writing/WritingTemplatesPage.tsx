/**
 * 需求26：英语四级写作标准库 - 写作模板页面
 * 
 * 实现写作模板库的浏览和使用功能
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
  Stack,
  Select,
  TextInput,
  Paper,
  Divider,
  Modal,
  Tabs,
  Code,
  List,
  Alert,
  LoadingOverlay,
  ActionIcon,
  Tooltip,
  Pagination,
} from '@mantine/core'
import {
  IconTemplate,
  IconSearch,
  IconFilter,
  IconEye,
  IconCopy,
  IconStar,
  IconBook,
  IconBulb,
  IconCheck,
  IconFileText,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { useDisclosure } from '@mantine/hooks'

import { writingApi, WritingType, WritingDifficulty, WritingTemplate } from '@/api/writing'

export function WritingTemplatesPage(): JSX.Element {
  // 状态管理
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedTemplate, setSelectedTemplate] = useState<WritingTemplate | null>(null)
  
  const [templateModalOpened, { open: openTemplateModal, close: closeTemplateModal }] = useDisclosure(false)

  const pageSize = 12

  // 查询写作模板列表
  const {
    data: templatesData,
    isLoading: templatesLoading,
  } = useQuery({
    queryKey: ['writing-templates', selectedType, selectedDifficulty, currentPage],
    queryFn: () => writingApi.getTemplates({
      skip: (currentPage - 1) * pageSize,
      limit: pageSize,
      writing_type: selectedType === 'all' ? undefined : selectedType as WritingType,
      difficulty: selectedDifficulty === 'all' ? undefined : selectedDifficulty as WritingDifficulty,
    }),
  })

  // 过滤模板
  const filteredTemplates = templatesData?.data?.filter(template =>
    searchQuery === '' || 
    template.template_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.usage_instructions?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  // 查看模板详情
  const viewTemplate = (template: WritingTemplate) => {
    setSelectedTemplate(template)
    openTemplateModal()
  }

  // 复制模板内容
  const copyTemplate = (template: WritingTemplate) => {
    const content = `
模板名称: ${template.template_name}
写作类型: ${template.writing_type}
难度等级: ${template.difficulty}

开头句式:
${template.opening_sentences?.map(sentence => `• ${sentence}`).join('\n') || ''}

过渡词汇:
${template.transition_phrases?.map(phrase => `• ${phrase}`).join('\n') || ''}

结尾句式:
${template.conclusion_sentences?.map(sentence => `• ${sentence}`).join('\n') || ''}

关键短语:
${template.key_phrases?.map(phrase => `• ${phrase}`).join('\n') || ''}
    `.trim()

    navigator.clipboard.writeText(content).then(() => {
      notifications.show({
        title: '复制成功',
        message: '模板内容已复制到剪贴板',
        color: 'green',
        icon: <IconCheck size={16} />,
      })
    })
  }

  // 获取写作类型标签
  const getWritingTypeLabel = (type: WritingType) => {
    const labels = {
      [WritingType.ARGUMENTATIVE]: '议论文',
      [WritingType.NARRATIVE]: '记叙文',
      [WritingType.DESCRIPTIVE]: '描述文',
      [WritingType.EXPOSITORY]: '说明文',
      [WritingType.PRACTICAL]: '应用文',
    }
    return labels[type] || type
  }

  // 获取难度标签
  const getDifficultyLabel = (difficulty: WritingDifficulty) => {
    const labels = {
      [WritingDifficulty.BASIC]: '基础级',
      [WritingDifficulty.INTERMEDIATE]: '中级',
      [WritingDifficulty.ADVANCED]: '高级',
      [WritingDifficulty.EXPERT]: '专家级',
    }
    return labels[difficulty] || difficulty
  }

  // 获取难度颜色
  const getDifficultyColor = (difficulty: WritingDifficulty) => {
    const colors = {
      [WritingDifficulty.BASIC]: 'green',
      [WritingDifficulty.INTERMEDIATE]: 'blue',
      [WritingDifficulty.ADVANCED]: 'orange',
      [WritingDifficulty.EXPERT]: 'red',
    }
    return colors[difficulty] || 'gray'
  }

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={templatesLoading} />

      {/* 页面标题 */}
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>写作模板库</Title>
          <Text size="lg" c="dimmed">
            专业的写作模板，帮助您快速构建文章结构
          </Text>
        </div>
        <Badge size="lg" color="blue">
          {templatesData?.total || 0} 个模板
        </Badge>
      </Group>

      {/* 筛选和搜索 */}
      <Card withBorder mb="lg">
        <Grid>
          <Grid.Col span={3}>
            <Select
              label="写作类型"
              placeholder="选择类型"
              value={selectedType}
              onChange={(value) => setSelectedType(value || 'all')}
              data={[
                { value: 'all', label: '全部类型' },
                { value: WritingType.ARGUMENTATIVE, label: '议论文' },
                { value: WritingType.NARRATIVE, label: '记叙文' },
                { value: WritingType.DESCRIPTIVE, label: '描述文' },
                { value: WritingType.EXPOSITORY, label: '说明文' },
                { value: WritingType.PRACTICAL, label: '应用文' },
              ]}
              leftSection={<IconFilter size={16} />}
            />
          </Grid.Col>
          <Grid.Col span={3}>
            <Select
              label="难度等级"
              placeholder="选择难度"
              value={selectedDifficulty}
              onChange={(value) => setSelectedDifficulty(value || 'all')}
              data={[
                { value: 'all', label: '全部难度' },
                { value: WritingDifficulty.BASIC, label: '基础级' },
                { value: WritingDifficulty.INTERMEDIATE, label: '中级' },
                { value: WritingDifficulty.ADVANCED, label: '高级' },
                { value: WritingDifficulty.EXPERT, label: '专家级' },
              ]}
              leftSection={<IconFilter size={16} />}
            />
          </Grid.Col>
          <Grid.Col span={6}>
            <TextInput
              label="搜索模板"
              placeholder="输入模板名称或关键词"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.currentTarget.value)}
              leftSection={<IconSearch size={16} />}
            />
          </Grid.Col>
        </Grid>
      </Card>

      {/* 模板列表 */}
      <Grid>
        {filteredTemplates.map((template) => (
          <Grid.Col key={template.id} span={4}>
            <Card withBorder h="100%" p="md">
              <Stack gap="sm" h="100%">
                {/* 模板头部 */}
                <Group justify="space-between">
                  <Text fw={600} size="sm" lineClamp={2}>
                    {template.template_name}
                  </Text>
                  {template.is_recommended && (
                    <Tooltip label="推荐模板">
                      <IconStar size={16} color="gold" />
                    </Tooltip>
                  )}
                </Group>

                {/* 标签 */}
                <Group gap="xs">
                  <Badge color="blue" size="sm">
                    {getWritingTypeLabel(template.writing_type)}
                  </Badge>
                  <Badge color={getDifficultyColor(template.difficulty)} size="sm">
                    {getDifficultyLabel(template.difficulty)}
                  </Badge>
                </Group>

                {/* 使用说明 */}
                <Text size="xs" c="dimmed" lineClamp={3} style={{ flex: 1 }}>
                  {template.usage_instructions || '专业的写作模板，帮助您快速构建文章结构'}
                </Text>

                {/* 统计信息 */}
                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    使用次数: {template.usage_count}
                  </Text>
                  <Text size="xs" c="dimmed">
                    平均分: {Math.round(template.average_score * 10) / 10}
                  </Text>
                </Group>

                <Divider />

                {/* 操作按钮 */}
                <Group justify="space-between">
                  <Button
                    variant="light"
                    size="xs"
                    leftSection={<IconEye size={14} />}
                    onClick={() => viewTemplate(template)}
                  >
                    查看详情
                  </Button>
                  <ActionIcon
                    variant="light"
                    size="sm"
                    onClick={() => copyTemplate(template)}
                  >
                    <IconCopy size={14} />
                  </ActionIcon>
                </Group>
              </Stack>
            </Card>
          </Grid.Col>
        ))}
      </Grid>

      {/* 分页 */}
      {templatesData && templatesData.total > pageSize && (
        <Group justify="center" mt="lg">
          <Pagination
            value={currentPage}
            onChange={setCurrentPage}
            total={Math.ceil(templatesData.total / pageSize)}
          />
        </Group>
      )}

      {/* 空状态 */}
      {filteredTemplates.length === 0 && !templatesLoading && (
        <Paper p="xl" ta="center">
          <IconTemplate size={48} color="gray" />
          <Text size="lg" fw={600} mt="md">
            暂无模板
          </Text>
          <Text c="dimmed">
            没有找到符合条件的写作模板
          </Text>
        </Paper>
      )}

      {/* 模板详情模态框 */}
      <Modal
        opened={templateModalOpened}
        onClose={closeTemplateModal}
        title={selectedTemplate?.template_name}
        size="lg"
      >
        {selectedTemplate && (
          <Tabs defaultValue="structure">
            <Tabs.List>
              <Tabs.Tab value="structure" leftSection={<IconFileText size={16} />}>
                模板结构
              </Tabs.Tab>
              <Tabs.Tab value="phrases" leftSection={<IconBook size={16} />}>
                常用句式
              </Tabs.Tab>
              <Tabs.Tab value="example" leftSection={<IconBulb size={16} />}>
                示例作文
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="structure" pt="md">
              <Stack gap="md">
                <Group>
                  <Badge color="blue">{getWritingTypeLabel(selectedTemplate.writing_type)}</Badge>
                  <Badge color={getDifficultyColor(selectedTemplate.difficulty)}>
                    {getDifficultyLabel(selectedTemplate.difficulty)}
                  </Badge>
                </Group>

                {selectedTemplate.usage_instructions && (
                  <Alert icon={<IconBulb size={16} />} color="blue">
                    <Text size="sm">{selectedTemplate.usage_instructions}</Text>
                  </Alert>
                )}

                {selectedTemplate.template_structure && (
                  <Paper p="md" withBorder>
                    <Text fw={600} mb="sm">模板结构</Text>
                    <Code block>
                      {JSON.stringify(selectedTemplate.template_structure, null, 2)}
                    </Code>
                  </Paper>
                )}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="phrases" pt="md">
              <Stack gap="md">
                {selectedTemplate.opening_sentences && selectedTemplate.opening_sentences.length > 0 && (
                  <Paper p="md" withBorder>
                    <Text fw={600} mb="sm">开头句式</Text>
                    <List>
                      {selectedTemplate.opening_sentences.map((sentence, index) => (
                        <List.Item key={index}>{sentence}</List.Item>
                      ))}
                    </List>
                  </Paper>
                )}

                {selectedTemplate.transition_phrases && selectedTemplate.transition_phrases.length > 0 && (
                  <Paper p="md" withBorder>
                    <Text fw={600} mb="sm">过渡词汇</Text>
                    <Group gap="xs">
                      {selectedTemplate.transition_phrases.map((phrase, index) => (
                        <Badge key={index} variant="light">
                          {phrase}
                        </Badge>
                      ))}
                    </Group>
                  </Paper>
                )}

                {selectedTemplate.conclusion_sentences && selectedTemplate.conclusion_sentences.length > 0 && (
                  <Paper p="md" withBorder>
                    <Text fw={600} mb="sm">结尾句式</Text>
                    <List>
                      {selectedTemplate.conclusion_sentences.map((sentence, index) => (
                        <List.Item key={index}>{sentence}</List.Item>
                      ))}
                    </List>
                  </Paper>
                )}

                {selectedTemplate.key_phrases && selectedTemplate.key_phrases.length > 0 && (
                  <Paper p="md" withBorder>
                    <Text fw={600} mb="sm">关键短语</Text>
                    <Group gap="xs">
                      {selectedTemplate.key_phrases.map((phrase, index) => (
                        <Badge key={index} variant="outline">
                          {phrase}
                        </Badge>
                      ))}
                    </Group>
                  </Paper>
                )}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="example" pt="md">
              {selectedTemplate.example_essay ? (
                <Paper p="md" withBorder>
                  <Text fw={600} mb="sm">示例作文</Text>
                  <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                    {selectedTemplate.example_essay}
                  </Text>
                </Paper>
              ) : (
                <Alert icon={<IconBulb size={16} />} color="gray">
                  暂无示例作文
                </Alert>
              )}
            </Tabs.Panel>
          </Tabs>
        )}
      </Modal>
    </Container>
  )
}
