/**
 * 用户激活页面
 *
 * 实现🔥需求20验收标准5：
 * - 激活链接处理
 * - 24小时有效期
 * - 支持过期重发
 */

import {
  Container,
  Card,
  Stack,
  Title,
  Text,
  Button,
  Center,
  Loader,
  Group,
  TextInput,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconCheck, IconAlertCircle, IconMail, IconArrowLeft } from '@tabler/icons-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  activateUser,
  resendActivationEmail,
  checkActivationStatus,
  type ActivationRequest,
  type ResendActivationRequest,
  type ActivationResponse,
} from '../../api/activation'

export function ActivationPage(): JSX.Element {
  const navigate = useNavigate()
  const { token } = useParams<{ token: string }>()
  const [activationStatus, setActivationStatus] = useState<
    'checking' | 'valid' | 'invalid' | 'expired' | 'activated'
  >('checking')
  const [showResendForm, setShowResendForm] = useState(false)

  // 重发激活邮件表单
  const resendForm = useForm({
    initialValues: {
      email: '',
    },
    validate: {
      email: (value: string) => {
        if (!value) return '请输入邮箱地址'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return '请输入正确的邮箱格式'
        return null
      },
    },
  })

  // 检查激活链接状态
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: ['activation-status', token],
    queryFn: () => checkActivationStatus(token || ''),
    enabled: !!token,
  })

  // 激活用户
  const activationMutation = useMutation<ActivationResponse, Error, ActivationRequest>({
    mutationFn: activateUser,
    onSuccess: data => {
      if (data.success) {
        setActivationStatus('activated')
        notifications.show({
          title: '激活成功',
          message: `欢迎 ${data.username}！您的账号已成功激活`,
          color: 'green',
          icon: <IconCheck size={16} />,
        })
      } else {
        if (data.message.includes('过期')) {
          setActivationStatus('expired')
        } else {
          setActivationStatus('invalid')
        }
        notifications.show({
          title: '激活失败',
          message: data.message,
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        })
      }
    },
    onError: error => {
      setActivationStatus('invalid')
      notifications.show({
        title: '激活失败',
        message: error.message || '网络错误，请稍后重试',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      })
    },
  })

  // 重发激活邮件
  const resendMutation = useMutation<ActivationResponse, Error, ResendActivationRequest>({
    mutationFn: resendActivationEmail,
    onSuccess: data => {
      if (data.success) {
        notifications.show({
          title: '发送成功',
          message: data.message,
          color: 'green',
          icon: <IconCheck size={16} />,
        })
        setShowResendForm(false)
      } else {
        notifications.show({
          title: '发送失败',
          message: data.message,
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        })
      }
    },
    onError: error => {
      notifications.show({
        title: '发送失败',
        message: error.message || '网络错误，请稍后重试',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      })
    },
  })

  // 检查激活状态
  useEffect(() => {
    if (statusData) {
      if (statusData.valid) {
        setActivationStatus('valid')
      } else if (statusData.message.includes('过期')) {
        setActivationStatus('expired')
      } else {
        setActivationStatus('invalid')
      }
    }
  }, [statusData])

  // 自动激活
  const handleActivate = () => {
    if (token) {
      activationMutation.mutate({ activation_token: token })
    }
  }

  // 重发激活邮件
  const handleResendActivation = (values: { email: string }) => {
    resendMutation.mutate({ email: values.email })
  }

  // 返回登录页面
  const handleBackToLogin = () => {
    navigate('/login')
  }

  // 返回首页
  const handleBackToHome = () => {
    navigate('/')
  }

  if (!token) {
    return (
      <Container size="sm" py="xl">
        <Center>
          <Card withBorder shadow="md" p="xl" radius="md" w="100%">
            <Stack gap="md" ta="center">
              <IconAlertCircle size={48} color="var(--mantine-color-red-6)" />
              <Title order={2} c="red">
                激活链接无效
              </Title>
              <Text c="dimmed">激活链接格式不正确，请检查邮件中的链接是否完整。</Text>
              <Button onClick={handleBackToHome} leftSection={<IconArrowLeft size={16} />}>
                返回首页
              </Button>
            </Stack>
          </Card>
        </Center>
      </Container>
    )
  }

  if (statusLoading || activationStatus === 'checking') {
    return (
      <Container size="sm" py="xl">
        <Center>
          <Card withBorder shadow="md" p="xl" radius="md" w="100%">
            <Stack gap="md" ta="center">
              <Loader size="lg" />
              <Title order={2}>正在验证激活链接</Title>
              <Text c="dimmed">请稍候，正在验证您的激活链接...</Text>
            </Stack>
          </Card>
        </Center>
      </Container>
    )
  }

  return (
    <Container size="sm" py="xl">
      <Center>
        <Card withBorder shadow="md" p="xl" radius="md" w="100%">
          {activationStatus === 'valid' && (
            <Stack gap="md" ta="center">
              <IconCheck size={48} color="var(--mantine-color-green-6)" />
              <Title order={2} c="green">
                准备激活账号
              </Title>
              <Text c="dimmed">您的激活链接有效，点击下方按钮完成账号激活。</Text>
              <Button
                size="lg"
                onClick={handleActivate}
                loading={activationMutation.isPending}
                disabled={activationMutation.isPending}
              >
                激活账号
              </Button>
              <Button variant="outline" onClick={handleBackToHome}>
                返回首页
              </Button>
            </Stack>
          )}

          {activationStatus === 'activated' && (
            <Stack gap="md" ta="center">
              <IconCheck size={48} color="var(--mantine-color-green-6)" />
              <Title order={2} c="green">
                激活成功
              </Title>
              <Text c="dimmed">恭喜！您的账号已成功激活，现在可以登录系统开始学习了。</Text>
              <Button size="lg" onClick={handleBackToLogin}>
                立即登录
              </Button>
              <Button variant="outline" onClick={handleBackToHome}>
                返回首页
              </Button>
            </Stack>
          )}

          {activationStatus === 'expired' && (
            <Stack gap="md" ta="center">
              <IconAlertCircle size={48} color="var(--mantine-color-orange-6)" />
              <Title order={2} c="orange">
                激活链接已过期
              </Title>
              <Text c="dimmed">您的激活链接已过期（有效期24小时）。请重新发送激活邮件。</Text>

              {!showResendForm ? (
                <Group justify="center" gap="md">
                  <Button
                    color="orange"
                    leftSection={<IconMail size={16} />}
                    onClick={() => setShowResendForm(true)}
                  >
                    重新发送激活邮件
                  </Button>
                  <Button variant="outline" onClick={handleBackToHome}>
                    返回首页
                  </Button>
                </Group>
              ) : (
                <form onSubmit={resendForm.onSubmit(handleResendActivation)}>
                  <Stack gap="md">
                    <TextInput
                      label="邮箱地址"
                      placeholder="请输入注册时使用的邮箱"
                      required
                      {...resendForm.getInputProps('email')}
                    />
                    <Group justify="center" gap="md">
                      <Button
                        type="submit"
                        loading={resendMutation.isPending}
                        disabled={resendMutation.isPending}
                        leftSection={<IconMail size={16} />}
                      >
                        发送激活邮件
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setShowResendForm(false)}
                        disabled={resendMutation.isPending}
                      >
                        取消
                      </Button>
                    </Group>
                  </Stack>
                </form>
              )}
            </Stack>
          )}

          {activationStatus === 'invalid' && (
            <Stack gap="md" ta="center">
              <IconAlertCircle size={48} color="var(--mantine-color-red-6)" />
              <Title order={2} c="red">
                激活链接无效
              </Title>
              <Text c="dimmed">激活链接无效或已被使用。如需帮助，请联系系统管理员。</Text>
              <Group justify="center" gap="md">
                <Button onClick={handleBackToLogin}>前往登录</Button>
                <Button variant="outline" onClick={handleBackToHome}>
                  返回首页
                </Button>
              </Group>
            </Stack>
          )}
        </Card>
      </Center>
    </Container>
  )
}
