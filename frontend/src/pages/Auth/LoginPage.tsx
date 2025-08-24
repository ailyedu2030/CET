import { LoginForm, LoginResponse, LoginTimeValidation } from '../../types/auth'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Container,
  Loader,
  Paper,
  PasswordInput,
  SegmentedControl,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function LoginPage(): JSX.Element {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [loginTimeValidation, setLoginTimeValidation] = useState<LoginTimeValidation>({
    isValid: true,
  })

  const form = useForm<LoginForm>({
    initialValues: {
      username: '',
      password: '',
      userType: 'student',
      agreedToPolicy: false,
    },
    validate: {
      username: (value: string) => {
        if (value.length < 1) return '请输入用户名'
        if (value.length < 3) return '用户名至少3个字符'
        return null
      },
      password: (value: string) => {
        if (value.length < 1) return '请输入密码'
        if (value.length < 6) return '密码至少6个字符'
        return null
      },
      agreedToPolicy: (value: boolean) => (!value ? '请同意数据保护政策' : null),
    },
  })

  // 登录时间验证（未成年人保护）
  const validateLoginTime = (): LoginTimeValidation => {
    const now = new Date()
    const hour = now.getHours()

    // 深夜禁用时间检查 (22:00-6:00)
    if (hour >= 22 || hour < 6) {
      return {
        isValid: false,
        message: '为保护学生健康，系统在22:00-6:00期间暂停服务',
      }
    }
    return { isValid: true }
  }

  // 模拟登录API调用
  const loginMutation = useMutation<LoginResponse, Error, LoginForm>({
    mutationFn: async (values: LoginForm): Promise<LoginResponse> => {
      // 登录时间验证
      const timeValidation = validateLoginTime()
      if (!timeValidation.isValid) {
        throw new Error(timeValidation.message)
      }

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1500))

      // 模拟登录成功响应
      return {
        success: true,
        user: {
          id: '1',
          username: values.username,
          userType: values.userType,
          lastLogin: new Date().toISOString(),
        },
        token: 'mock-jwt-token',
      }
    },
    onSuccess: (data: LoginResponse) => {
      notifications.show({
        title: '登录成功',
        message: `欢迎回来，${data.user.username}！`,
        color: 'green',
      })

      // 使用 authStore 存储认证信息
      login(data.user, data.token)

      // 根据用户类型跳转到对应页面
      const redirectPaths: Record<LoginResponse['user']['userType'], string> = {
        student: '/student/dashboard',
        teacher: '/teacher/dashboard',
        admin: '/admin/dashboard',
      }

      const redirectPath = redirectPaths[data.user.userType]
      if (redirectPath) {
        navigate(redirectPath)
      }
    },
    onError: (error: Error) => {
      notifications.show({
        title: '登录失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handleSubmit = (values: LoginForm): void => {
    // 再次验证登录时间
    const timeValidation = validateLoginTime()
    setLoginTimeValidation(timeValidation)

    if (!timeValidation.isValid) {
      return
    }

    loginMutation.mutate(values)
  }

  return (
    <Container size={420} my={40}>
      <Title ta="center" mb="md">
        英语四级学习系统
      </Title>

      <Text ta="center" c="dimmed" mb="xl">
        AI驱动的个性化英语学习平台
      </Text>

      {/* 登录时间限制提示 */}
      {!loginTimeValidation.isValid && (
        <Alert icon={<IconAlertTriangle size="1rem" />} title="系统提示" color="orange" mb="md">
          {loginTimeValidation.message}
        </Alert>
      )}

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            {/* 用户角色选择 */}
            <Box>
              <Text size="sm" fw={500} mb="xs">
                用户类型
              </Text>
              <SegmentedControl
                fullWidth
                data={[
                  { label: '学生', value: 'student' },
                  { label: '教师', value: 'teacher' },
                  { label: '管理员', value: 'admin' },
                ]}
                {...form.getInputProps('userType')}
              />
            </Box>

            <TextInput
              label="用户名"
              placeholder="请输入用户名"
              required
              {...form.getInputProps('username')}
            />

            <PasswordInput
              label="密码"
              placeholder="请输入密码"
              required
              {...form.getInputProps('password')}
            />

            {/* 数据保护政策同意 */}
            <Checkbox
              label={
                <Text size="sm">
                  我已阅读并同意
                  <Text component="a" href="#" c="blue" td="underline" mx={4}>
                    《学生数据保护政策》
                  </Text>
                  和
                  <Text component="a" href="#" c="blue" td="underline" mx={4}>
                    《用户服务协议》
                  </Text>
                </Text>
              }
              {...form.getInputProps('agreedToPolicy', { type: 'checkbox' })}
            />

            {/* 教育系统提示信息 */}
            <Alert
              icon={<IconInfoCircle size="1rem" />}
              title="学习提示"
              color="blue"
              variant="light"
            >
              <Text size="xs">
                • 建议每日学习时间不超过2小时
                <br />
                • 系统将记录您的学习进度和成果
                <br />• AI将为您提供个性化学习建议
              </Text>
            </Alert>

            <Button
              type="submit"
              fullWidth
              mt="xl"
              loading={loginMutation.isPending}
              disabled={!loginTimeValidation.isValid}
            >
              {loginMutation.isPending ? (
                <>
                  <Loader size="xs" mr="xs" />
                  登录中...
                </>
              ) : (
                '登录'
              )}
            </Button>
          </Stack>
        </form>
      </Paper>

      {/* 系统状态信息 */}
      <Text ta="center" size="xs" c="dimmed" mt="md">
        系统版本 v1.0.0 | 服务时间：6:00-22:00
      </Text>
    </Container>
  )
}
