/**
 * 离线教案编辑器
 * 
 * 支持离线编辑教案的组件：
 * - 离线数据存储
 * - 自动保存
 * - 冲突检测
 * - 同步状态显示
 */

import {
  Card,
  TextInput,
  Textarea,
  Button,
  Group,
  Stack,
  Badge,
  Alert,
  LoadingOverlay,
  Text,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import {
  IconDeviceFloppy,
  IconCloudUpload,
  IconWifiOff,
  IconAlertTriangle,
  IconCheck,
} from '@tabler/icons-react'
import { useForm } from '@mantine/form'
import { useEffect, useState } from 'react'

import { useOfflineData, useSyncStatus, useOfflineStatus } from '@/hooks/useOfflineData'
import { STORES } from '@/services/offlineStorage'

// 教案数据接口
interface LessonPlan {
  id: string
  title: string
  content: string
  objectives: string
  materials: string
  duration: number
  lastModified: number
  version: number
}

interface OfflineLessonPlanEditorProps {
  lessonPlanId?: string
  onSave?: (lessonPlan: LessonPlan) => void
  onCancel?: () => void
}

export function OfflineLessonPlanEditor({
  lessonPlanId,
  onSave,
  onCancel,
}: OfflineLessonPlanEditorProps): JSX.Element {
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  const { isOffline } = useOfflineStatus()
  const { isSync, pendingItems } = useSyncStatus()

  // 使用离线数据Hook
  const {
    data: lessonPlan,
    isLoading,
    create,
    update,
    isCreating,
    isUpdating,
  } = useOfflineData<LessonPlan>(
    lessonPlanId ? ['lessonPlan', lessonPlanId] : ['lessonPlans'],
    {
      storeType: STORES.LESSON_PLANS,
      enableSync: true,
    }
  )

  // 表单管理
  const form = useForm<Omit<LessonPlan, 'id' | 'lastModified' | 'version'>>({
    initialValues: {
      title: '',
      content: '',
      objectives: '',
      materials: '',
      duration: 45,
    },
    validate: {
      title: (value) => (value.length < 2 ? '标题至少需要2个字符' : null),
      content: (value) => (value.length < 10 ? '内容至少需要10个字符' : null),
    },
  })

  // 加载现有数据
  useEffect(() => {
    if (lessonPlan && !Array.isArray(lessonPlan)) {
      form.setValues({
        title: lessonPlan.title || '',
        content: lessonPlan.content || '',
        objectives: lessonPlan.objectives || '',
        materials: lessonPlan.materials || '',
        duration: lessonPlan.duration || 45,
      })
      setLastSaved(new Date(lessonPlan.lastModified))
    }
  }, [lessonPlan])

  // 监听表单变化
  useEffect(() => {
    let timer: number | null = null

    const handleFormChange = () => {
      setHasUnsavedChanges(true)

      if (autoSaveEnabled && !isOffline) {
        // 清除之前的定时器
        if (timer) {
          clearTimeout(timer)
        }

        // 延迟自动保存
        timer = window.setTimeout(() => {
          handleSave(true)
        }, 2000)
      }
    }

    // 简单的变化检测
    const interval = setInterval(handleFormChange, 1000)

    return () => {
      if (timer) {
        clearTimeout(timer)
      }
      clearInterval(interval)
    }
  }, [autoSaveEnabled, isOffline])

  // 保存处理
  const handleSave = async (isAutoSave = false) => {
    if (!form.isValid()) {
      if (!isAutoSave) {
        form.validate()
      }
      return
    }

    const formData = form.getValues()
    const saveData: LessonPlan = {
      ...formData,
      id: lessonPlanId || `lesson_${Date.now()}`,
      lastModified: Date.now(),
      version: (lessonPlan as LessonPlan)?.version ? (lessonPlan as LessonPlan).version + 1 : 1,
    }

    try {
      if (lessonPlanId) {
        update({ id: lessonPlanId, data: saveData })
      } else {
        create(saveData)
      }

      setHasUnsavedChanges(false)
      setLastSaved(new Date())
      
      if (onSave) {
        onSave(saveData)
      }
    } catch (error) {
      // 错误处理在Hook中已经处理
    }
  }

  // 获取状态显示
  const getStatusBadge = () => {
    if (isSync) {
      return <Badge color="blue" leftSection={<IconCloudUpload size={12} />}>同步中</Badge>
    }
    
    if (isOffline) {
      return <Badge color="orange" leftSection={<IconWifiOff size={12} />}>离线模式</Badge>
    }
    
    if (hasUnsavedChanges) {
      return <Badge color="yellow" leftSection={<IconAlertTriangle size={12} />}>未保存</Badge>
    }
    
    if (lastSaved) {
      return <Badge color="green" leftSection={<IconCheck size={12} />}>已保存</Badge>
    }
    
    return null
  }

  return (
    <Card withBorder>
      <LoadingOverlay visible={isLoading} />
      
      <Stack gap="md">
        {/* 头部状态栏 */}
        <Group justify="space-between">
          <Text size="lg" fw={600}>
            {lessonPlanId ? '编辑教案' : '新建教案'}
          </Text>
          
          <Group gap="xs">
            {getStatusBadge()}
            
            {pendingItems > 0 && (
              <Tooltip label={`${pendingItems} 项待同步`}>
                <Badge color="orange" variant="outline">
                  {pendingItems}
                </Badge>
              </Tooltip>
            )}
          </Group>
        </Group>

        {/* 离线提示 */}
        {isOffline && (
          <Alert color="orange" icon={<IconWifiOff size={16} />}>
            当前处于离线模式，您的更改将在网络恢复后自动同步
          </Alert>
        )}

        {/* 表单内容 */}
        <form onSubmit={form.onSubmit(() => handleSave())}>
          <Stack gap="md">
            <TextInput
              label="教案标题"
              placeholder="请输入教案标题"
              required
              {...form.getInputProps('title')}
            />

            <Textarea
              label="教学内容"
              placeholder="请输入教学内容"
              required
              minRows={6}
              {...form.getInputProps('content')}
            />

            <Textarea
              label="教学目标"
              placeholder="请输入教学目标"
              minRows={3}
              {...form.getInputProps('objectives')}
            />

            <Textarea
              label="教学材料"
              placeholder="请输入所需教学材料"
              minRows={3}
              {...form.getInputProps('materials')}
            />

            <TextInput
              label="课时长度（分钟）"
              type="number"
              min={1}
              max={180}
              {...form.getInputProps('duration')}
            />

            {/* 操作按钮 */}
            <Group justify="flex-end" gap="md">
              {onCancel && (
                <Button variant="outline" onClick={onCancel}>
                  取消
                </Button>
              )}
              
              <Group gap="xs">
                <ActionIcon
                  variant="outline"
                  onClick={() => setAutoSaveEnabled(!autoSaveEnabled)}
                  color={autoSaveEnabled ? 'blue' : 'gray'}
                >
                  <Tooltip label={autoSaveEnabled ? '关闭自动保存' : '开启自动保存'}>
                    <IconDeviceFloppy size={16} />
                  </Tooltip>
                </ActionIcon>
                
                <Button
                  type="submit"
                  loading={isCreating || isUpdating}
                  leftSection={<IconDeviceFloppy size={16} />}
                >
                  保存
                </Button>
              </Group>
            </Group>
          </Stack>
        </form>

        {/* 最后保存时间 */}
        {lastSaved && (
          <Text size="xs" c="dimmed" ta="right">
            最后保存：{lastSaved.toLocaleString()}
          </Text>
        )}
      </Stack>
    </Card>
  )
}
