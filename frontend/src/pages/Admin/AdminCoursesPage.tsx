/**
 * 管理员课程管理页面 - 需求6：课程管理
 * 实现完整的课程CRUD功能、课程分配管理、课程审核流程
 */

import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Pagination,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
  Alert,
  Grid,
  Tabs,
  SimpleGrid,
  Textarea,
  Switch,
  NumberInput,
  MultiSelect,
} from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconEdit,
  IconEye,
  IconPlus,
  IconRefresh,
  IconTrash,
  IconBook,
  IconUsers,
  IconCheck,
  IconAlertTriangle,
  IconStar,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/api/client'

// 课程接口
interface Course {
  id: number
  course_name: string
  course_code: string
  description?: string
  category: string
  difficulty_level: number
  duration_weeks: number
  total_hours: number
  max_students: number
  prerequisites: string[]
  learning_objectives: string[]
  syllabus_content: Record<string, any>
  status: string
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
  enrolled_students: number
  assigned_teachers: number
  completion_rate: number
}

// 课程分配接口
interface CourseAssignment {
  id: number
  course_id: number
  course_name: string
  teacher_id: number
  teacher_name: string
  class_id: number
  class_name: string
  start_date: string
  end_date: string
  schedule: Record<string, any>
  status: string
  created_at: string
}

// 课程统计接口
interface CourseStatistics {
  total_courses: number
  active_courses: number
  draft_courses: number
  archived_courses: number
  total_enrollments: number
  average_completion_rate: number
  popular_categories: Array<{ category: string; count: number }>
  recent_activities: Array<{
    action: string
    course_name: string
    timestamp: string
    user: string
  }>
}

