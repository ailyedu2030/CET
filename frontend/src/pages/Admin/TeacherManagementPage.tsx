/**
 * 教师信息管理页面 - 需求2：基础信息管理
 * 实现教师信息的CRUD操作、教学状态跟踪、薪酬管理、资质审核等功能
 */

import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  NumberInput,
  Pagination,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconEye, IconSearch, IconCurrencyYuan, IconCertificate } from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

// 教师信息接口
interface Teacher {
  id: number
  username: string
  email: string
  is_active: boolean
  profile: {
    real_name: string
    age?: number
    gender?: string
    title?: string
    subject?: string
    phone?: string
    introduction?: string
    teaching_status: string
    hire_date?: string
    contract_end_date?: string
    monthly_hours: number
    total_evaluations: number
    hourly_rate: number
    monthly_salary: number
    total_salary_paid: number
    last_salary_date?: string
    qualification_status: string
    last_review_date?: string
    next_review_date?: string
    qualification_notes?: string
    total_teaching_hours: number
    student_count: number
    average_rating: number
  }
  created_at: string
  updated_at: string
}

// 教师列表响应接口
interface TeacherListResponse {
  items: Teacher[]
  total: number
  page: number
  size: number
  pages: number
}

// 薪酬更新请求接口
interface SalaryUpdateRequest {
  hourly_rate: number
  monthly_salary: number
}

// 资质审核请求接口
interface QualificationReviewRequest {
  qualification_status: string
  notes?: string
}

