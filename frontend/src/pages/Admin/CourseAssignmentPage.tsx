/**
 * 课程分配管理页面 - 需求5：课程分配管理
 * 实现教师课程资质匹配、工作量平衡分配、时间冲突检测、一对多配置、权限划分等功能
 */

import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Pagination,
  Paper,
  Progress,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  Textarea,
  Title,
  Tooltip,
  Switch,
  Grid,
  Divider,
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
  IconAlertTriangle,
  IconRefresh,
  IconSettings,
  IconScale,
  IconShield,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  courseAssignmentApi,
  type CourseAssignmentRequest,
  type CourseAssignmentResponse,
} from '../../api/courseAssignment'

export function CourseAssignmentPage(): JSX.Element {
  const queryClient = useQueryClient()

  // 状态管理
  const [page, setPage] = useState(1)
  const [courseFilter, setCourseFilter] = useState<string | null>(null)
  const [teacherFilter, setTeacherFilter] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [_selectedAssignment, setSelectedAssignment] = useState<CourseAssignmentResponse | null>(
    null
  )
  const [activeTab, setActiveTab] = useState('assignments')

  // 模态框状态
  const [assignModalOpened, { open: openAssignModal, close: closeAssignModal }] =
    useDisclosure(false)
  const [workloadModalOpened, { open: openWorkloadModal, close: closeWorkloadModal }] =
    useDisclosure(false)
  const [rulesModalOpened, { open: openRulesModal, close: closeRulesModal }] = useDisclosure(false)

  // 表单管理
  const assignForm = useForm<CourseAssignmentRequest>({
    initialValues: {
      course_id: 0,
      teacher_ids: [],
      class_ids: [],
      assignment_type: 'single',
      start_date: '',
      end_date: '',
      schedule: {},
      notes: '',
    },
    validate: {
      course_id: value => (value === 0 ? '请选择课程' : null),
      teacher_ids: value => (value.length === 0 ? '请选择至少一个教师' : null),
      class_ids: value => (value.length === 0 ? '请选择至少一个班级' : null),
      start_date: value => (!value ? '请选择开始日期' : null),
      end_date: value => (!value ? '请选择结束日期' : null),
    },
  })

  // ===== 数据查询 =====

  // 获取课程分配列表
  const {
    data: assignmentsData,
    isLoading: assignmentsLoading,
    error: assignmentsError,
    refetch: refetchAssignments,
  } = useQuery({
    queryKey: ['course-assignments', page, courseFilter, teacherFilter, statusFilter],
    queryFn: async () => {
      return await courseAssignmentApi.getCourseAssignments({
        page,
        size: 20,
        course_id: courseFilter ? parseInt(courseFilter) : undefined,
        teacher_id: teacherFilter ? parseInt(teacherFilter) : undefined,
        status: statusFilter || undefined,
      })
    },
  })

  // 获取教师工作量统计
  const { data: workloadData } = useQuery({
    queryKey: ['teachers-workload'],
    queryFn: () => courseAssignmentApi.getAllTeachersWorkload(),
  })

  // 获取教室排课规则
  const { data: rulesData } = useQuery({
    queryKey: ['classroom-rules'],
    queryFn: () => courseAssignmentApi.getClassroomSchedulingRules(),
  })

  // ===== 数据操作 =====

  // 创建课程分配
  const assignMutation = useMutation({
    mutationFn: (data: CourseAssignmentRequest) => courseAssignmentApi.assignCourseToTeacher(data),
    onSuccess: () => {
      notifications.show({
        title: '分配成功',
        message: '课程分配创建成功',
        color: 'green',
      })
      closeAssignModal()
      assignForm.reset()
      queryClient.invalidateQueries({ queryKey: ['course-assignments'] })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '分配失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 删除课程分配
  const deleteMutation = useMutation({
    mutationFn: (id: number) => courseAssignmentApi.deleteCourseAssignment(id),
    onSuccess: () => {
      notifications.show({
        title: '删除成功',
        message: '课程分配删除成功',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['course-assignments'] })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '删除失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // ===== 事件处理 =====

  const handleCreateAssignment = () => {
    assignForm.reset()
    openAssignModal()
  }

  const handleEditAssignment = (assignment: CourseAssignmentResponse) => {
    setSelectedAssignment(assignment)
    assignForm.setValues({
      course_id: assignment.course_id,
      teacher_ids: assignment.teacher_ids,
      class_ids: assignment.class_ids,
      assignment_type: assignment.assignment_type as any,
      start_date: assignment.start_date,
      end_date: assignment.end_date,
      notes: '',
    })
    // TODO: 实现编辑模态框
    notifications.show({
      title: '功能开发中',
      message: '编辑功能正在开发中',
      color: 'blue',
    })
  }

  const handleDeleteAssignment = (assignment: CourseAssignmentResponse) => {
    if (window.confirm(`确定要删除课程分配 "${assignment.course?.name}" 吗？`)) {
      deleteMutation.mutate(assignment.id)
    }
  }

  const handleSubmitAssign = (values: CourseAssignmentRequest) => {
    assignMutation.mutate(values)
  }

  // 状态标签颜色映射
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green'
      case 'pending':
        return 'yellow'
      case 'completed':
        return 'blue'
      case 'cancelled':
        return 'red'
      default:
        return 'gray'
    }
  }

  // 状态标签文本映射
  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '进行中'
      case 'pending':
        return '待开始'
      case 'completed':
        return '已完成'
      case 'cancelled':
        return '已取消'
      default:
        return status
    }
  }

  // 工作量颜色映射
  const getWorkloadColor = (percentage: number) => {
    if (percentage >= 90) return 'red'
    if (percentage >= 70) return 'yellow'
    return 'green'
  }

  return (
    <Container size="xl" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>课程分配管理</Title>
          <Group>
            <Button
              leftSection={<IconScale size={16} />}
              variant="light"
              onClick={openWorkloadModal}
            >
              工作量平衡
            </Button>
            <Button
              leftSection={<IconSettings size={16} />}
              variant="light"
              onClick={openRulesModal}
            >
              排课规则
            </Button>
            <Button leftSection={<IconPlus size={16} />} onClick={handleCreateAssignment}>
              创建分配
            </Button>
          </Group>
        </Group>

        <Tabs value={activeTab} onChange={value => setActiveTab(value || 'assignments')}>
          <Tabs.List>
            <Tabs.Tab value="assignments" leftSection={<IconSchool size={16} />}>
              分配管理
            </Tabs.Tab>
            <Tabs.Tab value="workload" leftSection={<IconScale size={16} />}>
              工作量统计
            </Tabs.Tab>
            <Tabs.Tab value="conflicts" leftSection={<IconAlertTriangle size={16} />}>
              冲突检测
            </Tabs.Tab>
            <Tabs.Tab value="rules" leftSection={<IconShield size={16} />}>
              规则管理
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="assignments" pt="md">
            {/* 搜索和过滤 */}
            <Paper withBorder p="md" mb="md">
              <Group>
                <Select
                  placeholder="选择课程"
                  data={[]} // TODO: 从API获取课程列表
                  value={courseFilter}
                  onChange={setCourseFilter}
                  clearable
                  leftSection={<IconSchool size={16} />}
                />

                <Select
                  placeholder="选择教师"
                  data={[]} // TODO: 从API获取教师列表
                  value={teacherFilter}
                  onChange={setTeacherFilter}
                  clearable
                  leftSection={<IconUsers size={16} />}
                />

                <Select
                  placeholder="分配状态"
                  data={[
                    { value: 'active', label: '进行中' },
                    { value: 'pending', label: '待开始' },
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
                  onClick={() => refetchAssignments()}
                >
                  刷新
                </Button>
              </Group>
            </Paper>

            {/* 分配列表 */}
            <Paper withBorder>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>课程信息</Table.Th>
                    <Table.Th>分配教师</Table.Th>
                    <Table.Th>分配班级</Table.Th>
                    <Table.Th>分配类型</Table.Th>
                    <Table.Th>时间周期</Table.Th>
                    <Table.Th>状态</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {assignmentsData?.items.map(assignment => (
                    <Table.Tr key={assignment.id}>
                      <Table.Td>
                        <Stack gap="xs">
                          <Text fw={500}>{assignment.course?.name || '未知课程'}</Text>
                          {assignment.course?.code && (
                            <Text size="sm" c="dimmed">
                              编号: {assignment.course.code}
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap="xs">
                          {assignment.teachers?.map(teacher => (
                            <Text key={teacher.id} size="sm">
                              {teacher.real_name}
                            </Text>
                          )) || (
                            <Text size="sm" c="dimmed">
                              未分配教师
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap="xs">
                          {assignment.classes?.map(cls => (
                            <Text key={cls.id} size="sm">
                              {cls.name} ({cls.current_students}/{cls.max_students})
                            </Text>
                          )) || (
                            <Text size="sm" c="dimmed">
                              未分配班级
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Badge variant="light">
                          {assignment.assignment_type === 'single' && '单一分配'}
                          {assignment.assignment_type === 'multiple_teachers' && '多教师协作'}
                          {assignment.assignment_type === 'multiple_classes' && '多班级教学'}
                        </Badge>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap="xs">
                          <Text size="sm">
                            {new Date(assignment.start_date).toLocaleDateString('zh-CN')}
                          </Text>
                          <Text size="sm" c="dimmed">
                            至 {new Date(assignment.end_date).toLocaleDateString('zh-CN')}
                          </Text>
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Badge color={getStatusColor(assignment.status)} size="sm">
                          {getStatusText(assignment.status)}
                        </Badge>
                      </Table.Td>

                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="查看详情">
                            <ActionIcon
                              variant="light"
                              onClick={() => {
                                setSelectedAssignment(assignment)
                                // TODO: 打开详情模态框
                              }}
                            >
                              <IconEye size={16} />
                            </ActionIcon>
                          </Tooltip>

                          <Tooltip label="编辑分配">
                            <ActionIcon
                              variant="light"
                              color="blue"
                              onClick={() => handleEditAssignment(assignment)}
                            >
                              <IconEdit size={16} />
                            </ActionIcon>
                          </Tooltip>

                          <Tooltip label="删除分配">
                            <ActionIcon
                              variant="light"
                              color="red"
                              onClick={() => handleDeleteAssignment(assignment)}
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
              {assignmentsData && assignmentsData.pages > 1 && (
                <Group justify="center" p="md">
                  <Pagination value={page} onChange={setPage} total={assignmentsData.pages} />
                </Group>
              )}
            </Paper>

            {/* 加载状态 */}
            {assignmentsLoading && (
              <Paper withBorder p="xl" ta="center">
                <Text>正在加载分配信息...</Text>
              </Paper>
            )}

            {/* 错误状态 */}
            {assignmentsError && (
              <Alert color="red">
                <Text>加载分配信息失败: {assignmentsError.message}</Text>
              </Alert>
            )}
          </Tabs.Panel>

          <Tabs.Panel value="workload" pt="md">
            {/* 工作量统计 */}
            <Grid>
              {workloadData?.map(workload => (
                <Grid.Col key={workload.teacher_id} span={6}>
                  <Card withBorder>
                    <Stack>
                      <Group justify="space-between">
                        <Text fw={500}>教师ID: {workload.teacher_id}</Text>
                        <Badge color={getWorkloadColor(workload.workload_percentage)}>
                          {workload.workload_percentage.toFixed(1)}%
                        </Badge>
                      </Group>

                      <Progress
                        value={workload.workload_percentage}
                        color={getWorkloadColor(workload.workload_percentage)}
                        size="lg"
                      />

                      <Group>
                        <Text size="sm">班级: {workload.current_classes}</Text>
                        <Text size="sm">学生: {workload.current_students}</Text>
                        <Text size="sm">周课时: {workload.total_hours_per_week}</Text>
                      </Group>

                      {workload.is_overloaded && (
                        <Alert color="red">
                          <Text size="sm">工作量超载！</Text>
                        </Alert>
                      )}

                      <Text size="sm" c="dimmed">
                        可用容量: {workload.available_capacity}
                      </Text>
                    </Stack>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="conflicts" pt="md">
            <Alert color="blue">
              <Text size="sm">
                时间冲突检测功能正在开发中，将显示教师、班级、教室的时间冲突情况。
              </Text>
            </Alert>
          </Tabs.Panel>

          <Tabs.Panel value="rules" pt="md">
            <Stack>
              {rulesData?.map(rule => (
                <Card key={rule.rule_id} withBorder>
                  <Group justify="space-between">
                    <Stack gap="xs">
                      <Text fw={500}>{rule.rule_name}</Text>
                      <Badge variant="light" color={rule.enabled ? 'green' : 'gray'}>
                        {rule.enabled ? '已启用' : '已禁用'}
                      </Badge>
                      <Text size="sm" c="dimmed">
                        类型: {rule.rule_type === 'basic' ? '基础规则' : '高级规则'}
                      </Text>
                    </Stack>

                    <Switch
                      checked={rule.enabled}
                      onChange={event => {
                        // TODO: 更新规则状态
                        void event.currentTarget.checked
                      }}
                    />
                  </Group>
                </Card>
              ))}
            </Stack>
          </Tabs.Panel>
        </Tabs>

        {/* 创建分配模态框 - 需求5验收标准1&2 */}
        <Modal opened={assignModalOpened} onClose={closeAssignModal} title="创建课程分配" size="lg">
          <form onSubmit={assignForm.onSubmit(handleSubmitAssign)}>
            <Stack>
              <Select
                label="选择课程"
                placeholder="请选择课程"
                required
                data={[]} // TODO: 从API获取课程列表
                {...assignForm.getInputProps('course_id')}
                onChange={value =>
                  assignForm.setFieldValue('course_id', value ? parseInt(value) : 0)
                }
              />

              <Select
                label="分配类型"
                placeholder="请选择分配类型"
                required
                data={[
                  { value: 'single', label: '单一分配（1教师-1课程-1班级）' },
                  { value: 'multiple_teachers', label: '多教师协作（多教师-1课程-1班级）' },
                  { value: 'multiple_classes', label: '多班级教学（1教师-1课程-多班级）' },
                ]}
                {...assignForm.getInputProps('assignment_type')}
              />

              <Select
                label="选择教师"
                placeholder="请选择教师"
                required
                multiple
                data={[]} // TODO: 从API获取教师列表
                onChange={value =>
                  assignForm.setFieldValue(
                    'teacher_ids',
                    Array.isArray(value) ? value.map((v: string) => parseInt(v)) : []
                  )
                }
              />

              <Select
                label="选择班级"
                placeholder="请选择班级"
                required
                multiple
                data={[]} // TODO: 从API获取班级列表
                onChange={value =>
                  assignForm.setFieldValue(
                    'class_ids',
                    Array.isArray(value) ? value.map((v: string) => parseInt(v)) : []
                  )
                }
              />

              <Group grow>
                <DatePickerInput
                  label="开始日期"
                  placeholder="请选择开始日期"
                  required
                  {...assignForm.getInputProps('start_date')}
                />

                <DatePickerInput
                  label="结束日期"
                  placeholder="请选择结束日期"
                  required
                  {...assignForm.getInputProps('end_date')}
                />
              </Group>

              <Textarea
                label="备注"
                placeholder="请输入分配备注（可选）"
                rows={3}
                {...assignForm.getInputProps('notes')}
              />

              <Alert color="blue">
                <Text size="sm">系统将自动检查教师资质匹配、工作量平衡和时间冲突。</Text>
              </Alert>

              <Group justify="flex-end">
                <Button variant="light" onClick={closeAssignModal}>
                  取消
                </Button>
                <Button type="submit" loading={assignMutation.isPending}>
                  创建分配
                </Button>
              </Group>
            </Stack>
          </form>
        </Modal>

        {/* 工作量平衡模态框 - 需求5验收标准1 */}
        <Modal
          opened={workloadModalOpened}
          onClose={closeWorkloadModal}
          title="工作量平衡分析"
          size="lg"
        >
          <Stack>
            <Alert color="blue">
              <Text size="sm">工作量平衡功能可以分析教师工作负荷，提供平衡分配建议。</Text>
            </Alert>

            <Divider label="工作量统计" />

            <Grid>
              {workloadData?.slice(0, 6).map(workload => (
                <Grid.Col key={workload.teacher_id} span={4}>
                  <Card withBorder>
                    <Stack gap="xs">
                      <Text size="sm" fw={500}>
                        教师 {workload.teacher_id}
                      </Text>
                      <Progress
                        value={workload.workload_percentage}
                        color={getWorkloadColor(workload.workload_percentage)}
                        size="sm"
                      />
                      <Text size="xs" c="dimmed">
                        {workload.workload_percentage.toFixed(1)}% 负荷
                      </Text>
                    </Stack>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeWorkloadModal}>
                关闭
              </Button>
              <Button>生成平衡方案</Button>
            </Group>
          </Stack>
        </Modal>

        {/* 排课规则模态框 - 需求5验收标准4&5 */}
        <Modal
          opened={rulesModalOpened}
          onClose={closeRulesModal}
          title="教室排课规则管理"
          size="lg"
        >
          <Stack>
            <Alert color="blue">
              <Text size="sm">管理教室排课规则，包括基础规则和高级规则配置。</Text>
            </Alert>

            <Divider label="规则列表" />

            <Stack>
              {rulesData?.map(rule => (
                <Card key={rule.rule_id} withBorder>
                  <Group justify="space-between">
                    <Stack gap="xs">
                      <Group>
                        <Text fw={500}>{rule.rule_name}</Text>
                        <Badge
                          size="sm"
                          variant="light"
                          color={rule.rule_type === 'basic' ? 'blue' : 'purple'}
                        >
                          {rule.rule_type === 'basic' ? '基础' : '高级'}
                        </Badge>
                      </Group>

                      <Text size="sm" c="dimmed">
                        规则ID: {rule.rule_id}
                      </Text>

                      {rule.configuration && (
                        <Text size="xs" c="dimmed">
                          配置: {JSON.stringify(rule.configuration)}
                        </Text>
                      )}
                    </Stack>

                    <Group>
                      <Switch
                        checked={rule.enabled}
                        onChange={event => {
                          // TODO: 更新规则状态
                          void event.currentTarget.checked
                        }}
                      />
                      <ActionIcon variant="light" size="sm">
                        <IconEdit size={14} />
                      </ActionIcon>
                    </Group>
                  </Group>
                </Card>
              ))}
            </Stack>

            <Divider label="特殊情况豁免" />

            <Button variant="light" leftSection={<IconShield size={16} />}>
              申请规则豁免
            </Button>

            <Group justify="flex-end">
              <Button variant="light" onClick={closeRulesModal}>
                关闭
              </Button>
              <Button>保存规则</Button>
            </Group>
          </Stack>
        </Modal>
      </Stack>
    </Container>
  )
}
