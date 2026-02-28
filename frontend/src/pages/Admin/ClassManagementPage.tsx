/**
 * 班级管理页面 - 需求4：班级管理与资源配置
 * 实现班级创建、批量创建、资源配置、绑定规则验证等功能
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
  Alert,
  Tabs,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { DatePickerInput } from '@mantine/dates'
import {
  IconPlus,
  IconEdit,
  IconTrash,
  IconEye,
  IconUsers,
  IconSchool,
  IconSettings,
  IconHistory,
  IconCopy,
  IconRefresh,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  classManagementApi,
  type ClassCreate,
  type ClassUpdate,
  type ClassResponse,
  type ClassListResponse,
  type ClassBatchCreate,
} from '../../api/classManagement'

export function ClassManagementPage(): JSX.Element {
  const queryClient = useQueryClient()

  // 状态管理
  const [page, setPage] = useState(1)
  const [courseFilter, setCourseFilter] = useState<string | null>(null)
  const [teacherFilter, setTeacherFilter] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [selectedClass, setSelectedClass] = useState<ClassResponse | null>(null)
  const [activeTab, setActiveTab] = useState('list')

  // 模态框状态
  const [createModalOpened, { open: openCreateModal, close: closeCreateModal }] =
    useDisclosure(false)
  const [editModalOpened, { open: openEditModal, close: closeEditModal }] = useDisclosure(false)
  const [batchModalOpened, { open: openBatchModal, close: closeBatchModal }] = useDisclosure(false)
  const [detailModalOpened, { open: openDetailModal, close: closeDetailModal }] =
    useDisclosure(false)
  const [resourceModalOpened, { open: openResourceModal, close: closeResourceModal }] =
    useDisclosure(false)
  const [validationModalOpened, { open: openValidationModal, close: closeValidationModal }] =
    useDisclosure(false)

  // 绑定规则验证状态 - 需求8验收标准1
  const [validationResult, setValidationResult] = useState<any>(null)

  // 表单管理
  const createForm = useForm<ClassCreate>({
    initialValues: {
      name: '',
      description: '',
      code: '',
      course_id: 0,
      teacher_id: undefined,
      classroom_id: undefined,
      max_students: 50,
      start_date: undefined,
      end_date: undefined,
    },
    validate: {
      name: value => (value.length < 1 ? '班级名称不能为空' : null),
      course_id: value => (value === 0 ? '请选择课程' : null),
      max_students: value => (value < 1 || value > 200 ? '学生数量必须在1-200之间' : null),
    },
  })

  const editForm = useForm<ClassUpdate>({
    initialValues: {
      name: '',
      description: '',
      max_students: 50,
    },
  })

  const batchForm = useForm<ClassBatchCreate>({
    initialValues: {
      course_id: 0,
      teacher_id: undefined,
      class_prefix: '',
      class_count: 1,
      max_students_per_class: 50,
      start_date: undefined,
      end_date: undefined,
    },
    validate: {
      course_id: value => (value === 0 ? '请选择课程' : null),
      class_prefix: value => (value.length < 1 ? '班级前缀不能为空' : null),
      class_count: value => (value < 1 || value > 20 ? '班级数量必须在1-20之间' : null),
      max_students_per_class: value =>
        value < 1 || value > 200 ? '每班学生数必须在1-200之间' : null,
    },
  })

  // ===== 数据查询 =====

  // 获取班级列表
  const {
    data: classesData,
    isLoading: classesLoading,
    error: classesError,
    refetch: refetchClasses,
  } = useQuery<ClassListResponse>({
    queryKey: ['classes', page, courseFilter, teacherFilter, statusFilter],
    queryFn: async () => {
      return await classManagementApi.getClasses({
        page,
        size: 20,
        course_id: courseFilter ? parseInt(courseFilter) : undefined,
        teacher_id: teacherFilter ? parseInt(teacherFilter) : undefined,
        status: statusFilter || undefined,
      })
    },
  })

  // 获取可用课程列表
  const { data: coursesData } = useQuery({
    queryKey: ['available-courses'],
    queryFn: () => classManagementApi.getAvailableCourses(),
  })

  // 获取可用教师列表
  const { data: teachersData } = useQuery({
    queryKey: ['available-teachers'],
    queryFn: () => classManagementApi.getAvailableTeachers(),
  })

  // 获取可用教室列表
  const { data: classroomsData } = useQuery({
    queryKey: ['available-classrooms'],
    queryFn: () => classManagementApi.getAvailableClassrooms(),
  })

  // ===== 数据操作 =====

  // 创建班级
  const createMutation = useMutation({
    mutationFn: (data: ClassCreate) => classManagementApi.createClass(data),
    onSuccess: () => {
      notifications.show({
        title: '创建成功',
        message: '班级创建成功',
        color: 'green',
      })
      closeCreateModal()
      createForm.reset()
      queryClient.invalidateQueries({ queryKey: ['classes'] })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '创建失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 更新班级
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ClassUpdate }) =>
      classManagementApi.updateClass(id, data),
    onSuccess: () => {
      notifications.show({
        title: '更新成功',
        message: '班级信息更新成功',
        color: 'green',
      })
      closeEditModal()
      queryClient.invalidateQueries({ queryKey: ['classes'] })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '更新失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 删除班级
  const deleteMutation = useMutation({
    mutationFn: (id: number) => classManagementApi.deleteClass(id),
    onSuccess: () => {
      notifications.show({
        title: '删除成功',
        message: '班级删除成功',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['classes'] })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '删除失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 批量创建班级
  const batchCreateMutation = useMutation({
    mutationFn: (data: ClassBatchCreate) => classManagementApi.batchCreateClasses(data),
    onSuccess: result => {
      notifications.show({
        title: '批量创建成功',
        message: `成功创建 ${result.created_count} 个班级`,
        color: 'green',
      })
      closeBatchModal()
      batchForm.reset()
      queryClient.invalidateQueries({ queryKey: ['classes'] })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '批量创建失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 绑定规则验证 - 需求8验收标准1
  const validateBindingRulesMutation = useMutation({
    mutationFn: (params: { classId: number; teacherId?: number; courseId?: number }) =>
      classManagementApi.validateBindingRules(params.classId, {
        teacher_id: params.teacherId,
        course_id: params.courseId,
      }),
    onSuccess: result => {
      setValidationResult(result)
      openValidationModal()
    },
    onError: (error: Error) => {
      notifications.show({
        title: '验证失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // ===== 事件处理 =====

  const handleCreateClass = () => {
    createForm.reset()
    openCreateModal()
  }

  const handleEditClass = (classItem: ClassResponse) => {
    setSelectedClass(classItem)
    editForm.setValues({
      name: classItem.name,
      description: classItem.description || '',
      max_students: classItem.max_students,
    })
    openEditModal()
  }

  const handleDeleteClass = (classItem: ClassResponse) => {
    if (window.confirm(`确定要删除班级 "${classItem.name}" 吗？`)) {
      deleteMutation.mutate(classItem.id)
    }
  }

  const handleViewDetails = (classItem: ClassResponse) => {
    setSelectedClass(classItem)
    openDetailModal()
  }

  const handleConfigureResources = (classItem: ClassResponse) => {
    setSelectedClass(classItem)
    openResourceModal()
  }

  // 验证班级绑定规则 - 需求8验收标准1
  const handleValidateBindingRules = (classItem: ClassResponse) => {
    setSelectedClass(classItem)
    validateBindingRulesMutation.mutate({
      classId: classItem.id,
      teacherId: classItem.teacher_id,
      courseId: classItem.course_id,
    })
  }

  const handleSubmitCreate = (values: ClassCreate) => {
    createMutation.mutate(values)
  }

  const handleSubmitEdit = (values: ClassUpdate) => {
    if (!selectedClass) return
    updateMutation.mutate({ id: selectedClass.id, data: values })
  }

  const handleSubmitBatch = (values: ClassBatchCreate) => {
    batchCreateMutation.mutate(values)
  }

  // 状态标签颜色映射
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'preparing':
        return 'blue'
      case 'active':
        return 'green'
      case 'completed':
        return 'gray'
      case 'cancelled':
        return 'red'
      default:
        return 'gray'
    }
  }

  // 状态标签文本映射
  const getStatusText = (status: string) => {
    switch (status) {
      case 'preparing':
        return '筹备中'
      case 'active':
        return '进行中'
      case 'completed':
        return '已完成'
      case 'cancelled':
        return '已取消'
      default:
        return status
    }
  }

  return (
    <Container size="xl" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>班级管理与资源配置</Title>
          <Group>
            <Button leftSection={<IconCopy size={16} />} variant="light" onClick={openBatchModal}>
              批量创建
            </Button>
            <Button leftSection={<IconPlus size={16} />} onClick={handleCreateClass}>
              创建班级
            </Button>
          </Group>
        </Group>

        <Tabs value={activeTab} onChange={value => setActiveTab(value || 'list')}>
          <Tabs.List>
            <Tabs.Tab value="list" leftSection={<IconUsers size={16} />}>
              班级列表
            </Tabs.Tab>
            <Tabs.Tab value="statistics" leftSection={<IconSchool size={16} />}>
              统计概览
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="list" pt="md">
            {/* 搜索和过滤 */}
            <Paper withBorder p="md" mb="md">
              <Group>
                <Select
                  placeholder="选择课程"
                  data={
                    coursesData?.map(course => ({
                      value: course.id.toString(),
                      label: `${course.name} (${course.code || '无编号'})`,
                    })) || []
                  }
                  value={courseFilter}
                  onChange={setCourseFilter}
                  clearable
                  leftSection={<IconSchool size={16} />}
                />

                <Select
                  placeholder="选择教师"
                  data={
                    teachersData?.map(teacher => ({
                      value: teacher.id.toString(),
                      label: teacher.real_name,
                    })) || []
                  }
                  value={teacherFilter}
                  onChange={setTeacherFilter}
                  clearable
                  leftSection={<IconUsers size={16} />}
                />

                <Select
                  placeholder="班级状态"
                  data={[
                    { value: 'preparing', label: '筹备中' },
                    { value: 'active', label: '进行中' },
                    { value: 'completed', label: '已完成' },
                    { value: 'cancelled', label: '已取消' },
                  ]}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  clearable
                />

                <Button
                  leftSection={<IconRefresh size={16} />}
                  variant="light"
                  onClick={() => refetchClasses()}
                >
                  刷新
                </Button>
              </Group>
            </Paper>

            {/* 班级列表 */}
            <Paper withBorder>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>班级信息</Table.Th>
                    <Table.Th>课程信息</Table.Th>
                    <Table.Th>教师信息</Table.Th>
                    <Table.Th>学生情况</Table.Th>
                    <Table.Th>状态</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {classesData?.items.map(classItem => (
                    <Table.Tr key={classItem.id}>
                      <Table.Td>
                        <Stack gap="xs">
                          <Text fw={500}>{classItem.name}</Text>
                          {classItem.code && (
                            <Text size="sm" c="dimmed">
                              编号: {classItem.code}
                            </Text>
                          )}
                          {classItem.description && (
                            <Text size="xs" c="dimmed">
                              {classItem.description}
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap="xs">
                          <Text size="sm">{classItem.course?.name || '未分配课程'}</Text>
                          {classItem.course?.code && (
                            <Text size="xs" c="dimmed">
                              课程编号: {classItem.course.code}
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap="xs">
                          <Text size="sm">{classItem.teacher?.real_name || '未分配教师'}</Text>
                          {classItem.teacher?.email && (
                            <Text size="xs" c="dimmed">
                              {classItem.teacher.email}
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap="xs">
                          <Text size="sm">
                            {classItem.current_students}/{classItem.max_students}
                          </Text>
                          <Text size="xs" c="dimmed">
                            完成率: {(classItem.completion_rate * 100).toFixed(1)}%
                          </Text>
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Badge color={getStatusColor(classItem.status)} size="sm">
                          {getStatusText(classItem.status)}
                        </Badge>
                      </Table.Td>

                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="查看详情">
                            <ActionIcon
                              variant="light"
                              onClick={() => handleViewDetails(classItem)}
                            >
                              <IconEye size={16} />
                            </ActionIcon>
                          </Tooltip>

                          <Tooltip label="编辑班级">
                            <ActionIcon
                              variant="light"
                              color="blue"
                              onClick={() => handleEditClass(classItem)}
                            >
                              <IconEdit size={16} />
                            </ActionIcon>
                          </Tooltip>

                          <Tooltip label="资源配置">
                            <ActionIcon
                              variant="light"
                              color="green"
                              onClick={() => handleConfigureResources(classItem)}
                            >
                              <IconSettings size={16} />
                            </ActionIcon>
                          </Tooltip>

                          <Tooltip label="验证绑定规则">
                            <ActionIcon
                              variant="light"
                              color="orange"
                              onClick={() => handleValidateBindingRules(classItem)}
                              loading={validateBindingRulesMutation.isPending}
                            >
                              <IconSchool size={16} />
                            </ActionIcon>
                          </Tooltip>

                          <Tooltip label="删除班级">
                            <ActionIcon
                              variant="light"
                              color="red"
                              onClick={() => handleDeleteClass(classItem)}
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

              {/* 分页 */}
              {classesData && classesData.pages > 1 && (
                <Group justify="center" p="md">
                  <Pagination value={page} onChange={setPage} total={classesData.pages} />
                </Group>
              )}
            </Paper>

            {/* 加载状态 */}
            {classesLoading && (
              <Paper withBorder p="xl" ta="center">
                <Text>正在加载班级信息...</Text>
              </Paper>
            )}

            {/* 错误状态 */}
            {classesError && (
              <Alert color="red">
                <Text>加载班级信息失败: {classesError.message}</Text>
              </Alert>
            )}
          </Tabs.Panel>

          <Tabs.Panel value="statistics" pt="md">
            <Alert color="blue">
              <Text size="sm">
                统计概览功能正在开发中，将显示班级数量、学生分布、完成率等统计信息。
              </Text>
            </Alert>
          </Tabs.Panel>
        </Tabs>

        {/* 创建班级模态框 - 需求4验收标准1 */}
        <Modal opened={createModalOpened} onClose={closeCreateModal} title="创建班级" size="lg">
          <form onSubmit={createForm.onSubmit(handleSubmitCreate)}>
            <Stack>
              <TextInput
                label="班级名称"
                placeholder="请输入班级名称"
                required
                {...createForm.getInputProps('name')}
              />

              <TextInput
                label="班级编号"
                placeholder="请输入班级编号（可选）"
                {...createForm.getInputProps('code')}
              />

              <Select
                label="选择课程"
                placeholder="请选择课程"
                required
                data={
                  coursesData?.map(course => ({
                    value: course.id.toString(),
                    label: `${course.name} (${course.code || '无编号'})`,
                  })) || []
                }
                {...createForm.getInputProps('course_id')}
                onChange={value =>
                  createForm.setFieldValue('course_id', value ? parseInt(value) : 0)
                }
              />

              <Select
                label="分配教师"
                placeholder="请选择教师（可选）"
                data={
                  teachersData?.map(teacher => ({
                    value: teacher.id.toString(),
                    label: teacher.real_name,
                  })) || []
                }
                {...createForm.getInputProps('teacher_id')}
                onChange={value =>
                  createForm.setFieldValue('teacher_id', value ? parseInt(value) : undefined)
                }
                clearable
              />

              <Select
                label="分配教室"
                placeholder="请选择教室（可选）"
                data={
                  classroomsData?.map(classroom => ({
                    value: classroom.id.toString(),
                    label: `${classroom.name} (${classroom.building_name}) - 容量${classroom.capacity}`,
                  })) || []
                }
                {...createForm.getInputProps('classroom_id')}
                onChange={value =>
                  createForm.setFieldValue('classroom_id', value ? parseInt(value) : undefined)
                }
                clearable
              />

              <NumberInput
                label="最大学生数"
                placeholder="请输入最大学生数"
                required
                min={1}
                max={200}
                {...createForm.getInputProps('max_students')}
              />

              <Group grow>
                <DatePickerInput
                  label="开始日期"
                  placeholder="请选择开始日期"
                  {...createForm.getInputProps('start_date')}
                />

                <DatePickerInput
                  label="结束日期"
                  placeholder="请选择结束日期"
                  {...createForm.getInputProps('end_date')}
                />
              </Group>

              <Textarea
                label="班级描述"
                placeholder="请输入班级描述（可选）"
                rows={3}
                {...createForm.getInputProps('description')}
              />

              <Group justify="flex-end">
                <Button variant="light" onClick={closeCreateModal}>
                  取消
                </Button>
                <Button type="submit" loading={createMutation.isPending}>
                  创建班级
                </Button>
              </Group>
            </Stack>
          </form>
        </Modal>

        {/* 编辑班级模态框 */}
        <Modal opened={editModalOpened} onClose={closeEditModal} title="编辑班级" size="md">
          <form onSubmit={editForm.onSubmit(handleSubmitEdit)}>
            <Stack>
              <TextInput
                label="班级名称"
                placeholder="请输入班级名称"
                required
                {...editForm.getInputProps('name')}
              />

              <NumberInput
                label="最大学生数"
                placeholder="请输入最大学生数"
                required
                min={1}
                max={200}
                {...editForm.getInputProps('max_students')}
              />

              <Textarea
                label="班级描述"
                placeholder="请输入班级描述（可选）"
                rows={3}
                {...editForm.getInputProps('description')}
              />

              <Group justify="flex-end">
                <Button variant="light" onClick={closeEditModal}>
                  取消
                </Button>
                <Button type="submit" loading={updateMutation.isPending}>
                  保存更改
                </Button>
              </Group>
            </Stack>
          </form>
        </Modal>

        {/* 批量创建班级模态框 - 需求4验收标准2 */}
        <Modal opened={batchModalOpened} onClose={closeBatchModal} title="批量创建班级" size="lg">
          <form onSubmit={batchForm.onSubmit(handleSubmitBatch)}>
            <Stack>
              <Alert color="blue">
                <Text size="sm">
                  批量创建功能可以基于课程模板快速创建多个班级，班级名称将自动按序号生成。
                </Text>
              </Alert>

              <Select
                label="选择课程模板"
                placeholder="请选择课程模板"
                required
                data={
                  coursesData?.map(course => ({
                    value: course.id.toString(),
                    label: `${course.name} (${course.code || '无编号'})`,
                  })) || []
                }
                {...batchForm.getInputProps('course_id')}
                onChange={value =>
                  batchForm.setFieldValue('course_id', value ? parseInt(value) : 0)
                }
              />

              <Select
                label="分配教师"
                placeholder="请选择教师（可选）"
                data={
                  teachersData?.map(teacher => ({
                    value: teacher.id.toString(),
                    label: teacher.real_name,
                  })) || []
                }
                {...batchForm.getInputProps('teacher_id')}
                onChange={value =>
                  batchForm.setFieldValue('teacher_id', value ? parseInt(value) : undefined)
                }
                clearable
              />

              <TextInput
                label="班级名称前缀"
                placeholder="例如：英语A、CET4-"
                required
                {...batchForm.getInputProps('class_prefix')}
              />

              <NumberInput
                label="创建班级数量"
                placeholder="请输入要创建的班级数量"
                required
                min={1}
                max={20}
                {...batchForm.getInputProps('class_count')}
              />

              <NumberInput
                label="每班最大学生数"
                placeholder="请输入每班最大学生数"
                required
                min={1}
                max={200}
                {...batchForm.getInputProps('max_students_per_class')}
              />

              <Group grow>
                <DatePickerInput
                  label="开始日期"
                  placeholder="请选择开始日期"
                  {...batchForm.getInputProps('start_date')}
                />

                <DatePickerInput
                  label="结束日期"
                  placeholder="请选择结束日期"
                  {...batchForm.getInputProps('end_date')}
                />
              </Group>

              <Alert color="yellow">
                <Text size="sm">
                  预览：将创建 {batchForm.values.class_count} 个班级，命名为
                  {batchForm.values.class_prefix}01、{batchForm.values.class_prefix}02 等
                </Text>
              </Alert>

              <Group justify="flex-end">
                <Button variant="light" onClick={closeBatchModal}>
                  取消
                </Button>
                <Button type="submit" loading={batchCreateMutation.isPending}>
                  批量创建
                </Button>
              </Group>
            </Stack>
          </form>
        </Modal>

        {/* 班级详情模态框 */}
        <Modal opened={detailModalOpened} onClose={closeDetailModal} title="班级详情" size="lg">
          {selectedClass && (
            <Stack>
              <Card withBorder>
                <Stack>
                  <Group justify="space-between">
                    <Text fw={500} size="lg">
                      {selectedClass.name}
                    </Text>
                    <Badge color={getStatusColor(selectedClass.status)}>
                      {getStatusText(selectedClass.status)}
                    </Badge>
                  </Group>

                  {selectedClass.code && (
                    <Text size="sm" c="dimmed">
                      班级编号: {selectedClass.code}
                    </Text>
                  )}

                  {selectedClass.description && <Text size="sm">{selectedClass.description}</Text>}

                  <Group>
                    <Text size="sm">
                      <strong>课程:</strong> {selectedClass.course?.name || '未分配'}
                    </Text>
                    <Text size="sm">
                      <strong>教师:</strong> {selectedClass.teacher?.real_name || '未分配'}
                    </Text>
                  </Group>

                  <Group>
                    <Text size="sm">
                      <strong>学生数:</strong> {selectedClass.current_students}/
                      {selectedClass.max_students}
                    </Text>
                    <Text size="sm">
                      <strong>完成率:</strong> {(selectedClass.completion_rate * 100).toFixed(1)}%
                    </Text>
                  </Group>

                  <Group>
                    <Text size="sm">
                      <strong>创建时间:</strong>{' '}
                      {new Date(selectedClass.created_at).toLocaleString()}
                    </Text>
                    <Text size="sm">
                      <strong>更新时间:</strong>{' '}
                      {new Date(selectedClass.updated_at).toLocaleString()}
                    </Text>
                  </Group>
                </Stack>
              </Card>

              <Group justify="flex-end">
                <Button
                  leftSection={<IconSettings size={16} />}
                  onClick={() => {
                    closeDetailModal()
                    handleConfigureResources(selectedClass)
                  }}
                >
                  配置资源
                </Button>
                <Button
                  leftSection={<IconEdit size={16} />}
                  onClick={() => {
                    closeDetailModal()
                    handleEditClass(selectedClass)
                  }}
                >
                  编辑班级
                </Button>
              </Group>
            </Stack>
          )}
        </Modal>

        {/* 资源配置模态框 - 需求4验收标准3 */}
        <Modal
          opened={resourceModalOpened}
          onClose={closeResourceModal}
          title="班级资源配置"
          size="lg"
        >
          {selectedClass && (
            <Stack>
              <Alert color="blue">
                <Text size="sm">
                  配置班级的教学资源，包括教师分配、教室绑定等。变更将记录到资源变更历史中。
                </Text>
              </Alert>

              <Card withBorder>
                <Stack>
                  <Text fw={500}>当前资源配置</Text>

                  <Group>
                    <Text size="sm">
                      <strong>分配教师:</strong> {selectedClass.teacher?.real_name || '未分配'}
                    </Text>
                    <Text size="sm">
                      <strong>绑定教室:</strong> {selectedClass.classroom?.name || '未绑定'}
                    </Text>
                  </Group>

                  <Text size="sm">
                    <strong>课程:</strong> {selectedClass.course?.name || '未分配'}
                  </Text>
                </Stack>
              </Card>

              <Stack>
                <Select
                  label="重新分配教师"
                  placeholder="选择新的教师"
                  data={
                    teachersData
                      ?.filter(t => t.qualification_status === 'approved')
                      .map(teacher => ({
                        value: teacher.id.toString(),
                        label: `${teacher.real_name} - ${teacher.subject || '通用'}`,
                      })) || []
                  }
                  clearable
                />

                <Select
                  label="重新绑定教室"
                  placeholder="选择新的教室"
                  data={
                    classroomsData
                      ?.filter(c => c.is_available)
                      .map(classroom => ({
                        value: classroom.id.toString(),
                        label: `${classroom.name} (${classroom.building_name}) - 容量${classroom.capacity}`,
                      })) || []
                  }
                  clearable
                />

                <Textarea label="变更原因" placeholder="请输入资源变更的原因" rows={3} />
              </Stack>

              <Alert color="yellow">
                <Text size="sm">
                  <strong>绑定规则验证:</strong>{' '}
                  系统将自动验证1班级↔1教师、1班级↔1课程的绑定关系。
                </Text>
              </Alert>

              <Group justify="space-between">
                <Button
                  leftSection={<IconHistory size={16} />}
                  variant="light"
                  onClick={() => {
                    // TODO: 打开资源变更历史模态框
                    notifications.show({
                      title: '功能开发中',
                      message: '资源变更历史功能正在开发中',
                      color: 'blue',
                    })
                  }}
                >
                  查看变更历史
                </Button>

                <Group>
                  <Button variant="light" onClick={closeResourceModal}>
                    取消
                  </Button>
                  <Button>保存配置</Button>
                </Group>
              </Group>
            </Stack>
          )}
        </Modal>

        {/* 绑定规则验证结果模态框 - 需求8验收标准1 */}
        <Modal
          opened={validationModalOpened}
          onClose={closeValidationModal}
          title="班级绑定规则验证结果"
          size="lg"
        >
          {validationResult && (
            <Stack>
              <Alert
                color={validationResult.is_valid ? 'green' : 'red'}
                title={validationResult.is_valid ? '验证通过' : '验证失败'}
              >
                <Text size="sm">{validationResult.message}</Text>
              </Alert>

              {selectedClass && (
                <Paper withBorder p="md" bg="gray.0">
                  <Stack gap="xs">
                    <Text fw={500}>班级信息</Text>
                    <Group>
                      <Text size="sm">班级名称: {selectedClass.name}</Text>
                      <Text size="sm">课程ID: {validationResult.current_course_id}</Text>
                      {validationResult.current_teacher_id && (
                        <Text size="sm">教师ID: {validationResult.current_teacher_id}</Text>
                      )}
                    </Group>
                  </Stack>
                </Paper>
              )}

              <Group justify="flex-end">
                <Button variant="light" onClick={closeValidationModal}>
                  关闭
                </Button>
                {!validationResult.is_valid && <Button color="orange">申请规则豁免</Button>}
              </Group>
            </Stack>
          )}
        </Modal>
      </Stack>
    </Container>
  )
}