export function TeacherManagementPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null)

  const [detailOpened, { open: openDetail, close: closeDetail }] = useDisclosure(false)
  const [salaryOpened, { open: openSalary, close: closeSalary }] = useDisclosure(false)
  const [qualificationOpened, { open: openQualification, close: closeQualification }] =
    useDisclosure(false)

  // 薪酬更新表单
  const salaryForm = useForm<SalaryUpdateRequest>({
    initialValues: {
      hourly_rate: 0,
      monthly_salary: 0,
    },
    validate: {
      hourly_rate: value => (value < 0 ? '课时费不能为负数' : null),
      monthly_salary: value => (value < 0 ? '月薪不能为负数' : null),
    },
  })

  // 资质审核表单
  const qualificationForm = useForm<QualificationReviewRequest>({
    initialValues: {
      qualification_status: '',
      notes: '',
    },
  })

  // 获取教师列表
  const {
    data: teachersData,
    isLoading,
    error,
  } = useQuery<TeacherListResponse>({
    queryKey: ['teachers', page, search, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        size: '20',
      })

      if (search) params.append('search', search)
      if (statusFilter) params.append('teaching_status', statusFilter)

      const response = await fetch(`/api/v1/users/basic-info/teachers?${params}`)
      if (!response.ok) {
        throw new Error('获取教师列表失败')
      }
      return response.json()
    },
  })

  // 更新教师薪酬
  const salaryMutation = useMutation({
    mutationFn: async ({ teacherId, data }: { teacherId: number; data: SalaryUpdateRequest }) => {
      const response = await fetch(`/api/v1/users/basic-info/teachers/${teacherId}/salary`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('更新教师薪酬失败')
      }
      return response.json()
    },
    onSuccess: () => {
      notifications.show({
        title: '更新成功',
        message: '教师薪酬已更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['teachers'] })
      closeSalary()
    },
    onError: (error: Error) => {
      notifications.show({
        title: '更新失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 资质审核
  const qualificationMutation = useMutation({
    mutationFn: async ({
      teacherId,
      data,
    }: {
      teacherId: number
      data: QualificationReviewRequest
    }) => {
      const response = await fetch(`/api/v1/users/basic-info/teachers/${teacherId}/qualification`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('资质审核失败')
      }
      return response.json()
    },
    onSuccess: () => {
      notifications.show({
        title: '审核成功',
        message: '教师资质状态已更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['teachers'] })
      closeQualification()
    },
    onError: (error: Error) => {
      notifications.show({
        title: '审核失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handleSalaryUpdate = (teacher: Teacher) => {
    setSelectedTeacher(teacher)
    salaryForm.setValues({
      hourly_rate: teacher.profile.hourly_rate,
      monthly_salary: teacher.profile.monthly_salary,
    })
    openSalary()
  }

  const handleQualificationReview = (teacher: Teacher) => {
    setSelectedTeacher(teacher)
    qualificationForm.setValues({
      qualification_status: teacher.profile.qualification_status,
      notes: teacher.profile.qualification_notes || '',
    })
    openQualification()
  }

  const handleSalarySubmit = (values: SalaryUpdateRequest) => {
    if (!selectedTeacher) return

    salaryMutation.mutate({
      teacherId: selectedTeacher.id,
      data: values,
    })
  }

  const handleQualificationSubmit = (values: QualificationReviewRequest) => {
    if (!selectedTeacher) return

    qualificationMutation.mutate({
      teacherId: selectedTeacher.id,
      data: values,
    })
  }

  const getTeachingStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green'
      case 'inactive':
        return 'gray'
      case 'suspended':
        return 'red'
      case 'retired':
        return 'blue'
      default:
        return 'gray'
    }
  }

  const getTeachingStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return '在职'
      case 'inactive':
        return '休假'
      case 'suspended':
        return '停职'
      case 'retired':
        return '退休'
      default:
        return '未知'
    }
  }

  const getQualificationStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'green'
      case 'pending':
        return 'orange'
      case 'rejected':
        return 'red'
      case 'expired':
        return 'gray'
      default:
        return 'gray'
    }
  }

  const getQualificationStatusLabel = (status: string) => {
    switch (status) {
      case 'approved':
        return '已通过'
      case 'pending':
        return '待审核'
      case 'rejected':
        return '未通过'
      case 'expired':
        return '已过期'
      default:
        return '未知'
    }
  }

  return (
    <Container size="xl" py="md">
      <Stack>
        <Title order={2}>教师信息管理</Title>

        {/* 搜索和过滤 */}
        <Paper withBorder p="md">
          <Group>
            <TextInput
              placeholder="搜索教师姓名、用户名或邮箱"
              leftSection={<IconSearch size={16} />}
              value={search}
              onChange={event => setSearch(event.currentTarget.value)}
              style={{ flex: 1 }}
            />

            <Select
              placeholder="教学状态"
              data={[
                { value: '', label: '全部状态' },
                { value: 'active', label: '在职' },
                { value: 'inactive', label: '休假' },
                { value: 'suspended', label: '停职' },
                { value: 'retired', label: '退休' },
              ]}
              value={statusFilter}
              onChange={setStatusFilter}
              clearable
            />
          </Group>
        </Paper>

        {/* 教师列表 */}
        <Paper withBorder>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>教师信息</Table.Th>
                <Table.Th>教学状态</Table.Th>
                <Table.Th>教学数据</Table.Th>
                <Table.Th>薪酬信息</Table.Th>
                <Table.Th>资质状态</Table.Th>
                <Table.Th>操作</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {teachersData?.items.map(teacher => (
                <Table.Tr key={teacher.id}>
                  <Table.Td>
                    <Stack gap="xs">
                      <Text fw={500}>{teacher.profile.real_name}</Text>
                      <Text size="sm" c="dimmed">
                        {teacher.username} • {teacher.email}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {teacher.profile.title} • {teacher.profile.subject}
                      </Text>
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Badge
                      color={getTeachingStatusColor(teacher.profile.teaching_status)}
                      variant="light"
                    >
                      {getTeachingStatusLabel(teacher.profile.teaching_status)}
                    </Badge>
                  </Table.Td>

                  <Table.Td>
                    <Stack gap="xs">
                      <Text size="sm">教学时长：{teacher.profile.total_teaching_hours}h</Text>
                      <Text size="sm">学生人数：{teacher.profile.student_count}</Text>
                      <Text size="sm">平均评分：{teacher.profile.average_rating.toFixed(1)}</Text>
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Stack gap="xs">
                      <Text size="sm">课时费：¥{teacher.profile.hourly_rate}/h</Text>
                      <Text size="sm">月薪：¥{teacher.profile.monthly_salary}</Text>
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Badge
                      color={getQualificationStatusColor(teacher.profile.qualification_status)}
                      variant="light"
                    >
                      {getQualificationStatusLabel(teacher.profile.qualification_status)}
                    </Badge>
                  </Table.Td>

                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="查看详情">
                        <ActionIcon
                          variant="light"
                          onClick={() => {
                            setSelectedTeacher(teacher)
                            openDetail()
                          }}
                        >
                          <IconEye size={16} />
                        </ActionIcon>
                      </Tooltip>

                      <Tooltip label="薪酬管理">
                        <ActionIcon
                          variant="light"
                          color="green"
                          onClick={() => handleSalaryUpdate(teacher)}
                        >
                          <IconCurrencyYuan size={16} />
                        </ActionIcon>
                      </Tooltip>

                      <Tooltip label="资质审核">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          onClick={() => handleQualificationReview(teacher)}
                        >
                          <IconCertificate size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>

          {/* 分页 */}
          {teachersData && teachersData.pages > 1 && (
            <Group justify="center" p="md">
              <Pagination value={page} onChange={setPage} total={teachersData.pages} />
            </Group>
          )}
        </Paper>

        {/* 加载状态 */}
        {isLoading && (
          <Paper withBorder p="xl" ta="center">
            <Text>正在加载教师信息...</Text>
          </Paper>
        )}

        {/* 错误状态 */}
        {error && (
          <Paper withBorder p="xl" ta="center">
            <Text c="red">加载失败：{error.message}</Text>
          </Paper>
        )}
      </Stack>

      {/* 教师详情模态框 */}
      <Modal opened={detailOpened} onClose={closeDetail} title="教师详细信息" size="lg">
        {selectedTeacher && (
          <Stack>
            <Card withBorder>
              <Stack>
                <Title order={4}>基本信息</Title>
                <Group>
                  <Text>
                    <strong>姓名：</strong>
                    {selectedTeacher.profile.real_name}
                  </Text>
                  <Text>
                    <strong>年龄：</strong>
                    {selectedTeacher.profile.age || '未填写'}
                  </Text>
                  <Text>
                    <strong>性别：</strong>
                    {selectedTeacher.profile.gender || '未填写'}
                  </Text>
                </Group>
                <Text>
                  <strong>职称：</strong>
                  {selectedTeacher.profile.title || '未填写'}
                </Text>
                <Text>
                  <strong>学科：</strong>
                  {selectedTeacher.profile.subject || '未填写'}
                </Text>
                <Text>
                  <strong>联系电话：</strong>
                  {selectedTeacher.profile.phone || '未填写'}
                </Text>
              </Stack>
            </Card>

            <Card withBorder>
              <Stack>
                <Title order={4}>教学数据</Title>
                <Group>
                  <Text>
                    <strong>总教学时长：</strong>
                    {selectedTeacher.profile.total_teaching_hours}小时
                  </Text>
                  <Text>
                    <strong>学生人数：</strong>
                    {selectedTeacher.profile.student_count}
                  </Text>
                  <Text>
                    <strong>平均评分：</strong>
                    {selectedTeacher.profile.average_rating.toFixed(1)}
                  </Text>
                </Group>
                <Text>
                  <strong>教学状态：</strong>
                  {getTeachingStatusLabel(selectedTeacher.profile.teaching_status)}
                </Text>
              </Stack>
            </Card>

            <Card withBorder>
              <Stack>
                <Title order={4}>薪酬信息</Title>
                <Group>
                  <Text>
                    <strong>课时费：</strong>¥{selectedTeacher.profile.hourly_rate}/小时
                  </Text>
                  <Text>
                    <strong>月薪：</strong>¥{selectedTeacher.profile.monthly_salary}
                  </Text>
                </Group>
                <Text>
                  <strong>累计已发薪资：</strong>¥{selectedTeacher.profile.total_salary_paid}
                </Text>
              </Stack>
            </Card>

            <Card withBorder>
              <Stack>
                <Title order={4}>资质信息</Title>
                <Text>
                  <strong>资质状态：</strong>
                  {getQualificationStatusLabel(selectedTeacher.profile.qualification_status)}
                </Text>
                {selectedTeacher.profile.last_review_date && (
                  <Text>
                    <strong>最后审核：</strong>
                    {new Date(selectedTeacher.profile.last_review_date).toLocaleDateString()}
                  </Text>
                )}
                {selectedTeacher.profile.next_review_date && (
                  <Text>
                    <strong>下次审核：</strong>
                    {new Date(selectedTeacher.profile.next_review_date).toLocaleDateString()}
                  </Text>
                )}
              </Stack>
            </Card>
          </Stack>
        )}
      </Modal>

      {/* 薪酬更新模态框 */}
      <Modal opened={salaryOpened} onClose={closeSalary} title="更新教师薪酬">
        <form onSubmit={salaryForm.onSubmit(handleSalarySubmit)}>
          <Stack>
            <NumberInput
              label="课时费（元/小时）"
              required
              min={0}
              decimalScale={2}
              {...salaryForm.getInputProps('hourly_rate')}
            />

            <NumberInput
              label="月薪（元）"
              required
              min={0}
              decimalScale={2}
              {...salaryForm.getInputProps('monthly_salary')}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeSalary}>
                取消
              </Button>
              <Button type="submit" loading={salaryMutation.isPending}>
                更新薪酬
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 资质审核模态框 */}
      <Modal opened={qualificationOpened} onClose={closeQualification} title="教师资质审核">
        <form onSubmit={qualificationForm.onSubmit(handleQualificationSubmit)}>
          <Stack>
            <Select
              label="资质状态"
              required
              data={[
                { value: 'pending', label: '待审核' },
                { value: 'approved', label: '已通过' },
                { value: 'rejected', label: '未通过' },
                { value: 'expired', label: '已过期' },
              ]}
              {...qualificationForm.getInputProps('qualification_status')}
            />

            <Textarea
              label="审核备注"
              placeholder="请输入审核意见或备注"
              rows={4}
              {...qualificationForm.getInputProps('notes')}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeQualification}>
                取消
              </Button>
              <Button type="submit" loading={qualificationMutation.isPending}>
                提交审核
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Container>
  )
}
