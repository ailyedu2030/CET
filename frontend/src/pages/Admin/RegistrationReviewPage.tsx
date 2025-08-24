/**
 * 管理员注册审核页面 - 查看和审核用户注册申请
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
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Textarea,
  Title,
  Pagination,
  TextInput,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconCheck,
  IconX,
  IconEye,
  IconUser,
  IconChalkboard,
  IconRefresh,
  IconSearch,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { adminReview, registrationUtils } from '../../api/registration'

// 注册申请接口
interface RegistrationApplication {
  id: number
  user_id: number
  username: string
  email: string
  application_type: 'student' | 'teacher'
  status: 'pending' | 'approved' | 'rejected'
  submitted_at: string
  reviewed_at?: string
  reviewer_id?: number
  review_notes?: string
  application_data: Record<string, any>
  submitted_documents: Record<string, any>
}

// 申请列表响应
interface ApplicationListResponse {
  total: number
  page: number
  size: number
  items: RegistrationApplication[]
}

// 过滤参数
interface FilterParams {
  application_type?: string
  status?: string
  page: number
  size: number
  search?: string
}

export function RegistrationReviewPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [selectedApplication, setSelectedApplication] = useState<RegistrationApplication | null>(
    null
  )
  const [reviewModalOpened, { open: openReviewModal, close: closeReviewModal }] =
    useDisclosure(false)
  const [detailModalOpened, { open: openDetailModal, close: closeDetailModal }] =
    useDisclosure(false)
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve')
  const [reviewNotes, setReviewNotes] = useState('')

  // 过滤状态
  const [filters, setFilters] = useState<FilterParams>({
    page: 1,
    size: 20,
  })

  // 获取申请列表
  const {
    data: applicationsData,
    isLoading,
    error,
    refetch,
  } = useQuery<ApplicationListResponse>({
    queryKey: ['registration-applications', filters],
    queryFn: async () => {
      // 调用真实API获取申请列表
      return await adminReview.getApplications({
        application_type: filters.application_type as 'student' | 'teacher' | undefined,
        status: filters.status as 'pending' | 'approved' | 'rejected' | undefined,
        page: filters.page,
        size: filters.size,
        search: filters.search,
      })
    },
  })

  // 审核申请
  const reviewMutation = useMutation<
    { message: string },
    Error,
    { application_id: number; action: string; review_notes?: string }
  >({
    mutationFn: async ({ application_id, action, review_notes }) => {
      // 调用真实API进行审核
      return await adminReview.reviewApplication({
        application_id,
        action: action as 'approve' | 'reject',
        review_notes,
      })
    },
    onSuccess: (data, _variables) => {
      notifications.show({
        title: '审核成功',
        message: data.message,
        color: 'green',
      })
      closeReviewModal()
      setReviewNotes('')
      // 刷新列表
      queryClient.invalidateQueries({ queryKey: ['registration-applications'] })
    },
    onError: error => {
      notifications.show({
        title: '审核失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handleReview = (application: RegistrationApplication, action: 'approve' | 'reject') => {
    setSelectedApplication(application)
    setReviewAction(action)
    setReviewNotes('')
    openReviewModal()
  }

  const handleViewDetails = (application: RegistrationApplication) => {
    setSelectedApplication(application)
    openDetailModal()
  }

  const handleSubmitReview = () => {
    if (!selectedApplication) return

    reviewMutation.mutate({
      application_id: selectedApplication.id,
      action: reviewAction,
      review_notes: reviewNotes,
    })
  }

  const getTypeIcon = (type: string) => {
    return type === 'teacher' ? <IconChalkboard size={16} /> : <IconUser size={16} />
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <Title order={1}>注册申请审核</Title>
        <Button leftSection={<IconRefresh size={16} />} variant="light" onClick={() => refetch()}>
          刷新
        </Button>
      </Group>

      {/* 过滤器 */}
      <Paper withBorder p="md" mb="lg">
        <Group>
          <TextInput
            placeholder="搜索用户名、邮箱或姓名"
            leftSection={<IconSearch size={16} />}
            value={filters.search || ''}
            onChange={event =>
              setFilters({ ...filters, search: event.currentTarget.value, page: 1 })
            }
          />

          <Select
            placeholder="申请类型"
            data={[
              { value: '', label: '全部类型' },
              { value: 'student', label: '学生' },
              { value: 'teacher', label: '教师' },
            ]}
            value={filters.application_type || ''}
            onChange={value =>
              setFilters({ ...filters, application_type: value || undefined, page: 1 })
            }
          />

          <Select
            placeholder="审核状态"
            data={[
              { value: '', label: '全部状态' },
              { value: 'pending', label: '待审核' },
              { value: 'approved', label: '已通过' },
              { value: 'rejected', label: '已驳回' },
            ]}
            value={filters.status || ''}
            onChange={value => setFilters({ ...filters, status: value || undefined, page: 1 })}
          />
        </Group>
      </Paper>

      {/* 统计信息 */}
      {applicationsData && (
        <SimpleGrid cols={4} mb="lg">
          <Card withBorder padding="md" radius="md">
            <Text size="sm" c="dimmed">
              总申请数
            </Text>
            <Text size="xl" fw="bold">
              {applicationsData.total}
            </Text>
          </Card>
          <Card withBorder padding="md" radius="md">
            <Text size="sm" c="dimmed">
              待审核
            </Text>
            <Text size="xl" fw="bold" c="orange">
              {applicationsData.items.filter(app => app.status === 'pending').length}
            </Text>
          </Card>
          <Card withBorder padding="md" radius="md">
            <Text size="sm" c="dimmed">
              已通过
            </Text>
            <Text size="xl" fw="bold" c="green">
              {applicationsData.items.filter(app => app.status === 'approved').length}
            </Text>
          </Card>
          <Card withBorder padding="md" radius="md">
            <Text size="sm" c="dimmed">
              已驳回
            </Text>
            <Text size="xl" fw="bold" c="red">
              {applicationsData.items.filter(app => app.status === 'rejected').length}
            </Text>
          </Card>
        </SimpleGrid>
      )}

      {/* 申请列表 */}
      {isLoading ? (
        <Text ta="center">加载中...</Text>
      ) : error ? (
        <Alert color="red">加载申请列表失败，请刷新页面重试</Alert>
      ) : (
        <>
          <Paper withBorder>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>申请人</Table.Th>
                  <Table.Th>类型</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>提交时间</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {applicationsData?.items.map(application => (
                  <Table.Tr key={application.id}>
                    <Table.Td>
                      <Stack gap={2}>
                        <Text fw={500}>{application.application_data['real_name'] || '未知'}</Text>
                        <Text size="sm" c="dimmed">
                          {application.username} ({application.email})
                        </Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {getTypeIcon(application.application_type)}
                        <Text size="sm">
                          {registrationUtils.formatType(application.application_type)}
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={registrationUtils.getStatusColor(application.status)}
                        variant="light"
                      >
                        {registrationUtils.formatStatus(application.status)}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {new Date(application.submitted_at).toLocaleString('zh-CN')}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Button
                          size="xs"
                          variant="light"
                          leftSection={<IconEye size={14} />}
                          onClick={() => handleViewDetails(application)}
                        >
                          详情
                        </Button>
                        {application.status === 'pending' && (
                          <>
                            <Button
                              size="xs"
                              color="green"
                              leftSection={<IconCheck size={14} />}
                              onClick={() => handleReview(application, 'approve')}
                            >
                              通过
                            </Button>
                            <Button
                              size="xs"
                              color="red"
                              leftSection={<IconX size={14} />}
                              onClick={() => handleReview(application, 'reject')}
                            >
                              驳回
                            </Button>
                          </>
                        )}
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>

          {/* 分页 */}
          {applicationsData && applicationsData.total > filters.size && (
            <Group justify="center" mt="lg">
              <Pagination
                total={Math.ceil(applicationsData.total / filters.size)}
                value={filters.page}
                onChange={page => setFilters({ ...filters, page })}
              />
            </Group>
          )}
        </>
      )}

      {/* 审核模态框 */}
      <Modal
        opened={reviewModalOpened}
        onClose={closeReviewModal}
        title={`${reviewAction === 'approve' ? '通过' : '驳回'}申请`}
        size="md"
      >
        <Stack>
          <Text>
            确定要{reviewAction === 'approve' ? '通过' : '驳回'}用户{' '}
            <Text span fw={500}>
              {selectedApplication?.application_data['real_name']}
            </Text>{' '}
            的{registrationUtils.formatType(selectedApplication?.application_type || '')}
            注册申请吗？
          </Text>

          <Textarea
            label="审核备注"
            placeholder={`请输入${reviewAction === 'approve' ? '通过' : '驳回'}原因...`}
            value={reviewNotes}
            onChange={event => setReviewNotes(event.currentTarget.value)}
            rows={3}
          />

          <Group justify="flex-end">
            <Button variant="light" onClick={closeReviewModal}>
              取消
            </Button>
            <Button
              color={reviewAction === 'approve' ? 'green' : 'red'}
              loading={reviewMutation.isPending}
              onClick={handleSubmitReview}
            >
              确认{reviewAction === 'approve' ? '通过' : '驳回'}
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 详情模态框 */}
      <Modal opened={detailModalOpened} onClose={closeDetailModal} title="申请详情" size="lg">
        {selectedApplication && (
          <Stack>
            <Group>
              <Text fw={500}>申请人：</Text>
              <Text>{selectedApplication.application_data['real_name'] || '未知'}</Text>
            </Group>

            <Group>
              <Text fw={500}>用户名：</Text>
              <Text>{selectedApplication.username}</Text>
            </Group>

            <Group>
              <Text fw={500}>邮箱：</Text>
              <Text>{selectedApplication.email}</Text>
            </Group>

            <Group>
              <Text fw={500}>申请类型：</Text>
              <Badge>{registrationUtils.formatType(selectedApplication.application_type)}</Badge>
            </Group>

            <Group>
              <Text fw={500}>当前状态：</Text>
              <Badge color={registrationUtils.getStatusColor(selectedApplication.status)}>
                {registrationUtils.formatStatus(selectedApplication.status)}
              </Badge>
            </Group>

            <Stack>
              <Text fw={500}>申请信息：</Text>
              <Paper withBorder p="md" bg="gray.0">
                {Object.entries(selectedApplication.application_data).map(([key, value]) => (
                  <Group key={key} justify="space-between">
                    <Text size="sm" c="dimmed">
                      {key}:
                    </Text>
                    <Text size="sm">{String(value) || '-'}</Text>
                  </Group>
                ))}
              </Paper>
            </Stack>

            {selectedApplication.application_type === 'teacher' && (
              <Stack>
                <Text fw={500}>提交的资质材料：</Text>
                <Paper withBorder p="md" bg="gray.0">
                  {Object.entries(selectedApplication.submitted_documents).map(([key, value]) => (
                    <Group key={key} justify="space-between">
                      <Text size="sm" c="dimmed">
                        {key}:
                      </Text>
                      <Text size="sm">{value ? '已提交' : '未提交'}</Text>
                    </Group>
                  ))}
                </Paper>
              </Stack>
            )}

            {selectedApplication.review_notes && (
              <Stack>
                <Text fw={500}>审核备注：</Text>
                <Paper withBorder p="md" bg="gray.0">
                  <Text size="sm">{selectedApplication.review_notes}</Text>
                </Paper>
              </Stack>
            )}

            {selectedApplication.reviewed_at && (
              <Group>
                <Text fw={500}>审核时间：</Text>
                <Text size="sm">
                  {new Date(selectedApplication.reviewed_at).toLocaleString('zh-CN')}
                </Text>
              </Group>
            )}
          </Stack>
        )}
      </Modal>
    </Container>
  )
}
