/**
 * 注册状态查询页面 - 需求1验收标准8：公开API查询审核进度
 * 无需登录即可查询审核进度和结果
 */

import {
  Alert,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Paper,
  Stack,
  Text,
  TextInput,
  Title,
  Timeline,
  Loader,
  Stepper,
  Tooltip,
  ActionIcon,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import {
  IconSearch,
  IconInfoCircle,
  IconCheck,
  IconX,
  IconClock,
  IconUser,
  IconFileText,
  IconEye,
  IconRefresh,
  IconCalendar,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { studentRegistration, teacherRegistration, registrationUtils } from '../../api/registration'

// 查询表单接口
interface StatusQueryForm {
  applicationId: string
}

export function RegistrationStatusPage(): JSX.Element {
  const { applicationId: urlApplicationId } = useParams<{ applicationId: string }>()
  const [currentApplicationId, setCurrentApplicationId] = useState<string>(urlApplicationId || '')

  const form = useForm<StatusQueryForm>({
    initialValues: {
      applicationId: urlApplicationId || '',
    },
    validate: {
      applicationId: value => {
        if (!value) return '请输入申请ID'
        if (!/^\d+$/.test(value)) return '申请ID应为数字'
        return null
      },
    },
  })

  // 查询申请状态
  const {
    data: statusData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['registration-status', currentApplicationId],
    queryFn: async () => {
      if (!currentApplicationId) return null

      const applicationId = parseInt(currentApplicationId)

      // 尝试学生注册状态查询
      try {
        return await studentRegistration.getStatus(applicationId)
      } catch (studentError) {
        // 如果学生查询失败，尝试教师注册状态查询
        try {
          return await teacherRegistration.getStatus(applicationId)
        } catch (teacherError) {
          throw new Error('申请ID不存在或查询失败')
        }
      }
    },
    enabled: !!currentApplicationId,
    retry: false,
  })

  const handleQuery = (values: StatusQueryForm) => {
    setCurrentApplicationId(values.applicationId)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <IconClock size={20} />
      case 'approved':
        return <IconCheck size={20} />
      case 'rejected':
        return <IconX size={20} />
      default:
        return <IconInfoCircle size={20} />
    }
  }

  const getStatusDescription = (status: string) => {
    switch (status) {
      case 'pending':
        return '您的申请正在审核中，请耐心等待管理员处理。'
      case 'approved':
        return '恭喜！您的申请已通过审核，账号已激活，可以正常登录使用。'
      case 'rejected':
        return '很抱歉，您的申请未通过审核，请根据审核意见补充材料后重新申请。'
      default:
        return '申请状态未知，请联系管理员。'
    }
  }

  const renderStatusCard = () => {
    if (!statusData) return null

    return (
      <Card withBorder shadow="md" p="xl" radius="md">
        <Stack>
          <Group justify="space-between">
            <Title order={3}>申请状态</Title>
            <Badge
              color={registrationUtils.getStatusColor(statusData.status)}
              variant="light"
              size="lg"
              leftSection={getStatusIcon(statusData.status)}
            >
              {registrationUtils.formatStatus(statusData.status)}
            </Badge>
          </Group>

          <Text size="sm" c="dimmed">
            申请ID：{statusData.application_id}
          </Text>

          <Alert
            icon={getStatusIcon(statusData.status)}
            color={registrationUtils.getStatusColor(statusData.status)}
            title="审核状态说明"
          >
            {getStatusDescription(statusData.status)}
          </Alert>

          {/* 审核进度 */}
          <Paper withBorder p="md" mt="md">
            <Group justify="space-between" mb="xs">
              <Text fw={500} size="sm">
                审核进度
              </Text>
              <Text size="sm" c="dimmed">
                {statusData.status === 'pending'
                  ? '审核中'
                  : statusData.status === 'approved'
                    ? '已完成'
                    : '已结束'}
              </Text>
            </Group>

            <Stepper
              active={
                statusData.status === 'pending' ? 1 : statusData.status === 'approved' ? 2 : 1
              }
              size="sm"
            >
              <Stepper.Step
                label="申请提交"
                description="资料已提交"
                icon={<IconFileText size={16} />}
              />
              <Stepper.Step
                label="审核中"
                description={statusData.status === 'pending' ? '管理员审核中' : '审核已完成'}
                icon={<IconEye size={16} />}
                color={
                  statusData.status === 'pending'
                    ? 'blue'
                    : statusData.status === 'approved'
                      ? 'green'
                      : 'red'
                }
              />
              <Stepper.Step
                label="审核结果"
                description={
                  statusData.status === 'approved'
                    ? '审核通过'
                    : statusData.status === 'rejected'
                      ? '审核驳回'
                      : '等待结果'
                }
                icon={
                  statusData.status === 'approved' ? (
                    <IconCheck size={16} />
                  ) : statusData.status === 'rejected' ? (
                    <IconX size={16} />
                  ) : (
                    <IconClock size={16} />
                  )
                }
                color={
                  statusData.status === 'approved'
                    ? 'green'
                    : statusData.status === 'rejected'
                      ? 'red'
                      : 'gray'
                }
              />
            </Stepper>

            {/* 预计完成时间 */}
            {statusData.status === 'pending' && (
              <Alert icon={<IconCalendar size="1rem" />} color="blue" mt="md">
                <Group justify="space-between">
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>
                      预计审核完成时间
                    </Text>
                    <Text size="sm" c="dimmed">
                      {statusData.estimated_review_time || '1-3个工作日'}
                    </Text>
                  </Stack>
                  <Tooltip label="刷新状态">
                    <ActionIcon variant="light" onClick={() => refetch()}>
                      <IconRefresh size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Alert>
            )}
          </Paper>

          {/* 时间线 */}
          <Timeline active={statusData.status === 'pending' ? 0 : 1} bulletSize={24} lineWidth={2}>
            <Timeline.Item bullet={<IconUser size={12} />} title="申请提交" color="blue">
              <Text size="sm" c="dimmed">
                {new Date(statusData.submitted_at).toLocaleString('zh-CN')}
              </Text>
              <Text size="xs" c="dimmed">
                申请已成功提交，等待管理员审核
              </Text>
            </Timeline.Item>

            {statusData.reviewed_at && (
              <Timeline.Item
                bullet={
                  statusData.status === 'approved' ? <IconCheck size={12} /> : <IconX size={12} />
                }
                title={statusData.status === 'approved' ? '审核通过' : '审核驳回'}
                color={statusData.status === 'approved' ? 'green' : 'red'}
              >
                <Text size="sm" c="dimmed">
                  {new Date(statusData.reviewed_at).toLocaleString('zh-CN')}
                </Text>
                {statusData.review_notes && (
                  <Text size="xs" c="dimmed">
                    审核意见：{statusData.review_notes}
                  </Text>
                )}
              </Timeline.Item>
            )}

            {statusData.status === 'pending' && (
              <Timeline.Item bullet={<IconClock size={12} />} title="等待审核" color="orange">
                <Text size="sm" c="dimmed">
                  预计审核时间：{statusData.estimated_review_time || '1-3个工作日'}
                </Text>
                <Text size="xs" c="dimmed">
                  管理员将尽快处理您的申请
                </Text>
              </Timeline.Item>
            )}
          </Timeline>

          {/* 审核意见 */}
          {statusData.review_notes && (
            <Paper withBorder p="md" bg="gray.0">
              <Text fw={500} size="sm" mb="xs">
                审核意见：
              </Text>
              <Text size="sm">{statusData.review_notes}</Text>
            </Paper>
          )}

          {/* 操作按钮 */}
          <Group justify="center" mt="md">
            <Button variant="light" onClick={() => refetch()} loading={isLoading}>
              刷新状态
            </Button>

            {statusData.status === 'rejected' && (
              <Button
                color="blue"
                onClick={() => {
                  // 根据申请类型跳转到对应的注册页面
                  const registrationPath =
                    statusData.application_id % 2 === 0 ? '/register/student' : '/register/teacher'

                  notifications.show({
                    title: '重新申请',
                    message: '正在跳转到注册页面...',
                    color: 'blue',
                  })

                  // 延迟跳转，让用户看到提示
                  setTimeout(() => {
                    window.location.href = registrationPath
                  }, 1000)
                }}
              >
                重新申请
              </Button>
            )}
          </Group>
        </Stack>
      </Card>
    )
  }

  return (
    <Container size="md" py="xl">
      <Title ta="center" mb="xl">
        注册申请状态查询
      </Title>

      {/* 查询表单 */}
      <Paper withBorder shadow="md" p="xl" radius="md" mb="xl">
        <form onSubmit={form.onSubmit(handleQuery)}>
          <Stack>
            <Group>
              <IconSearch size={24} />
              <Title order={3}>查询申请状态</Title>
            </Group>

            <TextInput
              label="申请ID"
              placeholder="请输入您的申请ID"
              description="申请ID是您提交注册申请后获得的数字编号"
              required
              {...form.getInputProps('applicationId')}
            />

            <Button type="submit" loading={isLoading} disabled={!form.values.applicationId}>
              查询状态
            </Button>
          </Stack>
        </form>
      </Paper>

      {/* 查询结果 */}
      {isLoading && currentApplicationId && (
        <Paper withBorder p="xl" ta="center">
          <Loader size="lg" />
          <Text mt="md">正在查询申请状态...</Text>
          <Text size="sm" c="dimmed" mt="xs">
            申请ID：{currentApplicationId}
          </Text>
        </Paper>
      )}

      {error && (
        <Alert color="red" icon={<IconX size="1rem" />} title="查询失败">
          {error.message || '申请ID不存在或查询失败，请检查申请ID是否正确'}
        </Alert>
      )}

      {statusData && renderStatusCard()}

      {/* 空状态提示 */}
      {!isLoading && !error && !statusData && currentApplicationId && (
        <Alert color="blue" icon={<IconInfoCircle size="1rem" />} title="查询提示">
          <Text size="sm">
            未找到申请ID为{' '}
            <Text span fw={500}>
              {currentApplicationId}
            </Text>{' '}
            的注册申请。
            <br />
            请检查申请ID是否正确，或联系管理员确认申请状态。
          </Text>
        </Alert>
      )}

      {/* 帮助信息 */}
      <Paper withBorder p="md" mt="xl" bg="gray.0">
        <Stack gap="xs">
          <Text size="sm" fw={500}>
            温馨提示：
          </Text>
          <Text size="sm" c="dimmed">
            • 申请ID是您提交注册申请后系统自动生成的唯一编号
          </Text>
          <Text size="sm" c="dimmed">
            • 学生申请通常在1-3个工作日内完成审核
          </Text>
          <Text size="sm" c="dimmed">
            • 教师申请通常在3-5个工作日内完成审核
          </Text>
          <Text size="sm" c="dimmed">
            • 如有疑问，请联系管理员：admin@cet4.com 或致电：400-123-4567
          </Text>
        </Stack>
      </Paper>
    </Container>
  )
}
