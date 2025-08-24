/**
 * 教师资质管理页面 - 查看和更新资质认证状态
 */

import {
  Alert,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Text,
  Title,
  FileInput,
  Divider,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconCertificate,
  IconCheck,
  IconAlertTriangle,
  IconUpload,
  IconEye,
  IconRefresh,
  IconInfoCircle,
  IconClock,
  IconCalendar,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useAuthStore } from '../../stores/authStore'

// 资质状态接口
interface QualificationStatus {
  user_id: number
  qualification_status: 'complete' | 'partial' | 'incomplete'
  message: string
  missing_items: string[]
  completed_items: string[]
  completion_rate: number
  certificate_status: {
    teacher_certificate: boolean
    qualification_certificates: boolean
    honor_certificates: boolean
  }
  is_verified: boolean
  profile_created_at: string
  last_updated: string
  // 新增到期提醒相关字段
  expiry_warnings: Array<{
    certificate_type: string
    certificate_name: string
    expiry_date: string
    days_until_expiry: number
    urgency: 'high' | 'medium' | 'low'
  }>
  next_review_date?: string
  annual_review_status: 'pending' | 'completed' | 'overdue'
}

// 证书类型配置
const certificateConfig = {
  teacher_certificate: {
    label: '教师资格证书',
    description: '教师从业的基本资质证明',
    required: true,
  },
  qualification_certificates: {
    label: '职业资格证书',
    description: '专业能力认证，如英语等级证书等',
    required: false,
  },
  honor_certificates: {
    label: '荣誉证书',
    description: '教学成果、奖项等荣誉认证',
    required: false,
  },
}

