/**
 * 课程表管理页面 - 需求13实现
 */
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
  Alert,
  Switch,
  NumberInput,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { DatePickerInput } from '@mantine/dates'
import {
  IconCalendar,
  IconPlus,
  IconRefresh,
  IconAlertTriangle,
  IconBrain,
} from '@tabler/icons-react'
import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

// 课程表相关类型定义
interface ScheduleItem {
  id: number
  lessonPlanId: number
  lessonPlanTitle: string
  classId: number
  className: string
  teacherId: number
  teacherName: string
  roomId: number
  roomName: string
  dayOfWeek: number // 0-6, 0为周日
  startTime: string
  endTime: string
  duration: number
  date: string
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled'
  conflicts: Array<{
    type: 'teacher' | 'room' | 'class'
    message: string
  }>
  attendanceCount?: number
  totalStudents?: number
}

interface ClassRoom {
  id: number
  name: string
  capacity: number
  equipment: string[]
  building: string
  floor: number
  isAvailable: boolean
}

interface TimeSlot {
  id: number
  name: string
  startTime: string
  endTime: string
  duration: number
}

export function SchedulePage(): JSX.Element {
  const [selectedWeek, setSelectedWeek] = useState<Date>(new Date())
  const [selectedClass, setSelectedClass] = useState<string>('')
  const [selectedItem, setSelectedItem] = useState<ScheduleItem | null>(null)
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week')

  // 模态框状态
  const [scheduleModalOpened, { open: openScheduleModal, close: closeScheduleModal }] =
    useDisclosure(false)
  const [conflictModalOpened, { open: openConflictModal, close: closeConflictModal }] =
    useDisclosure(false)
  const [generateModalOpened, { open: openGenerateModal, close: closeGenerateModal }] =
    useDisclosure(false)

  // 时间段配置
  const timeSlots: TimeSlot[] = [
    { id: 1, name: '第1节', startTime: '08:00', endTime: '09:30', duration: 90 },
    { id: 2, name: '第2节', startTime: '09:50', endTime: '11:20', duration: 90 },
    { id: 3, name: '第3节', startTime: '13:30', endTime: '15:00', duration: 90 },
    { id: 4, name: '第4节', startTime: '15:20', endTime: '16:50', duration: 90 },
    { id: 5, name: '第5节', startTime: '19:00', endTime: '20:30', duration: 90 },
  ]

  const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

  // 模拟数据查询 - 课程表
  const {
    data: scheduleData,
    isLoading: scheduleLoading,
    refetch: refetchSchedule,
  } = useQuery({
    queryKey: ['schedule', selectedWeek, selectedClass],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockData: ScheduleItem[] = [
        {
          id: 1,
          lessonPlanId: 1,
          lessonPlanTitle: '英语语法基础 - 时态概述',
          classId: 1,
          className: '英语四级A班',
          teacherId: 1,
          teacherName: '张老师',
          roomId: 101,
          roomName: 'A101',
          dayOfWeek: 1,
          startTime: '08:00',
          endTime: '09:30',
          duration: 90,
          date: '2024-01-22',
          status: 'scheduled',
          conflicts: [],
          attendanceCount: 28,
          totalStudents: 30,
        },
        {
          id: 2,
          lessonPlanId: 2,
          lessonPlanTitle: '阅读理解技巧训练',
          classId: 1,
          className: '英语四级A班',
          teacherId: 1,
          teacherName: '张老师',
          roomId: 102,
          roomName: 'A102',
          dayOfWeek: 3,
          startTime: '13:30',
          endTime: '15:00',
          duration: 90,
          date: '2024-01-24',
          status: 'scheduled',
          conflicts: [
            {
              type: 'room',
              message: '教室A102在此时段已被占用',
            },
          ],
          totalStudents: 30,
        },
        {
          id: 3,
          lessonPlanId: 3,
          lessonPlanTitle: '写作技巧专项训练',
          classId: 2,
          className: '英语四级B班',
          teacherId: 2,
          teacherName: '李老师',
          roomId: 103,
          roomName: 'A103',
          dayOfWeek: 2,
          startTime: '09:50',
          endTime: '11:20',
          duration: 90,
          date: '2024-01-23',
          status: 'completed',
          conflicts: [],
          attendanceCount: 25,
          totalStudents: 28,
        },
      ]

      return mockData.filter(
        item => selectedClass === '' || item.classId.toString() === selectedClass
      )
    },
  })

  // 模拟数据查询 - 教室列表
  const { data: roomsData } = useQuery({
    queryKey: ['classrooms'],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 200))

      const mockRooms: ClassRoom[] = [
        {
          id: 101,
          name: 'A101',
          capacity: 40,
          equipment: ['投影仪', '音响', '白板'],
          building: 'A栋',
          floor: 1,
          isAvailable: true,
        },
        {
          id: 102,
          name: 'A102',
          capacity: 35,
          equipment: ['投影仪', '电脑'],
          building: 'A栋',
          floor: 1,
          isAvailable: false,
        },
        {
          id: 103,
          name: 'A103',
          capacity: 50,
          equipment: ['投影仪', '音响', '白板', '电脑'],
          building: 'A栋',
          floor: 1,
          isAvailable: true,
        },
      ]

      return mockRooms
    },
  })

  const getStatusBadge = (status: string) => {
    const config = {
      scheduled: { label: '已安排', color: 'blue' },
      ongoing: { label: '进行中', color: 'green' },
      completed: { label: '已完成', color: 'gray' },
      cancelled: { label: '已取消', color: 'red' },
    }
    const { label, color } = config[status as keyof typeof config]
    return (
      <Badge color={color} size="sm">
        {label}
      </Badge>
    )
  }

  const getConflictBadge = (conflicts: Array<{ type: string; message: string }>) => {
    if (conflicts.length === 0) return null

    return (
      <Tooltip label={conflicts.map(c => c.message).join(', ')}>
        <Badge color="red" size="xs" leftSection={<IconAlertTriangle size={10} />}>
          {conflicts.length} 冲突
        </Badge>
      </Tooltip>
    )
  }

  const handleCreateSchedule = useCallback(() => {
    setSelectedItem(null)
    openScheduleModal()
  }, [openScheduleModal])

  const handleEditSchedule = useCallback(
    (item: ScheduleItem) => {
      setSelectedItem(item)
      openScheduleModal()
    },
    [openScheduleModal]
  )

  const handleGenerateSchedule = useCallback(async () => {
    try {
      // 模拟智能生成课程表
      await new Promise(resolve => setTimeout(resolve, 2000))

      notifications.show({
        title: '课程表生成完成',
        message: '已智能生成本周课程表，检测到2个时间冲突',
        color: 'green',
      })

      refetchSchedule()
      closeGenerateModal()
    } catch (error) {
      notifications.show({
        title: '课程表生成失败',
        message: '请稍后重试',
        color: 'red',
      })
    }
  }, [refetchSchedule, closeGenerateModal])

  // 渲染课程表网格
  const renderScheduleGrid = () => {
    if (!scheduleData) return null

    return (
      <Paper withBorder>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th style={{ width: 100 }}>时间</Table.Th>
              {weekDays.slice(1, 6).map((day, index) => (
                <Table.Th key={index} style={{ textAlign: 'center' }}>
                  {day}
                </Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {timeSlots.map(slot => (
              <Table.Tr key={slot.id}>
                <Table.Td>
                  <div>
                    <Text size="sm" fw={500}>
                      {slot.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {slot.startTime}-{slot.endTime}
                    </Text>
                  </div>
                </Table.Td>
                {[1, 2, 3, 4, 5].map(dayOfWeek => {
                  const item = scheduleData.find(
                    s => s.dayOfWeek === dayOfWeek && s.startTime === slot.startTime
                  )

                  return (
                    <Table.Td key={dayOfWeek} style={{ textAlign: 'center', verticalAlign: 'top' }}>
                      {item ? (
                        <Card
                          withBorder
                          p="xs"
                          style={{
                            cursor: 'pointer',
                            backgroundColor:
                              item.conflicts.length > 0 ? 'var(--mantine-color-red-0)' : undefined,
                          }}
                          onClick={() => handleEditSchedule(item)}
                        >
                          <Stack gap="xs">
                            <Text size="xs" fw={500} truncate>
                              {item.lessonPlanTitle}
                            </Text>
                            <Group gap="xs" justify="center">
                              <Badge size="xs" variant="light">
                                {item.className}
                              </Badge>
                              <Badge size="xs" variant="light">
                                {item.roomName}
                              </Badge>
                            </Group>
                            <Group gap="xs" justify="center">
                              {getStatusBadge(item.status)}
                              {getConflictBadge(item.conflicts)}
                            </Group>
                            {item.attendanceCount !== undefined && (
                              <Text size="xs" c="dimmed">
                                出勤: {item.attendanceCount}/{item.totalStudents}
                              </Text>
                            )}
                          </Stack>
                        </Card>
                      ) : (
                        <Button
                          variant="light"
                          size="xs"
                          onClick={handleCreateSchedule}
                          style={{ width: '100%', height: 80 }}
                        >
                          <IconPlus size={16} />
                        </Button>
                      )}
                    </Table.Td>
                  )
                })}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Paper>
    )
  }

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>课程表管理</Title>
          <Text c="dimmed" mt="xs">
            智能生成课程表，自动检测冲突并提供调整建议
          </Text>
        </div>
        <Group>
          <Button leftSection={<IconBrain size={16} />} variant="light" onClick={openGenerateModal}>
            智能生成
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreateSchedule}>
            添加课程
          </Button>
        </Group>
      </Group>

      {/* 筛选和控制 */}
      <Paper withBorder p="md" mb="xl">
        <Group justify="space-between">
          <Group>
            <DatePickerInput
              label="选择周次"
              placeholder="选择日期"
              value={selectedWeek}
              onChange={date => setSelectedWeek(date || new Date())}
              leftSection={<IconCalendar size={16} />}
            />
            <Select
              label="班级筛选"
              placeholder="选择班级"
              value={selectedClass}
              onChange={value => setSelectedClass(value || '')}
              data={[
                { value: '', label: '全部班级' },
                { value: '1', label: '英语四级A班' },
                { value: '2', label: '英语四级B班' },
                { value: '3', label: '英语四级C班' },
              ]}
              clearable
            />
          </Group>
          <Group>
            <Select
              label="视图模式"
              value={viewMode}
              onChange={value => setViewMode((value as 'week' | 'month') || 'week')}
              data={[
                { value: 'week', label: '周视图' },
                { value: 'month', label: '月视图' },
              ]}
            />
            <ActionIcon variant="light" size="lg">
              <IconRefresh size={16} />
            </ActionIcon>
          </Group>
        </Group>
      </Paper>

      {/* 课程表网格 */}
      {scheduleLoading ? (
        <Paper withBorder>
          <Stack align="center" p="xl">
            <Text c="dimmed">加载课程表中...</Text>
          </Stack>
        </Paper>
      ) : (
        renderScheduleGrid()
      )}

      {/* 冲突提醒 */}
      {scheduleData && scheduleData.some(item => item.conflicts.length > 0) && (
        <Alert color="red" mt="md" icon={<IconAlertTriangle size={16} />}>
          <Text fw={500} mb="xs">
            检测到课程表冲突
          </Text>
          <Text size="sm">
            发现 {scheduleData.filter(item => item.conflicts.length > 0).length} 个时间冲突，
            请点击相应课程进行调整或使用智能调整功能。
          </Text>
          <Button size="xs" mt="xs" onClick={openConflictModal}>
            查看详情
          </Button>
        </Alert>
      )}

      {/* 智能生成模态框 */}
      <Modal
        opened={generateModalOpened}
        onClose={closeGenerateModal}
        title="智能生成课程表"
        size="md"
        centered
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text size="sm">系统将根据教案课时要求、教室可用时段和教师时间表智能生成课程表</Text>
          </Alert>

          <Select
            label="生成范围"
            placeholder="选择生成范围"
            data={[
              { value: 'week', label: '本周' },
              { value: 'month', label: '本月' },
              { value: 'semester', label: '整学期' },
            ]}
            defaultValue="week"
          />

          <Group grow>
            <Select
              label="优先级"
              placeholder="选择优先级"
              data={[
                { value: 'teacher', label: '教师时间优先' },
                { value: 'room', label: '教室利用率优先' },
                { value: 'student', label: '学生课程分布优先' },
              ]}
              defaultValue="teacher"
            />
            <NumberInput
              label="每日最大课时"
              placeholder="课时数"
              min={1}
              max={8}
              defaultValue={4}
            />
          </Group>

          <Switch label="自动冲突解决" description="自动调整冲突的课程安排" defaultChecked />

          <Switch label="发送通知" description="生成完成后通知相关教师和学生" defaultChecked />

          <Group justify="flex-end">
            <Button variant="light" onClick={closeGenerateModal}>
              取消
            </Button>
            <Button onClick={handleGenerateSchedule}>开始生成</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 课程编辑模态框 */}
      <Modal
        opened={scheduleModalOpened}
        onClose={closeScheduleModal}
        title={selectedItem ? '编辑课程安排' : '添加课程安排'}
        size="lg"
      >
        <Stack gap="md">
          <Group grow>
            <Select
              label="教案"
              placeholder="选择教案"
              data={[
                { value: '1', label: '英语语法基础 - 时态概述' },
                { value: '2', label: '阅读理解技巧训练' },
                { value: '3', label: '写作技巧专项训练' },
              ]}
              required
            />
            <Select
              label="班级"
              placeholder="选择班级"
              data={[
                { value: '1', label: '英语四级A班' },
                { value: '2', label: '英语四级B班' },
                { value: '3', label: '英语四级C班' },
              ]}
              required
            />
          </Group>

          <Group grow>
            <Select
              label="教室"
              placeholder="选择教室"
              data={
                roomsData?.map(room => ({
                  value: room.id.toString(),
                  label: `${room.name} (${room.capacity}人)`,
                  disabled: !room.isAvailable,
                })) || []
              }
              required
            />
            <Select
              label="教师"
              placeholder="选择教师"
              data={[
                { value: '1', label: '张老师' },
                { value: '2', label: '李老师' },
                { value: '3', label: '王老师' },
              ]}
              required
            />
          </Group>

          <Group grow>
            <Select
              label="星期"
              placeholder="选择星期"
              data={[
                { value: '1', label: '周一' },
                { value: '2', label: '周二' },
                { value: '3', label: '周三' },
                { value: '4', label: '周四' },
                { value: '5', label: '周五' },
              ]}
              required
            />
            <Select
              label="时间段"
              placeholder="选择时间段"
              data={timeSlots.map(slot => ({
                value: slot.id.toString(),
                label: `${slot.name} (${slot.startTime}-${slot.endTime})`,
              }))}
              required
            />
          </Group>

          <DatePickerInput label="开始日期" placeholder="选择开始日期" required />

          <Group justify="flex-end">
            <Button variant="light" onClick={closeScheduleModal}>
              取消
            </Button>
            <Button onClick={closeScheduleModal}>{selectedItem ? '更新' : '添加'}</Button>
          </Group>
        </Stack>
      </Modal>

      {/* 冲突详情模态框 */}
      <Modal
        opened={conflictModalOpened}
        onClose={closeConflictModal}
        title="课程表冲突详情"
        size="lg"
      >
        <Stack gap="md">
          <Alert color="red">
            <Text size="sm">以下课程存在时间冲突，请调整安排或使用智能调整功能</Text>
          </Alert>

          {scheduleData
            ?.filter(item => item.conflicts.length > 0)
            .map(item => (
              <Card key={item.id} withBorder>
                <Group justify="space-between" mb="md">
                  <div>
                    <Text fw={500}>{item.lessonPlanTitle}</Text>
                    <Text size="sm" c="dimmed">
                      {weekDays[item.dayOfWeek]} {item.startTime}-{item.endTime}
                    </Text>
                  </div>
                  <Badge color="red">{item.conflicts.length} 个冲突</Badge>
                </Group>

                <Stack gap="xs">
                  {item.conflicts.map((conflict, index) => (
                    <Alert key={index} color="orange" variant="light">
                      <Group justify="space-between">
                        <Text size="sm">{conflict.message}</Text>
                        <Button size="xs" variant="light">
                          自动调整
                        </Button>
                      </Group>
                    </Alert>
                  ))}
                </Stack>
              </Card>
            ))}

          <Group justify="flex-end">
            <Button variant="light" onClick={closeConflictModal}>
              关闭
            </Button>
            <Button leftSection={<IconBrain size={16} />}>智能解决所有冲突</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}
