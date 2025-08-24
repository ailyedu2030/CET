/**
 * 训练参数模板创建/编辑Modal组件 - 需求15实现
 * 复用现有Modal和表单模式
 */
import { useState } from 'react'
import {
  Modal,
  Stack,
  TextInput,
  Textarea,
  Switch,
  Button,
  Group,
  Alert,
  Tabs,
  Text,
  Divider,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import {
  IconTemplate,
  IconSettings,
  IconEye,
  IconDeviceFloppy,
  IconAlertTriangle,
} from '@tabler/icons-react'

import {
  trainingWorkshopApi,
  TrainingParameterTemplate,
  TrainingParameterTemplateRequest,
  TrainingParameterConfig,
} from '@/api/trainingWorkshop'
import { TrainingParameterConfigForm } from './TrainingParameterConfigForm'

interface TrainingParameterTemplateModalProps {
  opened: boolean
  onClose: () => void
  template?: TrainingParameterTemplate
  onSuccess: () => void
}

export function TrainingParameterTemplateModal({
  opened,
  onClose,
  template,
  onSuccess,
}: TrainingParameterTemplateModalProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('basic')
  const [loading, setLoading] = useState(false)
  const [parameterConfig, setParameterConfig] = useState<TrainingParameterConfig>(
    template?.config || trainingWorkshopApi.getDefaultParameterConfig()
  )

  const isEditing = !!template

  const form = useForm<Omit<TrainingParameterTemplateRequest, 'config'>>({
    initialValues: {
      name: template?.name || '',
      description: template?.description || '',
      is_default: template?.is_default || false,
    },
    validate: {
      name: value => {
        if (!value.trim()) return '模板名称不能为空'
        if (value.length < 2) return '模板名称至少2个字符'
        if (value.length > 100) return '模板名称不能超过100个字符'
        return null
      },
      description: value => {
        if (value && value.length > 500) return '描述不能超过500个字符'
        return null
      },
    },
  })

  const handleSubmit = async () => {
    // 验证基本信息
    const basicValidation = form.validate()
    if (basicValidation.hasErrors) {
      setActiveTab('basic')
      return
    }

    // 验证参数配置
    const configErrors = trainingWorkshopApi.validateParameterConfig(parameterConfig)
    if (configErrors.length > 0) {
      notifications.show({
        title: '参数配置验证失败',
        message: configErrors.join(', '),
        color: 'red',
      })
      setActiveTab('config')
      return
    }

    setLoading(true)

    try {
      const templateData: TrainingParameterTemplateRequest = {
        ...form.values,
        config: parameterConfig,
      }

      if (isEditing && template) {
        await trainingWorkshopApi.updateParameterTemplate(template.id!, templateData)
        notifications.show({
          title: '更新成功',
          message: '训练参数模板已更新',
          color: 'green',
        })
      } else {
        await trainingWorkshopApi.createParameterTemplate(templateData)
        notifications.show({
          title: '创建成功',
          message: '训练参数模板已创建',
          color: 'green',
        })
      }

      onSuccess()
      onClose()
    } catch (error: any) {
      notifications.show({
        title: isEditing ? '更新失败' : '创建失败',
        message: error.response?.data?.detail || '操作失败，请重试',
        color: 'red',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    form.reset()
    setParameterConfig(trainingWorkshopApi.getDefaultParameterConfig())
    setActiveTab('basic')
    onClose()
  }

  const handleParameterConfigSubmit = (config: TrainingParameterConfig) => {
    setParameterConfig(config)
    notifications.show({
      title: '配置已保存',
      message: '参数配置已保存到模板中',
      color: 'green',
    })
  }

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={
        <Group>
          <IconTemplate size={20} />
          <Text fw={500}>{isEditing ? '编辑训练参数模板' : '创建训练参数模板'}</Text>
        </Group>
      }
      size="xl"
      centered
    >
      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'basic')}>
        <Tabs.List>
          <Tabs.Tab value="basic" leftSection={<IconTemplate size={16} />}>
            基本信息
          </Tabs.Tab>
          <Tabs.Tab value="config" leftSection={<IconSettings size={16} />}>
            参数配置
          </Tabs.Tab>
          <Tabs.Tab value="preview" leftSection={<IconEye size={16} />}>
            预览
          </Tabs.Tab>
        </Tabs.List>

        {/* 基本信息标签页 */}
        <Tabs.Panel value="basic" pt="lg">
          <Stack gap="md">
            <TextInput
              label="模板名称"
              placeholder="请输入模板名称"
              required
              {...form.getInputProps('name')}
            />

            <Textarea
              label="模板描述"
              placeholder="请输入模板描述（可选）"
              rows={3}
              {...form.getInputProps('description')}
            />

            <Switch
              label="设为默认模板"
              description="设为默认模板后，创建新任务时将自动使用此配置"
              {...form.getInputProps('is_default', { type: 'checkbox' })}
            />

            {form.values.is_default && (
              <Alert icon={<IconAlertTriangle size={16} />} color="yellow">
                设为默认模板将取消其他模板的默认状态
              </Alert>
            )}
          </Stack>
        </Tabs.Panel>

        {/* 参数配置标签页 */}
        <Tabs.Panel value="config" pt="lg">
          <TrainingParameterConfigForm
            initialConfig={parameterConfig}
            onSubmit={handleParameterConfigSubmit}
            loading={loading}
          />
        </Tabs.Panel>

        {/* 预览标签页 */}
        <Tabs.Panel value="preview" pt="lg">
          <Stack gap="md">
            <Group justify="space-between">
              <Text fw={500}>模板预览</Text>
              <Text size="sm" c="dimmed">
                {isEditing ? '编辑模式' : '创建模式'}
              </Text>
            </Group>

            <Divider />

            <div>
              <Text size="sm" fw={500} mb="xs">
                基本信息
              </Text>
              <Stack gap="xs">
                <Group>
                  <Text size="sm" c="dimmed" w={100}>
                    名称:
                  </Text>
                  <Text size="sm">{form.values.name || '未设置'}</Text>
                </Group>
                <Group>
                  <Text size="sm" c="dimmed" w={100}>
                    描述:
                  </Text>
                  <Text size="sm">{form.values.description || '无描述'}</Text>
                </Group>
                <Group>
                  <Text size="sm" c="dimmed" w={100}>
                    默认模板:
                  </Text>
                  <Text size="sm" c={form.values.is_default ? 'green' : 'gray'}>
                    {form.values.is_default ? '是' : '否'}
                  </Text>
                </Group>
              </Stack>
            </div>

            <Divider />

            <div>
              <Text size="sm" fw={500} mb="xs">
                参数配置摘要
              </Text>
              <Stack gap="xs">
                <Group>
                  <Text size="sm" c="dimmed" w={120}>
                    知识点数量:
                  </Text>
                  <Text size="sm">{parameterConfig.knowledge_points.length}</Text>
                </Group>
                <Group>
                  <Text size="sm" c="dimmed" w={120}>
                    词汇库数量:
                  </Text>
                  <Text size="sm">{parameterConfig.vocabulary_library_ids.length}</Text>
                </Group>
                <Group>
                  <Text size="sm" c="dimmed" w={120}>
                    热点融合度:
                  </Text>
                  <Text size="sm">{parameterConfig.hot_topics_fusion_rate}%</Text>
                </Group>
                <Group>
                  <Text size="sm" c="dimmed" w={120}>
                    教案衔接度:
                  </Text>
                  <Text size="sm">{parameterConfig.lesson_plan_connection_rate}%</Text>
                </Group>
                <Group>
                  <Text size="sm" c="dimmed" w={120}>
                    总题目数:
                  </Text>
                  <Text size="sm">
                    {Object.values(parameterConfig.question_count_per_type).reduce(
                      (sum, count) => sum + count,
                      0
                    )}
                  </Text>
                </Group>
              </Stack>
            </div>
          </Stack>
        </Tabs.Panel>
      </Tabs>

      <Divider my="lg" />

      {/* 操作按钮 */}
      <Group justify="flex-end">
        <Button variant="light" onClick={handleClose}>
          取消
        </Button>
        <Button
          leftSection={<IconDeviceFloppy size={16} />}
          loading={loading}
          onClick={handleSubmit}
        >
          {isEditing ? '更新模板' : '创建模板'}
        </Button>
      </Group>
    </Modal>
  )
}
