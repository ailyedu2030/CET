/**
 * 教师个人信息维护页面 - 需求10验收标准5：基础信息更新
 */

import {
  Alert,
  Button,
  Card,
  Container,
  Group,
  Modal,
  SegmentedControl,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
  Box,
  Divider,
  Badge,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconUser,
  IconEdit,
  IconCheck,
  IconX,
  IconLock,
  IconShield,
  IconCalendar,
  IconPhone,
  IconMail,
  IconSchool,
} from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { teacherRegistration } from '../../api/registration'
import { changePassword } from '../../api/auth'

// 教师基础信息接口
interface TeacherProfile {
  id: number
  username: string
  email: string
  real_name: string
  age?: number
  gender?: string
  title?: string
  subject?: string
  phone?: string
  introduction?: string
  created_at: string
  updated_at: string
  last_password_change?: string
  password_reminder_enabled: boolean
}

// 基础信息更新请求接口
interface ProfileUpdateRequest {
  real_name: string
  age?: number
  gender?: string
  title?: string
  subject?: string
  phone?: string
  introduction?: string
  [key: string]: unknown
}

// 密码修改请求接口
interface PasswordChangeRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

export function TeacherProfilePage(): JSX.Element {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [editMode, setEditMode] = useState(false)
  const [passwordModalOpened, { open: openPasswordModal, close: closePasswordModal }] =
    useDisclosure(false)

  // 获取教师个人信息
  const { data: profile, isLoading } = useQuery<TeacherProfile>({
    queryKey: ['teacher-profile', user?.id],
    queryFn: async (): Promise<TeacherProfile> => {
      // 实际应该调用真实API: await teacherRegistration.getProfile(Number(user?.id))
      return {
        id: Number(user?.id) || 0,
        username: user?.username || '',
        email: 'teacher@example.com', // 临时邮箱
        real_name: '张三',
        age: 30,
        gender: '男',
        title: '副教授',
        subject: '英语',
        phone: '13800138000',
        introduction: '我是一名经验丰富的英语教师，专注于四级考试辅导。',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-01-20T14:30:00Z',
        last_password_change: '2024-01-01T00:00:00Z',
        password_reminder_enabled: true,
      }
    },
    enabled: !!user,
  })

  // 基础信息表单
  const profileForm = useForm<ProfileUpdateRequest>({
    initialValues: {
      real_name: profile?.real_name || '',
      age: profile?.age,
      gender: profile?.gender,
      title: profile?.title || '',
      subject: profile?.subject || '',
      phone: profile?.phone || '',
      introduction: profile?.introduction || '',
    },
    validate: {
      real_name: value => (!value ? '请输入真实姓名' : null),
      age: value => (value && (value < 18 || value > 80) ? '年龄应在18-80之间' : null),
      phone: value => (value && !/^1[3-9]\d{9}$/.test(value) ? '请输入正确的手机号码' : null),
    },
  })

  // 密码修改表单
  const passwordForm = useForm<PasswordChangeRequest>({
    initialValues: {
      old_password: '',
      new_password: '',
      confirm_password: '',
    },
    validate: {
      old_password: value => (!value ? '请输入当前密码' : null),
      new_password: value => {
        if (!value) return '请输入新密码'
        if (value.length < 8) return '密码至少8位'
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) return '密码需包含大小写字母和数字'
        return null
      },
      confirm_password: (value, values) =>
        value !== values.new_password ? '两次密码输入不一致' : null,
    },
  })

  // 更新基础信息
  const updateProfileMutation = useMutation({
    mutationFn: async (data: ProfileUpdateRequest) => {
      // 实际应该调用真实API
      if (user?.id) {
        return await teacherRegistration.updateProfile(Number(user.id), data)
      }
      throw new Error('用户未登录')
    },
    onSuccess: () => {
      notifications.show({
        title: '更新成功',
        message: '个人信息已成功更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['teacher-profile'] })
      setEditMode(false)
    },
    onError: () => {
      notifications.show({
        title: '更新失败',
        message: '个人信息更新失败，请重试',
        color: 'red',
      })
    },
  })

  // 修改密码
  const changePasswordMutation = useMutation({
    mutationFn: async (data: PasswordChangeRequest) => {
      // 实际应该调用真实API
      return await changePassword({
        old_password: data.old_password,
        new_password: data.new_password,
      })
    },
    onSuccess: () => {
      notifications.show({
        title: '密码修改成功',
        message: '密码已成功修改，请重新登录',
        color: 'green',
      })
      passwordForm.reset()
      closePasswordModal()
    },
    onError: () => {
      notifications.show({
        title: '密码修改失败',
        message: '密码修改失败，请检查当前密码是否正确',
        color: 'red',
      })
    },
  })

  const handleProfileSubmit = (values: ProfileUpdateRequest) => {
    updateProfileMutation.mutate(values)
  }

  const handlePasswordSubmit = (values: PasswordChangeRequest) => {
    changePasswordMutation.mutate(values)
  }

  const handleEditToggle = () => {
    if (editMode) {
      profileForm.setValues({
        real_name: profile?.real_name || '',
        age: profile?.age,
        gender: profile?.gender,
        title: profile?.title || '',
        subject: profile?.subject || '',
        phone: profile?.phone || '',
        introduction: profile?.introduction || '',
      })
    }
    setEditMode(!editMode)
  }

  // 检查密码是否需要更新提醒
  const shouldShowPasswordReminder = () => {
    if (!profile?.last_password_change) return true
    const lastChange = new Date(profile.last_password_change)
    const now = new Date()
    const daysSinceChange = Math.floor(
      (now.getTime() - lastChange.getTime()) / (1000 * 60 * 60 * 24)
    )
    return daysSinceChange > 90 // 90天提醒更新密码
  }

  if (isLoading) {
    return (
      <Container size="md" py="xl">
        <Text>加载中...</Text>
      </Container>
    )
  }

  return (
    <Container size="md" py="xl">
      <Stack gap="lg">
        {/* 页面标题 */}
        <Group justify="space-between">
          <Title order={1}>个人信息维护</Title>
          <Group>
            <Button
              leftSection={<IconLock size={16} />}
              variant="outline"
              onClick={openPasswordModal}
            >
              修改密码
            </Button>
            <Button
              leftSection={editMode ? <IconX size={16} /> : <IconEdit size={16} />}
              variant={editMode ? 'outline' : 'filled'}
              onClick={handleEditToggle}
            >
              {editMode ? '取消编辑' : '编辑信息'}
            </Button>
          </Group>
        </Group>

        {/* 密码更新提醒 */}
        {shouldShowPasswordReminder() && (
          <Alert
            icon={<IconShield size={16} />}
            title="密码安全提醒"
            color="orange"
            withCloseButton
          >
            <Text size="sm">
              为了账户安全，建议您定期更新密码。您的密码已超过90天未更新，请考虑修改密码。
            </Text>
            <Button size="xs" variant="outline" color="orange" mt="xs" onClick={openPasswordModal}>
              立即修改
            </Button>
          </Alert>
        )}

        {/* 基础信息卡片 */}
        <Card withBorder shadow="sm" p="lg" radius="md">
          <form onSubmit={profileForm.onSubmit(handleProfileSubmit)}>
            <Stack gap="md">
              <Group justify="space-between">
                <Group>
                  <IconUser size={24} />
                  <Title order={3}>基础信息</Title>
                </Group>
                {editMode && (
                  <Button
                    type="submit"
                    leftSection={<IconCheck size={16} />}
                    loading={updateProfileMutation.isPending}
                  >
                    保存更改
                  </Button>
                )}
              </Group>

              <Divider />

              {/* 账户信息（只读） */}
              <Group grow>
                <TextInput
                  label="用户名"
                  value={profile?.username}
                  readOnly
                  leftSection={<IconUser size={16} />}
                />
                <TextInput
                  label="邮箱地址"
                  value={profile?.email}
                  readOnly
                  leftSection={<IconMail size={16} />}
                />
              </Group>

              {/* 可编辑的基础信息 */}
              <TextInput
                label="真实姓名"
                placeholder="请输入真实姓名"
                required
                readOnly={!editMode}
                {...profileForm.getInputProps('real_name')}
              />

              <Group grow>
                <TextInput
                  label="年龄"
                  type="number"
                  placeholder="请输入年龄"
                  readOnly={!editMode}
                  {...profileForm.getInputProps('age')}
                />
                <Box>
                  <Text size="sm" fw={500} mb="xs">
                    性别
                  </Text>
                  <SegmentedControl
                    data={[
                      { label: '男', value: '男' },
                      { label: '女', value: '女' },
                      { label: '其他', value: '其他' },
                    ]}
                    disabled={!editMode}
                    {...profileForm.getInputProps('gender')}
                  />
                </Box>
              </Group>

              <Group grow>
                <TextInput
                  label="职称"
                  placeholder="如：助教、讲师、副教授等"
                  readOnly={!editMode}
                  leftSection={<IconSchool size={16} />}
                  {...profileForm.getInputProps('title')}
                />
                <TextInput
                  label="所授学科"
                  placeholder="如：英语四级、大学英语等"
                  readOnly={!editMode}
                  {...profileForm.getInputProps('subject')}
                />
              </Group>

              <TextInput
                label="联系电话"
                placeholder="请输入手机号码"
                readOnly={!editMode}
                leftSection={<IconPhone size={16} />}
                {...profileForm.getInputProps('phone')}
              />

              <Textarea
                label="自我介绍"
                placeholder="请简要介绍您的教学经历、专业背景等"
                rows={4}
                readOnly={!editMode}
                {...profileForm.getInputProps('introduction')}
              />
            </Stack>
          </form>
        </Card>

        {/* 账户信息卡片 */}
        <Card withBorder shadow="sm" p="lg" radius="md">
          <Stack gap="md">
            <Group>
              <IconCalendar size={24} />
              <Title order={3}>账户信息</Title>
            </Group>

            <Divider />

            <Group justify="space-between">
              <Text fw={500}>注册时间：</Text>
              <Text>
                {profile?.created_at
                  ? new Date(profile.created_at).toLocaleDateString('zh-CN')
                  : '未知'}
              </Text>
            </Group>

            <Group justify="space-between">
              <Text fw={500}>最后更新：</Text>
              <Text>
                {profile?.updated_at
                  ? new Date(profile.updated_at).toLocaleDateString('zh-CN')
                  : '未知'}
              </Text>
            </Group>

            <Group justify="space-between">
              <Text fw={500}>密码更新：</Text>
              <Group>
                <Text>
                  {profile?.last_password_change
                    ? new Date(profile.last_password_change).toLocaleDateString('zh-CN')
                    : '未知'}
                </Text>
                {shouldShowPasswordReminder() && (
                  <Badge color="orange" size="sm">
                    需要更新
                  </Badge>
                )}
              </Group>
            </Group>

            <Group justify="space-between">
              <Text fw={500}>密码提醒：</Text>
              <Badge color={profile?.password_reminder_enabled ? 'green' : 'gray'}>
                {profile?.password_reminder_enabled ? '已启用' : '已关闭'}
              </Badge>
            </Group>
          </Stack>
        </Card>
      </Stack>

      {/* 密码修改模态框 */}
      <Modal opened={passwordModalOpened} onClose={closePasswordModal} title="修改密码" size="md">
        <form onSubmit={passwordForm.onSubmit(handlePasswordSubmit)}>
          <Stack gap="md">
            <Alert icon={<IconShield size={16} />} color="blue">
              <Text size="sm">为了账户安全，请设置包含大小写字母、数字的强密码，长度至少8位。</Text>
            </Alert>

            <TextInput
              label="当前密码"
              type="password"
              placeholder="请输入当前密码"
              required
              {...passwordForm.getInputProps('old_password')}
            />

            <TextInput
              label="新密码"
              type="password"
              placeholder="请输入新密码"
              required
              {...passwordForm.getInputProps('new_password')}
            />

            <TextInput
              label="确认新密码"
              type="password"
              placeholder="请再次输入新密码"
              required
              {...passwordForm.getInputProps('confirm_password')}
            />

            <Group justify="flex-end">
              <Button variant="outline" onClick={closePasswordModal}>
                取消
              </Button>
              <Button
                type="submit"
                loading={changePasswordMutation.isPending}
                leftSection={<IconCheck size={16} />}
              >
                确认修改
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Container>
  )
}