export function TeacherQualificationPage(): JSX.Element {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [uploadModalOpened, { open: openUploadModal, close: closeUploadModal }] =
    useDisclosure(false)
  const [currentCertificateType, setCurrentCertificateType] = useState<string>('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)

  // 获取资质状态
  const {
    data: qualificationStatus,
    isLoading,
    error,
    refetch,
  } = useQuery<QualificationStatus>({
    queryKey: ['teacher-qualification-status', user?.id],
    queryFn: async () => {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      return {
        user_id: Number(user?.id) || 1,
        qualification_status: 'partial' as const,
        message: '资质认证基本完整，建议补充缺失材料',
        missing_items: ['honor_certificates'],
        completed_items: [
          'real_name',
          'subject',
          'teacher_certificate',
          'qualification_certificates',
        ],
        completion_rate: 85.7,
        certificate_status: {
          teacher_certificate: true,
          qualification_certificates: true,
          honor_certificates: false,
        },
        is_verified: true,
        profile_created_at: '2024-01-15T08:00:00Z',
        last_updated: '2024-01-20T14:30:00Z',
        // 到期提醒数据
        expiry_warnings: [
          {
            certificate_type: 'teacher_certificate',
            certificate_name: '教师资格证',
            expiry_date: '2024-12-31T23:59:59Z',
            days_until_expiry: 45,
            urgency: 'medium' as const,
          },
        ],
        next_review_date: '2024-12-01T00:00:00Z',
        annual_review_status: 'pending' as const,
      } as QualificationStatus
    },
    enabled: !!user?.id,
  })

  // 上传证书
  const uploadMutation = useMutation<
    { message: string; file_path: string },
    Error,
    { file: File; certificate_type: string; description?: string }
  >({
    mutationFn: async ({ file, certificate_type, description: _description }) => {
      // 模拟文件上传
      await new Promise(resolve => setTimeout(resolve, 2000))

      return {
        message: '资质材料上传成功',
        file_path: `/uploads/certificates/${certificate_type}/${file.name}`,
      }
    },
    onSuccess: data => {
      notifications.show({
        title: '上传成功',
        message: data.message,
        color: 'green',
      })
      closeUploadModal()
      setUploadFile(null)
      // 刷新资质状态
      queryClient.invalidateQueries({ queryKey: ['teacher-qualification-status'] })
    },
    onError: error => {
      notifications.show({
        title: '上传失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handleUploadCertificate = (certificateType: string) => {
    setCurrentCertificateType(certificateType)
    openUploadModal()
  }

  const handleSubmitUpload = () => {
    if (!uploadFile) {
      notifications.show({
        title: '请选择文件',
        message: '请选择要上传的证书文件',
        color: 'orange',
      })
      return
    }

    uploadMutation.mutate({
      file: uploadFile,
      certificate_type: currentCertificateType,
      description:
        certificateConfig[currentCertificateType as keyof typeof certificateConfig]?.label,
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'green'
      case 'partial':
        return 'yellow'
      case 'incomplete':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'complete':
        return '认证完整'
      case 'partial':
        return '基本完整'
      case 'incomplete':
        return '认证不完整'
      default:
        return '未知状态'
    }
  }

  if (isLoading) {
    return (
      <Container size="lg" py="xl">
        <Text ta="center">加载中...</Text>
      </Container>
    )
  }

  if (error) {
    return (
      <Container size="lg" py="xl">
        <Alert icon={<IconAlertTriangle size="1rem" />} title="加载失败" color="red">
          获取资质信息失败，请刷新页面重试
        </Alert>
      </Container>
    )
  }

  return (
    <Container size="lg" py="xl">
      <Group justify="space-between" mb="xl">
        <Title order={1}>教师资质认证</Title>
        <Button leftSection={<IconRefresh size={16} />} variant="light" onClick={() => refetch()}>
          刷新状态
        </Button>
      </Group>

      {/* 资质状态概览 */}
      <Paper withBorder p="xl" mb="xl" radius="md">
        <Group justify="space-between" align="flex-start">
          <Stack gap="md">
            <Group>
              <Title order={3}>认证状态</Title>
              <Badge
                color={getStatusColor(qualificationStatus?.qualification_status || '')}
                variant="filled"
                size="lg"
              >
                {getStatusLabel(qualificationStatus?.qualification_status || '')}
              </Badge>
            </Group>
            <Text size="lg" c="dimmed">
              {qualificationStatus?.message}
            </Text>
          </Stack>

          <Stack align="center">
            <Text size="xl" fw="bold">
              {qualificationStatus?.completion_rate.toFixed(1)}%
            </Text>
            <Progress
              value={qualificationStatus?.completion_rate || 0}
              color={getStatusColor(qualificationStatus?.qualification_status || '')}
              size="lg"
              w={120}
            />
            <Text size="sm" c="dimmed">
              完成度
            </Text>
          </Stack>
        </Group>

        {qualificationStatus?.missing_items && qualificationStatus.missing_items.length > 0 && (
          <Alert icon={<IconInfoCircle size="1rem" />} title="待完善项目" color="orange" mt="md">
            <Text size="sm">还需完善：{qualificationStatus.missing_items.join('、')}</Text>
          </Alert>
        )}
      </Paper>

      {/* 到期提醒 */}
      {qualificationStatus?.expiry_warnings && qualificationStatus.expiry_warnings.length > 0 && (
        <Paper withBorder p="xl" mb="xl" radius="md">
          <Group mb="md">
            <IconClock size={24} color="orange" />
            <Title order={3}>到期提醒</Title>
          </Group>

          <Stack gap="md">
            {qualificationStatus.expiry_warnings.map((warning, index) => (
              <Alert
                key={index}
                icon={<IconAlertTriangle size="1rem" />}
                color={
                  warning.urgency === 'high'
                    ? 'red'
                    : warning.urgency === 'medium'
                      ? 'orange'
                      : 'yellow'
                }
                title={`${warning.certificate_name}即将到期`}
              >
                <Group justify="space-between">
                  <Stack gap="xs">
                    <Text size="sm">
                      到期时间：{new Date(warning.expiry_date).toLocaleDateString('zh-CN')}
                    </Text>
                    <Text size="sm" c="dimmed">
                      剩余 {warning.days_until_expiry} 天
                    </Text>
                  </Stack>
                  <Button size="xs" variant="light">
                    立即更新
                  </Button>
                </Group>
              </Alert>
            ))}
          </Stack>

          {/* 年度审核提醒 */}
          {qualificationStatus.annual_review_status === 'pending' &&
            qualificationStatus.next_review_date && (
              <Alert icon={<IconCalendar size="1rem" />} color="blue" title="年度资质审核" mt="md">
                <Group justify="space-between">
                  <Stack gap="xs">
                    <Text size="sm">
                      下次审核时间：
                      {new Date(qualificationStatus.next_review_date).toLocaleDateString('zh-CN')}
                    </Text>
                    <Text size="sm" c="dimmed">
                      请提前准备相关资质材料
                    </Text>
                  </Stack>
                  <Button size="xs" variant="light" color="blue">
                    查看详情
                  </Button>
                </Group>
              </Alert>
            )}
        </Paper>
      )}

      {/* 证书管理 */}
      <Title order={3} mb="md">
        资质证书管理
      </Title>
      <SimpleGrid cols={3} spacing="md" mb="xl">
        {Object.entries(certificateConfig).map(([key, config]) => {
          const hasFile =
            qualificationStatus?.certificate_status[
              key as keyof typeof qualificationStatus.certificate_status
            ]

          return (
            <Card key={key} withBorder shadow="sm" padding="lg" radius="md">
              <Stack>
                <Group justify="space-between">
                  <IconCertificate size={24} color={hasFile ? 'green' : 'gray'} />
                  {hasFile && <IconCheck size={20} color="green" />}
                </Group>

                <Title order={4}>{config.label}</Title>
                <Text size="sm" c="dimmed">
                  {config.description}
                </Text>

                {config.required && (
                  <Badge color="red" variant="light" size="sm">
                    必需
                  </Badge>
                )}

                <Group justify="space-between" mt="auto">
                  <Badge color={hasFile ? 'green' : 'gray'} variant="light">
                    {hasFile ? '已上传' : '未上传'}
                  </Badge>
                  <Group>
                    {hasFile && (
                      <Button size="xs" variant="light" leftSection={<IconEye size={14} />}>
                        查看
                      </Button>
                    )}
                    <Button
                      size="xs"
                      leftSection={<IconUpload size={14} />}
                      onClick={() => handleUploadCertificate(key)}
                    >
                      {hasFile ? '更新' : '上传'}
                    </Button>
                  </Group>
                </Group>
              </Stack>
            </Card>
          )
        })}
      </SimpleGrid>

      {/* 认证历史 */}
      <Title order={3} mb="md">
        认证记录
      </Title>
      <Paper withBorder p="lg" radius="md">
        <Stack>
          <Group>
            <Text fw={500}>档案创建时间：</Text>
            <Text>
              {qualificationStatus?.profile_created_at
                ? new Date(qualificationStatus.profile_created_at).toLocaleDateString('zh-CN')
                : '未知'}
            </Text>
          </Group>
          <Divider />
          <Group>
            <Text fw={500}>最后更新时间：</Text>
            <Text>
              {qualificationStatus?.last_updated
                ? new Date(qualificationStatus.last_updated).toLocaleDateString('zh-CN')
                : '未知'}
            </Text>
          </Group>
          <Divider />
          <Group>
            <Text fw={500}>验证状态：</Text>
            <Badge color={qualificationStatus?.is_verified ? 'green' : 'orange'}>
              {qualificationStatus?.is_verified ? '已验证' : '待验证'}
            </Badge>
          </Group>
        </Stack>
      </Paper>

      {/* 帮助信息 */}
      <Alert icon={<IconInfoCircle size="1rem" />} title="认证说明" color="blue" mt="xl">
        <Text size="sm">
          • 教师资格证书是必需材料，请务必上传
          <br />
          • 职业资格证书和荣誉证书有助于提升认证完整度
          <br />
          • 所有证书都需要管理员审核后生效
          <br />• 如有疑问，请联系管理员获取帮助
        </Text>
      </Alert>

      {/* 上传模态框 */}
      <Modal
        opened={uploadModalOpened}
        onClose={closeUploadModal}
        title={`上传${certificateConfig[currentCertificateType as keyof typeof certificateConfig]?.label || '证书'}`}
        size="md"
      >
        <Stack>
          <Text size="sm" c="dimmed">
            {
              certificateConfig[currentCertificateType as keyof typeof certificateConfig]
                ?.description
            }
          </Text>

          <FileInput
            label="选择文件"
            placeholder="请选择证书文件"
            leftSection={<IconUpload size={14} />}
            accept="image/*,.pdf"
            value={uploadFile}
            onChange={setUploadFile}
          />

          <Alert icon={<IconInfoCircle size="1rem" />} color="blue">
            支持JPG、PNG、PDF格式，文件不超过5MB
          </Alert>

          <Group justify="flex-end">
            <Button variant="light" onClick={closeUploadModal}>
              取消
            </Button>
            <Button
              onClick={handleSubmitUpload}
              loading={uploadMutation.isPending}
              disabled={!uploadFile}
            >
              上传
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