export function AdminCoursesPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('courses')
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [page, setPage] = useState(1)

  const [courseModalOpened, { open: openCourseModal, close: closeCourseModal }] =
    useDisclosure(false)
  const [assignModalOpened, { open: openAssignModal, close: closeAssignModal }] =
    useDisclosure(false)
  const [detailModalOpened, { open: openDetailModal, close: closeDetailModal }] =
    useDisclosure(false)

  // 课程表单
  const courseForm = useForm({
    initialValues: {
      course_name: '',
      course_code: '',
      description: '',
      category: '',
      difficulty_level: 1,
      duration_weeks: 12,
      total_hours: 48,
      max_students: 30,
      prerequisites: [] as string[],
      learning_objectives: [] as string[],
      is_active: true,
    },
  })

  // 课程分配表单
  const assignForm = useForm({
    initialValues: {
      course_id: 0,
      teacher_id: 0,
      class_id: 0,
      start_date: null as Date | null,
      end_date: null as Date | null,
      schedule: '{}',
    },
  })

  // 获取课程列表
  const {
    data: coursesData,
    isLoading: coursesLoading,
    error: coursesError,
  } = useQuery({
    queryKey: ['courses', page],
    queryFn: async () => {
      const response = await apiClient.get(`/courses/?skip=${(page - 1) * 20}&limit=20`)
      return response.data as { items: Course[]; total: number; pages: number }
    },
  })

  // 获取课程分配列表
  const { data: assignmentsData } = useQuery({
    queryKey: ['course-assignments'],
    queryFn: async () => {
      const response = await apiClient.get('/courses/assignments/')
      return response.data as CourseAssignment[]
    },
  })

  // 获取课程统计
  const { data: statsData } = useQuery({
    queryKey: ['course-statistics'],
    queryFn: async () => {
      const response = await apiClient.get('/courses/statistics')
      return response.data as CourseStatistics
    },
  })

  // 创建/更新课程
  const courseMutation = useMutation({
    mutationFn: async (data: typeof courseForm.values) => {
      if (selectedCourse) {
        return await apiClient.put(`/courses/${selectedCourse.id}`, data)
      } else {
        return await apiClient.post('/courses/', data)
      }
    },
    onSuccess: () => {
      notifications.show({
        title: '操作成功',
        message: selectedCourse ? '课程更新成功' : '课程创建成功',
        color: 'green',
      })
      closeCourseModal()
      courseForm.reset()
      setSelectedCourse(null)
      queryClient.invalidateQueries({ queryKey: ['courses'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '操作失败',
        message: error.response?.data?.detail || '操作失败',
        color: 'red',
      })
    },
  })

  // 删除课程
  const deleteMutation = useMutation({
    mutationFn: async (courseId: number) => {
      return await apiClient.delete(`/courses/${courseId}`)
    },
    onSuccess: () => {
      notifications.show({
        title: '删除成功',
        message: '课程删除成功',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['courses'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '删除失败',
        message: error.response?.data?.detail || '课程删除失败',
        color: 'red',
      })
    },
  })

  // 分配课程
  const assignMutation = useMutation({
    mutationFn: async (data: typeof assignForm.values) => {
      return await apiClient.post('/courses/assignments/', {
        ...data,
        schedule: JSON.parse(data.schedule),
        start_date: data.start_date?.toISOString(),
        end_date: data.end_date?.toISOString(),
      })
    },
    onSuccess: () => {
      notifications.show({
        title: '分配成功',
        message: '课程分配成功',
        color: 'green',
      })
      closeAssignModal()
      assignForm.reset()
      queryClient.invalidateQueries({ queryKey: ['course-assignments'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '分配失败',
        message: error.response?.data?.detail || '课程分配失败',
        color: 'red',
      })
    },
  })

  const handleCreateCourse = () => {
    setSelectedCourse(null)
    courseForm.reset()
    openCourseModal()
  }

  const handleEditCourse = (course: Course) => {
    setSelectedCourse(course)
    courseForm.setValues({
      course_name: course.course_name,
      course_code: course.course_code,
      description: course.description || '',
      category: course.category,
      difficulty_level: course.difficulty_level,
      duration_weeks: course.duration_weeks,
      total_hours: course.total_hours,
      max_students: course.max_students,
      prerequisites: course.prerequisites,
      learning_objectives: course.learning_objectives,
      is_active: course.is_active,
    })
    openCourseModal()
  }

  const handleViewDetails = (course: Course) => {
    setSelectedCourse(course)
    openDetailModal()
  }

  const handleAssignCourse = (course: Course) => {
    assignForm.setFieldValue('course_id', course.id)
    openAssignModal()
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; label: string }> = {
      draft: { color: 'gray', label: '草稿' },
      active: { color: 'green', label: '活跃' },
      archived: { color: 'orange', label: '归档' },
      suspended: { color: 'red', label: '暂停' },
    }
    const statusInfo = statusMap[status] || { color: 'gray', label: status }
    return <Badge color={statusInfo.color}>{statusInfo.label}</Badge>
  }

  const getDifficultyBadge = (level: number) => {
    if (level <= 2) return <Badge color="green">初级</Badge>
    if (level <= 4) return <Badge color="yellow">中级</Badge>
    return <Badge color="red">高级</Badge>
  }

  return (
    <Container size="xl" py="lg">
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>课程管理</Title>
          <Text c="dimmed" size="sm">
            管理系统课程，包括创建、编辑、分配和监控
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreateCourse}>
            创建课程
          </Button>
          <Button leftSection={<IconRefresh size={16} />} variant="light">
            刷新
          </Button>
        </Group>
      </Group>

      {/* 统计卡片 */}
      {statsData && (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="lg">
          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  总课程数
                </Text>
                <Text fw={700} size="xl">
                  {statsData.total_courses}
                </Text>
              </div>
              <IconBook size={32} color="blue" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  活跃课程
                </Text>
                <Text fw={700} size="xl">
                  {statsData.active_courses}
                </Text>
              </div>
              <IconCheck size={32} color="green" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  总注册数
                </Text>
                <Text fw={700} size="xl">
                  {statsData.total_enrollments}
                </Text>
              </div>
              <IconUsers size={32} color="purple" />
            </Group>
          </Card>

          <Card withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">
                  完成率
                </Text>
                <Text fw={700} size="xl">
                  {(statsData.average_completion_rate * 100).toFixed(1)}%
                </Text>
              </div>
              <IconStar size={32} color="orange" />
            </Group>
          </Card>
        </SimpleGrid>
      )}

      <Tabs value={activeTab} onChange={value => setActiveTab(value || 'courses')}>
        <Tabs.List>
          <Tabs.Tab value="courses" leftSection={<IconBook size={16} />}>
            课程列表
          </Tabs.Tab>
          <Tabs.Tab value="assignments" leftSection={<IconUsers size={16} />}>
            课程分配
          </Tabs.Tab>
          <Tabs.Tab value="statistics" leftSection={<IconStar size={16} />}>
            统计分析
          </Tabs.Tab>
        </Tabs.List>

        {/* 课程列表标签页 */}
        <Tabs.Panel value="courses" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>课程信息</Table.Th>
                  <Table.Th>分类</Table.Th>
                  <Table.Th>难度</Table.Th>
                  <Table.Th>时长</Table.Th>
                  <Table.Th>学生数</Table.Th>
                  <Table.Th>状态</Table.Th>
                  <Table.Th>操作</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {coursesData?.items.map(course => (
                  <Table.Tr key={course.id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text fw={500}>{course.course_name}</Text>
                        <Text size="sm" c="dimmed">
                          {course.course_code}
                        </Text>
                        {course.description && (
                          <Text size="xs" c="dimmed" lineClamp={2}>
                            {course.description}
                          </Text>
                        )}
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Badge variant="light">{course.category}</Badge>
                    </Table.Td>
                    <Table.Td>{getDifficultyBadge(course.difficulty_level)}</Table.Td>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text size="sm">{course.duration_weeks} 周</Text>
                        <Text size="xs" c="dimmed">
                          {course.total_hours} 小时
                        </Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text size="sm">
                          {course.enrolled_students}/{course.max_students}
                        </Text>
                        <Text size="xs" c="dimmed">
                          完成率: {(course.completion_rate * 100).toFixed(1)}%
                        </Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>{getStatusBadge(course.status)}</Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="查看详情">
                          <ActionIcon variant="light" onClick={() => handleViewDetails(course)}>
                            <IconEye size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="编辑课程">
                          <ActionIcon variant="light" onClick={() => handleEditCourse(course)}>
                            <IconEdit size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="分配课程">
                          <ActionIcon
                            variant="light"
                            color="blue"
                            onClick={() => handleAssignCourse(course)}
                          >
                            <IconUsers size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="删除课程">
                          <ActionIcon
                            variant="light"
                            color="red"
                            onClick={() => deleteMutation.mutate(course.id)}
                          >
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>

            {coursesData && coursesData.pages > 1 && (
              <Group justify="center" p="md">
                <Pagination value={page} onChange={setPage} total={coursesData.pages} />
              </Group>
            )}
          </Paper>
        </Tabs.Panel>

        {/* 课程分配标签页 */}
        <Tabs.Panel value="assignments" pt="md">
          <Paper withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>课程</Table.Th>
                  <Table.Th>教师</Table.Th>
                  <Table.Th>班级</Table.Th>
                  <Table.Th>开始时间</Table.Th>
                  <Table.Th>结束时间</Table.Th>
                  <Table.Th>状态</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {assignmentsData?.map(assignment => (
                  <Table.Tr key={assignment.id}>
                    <Table.Td>
                      <Text fw={500}>{assignment.course_name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{assignment.teacher_name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{assignment.class_name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {new Date(assignment.start_date).toLocaleDateString('zh-CN')}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {new Date(assignment.end_date).toLocaleDateString('zh-CN')}
                      </Text>
                    </Table.Td>
                    <Table.Td>{getStatusBadge(assignment.status)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        </Tabs.Panel>

        {/* 统计分析标签页 */}
        <Tabs.Panel value="statistics" pt="md">
          {statsData && (
            <Grid>
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card withBorder>
                  <Title order={4} mb="md">
                    热门分类
                  </Title>
                  <Stack>
                    {statsData.popular_categories.map((category, index) => (
                      <Group key={index} justify="space-between">
                        <Badge variant="light">{category.category}</Badge>
                        <Text fw={500}>{category.count} 门课程</Text>
                      </Group>
                    ))}
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card withBorder>
                  <Title order={4} mb="md">
                    最近活动
                  </Title>
                  <Stack>
                    {statsData.recent_activities.map((activity, index) => (
                      <Paper key={index} withBorder p="sm">
                        <Group justify="space-between">
                          <div>
                            <Text size="sm" fw={500}>
                              {activity.action}
                            </Text>
                            <Text size="xs" c="dimmed">
                              {activity.course_name} - {activity.user}
                            </Text>
                          </div>
                          <Text size="xs" c="dimmed">
                            {new Date(activity.timestamp).toLocaleString('zh-CN')}
                          </Text>
                        </Group>
                      </Paper>
                    ))}
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          )}
        </Tabs.Panel>
      </Tabs>

      {/* 课程创建/编辑模态框 */}
      <Modal
        opened={courseModalOpened}
        onClose={closeCourseModal}
        title={selectedCourse ? '编辑课程' : '创建课程'}
        size="xl"
      >
        <form onSubmit={courseForm.onSubmit(values => courseMutation.mutate(values))}>
          <Stack>
            <Grid>
              <Grid.Col span={6}>
                <TextInput
                  label="课程名称"
                  placeholder="输入课程名称"
                  required
                  {...courseForm.getInputProps('course_name')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <TextInput
                  label="课程代码"
                  placeholder="输入课程代码"
                  required
                  {...courseForm.getInputProps('course_code')}
                />
              </Grid.Col>
            </Grid>

            <Textarea
              label="课程描述"
              placeholder="输入课程描述"
              rows={3}
              {...courseForm.getInputProps('description')}
            />

            <Grid>
              <Grid.Col span={6}>
                <Select
                  label="课程分类"
                  placeholder="选择课程分类"
                  required
                  data={[
                    { value: 'listening', label: '听力训练' },
                    { value: 'reading', label: '阅读理解' },
                    { value: 'writing', label: '写作训练' },
                    { value: 'translation', label: '翻译练习' },
                    { value: 'comprehensive', label: '综合训练' },
                  ]}
                  {...courseForm.getInputProps('category')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <Select
                  label="难度等级"
                  placeholder="选择难度等级"
                  required
                  data={[
                    { value: '1', label: '1 - 入门' },
                    { value: '2', label: '2 - 初级' },
                    { value: '3', label: '3 - 中级' },
                    { value: '4', label: '4 - 中高级' },
                    { value: '5', label: '5 - 高级' },
                  ]}
                  {...courseForm.getInputProps('difficulty_level')}
                />
              </Grid.Col>
            </Grid>

            <Grid>
              <Grid.Col span={4}>
                <NumberInput
                  label="课程周数"
                  placeholder="输入课程周数"
                  required
                  min={1}
                  max={52}
                  {...courseForm.getInputProps('duration_weeks')}
                />
              </Grid.Col>
              <Grid.Col span={4}>
                <NumberInput
                  label="总课时"
                  placeholder="输入总课时"
                  required
                  min={1}
                  max={200}
                  {...courseForm.getInputProps('total_hours')}
                />
              </Grid.Col>
              <Grid.Col span={4}>
                <NumberInput
                  label="最大学生数"
                  placeholder="输入最大学生数"
                  required
                  min={1}
                  max={100}
                  {...courseForm.getInputProps('max_students')}
                />
              </Grid.Col>
            </Grid>

            <MultiSelect
              label="前置课程"
              placeholder="选择前置课程（可选）"
              data={[]}
              {...courseForm.getInputProps('prerequisites')}
            />

            <MultiSelect
              label="学习目标"
              placeholder="输入学习目标"
              data={[]}
              searchable
              {...courseForm.getInputProps('learning_objectives')}
            />

            <Switch
              label="启用课程"
              {...courseForm.getInputProps('is_active', { type: 'checkbox' })}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeCourseModal}>
                取消
              </Button>
              <Button type="submit" loading={courseMutation.isPending}>
                {selectedCourse ? '更新' : '创建'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 课程分配模态框 */}
      <Modal opened={assignModalOpened} onClose={closeAssignModal} title="分配课程" size="lg">
        <form onSubmit={assignForm.onSubmit(values => assignMutation.mutate(values))}>
          <Stack>
            <Select
              label="选择教师"
              placeholder="选择教师"
              required
              data={[]}
              {...assignForm.getInputProps('teacher_id')}
            />

            <Select
              label="选择班级"
              placeholder="选择班级"
              required
              data={[]}
              {...assignForm.getInputProps('class_id')}
            />

            <Grid>
              <Grid.Col span={6}>
                <DatePickerInput
                  label="开始日期"
                  placeholder="选择开始日期"
                  required
                  {...assignForm.getInputProps('start_date')}
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <DatePickerInput
                  label="结束日期"
                  placeholder="选择结束日期"
                  required
                  {...assignForm.getInputProps('end_date')}
                />
              </Grid.Col>
            </Grid>

            <Textarea
              label="课程安排"
              placeholder="输入JSON格式的课程安排"
              rows={4}
              {...assignForm.getInputProps('schedule')}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeAssignModal}>
                取消
              </Button>
              <Button type="submit" loading={assignMutation.isPending}>
                分配课程
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 课程详情模态框 */}
      <Modal opened={detailModalOpened} onClose={closeDetailModal} title="课程详情" size="xl">
        {selectedCourse && (
          <Stack>
            <Grid>
              <Grid.Col span={6}>
                <Text fw={500}>课程名称</Text>
                <Text size="sm">{selectedCourse.course_name}</Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>课程代码</Text>
                <Text size="sm">{selectedCourse.course_code}</Text>
              </Grid.Col>
              <Grid.Col span={12}>
                <Text fw={500}>课程描述</Text>
                <Text size="sm">{selectedCourse.description || '无描述'}</Text>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>课程分类</Text>
                <Badge variant="light">{selectedCourse.category}</Badge>
              </Grid.Col>
              <Grid.Col span={6}>
                <Text fw={500}>难度等级</Text>
                {getDifficultyBadge(selectedCourse.difficulty_level)}
              </Grid.Col>
              <Grid.Col span={4}>
                <Text fw={500}>课程周数</Text>
                <Text size="sm">{selectedCourse.duration_weeks} 周</Text>
              </Grid.Col>
              <Grid.Col span={4}>
                <Text fw={500}>总课时</Text>
                <Text size="sm">{selectedCourse.total_hours} 小时</Text>
              </Grid.Col>
              <Grid.Col span={4}>
                <Text fw={500}>最大学生数</Text>
                <Text size="sm">{selectedCourse.max_students} 人</Text>
              </Grid.Col>
              <Grid.Col span={12}>
                <Text fw={500}>学习目标</Text>
                <Group gap="xs">
                  {selectedCourse.learning_objectives.map((objective, index) => (
                    <Badge key={index} size="sm" variant="outline">
                      {objective}
                    </Badge>
                  ))}
                </Group>
              </Grid.Col>
              <Grid.Col span={12}>
                <Text fw={500}>前置课程</Text>
                <Group gap="xs">
                  {selectedCourse.prerequisites.map((prerequisite, index) => (
                    <Badge key={index} size="sm" color="blue">
                      {prerequisite}
                    </Badge>
                  ))}
                  {selectedCourse.prerequisites.length === 0 && (
                    <Text size="sm" c="dimmed">
                      无前置课程要求
                    </Text>
                  )}
                </Group>
              </Grid.Col>
            </Grid>
          </Stack>
        )}
      </Modal>

      {/* 加载和错误状态 */}
      {coursesLoading && (
        <Paper withBorder p="xl" ta="center">
          <Text>正在加载课程信息...</Text>
        </Paper>
      )}

      {coursesError && (
        <Alert icon={<IconAlertTriangle size={16} />} title="加载失败" color="red">
          {coursesError.message}
        </Alert>
      )}
    </Container>
  )
}
