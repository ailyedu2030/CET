import React, { useState, useCallback, useEffect } from 'react'
import {
  Card,
  Text,
  Stack,
  Group,
  Badge,
  Button,
  Alert,
  Switch,
  Select,
  NumberInput,
  ActionIcon,
  Modal,
  ThemeIcon,
  LoadingOverlay,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import {
  IconBell,
  IconSend,
  IconSettings,
  IconCheck,
  IconX,
  IconUsers,
  IconBrain,
} from '@tabler/icons-react'
import {
  teacherNotificationApi,
  type WeaknessPushData,
  type ClassSummaryPushData,
  type NotificationSettings,
} from '../../api/teacherNotification'

// 薄弱点数据类型
interface WeakPoint {
  knowledge_point: {
    name: string
  }
  weakness_score: number
  priority_level: 'high' | 'medium' | 'low'
  recommended_actions: string[]
  estimated_improvement_time: string
}

// 薄弱环节数据类型
interface WeaknessData {
  student_name?: string
  class_name?: string
  weak_points?: WeakPoint[]
  overall_mastery?: number
  improvement_suggestions?: string[]
}

// 推送完成结果类型
interface PushCompleteResult {
  notification_id: string
  pushed_to_teachers: number[]
  push_channels_used?: string[]
}

interface TeacherPushComponentProps {
  studentId?: number
  classId?: number
  teacherId: number
  weaknessData?: WeaknessData
  onPushComplete?: (result: PushCompleteResult) => void
  showSettings?: boolean
}

export const TeacherPushComponent: React.FC<TeacherPushComponentProps> = ({
  studentId,
  classId,
  teacherId,
  weaknessData,
  onPushComplete,
  showSettings = true,
}) => {
  const queryClient = useQueryClient()
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [pushType, setPushType] = useState<'individual' | 'class'>('individual')

  // 获取推送设置
  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ['notification-settings', teacherId],
    queryFn: () => teacherNotificationApi.getNotificationSettings(teacherId),
  })

  // 获取班级薄弱点汇总
  const { data: classSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ['class-weakness-summary', classId],
    queryFn: () =>
      classId ? teacherNotificationApi.getClassWeaknessSummary(classId) : Promise.resolve(null),
    enabled: !!classId && pushType === 'class',
  })

  // 推送个人薄弱环节分析
  const pushWeaknessMutation = useMutation({
    mutationFn: teacherNotificationApi.pushWeaknessAnalysis,
    onSuccess: result => {
      notifications.show({
        title: '推送成功',
        message: `已向 ${result.pushed_to_teachers.length} 位教师推送薄弱环节分析`,
        color: 'green',
        icon: <IconCheck size={16} />,
      })
      if (onPushComplete) {
        onPushComplete(result)
      }
    },
    onError: error => {
      notifications.show({
        title: '推送失败',
        message: error.message,
        color: 'red',
        icon: <IconX size={16} />,
      })
    },
  })

  // 推送班级汇总分析
  const pushClassSummaryMutation = useMutation({
    mutationFn: teacherNotificationApi.pushClassSummary,
    onSuccess: result => {
      notifications.show({
        title: '班级推送成功',
        message: `已向 ${result.pushed_to_teachers.length} 位教师推送班级汇总分析`,
        color: 'green',
        icon: <IconCheck size={16} />,
      })
      if (onPushComplete) {
        onPushComplete(result)
      }
    },
    onError: error => {
      notifications.show({
        title: '推送失败',
        message: error.message,
        color: 'red',
        icon: <IconX size={16} />,
      })
    },
  })

  // 更新推送设置
  const updateSettingsMutation = useMutation({
    mutationFn: (newSettings: Partial<NotificationSettings>) =>
      teacherNotificationApi.updateNotificationSettings(teacherId, newSettings),
    onSuccess: () => {
      notifications.show({
        title: '设置已更新',
        message: '推送设置已成功更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['notification-settings', teacherId] })
      setSettingsModalOpen(false)
    },
    onError: error => {
      notifications.show({
        title: '更新失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 设置表单
  const settingsForm = useForm<Partial<NotificationSettings>>({
    initialValues: {
      weakness_threshold: settings?.weakness_threshold || 60,
      push_frequency: settings?.push_frequency || 'immediate',
      push_channels: settings?.push_channels || ['in_app'],
      class_summary_enabled: settings?.class_summary_enabled || true,
      individual_student_enabled: settings?.individual_student_enabled || true,
      urgent_only: settings?.urgent_only || false,
    },
  })

  // 更新表单初始值
  useEffect(() => {
    if (settings) {
      settingsForm.setValues({
        weakness_threshold: settings.weakness_threshold,
        push_frequency: settings.push_frequency,
        push_channels: settings.push_channels,
        class_summary_enabled: settings.class_summary_enabled,
        individual_student_enabled: settings.individual_student_enabled,
        urgent_only: settings.urgent_only,
      })
    }
  }, [settings, settingsForm])

  // 推送个人薄弱环节分析
  const handlePushWeakness = useCallback(() => {
    if (!weaknessData || !studentId) {
      notifications.show({
        title: '数据不足',
        message: '缺少学生薄弱环节分析数据',
        color: 'yellow',
      })
      return
    }

    const pushData: WeaknessPushData = {
      student_id: studentId,
      student_name: weaknessData.student_name || `学生${studentId}`,
      class_id: classId || 0,
      class_name: weaknessData.class_name || '未知班级',
      analysis_date: new Date().toISOString(),
      weak_points:
        weaknessData.weak_points?.map((wp: WeakPoint) => ({
          knowledge_point_name: wp.knowledge_point.name,
          weakness_score: wp.weakness_score,
          priority_level: wp.priority_level,
          recommended_actions: wp.recommended_actions,
          estimated_improvement_time: wp.estimated_improvement_time,
        })) || [],
      overall_mastery: weaknessData.overall_mastery || 0,
      improvement_suggestions: weaknessData.improvement_suggestions || [],
      requires_immediate_attention:
        weaknessData.weak_points?.some(
          (wp: WeakPoint) => wp.priority_level === 'high' && wp.weakness_score > 80
        ) || false,
    }

    pushWeaknessMutation.mutate(pushData)
  }, [weaknessData, studentId, classId, pushWeaknessMutation])

  // 推送班级汇总分析
  const handlePushClassSummary = useCallback(() => {
    if (!classSummary || !classId) {
      notifications.show({
        title: '数据不足',
        message: '缺少班级汇总分析数据',
        color: 'yellow',
      })
      return
    }

    const pushData: ClassSummaryPushData = {
      class_id: classId,
      class_name: classSummary.class_info.name,
      analysis_period: 'current',
      total_students: classSummary.class_info.student_count,
      students_needing_attention: classSummary.overall_stats.students_needing_attention,
      common_weak_points: classSummary.common_weak_points,
      class_average_mastery: classSummary.overall_stats.average_mastery,
      improvement_trends: [], // 可以从其他数据源获取
      recommended_class_actions: classSummary.recommendations,
    }

    pushClassSummaryMutation.mutate(pushData)
  }, [classSummary, classId, pushClassSummaryMutation])

  // 保存推送设置
  const handleSaveSettings = useCallback(() => {
    const values = settingsForm.values
    updateSettingsMutation.mutate(values)
  }, [settingsForm.values, updateSettingsMutation])

  // 判断是否应该自动推送
  const shouldAutoPush = useCallback(() => {
    if (!settings || !weaknessData) return false

    const hasHighPriorityWeakness = weaknessData.weak_points?.some(
      (wp: WeakPoint) =>
        wp.priority_level === 'high' && wp.weakness_score >= settings.weakness_threshold
    )

    return hasHighPriorityWeakness && settings.push_frequency === 'immediate'
  }, [settings, weaknessData])

  // 自动推送逻辑
  useEffect(() => {
    if (shouldAutoPush() && studentId) {
      // 延迟推送，避免过于频繁
      const timer = setTimeout(() => {
        handlePushWeakness()
      }, 2000)

      return () => clearTimeout(timer)
    }
    // 如果条件不满足，返回undefined（可选的清理函数）
    return undefined
  }, [shouldAutoPush, studentId, handlePushWeakness])

  return (
    <Stack gap="md">
      {/* 推送控制面板 */}
      <Card withBorder padding="lg">
        <Stack gap="md">
          <Group justify="space-between" align="center">
            <Group gap="xs">
              <ThemeIcon color="blue" variant="light">
                <IconBell size={20} />
              </ThemeIcon>
              <Text fw={500} size="lg">
                教师端推送
              </Text>
            </Group>
            {showSettings && (
              <ActionIcon variant="outline" onClick={() => setSettingsModalOpen(true)}>
                <IconSettings size={16} />
              </ActionIcon>
            )}
          </Group>

          {/* 推送类型选择 */}
          <Group>
            <Button
              variant={pushType === 'individual' ? 'filled' : 'outline'}
              onClick={() => setPushType('individual')}
              leftSection={<IconBrain size={16} />}
              disabled={!studentId || !weaknessData}
            >
              个人分析推送
            </Button>
            <Button
              variant={pushType === 'class' ? 'filled' : 'outline'}
              onClick={() => setPushType('class')}
              leftSection={<IconUsers size={16} />}
              disabled={!classId}
            >
              班级汇总推送
            </Button>
          </Group>

          {/* 个人推送面板 */}
          {pushType === 'individual' && (
            <Card withBorder padding="sm">
              <Stack gap="sm">
                <Group justify="space-between">
                  <Text fw={500}>个人薄弱环节分析推送</Text>
                  {shouldAutoPush() && (
                    <Badge color="orange" variant="light">
                      自动推送
                    </Badge>
                  )}
                </Group>

                {weaknessData && (
                  <Alert color="blue" title="推送内容预览">
                    <Stack gap="xs">
                      <Text size="sm">
                        学生: <strong>{weaknessData.student_name || `学生${studentId}`}</strong>
                      </Text>
                      <Text size="sm">
                        整体掌握度: <strong>{weaknessData.overall_mastery?.toFixed(1)}%</strong>
                      </Text>
                      <Text size="sm">
                        薄弱知识点: <strong>{weaknessData.weak_points?.length || 0}</strong> 个
                      </Text>
                      <Text size="sm">
                        高优先级:{' '}
                        <strong>
                          {weaknessData.weak_points?.filter(
                            (wp: any) => wp.priority_level === 'high'
                          ).length || 0}
                        </strong>{' '}
                        个
                      </Text>
                    </Stack>
                  </Alert>
                )}

                <Button
                  onClick={handlePushWeakness}
                  loading={pushWeaknessMutation.isPending}
                  disabled={!weaknessData || !studentId}
                  leftSection={<IconSend size={16} />}
                >
                  立即推送给教师
                </Button>
              </Stack>
            </Card>
          )}

          {/* 班级推送面板 */}
          {pushType === 'class' && (
            <Card withBorder padding="sm">
              <LoadingOverlay visible={summaryLoading} />
              <Stack gap="sm">
                <Text fw={500}>班级薄弱环节汇总推送</Text>

                {classSummary && (
                  <Alert color="green" title="班级汇总预览">
                    <Stack gap="xs">
                      <Text size="sm">
                        班级: <strong>{classSummary.class_info.name}</strong>
                      </Text>
                      <Text size="sm">
                        学生总数: <strong>{classSummary.class_info.student_count}</strong>
                      </Text>
                      <Text size="sm">
                        需要关注:{' '}
                        <strong>{classSummary.overall_stats.students_needing_attention}</strong> 人
                      </Text>
                      <Text size="sm">
                        班级平均掌握度:{' '}
                        <strong>{classSummary.overall_stats.average_mastery.toFixed(1)}%</strong>
                      </Text>
                      <Text size="sm">
                        共同薄弱点: <strong>{classSummary.common_weak_points.length}</strong> 个
                      </Text>
                    </Stack>
                  </Alert>
                )}

                <Button
                  onClick={handlePushClassSummary}
                  loading={pushClassSummaryMutation.isPending}
                  disabled={!classSummary || !classId}
                  leftSection={<IconSend size={16} />}
                >
                  推送班级汇总给教师
                </Button>
              </Stack>
            </Card>
          )}

          {/* 推送状态显示 */}
          {(pushWeaknessMutation.data || pushClassSummaryMutation.data) && (
            <Alert color="green" title="推送成功" icon={<IconCheck size={16} />}>
              <Stack gap="xs">
                <Text size="sm">推送时间: {new Date().toLocaleString()}</Text>
                <Text size="sm">
                  通知教师数:{' '}
                  {pushWeaknessMutation.data?.pushed_to_teachers.length ||
                    pushClassSummaryMutation.data?.pushed_to_teachers.length ||
                    0}
                </Text>
                <Text size="sm">
                  推送渠道:{' '}
                  {pushWeaknessMutation.data?.push_channels_used.join(', ') || '应用内通知'}
                </Text>
              </Stack>
            </Alert>
          )}
        </Stack>
      </Card>

      {/* 推送设置模态框 */}
      <Modal
        opened={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        title="推送设置"
        size="md"
      >
        <LoadingOverlay visible={settingsLoading} />
        <form onSubmit={settingsForm.onSubmit(handleSaveSettings)}>
          <Stack gap="md">
            <NumberInput
              label="薄弱分数阈值"
              description="超过此分数的薄弱点将触发推送"
              min={0}
              max={100}
              {...settingsForm.getInputProps('weakness_threshold')}
            />

            <Select
              label="推送频率"
              data={[
                { value: 'immediate', label: '立即推送' },
                { value: 'daily', label: '每日汇总' },
                { value: 'weekly', label: '每周汇总' },
              ]}
              {...settingsForm.getInputProps('push_frequency')}
            />

            <Stack gap="xs">
              <Text size="sm" fw={500}>
                推送渠道
              </Text>
              <Switch
                label="应用内通知"
                checked={settingsForm.values.push_channels?.includes('in_app')}
                onChange={event => {
                  const channels = settingsForm.values.push_channels || []
                  if (event.currentTarget.checked) {
                    settingsForm.setFieldValue('push_channels', [...channels, 'in_app'])
                  } else {
                    settingsForm.setFieldValue(
                      'push_channels',
                      channels.filter(c => c !== 'in_app')
                    )
                  }
                }}
              />
              <Switch
                label="邮件通知"
                checked={settingsForm.values.push_channels?.includes('email')}
                onChange={event => {
                  const channels = settingsForm.values.push_channels || []
                  if (event.currentTarget.checked) {
                    settingsForm.setFieldValue('push_channels', [...channels, 'email'])
                  } else {
                    settingsForm.setFieldValue(
                      'push_channels',
                      channels.filter(c => c !== 'email')
                    )
                  }
                }}
              />
            </Stack>

            <Switch
              label="启用班级汇总推送"
              {...settingsForm.getInputProps('class_summary_enabled', { type: 'checkbox' })}
            />

            <Switch
              label="启用个人分析推送"
              {...settingsForm.getInputProps('individual_student_enabled', { type: 'checkbox' })}
            />

            <Switch
              label="仅推送紧急情况"
              description="只推送高优先级的薄弱环节"
              {...settingsForm.getInputProps('urgent_only', { type: 'checkbox' })}
            />

            <Group justify="flex-end" mt="md">
              <Button variant="outline" onClick={() => setSettingsModalOpen(false)}>
                取消
              </Button>
              <Button type="submit" loading={updateSettingsMutation.isPending}>
                保存设置
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
