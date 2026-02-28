/**
 * 手机验证码组件
 *
 * 实现🔥需求20验收标准3：
 * - 手机号验证码验证
 * - 验证码有效期5分钟
 * - 60秒内重发限制
 */

import { TextInput, Button, Group, Stack, Text, Alert, PinInput, Paper } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconPhone, IconClock, IconCheck, IconAlertCircle } from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { useState, useEffect, useCallback } from 'react'

import {
  sendRegistrationSMS,
  verifyRegistrationSMS,
  type SendSMSRequest,
  type VerifySMSRequest,
  type VerificationResponse,
} from '../../api/verification'

// 组件属性接口
interface PhoneVerificationProps {
  onVerificationSuccess: (phoneNumber: string) => void
  onVerificationError?: (error: string) => void
  purpose?: string
  disabled?: boolean
}

export function PhoneVerification({
  onVerificationSuccess,
  onVerificationError,
  purpose = 'register',
  disabled = false,
}: PhoneVerificationProps): JSX.Element {
  const [step, setStep] = useState<'phone' | 'code'>('phone')
  const [countdown, setCountdown] = useState(0)
  const [verificationCode, setVerificationCode] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')

  // 手机号表单
  const phoneForm = useForm({
    initialValues: {
      phone: '',
    },
    validate: {
      phone: (value: string) => {
        if (!value) return '请输入手机号'
        if (!/^1[3-9]\d{9}$/.test(value)) return '请输入正确的手机号格式'
        return null
      },
    },
  })

  // 发送验证码
  const sendSMSMutation = useMutation<VerificationResponse, Error, SendSMSRequest>({
    mutationFn: sendRegistrationSMS,
    onSuccess: data => {
      if (data.success) {
        notifications.show({
          title: '验证码发送成功',
          message: `验证码已发送至 ${data.masked_target}，有效期5分钟`,
          color: 'green',
          icon: <IconCheck size={16} />,
        })
        setStep('code')
        setCountdown(60) // 60秒倒计时
        setPhoneNumber(phoneForm.values.phone)
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

  // 验证验证码
  const verifySMSMutation = useMutation<VerificationResponse, Error, VerifySMSRequest>({
    mutationFn: verifyRegistrationSMS,
    onSuccess: data => {
      if (data.success) {
        notifications.show({
          title: '验证成功',
          message: '手机号验证通过',
          color: 'green',
          icon: <IconCheck size={16} />,
        })
        onVerificationSuccess(phoneNumber)
      } else {
        notifications.show({
          title: '验证失败',
          message: `${data.message}${data.remaining_attempts ? `，还有${data.remaining_attempts}次机会` : ''}`,
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        })
        if (onVerificationError) {
          onVerificationError(data.message)
        }
      }
    },
    onError: error => {
      const errorMessage = error.message || '验证失败，请稍后重试'
      notifications.show({
        title: '验证失败',
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      })
      if (onVerificationError) {
        onVerificationError(errorMessage)
      }
    },
  })

  // 倒计时逻辑
  useEffect(() => {
    let timer: number | null = null
    if (countdown > 0) {
      timer = window.setTimeout(() => {
        setCountdown(countdown - 1)
      }, 1000)
    }
    return () => {
      if (timer) {
        clearTimeout(timer)
      }
    }
  }, [countdown])

  // 发送验证码
  const handleSendCode = useCallback(
    (values: { phone: string }) => {
      sendSMSMutation.mutate({
        phone_number: values.phone,
        purpose,
      })
    },
    [sendSMSMutation, purpose]
  )

  // 重新发送验证码
  const handleResendCode = useCallback(() => {
    if (countdown === 0) {
      sendSMSMutation.mutate({
        phone_number: phoneNumber,
        purpose,
      })
    }
  }, [countdown, phoneNumber, sendSMSMutation, purpose])

  // 验证验证码
  const handleVerifyCode = useCallback(() => {
    if (verificationCode.length === 6) {
      verifySMSMutation.mutate({
        target: phoneNumber,
        verification_code: verificationCode,
        purpose,
      })
    }
  }, [verificationCode, phoneNumber, verifySMSMutation, purpose])

  // 验证码输入完成时自动验证
  useEffect(() => {
    if (verificationCode.length === 6 && !verifySMSMutation.isPending) {
      handleVerifyCode()
    }
  }, [verificationCode, verifySMSMutation.isPending, handleVerifyCode])

  // 返回上一步
  const handleBackToPhone = useCallback(() => {
    setStep('phone')
    setVerificationCode('')
    setCountdown(0)
  }, [])

  if (step === 'phone') {
    return (
      <Paper withBorder p="md">
        <Stack gap="md">
          <Group gap="xs">
            <IconPhone size={20} />
            <Text fw={600}>手机号验证</Text>
          </Group>

          <form onSubmit={phoneForm.onSubmit(handleSendCode)}>
            <Stack gap="md">
              <TextInput
                label="手机号码"
                placeholder="请输入11位手机号码"
                required
                disabled={disabled || sendSMSMutation.isPending}
                {...phoneForm.getInputProps('phone')}
              />

              <Button
                type="submit"
                loading={sendSMSMutation.isPending}
                disabled={disabled || sendSMSMutation.isPending}
                fullWidth
              >
                发送验证码
              </Button>
            </Stack>
          </form>

          <Alert color="blue" icon={<IconClock size={16} />}>
            <Text size="sm">
              验证码有效期为5分钟，请及时输入。如未收到验证码，请检查手机号是否正确。
            </Text>
          </Alert>
        </Stack>
      </Paper>
    )
  }

  return (
    <Paper withBorder p="md">
      <Stack gap="md">
        <Group gap="xs">
          <IconPhone size={20} />
          <Text fw={600}>输入验证码</Text>
        </Group>

        <Text size="sm" c="dimmed">
          验证码已发送至 {phoneNumber.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')}
        </Text>

        <Stack gap="md" align="center">
          <PinInput
            length={6}
            value={verificationCode}
            onChange={setVerificationCode}
            disabled={disabled || verifySMSMutation.isPending}
            size="lg"
            type="number"
          />

          <Group gap="md">
            <Button
              variant="outline"
              onClick={handleBackToPhone}
              disabled={disabled || verifySMSMutation.isPending}
            >
              返回修改手机号
            </Button>

            <Button
              onClick={handleResendCode}
              disabled={disabled || countdown > 0 || sendSMSMutation.isPending}
              variant="light"
            >
              {countdown > 0 ? `${countdown}秒后重发` : '重新发送'}
            </Button>
          </Group>
        </Stack>

        {verifySMSMutation.isPending && (
          <Alert color="blue" icon={<IconClock size={16} />}>
            <Text size="sm">正在验证验证码...</Text>
          </Alert>
        )}

        <Alert color="orange" icon={<IconClock size={16} />}>
          <Text size="sm">验证码有效期为5分钟，请及时输入。输入完成后将自动验证。</Text>
        </Alert>
      </Stack>
    </Paper>
  )
}
