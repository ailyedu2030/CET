import {
  Alert,
  Button,
  Card,
  Group,
  Modal,
  Radio,
  Select,
  Stack,
  Text,
  Title,
  Badge,
  MultiSelect,
  Switch,
  Divider,
  Avatar,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import {
  IconLock,
  IconUsers,
  IconWorld,
  IconInfoCircle,
  IconCheck,
  IconX,
} from '@tabler/icons-react'
import { useState, useCallback, useEffect } from 'react'

interface PermissionSettingsModalProps {
  opened: boolean
  onClose: () => void
  resourceId: number
  resourceType: 'vocabulary' | 'knowledge' | 'material' | 'syllabus'
  currentPermission: 'private' | 'class' | 'public'
  onPermissionUpdate: (newPermission: string) => void
}

interface ClassInfo {
  id: number
  name: string
  studentCount: number
  teacherCount: number
}

interface TeacherInfo {
  id: number
  name: string
  email: string
  avatar?: string
  department: string
}

export function PermissionSettingsModal({
  opened,
  onClose,
  resourceId,
  resourceType,
  currentPermission,
  onPermissionUpdate,
}: PermissionSettingsModalProps): JSX.Element {
  const [permission, setPermission] = useState(currentPermission)
  const [selectedClasses, setSelectedClasses] = useState<string[]>([])
  const [selectedTeachers, setSelectedTeachers] = useState<string[]>([])
  const [allowDownload, setAllowDownload] = useState(true)
  const [allowEdit, setAllowEdit] = useState(false)
  const [expiryDate, setExpiryDate] = useState<string>('')
  const [loading, setLoading] = useState(false)

  // 模拟数据
  const [classes] = useState<ClassInfo[]>([
    { id: 1, name: 'CET4-A班', studentCount: 30, teacherCount: 2 },
    { id: 2, name: 'CET4-B班', studentCount: 28, teacherCount: 2 },
    { id: 3, name: 'CET6-A班', studentCount: 25, teacherCount: 1 },
  ])

  const [teachers] = useState<TeacherInfo[]>([
    { id: 1, name: '张老师', email: 'zhang@example.com', department: '英语系' },
    { id: 2, name: '李老师', email: 'li@example.com', department: '英语系' },
    { id: 3, name: '王老师', email: 'wang@example.com', department: '外语系' },
  ])

  const resourceTypeLabels = {
    vocabulary: '词汇库',
    knowledge: '知识点库',
    material: '教材',
    syllabus: '考纲',
  }

  const permissionOptions = [
    {
      value: 'private',
      label: '私有',
      description: '仅创建者可见和使用',
      icon: IconLock,
      color: 'gray',
    },
    {
      value: 'class',
      label: '班级共享',
      description: '指定班级的师生可见和使用',
      icon: IconUsers,
      color: 'blue',
    },
    {
      value: 'public',
      label: '全校共享',
      description: '全校师生可见和使用',
      icon: IconWorld,
      color: 'green',
    },
  ]

  const classOptions = classes.map(cls => ({
    value: cls.id.toString(),
    label: `${cls.name} (${cls.studentCount}人)`,
  }))

  const teacherOptions = teachers.map(teacher => ({
    value: teacher.id.toString(),
    label: `${teacher.name} - ${teacher.department}`,
  }))

  useEffect(() => {
    setPermission(currentPermission)
  }, [currentPermission])

  const handleSave = useCallback(async () => {
    setLoading(true)

    try {
      // 构建权限设置数据并模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      // 这里可以添加实际的API调用
      // await apiClient.put(`/resources/${resourceId}/permissions`, permissionData)

      notifications.show({
        title: '权限设置成功',
        message: `${resourceTypeLabels[resourceType]}的权限已更新为${permissionOptions.find(p => p.value === permission)?.label}`,
        color: 'green',
      })

      onPermissionUpdate(permission)
      onClose()
    } catch (error) {
      notifications.show({
        title: '权限设置失败',
        message: error instanceof Error ? error.message : '请稍后重试',
        color: 'red',
      })
    } finally {
      setLoading(false)
    }
  }, [
    resourceId,
    resourceType,
    permission,
    selectedClasses,
    selectedTeachers,
    allowDownload,
    allowEdit,
    expiryDate,
    onPermissionUpdate,
    onClose,
  ])

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`权限设置 - ${resourceTypeLabels[resourceType]}`}
      size="md"
      centered
    >
      <Stack gap="md">
        <Alert icon={<IconInfoCircle size="1rem" />} color="blue">
          <Text size="sm">设置资源的访问权限和使用规则。权限变更后立即生效。</Text>
        </Alert>

        {/* 权限级别选择 */}
        <Card withBorder p="md">
          <Title order={6} mb="md">
            访问权限
          </Title>
          <Radio.Group
            value={permission}
            onChange={value => setPermission(value as 'private' | 'class' | 'public')}
          >
            <Stack gap="sm">
              {permissionOptions.map(option => {
                const Icon = option.icon
                return (
                  <Card
                    key={option.value}
                    withBorder={permission === option.value}
                    p="sm"
                    style={{
                      cursor: 'pointer',
                      borderColor:
                        permission === option.value
                          ? `var(--mantine-color-${option.color}-5)`
                          : undefined,
                    }}
                    onClick={() => setPermission(option.value as 'private' | 'class' | 'public')}
                  >
                    <Group>
                      <Radio value={option.value} />
                      <Icon size={20} color={`var(--mantine-color-${option.color}-6)`} />
                      <div style={{ flex: 1 }}>
                        <Text fw={500}>{option.label}</Text>
                        <Text size="sm" c="dimmed">
                          {option.description}
                        </Text>
                      </div>
                      {permission === option.value && (
                        <Badge color={option.color} size="sm">
                          <IconCheck size={12} />
                        </Badge>
                      )}
                    </Group>
                  </Card>
                )
              })}
            </Stack>
          </Radio.Group>
        </Card>

        {/* 班级共享设置 */}
        {permission === 'class' && (
          <Card withBorder p="md">
            <Title order={6} mb="md">
              班级共享设置
            </Title>
            <Stack gap="md">
              <MultiSelect
                label="选择班级"
                placeholder="选择要共享的班级"
                data={classOptions}
                value={selectedClasses}
                onChange={setSelectedClasses}
                searchable
                clearable
              />

              <MultiSelect
                label="额外授权教师"
                placeholder="选择其他可访问的教师"
                data={teacherOptions}
                value={selectedTeachers}
                onChange={setSelectedTeachers}
                searchable
                clearable
              />

              {/* 显示已选择的教师 */}
              {selectedTeachers.length > 0 && (
                <Stack gap="xs">
                  <Text size="sm" fw={500}>
                    已授权教师:
                  </Text>
                  {selectedTeachers.map(teacherId => {
                    const teacher = teachers.find(t => t.id.toString() === teacherId)
                    return teacher ? (
                      <Group key={teacherId} justify="space-between">
                        <Group>
                          <Avatar size="sm" name={teacher.name} />
                          <div>
                            <Text size="sm">{teacher.name}</Text>
                            <Text size="xs" c="dimmed">
                              {teacher.department}
                            </Text>
                          </div>
                        </Group>
                        <Tooltip label="移除授权">
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="red"
                            onClick={() =>
                              setSelectedTeachers(prev => prev.filter(id => id !== teacherId))
                            }
                          >
                            <IconX size={12} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    ) : null
                  })}
                </Stack>
              )}
            </Stack>
          </Card>
        )}

        {/* 使用权限设置 */}
        <Card withBorder p="md">
          <Title order={6} mb="md">
            使用权限
          </Title>
          <Stack gap="md">
            <Group justify="space-between">
              <div>
                <Text size="sm" fw={500}>
                  允许下载
                </Text>
                <Text size="xs" c="dimmed">
                  用户可以下载资源文件
                </Text>
              </div>
              <Switch
                checked={allowDownload}
                onChange={event => setAllowDownload(event.currentTarget.checked)}
              />
            </Group>

            <Group justify="space-between">
              <div>
                <Text size="sm" fw={500}>
                  允许编辑
                </Text>
                <Text size="xs" c="dimmed">
                  授权用户可以编辑资源内容
                </Text>
              </div>
              <Switch
                checked={allowEdit}
                onChange={event => setAllowEdit(event.currentTarget.checked)}
              />
            </Group>

            <Divider />

            <div>
              <Text size="sm" fw={500} mb="xs">
                访问期限
              </Text>
              <Select
                placeholder="选择访问期限"
                value={expiryDate}
                onChange={value => setExpiryDate(value || '')}
                data={[
                  { value: '', label: '永久有效' },
                  { value: '7d', label: '7天后过期' },
                  { value: '30d', label: '30天后过期' },
                  { value: '90d', label: '90天后过期' },
                  { value: '1y', label: '1年后过期' },
                ]}
                clearable
              />
            </div>
          </Stack>
        </Card>

        {/* 权限预览 */}
        <Alert color="gray">
          <Text size="sm" fw={500} mb="xs">
            权限预览
          </Text>
          <Text size="sm">
            {permission === 'private' && '仅您可以查看和使用此资源'}
            {permission === 'class' &&
              `${selectedClasses.length} 个班级和 ${selectedTeachers.length} 位教师可以访问此资源`}
            {permission === 'public' && '全校师生都可以查看和使用此资源'}
          </Text>
          <Text size="xs" c="dimmed" mt="xs">
            {allowDownload ? '✓ 允许下载' : '✗ 禁止下载'} •
            {allowEdit ? ' ✓ 允许编辑' : ' ✗ 禁止编辑'} •
            {expiryDate ? ` 有效期: ${expiryDate}` : ' 永久有效'}
          </Text>
        </Alert>

        {/* 操作按钮 */}
        <Group justify="flex-end">
          <Button variant="light" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSave} loading={loading}>
            保存设置
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
